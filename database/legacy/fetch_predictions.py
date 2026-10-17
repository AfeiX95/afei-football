import json
from urllib.request import urlopen, Request

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# Try multiple prediction sources
sources = [
    ('FootyStats', 'https://footystats.org/norway/valerenga-vs-hamkam-prediction'),
    ('Kickoff', 'https://www.kickoff.com/norway/elite-serien/valerenga-vs-hamkam'),
    ('SoccerPunter', 'https://www.soccerpunter.com/football/Norway---Eliteserien/2026/round-16/valerenga---hamkam'),
]

for name, url in sources:
    try:
        req = Request(url, headers=headers)
        resp = urlopen(req, timeout=8)
        text = resp.read().decode('utf-8', errors='ignore')
        # Extract relevant prediction text
        lines = text.split('\n')
        prediction_lines = []
        for i, line in enumerate(lines):
            low = line.lower()
            if any(kw in low for kw in ['prediction', 'predicted score', 'win probability', 'tip', 'forecast', 'expected']):
                prediction_lines.append(line.strip()[:200])
        if prediction_lines:
            print(f'=== {name} ===')
            for pl in prediction_lines[:5]:
                print(f'  {pl}')
            print()
    except Exception as e:
        print(f'{name}: {e}')
