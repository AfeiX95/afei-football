# -*- coding: utf-8 -*-
import re, sys, io, json, html as htmlmod

fname = sys.argv[1]
raw = open(fname, 'rb').read()
html = raw.decode('utf-8', errors='replace')

out = io.StringIO()

m = re.search(r'var jsonData\s*=\s*(\{.*?\});', html, re.S)
if m:
    try:
        jd = json.loads(m.group(1))
        out.write('===== jsonData =====\n')
        out.write(json.dumps(jd, ensure_ascii=False, indent=1)[:9000])
        out.write('\n')
    except Exception as e:
        out.write('jsonData parse ERR: %r\n' % e)

m2 = re.search(r'var radarJsonData\s*=\s*\'(\{.*?\})\';', html, re.S)
if m2:
    try:
        rd = json.loads(m2.group(1))
        out.write('\n===== radarJsonData =====\n')
        out.write(json.dumps(rd, ensure_ascii=False, indent=1)[:9000])
        out.write('\n')
    except Exception as e:
        out.write('radar parse ERR: %r\n' % e)

# 查找比赛列表（vsMatches 可能很长，单独dump）
m3 = re.search(r'"vsMatches":\s*(\{.*?\})\s*,\s*"cupPoints"', html, re.S)
if m3:
    try:
        vm = json.loads(m3.group(1))
        out.write('\n===== vsMatches =====\n')
        out.write(json.dumps(vm, ensure_ascii=False, indent=1)[:12000])
        out.write('\n')
    except Exception as e:
        out.write('vsMatches parse ERR: %r\n' % e)

with open(fname + '.parsed2', 'w', encoding='utf-8') as f:
    f.write(out.getvalue())
print('parsed2 written', len(out.getvalue()))
