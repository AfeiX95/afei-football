# -*- coding: utf-8 -*-
"""文字与光效：粗体/常规/等宽字体、发光、斜切。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def load_font(path: str | Path, size: int) -> ImageFont.FreeTypeFont:
    key = (str(path), size)
    if key not in _CACHE:
        try:
            _CACHE[key] = ImageFont.truetype(str(path), size)
        except OSError:
            _CACHE[key] = ImageFont.load_default()
    return _CACHE[key]


def text_w(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return int(box[2] - box[0])


def glow_text(
    base: Image.Image,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    color: tuple[int, int, int],
    glow: int = 18,
    glow_color: tuple[int, int, int] | None = None,
    anchor: str = "ls",
) -> Image.Image:
    """先画发光层（模糊）再叠清晰文字。anchor 同 Pillow（默认左下基线）。"""
    gc = glow_color or color
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, text, font=font, fill=(*gc, 255), anchor=anchor)
    blurred = layer.filter(ImageFilter.GaussianBlur(glow))
    base.alpha_composite(blurred)
    base.alpha_composite(blurred)
    sharp = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sharp).text(xy, text, font=font, fill=(*color, 255), anchor=anchor)
    base.alpha_composite(sharp)
    return base


def skew_text(base: Image.Image, xy, text: str, font, color, glow=18, shear=-0.12, anchor="ls"):
    """斜切标题：先画到透明层，再做水平剪切，最后贴回。"""
    tmp = Image.new("RGBA", base.size, (0, 0, 0, 0))
    glow_text(tmp, xy, text, font, color, glow=glow, anchor=anchor)
    x0, y0, x1, y1 = tmp.getbbox() or (0, 0, 1, 1)
    crop = tmp.crop((x0, y0, x1, y1))
    w, h = crop.size
    pad = int(h * 0.35)
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    canvas.alpha_composite(crop, (pad, pad))
    # 水平剪切：x' = x + shear * (y - h/2)
    sheared = canvas.transform(
        canvas.size,
        Image.AFFINE,
        (1, shear, -shear * canvas.size[1] / 2, 0, 1, 0),
        resample=Image.BICUBIC,
    )
    base.alpha_composite(sheared, (x0 - pad, y0 - pad))
    return base
