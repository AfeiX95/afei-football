import re, sys
from urllib.request import urlopen, Request
sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

def fetch(url, timeout=10):
    req = Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    resp = urlopen(req, timeout=timeout)
    return resp.read().decode('utf-8', errors='ignore')

def strip_html(text):
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Focus on FootballPredictions.com
matches = [
    ('VAL-HAM', 'https://www.footballpredictions.com/norway/valerenga-vs-hamkam-prediction/'),
    ('BGL-LIL', 'https://www.footballpredictions.com/norway/bodo-glimt-vs-lillestrom-prediction/'),
]

for name, url in matches:
    try:
        html = fetch(url, timeout=10)
        text = strip_html(html)
        
        # Search for prediction content with more context
        keywords = ['prediction', 'match result', 'correct score', 'both teams to score', 
                     'over', 'under', 'win probability', 'home', 'away', 'draw',
                     'valerenga', 'hamkam', 'bodo', 'glimt', 'lillestrom',
                     'tip', 'forecast', 'ai prediction', 'computer prediction',
                     'half time', 'full time']
        
        print(f'\n{"="*60}')
        print(f'[{name}] Full text length: {len(text)}')
        print(f'{"="*60}')
        
        # Print sections with prediction keywords
        for i in range(0, len(text), 200):
            chunk = text[i:i+200]
            if any(kw in chunk.lower() for kw in ['predict', 'tip', 'forecast', 'probability', 'score', 'result', 'home win', 'away win', 'draw']):
                print(f'  ...{chunk}...')
    except Exception as e:
        print(f'\n[{name}] Error: {e}')

# Also try odds portal
print('\n\n' + '='*60)
print('Odds comparison attempts')
print('='*60)

odds_sites = [
    ('OddsP-VAL', 'https://www.oddsportal.com/football/norway/eliteserien/valerenga-hamkam-2026-08-01/'),
    ('OddsP-BGL', 'https://www.oddsportal.com/football/norway/eliteserien/bodo-glimt-lillestrom-2026-08-01/'),
]

for name, url in odds_sites:
    try:
        html = fetch(url, timeout=8)
        text = strip_html(html)
        print(f'\n[{name}] Length: {len(text)}')
        # Look for odds
        for kw in ['1x2', 'over', 'under', 'handicap', 'goal', 'prediction']:
            idx = text.lower().find(kw)
            if idx > 0:
                print(f'  ...{text[max(0,idx-30):idx+200]}...')
                break
    except Exception as e:
        print(f'\n[{name}] Error: {e}')
