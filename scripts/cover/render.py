# -*- coding: utf-8 -*-
"""渲染：HTML → PNG（headless Chrome）。文字全部由浏览器排版，中文零错字风险。"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

CHROME = os.environ.get("CHROME") or r"C:\Program Files\Google\Chrome\Application\chrome.exe"

RATIO_SIZE = {"3:4": (1080, 1440), "16:9": (1920, 1080)}


def render_html(html: str, out_png: Path, ratio: str = "3:4", scale: int = 2,
                tmp_dir: Path | None = None) -> Path:
    w, h = RATIO_SIZE[ratio]
    out_png = out_png.resolve()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = (tmp_dir or out_png.parent).resolve()
    tmp_dir.mkdir(parents=True, exist_ok=True)
    html_path = tmp_dir / (out_png.stem + ".html")
    html_path.write_text(html, encoding="utf-8")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
           "--allow-file-access-from-files", "--virtual-time-budget=2500", "--force-device-scale-factor=%d" % scale,
           "--window-size=%d,%d" % (w, h), "--screenshot=%s" % out_png,
           html_path.as_uri()]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180, check=False)
    if not out_png.exists():
        raise RuntimeError("渲染失败：%s（检查 Chrome 路径与磁盘权限）" % out_png)
    return out_png


def thumbnail(png: Path, out: Path, box: tuple[int, int] = (360, 480)) -> Path | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(png)
    im.thumbnail(box, Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return out
