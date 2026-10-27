# -*- coding: utf-8 -*-
"""Parse jingcai API JSON for today's matches (cron-safe, no -c flag)."""
import json, io, sys

path = sys.argv[1] if len(sys.argv) > 1 else '/i/阿飞说球/temp_jc_20260817.json'
with io.open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

value = data.get('value', {})
print("errorCode:", data.get('errorCode'), "| errorMessage:", data.get('errorMessage'))
print("totalCount:", value.get('totalCount'))
print("=" * 80)

for day in value.get('matchInfoList', []):
    biz = day.get('businessDate', '')
    print(f"\n### 营业日: {biz}  (matchCount={day.get('matchCount')})")
    for sub in day.get('subMatchList', []):
        status = sub.get('matchStatus', '')
        mid = sub.get('matchNumStr', '')
        league = sub.get('leagueAllName') or sub.get('leagueName') or ''
        home = sub.get('homeTeamAllName') or sub.get('homeTeamName') or ''
        away = sub.get('awayTeamAllName') or sub.get('awayTeamName') or ''
        mtime = sub.get('matchTime', '')
        mdate = sub.get('matchDate', '')
        had = sub.get('had') or {}
        h, d, a = had.get('h'), had.get('d'), had.get('a')
        odds = f"胜{h} 平{d} 负{a}" if h else "无SPF"
        print(f"[{mid}] {mdate} {mtime} | {league} | {home} vs {away} | {status} | {odds}")
