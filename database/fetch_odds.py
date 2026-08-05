import json
from urllib.request import urlopen, Request

url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c'
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(urlopen(req, timeout=15).read())

targets = ['瓦勒伦加', '汉坎', '博德', '利勒斯特']

for day in data.get('value', {}).get('matchInfoList', []):
    for sub in day.get('subMatchList', []):
        ha = sub.get('homeTeamAbbName', '')
        aa = sub.get('awayTeamAbbName', '')
        if any(t in ha or t in aa for t in targets):
            mid = sub.get('matchNumStr', '')
            had = sub.get('had', {})
            hhad = sub.get('hhad', {})
            crs = sub.get('crs', {})
            ttg = sub.get('ttg', {})
            print(f'=== {mid} {ha} vs {aa} ===')
            print(f'had: {json.dumps(had, ensure_ascii=False)}')
            print(f'hhad: {json.dumps(hhad, ensure_ascii=False)}')
            if crs:
                crs_str = json.dumps(crs, ensure_ascii=False)
                if len(crs_str) > 500:
                    crs_str = crs_str[:500] + '...'
                print(f'crs: {crs_str}')
            if ttg:
                print(f'ttg: {json.dumps(ttg, ensure_ascii=False)}')
            print()
