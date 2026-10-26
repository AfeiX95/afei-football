# -*- coding: utf-8 -*-
"""周日场次 → 小红书信息卡 JSON（4 场）。纯解析报告，不造数。"""
import argparse
import io
import json
import math
import re

HEAD = re.compile(r"^### (周[一二三四五六日]\d{3}) (\S+) (.+?) vs (.+?)　(\d{2}:\d{2}) 开赛", re.M)
PRED = re.compile(r"首选 \*\*(.+?)\*\* ([\d.]+)% · ([\d-]+)")
SECOND = re.compile(r"次选 (.+?) ([\d.]+)% · ([\d-]+)")
THIRD = re.compile(r"防范 (.+?) ([\d.]+)% · ([\d-]+)")
LAM = re.compile(r"综合 ([\d.]+) \+ ([\d.]+) = ([\d.]+)；信心 (\d+)/100（(\w)")
FORM = re.compile(
    r"近期 主 \d+ 场 ([\d.]+)进([\d.]+)失 / 客 \d+ 场 ([\d.]+)进([\d.]+)失；"
    r"交锋 (\d+) 场 场均 ([\d.]+) 球、低比分 (\d+)%、平局 (\d+)%；伤停 (\d+) 人")
ZERO = re.compile(r"零封率 (\d+)%，进球波动（标准差）([\d.]+)")
ZERO_A = re.compile(r"客队近 5 场场均 [\d.]+ 进 [\d.]+ 失，零封率 (\d+)%，波动 ([\d.]+)")
HALF = re.compile(r"主队进球里 (\d+)% 发生在上半场，客队 (\d+)%")


TAGS = {
    "周日002": ("破防主队", "铁血客场"),
    "周日003": ("火力全开", "历史拖节奏"),
    "周日004": ("最能打", "专治不服"),
    "周日026": ("后防漏风", "客场更稳"),
}


def pois(lam):
    return math.exp(-lam) * lam ** 2 / 2


def grid5(lh, la):
    rows = []
    tot = 0.0
    for h in range(5):
        row = []
        for a in range(5):
            p = (math.exp(-lh) * lh ** h / math.factorial(h)) * (math.exp(-la) * la ** a / math.factorial(a))
            row.append(p)
            tot += p
        rows.append(row)
    return [[round(100 * p / tot, 1) for p in r] for r in rows]


def wdl(lh, la):
    h = d = a = 0.0
    for i in range(12):
        for j in range(12):
            p = (math.exp(-lh) * lh ** i / math.factorial(i)) * (math.exp(-la) * la ** j / math.factorial(j))
            if i > j:
                h += p
            elif i == j:
                d += p
            else:
                a += p
    s = h + d + a
    return [round(100 * h / s, 1), round(100 * d / s, 1), round(100 * a / s, 1)]


def radar(fh):
    """六维：进攻 / 防守 / 零封能力 / 进球稳定 / 净胜状态 / 抢开局，均来自独立指标。"""
    def num(x, d=0.0):
        try:
            return float(x)
        except (TypeError, ValueError):
            return d
    atk = 18 + num(fh.get("pj")) * 30
    dfn = 96 - num(fh.get("sj")) * 26
    zro = 25 + num(fh.get("zero")) * 0.65
    stb = 95 - num(fh.get("vol"), 1.0) * 35
    st = 50 + (num(fh.get("pj")) - num(fh.get("sj"))) * 22
    fst = 20 + num(fh.get("half"), 50) * 0.7
    clamp = lambda x: max(15, min(95, round(x)))
    return [clamp(atk), clamp(dfn), clamp(zro), clamp(stb), clamp(st), clamp(fst)]


