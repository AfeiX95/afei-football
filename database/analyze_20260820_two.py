# -*- coding: utf-8 -*-
"""
2026-08-19/20 两场前瞻模型推演
周三002 马竞 vs 马拉加 | 周三007 奈梅亨 vs 博德闪耀
模型: v2.9.0 + C28/C29候选规则视角
"""
import math, random

def simulate(lam_h, lam_a, n=200000):
    res = {"home": 0, "draw": 0, "away": 0}
    scores = {}
    over25 = 0
    for _ in range(n):
        h = 0; p = math.exp(-lam_h); r = random.random(); cdf = p
        while cdf < r and h < 20:
            h += 1; p *= lam_h / h; cdf += p
        a = 0; p2 = math.exp(-lam_a); r2 = random.random(); cdf2 = p2
        while cdf2 < r2 and a < 20:
            a += 1; p2 *= lam_a / a; cdf2 += p2
        if h > a: res["home"] += 1
        elif h == a: res["draw"] += 1
        else: res["away"] += 1
        if h + a >= 3: over25 += 1
        scores[f"{h}-{a}"] = scores.get(f"{h}-{a}", 0) + 1
    nf = float(n)
    r = {k: round(v/nf*100, 1) for k, v in res.items()}
    top = sorted(scores.items(), key=lambda x: -x[1])[:10]
    top = [(s, round(p/nf*100, 1)) for s, p in top]
    return r, round(over25/nf*100, 1), top

def handicap(lam_h, lam_a, hcp, n=200000):
    res = {"home": 0, "draw": 0, "away": 0}
    for _ in range(n):
        h = 0; p = math.exp(-lam_h); r = random.random(); cdf = p
        while cdf < r and h < 20:
            h += 1; p *= lam_h / h; cdf += p
        a = 0; p2 = math.exp(-lam_a); r2 = random.random(); cdf2 = p2
        while cdf2 < r2 and a < 20:
            a += 1; p2 *= lam_a / a; cdf2 += p2
        adj = h + hcp
        if adj > a: res["home"] += 1
        elif adj == a: res["draw"] += 1
        else: res["away"] += 1
    nf = float(n)
    return {k: round(v/nf*100, 1) for k, v in res.items()}

print("=" * 72)
print("周三002 马竞 vs 马拉加 | 西甲第1轮 | 2026-08-20 03:00")
print("=" * 72)
print("市场隐含: 主73.8%/平17.4%/客8.9% | 让-1: 1.74/3.60/3.61")
# λ待外媒数据校准 (马竞豪门主场 vs 升班马/中游客场)
# 暂估: 马竞1.9, 马拉加0.7 (C05升班马客场λ×0.80待确认)
lam_h = 1.90; lam_a = 0.70
print(f"λ暂估: 马竞{lam_h} / 马拉加{lam_a}")
r, over, top = simulate(lam_h, lam_a)
print(f"模型: 主{r['home']}% 平{r['draw']}% 客{r['away']}% | 大2.5 {over}%")
print(f"比分Top: {top}")
hc = handicap(lam_h, lam_a, -1)
print(f"让-1: 马竞净胜2+ {hc['home']}% | 净胜1 {hc['draw']}% | 平或负 {hc['away']}%")

print()
print("=" * 72)
print("周三007 奈梅亨 vs 博德闪耀 | 欧冠附加赛 | 2026-08-20 03:00")
print("=" * 72)
print("市场隐含: 主37.7%/平25.3%/客37.0% | 让-1(奈梅亨): 4.85/4.30/1.45")
# 五五开场景, λ接近
lam_h = 1.30; lam_a = 1.25
print(f"λ暂估: 奈梅亨{lam_h} / 博德闪耀{lam_a}")
r, over, top = simulate(lam_h, lam_a)
print(f"模型: 主{r['home']}% 平{r['draw']}% 客{r['away']}% | 大2.5 {over}%")
print(f"比分Top: {top}")
hc = handicap(lam_h, lam_a, -1)
print(f"让-1(奈梅亨): 净胜2+ {hc['home']}% | 净胜1 {hc['draw']}% | 平或负 {hc['away']}%")
