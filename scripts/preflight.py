#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""写文一键盘（Preflight）— 字数(R32) + 发布门禁，一条命令出结论。

用法：
    python scripts/preflight.py                       # 最新一篇文章
    python scripts/preflight.py <文章.md> [<文章2.md>]
    python scripts/preflight.py --detail <文章.md>     # 附门禁逐项
退出码：0 = 全部通过；1 = 有未过项。

替代「手动跑 wordcount.py + cd 到模型脚本跑 check_article.py」两次往返。
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
WORDCOUNT = ROOT / "scripts" / "wordcount.py"
GATE_DIR = ROOT / "📚知识库" / "模型脚本"
GATE = GATE_DIR / "check_article.py"
ARTICLES = ROOT / "📝文章"


def run(cmd, cwd=None):
    try:
        r = subprocess.run([sys.executable, *cmd], cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return f"[ERR] {e}"


def latest_article():
    if not ARTICLES.exists():
        return None
    files = sorted(ARTICLES.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def parse_words(out):
    m = re.search(r"\[正文净字数\]\s*(\d+)", out)
    total = int(m.group(1)) if m else None
    band = ""
    for line in out.splitlines():
        if "← 落在区间" in line:
            band = line.strip()
            break
    warn = ""
    for line in out.splitlines():
        if line.strip().startswith("⚠️"):
            warn = line.strip()
            break
    return total, band, warn


def parse_gate(out):
    items = []
    for line in out.splitlines():
        m = re.match(r"^([✅❌⚠️])\s*(\d+\.\s*[^:：]+)[:：]\s*(.*)$", line.strip())
        if m:
            items.append((m.group(1), m.group(2).strip(), m.group(3).strip()))
    passed = "结果: PASS" in out
    ai = None
    for mark, name, detail in items:
        if "AI" in name:
            am = re.search(r"([\d.]+)", detail)
            if am:
                ai = am.group(1)
    return passed, items, ai


def main():
    ap = argparse.ArgumentParser(description="写文一键盘：字数 + 发布门禁")
    ap.add_argument("paths", nargs="*", help="md 文件路径；省略则取最新文章")
    ap.add_argument("--detail", action="store_true", help="附门禁逐项明细")
    args = ap.parse_args()

    paths = [Path(p) for p in args.paths] if args.paths else [latest_article()]
    paths = [p for p in paths if p]
    if not paths:
        print("[ERR] 未找到文章文件")
        return 1
    if not GATE.exists():
        print(f"[ERR] 未找到门禁脚本 {GATE}")
        return 1

    W = 60
    print("=" * W)
    print("  写文一键盘 preflight（字数 R32 + 发布门禁）")
    print("=" * W)

    failed = 0
    for n, path in enumerate(paths, 1):
        if not path.exists():
            print(f"[{n}/{len(paths)}] ❌ 文件不存在: {path}")
            failed += 1
            continue
        abs_path = str(path.resolve())
        wout = run([str(WORDCOUNT), abs_path])
        gout = run([str(GATE), abs_path], cwd=GATE_DIR)
        total, band, warn = parse_words(wout)
        gate_pass, items, ai = parse_gate(gout)

        ok = bool(band) and gate_pass
        if not ok:
            failed += 1
        print(f"[{n}/{len(paths)}] {'✅' if ok else '❌'} {path.name}")
        print(f"    字数　{total if total is not None else '?'}　{band or '（未落在任何 R32 区间）'}")
        if warn:
            print(f"          {warn}")
        print(f"    门禁　{'PASS ✅' if gate_pass else 'FAIL ❌'}"
              f"（{sum(1 for m, _, _ in items if m == '✅')}/{len(items)} 项通过）"
              + (f"　AI {ai}" if ai else ""))
        bad = [f"{m} {n_}" for m, n_, _ in items if m != "✅"]
        for b in bad:
            print(f"          {b}")
        if args.detail:
            for m, n_, d in items:
                print(f"          {m} {n_}: {d}")
        print(f"    判定　{'✅ 可发布' if ok else '🔧 需修稿'}")
        print("-" * W)

    print(f"合计：{len(paths) - failed}/{len(paths)} 通过" + ("" if failed else "　→ 全部可发布 ✅"))
    print("=" * W)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
