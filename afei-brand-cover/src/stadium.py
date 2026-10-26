# -*- coding: utf-8 -*-
"""背景与足球：加载球场底图、压暗与暗角、全息足球。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def load_bg(path: Path, size: tuple[int, int]) -> Image.Image:
    if path.exists():
        im = Image.open(path).convert("RGB")
        # 等比铺满（cover）
        sw, sh = size
        r = max(sw / im.width, sh / im.height)
        im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
        left = (im.width - sw) // 2
        top = (im.height - sh) // 2
        im = im.crop((left, top, left + sw, top + sh))
    else:
        im = Image.new("RGB", size, (5, 11, 18))
    return im.convert("RGBA")


def shade(im: Image.Image, top=(0, 0, 0), top_a=225, mid_a=40, bot_a=245) -> Image.Image:
    w, h = im.size
    grad = Image.new("L", (1, h))
    px = grad.load()
    for y in range(h):
        t = y / max(1, h - 1)
        if t < 0.34:
            a = top_a - (top_a - mid_a) * (t / 0.34)
        else:
            a = mid_a + (bot_a - mid_a) * ((t - 0.34) / 0.66)
        px[0, y] = int(max(0, min(255, a)))
    mask = grad.resize((w, h))
    layer = Image.new("RGBA", (w, h), (*top, 255))
    layer.putalpha(mask)
    return Image.alpha_composite(im, layer)


def vignette(im: Image.Image, strength: float = 0.55) -> Image.Image:
    w, h = im.size
    v = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(v)
    d.ellipse((-w * 0.25, -h * 0.25, w * 1.25, h * 1.25), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(min(w, h) // 8))
    inv = v.point(lambda p: int((255 - p) * strength))
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    layer.putalpha(inv)
    return Image.alpha_composite(im, layer)


def ball(im: Image.Image, center: tuple[int, int], r: int, green=(0, 240, 120)) -> Image.Image:
    """深色球体 + 荧光绿缝线 + 外发光。"""
    cx, cy = center
    size = r * 4
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = size // 2

    # 外发光
    halo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse((c - r, c - r, c + r, c + r), fill=(*green, 70))
    layer.alpha_composite(halo.filter(ImageFilter.GaussianBlur(r // 3)))

    # 球体
    d.ellipse((c - r, c - r, c + r, c + r), fill=(16, 26, 30, 255), outline=(*green, 120), width=2)

    # 球面明暗：左上高光 + 右下暗部
    shade_l = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade_l)
    for i in range(26, 0, -1):
        rx = r * (i / 26) * 0.92
        a = int(10 * (1 - i / 26) + 3)
        sd.ellipse((c - r * 0.30 - rx, c - r * 0.34 - rx, c - r * 0.30 + rx, c - r * 0.34 + rx),
                   fill=(190, 225, 215, a))
    shade_l = shade_l.filter(ImageFilter.GaussianBlur(r // 6))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((c - r, c - r, c + r, c + r), fill=255)
    layer.paste(shade_l, (0, 0), Image.composite(mask, Image.new("L", (size, size), 0), shade_l.split()[3]))

    dark_l = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dark_l)
    for i in range(18, 0, -1):
        rx = r * (i / 18) * 0.95
        dd.ellipse((c + r * 0.34 - rx, c + r * 0.38 - rx, c + r * 0.34 + rx, c + r * 0.38 + rx),
                   fill=(0, 0, 0, 14))
    layer.alpha_composite(dark_l.filter(ImageFilter.GaussianBlur(r // 5)), (0, 0))

    # 缝线：中心六边形 + 放射线
    import math

    hexp = [(c + r * 0.42 * math.cos(math.radians(60 * i - 90)),
             c + r * 0.42 * math.sin(math.radians(60 * i - 90))) for i in range(6)]
    d.polygon(hexp, outline=(*green, 230), width=3)
    for i in range(6):
        x, y = hexp[i]
        ang = math.radians(60 * i - 90)
        x2, y2 = c + r * 0.95 * math.cos(ang), c + r * 0.95 * math.sin(ang)
        d.line((x, y, x2, y2), fill=(*green, 150), width=2)
    d.arc((c - r * 0.62, c - r * 0.62, c + r * 0.62, c + r * 0.62), 200, 340,
          fill=(*green, 180), width=3)

    im.alpha_composite(layer, (cx - c, cy - c))
    return im
