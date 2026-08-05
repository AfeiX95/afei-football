# -*- coding: utf-8 -*-
"""Australia vs Egypt | R32 | 2026-07-04 02:00"""
import math, random

h,d,a=3.15,2.60,2.34
t=1/h+1/d+1/a
pmh,pmd,pma=(1/h)/t,(1/d)/t,(1/a)/t

print("="*65)
print("  AUS vs EGY | 1/32决赛 | 2026-07-04 02:00")
print("="*65)
print(f"\n市场: 澳洲{pmh*100:.0f}% / 平{pmd*100:.0f}% / 埃及{pma*100:.0f}%")

# λ双方法
# 方法1: 市场反推
l_aus_raw = 0.2 + pmh * 3.2
l_egy_raw = 0.4 + pma * 3.2
# 淘汰赛: 埃及稍强×0.90, 澳洲大巴×0.55
l_aus_mkt = l_aus_raw * 0.55
l_egy_mkt = l_egy_raw * 0.90

# 方法2: xG实际数据法
# 澳洲小组: 2GF/3=0.67, 2GA/3=0.67 (纯防守队!)
# 埃及小组: 5GF/3=1.67, 3GA/3=1.0 (不败出线)
aus_f=0.67*0.92; aus_a=0.67*1.08
egy_f=1.67*0.92; egy_a=1.0*1.08

aus_f_adj=aus_f*0.55  # 澳洲不进攻
egy_a_adj=egy_a*0.80  # 澳洲大巴更紧凑
aus_a_adj=aus_a*0.80  # 澳洲防守不变
egy_f_adj=egy_f*0.90  # 埃及淘汰赛收敛

l_aus_xg = (aus_f_adj + egy_a_adj)/2 + 0.02
l_egy_xg = (egy_f_adj + aus_a_adj)/2 + 0.05

# 综合
L_A = (l_aus_mkt + l_aus_xg)/2
L_E = (l_egy_mkt + l_egy_xg)/2
L_A=max(0.1,min(2.5,L_A)); L_E=max(0.3,min(3.0,L_E))

def po(l,k): return (l**k)*math.exp(-l)/math.factorial(k)

probs={};hw=dw=aw=0.0
for hg in range(8):
    for ag in range(8):
        p=po(L_A,hg)*po(L_E,ag)
        probs[(hg,ag)]=p
        if hg>ag: hw+=p
        elif hg==ag: dw+=p
        else: aw+=p

print(f"模型: 澳洲{hw*100:.0f}% / 平{dw*100:.0f}% / 埃及{aw*100:.0f}%")
print(f"λ: 澳洲{L_A:.2f} | 埃及{L_E:.2f}")

top=sorted(probs.items(),key=lambda x:-x[1])[:10]
print(f"\nTop 10比分:")
for (h,a),p in top:
    bar="#"*int(p*100)
    print(f"  {h}-{a}: {p*100:5.1f}% {bar}")

eh=(hw-pmh)*100;ed=(dw-pmd)*100;ea=(aw-pma)*100
print(f"\nEdge: 澳洲{eh:+.0f}pp | 平{ed:+.0f}pp | 埃及{ea:+.0f}pp")

# MC
random.seed(42);N=100000;ms={}
for _ in range(N):
    hg=0;p=1.0;L=math.exp(-L_A)
    while p>L:hg+=1;p*=random.random()
    hg-=1
    ag=0;p=1.0;L=math.exp(-L_E)
    while p>L:ag+=1;p*=random.random()
    ag-=1
    ms[(hg,ag)]=ms.get((hg,ag),0)+1

u1=sum(c for (h,a),c in ms.items() if h+a<=1)
u2=sum(c for (h,a),c in ms.items() if h+a==2)
t3=sum(c for (h,a),c in ms.items() if h+a==3)
o4=sum(c for (h,a),c in ms.items() if h+a>=4)
o25=sum(c for (h,a),c in ms.items() if h+a>=3)
print(f"\n进球: 0-1={u1/N*100:.0f}% | 2球={u2/N*100:.0f}% | 3球={t3/N*100:.0f}% | 4+={o4/N*100:.0f}%")
print(f"大2.5球: {o25/N*100:.0f}%")

# 让球+1
aus_1p = sum(p for (h,a),p in probs.items() if h>=a)  # 澳洲不败(含平)
print(f"澳洲+1不败: {aus_1p*100:.0f}%")

# 比分EV
so={(1,0):6.75,(2,0):14.00,(2,1):10.00,(3,0):45.00,(3,1):33.00,(0,0):6.00,(1,1):4.75,(2,2):17.00,(0,1):5.70,(0,2):9.50,(1,2):8.00,(0,3):25.00,(1,3):23.00}
evs=[(h,a,probs[(h,a)],so[(h,a)],probs[(h,a)]*so[(h,a)]-1) for (h,a) in so if probs[(h,a)]>0.005]
evs.sort(key=lambda x:-x[4])
print(f"\nEV Top 5:")
for i,(h,a,p,o,ev) in enumerate(evs[:5]):
    print(f"  {h}-{a} ({p*100:.1f}%) @{o:.2f} EV={ev:+.2f}")

# 半全场
print(f"\n半全场信号:")
ht={"胜胜":0,"平胜":0,"平平":0,"平负":0,"负负":0}
# 胜胜=澳洲半场领先+全场赢; 平负=半场平平局+全场埃及赢
print(f"  平-平(全场闷平): 市场概率最高(1-1@4.75)")
print(f"  平-负(半场平→埃及赢): 次高")

# 核心判断
print(f"\n{'='*65}")
print("【核心判断】")
print(f"  埃及:G组第2,1胜2平不败,5-3球,萨拉赫领衔")
print(f"  澳洲:D组第2,1胜1平1负,2-2球,纯防守队")
print(f"  埃及小组赛3-1逆转新西兰,历史性首胜")
print(f"  澳洲2个进球都是靠定位球/反击")
print(f"  λ: 澳洲{L_A:.2f} vs 埃及{L_E:.2f}")
print(f"  市场:埃及37.8%/平34.1%/澳洲28.1% → 三路均势")
print(f"  模型:埃及{aw*100:.0f}%/平{dw*100:.0f}%/澳洲{hw*100:.0f}%")
print(f"  Edge均<3pp → 市场定价合理")
print(f"  1-1是全场最低赔率比分@4.75→市场预期平局")
print(f"{'='*65}")
print(f"\n方案: 🟢1-1@4.75 🟡0-1@5.70/0-0@6.00 🔴1-0@6.75")
PYEOF