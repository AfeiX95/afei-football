# -*- coding: utf-8 -*-
"""通用官方数据兜底聚合器（当 500.com 被拦、fenxi_500 未产出 _data_<date>.json 时使用）。

用法：
    python -X utf8 scripts/build_data_from_official.py YYYYMMDD

数据源：
    state/intel/<date>/_intel_<date>.json
    state/intel/<date>/_books_<date>.json
    state/intel/<date>/_leagues_<date>.json
    state/matches/<matchId>/{result,history}.json
    state/intel/<date>/_extra_season_<date>.json（可选：手工/联网补充的赛季积分行，键为队名）
输出：
    state/intel/<date>/_data_<date>.json
"""
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATCHES = ROOT / "state" / "matches"

DEFAULT_ALIAS = {
    "不来梅": "云达不来梅", "门兴": "门兴格拉德巴赫", "诺丁汉": "诺丁汉森林",
    "米堡": "米德尔斯堡", "桑坦德": "桑坦德竞技", "里斯本": "葡萄牙体育",
    "巴黎圣曼": "巴黎圣日耳曼", "拜仁": "拜仁慕尼黑", "巴萨": "巴塞罗那",
    "马竞": "马德里竞技", "比利亚雷": "比利亚雷亚尔", "斯拉维亚": "布拉格斯拉维亚",
    "布伦特": "布伦特福德", "莱红牛": "RB莱比锡", "萨迪纳摩": "萨格勒布迪纳摩",
}


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def as_int(x, default=0):
    try:
        return int(str(x).replace("−", "-").replace("&#8722;", "-").strip())
    except (TypeError, ValueError):
        return default


def find_rank(lg_json, league, team, extra_season):
    if team in extra_season:
        return dict(extra_season[team])
    alias = DEFAULT_ALIAS.get(team, team)
    tbl = (lg_json.get("leagues") or {}).get(league) or {}
    rows = tbl.get("rows") or tbl.get("table") or []
    for r in rows:
        tname = str(r.get("team") or r.get("name") or "")
        if alias.lower() in tname.lower() or team.lower() in tname.lower():
            p = as_int(r.get("pld") or r.get("p"))
            gf, ga = as_int(r.get("gf")), as_int(r.get("ga"))
            if p >= 4:
                return {
                    "p": p, "w": as_int(r.get("w")), "d": as_int(r.get("d")), "l": as_int(r.get("l")),
                    "gf": gf, "ga": ga, "gd": gf - ga, "pts": as_int(r.get("pts")),
                    "rank": as_int(r.get("pos") or r.get("rank")),
                    "source": "维基积分榜（经 _leagues_ 缓存）",
                }
    return {}


def parse_recent(rows, team):
    out, seen = [], set()
    split = {"home": {"p": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0},
             "away": {"p": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0}}
    for r in rows or []:
        h, a = str(r.get("homeTeamShortName") or ""), str(r.get("awayTeamShortName") or "")
        d, s = str(r.get("matchDate") or ""), str(r.get("fullCourtGoal") or "")
        if (d, h, a) in seen or ":" not in s:
            continue
        seen.add((d, h, a))
        try:
            x, y = [int(v) for v in s.split(":")[:2]]
        except ValueError:
            continue
        is_home = (h == team) or (team in h and team not in a)
        out.append({"home": h, "away": a, "venue": "H" if is_home else "A", "score": f"{x}-{y}", "date": d})
        gf, ga = (x, y) if is_home else (y, x)
        slot = split["home" if is_home else "away"]
        slot["p"] += 1; slot["gf"] += gf; slot["ga"] += ga
        slot["w" if gf > ga else "d" if gf == ga else "l"] += 1
    for slot in split.values():
        slot["gd"] = slot["gf"] - slot["ga"]
        slot["pts"] = 3 * slot["w"] + slot["d"]
        slot["source"] = "竞彩官方 webapi 近 5 场逐场比分（非全季分项）"
    return out, split


def parse_h2h(rows, home_team):
    meetings, seen = [], set()
    w = d = l = gf_tot = ga_tot = over = under = 0
    for r in rows or []:
        h, a = str(r.get("homeTeamShortName") or ""), str(r.get("awayTeamShortName") or "")
        dt, s = str(r.get("matchDate") or ""), str(r.get("fullCourtGoal") or "")
        lg = str(r.get("tournamentShortName") or r.get("leagueShortName") or "")
        if (dt, h, a) in seen or ":" not in s:
            continue
        seen.add((dt, h, a))
        try:
            x, y = [int(v) for v in s.split(":")[:2]]
        except ValueError:
            continue
        meetings.append({"d": dt, "m": f"{h} {s} {a}", "league": lg})
        is_home = (h == home_team) or (home_team in h and home_team not in a)
        gf, ga = (x, y) if is_home else (y, x)
        gf_tot += gf; ga_tot += ga
        if gf > ga: w += 1
        elif gf == ga: d += 1
        else: l += 1
        if x + y >= 3: over += 1
        else: under += 1
    summary = {"n": len(meetings), "text": f"{home_team} {w}胜{d}平{l}负、",
               "gf": gf_tot, "ga": ga_tot, "over": over, "under": under} if meetings else None
    return meetings, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("day", help="YYYYMMDD")
    day = ap.parse_args().day
    intel_dir = ROOT / "state" / "intel" / day
    intel = jload(intel_dir / f"_intel_{day}.json")
    books = jload(intel_dir / f"_books_{day}.json")
    lg_json = jload(intel_dir / f"_leagues_{day}.json")
    extra_season = jload(intel_dir / f"_extra_season_{day}.json")

    data = {}
    for m in intel.get("matches") or []:
        no_full = m["no"]
        no = no_full[-3:]
        bid = (books.get(no) or {}).get("id") or str(m["matchId"])
        mid = str(m["matchId"])
        lg, home, away = m["league"], m["home"], m["away"]
        res = jload(MATCHES / mid / "result.json").get("value") or {}
        his = jload(MATCHES / mid / "history.json").get("value") or {}
        rec_h, split_h = parse_recent((res.get("home") or {}).get("matchList"), home)
        rec_a, split_a = parse_recent((res.get("away") or {}).get("matchList"), away)
        meetings, h2h_summary = parse_h2h(his.get("matchList"), home)
        th, ta = find_rank(lg_json, lg, home, extra_season), find_rank(lg_json, lg, away, extra_season)
        sh = {"total": th, "home": split_h["home"], "away": split_h["away"]} if th else {}
        sa = {"total": ta, "home": split_a["home"], "away": split_a["away"]} if ta else {}
        data[bid] = {
            "no": no_full, "league": lg, "home": home, "away": away,
            "source": "竞彩官方 webapi 近5场/交锋 + 维基/联网积分榜",
            "season_home": sh, "season_away": sa,
            "recent_home": {"matches": rec_h}, "recent_away": {"matches": rec_a},
            "meetings": meetings, "h2h": {"summary": h2h_summary} if h2h_summary else {},
        }
        print(f"{no_full} {lg} {home} vs {away} | rank=({th.get('rank','-')},{ta.get('rank','-')}) | rec=({len(rec_h)},{len(rec_a)}) | h2h={len(meetings)}")

    out_path = intel_dir / f"_data_{day}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} ({len(data)} matches)")


if __name__ == "__main__":
    main()
