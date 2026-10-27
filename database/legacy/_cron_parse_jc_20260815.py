# -*- coding: utf-8 -*-
"""解析竞彩API快照：按营业日分组列出场次（队名/联赛/时间/状态）"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

d = json.load(open(r'I:\阿飞说球\temp_jc_20260815.json', encoding='utf-8'))
value = d.get('value', {})
mil = value.get('matchInfoList', [])
print('totalCount:', value.get('totalCount'), '| lastUpdateTime:', value.get('lastUpdateTime'))
print('=' * 100)
for group in mil:
    bd = group.get('businessDate')
    subs = group.get('subMatchList', [])
    print(f'\n### 营业日 {bd}（{group.get("weekday")}） 场次 {len(subs)}')
    for m in subs:
        print(f"  {m.get('matchNumStr')} {m.get('matchDate')} {m.get('matchTime')} "
              f"[{m.get('matchStatus')}] {m.get('homeTeamAllName')} vs {m.get('awayTeamAllName')} "
              f"({m.get('leagueAllName')}) 主{ (m.get('homeRank') or '') } 客{ (m.get('awayRank') or '') } "
              f"单关:{m.get('bettingSingle')}")
