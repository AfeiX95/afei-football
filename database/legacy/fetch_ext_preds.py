import json, re, sys
from urllib.request import urlopen, Request
sys.stdout.reconfigure(encoding='utf-8')

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'

def fetch(url, timeout=10):
    req = Request(url, headers={'User-Agent': UA})
    resp = urlopen(req, timeout=timeout)
    return resp.read().decode('utf-8', errors='ignore')

def strip_html(text):
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def ddg_search(query):
    url = 'https://html.duckduckgo.com/html/?q=' + query.replace(' ', '+')
    try:
        html = fetch(url, timeout=10)
        results = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
        results = [strip_html(r) for r in results[:5]]
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
        titles = [strip_html(t) for t in titles[:5]]
        return list(zip(titles, results))
    except Exception as e:
        return [(f'Error: {e}', '')]

print('='*60)
print('Search 1: Valerenga vs HamKam')
print('='*60)
results1 = ddg_search('Valerenga vs HamKam prediction tips Eliteserien 2026')
for title, snippet in results1:
    print(f'\nTitle: {title}')
    if snippet: print(f'Snippet: {snippet[:300]}')

print('\n\n' + '='*60)
print('Search 2: Bodo Glimt vs Lillestrom')
print('='*60)
results2 = ddg_search('Bodo Glimt vs Lillestrm prediction tips Eliteserien 2026')
for title, snippet in results2:
    print(f'\nTitle: {title}')
    if snippet: print(f'Snippet: {snippet[:300]}')

# Direct fetch from prediction sites
print('\n\n' + '='*60)
print('Direct site fetches')
print('='*60)

sites = [
    ('Forebet-VAL', 'https://www.forebet.com/en/football-predictions/valerenga-vs-hamkam'),
    ('Forebet-BGL', 'https://www.forebet.com/en/football-predictions/bodoglimt-vs-lillestrom'),
    ('Predictz-NOR', 'https://www.predictz.com/predictions/norway/'),
]

for name, url in sites:
    try:
        html = fetch(url, timeout=8)
        text = strip_html(html)
        # Find prediction keywords
        for kw in ['forecast', 'prediction', 'probability', 'expected result', 'home win', 'away win', 'draw', 'tip']:
            idx = text.lower().find(kw)
            if idx > 0:
                snippet = text[max(0,idx-30):idx+250]
                print(f'\n[{name}] ...{snippet}...')
                break
        else:
            print(f'\n[{name}] No prediction keywords found, showing first 500 chars:')
            print(text[:500])
    except Exception as e:
        print(f'\n[{name}] Error: {e}')
