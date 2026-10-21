# -*- coding: utf-8 -*-
"""D 版单场深挖卡（2026-10-21 用户在大宫松鼠 vs 富山胜利 那张卡上定下的形态，本地复刻）。

合规依据：📚知识库/写作指南/小红书合规规范_20261021.md
- 不上：场次编号（周一001）、三项概率并列、比分概率矩阵数值、方向/结论百分比
- 只上：身价对标 + 战绩 + 攻防 + 六维雷达 + 情景热度（只上色）+ 核心矛盾与看点
用法：
    python -X utf8 scripts/xhs_card_d.py --input cards.json --out state/tmp/d_test --limit 1
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
html,body{margin:0;padding:0;background:#eef1f5}
body{width:%(w)dpx;height:%(h)dpx;overflow:hidden}
.card{position:relative;width:%(w)dpx;height:%(h)dpx;display:flex;flex-direction:column;
  padding:54px 62px 40px;background:#eef1f5;color:#0d1117;
  font-family:"Microsoft YaHei UI","Noto Sans SC",sans-serif;
  background-image:linear-gradient(rgba(10,60,90,.05) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(10,60,90,.05) 1px,transparent 1px);
  background-size:36px 36px}
.frame{position:absolute;inset:24px;border:1px solid rgba(10,60,90,.14);pointer-events:none}
.frame i{position:absolute;width:24px;height:24px;border:2px solid #0aa3c2}
.frame i.tl{left:-1px;top:-1px;border-right:0;border-bottom:0}
.frame i.tr{right:-1px;top:-1px;border-left:0;border-bottom:0}
.frame i.bl{left:-1px;bottom:-1px;border-right:0;border-top:0}
.frame i.br{right:-1px;bottom:-1px;border-left:0;border-top:0}
.top{display:flex;align-items:center;justify-content:space-between;font-family:%(mono)s;
  font-size:18px;letter-spacing:.12em;color:#4a5a68}
.top .lg{color:#0aa3c2;font-weight:700;letter-spacing:.2em}
.top .md{color:#8a99a6}
.top .pg{color:#e8402a;font-weight:700}
h1{margin:22px 0 0;font-size:74px;line-height:1.16;font-weight:900;text-align:center;letter-spacing:-.01em}
h1 .vs{margin:0 14px;font-size:30px;font-weight:400;color:#0aa3c2;vertical-align:middle}
.sub{margin-top:6px;text-align:center;font-size:18px;color:#6a7885;letter-spacing:.1em}
.sec{margin-top:20px}
.sh{display:flex;align-items:baseline;justify-content:space-between;border-bottom:1px solid rgba(10,60,90,.18);padding-bottom:5px}
.sh .n{font-size:22px;font-weight:800;letter-spacing:.06em;display:flex;align-items:center;gap:8px}
.sh .n::before{content:"";width:9px;height:9px;background:#0aa3c2}
.sh .h{font-family:%(mono)s;font-size:15px;color:#7b8996;letter-spacing:.06em}
.vs2{display:grid;grid-template-columns:1fr 1fr;margin-top:10px;background:#fff;border-left:3px solid #0aa3c2}
.vc{padding:10px 16px}
.vc+.vc{border-left:1px dashed rgba(10,60,90,.22)}
.vc .nm{font-size:20px;font-weight:800;display:flex;align-items:center;gap:8px}
.vc .nm em{font-style:normal;font-size:13px;font-family:%(mono)s;color:#0aa3c2;
  border:1px solid rgba(10,163,194,.5);padding:0 5px;font-weight:700}
.vc .big{margin-top:2px;font-size:36px;font-weight:900;color:#e8402a;line-height:1.12}
.vr{display:flex;justify-content:space-between;font-size:16px;color:#3d4b58;margin-top:1px}
.vr b{font-family:%(mono)s;font-weight:800;color:#0d1117}
.vbar{margin-top:9px;display:flex;align-items:center;justify-content:space-between;
  background:rgba(232,64,42,.07);padding:5px 12px;font-size:16px;color:#7a2f22}
.vbar b{font-family:%(mono)s;font-size:18px;color:#e8402a}
.fr2{margin-top:8px}
.fr{display:flex;align-items:center;justify-content:space-between;padding:3px 0}
.fr .l{display:flex;align-items:center;gap:9px}
.fr .nm{font-size:20px;font-weight:800;min-width:126px}
.badges{display:flex;gap:4px}
.badges i{width:26px;height:26px;display:flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:800;font-style:normal;border:1px solid}
.badges i.w{color:#0a7d5a;border-color:rgba(10,125,90,.55);background:rgba(10,125,90,.1)}
.badges i.d{color:#4a5a68;border-color:rgba(74,90,104,.45);background:rgba(74,90,104,.08)}
.badges i.l{color:#c2382f;border-color:rgba(194,56,47,.55);background:rgba(194,56,47,.1)}
.fr .r{font-family:%(mono)s;font-size:18px;font-weight:800;color:#0aa3c2}
.fr .s{font-size:15px;color:#6a7885}
.two{display:grid;grid-template-columns:1.02fr 0.98fr;gap:22px;margin-top:10px}
table.st{width:100%%;border-collapse:collapse;font-size:16px}
table.st th{font-size:16px;color:#6a7885;font-weight:700;padding:5px 0;border-bottom:1px solid rgba(10,60,90,.16)}
table.st th.a,table.st td.a{text-align:right;font-family:%(mono)s}
table.st td{padding:5px 0;border-bottom:1px dashed rgba(10,60,90,.1)}
table.st th:first-child,table.st td:first-child{width:40%%}
table.st th.a,table.st td.a{width:30%%;text-align:right}
table.st td.a{font-weight:700}
.lg2{margin-top:4px;font-size:14px;color:#6a7885;display:flex;gap:14px}
.lg2 span{display:flex;align-items:center;gap:5px}
.lg2 i{display:inline-block;width:10px;height:10px}
.heat .grid{display:grid;grid-template-columns:22px repeat(5,50px);gap:3px}
.heat .rb{display:flex;align-items:center;justify-content:center;font-family:%(mono)s;font-size:14px;color:#7b8996}
.heat .cell{height:40px;border-radius:2px}
.heat .ax{width:272px;display:flex;justify-content:space-around;margin-top:4px;font-family:%(mono)s;font-size:13px;color:#7b8996;padding-left:22px}
.heat .cap{margin-top:4px;font-size:14px;color:#7b8996;line-height:1.5}
.narr{margin-top:2px;font-size:17px;line-height:1.58;color:#1a242e;text-align:justify}
.narr b{color:#e8402a;font-weight:800;margin-right:6px}
.pt{margin-top:6px;font-size:17px;line-height:1.5;color:#0d1117;border-left:3px solid #0aa3c2;padding-left:9px}
.pt em{font-style:normal;font-weight:800;color:#0aa3c2;margin-right:5px}
.note{margin-top:auto;border:1px solid rgba(10,60,90,.14);background:rgba(255,255,255,.55);
  padding:6px 11px;font-size:14px;color:#5c6b78;line-height:1.5}
.foot{display:flex;align-items:flex-end;justify-content:space-between;margin-top:11px;font-size:15px;color:#6a7885}
.foot .b{font-size:25px;font-weight:800;letter-spacing:.06em;color:#0aa3c2;display:flex;align-items:center;gap:9px}
.foot .b i{display:inline-block;width:20px;height:7px;background:#0aa3c2;opacity:.7}
.foot .tag{font-family:%(mono)s;font-size:14px;color:#7b8996;letter-spacing:.04em;text-align:right}
""" % {"w": W, "h": H, "mono": MONO}


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""))


