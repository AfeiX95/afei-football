# -*- coding: utf-8 -*-
"""解析竞彩API JSON（新版matchInfoList结构）"""
import json, sys, datetime

with open(sys.argv[1], encoding='utf-8') as f:
    d = json.load(f)

v = d.get('value', {})
print('lastUpdateTime:', v.get('lastUpdateTime'))
print('totalCount:', v.get('totalCount'))
now = datetime.datetime.now()
print('now:', now.strftime('%Y-%m-%d %H:%M:%S'))
print('---')

def walk(matches, depth=0):
    for m in matches:
        md = m.get('matchDate', '')
        mt = m.get('matchTime', '')
        status = m.get('matchStatus', '')
        league = m.get('leagueAllName') or m.get('leagueName') or '?'
        home = m.get('homeTeamAllName') or m.get('homeTeamName') or '?'
        away = m.get('awayTeamAllName') or m.get('awayTeamName') or '?'
        hs = m.get('homeTeamScore', '')
        as_ = m.get('awayTeamScore', '')
        mnum = m.get('matchNumStr', m.get('matchNum', ''))
        sub = m.get('subMatchList')
        prefix = '  ' * depth
        line = f"{prefix}[{mnum}] {md} {mt} | {league} | {home} vs {away} | status={status} | score={hs}-{as_}"
        print(line)
        if isinstance(sub, list) and sub:
            walk(sub, depth+1)

mil = v.get('matchInfoList', [])
for group in mil:
    if isinstance(group, dict) and 'subMatchList' in group:
        print(f"== 分组: {group.get('businessDate', '?')} ==")
        walk(group.get('subMatchList', []))
    elif isinstance(group, list):
        walk(group)
    else:
        print('group:', json.dumps(group, ensure_ascii=False)[:500])
