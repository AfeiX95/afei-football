# -*- coding: utf-8 -*-
"""解析竞彩API JSON：列出所有场次，标注次日00:00-06:00凌晨场(归属今日销售期)。"""
import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else 'temp_jc_20260817.json'
with open(path, encoding='utf-8') as f:
    data = json.load(f)

value = data.get('value', {})
print("lastUpdateTime:", value.get('lastUpdateTime', 'N/A'))
match_info_list = value.get('matchInfoList', [])
print(f"营业日数量: {len(match_info_list)}")
print("=" * 110)

all_matches = []
for day in match_info_list:
    bd = day.get('businessDate', '')
    for sub in day.get('subMatchList', []):
        mt = sub.get('matchTime', '') or ''
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

all_matches.sort(key=lambda m: m['matchTime'])
if not all_matches:
    print("⚠️ API返回0场比赛")
    sys.exit(0)

bds = sorted(set(m['businessDate'] for m in all_matches))
print(f"营业日: {bds} | 总场次: {len(all_matches)}")
print("-" * 110)

early_morning = []   # 次日00:00-06:00，归属今日销售期
for m in all_matches:
    hm = m['matchTime'][11:16] if len(m['matchTime']) >= 16 else (m['matchTime'][:5] if len(m['matchTime']) >= 5 else '')
    md = m['matchDate']
    flag = ''
    if m['status'] != 'Selling':
        flag = f" [状态:{m['status']}]"
    if md and hm >= '00:00' and hm < '06:00':
        flag += ' 🌙凌晨场'
        early_morning.append(m)
    print(f"{m['matchNumStr']} | {m['matchTime']} | 比赛日:{md} | {m['leagueAllName']} | "
          f"{m['home']}({m['homeRank']}) vs {m['away']}({m['awayRank']}) | 单关:{m['single']}{flag}")

print("=" * 110)
if early_morning:
    print(f"\n✅ 检测到 {len(early_morning)} 场凌晨场(00:00-06:00, 归属今日销售期):")
    for m in early_morning:
        print(f"  - {m['matchNumStr']} {m['matchTime']} {m['leagueAllName']} {m['home']} vs {m['away']} 单关:{m['single']}")
else:
    print("\n❌ 无凌晨场(00:00-06:00)")

# 额外:列出所有matchDate=明天的场次
print("-" * 110)
tomorrow = sorted(set(m['matchDate'] for m in all_matches if m['matchDate']))
print(f"涉及比赛日: {tomorrow}")