def radial(card: dict, size: int = 226) -> str:
    r = card.get("radar") or {}
    dims = r.get("dims") or []
    hv, av = r.get("home") or [], r.get("away") or []
    if not dims or len(hv) != len(dims) or len(av) != len(dims):
        return ""
    cx = cy = size / 2.0
    rad = size / 2.0 - 58
    n = len(dims)

    def pt(i, val):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        rr = rad * max(0.06, min(1.0, float(val) / 100.0))
        return cx + rr * math.cos(ang), cy + rr * math.sin(ang)

    def poly(vals):
        return " ".join("%.1f,%.1f" % pt(i, v) for i, v in enumerate(vals))

    rings = []
    for k in (0.25, 0.5, 0.75, 1.0):
        rings.append('<polygon points="%s" fill="none" stroke="rgba(10,60,90,.16)" stroke-width="1"/>'
                     % " ".join("%.1f,%.1f" % (cx + rad * k * math.cos(-math.pi / 2 + i * 2 * math.pi / n),
                                               cy + rad * k * math.sin(-math.pi / 2 + i * 2 * math.pi / n))
                                for i in range(n)))
    labels = []
    for i, d in enumerate(dims):
        x, y = pt(i, 120)
        anchor = "middle"
        if x > cx + 8:
            anchor = "start"
        elif x < cx - 8:
            anchor = "end"
        labels.append('<text x="%.1f" y="%.1f" font-size="13" fill="#4a5a68" text-anchor="%s">%s</text>'
                      % (x, y, anchor, esc(d)))
    return ('<svg viewBox="0 0 %.0f %.0f" width="%.0f" height="%.0f" style="overflow:visible">%s'
            '<polygon points="%s" fill="rgba(10,163,194,.16)" stroke="#0aa3c2" stroke-width="2"/>'
            '<polygon points="%s" fill="rgba(232,64,42,.10)" stroke="#e8402a" stroke-width="2"/>'
            '%s</svg>' % (size, size, size, size, "".join(rings), poly(hv), poly(av), "".join(labels)))


