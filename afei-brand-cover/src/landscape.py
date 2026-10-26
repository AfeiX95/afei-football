# -*- coding: utf-8 -*-
"""横版 16:9 固定品牌封面（1920×1080），独立版面，不是竖版裁切。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from . import hud
from .portrait import _icon
from .stadium import ball, load_bg, shade, vignette
from .typography import glow_text, load_font, skew_text, text_w


def render(theme: dict, bg_path: Path, out_path: Path) -> Path:
    c = theme["colors"]
    f = theme["fonts"]
    cfg = theme["landscape"]
    W, H = cfg["w"], cfg["h"]
    brand = theme["brand"]

    im = load_bg(bg_path, (W, H))
    im = shade(im, top_a=214, mid_a=26, bot_a=240)
    im = vignette(im, 0.45)

    d = ImageDraw.Draw(im)
    green = tuple(c["green"])
    white = tuple(c["white"])
    muted = tuple(c["muted"])

    # ---- 品牌（左上）----
    d.rectangle((88, 74, 100, 176), fill=(*green, 255))
    glow_text(im, (128, 70), brand["name"], load_font(f["bold"], cfg["brand"]), white, glow=8, anchor="la")
    d.text((128, 150), brand["sub"], font=load_font(f["bold"], cfg["brand_sub"]), fill=(*muted, 255), anchor="la")

    # ---- 口号（右上）----
    qf = load_font(f["regular"], 30)
    d.text((W - 96, 84), brand["quote1"], font=qf, fill=(*white, 230), anchor="ra")
    d.text((W - 96, 130), brand["quote2"], font=qf, fill=(*white, 230), anchor="ra")
    d.text((W - 96, 178), brand["sign"], font=load_font(f["regular"], 26), fill=(*muted, 230), anchor="ra")

    # ---- 主标题（左）----
    t1 = load_font(f["bold"], cfg["title"])
    skew_text(im, (86, 470), brand["title1"], t1, white, glow=theme["glow"]["title"], anchor="ls")
    skew_text(im, (120, 690), brand["title2"], t1, green, glow=theme["glow"]["title"] + 8, anchor="ls")

    # ---- 标签行 ----
    tf = load_font(f["bold"], cfg["tags"])
    x = 92
    for i, tag in enumerate(brand["tags"]):
        if i:
            d.text((x, 762), "/", font=tf, fill=(*green, 220), anchor="la")
            x += text_w(d, "/", tf) + 14
        d.text((x, 762), tag, font=tf, fill=(*white, 240), anchor="la")
        x += text_w(d, tag, tf) + 14

    # ---- 右侧：全息足球 + 战术面板 ----
    hud.panel(d, (1508, 250, 1836, 556), r=14)
    d.text((1530, 268), "TACTICAL", font=load_font(f["mono"], 20), fill=(*green, 235), anchor="la")
    hud.mini_pitch(d, (1536, 310, 1810, 478))
    hud.bars(d, (1536, 494, 1810, 534), [0.4, 0.7, 0.5, 0.9, 0.6, 0.8], color=tuple(c["cyan"]))

    hud.panel(d, (1486, 576, 1840, 822), r=14)
    d.text((1508, 594), "MATCH ANALYSIS", font=load_font(f["mono"], 20), fill=(*green, 235), anchor="la")
    hud.chart(d, (1508, 636, 1816, 762), [0.3, 0.55, 0.4, 0.72, 0.58, 0.85, 0.7, 0.92])
    hud.ticks(d, (1508, 778, 1816, 804), n=9)

    im = ball(im, (1272, 660), 165)
    d = ImageDraw.Draw(im)

    # ---- 底部三栏目（横排，压在下缘）----
    hud.panel(d, (88, 862, W - 88, 1000), r=16)
    icons = ("cal", "target", "chart")
    slot = (W - 176) // 3
    for i, (t, s) in enumerate(brand["features"]):
        cx = 88 + slot * i + 40
        cy = 906
        _icon(d, icons[i], cx, cy, 38, green)
        d.text((cx + 62, cy - 6), t, font=load_font(f["bold"], cfg["feat"]), fill=(*white, 255), anchor="la")
        d.text((cx + 62, cy + 40), s, font=load_font(f["regular"], cfg["feat_sub"]), fill=(*muted, 240), anchor="la")
        if i < 2:
            d.line((88 + slot * (i + 1), 890, 88 + slot * (i + 1), 972), fill=(*green, 70), width=2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(out_path, "PNG")
    return out_path
