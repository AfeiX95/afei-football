# -*- coding: utf-8 -*-
"""D 版单场深挖卡 v2（2026-10-21 用户两轮定稿的形态，本地渲染器）。

合规依据：📚知识库/写作指南/小红书合规规范_20261021.md
- 不上：场次编号、三项概率并列、逐比分概率数值、方向/结论百分比、底部来源与话题标签
- 只上：身价对标 + 近期状态 + 历史交锋 + 攻防对照 + 六维雷达 + 泊松分布 + 蒙特卡洛热度
   + 核心矛盾与看点（100–200 字），浅色赛博底（不用黑底）

用法：
    XHS_HTML_TMP=<可写目录> python -X utf8 scripts/xhs_card_d.py --input cards.json --out <目录> [--limit N]
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1440
MONO = '"Consolas","JetBrains Mono","Microsoft YaHei UI",monospace'

CSS = """
*,*::before,*::after{box-sizing:border-box;-webkit-font-smoothing:antialiased}
html,body{margin:0;padding:0;background:#eef2f6}
body{width:%(w)dpx;height:%(h)dpx;overflow:hidden}
.card{position:relative;width:%(w)dpx;height:%(h)dpx;display:flex;flex-direction:column;
  padding:46px 54px 34px;background:#eef2f6;color:#0d1117;
  font-family:"Microsoft YaHei UI","Noto Sans SC",sans-serif;
  background-image:linear-gradient(rgba(10,90,120,.06) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(10,90,120,.06) 1px,transparent 1px);
  background-size:34px 34px}
.card::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(120%% 70%% at 12%% 0%%,rgba(10,163,194,.10),transparent 60%%),
             radial-gradient(90%% 60%% at 100%% 8%%,rgba(255,45,120,.08),transparent 60%%)}
