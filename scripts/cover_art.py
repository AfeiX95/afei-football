# -*- coding: utf-8 -*-
"""封面美术资产（纯 SVG 生成，无外部图片、无 AI 生图）。

生成一张 1080×1440 的「夜色球场 + 全息球」底图，供 cover 叠加文字层：
    python scripts/cover_art.py --out "<输出.svg>"
导出的 SVG 同时被 scripts/xhs_card_d.py 的封面模板内联引用（读过一次即可缓存在内存里）。
"""
from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

W, H = 1080, 1440


def _dots(n: int, cx: float, cy: float, rx: float, ry: float, seed: int,
          rmin: float = 0.8, rmax: float = 1.9) -> str:
    """在看台椭圆环里撒座位灯点（确定性随机，保证每次出图一致）。"""
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        a = rnd.uniform(0, math.tau)
        rr = rnd.uniform(0.62, 1.0)
        x = cx + math.cos(a) * rx * rr
        y = cy + math.sin(a) * ry * rr
        r = rnd.uniform(rmin, rmax)
        op = rnd.uniform(0.25, 0.85)
        col = "#8FE9C6" if rnd.random() < 0.72 else "#9FC6FF"
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{col}" opacity="{op:.2f}"/>')
    return "".join(out)


def stadium_svg() -> str:
    # ---- 透视球场几何：远边窄、近边宽 ----
    far_l, far_r, far_y = 300, 780, 760
    near_l, near_r, near_y = 60, 1020, 1290
    mid_y = (far_y + near_y) / 2
    t = (mid_y - far_y) / (near_y - far_y)
    mid_l = far_l + (near_l - far_l) * t
    mid_r = far_r + (near_r - far_r) * t
    cx = (mid_l + mid_r) / 2

    def y_at(frac: float) -> float:
        return far_y + (near_y - far_y) * frac

    def x_edge(frac: float, left: bool) -> float:
        return (far_l + (near_l - far_l) * frac) if left else (far_r + (near_r - far_r) * frac)

    # 草皮条纹
    stripes = []
    for i in range(9):
        f0, f1 = i / 9, (i + 1) / 9
        y0, y1 = y_at(f0), y_at(f1)
        x0l, x0r, x1l, x1r = x_edge(f0, True), x_edge(f0, False), x_edge(f1, True), x_edge(f1, False)
        col = "#0B3B2A" if i % 2 == 0 else "#0E4632"
        stripes.append(f'<polygon points="{x0l:.1f},{y0:.1f} {x0r:.1f},{y0:.1f} '
                       f'{x1r:.1f},{y1:.1f} {x1l:.1f},{y1:.1f}" fill="{col}"/>')

    # 禁区与球门（远、近两端）
    def box(frac_y0: float, frac_y1: float, inset_ratio: float) -> str:
        y0, y1 = y_at(frac_y0), y_at(frac_y1)
        l0, r0 = x_edge(frac_y0, True), x_edge(frac_y0, False)
        l1, r1 = x_edge(frac_y1, True), x_edge(frac_y1, False)
        w0 = (r0 - l0) * inset_ratio
        w1 = (r1 - l1) * inset_ratio
        return (f'<polygon points="{l0 + w0:.1f},{y0:.1f} {r0 - w0:.1f},{y0:.1f} '
                f'{r1 - w1:.1f},{y1:.1f} {l1 + w1:.1f},{y1:.1f}" fill="none" '
                f'stroke="rgba(235,255,246,.55)" stroke-width="2"/>')

    # 中圈（椭圆透视）
    rx = (mid_r - mid_l) * 0.16
    ry = rx * 0.42

    # 球网
    def goal(frac: float, width_ratio: float, height: float) -> str:
        y = y_at(frac)
        l, r = x_edge(frac, True), x_edge(frac, False)
        w = (r - l) * width_ratio
        x0, x1 = (l + r) / 2 - w / 2, (l + r) / 2 + w / 2
        lines = "".join(
            f'<line x1="{x0 + (x1 - x0) * k / 8:.1f}" y1="{y:.1f}" x2="{x0 + (x1 - x0) * k / 8:.1f}" y2="{y - height:.1f}" '
            f'stroke="rgba(190,255,225,.28)" stroke-width="1"/>' for k in range(9))
        return (f'<g><line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" '
                f'stroke="rgba(235,255,246,.75)" stroke-width="3"/>'
                f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x0:.1f}" y2="{y - height:.1f}" stroke="rgba(235,255,246,.75)" stroke-width="2"/>'
                f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y - height:.1f}" stroke="rgba(235,255,246,.75)" stroke-width="2"/>'
                f'<line x1="{x0:.1f}" y1="{y - height:.1f}" x2="{x1:.1f}" y2="{y - height:.1f}" stroke="rgba(235,255,246,.55)" stroke-width="2"/>'
                f'{lines}</g>')

    # 全息球线框（二十面体投影近似）
    bx, by, br = cx, 560, 118
    hexpts = []
    for k in range(6):
        a = math.tau * k / 6 - math.pi / 2
        hexpts.append((bx + math.cos(a) * br * 0.62, by + math.sin(a) * br * 0.62))
    hexline = " ".join(f"{x:.1f},{y:.1f}" for x, y in hexpts)
    spokes = "".join(
        f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#7CF6C5" stroke-width="1.4" opacity=".55"/>'
        for x, y in hexpts)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#03070C"/><stop offset=".45" stop-color="#061019"/><stop offset="1" stop-color="#02060A"/>
  </linearGradient>
  <radialGradient id="floodGlow" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="#D9FFF0" stop-opacity=".85"/><stop offset=".55" stop-color="#59F2B6" stop-opacity=".18"/>
    <stop offset="1" stop-color="#59F2B6" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="pitchGlow" cx=".5" cy=".62" r=".62">
    <stop offset="0" stop-color="#35F59B" stop-opacity=".30"/><stop offset=".55" stop-color="#0E6B45" stop-opacity=".18"/>
    <stop offset="1" stop-color="#04121A" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="bowl" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0A1720"/><stop offset="1" stop-color="#040B11"/>
  </linearGradient>
  <filter id="soft" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="18"/></filter>
  <filter id="soft2" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="ballGlow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="10" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="grid" width="54" height="54" patternUnits="userSpaceOnUse">
    <path d="M54 0H0V54" fill="none" stroke="rgba(255,255,255,.045)" stroke-width="1"/>
  </pattern>