def build(path, only):
    s = io.open(path, encoding="utf-8").read()
    heads = list(HEAD.finditer(s))
    out = []
    for idx, m in enumerate(heads):
        no, lg, home, away, kick = m.groups()
        if only and no not in only:
            continue
        end = heads[idx + 1].start() if idx + 1 < len(heads) else len(s)
        blk = s[m.start():end]
        p = PRED.search(blk)
        sec = SECOND.search(blk)
        thd = THIRD.search(blk)
        lam = LAM.search(blk)
        fm = FORM.search(blk)
        if not (lam and fm):
            continue
        lh, la = float(lam.group(1)), float(lam.group(2))
        pj_h, sj_h, pj_a, sj_a = (float(fm.group(i)) for i in (1, 2, 3, 4))
        h2h_n, h2h_avg, h2h_low, h2h_draw, inj = int(fm.group(5)), fm.group(6), fm.group(7), fm.group(8), int(fm.group(9))
        zr = ZERO.search(blk)
        zar = ZERO_A.search(blk)
        zh = zr.group(1) if zr else "—"
        za = zar.group(1) if zar else "—"
        vh = zr.group(2) if zr else ""
        hr = HALF.search(blk)
        hh, ha_ = (hr.group(1), hr.group(2)) if hr else ("—", "—")
        va = zar.group(2) if zar else ""
        pick = p.group(1) if p else ""
        card = {
            "no": no, "league": lg, "kick": kick, "home": home, "away": away,
            "model": {"lam": [lh, la], "grid": grid5(lh, la), "wdl": wdl(lh, la)},
            "form": {
                "home": {"pj": pj_h, "sj": sj_h, "gf": round(pj_h * 5, 1), "ga": round(sj_h * 5, 1), "n": 5,
                         "ha": f"零封 {zh}%", "zero": float(zh) if zh != "—" else 0.0, "vol": float(vh or 0)},
                "away": {"pj": pj_a, "sj": sj_a, "gf": round(pj_a * 5, 1), "ga": round(sj_a * 5, 1), "n": 5,
                         "ha": f"零封 {za}%", "zero": float(za) if za != "—" else 0.0, "vol": float(va or 0)},
                "h2h": {"n": h2h_n, "avg_goals": h2h_avg, "note": f"低比分 {h2h_low}% · 平 {h2h_draw}%"},
                "h2h_short": f"交锋 {h2h_n} 场 · 场均 {h2h_avg} 球 · 平 {h2h_draw}%",
            "h2h_stats": {"n": h2h_n, "draw": h2h_draw, "low": h2h_low},
            },
            "radar": {"dims": ["进攻", "防守", "零封能力", "进球稳定", "净胜状态", "抢开局"],
                       "home": radar({"pj": pj_h, "sj": sj_h, "zero": zh, "vol": vh, "half": hh}),
                       "away": radar({"pj": pj_a, "sj": sj_a, "zero": za, "vol": va, "half": ha_})},
            "pie_mode": "none",
            "heat": True,
            "intel": {"common": [f"场均进失：主 {pj_h:.1f}进/{sj_h:.1f}失 · 客 {pj_a:.1f}进/{sj_a:.1f}失",
                                 f"伤停：{inj} 人",
                                 f"交锋 {h2h_n} 场 · 场均 {h2h_avg} 球 · 低比分 {h2h_low}%"]},
            "intel2": {
                "home": {"good": [f"上半场进球占比 {hh}%，发力时段靠前" if hh != "—" else "上半场进球占比数据缺失",
                                  f"主场场均 {pj_h:.1f} 球，场均净胜 {pj_h - sj_h:+.1f}"],
                         "bad": [f"防守端近 5 场失 {sj_h * 5:.1f} 球"] if sj_h > 1.0 else []},
                "away": {"good": [f"上半场进球占比 {ha_}%，节奏与主队相当" if ha_ != "—" else "上半场进球占比数据缺失",
                                  f"客场场均 {pj_a:.1f} 球，场均净胜 {pj_a - sj_a:+.1f}"],
                         "bad": [f"防守端近 5 场失 {sj_a * 5:.1f} 球"] if sj_a > 1.0 else []},
            },
            "h2h_short": f"交锋 {h2h_n} 场 · 场均 {h2h_avg} 球 · 平 {h2h_draw}%",
            "h2h_stats": {"n": h2h_n, "draw": h2h_draw, "low": h2h_low},
            "h2h_detail": {"record": f"近 {h2h_n} 次交锋 · 场均 {h2h_avg} 球",
                           "scores": [],
                           "note": f"低比分场次占 {h2h_low}%，平局占 {h2h_draw}%；交锋场均 {h2h_avg} 球。"},
            "narr": ((f"【{TAGS[no][0]} vs {TAGS[no][1]}】" if no in TAGS else "")
                     + f"{home}的零封是 {zh}%，{away}是 {za}%——一个门关不上，一个门关得死。"
                     + f"两队交锋 {h2h_n} 次，低比分占 {h2h_low}%、平局占 {h2h_draw}%，"
                     + ("先破门的一方基本就拿走了节奏。" if h2h_draw and int(h2h_draw) >= 40 else "这一场多半比谁先犯错。")),
            "point": f"看{away if '客' in pick else (home if '主' in pick else '防线更稳的一方')}能不能把节奏先按住：两边场均进失摆在这里，先丢球的一方要改主意。",
        }
        if sec and thd:
            card["dir_note"] = f"首选 {p.group(1)} {p.group(2)}% · 次选 {sec.group(1)} · 防范 {thd.group(1)}"
        out.append(card)
    return {"meta": {"date": getattr(__import__("sys").modules[__name__], "REPORT_DATE", "10.25"), "weekday": getattr(__import__("sys").modules[__name__], "REPORT_WEEKDAY", "周日")}, "matches": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = [x.strip() for x in a.only.split(",") if x.strip()] if a.only else []
    data = build(a.report, only)
    io.open(a.out, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"✅ {len(data['matches'])} 场 → {a.out}")


if __name__ == "__main__":
    main()