def heat(card: dict) -> str:
    g = (card.get("model") or {}).get("grid") or []
    if not g:
        return ""
    mx = max(max(row) for row in g) or 1
    cells = []
    for i, row in enumerate(g[:5]):
        cells.append('<div class="rb">%d</div>' % i)
        for v in row[:5]:
            al = 0.06 + 0.86 * (float(v) / mx)
            cells.append('<div class="cell" style="background:rgba(232,64,42,%.2f)"></div>' % al)
    ax = "".join("<span>%d</span>" % i for i in range(5))
    return ('<div class="grid">%s</div><div class="ax">%s</div>'
            '<div class="cap">横轴主队进球（4 记作 4 球以上），纵轴客队进球；只示强弱，不标数值。</div>'
            % ("".join(cells), ax))


def ranks(v: dict) -> tuple:
    txt = (v.get("rank_text") or "").replace("第", "")
    parts = [p.strip() for p in txt.replace("·", "|").split("|") if p.strip()]
    return (parts[0] if parts else "—"), (parts[-1] if len(parts) > 1 else "—")


def card_html(card: dict, meta: dict, idx: int, total: int) -> str:
    f = card.get("form") or {}
    fh, fa = f.get("home") or {}, f.get("away") or {}
    v = card.get("value") or {}
    rh, ra = ranks(v)

    def badges(seq):
        cls = {"W": "w", "D": "d", "L": "l"}
        txt = {"W": "胜", "D": "平", "L": "负"}
        return "".join('<i class="%s">%s</i>' % (cls.get(s, "d"), txt.get(s, "平")) for s in (seq or [])[:5])

    home, away = esc(card.get("home")), esc(card.get("away"))
    league = esc(card.get("league"))
    focus = card.get("focus") or []
    narr_text = card.get("narr") or " ".join(
        x for x in [card.get("contrast") or ""] + list(focus) if x)
    narr = esc(narr_text[:150])
    point = esc(card.get("point") or (focus[0] if focus else ""))
    net_h = fh.get("net") or 0
    net_a = fa.get("net") or 0
    pt_html = ('<div class="pt"><em>看点</em>' + point + "</div>") if point else ""
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="card">
<div class="frame"><i class="tl"></i><i class="tr"></i><i class="bl"></i><i class="br"></i></div>
<div class="top"><span class="lg">» {league}</span><span class="md">// MATCH DATA CARD</span>
<span>{esc(card.get("kick"))}</span><span class="pg">{idx:02d} / {total:02d}</span></div>
<h1>{home}<span class="vs">vs</span>{away}</h1>
<div class="sub">{league} · 公开数据卡</div>

<section class="sec"><div class="sh"><span class="n">硬实力对标</span>
<span class="h">身价 / 联赛名次 · 懂球帝身价表</span></div>
<div class="vs2">
  <div class="vc"><div class="nm">{home}<em>{league}</em></div>
    <div class="big">{esc(v.get("home_text"))}</div>
    <div class="vr"><span>联赛名次</span><b>{esc(rh)}</b></div></div>
  <div class="vc"><div class="nm">{away}<em>{league}</em></div>
    <div class="big">{esc(v.get("away_text"))}</div>
    <div class="vr"><span>联赛名次</span><b>{esc(ra)}</b></div></div>
