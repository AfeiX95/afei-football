#!/usr/bin/env python3
"""Get all matches with detailed info."""
import json
import urllib.request
from datetime import datetime, timezone, timedelta

BJT = timezone(timedelta(hours=8))
now = datetime.now(BJT)
print(f"当前北京时间: {now.strftime('%Y-%m-%d %H:%M')} ({now.strftime('%A')})")
weekday = now.weekday()  # Mon=0, Sun=6
is_weekend = weekday >= 4  # Fri=4, Sat=5, Sun=6
cutoff_hour = 23 if is_weekend else 22
print(f"今天是{'周末' if is_weekend else '工作日'}，封盘时间: {cutoff_hour}:00")
print(f"距离封盘: {'已过封盘 ' + str(now.hour - cutoff_hour) + '小时' if now.hour >= cutoff_hour else '还有 ' + str(cutoff_hour - now.hour) + '小时'}")

url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=15)
data = json.loads(resp.read().decode('utf-8'))

match_days = data.get('value', {}).get('matchInfoList', [])
print(f"\nAPI返回了 {len(match_days)} 个比赛日")

all_matches = []
for day in match_days:
    bdate = day.get('businessDate', '?')
    weekday_str = day.get('weekday', '?')
    subs = day.get('subMatchList', [])
    print(f"\n=== 销售日: {bdate} ({weekday_str}) — {len(subs)} 场 ===")
    for m in subs:
        mid = m.get('matchNumStr', '?')
        home = m.get('homeTeamAllName', m.get('homeTeamAbbName', '?'))
        away = m.get('awayTeamAllName', m.get('awayTeamAbbName', '?'))
        league = m.get('leagueAbbName', '?')
        match_date = m.get('matchDate', '?')
        match_time = m.get('matchTime', '?')
        status = m.get('matchStatus', '?')
        
        # Parse kickoff time
        kickoff_str = f"{match_date} {match_time}"
        
        # Check if in early morning window (00:00-06:00)
        is_early = False
        if match_time:
            hour = int(match_time.split(':')[0])
            if 0 <= hour <= 6:
                is_early = True
        
        all_matches.append({
            'mid': mid, 'home': home, 'away': away, 'league': league,
            'bdate': bdate, 'match_date': match_date, 'match_time': match_time,
            'status': status, 'is_early': is_early
        })
        
        flag = ' ⏰ 凌晨场!' if is_early else ''
        print(f"  {mid} | {home} vs {away} | {match_date} {match_time} | {league} | {status}{flag}")

print(f"\n\n{'='*60}")
print("结论分析")
print(f"{'='*60}")

early_matches = [m for m in all_matches if m['is_early']]
if early_matches:
    print(f"\n✅ 发现 {len(early_matches)} 场凌晨场比赛！")
    print(f"⚠️ 当前时间: {now.strftime('%H:%M')}，{'已过封盘时间！' if now.hour >= cutoff_hour else f'距封盘还有 {cutoff_hour - now.hour} 小时'}")
    for m in early_matches:
        print(f"  • {m['mid']} {m['home']} vs {m['away']} 开赛 {m['match_date']} {m['match_time']}")
else:
    # Check if any matches are selling today at all
    selling_matches = [m for m in all_matches if m['status'] == 'Selling']
    if selling_matches:
        print(f"\n❌ 今日无凌晨场（00:00-06:00开赛）比赛")
        print(f"   有 {len(selling_matches)} 场在售比赛（最早开赛时间需进一步确认）")
    else:
        print(f"\n❌ 今日无在售比赛")
