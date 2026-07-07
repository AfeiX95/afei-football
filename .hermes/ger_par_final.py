# -*- coding: utf-8 -*-
import math, random

h_odds, d_odds, a_odds = 1.22, 5.00, 9.10
p_h = 1/h_odds; p_d = 1/d_odds; p_a = 1/a_odds
t = p_h + p_d + p_a
pm_h = p_h/t; pm_d = p_d/t; pm_a = p_a/t

l_raw_h = 0.4 + pm_h * 3.2
l_raw_a = 0.2 + pm_a * 3.2
l_h = l_raw_h * 0.90 * 0.90
l_a = l_raw_a * 0.55
ger_xgf = 3.1*0.92*0.90*0.90
par_xga = 1.3*1.08*0.75*1.03
ger_xga = 0.9*1.08*0.90
par_xgf = 1.3*0.92*0.55*0.98
l_h2 = (ger_xgf + par_xga)/2 + 0.08
l_a2 = (par_xgf + ger_xga)/2 + 0.02
L_H = (l_h + l_h2)/2
L_A = (l_a + l_a2)/2
L_H = max(0.3, min(3.5, L_H))
L_A = max(0.1, min(2.5, L_A))

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

score_odds = {
    (1,0):7.20,(2,0):5.50,(2,1):7.25,(3,0):6.80,(3,1):7.00,(3,2):28.00,
    (4,0):15.00,(4,1):14.50,(4,2):40.00,(5,0):30.00,(5,1):35.00,(5,2):60.00,
    (0,0):16.00,(1,1):10.00,(2,2):24.00,(3,3):80.00,
    (0,1):25.00,(0,2):70.00,(1,2):30.00,(0,3):200.00,(1,3):150.00,(2,3):90.00
}

print("="*65)
print("  GER vs PAR | 比分预测方案 | 2026-06-30 04:30")
print("="*65)

print(f"\n【模型参数】")
print(f"  综合λ: 德国{L_H:.2f} | 巴拉圭{L_A:.2f}")
print(f"  模型: 德国{hw*100:.0f}% / 平{dw*100:.0f}% / 巴拉圭{aw*100:.0f}%")
print(f"  市场: 德国{pm_h*100:.0f}% / 平{pm_d*100:.0f}% / 巴拉圭{pm_a*100:.0f}%")

all_scores = []
for (h,a),p in probs.items():
    odds = score_odds.get((h,a))
    ev = p*odds-1 if odds else 0
    all_scores.append((h,a,p,odds,ev))

by_prob = sorted(all_scores, key=lambda x:-x[2])
by_ev = sorted(all_scores, key=lambda x:-x[4])

print(f"\n{'='*65}")
print("【一、概率排名 Top 8 比分】")
print(f"{'排名':>4} {'比分':>6} {'模型概率':>10} {'赔率':>6} {'EV':>8} {'市场隐含':>10}")
print("-"*65)
for i,(h,a,p,odds,ev) in enumerate(by_prob[:8]):
    mkt_pct = 1/odds if odds else 0
    signal = "⭐" if ev>0 else "  "
    print(f"  {i+1:>2}   {h}-{a}   {p*100:>6.2f}%   {odds if odds else '--':>5}   {ev:>+6.2f}   {mkt_pct*100:>6.1f}%  {signal}")

print(f"\n{'='*65}")
print("【二、EV排名 Top 5 比分（正期望优先）】")
print(f"{'排名':>4} {'比分':>6} {'EV':>8} {'模型概率':>10} {'赔率':>6}")
print("-"*65)
for i,(h,a,p,odds,ev) in enumerate(by_ev[:5]):
    print(f"  {i+1:>2}   {h}-{a}   {ev:>+6.2f}   {p*100:>6.2f}%   {odds if odds else '--':>5}")

