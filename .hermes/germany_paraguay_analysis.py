# -*- coding: utf-8 -*-
import math, random

print("=" * 60)
print("GER vs PAR | 1/32决赛 | 2026-06-30 04:30")
print("=" * 60)

# ===== 市场赔率 =====
h_odds, d_odds, a_odds = 1.22, 5.00, 9.10

p_h = 1/h_odds; p_d = 1/d_odds; p_a = 1/a_odds
total = p_h + p_d + p_a
p_mkt_h = p_h / total
p_mkt_d = p_d / total
p_mkt_a = p_a / total

print("\n=== 市场隐含概率 ===")
print(f"德国胜: {p_mkt_h*100:.1f}%")
print(f"平局:   {p_mkt_d*100:.1f}%")
print(f"巴拉圭: {p_mkt_a*100:.1f}%")
print(f"水钱: {(total-1)*100:.1f}%")

# ===== 球队数据 =====
# 德国近10场: 9W0D1L, GF31 GA9, 场均3.1/0.9
# 小组赛: 10GF/3=3.33, 4GA/3=1.33
ger_xgf = 3.1 * 0.92
ger_xga = 0.9 * 1.08

# 巴拉圭近10场: 4W2D4L, GF13 GA13, 场均1.3/1.3
# 小组赛: 2GF/3=0.67, 4GA/3=1.33
par_xgf = 1.3 * 0.92
par_xga = 1.3 * 1.08

print(f"\n=== xG估算 ===")
print(f"德国 xG_f={ger_xgf:.2f} xG_a={ger_xga:.2f}")
print(f"巴拉圭 xG_f={par_xgf:.2f} xG_a={par_xga:.2f}")

# ===== 方法1: 市场λ + 淘汰赛修正 =====
l_ger_raw = 0.4 + p_mkt_h * 3.2
l_par_raw = 0.2 + p_mkt_a * 3.2

# 淘汰赛: 德国(强)×0.9, 巴拉圭(弱大巴)×0.55
# 伤停: 穆西亚拉OUT(-10%), 阿尔德雷特OUT(+3%防守弱化), 索萨OUT(微)
l_ger_mkt = l_ger_raw * 0.90 * 0.90  # KO修正 * 穆西亚拉伤
l_par_mkt = l_par_raw * 0.55 * 1.00  # KO大巴 * 索萨伤影响微

l_ger_mkt = max(0.3, min(3.5, l_ger_mkt))
l_par_mkt = max(0.1, min(2.5, l_par_mkt))

print(f"\n=== 方法1: 市场λ+修正 ===")
print(f"德国: λ_raw={l_ger_raw:.3f} -> λ_mkt={l_ger_mkt:.3f}")
print(f"巴拉圭: λ_raw={l_par_raw:.3f} -> λ_mkt={l_par_mkt:.3f}")

# ===== 方法2: xG实际数据法 =====
ger_xgf_adj = ger_xgf * 0.90 * 0.90  # KO * 穆西亚拉
par_xga_adj = par_xga * 0.75 * 1.03  # 大巴 * 阿尔德雷特伤
ger_xga_adj = ger_xga * 0.90  # KO防守
par_xgf_adj = par_xgf * 0.55 * 0.98  # KO大巴 * 索萨(微)

# 状态修正(适度)
ger_form = 0.08
par_form = 0.02

l_ger_xg = (ger_xgf_adj + par_xga_adj) / 2 + ger_form
l_par_xg = (par_xgf_adj + ger_xga_adj) / 2 + par_form

l_ger_xg = max(0.3, min(3.5, l_ger_xg))
l_par_xg = max(0.1, min(2.5, l_par_xg))

print(f"\n=== 方法2: xG法 ===")
print(f"德国: λ_xg={l_ger_xg:.3f}")
print(f"巴拉圭: λ_xg={l_par_xg:.3f}")

# ===== 综合 =====
L_GER = (l_ger_mkt + l_ger_xg) / 2
L_PAR = (l_par_mkt + l_par_xg) / 2
print(f"\n=== 综合λ ===")
print(f"德国λ: {L_GER:.3f}")
print(f"巴拉圭λ: {L_PAR:.3f}")

# ===== 泊松 =====
def poisson(lmbda, k):
    return (lmbda**k) * math.exp(-lmbda) / math.factorial(k)

probs = {}
hw = dw = aw = 0.0
for h in range(8):
    for a in range(8):
        p = poisson(L_GER, h) * poisson(L_PAR, a)
        probs[(h,a)] = p
        if h>a: hw += p
        elif h==a: dw += p
        else: aw += p

print(f"\n=== 泊松模型 ===")
print(f"德国胜: {hw*100:.1f}%")
print(f"平局:   {dw*100:.1f}%")
print(f"巴拉圭: {aw*100:.1f}%")

top = sorted(probs.items(), key=lambda x:-x[1])[:10]
print(f"\nTop 10比分:")
for (h,a),p in top:
    bar = "#" * int(p*100)
    print(f"  {h}-{a}: {p*100:5.1f}% {bar}")

# ===== Edge =====
eh = hw - p_mkt_h
ed = dw - p_mkt_d
ea = aw - p_mkt_a

def el(e):
    if e>0.10: return "强价值"
    elif e>0.06: return "强价值"
    elif e>0.03: return "中价值"
    elif e>0: return "弱价值"
    else: return "无价值"

