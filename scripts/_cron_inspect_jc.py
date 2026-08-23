# -*- coding: utf-8 -*-
"""检查竞彩API JSON结构"""
import json, sys

with open(sys.argv[1], encoding='utf-8') as f:
    d = json.load(f)

print('top keys:', list(d.keys()))
v = d.get('value')
if v is None:
    print('value is None, full keys:', list(d.keys()))
    # 打印部分内容
    s = json.dumps(d, ensure_ascii=False)[:2000]
    print(s)
else:
    print('value keys:', list(v.keys()))
    for k in v.keys():
        val = v[k]
        if isinstance(val, list):
            print(f'  {k}: list len={len(val)}')
        elif isinstance(val, dict):
            print(f'  {k}: dict keys={list(val.keys())[:10]}')
        else:
            print(f'  {k}: {val}')
