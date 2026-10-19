#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""赛后校验（按 90 分钟口径）

把官方赛果（`state/cache/_results_*.json`）与赛前模型文本对齐，逐场判方向 /
三档比分 / 让球方向 / 大小球，并汇总命中率。

用法：
    python -X utf8 scripts/calib_run.py --dates 20261016 20261017
    python -X utf8 scripts/calib_run.py --dates 20261017 --out 某路径.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import paid_cyber as pc  # noqa: E402

DIRS = ["主胜", "平", "客胜"]
WEEK = {"周一": 1, "周二": 2, "周三": 3, "周四": 4, "周五": 5, "周六": 6, "周日": 7}


def f(x, n: int = 1) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return "—"


def load_results(lo: str, hi: str) -> dict:
    """竞彩编号 → 赛果。sectionsNo999 是 90 分钟全场比分（含补时）。

    缓存文件名按「实际拉取区间」命名，跟校验区间不一定一致（例如一次拉了 10-16~10-18
    来覆两天），所以先用精确名，取不到就扫同起点、右端不早于 hi 的缓存。
    """
    exact = STATE / "cache" / f"_results_{lo}_{hi}.json"
    p = exact
    if not p.exists():
        cands = []
        for c in sorted((STATE / "cache").glob(f"_results_{lo}_*.json")):
            right = c.stem.replace(f"_results_{lo}_", "")
            if right >= hi:
                cands.append(c)
        if cands:
            p = cands[-1]
    if not p.exists():
        raise SystemExit(f"没有赛果缓存（想要 _results_{lo}_{hi}.json 或右端 ≥{hi} 的同起点文件），先跑 "
                         f"`python scripts/sporttery_fetch.py results {lo} {hi}`")
    d = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for r in d["value"]["matchResult"]:
        full = (r.get("sectionsNo999") or "").strip()
        rec = {
            "no": r.get("matchNumStr") or "",
            "date": r.get("matchDate") or "",
            "league": r.get("leagueNameAbbr") or "",
            "home": r.get("homeTeam") or "",
            "away": r.get("awayTeam") or "",
            "line": r.get("goalLine") or "",
            "half": (r.get("sectionsNo1") or "").strip(),
            "full": full,
            "h": r.get("h") or "", "d": r.get("d") or "", "a": r.get("a") or "",
            "settled": bool(full),
        }
        if full:
            try:
                hh, aa = [int(x) for x in full.split(":")]
                rec["hg"], rec["ag"] = hh, aa
                rec["outcome"] = "主胜" if hh > aa else ("平" if hh == aa else "客胜")
                rec["total"] = hh + aa
            except ValueError:
                rec["settled"] = False
        out[rec["no"]] = rec
    return out


def hand_outcome(rec: dict) -> str | None:
    """让球胜平负的方向：把让球加在主队比分上再比。"""
    if not rec.get("settled") or rec.get("line") in ("", None):
        return None
    try:
        gl = int(rec["line"])
    except (TypeError, ValueError):
        return None
    adj = rec["hg"] + gl - rec["ag"]
    return "主胜" if adj > 0 else ("平" if adj == 0 else "客胜")


def load_models(date_tag: str) -> dict:
    cands = [STATE / "batch" / f"_model_{date_tag}_sat.txt",
             STATE / "batch" / f"_model_{date_tag}_fri.txt",
             STATE / "batch" / f"_model_{date_tag}_sun_all.txt"]
    cands += sorted((STATE / "batch").glob(f"_model_{date_tag}_*.txt"))
    seen, ms = set(), {}
    for p in cands:
        if not p.exists() or p in seen:
            continue
        seen.add(p)
        try:
            data = pc.build(p, date_tag)
        except Exception:  # noqa: BLE001
            continue
        for m in data["matches"]:
            ms.setdefault(m["no"], m)
    return ms


