#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把一批小红书卡图装成一份多页 PDF（2026-10-16 接入管线）。

用途：存档 / 打印 / 合订成册 / 发给不刷小红书的人。九张卡 → 一份 9 页 PDF，
顺序＝文件名序号（`01_封面.png` 在最前，与小红书上传顺序一致）。

两种引擎
  pdfcraft（默认，实测）：先 `pdfcraft-cli batch <png…> --steps convert --out-dir <临时>` 逐张转 PDF，
                          再 `pdfcraft-cli combine <pdf…> --out 合集.pdf` 合并；
                          `--title/--author` 走 `pdfcraft-cli edit` 写文档属性。
  pil（兜底，零外部依赖）：用 bundled Pillow 把 PNG 依次写进同一个 PDF（体积略大，任何机器都能跑）。

用法
  python scripts/cards_pdf.py "📝文章/20261016/小红书_周五八场"
  → <批次目录>/卡片合集.pdf
  python scripts/cards_pdf.py <批次目录> --title "10/16 八场数据：主客场差在哪" --author "@阿飞·赛博聊球"
  python scripts/cards_pdf.py <批次目录> --engine pil        # 不依赖 PdfCraft

参数：--out 文件 · --engine pdfcraft|pil · --title T · --author A · --dry-run · --cli 路径
找 CLI 顺序：--cli → 环境变量 PDFCRAFT_CLI → C:\\Program Files\\PdfCraft\\pdfcraft-cli.exe → PATH
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLI = r"C:\Program Files\PdfCraft\pdfcraft-cli.exe"


def find_cli(explicit: str = "") -> str:
    if explicit:
        return explicit
    env = os.environ.get("PDFCRAFT_CLI", "").strip()
    if env:
        return env
    if Path(DEFAULT_CLI).exists():
        return DEFAULT_CLI
    return "pdfcraft-cli"


def collect_png(paths) -> list:
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += sorted(q for q in p.iterdir() if q.suffix.lower() in (".png", ".jpg", ".jpeg"))
        elif p.exists() and p.suffix.lower() in (".png", ".jpg", ".jpeg"):
            files.append(p)
    return files


def run(cmd: list, dry: bool) -> subprocess.CompletedProcess:
    pretty = " ".join('"%s"' % c if " " in c else c for c in cmd)
    if dry:
        print("  $ " + pretty)
        return subprocess.CompletedProcess(cmd, 0, "", "")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("  ❌ " + pretty)
        print("     " + ((r.stderr or r.stdout or "").strip()[:300]))
    return r


