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

# Try additional sites
sites = [
    ('Sportskeeda-VAL', 'https://www.sportskeeda.com/football/valerenga-vs-hamkam-prediction'),
    ('Sportskeeda-BGL', 'https://www.sportskeeda.com/football/bodo-glimt-vs-lillestrom-prediction'),
    ('Goal-VAL', 'https://www.goal.com/en/match/valerenga-vs-hamkam/2w9f1g7j6v'),
    ('Goal-BGL', 'https://www.goal.com/en/match/bodo-glimt-vs-lillestrom/2w9f1g7j6v'),
    ('FootyStats-VAL', 'https://footystats.org/norway/valerenga-vs-hamkam'),
    ('FootyStats-BGL', 'https://footystats.org/norway/bodo-glimt-vs-lillestrom'),
]

for name, url in sites:
    try:
        html = fetch(url, timeout=8)
        text = strip_html(html)
        print(f'\n{"="*60}')
        print(f'[{name}] Length: {len(text)}')
        
        # Find prediction content
        for kw in ['prediction', 'tip', 'forecast', 'score', 'probability', 'expected',
                    'home win', 'away win', 'draw', 'verdict', 'form', 'h2h',
                    'btts', 'over 2', 'under 2']:
            idx = text.lower().find(kw)
            if idx > 0:
                snippet = text[max(0,idx-30):idx+300]
                print(f'  [{kw}] ...{snippet[:250]}...')
                break
        else:
            print(f'  First 400: {text[:400]}')
    except Exception as e:
        print(f'\n[{name}] Error: {e}')
