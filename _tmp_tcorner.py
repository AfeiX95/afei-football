# -*- coding: utf-8 -*-
import urllib.request, ssl, sys, io, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://www.totalcorner.com/zh-tw/stats/fc-tokyo-vs-jef-utd-chiba/198656153'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.totalcorner.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}
try:
    req = urllib.request.Request(url, headers=headers)
    r = urllib.request.urlopen(req, timeout=40, context=ctx)
    data = r.read()
    open(r'I:\阿飞说球\_tmp_tcorner.html', 'wb').write(data)
    print('tcorner OK', r.status, len(data))
except Exception as e:
    print('tcorner ERR', repr(e))

# Jina Reader 兜底
try:
    jurl = 'https://r.jina.ai/' + url
    req2 = urllib.request.Request(jurl, headers={'User-Agent': 'Mozilla/5.0'})
    r2 = urllib.request.urlopen(req2, timeout=60, context=ctx)
    d2 = r2.read()
    open(r'I:\阿飞说球\_tmp_tcorner_jina.txt', 'wb').write(d2)
    print('tcorner jina OK', r2.status, len(d2))
except Exception as e:
    print('tcorner jina ERR', repr(e))
