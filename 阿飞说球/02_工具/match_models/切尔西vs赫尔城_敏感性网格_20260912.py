# -*- coding: utf-8 -*-
"""周六012 切尔西 vs 赫尔城 — λ±10% 敏感性网格(公众号深度版用)

为什么要网格: 赫尔城"场均失0.4球"是极端小样本(赛季3场0失球), 直接用会
把 λ_切尔西 算到 1.96(和对手齐平), 与市场 79.8% 完全背离 → 模型此处失效。
改用"市场隐含 λ 反推 + ±10% 五场景", 作为公众号深度版的区间口径(规范: 不用单点)。
"""
import math
import os
import sys
from itertools import product

ROOT = r'D:\Hermes\football'
sys.path.insert(0, os.path.join(ROOT, '阿飞说球', '02_工具'))
import afei_generator as G  # noqa: E402


def lam_from_market(mH, mD, mA, iters=200):
    """由市场胜平负隐含概率反推 (λh, λa) —— 网格搜索最小化与市场概率的平方差"""
    best, best_err = None, 1e9
    h = 0.6
    while h <= 3.6:
        a = 0.4
        while a <= 3.2:
            probs = {(x, y): G.poisson_pmf(x, h) * G.poisson_pmf(y, a) for x, y in product(range(8), repeat=2)}
            pH = sum(p for (x, y), p in probs.items() if x > y)
            pD = sum(p for (x, y), p in probs.items() if x == y)
            pA = sum(p for (x, y), p in probs.items() if x < y)
            err = (pH - mH) ** 2 + (pD - mD) ** 2 + (pA - mA) ** 2
            if err < best_err:
                best_err, best = err, (h, a)
            a += 0.02
        h += 0.02
    return best, best_err


def dist(lh, la):
    probs = {(x, y): G.poisson_pmf(x, lh) * G.poisson_pmf(y, la) for x, y in product(range(8), repeat=2)}
    pH = sum(p for (x, y), p in probs.items() if x > y)
    pD = sum(p for (x, y), p in probs.items() if x == y)
    pA = sum(p for (x, y), p in probs.items() if x < y)
    over = sum(p for (x, y), p in probs.items() if x + y > 2.5)
    n1 = sum(p for (x, y), p in probs.items() if x - y == 1)
    n2e = sum(p for (x, y), p in probs.items() if x - y == 2)
    n2p = sum(p for (x, y), p in probs.items() if x - y >= 2)
    top = sorted(probs.items(), key=lambda kv: -kv[1])[:5]
    return dict(pH=pH, pD=pD, pA=pA, over=over, n1=n1, n2e=n2e, n2p=n2p, top=top)


mH, mD, mA = 0.798, 0.134, 0.068
(lh0, la0), err = lam_from_market(mH, mD, mA)
print(f'市场反推 λ: 切尔西 {lh0:.2f} / 赫尔城 {la0:.2f}  (拟合误差 {err:.5f})')
d0 = dist(lh0, la0)
print(f'  校验: 主 {d0["pH"]*100:.1f} / 平 {d0["pD"]*100:.1f} / 客 {d0["pA"]*100:.1f}  (市场 79.8/13.4/6.8)')
print()

print('=== λ±10% 五场景(主场视角) ===')
print(f'{"场景":26s}{"λ切":>6s}{"λ赫":>6s}{"主胜":>7s}{"平":>6s}{"客胜":>7s}{"大2.5":>7s}{"净胜1":>7s}{"净胜2":>7s}{"净胜2+":>8s}')
rows = []
for tag, mh, ma in [('基准', 1.0, 1.0), ('切尔西-10%', 0.9, 1.0), ('切尔西+10%', 1.1, 1.0),
                    ('赫尔城+10%(防守更差)', 1.0, 1.1), ('赫尔城-10%(防守更好)', 1.0, 0.9),
                    ('双降-10%(闷)', 0.9, 0.9), ('双升+10%(开)', 1.1, 1.1)]:
    lh, la = lh0 * mh, la0 * ma
    d = dist(lh, la)
    rows.append((tag, lh, la, d))
    print(f'{tag:26s}{lh:6.2f}{la:6.2f}{d["pH"]*100:7.1f}{d["pD"]*100:6.1f}{d["pA"]*100:7.1f}'
          f'{d["over"]*100:7.1f}{d["n1"]*100:7.1f}{d["n2e"]*100:7.1f}{d["n2p"]*100:8.1f}')

print()
print('=== 区间汇总(五场景的 min-max) ===')
for key, name in [('pH', '主胜'), ('pD', '平局'), ('pA', '客胜'), ('over', '大2.5'), ('n2p', '净胜2球以上')]:
    vals = [d[key] * 100 for _, _, _, d in rows]
    print(f'  {name:10s} {min(vals):5.1f}% ~ {max(vals):5.1f}%')

print()
print('=== 基准场景 TOP5 比分 ===')
for (h, a), p in d0['top']:
    print(f'  {h}:{a}  {p*100:.1f}%')
print()
print(f'让球(-2)口径(基准): 让胜(净胜3+) {sum(p for (x,y),p in [(k,v) for k,v in [((x,y), G.poisson_pmf(x,lh0)*G.poisson_pmf(y,la0)) for x,y in product(range(8),repeat=2)]] if x-y>=3)*100:.1f}%'
      f' / 走水(净胜2) {d0["n2e"]*100:.1f}% / 让负(净胜≤1或不胜) {(1-sum(p for (x,y),p in [(k,v) for k,v in [((x,y), G.poisson_pmf(x,lh0)*G.poisson_pmf(y,la0)) for x,y in product(range(8),repeat=2)]] if x-y>=2))*100:.1f}%')