print(f"\n=== Edge ===")
print(f"德国胜: {eh*100:+.1f}pp [{el(eh)}]")
print(f"平局:   {ed*100:+.1f}pp [{el(ed)}]")
print(f"巴拉圭: {ea*100:+.1f}pp [{el(ea)}]")
print(f"品牌修正后德国Edge: {(eh-0.03)*100:+.1f}pp")

# ===== 蒙特卡洛 =====
random.seed(42)
N=100000
mc={'h':0,'d':0,'a':0}
ms={}
for _ in range(N):
    hg=0;p=1.0;Lh=math.exp(-L_GER)
    while p>Lh:hg+=1;p*=random.random()
    hg-=1
    ag=0;p=1.0;La=math.exp(-L_PAR)
    while p>La:ag+=1;p*=random.random()
    ag-=1
    if hg>ag:mc['h']+=1
    elif hg==ag:mc['d']+=1
    else:mc['a']+=1
    ms[(hg,ag)]=ms.get((hg,ag),0)+1

print(f"\n=== MC (N={N:,}) ===")
print(f"德国胜: {mc['h']/N*100:.1f}%")
print(f"平局:   {mc['d']/N*100:.1f}%")
print(f"巴拉圭: {mc['a']/N*100:.1f}%")

# 进球
u2=sum(c for (h,a),c in ms.items() if h+a<=1)
t3=sum(c for (h,a),c in ms.items() if h+a in [2,3])
o4=sum(c for (h,a),c in ms.items() if h+a>=4)
o25=sum(c for (h,a),c in ms.items() if h+a>=3)
print(f"\n进球: 0-1={u2/N*100:.1f}% | 2-3={t3/N*100:.1f}% | 4+={o4/N*100:.1f}%")
print(f"大2.5球: {o25/N*100:.1f}%")

# 让球
b2 = sum(p for (h,a),p in probs.items() if h>=a+2)
b1 = sum(p for (h,a),p in probs.items() if h==a+1)
print(f"\n让球(-1): 德国-1={b2*100:.1f}% | 赢1球={b1*100:.1f}% | 巴+1={(1-b2)*100:.1f}%")

# Kelly
def kelly(odds, p, cf=1.0):
    b=odds-1;q=1-p
    f=(b*p-q)/b
    return max(0,f)*0.5*cf

kh=kelly(h_odds, hw)
kd=kelly(d_odds, dw)
ka=kelly(a_odds, aw, 0.7)
print(f"\n=== Kelly ===")
print(f"德国 @{h_odds:.2f}: {kh*100:.1f}%")
print(f"平局 @{d_odds:.2f}: {kd*100:.1f}%")
print(f"巴拉圭 @{a_odds:.2f}: {ka*100:.1f}%")

# 比分EV
odds_map = {
    (1,0):7.20,(2,0):5.50,(2,1):7.25,(3,0):6.80,(3,1):7.00,(3,2):28.00,
    (4,0):15.00,(4,1):14.50,(4,2):40.00,(5,0):30.00,(5,1):35.00,(5,2):60.00,
    (0,0):16.00,(1,1):10.00,(2,2):24.00,(3,3):80.00,
    (0,1):25.00,(0,2):70.00,(1,2):30.00,(0,3):200.00,(1,3):150.00,(2,3):90.00
}
evs=[]
for (h,a),p in probs.items():
    o=odds_map.get((h,a))
    if o and p>0.001:
        ev=p*o-1
        evs.append((h,a,p,o,ev))
evs.sort(key=lambda x:-x[4])
print(f"\n=== Top5 比分EV ===")
for i,(h,a,p,o,ev) in enumerate(evs[:5]):
    print(f"  {i+1}. {h}-{a} ({p*100:.1f}%) @{o:.2f} EV={ev:+.2f}")

# 盘口轨迹
print(f"\n=== 盘口轨迹 ===")
ts = [
    ("06-28 09:40", 1.27, 4.60, 8.00),
    ("06-28 16:15", 1.24, 4.90, 8.40),
    ("06-28 22:29", 1.22, 5.10, 8.80),
    ("06-29 10:07", 1.20, 5.18, 9.70),
    ("06-29 12:26", 1.19, 5.18, 10.50),
    ("06-29 14:53", 1.22, 5.00, 9.10),
]
for t,h,d,a in ts:
    imp = (1/h)/(1/h+1/d+1/a)*100
    print(f"  {t} | {h} / {d} / {a} | 德国={imp:.1f}%")

# 半全场
print(f"\n=== 半全场 ===")
ht_odds = {"胜胜":1.63,"平胜":4.10,"平平":8.10}
ht_total = sum(1/o for o in ht_odds.values())
for k,o in ht_odds.items():
    print(f"  {k}: {(1/o)/ht_total*100:.1f}%")

# 总进球
tg = {0:16.00,1:6.10,2:4.00,3:3.35,4:4.30,5:7.75,6:14.00,7:22.00}
tg_sum = sum(1/v for v in tg.values())
exp_tg = sum(g*(1/o)/tg_sum for g,o in tg.items())
print(f"\n期望总进球(市场): {exp_tg:.2f}")
print(f"模型λ和: {L_GER+L_PAR:.2f}")

# MPS
csi = 2.2; mpi = 0.1; rdi = 0.3
mps = csi - mpi + rdi
print(f"\nMPS: {mps:.1f} -> {'主强' if mps>0.8 else '均衡' if mps>-0.8 else '冷门'}")
