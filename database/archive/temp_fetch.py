import urllib.request, re, json

# Try to get竞彩网 odds for this match
# First check if match exists on sporttery
urls_to_try = [
    "https://zq.titan007.com/odds/2929675cn.htm",
    "https://zq.titan007.com/oddslist/2929675cn.htm",
]
for url in urls_to_try:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read()
        if raw[:3] == b"\xef\xbb\xbf":
            raw = raw[3:]
        html = raw.decode("gbk", errors="ignore")
        # Look for odds data
        for kw in ["欧赔", "亚盘", "赔率", "初盘", "即时", "威廉", "立博", "澳门"]:
            idx = html.find(kw)
            if idx > 0:
                snippet = html[max(0,idx-50):idx+300]
                snippet = re.sub(r"<[^>]+>", " ", snippet)
                snippet = re.sub(r"\s+", " ", snippet).strip()
                print(f"[{url.split('/')[-1]}][{kw}] {snippet[:200]}")
        print(f"--- {url} OK, len={len(html)} ---")
    except Exception as e:
        print(f"--- {url} Error: {e} ---")
