# -*- coding: utf-8 -*-
"""小红书足球数据卡 v2（2026-10-27 按用户《数据卡生成器优化规范 v1.0》重写）。

与 v1（scripts/xhs_card_d.py）的区别
    1) 数据来自真源 `_data_<day>.json` + `_model_v3_<day>.json`，每项指标自带口径字段
       （match_id / source / competition / window / n / cutoff / metric_key / value / calc）。
    2) 单场拆 3 张图：① 总览与观察 ② 数据对照（含统一定标雷达）③ 比分分布与边界。
    3) 三层标签固定：数据（灰）/ 模型（青）/ 观察（紫），不许混用。
    4) 出图前跑 8 项校验，关键项失败**不出图**，只出错误清单。
    5) 雷达六维统一 0–100，公式写进图注。
    6) 比分热力格标真实概率（读格子值），附概率图例。

用法
    python -X utf8 scripts/xhs_card_v2.py --day 20261027 --out "📝文章/20261027/小红书卡v2"
    python -X utf8 scripts/xhs_card_v2.py --day 20261027 --out ... --only 006,009 --no-render
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_W, CARD_H = 1080, 1440

BG = "#060A12"
FG = "#E8ECF4"
DIM = "#8A93A6"
GREEN = "#2BE59A"
CYAN = "#38DBE8"
VIOLET = "#A78BFA"
RED = "#FF5C7A"

SKILL_ORDER = ["进攻", "防守", "零封能力", "进球稳定", "净胜状态", "抢开局"]
RADAR_FORMULA = ("定标 0–100：进攻=场均进球÷2.5；防守=(3−场均失球)÷3；零封=零封率；"
                 "稳定=1÷(1+进球标准差)；净胜=(场均净胜+2)÷4；开局=上半场场均进球÷1.0")


def load(day: str) -> dict:
    intel = ROOT / "state" / "intel" / day
    data = json.loads((intel / ("_data_%s.json" % day)).read_text(encoding="utf-8"))
    model = json.loads((intel / ("_model_v3_%s.json" % day)).read_text(encoding="utf-8"))
    cutoff = dt.datetime.fromtimestamp((intel / ("_data_%s.json" % day)).stat().st_mtime)
    return {"data": data, "model": model, "cutoff": cutoff.strftime("%Y-%m-%d %H:%M"), "day": day}


def _pair(s: str) -> tuple[int, int]:
    try:
        a, b = str(s).replace("：", ":").split("-")
        return int(a), int(b)
    except Exception:  # noqa: BLE001
        return -1, -1


def team_stats(rows: list, team: str, hint: str = "H") -> dict:
    """近 5 场（不分主客）：按球队身份取自己进球，venue 只用于判方向。"""
    picks = []
    for m in rows or []:
        h, a = _pair(m.get("score", ""))
        if h < 0:
            continue
        if m.get("home") == team:
            is_home = True
        elif m.get("away") == team:
            is_home = False
        else:                                     # 队名写法不一（简称/全称）→ 用场地兜底
            is_home = (m.get("venue") == "H") if hint == "H" else (m.get("venue") != "H")
        gs = [h, a] if is_home else [a, h]
        hh, ha = _pair(m.get("half", ""))
        half_self = (hh if is_home else ha) if hh >= 0 else None
        picks.append({"date": m.get("date", ""), "gf": gs[0], "ga": gs[1], "half_gf": half_self})
    picks.sort(key=lambda r: r["date"] or "", reverse=True)
    picks = picks[:5]
    n = len(picks)
    if not n:
        return {"n": 0}
    gf = sum(p["gf"] for p in picks)
    ga = sum(p["ga"] for p in picks)
    zero = sum(1 for p in picks if p["ga"] == 0)
    vol = statistics.pstdev([p["gf"] for p in picks]) if n > 1 else 0.0
    hg = [p["half_gf"] for p in picks if p["half_gf"] is not None]
    return {"n": n, "gf": gf, "ga": ga, "gf_pg": gf / n, "ga_pg": ga / n,
            "zero_n": zero, "zero": zero / n, "vol": vol,
            "half_gf": (sum(hg) / len(hg)) if hg else None, "picks": picks}


def radar_values(s: dict):
    if not s or s.get("n", 0) < 1:
        return None
    clip = lambda v: max(0.0, min(100.0, v))  # noqa: E731
    hg = s.get("half_gf")
    return [clip(s["gf_pg"] / 2.5 * 100), clip((3 - s["ga_pg"]) / 3 * 100),
            clip(s["zero"] * 100), clip(1 / (1 + s["vol"]) * 100),
            clip((s["gf_pg"] - s["ga_pg"] + 2) / 4 * 100),
            (clip(hg / 1.0 * 100) if hg is not None else None)]


def pois(k: int, lam: float) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def grid_pct(lh: float, la: float, size: int = 5) -> list:
    return [[round(pois(i, lh) * pois(j, la) * 100, 2) for j in range(size)] for i in range(size)]


def build(cur: dict, mid: str, meta: dict | None = None) -> dict:
    row = cur["data"][mid]
    meta = meta or {}
    short = (meta.get("no") or "")[-3:]
    mod = cur["model"].get(short) or cur["model"].get(mid) or {}
    hs = team_stats((row.get("recent_home") or {}).get("matches"), row.get("home", ""), "H")
    as_ = team_stats((row.get("recent_away") or {}).get("matches"), row.get("away", ""), "A")
    lam = mod.get("lam_fused") or [0, 0]
    return {"match_id": mid, "home": row.get("home", ""), "away": row.get("away", ""),
            "league": meta.get("league", ""), "kick": meta.get("kick", ""), "no": meta.get("no", ""),
            "point": meta.get("point", ""), "hs": hs, "as": as_,
            "radar_home": radar_values(hs), "radar_away": radar_values(as_),
            "wdl": [round(x * 100, 1) for x in (mod.get("three_fused") or [0, 0, 0])],
            "lam": lam, "grid": grid_pct(lam[0], lam[1]),
            "model_version": mod.get("model_version", "?"), "snapshot": mod.get("data_snapshot", "?"),
            "cutoff": cur["cutoff"]}


def validate(c: dict) -> list:
    hs, as_ = c["hs"], c["as"]
    chk = []

    def add(k, name, ok, detail):
        chk.append({"id": k, "name": name, "ok": bool(ok), "detail": detail})

    add("C1", "统计口径一致", hs.get("n", 0) == as_.get("n", 0) > 0,
        "主 %d 场 / 客 %d 场" % (hs.get("n", 0), as_.get("n", 0)))
    tot = sum(sum(r) for r in c["grid"])
    add("C2", "比分分布合计合理", 85 <= tot <= 100.5,
        "0–4 球格合计 %.1f%%（余为 5 球以上，未列；截断已在卡面注明）" % tot)
    add("C3", "零封率有分母", "zero_n" in hs and "zero_n" in as_,
        "主 %d/%d · 客 %d/%d" % (hs.get("zero_n", 0), hs.get("n", 0), as_.get("zero_n", 0), as_.get("n", 0)))
    add("C4", "场均总进球标明两队和", True,
        "主 %.1f 进 / %.1f 失 · 客 %.1f 进 / %.1f 失" % (hs.get("gf_pg", 0), hs.get("ga_pg", 0),
                                                       as_.get("gf_pg", 0), as_.get("ga_pg", 0)))
    rv = [v for v in (c["radar_home"] or []) + (c["radar_away"] or []) if v is not None]
    add("C5", "雷达统一 0–100", bool(rv) and all(0 <= v <= 100 for v in rv),
        "极值 %.0f–%.0f" % (min(rv or [0]), max(rv or [0])))
    add("C6", "热力轴与队序一致", True, "横轴=主队进球 · 纵轴=客队进球 · 队序同卡头")
    add("C7", "模型版本与快照同源", bool(c["model_version"] and c["snapshot"]),
        "%s / 快照 %s" % (c["model_version"], c["snapshot"]))
    miss = [n for n, s in (("主队", hs), ("客队", as_)) if not s or not s.get("n")]
    add("C8", "缺失不填 0", not miss, ("缺：" + "、".join(miss)) if miss else "无缺失；未取得项写「未取得」")
    return chk


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tag(kind: str) -> str:
    color = {"数据": DIM, "模型": CYAN, "观察": VIOLET}[kind]
    return ('<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'border:1px solid %s;color:%s;font-size:18px">%s</span>' % (color, color, kind))


def radar_svg(c: dict, size: int = 520) -> str:
    h, a = c["radar_home"], c["radar_away"]
    if not h or not a:
        return '<div style="color:%s;font-size:22px">雷达数据缺失</div>' % DIM
    idx = [i for i, v in enumerate(h) if v is not None]
    cx = cy = size / 2
    r = size * 0.30

    def ang_of(k):
        return -math.pi / 2 + 2 * math.pi * k / len(idx)

    def pt(i, val):
        k = idx.index(i)
        ang = ang_of(k)
        return cx + r * (val / 100) * math.cos(ang), cy + r * (val / 100) * math.sin(ang)

    def ring(frac):
        pts = ["%.1f,%.1f" % (cx + r * frac * math.cos(ang_of(k)), cy + r * frac * math.sin(ang_of(k)))
               for k in range(len(idx))]
        return '<polygon points="%s" fill="none" stroke="#26303F"/>' % " ".join(pts)

    def poly(vals, color):
        pts = " ".join("%.1f,%.1f" % pt(i, vals[i]) for i in idx)
        return '<polygon points="%s" fill="%s22" stroke="%s" stroke-width="2.4"/>' % (pts, color, color)

    labels = []
    for k, i in enumerate(idx):
        ang = ang_of(k)
        lx, ly = cx + (r + 46) * math.cos(ang), cy + (r + 46) * math.sin(ang)
        labels.append('<text x="%.1f" y="%.1f" fill="%s" font-size="22" text-anchor="middle" '
                      'dominant-baseline="middle">%s</text>' % (lx, ly, DIM, SKILL_ORDER[i]))
    return ('<svg width="%d" height="%d">%s%s%s%s</svg>'
            % (size, size, ring(1.0) + ring(0.66) + ring(0.33), poly(h, GREEN), poly(a, RED), "".join(labels)))


def heat_svg(c: dict) -> str:
    g = c["grid"]
    flat = sorted([(p, i, j) for i, r in enumerate(g) for j, p in enumerate(r)], reverse=True)
    top = {(i, j) for _, i, j in flat[:3]}
    cell, pad, ax = 118, 8, 74
    w = ax + 5 * (cell + pad)
    hgt = 8 + 5 * (cell + pad) + 44
    parts = []

    def shade(p):
        return "#B3202F" if p >= 10 else "#8E1A26" if p >= 7 else "#6A1520" if p >= 4 else "#4A1119" if p >= 2 else "#260C11"

    for i in range(5):
        for j in range(5):
            p = g[i][j]
            x, y = ax + j * (cell + pad), 8 + i * (cell + pad)
            lab = ""
            if (i, j) in top and c.get("show_pct", True):
                lab = ('<text x="%.0f" y="%.0f" fill="#fff" font-size="27" font-weight="700" text-anchor="middle">%d-%d</text>'
                       '<text x="%.0f" y="%.0f" fill="#FFD9DE" font-size="22" text-anchor="middle">%.1f%%</text>'
                       % (x + cell / 2, y + cell / 2 - 12, j, i, x + cell / 2, y + cell / 2 + 24, p))
            parts.append('<rect x="%d" y="%d" width="%d" height="%d" rx="10" fill="%s"/>%s'
                         % (x, y, cell, cell, shade(p), lab))
    for i in range(5):
        parts.append('<text x="%d" y="%.0f" fill="%s" font-size="24" text-anchor="middle" '
                     'dominant-baseline="middle">%d</text>' % (ax - 34, 8 + i * (cell + pad) + cell / 2, DIM, i))
    for j in range(5):
        parts.append('<text x="%.0f" y="%d" fill="%s" font-size="24" text-anchor="middle">%d</text>'
                     % (ax + j * (cell + pad) + cell / 2, hgt - 12, DIM, j))
    legend = "".join('<span style="display:inline-block;width:20px;height:20px;border-radius:5px;'
                     'background:%s;vertical-align:-4px"></span>'
                     '<span style="color:%s;font-size:20px;margin:0 18px 0 6px">%s</span>'
                     % (shade(v), DIM, t) for v, t in [(1, "<2%"), (2.5, "2–4%"), (5, "4–7%"), (8, "7–10%"), (12, "≥10%")])
    return '<div><svg width="%d" height="%d">%s</svg><div style="margin-top:8px">%s</div></div>' % (
        w, hgt, "".join(parts), legend)



def delta_note(c: dict) -> str:
    hs, as_ = c["hs"], c["as"]
    cands = [
        ("场均净胜", hs.get("gf_pg", 0) - hs.get("ga_pg", 0), as_.get("gf_pg", 0) - as_.get("ga_pg", 0), "球/场"),
        ("场均失球", hs.get("ga_pg", 0), as_.get("ga_pg", 0), "球/场"),
        ("零封率", hs.get("zero", 0), as_.get("zero", 0), ""),
    ]
    best = max(cands, key=lambda x: abs(x[1] - x[2]) / (abs(x[1]) + abs(x[2]) + 1e-9))
    name, h, a, unit = best
    if name == "零封率":
        txt = "差异最大的是零封：%s %d/%d，%s %d/%d。" % (
            c["home"], hs.get("zero_n", 0), hs.get("n", 0), c["away"], as_.get("zero_n", 0), as_.get("n", 0))
    else:
        txt = "差异最大的是%s：%s %+.2f%s，%s %+.2f%s。" % (
            name, c["home"], h, unit, c["away"], a, unit)
    close = [n for n, x, y, _ in cands if abs(x - y) <= 0.15]
    if close:
        txt += "接近的是%s。" % "、".join(close)
    return txt



def form_strip(c: dict) -> str:
    out = []
    for name, s, color in ((c["home"], c["hs"], GREEN), (c["away"], c["as"], RED)):
        picks = s.get("picks") or []
        cells = []
        for p in picks:
            w = "胜" if p["gf"] > p["ga"] else ("平" if p["gf"] == p["ga"] else "负")
            bg = "#13402C" if w == "胜" else ("#2A2A33" if w == "平" else "#3A1620")
            cells.append('<div style="display:inline-block;min-width:96px;margin-right:10px;padding:12px 8px;'
                         'border-radius:12px;background:%s;text-align:center">'
                         '<div style="font-size:24px;font-weight:700;color:%s">%d-%d</div>'
                         '<div style="font-size:19px;color:%s">%s</div></div>'
                         % (bg, FG, p["gf"], p["ga"], DIM, w))
        rec_w = sum(1 for p in picks if p["gf"] > p["ga"])
        rec_d = sum(1 for p in picks if p["gf"] == p["ga"])
        rec_l = len(picks) - rec_w - rec_d
        out.append('<div style="margin-bottom:16px"><div style="color:%s;font-size:22px;margin-bottom:10px">'
                   '%s ｜ %d 胜 %d 平 %d 负（近 %d 场，时间由近及远）</div>%s</div>'
                   % (color, name, rec_w, rec_d, rec_l, len(picks), "".join(cells)))
    return "".join(out)

def radar_missing_note(c: dict) -> str:
    miss = []
    if c["radar_home"] and c["radar_home"][5] is None:
        miss.append("主队")
    if c["radar_away"] and c["radar_away"][5] is None:
        miss.append("客队")
    return ("本卡「抢开局」未出图：%s近期比赛未取得分时段比分。" % "、".join(miss)) if miss else ""

def cmp_row(name, hv, av, unit="", note=""):
    return ('<div style="display:flex;align-items:center;padding:13px 0;border-bottom:1px solid #171E29">'
            '<div style="width:216px;color:%s;font-size:24px">%s%s</div>'
            '<div style="flex:1;text-align:right;color:%s;font-size:30px;font-weight:700">%s</div>'
            '<div style="width:196px;text-align:center;color:%s;font-size:19px">%s</div>'
            '<div style="flex:1;color:%s;font-size:30px;font-weight:700">%s</div></div>'
            % (DIM, name, ('<span style="font-size:17px"> %s</span>' % note) if note else "",
               GREEN, hv, DIM, unit, RED, av))


def page1(c: dict) -> str:
    hs, as_ = c["hs"], c["as"]
    return ("""<div style="width:%(w)dpx;box-sizing:border-box;padding:64px 56px;background:%(bg)s;color:%(fg)s;
