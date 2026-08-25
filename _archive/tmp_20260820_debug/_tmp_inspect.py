# -*- coding: utf-8 -*-
import re, sys, io, html as htmlmod

fname = sys.argv[1]
html = open(fname, encoding='utf-8', errors='replace').read()

# 找正文关键词位置
for kw in ['柏太阳神', '长崎', '排名', '交锋', '伤', '预计阵容', '分析', 'Kashiwa', 'Nagasaki']:
    idxs = [m.start() for m in re.finditer(re.escape(kw), html)]
    print(kw, '->', len(idxs), 'hits', idxs[:8])

# 找出所有脚本外的长文本段
body = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
body = re.sub(r'<style.*?</style>', ' ', body, flags=re.S)
text = re.sub(r'<[^>]+>', '|', body)
text = htmlmod.unescape(text)
text = re.sub(r'\|+', '|', text)
text = re.sub(r'[ \t]+', ' ', text)
segments = [s.strip() for s in text.split('|') if len(s.strip()) > 15]
out = '\n'.join(segments)
open(fname + '.alltext', 'w', encoding='utf-8').write(out)
print('alltext written', len(out))
