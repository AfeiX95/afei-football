import math
from collections import Counter

xG_home = 0.85  # 卡萨皮亚
xG_away = 1.05  # 托林斯

def pp(k, lam):
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

# 泊松分布
sm = {}
wh = wd = wa = 0.0
for h in range(7):
    for a in range(7):
        p = pp(h, xG_home) * pp(a, xG_away)
        sm[(h, a)] = p
        if h > a: wh += p
        elif h == a: wd += p
        else: wa += p

ss = sorted(sm.items(), key=lambda x: -x[1])
print(f'主胜{wh*100:.1f}% 平{wd*100:.1f}% 客胜{wa*100:.1f}%')
for (h, a), p in ss[:10]:
    print(f'  {h}-{a}: {p*100:.1f}%')

# 蒙特卡洛近似
import random
random.seed(42)
hw = dr = aw = ov = 0
n = 100000
sc = Counter()
for _ in range(n):
    hg = sum(1 for _ in range(1000) if random.random() < xG_home/1000)
    ag = sum(1 for _ in range(1000) if random.random() < xG_away/1000)
    sc[(hg, ag)] += 1
    if hg > ag: hw += 1
    elif hg == ag: dr += 1
    else: aw += 1
    if hg + ag >= 3: ov += 1

print(f'\nMC: 主{hw/n*100:.1f}% 平{dr/n*100:.1f}% 客{aw/n*100:.1f}%')
print(f'大2.5:{ov/n*100:.1f}% 小2.5:{(n-ov)/n*100:.1f}%')
for (h, a), c in sc.most_common(8):
    print(f'  {h}-{a}: {c/n*100:.1f}%')

# 敏感度
print('\n敏感度:')
for xh in [0.65, 0.85, 1.05]:
    for xa in [0.85, 1.05, 1.25]:
        ph = sum(pp(h,xh)*pp(a,xa) for h in range(7) for a in range(7) if h>a)
        pd = sum(pp(h,xh)*pp(a,xa) for h in range(7) for a in range(7) if h==a)
        pa = sum(pp(h,xh)*pp(a,xa) for h in range(7) for a in range(7) if h<a)
        print(f'  ({xh},{xa}): W{ph*100:.0f}% D{pd*100:.0f}% L{pa*100:.0f}%')
