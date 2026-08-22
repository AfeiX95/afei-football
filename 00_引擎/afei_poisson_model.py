# -*- coding: utf-8 -*-
"""
AFEI 泊松模型 v2.1 — 弗鲁米嫩塞 vs 瓦斯科达伽马
巴西杯次回合 2026-08-06 08:30 马拉卡纳
"""
import math
import random
from itertools import product

random.seed(42)

def poisson_pmf(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def poisson_cdf(k, lam):
    return sum(poisson_pmf(i, lam) for i in range(k + 1))

# ============ L0 数据输入 ============
HOME, AWAY = "弗鲁米嫩塞", "瓦斯科达伽马"
odds = {"H": 1.92, "D": 2.93, "A": 3.88}          # 欧赔 竞彩官方
odds_goals = [6.8, 3.6, 3.1, 4.3, 7.8, 18, 40, 70] # 0球..7+球

# 联赛场均 (赛季)
h_gf, h_ga = 1.43, 1.19     # 主队总场均进/失
a_gf, a_ga = 1.15, 1.55     # 客队总场均进/失
h_gf_home, h_ga_home = 1.64, 1.00   # 主队主场
a_gf_away, a_ga_away = 1.11, 1.89   # 客队客场
h_recent, a_recent = (0.83, 0.83), (0.50, 1.67)   # 近6场进/失

# ============ L0.5 战略目标判断 ============
# 巴西杯次回合,首回合0-0,无客场进球 → 主队需赢球90分钟晋级,客队目标"不输拖点球"
home_mult = 0.90    # 强势方(90分钟解决,但状态一般+平局惯性 → 0.90)
away_mult = 0.55    # 弱势方(不输/拖点球 → 0.5~0.6)
home_adv = 0.15     # 主场修正

# 状态修正(近5场: W+0.08 / D+0.02 / L-0.05, ±0.25)
# 主队近6: 1W4D1L | 客队近6: 1W1D4L
h_form = 1*0.08 + 4*0.02 - 1*0.05   # +0.11
a_form = 1*0.08 + 1*0.02 - 4*0.05   # -0.10

print("=" * 60)
print(f"【战略目标判断】巴西杯次回合(总比分0-0,无客场进球规则)")
print(f"  强势方: {HOME} 目标='90分钟解决'  xG×{home_mult}")
print(f"  弱势方: {AWAY} 目标='不输(拖点球)'  xG×{away_mult}")
print(f"  状态修正: 主{h_form:+.2f} 客{a_form:+.2f} | 主场修正 +{home_adv}")
print("=" * 60)

# ============ L1 xG → λ ============
h_xgf = h_gf * 0.92 * home_mult
a_xgf = a_gf * 0.92 * away_mult
h_xga = h_ga * 1.08
a_xga = a_ga * 1.08

lam_h = (h_xgf + a_xga) / 2 + home_adv + h_form
lam_a = (a_xgf + h_xga) / 2 + a_form

print(f"\n【xG模型】")
print(f"  xG_for: 主{h_xgf:.3f}×0.92×{home_mult}  客{a_xgf:.3f}×0.92×{away_mult}")
print(f"  xG_ag:  主{h_xga:.3f}  客{a_xga:.3f}")
print(f"  λ_home = {lam_h:.3f} | λ_away = {lam_a:.3f}")

# ============ 泊松比分矩阵 ============
MAXG = 8
probs = {}
for h, a in product(range(MAXG), repeat=2):
    probs[(h, a)] = poisson_pmf(h, lam_h) * poisson_pmf(a, lam_a)

pH = sum(p for (h, a), p in probs.items() if h > a)
pD = sum(p for (h, a), p in probs.items() if h == a)
pA = sum(p for (h, a), p in probs.items() if h < a)

# 大小球
p_over25 = sum(p for (h, a), p in probs.items() if h + a > 2.5)
p_over15 = sum(p for (h, a), p in probs.items() if h + a > 1.5)
p_over35 = sum(p for (h, a), p in probs.items() if h + a > 3.5)
exp_goals = lam_h + lam_a

# 双单
p_odd = sum(p for (h, a), p in probs.items() if (h + a) % 2 == 1)
p_even = 1 - p_odd

# 双方进球
p_btts = sum(p for (h, a), p in probs.items() if h > 0 and a > 0)

print(f"\n  P_model: 主胜{pH*100:.1f}% / 平局{pD*100:.1f}% / 客胜{pA*100:.1f}%")
print(f"  期望总进球: {exp_goals:.2f} | 大2.5球{p_over25*100:.1f}% 小2.5球{(1-p_over25)*100:.1f}%")
print(f"  大1.5球{p_over15*100:.1f}% | 大3.5球{p_over35*100:.1f}%")
print(f"  双方进球{p_btts*100:.1f}% | 单数{p_odd*100:.1f}% / 双数{p_even*100:.1f}%")

# ============ L2 市场隐含概率 ============
inv = {k: 1 / v for k, v in odds.items()}
S = sum(inv.values())
pM = {k: v / S for k, v in inv.items()}
print(f"\n【市场隐含】(去水)")
print(f"  P_market: 主胜{pM['H']*100:.1f}% / 平局{pM['D']*100:.1f}% / 客胜{pM['A']*100:.1f}%")

# ============ L3 Edge ============
model_p = {"H": pH, "D": pD, "A": pA}
print(f"\n【Edge检测】")
for k, name in [("H", "主胜"), ("D", "平局"), ("A", "客胜")]:
    e = (model_p[k] - pM[k]) * 100
    tag = "强价值(必出单)" if e > 6 else "中价值(可出单)" if e > 3 else "弱价值(观察)" if e > 0 else "无价值(放弃)"
    print(f"  {name} Edge: {e:+.1f}%  [{tag}]")

# ============ L3 比分EV ============
score_odds = {
    # 胜
    (1,0):8, (2,0):8, (2,1):20, (3,0):21, (3,1):37, (3,2):60,
    (4,0):60, (4,1):110, (4,2):150, (5,0):150, (5,1):300, (5,2):300,
    # 平
    (0,0):6.8, (1,1):5.5, (2,2):18, (3,3):90,
    # 负
    (0,1):9.25, (0,2):19, (1,2):14, (0,3):45, (1,3):45, (2,3):55,
    (0,4):175, (1,4):150, (2,4):250, (0,5):700, (1,5):550, (2,5):700,
}
evs = []
for sc, p in probs.items():
    if sc in score_odds:
        o = score_odds[sc]
        ev = p * o - 1
        evs.append((ev, sc, p, o))
evs.sort(reverse=True)
print(f"\n【比分EV】Top 6")
for ev, sc, p, o in evs[:6]:
    print(f"  {sc[0]}-{sc[1]} ({p*100:.1f}%) @{o:.2f}  EV={ev:+.2f}")

# ============ L4 Kelly ============
print(f"\n【Kelly仓位】")
for k, name in [("H", "主胜"), ("A", "客胜")]:
    o = odds[k]
    b = o - 1
    p = model_p[k]
    q = 1 - p
    f = (b * p - q) / b
    stake = f * 0.5  # 保守系数
    if stake > 0:
        print(f"  {name}@{o:.2f}: 全Kelly f*={f*100:.1f}% → 实战仓位 {stake*100:.1f}%")

# ============ 蒙特卡洛模拟 ============
N = 20000
res = {"H": 0, "D": 0, "A": 0, "over25": 0, "btss": 0}
for _ in range(N):
    gh = random.expovariate(1 / lam_h)  # 用泊松近似采样
    # 用正态近似?直接泊松采样:
# 修正:泊松采样
def poisson_sample(lam):
    L = math.exp(-lam); k = 0; p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

res = {"H": 0, "D": 0, "A": 0, "over25": 0, "btss": 0}
for _ in range(N):
    gh = poisson_sample(lam_h)
    ga = poisson_sample(lam_a)
    if gh > ga: res["H"] += 1
    elif gh == ga: res["D"] += 1
    else: res["A"] += 1
    if gh + ga > 2.5: res["over25"] += 1
    if gh > 0 and ga > 0: res["btss"] += 1

print(f"\n【蒙特卡洛 {N}次模拟】")
print(f"  主胜{res['H']/N*100:.1f}% / 平{res['D']/N*100:.1f}% / 客胜{res['A']/N*100:.1f}%")
print(f"  大2.5球{res['over25']/N*100:.1f}% | 双方进球{res['btss']/N*100:.1f}%")

# ============ 晋级概率(次回合推演) ============
# 总比分0-0。主队90分钟赢→晋级;平→点球(50/50);输→出局
promote = pH + pD * 0.5
print(f"\n【晋级推演】总比分0-0,无客场进球")
print(f"  {HOME} 90分钟晋级概率 ≈ {pH*100:.1f}% | 拖点球 {pD*100:.1f}% | 点球胜 +{pD*0.5*100:.1f}%")
print(f"  {HOME} 总晋级概率 ≈ {promote*100:.1f}% | {AWAY} ≈ {(1-promote)*100:.1f}%")
