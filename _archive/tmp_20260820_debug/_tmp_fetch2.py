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
    ('m7m', 'https://news.7m.com.cn/mobi/news/20260820/735942.shtml'),
    ('sohu', 'https://www.sohu.com/a/1065348118_122918735'),
]

for name, url in targets:
    out = r'I:\阿飞说球\_tmp_' + name + '.html'
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        r = urllib.request.urlopen(req, timeout=40, context=ctx)
        data = r.read()
        with open(out, 'wb') as f:
            f.write(data)
        print(f'{name}: HTTP {r.status} bytes={len(data)}')
    except Exception as e:
        print(f'{name}: ERR {repr(e)}')
    time.sleep(1)
