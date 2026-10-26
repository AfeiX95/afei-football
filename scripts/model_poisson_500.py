# -*- coding: utf-8 -*-
"""
500 数据结构上的 λ 双法 + 泊松 —— 内部分析模型层（周二档 20261027）
输入：state/intel/<day>/_data_<day>.json（赛季分项/近期/交锋）
      state/intel/<day>/_books_<day>.json（500 亚指/欧指/大小 初盘+即时）
输出：state/intel/<day>/_model_<day>.json

口径（写进报告「二、模型」，固定不随场变）：
  λ 样本法    λh = (主队主场场均进球 + 客队客场场均失球)/2，λa 对称；夹取 [0.2, 3.2]
  λ 市场反推  网格搜 (λh, λa)：拟合①欧赔去水三向 ②大小盘水位隐含总进球（权重 0.5）
  综合        两法等权（某法缺数据则只用另一法）
  三向/AH/大小/比分  由综合 λ 的独立 Poisson 解算；AH 按整数球、半球、四分之一球分别算走水
  亚盘符号：500 原始盘口负数 = 主队让球（主让），正数 = 主队受让
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DAY = "20261027"
DATA = ROOT / "state" / "intel" / DAY / f"_data_{DAY}.json"
BOOKS = ROOT / "state" / "intel" / DAY / f"_books_{DAY}.json"
OUT = ROOT / "state" / "intel" / DAY / f"_model_{DAY}.json"
N = 12


def poisson(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def grid_probs(lh, la, n=N):
    ph = [poisson(i, lh) for i in range(n + 1)]
    pa = [poisson(j, la) for j in range(n + 1)]
    m = [[ph[i] * pa[j] for j in range(n + 1)] for i in range(n + 1)]
    s = sum(sum(r) for r in m)
    return [[v / s for v in row] for row in m]


def three_way(m):
    h = sum(m[i][j] for i in range(len(m)) for j in range(len(m)) if i > j)
    d = sum(m[i][i] for i in range(len(m)))
    return h, d, 1 - h - d


def _is_quarter(line):
    return abs(line * 2 - round(line * 2)) > 1e-9


def ah_home(m, line):
    """主队视角：line 为 500 原值（负 = 主让）。返回 (赢, 走水, 输) 概率份额"""
    if _is_quarter(line):
        a = ah_home(m, line - 0.25)
        b = ah_home(m, line + 0.25)
        return tuple((x + y) / 2 for x, y in zip(a, b))
    w = p = l = 0.0
    for i in range(len(m)):
        for j in range(len(m)):
            diff = i - j + line
            if abs(diff) < 1e-9:
                p += m[i][j]
            elif diff > 0:
                w += m[i][j]
            else:
                l += m[i][j]
    return w, p, l


def ou_prob(m, line):
    """大小盘：line 为总进球门槛（取绝对值后传入）"""
    if _is_quarter(line):
        a = ou_prob(m, line - 0.25)
        b = ou_prob(m, line + 0.25)
        return tuple((x + y) / 2 for x, y in zip(a, b))
    over = push = under = 0.0
    for i in range(len(m)):
        for j in range(len(m)):
            t = i + j
            if abs(t - line) < 1e-9:
                push += m[i][j]
            elif t > line:
                over += m[i][j]
            else:
                under += m[i][j]
    return over, push, under


def devig_three(ox_list):
    tot = [0.0, 0.0, 0.0]
    for o in ox_list:
        inv = [1 / x for x in o]
        s = sum(inv)
        for k in range(3):
            tot[k] += inv[k] / s
    return [x / len(ox_list) for x in tot], len(ox_list)


def modal_signed(entries):
    c = Counter(round(e["close"]["line"], 2) for e in entries.values())
    line, _ = c.most_common(1)[0]
    books = [k for k, e in entries.items() if abs(e["close"]["line"] - line) < 1e-9]
    return line, books


def avg_water(entries, keys, side):
    return sum(entries[k]["close"][side] for k in keys) / len(keys)


def implied_total(entries, line_abs):
    over_w = sum(e["close"]["home"] for e in entries.values()) / len(entries)
    under_w = sum(e["close"]["away"] for e in entries.values()) / len(entries)
    p_over = (1 / (1 + under_w))
    p_under = (1 / (1 + over_w))
    p_over = p_over / (p_over + p_under)
    best, bl = None, None
    lam = 0.4
    while lam <= 6.0:
        c = sum(poisson(t, lam) for t in range(0, N + 1) if t > line_abs)
        err = abs(c - p_over)
        if best is None or err < best:
            best, bl = err, lam
        lam += 0.02
    return bl, p_over, over_w, under_w


def mc_sim(lam_h, lam_a, line_ah, line_ou, n=100000, seed=20261027):
    """蒙特卡洛 10 万次（Poisson 抽样）。按 match-model-pipeline Step 6 口径：
    三向 / 亚盘（四分之一球拆两注、整数球走水） / 大小盘（含走水） / 比分与进球分布。
    优先 numpy，无 numpy 时退回 Knuth 乘法法（与 skill/scripts/mc-simulation.py 同源）。"""
    try:
        import numpy as np
    except Exception:
        np = None
    if np is not None:
        rng = np.random.default_rng(seed)
        h = rng.poisson(lam_h, n).astype(int)
        a = rng.poisson(lam_a, n).astype(int)
    else:
        import random
        rnd = random.Random(seed)

        def psample(lam):
            L = math.exp(-lam)
            k, pr = 0, 1.0
            while pr > L:
                k += 1
                pr *= rnd.random()
            return k - 1

        h = [psample(lam_h) for _ in range(n)]
        a = [psample(lam_a) for _ in range(n)]
    w = d = l = 0
    ah_w = ah_p = ah_l = 0.0
    ov = pu = un = 0.0
    sc = {}
    goals = {}
    for i in range(n):
        hg, ag = int(h[i]), int(a[i])
        if hg > ag:
            w += 1
        elif hg == ag:
            d += 1
        else:
            l += 1
        if _is_quarter(line_ah):
            for sub in (line_ah - 0.25, line_ah + 0.25):
                df = hg - ag + sub
                if df > 0:
                    ah_w += 0.5
                elif df == 0:
                    ah_p += 0.5
                else:
                    ah_l += 0.5
        else:
            df = hg - ag + line_ah
            if df > 0:
                ah_w += 1
            elif df == 0:
                ah_p += 1
            else:
                ah_l += 1
        t = hg + ag
        if line_ou is not None:
            if _is_quarter(line_ou):
                for sub in (line_ou - 0.25, line_ou + 0.25):
                    if t > sub:
                        ov += 0.5
                    elif t == sub:
                        pu += 0.5
                    else:
                        un += 0.5
            else:
                if t > line_ou:
                    ov += 1
                elif t == line_ou:
                    pu += 1
                else:
                    un += 1
        key = f"{hg}-{ag}"
        sc[key] = sc.get(key, 0) + 1
        goals[min(t, 8)] = goals.get(min(t, 8), 0) + 1
    top = sorted(sc.items(), key=lambda x: -x[1])[:8]
    return {
        "n": n,
        "w": round(w / n, 4), "d": round(d / n, 4), "l": round(l / n, 4),
        "ah_w": round(ah_w / n, 4), "ah_p": round(ah_p / n, 4), "ah_l": round(ah_l / n, 4),
        "o": round(ov / n, 4) if line_ou is not None else None,
        "p": round(pu / n, 4) if line_ou is not None else None,
        "u": round(un / n, 4) if line_ou is not None else None,
        "top": [[k, round(v / n, 4)] for k, v in top],
        "goals": {k: round(v / n, 4) for k, v in sorted(goals.items())},
        "zero": [round(sum(v for k, v in sc.items() if k.endswith("-0")) / n, 4),
                 round(sum(v for k, v in sc.items() if k.startswith("0-")) / n, 4)],
    }


def sens_grid(lam_h, lam_a, step=0.2):
    """敏感性：λ 主/客 各 ±step 的 3×3 网格，返回 (主胜最小, 最大, 摆动 pp)"""
    hs = []
    for dh in (-step, 0.0, step):
        for da in (-step, 0.0, step):
            m = grid_probs(max(0.2, lam_h + dh), max(0.2, lam_a + da))
            hs.append(three_way(m)[0])
    return round(min(hs), 4), round(max(hs), 4), round((max(hs) - min(hs)) * 100, 1)


def fit_market(mkt3, total_hint=None):
    best = None
    lh = 0.30
    while lh <= 3.20:
        la = 0.30
        while la <= 3.20:
            m = grid_probs(lh, la)
            h, d, a = three_way(m)
            e = (h - mkt3[0]) ** 2 + (d - mkt3[1]) ** 2 + (a - mkt3[2]) ** 2
            if total_hint:
                e += 0.5 * ((lh + la) - total_hint) ** 2
            if best is None or e < best[0]:
                best = (e, lh, la)
            la += 0.05
        lh += 0.05
    return round(best[1], 2), round(best[2], 2)


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    books = json.load(open(BOOKS, encoding="utf-8"))
    out = {}
    for num, b in books.items():
        row = data.get(b["id"])
        if not row:
            continue
        hh = (row["season_home"].get("home") or {})
        ha = (row["season_away"].get("away") or {})
        if hh.get("p") and ha.get("p"):
            ld = [min(3.2, max(0.2, hh["gf"] / hh["p"] / 2 + ha["ga"] / ha["p"] / 2)),
                  min(3.2, max(0.2, ha["gf"] / ha["p"] / 2 + hh["ga"] / hh["p"] / 2))]
        else:
            ld = None
        ox = [v["close"] for v in b["ox"].values() if v.get("close")]
        mkt3, nbook = devig_three(ox)
        if b.get("ou"):
            line_ou_signed, _ = modal_signed(b["ou"])
            line_ou = abs(line_ou_signed)
            total_hint, p_over_imp, over_w, under_w = implied_total(b["ou"], line_ou)
        else:
            line_ou, total_hint, p_over_imp, over_w, under_w = None, 2.60, None, None, None
        lm = fit_market(mkt3, total_hint)
        lm_1x2 = fit_market(mkt3, None)
        lam = [(x + y) / 2 for x, y in zip(ld, lm)] if ld else list(lm)
        m = grid_probs(*lam)
        h, d, a = three_way(m)
        if b.get("ah"):
            line_ah, ah_books = modal_signed(b["ah"])
            w_ah = avg_water(b["ah"], ah_books, "home")
            w_ah_a = avg_water(b["ah"], ah_books, "away")
        else:
            line_ah, ah_books, w_ah, w_ah_a = 0.0, [], 0.90, 0.90
        aw, ap, al = ah_home(m, line_ah)
        ev_ah = [aw * w_ah - al, al * w_ah_a - aw]
        if line_ou is None:
            ow = op = ou_ = None
            ev_ou = [None, None]
        else:
            ow, op, ou_ = ou_prob(m, line_ou)
            ev_ou = [ow * over_w - ou_, ou_ * under_w - ow]
        # 跨盘自洽：只用欧赔拟合的 λ 给亚盘/大小定价，EV 偏离 0 = 该盘与欧赔不一致
        m_mkt = grid_probs(*lm_1x2)
        aw_m, ap_m, al_m = ah_home(m_mkt, line_ah)
        ev_ah_mkt = [aw_m * w_ah - al_m, al_m * w_ah_a - aw_m]
        if line_ou is None:
            ev_ou_mkt = [None, None]
        else:
            ow_m, op_m, ou_m = ou_prob(m_mkt, line_ou)
            ev_ou_mkt = [ow_m * over_w - ou_m, ou_m * under_w - ow_m]
        # 水位隐含（去水后）
        imp_ah = [1 / (1 + w_ah), 1 / (1 + w_ah_a)]
        s_ah = sum(imp_ah)
        imp_ah = [x / s_ah for x in imp_ah]
        if line_ou is None:
            imp_ou = [None, None]
        else:
            imp_ou = [1 / (1 + over_w), 1 / (1 + under_w)]
            s_ou = sum(imp_ou)
            imp_ou = [x / s_ou for x in imp_ou]
        # 三盘位移：开盘均值 → 即时均值
        def ox_avg(key):
            vals = [v[key] for v in b["ox"].values() if v.get(key)]
            if not vals:
                return None
            return [sum(v[k] for v in vals) / len(vals) for k in range(3)]
        ox_open, ox_close = ox_avg("open"), ox_avg("close")
        ah_open = ([e["open"]["line"] for e in b["ah"].values()] if b.get("ah") else [])
        ah_close = ([e["close"]["line"] for e in b["ah"].values()] if b.get("ah") else [])
        ou_open = ([e["open"]["line"] for e in b["ou"].values()] if b.get("ou") else [])
        ou_close = ([e["close"]["line"] for e in b["ou"].values()] if b.get("ou") else [])
        scores = sorted([(f"{i}-{j}", m[i][j]) for i in range(6) for j in range(6)],
                        key=lambda x: -x[1])[:6]
        mc = mc_sim(lam[0], lam[1], line_ah, line_ou)
        s_min, s_max, s_swing = sens_grid(lam[0], lam[1])
        out[num] = {
            "match": b["match"], "kickoff": b["kickoff"], "id": b["id"], "books_ox": nbook,
            "lam_data": ld, "lam_mkt": list(lm), "lam_1x2": list(lm_1x2),
            "lam": [round(x, 3) for x in lam], "lam_total": round(sum(lam), 3),
            "market3": [round(x, 4) for x in mkt3],
            "model3": [round(h, 4), round(d, 4), round(a, 4)],
            "edge3": [round((h - mkt3[0]) * 100, 1), round((d - mkt3[1]) * 100, 1),
                      round((a - mkt3[2]) * 100, 1)],
            "ah_line": line_ah, "ah_books": ah_books,
            "ah_side": "主让" if line_ah < 0 else ("平手" if line_ah == 0 else "主受让"),
            "ah_home": round(aw, 4), "ah_push": round(ap, 4), "ah_away": round(al, 4),
            "ah_water": [round(w_ah, 3), round(w_ah_a, 3)],
            "ev_ah": [round(x * 100, 1) for x in ev_ah],
            "ou_line": line_ou, "ou_over": round(ow, 4) if ow is not None else None,
            "ou_push": round(op, 4) if op is not None else None,
            "ou_under": round(ou_, 4) if ou_ is not None else None,
            "ou_water": [round(over_w, 3) if over_w else None,
                         round(under_w, 3) if under_w else None],
            "ou_implied_total": total_hint,
            "ou_p_over_implied": round(p_over_imp, 4) if p_over_imp else None,
            "ev_ou": [round(x * 100, 1) if x is not None else None for x in ev_ou],
            "over15": round(sum(m[i][j] for i in range(8) for j in range(8) if i + j > 1.5), 4),
            "over25": round(sum(m[i][j] for i in range(8) for j in range(8) if i + j > 2.5), 4),
            "over35": round(sum(m[i][j] for i in range(8) for j in range(8) if i + j > 3.5), 4),
            "btts": round(sum(m[i][j] for i in range(1, 8) for j in range(1, 8)), 4),
            "top_scores": [[k, round(v, 4)] for k, v in scores],
            "mc": mc,
            "mc_gap": round(max(abs(mc["w"] - h), abs(mc["d"] - d), abs(mc["l"] - a)) * 100, 2),
            "sens": [s_min, s_max, s_swing],
            "ev_ah_mkt": [round(x * 100, 1) for x in ev_ah_mkt],
            "ev_ou_mkt": [round(x * 100, 1) if x is not None else None for x in ev_ou_mkt],
            "imp_ah": [round(x, 4) for x in imp_ah],
            "imp_ou": [round(x, 4) if x is not None else None for x in imp_ou],
            "ox_open": [round(x, 2) for x in ox_open] if ox_open else None,
            "ox_close": [round(x, 2) for x in ox_close] if ox_close else None,
            "ah_open_lines": ah_open, "ah_close_lines": ah_close,
            "ou_open_lines": ou_open, "ou_close_lines": ou_close,
        }
        r = out[num]
        print(num, r["match"], "λ", r["lam"], "3way", r["model3"], "vs", r["market3"],
              "| AH", line_ah, r["ah_home"], "EV", r["ev_ah"], "| OU", line_ou, "EV", r["ev_ou"])
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("→", OUT)


if __name__ == "__main__":
    main()