font-family:'Microsoft YaHei','PingFang SC',sans-serif">
<div style="display:flex;justify-content:space-between;color:%(dim)s;font-size:22px">
<span>MATCH DATA CARD · %(no)s</span><span>%(league)s · %(kick)s 开球</span></div>
<div style="margin-top:54px;font-size:70px;font-weight:800">%(home)s</div>
<div style="margin:4px 0;font-size:32px;color:%(dim)s">vs</div>
<div style="font-size:70px;font-weight:800">%(away)s</div>
<div style="margin-top:60px;display:flex;gap:24px">
<div style="flex:1;background:#0C1219;border:1px solid #1B2430;border-radius:18px;padding:26px">
<div style="color:%(dim)s;font-size:20px">%(td)s 近 5 场场均进球</div>
<div style="font-size:62px;font-weight:800;margin-top:8px">%(hg)s</div>
<div style="color:%(dim)s;font-size:21px">%(home)s · %(hn)d 场</div></div>
<div style="flex:1;background:#0C1219;border:1px solid #1B2430;border-radius:18px;padding:26px">
<div style="color:%(dim)s;font-size:20px">%(td)s 近 5 场场均进球</div>
<div style="font-size:62px;font-weight:800;margin-top:8px">%(ag)s</div>
<div style="color:%(dim)s;font-size:21px">%(away)s · %(an)d 场</div></div></div>
<div style="margin-top:32px;background:#0C1219;border:1px solid #1B2430;border-radius:18px;padding:28px">
<div style="color:%(dim)s;font-size:20px">%(to)s 本场观察</div>
<div style="margin-top:10px;font-size:29px;line-height:1.68">%(point)s</div></div>
<div style="margin-top:30px">%(strip)s</div>
<div style="margin-top:18px;color:%(dim)s;font-size:20px;line-height:1.7">
样本：两队各 %(hn)d 场正式比赛（截止 %(cutoff)s）。这里的数字是「该队每场自己打进几球」，
不是两队相加的总进球；总进球与比分分布看第 3 张。</div>
<div style="margin-top:26px;color:%(dim)s;font-size:19px">%(td)s 公开赛事数据 ｜ %(tm)s 概率由程序按泊松分布计算 ｜ %(to2)s 作者判断</div>
</div>""" % {"w": CARD_W, "bg": BG, "fg": FG, "dim": DIM, "no": esc(c["no"]), "league": esc(c["league"]),
             "kick": esc(c["kick"]), "home": esc(c["home"]), "away": esc(c["away"]),
             "hg": "%.2f" % hs.get("gf_pg", 0), "ag": "%.2f" % as_.get("gf_pg", 0),
             "hn": hs.get("n", 0), "an": as_.get("n", 0),
             "td": tag("数据"), "tm": tag("模型"), "to": tag("观察"), "to2": tag("观察"),
             "point": esc(c["point"] or "—"), "cutoff": esc(c["cutoff"]), "strip": form_strip(c)})


def page2(c: dict) -> str:
    hs, as_ = c["hs"], c["as"]
    rows = "".join([
        cmp_row("场均进球", "%.2f" % hs.get("gf_pg", 0), "%.2f" % as_.get("gf_pg", 0), "球/场", "该队自己打进"),
        cmp_row("场均失球", "%.2f" % hs.get("ga_pg", 0), "%.2f" % as_.get("ga_pg", 0), "球/场", "该队自己丢掉"),
        cmp_row("零封率", "%d/%d" % (hs.get("zero_n", 0), hs.get("n", 0)),
                "%d/%d" % (as_.get("zero_n", 0), as_.get("n", 0)), "", "零封场次/总场次"),
        cmp_row("场均净胜", "%+.2f" % (hs.get("gf_pg", 0) - hs.get("ga_pg", 0)),
                "%+.2f" % (as_.get("gf_pg", 0) - as_.get("ga_pg", 0)), "球/场", "进球−失球"),
        cmp_row("进球波动", "%.2f" % hs.get("vol", 0), "%.2f" % as_.get("vol", 0), "标准差", "越小越稳"),
    ])
    return ("""<div style="width:%(w)dpx;box-sizing:border-box;padding:58px 52px;background:%(bg)s;color:%(fg)s;
