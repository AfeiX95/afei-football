# -*- coding: utf-8 -*-
# 周六005 热刺 vs 维拉 市场定价 + 泊松粗算 (临时 runner)
import math

def devig(odds):
    ps = [1/o for o in odds]
    s = sum(ps)
    return [p/s for p in ps]

print("=== 一、市场定价去水 ===")
spf = [1.82, 3.45, 3.45]
p = devig(spf)
print("胜平负 %s -> 主%.2f%% 平%.2f%% 客%.2f%%" % (spf, p[0]*100, p[1]*100, p[2]*100))
print("  主胜赔率 %.2f -> C15档位: %s" % (spf[0], "C15b(1.50-2.00)陷阱档" if 1.50<=spf[0]<=2.00 else ("C15a(<1.50)" if spf[0]<1.50 else "非C15")))

rq = [3.50, 3.60, 1.77]   # 让球-1 (主队让1球): 胜=净胜2+ / 平=净胜1 / 负=客不败
q = devig(rq)
print("让球-1(热刺让1球) %s -> 打穿(净胜2+)%.2f%% 走盘(净胜1)%.2f%% 客不败%.2f%%" % (rq, q[0]*100, q[1]*100, q[2]*100))
print("  校验: 热刺不胜(SPF平+客) = %.2f%% vs 让球-1负 %.2f%% 差 %.2fpp" % ((p[1]+p[2])*100, q[2]*100, (p[1]+p[2]-q[2])*100))

ttg = [14.00,5.50,3.75,3.70,5.00,9.00,16.00,25.00]
t = devig(ttg)
print("总进球去水: " + ", ".join("%d球%.2f%%" % (i, t[i]*100) for i in range(7)) + ", 7+%.2f%%" % (t[7]*100))
print("  小2.5 %.2f%% | 大2.5 %.2f%% | 重心 %.2f 球" % (sum(t[:3])*100, (1-sum(t[:3]))*100, sum(i*t[i] for i in range(7))+7*t[7]))

scores = {"1:0":8.50,"2:0":9.50,"2:1":7.00,"3:0":16.00,"3:1":13.00,"3:2":22.00,"4:0":36.00,"4:1":31.00,
 "4:2":50.00,"5:0":120.0,"5:1":90.00,"5:2":125.0,"胜其它":45.00,
 "0:0":14.00,"1:1":7.00,"2:2":12.00,"3:3":50.00,"平其它":300.0,
 "0:1":13.00,"0:2":22.00,"1:2":11.00,"0:3":55.00,"1:3":30.00,"2:3":35.00,"0:4":175.0,"1:4":90.00,
 "2:4":100.0,"0:5":550.0,"1:5":350.0,"2:5":350.0,"负其它":120.0}
print("  比分最低五档: " + ", ".join("%s(%.2f)" % (k,v) for k,v in sorted(scores.items(), key=lambda x:x[1])[:5]))

print()
print("=== 二、泊松粗算 (多口径) ===")
def pois(l,k): return math.exp(-l)*l**k/math.factorial(k)

def model(lh, la, name, rho=-0.05):
    m = {}
    for i in range(9):
        for j in range(9):
            m[(i,j)] = pois(lh,i)*pois(la,j)
    for (i,j) in [(0,0),(1,0),(0,1),(1,1)]:
        if (i,j)==(0,0): m[(i,j)] *= (1-rho*lh*la)
        elif (i,j)==(1,0): m[(i,j)] *= (1+rho*lh)
        elif (i,j)==(0,1): m[(i,j)] *= (1+rho*la)
        else: m[(i,j)] *= (1-rho)
    tot = sum(m.values()); m = {k:v/tot for k,v in m.items()}
    hw = sum(v for (i,j),v in m.items() if i>j)
    dr = sum(v for (i,j),v in m.items() if i==j)
    aw = sum(v for (i,j),v in m.items() if i<j)
    o25 = sum(v for (i,j),v in m.items() if i+j>=3)
    u15 = sum(v for (i,j),v in m.items() if i+j<=1)
    hh2 = sum(v for (i,j),v in m.items() if i+j>=2)
    print("%-28s λ总%.2f(主%.2f/客%.2f) 主%.1f%% 平%.1f%% 客%.1f%% | 大2.5 %.1f%% | 主净胜2+ %.1f%% | 主不败 %.1f%%"
          % (name, lh+la, lh, la, hw*100, dr*100, aw*100, o25*100,
             sum(v for (i,j),v in m.items() if i-j>=2)*100, (hw+dr)*100))
    top = sorted(m.items(), key=lambda x:-x[1])[:6]
    print("     比分Top6: " + ", ".join("%d:%d %.1f%%" % (k[0],k[1],v*100) for k,v in top))
    return m

model(1.55, 1.25, "A 近10场总量(含4场热身)")
model(0.875, 0.75, "B 英超总量(4场,0进球)")
model(1.00, 0.50, "C 英超主客场分离")
model(1.55, 1.55, "D H2H口径(场均3.1)")
model(1.25, 0.95, "E 折中(状态+伤停)")

print()
print("=== 三、H2H 近10场 ===")
h2h = [("2026-05-04","维拉",1,2,"热刺"),("2026-01-11","热刺",1,2,"维拉"),("2025-10-19","热刺",1,2,"维拉"),
 ("2025-05-17","维拉",2,0,"热刺"),("2025-02-10","维拉",2,1,"热刺"),("2024-11-03","热刺",4,1,"维拉"),
 ("2024-03-10","维拉",0,4,"热刺"),("2023-11-26","热刺",1,2,"维拉"),("2023-05-13","维拉",2,1,"热刺"),
 ("2023-01-01","热刺",0,2,"维拉")]
sw=0; dw=0; dr=0; g=0; big=0
for d,hm,hg,ag,aw_ in h2h:
    g += hg+ag
    if hg+ag>=3: big+=1
    if hg==ag: dr+=1
    elif (hg>ag and hm=="热刺") or (ag>hg and aw_=="热刺"): sw+=1
    else: dw+=1
print("热刺%d胜 %d平 %d负 | 总%d球场均%.2f | 大2.5 %d/%d=%d%%" % (sw,dr,dw,g,g/len(h2h),big,len(h2h),100*big/len(h2h)))
hah=[x for x in h2h if x[1]=="热刺"]
print("热刺主场%d场: " % len(hah) + " | ".join("%d:%d(%s)" % (x[2],x[3],"胜" if x[2]>x[3] else "负") for x in hah))
