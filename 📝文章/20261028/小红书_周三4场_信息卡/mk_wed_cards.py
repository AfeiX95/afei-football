# -*- coding: utf-8 -*-
"""周三档 4 场焦点战 → 小红书一图流全维技术海报 JSON（数据来源：_model_v3 + _data，纯技术参数与近期表现拆解）。"""
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
DAY = "20261028"
PICK = ["006", "011", "014", "015"]
PICK6 = ["006", "011", "014", "015", "012", "013"]

B_RAW = json.loads((ROOT / f"state/intel/{DAY}/_books_{DAY}.json").read_text(encoding="utf-8"))
M = json.loads((ROOT / f"state/intel/{DAY}/_model_v3_{DAY}.json").read_text(encoding="utf-8"))
D = json.loads((ROOT / f"state/intel/{DAY}/_data_{DAY}.json").read_text(encoding="utf-8"))


def pois(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def grid5(lh, la):
    rows = [[pois(h, lh) * pois(a, la) for a in range(5)] for h in range(5)]
    tot = sum(sum(r) for r in rows)
    return [[round(100 * p / tot, 1) for p in r] for r in rows]


def recent(block, is_home_team=True, n=5):
    """按 venue 字段取本队视角的近 n 场全维技术参数（含上下半场进失球、半场领先率、同主客战绩、波动率）。"""
    rows = (block.get("matches") or [])
    rows = [r for r in rows if (r.get("score") or "-") != "-"][:n]
    gf = ga = 0
    ht_gf = ht_ga = 0
    zero = 0
    ht_lead = 0
    ht_unbeat = 0
    w = d = l = 0
    vw = vd = vl = vgf = vga = vn = 0
    lst = []
    seq = []
    flow = []
    target_venue = "H" if is_home_team else "A"
    for r in rows:
        hs, as_ = [int(x) for x in r["score"].split("-")]
        is_h = (r.get("venue") == "H")
        mine, opp = (hs, as_) if is_h else (as_, hs)
        gf += mine
        ga += opp
        lst.append(mine)
        if opp == 0:
            zero += 1
        if mine > opp:
            w += 1
            seq.append("W")
            res_cn = "胜"
        elif mine == opp:
            d += 1
            seq.append("D")
            res_cn = "平"
        else:
            l += 1
            seq.append("L")
            res_cn = "负"
        flow.append(f"进{mine}失{opp}({res_cn})")

        # 半场数据
        half_str = str(r.get("half") or "")
        if ":" in half_str:
            hhs, has_ = [int(x) for x in half_str.split(":")]
            mhg, ohg = (hhs, has_) if is_h else (has_, hhs)
            ht_gf += mhg
            ht_ga += ohg
            if mhg > ohg:
                ht_lead += 1
            if mhg >= ohg:
                ht_unbeat += 1

        # 近5场内的同主客统计（用于杯赛无积分榜时）
        if r.get("venue") == target_venue:
            vn += 1
            vgf += mine
            vga += opp
            if mine > opp:
                vw += 1
            elif mine == opp:
                vd += 1
            else:
                vl += 1

    n_ = len(rows) or 1
    mu = sum(lst) / n_
    sd = (sum((v - mu) ** 2 for v in lst) / n_) ** 0.5
    sh_gf = max(0, gf - ht_gf)
    sh_ga = max(0, ga - ht_ga)
    return {
        "pj": round(gf / n_, 2),
        "sj": round(ga / n_, 2),
        "gd_avg": round((gf - ga) / n_, 2),
        "gf": gf,
        "ga": ga,
        "n": len(rows),
        "w": w,
        "d": d,
        "l": l,
        "l5": f"{w}胜{d}平{l}负",
        "seq": seq,
        "flow": flow,
        "zero": round(100 * zero / n_, 1),
        "unbeat": round(100 * (w + d) / n_, 1),
        "vol": round(sd, 2),
        "ht_gf": ht_gf,
        "ht_ga": ht_ga,
        "sh_gf": sh_gf,
        "sh_ga": sh_ga,
        "ht_lead": round(100 * ht_lead / n_),
        "ht_unbeat": round(100 * ht_unbeat / n_),
        "venue_rec": f"{vw}胜{vd}平{vl}负",
        "venue_gf": vgf,
        "venue_ga": vga,
        "venue_n": vn,
    }


def season_info(b, is_home_team=True, rec=None):
    """提取赛季积分榜与同主客战绩；若为杯赛无积分榜则退回近期同主客统计。"""
    key = "season_home" if is_home_team else "season_away"
    vkey = "home" if is_home_team else "away"
    vname = "主场" if is_home_team else "客场"
    s = b.get(key) or {}
    tot = s.get("total") or {}
    ven = s.get(vkey) or {}
    if tot and tot.get("p"):
        rank_txt = f"意甲第{tot['rank']} · {tot['w']}胜{tot['d']}平{tot['l']}负 · {tot['pts']}分"
        ven_txt = f"本季{vname} {ven['w']}胜{ven['d']}平{ven['l']}负"
        ven_sub = f"进{ven['gf']}失{ven['ga']} · 勝率{ven['wr']}%"
        return {"rank_txt": rank_txt, "ven_txt": ven_txt, "ven_sub": ven_sub}
    # 杯赛回退
    if rec:
        rank_txt = f"近5战 {rec['l5']} · 进{rec['gf']}失{rec['ga']}"
        ven_txt = f"近期{vname} {rec['venue_rec']}"
        ven_sub = f"近{rec['venue_n']}个{vname}进{rec['venue_gf']}失{rec['venue_ga']}"
        return {"rank_txt": rank_txt, "ven_txt": ven_txt, "ven_sub": ven_sub}
    return {"rank_txt": "杯赛轮次", "ven_txt": "—", "ven_sub": "—"}


def h2h(block):
    h = block.get("h2h") or {}
    s = h.get("summary") or {}
    n = int(s.get("n") or 0)
    gf, ga = int(s.get("gf") or 0), int(s.get("ga") or 0)
    over, under = int(s.get("over") or 0), int(s.get("under") or 0)
    txt = (s.get("text") or "").rstrip("，, ")
    m_w = re.search(r"(\d+)胜", txt)
    m_d = re.search(r"(\d+)平", txt)
    m_l = re.search(r"(\d+)负", txt)
    w = int(m_w.group(1)) if m_w else 0
    draw = int(m_d.group(1)) if m_d else 0
    l = int(m_l.group(1)) if m_l else 0
    avg = round((gf + ga) / n, 2) if n else 0
    return {
        "n": n,
        "w": w,
        "d": draw,
        "l": l,
        "gf": gf,
        "ga": ga,
        "avg": avg,
        "draw": round(100 * draw / n) if n else 0,
        "low": round(100 * under / n) if n else 0,
        "scores": [],
        "text": txt,
    }


def radar(f):
    c = lambda x: max(18, min(96, round(x)))
    # 抢开局由真实上半场净胜、上半场进球数与半场领先率驱动
    open_score = 32 + f["ht_lead"] * 0.42 + (f["ht_gf"] - f["ht_ga"]) * 4.5
    return [
        c(18 + f["pj"] * 30),              # 进攻
        c(96 - f["sj"] * 26),              # 防守
        c(25 + f["zero"] * 0.65),          # 零封能力
        c(95 - f["vol"] * 35),             # 进球稳定
        c(50 + (f["pj"] - f["sj"]) * 22),  # 净胜状态
        c(open_score),                     # 抢开局
    ]


LEAGUES = {
    "006": "意甲 · 第9轮",
    "011": "英联赛杯 · 第四轮",
    "012": "英联赛杯 · 第四轮",
    "013": "意甲 · 第9轮",
    "014": "意甲 · 第9轮",
    "015": "英联赛杯 · 第四轮",
}

TAGS = {
    "006": ("主场防线稳健", "客场下半场承压"),
    "011": ("主场三战零封", "客场半场抢攻"),
    "012": ("主场高压逼抢", "客场防线抗压"),
    "013": ("主场攻防均衡", "客场边路反击"),
    "014": ("主场半场密防", "客场后程发力"),
    "015": ("主场火力全开", "转换防线承压"),
}

NARR = {
    "006": (
        "AC米兰本季前 8 轮 5 胜 3 平保持不败，其中主场 3 战全胜进 8 球仅失 2 球，近 5 场上半场进 5 失 2 抢开局强势；"
        "博洛尼亚前 8 轮 2 胜 2 平 4 负排第 13，近 5 场上半场仅失 1 球但下半场丢掉 5 球，体能节点后防线承压明显。"
    ),
    "011": (
        "两队近期同处进攻爆发期：伯恩茅斯近 5 场 4 胜 1 负轰入 12 球、4 场零封，近 3 个主场全胜进 8 球 0 失球；"
        "阿斯顿维拉近 5 场 4 胜 1 平打进 14 球仅失 4 球，上半场共进 8 球失 1 球。开场前 45 分钟的高位对攻是胜负手。"
    ),
    "012": "杯赛单场淘汰赛制下，主队依托主场高位压迫争取上半场建立优势，客队更重中路协防与二点保护。",
    "013": "意甲周中快节奏轮换战，主队依托肋部配合与边路套上施压，客队依靠低位防守后的快速纵向推进寻找空档。",
    "014": (
        "热那亚近 5 场 3 胜 2 负、进 5 球失 5 球，上半场仅失 1 球但下半场丢 4 球；"
        "尤文图斯本季客场 4 战 2 胜 1 平 1 负进 6 失 4，近 5 场上半场进 3 失 5 偏慢热、下半场进 4 失 2 后程发力，过往 6 次交锋热那亚仅入 1 球。"
    ),
    "015": (
        "英联杯强强对话。利物浦近 5 场 4 胜 1 负轰入 14 球同时也丢了 10 球，其中下半场进 7 球失 7 球大开大合；"
        "切尔西近 5 场 2 胜 1 平 2 负进 9 球失 8 球，下半场同样进 6 球失 6 球，两队近期失球均高度集中在下半场。"
    ),
}

POINT = {
    "006": "数据反差：米兰近5场上半场进5失2 vs 博洛尼亚近5场下半场失5球",
    "011": "数据反差：两队近5场半场领先率均达80%(合计上半场进14失3)",
    "012": "数据反差：主队上半场进3失2 vs 客队近5场上半场进1失8",
    "013": "数据反差：两队近5场六维综合均值同为55.8分，下半场合计失12球",
    "014": "数据反差：近6次交锋热那亚仅进1球(尤文进8球)，热那亚半场失1球 vs 下半场失4球",
    "015": "数据反差：利物浦近5场下半场进7失7 × 切尔西近5场下半场进6失6",
}


def build_card(no):
    mid = B_RAW[no]["id"]
    kick = B_RAW[no]["kickoff"].split()[-1]
    b = D[mid]
    fh = recent(b.get("recent_home") or {}, is_home_team=True)
    fa = recent(b.get("recent_away") or {}, is_home_team=False)
    sh_info = season_info(b, is_home_team=True, rec=fh)
    sa_info = season_info(b, is_home_team=False, rec=fa)
    h2 = h2h(b)
    rh = radar(fh)
    ra = radar(fa)
    t_pair = TAGS.get(no, ("主场近况", "客场近况"))
    card = {
        "no": no,
        "league": LEAGUES.get(no, B_RAW[no]["match"].split()[0]),
        "kick": kick,
        "home": b["home"],
        "away": b["away"],
        "form": {
            "home": {**fh, **sh_info, "ha": f"零封 {fh['zero']:.0f}%"},
            "away": {**fa, **sa_info, "ha": f"零封 {fa['zero']:.0f}%"},
            "h2h": {
                "n": h2["n"],
                "w": h2["w"],
                "d": h2["d"],
                "l": h2["l"],
                "gf": h2["gf"],
                "ga": h2["ga"],
                "avg_goals": h2["avg"],
                "draw": h2["draw"],
                "text": h2["text"],
                "note": f"近{h2['n']}次交锋 主{h2['w']}胜{h2['d']}平{h2['l']}负",
            },
            "h2h_short": f"交锋 {h2['n']} 场 ({h2['w']}胜{h2['d']}平{h2['l']}负 · 进{h2['gf']}失{h2['ga']})",
            "h2h_stats": {"n": h2["n"], "draw": h2["draw"]},
        },
        "radar": {
            "dims": ["进攻", "防守", "零封能力", "进球稳定", "净胜状态", "抢开局"],
            "home": rh,
            "away": ra,
            "avg_home": round(sum(rh) / len(rh), 1),
            "avg_away": round(sum(ra) / len(ra), 1),
        },
        "pie_mode": "none",
        "heat": False,
        "intel": {
            "common": [
                f"场均进失：主 {fh['pj']:.2f} 进 / {fh['sj']:.2f} 失 · 客 {fa['pj']:.2f} 进 / {fa['sj']:.2f} 失",
                f"半场得失：主 上半场进{fh['ht_gf']}失{fh['ht_ga']} · 客 上半场进{fa['ht_gf']}失{fa['ht_ga']}",
                f"交锋 {h2['n']} 场 · 主 {h2['w']}胜{h2['d']}平{h2['l']}负",
            ]
        },
        "intel2": {
            "home": {
                "good": [f"近 {fh['n']} 场场均 {fh['pj']:.2f} 球，共进 {fh['gf']} 失 {fh['ga']}"],
                "bad": [f"近 {fh['n']} 场进球波动 {fh['vol']:.2f}，场次间起伏较大"] if fh["vol"] > 1.0 else [],
            },
            "away": {
                "good": [f"近 {fa['n']} 场场均 {fa['pj']:.2f} 球、失 {fa['sj']:.2f} 球"],
                "bad": [f"近 {fa['n']} 场共失 {fa['ga']} 球，防线承压"] if fa["sj"] > 1.3 else [],
            },
        },
        "h2h_short": f"交锋 {h2['n']} 场 · 主 {h2['w']}胜{h2['d']}平{h2['l']}负",
        "h2h_stats": {"n": h2["n"], "draw": h2["draw"]},
        "h2h_detail": {
            "record": f"近 {h2['n']} 次交锋 · 主 {h2['w']}胜{h2['d']}平{h2['l']}负",
            "scores": [],
            "note": f"过往 {h2['n']} 次交锋主队进 {h2['gf']} 球、客队进 {h2['ga']} 球。",
        },
        "narr": f"【{t_pair[0]} vs {t_pair[1]}】" + NARR.get(no, ""),
        "point": POINT.get(no, f"数据反差：{t_pair[0]} vs {t_pair[1]}"),
    }
    print(no, b["home"], "vs", b["away"], "radar_avg", card["radar"]["avg_home"], card["radar"]["avg_away"])
    return card


cards = [build_card(no) for no in PICK]
out = {
    "meta": {
        "date": "10.28",
        "weekday": "星期三",
        "kick_day": "10/28–10/29 赛程",
        "tail": "4 场近期战绩与上下半场得失统计",
    },
    "matches": cards,
}
(ROOT / f"📝文章/{DAY}/_cards_wed.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("✅ _cards_wed.json (4场纯历史数据版) 写入完成")