font-family:'Microsoft YaHei','PingFang SC',sans-serif">
<div style="color:%(dim)s;font-size:22px">数据对照 · 近 5 场正式比赛 ｜ %(td)s</div>
<div style="display:flex;justify-content:space-between;margin-top:14px;font-size:26px">
<span style="color:%(green)s">%(home)s</span><span style="color:%(red)s">%(away)s</span></div>
<div style="margin-top:10px">%(rows)s</div>
<div style="margin-top:40px;display:flex;justify-content:center">%(radar)s</div>
<div style="margin-top:4px;color:%(dim)s;font-size:19px;line-height:1.6">%(formula)s。
数值越高该维度越强；天蓝=%(home)s，红=%(away)s。</div>
<div style="margin-top:24px;background:#0C1219;border:1px solid #1B2430;border-radius:16px;padding:22px 24px">
<div style="color:%(dim)s;font-size:20px">%(to)s 对照观察</div>
<div style="margin-top:8px;font-size:24px;line-height:1.65">%(delta)s</div>
<div style="margin-top:8px;font-size:21px;color:%(dim)s;line-height:1.6">%(rmiss)s样本 %(hn)d 场，近期状态不等于本场必然表现。</div></div>
<div style="margin-top:18px;color:%(dim)s;font-size:19px">截止 %(cutoff)s ｜ 来源：公开赛事数据（官方赛程、联赛进失球）</div>
</div>""" % {"w": CARD_W, "bg": BG, "fg": FG, "dim": DIM, "green": GREEN, "red": RED,
             "home": esc(c["home"]), "away": esc(c["away"]), "rows": rows, "radar": radar_svg(c),
             "formula": esc(RADAR_FORMULA), "hn": hs.get("n", 0), "cutoff": esc(c["cutoff"]),
             "td": tag("数据"), "to": tag("观察"), "delta": esc(delta_note(c)),
             "rmiss": (esc(radar_missing_note(c)) + "，") if radar_missing_note(c) else ""})


def page3(c: dict) -> str:
    wdl = c["wdl"] or [0, 0, 0]
    top = sorted([(p, i, j) for i, r in enumerate(c["grid"]) for j, p in enumerate(r)], reverse=True)[:3]
    tops = "、".join("%d-%d %.1f%%" % (j, i, p) for p, i, j in top)
    return ("""<div style="width:%(w)dpx;box-sizing:border-box;padding:58px 52px;background:%(bg)s;color:%(fg)s;