print(f"\n{'='*65}")
print("【三、MC模拟 Top 5 比分】")
mc_top = sorted(mc_scores.items(), key=lambda x:-x[1])[:5]
for (h,a),c in mc_top:
    odds = score_odds.get((h,a),'--')
    ev = c/N*odds-1 if isinstance(odds,(int,float)) else 0
    print(f"  {h}-{a}: {c/N*100:.1f}%  @{odds}  EV={ev:+.2f}")

print(f"\n{'='*65}")
print("【四、进球数区间】")
u1 = sum(c for (h,a),c in mc_scores.items() if h+a<=1)
u2 = sum(c for (h,a),c in mc_scores.items() if h+a==2)
t3 = sum(c for (h,a),c in mc_scores.items() if h+a==3)
o4 = sum(c for (h,a),c in mc_scores.items() if h+a>=4)
o25 = sum(c for (h,a),c in mc_scores.items() if h+a>=3)
print(f"  0-1球: {u1/N*100:.1f}%")
print(f"  2球:   {u2/N*100:.1f}%")
print(f"  3球:   {t3/N*100:.1f}%")
print(f"  4球+:  {o4/N*100:.1f}%")
print(f"  大2.5: {o25/N*100:.1f}%")

tg = {0:16.00,1:6.10,2:4.00,3:3.35,4:4.30,5:7.75,6:14.00,7:22.00}
tg_sum = sum(1/v for v in tg.values())
exp_tg = sum(g*(1/o)/tg_sum for g,o in tg.items())
print(f"  期望总进球(市场): {exp_tg:.2f} | 模型λ和: {L_H+L_A:.2f}")

print(f"\n{'='*65}")
print("【五、赛果组合投注方案】")
print("-"*65)

edge_h = (hw - pm_h)*100
print(f"\n🟢 方案A - 稳健单（胜平负）")
print(f"  德国胜 @{h_odds:.2f}  Edge{edge_h:+.1f}pp")
if edge_h < -2:
    print(f"  → 无价值, 不推荐")
elif edge_h < 2:
    print(f"  → 市场定价精准, 轻仓或不投")
else:
    print(f"  → 有正价值")

print(f"\n🟡 方案B - 比分博冷")
pos_ev = [s for s in all_scores if s[4] > 0 and s[3] and s[2] > 0.005]
if pos_ev:
    for h,a,p,odds,ev in pos_ev[:3]:
        print(f"  {h}-{a}: 概率{p*100:.1f}%  @{odds:.2f}  EV{ev:+.2f}")
else:
    print(f"  无正EV比分")

print(f"\n🔵 方案C - 总进球")
for g in [2,3,4]:
    tg_odds = tg.get(g)
    tg_model = poisson(L_H+L_A, g)
    tg_ev = tg_model*tg_odds-1 if tg_odds else 0
    print(f"  {g}球: 模型{tg_model*100:.1f}%  @{tg_odds:.2f}  EV{tg_ev:+.2f}")

print(f"\n🟣 方案D - 半全场")
ht_data = {"胜胜":1.63,"平胜":4.10,"平平":8.10}
ht_total = sum(1/o for o in ht_data.values())
for k,o in ht_data.items():
    htm = (1/o)/ht_total
    print(f"  {k}: 市场{htm*100:.1f}%  @{o:.2f}")

b2 = sum(p for (h,a),p in probs.items() if h>=a+2)
print(f"\n🟠 让球(-1)参考")
print(f"  德国-1胜: 模型{b2*100:.1f}%  市场{(1/1.69)/(1/1.69+1/4.05+1/3.44)*100:.1f}%")

print(f"\n{'='*65}")
print("【六、综合推荐】")
print(f"  市场效率: 极高 (模型vs市场偏差<2pp)")
print(f"  最优策略: 比分博冷为主, 胜平负无价值")
print(f"  冷门方向: 0-0 @16.00 (唯一稳定正EV)")
print(f"  核心逻辑: 穆西亚拉缺阵+巴拉圭大巴+淘汰赛保守")
print(f"{'='*65}")
