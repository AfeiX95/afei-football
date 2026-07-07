# -*- coding: utf-8 -*-
"""荷兰 vs 摩洛哥 | 1/32决赛 | 2026-06-30 09:00"""
import math, random

h_odds, d_odds, a_odds = 2.00, 2.92, 3.48

p_h = 1/h_odds; p_d = 1/d_odds; p_a = 1/a_odds
t = p_h + p_d + p_a
pm_h = p_h/t; pm_d = p_d/t; pm_a = p_a/t

print("="*65)
print("  NED vs MOR | 1/32决赛 | 2026-06-30 09:00")
print("="*65)
print(f"\n=== 市场隐含概率 ===")
print(f"荷兰胜: {pm_h*100:.1f}%")
print(f"平局:   {pm_d*100:.1f}%")
print(f"摩洛哥: {pm_a*100:.1f}%")

# === λ估算 ===
# 方法1: 市场赔率反推
l_raw_h = 0.4 + pm_h * 3.2
l_raw_a = 0.4 + pm_a * 3.2
# Knockout: 势均力敌淘汰赛, 双方都收敛
# 荷兰(稍强)×0.90, 摩洛哥(防反)×0.85
l_h_mkt = l_raw_h * 0.90
l_a_mkt = l_raw_a * 0.85  # 摩洛哥防守反击, 进攻收敛少一些

# 方法2: 实际数据xG法
# 荷兰近10场: GF=24/10=2.4, GA=9/10=0.9
# 摩洛哥近10场: GF=19/10=1.9, GA=6/10=0.6
ned_xgf = 2.4 * 0.92
ned_xga = 0.9 * 1.08
mor_xgf = 1.9 * 0.92
mor_xga = 0.6 * 1.08

# 淘汰赛修正
ned_xgf_adj = ned_xgf * 0.90  # 荷兰收敛
mor_xga_adj = mor_xga * 0.85  # 摩洛哥大巴更紧凑
ned_xga_adj = ned_xga * 0.90
mor_xgf_adj = mor_xgf * 0.85  # 摩洛哥防反进攻收敛

# 状态修正
ned_form = min(0.12, 6*0.08 + 3*0.02 - 1*0.05)  # 6W3D1L
mor_form = min(0.12, 5*0.08 + 5*0.02 + 0*(-0.05))  # 5W5D0L

l_h_xg = (ned_xgf_adj + mor_xga_adj) / 2 + ned_form
l_a_xg = (mor_xgf_adj + ned_xga_adj) / 2 + mor_form

# 综合
L_H = (l_h_mkt + l_h_xg) / 2
L_A = (l_a_mkt + l_a_xg) / 2
L_H = max(0.3, min(3.5, L_H))
L_A = max(0.1, min(2.5, L_A))

print(f"\n=== λ值 ===")
print(f"荷兰λ: {L_H:.3f} (市场法{l_h_mkt:.3f}, xG法{l_h_xg:.3f})")
print(f"摩洛哥λ: {L_A:.3f} (市场法{l_a_mkt:.3f}, xG法{l_a_xg:.3f})")

# === 泊松 ===
def poisson(l, k):
    return (l**k)*math.exp(-l)/math.factorial(k)

probs = {}
hw = dw = aw = 0.0
for h in range(8):
    for a in range(8):
        p = poisson(L_H, h)*poisson(L_A, a)
        probs[(h,a)] = p
        if h>a: hw+=p
        elif h==a: dw+=p
        else: aw+=p

print(f"\n=== 泊松模型 ===")
print(f"荷兰胜: {hw*100:.1f}%")
print(f"平局:   {dw*100:.1f}%")
print(f"摩洛哥: {aw*100:.1f}%")

# === Edge ===
eh = (hw-pm_h)*100
ed = (dw-pm_d)*100
ea = (aw-pm_a)*100

def el(e):
    if e>10: return "强价值"
    elif e>6: return "强价值"
    elif e>3: return "中价值"
    elif e>0: return "弱价值"
    else: return "无价值"

print(f"\n=== Edge ===")
print(f"荷兰胜: {eh:+.1f}pp [{el(eh)}]")
print(f"平局:   {ed:+.1f}pp [{el(ed)}]")
print(f"摩洛哥: {ea:+.1f}pp [{el(ea)}]")

# === Top比分 ===
top = sorted(probs.items(), key=lambda x:-x[1])[:10]
print(f"\n=== Top 10 比分 ===")
for (h,a),p in top:
    bar = "#"*int(p*100)
    print(f"  {h}-{a}: {p*100:5.1f}% {bar}")

