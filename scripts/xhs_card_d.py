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
.sec{margin-top:13px;position:relative;z-index:2}
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
.two{display:grid;gap:22px;margin-top:7px;align-items:start}
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
.heat .cell{height:31px;border-radius:2px}
.heat .ax{display:flex;justify-content:space-around;margin-top:3px;font-family:%(mono)s;font-size:12px;color:#7b8996;padding-left:22px}
.heat .cap{margin-top:3px;font-size:13px;color:#7b8996}
/* 叙事 */
.narr{font-size:16px;line-height:1.62;color:#1a242e;text-align:justify}
.narr b{color:#e8402a;font-weight:800;margin-right:5px}
.pt{margin-top:6px;font-size:16px;line-height:1.55;border-left:3px solid #0aa3c2;padding-left:9px}
.pt em{font-style:normal;font-weight:800;color:#0aa3c2;margin-right:5px}

/* 对比条（按胜率条的排法：两端数值 + 中间双色条） */
.cmp{margin-top:6px}
.cmp .row{margin-top:5px}
.cmp .lab{font-size:13px;color:#6a7885;letter-spacing:.02em;text-align:center}
.cmp .rb{display:flex;align-items:center;gap:7px;font-family:%(mono)s;font-size:15px;font-weight:800;color:#22303c}
.cmp .rb .v{width:46px}
.cmp .rb .v.r{text-align:right;color:#b8331f}
.cmp .rb .v.l{color:#0a768f}
.cmp .track{flex:1;height:9px;display:flex;background:rgba(10,90,120,.10)}
.cmp .track i{display:block;height:9px}
.cmp .track i.l{background:linear-gradient(90deg,#0aa3c2,#63d2e6)}
.cmp .track i.r{background:linear-gradient(90deg,#ff85a9,#e8402a)}
/* 情报 */
.intel{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:6px}
.ic{background:#fff;border:1px solid rgba(10,90,120,.14);padding:7px 9px}
.ic .t{font-size:14px;font-weight:800;display:flex;align-items:center;gap:6px;margin-bottom:3px}
.ic .t i{width:6px;height:6px;display:inline-block}
.ic.g .t{color:#0a7d5a}.ic.g .t i{background:#0a7d5a}
.ic.b .t{color:#b8331f}.ic.b .t i{background:#b8331f}
.ic ul{margin:0;padding-left:13px}
.ic li{font-size:13px;line-height:1.45;color:#22303c;margin-bottom:2px}
.ic li::marker{color:#9aa8b4}
""" % {"w": W, "h": H, "mono": MONO}


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


# ---------------------------------------------------------------- 组件
def radial(card: dict, size: int = 300) -> str:
    r = card.get("radar") or {}
    dims = r.get("dims") or []
    hv, av = r.get("home") or [], r.get("away") or []
    if not dims or len(hv) != len(dims) or len(av) != len(dims):
        return ""
    cx = cy = size / 2.0
    rad = size / 2.0 - 74
    n = len(dims)

    def pt(i, val):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        rr = rad * max(0.06, min(1.0, float(val) / 100.0))
        return cx + rr * math.cos(ang), cy + rr * math.sin(ang)

    def poly(vals):
        return " ".join("%.1f,%.1f" % pt(i, v) for i, v in enumerate(vals))

    rings = []
    for k in (0.25, 0.5, 0.75, 1.0):
        rings.append('<polygon points="%s" fill="none" stroke="rgba(10,90,120,.16)" stroke-width="1"/>'
                     % " ".join("%.1f,%.1f" % (cx + rad * k * math.cos(-math.pi / 2 + i * 2 * math.pi / n),
                                               cy + rad * k * math.sin(-math.pi / 2 + i * 2 * math.pi / n))
                                for i in range(n)))
    labels = []
    for i, d in enumerate(dims):
        x, y = pt(i, 122)
        anchor = "middle"
        if x > cx + 8:
            anchor = "start"
        elif x < cx - 8:
            anchor = "end"
        labels.append('<text x="%.1f" y="%.1f" font-size="16" font-weight="700" fill="#3f5566" '
                      'text-anchor="%s">%s</text>' % (x, y, anchor, esc(d)))
    return ('<svg viewBox="0 0 %.0f %.0f" width="%.0f" height="%.0f" style="overflow:visible">%s'
            '<polygon points="%s" fill="rgba(10,163,194,.18)" stroke="#0aa3c2" stroke-width="2.4"/>'
            '<polygon points="%s" fill="rgba(232,64,42,.12)" stroke="#e8402a" stroke-width="2.4"/>'
            '%s</svg>' % (size, size, size, size, "".join(rings), poly(hv), poly(av), "".join(labels)))


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
    cells = []
    for i, row in enumerate(g[:5]):
        cells.append('<div class="rb">%d</div>' % i)
        for v in row[:5]:
            al = 0.05 + 0.88 * (float(v) / mx)
            cells.append('<div class="cell" style="background:rgba(232,64,42,%.2f)"></div>' % al)
    ax = "".join("<span>%d</span>" % i for i in range(5))
    return ('<div class="grid">%s</div><div class="ax">%s</div>'
            '<div class="cap">横轴主队进球（4 记 4 球以上）· 纵轴客队进球 · 颜色越深概率越高</div>'
            % ("".join(cells), ax))


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
    <div class="rk">名次 {esc(rh)}</div></div>
  <div class="side r"><div class="tn">{esc(card.get("away"))}<em>{esc(card.get("league"))}</em></div>{money(v.get("away_text"))}
    <div class="rk">名次 {esc(ra)}</div></div>
</div>
<div class="bar"><i class="l" style="width:{wl:.1f}%"></i><i class="r" style="width:{100 - wl:.1f}%"></i></div>
<div class="vmeta"><span>主队占比 {wl:.0f}%</span><span>全队总值差 <b>{esc(v.get("ratio"))}</b></span></div>
</div>"""


def cmp_rows(card: dict) -> str:
    f = card.get("form") or {}
    fh, fa = f.get("home") or {}, f.get("away") or {}
    def avg(v, n):
        try:
            return "%.1f" % (float(v) / float(n))
        except (TypeError, ZeroDivisionError, ValueError):
            return "0.0"
    nh, na = fh.get("n") or 5, fa.get("n") or 5
    rows = [
        ("进球", fh.get("gf"), fa.get("gf")),
        ("失球", fh.get("ga"), fa.get("ga")),
        ("场均进", avg(fh.get("gf"), nh), avg(fa.get("gf"), na)),
        ("场均失", avg(fh.get("ga"), nh), avg(fa.get("ga"), na)),
        ("净胜球", fh.get("net"), fa.get("net")),
        ("不败率", "%d%%" % round(100 * (fh.get("unbeaten") or 0)),
         "%d%%" % round(100 * (fa.get("unbeaten") or 0))),
    ]
    out = ['<div class="row"><div class="lab" style="display:flex;justify-content:space-between;'
           'font-weight:800"><span style="color:#0a768f">%s</span>'
           '<span style="color:#b8331f">%s</span></div></div>' % (esc(card.get("home")), esc(card.get("away")))]
    for lab, a, b in rows:
        try:
            x, y = float(str(a).replace("%", "")), float(str(b).replace("%", ""))
        except ValueError:
            x = y = 1.0
        tot = (x + y) or 1
        wl = max(4.0, min(96.0, 100.0 * x / tot))
        out.append(
            '<div class="row"><div class="lab">%s</div><div class="rb">'
            '<span class="v l">%s</span><span class="track">'
            '<i class="l" style="width:%.1f%%"></i><i class="r" style="width:%.1f%%"></i></span>'
            '<span class="v r">%s</span></div></div>'
            % (esc(lab), esc(a), wl, 100 - wl, esc(b)))
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

    return (cell(home, "g", it.get("home_good")) + cell(home, "b", it.get("home_bad")) +
            cell(away, "g", it.get("away_good")) + cell(away, "b", it.get("away_bad")))


def card_html(card: dict, idx: int, total: int) -> str:
    f = card.get("form") or {}
    fh, fa = f.get("home") or {}, f.get("away") or {}
    home, away = esc(card.get("home")), esc(card.get("away"))
    league = esc(card.get("league"))
    focus = card.get("focus") or []
    narr = esc((card.get("narr") or " ".join(x for x in [card.get("contrast") or ""] + list(focus) if x))[:210])
    point = esc(card.get("point") or (focus[0] if focus else ""))
    h2h = esc(f.get("h2h") or "")

    def badges(seq):
        cls = {"W": "w", "D": "d", "L": "l"}
        txt = {"W": "胜", "D": "平", "L": "负"}
        return "".join('<i class="%s">%s</i>' % (cls.get(s, "d"), txt.get(s, "平")) for s in (seq or [])[:5])

    pt_html = ('<div class="pt"><em>看点</em>' + point + "</div>") if point else ""
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="card">
<div class="frame"><i class="tl"></i><i class="tr"></i><i class="bl"></i><i class="br"></i></div>
<div class="top"><span class="lg">» {league}</span><span class="md">// MATCH DATA CARD</span>
<span>{esc(card.get("kick"))}</span><span class="bd">@阿飞·赛博聊球</span></div>
<h1>{home}<span class="vs">vs</span>{away}</h1>

<section class="sec"><div class="sh"><span class="n">身价对标</span><span class="h">2026 年 10 月估值</span></div>
{value_block(card)}</section>

<section class="sec"><div class="sh"><span class="n">数据对照 · 六维</span>
<span class="h">近 5 场 · {esc(f.get("h2h_short") or h2h or "同主客 10 场")}</span></div>
<div class="two c2b stretch">
  <div>
    <div class="fr"><div class="l"><span class="nm">{home}</span><span class="badges">{badges(fh.get("seq"))}</span></div>
      <span class="r">{esc(fh.get("l5"))}</span></div>
    <div class="sub2">{esc(fh.get("ha"))}　场均 {esc(fh.get("pj"))} 进 / {esc(fh.get("sj"))} 失</div>
    <div class="fr"><div class="l"><span class="nm">{away}</span><span class="badges">{badges(fa.get("seq"))}</span></div>
      <span class="r">{esc(fa.get("l5"))}</span></div>
    <div class="sub2">{esc(fa.get("ha"))}　场均 {esc(fa.get("pj"))} 进 / {esc(fa.get("sj"))} 失</div>
    <div class="cmp">{cmp_rows(card)}</div>
  </div>
  <div class="rad">{radial(card)}
    <div class="lg2"><span><i style="background:#0aa3c2"></i>{home}</span>
    <span><i style="background:#e8402a"></i>{away}</span></div></div>
</div></section>

<section class="sec"><div class="sh"><span class="n">进球分布 · 比分热度</span><span class="h">泊松分布 · 蒙特卡洛 2 万次</span></div>
<div class="two c2b">
  <div class="pois">
    <div class="pr" style="color:#0aa3c2;font-weight:800"><span></span><span>{home} / {away}</span><span style="text-align:right">主 / 客</span></div>
    {pois_bars(card)}
  </div>
  <div class="heat">{mc_heat(card)}</div>
</div></section>

<section class="sec"><div class="sh"><span class="n">情报整理</span><span class="h">公开报道 · 需核原文</span></div>
<div class="intel">{intel_block(card)}</div></section>

<section class="sec"><div class="sh"><span class="n">核心矛盾与看点</span><span class="h">已发生数据 + 观察点</span></div>
<div class="two c1b" style="margin-top:6px">
  <div class="narr"><b>核心矛盾</b>{narr}</div>
  <div>{pt_html or '<div class="narr">—</div>'}</div>
</div></section>
</div></body></html>"""


def shot(html_path: Path, png_path: Path) -> bool:
    png_path = png_path.resolve()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    chrome = os.environ.get("CHROME") or r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
           "--virtual-time-budget=1200", "--force-device-scale-factor=2",
           "--window-size=%d,%d" % (W, H), "--screenshot=%s" % png_path,
           html_path.resolve().as_uri()]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    except Exception:  # noqa: BLE001
        return False
    return png_path.exists()


def main() -> None:
    ap = argparse.ArgumentParser(description="D 版单场深挖卡 v2（合规形态）")
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    data = json.loads(Path(a.input).read_text(encoding="utf-8"))
    ms = data.get("matches") or []
    if a.limit:
        ms = ms[:a.limit]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="d_", dir=os.environ.get("XHS_HTML_TMP") or out))
    for i, c in enumerate(ms, 1):
        h = tmp / ("%02d.html" % i)
        h.write_text(card_html(c, i, len(ms)), encoding="utf-8")
        png = out / ("%02d_%s_%s.png" % (i, c.get("no", ""), c.get("home", "") + "vs" + c.get("away", "")))
        ok = shot(h, png)
        print(("  ✅ " if ok else "  ❌ ") + png.name +
              ("  %dKB" % (png.stat().st_size // 1024) if ok else ""))


if __name__ == "__main__":
    main()
