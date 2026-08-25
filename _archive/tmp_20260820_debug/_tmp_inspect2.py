# -*- coding: utf-8 -*-
import re, sys, io

fname = sys.argv[1]
html = open(fname, encoding='utf-8', errors='replace').read()

# 打印几个关键位置的上下文
for pos in [2080, 28750, 30418, 377213]:
    print(f'===== pos {pos} =====')
    print(html[pos-200:pos+400].replace('\n', ' '))
    print()

# 查找内嵌 JSON 或接口 URL
print('===== scripts with data =====')
for m in re.finditer(r'<script[^>]*>(.*?)</script>', html, re.S):
    s = m.group(1)
    if 'analysis' in s.lower() or 'analy' in s.lower() or 'fenxi' in s.lower() or 'data' in s.lower():
        print(s[:800])
        print('---')
