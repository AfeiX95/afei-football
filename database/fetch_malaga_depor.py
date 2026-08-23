# -*- coding: utf-8 -*-
"""拉取 周一010 马拉加 vs 拉科 竞彩特征分析数据 (2026-08-25 03:30)"""
import json, sys
from urllib.request import urlopen, Request
sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

def get(url):
    req = Request(url, headers={'User-Agent': UA})
    return json.loads(urlopen(req, timeout=15).read())

url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c'
data = get(url)

targets = ['马拉加', '拉科']
found = []
for day in data.get('value', {}).get('matchInfoList', []):
    for sub in day.get('subMatchList', []):
        ha = sub.get('homeTeamAbbName', '')
        aa = sub.get('awayTeamAbbName', '')
        if '马拉加' in ha or '拉科' in ha or '马拉加' in aa or '拉科' in aa:
            mid = sub.get('matchId', '')
            match_num = sub.get('matchNumStr', '')
            print(f'=== {match_num}: {ha} vs {aa} | matchId={mid} ===')
            found.append((match_num, ha, aa, mid))

for match_num, ha, aa, mid in found:
    if not mid:
        continue
    try:
        feature_url = f'https://webapi.sporttery.cn/gateway/uniform/football/getAnalysisV1.qry?channel=c&matchId={mid}'
        fdata = get(feature_url)
        value = fdata.get('value', {})
        out = {'match': f'{ha} vs {aa}', 'matchNum': match_num}
        mi = value.get('matchInfo', {})
        if mi:
            out['matchInfo'] = mi
        analysis = value.get('analysis', {})
        if analysis:
            out['analysis'] = analysis
        with open('database/fetch_malaga_depor_feature.json', 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        # 打印结构概览（不打印全部，避免过长）
        def walk(d, prefix='', depth=0):
            if depth > 3: return
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, (dict, list)):
                        print(f'{prefix}{k}: ({type(v).__name__}, {len(v)})')
                        walk(v, prefix + '  ', depth + 1)
                    else:
                        s = str(v)
                        if len(s) > 60: s = s[:60] + '...'
                        print(f'{prefix}{k}: {s}')
            elif isinstance(d, list) and d:
                print(f'{prefix}[0] 样例:')
                walk(d[0], prefix + '  ', depth + 1)
        walk(out)
    except Exception as e:
        print(f'Feature analysis error: {e}')
