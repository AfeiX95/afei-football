# -*- coding: utf-8 -*-
"""解析竞彩API JSON，列出今日所有场次，标注早场(09:00-12:00)。"""
import json, sys, os

path = sys.argv[1] if len(sys.argv) > 1 else 'temp_jc_20260817.json'
with open(path, encoding='utf-8') as f:
    data = json.load(f)

match_info_list = data.get('value', {}).get('matchInfoList', [])
print(f"营业日数量: {len(match_info_list)}")
print("=" * 100)

all_matches = []
for day in match_info_list:
    bd = day.get('businessDate', '')
    for sub in day.get('subMatchList', []):
        mt = sub.get('matchTime', '')
        # matchTime 形如 "2026-08-17 10:00:00"
        hm = mt[11:16] if len(mt) >= 16 else mt
        all_matches.append({
            'businessDate': bd,
            'matchNumStr': sub.get('matchNumStr', ''),
            'leagueAllName': sub.get('leagueAllName', ''),
            'home': sub.get('homeTeamAllName', '') or sub.get('homeTeamName', ''),
            'away': sub.get('awayTeamAllName', '') or sub.get('awayTeamName', ''),
            'homeRank': sub.get('homeRank', ''),
            'awayRank': sub.get('awayRank', ''),
            'matchTime': mt,
            'matchDate': sub.get('matchDate', ''),
            'status': sub.get('matchStatus', ''),
            'single': sub.get('single', ''),
        })

# 按时间排序
all_matches.sort(key=lambda m: m['matchTime'])
if not all_matches:
    print("⚠️ API返回0场比赛")
    sys.exit(0)

print(f"今日(营业日 {all_matches[0]['businessDate']})共 {len(all_matches)} 场：")
print("-" * 100)
early = []
for m in all_matches:
    hm = m['matchTime'][11:16] if len(m['matchTime']) >= 16 else ''
    flag = ''
    if m['status'] != 'Selling':
        flag = f" [状态:{m['status']}]"
    if hm >= '09:00' and hm < '12:00':
        flag += ' ⚡早场'
        early.append(m)
    print(f"{m['matchNumStr']} | {m['matchTime']} | {m['leagueAllName']} | "
          f"{m['home']}({m['homeRank']}) vs {m['away']}({m['awayRank']}) | 单关:{m['single']}{flag}")

print("=" * 100)
if early:
    print(f"\n✅ 检测到 {len(early)} 场北京时间09:00-12:00早场:")
    for m in early:
        print(f"  - {m['matchNumStr']} {m['matchTime']} {m['leagueAllName']} {m['home']} vs {m['away']}")
else:
    print("\n❌ 今日无09:00-12:00早场")
