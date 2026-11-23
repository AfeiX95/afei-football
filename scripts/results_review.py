"""传足近 N 期 + 竞彩近 N 天 赛果复盘（官方 webapi 直取，90 分钟口径）。

用法：
    python -X utf8 scripts/results_review.py --end 2026-11-23 --days 30 --issues 30 --base 100

产物：
    state/cache/_review_sfc_<end>.json      传足原始开奖（近 base 期）
    state/cache/_review_jc_<begin>_<end>.json 竞彩原始赛果（近 days 天）
    stdout 打印 JSON 汇总（供写复盘报告）
口径：竞彩只认 sectionsNo999（90 分钟）；h/d/a 为胜平负最终 SP；无胜平负 SP 的场次不进热门命中分母。
"""
import argparse, json, os, sys, time, datetime as dt
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sporttery_fetch as sf  # noqa: E402

ROOT = sf.ROOT
CACHE = sf.OUT_CACHE


def fetch_sfc(n):
    rows, page = [], 1
    while len(rows) < n:
        st, b = sf.raw(sf.HOST + "/gateway/lottery/getHistoryPageListV1.qry?gameNo=90&provinceId=0"
                       "&pageSize=30&isVerify=1&pageNo=%d" % page, referer="https://www.sporttery.cn/")
        if st != 200:
            print("sfc HTTP", st, file=sys.stderr); break
        lst = json.loads(b.decode())["value"]["list"]
        if not lst:
            break
        rows += lst; page += 1; time.sleep(0.3)
    return rows[:n]


def fetch_jc(begin, end):
    out, d0, d1 = [], dt.date.fromisoformat(begin), dt.date.fromisoformat(end)
    cur = d0
    while cur <= d1:
        ce = min(cur + dt.timedelta(days=6), d1)
        page = 1
        while True:
            st, b = sf.get("/gateway/uniform/football/getUniformMatchResultV1.qry",
                           {"matchBeginDate": cur.isoformat(), "matchEndDate": ce.isoformat(), "leagueId": "",
                            "pageSize": 100, "pageNo": page, "isFix": 0, "matchPage": 1, "pcOrWap": 1},
                           referer=sf.REF_SGKJ)
            if st != 200:
                print("jc HTTP", st, cur, file=sys.stderr); break
            v = json.loads(b.decode()).get("value") or {}
            out += v.get("matchResult") or []
            if page >= int(v.get("pages") or 1):
                break
            page += 1; time.sleep(0.3)
        cur = ce + dt.timedelta(days=1); time.sleep(0.3)
    seen, uniq = set(), []
    for m in out:
        if m.get("matchId") in seen:
            continue
        seen.add(m.get("matchId")); uniq.append(m)
    return uniq


def num(s):
    try:
        return int(str(s).replace(",", ""))
    except Exception:
        return 0


def fnum(s):
    try:
        return float(s)
    except Exception:
        return None


