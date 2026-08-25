# -*- coding: utf-8 -*-
import re, io, sys, html as htmlmod

def clean(body):
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<style.*?</style>', '', body, flags=re.S)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'</(p|div|h\d|li)>', '\n', body)
    body = re.sub(r'<[^>]+>', '', body)
    body = htmlmod.unescape(body)
    body = re.sub(r'[ \t\u3000]+', ' ', body)
    body = re.sub(r'\n\s*\n+', '\n', body)
    lines = [l.strip() for l in body.split('\n') if l.strip()]
    return '\n'.join(lines)

fname = sys.argv[1]
html = open(fname, encoding='utf-8', errors='replace').read()

# 网易正文容器
m = re.search(r'<div[^>]*class="[^"]*post_body[^"]*"[^>]*>(.*?)<div[^>]*class="[^"]*post_statement', html, re.S)
if not m:
    m = re.search(r'<div[^>]*class="[^"]*post_body[^"]*"[^>]*>(.*)', html, re.S)
if not m:
    # 通用: 找 <p> 段落最密集区域
    m = re.search(r'(<p>.*)</body>', html, re.S)
if m:
    print(clean(m.group(1)))
else:
    print('BODY NOT FOUND')
