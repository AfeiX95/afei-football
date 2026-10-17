import re, sys, ssl
from urllib.request import urlopen, Request
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

def fetch(url, timeout=10):
    req = Request(url, headers={
        'User-Agent': UA, 
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    })
    resp = urlopen(req, timeout=timeout, context=ctx)
    return resp.read().decode('utf-8', errors='ignore')

def strip_html(text):
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Try with SSL bypass
matches = [
    ('VAL-HAM-FP', 'https://www.footballpredictions.com/norway/valerenga-vs-hamkam-prediction/'),
    ('BGL-LIL-FP', 'https://www.footballpredictions.com/norway/bodo-glimt-vs-lillestrom-prediction/'),
    ('VAL-HAM-SV', 'https://www.soccer-vital.com/predictions/valerenga-hamkam/'),
    ('BGL-LIL-SV', 'https://www.soccer-vital.com/predictions/bodo-glimt-lillestrom/'),
    ('VAL-HAM-FB', 'https://www.forebet.com/en/football-predictions/valerenga-vs-hamkam'),
    ('BGL-LIL-FB', 'https://www.forebet.com/en/football-predictions/bodoglimt-vs-lillestrom'),
]

for name, url in matches:
    try:
        html = fetch(url, timeout=10)
        text = strip_html(html)
        print(f'\n{"="*60}')
        print(f'[{name}] Length: {len(text)}')
        
        # Find prediction-related content
        found_any = False
        for kw in ['prediction', 'forecast', 'probability', 'match result', 'correct score', 
                    'tip', 'home win', 'away win', 'over 2.5', 'under 2.5',
                    'btts', 'both teams']:
            idx = text.lower().find(kw)
            if idx > 0:
                snippet = text[max(0,idx-50):idx+300]
                print(f'  [{kw}] ...{snippet}...')
                found_any = True
        
        if not found_any:
            print(f'  First 500 chars: {text[:500]}')
    except Exception as e:
        print(f'\n[{name}] Error: {e}')
