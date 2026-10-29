# -*- coding: utf-8 -*-
"""发布前 A/B 分层安全闸（防止把内部稿或内部口径发上平台）。

用法：
    python -X utf8 scripts/check_pub_safety.py 20261030          # 扫某天的文章目录
    python -X utf8 scripts/check_pub_safety.py 20261030 --files a.md b.md

三层检查：
  1. 文件分层：文件名命中 A 层标记（内部分析报告/全盘分析报告/赛后校验/_cards/_model/校验）→ FAIL，禁止发布；
     只有文件名带「前瞻」的 .md 才算 B 层可发布稿。
  2. 内部口径：模型/泊松/蒙特卡洛/λ/EV/凯利/融合/权重/样本/快照/后台/内部/数据侧/点估计/置信/区间。
  3. 平台红线：盘口行话、博彩引导、竞彩口径、表格行、<details> 块、联系方式。
退出码：0 全部干净；1 有 FAIL。
"""
from __future__ import annotations

import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

A_LAYER_MARKS = ("内部分析报告", "全盘分析报告", "赛后校验", "_cards", "_model", "校验", "台账")

GROUPS = {
    "内部口径": ["模型", "泊松", "蒙特卡洛", "λ", "EV", "凯利", "融合", "权重",
                 "样本", "快照", "后台", "内部", "数据侧", "点估计", "置信", "区间"],
    "盘口行话": ["盘口", "赔率", "庄家", "水位", "受让", "球半", "上盘", "下盘", "走盘",
                 "让球盘", "打穿", "穿盘"],
    "博彩引导": ["投注", "下注", "重注", "跟单", "稳胆", "必中", "稳赢", "串关", "过关",
                 "私信", "微信号", "二维码", "扫码"],
    "竞彩口径": ["竞彩", "彩票", "彩果", "让球"],
}


def check_one(path: str) -> tuple[bool, list[str]]:
    name = os.path.basename(path)
    problems: list[str] = []
    if any(m in name for m in A_LAYER_MARKS):
        problems.append(f"文件分层：{name} 命中 A 层标记，禁止上传（内部稿只留在本地）")
    text = open(path, encoding="utf-8").read()
    for group, words in GROUPS.items():
        hits = [w for w in words if w in text]
        if hits:
            problems.append(f"{group}：{', '.join(hits)}")
    if re.search(r"^\|", text, re.M):
        problems.append("结构残留：表格行（内部报告格式，公开稿不出现）")
    if "<details>" in text:
        problems.append("结构残留：<details> 块")
    return (not problems), problems


def main() -> int:
    day = sys.argv[1] if len(sys.argv) > 1 else ""
    if "--files" in sys.argv:
        files = sys.argv[sys.argv.index("--files") + 1:]
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "📝文章", day, "*.md")))
    if not files:
        print(f"没找到稿件：📝文章/{day}/*.md")
        return 1

    print("=" * 62)
    print(f"  发布前 A/B 分层安全闸　{day or ''}　共 {len(files)} 个文件")
    print("=" * 62)
    bad = 0
    for f in files:
        ok, problems = check_one(f)
        layer = "B层·公开稿" if ok else "涉及内部/红线"
        print(f"\n{'✅' if ok else '❌'} [{layer}] {os.path.basename(f)}")
        for p in problems:
            print(f"     - {p}")
        bad += 0 if ok else 1

    print("\n" + "-" * 62)
    if bad:
        print(f"结果：{bad}/{len(files)} 个文件不可直接发布 ❌（A 层内部稿本来就不该上平台）")
        return 1
    print(f"结果：{len(files)}/{len(files)} 干净 ✅　可发布（仍须过 preflight 与 check_dup）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
