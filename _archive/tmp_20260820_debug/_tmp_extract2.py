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
outname = sys.argv[2]
html = open(fname, encoding='utf-8', errors='replace').read()

result = 'BODY NOT FOUND'
m = re.search(r'<div[^>]*class="[^"]*post_body[^"]*"[^>]*>(.*?)<div[^>]*class="[^"]*post_statement', html, re.S)
if not m:
    m = re.search(r'<div[^>]*class="[^"]*post_body[^"]*"[^>]*>(.*)', html, re.S)
if not m:
    m = re.search(r'(<p>.*)</body>', html, re.S)
if m:
    result = clean(m.group(1))

with open(outname, 'w', encoding='utf-8') as f:
    f.write(result)
print('written', outname, len(result))
