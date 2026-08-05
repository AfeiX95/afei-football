# -*- coding: utf-8 -*-
"""
竞彩网数据抓取器
从 webapi.sporttery.cn 获取当日竞彩赛程+赔率
"""
import requests
import json
import sys
from datetime import datetime

API_URL = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry"

def fetch_matches(date_str=None):
    params = {"channel": "c"}
    if date_str:
        params["date"] = date_str
    try:
        resp = requests.get(API_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        print(f"[ERROR] Fetch failed: {e}")
        return None

def parse_matches(raw_data):
    results = []
    try:
        matches = raw_data.get("value", {}).get("matchInfoList", [])
        for m in matches:
            match = {
                "match_id": m.get("matchId"),
                "match_index": m.get("matchIndex"),
                "league": m.get("leagueName"),
                "home_team": m.get("homeTeamName"),
                "away_team": m.get("awayTeamName"),
                "kickoff": m.get("matchTime"),
                "status": m.get("matchStatus"),
                "odds": {
                    "home": m.get("oddsData", {}).get("homeWin"),
                    "draw": m.get("oddsData", {}).get("draw"),
                    "away": m.get("oddsData", {}).get("awayWin"),
                },
                "handicap": m.get("handicapData"),
            }
            results.append(match)
    except Exception as e:
        print(f"[ERROR] Parse failed: {e}")
    return results

def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"[INFO] Fetching matches for {date_str or 'today'}...")
    raw = fetch_matches(date_str)
    if not raw:
        print("[ERROR] No data returned")
        return
    matches = parse_matches(raw)
    print(f"[INFO] Found {len(matches)} matches")
    for m in matches:
        print(f"  {m['match_index']} {m['league']} {m['home_team']} vs {m['away_team']} "
              f"({m['odds']['home']}/{m['odds']['draw']}/{m['odds']['away']})")
    output_path = f"I:/阿飞说球/database/cache/jingcai_{date_str or 'today'}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Saved to {output_path}")

if __name__ == "__main__":
    main()