</defs>

<rect width="{W}" height="{H}" fill="url(#sky)"/>
<rect width="{W}" height="{H}" fill="url(#grid)"/>

<!-- 看台：外环 + 内环 + 座位灯 -->
<ellipse cx="{cx}" cy="{far_y + 40}" rx="{near_r - near_l + 120}" ry="300" fill="url(#bowl)" opacity=".95"/>
<ellipse cx="{cx}" cy="{far_y + 60}" rx="{near_r - near_l + 60}" ry="250" fill="#030A10"/>
{_dots(520, cx, far_y + 40, (near_r - near_l + 96) / 2 + 60, 240, 7)}
<ellipse cx="{cx}" cy="{far_y + 40}" rx="{near_r - near_l + 120}" ry="300" fill="none" stroke="rgba(90,240,190,.16)" stroke-width="2"/>

<!-- 泛光灯与光柱 -->
<g filter="url(#soft)">
  <ellipse cx="150" cy="470" rx="150" ry="120" fill="url(#floodGlow)" opacity=".8"/>
  <ellipse cx="930" cy="470" rx="150" ry="120" fill="url(#floodGlow)" opacity=".8"/>
  <ellipse cx="{cx}" cy="300" rx="260" ry="140" fill="url(#floodGlow)" opacity=".45"/>
</g>
<g opacity=".20" fill="url(#floodGlow)">
  <polygon points="150,470 420,{far_y + 10} 520,{near_y} 120,{near_y}"/>
  <polygon points="930,470 660,{far_y + 10} 560,{near_y} 960,{near_y}"/>
</g>

<!-- 草皮 -->
<g>{"".join(stripes)}</g>
<ellipse cx="{cx}" cy="{mid_y}" rx="480" ry="330" fill="url(#pitchGlow)"/>

<!-- 白线 -->
<g fill="none" stroke="rgba(240,255,248,.72)" stroke-width="2.4">
  <polygon points="{far_l},{far_y} {far_r},{far_y} {near_r},{near_y} {near_l},{near_y}"/>
  <line x1="{mid_l:.1f}" y1="{mid_y:.1f}" x2="{mid_r:.1f}" y2="{mid_y:.1f}"/>
  <ellipse cx="{cx:.1f}" cy="{mid_y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}"/>
</g>
{box(0.0, 0.16, 0.20)}
{box(0.84, 1.0, 0.20)}
{box(0.0, 0.06, 0.34)}
{box(0.94, 1.0, 0.34)}
{goal(0.0, 0.14, 30)}
{goal(1.0, 0.20, 44)}

<!-- 全息球 -->
<g filter="url(#ballGlow)">
  <circle cx="{bx}" cy="{by}" r="{br}" fill="rgba(30,220,160,.06)" stroke="#8DFBD0" stroke-width="2.6"/>
  <polygon points="{hexline}" fill="none" stroke="#7CF6C5" stroke-width="2"/>
  <circle cx="{bx}" cy="{by}" r="{br * 0.42:.0f}" fill="none" stroke="#7CF6C5" stroke-width="1.6" opacity=".85"/>
  {spokes}
</g>
<g opacity=".55" filter="url(#soft2)" fill="none" stroke="#5CF3BE" stroke-width="1.6">
  <ellipse cx="{bx}" cy="{by + br + 26}" rx="{br * 1.15:.0f}" ry="20"/>
  <ellipse cx="{bx}" cy="{by + br + 26}" rx="{br * 0.76:.0f}" ry="12" opacity=".6"/>
</g>

<!-- 边缘暗角 -->
<radialGradient id="vig" cx=".5" cy=".5" r=".72">
  <stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".82"/>
</radialGradient>
<rect width="{W}" height="{H}" fill="url(#vig)"/>
</svg>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(stadium_svg(), encoding="utf-8")
    print("wrote", p, len(stadium_svg()), "bytes")


if __name__ == "__main__":
    main()
