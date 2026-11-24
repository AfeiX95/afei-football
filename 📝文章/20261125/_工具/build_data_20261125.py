# -*- coding: utf-8 -*-
"""20261125 批次数据聚合：官方 webapi 近5场/交锋 + 维基/联网积分榜。"""
import json, sys
from pathlib import Path

ROOT = Path(r"I:\阿飞说球")
DAY = "20261125"
INTEL = ROOT / "state" / "intel" / DAY
MATCHES = ROOT / "state" / "matches"

NAME_ALIAS = {
    "萨巴赫": "萨巴赫",
    "巴萨": "巴塞罗那",
    "斯拉维亚": "布拉格斯拉维亚",
    "比利亚雷": "比利亚雷亚尔",
    "里斯本": "葡萄牙体育",
    "曼联": "曼联",
    "国际米兰": "国际米兰",
    "斯图加特": "斯图加特",
    "布鲁日": "布鲁日",
    "利物浦": "利物浦",
    "马竞": "马德里竞技",
    "维京": "维京",
    "巴黎圣曼": "巴黎圣日耳曼",
    "罗马": "罗马",
    "里尔": "里尔",
    "拜仁": "拜仁慕尼黑",
}

EXTRA_SEASON = {
    "鹿岛鹿角": {
        "p": 4, "w": 3, "d": 1, "l": 0, "gf": 11, "ga": 1, "gd": 10, "pts": 10, "rank": 2,
        "source": "2026/27 亚冠精英东亚区前4轮战绩（freetips / AFC 联网核实）",
    },
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
            "source": "竞彩官方 webapi 近5场/交锋 + 维基/联网积分榜 + Open-Meteo 天气",
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
