# -*- coding: utf-8 -*-
"""07:30早场前瞻窗口 - 解析竞彩网API，列出今日所有场次，标记09:00-12:00早场"""
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PATH = r'I:\阿飞说球\temp_jc_20260823.json'

with open(PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

info_list = data.get('value', {}).get('matchInfoList', [])
if not info_list:
    print("❌ API返回空 matchInfoList — 今日无竞彩场次或数据异常")
    sys.exit(0)

all_matches = []
for day in info_list:
    biz_date = day.get('businessDate', '')
    for sub in day.get('subMatchList', []):
        m = {
            'num': sub.get('matchNumStr', ''),
            'league': sub.get('leagueAllName') or sub.get('leagueName') or '',
            'home': sub.get('homeTeamAllName') or sub.get('homeTeamName') or '',
            'away': sub.get('awayTeamAllName') or sub.get('awayTeamName') or '',
            'matchDate': sub.get('matchDate', ''),
            'matchTime': sub.get('matchTime', ''),
            'status': sub.get('matchStatus', ''),
            'bizDate': biz_date,
        }
        # matchTime 可能是 "HH:MM:SS" 或 "YYYY-MM-DD HH:MM:SS"
        t = str(m['matchTime'])
        if len(t) == 8:  # 纯时间
            m['time_str'] = f"{m['matchDate']} {t}"
            m['hhmm'] = t[:5]
        else:
            m['time_str'] = t
            m['hhmm'] = t[11:16] if len(t) >= 16 else t
        all_matches.append(m)

# 去重排序
seen = set()
unique = []
for m in all_matches:
    key = (m['num'], m['home'], m['away'], m['time_str'])
    if key in seen:
        continue
    seen.add(key)
    unique.append(m)

unique.sort(key=lambda x: (x['time_str'], x['num']))

print(f"=== 今日竞彩场次总览（{len(unique)}场）===")
early = []
for m in unique:
    hhmm = m['hhmm']
    is_early = '09:00' <= hhmm < '12:00'
    flag = ' ⭐早场' if is_early else ''
    if is_early:
        early.append(m)
    print(f"[{m['num']}] {m['league']} | {m['home']} vs {m['away']} | 开赛{m['time_str']} | 状态:{m['status']}{flag}")

print()
print(f"=== 早场比赛（09:00-12:00开赛）：{len(early)}场 ===")
for m in early:
    print(f"[{m['num']}] {m['league']} | {m['home']} vs {m['away']} | {m['time_str']}")

# 输出营业日信息
biz_dates = sorted(set(m['bizDate'] for m in unique))
print(f"\n营业日: {biz_dates}")
