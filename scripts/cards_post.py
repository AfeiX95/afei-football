#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""小红书卡片「发布版」批处理（PhotoCraft 无头，2026-10-16 接入管线）。

为什么有这一步：`xhs_html.py` 出的是 2160×2880 的 PNG（封面约 360 KB，每场约 520–610 KB），
上传后平台还会再压一遍；先本地转成 WebP（质量 82）体积大约只剩一半，肉眼几乎看不出差别。
实测（2026-10-16 周五八场封面）：PNG 368 KB → WebP 161,804 字节（−56%）。

两种用法
  1) 逐张转换（默认，不需要任何 actions 文件）
     python scripts/cards_post.py "📝文章/20261016/小红书_周五八场"
     → <批次目录>/发布版/*.webp
  2) 统一动作（PhotoCraft 的 actions JSON，用来统一色调 / 加水印 / 裁边；Photoshop 的 .atn 也认）
     python scripts/cards_post.py <批次目录> --actions 动作.json --action 动作名
     → 走 `photocraft-cli batch --actions …`，输出同样落在 --out

参数：--out 目录（默认 <批次>/发布版）· --format webp|jpg|png · --quality 1-100 ·
      --actions 文件 · --action 名称 · --dry-run · --cli 路径
找 CLI 的顺序：--cli → 环境变量 PHOTOCRAFT_CLI → C:\\Program Files\\PhotoCraft\\photocraft-cli.exe → PATH

注意：文件名里的中文会原样保留（输出名 = 原名 + 新扩展名），小红书按文件名排序上传即对。
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLI = r"C:\Program Files\PhotoCraft\photocraft-cli.exe"


def find_cli(explicit: str = "") -> str:
    if explicit:
        return explicit
    env = os.environ.get("PHOTOCRAFT_CLI", "").strip()
    if env:
        return env
    if Path(DEFAULT_CLI).exists():
        return DEFAULT_CLI
    return "photocraft-cli"


def collect(paths, want_suffixes=(".png",)) -> list:
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += sorted(q for q in p.iterdir() if q.suffix.lower() in want_suffixes)
        elif p.exists() and p.suffix.lower() in want_suffixes:
            files.append(p)
    return files


def kb(n: int) -> str:
    return "%.0f KB" % (n / 1024.0)


def main() -> int:
    ap = argparse.ArgumentParser(description="小红书卡片发布版批处理（PhotoCraft）")
    ap.add_argument("paths", nargs="*", help="批次目录（或若干 PNG）；默认最近一个 📝文章/*/小红书* 目录")
    ap.add_argument("--out", default="", help="输出目录（默认 <批次>/发布版）")
    ap.add_argument("--format", default="webp", choices=["webp", "jpg", "png"], help="输出格式（默认 webp）")
    ap.add_argument("--quality", type=int, default=82, help="JPEG/WebP 质量 1-100（默认 82）")
    ap.add_argument("--actions", default="", help="PhotoCraft actions JSON / .atn：给了就走整目录统一动作")
    ap.add_argument("--action", default="", help="actions 文件里的动作名（多于一个时必须给）")
    ap.add_argument("--cli", default="", help="photocraft-cli 路径（默认自动找）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将执行的命令")
    a = ap.parse_args()

    paths = a.paths
    if not paths:
        cands = sorted(ROOT.glob("📝文章/*/小红书*"), reverse=True)
        if not cands:
            print("❌ 没给目录，也没找到 📝文章/*/小红书*")
            return 1
        paths = [cands[0]]
        print("（未指定目录，用最近一批：%s）" % paths[0])

    files = collect(paths)
    if not files:
        print("❌ %s 里没有 PNG" % paths)
        return 1

    first = Path(paths[0]) if Path(paths[0]).is_dir() else files[0].parent
    out_dir = Path(a.out) if a.out else first / "发布版"
    out_dir.mkdir(parents=True, exist_ok=True)
    cli = find_cli(a.cli)
    print("PhotoCraft：%s" % cli)
    print("输入 %d 张 → 输出 %s（%s 质量 %d）" % (len(files), out_dir, a.format, a.quality))

    # 整目录统一动作（batch 需要 --actions）
    if a.actions:
        cmd = [cli, "batch", "--actions", a.actions]
        if a.action:
            cmd += ["--action", a.action]
        cmd += ["--in", str(first), "--out", str(out_dir), "--format", a.format, "--quality", str(a.quality)]
        print("  $ " + " ".join('"%s"' % c if " " in c else c for c in cmd))
        if a.dry_run:
            return 0
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        sys.stdout.write(r.stdout or "")
        sys.stderr.write(r.stderr or "")
        made = sorted(out_dir.glob("*." + a.format))
        print("✅ 统一动作完成，产出 %d 张 → %s" % (len(made), out_dir))
        return 0 if r.returncode == 0 else 1

    before = after = 0
    fails = []
    for src in files:
        dst = out_dir / (src.stem + "." + a.format)
        cmd = [cli, "convert", str(src), str(dst), "--format", a.format, "--quality", str(a.quality)]
        if a.dry_run:
            print("  $ " + " ".join('"%s"' % c if " " in c else c for c in cmd))
            continue
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0 or not dst.exists():
            fails.append((src.name, (r.stderr or r.stdout or "").strip()[:120]))
            print("  ❌ %s  %s" % (src.name, fails[-1][1]))
            continue
        b, n = src.stat().st_size, dst.stat().st_size
        before += b
        after += n
        print("  ✅ %-38s %8s → %8s  (%+d%%)" % (src.name, kb(b), kb(n), round((n - b) * 100.0 / b)))
    if a.dry_run:
        return 0

    if before:
        print("合计：%s → %s，省 %d%%（%d 张 → %s）"
              % (kb(before), kb(after), round((before - after) * 100.0 / before), len(files) - len(fails), out_dir))
    if fails:
        print("❌ %d 张失败" % len(fails))
        return 1
    print("✅ 发布版就绪：%s" % out_dir)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
