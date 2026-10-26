#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""给文章补齐 / 规范化「固定尾块」：话题标签 + 数据来源 + 免责声明。

幂等：重复执行不会叠加多块，只会把已有三块重排到文件末尾并统一措辞。

用法：
    python -X utf8 scripts/tail_block.py "<文章.md>" --tags "#日职,#韩职" [--dry-run]
    python -X utf8 scripts/tail_block.py "<文章.md>"            # 按联赛关键词自动猜标签

说明文档：📚知识库/写作指南/文章固定尾块.md
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

LEAGUE_TAGS = {
    "日职": "#日职", "J联赛": "#日职",
    "韩职": "#韩职", "K联赛": "#韩职",
    "英超": "#英超", "英冠": "#英冠",
    "意甲": "#意甲", "德甲": "#德甲", "德乙": "#德乙",
    "西甲": "#西甲", "法甲": "#法甲", "葡超": "#葡超",
    "荷甲": "#荷甲", "荷乙": "#荷乙", "瑞超": "#瑞超", "澳超": "#澳超",
    "欧冠": "#欧冠", "欧联": "#欧联", "中超": "#中超", "世界杯": "#世界杯",
    "欧洲杯": "#欧洲杯", "亚冠": "#亚冠",
}
FIXED_TAGS = ["#赛事前瞻", "#足球分析"]
BANNED = ["投注", "下注", "串关", "跟单", "稳赚", "包中", "必胜"]

DATA_LINE = (
    "数据来源：公开赛事数据 · 官方赛程 · 联赛积分与主客场进失球"
    "（数据截至发布时；90 分钟口径，加时与点球不计）。"
)
DISCLAIMER_LINE = (
    "免责声明：本文为个人观察与公开数据整理，仅供交流参考，"
    "不构成任何购买或投资建议；赛事结果存在不确定性，请理性看待比赛，量力而行。"
)

TAIL_PATTERNS = re.compile(r"^(话题标签|标签|数据来源|免责声明|免责说明|免责)\s*[:：]")


def guess_tags(text: str, path: Path) -> tuple[list[str], str]:
    """按正文与文件名里的联赛关键词猜标签；返回 (标签列表, 说明)。"""
    hay = f"{path.name}\n{text}"
    hit: list[str] = []
    for kw, tag in LEAGUE_TAGS.items():
        if kw in hay and tag not in hit:
            hit.append(tag)
    teams = re.findall(r"话题标签：[^\n]*", text)
    if teams:
        for t in re.findall(r"#[^\s#]+", teams[0]):
            if t not in hit and t not in FIXED_TAGS:
                hit.append(t)
    tags = hit[:4] + FIXED_TAGS
    note = "按关键词猜" if hit else "没猜出联赛，只给固定标签"
    return tags, note


def split_tail(lines: list[str]) -> tuple[list[str], list[str]]:
    """把文件末尾的尾块行切出来，返回 (正文行, 尾块行)。

    从最后一行往前扫：空行与以「话题标签/数据来源/免责…」开头的行都算尾块，
    遇到第一行正文就停。
    """
    i = len(lines) - 1
    while i >= 0 and (lines[i].strip() == "" or TAIL_PATTERNS.match(lines[i].strip())):
        i -= 1
    body = [ln for ln in lines[: i + 1]]
    while body and not body[-1].strip():
        body.pop()
    tail: list[str] = []
    for ln in lines[i + 1 :]:
        if not ln.strip():
            continue
        if ln.startswith("数据来源") and "免责" in ln:
            idx = ln.find("免责")
            tail.append(ln[:idx].strip())
            tail.append(ln[idx:].strip())
        else:
            tail.append(ln.strip())
    return body, tail


def build_tail(tags: list[str]) -> list[str]:
    tag_line = "话题标签：" + " ".join(dict.fromkeys(tags))
    return [tag_line, "", DATA_LINE, "", DISCLAIMER_LINE]


def main() -> None:
    ap = argparse.ArgumentParser(description="补齐文章固定尾块（话题标签/数据来源/免责）")
    ap.add_argument("file")
    ap.add_argument("--tags", default="", help="逗号分隔的标签，如 #日职,#韩职")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    p = Path(a.file)
    if not p.exists():
        raise SystemExit(f"找不到文件：{p}")
    raw = io.open(p, encoding="utf-8").read()
    lines = raw.splitlines()

    body, old_tail = split_tail(lines)
    if a.tags.strip():
        tags = [t.strip() if t.strip().startswith("#") else "#" + t.strip()
                for t in a.tags.split(",") if t.strip()]
        note = "命令行指定"
    else:
        tags, note = guess_tags(raw, p)
        for t in FIXED_TAGS:  # 固定标签始终在
            if t not in tags:
                tags.append(t)

    new_tail = build_tail(tags)
    out = "\n".join(body + [""] + new_tail) + "\n"

    warn = [w for w in BANNED if any(w in ln for ln in new_tail)]
    changed = out != raw
    print(f"[尾块] {p.name}")
    print(f"  标签：{' '.join(tags)}（{note}）")
    print(f"  原尾块：{len(old_tail)} 行 → 新尾块：3 块固定格式")
    if warn:
        print(f"  ⚠ 禁词命中（需人工改）：{', '.join(sorted(set(warn)))}")
    print(f"  结果：{'内容已更新' if changed else '已规范，无需改动'}")
    if a.dry_run:
        print("  —— dry-run，未写盘")
        return
    if changed:
        io.open(p, "w", encoding="utf-8", newline="\n").write(out)


if __name__ == "__main__":
    main()
