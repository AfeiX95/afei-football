# -*- coding: utf-8 -*-
"""读者视角过滤（R55）：扫公开稿里的「内部语言」，防止把分析日志当文章发。

用法
    python -X utf8 scripts/reader_lens.py "📝文章/20261022/xxx.md"
    python -X utf8 scripts/reader_lens.py "📝文章/20261022/xxx.md" --strict   # 有命中退出码 1

口径（R55 第三条）：以下默认不出现在公开文章里
    概率差值 / 去水与返还率 / 让球三格映射 / 样本外回测与校准 / 规则代号与工具名 /
    「同一事件」「本批最大分歧」「口径已修正」/ 没解释的冷门指数 / 内部流程词 /
    模型口径（后台模型 / 数据快照 / 一致性校验 / 点估计 / 权重）/ 押注用语（押·下注·重仓）/
    让球行话（球半·平手盘·让半档·上下盘）

注意：命中不等于错。当某项数据本身就是文章主题、且能用球迷语言解释时，可保留；
本脚本只负责把「可能是内部语言」的句子摆到眼前，由人做取舍。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RULES = [
    ("概率差值", re.compile(r"差\s*\d+(?:\.\d+)?\s*个?百分点|百分点差|相差\s*\d+(?:\.\d+)?\s*个?百分点")),
    ("模型对照", re.compile(r"(?:模型|后台模型)[^。！？\n]{0,12}\d+(?:\.\d+)?\s*%")),
    ("去水口径", re.compile(r"去水|返还率|抽水|三格|各格")),
    ("让球映射", re.compile(r"让球\s*[+＋−\-]?\s*\d|受让\s*[一二两三四半]?球|让[一二两三四]球")),
    ("校验流程", re.compile(r"样本外|回测|校准|同一事件|事件\s*ID|证据链|方法论|观察假设|判据")),
    ("代号工具", re.compile(r"\bR\d{2}\b|\bS\d{2}\b|Skill|门禁|PASS|scan_form|prob_gate|preflight")),
    ("内部叙事", re.compile(r"本批最大|最大分歧|口径(?:已)?(?:修正|对齐|统一)|不是之前的数字|之前的稿|评审|外部意见")),
    ("未解释指标", re.compile(r"冷门指数|置信度|Edge|溢价|方差")),
    ("博彩用语", re.compile(r"让球盘|水位|盘口|赔率|投注|串关|稳胆|包中|回血|上岸")),
    # 2026-10-27 用户要求（m02460）：把「内部分析口径」与「押注/让球行话」也拦下来
    ("模型口径", re.compile(r"后台模型|模型\s*[vV]?\d+\.\d|数据快照|快照\s*\d{6,}|"
                            r"一致性校验|点估计|置信区间|区间内|样本量|样本外|融合权重|权重\s*\d")),
    ("押注用语", re.compile(r"押(?!金|韵|运)|下注|下重手|梭哈|重仓|稳胆|跟单|中奖|回本")),
    ("让球行话", re.compile(r"球半|平手盘|让半档|退一档|抬一档|上盘|下盘|让平半|受让半球")),
]


def scan(text: str) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">") or s.startswith("数据来源"):
            continue
        for name, rx in RULES:
            m = rx.search(s)
            if m:
                snippet = s[max(0, m.start() - 12): m.end() + 16]
                hits.append((i, name, snippet))
    return hits


def main() -> None:
    ap = argparse.ArgumentParser(description="R55 读者视角过滤：扫公开稿里的内部语言")
    ap.add_argument("path", help="文章 md 路径")
    ap.add_argument("--strict", action="store_true", help="有命中则退出码 1")
    a = ap.parse_args()

    p = a.path if os.path.isabs(a.path) else os.path.join(ROOT, a.path)
    text = io.open(p, encoding="utf-8").read()
    hits = scan(text)

    print("=" * 60)
    print("R55 读者视角过滤 · %s" % os.path.basename(p))
    print("=" * 60)
    if not hits:
        print("  ✅ 未检出内部语言（概率差 / 去水 / 让球映射 / 回测 / 代号）")
        return
    for ln, name, snip in hits:
        print("  · [%s] 第 %d 行 … %s …" % (name, ln, snip))
    print("-" * 60)
    print("  %d 处待人工判断：数据本身是主题就留，只是分析过程就删。" % len(hits))
    if a.strict:
        sys.exit(1)


if __name__ == "__main__":
    main()
