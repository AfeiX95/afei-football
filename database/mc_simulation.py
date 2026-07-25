"""
快速跑泊松+蒙特卡洛模型，输出核心概率/比分/大小球/敏感性。
用法：在 execute_code 中直接调用，或修改 team 数据后运行。

来自 match-model-pipeline skill，2026-06-23 会话验证。
"""
import math, random

# ====== 队伍数据（按需修改） ======
home = {'name':'主队','fifa':10,'gScored':2.0,'gConceded':0.8,'attack':80,'midfield':75,'defense':70,'morale':75,'worthScore':80}
away = {'name':'客队','fifa':40,'gScored':1.2,'gConceded':1.1,'attack':55,'midfield':52,'defense':50,'morale':65,'worthScore':25}

# ====== v3 λ估算 ======
def est(h, a):
    lh = h['gScored']*0.65 + a['gConceded']*0.25 + 0.25 + (a['fifa']-h['fifa'])/50*0.15
    la = a['gScored']*0.60 + h['gConceded']*0.25 - (a['fifa']-h['fifa'])/50*0.10
    return max(0.3,min(3.5,lh)), max(0.1,min(2.5,la))

# ====== 迭代式PMF（无阶乘溢出） ======
def pmf(k, lam):
    p = math.exp(-lam)
    for i in range(1,k+1): p *= lam/i
    return p

# ====== 泊松概率（归一化） ======
def calc(lh, la):
    mx = max(8, int(math.ceil(max(lh,la)*3)))
    w=d=l=0.0; goals={}; scores=[]; tot=0
    for h in range(mx+1):
        for a in range(mx+1):
            p = pmf(h,lh)*pmf(a,la); tot+=p
            if h>a: w+=p
            elif h==a: d+=p
            else: l+=p
            goals[min(h+a,8)]=goals.get(min(h+a,8),0)+p
            scores.append((h,a,p))
    scores.sort(key=lambda x:-x[2])
    return {'w':round(w/tot*100,1),'d':round(d/tot*100,1),'l':round(l/tot*100,1),'g':goals,'top':scores[:10]}

# ====== MC（poissonSample逆CDF） ======
def psample(lam):
    L=math.exp(-lam); k=0; p=1
    while p>L: k+=1; p*=random.random()
    return k-1

def mc(lh, la, n=200000):
    w=d=l=o25=o15=o35=0; sc={}
    for _ in range(n):
        hg, ag = psample(lh), psample(la)
        if hg>ag: w+=1
        elif hg==ag: d+=1
        else: l+=1
        t=hg+ag
        if t>=3: o25+=1
        if t>=2: o15+=1
        if t>=4: o35+=1
        k=f"{hg}-{ag}"; sc[k]=sc.get(k,0)+1
    top=sorted(sc.items(),key=lambda x:-x[1])[:10]
    return {'w':round(w/n*100,1),'d':round(d/n*100,1),'l':round(l/n*100,1),
            'o15':round(o15/n*100,1),'o25':round(o25/n*100,1),'o35':round(o35/n*100,1),
            'top':[(s,round(c/n*100,1)) for s,c in top]}

# ====== RUN ======
hl, al = est(home, away)
p = calc(hl, al)
m = mc(hl, al)

print(f"λ: {home['name']} {hl:.2f}  {away['name']} {al:.2f}")
print(f"泊松: {home['name']}胜 {p['w']}%  平 {p['d']}%  {away['name']}胜 {p['l']}%")
print(f"MC:   {home['name']}胜 {m['w']}%  平 {m['d']}%  {away['name']}胜 {m['l']}%")
print(f"大小球: 大1.5 {m['o15']}%  大2.5 {m['o25']}%  大3.5 {m['o35']}%")
print(f"零封: {home['name']} {round(math.exp(-al)*100,1)}%  {away['name']} {round(math.exp(-hl)*100,1)}%")
print(f"\n最可能比分:")
for s,c in m['top']: print(f"  {s}: {c}%")
print(f"\n敏感性 3×3:")
for dh in [-0.2,0,0.2]:
    row=[]
    for da in [-0.2,0,0.2]:
        r=calc(hl+dh,al+da)
        mark=" ★" if dh==0 and da==0 else ""
        row.append(f"{r['w']}/{r['d']}/{r['l']}{mark}")
    print(f"  λ主={hl+dh:.1f}: {' | '.join(row)}")