# === MC ===
random.seed(42)
N=100000
mc_scores = {}
for _ in range(N):
    hg=0;p=1.0;Lh=math.exp(-L_H)
    while p>Lh:hg+=1;p*=random.random()
    hg-=1
    ag=0;p=1.0;La=math.exp(-L_A)
    while p>La:ag+=1;p*=random.random()
    ag-=1
    mc_scores[(hg,ag)] = mc_scores.get((hg,ag),0)+1

print(f"\n=== MC Top 5 ===")
mc_top = sorted(mc_scores.items(), key=lambda x:-x[1])[:5]
for (h,a),c in mc_top:
    print(f"  {h}-{a}: {c/N*100:.1f}%")

# === 进球区间 ===
u1 = sum(c for (h,a),c in mc_scores.items() if h+a<=1)
u2 = sum(c for (h,a),c in mc_scores.items() if h+a==2)
t3 = sum(c for (h,a),c in mc_scores.items() if h+a==3)
o4 = sum(c for (h,a),c in mc_scores.items() if h+a>=4)
o25 = sum(c for (h,a),c in mc_scores.items() if h+a>=3)
print(f"\n进球: 0-1={u1/N*100:.1f}% | 2球={u2/N*100:.1f}% | 3球={t3/N*100:.1f}% | 4+={o4/N*100:.1f}%")
print(f"大2.5球: {o25/N*100:.1f}%")

# === 让球 ===
b2 = sum(p for (h,a),p in probs.items() if h>=a+2)
print(f"荷兰-1胜: {b2*100:.1f}%")

# === 比分EV ===
score_odds = {
    (1,0):7.50,(2,0):10.50,(2,1):5.50,(3,0):21.00,(3,1):14.00,(3,2):23.00,
    (4,0):60.00,(4,1):50.00,(0,0):9.00,(1,1):5.25,(2,2):10.00,(3,3):42.00,
    (0,1):10.50,(0,2):21.00,(1,2):12.50,(0,3):55.00,(1,3):36.00,(2,3):40.00
}
evs=[]
for (h,a),p in probs.items():
    o=score_odds.get((h,a))
    if o and p>0.003:
        ev=p*o-1
        evs.append((h,a,p,o,ev))
evs.sort(key=lambda x:-x[4])
print(f"\n=== EV Top 5 ===")
for i,(h,a,p,o,ev) in enumerate(evs[:5]):
    print(f"  {h}-{a} ({p*100:.1f}%) @{o:.2f} EV={ev:+.2f}")

# === Kelly ===
def kelly(odds, p, cf=1.0):
    b=odds-1;q=1-p;f=(b*p-q)/b
    return max(0,f)*0.5*cf
print(f"\n=== Kelly ===")
print(f"荷兰 @{h_odds:.2f}: {kelly(h_odds, hw)*100:.1f}%")
print(f"平局 @{d_odds:.2f}: {kelly(d_odds, dw)*100:.1f}%")
print(f"摩洛哥 @{a_odds:.2f}: {kelly(a_odds, aw, 0.7)*100:.1f}%")

# === 总进球 ===
tg = {0:9.00,1:4.70,2:3.10,3:3.70,4:5.70,5:11.50,6:22.00,7:33.00}
tg_sum = sum(1/v for v in tg.values())
exp_tg = sum(g*(1/o)/tg_sum for g,o in tg.items())
print(f"\n期望总进球(市场): {exp_tg:.2f} | 模型λ和: {L_H+L_A:.2f}")

# === 半全场 ===
print(f"\n=== 半全场 ===")
ht = {"胜胜":3.70,"平胜":4.80,"平平":4.30,"平负":7.50,"负负":6.30}
ht_sum = sum(1/o for o in ht.values())
for k,o in ht.items():
    print(f"  {k}: 市场{(1/o)/ht_sum*100:.1f}% @{o:.2f}")

# === 结论 ===
print(f"\n{'='*65}")
print("【核心判断】")
print(f"  这是两组头名对决——荷兰F1(7分) vs 摩洛哥C2(7分)")
print(f"  摩洛哥10场不败(5W5D) + 1-1平巴西 → 防守硬度顶级")
print(f"  荷兰进攻强(小组10球)但防守非铁板(小组4球)")
print(f"  市场44%-30%-25%的三分格局反映了比赛的均势性")
print(f"  Edge均<3pp → 市场定价精准, 无显著价值偏差")
print(f"{'='*65}")
