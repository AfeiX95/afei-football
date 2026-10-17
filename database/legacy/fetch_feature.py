import json, sys
from urllib.request import urlopen, Request
sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

# Try to get match IDs from the calculator API
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
            print(f'{match_num}: {ha} vs {aa} | matchId={mid}')
            
            # Try to get feature analysis
            if mid:
                try:
                    feature_url = f'https://webapi.sporttery.cn/gateway/uniform/football/getAnalysisV1.qry?channel=c&matchId={mid}'
                    fdata = json.loads(urlopen(Request(feature_url, headers={'User-Agent': UA}), timeout=10).read())
                    # Print key analysis data
                    value = fdata.get('value', {})
                    if value:
                        # Match info
                        mi = value.get('matchInfo', {})
                        if mi:
                            print(f'  Match Info: {json.dumps(mi, ensure_ascii=False)[:500]}')
                        # Analysis
                        analysis = value.get('analysis', {})
                        if analysis:
                            for key in analysis:
                                item = analysis[key]
                                if item:
                                    s = json.dumps(item, ensure_ascii=False)
                                    if len(s) > 300:
                                        s = s[:300] + '...'
                                    print(f'  [{key}] {s}')
                except Exception as e:
                    print(f'  Feature analysis error: {e}')
            print()