def pdf_pages(cli: str, pdf: Path):
    """返回页数（PdfCraft info 的 JSON 摘要）；拿不到就 None。"""
    try:
        r = subprocess.run([cli, "info", str(pdf)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout)
        for k in ("pages", "page_count", "num_pages"):
            if isinstance(data.get(k), int):
                return data[k]
        for v in data.values():
            if isinstance(v, dict):
                for k in ("pages", "page_count"):
                    if isinstance(v.get(k), int):
                        return v[k]
    except Exception:
        return None
    return None


def build_with_pdfcraft(cli: str, pngs: list, out: Path, title: str, author: str, dry: bool) -> bool:
    tmp = Path(tempfile.mkdtemp(prefix="cards_pdf_"))
    try:
        batch = [cli, "batch"] + [str(p) for p in pngs] + ["--steps", "convert", "--out-dir", str(tmp)]
        if run(batch, dry).returncode != 0:
            return False
        if dry:
            print("  （dry-run：跳过 combine/edit/info）")
            return True
        # batch 输出文件名 = 各输入 stem；按原始顺序重排，保证封面在第一页
        pdfs = []
        for p in pngs:
            cand = tmp / (p.stem + ".pdf")
            if not cand.exists():
                print("  ❌ 没等到 %s" % cand.name)
                return False
            pdfs.append(cand)
        tmp_out = tmp / "combined.pdf"
        if run([cli, "combine"] + [str(p) for p in pdfs] + ["--out", str(tmp_out)], dry).returncode != 0:
            return False
        if title or author:
            edited = tmp / "edited.pdf"
            cmd = [cli, "edit", str(tmp_out), "--out", str(edited)]
            if title:
                cmd += ["--title", title]
            if author:
                cmd += ["--author", author]
            if run(cmd, dry).returncode == 0 and edited.exists():
                tmp_out = edited
        shutil.move(str(tmp_out), str(out))
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build_with_pil(pngs: list, out: Path) -> bool:
    try:
        from PIL import Image
    except Exception as e:  # 兜底引擎要靠 bundled Pillow
        print("  ❌ 没有 Pillow：%s" % e)
        return False
    pages = []
    try:
        for p in pngs:
            im = Image.open(p)
            pages.append(im.convert("RGB"))
        pages[0].save(out, "PDF", save_all=True, append_images=pages[1:], resolution=200.0)
        return True
    except Exception as e:
        print("  ❌ Pillow 装订失败：%s" % e)
        return False
    finally:
        for im in pages:
            try:
                im.close()
            except Exception:
                pass


def main() -> int:
    ap = argparse.ArgumentParser(description="把一批小红书卡图装成多页 PDF")
    ap.add_argument("paths", nargs="*", help="批次目录（或若干图片）；默认最近一个 📝文章/*/小红书* 目录")
    ap.add_argument("--out", default="", help="输出 PDF（默认 <批次>/卡片合集.pdf）")
    ap.add_argument("--engine", default="pdfcraft", choices=["pdfcraft", "pil"], help="装订引擎（默认 pdfcraft）")
    ap.add_argument("--title", default="", help="PDF 标题（写在文档属性里）")
    ap.add_argument("--author", default="", help="PDF 作者")
    ap.add_argument("--cli", default="", help="pdfcraft-cli 路径（默认自动找）")
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

    pngs = collect_png(paths)
    if not pngs:
        print("❌ %s 里没有 PNG/JPG" % paths)
        return 1
    first = Path(paths[0]) if Path(paths[0]).is_dir() else pngs[0].parent
    out = Path(a.out) if a.out else first / "卡片合集.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    # 标题/作者没给就从同目录的 cards.json 取（xhs_title / brand），省得每次手打
    if not a.title or not a.author:
        cj = first / "cards.json"
        if cj.exists():
            try:
                meta = json.loads(cj.read_text(encoding="utf-8"))
                if not a.title:
                    # 优先用带日期的 caption_title（归档 PDF 里日期有意义），其次封面标题
                    a.title = str(meta.get("caption_title") or meta.get("xhs_title") or meta.get("title") or "").strip()
                if not a.author:
                    a.author = str(meta.get("brand") or "").strip()
            except Exception as e:
                print("  ⚠️ cards.json 读不出来（%s），标题/作者留空" % e)

    print("装订 %d 张 → %s（引擎 %s）" % (len(pngs), out, a.engine))
    if a.title or a.author:
        print("   文档属性：%s%s" % (a.title, (" ／ " + a.author) if a.author else ""))
    for p in pngs:
        print("   · %s" % p.name)

    engine = a.engine
    cli = find_cli(a.cli)
    if engine == "pdfcraft":
        print("PdfCraft：%s" % cli)
        if not shutil.which(cli) and not Path(cli).exists():
            print("  ⚠️ 找不到 pdfcraft-cli → 退回 pil 引擎")
            engine = "pil"
    if engine == "pdfcraft":
        ok = build_with_pdfcraft(cli, pngs, out, a.title, a.author, a.dry_run)
    else:
        ok = build_with_pil(pngs, out)
    if a.dry_run:
        return 0
    if not ok or not out.exists():
        print("❌ 没出 PDF")
        return 1
    pages = pdf_pages(cli, out) if engine == "pdfcraft" else len(pngs)
    print("✅ %s（%s，%s 页）" % (out, "%.2f MB" % (out.stat().st_size / 1048576.0),
                                 pages if pages is not None else "?"))
    if pages is not None and pages != len(pngs):
        print("⚠️ 页数 %s 与图片数 %d 不一致，检查一下" % (pages, len(pngs)))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
