# -*- coding: utf-8 -*-
"""20261127 批次数据聚合：官方 webapi 近5场/交锋 + 维基/联网积分榜。"""
import sys
from pathlib import Path

ROOT = Path(r"I:\阿飞说球")
DAY = "20261127"
INTEL = ROOT / "state" / "intel" / DAY
MATCHES = ROOT / "state" / "matches"

NAME_ALIAS = {
    "不来梅": "云达不来梅",
    "门兴": "门兴格拉德巴赫",
    "威尼斯": "威尼斯",
    "博洛尼亚": "博洛尼亚",
    "布雷斯特": "布雷斯特",
    "巴黎FC": "巴黎FC",
    "诺丁汉": "诺丁汉森林",
    "切尔西": "切尔西",
    "南安普敦": "南安普敦",
    "米堡": "米德尔斯堡",
    "莱万特": "莱万特",
    "桑坦德": "桑坦德竞技",
    "格罗宁根": "格罗宁根",
    "威廉二世": "威廉二世",
    "海登海姆": "海登海姆",
    "纽伦堡": "纽伦堡",
    "芬洛": "芬洛",
    "瓦尔韦克": "瓦尔韦克",
}

EXTRA_SEASON = {
    "麦克阿瑟": {"p": 5, "w": 2, "d": 2, "l": 1, "gf": 8, "ga": 7, "gd": 1, "pts": 8, "rank": 5, "source": "澳超前5轮联网核实"},
    "墨尔本城": {"p": 5, "w": 2, "d": 1, "l": 2, "gf": 8, "ga": 7, "gd": 1, "pts": 7, "rank": 7, "source": "澳超前5轮联网核实"},
}

sys.path.insert(0, str(ROOT / "📝文章" / "20261123" / "_工具"))
import build_data_20261123 as b23  # noqa: E402


def main():
    intel = b23.jload(INTEL / f"_intel_{DAY}.json")
    books = b23.jload(INTEL / f"_books_{DAY}.json")
    lg_json = b23.jload(INTEL / f"_leagues_{DAY}.json")
    b23.NAME_ALIAS.update(NAME_ALIAS)
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
            "source": "竞彩官方 webapi 近5场/交锋 + 维基/联网积分榜",
            "season_home": sh,
            "season_away": sa,
            "recent_home": {"matches": rec_h},
            "recent_away": {"matches": rec_a},
            "meetings": meetings,
            "h2h": {"summary": h2h_summary} if h2h_summary else {},
        }
        print(f"{no_full} {lg} {home} vs {away} | rank=({th.get('rank','-')},{ta.get('rank','-')}) | rec=({len(rec_h)},{len(rec_a)}) | h2h={len(meetings)}")

    out_path = INTEL / f"_data_{DAY}.json"
    b23.jdump(out_path, data)
    print(f"Wrote {out_path} ({len(data)} matches)")


if __name__ == "__main__":
    main()
