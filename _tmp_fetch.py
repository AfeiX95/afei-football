# -*- coding: utf-8 -*-
import urllib.request, ssl, sys, io, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

targets = [
    ('qmw1', 'https://www.qiumiwu.com/news/1990634411925'),
    ('qmw2', 'https://www.qiumiwu.com/news/1990635446115'),
    ('titan', 'https://m.titan007.com/Analy/Analysis/3000414.htm'),
    ('tcorner', 'https://www.totalcorner.com/zh-tw/stats/fc-tokyo-vs-jef-utd-chiba/198656153'),
    ('bdplus', 'https://bongdaplus.vn/j-league/nhan-dinh-bong-da-fc-tokyo-vs-jef-united-chiba-17h30-ngay-21-8-ghim-chan-nhau-5141122608.html'),
]

for name, url in targets:
    out = r'I:\阿飞说球\_tmp_' + name + '.html'
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        r = urllib.request.urlopen(req, timeout=40, context=ctx)
        data = r.read()
        with open(out, 'wb') as f:
            f.write(data)
        print(f'{name}: HTTP {r.status} bytes={len(data)} -> {out}')
    except Exception as e:
        print(f'{name}: ERR {repr(e)}')
    time.sleep(1)