</div>
<div class="vbar"><span>全队总值差 <b>{esc(v.get("ratio"))}</b></span>
<span>阵容人数 / 平均年龄 / 外籍占比：本机暂无结构化源，不上行</span></div>
</section>

<section class="sec"><div class="sh"><span class="n">战绩概览</span><span class="h">近 5 场 · 左旧 → 右新</span></div>
<div class="fr2">
  <div class="fr"><div class="l"><span class="nm">{home}</span><span class="badges">{badges(fh.get("seq"))}</span></div>
    <span class="r">{esc(fh.get("l5"))}</span></div>
  <div class="fr"><span class="s">{esc(fh.get("ha"))}</span><span class="s">场均 {esc(fh.get("pj"))} 进 / {esc(fh.get("sj"))} 失</span></div>
  <div class="fr"><div class="l"><span class="nm">{away}</span><span class="badges">{badges(fa.get("seq"))}</span></div>
    <span class="r">{esc(fa.get("l5"))}</span></div>
  <div class="fr"><span class="s">{esc(fa.get("ha"))}</span><span class="s">场均 {esc(fa.get("pj"))} 进 / {esc(fa.get("sj"))} 失</span></div>
</div></section>

<section class="sec"><div class="sh"><span class="n">攻防对照</span><span class="h">近 5 场 · 公开赛事数据</span></div>
<div class="two">
  <table class="st">
    <tr><th></th><th class="a">{home}</th><th class="a">{away}</th></tr>
    <tr><td>进球</td><td class="a">{esc(fh.get("gf"))}</td><td class="a">{esc(fa.get("gf"))}</td></tr>
    <tr><td>失球</td><td class="a">{esc(fh.get("ga"))}</td><td class="a">{esc(fa.get("ga"))}</td></tr>
    <tr><td>场均进</td><td class="a">{esc(fh.get("pj"))}</td><td class="a">{esc(fa.get("pj"))}</td></tr>
    <tr><td>场均失</td><td class="a">{esc(fh.get("sj"))}</td><td class="a">{esc(fa.get("sj"))}</td></tr>
    <tr><td>净胜球</td><td class="a">{'+' if net_h > 0 else ''}{esc(net_h)}</td><td class="a">{'+' if net_a > 0 else ''}{esc(net_a)}</td></tr>
  </table>
  <div class="rad">{radial(card)}
    <div class="lg2"><span><i style="background:#0aa3c2"></i>{home}</span>
    <span><i style="background:#e8402a"></i>{away}</span></div></div>
</div></section>

<section class="sec"><div class="sh"><span class="n">情景热度 · 核心矛盾</span><span class="h">只示强弱，不标数值</span></div>
<div class="two" style="grid-template-columns:0.84fr 1.16fr">
  <div class="heat">{heat(card)}</div>
  <div><div class="narr"><b>核心矛盾</b>{narr}</div>{pt_html}</div>
</div></section>

<div class="note">本卡数据：近 5 场赛果 · 公开估值 · 情景推演示意（只示强弱，不标数值）。阵容人数、平均年龄、外籍占比本机暂无结构化来源，故不上行。</div>
<div class="foot"><div>数据来源：公开赛事数据 · 官方名单<br>身价：懂球帝联赛身价表</div>
<div><div class="b"><i></i>@阿飞·赛博聊球</div><div class="tag">#足球数据 #球队近况 #赛博聊球</div></div></div>
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
    ap = argparse.ArgumentParser(description="D 版单场深挖卡（合规形态）")
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
        h.write_text(card_html(c, data, i, len(ms)), encoding="utf-8")
        png = out / ("%02d_%s_%s.png" % (i, c.get("no", ""), c.get("home", "") + "vs" + c.get("away", "")))
        ok = shot(h, png)
        print(("  ✅ " if ok else "  ❌ ") + png.name +
              ("  %dKB" % (png.stat().st_size // 1024) if ok else ""))


if __name__ == "__main__":
    main()
