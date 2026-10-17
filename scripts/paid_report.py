# -*- coding: utf-8 -*-
"""付费内部资料生成器：单批（默认最新 _model_*.txt）→ 自包含 HTML（A4 可打印，每场两页）。

数据来源（全部本地产物，不联网）：
  state/batch/_model_<批次>.txt     后台模型全量输出（λ双法/胜平负/让球/总进球/比分Top8/EV/三重检查）
  state/records/_ext_<日期>.json    外部公开赛前预报（Sports Mole）
  state/records/_ext_<日期>af.json  外部数据接口算法（API-Football，只用方向）
  📝文章/<日期>/小红书_*/cards.json 场次号/开赛时间/展示队名
  state/odds.sqlite                 盘口位移样本（有则展示，无则标注）

用法：
  python scripts/paid_report.py                       # 自动取 state/batch 里最新的 _model_*.txt
  python scripts/paid_report.py --model state/batch/_model_20261017_sat.txt --out "📝文章/20261017/xxx.html"
  python scripts/paid_report.py                      # 只出 A4 打印版 HTML（PDF 已默认关闭）
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
BATCH_DIR = STATE / "batch"
RECORDS = STATE / "records"

RE_HEAD = re.compile(r"^周六(\d{3})\s+(\S+)\s+vs\s+(\S+)\s+\[(.+?)\]\s+id=(\d+)")
RE_F = r"([\d.]+)%"

# 外媒理由中文摘要（付费资料里给读者看得懂的一句话；按展示队名键）
SM_GIST = {
    "埃弗顿": "客队火力是真强，但客场也能崩——节前在布伦特福德 0-3 就是例子，主队主场三场不败有得打。",
    "曼城": "主场气氛与实力差距都在主队这边，预报认为是一场干净的完胜，没给客队留进球。",
    "布伦特": "两队近六次交锋场场至少两个球，预报干脆给了一场对攻平局。",
    "贝蒂斯": "客队进攻端状态极热，主队主场虽强但扛不住对攻，预报给客队两球取胜。",
    "巴伦西亚": "主队主场刚被打崩，客队客场更稳，但预报只给一球优势，判成平局。",
}


def fnum(s: str) -> float:
    return float(s)


# ---------------------------------------------------------------- 解析模型文本
def parse_model(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    blocks: list[list[str]] = []
    cur: list[str] = []
    for ln in lines:
        if ln.startswith("======"):
            if cur:
                blocks.append(cur)
            cur = []
            continue
        cur.append(ln)
    if cur:
        blocks.append(cur)

    out: list[dict] = []
    for b in blocks:
        m = None
        for ln in b:
            m = RE_HEAD.match(ln.strip())
            if m:
                break
        if not m:
            continue
        d: dict = {
            "no": "周六" + m.group(1), "home": m.group(2), "away": m.group(3),
            "league": m.group(4), "mid": m.group(5), "warn": [], "top": [],
        }
        for ln in b:
            s = ln.strip()
            if s.startswith("备注："):
                d["note"] = s[3:].strip()
            elif s.startswith("方法1"):
                nums = re.findall(r"(\d+\.\d+)", s)
                if len(nums) >= 2:
                    d["lam1"] = [fnum(nums[0]), fnum(nums[1])]
            elif s.startswith("方法2"):
                nums = re.findall(r"(\d+\.\d+)", s)
                if len(nums) >= 2:
                    d["lam2"] = [fnum(nums[0]), fnum(nums[1])]
            elif s.startswith("综合 λ"):
                nums = re.findall(r"(\d+\.\d+)", s)
                d["lam"] = [fnum(nums[0]), fnum(nums[1])]
            elif s.startswith("进球期望合计"):
                d["lam_total"] = fnum(re.search(r"=\s*([\d.]+)", s).group(1))
            elif s.startswith("修正明细"):
                d["fix"] = s.split(":", 1)[1].strip() if ":" in s else s
            elif s.startswith("伤停") and "λ主×(1" in s:
                d["inj"] = s
            elif s.startswith("胜平负"):
                nums = re.findall(RE_F, s)
                if len(nums) == 6:
                    d["p"] = [fnum(x) for x in nums[:3]]
                    d["mk"] = [fnum(x) for x in nums[3:]]
            elif s.startswith("Edge(模型-市场)") and "p_edge" not in d:
                pp = re.findall(r"([+-][\d.]+)pp", s)
                if len(pp) == 3:
                    d["p_edge"] = [fnum(x) for x in pp]
            elif s.startswith("固定奖金"):
                nums = re.findall(r"(\d+\.\d+)", s)
                if len(nums) >= 3:
                    d["odds"] = [fnum(x) for x in nums[:3]]
                    d["payout"] = fnum(nums[3]) if len(nums) > 3 else None
            elif s.startswith("让球("):
                mm = re.search(r"让球\(([+-]?\d+)\)", s)
                d["hand"] = int(mm.group(1)) if mm else 0
                nums = re.findall(RE_F, s)
                if len(nums) == 6:
                    d["hp"] = [fnum(x) for x in nums[:3]]
                    d["hmk"] = [fnum(x) for x in nums[3:]]
            elif s.startswith("Edge(模型-市场)") and "h_edge" not in d:
                pp = re.findall(r"([+-][\d.]+)pp", s)
                if len(pp) == 3:
                    d["h_edge"] = [fnum(x) for x in pp]
            elif s.startswith("胜率(不含平)"):
                nums = re.findall(RE_F, s)
                if len(nums) >= 2:
                    d["win_nodraw"] = [fnum(nums[0]), fnum(nums[1])]
            elif s.startswith("总进球"):
                d["goals"] = [fnum(x) for x in re.findall(r"\d+:\s*([\d.]+)%", s)]
            elif s.startswith("大1.5"):
                nums = re.findall(RE_F, s)
                for k, v in zip(["over15", "over25", "over35", "btts"], nums):
                    d[k] = fnum(v)
            elif re.match(r"^\d+-\d+\s+[\d.]+%", s):
                mm = re.match(r"^(\d+)-(\d+)\s+([\d.]+)%\s+([\d.]+)\s+EV\s+([+-][\d.]+)$", s)
                if mm:
                    d["top"].append({"s": f"{mm.group(1)}-{mm.group(2)}", "p": fnum(mm.group(3)),
                                     "odd": fnum(mm.group(4)), "ev": fnum(mm.group(5))})
            elif s.startswith("⚠️") or s.startswith("🔴"):
                d["warn"].append(s)
        if "p" in d:
            out.append(d)
    return out


# ---------------------------------------------------------------- 外部预测
def load_ext(day: str) -> list[dict]:
    items: list[dict] = []
    for name in (f"_ext_{day}.json", f"_ext_{day}af.json"):
        p = RECORDS / name
        if not p.exists():
            continue
        try:
            j = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:  # noqa: BLE001
            continue
        for it in j.get("items", []):
            it["_src"] = name
            items.append(it)
    return items


def dir_of(pred: str, predicted_dir: str = "") -> str | None:
    if predicted_dir:
        return predicted_dir
    m = re.search(r"(\d+)\s*-\s*(\d+)", pred or "")
    if not m:
        return None
    h, a = int(m.group(1)), int(m.group(2))
    return "主胜" if h > a else ("平" if h == a else "客胜")


def match_ext(items: list[dict], home: str, away: str) -> dict:
    got = {"sm": None, "af": None}
    for it in items:
        h, a = it.get("home", ""), it.get("away", "")
        if not h or not a:
            continue
        if (home.startswith(h[:2]) or h.startswith(home[:2])) and (away.startswith(a[:2]) or a.startswith(away[:2])):
            if it["_src"].endswith("af.json"):
                got["af"] = got["af"] or it
            else:
                got["sm"] = got["sm"] or it
    return got


def load_cards(date_dir: Path) -> dict:
    idx: dict = {}
    for p in sorted(date_dir.glob("小红书_*/cards.json")):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for m in j.get("matches", []):
            idx[str(m.get("sporttery_match_id", ""))] = m
    return idx


# ---------------------------------------------------------------- 信心指数
def confidence(d: dict, ext: dict) -> dict:
    note = d.get("note", "")
    hs = [int(x) for x in re.findall(r"主场\s*(\d+)\s*场", note)]
    as_ = [int(x) for x in re.findall(r"客场\s*(\d+)\s*场", note)]
    both = re.search(r"样本都是\s*(\d+)\s*场", note)
    n = min(hs[0] if hs else 0, as_[0] if as_ else 0) or (int(both.group(1)) if both else 0)
    w1 = 20 if n >= 4 else 16 if n == 3 else 10 if n == 2 else 4 if n == 1 else 8

    l1, l2 = d.get("lam1"), d.get("lam2")
    if l1 and l2:
        gaps = [abs(a - b) / ((a + b) / 2) for a, b in zip(l1, l2)]
        g = sum(gaps) / 2
    else:
        g = 0.25
    w2 = max(0.0, 20 * (1 - g / 0.45))

    dirs = ["主胜", "平", "客胜"]
    mdl = dirs[max(range(3), key=lambda i: d["p"][i])]
    mkt = dirs[max(range(3), key=lambda i: d["mk"][i])]
    votes = [mkt == mdl]
    for k in ("sm", "af"):
        e = ext.get(k)
        if e:
            dd = dir_of(e.get("predicted", ""), e.get("predicted_dir", ""))
            if dd:
                votes.append(dd == mdl)
    agree = sum(1 for v in votes if v)
    w3 = {3: 25, 2: 17, 1: 8, 0: 2}.get(agree, 8)

    maxpp = max(abs(x) for x in d["p_edge"]) if "p_edge" in d else 99
    w4 = 25 if maxpp <= 3 else 21 if maxpp <= 6 else 17 if maxpp <= 10 else 11 if maxpp <= 15 else 6 if maxpp <= 20 else 3

    top3 = sum(t["p"] for t in d["top"][:3])
    w5 = min(10.0, 10 * top3 / 26)

    total = w1 + w2 + w3 + w4 + w5
    grade = "A · 高" if total >= 78 else "B · 中高" if total >= 66 else "C · 中" if total >= 52 else "D · 谨慎"
    return {
        "total": round(total), "grade": grade, "n_sample": n, "gap": round(g * 100),
        "agree": agree, "maxpp": maxpp, "top3": round(top3, 1),
        "w1": round(w1), "w2": round(w2), "w3": w3, "w4": w4, "w5": round(w5, 1),
        "model_dir": mdl, "market_dir": mkt,
    }


def load_quotes(mids: set[str]) -> dict:
    p = STATE / "odds.sqlite"
    got: dict = {}
    if not p.exists():
        return got
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        for mid in mids:
            rows = list(con.execute(
                "select taken_at,market,line,h,d,a from quote where match_id=? order by taken_at", (mid,)))
            if rows:
                got[mid] = rows
        con.close()
    except Exception:  # noqa: BLE001
        pass
    return got


# ---------------------------------------------------------------- HTML
CSS = """
:root{--paper:#F7F4EF;--ink:#171614;--muted:#6F6A62;--rule:#E0D9CE;--accent:#8C5A3C;
--gold:#A9812F;--deep:#22201D;--green:#2F6B4F;--red:#9B3B2F;--card:#FFFDFA}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#E6E2DA;color:var(--ink);
font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
.page{width:210mm;height:297mm;background:var(--paper);margin:0 auto 8mm;padding:15mm 15mm 13mm;
position:relative;box-shadow:0 2px 18px rgba(0,0,0,.10);overflow:hidden}
.serif{font-family:"Songti SC","Source Han Serif SC","Noto Serif SC",serif}
.rh{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--rule);
padding-bottom:2.2mm;margin-bottom:6mm;font-size:8.2pt;color:var(--muted);letter-spacing:.06em}
.rh b{color:var(--accent);font-weight:600}
.rf{position:absolute;left:15mm;right:15mm;bottom:7mm;display:flex;justify-content:space-between;
font-size:7.4pt;color:var(--muted);border-top:1px solid var(--rule);padding-top:2mm}
/* 封面 */
.cover{padding-top:26mm}
.kicker{display:inline-block;background:var(--accent);color:#fff;font-size:9pt;letter-spacing:.24em;
padding:2.2mm 5mm;margin-bottom:11mm}
.cover h1{font-size:30pt;line-height:1.24;letter-spacing:.01em;margin-bottom:5mm}
.cover .sub{font-size:11pt;color:var(--muted);line-height:1.9;max-width:152mm}
.cover .meta{margin-top:8mm;font-size:8.8pt;color:var(--muted);line-height:2}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);margin:11mm 0 7mm;border-top:1px solid var(--rule);
border-bottom:1px solid var(--rule)}
.kpi{padding:5.5mm 4mm;border-right:1px solid var(--rule)}
.kpi:last-child{border-right:none}
.kpi .v{font-size:20pt;font-weight:700;color:var(--accent);line-height:1.1}
.kpi .l{font-size:8pt;color:var(--muted);margin-top:2mm;line-height:1.6}
.toc{margin-top:6mm}
.toc .row{display:flex;justify-content:space-between;align-items:center;padding:2.4mm 0;
border-bottom:1px dotted var(--rule);font-size:9.6pt}
.toc .row .n{color:var(--accent);font-weight:600;width:17mm}
.toc .row .t{flex:1}
.toc .row .c{color:var(--muted);font-size:8.2pt;width:44mm;text-align:right;white-space:nowrap}
/* 通用 */
h2.sec{font-size:14pt;margin:0 0 3.4mm;padding-left:3.4mm;border-left:3px solid var(--accent);line-height:1.3}
h4.blkttl{font-size:9.2pt;margin:4mm 0 2mm;color:var(--deep);letter-spacing:.02em}
table.ov{width:100%;border-collapse:collapse;font-size:8.6pt}
table.ov th{text-align:left;color:var(--muted);font-weight:500;font-size:7.6pt;letter-spacing:.05em;
border-bottom:1px solid var(--ink);padding:2.2mm 1.6mm}
table.ov td{padding:2.4mm 1.6mm;border-bottom:1px solid var(--rule);vertical-align:middle}
.bar{height:2mm;background:#E6DFD3;position:relative;width:20mm;display:inline-block;vertical-align:middle}
.bar i{position:absolute;left:0;top:0;bottom:0;background:var(--accent)}
/* 单场头 */
.mhead{margin-bottom:4mm}
.mtop{display:flex;justify-content:space-between;align-items:flex-start;gap:6mm}
.mtag{font-size:8.4pt;color:var(--muted);letter-spacing:.04em;line-height:1.85}
.mtag b{color:var(--accent);font-weight:600}
.mtitle{font-size:22pt;line-height:1.22;margin:2mm 0 1.4mm}
.mtitle .vs{font-size:11pt;color:var(--muted);margin:0 2.2mm;font-weight:400}
.ring{flex:0 0 32mm;text-align:center}
.verdict{display:grid;grid-template-columns:repeat(3,1fr);gap:2.4mm;margin:3mm 0 5mm}
.verdict div{background:var(--card);border:1px solid var(--rule);padding:3mm 3.2mm}
.verdict .k{font-size:7.4pt;color:var(--muted);letter-spacing:.1em}
.verdict .v{font-size:11pt;font-weight:600;margin-top:1.2mm}
.verdict .p{font-size:7.8pt;color:var(--muted);margin-top:.8mm}
.cards2{display:grid;grid-template-columns:1fr 1fr;gap:3.2mm;margin-bottom:4mm}
.blk{background:var(--card);border:1px solid var(--rule);padding:3.6mm 4mm}
.blk h4{font-size:9pt;margin-bottom:2.2mm;color:var(--deep);display:flex;align-items:center;gap:2mm}
.blk h4 em{font-style:normal;font-size:7.2pt;color:var(--accent);letter-spacing:.12em;border:1px solid var(--accent);
padding:.4mm 1.5mm}
.blk p{font-size:8.4pt;line-height:1.8;color:#3A3733}
.blk p+p{margin-top:1.4mm}
.blk .kv{font-size:8.2pt;line-height:1.85}
.blk .kv span{color:var(--muted)}
.num-hi{color:var(--accent);font-weight:700}
.hbar{display:flex;height:5.4mm;margin:2mm 0 1.2mm;font-size:7pt;color:#fff;font-weight:600}
.hbar div{display:flex;align-items:center;justify-content:center;white-space:nowrap;overflow:hidden}
.hbar .a{background:#7C4A32}.hbar .b{background:#B9A48C}.hbar .c{background:#3F4A55}
.legend{display:flex;justify-content:space-between;font-size:7.2pt;color:var(--muted)}
.dims{display:grid;gap:2.4mm;font-size:8.2pt}
.dim{display:grid;grid-template-columns:38mm 1fr 15mm;align-items:center;gap:3mm}
.dim .tr{height:2.2mm;background:#E6DFD3;position:relative}
.dim .tr i{position:absolute;left:0;top:0;bottom:0;background:var(--gold)}
.dim .vl{text-align:right;color:var(--muted);font-size:7.6pt}
table.sc{width:100%;border-collapse:collapse;font-size:8pt}
table.sc th{font-size:7pt;color:var(--muted);font-weight:500;text-align:right;padding:1.4mm 1.2mm;
border-bottom:1px solid var(--ink)}
table.sc th:first-child{text-align:left}
table.sc td{padding:1.3mm 1.2mm;text-align:right;border-bottom:1px solid var(--rule)}
table.sc td:first-child{text-align:left;font-weight:600}
table.sc .up{color:var(--green);font-weight:600}
table.sc .dn{color:var(--muted)}
.gauges{display:grid;grid-template-columns:1fr 1fr;gap:2.2mm;margin-top:1.6mm}
.gauges .g{background:var(--card);border:1px solid var(--rule);padding:2.2mm 2.8mm;display:flex;
justify-content:space-between;font-size:8pt}
.gauges .g b{color:var(--accent)}
table.three{width:100%;border-collapse:collapse;font-size:8.2pt}
table.three th{text-align:left;font-size:7.2pt;color:var(--muted);font-weight:500;padding:1.6mm 1.6mm;
border-bottom:1px solid var(--ink)}
table.three td{padding:2mm 1.6mm;border-bottom:1px solid var(--rule);vertical-align:top;line-height:1.65}
table.three td:first-child{color:var(--muted);width:26mm}
table.three .gist{color:#3A3733}
table.three .src{color:var(--muted);font-size:7.4pt}
.warns{margin-top:3.4mm;font-size:7.9pt;line-height:1.8;color:#5A4B3C;background:#F1EADC;
border-left:2.5px solid var(--gold);padding:2.8mm 3.6mm}
.warns b{color:var(--red)}
.note{font-size:7.6pt;color:var(--muted);line-height:1.8;margin-top:2.6mm}
.plain{font-size:8.8pt;line-height:1.95;color:#3A3733}
.plain h3{font-size:10.2pt;margin:5mm 0 1.6mm;color:var(--deep)}
.plain ol,.plain ul{margin-left:4.6mm}
.plain li{margin-bottom:1.3mm}
.disclaim{margin-top:6mm;border:1px solid var(--rule);background:var(--card);padding:4.4mm 5mm;
font-size:7.8pt;color:var(--muted);line-height:1.9}
@media print{
  body{background:#fff}
  .page{margin:0;box-shadow:none;page-break-after:always}
  .page:last-child{page-break-after:auto}
  @page{size:A4;margin:0}
}
@media screen and (max-width:900px){.page{width:100%;height:auto;padding:6vw}}
"""


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


RE_DATE_QUIRK = re.compile(r"(\d{1,2}) 比 (\d{1,2})(?= (?:欧冠|欧联|欧协|联赛杯|英联杯|足总杯|国王杯))")


def clean_note(s: str) -> str:
    """模型备注把日期写成「10 比 15 欧冠」，公开资料里改成 10/15 免得和比分混淆。"""
    return RE_DATE_QUIRK.sub(r"\1/\2", s)


def bar_html(v: float, mx: float, w: str = "20mm") -> str:
    pct = max(0, min(100, v / mx * 100))
    return f'<span class="bar" style="width:{w}"><i style="width:{pct:.0f}%"></i></span>'


def ring_svg(total: int) -> str:
    r, c = 26, 2 * 3.14159 * 26
    on = c * total / 100
    col = "#8C5A3C" if total >= 66 else "#A9812F" if total >= 52 else "#9B3B2F"
    return f"""<svg viewBox="0 0 64 64" width="82" height="82">
<circle cx="32" cy="32" r="26" fill="none" stroke="#E6DFD3" stroke-width="5"/>
<circle cx="32" cy="32" r="26" fill="none" stroke="{col}" stroke-width="5" stroke-linecap="round"
 stroke-dasharray="{on:.1f} {c:.1f}" transform="rotate(-90 32 32)"/>
<text x="32" y="34" text-anchor="middle" font-size="19" font-weight="700" fill="{col}"
 font-family="system-ui">{total}</text>
<text x="32" y="47" text-anchor="middle" font-size="7" fill="#6F6A62">信心指数</text></svg>"""


def struct_bar(p: list[float], labels: list[str], cls: list[str]) -> str:
    seg = "".join(f'<div class="{c}" style="width:{v:.1f}%">{lab} {v:.1f}%</div>'
                  for v, lab, c in zip(p, labels, cls))
    return f'<div class="hbar">{seg}</div>'


def dims_html(c: dict) -> str:
    rows = [
        ("样本厚度", c["w1"], 20, f"主客分离样本 {c['n_sample']} 场"),
        ("双法收敛", c["w2"], 20, f"两条 λ 平均相对差 {c['gap']}%"),
        ("三方一致", c["w3"], 25, f"定价/公开预报/接口算法与模型同向 {c['agree']}/3"),
        ("分歧可控", c["w4"], 25, f"胜平负最大偏差 {c['maxpp']:.1f}pp"),
        ("比分集中", c["w5"], 10, f"Top3 比分合计 {c['top3']}%"),
    ]
    out = []
    for nm, v, mx, tip in rows:
        pct = max(0, min(100, v / mx * 100))
        out.append(f'<div class="dim"><div>{nm}<br><span style="font-size:6.8pt;color:#8C8378">{tip}</span></div>'
                   f'<div class="tr"><i style="width:{pct:.0f}%"></i></div>'
                   f'<div class="vl">{v:g}/{mx}</div></div>')
    return '<div class="dims">' + "".join(out) + "</div>"


def goals_chart(goals: list[float]) -> str:
    if not goals:
        return ""
    mx = max(goals)
    cells = []
    for i, g in enumerate(goals):
        lab = "7+" if i == 7 else str(i)
        h = max(2, g / mx * 24)
        cells.append(
            f'<div style="flex:1;text-align:center">'
            f'<div style="height:24mm;display:flex;align-items:flex-end;justify-content:center">'
            f'<div style="width:70%;height:{h:.1f}mm;background:{"#8C5A3C" if g >= 14 else "#C3B3A0"}"></div></div>'
            f'<div style="font-size:6.8pt;color:#6F6A62;margin-top:.6mm">{g:.1f}%</div>'
            f'<div style="font-size:6.8pt;color:#9A9186">{lab}</div></div>')
    return ('<div style="display:flex;align-items:flex-end;gap:.4mm;margin-top:1.6mm">' + "".join(cells) + "</div>"
            '<div style="font-size:6.8pt;color:#9A9186;text-align:center;margin-top:.8mm">总进球数分布（模型，2 万次抽样）</div>')


def pick_score(top: list[dict], outcome: str) -> str:
    """按方向挑比分：主胜挑主>客里概率最高的，平挑主=客的，客胜反过来。"""
    def sign(s: str) -> int:
        h, a = s.split("-")
        return (int(h) > int(a)) - (int(h) < int(a))

    want = {"主胜": 1, "平": 0, "客胜": -1}.get(outcome, 1)
    for t in top:
        if sign(t["s"]) == want:
            return t["s"]
    return top[0]["s"]


def verdicts(d: dict) -> list[dict]:
    order = sorted(range(3), key=lambda i: -d["p"][i])
    names = ["主胜", "平", "客胜"]
    hi = [pick_score(d["top"], names[i]) for i in order]
    out = [{"k": "首选", "v": names[order[0]], "p": d["p"][order[0]], "s": hi[0]}]
    if d["p"][order[1]] >= 15:
        out.append({"k": "次选", "v": names[order[1]], "p": d["p"][order[1]], "s": hi[1]})
    else:
        big = "大 2.5" if d.get("over25", 0) >= 60 else ("小 2.5" if d.get("over25", 0) <= 40 else "大 1.5")
        out.append({"k": "次选", "v": big, "p": d.get("over25", 0), "s": hi[1]})
    out.append({"k": "防范", "v": names[order[2]] + " 或 " + hi[2], "p": d["p"][order[2]], "s": hi[2]})
    return out


def hand_comment(ho: int, edge: list[float]) -> str:
    mx = max(edge, key=abs)
    side = "主队" if edge.index(mx) == 0 else ("平局" if edge.index(mx) == 1 else "客队")
    if abs(mx) >= 10:
        return f"让球一侧模型与定价差了 {mx:+.1f}pp，方向落在{side}，这类位置先看样本再看分歧。"
    return f"让球结构两边接近（最大差 {mx:+.1f}pp），这个盘口本身没有明显错位。"


def overview_hint(matches: list[dict]) -> str:
    best = max(matches, key=lambda m: m["conf"]["total"])
    worst = min(matches, key=lambda m: m["conf"]["total"])
    big = [m for m in matches if m["conf"]["maxpp"] >= 15]
    s = (f"信心最高的是 {best['no']} {best['home']}vs{best['away']}"
         f"（{best['conf']['total']} 分，{best['conf']['grade']}），"
         f"最低的是 {worst['no']} {worst['home']}vs{worst['away']}（{worst['conf']['total']} 分）。")
    if big:
        s += "分歧超过 15 个百分点的有 " + "、".join(
            f"{m['no']}（{m['conf']['maxpp']:.1f}pp）" for m in big) + \
            "，这几场模型侧的数据缺口要先承认，只做方向参考。"
    return s


def match_page_a(m: dict, idx: int, total: int, n: int) -> str:
    c, p, mk = m["conf"], m["p"], m["mk"]
    hp, hmk = m.get("hp", [0, 0, 0]), m.get("hmk", [0, 0, 0])
    ho = m.get("hand", 0)
    ho_s = f"+{ho}" if ho > 0 else str(ho)
    payout = m.get("payout") or 0
    over = sum(100 / x for x in m["odds"])
    vhtml = "".join(f'<div><div class="k">{v["k"]}</div><div class="v">{v["v"]}</div>'
                    f'<div class="p">模型 {v["p"]:.1f}% · 比分 {v["s"]}</div></div>' for v in verdicts(m))

    sm, af = m["ext"].get("sm"), m["ext"].get("af")
    if sm and sm.get("predicted"):
        gist = SM_GIST.get(sm.get("home", ""), "")
        sm_row = (f'<b>{esc(sm["predicted"])}</b>'
                  + (f'<br><span class="gist">{esc(gist)}</span>' if gist else "")
                  + f'<br><span class="src">原文：{esc((sm.get("note") or "")[:190])}…</span>')
    else:
        sm_row = '<span class="src">本篇未取到公开预报（该轮汇总页只覆盖部分场次）</span>'
    if af:
        af_row = (f'方向 <b>{esc(af.get("predicted_dir", ""))}</b>'
                  f'<br><span class="src">接口原文：{esc((af.get("note") or "")[:120])}</span>')
    else:
        af_row = '<span class="src">本篇未取到该源</span>'

    return f"""
<section class="page">
  <div class="rh"><span><b>{m["no"]}</b> · {m["league"]} · {m["kick"]} · 结构与结论</span>
  <span>第 {idx} 页 / 共 {total} 页</span></div>
  <div class="mhead">
    <div class="mtop">
      <div style="flex:1">
        <div class="mtag"><b>{m["no"]}</b> · {m["league"]} · {m["kick"]} 开赛 · λ 合计 {m.get("lam_total", 0):.2f}</div>
        <div class="mtitle serif">{m["home"]}<span class="vs">vs</span>{m["away"]}</div>
        <div class="mtag">模型方向 <b>{c["model_dir"]}</b> · 定价方向 {c["market_dir"]} ·
        外部同向 <b>{c["agree"]}/3</b> · 档位 <b>{c["grade"]}</b></div>
      </div>
      <div class="ring">{ring_svg(c["total"])}</div>
    </div>
  </div>

  <div class="verdict">{vhtml}</div>

  <div class="cards2">
    <div class="blk">
      <h4><em>盘口</em>胜平负结构</h4>
      {struct_bar(p, ["主", "平", "客"], ["a", "b", "c"])}
      <div class="legend"><span>上：模型</span><span>最大偏差 {c["maxpp"]:.1f}pp</span></div>
      {struct_bar(mk, ["主", "平", "客"], ["a", "b", "c"])}
      <div class="legend"><span>下：官方定价去水后</span><span>返奖率 {payout:.1f}%</span></div>
      <p style="margin-top:2.2mm">固定奖金 <span class="num-hi">{m["odds"][0]:.2f} / {m["odds"][1]:.2f} / {m["odds"][2]:.2f}</span>，
      三项隐含概率合计 {over:.1f}%，结构成本 {over - 100:.1f} 个百分点。</p>
      <p>三项偏差：主 {m["p_edge"][0]:+.1f}pp / 平 {m["p_edge"][1]:+.1f}pp / 客 {m["p_edge"][2]:+.1f}pp。
      {esc(edge_comment(c["maxpp"], c["model_dir"], c["market_dir"]))}</p>
    </div>
    <div class="blk">
      <h4><em>盘口</em>让球（{ho_s}）结构</h4>
      {struct_bar(hp, ["主", "平", "客"], ["a", "b", "c"])}
      <div class="legend"><span>上：模型（让球后）</span><span>偏差 {max(abs(x) for x in m.get("h_edge", [0])):.1f}pp</span></div>
      {struct_bar(hmk, ["主", "平", "客"], ["a", "b", "c"])}
      <div class="legend"><span>下：定价去水后</span></div>
      <p style="margin-top:2.2mm">去掉平局后的胜负拆分：主 {m.get("win_nodraw", [0, 0])[0]:.1f}% /
      客 {m.get("win_nodraw", [0, 0])[1]:.1f}%。</p>
      <p>{esc(hand_comment(ho, m.get("h_edge", [0, 0, 0])))}</p>
    </div>
  </div>

  <h4 class="blkttl">三方对照：同一场球，四种口径</h4>
  <table class="three">
    <tr><th>来源</th><th>给出的结论</th></tr>
    <tr><td>后台模型</td><td>主 {p[0]:.1f}% / 平 {p[1]:.1f}% / 客 {p[2]:.1f}%；让球（{ho_s}）
    主 {hp[0]:.1f}% / 平 {hp[1]:.1f}% / 客 {hp[2]:.1f}%；大 2.5 <b>{m.get("over25", 0):.1f}%</b>，
    双方进球 {m.get("btts", 0):.1f}%；比分最靠前 {m["top"][0]["s"]}（{m["top"][0]["p"]}%）</td></tr>
    <tr><td>官方定价</td><td>去水后 主 {mk[0]:.1f}% / 平 {mk[1]:.1f}% / 客 {mk[2]:.1f}%；固定奖金
    {m["odds"][0]:.2f} / {m["odds"][1]:.2f} / {m["odds"][2]:.2f}，返奖率 {payout:.1f}%</td></tr>
    <tr><td>公开赛前预报</td><td>{sm_row}</td></tr>
    <tr><td>数据接口算法</td><td>{af_row}</td></tr>
  </table>

  <div class="warns">
    <b>这一页怎么读</b><br>
    ①先看两行的色块是否同侧：同侧且长度差小，说明模型与定价互相印证；
    差得远时不要急着认定哪边更准，先看第二页的分歧是否来自样本薄或伤停未反映。<br>
    ②让球盘比胜平负更能看出错位：同一方向上让球偏差比胜平负偏差更大，说明分歧集中在「赢几个」而不是「谁赢」。<br>
    ③外部两源只是参照系，公开预报给的是比分、接口算法只给方向，它们不改变模型结论，只用来标出「三家站成几排」。
  </div>
  <div class="rf"><span>阿飞 · 赛博聊球 · 内部资料 · {m["no"]}</span>
  <span>仅统计 90 分钟 · 不构成任何购买建议</span></div>
</section>"""


def edge_comment(maxpp: float, mdl: str, mkt: str) -> str:
    if mdl == mkt:
        if maxpp <= 6:
            return f"两套算法方向一致、幅度也接近（最大 {maxpp:.1f}pp），这是本份里可信度较高的位置之一。"
        return f"方向一致，但幅度差 {maxpp:.1f} 个百分点：定价比模型更极端，说明市场在押某件模型还没反映的事。"
    return f"方向相反（模型 {mdl}、定价 {mkt}），偏差 {maxpp:.1f}pp，属于必须交代分歧的场次。"


def match_page_b(m: dict, idx: int, total: int) -> str:
    c = m["conf"]
    ho = m.get("hand", 0)
    ho_s = f"+{ho}" if ho > 0 else str(ho)
    ev_up = [t for t in m["top"] if t["ev"] > 0]
    ev_txt = "；".join(f'{t["s"]}（模型 {t["p"]}%，定价 {t["odd"]:.2f}，溢价 {t["ev"]:+.2f}）' for t in ev_up) \
        if ev_up else "Top8 里没有正溢价格子，定价把主流比分覆盖得比较紧，这场价值不在比分单项上。"
    q = m.get("quotes") or []
    q_txt = (f"本场抓到 {len(q)} 条定价快照，可看位移。" if q
             else "本场没有定价位移快照（采集器只留下 10-12 的样本），盘口解读只基于当前固定奖金。")
    return f"""
<section class="page">
  <div class="rh"><span><b>{m["no"]}</b> · {m["league"]} · {m["home"]}vs{m["away"]} · 指数与细节</span>
  <span>第 {idx} 页 / 共 {total} 页</span></div>

  <h2 class="sec">信心指数 {c["total"]} / 100 · {c["grade"]}</h2>
  <div class="cards2" style="grid-template-columns:1.15fr 1fr">
    <div class="blk">
      <h4><em>五维</em>这份分析有多可靠</h4>
      {dims_html(c)}
      <p style="margin-top:2.4mm;color:#6F6A62;font-size:7.8pt">总分 60 以上表示方向可用、幅度要打折；
      本场落在「{c["grade"]}」档，用法见附录。</p>
    </div>
    <div class="blk">
      <h4><em>比分</em>定价漏洞（溢价 = 模型概率 × 定价 − 1）</h4>
      <p>{esc(ev_txt)}</p>
      <table class="sc" style="margin-top:2mm">
        <tr><th>比分</th><th>模型</th><th>定价</th><th>溢价</th></tr>
        {"".join(f'<tr><td>{t["s"]}</td><td>{t["p"]:.1f}%</td><td>{t["odd"]:.2f}</td>'
                 f'<td class="{"up" if t["ev"] > 0 else "dn"}">{t["ev"]:+.2f}</td></tr>' for t in m["top"][:8])}
      </table>
    </div>
  </div>

  <div class="cards2">
    <div class="blk">
      <h4><em>进球</em>大小球与双方进球</h4>
      <div class="gauges">
        <div class="g"><span>大 1.5</span><b>{m.get("over15", 0):.1f}%</b></div>
        <div class="g"><span>大 2.5</span><b>{m.get("over25", 0):.1f}%</b></div>
        <div class="g"><span>大 3.5</span><b>{m.get("over35", 0):.1f}%</b></div>
        <div class="g"><span>双方进球</span><b>{m.get("btts", 0):.1f}%</b></div>
      </div>
      {goals_chart(m.get("goals", []))}
    </div>
    <div class="blk">
      <h4><em>λ</em>两套算法与修正明细</h4>
      <div class="kv">
        <div><span>方法一（实际数据，主客分离）</span><br>{m.get("lam1", [0, 0])[0]:.3f} / {m.get("lam1", [0, 0])[1]:.3f}</div>
        <div><span>方法二（定价反推）</span><br>{m.get("lam2", [0, 0])[0]:.3f} / {m.get("lam2", [0, 0])[1]:.3f}</div>
        <div><span>综合 λ（合计 {m.get("lam_total", 0):.2f}）</span><br><b>{m.get("lam", [0, 0])[0]:.3f} / {m.get("lam", [0, 0])[1]:.3f}</b></div>
        <div style="margin-top:1.4mm"><span>修正</span><br>{esc(clean_note(m.get("fix", "—")))}</div>
        {f'<div style="margin-top:1.4mm"><span>伤停修正</span><br>{esc(clean_note(m.get("inj", "")))}</div>' if m.get("inj") else ""}
      </div>
    </div>
  </div>

  <h4 class="blkttl">赛果底子（公开数据，用来判断模型有没有吃错样本）</h4>
  <div class="blk">
    <p>{esc(clean_note(m.get("note") or "—"))}</p>
  </div>

  <div class="warns">
    <b>风险与不确定</b><br>
    {"".join(f"· {esc(w)}<br>" for w in (m.get("warn") or [])) or "· 本场没有触发预警项。<br>"}
    · {esc(q_txt)}<br>
    · 让球盘口为 {ho_s}，若临场调整，让球一侧的偏差结论要重算；本份不含临场首发变动后的重算。
  </div>
  <div class="rf"><span>阿飞 · 赛博聊球 · 内部资料 · {m["no"]}</span>
  <span>仅统计 90 分钟 · 不构成任何购买建议</span></div>
</section>"""


def build_html(matches: list[dict], date_tag: str, stamp: str) -> str:
    n = len(matches)
    total = 2 + 2 * n + 1
    agree_all = sum(1 for m in matches if m["conf"]["agree"] == 3)
    big_edge = sum(1 for m in matches if m["conf"]["maxpp"] >= 10)
    avg_conf = sum(m["conf"]["total"] for m in matches) / max(1, n)
    leagues: dict[str, int] = {}
    for m in matches:
        leagues[m["league"]] = leagues.get(m["league"], 0) + 1
    league_txt = " / ".join(f"{k} {v}" for k, v in leagues.items())

    pages: list[str] = []
    toc_rows = "".join(
        f'<div class="row"><div class="n">{m["no"]}</div><div class="t">{m["home"]} vs {m["away"]}</div>'
        f'<div class="c">{m["kick"]} · {m["conf"]["grade"]}</div></div>' for m in matches)

    pages.append(f"""
<section class="page cover">
  <div class="rh"><span><b>阿飞 · 赛博聊球</b> · 内部资料</span><span>第 1 页 / 共 {total} 页</span></div>
  <div class="kicker">付费内部资料 · 全维度复盘</div>
  <h1 class="serif">{date_tag} 六场<br>盘口结构 · 信心指数 · 全维度拆解</h1>
  <div class="sub">后台模型 × 官方定价 × 外部公开预报，三条线并排。每场分两页：第一页给结构、让球错位与三方对照，
  第二页给信心五维打分、比分定价漏洞、进球分布、λ 修正明细与风险提示。数据全部来自公开赛果与公开定价，
  只统计 90 分钟常规时间。</div>
  <div class="kpis">
    <div class="kpi"><div class="v">{n}</div><div class="l">覆盖场次<br>{league_txt}</div></div>
    <div class="kpi"><div class="v">{avg_conf:.0f}</div><div class="l">平均信心指数<br>满分 100</div></div>
    <div class="kpi"><div class="v">{big_edge}</div><div class="l">场次存在 ≥10 个百分点<br>模型与定价分歧</div></div>
    <div class="kpi"><div class="v">{agree_all}</div><div class="l">场次三方完全同向<br>（模型/定价/外部）</div></div>
  </div>
  <div class="toc">
    <div class="row" style="border-bottom:1px solid var(--ink);font-weight:600;color:var(--accent)">
    <div class="n">目录</div><div class="t">场次</div><div class="c">开赛 · 信心档</div></div>
    {toc_rows}
    <div class="row"><div class="n">附</div><div class="t">方法论、口径与免责说明</div><div class="c">末页</div></div>
  </div>
  <div class="meta">生成时间 {stamp} · 版本 v1.0（首批）· 内部复盘材料，不做公开投放<br>
  数据来源：公开赛果数据（竞彩官方定价、公开赛程与伤停、公开赛前预报）· 后台模型 v2.10.0<br>
  阅读顺序建议：先看第 2 页总览定位分歧，再按目录翻单场；每场第二页的「风险与不确定」比第一页更重要。</div>
  <div class="rf"><span>阿飞 · 赛博聊球 · 内部资料</span><span>仅统计 90 分钟 · 不构成任何购买建议</span></div>
</section>""")

    ov_rows = ""
    for m in matches:
        c = m["conf"]
        ov_rows += (
            f'<tr><td><b>{m["no"]}</b><br><span style="color:#8C8378;font-size:7.2pt">{m["league"]}</span></td>'
            f'<td>{m["home"]}<br><span style="color:#8C8378">{m["away"]}</span></td>'
            f'<td>{m["p"][0]:.1f} / {m["p"][1]:.1f} / {m["p"][2]:.1f}</td>'
            f'<td>{m["mk"][0]:.1f} / {m["mk"][1]:.1f} / {m["mk"][2]:.1f}</td>'
            f'<td>{c["model_dir"]}<br><span style="color:#8C8378;font-size:7.2pt">定价 {c["market_dir"]}</span></td>'
            f'<td><span style="color:{"#9B3B2F" if c["maxpp"] >= 10 else "#2F6B4F"};font-weight:600">'
            f'{c["maxpp"]:.1f}pp</span></td>'
            f'<td>{bar_html(c["total"], 100, "18mm")} <span style="font-size:7.2pt;color:#6F6A62">'
            f'{c["total"]} · {c["grade"]}</span></td></tr>')
    pages.append(f"""
<section class="page">
  <div class="rh"><span><b>总览</b> · 六场一页看完</span><span>第 2 页 / 共 {total} 页</span></div>
  <h2 class="sec">胜平负结构：模型 / 定价 / 偏差</h2>
  <table class="ov">
    <tr><th style="width:13mm">场次</th><th style="width:28mm">对阵</th>
    <th>模型 主/平/客</th><th>定价 主/平/客（去水）</th><th>方向</th><th>最大偏差</th><th>信心</th></tr>
    {ov_rows}
  </table>
  <div class="warns" style="margin-top:5mm">
    <b>怎么用这一页</b><br>
    ①「最大偏差」= 模型与官方定价在胜平负三项上的最大差值，<b>偏差越大不代表机会越大</b>：
    国内联赛的定价通常更贴近真实，超过 10 个百分点时先假定是模型侧数据有缺口（样本薄、伤停未反映、
    赛程强度不均），这类场次只做方向参考。<br>
    ②方向一致且偏差小的场次（≤6 个百分点）是两套算法互相印证的位置，本批最稳的两处就在这里。<br>
    ③信心指数不是胜率，它衡量的是这份分析本身有多可靠：样本厚度、两条 λ 是否收敛、三方是否同向、
    分歧是否可控、比分是否集中，五项加权。
  </div>
  <div class="note">本批速读：{esc(overview_hint(matches))}</div>
  <div class="note">阅读提示：每一场占两页。第一页看结构与让球错位，第二页看信心打分、比分定价与风险。
  所有百分比都是估值不是承诺；这里的每一项都建立在「90 分钟常规时间」口径上。</div>
  <div class="rf"><span>阿飞 · 赛博聊球 · 内部资料</span><span>仅统计 90 分钟 · 不构成任何购买建议</span></div>
</section>""")

    for i, m in enumerate(matches):
        pages.append(match_page_a(m, 3 + 2 * i, total, n))
        pages.append(match_page_b(m, 4 + 2 * i, total))

    pages.append(f"""
<section class="page">
  <div class="rh"><span><b>附录</b> · 方法论与口径</span><span>第 {total} 页 / 共 {total} 页</span></div>
  <h2 class="sec">这份资料怎么算出来的</h2>
  <div class="plain">
    <h3>一、进球期望（λ）两条路，再取一个值</h3>
    <ol>
      <li><b>实际数据法</b>：分开算主队主场、客队客场的攻防效率；样本不足（≤3 场）时按样本量权重混入近十场，
      避免两三轮就把一支球队定死。</li>
      <li><b>定价反推法</b>：从官方固定奖金反解出一条隐含的比分分布，得到第二条 λ。两条路差得多，
      说明市场与赛果之间存在叙事溢价，或者我方样本有缺口。</li>
      <li><b>取综合 λ</b> 后按状态、交锋、伤停做很小的修正（一般不超过 ±0.25），修正越大越说明基础数据有偏。</li>
    </ol>
    <h3>二、概率与比分</h3>
    <p>用泊松分布做 2 万次蒙特卡洛抽样，得到胜平负、让球、总进球与比分矩阵，抽样误差控制在 0.5 个百分点以内，
    所以正文百分比保留一位小数。所有结果<b>只统计 90 分钟常规时间</b>，加时与点球不计。</p>
    <h3>三、去水与溢价</h3>
    <p>官方固定奖金三项隐含概率之和通常超过 100%，超出部分是结构成本（本批 11.3–11.5 个百分点）。
    按比例归一后得到「去水后概率」，才能与模型概率放在同一把尺子上比较。溢价 EV = 模型概率 × 固定奖金 − 1；
    为正表示这一格上模型估值高于定价，但溢价为正不等于值得下注，样本薄时它同样会错。</p>
    <h3>四、信心指数五项</h3>
    <ul>
      <li><b>样本厚度（20 分）</b>：主客分离样本场数，两场以内只能算参考。</li>
      <li><b>双法收敛（20 分）</b>：两条 λ 的相对差，差得多说明两套证据打架。</li>
      <li><b>三方一致（25 分）</b>：官方定价方向、公开预报、接口算法三条线里，有几条与模型同向。</li>
      <li><b>分歧可控（25 分）</b>：胜平负最大偏差，超过 10 个百分点按「先假定我方有缺口」处理，扣分。</li>
      <li><b>比分集中（10 分）</b>：Top3 比分概率之和，集中度低意味着结果更随机、比分推荐更不可靠。</li>
    </ul>
    <p><b>怎么读总分</b>：A（≥78）结构与证据互相印证，可作为方向主参考；B（66–77）方向可信但幅度要打折；
    C（52–65）只能当一种视角；D（&lt;52）证据不足，本份只做记录不做参考。</p>
    <h3>五、本批口径</h3>
    <ul>
      <li>覆盖 {n} 场，日期 {date_tag}，全部为公开赛程与公开定价数据。</li>
      <li>外部预报只取公开赛前预报的比分与理由，以及数据接口算法的方向；接口免费层的百分比字段有坏值
      （固定 10/45/45、进球 −2.5），不采信、不展示。</li>
      <li>定价位移：本批没有可用的历史快照，盘口解读只基于当前固定奖金结构。</li>
      <li>让球盘口若临场调整，让球一侧的偏差结论需要重算；本份不含临场首发变动后的重算。</li>
    </ul>
  </div>
  <div class="disclaim">
    <b>免责与使用范围</b><br>
    本资料为内部复盘材料，用于检验模型口径与记录判断过程，不作公开投放、不对外销售、不作为任何形式的购买建议。
    文中百分比均为模型估值或定价隐含概率，不是承诺；足球比赛受红牌、伤退、天气、判罚等随机因素影响，
    任何概率都可能不成立。请理性看球。数据来源：公开赛果数据（竞彩官方定价、公开赛程与伤停、公开赛前预报）。
    仅统计 90 分钟常规时间赛果。生成：{stamp} · 模型版本 v2.10.0 · 内部资料。
  </div>
  <div class="rf"><span>阿飞 · 赛博聊球 · 内部资料</span><span>仅统计 90 分钟 · 不构成任何购买建议</span></div>
</section>""")

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{date_tag} 六场全维度内部资料 · 阿飞·赛博聊球</title>
<style>{CSS}</style></head><body>
{"".join(pages)}
</body></html>"""


def export_pdf(html_path: Path) -> None:
    """用本机 Chrome 把 HTML 导成 A4 PDF（每 .page 一张，@page margin 0）。"""
    pdf = html_path.with_suffix(".pdf")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  （未装 playwright，跳过 PDF；HTML 已生成）")
        return
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(channel="chrome", headless=True)
            pg = b.new_page(viewport={"width": 900, "height": 1200}, device_scale_factor=1.5)
            pg.goto(html_path.resolve().as_uri())
            pg.wait_for_timeout(500)
            pg.emulate_media(media="print")
            pg.pdf(path=str(pdf), format="A4", print_background=True,
                   margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            b.close()
        print(f"✅ {pdf.name}  ({pdf.stat().st_size / 1024:.0f} KB)")
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ PDF 导出失败（HTML 已生成）：{e}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="", help="模型文本，默认 state/batch 最新 _model_*.txt")
    ap.add_argument("--out", default="", help="输出 html 路径")
    ap.add_argument("--date-dir", default="", help="日期目录，用于取 cards.json（默认从模型文件名推）")
    ap.add_argument("--pdf", action=argparse.BooleanOptionalAction, default=False,
                    help="是否同时导出 A4 PDF（默认不导；付费成品已改用赛博可交互 HTML）")
    args = ap.parse_args()

    mpath = Path(args.model) if args.model else max(BATCH_DIR.glob("_model_*.txt"), key=lambda p: p.stat().st_mtime)
    if not mpath.is_absolute():
        mpath = ROOT / mpath
    day = re.search(r"_model_(\d{8})", mpath.name).group(1)
    date_dir = Path(args.date_dir) if args.date_dir else ROOT / "📝文章" / day
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    raw = parse_model(mpath)
    if not raw:
        sys.exit(f"❌ 没解析到任何场次：{mpath}")
    print(f"模型文本：{mpath.name} → {len(raw)} 场")

    cards = load_cards(date_dir) if date_dir.exists() else {}
    ext_items = load_ext(day)
    print(f"卡片索引 {len(cards)} 场；外部记录 {len(ext_items)} 条")
    quotes = load_quotes({d["mid"] for d in raw})

    matches = []
    for d in raw:
        card = cards.get(d["mid"], {})
        d["home"] = card.get("home", d["home"])
        d["away"] = card.get("away", d["away"])
        d["league"] = card.get("league", d["league"])
        d["kick"] = card.get("kick", "—")
        e = match_ext(ext_items, card.get("home", d["home"]), card.get("away", d["away"]))
        d["ext"] = e
        d["conf"] = confidence(d, e)
        d["quotes"] = quotes.get(d["mid"], [])
        matches.append(d)

    matches.sort(key=lambda m: m["kick"])
    html = build_html(matches, f"{day[:4]}.{day[4:6]}.{day[6:]}", stamp)
    out = Path(args.out) if args.out else date_dir / f"付费内部资料_六场全维度_{day}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"\n✅ {out}  ({len(html) / 1024:.0f} KB)")
    if args.pdf:
        export_pdf(out)
    for m in matches:
        c = m["conf"]
        print(f"  {m['no']} {m['home']}vs{m['away']:<7} 信心 {c['total']:>3} {c['grade']:<7} "
              f"方向 {c['model_dir']} 定价 {c['market_dir']} 偏差 {c['maxpp']:>5.1f}pp 同向 {c['agree']}/3")


if __name__ == "__main__":
    main()