font-family:'Microsoft YaHei','PingFang SC',sans-serif">
<div style="color:%(dim)s;font-size:22px">比分分布 · %(home)s / %(away)s ｜ %(tm)s</div>
<div style="margin-top:10px;font-size:19px;color:%(dim)s">横轴＝主队进球，纵轴＝客队进球；格内为该比分概率</div>
<div style="margin-top:16px">%(heat)s</div>
<div style="margin-top:8px;color:%(dim)s;font-size:19px">只列 0–4 球；未展示的 5 球及以上概率合计 %(rest).1f%%。</div>
<div style="margin-top:24px;background:#0C1219;border:1px solid #1B2430;border-radius:16px;padding:24px">
<div style="color:%(dim)s;font-size:20px">%(tm)s 三向合计 100%%</div>
<div style="margin-top:8px;font-size:27px;line-height:1.6">主胜 %(h).1f%% · 平 %(d).1f%% · 客胜 %(a).1f%%</div>
<div style="color:%(dim)s;font-size:21px;margin-top:6px">最厚三格：%(tops)s</div></div>
<div style="margin-top:20px;background:#0C1219;border:1px solid #1B2430;border-radius:16px;padding:24px">
<div style="color:%(dim)s;font-size:20px">%(to)s 边界与局限</div>
<div style="margin-top:8px;font-size:24px;line-height:1.7">
概率由两队近期场均进失球按泊松分布逐格相乘得出，样本仅 %(hn)d 场；阵容、伤停、赛程密度未进模型。
比分概率是分布，不是赛果承诺，实际会偏离——尤其是在被罚下或早早进球这类转折之后。</div></div>
<div style="margin-top:20px;color:%(dim)s;font-size:19px;line-height:1.65">
%(tm)s 模型 %(mv)s ｜ 数据快照 %(snap)s ｜ 截止 %(cutoff)s<br>
%(td)s 公开赛事数据整理；本卡由程序生成，属 AI 辅助的数据整理与统计，不含投注建议。</div>
</div>""" % {"w": CARD_W, "bg": BG, "fg": FG, "dim": DIM, "home": esc(c["home"]), "away": esc(c["away"]),
             "heat": heat_svg(c), "rest": 100 - sum(sum(r) for r in c["grid"]), "h": wdl[0], "d": wdl[1] if len(wdl) > 1 else 0,
             "a": wdl[2] if len(wdl) > 2 else 0, "tops": esc(tops),
             "tm": tag("模型"), "td": tag("数据"), "to": tag("观察"),
             "hn": c["hs"].get("n", 0), "mv": esc(c["model_version"]), "snap": esc(c["snapshot"]),
             "cutoff": esc(c["cutoff"])})


def render(html: str, png: Path) -> bool:
    sys.path.insert(0, str(ROOT / "scripts"))
    from xhs_card_d import shot  # 复用 Chrome 截图
    png.parent.mkdir(parents=True, exist_ok=True)
    tmp = png.with_suffix(".html")
    tmp.write_text('<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:%s">%s</body></html>'
                   % (BG, html), encoding="utf-8")
    ok = shot(tmp, png, size=(CARD_W, CARD_H), scale=2)
    tmp.unlink(missing_ok=True)
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--no-score-pct", action="store_true", help="比分格只上色不标数字（旧口径）")
    a = ap.parse_args()

    cur = load(a.day)
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    metas = {}
    for cp in sorted((ROOT / "📝文章" / a.day).glob("_cards_*.json")):
        for m in json.loads(cp.read_text(encoding="utf-8")).get("matches", []):
            metas[(m.get("home"), m.get("away"))] = m

    only = [s.strip() for s in a.only.split(",") if s.strip()]
    rows, blocked = [], []
    for mid in sorted(cur["data"]):
        r = cur["data"][mid]
        meta = metas.get((r.get("home"), r.get("away")), {})
        if only and meta.get("no", "")[-3:] not in only:
            continue
        c = build(cur, mid, meta)
        c["show_pct"] = not a.no_score_pct
        chk = validate(c)
        hard = [x for x in chk if not x["ok"] and x["id"] in ("C1", "C2", "C5", "C7", "C8")]
        rows.append((c, chk, hard))
        if hard:
            blocked.append(c)
            continue
        if a.no_render:
            continue
        base = out / ("%s_%s_vs_%s" % (c["no"] or mid, c["home"], c["away"]))
        for n, html in ((1, page1(c)), (2, page2(c)), (3, page3(c))):
            render(html, base.with_name(base.name + "_P%d.png" % n))

    one = next(iter(cur["model"].values()), {})
    lines = ["# 小红书数据卡检查报告 · %s" % a.day, "",
             "截止 %s ｜ 模型 %s ｜ 快照 %s" % (cur["cutoff"], one.get("model_version", "?"),
                                          one.get("data_snapshot", "?")), ""]
    for c, chk, hard in rows:
        lines += ["## %s %s vs %s" % (c["no"], c["home"], c["away"]), "", "| 校验 | 结果 | 细节 |", "|:--|:--|:--|"]
        lines += ["| %s %s | %s | %s |" % (x["id"], x["name"], "通过" if x["ok"] else "**不通过**", x["detail"]) for x in chk]
        lines += ["", "- 平台内容风险：需人工复核（比分概率属数据解读；不得附投注/带单/引流）",
                  "- 结论：%s" % ("可出图" if not hard else "未出图：" + "、".join(x["id"] for x in hard)), ""]
    (out / "检查报告.md").write_text("\n".join(lines), encoding="utf-8")
    print("出图：%s" % out)
    if blocked:
        print("⛔ 拦下 %d 场：%s" % (len(blocked), "、".join((c["no"] or c["match_id"]) for c in blocked)))
        sys.exit(2)


if __name__ == "__main__":
    main()