def tier(cnt, amt):
    if cnt == 0:
        return "滚存(0注)"
    if amt >= 5_000_000:
        return "500万封顶"
    if amt >= 1_000_000:
        return "100-500万"
    if amt >= 50_000:
        return "5-100万"
    return "5万以下火锅"


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def analyze_sfc(rows, n_recent, jc_index):
    per, recent = [], rows[:n_recent]
    for r in rows:
        res = r["lotteryDrawResult"].split()
        p1 = (r.get("prizeLevelList") or [{}])
        first = next((x for x in p1 if x.get("prizeLevel") == "一等奖"), {})
        second = next((x for x in p1 if x.get("prizeLevel") == "二等奖"), {})
        rj = (r.get("prizeLevelListRj") or [{}])[0]
        c = Counter(res)
        leagues = Counter(m.get("matchName") for m in r.get("matchList") or [])
        # 冷门：联到竞彩 SP，赛果方向 SP>=3.5 视为冷、该场最低 SP 方向打出视为热门兑现
        cold, fav_hit, fav_n, cold_list = 0, 0, 0, []
        for m in r.get("matchList") or []:
            hid = m.get("infohubMatchId")
            j = jc_index.get(hid) if isinstance(hid, (int, str)) else None
            if not j:
                continue
            sp = {"3": fnum(j.get("h")), "1": fnum(j.get("d")), "0": fnum(j.get("a"))}
            if None in sp.values():
                continue
            fav_n += 1
            fav = min(sp, key=sp.get)
            if m["result"] == fav:
                fav_hit += 1
            if sp.get(m["result"], 0) >= 3.5:
                cold += 1
                cold_list.append("%s %s %s-%s(%s) SP%.2f" % (m["matchNum"], m["matchName"], m["masterTeamAllName"],
                                                            m["guestTeamAllName"], m["czScore"], sp[m["result"]]))
        per.append({
            "issue": r["lotteryDrawNum"], "date": r["lotteryDrawTime"], "result": "".join(res),
            "n3": c["3"], "n1": c["1"], "n0": c["0"], "nstar": c["*"],
            "first_cnt": num(first.get("stakeCount")), "first_amt": num(first.get("stakeAmount")),
            "second_cnt": num(second.get("stakeCount")), "second_amt": num(second.get("stakeAmount")),
            "rj_cnt": num(rj.get("stakeCount")), "rj_amt": num(rj.get("stakeAmount")),
            "sale": num(r.get("totalSaleAmount")), "sale_rj": num(r.get("totalSaleAmountRj")),
            "pool": num(r.get("poolBalanceAfterdraw")),
            "tier": tier(num(first.get("stakeCount")), num(first.get("stakeAmount"))),
            "leagues": dict(leagues), "jc_matched": fav_n, "fav_hit": fav_hit, "cold": cold, "cold_list": cold_list,
        })

    def agg(ps):
        t = sum(p["n3"] + p["n1"] + p["n0"] for p in ps) or 1
        return {
            "periods": len(ps),
            "share_3": pct(sum(p["n3"] for p in ps), t), "share_1": pct(sum(p["n1"] for p in ps), t),
            "share_0": pct(sum(p["n0"] for p in ps), t),
            "avg_3": round(sum(p["n3"] for p in ps) / len(ps), 2), "avg_1": round(sum(p["n1"] for p in ps) / len(ps), 2),
            "avg_0": round(sum(p["n0"] for p in ps) / len(ps), 2),
            "tiers": dict(Counter(p["tier"] for p in ps)),
            "rj_tiers": dict(Counter("<1千" if p["rj_amt"] < 1000 else "1千-1万" if p["rj_amt"] < 10000 else
                                     "1-10万" if p["rj_amt"] < 100000 else ">=10万" for p in ps)),
            "median_first": sorted(p["first_amt"] for p in ps)[len(ps) // 2],
            "median_rj": sorted(p["rj_amt"] for p in ps)[len(ps) // 2],
            "avg_sale": round(sum(p["sale"] for p in ps) / len(ps)),
            "fav_hit": pct(sum(p["fav_hit"] for p in ps), sum(p["jc_matched"] for p in ps)),
            "jc_matched": sum(p["jc_matched"] for p in ps),
            "cold_per_period": round(sum(p["cold"] for p in ps) / len(ps), 2),
        }
    lg = Counter()
    lg_res = defaultdict(Counter)
    for r in recent:
        for m in r.get("matchList") or []:
            lg[m["matchName"]] += 1; lg_res[m["matchName"]][m["result"]] += 1
    return {"recent": agg(per[:n_recent]), "base": agg(per), "per": per[:n_recent],
            "league_mix": {k: {"n": v, **dict(lg_res[k])} for k, v in lg.most_common()}}


def analyze_jc(rows):
    done = [m for m in rows if str(m.get("matchResultStatus")) == "2" and m.get("sectionsNo999") not in (None, "", "-")]
    out = {"total_rows": len(rows), "settled": len(done)}
    res, gl_res, goals, scores, ht_ft = Counter(), Counter(), Counter(), Counter(), Counter()
    buckets = defaultdict(lambda: [0, 0, 0.0])  # 热门SP桶: n, hit, sum implied
    by_lg = defaultdict(lambda: {"n": 0, "H": 0, "D": 0, "A": 0, "fav_n": 0, "fav_hit": 0, "goals": 0})
    by_day = defaultdict(lambda: {"n": 0, "fav_n": 0, "fav_hit": 0, "cold": 0})
    colds, fav_n, fav_hit, draw_sp_sum, win_sp = [], 0, 0, 0, []
    implied = {"H": [0.0, 0], "D": [0.0, 0], "A": [0.0, 0]}
    for m in done:
        try:
            h, a = [int(x) for x in m["sectionsNo999"].split(":")]
        except Exception:
            continue
        r = "H" if h > a else "D" if h == a else "A"
        res[r] += 1; goals[min(h + a, 7)] += 1; scores["%d:%d" % (h, a)] += 1
        L = by_lg[m.get("leagueNameAbbr")]; L["n"] += 1; L[r] += 1; L["goals"] += h + a
        D = by_day[m["matchDate"]]; D["n"] += 1
        try:
            gl = int(str(m.get("goalLine") or "0").replace("+", ""))
            adj = h + gl - a
            gl_res["让胜" if adj > 0 else "让平" if adj == 0 else "让负"] += 1
        except Exception:
            pass
        if m.get("sectionsNo1") and ":" in str(m["sectionsNo1"]):
            hh, ha = [int(x) for x in m["sectionsNo1"].split(":")]
            hr = "H" if hh > ha else "D" if hh == ha else "A"
            ht_ft[hr + r] += 1
        sp = {"H": fnum(m.get("h")), "D": fnum(m.get("d")), "A": fnum(m.get("a"))}
        if None in sp.values() or min(sp.values()) <= 1.0:
            continue
        s = sum(1 / v for v in sp.values())
        for k in sp:
            implied[k][0] += (1 / sp[k]) / s; implied[k][1] += 1
        fav = min(sp, key=sp.get)
        fav_n += 1; L["fav_n"] += 1; D["fav_n"] += 1
        hit = r == fav
        fav_hit += hit; L["fav_hit"] += hit; D["fav_hit"] += hit
        f = sp[fav]
        bk = "<=1.30" if f <= 1.30 else "1.31-1.50" if f <= 1.50 else "1.51-1.80" if f <= 1.80 else \
             "1.81-2.10" if f <= 2.10 else ">2.10"
        buckets[bk][0] += 1; buckets[bk][1] += hit; buckets[bk][2] += (1 / f) / s
        win_sp.append(sp[r])
        if sp[r] >= 4.0:
            D["cold"] += 1
            colds.append({"date": m["matchDate"], "num": m["matchNumStr"], "lg": m.get("leagueNameAbbr"),
                          "home": m.get("allHomeTeam") or m.get("homeTeam"), "away": m.get("allAwayTeam") or m.get("awayTeam"),
                          "score": m["sectionsNo999"], "res": r, "sp": sp[r], "fav": fav, "fav_sp": f})
    n = sum(res.values()) or 1
    out.update({
        "had": {k: [res[k], pct(res[k], n)] for k in "HDA"},
        "implied_avg": {k: round(100 * v[0] / v[1], 1) if v[1] else None for k, v in implied.items()},
        "hhad": {k: [v, pct(v, sum(gl_res.values()))] for k, v in gl_res.items()},
        "goals": {str(k) + ("+" if k == 7 else ""): v for k, v in sorted(goals.items())},
        "avg_goals": round(sum(min(k, 7) * v for k, v in goals.items()) / n, 2),
        "top_scores": scores.most_common(12),
        "ht_ft": ht_ft.most_common(9),
        "fav": {"n": fav_n, "hit": fav_hit, "rate": pct(fav_hit, fav_n)},
        "fav_buckets": {k: {"n": v[0], "hit": v[1], "rate": pct(v[1], v[0]),
                            "implied": round(100 * v[2] / v[0], 1) if v[0] else None}
                        for k, v in sorted(buckets.items())},
        "avg_win_sp": round(sum(win_sp) / len(win_sp), 2) if win_sp else None,
        "cold_n": len(colds), "cold_rate": pct(len(colds), fav_n),
        "colds_top": sorted(colds, key=lambda x: -x["sp"])[:20],
        "by_league": {k: {**v, "fav_rate": pct(v["fav_hit"], v["fav_n"]), "draw_rate": pct(v["D"], v["n"]),
                          "avg_goals": round(v["goals"] / v["n"], 2)}
                      for k, v in sorted(by_lg.items(), key=lambda kv: -kv[1]["n"]) if v["n"] >= 12},
        "by_week": {},
    })
    wk = defaultdict(lambda: [0, 0, 0, 0, 0])
    for d, v in by_day.items():
        w = dt.date.fromisoformat(d).isocalendar()[1]
        wk[w][0] += v["n"]; wk[w][1] += v["fav_n"]; wk[w][2] += v["fav_hit"]; wk[w][3] += v["cold"]
    for w, v in sorted(wk.items()):
        ds = sorted(d for d in by_day if dt.date.fromisoformat(d).isocalendar()[1] == w)
        out["by_week"]["%s~%s" % (ds[0], ds[-1])] = {"n": v[0], "fav_rate": pct(v[2], v[1]), "cold": v[3]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--end", default=dt.date.today().isoformat())
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--issues", type=int, default=30)
    ap.add_argument("--base", type=int, default=100)
    a = ap.parse_args()
    sf.warmup()
    end = dt.date.fromisoformat(a.end)
    begin = end - dt.timedelta(days=a.days - 1)
    sfc = fetch_sfc(a.base)
    json.dump(sfc, open(os.path.join(CACHE, "_review_sfc_%s.json" % a.end), "w", encoding="utf-8"), ensure_ascii=False)
    # 传足冷热需要竞彩 SP：取覆盖近 issues 期的竞彩区间
    sfc_begin = min(dt.date.fromisoformat(r["lotteryDrawTime"]) for r in sfc[:a.issues]) - dt.timedelta(days=6)
    jbeg = min(begin, sfc_begin)
    jc_all = fetch_jc(jbeg.isoformat(), a.end)
    json.dump(jc_all, open(os.path.join(CACHE, "_review_jc_%s_%s.json" % (jbeg, a.end)), "w", encoding="utf-8"),
              ensure_ascii=False)
    idx = {m.get("matchId"): m for m in jc_all}
    jc = [m for m in jc_all if begin.isoformat() <= m["matchDate"] <= a.end]
    rep = {"window": {"jc": [begin.isoformat(), a.end], "sfc_issues": [sfc[a.issues - 1]["lotteryDrawNum"],
                                                                         sfc[0]["lotteryDrawNum"]],
                      "sfc_base": [sfc[-1]["lotteryDrawNum"], sfc[0]["lotteryDrawNum"]]},
           "sfc": analyze_sfc(sfc, a.issues, idx), "jc": analyze_jc(jc)}
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
