# -*- coding: utf-8 -*-
"""HUD 装饰：数据面板、折线、迷你战术板、角标。"""
from __future__ import annotations

from PIL import ImageDraw

GREEN = (0, 240, 120)
CYAN = (34, 224, 224)
PANEL = (6, 18, 26, 190)


def panel(d: ImageDraw.ImageDraw, box, r: int = 14, edge=GREEN, width: int = 2) -> None:
    d.rounded_rectangle(box, radius=r, fill=PANEL, outline=(*edge, 210), width=width)
    x0, y0, x1, y1 = box
    d.rectangle((x0, y0 + 8, x0 + 4, y1 - 8), fill=(*edge, 235))


def corner(d: ImageDraw.ImageDraw, xy, size=18, color=GREEN, width=2) -> None:
    x, y = xy
    d.line((x, y, x + size, y), fill=(*color, 220), width=width)
    d.line((x, y, x, y + size), fill=(*color, 220), width=width)


def chart(d: ImageDraw.ImageDraw, box, points, color=GREEN) -> None:
    x0, y0, x1, y1 = box
    d.line((x0, y1, x1, y1), fill=(*color, 90), width=1)
    d.line((x0, y0, x0, y1), fill=(*color, 90), width=1)
    step = (x1 - x0) / max(1, len(points) - 1)
    xy = [(x0 + i * step, y1 - v * (y1 - y0)) for i, v in enumerate(points)]
    d.line(xy, fill=(*color, 235), width=3, joint="curve")
    for px, py in xy:
        d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=(*color, 255))


def bars(d: ImageDraw.ImageDraw, box, vals, color=CYAN) -> None:
    x0, y0, x1, y1 = box
    n = len(vals)
    step = (x1 - x0) / n
    for i, v in enumerate(vals):
        bx0 = x0 + i * step + step * 0.18
        bx1 = bx0 + step * 0.55
        d.rectangle((bx0, y1 - v * (y1 - y0), bx1, y1), fill=(*color, 200))


def mini_pitch(d: ImageDraw.ImageDraw, box, color=GREEN) -> None:
    x0, y0, x1, y1 = box
    d.rectangle((x0, y0, x1, y1), outline=(*color, 200), width=2)
    my = (y0 + y1) // 2
    d.line((x0, my, x1, my), fill=(*color, 160), width=2)
    cx, cy = (x0 + x1) // 2, my
    rx, ry = (x1 - x0) // 8, (y1 - y0) // 10
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=(*color, 160), width=2)
    for k in ((0.18, 0.30), (0.82, 0.30), (0.18, 0.70), (0.82, 0.70), (0.5, 0.5)):
        px, py = x0 + (x1 - x0) * k[0], y0 + (y1 - y0) * k[1]
        d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(*CYAN, 235))


def ticks(d: ImageDraw.ImageDraw, box, n=8, color=GREEN) -> None:
    x0, y0, x1, _ = box
    step = (x1 - x0) / (n - 1)
    for i in range(n):
        x = x0 + i * step
        d.line((x, y0, x, y0 + (10 if i % 2 == 0 else 6)), fill=(*color, 170), width=2)
