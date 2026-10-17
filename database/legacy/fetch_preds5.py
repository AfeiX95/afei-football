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

# Get full text from FootballPredictions
matches = [
    ('VAL-HAM', 'https://www.footballpredictions.com/norway/valerenga-vs-hamkam-prediction/'),
    ('BGL-LIL', 'https://www.footballpredictions.com/norway/bodo-glimt-vs-lillestrom-prediction/'),
]

for name, url in matches:
    try:
        html = fetch(url, timeout=10)
        text = strip_html(html)
        print(f'\n{"="*60}')
        print(f'[{name}] FULL TEXT (key sections)')
        print(f'{"="*60}')
        
        # Print the full text in chunks to find prediction data
        # Look for the prediction section specifically
        sections = text.split('.')
        for i, section in enumerate(sections):
            section = section.strip()
            if len(section) > 30 and any(kw in section.lower() for kw in [
                'prediction', 'tip', 'we predict', 'forecast', 'expected',
                'home win', 'away win', 'draw', 'score', 'goal',
                'probability', 'chance', 'likely', 'verdict', 'best bet',
                'valerenga', 'hamkam', 'bodo', 'glimt', 'lillestrom',
                'form', 'h2h', 'head to head', 'stats', 'analysis',
                'over', 'under', 'btts', 'clean sheet'
            ]):
                print(f'  [{i}] {section[:250]}')
                
    except Exception as e:
        print(f'\n[{name}] Error: {e}')