.frame{position:absolute;inset:20px;border:1px solid rgba(10,90,120,.16);pointer-events:none}
.frame i{position:absolute;width:22px;height:22px;border:2px solid #0aa3c2}
.frame i.tl{left:-1px;top:-1px;border-right:0;border-bottom:0}
.frame i.tr{right:-1px;top:-1px;border-left:0;border-bottom:0}
.frame i.bl{left:-1px;bottom:-1px;border-right:0;border-top:0}
.frame i.br{right:-1px;bottom:-1px;border-left:0;border-top:0}
.top{display:flex;align-items:center;justify-content:space-between;font-family:%(mono)s;
  font-size:17px;letter-spacing:.12em;color:#3f5566;position:relative;z-index:2}
.top .lg{color:#0aa3c2;font-weight:700;letter-spacing:.18em}
.top .md{color:#8a99a6}
.top .pg{color:#e8402a;font-weight:800}
.top .bd{color:#0aa3c2;font-weight:800;letter-spacing:.04em}
h1{margin:16px 0 0;font-size:76px;line-height:1.14;font-weight:900;text-align:center;letter-spacing:-.01em;position:relative;z-index:2}
h1 .vs{margin:0 14px;font-size:30px;font-weight:400;color:#0aa3c2;vertical-align:middle}
.sec{margin-top:11px;position:relative;z-index:2}
.sh{display:flex;align-items:baseline;justify-content:space-between;border-bottom:1px solid rgba(10,90,120,.2);padding-bottom:4px}
.sh .n{font-size:21px;font-weight:800;letter-spacing:.05em;display:flex;align-items:center;gap:8px}
.sh .n::before{content:"";width:9px;height:9px;background:#0aa3c2}
.sh .h{font-family:%(mono)s;font-size:14px;color:#7b8996;letter-spacing:.05em}
/* 身价块：突出 */
.val{margin-top:8px;background:linear-gradient(180deg,#ffffff,#f3f8fb);
  border:1px solid rgba(10,90,120,.16);border-left:5px solid #0aa3c2;padding:9px 15px 8px}
.val .head{display:flex;align-items:flex-end;justify-content:space-between}
.val .side{flex:1}
.val .side.r{text-align:right}
.val .tn{font-size:19px;font-weight:800;letter-spacing:.02em}
.val .tn em{font-style:normal;font-size:12px;font-family:%(mono)s;color:#0aa3c2;
  border:1px solid rgba(10,163,194,.55);padding:0 5px;margin-left:6px;vertical-align:2px}
.val .money{font-family:%(mono)s;font-size:44px;font-weight:900;line-height:1.02;color:#e8402a;letter-spacing:-.01em}
.val .money small{font-size:20px;font-weight:700;color:#7a2f22;margin-left:3px}
.val .rk{font-size:14px;color:#5c6b78;font-family:%(mono)s}
.bar{display:flex;height:10px;margin-top:9px;background:rgba(10,90,120,.1)}
.bar i{display:block;height:10px}
.bar i.l{background:linear-gradient(90deg,#0aa3c2,#41c8e0)}
.bar i.r{background:linear-gradient(90deg,#ff86ab,#e8402a)}
.vmeta{display:flex;justify-content:space-between;margin-top:5px;font-size:14px;color:#5c6b78;font-family:%(mono)s}
.vmeta b{color:#e8402a;font-size:16px}
/* 两列 */
.two{display:grid;gap:20px;margin-top:5px;align-items:start}
.two.stretch{align-items:stretch}
table.st.fill{height:100%%}
.c2{grid-template-columns:1fr 1fr}
.c1b{grid-template-columns:1.06fr .94fr}
.c2b{grid-template-columns:.9fr 1.1fr}
/* 战绩 */
.fr{display:flex;align-items:center;justify-content:space-between;padding:2px 0}
.fr .l{display:flex;align-items:center;gap:8px}
.fr .nm{font-size:19px;font-weight:800;min-width:112px}
.badges{display:flex;gap:4px}
.badges i{width:24px;height:24px;display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:800;font-style:normal;border:1px solid}
.badges i.w{color:#0a7d5a;border-color:rgba(10,125,90,.55);background:rgba(10,125,90,.1)}
.badges i.d{color:#4a5a68;border-color:rgba(74,90,104,.45);background:rgba(74,90,104,.08)}
.badges i.l{color:#c2382f;border-color:rgba(194,56,47,.55);background:rgba(194,56,47,.1)}
.fr .r{font-family:%(mono)s;font-size:17px;font-weight:800;color:#0aa3c2}
.sub2{font-size:14px;color:#5c6b78;padding:0 0 3px}
.h2h{background:#fff;border:1px solid rgba(10,90,120,.14);padding:6px 10px;
  font-size:14px;line-height:1.45;color:#22303c}
.h2h b{color:#0aa3c2;font-family:%(mono)s}
/* 攻防表 */
table.st{width:100%%;border-collapse:collapse;font-size:16px}
table.st th{font-size:14px;color:#6a7885;font-weight:700;padding:4px 0;border-bottom:1px solid rgba(10,90,120,.18)}
table.st th.a,table.st td.a{text-align:right;font-family:%(mono)s}
table.st th:first-child,table.st td:first-child{width:36%%}
table.st td{padding:6px 0;border-bottom:1px dashed rgba(10,90,120,.12)}
table.st td.a{font-weight:800;width:32%%}
/* 雷达 */
.rad{display:flex;flex-direction:column;align-items:center;justify-content:center}
.lg2{font-size:13px;color:#5c6b78;display:flex;gap:14px;margin-top:2px}
.lg2 span{display:flex;align-items:center;gap:5px}
.lg2 i{display:inline-block;width:10px;height:10px}
/* 泊松 */
.pois{margin-top:6px}
.pr{display:grid;grid-template-columns:30px 1fr 74px;align-items:center;gap:7px;white-space:nowrap;
  font-family:%(mono)s;font-size:13px;color:#3f5566;margin-top:3px}
.pr .pb{height:11px;background:rgba(10,90,120,.08);position:relative}
.pr .pb i{position:absolute;left:0;top:0;bottom:0;display:block}
.pr .pb i.h{background:linear-gradient(90deg,#0aa3c2,#66d6ea)}
.pr .pb i.a{background:linear-gradient(90deg,#ff7ba3,#e8402a);top:6px;height:5px}
.pr .pv{text-align:right;font-weight:700;color:#22303c;font-size:12px}
.pr .pv em{font-style:normal;color:#9aa8b4;margin:0 1px}
/* 热力 */
.heat .grid{display:grid;grid-template-columns:22px repeat(5,1fr);gap:3px}
.heat .rb{display:flex;align-items:center;justify-content:center;font-family:%(mono)s;font-size:13px;color:#7b8996}
.heat .cell{height:37px;border-radius:2px}
.heat .ax{display:flex;justify-content:space-around;margin-top:3px;font-family:%(mono)s;font-size:12px;color:#7b8996;padding-left:22px}
.heat .cap{margin-top:3px;font-size:13px;color:#7b8996}
/* 叙事 */
.narr{font-size:14.6px;line-height:1.5;color:#1a242e;text-align:justify}
.narr b{color:#e8402a;font-weight:800;margin-right:5px}
.pt{margin-top:6px;font-size:16px;line-height:1.55;border-left:3px solid #0aa3c2;padding-left:9px}
.pt em{font-style:normal;font-weight:800;color:#0aa3c2;margin-right:5px}

/* 对比条（按胜率条的排法：两端数值 + 中间双色条） */
.cmp{margin-top:6px}
.cmp .row{margin-top:5px}
.cmp .lab{font-size:13px;color:#6a7885;letter-spacing:.02em;text-align:center}
.cmp .rb{display:flex;align-items:center;gap:7px;font-family:%(mono)s;font-size:15px;font-weight:800;color:#22303c}
.cmp .rb .v{width:46px}
.cmp .rb .v.w{color:#7c8d9c;font-weight:600}
.cmp .rb .v.b{font-weight:900}
.cmp .rb .v.r{text-align:right;color:#b8331f}
.cmp .rb .v.l{color:#0a768f}
.cmp .track{flex:1;height:9px;display:flex;background:rgba(10,90,120,.10)}
.cmp .track i{display:block;height:9px}
.cmp .track i.l{background:linear-gradient(90deg,#0aa3c2,#63d2e6)}
.cmp .track i.r{background:linear-gradient(90deg,#ff85a9,#e8402a)}
/* 胜平负饼图 */
.pie{display:flex;align-items:center;justify-content:center;margin-top:2px}
.pielg{display:flex;flex-direction:column;gap:6px;margin-left:16px;font-size:14px;color:#33434f}
.pielg span{display:flex;align-items:center;gap:7px;white-space:nowrap}
.pielg i{width:10px;height:10px;display:inline-block}
.pielg b{font-family:Consolas,JetBrains Mono,monospace;font-size:16px;color:#22303c}
/* 赛果构成双饼 */
.fps{display:flex;gap:22px;align-items:flex-start}
.fp{text-align:center}
.fpt{font-size:14px;font-weight:800;color:#22303c;margin-bottom:2px}
.fpl{font-size:12.5px;color:#5c6b78;margin-top:2px}
.fpn{font-size:11.5px;color:#7b8794;margin-top:4px}
/* 情报 */
.intel{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px}
.ic{background:#fff;border:1px solid rgba(10,90,120,.14);padding:6px 8px}
.ic.wide{grid-column:1 / -1}
.ic.wide .t i{background:#c2382f}
.ic .t{font-size:14px;font-weight:800;display:flex;align-items:center;gap:6px;margin-bottom:3px}
.ic .t i{width:6px;height:6px;display:inline-block}
.ic.g .t{color:#0a7d5a}.ic.g .t i{background:#0a7d5a}
.ic.b .t{color:#b8331f}.ic.b .t i{background:#b8331f}
.ic ul{margin:0;padding-left:13px}
.ic2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.ic2 .t{font-size:19px;font-weight:900;color:#E9F4FF;margin-bottom:6px}
.ic2 ul{margin:0;padding-left:18px}
.ic2 li{font-size:19px;line-height:1.55;margin-bottom:5px;color:#C6D4E4}
.ic2 li.g::marker{color:#00F078}
.ic2 li.b::marker{color:#FF6B8A}
.ic li{font-size:12.5px;line-height:1.36;color:#22303c;margin-bottom:1px}
.ic li::marker{color:#9aa8b4}
""" % {"w": W, "h": H, "mono": MONO}


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


# ---------------------------------------------------------------- 组件
def radial(card: dict, size: int = 330) -> str:
    r = card.get("radar") or {}
    dims = r.get("dims") or []
    hv, av = r.get("home") or [], r.get("away") or []
    if not dims or len(hv) != len(dims) or len(av) != len(dims):
        return ""
    cx = cy = size / 2.0
    rad = size / 2.0 - 62
    n = len(dims)

    def pt(i, val):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        rr = rad * max(0.06, min(1.0, float(val) / 100.0))
        return cx + rr * math.cos(ang), cy + rr * math.sin(ang)

    def poly(vals):
        return " ".join("%.1f,%.1f" % pt(i, v) for i, v in enumerate(vals))

    rings = []
    for k in (0.25, 0.5, 0.75, 1.0):
        rings.append('<polygon points="%s" fill="none" stroke="rgba(150,205,230,.34)" stroke-width="1.1"/>'
                     % " ".join("%.1f,%.1f" % (cx + rad * k * math.cos(-math.pi / 2 + i * 2 * math.pi / n),
                                               cy + rad * k * math.sin(-math.pi / 2 + i * 2 * math.pi / n))
                                for i in range(n)))
    labels = []
    for i, d in enumerate(dims):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        lr = rad + 26                      # 标签放在多边形外 26px，避免压线
        x = cx + lr * math.cos(ang)
        y = cy + lr * math.sin(ang) + 5
        anchor = "middle"
        if x > cx + 8:
            anchor = "start"
        elif x < cx - 8:
            anchor = "end"
        labels.append('<text x="%.1f" y="%.1f" font-size="15" font-weight="700" fill="#CFE0EC" '
                      'text-anchor="%s">%s</text>' % (x, y, anchor, esc(d)))
    axes = "".join(
        '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="rgba(150,205,230,.20)" stroke-width="1"/>'
        % (cx, cy, cx + rad * math.cos(-math.pi / 2 + i * 2 * math.pi / n),
           cy + rad * math.sin(-math.pi / 2 + i * 2 * math.pi / n))
        for i in range(n))
    svg = ("<svg viewBox=\"0 0 %.0f %.0f\" width=\"%.0f\" height=\"%.0f\" style=\"overflow:visible\">"
           % (size, size, size, size))
    svg += "".join(rings) + axes
    svg += '<polygon points="%s" fill="rgba(0,240,120,.22)" stroke="#00F078" stroke-width="2.8"/>' % poly(hv)
    svg += '<polygon points="%s" fill="rgba(255,107,129,.24)" stroke="#FF6B81" stroke-width="2.8"/>' % poly(av)
    svg += "".join(labels) + "</svg>"
    return svg


def wdl_pie(card: dict, size: int = 236) -> str:
    """胜平负饼图（模型口径）。只画面积与标签，不出方向建议。"""
    md = card.get("model") or {}
    w = md.get("wdl") or [0.34, 0.33, 0.33]
    tot = sum(w) or 1
    w = [x / tot for x in w]
    colors = ["#0aa3c2", "#9aa8b4", "#e8402a"]
    names = ["主胜", "平", "客胜"]
    r, cx, cy = size / 2.0 - 14, size / 2.0, size / 2.0
    ang = -90.0
    arcs = []
    for val, col in zip(w, colors):
        sweep = 360.0 * val
        a0, a1 = math.radians(ang), math.radians(ang + sweep)
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        large = 1 if sweep > 180 else 0
        arcs.append('<path d="M%.2f %.2f L%.2f %.2f A%.2f %.2f 0 %d 1 %.2f %.2f Z" fill="%s" '
                    'stroke="#f4f7fa" stroke-width="2"/>'
                    % (cx, cy, x0, y0, r, r, large, x1, y1, col))
        ang += sweep
    hole = ('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff"/>' % (cx, cy, r * 0.58))
    center = ('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="13" fill="#6a7885">主胜</text>'
              '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="30" font-weight="800" '
              'fill="#b8331f" font-family="%s">%.1f%%</text>'
              % (cx, cy - 6, cx, cy + 22, "Consolas,JetBrains Mono,monospace", w[0] * 100))
    lg = ('<div class="pielg">' + "".join(
        '<span><i style="background:%s"></i>%s <b>%.1f%%</b></span>' % (c, n, v * 100)
        for c, n, v in zip(colors, names, w)) + "</div>")
    return ('<svg viewBox="0 0 %.0f %.0f" width="%.0f" height="%.0f">%s%s%s</svg>%s'
            % (size, size, size, size, "".join(arcs), hole, center, lg))


def form_pies(card: dict, size: int = 168) -> str:
    """近 10 场赛果构成（已发生场次占比，不预测、不涉市场口径）。

    左：主队同主场 10 场；右：客队同客场 10 场。三段 = 胜/平/负场次。
    """
    f = card.get("form") or {}
    pairs = [(card.get("home"), (f.get("home") or {}).get("ha")),
             (card.get("away"), (f.get("away") or {}).get("ha"))]
    colors = ["#0aa3c2", "#9aa8b4", "#e8402a"]
    names = ["胜", "平", "负"]
    blocks = []
    for who, ha in pairs:
        nums = [int(x) for x in re.findall(r"(\d+)\s*胜\s*(\d+)\s*平\s*(\d+)\s*负", str(ha or ""))[0]]             if re.findall(r"(\d+)\s*胜\s*(\d+)\s*平\s*(\d+)\s*负", str(ha or "")) else [0, 0, 0]
        tot = sum(nums) or 1
        share = [n / tot for n in nums]
        cx = cy = size / 2.0
        r = size / 2.0 - 8
        ang, arcs = -90.0, []
        for val, col in zip(share, colors):
            sweep = 360.0 * val
            a0, a1 = math.radians(ang), math.radians(ang + sweep)
            x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
            x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
            if sweep > 0.4:
                arcs.append('<path d="M%.2f %.2f L%.2f %.2f A%.2f %.2f 0 %d 1 %.2f %.2f Z" fill="%s" '
                            'stroke="#f4f7fa" stroke-width="2"/>'
                            % (cx, cy, x0, y0, r, r, 1 if sweep > 180 else 0, x1, y1, col))
            ang += sweep
        hole = '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#fff"/>' % (cx, cy, r * 0.56)
        txt = ('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="12" fill="#6a7885">%s 场</text>'
               '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="19" font-weight="800" '
               'fill="#22303c" font-family="Consolas,JetBrains Mono,monospace">%d-%d-%d</text>'
               % (cx, cy - 5, tot, cx, cy + 15, nums[0], nums[1], nums[2]))
        blocks.append(
            '<div class="fp"><div class="fpt">%s</div>'
            '<svg viewBox="0 0 %d %d" width="%d" height="%d">%s%s%s</svg>'
            '<div class="fpl">胜 %d · 平 %d · 负 %d</div></div>'
            % (esc(who), size, size, size, size, "".join(arcs), hole, txt, nums[0], nums[1], nums[2]))
    return ('<div class="fps">%s</div><div class="fpn">同主场 / 同客场近 10 场交锋状态，'
            '已发生场次占比</div>' % "".join(blocks))


def pois_bars(card: dict) -> str:
    lam = (card.get("model") or {}).get("lam") or []
    if len(lam) != 2:
        return ""

    def pmf(k, lam_):
        return math.exp(-lam_) * lam_ ** k / math.factorial(k)

    hs = [pmf(k, lam[0]) for k in range(5)]
    as_ = [pmf(k, lam[1]) for k in range(5)]
    mx = max(hs + as_) or 1
    rows = []
    for k in range(5):
        rows.append('<div class="pr"><span>%d 球</span><span class="pb">'
                    '<i class="h" style="width:%.1f%%"></i><i class="a" style="width:%.1f%%"></i>'
                    '</span><span class="pv">%d%%<em>/</em>%d%%</span></div>'
                    % (k, 100 * hs[k] / mx, 100 * as_[k] / mx,
                       round(100 * hs[k]), round(100 * as_[k])))
    return "".join(rows)


def mc_heat(card: dict) -> str:
    g = (card.get("model") or {}).get("grid") or []
    if not g:
        return ""
    mx = max(max(row) for row in g) or 1
    # grid[h][a]：h=主队进球，a=客队进球（严格只上色不标具体比分数字，防 OCR 误判为比分推荐）
    cells = []
    for a in range(5):                      # 纵轴：客队进球
        cells.append('<div class="rb">%d</div>' % a)
        for h in range(5):                  # 横轴：主队进球
            v = g[h][a] if h < len(g) and a < len(g[h]) else 0
            al = 0.05 + 0.88 * (float(v) / mx)
            cells.append('<div class="cell" style="background:rgba(232,64,42,%.2f)"></div>' % al)
    ax = "".join("<span>%d</span>" % i for i in range(5))
    home = esc(card.get("home") or "主队")
    away = esc(card.get("away") or "客队")
    return ('<div class="axlab">↓ %s 进球（纵轴）</div><div class="grid">%s</div>'
            '<div class="ax">%s</div><div class="axlab r">%s 进球（横轴）→</div>'
            '<div class="cap">主客进球区间热图 · 横轴主队、纵轴客队 · 颜色深浅代表区间密度</div>'
            % (away, "".join(cells), ax, home))


def value_block(card: dict) -> str:
    v = card.get("value") or {}
    h, a = float(v.get("home_m") or 0), float(v.get("away_m") or 0)
    if not (h and a):
        return ""
    tot = h + a
    wl = max(6.0, min(94.0, 100.0 * h / tot))
    txt = (v.get("rank_text") or "").replace("第", "")
    parts = [p.strip() for p in txt.replace("·", "|").split("|") if p.strip()]
    rh = parts[0] if parts else "—"
    ra = parts[-1] if len(parts) > 1 else "—"

    def money(t):
        t = (t or "").strip()
        for u in ("亿欧", "万欧"):
            if t.endswith(u):
                num = t[:-len(u)].strip()
                return ('<span class="money">%s<small>%s</small></span>' % (esc(num), u))
        return '<span class="money">%s</span>' % esc(t)

    return f"""<div class="val">
<div class="head">
  <div class="side"><div class="tn">{esc(card.get("home"))}<em>{esc(card.get("league"))}</em></div>{money(v.get("home_text"))}
    {'<div class="rk">名次 %s</div>' % esc(rh) if v.get("rank_text") else ""}</div>
  <div class="side r"><div class="tn">{esc(card.get("away"))}<em>{esc(card.get("league"))}</em></div>{money(v.get("away_text"))}
    {('<div class="rk">名次 %s</div>' % esc(ra)) if v.get("rank_text") else ""}</div>
</div>
<div class="bar"><i class="l" style="width:{wl:.1f}%"></i><i class="r" style="width:{100 - wl:.1f}%"></i></div>
<div class="vmeta"><span>主队占比 {wl:.0f}%</span><span>全队总值差 <b>{esc(v.get("ratio"))}</b></span></div>
</div>"""


def cmp_rows(card: dict) -> str:
    f = card.get("form") or {}
    fh, fa = f.get("home") or {}, f.get("away") or {}

    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    pj_h, sj_h = num(fh.get("pj")), num(fh.get("sj"))
    pj_a, sj_a = num(fa.get("pj")), num(fa.get("sj"))
    _sh = fh.get("seq") or ""
    _sa = fa.get("seq") or ""
    seqh = ("".join(_sh) if isinstance(_sh, list) else str(_sh)).upper()
    seqa = ("".join(_sa) if isinstance(_sa, list) else str(_sa)).upper()
    win_h = 100.0 * seqh.count("W") / len(seqh) if seqh else None
    win_a = 100.0 * seqa.count("W") / len(seqa) if seqa else None
    zh, za = num(fh.get("zero")), num(fa.get("zero"))

    rows = [
        ("场均进球", "%.2f" % pj_h, "%.2f" % pj_a, None),
        ("场均失球", "%.2f" % sj_h, "%.2f" % sj_a, None),
        ("场均净胜", "%+.2f" % (pj_h - sj_h), "%+.2f" % (pj_a - sj_a), "zero"),
        ("零封率", "%d%%" % round(zh), "%d%%" % round(za), None),
        *([("近五场胜率", "%d%%" % round(win_h), "%d%%" % round(win_a), None)]
          if (win_h is not None or win_a is not None) else []),
        ("场均总进球", "%.2f" % (pj_h + sj_h), "%.2f" % (pj_a + sj_a), None),
    ]
    out = ['<div class="row"><div class="lab" style="display:flex;justify-content:space-between;'
           'font-weight:800"><span style="color:#0a768f">%s</span>'
           '<span style="color:#b8331f">%s</span></div></div>' % (esc(card.get("home")), esc(card.get("away")))]
    for lab, a, b, mode in rows:
        if mode == "zero":
            xa = abs(num(a.replace("+", "")))
            xb = abs(num(b.replace("+", "")))
            mx = max(xa, xb, 0.01)
            wa, wb = 48 * xa / mx, 48 * xb / mx
            out.append(
                '<div class="row"><div class="lab">%s</div><div class="rb">'
                '<span class="v l">%s</span><span class="track z">'
                '<i class="ln"></i><i class="l" style="width:%.1f%%"></i>'
                '<i class="r" style="width:%.1f%%"></i></span><span class="v r">%s</span></div></div>'
                % (esc(lab), esc(a), wa, wb, esc(b)))
            continue
        x = num(a.replace("%", "").replace("+", ""))
        y = num(b.replace("%", "").replace("+", ""))
        tot = (x + y) or 1
        wl = max(4.0, min(96.0, 100.0 * x / tot))
        # 谁更优：场均失球越小越好，其余越大越好
        lower_better = ("失球" in lab)
        hb = (x < y) if lower_better else (x > y)
        la_cls, lb_cls = ("b", "w") if hb else ("w", "b")
        out.append(
            '<div class="row"><div class="lab">%s</div><div class="rb">'
            '<span class="v l %s">%s</span><span class="track">'
            '<i class="l" style="width:%.1f%%"></i><i class="r" style="width:%.1f%%"></i>'
            '</span><span class="v r %s">%s</span></div></div>'
            % (esc(lab), la_cls, esc(a), wl, 100 - wl, lb_cls, esc(b)))
    return "".join(out)


def intel_block(card: dict) -> str:
    it = card.get("intel") or {}
    if not it:
        return ""
    home, away = esc(card.get("home")), esc(card.get("away"))

    def cell(who, kind, items):
        if not items:
            return ""
        tag = "有利情报" if kind == "g" else "不利情报"
        lis = "".join("<li>%s</li>" % esc(x) for x in items[:3])
        return ('<div class="ic %s"><div class="t"><i></i>%s · %s</div><ul>%s</ul></div>'
                % (kind, who, tag, lis))

    common = it.get("common") or []
    wide = ""
    if common:
        lis = "".join("<li>%s</li>" % esc(x) for x in common[:3])
        blk = card.get("intel2") or {}
        if blk:
            def col(side_key, title):
                d_ = blk.get(side_key) or {}
                good = "".join('<li class="g">%s</li>' % esc(x) for x in (d_.get("good") or [])[:2])
                bad = "".join('<li class="b">%s</li>' % esc(x) for x in (d_.get("bad") or [])[:1])
                return ('<div class="ic"><div class="t"><i></i>%s</div><ul class="ig">%s</ul>'
                        '<ul class="ib">%s</ul></div>' % (esc(title), good, bad))
            wide = '<div class="ic2">%s%s</div>' % (col("home", card.get("home") or "主队"), col("away", card.get("away") or "客队"))
        else:
            wide = '<div class="ic wide"><div class="t"><i></i>近 5 场 · 交锋 · 伤停</div><ul>%s</ul></div>' % lis
    return (cell(home, "g", it.get("home_good")) + cell(home, "b", it.get("home_bad")) +
            cell(away, "g", it.get("away_good")) + cell(away, "b", it.get("away_bad")) + wide)


# ---------------------------------------------------------------- 皮肤（每天轮换）
SKINS = {
    "neon": {"name": "荧光绿", "bg": "#060A12", "bg2": "#0A1018", "panel": "#0D1723",
             "text": "#E9F4FF", "muted": "#8FA3B8", "accent": "#00F078", "accent_soft": "#39FFA8",
             "accent2": "#00D8FF", "red": "#FF4D6A", "red_soft": "#FF8DA1", "pink": "#FF3FA4"},
    "cyan": {"name": "青蓝", "bg": "#050B14", "bg2": "#08111C", "panel": "#0B1524",
             "text": "#E6F3FF", "muted": "#87A0B8", "accent": "#22D3FF", "accent_soft": "#7BE7FF",
             "accent2": "#7C5CFF", "red": "#FF5A7A", "red_soft": "#FF95AC", "pink": "#C77DFF"},
    "violet": {"name": "紫粉", "bg": "#0A0714", "bg2": "#0F0A1D", "panel": "#150F26",
               "text": "#F0EBFF", "muted": "#9C8FB8", "accent": "#B26BFF", "accent_soft": "#D3A6FF",
               "accent2": "#FF4FD8", "red": "#FF5C7A", "red_soft": "#FF9AB0", "pink": "#FF7AC8"},
    "amber": {"name": "琥珀", "bg": "#0B0803", "bg2": "#120D05", "panel": "#1A1308",
              "text": "#FFF6E6", "muted": "#B49B76", "accent": "#FFB020", "accent_soft": "#FFD06B",
              "accent2": "#FF6A00", "red": "#FF5A4A", "red_soft": "#FF9B8F", "pink": "#FF8A5C"},
    "ice": {"name": "冰蓝", "bg": "#050A10", "bg2": "#081018", "panel": "#0B1620",
            "text": "#EAF6FF", "muted": "#7E96AA", "accent": "#5CE1E6", "accent_soft": "#A6F0F3",
            "accent2": "#3D7BFF", "red": "#FF5F7E", "red_soft": "#FF9DB2", "pink": "#7FD8FF"},
}
SKIN_ORDER = ["neon", "cyan", "violet", "amber", "ice"]


def skin_for(date_str: str | None, want: str | None = None) -> dict:
    if want and want in SKINS:
        return dict(SKINS[want], key=want)
    import datetime as _dt
    d = date_str or _dt.date.today().strftime("%Y%m%d")
    digits = "".join(ch for ch in str(d) if ch.isdigit())
    seed = int(digits) if digits else 0
    key = SKIN_ORDER[seed % len(SKIN_ORDER)]
    return dict(SKINS[key], key=key)


LIGHT_MAP = {
    "#eef2f6": "bg", "#f3f8fb": "bg2", "#fff": "panel", "#ffffff": "panel",
    "#0d1117": "text", "#1a242e": "text", "#22303c": "text",
    "#5c6b78": "muted", "#7b8996": "muted", "#6a7885": "muted", "#8a99a6": "muted",
    "#9aa8b4": "muted", "#4a5a68": "muted", "#3f5566": "muted",
    "#0aa3c2": "accent", "#41c8e0": "accent", "#66d6ea": "accent_soft", "#0a768f": "accent2",
    "#e8402a": "red", "#b8331f": "red", "#c2382f": "red", "#7a2f22": "red_soft",
    "#ff86ab": "pink", "#ff7ba3": "pink", "#ff85a9": "pink", "#0a7d5a": "accent2",
    "#2a3c48": "text", "#33434f": "muted", "#7b8794": "muted", "#63d2e6": "accent_soft",
}


COMPACT_CSS = """
<style>
.card{padding:32px 44px 22px}
h1{font-size:64px;margin-top:10px}
.sec{margin-top:8px}
.val{margin-top:6px;padding:7px 13px 6px}
.val .side .money{font-size:34px}
.sh{padding-bottom:3px}
.narr{line-height:1.42}

.axlab{font-size:15px;font-weight:800;color:#8FA3B8;letter-spacing:.04em;margin:2px 0}
.axlab.r{text-align:right}
.track.z{position:relative}
.track.z .ln{position:absolute;left:50%;top:-3px;bottom:-3px;width:2px;background:#F0F5FF;box-shadow:0 0 4px rgba(240,245,255,.8)}
.track.z .l{position:absolute;right:50%;top:0;bottom:0;background:linear-gradient(90deg,#00F07800,#00F078)}
.track.z .r{position:absolute;left:50%;top:0;bottom:0;background:linear-gradient(90deg,#FF6B81,#FF6B8100)}
.cell{display:flex;align-items:center;justify-content:center}
</style>
"""


def _apply_skin(html: str, skin: dict) -> str:
    def hexrep(m):
        key = LIGHT_MAP.get(m.group(0).lower())
        return skin[key] if key else m.group(0)
    out = re.sub(r"#[0-9a-fA-F]{3,8}", hexrep, html)
    acc = skin["accent"].lstrip("#")
    rgb = "%d,%d,%d" % (int(acc[0:2], 16), int(acc[2:4], 16), int(acc[4:6], 16))
    out = re.sub(r"rgba\(10,\s*90,\s*120,", "rgba(%s," % rgb, out)
    out = re.sub(r"rgba\(10,\s*90,\s*120\s*,", "rgba(%s," % rgb, out)
    return out.replace("</body>", COMPACT_CSS + "</body>")


def _scale_font_css(html: str, k: float) -> str:
    """只放大 CSS 里的 font-size，不改几何尺寸。"""
    if abs(k - 1.0) < 1e-6:
        return html
    return re.sub(r"font-size:(\d+(?:\.\d+)?)px",
                  lambda m: "font-size:%.1fpx" % (float(m.group(1)) * k), html)


def card_html(card: dict, idx: int, total: int) -> str:
    f = card.get("form") or {}
    fh, fa = f.get("home") or {}, f.get("away") or {}
    home, away = esc(card.get("home")), esc(card.get("away"))
    league = esc(card.get("league"))
    focus = card.get("focus") or []
    narr = esc((card.get("narr") or " ".join(x for x in [card.get("contrast") or ""] + list(focus) if x))[:210])
    point = esc(card.get("point") or (focus[0] if focus else ""))
    _h2h = f.get("h2h")
    if isinstance(_h2h, dict):
        h2h_line = f.get("h2h_short") or ("交锋 %s 场 · 场均 %s 球" % (_h2h.get("n") or "—", _h2h.get("avg_goals") or "—"))
    else:
        h2h_line = _h2h or f.get("h2h_short") or ""
    h2h = esc(h2h_line)

    def badges(seq):
        cls = {"W": "w", "D": "d", "L": "l"}
        txt = {"W": "胜", "D": "平", "L": "负"}
        return "".join('<i class="%s">%s</i>' % (cls.get(s, "d"), txt.get(s, "平")) for s in (seq or [])[:5])

    pt_html = ('<div class="pt"><em>看点</em>' + point + "</div>") if point else ""
    # 报告里没有六维数据时，整块不画，对比条占满整行（不拿假数据凑图）
    has_radar = bool((card.get("radar") or {}).get("dims"))
    nr = "" if has_radar else " noradar"
    radblock = ""
    if has_radar:
        radblock = ('<div class="rad">' + radial(card) +
                    '<div class="lg2"><span><i style="background:#00F078"></i>' + home + '</span>'
                    '<span><i style="background:#FF6B81"></i>' + away + '</span></div></div>')
    quick = ""
    fm = card.get("form") or {}
    cells = []
    for who, tag in (("home", "主队近况"), ("away", "客队近况")):
        f = fm.get(who) or {}
        if f:
            l5 = (f.get("l5") or "").strip()
            tail = "场均进 %s 失 %s" % (f.get("pj") or "—", f.get("sj") or "—")
            cells.append((tag, ("%s ／ %s" % (l5, tail)) if l5 else tail))
    h2h = fm.get("h2h")
    if isinstance(h2h, dict) and h2h:
        cells.append(("交锋", "%s 场 主队 %s胜%s平%s负" % (h2h.get("n") or "—", h2h.get("w") or 0,
                                                     h2h.get("d") or 0, h2h.get("l") or 0)))
    elif isinstance(h2h, str) and h2h.strip():
        cells.append(("交锋", h2h))
    quick_cells = ""
    if cells:
        quick_cells = ('<div class="sh" style="margin-bottom:6px"><span class="n" style="font-size:19px">本场速记</span>'
                       '<span class="h">只列已发生的数字</span></div><div style="display:grid;'
                       'grid-template-columns:1fr 1fr;gap:12px">')
        for tag, val in cells:
            quick_cells += ('<div style="background:#fff;border-left:5px solid #0a768f;padding:12px 14px">'
                            '<b style="display:block;font-size:17px;color:#0a768f;letter-spacing:.06em">%s</b>'
                            '<span style="display:block;margin-top:6px;font-size:21px;color:#2a3c48;line-height:1.35">%s</span>'
                            '</div>' % (esc(tag), esc(val)))
        quick_cells += "</div>"

    pie_inner = form_pies(card) if card.get("pie_mode") == "form" else (wdl_pie(card) if card.get("pie_mode") not in (None, "none") else "")
    heat_html = '<div class="heat">' + mc_heat(card) + '</div>' if card.get("heat", True) else ""
    scores = card.get("h2h_scores") or []
    score_html = ""
    detail = card.get("h2h_detail") or {}
    if detail:
        rec = esc(detail.get("record") or "")
        note = esc(detail.get("note") or "")
        chips = "".join('<span style="display:inline-block;padding:5px 11px;margin:0 8px 8px 0;'
                        'border:1px solid rgba(0,240,120,.45);border-radius:6px;font-weight:800;'
                        'font-family:ui-monospace,Consolas,monospace;font-size:19px">%s</span>' % esc(x)
                        for x in (detail.get("scores") or []))
        score_html = ('<div class="sh"><span class="n">历史交锋</span><span class="h">%s</span></div>' % rec +
                      ('<div style="margin-top:6px">%s</div>' % chips if chips else '') +
                      ('<div class="narr" style="margin-top:4px">%s</div>' % note if note else ''))
    elif scores:
        chips = "".join('<span style="display:inline-block;padding:5px 11px;margin:0 8px 8px 0;'
                        'border:1px solid rgba(0,240,120,.45);border-radius:6px;font-weight:800;'
                        'font-family:ui-monospace,Consolas,monospace;font-size:%dpx">%s</span>'
                        % (int(20 * (card.get("_fs") or 1.15)), esc(x)) for x in scores)
        score_html = ('<div class="sh"><span class="n">历史交锋比分</span><span class="h">近 %d 次</span></div>'
                      '<div style="margin-top:6px">%s</div>' % (len(scores), chips))
    if not detail and not scores:
        score_html = ('<div class="sh"><span class="n">读数口径</span><span class="h">只说明数据怎么来的</span></div>'
                      '<div class="narr" style="margin-top:6px">'
                      '・场均进/失取近 5 场同主客；・交锋取最近 5 次同主客；'
                      '・比分格为历史频次，只上色不标数字；・全部 90 分钟口径，加时与点球不计。</div>')
    if pie_inner:
        pie_inner = '<div class="pie">' + pie_inner + '</div>'
    h2h_left = ""
    if detail:
        _chips = ""
        if os.environ.get("XHS_SHOW_H2H_SCORES") == "1":
            _chips = "".join('<span style="display:inline-block;padding:4px 9px;margin:0 6px 6px 0;'
                             'border:1px solid rgba(0,240,120,.45);border-radius:6px;font-weight:800;'
                             'font-family:ui-monospace,Consolas,monospace;font-size:19px">%s</span>' % esc(x)
                             for x in (detail.get("scores") or []))
        elif detail.get("note"):
            _chips = ('<div style="font-size:15px;color:#B8C7D9;background:rgba(255,255,255,.04);'
                      'border-left:3px solid #00F078;padding:6px 10px;border-radius:4px">%s</div>'
                      % esc(detail.get("note")))
        st = card.get("h2h_stats") or {}
        kpi = ""
        if st:
            kpi = ('<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px">'
                   + "".join('<div style="background:rgba(0,240,120,.08);border:1px solid rgba(0,240,120,.28);'
                             'border-radius:8px;padding:8px 10px;text-align:center">'
                             '<div style="font-family:ui-monospace,Consolas,monospace;font-size:22px;'
                             'font-weight:900;color:#00F078">%s</div>'
                             '<div style="font-size:14px;color:#9FB2C8;margin-top:2px">%s</div></div>' % (v, k)
                             for k, v in (("交锋场次", st.get("n") or "—"), ("平局占比", "%s%%" % (st.get("draw") if st.get("draw") not in (None, "") else "—")),
                                          ("≤2球占比", "%s%%" % (st.get("low") if st.get("low") not in (None, "") else "—"))))
                   + '</div>')
        _pois = pois_bars(card)
        pois_html = ""
        if _pois:
            pois_html = ('<div class="sh" style="margin-top:12px"><span class="n">单队进球分布</span>'
                         '<span class="h">绿＝主队 / 红＝客队 0~4 球占比</span></div>'
                         '<div class="pois" style="margin-top:4px">' + _pois + '</div>')
        h2h_left = ('<div class="sh"><span class="n">历史交锋</span><span class="h">%s</span></div>' %
                    esc(detail.get("record") or "") +
                    ('<div style="margin-top:4px">%s</div>' % _chips if _chips else '') +
                    kpi + pois_html)
        score_html = ""
    left_col = pie_inner or h2h_left or quick_cells
    if left_col or heat_html.strip():
        title = (card.get("pie_title") or "").strip()
        head = ""
        if title:
            head = ('<div class="sh"><span class="n">' + esc(title) + '</span><span class="h">' +
                    esc(card.get("pie_note") or "") + (' · 只上色不标数字' if heat_html.strip() else '') +
                    '</span></div>')
        pie_sec = ('<section class="sec">' + head +
                   '<div class="two c2b"><div>' + left_col + '</div>' + heat_html + '</div>' + score_html + '</section>')
    else:
        pie_sec = ""
    extra_css = "" if value_block(card) else ("<style>.card .sec{margin-top:16px}.heat .cell{height:54px}.ic2{grid-column:1 / -1}"
                                              ".ic2{display:grid;grid-template-columns:1fr 1fr;gap:16px;width:100%}</style>")
    vb = value_block(card)
    val_sec = ('<section class="sec"><div class="sh"><span class="n">身价对标</span>'
               '<span class="h">2026 年 10 月估值</span></div>' + vb + "</section>") if vb else ""
    def _hdr(name, f):
        if not (f.get("seq") or f.get("l5")):
            return ""
        return ('<div class="fr"><div class="l"><span class="nm">' + name + '</span>'
                '<span class="badges">' + badges(f.get("seq")) + '</span></div>'
                '<span class="r">' + esc(f.get("l5")) + '</span></div>')

    hdr_home, hdr_away = "", ""   # 兼容：原卡片头块已废弃，留空占位

    inj_hint = ""
    _src = locals().get("card")
    if not isinstance(_src, dict):
        _lst = locals().get("ms") or []
        _src = _lst[0] if _lst and isinstance(_lst[0], dict) else {}
    for line in ((_src.get("intel") or {}).get("common") or []):
        m = re.search(r"伤停[：:]?\s*(\d+)\s*人", str(line))
        if m:
            inj_hint = "%s 人" % m.group(1)
            break
    if not inj_hint:
        inj_hint = "未公布"

    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>{extra_css}<div class="card">
<div class="frame"><i class="tl"></i><i class="tr"></i><i class="bl"></i><i class="br"></i></div>
<div class="top"><span class="lg">» {league}</span><span class="md">// MATCH DATA CARD</span>
<span>{esc(card.get("kick"))}</span><span class="bd">@阿飞·赛博聊球</span></div>
<h1>{home}<span class="vs">vs</span>{away}</h1>

{val_sec}

<section class="sec"><div class="sh"><span class="n">数据对照 · 六维</span>
<span class="h">近 5 场 · {esc(h2h_line)}</span></div>
<div class="two c2b stretch{nr}">
  <div>
    {hdr_home}
    {hdr_away}
    <div class="cmp">{cmp_rows(card)}</div>
  </div>
  {radblock}
</div></section>

{pie_sec}

<section class="sec"><div class="sh"><span class="n">情报整理</span><span class="h">近期 · 交锋 · 伤停 {inj_hint}</span></div>
<div class="intel">{intel_block(card)}</div></section>

<section class="sec"><div class="sh"><span class="n">核心矛盾与看点</span><span class="h">已发生数据 + 观察点</span></div>
<div class="two c1b" style="margin-top:6px">
  <div class="narr"><b>核心矛盾</b>{narr}</div>
  <div>{pt_html or '<div class="narr">—</div>'}</div>
</div></section>

<div class="foot2" style="margin-top:auto"><span>公开赛事数据整理 · 个人观察</span>
<span>仅供交流参考，不构成任何购买建议，请理性看待比赛</span></div>
</div></body></html>"""


def shot(html_path: Path, png_path: Path, size=None, scale=2) -> bool:
    png_path = png_path.resolve()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    chrome = os.environ.get("CHROME") or r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
           "--virtual-time-budget=1200", "--force-device-scale-factor=%d" % scale,
           "--window-size=%d,%d" % (size or (W, H)), "--screenshot=%s" % png_path,
           html_path.resolve().as_uri()]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    except Exception:  # noqa: BLE001
        return False
    return png_path.exists()


COVER_CSS = """
.cov{padding:0 0 10px 0;width:100%;flex:1;display:flex;flex-direction:column;text-align:left;justify-content:space-between}
.top{width:100%}
.cov .eyebrow{margin-top:14px;font-size:19px;letter-spacing:.26em;color:#0a768f;font-weight:800}
.cov .date{display:flex;align-items:baseline;gap:18px;margin-top:20px}
.cov .date b{font-family:var(--mono);font-size:182px;line-height:.94;font-weight:800;color:#0b1b23;letter-spacing:-.03em}
.cov .date span{font-size:66px;font-weight:900;color:#0a768f;letter-spacing:.04em}
.cov .k1{margin-top:6px;font-size:200px;line-height:1;font-weight:900;color:#b8331f;letter-spacing:.12em}
.cov .k2{margin-top:10px;font-size:84px;line-height:1.05;font-weight:900;color:#0b1b23;letter-spacing:.02em}
.cov .k2 i{display:inline-block;width:14px;height:52px;background:#0a768f;margin-right:18px;vertical-align:-6px}
.cov .rule{height:5px;margin:20px 0 0;background:linear-gradient(90deg,#0a768f,#0a768f 46%,#e8402a 46%,#e8402a)}
.cov .pts{margin-top:26px;display:grid;gap:30px}
.cov .pt2{background:#fff;border-left:5px solid #0a768f;padding:14px 18px}
.cov .pt2 b{display:inline-block;font-size:33px;font-family:var(--mono);color:#b8331f;font-weight:800;
  line-height:1.1;margin-right:10px}
.cov .pt2 span{display:inline;font-size:22px;color:#2a3c48;line-height:1.45}
.cov .pt2:nth-child(even){border-left-color:#e8402a}
.cov .lgline{margin-top:16px;font-size:26px;line-height:1.35;letter-spacing:.06em;color:#0a768f;font-weight:800}
.cov .chips{margin-top:26px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.cov .chip{border-top:4px solid #c02a2a;background:rgba(255,255,255,.82);padding:18px 16px 16px}
.cov .chip b{display:block;font-size:46px;line-height:1.05;font-weight:900;color:#0b1b23}
.cov .chip span{display:block;margin-top:6px;font-size:22px;letter-spacing:.05em;color:#0a768f;font-weight:700}
.cov .lgline2{margin-top:14px;font-size:23px;letter-spacing:.04em;color:#5a7180;font-weight:700}
.cov .tags3{margin-top:0;font-size:62px;line-height:1.2;font-weight:900;color:rgba(11,27,35,.13);letter-spacing:.02em;white-space:nowrap}
.cov .tags3 i{font-style:normal;color:rgba(184,51,31,.22);margin:0 6px}
.cov .en{margin-top:2px;margin-bottom:4px;font-family:var(--mono);font-size:17px;letter-spacing:.22em;color:rgba(11,27,35,.42)}
.cov .fill{display:none}
.foot2{width:100%;padding-top:10px;display:flex;justify-content:space-between;align-items:flex-end;
  font-size:18px;color:#5b7280}
"""


def cover_html(data: dict) -> str:
    """封面固定模板（2026-10-22 定）：只留品牌 + 日期 + 前瞻 + 三个固定槽位。

    固定不变的：顶栏（足球·赛程 / DATA CARD / @阿飞·赛博聊球）、日期块、主标题「前瞻」、
    品牌行「阿飞·赛博聊球」、三格 KPI（场数 / 时段数 / 0 处主观结论）、幽灵字与页脚。
    每日只换：日期、星期、联赛清单、KPI 数字（槽位位置与字号永不变，避免版式漂移）。
    """
    ms = data.get("matches") or []
    meta = data.get("meta") or {}
    m_date = meta.get("date") or "10.22"
    m_wd = meta.get("weekday") or "星期四"
    m_lg = meta.get("leagues") or "足球 · 赛程"
    m_kd = meta.get("kick_day") or "%s 开赛" % m_date.replace(".", "/")
    m_tail = meta.get("tail") or "%d 场，先看账，再看球" % len(ms)
    m_tags = meta.get("tags") or ["交锋状态", "伤停情报", "账面反差"]
    m_en = meta.get("en") or "SCHEDULE · GOALS · INJURY · LAST 10 MATCHES"
    slots = list(meta.get("kick_slots") or [])
    if not slots:
        seen = []
        for m in ms:
            t = (m.get("kick") or "").split()
            t = t[-1] if t else ""
            if t and t not in seen:
                seen.append(t)
        slots = sorted(seen)
    n_slot = len(slots)
    chips = [("%d 场" % len(ms), "一张卡一场"),
             ("%d 段" % n_slot, "开球时段"),
             ("0 处", "方向与结论")]
    chip_html = "".join(
        '<div class="chip"><b>%s</b><span>%s</span></div>' % (esc(a), esc(b)) for a, b in chips)
    tags3 = "<i>·</i>".join(esc(t) for t in m_tags)
    def _hdr(name, f):
        if not (f.get("seq") or f.get("l5")):
            return ""
        return ('<div class="fr"><div class="l"><span class="nm">' + name + '</span>'
                '<span class="badges">' + badges(f.get("seq")) + '</span></div>'
                '<span class="r">' + esc(f.get("l5")) + '</span></div>')

    hdr_home, hdr_away = "", ""   # 兼容：原卡片头块已废弃，留空占位

    inj_hint = ""
    _src = locals().get("card")
    if not isinstance(_src, dict):
        _lst = locals().get("ms") or []
        _src = _lst[0] if _lst and isinstance(_lst[0], dict) else {}
    for line in ((_src.get("intel") or {}).get("common") or []):
        m = re.search(r"伤停[：:]?\s*(\d+)\s*人", str(line))
        if m:
            inj_hint = "%s 人" % m.group(1)
            break
    if not inj_hint:
        inj_hint = "未公布"

    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>{CSS}{COVER_CSS}</style></head>
<body>{extra_css}<div class="card">
<div class="frame"><i class="tl"></i><i class="tr"></i><i class="bl"></i><i class="br"></i></div>
<div class="top"><span class="lg">» 足球 · 赛程</span><span class="md">// DATA CARD · {len(ms)}</span>
<span>@{esc(m_date and '阿飞·赛博聊球')}</span></div>
<div class="cov">
  <div class="date"><b>{esc(m_date)}</b><span>{esc(m_wd)}</span></div>
  <div class="k1">前瞻</div>
  <div class="k2"><i></i>阿飞·赛博聊球</div>
  <div class="rule"></div>
  <div class="chips">{chip_html}</div>
  <div class="lgline">{esc(m_lg)}</div>
  <div class="lgline2">{esc(m_kd)}</div>
  <div class="fill"></div>
  <div class="tags3">{tags3}</div>
  <div class="en">{esc(m_en)}</div>
</div>
<div class="foot2"><span>数据来源：公开赛事数据 · 官方赛程 · 联赛积分与主客场进失球</span><span>{esc(m_tail)}</span></div>
</div></body></html>"""


# ============ 深色赛博封面（2026-10-22 定稿 · 用户提案版） ============
DARK_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#0B0F19}
body{width:var(--bw,1080px);height:var(--bh,1440px);overflow:hidden;font-family:"Noto Sans SC","Microsoft YaHei",sans-serif}
.dk{position:relative;width:1080px;height:1440px;padding:56px 64px 48px;display:flex;flex-direction:column;
    background:
      linear-gradient(180deg,rgba(0,255,102,.05),transparent 38%),
      repeating-linear-gradient(0deg,rgba(255,255,255,.045) 0 1px,transparent 1px 48px),
      repeating-linear-gradient(90deg,rgba(255,255,255,.045) 0 1px,transparent 1px 48px),
      #0B0F19}
.dk .frame{position:absolute;inset:22px;border:1px solid rgba(0,255,102,.18);pointer-events:none}
.dk .top{display:flex;justify-content:space-between;align-items:center;font-size:20px;letter-spacing:.16em;
         color:#8A99AD;font-weight:700;text-transform:uppercase}
.dk .top b{color:#00FF66;font-weight:800}
.dk .hero{margin-top:86px}
.dk .hero .dt{font-size:196px;line-height:.94;font-weight:900;letter-spacing:-.03em;color:#F2F7FF;
              text-shadow:0 0 42px rgba(0,255,102,.28)}
.dk .hero .dt i{color:#00FF66;font-style:normal}
.dk .hero .wd{margin-top:14px;font-size:44px;font-weight:800;color:#F2F7FF;letter-spacing:.04em}
.dk .hero .wd span{color:#00FF66}
.dk .hero .sub{margin-top:12px;font-size:22px;letter-spacing:.14em;color:#8A99AD;font-weight:600}
.dk .bars{display:flex;gap:10px;margin-top:26px}
.dk .bars i{display:block;height:5px;flex:1;background:#00FF66}
.dk .bars i:nth-child(2){background:rgba(0,255,102,.42)}
.dk .bars i:nth-child(3){background:rgba(0,255,102,.18)}
.dk .caps{margin-top:44px;border:1px solid rgba(0,255,102,.28);border-radius:16px;background:rgba(12,20,32,.86);
          padding:26px 28px;display:grid;gap:18px}
.dk .caps .row{display:flex;align-items:baseline;gap:14px}
.dk .caps .row em{font-style:normal;color:#00FF66;font-size:24px;font-weight:800;letter-spacing:.04em}
.dk .caps .row b{font-size:34px;font-weight:800;color:#EAF2FF;letter-spacing:.02em}
.dk .caps .row span{margin-left:auto;font-size:22px;color:#8A99AD;font-weight:600;letter-spacing:.06em}
.dk .lgrow{margin-top:34px;font-size:23px;line-height:1.5;color:#B9C6D8;font-weight:700;letter-spacing:.06em}
.dk .lgrow i{color:#00FF66;font-style:normal;padding:0 8px}
.dk .grow{flex:1}
.dk .ipbar{display:flex;align-items:center;gap:18px}
.dk .ipbar em{display:block;width:8px;height:58px;background:#00FF66;border-radius:2px}
.dk .ipbar b{font-size:52px;font-weight:900;color:#F2F7FF;letter-spacing:.02em}
.dk .ipbar b i{color:#8A99AD;font-style:normal;font-weight:800}
.dk .foot{display:flex;justify-content:space-between;margin-top:18px;font-size:19px;letter-spacing:.08em;color:#5E6E82;font-weight:600}
"""


def cover_dark_html(data: dict) -> str:
    """深色赛博封面：顶部参数栏 / 日期大标题 / 数据胶囊 / 底部 IP，四块固定。"""
    ms = data.get("matches") or []
    meta = data.get("meta") or {}
    m_date = meta.get("date") or "10.22"
    m_wd = meta.get("weekday") or "星期四"
    m_lg = meta.get("leagues") or "足球 · 赛程"
    m_kd = meta.get("kick_day") or "%s 开赛" % m_date.replace(".", "/")
    m_tail = meta.get("tail") or "%d 场，先看账，再看球" % len(ms)
    slots = list(meta.get("kick_slots") or [])
    if not slots:
        seen = []
        for m in ms:
            t = (m.get("kick") or "").split()
            t = t[-1] if t else ""
            if t and t not in seen:
                seen.append(t)
        slots = sorted(seen)
    lgs = [x.strip() for x in m_lg.replace("·", ",").replace("、", ",").split(",") if x.strip()]
    lg_html = "<i>·</i>".join(esc(x) for x in lgs)
    rows = [("%d" % len(ms), "场硬核拆解", "全景"),
            ("%d" % len(slots), "段开球时段", m_kd),
            ("0", "处主观臆测与结论", "只列已发生")]
    cap = "".join('<div class="row"><em>%s</em><b>%s</b><span>%s</span></div>' % (esc(a), esc(b), esc(c))
                  for a, b, c in rows)
    d1, _, d2 = m_date.partition(".")
    dt = '10<i>.</i>23' if not d2 else '%s<i>.</i>%s' % (d1, d2)
    def _hdr(name, f):
        if not (f.get("seq") or f.get("l5")):
            return ""
        return ('<div class="fr"><div class="l"><span class="nm">' + name + '</span>'
                '<span class="badges">' + badges(f.get("seq")) + '</span></div>'
                '<span class="r">' + esc(f.get("l5")) + '</span></div>')

    hdr_home, hdr_away = "", ""   # 兼容：原卡片头块已废弃，留空占位

    inj_hint = ""
    _src = locals().get("card")
    if not isinstance(_src, dict):
        _lst = locals().get("ms") or []
        _src = _lst[0] if _lst and isinstance(_lst[0], dict) else {}
    for line in ((_src.get("intel") or {}).get("common") or []):
        m = re.search(r"伤停[：:]?\s*(\d+)\s*人", str(line))
        if m:
            inj_hint = "%s 人" % m.group(1)
            break
    if not inj_hint:
        inj_hint = "未公布"

    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>{DARK_CSS}</style></head>
<body><div class="dk">
<div class="frame"></div>
<div class="top"><span><b>{len(ms)}</b> MATCHES // DATA CARD</span><span>阿飞 · 赛博聊球</span></div>
<div class="hero">
  <div class="dt">{dt}</div>
  <div class="wd">星期{esc(m_wd.replace("星期", ""))} <span>赛事前瞻</span></div>
  <div class="sub">数据拆解 · 公开口径 · 不猜结局</div>
  <div class="bars"><i></i><i></i><i></i></div>
</div>
<div class="caps">{cap}</div>
<div class="lgrow">{lg_html}</div>
<div class="grow"></div>
<div class="ipbar"><em></em><b>阿飞 <i>·</i> 赛博聊球</b></div>
<div class="foot"><span>公开赛事数据 · 官方赛程 · 积分与主客场进失球</span><span>{esc(m_tail)}</span></div>
</div></body></html>"""


# ============ 封面 v2.0：赛博数据终端 × 绿茵球场（2026-10-22 定稿） ============
PITCH_SVG = """
<svg class="pitch" viewBox="0 0 960 620" preserveAspectRatio="xMidYMid meet">
  <defs>
    <linearGradient id="gr" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#003D2B" stop-opacity=".30"/>
      <stop offset="1" stop-color="#003D2B" stop-opacity=".58"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2.4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <polygon points="250,10 710,10 930,600 30,600" fill="url(#gr)"/>
  <g fill="none" stroke="#00F078" stroke-width="2.1" opacity=".62" filter="url(#glow)">
    <polygon points="250,10 710,10 930,600 30,600"/>
    <line x1="140" y1="305" x2="820" y2="305"/>
    <ellipse cx="480" cy="305" rx="116" ry="62"/>
    <polygon points="150,470 810,470 930,600 30,600"/>
    <polygon points="198,150 762,150 710,10 250,10"/>
    <polygon points="300,556 660,556 690,600 270,600"/>
    <polygon points="360,60 600,60 570,10 390,10"/>
    <line x1="140" y1="305" x2="140" y2="470"/>
    <line x1="820" y1="305" x2="820" y2="470"/>
  </g>
  <g fill="none" stroke="#9CFFCF" stroke-width="1.5" opacity=".45" filter="url(#glow)">
    <circle cx="480" cy="244" r="46"/>
    <polygon points="480,212 510,234 499,270 461,270 450,234"/>
    <circle cx="480" cy="244" r="15"/>
  </g>
</svg>
"""

V2_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#080D16}
body{width:var(--bw,1080px);height:var(--bh,1440px);overflow:hidden;font-family:"Noto Sans SC","Microsoft YaHei",sans-serif}
.v2{position:relative;width:var(--bw,1080px);height:var(--bh,1440px);padding:50px 62px 42px;display:flex;flex-direction:column;
    background:
      radial-gradient(1200px 520px at 50% -8%,rgba(0,240,120,.13),transparent 62%),
      repeating-linear-gradient(0deg,rgba(255,255,255,.04) 0 1px,transparent 1px 54px),
      repeating-linear-gradient(90deg,rgba(255,255,255,.04) 0 1px,transparent 1px 54px),
      #080D16}
.v2 .frame{position:absolute;inset:20px;border:1px solid rgba(0,240,120,.16);pointer-events:none}
.v2 .top{display:flex;justify-content:space-between;align-items:center;font-size:19px;letter-spacing:.14em;color:#91A2BA;font-weight:700}
.v2 .top b{color:#00F078}
.v2 .hero{margin-top:34px}
.v2 .dt{font-size:158px;line-height:.92;font-weight:900;letter-spacing:-.03em;color:#F0F5FF}
.v2 .dt i{color:#00F078;font-style:normal}
.v2 .wd{margin-top:10px;font-size:40px;font-weight:900;color:#F0F5FF;letter-spacing:.03em}
.v2 .wd em{font-style:normal;color:#00F078}
.v2 .stat{margin-top:10px;font-size:24px;font-weight:700;color:#91A2BA;letter-spacing:.06em}
.v2 .stat b{color:#F0F5FF}
.v2 .sub{margin-top:8px;font-size:21px;font-weight:700;color:#5E9F84;letter-spacing:.12em}
.v2 .bars{display:flex;gap:9px;margin-top:18px}
.v2 .bars i{flex:1;height:4px;background:#00F078}
.v2 .bars i:nth-child(2){background:rgba(0,240,120,.42)}
.v2 .bars i:nth-child(3){background:rgba(0,240,120,.16)}
.v2 .stage{position:relative;margin-top:16px;flex:1;min-height:0}
.v2 .stage .pitch{position:absolute;left:50%;top:50%;transform:translate(-50%,-52%);width:100%;max-height:100%}
.v2 .kpi{position:relative;display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin-top:18px;
         border:1px solid rgba(0,240,120,.2);border-radius:12px;background:rgba(10,18,28,.72)}
.v2 .kpi div{padding:16px 20px;border-right:1px solid rgba(0,240,120,.14)}
.v2 .kpi div:last-child{border-right:0}
.v2 .kpi b{display:block;font-size:40px;font-weight:900;color:#00F078;line-height:1}
.v2 .kpi b i{font-size:22px;font-style:normal;color:#91A2BA;font-weight:700;margin-left:6px}
.v2 .kpi span{display:block;margin-top:7px;font-size:20px;color:#C6D4E6;font-weight:700;letter-spacing:.04em}
.v2 .lg{margin-top:16px;font-size:21px;line-height:1.45;color:#7E90A8;font-weight:700;letter-spacing:.05em}
.v2 .ipbar{display:flex;align-items:center;gap:16px;margin-top:16px}
.v2 .ipbar em{display:block;width:7px;height:50px;background:#00F078;border-radius:2px}
.v2 .ipbar b{font-size:46px;font-weight:900;color:#F0F5FF;letter-spacing:.02em}
.v2 .ipbar b i{color:#91A2BA;font-style:normal}
.v2 .ipbar span{margin-left:auto;font-size:20px;color:#91A2BA;font-weight:700;letter-spacing:.08em}
.v2.wide{width:1920px;height:1080px;padding:44px 72px 40px}
.v2.wide .hero{margin-top:26px}
.v2.wide .dt{font-size:150px}
.v2.wide .stage{position:absolute;right:60px;top:118px;width:920px;height:690px;margin:0}
.v2.wide .stage .pitch{left:0;top:0;transform:none;width:920px}
.v2.wide .bars{width:600px}
.v2.wide .kpi{position:absolute;left:72px;bottom:214px;width:840px}
.v2.wide .lg{position:absolute;left:72px;bottom:160px;width:900px;font-size:18px;white-space:nowrap}
.v2.wide .ipbar{position:absolute;left:72px;bottom:74px;width:900px}
.v2.wide .foot{position:absolute;left:72px;right:72px;bottom:18px;margin-top:0}
.v2 .foot{display:flex;justify-content:space-between;margin-top:14px;font-size:18px;letter-spacing:.07em;color:#4E5E72;font-weight:600}
"""


def cover_v2_html(data: dict, wide: bool = False) -> str:
    """封面 v2.0：赛博数据终端 × 俯视绿茵球场。全部字段由 cards.json 驱动。"""
    ms = data.get("matches") or []
    meta = data.get("meta") or {}
    m_date = meta.get("date") or "10.22"
    m_wd = (meta.get("weekday") or "星期四").replace("星期", "").replace("周", "")
    m_kd = meta.get("kick_day") or "%s 开赛" % m_date.replace(".", "/")
    m_tail = meta.get("tail") or "%d 场，先看账，再看球" % len(ms)
    n = len(ms)
    lgs = []
    for m in ms:
        lg = (m.get("league") or "").strip()
        if lg and lg not in lgs:
            lgs.append(lg)
    slots = []
    for m in ms:
        t = (m.get("kick") or "").split()
        t = t[-1] if t else ""
        if t and t not in slots:
            slots.append(t)
    d1, _, d2 = m_date.partition(".")
    dt = "%s<i>.</i>%s" % (d1, d2) if d2 else m_date
    bw, bh = (1920, 1080) if wide else (1080, 1440)
    cells = [(str(n), "场", "赛事拆解"), (str(len(slots)), "段", "开球时段"), (str(len(lgs)), "项", "联赛覆盖")]
    kpi = "".join('<div><b>%s<i>%s</i></b><span>%s</span></div>' % c for c in cells)
    lg_html = " <i>·</i> ".join(esc(x) for x in lgs)
    lg_top = esc(" · ".join(lgs[:3])) + (" 等 %d 项联赛" % len(lgs) if len(lgs) > 3 else "")
    cls = "v2 wide" if wide else "v2"
    def _hdr(name, f):
        if not (f.get("seq") or f.get("l5")):
            return ""
        return ('<div class="fr"><div class="l"><span class="nm">' + name + '</span>'
                '<span class="badges">' + badges(f.get("seq")) + '</span></div>'
                '<span class="r">' + esc(f.get("l5")) + '</span></div>')

    hdr_home, hdr_away = "", ""   # 兼容：原卡片头块已废弃，留空占位

    inj_hint = ""
    _src = locals().get("card")
    if not isinstance(_src, dict):
        _lst = locals().get("ms") or []
        _src = _lst[0] if _lst and isinstance(_lst[0], dict) else {}
    for line in ((_src.get("intel") or {}).get("common") or []):
        m = re.search(r"伤停[：:]?\s*(\d+)\s*人", str(line))
        if m:
            inj_hint = "%s 人" % m.group(1)
            break
    if not inj_hint:
        inj_hint = "未公布"

    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>:root{{--bw:{bw}px;--bh:{bh}px}}{V2_CSS}</style></head>
<body><div class="{cls}">
<div class="frame"></div>
<div class="top"><span><b>{n}</b> MATCHES // DATA CARD</span><span>@阿飞·赛博聊球</span></div>
<div class="hero">
  <div class="dt">{dt}</div>
  <div class="wd">星期{m_wd} <em>｜足球赛事前瞻</em></div>
  <div class="stat"><b>{n} 场赛事</b> · <b>{len(slots)} 个开球时段</b> · {esc(m_kd)}</div>
  <div class="sub">公开数据 · 近期表现 · 数据观察</div>
  <div class="bars"><i></i><i></i><i></i></div>
</div>
<div class="stage">{PITCH_SVG}</div>
<div class="kpi">{kpi}</div>
<div class="lg">{lg_html}</div>
<div class="ipbar"><em></em><b>阿飞 <i>·</i> 赛博聊球</b><span>用数据拆解比赛</span></div>
<div class="foot"><span>公开赛事数据 · 官方赛程 · 积分与主客场进失球</span><span>{esc(m_tail)}</span></div>
</div></body></html>"""


# ============ 封面 v3.0：场数进主标题 + 右侧竖排数据卡（2026-10-23 定） ============
ICON_BALL = '<svg viewBox="0 0 48 48" fill="none" stroke="#00F078" stroke-width="2.2"><circle cx="24" cy="24" r="17"/><polygon points="24,12 33,18 30,29 18,29 15,18" stroke-linejoin="round"/></svg>'
ICON_CLOCK = '<svg viewBox="0 0 48 48" fill="none" stroke="#00F078" stroke-width="2.2"><circle cx="24" cy="24" r="17"/><path d="M24 14v10l7 5"/></svg>'
ICON_LAYER = '<svg viewBox="0 0 48 48" fill="none" stroke="#00F078" stroke-width="2.2"><path d="M24 10 40 18 24 26 8 18z"/><path d="M8 26 24 34 40 26"/><path d="M8 32 24 40 40 32"/></svg>'

V3_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#050B12}
body{width:var(--bw,1080px);height:var(--bh,1440px);overflow:hidden;font-family:"Noto Sans SC","Microsoft YaHei",sans-serif}
.v3{position:relative;width:var(--bw,1080px);height:var(--bh,1440px);overflow:hidden;
    background:
      radial-gradient(900px 460px at 18% 4%,rgba(0,240,120,.14),transparent 60%),
      radial-gradient(700px 500px at 88% 22%,rgba(0,140,255,.10),transparent 62%),
      repeating-linear-gradient(0deg,rgba(255,255,255,.035) 0 1px,transparent 1px 54px),
      repeating-linear-gradient(90deg,rgba(255,255,255,.035) 0 1px,transparent 1px 54px),
      #050B12}
.v3 .frame{position:absolute;inset:18px;border:1px solid rgba(0,240,120,.14)}
.v3 .top{position:absolute;left:62px;right:62px;top:44px;display:flex;justify-content:space-between;
         font-size:19px;letter-spacing:.14em;color:#8FA2B8;font-weight:700}
.v3 .top b{color:#00F078}
.v3 .date{position:absolute;left:62px;top:100px}
.v3 .date b{display:block;font-size:126px;line-height:.88;font-weight:900;color:#F2F7FF;letter-spacing:-.03em}
.v3 .date b i{color:#00F078;font-style:normal}
.v3 .date span{display:block;margin-top:12px;font-size:25px;font-weight:800;color:#9FB2C8;letter-spacing:.05em}
.v3 .title{position:absolute;left:62px;top:300px;font-size:84px;line-height:1.1;font-weight:900;color:#F2F7FF;letter-spacing:-.01em}
.v3 .title em{font-style:normal;color:#00F078}
.v3 .stat{position:absolute;left:62px;top:512px;font-size:25px;font-weight:700;color:#A9BACE;letter-spacing:.04em}
.v3 .stat b{color:#F2F7FF}
.v3 .slogan{position:absolute;left:62px;top:558px;font-size:22px;font-weight:800;color:#5EAF8C;letter-spacing:.14em}
.v3 .kpiR{position:absolute;right:62px;top:104px;width:306px;display:grid;gap:14px}
.v3 .kcard{position:relative;border:1px solid rgba(0,240,120,.26);border-radius:14px;background:rgba(8,16,24,.78);
           padding:16px 18px;display:flex;align-items:center;gap:12px}
.v3 .kcard b{font-size:52px;font-weight:900;color:#00F078;line-height:1}
.v3 .kcard b i{font-size:22px;font-style:normal;color:#9FB2C8;font-weight:700;margin-left:4px}
.v3 .kcard span{display:block;font-size:20px;color:#C9D6E6;font-weight:700;letter-spacing:.04em;margin-top:4px}
.v3 .kcard .ico{position:absolute;right:14px;top:12px;width:42px;height:42px;opacity:.9}
.v3 .pitchwrap{position:absolute;left:0;right:0;top:600px;height:560px}
.v3 .pitchwrap svg{position:absolute;left:50%;top:0;transform:translateX(-50%);width:920px}
.v3 .divider{position:absolute;left:62px;right:62px;bottom:238px;display:flex;align-items:center;gap:16px;
             font-size:18px;letter-spacing:.2em;color:#5C6E84;font-weight:700}
.v3 .divider i{flex:1;height:1px;background:rgba(0,240,120,.3)}
.v3 .divider u{text-decoration:none;color:#00F078;letter-spacing:.1em}
.v3 .brand{position:absolute;left:62px;bottom:96px;display:flex;align-items:center;gap:16px}
.v3 .brand em{display:block;width:8px;height:56px;background:#00F078;border-radius:2px}
.v3 .brand b{display:block;font-size:50px;font-weight:900;color:#F2F7FF;letter-spacing:.02em}
.v3 .brand b i{color:#8FA2B8;font-style:normal}
.v3 .brand span{display:block;margin-top:6px;font-size:19px;color:#9FB2C8;font-weight:700;letter-spacing:.1em}
.v3.wide .top{top:38px;left:72px;right:72px}
.v3.wide .date{left:72px;top:88px}
.v3.wide .date b{font-size:116px}
.v3.wide .title{left:72px;top:266px;font-size:74px}
.v3.wide .stat{left:72px;top:452px}
.v3.wide .slogan{left:72px;top:494px}
.v3.wide .kpiR{right:auto;left:72px;top:548px;width:840px;display:flex;gap:14px}
.v3.wide .kcard{flex:1;padding:14px 16px}
.v3.wide .kcard b{font-size:46px}
.v3.wide .kcard .ico{width:34px;height:34px;right:12px;top:10px}
.v3.wide .pitchwrap{left:auto;right:16px;top:150px;width:900px;height:620px}
.v3.wide .pitchwrap svg{width:880px}
.v3.wide .divider{display:none}
.v3.wide .brand{left:72px;bottom:96px}
.v3.wide .foot{left:72px;right:72px;bottom:26px}
.v3 .foot{position:absolute;left:62px;right:62px;bottom:36px;display:flex;justify-content:space-between;gap:24px;
          font-size:16px;letter-spacing:.03em;color:#46566A;font-weight:600}
"""


def cover_v3_html(data: dict, wide: bool = False) -> str:
    """封面 v3.0：日期 + 「N 场足球赛事前瞻」主标题 + 右侧三张竖排数据卡 + 球场 + 品牌。"""
    ms = data.get("matches") or []
    meta = data.get("meta") or {}
    m_date = meta.get("date") or "10.22"
    m_wd = (meta.get("weekday") or "星期四").replace("星期", "").replace("周", "")
    m_kd = meta.get("kick_day") or "%s 开赛" % m_date.replace(".", "/")
    m_tail = meta.get("tail") or "%d 场，先看账，再看球" % len(ms)
    n = len(ms)
    lgs = []
    for m in ms:
        lg = (m.get("league") or "").strip()
        if lg and lg not in lgs:
            lgs.append(lg)
    slots = []
    for m in ms:
        t = (m.get("kick") or "").split()
        t = t[-1] if t else ""
        if t and t not in slots:
            slots.append(t)
    d1, _, d2 = m_date.partition(".")
    dt = "%s<i>.</i>%s" % (d1, d2) if d2 else m_date
    bw, bh = (1920, 1080) if wide else (1080, 1440)
    cls = "v3 wide" if wide else "v3"
    cards = [(str(n), "场", "赛事拆解", ICON_BALL),
             (str(len(slots)), "段", "开球时段", ICON_CLOCK),
             (str(len(lgs)), "项", "联赛覆盖", ICON_LAYER)]
    kpi = "".join(
        '<div class="kcard"><div><b>%s<i>%s</i></b><span>%s</span></div><div class="ico">%s</div></div>' % c
        for c in cards)
    lg_line = " · ".join(lgs)
    def _hdr(name, f):
        if not (f.get("seq") or f.get("l5")):
            return ""
        return ('<div class="fr"><div class="l"><span class="nm">' + name + '</span>'
                '<span class="badges">' + badges(f.get("seq")) + '</span></div>'
                '<span class="r">' + esc(f.get("l5")) + '</span></div>')

    hdr_home, hdr_away = "", ""   # 兼容：原卡片头块已废弃，留空占位

    inj_hint = ""
    _src = locals().get("card")
    if not isinstance(_src, dict):
        _lst = locals().get("ms") or []
        _src = _lst[0] if _lst and isinstance(_lst[0], dict) else {}
    for line in ((_src.get("intel") or {}).get("common") or []):
        m = re.search(r"伤停[：:]?\s*(\d+)\s*人", str(line))
        if m:
            inj_hint = "%s 人" % m.group(1)
            break
    if not inj_hint:
        inj_hint = "未公布"

    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>:root{{--bw:{bw}px;--bh:{bh}px}}{V3_CSS}</style></head>
<body><div class="{cls}">
<div class="frame"></div>
<div class="top"><span><b>{n}</b> MATCHES // DATA CARD</span><span>阿飞 · 赛博聊球</span></div>
<div class="date"><b>{dt}</b><span>星期{m_wd} ｜ {esc(m_kd)}</span></div>
<div class="title"><em>{n} 场</em>足球<br>赛事前瞻</div>
<div class="stat"><b>{n} 场赛事</b> · <b>{len(slots)} 个开球时段</b> · <b>{len(lgs)} 项联赛</b></div>
<div class="slogan">公开数据 · 近期表现 · 数据观察</div>
<div class="kpiR">{kpi}</div>
<div class="pitchwrap">{PITCH_SVG}</div>
<div class="divider"><u>FOOTBALL</u><i></i><u>DATA</u><i></i><u>ANALYSIS</u></div>
<div class="brand"><em></em><div><b>阿飞 <i>·</i> 赛博聊球</b><span>用数据拆解比赛</span></div></div>
<div class="foot"><span>{esc(lg_line)}</span><span>{esc(m_tail)}</span></div>
</div></body></html>"""


# ============ 封面 v4.0（赛博战术矩阵海报） & Poster（转播级对阵巨幅海报） ============
def _mini_radar_svg(card: dict, size: int = 108, col_h: str = "#00F078", col_a: str = "#FF5E7E") -> str:
    r = card.get("radar") or {}
    hv = (r.get("home") or [60, 60, 60, 60, 60, 60])[:6]
    av = (r.get("away") or [50, 50, 50, 50, 50, 50])[:6]
    cx = cy = size / 2.0
    rad = size * 0.42
    rings = []
    for k in (0.35, 0.68, 1.0):
        pts = []
        for i in range(6):
            ang = math.radians(-90 + i * 60)
            pts.append(f"{cx + rad * k * math.cos(ang):.1f},{cy + rad * k * math.sin(ang):.1f}")
        rings.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="rgba(160,195,230,{0.16 if k<1 else 0.32})" stroke-width="1"/>')
    axes = []
    for i in range(6):
        ang = math.radians(-90 + i * 60)
        axes.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + rad * math.cos(ang):.1f}" y2="{cy + rad * math.sin(ang):.1f}" stroke="rgba(160,195,230,0.16)" stroke-width="1"/>')

    def _poly(vals, stroke, fill):
        pts = []
        dots = []
        for i, v in enumerate(vals):
            ratio = max(0.12, min(1.0, float(v) / 100.0))
            ang = math.radians(-90 + i * 60)
            px = cx + rad * ratio * math.cos(ang)
            py = cy + rad * ratio * math.sin(ang)
            pts.append(f"{px:.1f},{py:.1f}")
            dots.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.4" fill="{stroke}"/>')
        return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linejoin="round"/>' + "".join(dots)

    return (f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" style="overflow:visible">'
            + "".join(rings) + "".join(axes)
            + _poly(av, col_a, "rgba(255,94,126,0.20)")
            + _poly(hv, col_h, "rgba(0,240,120,0.22)")
            + "</svg>")


def _extract_tag_pair(card: dict) -> tuple:
    narr = str(card.get("narr") or "")
    m = re.search(r"【([^】]+)】", narr)
    if m:
        parts = [p.strip() for p in re.split(r"vs|VS|×|/", m.group(1)) if p.strip()]
        if len(parts) >= 2:
            return parts[0], parts[1]
        return m.group(1), "战术博弈"
    return "主场态势", "客场走势"


V4_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#040811}
body{width:var(--bw,1080px);height:var(--bh,1440px);overflow:hidden;font-family:"Noto Sans SC","Microsoft YaHei",sans-serif;color:#F2F7FF}
.v4{position:relative;width:var(--bw,1080px);height:var(--bh,1440px);overflow:hidden;padding:42px 52px 34px;display:flex;flex-direction:column;
    background:
      radial-gradient(920px 520px at 12% 8%,rgba(0,240,120,.17),transparent 62%),
      radial-gradient(780px 520px at 90% 18%,rgba(0,180,255,.15),transparent 64%),
      radial-gradient(860px 580px at 50% 82%,rgba(255,77,109,.10),transparent 66%),
      repeating-linear-gradient(0deg,rgba(255,255,255,.028) 0 1px,transparent 1px 48px),
      repeating-linear-gradient(90deg,rgba(255,255,255,.028) 0 1px,transparent 1px 48px),
      #040811}
.v4 .hud-frame{position:absolute;inset:16px;border:1px solid rgba(0,240,120,.16);pointer-events:none}
.v4 .hud-frame::before,.v4 .hud-frame::after{content:"";position:absolute;width:28px;height:28px;border-color:#00F078;border-style:solid}
.v4 .hud-frame::before{left:-1px;top:-1px;border-width:3px 0 0 3px}
.v4 .hud-frame::after{right:-1px;bottom:-1px;border-width:0 3px 3px 0}
.v4 .wm{position:absolute;right:36px;top:64px;font-size:158px;font-weight:900;letter-spacing:-.04em;
        color:transparent;-webkit-text-stroke:1.5px rgba(0,240,120,.07);pointer-events:none;line-height:1;font-family:Impact,"Arial Black",sans-serif}
.v4 .bg-pitch{position:absolute;left:50%;bottom:80px;transform:translateX(-50%);width:980px;opacity:.16;pointer-events:none}
.v4 .topbar{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:center;
            padding-bottom:14px;border-bottom:1px solid rgba(0,240,120,.22)}
.v4 .topbar .tl{display:flex;align-items:center;gap:12px;font-size:17px;font-weight:800;letter-spacing:.14em;color:#9FB2C8}
.v4 .topbar .dot{width:10px;height:10px;border-radius:50%;background:#00F078;box-shadow:0 0 12px #00F078}
.v4 .topbar .tr{font-size:18px;font-weight:800;color:#00F078;letter-spacing:.08em;background:rgba(0,240,120,.10);
                border:1px solid rgba(0,240,120,.32);padding:5px 14px;border-radius:999px}
.v4 .hero{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:stretch;gap:24px;margin-top:20px}
.v4 .hero-l{flex:1;display:flex;flex-direction:column;justify-content:space-between}
.v4 .date-row{display:flex;align-items:baseline;gap:18px}
.v4 .date-num{font-size:112px;line-height:.86;font-weight:900;letter-spacing:-.04em;color:#FFFFFF;
              text-shadow:0 6px 28px rgba(0,240,120,.22)}
.v4 .date-num i{color:#00F078;font-style:normal}
.v4 .date-meta{display:flex;flex-direction:column;gap:6px}
.v4 .date-meta .wd{display:inline-block;background:#00F078;color:#041018;font-size:20px;font-weight:900;
                   padding:3px 12px;border-radius:6px;letter-spacing:.06em;width:fit-content}
.v4 .date-meta .kd{font-size:20px;font-weight:700;color:#9FB2C8;letter-spacing:.04em}
.v4 .headline{margin-top:14px}
.v4 .headline .kicker{display:inline-flex;align-items:center;gap:10px;font-size:22px;font-weight:900;color:#00D2FF;
                      letter-spacing:.08em;margin-bottom:6px}
.v4 .headline .kicker::before{content:"";width:18px;height:4px;background:#00D2FF;border-radius:2px}
.v4 .headline h1{margin:0;font-size:62px;line-height:1.08;font-weight:900;letter-spacing:-.01em;color:#F4F8FF}
.v4 .headline h1 em{font-style:normal;background:linear-gradient(90deg,#00F078,#00D2FF);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.v4 .hero-tags{display:flex;gap:10px;margin-top:14px;flex-wrap:wrap}
.v4 .hero-tags span{font-size:17px;font-weight:700;color:#C8D8E8;background:rgba(255,255,255,.05);
                    border:1px solid rgba(255,255,255,.12);padding:6px 14px;border-radius:8px;letter-spacing:.04em}
.v4 .hero-tags span b{color:#00F078}
.v4 .hero-r{width:270px;display:grid;grid-template-rows:repeat(3,1fr);gap:10px}
.v4 .stat-box{position:relative;background:linear-gradient(135deg,rgba(12,24,38,.88),rgba(7,14,24,.92));
              border:1px solid rgba(0,240,120,.28);border-radius:12px;padding:12px 16px;display:flex;align-items:center;justify-content:space-between}
.v4 .stat-box b{font-size:40px;font-weight:900;color:#00F078;line-height:1;font-family:ui-monospace,Consolas,monospace}
.v4 .stat-box b i{font-size:18px;font-style:normal;color:#8FA6C0;margin-left:4px;font-family:"Noto Sans SC",sans-serif}
.v4 .stat-box span{display:block;font-size:16px;font-weight:700;color:#C0D0E2;margin-top:4px;letter-spacing:.04em}
.v4 .stat-box .ico{width:36px;height:36px;opacity:.88}

.v4 .sec-bar{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:center;
             margin:20px 0 12px;padding:8px 14px;background:rgba(0,240,120,.07);border-left:4px solid #00F078;border-radius:0 8px 8px 0}
.v4 .sec-bar .st{font-size:20px;font-weight:900;color:#F2F7FF;letter-spacing:.08em}
.v4 .sec-bar .sh{font-size:16px;font-weight:700;color:#8FA6C0;display:flex;align-items:center;gap:14px}
.v4 .sec-bar .sh i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px}

.v4 .mgrid{position:relative;z-index:2;flex:1;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;gap:16px;min-height:0}
.v4 .mcard{position:relative;background:linear-gradient(160deg,rgba(13,25,40,.92),rgba(7,13,22,.95));
           border:1px solid rgba(0,240,120,.26);border-radius:16px;padding:16px 18px;display:flex;flex-direction:column;justify-content:space-between;
           box-shadow:0 12px 32px rgba(0,0,0,.45);overflow:hidden}
.v4 .mcard::before{content:"";position:absolute;left:0;top:0;right:0;height:3px;
                   background:linear-gradient(90deg,#00F078,#00D2FF 55%,rgba(255,94,126,.8))}
.v4 .mc-top{display:flex;justify-content:space-between;align-items:center;font-size:15px;font-weight:800}
.v4 .mc-lg{color:#00D2FF;background:rgba(0,210,255,.10);border:1px solid rgba(0,210,255,.30);padding:3px 10px;border-radius:6px;letter-spacing:.04em}
.v4 .mc-tm{color:#F2F7FF;font-family:ui-monospace,Consolas,monospace;font-size:17px;background:rgba(255,255,255,.07);padding:3px 10px;border-radius:6px}
.v4 .mc-body{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:8px 0 6px}
.v4 .mc-teams{flex:1;display:flex;flex-direction:column;gap:8px;min-width:0}
.v4 .mc-trow{display:flex;align-items:center;justify-content:space-between;gap:8px}
.v4 .mc-tname{font-size:28px;font-weight:900;color:#FFFFFF;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
              display:flex;align-items:center;gap:8px}
.v4 .mc-tname i{display:inline-block;width:6px;height:24px;border-radius:3px}
.v4 .mc-tstat{font-size:15px;font-weight:800;color:#A8BDD4;font-family:ui-monospace,Consolas,monospace;white-space:nowrap}
.v4 .mc-tstat b{color:#00F078;font-size:18px}
.v4 .mc-tstat.away b{color:#FF6B8B}
.v4 .mc-rad{width:106px;height:106px;flex-shrink:0;display:flex;align-items:center;justify-content:center;
            background:radial-gradient(circle,rgba(0,240,120,.08),transparent 70%);border-radius:50%}
.v4 .mc-bars{display:flex;flex-direction:column;gap:6px;background:rgba(4,9,16,.65);padding:9px 12px;border-radius:10px;border:1px solid rgba(255,255,255,.06)}
.v4 .mc-brow{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:800}
.v4 .mc-brow .bv{width:38px;font-family:ui-monospace,Consolas,monospace;font-size:16px;color:#00F078}
.v4 .mc-brow .bv.r{text-align:right;color:#FF6B8B}
.v4 .mc-brow .blab{width:64px;text-align:center;color:#8FA6C0;font-size:13px}
.v4 .mc-brow .btrack{flex:1;height:7px;background:rgba(255,255,255,.08);border-radius:99px;overflow:hidden;display:flex}
.v4 .mc-brow .btrack i.h{background:linear-gradient(90deg,#00B862,#00F078);height:100%}
.v4 .mc-brow .btrack i.a{background:linear-gradient(90deg,#FF5E7E,#FF2E55);height:100%;margin-left:auto}
.v4 .mc-foot{display:flex;justify-content:space-between;align-items:center;gap:8px;padding-top:6px;border-top:1px dashed rgba(159,178,200,.18);font-size:14px;font-weight:800}
.v4 .mc-tag{color:#00F078;background:rgba(0,240,120,.09);border:1px solid rgba(0,240,120,.24);padding:3px 9px;border-radius:5px;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:65%}
.v4 .mc-h2h{color:#9FB2C8;white-space:nowrap;font-size:13px}

.v4 .botbar{position:relative;z-index:2;margin-top:16px;padding-top:12px;border-top:1px solid rgba(0,240,120,.22);
            display:flex;justify-content:space-between;align-items:center}
.v4 .brand-box{display:flex;align-items:center;gap:14px}
.v4 .brand-box em{display:block;width:7px;height:44px;background:linear-gradient(180deg,#00F078,#00D2FF);border-radius:3px}
.v4 .brand-box b{display:block;font-size:34px;font-weight:900;color:#FFFFFF;letter-spacing:.02em;line-height:1}
.v4 .brand-box b i{color:#00F078;font-style:normal}
.v4 .brand-box span{display:block;margin-top:5px;font-size:15px;font-weight:700;color:#8FA6C0;letter-spacing:.08em}
.v4 .disc{text-align:right;font-size:14px;color:#6E849E;font-weight:600;line-height:1.45}
.v4 .disc b{color:#9FB2C8}

.v4.wide{padding:36px 56px 28px}
.v4.wide .hero{margin-top:12px;align-items:center}
.v4.wide .date-num{font-size:86px}
.v4.wide .headline h1{font-size:46px}
.v4.wide .hero-r{width:580px;grid-template-rows:1fr;grid-template-columns:repeat(3,1fr);gap:12px}
.v4.wide .stat-box{padding:16px 16px}
.v4.wide .stat-box b{font-size:36px;white-space:nowrap}
.v4.wide .stat-box span{white-space:nowrap;font-size:15px}
.v4.wide .mgrid{grid-template-columns:repeat(4,1fr);grid-template-rows:1fr;gap:14px}
.v4.wide .mc-body{flex-direction:column;align-items:stretch}
.v4.wide .mc-rad{margin:2px auto;width:96px;height:96px}
"""


def cover_v4_html(data: dict, wide: bool = False) -> str:
    """封面 v4.0：赛博战术矩阵海报（4 场焦点对阵 + 实时双队六维雷达 + 进失球能量条）。"""
    ms = data.get("matches") or []
    meta = data.get("meta") or {}
    m_date = meta.get("date") or "10.28"
    m_wd = (meta.get("weekday") or "星期三").replace("星期", "").replace("周", "")
    m_kd = meta.get("kick_day") or "%s 赛程" % m_date.replace(".", "/")
    m_tail = meta.get("tail") or "%d 场焦点赛事 · 近期攻防与交锋数据整理" % len(ms)
    n = len(ms)
    lgs = []
    lg_short = []
    for m in ms:
        lg = (m.get("league") or "").strip()
        if lg and lg not in lgs:
            lgs.append(lg)
        s = lg.split("·")[0].strip() if lg else ""
        if s and s not in lg_short:
            lg_short.append(s)
    slots = []
    for m in ms:
        t = (m.get("kick") or "").split()
        t = t[-1] if t else ""
        if t and t not in slots:
            slots.append(t)
    d1, _, d2 = m_date.partition(".")
    dt = "%s<i>.</i>%s" % (d1, d2) if d2 else m_date
    bw, bh = (1920, 1080) if wide else (1080, 1440)
    cls = "v4 wide" if wide else "v4"

    # 统计汇总（交锋场均进球）
    h2h_avgs = [float(((m.get("form") or {}).get("h2h") or {}).get("avg_goals") or 0) for m in ms]
    h2h_avgs = [x for x in h2h_avgs if x > 0]
    avg_all = ("%.2f" % (sum(h2h_avgs) / len(h2h_avgs))) if h2h_avgs else "2.50"

    kpi_items = [
        (str(n), "场", "焦点赛事拆解", ICON_BALL),
        (avg_all, "球", "历史交锋场均", ICON_CLOCK),
        ("6", "维", "攻防雷达建模", ICON_LAYER),
    ]
    kpi_html = "".join(
        '<div class="stat-box"><div><b>%s<i>%s</i></b><span>%s</span></div><div class="ico">%s</div></div>' % c
        for c in kpi_items
    )

    mcards = []
    for idx, c in enumerate(ms[:4], 1):
        fh = (c.get("form") or {}).get("home") or {}
        fa = (c.get("form") or {}).get("away") or {}
        h2 = (c.get("form") or {}).get("h2h") or {}
        hpj, apj = float(fh.get("pj") or 0), float(fa.get("pj") or 0)
        hsj, asj = float(fh.get("sj") or 0), float(fa.get("sj") or 0)
        hz, az = float(fh.get("zero") or 0), float(fa.get("zero") or 0)
        tot_pj = (hpj + apj) or 1.0
        tot_z = (hz + az) or 1.0
        w_pj_h = max(12.0, min(88.0, 100.0 * hpj / tot_pj))
        w_z_h = max(12.0, min(88.0, 100.0 * hz / tot_z)) if (hz + az) > 0 else 50.0
        t1, t2 = _extract_tag_pair(c)
        rad_svg = _mini_radar_svg(c, size=104)
        h2h_txt = "交锋 %s 场 · 场均 %s 球" % (h2.get("n") or "—", h2.get("avg_goals") or "—")
        mcards.append(f"""
        <div class="mcard">
          <div class="mc-top">
            <span class="mc-lg">0{idx} · {esc(c.get("league") or "")}</span>
            <span class="mc-tm">KICKOFF {esc(c.get("kick") or "")}</span>
          </div>
          <div class="mc-body">
            <div class="mc-teams">
              <div class="mc-trow">
                <span class="mc-tname"><i style="background:#00F078"></i>{esc(c.get("home") or "")}</span>
                <span class="mc-tstat">场均 <b>{hpj:.2f}</b> 球</span>
              </div>
              <div class="mc-trow">
                <span class="mc-tname"><i style="background:#FF5E7E"></i>{esc(c.get("away") or "")}</span>
                <span class="mc-tstat away">场均 <b>{apj:.2f}</b> 球</span>
              </div>
            </div>
            <div class="mc-rad">{rad_svg}</div>
          </div>
          <div class="mc-bars">
            <div class="mc-brow">
              <span class="bv">{hpj:.2f}</span>
              <div class="btrack"><i class="h" style="width:{w_pj_h:.1f}%"></i><i class="a" style="width:{100-w_pj_h:.1f}%"></i></div>
              <span class="blab">近5场进球</span>
              <span class="bv r">{apj:.2f}</span>
            </div>
            <div class="mc-brow">
              <span class="bv">{hsj:.2f}</span>
              <div class="btrack"><i class="h" style="width:{w_z_h:.1f}%"></i><i class="a" style="width:{100-w_z_h:.1f}%"></i></div>
              <span class="blab">场均失球</span>
              <span class="bv r">{asj:.2f}</span>
            </div>
          </div>
          <div class="mc-foot">
            <span class="mc-tag">▸ {esc(t1)} × {esc(t2)}</span>
            <span class="mc-h2h">{esc(h2h_txt)}</span>
          </div>
        </div>""")

    lg_kicker = " × ".join(lg_short) if lg_short else "五大联赛"
    lg_line = " · ".join(lgs)
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>:root{{--bw:{bw}px;--bh:{bh}px}}{V4_CSS}</style></head>
<body><div class="{cls}">
  <div class="hud-frame"></div>
  <div class="wm">MATCHDAY</div>
  <div class="bg-pitch">{PITCH_SVG}</div>
  <div class="topbar">
    <div class="tl"><span class="dot"></span><span>MATCHDAY TACTICAL DOSSIER // 90-MIN REGULAR TIME</span></div>
    <div class="tr">@阿飞·赛博聊球</div>
  </div>
  <div class="hero">
    <div class="hero-l">
      <div class="date-row">
        <div class="date-num">{dt}</div>
        <div class="date-meta">
          <span class="wd">星期{m_wd} · 赛前档案</span>
          <span class="kd">{esc(m_kd)} ｜ {len(slots)} 个开球时段</span>
        </div>
      </div>
      <div class="headline">
        <div class="kicker">{esc(lg_kicker)} · 焦点对阵全维拆解</div>
        <h1><em>{n} 场</em>足球赛事<br>数据前瞻海报</h1>
      </div>
      <div class="hero-tags">
        <span><b>01</b> 近 5 场同主客进失球</span>
        <span><b>02</b> 6 维攻防能力雷达</span>
        <span><b>03</b> 过往交锋与进球区间热图</span>
      </div>
    </div>
    <div class="hero-r">{kpi_html}</div>
  </div>
  <div class="sec-bar">
    <span class="st">» 当日焦点对阵矩阵 · TACTICAL MATCHUP MATRIX</span>
    <span class="sh"><span><i style="background:#00F078"></i>主队近况与雷达</span><span><i style="background:#FF5E7E"></i>客队近况与雷达</span></span>
  </div>
  <div class="mgrid">{"".join(mcards)}</div>
  <div class="botbar">
    <div class="brand-box">
      <em></em>
      <div><b>阿飞 <i>·</i> 赛博聊球</b><span>用客观数据拆解每一场比赛 · 左滑查看单场深挖卡 »</span></div>
    </div>
    <div class="disc">
      <div><b>{esc(lg_line)}</b></div>
      <div>{esc(m_tail)} · 仅供战术交流</div>
    </div>
  </div>
</div></body></html>"""


POSTER_RADAR_SPEC = {
    3: (308, 258, 82.0, 12.5),
    4: (304, 216, 78.0, 12.5),
    5: (284, 162, 60.0, 11.5),
    6: (268, 132, 48.0, 10.5),
}


def _poster_radar_svg(
    card: dict,
    w: int = 304,
    h: int = 216,
    rad: float = 78.0,
    fs: float = 12.5,
    col_h: str = "#00F5D4",
    col_a: str = "#FF5E7E",
) -> str:
    """自适应全尺寸六维雷达图（支持 3/4/5/6 场模板，含 6 轴名称与主客双队实时分值对照）。"""
    r = card.get("radar") or {}
    hv = [int(round(float(x))) for x in (r.get("home") or [60, 60, 60, 60, 60, 60])[:6]]
    av = [int(round(float(x))) for x in (r.get("away") or [50, 50, 50, 50, 50, 50])[:6]]
    short_dims = ["进攻", "防守", "零封", "稳定", "净胜", "开局"]
    cx, cy = w / 2.0, h / 2.0

    rings = []
    for k in (0.25, 0.50, 0.75, 1.0):
        pts = []
        for i in range(6):
            ang = math.radians(-90 + i * 60)
            pts.append(f"{cx + rad * k * math.cos(ang):.1f},{cy + rad * k * math.sin(ang):.1f}")
        stroke_col = "rgba(212,255,0,0.34)" if k == 1.0 else "rgba(160,195,230,0.16)"
        dash = "" if k == 1.0 else ' stroke-dasharray="3,2"'
        rings.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="{stroke_col}" stroke-width="{1.3 if k==1.0 else 1}"{dash}/>')

    axes = []
    for i in range(6):
        ang = math.radians(-90 + i * 60)
        axes.append(
            f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + rad * math.cos(ang):.1f}" '
            f'y2="{cy + rad * math.sin(ang):.1f}" stroke="rgba(160,195,230,0.20)" stroke-width="1"/>'
        )

    def _poly(vals, stroke, fill, r_dot):
        pts, dots = [], []
        for i, v in enumerate(vals):
            ratio = max(0.14, min(1.0, float(v) / 100.0))
            ang = math.radians(-90 + i * 60)
            px = cx + rad * ratio * math.cos(ang)
            py = cy + rad * ratio * math.sin(ang)
            pts.append(f"{px:.1f},{py:.1f}")
            dots.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_dot}" fill="{stroke}" stroke="#070912" stroke-width="1"/>')
        return (
            f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="2.4" stroke-linejoin="round"/>'
            + "".join(dots)
        )

    top_off = max(8.5, fs * 0.95)
    bot_off = max(13.5, fs * 1.48)
    side_off = 8.0
    label_pos = [
        (cx, cy - rad - top_off, "middle"),                      # 0: 顶 (进攻)
        (cx + rad * 0.866 + side_off, cy - rad * 0.5 + 3, "start"),  # 1: 右上 (防守)
        (cx + rad * 0.866 + side_off, cy + rad * 0.5 + 5, "start"),  # 2: 右下 (零封)
        (cx, cy + rad + bot_off, "middle"),                      # 3: 底 (稳定)
        (cx - rad * 0.866 - side_off, cy + rad * 0.5 + 5, "end"),    # 4: 左下 (净胜)
        (cx - rad * 0.866 - side_off, cy - rad * 0.5 + 3, "end"),    # 5: 左上 (开局)
    ]
    labels = []
    for i in range(6):
        lx, ly, anchor = label_pos[i]
        d_txt = short_dims[i]
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'font-size="{fs}" font-weight="900" font-family="Noto Sans SC,Microsoft YaHei,sans-serif" fill="#DCE8F8">'
            f'{d_txt} <tspan fill="{col_h}" font-family="ui-monospace,Consolas,monospace">{hv[i]}</tspan>'
            f'<tspan fill="#6E829A">/</tspan>'
            f'<tspan fill="{col_a}" font-family="ui-monospace,Consolas,monospace">{av[i]}</tspan></text>'
        )

    return (
        f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" style="overflow:visible">'
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rad:.1f}" fill="rgba(0,245,212,0.035)"/>'
        + "".join(rings)
        + "".join(axes)
        + _poly(av, col_a, "rgba(255,94,126,0.22)", 3.0)
        + _poly(hv, col_h, "rgba(0,245,212,0.25)", 3.4)
        + "".join(labels)
        + "</svg>"
    )


POSTER_CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#060913}
body{width:1080px;height:1440px;overflow:hidden;font-family:"Noto Sans SC","Microsoft YaHei",sans-serif;color:#F5F7FA}
.pst{position:relative;width:1080px;height:1440px;overflow:hidden;padding:22px 28px 18px;display:flex;flex-direction:column;
     background:
       radial-gradient(920px 440px at 88% 4%,rgba(212,255,0,.15),transparent 60%),
       radial-gradient(820px 540px at 10% 32%,rgba(0,245,212,.12),transparent 62%),
       radial-gradient(920px 520px at 50% 96%,rgba(255,56,100,.11),transparent 65%),
       linear-gradient(180deg,#060913 0%,#0A1020 52%,#060913 100%)}
.pst .grid-bg{position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.065) 1px,transparent 1px);
              background-size:24px 24px;opacity:.55;pointer-events:none}
.pst .border-out{position:absolute;inset:12px;border:1.5px solid rgba(212,255,0,.22);pointer-events:none}

.pst .mast{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:flex-end;
           padding-bottom:10px;border-bottom:2px solid rgba(212,255,0,.38)}
.pst .mast-l .eyebrow{display:inline-flex;align-items:center;gap:10px;background:#D4FF00;color:#060913;
                      font-size:13px;font-weight:900;padding:3px 10px;border-radius:4px;letter-spacing:.10em}
.pst .mast-l h1{margin:6px 0 0;font-size:38px;font-weight:900;line-height:1.06;letter-spacing:-.02em;color:#FFFFFF}
.pst .mast-l h1 em{font-style:normal;color:#D4FF00;margin-left:8px}
.pst .mast-l .sub{margin-top:5px;font-size:14px;font-weight:700;color:#A8B8CE;letter-spacing:.03em;display:flex;align-items:center;gap:14px}
.pst .mast-l .sub span.lgd{display:inline-flex;align-items:center;gap:5px;font-size:13px;color:#DCE8F8;background:rgba(255,255,255,.06);
                           padding:2px 8px;border-radius:4px;border:1px solid rgba(255,255,255,.10)}
.pst .mast-l .sub span.lgd i{display:inline-block;width:9px;height:9px;border-radius:2px}
.pst .mast-r{text-align:right;flex-shrink:0}
.pst .mast-r .big-dt{font-size:68px;font-weight:900;line-height:.86;color:#FFFFFF;font-family:Impact,"Arial Black",sans-serif;letter-spacing:.01em}
.pst .mast-r .big-dt i{color:#D4FF00;font-style:normal}
.pst .mast-r .wd{margin-top:5px;font-size:15px;font-weight:800;color:#00F5D4;letter-spacing:.05em;white-space:nowrap}

.pst .b-list{position:relative;z-index:2;flex:1;display:flex;flex-direction:column;justify-content:space-between;gap:9px;margin:9px 0 8px}
.pst .b-row{position:relative;flex:1;background:linear-gradient(90deg,rgba(14,23,40,.96),rgba(10,16,30,.94) 50%,rgba(22,15,32,.96));
            border:1px solid rgba(255,255,255,.13);border-left:5px solid #D4FF00;border-radius:12px;padding:7px 12px 7px;
            display:flex;flex-direction:column;justify-content:space-between;box-shadow:0 8px 22px rgba(0,0,0,.45)}

.pst .b-top{display:flex;justify-content:space-between;align-items:center;gap:8px;padding-bottom:4px;
            border-bottom:1px solid rgba(255,255,255,.08);font-size:12.5px;font-weight:800}
.pst .bt-left{display:flex;align-items:center;gap:8px;white-space:nowrap}
.pst .bt-idx{background:#D4FF00;color:#060913;font-weight:900;padding:1px 7px;border-radius:3px;font-size:12px;letter-spacing:.06em;white-space:nowrap}
.pst .bt-tm{color:#FFFFFF;font-family:ui-monospace,Consolas,monospace;font-size:14px;background:rgba(255,255,255,.08);padding:1px 7px;border-radius:4px;white-space:nowrap}
.pst .bt-lg{color:#00F5D4;font-weight:900;letter-spacing:.03em;white-space:nowrap}
.pst .bt-mid{color:#C6D6EA;font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pst .bt-mid b.h{color:#00F5D4}
.pst .bt-mid b.a{color:#FF5E7E}
.pst .bt-h2h{color:#D4FF00;background:rgba(212,255,0,.09);border:1px solid rgba(212,255,0,.26);padding:1px 8px;border-radius:4px;font-size:12px;white-space:nowrap}

.pst .b-main{display:grid;grid-template-columns:342px 304px 342px;align-items:center;justify-content:space-between;gap:6px;margin:2px 0}
.pst .b-side{display:flex;flex-direction:column;gap:5px}
.pst .t-hdr{display:flex;align-items:center;justify-content:space-between;gap:6px}
.pst .b-side.away .t-hdr{flex-direction:row-reverse}
.pst .tname{font-size:24px;font-weight:900;color:#FFFFFF;letter-spacing:-.01em;display:flex;align-items:center;gap:6px;white-space:nowrap}
.pst .tname i.bar{display:inline-block;width:5px;height:20px;border-radius:2px;background:#00F5D4}
.pst .b-side.away .tname i.bar{background:#FF5E7E}
.pst .seq-wrap{display:flex;align-items:center;gap:3px}
.pst .seq-wrap .l5-txt{font-size:11.5px;font-weight:800;color:#9AB0C8;margin-right:3px;font-family:ui-monospace,Consolas,monospace}
.pst .b-side.away .seq-wrap .l5-txt{margin-right:0;margin-left:3px}
.pst .seq-wrap i{font-style:normal;width:18px;height:18px;border-radius:3px;display:inline-flex;align-items:center;justify-content:center;
                 font-size:11px;font-weight:900;color:#060913}
.pst .seq-wrap i.W{background:#00F5D4}
.pst .seq-wrap i.D{background:#FFD166}
.pst .seq-wrap i.L{background:#FF5E7E;color:#FFFFFF}

.pst .p-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:4px}
.pst .p-cell{background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);border-radius:6px;padding:4px 6px;display:flex;flex-direction:column;justify-content:center}
.pst .b-side.home .p-cell{border-top:2px solid rgba(0,245,212,.45)}
.pst .b-side.away .p-cell{border-top:2px solid rgba(255,94,126,.45);text-align:right}
.pst .p-cell .k{font-size:10.5px;font-weight:700;color:#8CA2BC;line-height:1.15;white-space:nowrap}
.pst .p-cell .v{font-size:14.5px;font-weight:900;color:#00F5D4;font-family:ui-monospace,Consolas,monospace;line-height:1.2;margin-top:2px;white-space:nowrap}
.pst .b-side.away .p-cell .v{color:#FF5E7E}
.pst .p-cell .s{font-size:10px;font-weight:700;color:#B8C8DC;line-height:1.15;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

.pst .flow-bar{background:rgba(0,0,0,.36);border:1px solid rgba(255,255,255,.08);border-radius:5px;padding:3px 6px;
               font-size:10.5px;font-weight:800;color:#C4D4E8;display:flex;align-items:center;justify-content:space-between;gap:3px;
               font-family:ui-monospace,Consolas,monospace;white-space:nowrap}
.pst .flow-bar b{color:#D4FF00;font-family:"Noto Sans SC",sans-serif;font-size:10.5px;flex-shrink:0}
.pst .flow-bar span{background:rgba(255,255,255,.05);padding:1px 4px;border-radius:3px}

.pst .b-center{position:relative;width:304px;height:216px;display:flex;align-items:center;justify-content:center}

.pst .b-foot{display:flex;align-items:center;justify-content:space-between;gap:10px;padding-top:4px;border-top:1px solid rgba(255,255,255,.08)}
.pst .b-chip{font-size:12px;font-weight:900;color:#D4FF00;background:rgba(212,255,0,.10);border:1px solid rgba(212,255,0,.30);
             padding:2px 8px;border-radius:4px;white-space:nowrap}
.pst .b-bars{display:flex;align-items:center;gap:12px;flex:1;max-width:340px}
.pst .b-bar{flex:1;display:flex;align-items:center;gap:5px;font-size:11px;font-weight:800;color:#98ABC2;white-space:nowrap}
.pst .b-bar b.h{color:#00F5D4;font-family:ui-monospace,Consolas,monospace}
.pst .b-bar b.a{color:#FF5E7E;font-family:ui-monospace,Consolas,monospace}
.pst .b-bar .trk{flex:1;height:6px;background:rgba(255,255,255,.09);border-radius:99px;overflow:hidden;display:flex}
.pst .b-bar .trk i.h{background:linear-gradient(90deg,#00F5D4,#D4FF00);height:100%}
.pst .b-bar .trk i.a{background:linear-gradient(90deg,#FF5E7E,#FF2A55);height:100%;margin-left:auto}
.pst .b-pt{font-size:12px;font-weight:800;color:#DCE8F8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

.pst .p-foot{position:relative;z-index:2;display:flex;justify-content:space-between;align-items:center;
             padding-top:8px;border-top:1px solid rgba(212,255,0,.28)}
.pst .p-brand{display:flex;align-items:center;gap:10px}
.pst .p-brand em{width:6px;height:32px;background:#D4FF00;display:block;border-radius:2px}
.pst .p-brand b{font-size:24px;font-weight:900;color:#FFFFFF;display:block;line-height:1}
.pst .p-brand b i{color:#D4FF00;font-style:normal}
.pst .p-brand span{font-size:12.5px;font-weight:700;color:#98ABC2;display:block;margin-top:3px;letter-spacing:.04em}
.pst .p-note{text-align:right;font-size:12px;color:#7E92AA;font-weight:600;line-height:1.35}

/* ====== 3 场模板（n3：超大雷达 R=82px + 宽裕参数格） ====== */
.pst.n3{padding:24px 28px 20px}
.pst.n3 .mast-l h1{font-size:40px}
.pst.n3 .mast-r .big-dt{font-size:72px}
.pst.n3 .b-list{gap:14px;margin:12px 0 10px}
.pst.n3 .b-row{padding:10px 12px 10px;border-radius:14px}
.pst.n3 .b-top{padding-bottom:6px;font-size:12.5px}
.pst.n3 .bt-idx{font-size:12px;padding:1px 8px}
.pst.n3 .bt-tm{font-size:14px}
.pst.n3 .bt-mid{font-size:12px}
.pst.n3 .bt-h2h{font-size:12px;padding:1px 8px}
.pst.n3 .b-main{grid-template-columns:340px 308px 340px;gap:6px;margin:4px 0}
.pst.n3 .b-side{gap:8px}
.pst.n3 .tname{font-size:26px}
.pst.n3 .tname i.bar{height:22px;width:5px}
.pst.n3 .seq-wrap i{width:19px;height:19px;font-size:11.5px}
.pst.n3 .p-grid{gap:6px}
.pst.n3 .p-cell{padding:7px 6px;border-radius:8px}
.pst.n3 .p-cell .k{font-size:11px}
.pst.n3 .p-cell .v{font-size:15px;margin-top:3px}
.pst.n3 .p-cell .s{font-size:10px;margin-top:2px}
.pst.n3 .flow-bar{padding:5px 6px;font-size:10.5px}
.pst.n3 .flow-bar b{font-size:10.5px}
.pst.n3 .b-center{width:308px;height:258px}
.pst.n3 .b-foot{padding-top:6px}
.pst.n3 .b-chip{font-size:12.5px;padding:2px 9px}
.pst.n3 .b-bar{font-size:11.5px}
.pst.n3 .b-pt{font-size:12.5px}

/* ====== 5 场模板（n5：5 行高密度全维矩阵 R=60px） ====== */
.pst.n5{padding:16px 24px 14px}
.pst.n5 .mast{padding-bottom:7px}
.pst.n5 .mast-l .eyebrow{font-size:12px;padding:2px 8px}
.pst.n5 .mast-l h1{font-size:33px;margin-top:4px}
.pst.n5 .mast-l .sub{font-size:13px;margin-top:3px}
.pst.n5 .mast-r .big-dt{font-size:58px}
.pst.n5 .mast-r .wd{font-size:13.5px;margin-top:3px}
.pst.n5 .b-list{gap:6px;margin:7px 0 6px}
.pst.n5 .b-row{padding:5px 10px 4px;border-radius:10px}
.pst.n5 .b-top{padding-bottom:3px;font-size:11.5px}
.pst.n5 .bt-idx{font-size:11px;padding:1px 6px}
.pst.n5 .bt-tm{font-size:12.5px;padding:1px 6px}
.pst.n5 .bt-mid{font-size:11px}
.pst.n5 .bt-h2h{font-size:11px;padding:1px 6px}
.pst.n5 .b-main{grid-template-columns:354px 284px 354px;gap:5px;margin:1px 0}
.pst.n5 .b-side{gap:3px}
.pst.n5 .tname{font-size:20px}
.pst.n5 .tname i.bar{height:17px;width:4px}
.pst.n5 .seq-wrap .l5-txt{font-size:10.5px}
.pst.n5 .seq-wrap i{width:16px;height:16px;font-size:10px}
.pst.n5 .p-grid{gap:3px}
.pst.n5 .p-cell{padding:2.5px 5px;border-radius:5px}
.pst.n5 .p-cell .k{font-size:9.5px}
.pst.n5 .p-cell .v{font-size:13px;margin-top:1px}
.pst.n5 .p-cell .s{font-size:9px;margin-top:0}
.pst.n5 .flow-bar{padding:2px 5px;font-size:9.8px}
.pst.n5 .flow-bar b{font-size:9.8px}
.pst.n5 .b-center{width:284px;height:162px}
.pst.n5 .b-foot{padding-top:3px}
.pst.n5 .b-chip{font-size:11px;padding:1px 6px}
.pst.n5 .b-bar{font-size:10px}
.pst.n5 .b-bar .trk{height:5px}
.pst.n5 .b-pt{font-size:11px}
.pst.n5 .p-foot{padding-top:6px}
.pst.n5 .p-brand b{font-size:21px}
.pst.n5 .p-brand span{font-size:11.5px}
.pst.n5 .p-note{font-size:11px}

/* ====== 6 场模板（n6：6 行超密战术看板 R=48px） ====== */
.pst.n6{padding:14px 22px 12px}
.pst.n6 .mast{padding-bottom:6px}
.pst.n6 .mast-l .eyebrow{font-size:11px;padding:2px 7px}
.pst.n6 .mast-l h1{font-size:29px;margin-top:3px}
.pst.n6 .mast-l .sub{font-size:12px;margin-top:2px;gap:10px}
.pst.n6 .mast-l .sub span.lgd{font-size:11.5px;padding:1px 6px}
.pst.n6 .mast-r .big-dt{font-size:50px}
.pst.n6 .mast-r .wd{font-size:12.5px;margin-top:2px}
.pst.n6 .b-list{gap:5px;margin:5px 0 5px}
.pst.n6 .b-row{padding:3.5px 9px 3px;border-radius:8px;border-left-width:4px}
.pst.n6 .b-top{padding-bottom:2px;font-size:10.5px}
.pst.n6 .bt-idx{font-size:10px;padding:1px 5px}
.pst.n6 .bt-tm{font-size:11.5px;padding:0 5px}
.pst.n6 .bt-mid{font-size:10.2px}
.pst.n6 .bt-h2h{font-size:10.2px;padding:0 6px}
.pst.n6 .b-main{grid-template-columns:364px 268px 364px;gap:4px;margin:0}
.pst.n6 .b-side{gap:2.5px}
.pst.n6 .tname{font-size:17.5px}
.pst.n6 .tname i.bar{height:14px;width:4px}
.pst.n6 .seq-wrap .l5-txt{font-size:10px}
.pst.n6 .seq-wrap i{width:14px;height:14px;font-size:9px}
.pst.n6 .p-grid{gap:2.5px}
.pst.n6 .p-cell{padding:1.5px 4px;border-radius:4px}
.pst.n6 .p-cell .k{font-size:8.8px;line-height:1.1}
.pst.n6 .p-cell .v{font-size:11.8px;line-height:1.12;margin-top:0}
.pst.n6 .p-cell .s{font-size:8.2px;line-height:1.1;margin-top:0}
.pst.n6 .flow-bar{padding:1.5px 4px;font-size:9.2px}
.pst.n6 .flow-bar b{font-size:9.2px}
.pst.n6 .flow-bar span{padding:0 3px}
.pst.n6 .b-center{width:268px;height:132px}
.pst.n6 .b-foot{padding-top:2px}
.pst.n6 .b-chip{font-size:10px;padding:1px 5px}
.pst.n6 .b-bars{max-width:300px;gap:8px}
.pst.n6 .b-bar{font-size:9.5px}
.pst.n6 .b-bar .trk{height:4px}
.pst.n6 .b-pt{font-size:10px}
.pst.n6 .p-foot{padding-top:5px}
.pst.n6 .p-brand em{height:26px;width:5px}
.pst.n6 .p-brand b{font-size:19px}
.pst.n6 .p-brand span{font-size:10.5px;margin-top:2px}
.pst.n6 .p-note{font-size:10px;line-height:1.25}
"""


def cover_poster_html(data: dict, n_override: int = 0) -> str:
    """一图流全维技术海报（自适应 3 / 4 / 5 / 6 场模板，赛博黑金风格）。"""
    ms_all = data.get("matches") or []
    n_target = n_override if n_override in (3, 4, 5, 6) else max(3, min(6, len(ms_all) or 4))
    ms = ms_all[:n_target]
    n_actual = max(3, min(6, len(ms)))
    rw, rh_svg, r_rad, r_fs = POSTER_RADAR_SPEC.get(n_actual, POSTER_RADAR_SPEC[4])

    meta = data.get("meta") or {}
    m_date = meta.get("date") or "10.28"
    m_wd = (meta.get("weekday") or "星期三").replace("星期", "").replace("周", "")
    m_kd = meta.get("kick_day") or "%s 赛程" % m_date.replace(".", "/")
    d1, _, d2 = m_date.partition(".")
    dt = "%s<i>.</i>%s" % (d1, d2) if d2 else m_date
    lg_short = []
    for m in ms:
        s = (m.get("league") or "").split("·")[0].strip()
        if s and s not in lg_short:
            lg_short.append(s)
    lg_title = " × ".join(lg_short[:3]) if lg_short else "焦点赛事"

    def _seq_badges(seq):
        mp = {"W": "胜", "D": "平", "L": "负"}
        return "".join(f'<i class="{s}">{mp.get(s, "平")}</i>' for s in (seq or ["W", "D", "W", "L", "W"])[:5])

    rows = []
    for idx, c in enumerate(ms, 1):
        fh = (c.get("form") or {}).get("home") or {}
        fa = (c.get("form") or {}).get("away") or {}
        h2 = (c.get("form") or {}).get("h2h") or {}
        r_obj = c.get("radar") or {}
        rh = r_obj.get("home") or [65, 65, 50, 50, 60, 55]
        ra = r_obj.get("away") or [55, 60, 40, 50, 50, 55]
        avg_rh = float(r_obj.get("avg_home") or (sum(rh) / len(rh)))
        avg_ra = float(r_obj.get("avg_away") or (sum(ra) / len(ra)))

        hpj, apj = float(fh.get("pj") or 0), float(fa.get("pj") or 0)
        hsj, asj = float(fh.get("sj") or 0), float(fa.get("sj") or 0)
        hgd = float(fh.get("gd_avg") if fh.get("gd_avg") is not None else (hpj - hsj))
        agd = float(fa.get("gd_avg") if fa.get("gd_avg") is not None else (apj - asj))
        hz, az = float(fh.get("zero") or 0), float(fa.get("zero") or 0)
        hunb, aunb = float(fh.get("unbeat") or 60), float(fa.get("unbeat") or 60)
        hvol, avol = float(fh.get("vol") or 0), float(fa.get("vol") or 0)

        h_ht_gf, h_ht_ga = int(fh.get("ht_gf") or 0), int(fh.get("ht_ga") or 0)
        a_ht_gf, a_ht_ga = int(fa.get("ht_gf") or 0), int(fa.get("ht_ga") or 0)
        h_sh_gf, h_sh_ga = int(fh.get("sh_gf") or 0), int(fh.get("sh_ga") or 0)
        a_sh_gf, a_sh_ga = int(fa.get("sh_gf") or 0), int(fa.get("sh_ga") or 0)
        h_ht_lead, a_ht_lead = int(fh.get("ht_lead") or 0), int(fa.get("ht_lead") or 0)
        h_ht_unb, a_ht_unb = int(fh.get("ht_unbeat") or 0), int(fa.get("ht_unbeat") or 0)

        h_rank_txt = fh.get("rank_txt") or f"近5战 {fh.get('l5') or ''}"
        a_rank_txt = fa.get("rank_txt") or f"近5战 {fa.get('l5') or ''}"
        h_ven_txt = fh.get("ven_txt") or "主场表现"
        a_ven_txt = fa.get("ven_txt") or "客场表现"
        h_ven_sub = fh.get("ven_sub") or f"场均进{hpj:.2f}"
        a_ven_sub = fa.get("ven_sub") or f"场均进{apj:.2f}"

        h_flow_items = [esc(x.replace("(", "").replace(")", "")) for x in (fh.get("flow") or [])[:5]]
        a_flow_items = [esc(x.replace("(", "").replace(")", "")) for x in (fa.get("flow") or [])[:5]]
        h_flow = "".join(f"<span>{x}</span>" for x in h_flow_items) or f"<span>共进{fh.get('gf',0)}失{fh.get('ga',0)}</span>"
        a_flow = "".join(f"<span>{x}</span>" for x in a_flow_items) or f"<span>共进{fa.get('gf',0)}失{fa.get('ga',0)}</span>"

        tot_pj = (hpj + apj) or 1.0
        w_pj = max(14.0, min(86.0, 100.0 * hpj / tot_pj))
        tot_rad = (avg_rh + avg_ra) or 1.0
        w_rad = max(18.0, min(82.0, 100.0 * avg_rh / tot_rad))

        t1, t2 = _extract_tag_pair(c)
        rad_svg = _poster_radar_svg(c, w=rw, h=rh_svg, col_h="#00F5D4", col_a="#FF5E7E", rad=r_rad, fs=r_fs)
        h2_low = h2.get("low") if h2.get("low") not in (None, "") else ((c.get("h2h_stats") or {}).get("low") or "—")
        h2h_str = (
            f"近{h2.get('n', 6)}次交锋：主{h2.get('w', 0)}胜{h2.get('d', 0)}平{h2.get('l', 0)}负 "
            f"(进{h2.get('gf', 0)}失{h2.get('ga', 0)}) · 场均{h2.get('avg_goals', '—')}球 · ≤2球占{h2_low}%"
        )
        pt_str = c.get("point") or f"焦点：{t1} vs {t2}"

        rows.append(f"""
        <div class="b-row">
          <div class="b-top">
            <div class="bt-left">
              <span class="bt-idx">MATCH 0{idx}</span>
              <span class="bt-tm">{esc(c.get("kick") or "")}</span>
              <span class="bt-lg">{esc(c.get("league") or "")}</span>
            </div>
            <div class="bt-mid"><b class="h">{esc(h_rank_txt)}</b> <span>vs</span> <b class="a">{esc(a_rank_txt)}</b></div>
            <div class="bt-h2h">{esc(h2h_str)}</div>
          </div>
          <div class="b-main">
            <div class="b-side home">
              <div class="t-hdr">
                <div class="tname"><i class="bar"></i>{esc(c.get("home") or "")}</div>
                <div class="seq-wrap"><span class="l5-txt">{esc(fh.get("l5") or "")}</span>{_seq_badges(fh.get("seq"))}</div>
              </div>
              <div class="p-grid">
                <div class="p-cell">
                  <span class="k">近5场均进/失</span>
                  <span class="v">{hpj:.2f} / {hsj:.2f}</span>
                  <span class="s">5场共进{fh.get("gf",0)}失{fh.get("ga",0)}</span>
                </div>
                <div class="p-cell">
                  <span class="k">同主客战力</span>
                  <span class="v">{esc(h_ven_txt.replace("本季","").replace("近期",""))}</span>
                  <span class="s">{esc(h_ven_sub)}</span>
                </div>
                <div class="p-cell">
                  <span class="k">上半场抢开局</span>
                  <span class="v">进{h_ht_gf} 失{h_ht_ga}</span>
                  <span class="s">领先{h_ht_lead}% · 不败{h_ht_unb}%</span>
                </div>
                <div class="p-cell">
                  <span class="k">下半场后程得失</span>
                  <span class="v">进{h_sh_gf} 失{h_sh_ga}</span>
                  <span class="s">零封{hz:.0f}% · 不败{hunb:.0f}%</span>
                </div>
                <div class="p-cell">
                  <span class="k">进球波动 / 净胜</span>
                  <span class="v">σ{hvol:.2f} / {hgd:+.1f}</span>
                  <span class="s">稳定{rh[3]} · 净胜分{rh[4]}</span>
                </div>
                <div class="p-cell">
                  <span class="k">六维综合均值</span>
                  <span class="v">{avg_rh:.1f} 分</span>
                  <span class="s">攻{rh[0]} 防{rh[1]} 开{rh[5]}</span>
                </div>
              </div>
              <div class="flow-bar"><b>近5战</b>{h_flow}</div>
            </div>

            <div class="b-center">{rad_svg}</div>

            <div class="b-side away">
              <div class="t-hdr">
                <div class="tname">{esc(c.get("away") or "")}<i class="bar"></i></div>
                <div class="seq-wrap">{_seq_badges(fa.get("seq"))}<span class="l5-txt">{esc(fa.get("l5") or "")}</span></div>
              </div>
              <div class="p-grid">
                <div class="p-cell">
                  <span class="k">近5场均进/失</span>
                  <span class="v">{apj:.2f} / {asj:.2f}</span>
                  <span class="s">5场共进{fa.get("gf",0)}失{fa.get("ga",0)}</span>
                </div>
                <div class="p-cell">
                  <span class="k">同主客战力</span>
                  <span class="v">{esc(a_ven_txt.replace("本季","").replace("近期",""))}</span>
                  <span class="s">{esc(a_ven_sub)}</span>
                </div>
                <div class="p-cell">
                  <span class="k">上半场抢开局</span>
                  <span class="v">进{a_ht_gf} 失{a_ht_ga}</span>
                  <span class="s">领先{a_ht_lead}% · 不败{a_ht_unb}%</span>
                </div>
                <div class="p-cell">
                  <span class="k">下半场后程得失</span>
                  <span class="v">进{a_sh_gf} 失{a_sh_ga}</span>
                  <span class="s">零封{az:.0f}% · 不败{aunb:.0f}%</span>
                </div>
                <div class="p-cell">
                  <span class="k">进球波动 / 净胜</span>
                  <span class="v">σ{avol:.2f} / {agd:+.1f}</span>
                  <span class="s">稳定{ra[3]} · 净胜分{ra[4]}</span>
                </div>
                <div class="p-cell">
                  <span class="k">六维综合均值</span>
                  <span class="v">{avg_ra:.1f} 分</span>
                  <span class="s">攻{ra[0]} 防{ra[1]} 开{ra[5]}</span>
                </div>
              </div>
              <div class="flow-bar"><b>近5战</b>{a_flow}</div>
            </div>
          </div>
          <div class="b-foot">
            <span class="b-chip">▸ {esc(t1)} × {esc(t2)}</span>
            <div class="b-bars">
              <div class="b-bar">
                <span>火力</span><b class="h">{hpj:.2f}</b>
                <div class="trk"><i class="h" style="width:{w_pj:.1f}%"></i><i class="a" style="width:{100-w_pj:.1f}%"></i></div>
                <b class="a">{apj:.2f}</b>
              </div>
              <div class="b-bar">
                <span>六维</span><b class="h">{avg_rh:.1f}</b>
                <div class="trk"><i class="h" style="width:{w_rad:.1f}%"></i><i class="a" style="width:{100-w_rad:.1f}%"></i></div>
                <b class="a">{avg_ra:.1f}</b>
              </div>
            </div>
            <span class="b-pt">{esc(pt_str)}</span>
          </div>
        </div>""")

    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>{POSTER_CSS}</style></head>
<body><div class="pst n{n_actual}">
  <div class="grid-bg"></div>
  <div class="border-out"></div>
  <div class="mast">
    <div class="mast-l">
      <span class="eyebrow">ALL-IN-ONE TECHNICAL DOSSIER // 90-MIN REGULAR TIME DATA</span>
      <h1>{esc(lg_title)}<em>{len(ms)} 场焦点战全维技术图谱</em></h1>
      <div class="sub">
        <span>2× 六维雷达对撞 · 上下半场得失拆分 · 同主客战力 · 波动度(σ)与交锋档案</span>
        <span class="lgd"><i style="background:#00F5D4"></i>主队参数/雷达</span>
        <span class="lgd"><i style="background:#FF5E7E"></i>客队参数/雷达</span>
      </div>
    </div>
    <div class="mast-r">
      <div class="big-dt">{dt}</div>
      <div class="wd">星期{m_wd} ｜ {esc(m_kd)}</div>
    </div>
  </div>
  <div class="b-list">{"".join(rows)}</div>
  <div class="p-foot">
    <div class="p-brand">
      <em></em>
      <div><b>阿飞 <i>·</i> 赛博聊球</b><span>一图流全维数据看板 · 深度战术与数据拆解见正文</span></div>
    </div>
    <div class="p-note">
      <div>数据口径：90 分钟常规时间 · 官方赛程与近 5 场全/半场客观数据统计</div>
      <div>仅供球迷战术交流参考，不构成任何建议</div>
    </div>
  </div>
</div></body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description="D 版单场深挖卡 v2（合规形态 + 3/4/5/6场赛博黑金一图流海报模板）")
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--template", type=int, choices=[0, 3, 4, 5, 6], default=0, help="指定 3/4/5/6 场一图流海报模板（0=按输入场次数自适应）")
    ap.add_argument("--all-templates", action="store_true", help="一次性输出 3场/4场/5场/6场 四套赛博黑金海报模板示例图（模板_3场_海报.png 等）")
    ap.add_argument("--cover", action="store_true", help="额外输出 00_封面.png")
    ap.add_argument("--only-cover", action="store_true", help="一图流模式：只生成封面海报，不生成单场内页卡")
    ap.add_argument("--cover-style", choices=["poster", "v4", "v3", "v2", "v2-wide", "dark", "light"], default="poster", help="封面风格")
    a = ap.parse_args()
    if a.all_templates:
        a.only_cover = True
    if a.only_cover or a.template or a.all_templates:
        a.cover = True
    data = json.loads(Path(a.input).read_text(encoding="utf-8"))
    ms = data.get("matches") or []
    if a.limit:
        ms = ms[:a.limit]
    try:
        import xhs_riskcheck
        hits = xhs_riskcheck.scan_cards(data, ms)
        if hits:
            print("❌ 风控自检未通过（命中 %d 处），已阻止出图：" % len(hits))
            for cat, frag, where, why in hits:
                print("  [%s] %s -> %r (%s)" % (cat, where, frag, why))
            sys.exit(2)
    except ImportError:
        pass
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    _tmp_env = os.environ.get("XHS_HTML_TMP")
    if _tmp_env and Path(_tmp_env).is_dir():
        tmp = Path(_tmp_env)  # 沙箱下 mkdtemp 新建目录会被 ACL 拒写，用预建目录
    else:
        tmp = Path(tempfile.mkdtemp(prefix="d_", dir=_tmp_env or out))
    if a.all_templates:
        for n_tpl in (3, 4, 5, 6):
            if len(ms) < n_tpl:
                print(f"  ⚠️ 输入场次({len(ms)})少于 {n_tpl} 场，跳过 {n_tpl} 场模板")
                continue
            th = tmp / f"tpl_{n_tpl}.html"
            th.write_text(cover_poster_html(data, n_override=n_tpl), encoding="utf-8")
            tpng = out / f"模板_{n_tpl}场_海报.png"
            tok = shot(th, tpng)
            print(("  ✅ " if tok else "  ❌ ") + tpng.name +
                  ("  %dKB" % (tpng.stat().st_size // 1024) if tok else ""))
    if a.cover and not a.all_templates:
        ch = tmp / "00.html"
        if a.cover_style == "v4":
            html = cover_v4_html(data)
        elif a.cover_style == "poster":
            html = cover_poster_html(data, n_override=a.template)
        elif a.cover_style == "v3":
            html = cover_v3_html(data)
        elif a.cover_style == "v2":
            html = cover_v2_html(data)
        elif a.cover_style == "v2-wide":
            html = cover_v2_html(data, wide=True)
        elif a.cover_style == "dark":
            html = cover_dark_html(data)
        else:
            html = cover_html(data)
        ch.write_text(html, encoding="utf-8")
        cpng = out / "00_封面.png"
        ok = shot(ch, cpng)
        print(("  ✅ " if ok else "  ❌ ") + cpng.name +
              ("  %dKB" % (cpng.stat().st_size // 1024) if ok else ""))
        if a.cover_style == "v4":
            ph = tmp / "00_poster.html"
            ph.write_text(cover_poster_html(data), encoding="utf-8")
            bpng = out / "00_封面_海报版.png"
            bok = shot(ph, bpng)
            print(("  ✅ " if bok else "  ❌ ") + bpng.name +
                  ("  %dKB" % (bpng.stat().st_size // 1024) if bok else ""))
        elif a.cover_style == "poster":
            import shutil as _shutil
            bpng = out / "00_封面_海报版.png"
            if cpng.exists():
                _shutil.copy2(cpng, bpng)
                print("  ✅ " + bpng.name + "  %dKB" % (bpng.stat().st_size // 1024))
        if a.cover_style in ("v2", "v3", "v4"):
            # 16:9 横版（头条信息流裁切备用）
            wh = tmp / "00_wide.html"
            if a.cover_style == "v4":
                wh.write_text(cover_v4_html(data, wide=True), encoding="utf-8")
            elif a.cover_style == "v3":
                wh.write_text(cover_v3_html(data, wide=True), encoding="utf-8")
            else:
                wh.write_text(cover_v2_html(data, wide=True), encoding="utf-8")
            wpng = out / "00_封面_16x9.png"
            wok = shot(wh, wpng, size=(1920, 1080))
            print(("  ✅ " if wok else "  ❌ ") + wpng.name +
                  ("  %dKB" % (wpng.stat().st_size // 1024) if wok else ""))
        if a.cover_style in ("v2", "v3", "v4", "poster"):
            # 缩略图预览（验证信息流可读性）：用 Pillow 等比缩，避免固定 body 宽度被裁
            ppng = out / "00_封面_预览.png"
            pok = False
            try:
                from PIL import Image
                im = Image.open(cpng)
                im.thumbnail((360, 480), Image.LANCZOS)
                im.save(ppng)
                pok = True
            except Exception:  # noqa: BLE001
                pok = shot(ch, ppng, size=(360, 480), scale=1)
            print(("  ✅ " if pok else "  ❌ ") + ppng.name +
                  ("  %dKB" % (ppng.stat().st_size // 1024) if pok else ""))
    if not a.only_cover:
        for i, c in enumerate(ms, 1):
            h = tmp / ("%02d.html" % i)
            _skin = skin_for((data.get("meta") or {}).get("date"), os.environ.get("CARD_SKIN") or None)
            _html = _scale_font_css(card_html(c, i, len(ms)), float(os.environ.get("CARD_FS", "1") or 1))
            h.write_text(_apply_skin(_html, _skin), encoding="utf-8")
            png = out / ("%02d_%s.png" % (i, c.get("home", "") + "vs" + c.get("away", "")))
            ok = shot(h, png)
            print(("  ✅ " if ok else "  ❌ ") + png.name +
                  ("  %dKB" % (png.stat().st_size // 1024) if ok else ""))
    if not _tmp_env and tmp.exists():
        import shutil as _sh
        _sh.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
