# -*- coding: utf-8 -*-
"""20261123 批次数据聚合：官方 webapi 近5场/交锋 + 维基/联网积分榜 + Open-Meteo 天气。"""
import json
from pathlib import Path

ROOT = Path(r"I:\阿飞说球")
DAY = "20261123"
INTEL = ROOT / "state" / "intel" / DAY
MATCHES = ROOT / "state" / "matches"

NAME_ALIAS = {
    "厄格里特": "Örgryte",
    "卡尔马": "Kalmar",
    "哈马比": "Hammarby",
    "哥德堡": "IFK Göteborg",
    "蒙扎": "蒙扎",
    "佛罗伦萨": "佛罗伦萨",
    "索肖": "Sochaux",
    "敦刻尔克": "Dunkerque",
    "布伦特": "布伦特福德",
    "埃弗顿": "埃弗顿",
    "莱万特": "莱万特",
    "埃尔切": "埃尔切",
    "博塔弗戈": "Botafogo",
    "圣保罗": "São Paulo",
}

# 联网核实补充：2026 MLS 西部常规赛最终积分榜（SportsGambler / AP News / MLS 官网）
EXTRA_SEASON = {
    "圣路易城": {
        "p": 34, "w": 15, "d": 9, "l": 10, "gf": 59, "ga": 48, "gd": 11, "pts": 54, "rank": 3,
        "source": "2026 MLS 西部常规赛积分榜（SportsGambler / AP News 联网核实）",
    },
    "洛杉矶FC": {
        "p": 34, "w": 12, "d": 11, "l": 11, "gf": 52, "ga": 40, "gd": 12, "pts": 47, "rank": 6,
        "source": "2026 MLS 西部常规赛积分榜（SportsGambler / AP News 联网核实）",
    },
}

