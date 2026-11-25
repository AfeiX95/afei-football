# -*- coding: utf-8 -*-
"""20261126 批次数据聚合：官方 webapi 近5场/交锋 + 欧罗巴排名。"""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\阿飞说球")
DAY = "20261126"
INTEL = ROOT / "state" / "intel" / DAY
MATCHES = ROOT / "state" / "matches"

# 竞彩官方排名与联网核实欧罗巴前4轮积分（部分队补充）
EXTRA_SEASON = {
    "伯恩茅斯": {"p": 4, "w": 4, "d": 0, "l": 0, "gf": 10, "ga": 2, "gd": 8, "pts": 12, "rank": 2, "source": "欧罗巴4轮官方排名"},
    "本菲卡": {"p": 4, "w": 4, "d": 0, "l": 0, "gf": 11, "ga": 2, "gd": 9, "pts": 12, "rank": 1, "source": "欧罗巴4轮官方排名"},
    "桑德兰": {"p": 4, "w": 2, "d": 1, "l": 1, "gf": 6, "ga": 4, "gd": 2, "pts": 7, "rank": 11, "source": "欧罗巴4轮联网核实"},
    "比亚韦": {"p": 4, "w": 1, "d": 0, "l": 3, "gf": 4, "ga": 9, "gd": -5, "pts": 3, "rank": 29, "source": "欧罗巴4轮联网核实"},
    "水晶宫": {"p": 4, "w": 1, "d": 2, "l": 1, "gf": 5, "ga": 5, "gd": 0, "pts": 5, "rank": 21, "source": "欧罗巴4轮联网核实"},
    "皇家社会": {"p": 4, "w": 1, "d": 2, "l": 1, "gf": 5, "ga": 5, "gd": 0, "pts": 5, "rank": 20, "source": "欧罗巴4轮联网核实"},
    "霍芬海姆": {"p": 4, "w": 1, "d": 1, "l": 2, "gf": 5, "ga": 6, "gd": -1, "pts": 4, "rank": 23, "source": "欧罗巴4轮联网核实"},
    "格风暴": {"p": 4, "w": 1, "d": 1, "l": 2, "gf": 4, "ga": 6, "gd": -2, "pts": 4, "rank": 24, "source": "欧罗巴4轮联网核实"},
    "奈梅亨": {"p": 4, "w": 2, "d": 1, "l": 1, "gf": 7, "ga": 5, "gd": 2, "pts": 7, "rank": 12, "source": "欧罗巴4轮联网核实"},
    "雷恩": {"p": 4, "w": 1, "d": 3, "l": 0, "gf": 5, "ga": 4, "gd": 1, "pts": 6, "rank": 17, "source": "欧罗巴4轮联网核实"},
}

sys.path.insert(0, str(ROOT / "📝文章" / "20261123" / "_工具"))
import build_data_20261123 as b23  # noqa: E402


def main():
    intel = b23.jload(INTEL / f"_intel_{DAY}.json")
    books = b23.jload(INTEL / f"_books_{DAY}.json")
    lg_json = b23.jload(INTEL / f"_leagues_{DAY}.json")
    b23.EXTRA_SEASON.clear()
    b23.EXTRA_SEASON.update(EXTRA_SEASON)

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
        res = b23.jload(res_path).get("value") or {} if res_path.exists() else {}
        hm_rows = (res.get("home") or {}).get("matchList") or []
        am_rows = (res.get("away") or {}).get("matchList") or []

        his_path = MATCHES / mid / "history.json"
        his = b23.jload(his_path).get("value") or {} if his_path.exists() else {}
        h2h_rows = his.get("matchList") or []

        rec_h, split_h = b23.parse_recent(hm_rows, home)
        rec_a, split_a = b23.parse_recent(am_rows, away)
        meetings, h2h_summary = b23.parse_h2h(h2h_rows, home)

        th = b23.find_rank(lg_json, lg, home)
        ta = b23.find_rank(lg_json, lg, away)

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
            "source": "竞彩官方 webapi 近5场/交锋 + 欧罗巴4轮战绩",
            "season_home": sh,
            "season_away": sa,
            "recent_home": {"matches": rec_h},
            "recent_away": {"matches": rec_a},
            "meetings": meetings,
            "h2h": {"summary": h2h_summary} if h2h_summary else {},
        }
        print(f"{no_full} {lg} {home} vs {away} | rec=({len(rec_h)},{len(rec_a)}) | h2h={len(meetings)}")

    out_path = INTEL / f"_data_{DAY}.json"
    b23.jdump(out_path, data)
    print(f"Wrote {out_path} ({len(data)} matches)")


if __name__ == "__main__":
    main()
