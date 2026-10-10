# -*- coding: utf-8 -*-
"""验证"市场反推 λ 总量"方法是否可靠 (用 560 场历史样本)

若市场反推的 λ 总量能预测实际总进球 -> 该方法可用作"市场对这场比赛进球量的定价"。
否则不能用它去质疑模型。
"""
import math
import os
import re
import sys

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                                     '00_引擎', 'backtest'))


def pois(k, lam):
    return lam ** k * math.exp(-lam) / math.factorial(k)


def probs_from(lh, la, n=12):
    ph = pd = pa = 0.0
    for h in range(n):
        for a in range(n):
            p = pois(h, lh) * pois(a, la)
            if h > a:
                ph += p
            elif h == a:
                pd += p
            else:
                pa += p
    return ph, pd, pa


def infer(mk, step=0.03):
    best, be = None, 1e9
    lh = 0.3
    while lh <= 3.6:
        la = 0.2
        while la <= 3.0:
            ph, pd, pa = probs_from(lh, la)
            e = (ph - mk[0]) ** 2 + (pd - mk[1]) ** 2 + (pa - mk[2]) ** 2
            if e < be:
                be, best = e, (lh, la)
            la += step
        lh += step
    return best


# ---- 载入历史
rows = []
seen = set()
for fn in sorted(os.listdir(BASE)):
    if not (fn.startswith('matches_') and fn.endswith('.tsv')):
        continue
    with open(os.path.join(BASE, fn), encoding='utf-8') as f:
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) < 10 or p[9] != 'done':
                continue
            k = (p[0], p[3])
            if k in seen or not (p[6] and p[7] and p[8]):
                continue
            seen.add(k)
            try:
                fh, fa = map(int, p[5].split(':'))
                o = {'H': float(p[6]), 'D': float(p[7]), 'A': float(p[8])}
            except ValueError:
                continue
            inv = {kk: 1 / v for kk, v in o.items()}
            s = sum(inv.values())
            rows.append({'p': {kk: v / s for kk, v in inv.items()}, 'tot': fh + fa,
                         'fh': fh, 'fa': fa})

print(f'样本 {len(rows)} 场(有胜平负赔率且已开奖)')
print()

# 抽薄: 每 5 场取 1 场做 λ 反推(网格搜索较慢)
sub = rows[::5]
print(f'抽 {len(sub)} 场做反推(网格搜索)')
print()

preds, acts = [], []
for r in sub:
    lh, la = infer((r['p']['H'], r['p']['D'], r['p']['A']))
    preds.append(lh + la)
    acts.append(r['tot'])

n = len(preds)
mp = sum(preds) / n
ma = sum(acts) / n
bias = mp - ma
mae = sum(abs(p - a) for p, a in zip(preds, acts)) / n
r2 = 1 - sum((p - a) ** 2 for p, a in zip(preds, acts)) / sum((a - ma) ** 2 for a in acts)

print('=' * 88)
print('市场反推 λ总量 vs 实际总进球')
print()
print('  反推 λ总量 均值 = %.3f' % mp)
print('  实际总进球 均值 = %.3f' % ma)
print('  偏差(反推 - 实际) = %+.3f 球' % bias)
print('  平均绝对误差 MAE  = %.3f 球' % mae)
print('  R² = %.4f' % r2)
print()
if abs(bias) < 0.15:
    print('  ✅ 反推 λ总量 与实际总进球基本无偏 -> 可用作"市场对进球量的定价"')
else:
    print('  ⚠️ 存在 %.2f 球偏差 -> 用作进球量基准时需扣除该偏差' % bias)

print()
print('  分档看偏差(检查是否随进球量变化):')
buckets = {}
for p, a in zip(preds, acts):
    k = int(p)
    buckets.setdefault(k, []).append(a)
print('  %-14s %5s %10s %10s %8s' % ('反推λ总量档', 'n', '反推均值', '实际均值', '偏差'))
for k in sorted(buckets):
    v = buckets[k]
    if len(v) < 8:
        continue
    pm = sum(x for x in v) / len(v)
    mm = sum([k] * len(v)) / len(v)     # 近似用档位中值
    print('  %-14s %5d %10.2f %10.2f %+8.2f' % (f'~{k}', len(v), pm, pm, 0.0))
print()
print('  (注: 上面的"实际均值"列需直接算, 见下)')
print('  %-14s %5s %10s %10s %8s' % ('反推λ总量档', 'n', '反推均值', '实际均值', '偏差'))
for k in sorted(buckets):
    v = buckets[k]
    if len(v) < 8:
        continue
    am = sum(v) / len(v)
    print('  %-14s %5d %10s %10.2f %+8.2f' % (f'~{k}', len(v), '—', am, k - am))
