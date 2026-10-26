# -*- coding: utf-8 -*-
"""竖版 3:4 固定品牌封面（1536×2048）。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from . import hud
from .stadium import ball, load_bg, shade, vignette
from .typography import glow_text, load_font, skew_text, text_w


def render(theme: dict, bg_path: Path, out_path: Path) -> Path:
    c = theme["colors"]
    f = theme["fonts"]
    cfg = theme["portrait"]
    W, H = cfg["w"], cfg["h"]
    brand = theme["brand"]

    im = load_bg(bg_path, (W, H))
    im = shade(im, top_a=232, mid_a=30, bot_a=246)
    im = vignette(im, 0.5)

    d = ImageDraw.Draw(im)
    green = tuple(c["green"])
    white = tuple(c["white"])
    muted = tuple(c["muted"])

    # ---- 品牌 ----
    d.rectangle((100, 118, 114, 268), fill=(*green, 255))
    glow_text(im, (152, 116), brand["name"], load_font(f["bold"], cfg["brand"]), white, glow=10, anchor="la")
    d.text((152, 214), brand["sub"], font=load_font(f["bold"], cfg["brand_sub"]), fill=(*muted, 255), anchor="la")

    # ---- 口号（右上，右对齐）----
    qf = load_font(f["regular"], 34)
    d.text((W - 104, 132), brand["quote1"], font=qf, fill=(*white, 235), anchor="ra")
    d.text((W - 104, 184), brand["quote2"], font=qf, fill=(*white, 235), anchor="ra")
    d.text((W - 104, 238), brand["sign"], font=load_font(f["regular"], 28), fill=(*muted, 235), anchor="ra")

    # ---- 主标题 ----
    t1 = load_font(f["bold"], cfg["title"])
    skew_text(im, (104, 600), brand["title1"], t1, white, glow=theme["glow"]["title"], anchor="ls")
    skew_text(im, (150, 890), brand["title2"], t1, green, glow=theme["glow"]["title"] + 10, anchor="ls")

    # ---- 标签行 ----
    tf = load_font(f["bold"], cfg["tags"])
    x = 108
    for i, tag in enumerate(brand["tags"]):
        if i:
            d.text((x, 1030), "/", font=tf, fill=(*green, 220), anchor="la")
            x += text_w(d, "/", tf) + 18
        d.text((x, 1030), tag, font=tf, fill=(*white, 240), anchor="la")
        x += text_w(d, tag, tf) + 18

    # ---- HUD ----
    hud.panel(d, (92, 1150, 486, 1490), r=16)
    d.text((118, 1170), "MATCH ANALYSIS", font=load_font(f["mono"], 22), fill=(*green, 235), anchor="la")
    hud.chart(d, (118, 1228, 460, 1374), [0.35, 0.55, 0.42, 0.70, 0.60, 0.82, 0.66, 0.9])
    hud.ticks(d, (118, 1392, 460, 1418), n=9)
    for i, lab in enumerate(["ODDS", "FORM", "TACTICS", "INJURY"]):
        d.text((118 + i * 88, 1428), lab, font=load_font(f["mono"], 19), fill=(*muted, 235), anchor="la")

    hud.panel(d, (1058, 1116, 1444, 1448), r=16)
    d.text((1082, 1136), "TACTICAL", font=load_font(f["mono"], 22), fill=(*green, 235), anchor="la")
    hud.mini_pitch(d, (1090, 1182, 1412, 1368))
    hud.bars(d, (1090, 1388, 1412, 1428), [0.4, 0.7, 0.5, 0.9, 0.6, 0.8], color=tuple(c["cyan"]))

    # ---- 足球 ----
    im = ball(im, (W // 2, 1430), 196)
    d = ImageDraw.Draw(im)

    # ---- 底部三栏目 ----
    hud.panel(d, (96, 1700, W - 96, 1892), r=18)
    icons = ("cal", "target", "chart")
    slot = (W - 192) // 3
    for i, (t, s) in enumerate(brand["features"]):
        cx = 96 + slot * i + 44
        cy = 1772
        _icon(d, icons[i], cx, cy, 46, green)
        d.text((cx + 74, cy - 4), t, font=load_font(f["bold"], cfg["feat"]), fill=(*white, 255), anchor="la")
        d.text((cx + 74, cy + 52), s, font=load_font(f["regular"], cfg["feat_sub"]), fill=(*muted, 240), anchor="la")
        if i < 2:
            d.line((96 + slot * (i + 1), 1740, 96 + slot * (i + 1), 1856), fill=(*green, 70), width=2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(out_path, "PNG")
    return out_path


def _icon(d: ImageDraw.ImageDraw, kind: str, x: int, y: int, size: int, color) -> None:
    col = (*color, 255)
    w = 3
    if kind == "cal":
        d.rounded_rectangle((x, y, x + size, y + size), radius=10, outline=col, width=w)
        d.line((x, y + size * 0.34, x + size, y + size * 0.34), fill=col, width=w)
        d.line((x + size * 0.28, y - 6, x + size * 0.28, y + 8), fill=col, width=w)
        d.line((x + size * 0.72, y - 6, x + size * 0.72, y + 8), fill=col, width=w)
    elif kind == "target":
        d.ellipse((x, y, x + size, y + size), outline=col, width=w)
        d.ellipse((x + size * 0.3, y + size * 0.3, x + size * 0.7, y + size * 0.7), outline=col, width=w)
        d.line((x + size * 0.5, y - 6, x + size * 0.5, y + size * 0.16), fill=col, width=w)
    else:
        d.line((x, y + size, x, y + size * 0.2), fill=col, width=w)
        d.line((x + size * 0.5, y + size, x + size * 0.5, y), fill=col, width=w)
        d.line((x + size, y + size, x + size, y + size * 0.45), fill=col, width=w)
        d.line((x - 4, y + size, x + size + 4, y + size), fill=col, width=w)
