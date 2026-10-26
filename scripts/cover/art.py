# -*- coding: utf-8 -*-
"""AFEI 封面系统 · 视觉资产（纯 SVG，零外部图片、零 AI 生图）。

提供三类资产：
  stadium_svg()   夜色球场（透视草皮 + 看台灯点 + 泛光灯）——模板 A 主视觉
  hud_frame()     四角 HUD 刻度与数据微面板——所有模板共用
  ball_svg()      全息线框足球——模板 A/B 的点睛元素
"""
from __future__ import annotations

from pathlib import Path

import math
import random

# ---------------- 配色（与 theme.json 保持同源） ----------------
GREEN = "#00F078"
CYAN = "#00D8D8"


def _dots(n: int, cx: float, cy: float, rx: float, ry: float, seed: int,
          inner: float = 0.55, rmin: float = 0.7, rmax: float = 1.8) -> str:
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        a = rnd.uniform(0, math.tau)
        rr = rnd.uniform(inner, 1.0)
        x, y = cx + math.cos(a) * rx * rr, cy + math.sin(a) * ry * rr
        r = rnd.uniform(rmin, rmax)
        op = rnd.uniform(0.18, 0.8)
        col = "#8FE9C6" if rnd.random() < 0.74 else "#A8CBFF"
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{col}" opacity="{op:.2f}"/>')
    return "".join(out)


def stadium_svg(vw: int = 1080, vh: int = 1440, far_y: float = 720, near_y: float = 1320,
                seed: int = 11, crop: tuple[float, float, float, float] | None = None) -> str:
    """夜色球场：远边窄、近边宽的透视草皮，后方椭圆形看台碗。

    crop=(x, y, w, h) 时只显示该区域（避免把整张 1080×1440 压扁）。
    """
    far_l, far_r = 312, 768
    near_l, near_r = 44, 1036
    mid_y = (far_y + near_y) / 2
    cx = vw / 2

    def y_at(f: float) -> float:
        return far_y + (near_y - far_y) * f

    def x_edge(f: float, left: bool) -> float:
        return (far_l + (near_l - far_l) * f) if left else (far_r + (near_r - far_r) * f)

    stripes = []
    for i in range(10):
        f0, f1 = i / 10, (i + 1) / 10
        y0, y1 = y_at(f0), y_at(f1)
        l0, r0, l1, r1 = x_edge(f0, True), x_edge(f0, False), x_edge(f1, True), x_edge(f1, False)
        col = "#0A3728" if i % 2 == 0 else "#0E4A34"
        stripes.append(f'<polygon points="{l0:.1f},{y0:.1f} {r0:.1f},{y0:.1f} '
                       f'{r1:.1f},{y1:.1f} {l1:.1f},{y1:.1f}" fill="{col}"/>')

    def box(fy0: float, fy1: float, inset: float) -> str:
        y0, y1 = y_at(fy0), y_at(fy1)
        l0, r0 = x_edge(fy0, True), x_edge(fy0, False)
        l1, r1 = x_edge(fy1, True), x_edge(fy1, False)
        w0, w1 = (r0 - l0) * inset, (r1 - l1) * inset
        return (f'<polygon points="{l0 + w0:.1f},{y0:.1f} {r0 - w0:.1f},{y0:.1f} '
                f'{r1 - w1:.1f},{y1:.1f} {l1 + w1:.1f},{y1:.1f}" fill="none" '
                f'stroke="rgba(236,255,247,.55)" stroke-width="2"/>')

    rx = (x_edge(0.5, False) - x_edge(0.5, True)) * 0.155
    ry = rx * 0.44

    def goal(f: float, wr: float, h: float) -> str:
        y = y_at(f)
        l, r = x_edge(f, True), x_edge(f, False)
        w = (r - l) * wr
        x0, x1 = (l + r) / 2 - w / 2, (l + r) / 2 + w / 2
        bars = "".join(
            f'<line x1="{x0 + (x1 - x0) * k / 8:.1f}" y1="{y:.1f}" x2="{x0 + (x1 - x0) * k / 8:.1f}" '
            f'y2="{y - h:.1f}" stroke="rgba(196,255,231,.26)" stroke-width="1"/>' for k in range(9))
        return (f'<g><line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" stroke="rgba(236,255,247,.8)" stroke-width="3"/>'
                f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x0:.1f}" y2="{y - h:.1f}" stroke="rgba(236,255,247,.7)" stroke-width="2"/>'
                f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y - h:.1f}" stroke="rgba(236,255,247,.7)" stroke-width="2"/>'
                f'<line x1="{x0:.1f}" y1="{y - h:.1f}" x2="{x1:.1f}" y2="{y - h:.1f}" stroke="rgba(236,255,247,.5)" stroke-width="2"/>'
                f'{bars}</g>')

    bowl_cy = far_y - 90
    vx, vy, cw, ch = crop if crop else (0, 0, vw, vh)
    return f"""<svg class="art" xmlns="http://www.w3.org/2000/svg" viewBox="{vx} {vy} {cw} {ch}" preserveAspectRatio="xMidYMid slice">
<defs>
  <radialGradient id="flood" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="#DDFFF2" stop-opacity=".9"/><stop offset=".5" stop-color="#4FF0B4" stop-opacity=".16"/>
    <stop offset="1" stop-color="#4FF0B4" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="pitchLit" cx=".5" cy=".58" r=".6">
    <stop offset="0" stop-color="#3BF7A4" stop-opacity=".34"/><stop offset=".5" stop-color="#0E7A4E" stop-opacity=".2"/>
    <stop offset="1" stop-color="#04121A" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="bowl" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0B1A24"/><stop offset="1" stop-color="#03090F"/>
  </linearGradient>
  <filter id="b18" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="18"/></filter>
  <radialGradient id="vig" cx=".5" cy=".5" r=".74">
    <stop offset=".5" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".9"/>
  </radialGradient>
</defs>

<ellipse cx="{cx}" cy="{bowl_cy}" rx="{near_r - near_l + 210}" ry="330" fill="url(#bowl)"/>
<ellipse cx="{cx}" cy="{bowl_cy + 26}" rx="{near_r - near_l + 160}" ry="286" fill="#040B10"/>
{_dots(760, cx, bowl_cy, (near_r - near_l) / 2 + 150, 268, seed)}
<ellipse cx="{cx}" cy="{bowl_cy}" rx="{near_r - near_l + 210}" ry="330" fill="none" stroke="rgba(94,244,192,.14)" stroke-width="2"/>

<g filter="url(#b18)">
  <ellipse cx="118" cy="{far_y - 300}" rx="170" ry="130" fill="url(#flood)" opacity=".8"/>
  <ellipse cx="{vw - 118}" cy="{far_y - 300}" rx="170" ry="130" fill="url(#flood)" opacity=".8"/>
  <ellipse cx="{cx}" cy="{far_y - 470}" rx="300" ry="150" fill="url(#flood)" opacity=".42"/>
</g>
<g opacity=".16" fill="url(#flood)">
  <polygon points="118,{far_y - 300} {far_l + 40},{far_y} {far_l + 220},{near_y} 60,{near_y}"/>
  <polygon points="{vw - 118},{far_y - 300} {far_r - 40},{far_y} {far_r - 220},{near_y} {vw - 60},{near_y}"/>
</g>

<g>{"".join(stripes)}</g>
<ellipse cx="{cx}" cy="{mid_y}" rx="500" ry="340" fill="url(#pitchLit)"/>
<g fill="none" stroke="rgba(240,255,248,.72)" stroke-width="2.6">
  <polygon points="{far_l},{far_y} {far_r},{far_y} {near_r},{near_y} {near_l},{near_y}"/>
  <line x1="{x_edge(0.5, True):.1f}" y1="{mid_y:.1f}" x2="{x_edge(0.5, False):.1f}" y2="{mid_y:.1f}"/>
  <ellipse cx="{cx}" cy="{mid_y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"/>
</g>
{box(0.0, 0.17, 0.20)}{box(0.83, 1.0, 0.20)}{box(0.0, 0.06, 0.35)}{box(0.94, 1.0, 0.35)}
{goal(0.0, 0.13, 32)}{goal(1.0, 0.19, 46)}
<rect width="{vw}" height="{vh}" fill="url(#vig)"/>
</svg>"""


