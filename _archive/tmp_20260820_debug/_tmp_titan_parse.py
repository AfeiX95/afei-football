# -*- coding: utf-8 -*-
import re, sys, io, json, html as htmlmod

fname = sys.argv[1]
raw = open(fname, 'rb').read()
html = raw.decode('gbk', errors='replace')

out = io.StringIO()

# 1. jsonData (积分)
m = re.search(r'var jsonData\s*=\s*(\{.*?\});', html, re.S)
if m:
    try:
        jd = json.loads(m.group(1))
        out.write('===== jsonData =====\n')
        out.write(json.dumps(jd, ensure_ascii=False, indent=1)[:6000])
        out.write('\n')
    except Exception as e:
        out.write('jsonData parse ERR: %r\n' % e)

# 2. radarJsonData (雷达图对比)
m2 = re.search(r'var radarJsonData\s*=\s*\'(\{.*?\})\';', html, re.S)
if m2:
    try:
        rd = json.loads(m2.group(1))
        out.write('\n===== radarJsonData =====\n')
        out.write(json.dumps(rd, ensure_ascii=False, indent=1)[:8000])
        out.write('\n')
    except Exception as e:
        out.write('radar parse ERR: %r\n' % e)

# 3. 其他中文长文本（如分析正文）
body = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
body = re.sub(r'<style.*?</style>', ' ', body, flags=re.S)
text = re.sub(r'<[^>]+>', '|', body)
text = htmlmod.unescape(text)
text = re.sub(r'\|+', '|', text)
text = re.sub(r'[ \t]+', ' ', text)
segments = [s.strip() for s in text.split('|') if len(s.strip()) > 10]
out.write('\n===== text segments =====\n')
out.write('\n'.join(segments[:200]))

with open(fname + '.parsed', 'w', encoding='utf-8') as f:
    f.write(out.getvalue())
print('parsed written', len(out.getvalue()))