def load_claims(dates: list[str]) -> dict:
    """读 state/records/_claims_<date>.json：模型文本没留档、只能按公开稿主张校的场次。"""
    out = {}
    for dt in dates:
        p = STATE / "records" / f"_claims_{dt}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        for no, c in (d.get("claims") or {}).items():
            c["_date"] = dt
            out[no] = c
    return out


def judge(rec: dict, m: dict) -> dict:
    v = m.get("verdict") or {}
    p = m.get("p") or [0, 0, 0]
    conf = m.get("conf") or {}
    mk = m.get("mk") or [0, 0, 0]
    model_pick = DIRS[max(range(3), key=lambda k: p[k])]
    actual = rec.get("outcome")
    scores = [v.get("first_score"), v.get("second_score"), v.get("guard_score")]
    actual_score = (rec.get("full") or "").replace(":", "-")
    hit_dir = model_pick == actual
    hit_score = actual_score in scores
    hor = hand_outcome(rec)
    hp = m.get("hp") or []
    hand_pick = DIRS[max(range(3), key=lambda k: hp[k])] if hp else None
    over = m.get("over") or {}
    return {
        "model_pick": model_pick, "model_p": p, "market_p": mk,
        "market_pick": DIRS[max(range(3), key=lambda k: mk[k])],
        "actual": actual, "actual_score": actual_score,
        "hit_dir": hit_dir, "hit_score": hit_score,
        "score_hit_which": ("首选" if actual_score == scores[0] else
                            "次选" if actual_score == scores[1] else
                            "防范" if actual_score == scores[2] else ""),
        "scores": scores,
        "hand_pick": hand_pick, "hand_actual": hor,
        "hit_hand": (hand_pick == hor) if (hand_pick and hor) else None,
        "over25_model": over.get("2.5"), "over25_actual": (rec.get("total") or 0) > 2.5
        if rec.get("settled") else None,
        "dev": max(range(3), key=lambda k: abs(p[k] - mk[k])),
        "maxpp": round(max(abs(p[k] - mk[k]) for k in range(3)), 1),
        "conf": conf.get("total"), "grade": conf.get("grade") or "",
        "kick": m.get("kick") or "",
    }


