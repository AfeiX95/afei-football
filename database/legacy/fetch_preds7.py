import re, sys, ssl
from urllib.request import urlopen, Request
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

def fetch(url, timeout=10):
    req = Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    resp = urlopen(req, timeout=timeout, context=ctx)
    return resp.read().decode('utf-8', errors='ignore')

def strip_html(text):
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Try SoccerPunter and other sites
sites = [
    ('SP-VAL', 'https://www.soccerpunter.com/football/Norway-Eliteserien/2026/round-16/valerenga-hamkam'),
    ('SP-BGL', 'https://www.soccerpunter.com/football/Norway-Eliteserien/2026/round-16/bodo-glimt-lillestrom'),
    ('Whoscored', 'https://www.whoscored.com/Regions/26/Tournaments/95/Season/10359/Fixtures/Norway-Eliteserien'),
    ('SofaScore', 'https://www.sofascore.com/football/2026-08-01'),
]

for name, url in sites:
    try:
        html = fetch(url, timeout=8)
        text = strip_html(html)
        print(f'\n{"="*60}')
        print(f'[{name}] Length: {len(text)}')
        
        # Search for specific team mentions
        for team in ['Valerenga', 'Hamkam', 'Bodo', 'Glimt', 'Lillestrom']:
            idx = text.lower().find(team.lower())
            if idx > 0:
                snippet = text[max(0,idx-50):idx+300]
                print(f'  [{team}] ...{snippet[:250]}...')
        if len(text) > 0:
            print(f'  First 400: {text[:400]}')
    except Exception as e:
        print(f'\n[{name}] Error: {e}')
