# -*- coding: utf-8 -*-
"""诊断: 520 场是怎么来的 / 哪个文件子集能复现 state 的 502 场与三个桶值"""
import json
import math
import os
import re
import time

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, 'calibration_state.json')


def rows_in(fn):
    out = []
    with open(os.path.join(BASE, fn), encoding='utf-8') as f:
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) < 10 or p[9] != 'done':
                continue
            if not (p[6] and p[7] and p[8]):
                continue
            out.append(p)
    return out


files = []
for fn in sorted(os.listdir(BASE)):
    if fn.startswith('matches_') and fn.endswith('.tsv'):
        mt = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(os.path.join(BASE, fn))))
        rows = rows_in(fn)
        files.append((fn, mt, rows))

print(f'{"file":42s} {"mtime":17s} {"rows":>5s} {"uniq_in_file":>11s}')
seen_all = set()
tot = 0
for fn, mt, rows in files:
    uniq = 0
    for p in rows:
        k = (p[0], p[3])
        if k not in seen_all:
            seen_all.add(k)
            uniq += 1
    tot += uniq
    print(f'{fn:42s} {mt:17s} {len(rows):5d} {uniq:11d}')
print(f'{"TOTAL(去重后)":42s} {"":17s} {"":5s} {tot:11d}')
print(f'state.sample_size = {json.load(open(STATE, encoding="utf-8"))["sample_size"]}')
print()


def buckets(rows):
    ms = []
    for p in rows:
        m = re.match(r'^(.*?)\(([+-]?\d+)\)VS(.*)$', p[3])
        if not m:
            continue
        try:
            fh, fa = map(int, p[5].split(':'))
            odds = {'H': float(p[6]), 'D': float(p[7]), 'A': float(p[8])}
        except ValueError:
            continue
        inv = {k: 1 / v for k, v in odds.items()}
        s = sum(inv.values())
        ms.append({'p': {k: v / s for k, v in inv.items()},
                   'res': 'H' if fh > fa else ('A' if fh < fa else 'D')})

    def br(kind, lo, hi):
        g = [m for m in ms if lo <= m['p'][kind] < hi]
        if len(g) < 8:
            return None, len(g)
        hits = sum(1 for m in g if m['res'] == kind)
        ap = sum(m['p'][kind] for m in g) / len(g)
        return hits / len(g) / ap, len(g)

    d, dn = br('D', .20, .30)
    hs = [br(k, .40, .70) for k in 'HA']
    hs = [x for x in hs if x[0]]
    cs = [br(k, 0.0, .30) for k in 'HA']
    cs = [x for x in cs if x[0]]
    hot = sum(x[0] for x in hs) / len(hs) if hs else None
    cold = sum(x[0] for x in cs) / len(cs) if cs else None
    return len(ms), d, dn, hot, cold


print('state buckets: draw_20_30=1.069 hot_40_70=1.015 cold_0_30=0.884')
print()
print(f'{"子集":46s} {"n":>4s} {"draw":>7s} {"hot":>7s} {"cold":>7s}')
# 场景A: 全部
scenarios = [('全部文件', None)]
# 场景B: 排除 mtime >= 2026-09-18 的文件
scenarios.append(('排除 mtime>=2026-09-18', lambda mt: mt >= '2026-09-18'))
# 场景C: 逐个排除一个文件, 看哪个能逼近
for fn, mt, rows in files:
    if mt >= '2026-09-18':
        scenarios.append((f'排除 {fn}', fn))

for name, cond in scenarios:
    if cond is None:
        rows = [p for _, _, r in files for p in r]
    elif callable(cond):
        rows = [p for _, mt, r in files if not cond(mt) for p in r]
    else:
        rows = [p for fn, _, r in files if fn != cond for p in r]
    # 去重
    seen, ded = set(), []
    for p in rows:
        k = (p[0], p[3])
        if k in seen:
            continue
        seen.add(k)
        ded.append(p)
    n, d, dn, hot, cold = buckets(ded)
    ds = f'{d:.3f}' if d else 'None'
    hs = f'{hot:.3f}' if hot else 'None'
    cs = f'{cold:.3f}' if cold else 'None'
    print(f'{name:46s} {n:4d} {ds:>7s} {hs:>7s} {cs:>7s}')
