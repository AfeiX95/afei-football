import json, sys
from urllib.request import urlopen, Request
sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

# Get detailed odds
url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c'
req = Request(url, headers={'User-Agent': UA})
data = json.loads(urlopen(req, timeout=15).read())

targets = ['瓦勒伦加', '汉坎', '博德', '利勒斯特']

for day in data.get('value', {}).get('matchInfoList', []):
    for sub in day.get('subMatchList', []):
        ha = sub.get('homeTeamAbbName', '')
        aa = sub.get('awayTeamAbbName', '')
        if any(t in ha or t in aa for t in targets):
            mid = sub.get('matchId', '')
            match_num = sub.get('matchNumStr', '')
            print(f'\n{"="*50}')
            print(f'{match_num}: {ha} vs {aa}')
            print(f'{"="*50}')
            
            # Print all available data
            for key in sorted(sub.keys()):
                val = sub[key]
                if val and key not in ['subMatchList', 'matchId']:
                    s = json.dumps(val, ensure_ascii=False) if isinstance(val, (dict, list)) else str(val)
                    if len(s) > 400:
                        s = s[:400] + '...'
                    print(f'  {key}: {s}')
