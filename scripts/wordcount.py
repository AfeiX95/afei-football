# -*- coding: utf-8 -*-
"""
阿飞说球 — 文章正文字数核对（R32：800–1500 字）

统计「正文净字数」，排除运营块与格式噪音：
  排除：H1 标题行、`> 标签` 行、`<details>…</details>` 配图段落、
        免责/数据来源模板、Markdown 表格分隔行、纯符号行
  计入：中文/西文/数字正文（合并计数，中文按字、西文按词近似）

用法：
    python scripts/wordcount.py                      # 自动找 📝文章/ 下最新的 md
    python scripts/wordcount.py <文件路径>            # 指定文件
    python scripts/wordcount.py <文件路径> --detail   # 显示分段统计
"""
import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

# 目标区间（R32）
RANGES = {
    "单场前瞻": (800, 1500),
    "双场合集": (800, 1500),
    "多场合集": (800, 1500),
}

EXCLUDE_PATTERNS = [
    r"^#\s",                      # H1 标题
    r"^>\s*标签[:：]",            # 标签行
    r"^数据来源[:：]",            # 数据来源模板
    r"^注[:：]本文基于",          # 免责模板
    r"^---\s*$",                  # 分隔线
    r"^[\s|:\-]+$",               # 表格分隔行/纯符号行
]


def clean_lines(text: str):
    """返回 (正文行列表, 被排除行数)"""
    # 去掉 details 配图段
    text = re.sub(r"(?s)<details>.*?</details>", "", text)
    kept, dropped = [], 0
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if any(re.match(p, s) for p in EXCLUDE_PATTERNS):
            dropped += 1
            continue
        kept.append(s)
    return kept, dropped


def count_chars(lines):
    """正文净字数：中文字符逐字计数，西文/数字按词计数"""
    text = "\n".join(lines)
    text = re.sub(r"\|", " ", text)          # 表格竖线当空格
    text = re.sub(r"\*\*|\*|`|#", "", text)   # 去格式符
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9]+", text))
    return cjk, words, cjk + words


def find_latest_article():
    base = ROOT / "📝文章"
    if not base.exists():
        return None
    files = sorted(base.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main():
    ap = argparse.ArgumentParser(description="文章正文字数核对（R32）")
    ap.add_argument("path", nargs="?", help="md 文件路径；省略则取最新文章")
    ap.add_argument("--detail", action="store_true", help="显示分段统计")
    args = ap.parse_args()

    path = Path(args.path) if args.path else find_latest_article()
    if not path or not path.exists():
        print("[ERR] 未找到文章文件")
        return 1

    raw = path.read_text(encoding="utf-8")
    lines, dropped = clean_lines(raw)
    cjk, words, total = count_chars(lines)

    # 结构指标
    headings = len([l for l in lines if l.startswith("#")])
    tables = len([l for l in lines if l.startswith("|")])
    quotes = len([l for l in lines if l.startswith(">")])
    bold_lines = len([l for l in lines if l.startswith("**")])
    paras = len(lines)

    print(f"[文章] {path.name}")
    print(f"[正文净字数] {total}  （中文字 {cjk} + 西文词 {words}）")
    print(f"[排除行数] {dropped}（标题/标签/配图/免责/格式行）")
    if args.detail:
        print(f"[结构] 小标题 {headings} ｜ 表格行 {tables} ｜ 引用块 {quotes} ｜ 加粗行 {bold_lines} ｜ 有效行 {paras}")
    print()
    print("[R32 目标区间]")
    for label, (lo, hi) in RANGES.items():
        flag = "← 落在区间" if lo <= total <= hi else ""
        print(f"  {label}: {lo}-{hi} 字 {flag}")
    if total < 800:
        print(f"\n⚠️ 低于下限，建议补 ①战意细节 ②市场定价对比 ③风险提示")
    elif total > 1500:
        print(f"\n⚠️ 超过上限，建议删 ①重复铺垫 ②形容词堆砌 ③无关数据罗列")
    return 0


if __name__ == "__main__":
    sys.exit(main())