# Open-Meteo 实测比赛时刻天气（2026-11-23/24 UTC 对应各球场坐标）
WEATHER_BY_NO = {
    "001": {"time": "2026-11-23 18:00 UTC (哥德堡·旧乌勒维)", "temp": 0.6, "rain": 0.0, "wind": 12.6},
    "002": {"time": "2026-11-23 18:00 UTC (斯德哥尔摩·3Arena)", "temp": 2.2, "rain": 0.1, "wind": 18.0},
    "003": {"time": "2026-11-23 20:00 UTC (蒙扎·U-Power)", "temp": 7.3, "rain": 0.0, "wind": 6.0},
    "004": {"time": "2026-11-23 20:00 UTC (蒙贝利亚尔·博纳尔)", "temp": 2.3, "rain": 0.2, "wind": 7.0},
    "005": {"time": "2026-11-23 20:00 UTC (伦敦·Gtech社区)", "temp": 4.1, "rain": 0.0, "wind": 8.6},
    "006": {"time": "2026-11-23 20:00 UTC (瓦伦西亚·城市球场)", "temp": 11.7, "rain": 0.0, "wind": 5.4},
    "007": {"time": "2026-11-23 23:00 UTC (里约·尼尔顿桑托斯)", "temp": 26.8, "rain": 0.0, "wind": 3.1},
    "008": {"time": "2026-11-24 01:00 UTC (圣路易斯·Energizer)", "temp": 1.0, "rain": 0.0, "wind": 15.9},
}


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def jdump(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def as_int(x, default=0):
    try:
        return int(str(x).replace("−", "-").replace("&#8722;", "-").strip())
    except (TypeError, ValueError):
        return default


def find_rank(lg_json, league, team):
    if team in EXTRA_SEASON:
        return dict(EXTRA_SEASON[team])
    alias = NAME_ALIAS.get(team, team)
    tbl = (lg_json.get("leagues") or {}).get(league) or {}
    rows = tbl.get("rows") or tbl.get("table") or []
    for r in rows:
        tname = str(r.get("team") or r.get("name") or "")
        if alias.lower() in tname.lower() or team.lower() in tname.lower():
            p = as_int(r.get("pld") or r.get("p"))
            gf = as_int(r.get("gf"))
            ga = as_int(r.get("ga"))
            if p >= 4:
                return {
                    "p": p,
                    "w": as_int(r.get("w")),
                    "d": as_int(r.get("d")),
                    "l": as_int(r.get("l")),
                    "gf": gf,
                    "ga": ga,
                    "gd": gf - ga,
                    "pts": as_int(r.get("pts")),
                    "rank": as_int(r.get("pos") or r.get("rank")),
                    "source": "维基积分榜（经 _leagues_ 缓存）",
                }
    return {}


def parse_recent(rows, team):
    out = []
    seen = set()
    split = {
        "home": {"p": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0},
        "away": {"p": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0},
    }
    for r in rows or []:
        h = str(r.get("homeTeamShortName") or "")
        a = str(r.get("awayTeamShortName") or "")
        d = str(r.get("matchDate") or "")
        key = (d, h, a)
        if key in seen:
            continue
        seen.add(key)
        s = str(r.get("fullCourtGoal") or "")
        if ":" not in s:
            continue
        try:
            x, y = [int(v) for v in s.split(":")[:2]]
        except ValueError:
            continue
        is_home = (h == team) or (team in h and team not in a)
        venue = "H" if is_home else "A"
        out.append({"home": h, "away": a, "venue": venue, "score": f"{x}-{y}", "date": d})
        gf, ga = (x, y) if is_home else (y, x)
        slot = split["home" if is_home else "away"]
        slot["p"] += 1
        slot["gf"] += gf
        slot["ga"] += ga
        if gf > ga:
            slot["w"] += 1
        elif gf == ga:
            slot["d"] += 1
        else:
            slot["l"] += 1
    for slot in split.values():
        slot["gd"] = slot["gf"] - slot["ga"]
        slot["pts"] = 3 * slot["w"] + slot["d"]
        slot["source"] = "竞彩官方 webapi 近 5 场逐场比分（非全季分项）"
    return out, split


def parse_h2h(rows, home_team):
    meetings = []
    seen = set()
    w = d = l = gf_tot = ga_tot = over = under = 0
    for r in rows or []:
        h = str(r.get("homeTeamShortName") or "")
        a = str(r.get("awayTeamShortName") or "")
        dt = str(r.get("matchDate") or "")
        s = str(r.get("fullCourtGoal") or "")
        lg = str(r.get("tournamentShortName") or r.get("leagueShortName") or "")
        key = (dt, h, a)
        if key in seen or ":" not in s:
            continue
        seen.add(key)
        try:
            x, y = [int(v) for v in s.split(":")[:2]]
        except ValueError:
            continue
        meetings.append({"d": dt, "m": f"{h} {s} {a}", "league": lg})
        is_home = (h == home_team) or (home_team in h and home_team not in a)
        gf, ga = (x, y) if is_home else (y, x)
        gf_tot += gf
        ga_tot += ga
        if gf > ga:
            w += 1
        elif gf == ga:
            d += 1
        else:
            l += 1
        if x + y >= 3:
            over += 1
        else:
            under += 1
    summary = None
    if meetings:
        summary = {
            "n": len(meetings),
            "text": f"{home_team} {w}胜{d}平{l}负、",
            "gf": gf_tot,
            "ga": ga_tot,
            "over": over,
            "under": under,
        }
    return meetings, summary


def main():
    intel = jload(INTEL / f"_intel_{DAY}.json")
    books = jload(INTEL / f"_books_{DAY}.json")
    lg_path = INTEL / f"_leagues_{DAY}.json"
    lg_json = jload(lg_path)

    # 写入 8 场 Open-Meteo 比赛时刻天气到 _leagues_20261123.json
    lg_matches = lg_json.setdefault("matches", {})
    for m in intel.get("matches") or []:
        no_full = m["no"]
        no = no_full[-3:]
        slot = lg_matches.setdefault(no_full, {})
        if no in WEATHER_BY_NO:
            slot["weather"] = WEATHER_BY_NO[no]
    jdump(lg_path, lg_json)

    data = {}
    for m in intel.get("matches") or []:
        no_full = m["no"]
        no = no_full[-3:]
        bid = (books.get(no) or {}).get("id") or str(m["matchId"])
        mid = str(m["matchId"])
        lg = m["league"]
        home = m["home"]
        away = m["away"]

        res_path = MATCHES / mid / "result.json"
        res = jload(res_path).get("value") or {} if res_path.exists() else {}
        hm_rows = (res.get("home") or {}).get("matchList") or []
        am_rows = (res.get("away") or {}).get("matchList") or []

        his_path = MATCHES / mid / "history.json"
        his = jload(his_path).get("value") or {} if his_path.exists() else {}
        h2h_rows = his.get("matchList") or []

        rec_h, split_h = parse_recent(hm_rows, home)
        rec_a, split_a = parse_recent(am_rows, away)
        meetings, h2h_summary = parse_h2h(h2h_rows, home)

        th = find_rank(lg_json, lg, home)
        ta = find_rank(lg_json, lg, away)

        sh, sa = {}, {}
        if th:
            sh["total"] = th
            sh["home"] = split_h["home"]
            sh["away"] = split_h["away"]
        if ta:
            sa["total"] = ta
            sa["home"] = split_a["home"]
            sa["away"] = split_a["away"]

        data[bid] = {
            "no": no_full,
            "league": lg,
            "home": home,
            "away": away,
            "source": "竞彩官方 webapi 近5场/交锋 + 维基/联网积分榜 + Open-Meteo 天气",
            "season_home": sh,
            "season_away": sa,
            "recent_home": {"matches": rec_h},
            "recent_away": {"matches": rec_a},
            "meetings": meetings,
            "h2h": {"summary": h2h_summary} if h2h_summary else {},
        }
        print(
            f"{no_full} {lg} {home} vs {away} | rank=({th.get('rank','-')},{ta.get('rank','-')}) | "
            f"rec=({len(rec_h)},{len(rec_a)}) | h2h={len(meetings)} | weather={WEATHER_BY_NO[no]['temp']}C"
        )

    out_path = INTEL / f"_data_{DAY}.json"
    jdump(out_path, data)
    print(f"Wrote {out_path} ({len(data)} matches)")


if __name__ == "__main__":
    main()
