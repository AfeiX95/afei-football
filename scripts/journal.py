# -*- coding: utf-8 -*-
"""
阿飞说球 — 项目进度日记生成器（日记 / 工作交接）

自动汇总「指定日期」的项目进度，输出 docs/日记/YYYY-MM-DD.md：
  · 当日提交（git log）
  · 当日产出（按顶层目录分组的文件变更 + 未提交变更）
  · 状态快照（state/model-state.json：批次/累计/方向率/规则数/任务数）
  · 交接指针（HANDOFF 最新节标题 + 下一步目标首条）

设计要点：
  · 幂等：重复运行只刷新 AUTO 区块；<!-- AUTO:END --> 之后的人工「手记」永不覆盖
  · 分工：HANDOFF = 面向下一次会话的交接；日记 = 面向往后回看的时间线
  · 纯本地、零依赖（只用标准库）

用法：
    python scripts/journal.py                    # 今天
    python scripts/journal.py --date 2026-09-19  # 指定日期
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "日记"


def git(*args):
    """执行 git 命令，返回 UTF-8 文本（失败返回空串）。

    注意：固定 -c core.quotepath=false，否则中文/emoji 路径会被转义成
    八进制形式（如 "\\360\\237\\223\\232..."），导致分组与可读性都失效。
    """
    try:
        r = subprocess.run(
            ["git", "-c", "core.quotepath=false", *args],
            capture_output=True,
            cwd=str(ROOT),
        )
        return r.stdout.decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


def collect_commits(day: str):
    since = f"{day} 00:00:00"
    until = f"{day} 23:59:59"
    out = git(
        "log",
        f"--since={since}",
        f"--until={until}",
        "--pretty=format:- `%h` %s",
    )
    lines = [l for l in out.splitlines() if l.strip()]
    return lines if lines else ["- （当日无提交）"]


def collect_files(day: str):
    since = f"{day} 00:00:00"
    until = f"{day} 23:59:59"
    files = []
    # 当日提交涉及的文件
    out = git("log", f"--since={since}", f"--until={until}", "--name-only", "--pretty=format:")
    files += [l.strip() for l in out.splitlines() if l.strip()]
    # 未提交的工作区变更（-uall 让未跟踪目录展开为具体文件）
    dirty = git("status", "--porcelain", "-uall")
    for line in dirty.splitlines():
        p = line[3:].strip().strip('"')
        if p:
            files.append(p)
    # 去重 + 规整分隔符
    uniq = []
    for f in files:
        f = f.replace("/", "\\")
        if f not in uniq:
            uniq.append(f)
    return uniq


def group_by_top(files):
    groups = {}
    for f in files:
        top = f.split("\\")[0] if "\\" in f else "(根目录)"
        groups.setdefault(top, []).append(f)
    return groups


def state_snapshot():
    p = ROOT / "state" / "model-state.json"
    if not p.exists():
        return "- （未找到 state/model-state.json）"
    try:
        s = json.loads(p.read_text(encoding="utf-8"))
        c = s.get("calibration", {})
        rate = c.get("direction_rate", 0) * 100
        return "\n".join(
            [
                f"- 批次：**batch{c.get('last_batch')}**（{c.get('last_batch_date')}）",
                f"- 累计场次：**{c.get('total_matches')}**　方向正确：{c.get('direction_correct')}（{rate:.1f}%）",
                f"- 候选/正式规则：{len(s.get('candidate_rules', {}))} 条　"
                f"活动任务：{len(s.get('active_tasks', []))} 条　"
                f"待校验文章：{len(s.get('published_articles_pending_check', []))} 条",
                f"- 模型版本：{s.get('model_version')}",
            ]
        )
    except Exception as e:
        return f"- （state 解析失败：{e}）"


def handoff_pointer():
    p = ROOT / "docs" / "HANDOFF.md"
    if not p.exists():
        return "- （未找到 docs/HANDOFF.md）"
    lines = p.read_text(encoding="utf-8").splitlines()
    idx = [i for i, l in enumerate(lines) if l.startswith("## ")]
    if not idx:
        return "- （HANDOFF 无分节）"
    last = idx[-1]
    block = [f"- 最新交接节：{lines[last].strip()}"]
    # 该节内"下一步目标"的首条
    for i in range(last, len(lines)):
        if "下一步目标" in lines[i]:
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## "):
                    break
                if re.match(r"^\s*-\s", lines[j]):
                    block.append(f"- 下一步首条：{lines[j].strip()}")
                    break
            break
    return "\n".join(block)


MANUAL_DEFAULT = """## ✍️ 手记（人工，脚本永不覆盖）

> 记当天的心得、踩坑、决策理由、明天第一件事。HANDOFF 面向"下一次会话"，这里面向"往后回看"。

- 
"""


def build(day: str):
    commits = collect_commits(day)
    files = collect_files(day)
    groups = group_by_top(files)

    if groups:
        prod = ""
        for top, items in groups.items():
            prod += f"### {top}\n"
            for f in sorted(items):
                prod += f"- `{f}`\n"
            prod += "\n"
    else:
        prod = "- （当日无文件变更）\n"

    auto = (
        f"<!-- AUTO:BEGIN｜由 scripts/journal.py 生成，勿手改此区块 -->\n"
        f"## 📌 当日提交（{len([c for c in commits if c.startswith('- `')])} 条）\n\n"
        + "\n".join(commits)
        + "\n\n## 📦 当日产出\n\n"
        + prod
        + "## 📊 状态快照\n\n"
        + state_snapshot()
        + "\n\n## 🔗 交接指针\n\n"
        + handoff_pointer()
        + "\n\n<!-- AUTO:END -->\n"
    )
    return auto


def main():
    ap = argparse.ArgumentParser(description="生成项目进度日记")
    ap.add_argument("--date", default=date.today().isoformat(), help="目标日期 yyyy-MM-dd，默认今天")
    args = ap.parse_args()
    day = args.date

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / f"{day}.md"

    # 保留人工手记
    manual = MANUAL_DEFAULT
    if out_file.exists():
        old = out_file.read_text(encoding="utf-8")
        m = re.search(r"(?s)<!-- AUTO:END -->(.*)$", old)
        if m and m.group(1).strip():
            manual = m.group(1).strip() + "\n"

    doc = f"# {day} 工作日记\n\n{build(day)}\n{manual}"
    out_file.write_text(doc, encoding="utf-8")
    print(f"[OK] journal written: docs/日记/{day}.md")
    print(f"     size={out_file.stat().st_size} bytes")


if __name__ == "__main__":
    main()
