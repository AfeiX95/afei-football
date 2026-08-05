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

# Try multiple sites
attempts = [
    ('Forebet-VAL-v2', 'https://www.forebet.com/en/football-predictions/valerenga-vs-hamkam'),
    ('Forebet-BGL-v2', 'https://www.forebet.com/en/football-predictions/bodo-glimt-vs-lillestrom'),
    ('FootballP-VAL', 'https://www.footballpredictions.com/norway/valerenga-vs-hamkam-prediction/'),
    ('FootballP-BGL', 'https://www.footballpredictions.com/norway/bodo-glimt-vs-lillestrom-prediction/'),
    ('SoccerVital-VAL', 'https://www.soccer-vital.com/predictions/valerenga-hamkam/'),
    ('SoccerVital-BGL', 'https://www.soccer-vital.com/predictions/bodo-glimt-lillestrom/'),
    ('WinC-VAL', 'https://www.wincomparator.com/en/football-predictions/valerenga-hamkam/'),
    ('WinC-BGL', 'https://www.wincomparator.com/en/football-predictions/bodo-glimt-lillestrom/'),
]

for name, url in attempts:
    try:
        html = fetch(url, timeout=8)
        text = strip_html(html)
        # Find prediction keywords
        found = False
        for kw in ['prediction', 'forecast', 'probability', 'expected result', 'home win', 'away win', 'correct score', 'tip', 'win probability']:
            idx = text.lower().find(kw)
            if idx > 0:
                snippet = text[max(0,idx-50):idx+300]
                print(f'\n[{name}] ...{snippet}...')
                found = True
                break
        if not found:
            print(f'\n[{name}] No keywords. First 300 chars:')
            print(text[:300])
    except Exception as e:
        print(f'\n[{name}] Error: {e}')