def ball_svg(size: int = 240, cx: float | None = None, cy: float | None = None) -> str:
    """全息线框足球（正圆 + 六边形 + 辐条 + 轨道环）。"""
    c = size / 2
    r = size * 0.42
    pts = []
    for k in range(6):
        a = math.tau * k / 6 - math.pi / 2
        pts.append((c + math.cos(a) * r * 0.62, c + math.sin(a) * r * 0.62))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    spokes = "".join(
        f'<line x1="{c}" y1="{c}" x2="{x:.1f}" y2="{y:.1f}" stroke="{CYAN}" stroke-width="1.2" opacity=".5"/>'
        for x, y in pts)
    inner = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 0.12:.1f}" fill="none" stroke="{GREEN}" stroke-width="1" opacity=".7"/>'
        for x, y in pts)
    style = "" if cx is None else f"position:absolute;left:{cx - c:.0f}px;top:{cy - c:.0f}px;"
    return f"""<svg class="ball" style="{style}" width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
<defs><filter id="bg{size}" x="-60%" y="-60%" width="220%" height="220%">
<feGaussianBlur stdDeviation="{size * 0.05:.1f}" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<g filter="url(#bg{size})">
  <circle cx="{c}" cy="{c}" r="{r:.1f}" fill="rgba(30,220,170,.05)" stroke="#9CFBD6" stroke-width="2.2"/>
  <polygon points="{poly}" fill="none" stroke="{GREEN}" stroke-width="1.8"/>
  <circle cx="{c}" cy="{c}" r="{r * 0.42:.1f}" fill="none" stroke="{GREEN}" stroke-width="1.3" opacity=".75"/>
  {spokes}{inner}
</g>
<g fill="none" stroke="{CYAN}" stroke-width="1.2" opacity=".45">
  <ellipse cx="{c}" cy="{c + r + 18}" rx="{r * 1.1:.0f}" ry="14"/>
  <ellipse cx="{c}" cy="{c + r + 18}" rx="{r * 0.7:.0f}" ry="8"/>
</g>
</svg>"""


def hud_frame() -> str:
    """四角 HUD 刻度（叠在任意画布上，装饰但克制）。"""
    tick = (f'<path d="M0 26V0h26" stroke="{GREEN}" stroke-width="2" fill="none" opacity=".55"/>')
    return (f'<div class="hud tl">{tick}</div><div class="hud tr">{tick}</div>'
            f'<div class="hud bl">{tick}</div><div class="hud br">{tick}</div>')


def photo_bg(src: str, cls: str = "") -> str:
    """照片级背景：本地图片 + 压暗遮罩（文字可读性由遮罩保证）。"""
    uri = Path(src).resolve().as_uri()
    div = '<div class="photobg %s" style="background-image:url(&quot;%s&quot;)">' % (cls, uri)
    return div + '<i class="pscrim"></i></div>'
