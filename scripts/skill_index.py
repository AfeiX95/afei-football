#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成技能索引 📚知识库/skills/INDEX.md（技能按需加载入口）。

用法：
    python scripts/skill_index.py

何时重跑：**任何 SKILL.md 增删或改动了标题**（新增规则节、拆章）之后。
索引给出行号，agent 便可 `read SKILL.md offset=<行> limit=<长度>` 定点加载，
避免整篇读（242KB ≈60K tokens → 索引 20KB ≈5K tokens）。

设计取舍（2026-10-11 修）：三级小节（`###`）在长技能里有 479 条，全进索引会把
INDEX.md 从 18KB 撑到 40KB+，得不偿失 → 所以只把**编号型标题**（R1/R41/C15b…）
收进「规则编号速查」一节（一行一个技能），其余三级小节按需 `grep "^### " <技能>/SKILL.md` 直接拿行号。
"""
import re
import sys
from pathlib import Path

# Windows 控制台默认 GBK，打印 📚 等 emoji 会 UnicodeEncodeError（2026-10-11 修）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "📚知识库" / "skills"
OUT = SK / "INDEX.md"

# 加载策略：按行数分档
def policy(n):
    if n <= 200:
        return "全量读"
    if n <= 400:
        return "读前 30 行 + 跳读目标小节"
    return "先查本索引定位，只读目标小节"


def clean(s, width=72):
    s = re.sub(r"\s+", " ", s).replace("|", "／").strip().strip('"').strip()
    return (s[:width] + "…") if len(s) > width else (s or "—")


def scan():
    dirs = [x for x in SK.iterdir() if x.is_dir() and (x / "SKILL.md").exists()]
    dirs.sort(key=lambda p: -(p / "SKILL.md").stat().st_size)
    rows, details = [], []
    for d in dirs:
        f = d / "SKILL.md"
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        n = len(lines)
        name = ver = desc = ""
        for l in lines[:20]:
            if l.startswith("name:"):
                name = l.split(":", 1)[1].strip()
            elif l.startswith("version:"):
                ver = l.split(":", 1)[1].strip()
            elif l.startswith("description:"):
                desc = l.split(":", 1)[1].strip()
        heads, ids, in_code = [], [], False
        for i, l in enumerate(lines, 1):
            if l.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            m = re.match(r"^(#{2,3})\s+(\S.*)$", l)
            if not m:
                continue
            title = m.group(2).strip()
            if m.group(1) == "##":
                heads.append((i, title[:52]))
            # 编号型标题（R1 / R41 / C15b / R20b…）→ 速查表；只收本项目的规则系列
            # R（写作规则）/ C（修正规则），避免把 L1/L2 这类管线步骤误收进来。
            rid = re.match(r"^([RC]\d{1,2}[a-z]?)(?=[\s\.、:：]|$)", title)
            if rid:
                ids.append((i, rid.group(1)))
        rows.append((d.name, n, ver, policy(n), desc))
        details.append((d.name, n, heads, ids))
    return rows, details


def main():
    rows, details = scan()
    heavy = [r for r in rows if r[1] > 400]
    heavy_txt = "，".join("`%s` %d 行 ≈%dK tokens" % (r[0], r[1], r[1] // 70) for r in heavy)
    out = [
        "# 技能索引（按需加载 · 免全量读）",
        "",
        "> 生成：`python scripts/skill_index.py`（SKILL.md 增删或改标题后重跑）。",
        "> **用法**：先在本文件定位技能与目标小节行号，再",
        "> `read 📚知识库/skills/<技能>/SKILL.md offset=<行号> limit=<小节长度>`，避免整篇加载。",
        "> 行数 > 400 的技能**禁止全量读**（%s）。" % heavy_txt,
        "",
        "## 常用组合（按任务，只加载需要的）",
        "",
        "| 任务 | 加载 |",
        "|---|---|",
        "| 写/改赛事前瞻文章 | `afei-writing-standards`（按小节：规则清单/格式模板/合规替换）→ `football-match-preview-article`（格式与结构）→ `humanizer-zh`（去 AI 味） |",
        "| 跑后台模型出预测 | `match-model-pipeline`（按小节：管线步骤 / 国内联赛模式 / λ 估算） |",
        "| 赛后批次校验 | `football-calibration-batch`（109 行，可全量）|",
        "| 只记账 / 交接 / 改 state | **不需要任何技能** |",
        "| 头条数据优化 | `football-toutiao-content-optimization`（233 行，读前 30 行 + 跳读）|",
        "",
        "## 一览",
        "",
        "| 技能 | 行数 | 版本 | 加载策略 | 用途 |",
        "|---|---:|---|---|---|",
    ]
    for name, n, ver, pol, desc in rows:
        out.append(f"| `{name}` | {n} | {ver} | {pol} | {clean(desc)} |")
    fast = [(name, n, ids) for name, n, heads, ids in details if ids]
    if fast:
        out += ["", "## 规则编号速查（编号 → 行号）", "",
                "> 编号型标题（R1/R41/C15b…）可能藏在三级 `###` 里，这里给出行号，免去全篇找。", ""]
        for name, n, ids in fast:
            out.append("| `%s` | %s |" % (name, " · ".join("L%d=%s" % (i, k) for i, k in ids)))
    out += ["", "## 分节行号（二级 `##`）", "",
            "> 三级小节（`###`）不在此逐一索引（长技能里有 479 条，全收会让本文件翻倍）。",
            "> 要定位时直接 `grep \"^### \" 📚知识库/skills/<技能>/SKILL.md`，零成本拿行号。", ""]
    for name, n, heads, ids in details:
        out.append(f"### `{name}`（{n} 行，{policy(n)}）")
        if heads:
            out += [f"- L{i}｜{h}" for i, h in heads]
        else:
            out.append("- （无二级标题）")
        out.append("")
    OUT.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"[OK] {OUT.relative_to(ROOT)}  {OUT.stat().st_size} bytes  "
          f"skills={len(rows)}  headings={sum(len(h) for _, _, h, _ in details)}  "
          f"ids={sum(len(x) for _, _, x in fast)}")


if __name__ == "__main__":
    main()
