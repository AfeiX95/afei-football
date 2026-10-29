# -*- coding: utf-8 -*-
"""数据审计模块（L1 层，有否决权）

职责：
1. 从**逐场原始记录**重算近 N 场胜平负 / 进球 / 失球，禁止用自然语言汇总；
2. 校验逐场与汇总是否一致（主客场归属用队名判定，不用 venue 字段猜）；
3. 校验赛季行是否自洽（w+d+l == p、gf-ga == gd）；
4. 检测重复场次；
5. 给出数据质量等级：A / B / C / DATA_INVALID，并据此决定后续能否给高置信度结论。

用法：
    python -X utf8 scripts/audit_data.py 20261027
产出：
    state/intel/<day>/_audit_<day>.json   机器可读
    state/intel/<day>/_audit_<day>.md     给人看（含与上一版报告「近 5 场场均」的差异）
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import _names  # noqa: E402  队名归一与别名词典（database/config/team_aliases.json）
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_score(s):
    try:
        a, b = [int(x) for x in str(s).split("-")]
        return a, b
    except Exception:
        return None


def outcome(gf, ga):
    if gf > ga:
        return "W"
    if gf == ga:
        return "D"
    return "L"


def norm_name(s):
    return re.sub(r"[\s\u00b7\.]", "", str(s or ""))


def same_team(a, b):
    return _names.name_hit(a, b)


def team_rows(matches, team):
    """把逐场记录折算成该队视角的 (gf, ga, result, date)，用队名判定主客。"""
    out = []
    for m in matches:
        sc = parse_score(m.get("score"))
        if not sc:
            continue
        h, a = m.get("home", ""), m.get("away", "")
        if same_team(team, h):
            gf, ga = sc
        elif same_team(team, a):
            gf, ga = sc[1], sc[0]
        else:
            # 队名都不是本队：记录一条无法归属
            out.append({"date": m.get("date"), "unmatched": True,
                        "home": h, "away": a, "score": m.get("score")})
            continue
        out.append({"date": m.get("date"), "gf": gf, "ga": ga, "result": outcome(gf, ga),
                    "venue_flag": m.get("venue"), "home": h, "away": a})
    out.sort(key=lambda r: (r.get("date") or ""), reverse=True)
    return out


def dedupe(rows):
    """同一场重复出现时只留一条，并返回重复清单"""
    seen, keep, dups = set(), [], []
    for r in rows:
        if r.get("unmatched"):
            keep.append(r)
            continue
        key = (r.get("date"), r.get("home"), r.get("away"), r["gf"], r["ga"])
        if key in seen:
            dups.append(f"{r.get('date')} {r.get('home')} vs {r.get('away')} {r['gf']}-{r['ga']}")
            continue
        seen.add(key)
        keep.append(r)
    return keep, dups


def audit_season(season):
    """赛季行自洽性检查"""
    errs = []
    for part in ("total", "home", "away"):
        d = season.get(part)
        if not d or not d.get("p"):
            continue
        if d["w"] + d["d"] + d["l"] != d["p"]:
            errs.append(f"{part}: w+d+l={d['w']+d['d']+d['l']} != p={d['p']}")
        if d["gf"] - d["ga"] != d["gd"]:
            errs.append(f"{part}: gf-ga={d['gf']-d['ga']} != gd={d['gd']}")
    return errs


def aggregate(rows, n=None):
    ok = [r for r in rows if not r.get("unmatched")]
    if n:
        ok = ok[:n]
    if not ok:
        return None
    gf = sum(r["gf"] for r in ok)
    ga = sum(r["ga"] for r in ok)
    w = sum(1 for r in ok if r["result"] == "W")
    d = sum(1 for r in ok if r["result"] == "D")
    l = sum(1 for r in ok if r["result"] == "L")
    return {"n": len(ok), "gf": gf, "ga": ga, "w": w, "d": d, "l": l,
            "gf_pg": round(gf / len(ok), 2), "ga_pg": round(ga / len(ok), 2)}


def dup_check(matches):
    keys = Counter()
    for m in matches:
        sc = parse_score(m.get("score"))
        if not sc:
            continue
        keys[(m.get("date"), frozenset((m.get("home"), m.get("away"))), sc)] += 1
    return [f"{k[0]} {sorted(k[1])} {k[2][0]}-{k[2][1]}" for k, v in keys.items() if v > 1]


def report_recent5(md_text, num, side):
    """从现有报告里抓「近 5 场场均进/失」数值，做新旧对照"""
    pat = rf"### {num} .*?(?=### |\Z)"
    blk = re.search(pat, md_text, re.S)
    if not blk:
        return None
    m = re.search(r"近 (\d+) 场场均进/失：主 ([\d.]+)/([\d.]+)；客 ([\d.]+)/([\d.]+)", blk.group(0))
    if not m:
        return None
    if side == "home":
        return float(m.group(2)), float(m.group(3)), int(m.group(1))
    return float(m.group(4)), float(m.group(5)), int(m.group(1))


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else "20261027"
    ddir = ROOT / "state" / "intel" / day
    data = json.load(open(ddir / f"_data_{day}.json", encoding="utf-8"))
    books = json.load(open(ddir / f"_books_{day}.json", encoding="utf-8"))
    rep = ROOT / "📝文章" / day / f"{day}_周二10场_内部分析报告.md"
    md_text = rep.read_text(encoding="utf-8") if rep.exists() else ""
    by_id, by_num = {}, books

    result = {}
    for num, b in by_num.items():
        row = data.get(b["id"])
        if not row:
            continue
        home, away = row["home"], row["away"]
        rh_raw = team_rows((row.get("recent_home") or {}).get("matches", []), home)
        ra_raw = team_rows((row.get("recent_away") or {}).get("matches", []), away)
        rh, dup_h = dedupe(rh_raw)
        ra, dup_a = dedupe(ra_raw)
        agg_h5, agg_a5 = aggregate(rh, 5), aggregate(ra, 5)
        agg_h10, agg_a10 = aggregate(rh, 10), aggregate(ra, 10)
        errs = []
        warns = []
        errs += [f"home season: {e}" for e in audit_season(row.get("season_home") or {})]
        errs += [f"away season: {e}" for e in audit_season(row.get("season_away") or {})]
        unmatched = [r for r in rh + ra if r.get("unmatched")]
        if unmatched:
            errs.append(f"{len(unmatched)} 场逐场记录无法归属到本队（队名不匹配）")
        dups = dup_h + dup_a
        if dups:
            warns.append(f"重复场次已去重: {dups}")
        # 场地归属核对：venue=H 时本队应为主队
        venue_err = []
        for team, rows in ((home, rh), (away, ra)):
            for r in rows:
                if r.get("unmatched"):
                    continue
                want_home = r["venue_flag"] == "H"
                is_home = same_team(r["home"], team)
                if r["venue_flag"] in ("H", "A") and want_home != is_home:
                    venue_err.append(f"{r['date']} {team} venue={r['venue_flag']}")
        if venue_err:
            errs.append(f"venue 与主客场不一致: {venue_err[:3]}")

        old_h = report_recent5(md_text, num, "home")
        old_a = report_recent5(md_text, num, "away")
        diffs = []
        if old_h and agg_h5:
            if (round(old_h[0], 2), round(old_h[1], 2)) != (agg_h5["gf_pg"], agg_h5["ga_pg"]):
                diffs.append(f"主 报告 {old_h[0]:.2f}/{old_h[1]:.2f} → 审计 {agg_h5['gf_pg']:.2f}/{agg_h5['ga_pg']:.2f}")
        if old_a and agg_a5:
            if (round(old_a[0], 2), round(old_a[1], 2)) != (agg_a5["gf_pg"], agg_a5["ga_pg"]):
                diffs.append(f"客 报告 {old_a[0]:.2f}/{old_a[1]:.2f} → 审计 {agg_a5['gf_pg']:.2f}/{agg_a5['ga_pg']:.2f}")

        if errs:
            grade = "DATA_INVALID"
        elif warns:
            grade = "B"
        elif agg_h5 and agg_a5 and agg_h5["n"] >= 5 and agg_a5["n"] >= 5:
            grade = "A"
        elif agg_h5 and agg_a5:
            grade = "B"
        elif agg_h5 or agg_a5:
            grade = "C"
        else:
            grade = "DATA_INVALID"

        result[num] = {
            "id": b["id"], "match": f"{home} vs {away}",
            "grade": grade, "errors": errs, "warnings": warns, "diffs": diffs,
            "recent_home": {"n5": agg_h5, "n10": agg_h10},
            "recent_away": {"n5": agg_a5, "n10": agg_a10},
            "season_home_total": (row.get("season_home") or {}).get("total"),
            "season_away_total": (row.get("season_away") or {}).get("total"),
        }

    (ddir / f"_audit_{day}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1),
                                             encoding="utf-8")
    lines = [f"# 数据审计 {day}", "",
             "口径：近 N 场一律由逐场比分重算（主客归属按队名判定）；赛季行只做自洽校验。", "",
             "| 场次 | 对阵 | 等级 | 逐场重算（近5，进/失）主 | 客 | 与旧报告差异 | 警告 | 错误 |",
             "|---|---|---|---|---|---|---|---|"]
    for num in sorted(result):
        r = result[num]
        h5, a5 = r["recent_home"]["n5"], r["recent_away"]["n5"]
        h_s = f"{h5['gf_pg']:.2f}/{h5['ga_pg']:.2f}" if h5 else "缺"
        a_s = f"{a5['gf_pg']:.2f}/{a5['ga_pg']:.2f}" if a5 else "缺"
        lines.append(f"| {num} | {r['match']} | {r['grade']} | {h_s} | {a_s} | "
                     f"{'；'.join(r['diffs']) or '—'} | {'；'.join(r['warnings']) or '—'} | "
                     f"{'；'.join(r['errors']) or '—'} |")
    (ddir / f"_audit_{day}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    bad = [n for n in result if result[n]["grade"] == "DATA_INVALID"]
    diffn = [n for n in result if result[n]["diffs"]]
    print(f"审计完成：{len(result)} 场；DATA_INVALID {len(bad)} 场 {bad}；与旧报告不一致 {len(diffn)} 场 {diffn}")
    print(f"→ {ddir / f'_audit_{day}.md'}")


if __name__ == "__main__":
    main()
