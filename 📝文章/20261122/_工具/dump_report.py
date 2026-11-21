# -*- coding: utf-8 -*-
"""从 A 层内部报告里抽取逐场关键行，供 B 层公开稿对照（只读，不改报告）。

用法：
    python -X utf8 "📝文章/20261122/_工具/dump_report.py" 004 005 007
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path("I:/阿飞说球")
REPORT = BASE / "📝文章" / "20261122" / "20261122_周日16场_内部分析报告.md"

PATS = {
    "状态": r"近期状态（近 5 场逐场重算[^）]*）：(.+)",
    "逐场": r"逐场战绩（近 5）：(.+)",
    "交锋": r"历史交锋：(.+)",
    "核心矛盾": r"\*\*核心矛盾[^*]*\*\*：(.+)",
    "胜负手": r"\*\*胜负手[^*]*\*\*：(.+)",
    "看点": r"\*\*比赛看点\*\*：(.+)",
    "分级": r"把握分级与共振：\*\*(.+?)\*\*",
    "方向": r"- 方向：(.+)",
    "比分": r"- 比分：(.+)",
    "融合": r"融合三向（出结论用，λ_C）：\*\*(.+?)\*\*",
    "媒体": r"- 全球/主流媒体前瞻：(.+)",
}


def main() -> int:
    want = set(sys.argv[1:])
    text = REPORT.read_text(encoding="utf-8")
    parts = re.split(r"^### ", text, flags=re.M)[1:]
    for sec in parts:
        m = re.match(r"(\d{3})\s+(.+)", sec)
        if not m:
            continue
        no, head = m.group(1), m.group(2).split("｜")
        if want and no not in want:
            continue
        print("=" * 70)
        print(no, "｜".join(head[:3]))
        for key, pat in PATS.items():
            mm = re.search(pat, sec)
            if mm:
                val = re.sub(r"\s+", " ", mm.group(1)).strip()
                print(f"  {key}: {val}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
