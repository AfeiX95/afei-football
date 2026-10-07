#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""开工简报（Brief）— 一条命令替代「全量读 HANDOFF + model-state.json」。

用法：
    python scripts/brief.py            # 紧凑简报（默认，约 3KB）
    python scripts/brief.py --handoff  # 额外打印最新交接节全文
    python scripts/brief.py --json     # 结构化输出

设计原则（token 纪律）：
  · 只打印热数据：批次统计、真待办（open_items）、待校验文章、最新交接节位置。
  · 冷数据（state/task-log.json、HANDOFF 历史节）只给路径与行号，让 agent 按需定点读。
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "model-state.json"
HANDOFF = ROOT / "docs" / "HANDOFF.md"
ARTICLES = ROOT / "📝文章"
JOURNALS = ROOT / "docs" / "日记"

TYPE_ORDER = ["待校验", "待开奖", "数据缺口", "研究", "存量", "流程"]


def load_state():
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] state 解析失败: {e}", file=sys.stderr)
        return {}


def handoff_sections():
    """返回 [(标题, 起始行号, 行数)]，行号 1-based，含结尾行。"""
    if not HANDOFF.exists():
        return [], 0
    lines = HANDOFF.read_text(encoding="utf-8").splitlines()
    idx = [i for i, l in enumerate(lines) if l.startswith("## ")]
    out = []
    for n, i in enumerate(idx):
        end = idx[n + 1] - 1 if n + 1 < len(idx) else len(lines) - 1
        out.append((lines[i].strip(), i + 1, end - i + 1))
    return out, len(lines)


def article_dirs(limit=3):
    if not ARTICLES.exists():
        return []
    dirs = [d for d in ARTICLES.iterdir() if d.is_dir() and re.fullmatch(r"\d{8}", d.name)]
    dirs.sort(key=lambda d: d.name, reverse=True)
    return [(d.name, len(list(d.glob("*.md")))) for d in dirs[:limit]]


def fmt_pending(p):
    if isinstance(p, dict):
        raw = str(p.get("path") or p.get("file", ""))
        date = p.get("date") or ""
        if not date:
            m = re.search(r"(\d{4})-?(\d{2})-?(\d{2})", raw)
            date = m.group(0) if m else "?"
        name = Path(raw).name
        extra = []
        if p.get("words"):
            extra.append(f"{p['words']}字")
        if p.get("gate"):
            extra.append(f"门禁{p['gate']}")
        if p.get("ai"):
            extra.append(f"AI{p['ai']}")
        tail = ("　" + "／".join(extra)) if extra else ""
        return f"{date}　{name}{tail}"
    m = re.search(r"📝文章[/\\](\d{8})[/\\]([^)（\s]+)", p)
    if m:
        return f"{m.group(1)}　{m.group(2)[:46]}"
    return p[:70]


def main():
    ap = argparse.ArgumentParser(description="阿飞说球开工简报")
    ap.add_argument("--handoff", action="store_true", help="额外打印最新交接节全文")
    ap.add_argument("--json", action="store_true", help="结构化输出")
    args = ap.parse_args()

    s = load_state()
    c = s.get("calibration", {})
    open_items = s.get("open_items", s.get("active_tasks", []))
    pending = s.get("pending_checks", s.get("published_articles_pending_check", []))
    secs, hl = handoff_sections()
    latest = secs[-1] if secs else ("（无）", 0, 0)

    if args.json:
        print(json.dumps({
            "now": datetime.now().strftime("%Y-%m-%d %H:%M %A"),
            "model_version": s.get("model_version"),
            "schema_version": s.get("schema_version"),
            "calibration": c,
            "open_items": open_items,
            "pending_checks": pending,
            "handoff_latest": {"title": latest[0], "start": latest[1], "lines": latest[2], "total": hl},
            "candidate_rules": sorted(s.get("candidate_rules", {}).keys()),
            "counters": s.get("counters", {}),
        }, ensure_ascii=False, indent=2))
        return

    W = 62
    print("=" * W)
    print("  阿飞说球 · 开工简报   " + datetime.now().strftime("%Y-%m-%d %H:%M %A"))
    print("=" * W)
    print(f"[模型] {s.get('model_version')}　[state schema] v{s.get('schema_version')}　"
          f"[updated] {s.get('updated')}")
    rate = c.get("direction_rate", 0) * 100
    print(f"[批次] batch{c.get('last_batch')}（{c.get('last_batch_date')}）　"
          f"累计 {c.get('total_matches')} 场　方向 {c.get('direction_correct')}（{rate:.1f}%）")
    print(f"[规则] 候选+正式 {len(s.get('candidate_rules', {}))} 条　"
          f"[待办] {len(open_items)} 条　[待校验] {len(pending)} 篇")

    print("-" * W)
    print(f"■ 待办 open_items（{len(open_items)} 条）")
    groups = {}
    for it in open_items:
        if isinstance(it, dict):
            groups.setdefault(it.get("type", "其他"), []).append(it.get("text", ""))
        else:
            groups.setdefault("其他", []).append(str(it))
    for t in TYPE_ORDER + [k for k in groups if k not in TYPE_ORDER]:
        if t not in groups:
            continue
        print(f"  [{t}] {len(groups[t])} 条")
        for txt in groups[t]:
            print(f"    · {txt}")

    print("-" * W)
    print(f"■ 待校验文章（{len(pending)} 篇，逐篇按 90 分钟口径复核）")
    for p in pending:
        print(f"    · {fmt_pending(p)}")

    print("-" * W)
    print("■ 最新交接节（只读这一段，勿全量读 HANDOFF）")
    print(f"    {latest[0]}")
    print(f"    位置 docs/HANDOFF.md:{latest[1]}-{latest[1] + latest[2] - 1}（全文件 {hl} 行）")
    print(f"    → read docs/HANDOFF.md offset={latest[1]} limit={latest[2]}")

    dirs = article_dirs()
    if dirs:
        print("-" * W)
        print("■ 📝文章 最近目录")
        print("    " + "　".join(f"{n}({k}篇)" for n, k in dirs))

    print("-" * W)
    print("■ 候选规则名（明细见 afei-writing-standards / 修正规则.md）")
    names = sorted(s.get("candidate_rules", {}).keys())
    for i in range(0, len(names), 4):
        print("    " + "　".join(names[i:i + 4]))

    print("-" * W)
    print("■ 写文／收工命令")
    print("    python scripts/preflight.py <文章.md>    # 字数(R32)+发布门禁 一键盘")
    print("    python scripts/wordcount.py <文章.md>    # 仅字数")
    print("    python check_article.py <文章.md>        # 仅门禁（cwd=📚知识库/模型脚本）")
    print("    收工：HANDOFF 追加一节 + state 同步 + python scripts/journal.py + git commit")

    print("-" * W)
    print("■ Token 纪律")
    print(f"    · HANDOFF 全量 {hl} 行，只读上面给的区间")
    print("    · 技能按需加载：先看 📚知识库/skills/INDEX.md 定位小节，别整篇读")
    print("    · state/task-log.json = 冷数据（闭环历史），只在下批校验收尾时读")
    print("    · 三种记录：HANDOFF=交接(只追加节)｜docs/日记=时间线｜state=机器状态")
    print("=" * W)

    if args.handoff and secs:
        print()
        lines = HANDOFF.read_text(encoding="utf-8").splitlines()
        print(f"--- {latest[0]} (docs/HANDOFF.md:{latest[1]}-{latest[1] + latest[2] - 1}) ---")
        print("\n".join(lines[latest[1] - 1:latest[1] - 1 + latest[2]]))


if __name__ == "__main__":
    main()
