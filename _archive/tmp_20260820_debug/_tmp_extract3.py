# -*- coding: utf-8 -*-
import re, io, sys, html as htmlmod

def clean(body):
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<style.*?</style>', '', body, flags=re.S)
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'</(p|div|h\d|li|tr|td)>', '\n', body)
    body = re.sub(r'<[^>]+>', '', body)
    body = htmlmod.unescape(body)
    body = re.sub(r'[ \t\u3000]+', ' ', body)
    body = re.sub(r'\n\s*\n+', '\n', body)
    lines = [l.strip() for l in body.split('\n') if l.strip()]
    return '\n'.join(lines)

fname = sys.argv[1]
outname = sys.argv[2]
html = open(fname, encoding='utf-8', errors='replace').read()

# 列出所有 class 名供诊断
classes = sorted(set(re.findall(r'class="([^"]+)"', html)))
with open(outname + '.classes', 'w', encoding='utf-8') as f:
    f.write('\n'.join(classes))

# 尝试常见正文容器
candidates = [
    r'<div[^>]*class="[^"]*news-content[^"]*"[^>]*>(.*?)<div',
    r'<div[^>]*class="[^"]*article-content[^"]*"[^>]*>(.*?)<div',
    r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)<div',
    r'<div[^>]*class="[^"]*detail[^"]*"[^>]*>(.*?)<div',
    r'<div[^>]*class="[^"]*text[^"]*"[^>]*>(.*?)<div',
    r'(<p[^>]*>.*?)<div[^>]*class="[^"]*(comment|footer|related)',
]
result = 'BODY NOT FOUND'
for pat in candidates:
    m = re.search(pat, html, re.S)
    if m and len(m.group(1)) > 200:
        result = clean(m.group(1))
        break
if result == 'BODY NOT FOUND':
    # 兜底：所有 <p> 内容
    ps = re.findall(r'<p[^>]*>(.*?)</p>', html, re.S)
    if ps:
        result = clean('<p>' + '</p><p>'.join(ps) + '</p>')

with open(outname, 'w', encoding='utf-8') as f:
    f.write(result)
print('written', outname, len(result))
