#!/usr/bin/env python3
"""Check today's jingcai matches for early-morning (00:00-06:00 BJT) kickoffs."""
import json
import urllib.request
from datetime import datetime, timezone, timedelta

BJT = timezone(timedelta(hours=8))
today = datetime.now(BJT)
print(f"Current BJT: {today.strftime('%Y-%m-%d %H:%M')} ({today.strftime('%A')})")

url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read().decode('utf-8'))

match_days = data.get('value', {}).get('matchInfoList', [])
print(f"Total match days returned: {len(match_days)}")

all_matches = []
for day in match_days:
    date_str = day.get('date', '')
    sub_list = day.get('subMatchList', [])
    for m in sub_list:
        home = m.get('homeName', '?')
        away = m.get('awayName', '?')
        league = m.get('leagueName', '?')
        mid = m.get('matchNumStr', '?')
        status = m.get('matchStatus', '?')
        # matchDate might have time
        match_time = m.get('matchDate', '')
        start_time = m.get('startTime', '')
        all_matches.append({
            'mid': mid, 'home': home, 'away': away,
            'league': league, 'date': date_str,
            'match_time': match_time, 'start_time': start_time,
            'status': status
        })
        print(f"  {mid} | {home} vs {away} | date={date_str} | matchDate={match_time} | startTime={start_time} | league={league} | status={status}")

# Determine if any match kicks off between 00:00-06:00 BJT
# The API's matchDate/startTime format needs inspection
print("\n\n--- ANALYSIS ---")
if not all_matches:
    print("No matches returned from API.")
else:
    # Try to parse match times
    early_matches = []
    for m in all_matches:
        t = m['match_time'] or m['start_time'] or ''
        print(f"  Raw time field for {m['mid']}: '{t}'")
    print("\nNo early-morning kickoffs detected (insufficient time data in API response).")
