# -*- coding: utf-8 -*-
"""model_v3.py —— 三套 λ（数据 / 市场 / 融合）+ Edge(A vs B) + 参数不确定性区间。

设计口径（评审 P0-5 / P0-6 / P0-8 落地）：

A. λ_data（独立模型）
   r_home = 主队主场场均进球（同主客样本，n = 主场场次）
   prior_home = (主队全季场均进球 + 客队全季场均失球) / 2   ← 场地中性的池化估计
   λ_A_h = (n·r + k·prior) / (n + k)                          ← 经验贝叶斯收缩，k = 4
   再乘对手防守强度指数（对手全季场均失球 / 两队场均失球均值，夹取 [0.75, 1.35]）的 0.5 次方，
   半强度修正，避免与收缩重复计入。
   k 随数据等级调整：A 档 4、B/C 档 6（样本可疑时更靠先验）；A 档以外还给 note 标记。

B. λ_market（市场隐含）  由 model_poisson_500.fit_market() 在 Poisson 网格上同时拟合
   欧赔去水三向 + 大小水位隐含总进球，产出 (λ_h, λ_a)。这是「市场共识」，用于算 Edge，不用于覆盖数据。

C. λ_fused（融合，用于出结论）
   权重按数据等级：A 0.65 / B 0.50 / C 0.35 / DATA_INVALID 0（不融合，只报市场）。
   λ_C = w·λ_A + (1-w)·λ_B。

Edge 一律用 **A vs B**（独立信号对市场），不再拿 C 去比自己（那是循环）。

不确定性：λ 的后验近似 Gamma(shape = n_eff·λ̂, rate = n_eff)（mean = λ̂, sd = λ̂/√n_eff），
对 (λ_h, λ_a) 各抽 draws 次，重算主胜概率，取 5% / 95% 分位作为区间——样本越薄区间越宽。

用法：
    python -X utf8 scripts/model_v3.py 20261027      # 打印逐场 λ 与区间
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import model_poisson_500 as mp  # noqa: E402

CLIP = (0.20, 3.20)
K_BY_GRADE = {"A": 4.0, "B": 6.0, "C": 6.0, "DATA_INVALID": 6.0}
W_BY_GRADE = {"A": 0.65, "B": 0.50, "C": 0.35, "DATA_INVALID": 0.0}
MODEL_VERSION = "v3.1"


def snapshot_id(day):
    """数据快照标识 = 当日 _books/_data 两份原始 json 的 sha256 前 12 位（可追溯、可比对）"""
    import hashlib
    d = ROOT / "state" / "intel" / day
    h = hashlib.sha256()
    for name in (f"_books_{day}.json", f"_data_{day}.json"):
        fp = d / name
        if fp.exists():
            h.update(fp.read_bytes())
    return h.hexdigest()[:12]


def evidence_grade(w_data, grade):
    """预测证据等级（与「数据完整性等级」分开）：由融合时数据侧的权重决定"""
    if grade == "DATA_INVALID" or not w_data:
        return "市场单腿（无独立证据）"
    if w_data >= 0.50:
        return "较强（数据侧权重 ≥0.50）"
    if w_data >= 0.25:
        return "中等（数据侧权重 0.25–0.50）"
    return "偏弱（数据侧权重 <0.25）"


def _rate(block, key):
    b = block.get(key) or {}
    p = b.get("p") or 0
    if not p:
        return None, 0
    return (b.get("gf", 0) / p, b.get("ga", 0) / p), p


def data_lam(row, grade="A"):
    """返回 dict(lam=(h,a), n=(nh,na), prior=(ph,pa), idx=(ih,ia), notes=[...])"""
    sh, sa = row["season_home"], row["season_away"]
    t1, t2 = sh.get("total"), sa.get("total")
    h1, _ = _rate(sh, "home")   # 主队主场 (进/失 per match)
    a2, _ = _rate(sa, "away")   # 客队客场 (进/失 per match)
    notes = []
    if not (t1 and t2 and h1 and a2):
        return None
    k = K_BY_GRADE.get(grade, 4.0)
    p_h_total = t1.get("p") or 0
    p_a_total = t2.get("p") or 0
    if not (p_h_total and p_a_total):
        return None
    gf_h_season = t1["gf"] / p_h_total
    ga_h_season = t1["ga"] / p_h_total
    gf_a_season = t2["gf"] / p_a_total
    ga_a_season = t2["ga"] / p_a_total

    prior_h = (gf_h_season + ga_a_season) / 2
    prior_a = (gf_a_season + ga_h_season) / 2

    n_h = sh["home"]["p"]
    n_a = sa["away"]["p"]
    lam_h = (n_h * h1[0] + k * prior_h) / (n_h + k)
    lam_a = (n_a * a2[0] + k * prior_a) / (n_a + k)

    # 对手防守强度（半强度）
    pair_ga = (ga_h_season + ga_a_season) / 2
    idx_vs_away = min(1.35, max(0.75, ga_a_season / pair_ga)) if pair_ga else 1.0
    idx_vs_home = min(1.35, max(0.75, ga_h_season / pair_ga)) if pair_ga else 1.0
    lam_h *= idx_vs_away ** 0.5
    lam_a *= idx_vs_home ** 0.5

    lam_h = min(CLIP[1], max(CLIP[0], lam_h))
    lam_a = min(CLIP[1], max(CLIP[0], lam_a))
    if n_h < 5 or n_a < 5:
        notes.append(f"同主客样本不足（主 {n_h} 场 / 客 {n_a} 场），已向全季池化值收缩，融合权重按样本打折")
    if min(p_h_total, p_a_total) <= 4:
        notes.append(f"全季样本仅 {min(p_h_total, p_a_total)} 场（小组赛阶段），先验本身不独立，A 模型话语权应再降")
    return {"lam": (lam_h, lam_a), "n": (n_h, n_a), "prior": (prior_h, prior_a),
            "idx": (idx_vs_home, idx_vs_away), "k": k, "notes": notes}


def market_lam(mkt3, total_hint=None):
    """市场联合拟合（三向 + 总进球一起进目标函数）"""
    if not mkt3:
        return None
    return mp.fit_market(mkt3, total_hint)


def scale_to_total(lam, total):
    """把一条 λ 按比例缩放到给定总进球（大小盘单独拟合用）"""
    if not lam or not total:
        return None
    s = float(lam[0]) + float(lam[1])
    if s <= 0:
        return None
    f = float(total) / s
    return (round(float(lam[0]) * f, 2), round(float(lam[1]) * f, 2))


def lam_pack(mkt3, total_hint=None):
    """四套 λ 显式命名，杜绝「不同方法同名」：
    odds_only   只拟合欧赔三向（不看大小盘）
    totals_only 只吃大小盘总进球（形状沿用 odds_only 比例）
    market_joint 三向 + 总进球联合拟合（用于融合与 Edge）
    """
    if not mkt3:
        return {"odds_only": None, "totals_only": None, "market_joint": None}
    lo = mp.fit_market(mkt3, None)
    return {
        "odds_only": lo,
        "totals_only": scale_to_total(lo, total_hint),
        "market_joint": mp.fit_market(mkt3, total_hint),
    }


def fuse(lam_a, lam_b, grade="A", n_eff=None):
    """融合权重 = 等级权重 × 样本折扣（同主客最小样本 / 5，上限 1）"""
    w = W_BY_GRADE.get(grade, 0.5)
    if n_eff and min(n_eff) > 0:
        w *= min(1.0, min(n_eff) / 5.0)
    if lam_a is None:
        return (lam_b[0], lam_b[1]), 0.0
    if lam_b is None:
        return (lam_a[0], lam_a[1]), 1.0
    return ((w * lam_a[0] + (1 - w) * lam_b[0],
             w * lam_a[1] + (1 - w) * lam_b[1]), w)


def three_way(lam):
    return mp.three_way(mp.grid_probs(lam[0], lam[1]))


def edge(lam_a, mkt3):
    """Edge = P_A - P_market（pp）"""
    if lam_a is None or not mkt3:
        return None
    pa = three_way(lam_a)
    return tuple((x - y) * 100 for x, y in zip(pa, mkt3))


def uncertainty(lam, n_eff, draws=4000, seed=20261027):
    """【λ_A 单独·对照用】λ ~ Gamma(shape=(n+k)·λ̂, rate=n+k)，逐次抽样算 P(主胜)，取 5%/95%。
    它把市场信息排除在外，不是完整预测不确定性，只用来和融合区间对照。
    """
    rng = np.random.default_rng(seed)
    nh = max(2.0, float(n_eff[0]))
    na = max(2.0, float(n_eff[1]))
    lh = rng.gamma(shape=nh * lam[0], scale=1.0 / nh, size=draws)
    la = rng.gamma(shape=na * lam[1], scale=1.0 / na, size=draws)
    # 向量化 Poisson 三向
    m = np.arange(0, 8)
    facts = np.array([float(math.factorial(k)) for k in m])

    def pmf(lam_vec):
        lam_vec = lam_vec[:, None]
        return np.exp(-lam_vec) * lam_vec ** m / facts

    Mh = pmf(lh)  # (draws, 8)
    Ma = pmf(la)
    # 主胜 = sum_{i>j} P(i,j)
    joint = Mh[:, :, None] * Ma[:, None, :]  # (draws, 8, 8)
    mask = np.triu(np.ones((8, 8)), k=1).T  # i>j
    p_home = (joint * mask).sum(axis=(1, 2))
    return float(np.percentile(p_home, 5) * 100), float(np.percentile(p_home, 95) * 100)


def uncertainty_fused(lam_a, lam_b, w, n_eff, draws=4000, seed=20261027):
    """【出结论用】模型参数不确定性区间。

    口径（用户 m01870 要求写清）：
      · 只对 λ_A 抽后验 Gamma(shape=(n+k)·λ_A, rate=n+k)；
      · λ_B（市场联合拟合）视为固定常数，不抽；
      · 每一次抽样都按 λ_C = w·λ_A_draw + (1−w)·λ_B 重新融合，再算泊松三向；
      · 取 P(主胜) 的 5% / 95% 分位。
    它回答的是「模型参数估错会把胜率算成多少」，不是「90% 把握赛果落在这一段」；
    赛果本身的不确定性由三向概率表达，不另设区间。
    w = 0（无独立模型）返回 None：此时区间退化为市场点值，谈不确定性无意义。
    """
    if lam_a is None or lam_b is None or w <= 0:
        return None
    rng = np.random.default_rng(seed)
    nh = max(2.0, float(n_eff[0]))
    na = max(2.0, float(n_eff[1]))
    lh = rng.gamma(shape=nh * float(lam_a[0]), scale=1.0 / nh, size=draws)
    la = rng.gamma(shape=na * float(lam_a[1]), scale=1.0 / na, size=draws)
    lc_h = w * lh + (1.0 - w) * float(lam_b[0])
    lc_a = w * la + (1.0 - w) * float(lam_b[1])
    m = np.arange(0, 8)
    facts = np.array([float(math.factorial(k)) for k in m])

    def pmf(lam_vec):
        v = lam_vec[:, None]
        return np.exp(-v) * v ** m / facts

    Mh, Ma = pmf(lc_h), pmf(lc_a)
    joint = Mh[:, :, None] * Ma[:, None, :]
    mask = np.triu(np.ones((8, 8)), k=1).T
    p_home = (joint * mask).sum(axis=(1, 2))
    return float(np.percentile(p_home, 5) * 100), float(np.percentile(p_home, 95) * 100)


def build_single(day, num, grade="A"):
    """单场 v3 全量数值（生成器直接消费）"""
    import settle
    d = ROOT / "state" / "intel" / day
    data = json.loads((d / f"_data_{day}.json").read_text(encoding="utf-8"))
    books = json.loads((d / f"_books_{day}.json").read_text(encoding="utf-8"))
    model = json.loads((d / f"_model_{day}.json").read_text(encoding="utf-8"))
    row = data[books[num]["id"]]
    v = model[num]
    mkt3 = v["market3"]
    la = data_lam(row, grade)
    pack = lam_pack(mkt3, v.get("ou_implied_total"))
    lb = pack["market_joint"]
    lc, w = fuse(la["lam"] if la else None, lb, grade, la["n"] if la else None)
    grid = mp.grid_probs(lc[0], lc[1])
    n_eff = (la["n"][0] + la["k"], la["n"][1] + la["k"]) if la else (3, 3)
    out = {
        "model_version": MODEL_VERSION,
        "data_snapshot": snapshot_id(day),
        "grade": grade,
        "data_grade": grade,
        "lam_data": la["lam"] if la else None,
        "lam_odds_only": pack["odds_only"],
        "lam_totals_only": pack["totals_only"],
        "lam_market_joint": lb,
        "lam_market": lb,
        "lam_fused": lc,
        "w_data": w,
        "evidence_grade": evidence_grade(w, grade),
        "k": la["k"] if la else 0.0,
        "n_eff": la["n"] if la else (0, 0),
        "three_data": three_way(la["lam"]) if la else None,
        "three_b": mkt3,
        "three_c": three_way(lc),
        "edge_ab": edge(la["lam"] if la else None, mkt3),
        "notes": la["notes"] if la else ["无非同主客样本，λ 只走市场反推"],
        "interval_home_data": uncertainty(la["lam"], n_eff) if la else None,
        "interval_home": uncertainty_fused(la["lam"] if la else None, lb, w, n_eff),
        "interval_meta": {
            "kind": "model_parameter_market_fixed",
            "label": "模型参数不确定性（市场 λ_B 视为固定）",
            "draws": 4000,
            "seed": 20261027,
            "market_fixed": True,
            "n_eff": [round(float(n_eff[0]), 3), round(float(n_eff[1]), 3)],
            "refused_because": None if (la and lb and w > 0) else "无独立模型或无市场拟合，区间不适用",
        },
        "top_scores": _top_scores(grid, 8),
        "sens": mp.sens_grid(lc[0], lc[1]),
    }
    ahline = v.get("ah_line")
    if ahline is not None:
        ev = settle.ev_ah(grid, ahline, v["ah_water"][0], v["ah_water"][1])
        out["ah"] = {"line": ahline, "side": v.get("ah_side"), "dist": ev[2],
                     "ev": (ev[0] * 100, ev[1] * 100), "water": tuple(v["ah_water"])}
    else:
        out["ah"] = {"line": None, "side": None, "dist": None, "ev": (None, None), "water": (0, 0)}
    ouline = v.get("ou_line")
    if ouline is not None:
        ev = settle.ev_ou(grid, abs(ouline), v["ou_water"][0], v["ou_water"][1])
        out["ou"] = {"line": ouline, "dist": ev[2], "ev": (ev[0] * 100, ev[1] * 100), "water": tuple(v["ou_water"])}
    else:
        out["ou"] = {"line": None, "dist": None, "ev": (None, None), "water": (0, 0)}
    mc = mp.mc_sim(lc[0], lc[1], ahline, abs(ouline) if ouline is not None else None)
    out["mc"] = mc
    tw = three_way(lc)
    out["mc_gap"] = max(abs(mc["w"] - tw[0]), abs(mc["d"] - tw[1]), abs(mc["l"] - tw[2])) * 100
    return out


def _top_scores(grid, n=8):
    pairs = [(grid[i][j], i, j) for i in range(len(grid)) for j in range(len(grid))]
    pairs.sort(reverse=True)
    return [(f"{i}-{j}", p) for p, i, j in pairs[:n]]


def build(day="20261027", grade_map=None):
    d = ROOT / "state" / "intel" / day
    data = json.loads((d / f"_data_{day}.json").read_text(encoding="utf-8"))
    books = json.loads((d / f"_books_{day}.json").read_text(encoding="utf-8"))
    model = json.loads((d / f"_model_{day}.json").read_text(encoding="utf-8"))
    grade_map = grade_map or {}
    out = {}
    for num, b in sorted(books.items()):
        row = data[b["id"]]
        v = model.get(num) or {}
        grade = grade_map.get(num, "A")
        mkt3 = v.get("market3")
        la = data_lam(row, grade)
        pack = lam_pack(mkt3, v.get("ou_implied_total"))
        lb = pack["market_joint"]
        lc, w = fuse(la["lam"] if la else None, lb, grade,
                     la["n"] if la else None)
        ne = (la["n"][0] + la["k"], la["n"][1] + la["k"]) if la else (3, 3)
        out[num] = {
            "model_version": MODEL_VERSION,
            "data_snapshot": snapshot_id(day),
            "grade": grade,
            "data_grade": grade,
            "lam_data": la["lam"] if la else None,
            "lam_odds_only": pack["odds_only"],
            "lam_totals_only": pack["totals_only"],
            "lam_market_joint": lb,
            "lam_market": lb,
            "lam_fused": lc,
            "w_data": w,
            "evidence_grade": evidence_grade(w, grade),
            "three_data": three_way(la["lam"]) if la else None,
            "three_market": mkt3,
            "three_fused": three_way(lc),
            "edge_A_vs_mkt": edge(la["lam"] if la else None, mkt3),
            "n_eff": la["n"] if la else (0, 0),
            "interval_home_data": uncertainty(la["lam"], ne) if la else None,
            "interval_home": uncertainty_fused(la["lam"] if la else None, lb, w, ne),
            "notes": (la["notes"] if la else ["无非同主客样本，λ 只走市场反推"]),
        }
    return out


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else "20261027"
    d = ROOT / "state" / "intel" / day
    audit_path = d / f"_audit_{day}.json"
    grade_map = {}
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        for num, r in audit.items():
            grade_map[num] = r["grade"]
    res = build(day, grade_map)
    out_path = d / f"_model_v3_{day}.json"
    out_path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for num, r in res.items():
        la, lb, lc = r["lam_data"], r["lam_market"], r["lam_fused"]
        f = lambda x: "—" if x is None else f"{x[0]:.2f}/{x[1]:.2f}"
        e = r["edge_A_vs_mkt"]
        print(f"{num} [{r['grade']}] A {f(la)} | B {f(lb)} | C {f(lc)} (w={r['w_data']:.2f}) "
              f"| Edge {'—' if e is None else '/'.join(f'{x:+.1f}' for x in e)} "
              "| P(主) 参数区间 " + ("n/a" if not r["interval_home"] else
              f"{r['interval_home'][0]:.0f}–{r['interval_home'][1]:.0f}%"))
        _d = r["interval_home_data"]
        print("   数据侧区间 " + ("n/a" if not _d else f"{_d[0]:.0f}–{_d[1]:.0f}%") + f" | 证据等级 {r['evidence_grade']}")
    print(f"→ {out_path}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