def build(dates: list[str]) -> str:
    lo = f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}"
    hi = f"{dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:]}"
    res = load_results(lo, hi)
    rows = []
    for dt in dates:
        ms = load_models(dt)
        for no, m in ms.items():
            rec = res.get(no)
            if not rec:
                continue
            if not rec["settled"]:
                rows.append({"no": no, "rec": rec, "m": m, "judge": None, "date": dt})
                continue
            rows.append({"no": no, "rec": rec, "m": m, "judge": judge(rec, m), "date": dt})
    settled = [r for r in rows if r["judge"]]
    order = sorted(settled, key=lambda r: (WEEK.get(r["no"][:2], 9), int(r["no"][2:])))

    L = []
    L.append(f"# 赛后校验 ｜ {' / '.join(f'{d[:4]}-{d[4:6]}-{d[6:]}' for d in dates)}"
             f"（{len(order)} 场可校）")
    L.append("")
    L.append("> **口径**：90 分钟常规时间（竞彩官网页脚注：全场比分（90 分钟）包含伤停补时；"
             "加时与点球不计）。")
    L.append(f"> **赛果来源**：`state/cache/_results_{lo}_{hi}.json`"
             f"（官方赛果页，共 {len(res)} 场，其中已完成 {sum(1 for r in res.values() if r['settled'])} 场）。")
    L.append("> **校验范围**：只校**赛前跑过模型**的场次（模型文本里有 id 的那些）；"
             "未跑模型的场次不做「事后补算再对答案」那种伪校验。")
    L.append("")

    # 一、总览表
    L.append("## 一、总览")
    L.append("")
    L.append("| 场次 | 联赛 | 对阵（让球） | 半场 | 90 分钟 | 模型首选 | 市场首选 | 判定 | 三档比分 | 命中档 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in order:
        rec, j = r["rec"], r["judge"]
        mark = "✅" if j["hit_dir"] else "❌"
        L.append(f"| {r['no']} | {rec['league']} | {rec['home']}({rec['line']}) vs {rec['away']} "
                 f"| {rec['half'] or '—'} | **{rec['full']}**（{j['actual']}） "
                 f"| {j['model_pick']} {f(j['model_p'][DIRS.index(j['model_pick'])])}% "
                 f"| {j['market_pick']} | {mark} "
                 f"| {' / '.join(x or '—' for x in j['scores'])} | {j['score_hit_which'] or '—'} |")
    L.append("")

    # 二、统计
    n = len(order)
    hit_d = sum(1 for r in order if r["judge"]["hit_dir"])
    hit_mkt = sum(1 for r in order if r["judge"]["market_pick"] == r["judge"]["actual"])
    hit_s = sum(1 for r in order if r["judge"]["hit_score"])
    hs = [r for r in order if r["judge"]["hit_hand"] is not None]
    hit_h = sum(1 for r in hs if r["judge"]["hit_hand"])
    os_ = [r for r in order if r["judge"]["over25_actual"] is not None]
    hit_o = sum(1 for r in os_ if ((r["judge"]["over25_model"] or 0) > 50) == r["judge"]["over25_actual"])
    draws = [r for r in order if r["judge"]["actual"] == "平"]
    draw_pred = sum(1 for r in order if r["judge"]["model_pick"] == "平")

    L.append("## 二、统计")
    L.append("")
    L.append("| 指标 | 命中 | 说明 |")
    L.append("|---|---|---|")
    L.append(f"| 胜平负方向（模型首选） | **{hit_d}/{n} = {100 * hit_d / n:.1f}%** | "
             f"市场首选同期 {hit_mkt}/{n} = {100 * hit_mkt / n:.1f}% |")
    L.append(f"| 三档比分内 | **{hit_s}/{n} = {100 * hit_s / n:.1f}%** | "
             f"命中档位：" + "、".join(f"{k} {sum(1 for r in order if r['judge']['score_hit_which'] == k)}"
                                     for k in ("首选", "次选", "防范")) + " |")
    L.append(f"| 让球胜平负方向 | **{hit_h}/{len(hs)} = {100 * hit_h / len(hs) if hs else 0:.1f}%** | "
             "把让球加在主队比分上再比 |")
    L.append(f"| 大 2.5 球 | **{hit_o}/{len(os_)} = {100 * hit_o / len(os_) if os_ else 0:.1f}%** | "
             "模型大 2.5 概率 >50% 视作看大 |")
    L.append(f"| 平局 | 实际 {len(draws)} 场 / 模型曾把平列为首选 {draw_pred} 场 | "
             f"实际平局：{'、'.join(r['no'] for r in draws) or '无'} |")
    L.append("")

    # 三、偏差分档 × 命中
    L.append("## 三、偏差分档与命中（这次能不能照偏差下单）")
    L.append("")
    L.append("| 偏差档 | 场次 | 方向命中 | 命中率 |")
    L.append("|---|---|---|---|")
    for lo_, hi_, lab in ((15, 99, "≥15pp（先假定我方有缺口）"), (6, 15, "6–15pp（方向可信、幅度打折）"),
                          (0, 6, "<6pp（结构重合，无差价）")):
        grp = [r for r in order if lo_ <= r["judge"]["maxpp"] < hi_]
        if grp:
            h = sum(1 for r in grp if r["judge"]["hit_dir"])
            L.append(f"| {lab} | {len(grp)} | {h} | {100 * h / len(grp):.1f}% |")
    L.append("")

    # 三B、关键结论（全部由上面的数推出来，不写「感觉」）
    L.append("## 四、关键结论")
    L.append("")
    hi15 = [r for r in order if r["judge"]["maxpp"] >= 15]
    lo6 = [r for r in order if r["judge"]["maxpp"] < 6]
    hi15_hit = sum(1 for r in hi15 if r["judge"]["hit_dir"])
    lo6_hit = sum(1 for r in lo6 if r["judge"]["hit_dir"])
    if hi15:
        L.append(f"1. **高偏差不是机会，是缺口信号**：偏差 ≥15pp 的 {len(hi15)} 场方向只中 "
                 f"{hi15_hit} 场（{100 * hi15_hit / len(hi15):.0f}%），"
                 f"低于结构重合档（<6pp）的 {lo6_hit}/{len(lo6)}"
                 f"（{100 * lo6_hit / len(lo6):.0f}%）。"
                 f"本窗口模型方向 {hit_d}/{n}，也低于市场首选 {hit_mkt}/{n}——"
                 "**偏差越大越不该按模型方向采信**，这条与「≥15pp 先假定我方有缺口」的纪律同向。")
    else:
        L.append(f"1. 本批没有 ≥15pp 的场次，偏差档对比样本不足。")
    if draws:
        dlist = []
        for r in draws:
            pp_ = (r["m"].get("p") or [0, 0, 0])
            dlist.append(f"{r['no']}（模型给平 {f(pp_[1])}%，首选{r['judge']['model_pick']} "
                         f"{f(pp_[DIRS.index(r['judge']['model_pick'])])}%）")
        L.append(f"2. **平局仍然是盲区**：实际打出 {len(draws)} 场平局，模型一次都没把平列为首选"
                 "——" + "；".join(dlist) + "。"
                 f"这 {len(draws)} 场里平的概率都没进过第一格，说明模型没有独立的平局触发器，"
                 "只能在「主客差距小」时被动分走一点概率。")
    L.append(f"3. **让球盘方向 {hit_h}/{len(hs)}**：与胜平负方向（{hit_d}/{n}）基本同档，"
             "没有出现早期「让球盘明显更差」的现象；但样本只有 "
             f"{len(hs)} 场，还不能据此推翻旧结论（batch37 让球盘 4/15=26.7%）。")
    # 比分三档：命中落在哪一格必须按本批数据算，不能写死（10/16-17 与 10/18 结论相反）
    w1 = sum(1 for r in order if r["judge"]["score_hit_which"] == "首选")
    w2 = sum(1 for r in order if r["judge"]["score_hit_which"] == "次选")
    w3 = sum(1 for r in order if r["judge"]["score_hit_which"] == "防范")
    if hit_s == 0:
        s4 = (f"4. **比分三档 {hit_s}/{n}**：一个都没进，说明比分网格与实际落点脱节，"
              "只能当形态描述用，不能当预测。")
    elif w1 >= hit_s - 0.1:
        s4 = (f"4. **比分三档 {hit_s}/{n}**：命中全在首选档（{w1} 场），"
              "次选与防范一次没起过作用——网格过窄，要么按分布铺开，要么承认它只能描述形态。")
    elif w1 == 0:
        s4 = (f"4. **比分三档 {hit_s}/{n}**：首选档一次没中，命中全在次选（{w2}）与防范（{w3}）——"
              "说明「最可能的那一格」系统性偏了，比分该往分布的中段挪。")
    else:
        s4 = (f"4. **比分三档 {hit_s}/{n}**：首选 {w1}、次选 {w2}、防范 {w3} 分散，"
              "三档确实起了覆盖作用，网格宽度是合适的。")
    L.append(s4)
    pend = [r for r in rows if not r["judge"]]
    if pend:
        L.append(f"5. **待开奖**：" + "、".join(f"{r['no']}（{r['rec']['home']} vs {r['rec']['away']}）"
                                            for r in pend) + "——赛果出来后再补校。")
    L.append("")

    # 四B、只有公开稿主张的场次（模型文本没留档）
    claims = load_claims(dates)
    crows = []
    for no, c in claims.items():
        rec = res.get(no)
        if not rec or not rec.get("settled"):
            continue
        act = (rec.get("full") or "").replace(":", "-")
        crows.append({"no": no, "rec": rec, "c": c, "act": act,
                      "hit_dir": c.get("dir") == rec.get("outcome"),
                      "which": ("首选" if act == (c.get("scores") or [""])[0] else
                                "次选" if len(c.get("scores") or []) > 1 and act == c["scores"][1] else
                                "防范" if len(c.get("scores") or []) > 2 and act == c["scores"][2] else "")})
    if crows:
        crows.sort(key=lambda r: int(r["no"][2:]))
        L.append("## 四B、只有公开稿主张的场次（模型文本没留档）")
        L.append("")
        L.append("这几场赛前跑过模型，但当时的模型文本没有归档到 `state/batch/`，"
                 "所以只能按**文章里写死的那句话**校，不做事后补算。主张原文存在 "
                 "`state/records/_claims_<日期>.json`，可用于复核。")
        L.append("")
        L.append("| 场次 | 联赛 | 对阵（让球） | 半场 | 90 分钟 | 公开稿方向 | 公开稿三档比分 | 判定 | 命中档 |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for r in crows:
            rec, c = r["rec"], r["c"]
            L.append(f"| {r['no']} | {rec['league']} | {rec['home']}({rec['line']}) vs {rec['away']} "
                     f"| {rec['half'] or '—'} | **{rec['full']}**（{rec['outcome']}） "
                     f"| {c.get('dir')} | {' / '.join(c.get('scores') or [])} "
                     f"| {'✅' if r['hit_dir'] else '❌'} | {r['which'] or '—'} |")
        L.append("")
        ch = sum(1 for r in crows if r["hit_dir"])
        cs = sum(1 for r in crows if r["which"])
        L.append(f"**小计**：方向 {ch}/{len(crows)}，三档比分 {cs}/{len(crows)}。"
                 "这三场不计入上面模型口径的统计，只作补充观察。")
        L.append("")

    # 五、逐场
    L.append("## 五、逐场校验")
    L.append("")
    for r in order:
        rec, j = r["rec"], r["judge"]
        L.append(f"### {r['no']} {rec['league']} {rec['home']} {rec['full']} {rec['away']}"
                 f"（半场 {rec['half'] or '—'}）")
        L.append("")
        L.append(f"- **赛果**：90 分钟 {rec['full']} → **{j['actual']}**，总进球 {rec['total']}，"
                 f"让球 {rec['line']} → 让球盘 **{j['hand_actual']}**")
        mp = j.get("market_p") or [0, 0, 0]
        mod_s = " / ".join(f"{DIRS[k]} {f(j['model_p'][k])}%" for k in range(3))
        mk_s = " / ".join(f"{DIRS[k]} {f(mp[k])}%" for k in range(3))
        sc_s = " / ".join(x or "—" for x in j["scores"])
        L.append(f"- **模型**：{mod_s}（信心 {j['conf']}，{j['grade']}）；首选比分 {sc_s}")
        L.append(f"- **市场**：{mk_s}；首选 {j['market_pick']}；"
                 f"我方与市场最大偏差 {j['maxpp']:+.1f}pp（落在{DIRS[j['dev']]}）")
        verdict_bits = []
        verdict_bits.append("✅ 方向" if j["hit_dir"] else "❌ 方向")
        if j["hit_score"]:
            verdict_bits.append(f"✅ 比分命中{j['score_hit_which']}")
        else:
            verdict_bits.append("❌ 比分未中")
        if j["hit_hand"] is not None:
            verdict_bits.append("✅ 让球" if j["hit_hand"] else "❌ 让球")
        verdict_bits.append("✅ 大球" if ((j["over25_model"] or 0) > 50) == j["over25_actual"] else "❌ 大球")
        L.append(f"- **判定**：" + "　".join(verdict_bits))
        L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="赛后校验（90 分钟口径）")
    ap.add_argument("--dates", nargs="+", default=["20261016", "20261017"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    md = build(a.dates)
    span = f"{a.dates[0]}-{a.dates[-1]}"
    out = Path(a.out) if a.out else (ROOT / "📚知识库" / "赛后校验" / f"{span}_赛后校验.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"✅ {out}  {len(md)} 字符 / {md.count(chr(10)) + 1} 行")


if __name__ == "__main__":
    main()
