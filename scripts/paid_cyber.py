# -*- coding: utf-8 -*-
"""赛博版全维度推演：数据层。

把「数理统计模型 / 高阶数据 / 基本面情报 / 市场定价」四层算成一份 JSON，
交给 scripts/cyber_app.html（自包含可交互信息卡）渲染。

用法：
    python scripts/paid_cyber.py                # 出 HTML
    python scripts/paid_cyber.py --dump         # 只算数据，打印到 state/tmp/cyber_data.json
    python scripts/paid_cyber.py --model state/batch/_model_20261017_sat.txt --out xxx.html

口径纪律（沿用付费资料线）：
- 只统计 90 分钟常规时间；公开稿禁用词不适用于内部资料，但接口坏值（10/45/45、进球 -2.5）一律不采信；
- xG/xGA、npxG、PPDA、定位球 xG、天气与裁判尺度**没有数据源**，页面显式标注缺口，不用估算值冒充；
- Dixon-Coles 的 ρ 取固定值并写明来源，本批样本量不足以逐场拟合。
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

STATE = ROOT / "state"
BATCH = STATE / "batch"
MATCHES = STATE / "matches"
TMP = STATE / "tmp"

import paid_report as pr  # noqa: E402  复用模型文本解析与外部预测匹配

MAXG = 7            # 比分矩阵 0..7
RHO = -0.08         # Dixon-Coles 低比分相关参数（文献区间 -0.05~-0.15，取中值偏保守）
SAMPLES = 20000     # 模型侧的抽样次数，仅用于标注


def pois_matrix(lam: float, mu: float) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(MAXG):
        pi = math.exp(-lam) * lam ** i / math.factorial(i)
        row = []
        for j in range(MAXG):
            pj = math.exp(-mu) * mu ** j / math.factorial(j)
            row.append(pi * pj)
        out.append(row)
    return out


def dc_tau(i: int, j: int, lam: float, mu: float, rho: float = RHO) -> float:
    """Dixon-Coles 低比分修正因子（只作用于 0-0 / 1-0 / 0-1 / 1-1）。"""
    if i == 0 and j == 0:
        return 1 - lam * mu * rho
    if i == 0 and j == 1:
        return 1 + lam * rho
    if i == 1 and j == 0:
        return 1 + mu * rho
    if i == 1 and j == 1:
        return 1 - rho
    return 1.0


def dc_matrix(lam: float, mu: float, rho: float = RHO) -> list[list[float]]:
    base = pois_matrix(lam, mu)
    out = [[base[i][j] * dc_tau(i, j, lam, mu, rho) for j in range(MAXG)] for i in range(MAXG)]
    tot = sum(sum(r) for r in out)
    return [[v / tot for v in r] for r in out]


def outcomes(mat: list[list[float]]) -> list[float]:
    home = sum(mat[i][j] for i in range(MAXG) for j in range(MAXG) if i > j)
    draw = sum(mat[i][i] for i in range(MAXG))
    away = sum(mat[i][j] for i in range(MAXG) for j in range(MAXG) if i < j)
    return [p * 100 for p in (home, draw, away)]


def goals_dist(mat: list[list[float]]) -> list[float]:
    dist = [0.0] * (MAXG * 2)
    for i in range(MAXG):
        for j in range(MAXG):
            dist[i + j] += mat[i][j]
    return [round(v * 100, 1) for v in dist]


def read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return {}


# ---------------------------------------------------------------- 变盘快照
def devig(odds: list[float], payout: float) -> list[float]:
    """固定奖金 → 去水概率（%）；payout 为返还率小数（如 0.885）。"""
    raw = [payout / o * 100 for o in odds]
    s = sum(raw)
    return [round(x / s * 100, 1) for x in raw]


def load_moves(day: str) -> dict:
    return read_json(Path(STATE / "records" / f"_move_{day}.json")).get("matches", {})


def attach_move(mv: dict, payout_pct: float | None, model_goals: list[float]) -> dict | None:
    if not mv:
        return None
    payout = (payout_pct or 88.5) / 100
    spf = mv.get("spf") or []
    hand = mv.get("hand") or []
    new = spf[-1] if spf else None
    old = spf[0] if spf else None
    out: dict = {"name": mv.get("name", ""), "notes": mv.get("notes", []), "spf": spf, "hand": hand}
    if new:
        out["latest_spf"] = {"t": new["t"], "odds": [new["h"], new["d"], new["a"]],
                             "p": devig([new["h"], new["d"], new["a"]], payout)}
        out["open_spf"] = {"t": old["t"], "odds": [old["h"], old["d"], old["a"]],
                           "p": devig([old["h"], old["d"], old["a"]], payout)}
        out["spf_move"] = [round(out["latest_spf"]["p"][i] - out["open_spf"]["p"][i], 1) for i in range(3)]
    if hand:
        hnew, hold = hand[-1], hand[0]
        out["latest_hand"] = {"t": hnew["t"], "odds": [hnew["h"], hnew["d"], hnew["a"]],
                              "p": devig([hnew["h"], hnew["d"], hnew["a"]], payout)}
        out["open_hand"] = {"t": hold["t"], "odds": [hold["h"], hold["d"], hold["a"]],
                            "p": devig([hold["h"], hold["d"], hold["a"]], payout)}
        out["hand_move"] = [round(out["latest_hand"]["p"][i] - out["open_hand"]["p"][i], 1) for i in range(3)]
    g = mv.get("goals")
    if g:
        keys = ["0", "1", "2", "3", "4", "5", "6"]
        new_p = devig([g["new"][k] for k in keys], payout)
        old_p = devig([g["old"][k] for k in keys], payout)
        mg = (model_goals or [])[:7]
        s = sum(mg) or 1
        out["goals"] = {
            "t_old": g.get("t_old"), "t_new": g.get("t_new"),
            "odds_old": [g["old"][k] for k in keys], "odds_new": [g["new"][k] for k in keys],
            "p_old": old_p, "p_new": new_p,
            "model": [round(x / s * 100, 1) for x in mg],
            "lowest": keys[max(range(7), key=lambda i: -(g["new"][keys[i]]))],
        }
    h = mv.get("htft")
    if h:
        rows = []
        for k in ("负负", "平胜", "平平", "平负", "负平", "胜负"):
            if k in h["new"] or k in h["old"]:
                o0, o1 = h["old"].get(k), h["new"].get(k)
                rows.append({"k": k, "old": o0, "new": o1,
                             "chg": round(o1 - o0, 2) if (o0 and o1) else None})
        rows.sort(key=lambda r: r["new"] or 99)
        draw_half = sum(h["new"][k] for k in ("平胜", "平平", "平负") if k in h["new"])
        out["htft"] = {"t_old": h.get("t_old"), "t_new": h.get("t_new"), "rows": rows,
                       "draw_half_sum": round(draw_half, 2)}
    pool = mv.get("score_pool")
    if pool:
        items = sorted(pool.items(), key=lambda kv: kv[1])
        out["pool"] = [{"s": k, "odd": v, "p": round(100 / v, 1),
                        "dir": "主胜" if int(k.split("-")[0]) > int(k.split("-")[1])
                               else "平" if int(k.split("-")[0]) == int(k.split("-")[1]) else "客胜"}
                       for k, v in items]
    return out



# ---------------------------------------------------------------- 高阶数据（可得口径）
def team_form(mid: str, team: str, side: str) -> dict:
    """近期比赛结构：上下半场进球分布、零封率、进失球离散度、休整天数。"""
    d = read_json(MATCHES / mid / "result.json").get("value", {}).get(side, {})
    rows = d.get("matchList", []) or []
    gf, ga, ht_gf, ht_ga, dates, cs = [], [], [], [], [], 0
    for r in rows:
        try:
            full = [int(x) for x in str(r.get("fullCourtGoal", "0:0")).split(":")]
            half = [int(x) for x in str(r.get("halfTimeGoal", "0:0")).split(":")]
        except Exception:  # noqa: BLE001
            continue
        is_home = r.get("homeTeamShortName", "") == team
        f = full[0] if is_home else full[1]
        a = full[1] if is_home else full[0]
        hf = half[0] if is_home else half[1]
        ha = half[1] if is_home else half[0]
        gf.append(f)
        ga.append(a)
        ht_gf.append(hf)
        ht_ga.append(ha)
        if a == 0:
            cs += 1
        if r.get("matchDate"):
            dates.append(str(r["matchDate"]))

    n = len(gf)

    def sd(xs: list[int]) -> float:
        if len(xs) < 2:
            return 0.0
        m = sum(xs) / len(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

    tot_full = sum(g + a for g, a in zip(gf, ga))
    tot_1h = sum(g + a for g, a in zip(ht_gf, ht_ga))
    return {
        "n": n,
        "gf_avg": round(sum(gf) / n, 2) if n else None,
        "ga_avg": round(sum(ga) / n, 2) if n else None,
        "cs_rate": round(cs / n * 100) if n else None,
        "sd_for": round(sd(gf), 2),
        "sd_against": round(sd(ga), 2),
        "goals_1h": tot_1h,
        "goals_2h": tot_full - tot_1h,
        "share_1h": round(tot_1h / tot_full * 100, 1) if tot_full else None,
        "last_date": max(dates) if dates else None,
        "results": [
            {"d": r.get("matchDate"), "m": f"{r.get('homeTeamShortName','')} {r.get('fullCourtGoal','')} {r.get('awayTeamShortName','')}",
             "ht": r.get("halfTimeGoal")}
            for r in rows
        ],
    }


def meetings(mid: str) -> dict:
    d = read_json(MATCHES / mid / "history.json").get("value", {})
    rows = d.get("matchList", []) or []
    low, btts, draws, totals, detail = 0, 0, 0, [], []
    for r in rows:
        try:
            full = [int(x) for x in str(r.get("fullCourtGoal", "0:0")).split(":")]
        except Exception:  # noqa: BLE001
            continue
        t = full[0] + full[1]
        totals.append(t)
        if t <= 2:
            low += 1
        if full[0] > 0 and full[1] > 0:
            btts += 1
        if full[0] == full[1]:
            draws += 1
        detail.append({"d": r.get("matchDate"), "m": f"{r.get('homeTeamShortName','')} {r.get('fullCourtGoal','')} {r.get('awayTeamShortName','')}",
                       "league": r.get("tournamentShortName", "")})
    n = len(rows)
    return {
        "n": n,
        "low2": round(low / n * 100) if n else None,
        "btts": round(btts / n * 100) if n else None,
        "draw": round(draws / n * 100) if n else None,
        "avg_total": round(sum(totals) / len(totals), 2) if totals else None,
        "detail": detail,
    }


def injuries(mid: str) -> list[dict]:
    d = read_json(MATCHES / mid / "injury.json").get("value", {})
    out = []
    for side in ("home", "away"):
        blk = d.get(side, {}) or {}
        for p in blk.get("injuriesAndSuspensionsList", []) or []:
            out.append({
                "team": blk.get("teamShortName", ""),
                "side": side,
                "name": p.get("personName", ""),
                "pos": p.get("playerPositionDesc", ""),
                "apps": p.get("appearanceCnt", 0),
                "kind": "停赛" if p.get("suspensionFlag") else "伤",
            })
    return out


# ---------------------------------------------------------------- 模型侧衍生
def top_scores(mat: list[list[float]], n: int = 8) -> list[dict]:
    cells = [(i, j, mat[i][j]) for i in range(MAXG) for j in range(MAXG)]
    cells.sort(key=lambda x: -x[2])
    return [{"s": f"{i}-{j}", "p": round(p * 100, 1)} for i, j, p in cells[:n]]


def score_odds(d: dict) -> dict:
    return {t["s"]: {"p": t["p"], "odd": t["odd"], "ev": t["ev"]} for t in d.get("top", [])}


def pick_score(top: list[dict], outcome: str, exclude: tuple = (), strict: bool = False) -> str:
    """取该方向下概率最高的比分。

    exclude：已用过的比分跳过，保证首选/次选/防范三档不撞车。
    strict：只在本方向内取；本方向内没有可选格时返回空串，由调用方决定退回。

    注意：调用方应传入「按概率降序的全矩阵格子」（不是 top12）——
    top12 里某个方向可能只占一格，排除后就会跨方向退让，
    这正是「防范 主胜 1-3」这种方向与标签相反的比分的来源。
    """
    want = {"主胜": lambda s: int(s.split("-")[0]) > int(s.split("-")[1]),
            "平": lambda s: int(s.split("-")[0]) == int(s.split("-")[1]),
            "客胜": lambda s: int(s.split("-")[0]) < int(s.split("-")[1])}[outcome]
    for t in top:
        if want(t["s"]) and t["s"] not in exclude:
            return t["s"]
    if strict:
        return ""
    for t in top:
        if t["s"] not in exclude:
            return t["s"]
    return top[0]["s"]


def all_cells(mat: list[list[float]]) -> list[dict]:
    """按概率降序的全部 49 个格子（not top-N）。

    三档比分要保证「防范」落在它自己的方向上，就必须能往下翻——
    top12 里客胜档常常只有一格，翻不到第二格就只能退回跨方向，
    于是出现「防范 客胜」却写了主胜比分。全矩阵取保证同向永远有解。
    """
    cells = [(i, j, mat[i][j]) for i in range(MAXG) for j in range(MAXG)]
    cells.sort(key=lambda x: -x[2])
    return [{"s": f"{i}-{j}", "p": round(p * 100, 1)} for i, j, p in cells]


def verdicts(m: dict, top: list[dict], cells: list[dict] | None = None) -> dict:
    """三档＝三个赛果按模型概率从高到低各占一格，不是三个独立建议。

    🔴 旧写法的病灶（2026-10-19 用户 m07919 指出「首选主胜然后次选客胜，看着逻辑不通」）：
    只要定价最热的那格与模型首选同格，旧代码就把「防范」直接赋值成「次选」，
    于是出现「首选主胜 51.3%｜次选客胜 28.3%｜防范客胜 28.3%」——两档同向、同概率、同比分，
    读者看到的是一句自相矛盾的话。现在改成：
        首选 = order[0]（模型最高）
        次选 = order[1]（模型第二）
        兜底 = order[2]（模型最低）
    三个方向一定互不相同，比分各自在该方向内取概率最高的一格。
    定价热格的信息不再塞进方向位，而是单独放在 guard_mk_p / market_hot 里说明。
    """
    p, mk = m["p"], m["mk"]
    order = sorted(range(3), key=lambda i: -p[i])
    lab = ["主胜", "平", "客胜"]
    grid = cells if cells else top

    first_i, second_i, third_i = order[0], order[1], order[2]
    f = pick_score(grid, lab[first_i])
    s = pick_score(grid, lab[second_i], exclude=(f,))
    g = pick_score(grid, lab[third_i], exclude=(f, s), strict=True) \
        or pick_score(grid, lab[third_i], exclude=(f, s))

    hot_i = max(range(3), key=lambda i: mk[i])
    return {
        "first": lab[first_i], "first_p": p[first_i], "first_score": f,
        "second": lab[second_i], "second_p": p[second_i], "second_score": s,
        "guard": lab[third_i], "guard_p": p[third_i], "guard_score": g,
        "guard_model_p": p[third_i], "guard_mk_p": mk[third_i],
        "guard_mode": "第三可能",
        # 定价最热那格（可能与首选同格，也可能不同）——单独给，不占方向位
        "market_hot": lab[hot_i], "market_hot_mk_p": mk[hot_i], "market_hot_model_p": p[hot_i],
        "hot_is_first": hot_i == first_i,
        "order": [lab[i] for i in order],
    }


def cold_index(m: dict) -> dict:
    """冷门指数＝市场最热结果在模型里只剩多少「未被覆盖」的概率。"""
    mk, p = m["mk"], m["p"]
    lab = ["主胜", "平", "客胜"]
    fav = max(range(3), key=lambda i: mk[i])
    # 市场定价的反向结果（除最热外的两格），模型给的概率就是冷门空间
    others = [i for i in range(3) if i != fav]
    cold = sum(p[i] for i in others)
    srt = sorted(others, key=lambda i: -p[i])
    return {
        "fav": lab[fav],
        "fav_mk": mk[fav],
        "fav_model": p[fav],
        "index": round(cold, 1),
        "main_cold": lab[srt[0]],
        "main_cold_p": p[srt[0]],
        "second_cold": lab[srt[1]],
        "second_cold_p": p[srt[1]],
    }


def steps_text(m: dict, mat: list[list[float]], cold: dict, tech: dict) -> dict:
    p, mk, lam = m["p"], m["mk"], m.get("lam", [0, 0])
    lab = ["主胜", "平", "客胜"]
    top = sorted(range(3), key=lambda i: -p[i])
    edge = [p[i] - mk[i] for i in range(3)]
    mx = max(range(3), key=lambda i: abs(edge[i]))
    hand = m.get("hand", 0)
    he = m.get("h_edge", [0, 0, 0])
    hmax = max(range(3), key=lambda i: abs(he[i]))
    pattern = (
        f"模型给{lab[top[0]]} {p[top[0]]:.1f}%，定价去水后给{lab[max(range(3), key=lambda i: mk[i])]} "
        f"{mk[max(range(3), key=lambda i: mk[i])]:.1f}%，两边最大偏差在{lab[mx]} {edge[mx]:+.1f}pp。"
    )
    if abs(edge[mx]) < 6:
        pattern += "两边结构基本重合，格局可以按「定价给的强弱势」直接用。"
    elif abs(edge[mx]) >= 15:
        pattern += "偏差超过 15 个百分点，按纪律先假定我方样本有缺口，这一格只做方向参考。"
    else:
        pattern += "偏差中等，说明市场在押某件模型还没反映的事，方向可信、幅度要打折。"

    tot = (
        f"λ 合计 {lam[0]:.2f}+{lam[1]:.2f}={lam[0]+lam[1]:.2f}，模型给大 2.5 球 "
        f"{m.get('over25', 0):.1f}%、大 3.5 球 {m.get('over35', 0):.1f}%、双方进球 {m.get('btts', 0):.1f}%。"
    )
    if m.get("over25", 0) >= 60:
        tot += "总量偏高，比分重心落在 2-1、2-2、3-1 一带，低比分可以排除。"
    elif m.get("over25", 0) <= 42:
        tot += "总量偏低，比分重心落在 1-0、1-1、0-0 一带，别指望大比分。"
    else:
        tot += "总量居中，胜负方向确定后比分只剩两三个候选。"

    t3 = top_scores(mat, 3)
    mat_txt = "；".join(f"{t['s']} {t['p']}%" for t in t3) + "。"

    hdesc = f"让球({hand:+d}) 里模型与定价偏差最大的一格是{['主胜','平','客胜'][hmax]} {he[hmax]:+.1f}pp"
    if abs(he[hmax]) >= 10:
        mat_txt += f" {hdesc}，说明分歧落在「赢几个」而不是「谁赢」。"
    else:
        mat_txt += f" {hdesc}，让球一侧两边接近，盘口本身没有明显错位。"

    # 做排除：拿方向和总量去划掉逻辑相悖的比分，再标出定价虚高的那几格
    excl: list[dict] = []
    lab_o = lab[order_now := top[0]]
    if m.get("over25", 0) >= 62:
        excl.append({"k": "0-0 与 1-0", "kind": "排除",
                     "why": f"模型大 2.5 球 {m.get('over25', 0):.1f}%、双方进球 {m.get('btts', 0):.1f}%，两队都不是闷战型，"
                            "零封对面的概率不足三成"})
    big = sum(mat[i][j] for i in range(MAXG) for j in range(MAXG) if i + j >= 5) * 100
    if big < 10:
        excl.append({"k": "总进球 5 球以上", "kind": "排除" if big < 6 else "降权",
                     "why": f"模型合计 {big:.1f}%，尾部太薄；真出现 4-2、3-3 这类比分，说明早段就失控了"})
    if lab_o == "主胜":
        bad = sum(mat[i][j] for i in range(MAXG) for j in range(MAXG) if i <= j - 2) * 100
        excl.append({"k": "客队净胜 2 球以上", "kind": "排除" if bad < 8 else "降权",
                     "why": f"与主推方向相悖，模型合计 {bad:.1f}%"})
    elif lab_o == "客胜":
        bad = sum(mat[i][j] for i in range(MAXG) for j in range(MAXG) if i - 2 >= j) * 100
        excl.append({"k": "主队净胜 2 球以上", "kind": "排除" if bad < 8 else "降权",
                     "why": f"与主推方向相悖，模型合计 {bad:.1f}%"})
    odds = score_odds(m)
    rich = [{"k": s, "kind": "降权",
             "why": f"定价 {v['odd']:.2f} 隐含 {100/v['odd']:.1f}%，模型给 {v['p']:.1f}%，溢价 {v['ev']:+.2f}（定价虚高，不做主推）"}
            for s, v in odds.items() if v["ev"] <= -0.4]
    return {"pattern": pattern, "total": tot, "matrix": mat_txt,
            "exclude": excl, "rich": rich[:3],
            "tail5": round(big, 1), "draw_p": p[1],
            "low_risk": cold["main_cold"], "low_risk_p": cold["main_cold_p"]}


# ---------------------------------------------------------------- 汇总

def kick_of(mid: str) -> str:
    """开赛时间兜底：state/matches/<id>/head.json 的 matchDateTime（2026-10-18 15:00 → 10/18 15:00）。"""
    for mid_ in (str(mid),):
        p = ROOT / "state" / "matches" / mid_ / "head.json"
        try:
            v = json.loads(p.read_text(encoding="utf-8")).get("value") or {}
        except Exception:
            continue
        dt = (v.get("matchDateTime") or "").strip()
        if len(dt) >= 16:
            return dt[5:10].replace("-", "/") + " " + dt[11:16]
    return ""

def build(model_path: Path, date_tag: str) -> dict:
    matches_raw = pr.parse_model(model_path)
    ext_items = pr.load_ext(date_tag.replace("-", ""))
    cards = pr.load_cards(ROOT / "📝文章" / date_tag.replace("-", ""))
    oddsq = pr.load_quotes({m["mid"] for m in matches_raw})

    out = []
    moves = load_moves(date_tag)
    for m in matches_raw:
        mid = m["mid"]
        lam = m.get("lam") or [1.3, 1.2]
        mat_p = pois_matrix(lam[0], lam[1])
        mat_dc = dc_matrix(lam[0], lam[1])
        oc_p, oc_dc = outcomes(mat_p), outcomes(mat_dc)
        dist = goals_dist(mat_dc)
        top = top_scores(mat_dc, 12)
        top = [{**t, **({"odd": score_odds(m)[t["s"]]["odd"], "ev": score_odds(m)[t["s"]]["ev"]}
                        if t["s"] in score_odds(m) else {})} for t in top]
        ext = pr.match_ext(ext_items, m["home"], m["away"])
        card = cards.get(mid, {})
        tech_h = team_form(mid, m["home"], "home")
        tech_a = team_form(mid, m["away"], "away")
        meet = meetings(mid)
        inj = injuries(mid)
        cold = cold_index(m)
        steps = steps_text(m, mat_dc, cold, {})
        conf = pr.confidence(m, ext)
        low_delta = [
            {"s": "0-0", "p_pois": round(mat_p[0][0] * 100, 1), "p_dc": round(mat_dc[0][0] * 100, 1)},
            {"s": "1-0", "p_pois": round(mat_p[1][0] * 100, 1), "p_dc": round(mat_dc[1][0] * 100, 1)},
            {"s": "0-1", "p_pois": round(mat_p[0][1] * 100, 1), "p_dc": round(mat_dc[0][1] * 100, 1)},
            {"s": "1-1", "p_pois": round(mat_p[1][1] * 100, 1), "p_dc": round(mat_dc[1][1] * 100, 1)},
        ]
        out.append({
            "no": m["no"], "league": m.get("league", ""), "home": m["home"], "away": m["away"],
            "mid": mid, "kick": card.get("kick") or kick_of(mid), "hand": m.get("hand", 0),
            "lam": {"l1": m.get("lam1"), "l2": m.get("lam2"), "fin": lam,
                    "total": round(sum(lam), 2)},
            "p": m["p"], "mk": m["mk"], "edge": m.get("p_edge", [m["p"][i] - m["mk"][i] for i in range(3)]),
            "hp": m.get("hp"), "hmk": m.get("hmk"), "h_edge": m.get("h_edge"),
            "odds": m.get("odds"), "payout": m.get("payout"),
            "over": {"1.5": m.get("over15"), "2.5": m.get("over25"), "3.5": m.get("over35")},
            "btts": m.get("btts"), "goals": m.get("goals") or dist, "goals_dc": dist,
            "win_nodraw": m.get("win_nodraw"),
            "top": top, "matrix": [[round(v * 100, 2) for v in r] for r in mat_dc],
            "matrix_pois": [[round(v * 100, 2) for v in r] for r in mat_p],
            "oc": {"pois": [round(v, 1) for v in oc_p], "dc": [round(v, 1) for v in oc_dc]},
            "low_delta": low_delta,
            "verdict": verdicts(m, top, all_cells(mat_dc)),
            "conf": conf, "cold": cold, "steps": steps,
            "tech": {"home": tech_h, "away": tech_a, "meet": meet},
            "intel": {"inj": inj, "note": pr.clean_note(m.get("note") or ""),
                      "fix": pr.clean_note(m.get("fix") or ""), "inj_text": pr.clean_note(m.get("inj") or "")},
            "ext": {"sm": ext.get("sm"), "af": ext.get("af")},
            "warn": m.get("warn", []),
            "quote": oddsq.get(mid),
            "move": attach_move(moves.get(mid), m.get("payout"), m.get("goals")),
        })

    return {
        "meta": {
            "date": date_tag,
            "stamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "model": model_path.name,
            "rho": RHO,
            "samples": SAMPLES,
            "count": len(out),
        },
        "matches": out,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None, help="模型文本，默认取 state/batch 里最新的 _model_*.txt")
    ap.add_argument("--date", default=None, help="日期目录，默认 20261017")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dump", action="store_true")
    args = ap.parse_args()

    date_tag = args.date or "20261017"
    model_path = Path(args.model) if args.model else sorted(BATCH.glob("_model_*.txt"))[-1]
    data = build(model_path, date_tag)

    TMP.mkdir(parents=True, exist_ok=True)
    if args.dump:
        p = TMP / "cyber_data.json"
        p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"dumped {p} · {len(data['matches'])} 场")
        return

    tpl = (ROOT / "scripts" / "cyber_app.html").read_text(encoding="utf-8")
    tag = f"{date_tag[:4]}.{date_tag[4:6]}.{date_tag[6:]}"
    html = (tpl.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
               .replace("__TITLE__", f"{tag} 全维度推演 · 阿飞·赛博聊球"))
    out = Path(args.out) if args.out else (
        ROOT / "📝文章" / date_tag / f"六场全维度推演_海报版_{date_tag}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"✅ {out}  {out.stat().st_size/1024:.0f}KB · {len(data['matches'])} 场")


if __name__ == "__main__":
    main()
