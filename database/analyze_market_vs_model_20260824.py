# -*- coding: utf-8 -*-
"""2026-08-24 市场vs模型 复盘统计 (Batch#24 补充: 08-22~24 第一页31场)
新13场 + 上次待开奖6场验证 + C15a/C15b 累计更新
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 格式: (编号, 联赛, 主队, 让球, 客队, 胜, 平, 负, 半场, 全场)
NEW = [
    ('周日027','巴甲','桑托斯',-1,'米拉索尔', 1.66,3.45,4.22, '0:1','1:1'),
    ('周日026','美职','新英格兰',-1,'纽约城', 2.11,3.35,2.80, '1:1','1:1'),
    ('周日025','葡超','波尔图',-2,'阿罗卡', 1.15,5.70,11.80, '0:0','2:0'),
    ('周日024','西甲','埃尔切',+1,'巴萨', 8.75,5.50,1.20, '0:2','0:5'),
    ('周日023','意甲','亚特兰大',-1,'萨索洛', 1.41,4.08,5.70, '1:0','2:1'),
    ('周日022','意甲','都灵',+1,'AC米兰', 4.18,3.32,1.70, '0:0','1:2'),
    ('周日021','西甲','赫塔费',-1,'桑坦德', 2.05,2.80,3.51, '0:0','1:0'),
    ('周日020','葡超','圣克拉拉',-1,'法马利康', 2.59,2.65,2.73, '1:0','1:0'),
    ('周日019','意甲','威尼斯',-1,'莱切', 1.92,2.85,3.88, '0:0','0:2'),
    ('周日018','意甲','弗洛西诺',+1,'尤文图斯', 7.20,4.65,1.29, '0:1','0:1'),
    ('周日017','英超','纽卡斯尔',+1,'利物浦', 3.52,3.84,1.71, '1:0','2:2'),
    ('周日016','法甲','勒阿弗尔',+1,'摩纳哥', 3.48,3.35,1.84, '0:1','0:1'),
    ('周日015','西甲','马竞',-1,'比利亚雷', 1.66,3.55,4.08, '0:0','2:2'),
]
# 上次 Batch#24 待开奖 6 场 (现已开奖)
SETTLED = [
    ('周日014','荷甲','坎布尔',+2,'费耶诺德', 12.00,6.90,1.11, '0:4','2:5'),
    ('周日013','瑞超','哈马比',-1,'盖斯', 1.27,4.95,7.15, '2:0','2:0'),
    ('周日012','葡超','吉马良斯',-1,'葡国民', 1.52,3.65,5.05, '1:0','1:0'),
    ('周日011','德国杯','不伦瑞克',+1,'柏林联合', 3.40,3.40,1.85, '1:1','2:4'),
    ('周日010','法甲','昂热',+1,'里尔', 4.85,3.35,1.60, '0:2','0:2'),
    ('周日009','英超','曼城',-1,'伯恩茅斯', 1.36,4.55,5.75, '0:1','2:1'),
]

def implied(h, d, a):
    inv = [1/h, 1/d, 1/a]
    s = sum(inv)
    return [x/s for x in inv]

def parse_score(s):
    h, a = s.split(':')
    return int(h), int(a)

def analyze(matches, label):
    print(f'===== {label}: {len(matches)}场 =====')
    dir_hit = 0
    draws = 0
    over25 = 0
    h1_win = h1_lose = h1_push = 0   # 让-1方
    h2_win = h2_lose = h2_push = 0   # 让-2方
    r1_win = r1_lose = r1_push = 0   # 受让+1方
    r2_win = r2_lose = r2_push = 0   # 受让+2方
    c15a = []  # 主胜<1.50 让-1
    c15b = []  # 1.50-2.00 让-1
    for (num, lg, home, hc, away, sh, sd, sa, half, full) in matches:
        mp = implied(sh, sd, sa)
        fav = max(range(3), key=lambda i: mp[i])
        fh, fa = parse_score(full)
        res = 'H' if fh > fa else ('D' if fh == fa else 'A')
        fav_res = ['H','D','A'][fav]
        hit = res == fav_res
        dir_hit += hit
        if res == 'D': draws += 1
        if fh + fa >= 3: over25 += 1
        # 让球
        if hc < 0:  # 主队让球
            margin = fh - fa
            if hc == -1:
                if margin >= 2: h1_win += 1
                elif margin == 1: h1_push += 1
                else: h1_lose += 1
                if sh < 1.50: c15a.append((home, sh, full, '未翻' if res=='H' else '翻车'))
                elif 1.50 <= sh <= 2.00: c15b.append((home, sh, full, '未翻' if res=='H' else '翻车'))
            elif hc == -2:
                if margin >= 3: h2_win += 1
                elif margin == 2: h2_push += 1
                else: h2_lose += 1
        else:  # 主队受让
            margin = fa - fh
            if hc == 1:
                if margin == 0: r1_win += 1
                elif margin == 1: r1_push += 1
                else: r1_lose += 1
            elif hc == 2:
                if margin <= 1: r2_win += 1
                elif margin == 2: r2_push += 1
                else: r2_lose += 1
        mark = '✅' if hit else '❌'
        print(f'  {num} {home}({hc:+d})vs{away} 热门={["主","平","客"][fav]} {mp[fav]*100:.0f}% 实际{full} → {mark}')
    n = len(matches)
    print(f'  市场方向: {dir_hit}/{n} = {dir_hit/n*100:.1f}%')
    print(f'  平局: {draws}/{n} = {draws/n*100:.1f}%')
    print(f'  大球(>=3): {over25}/{n} = {over25/n*100:.1f}%')
    print(f'  让-1方: 赢{h1_win}/输{h1_lose}/走{h1_push} → 赢盘率 {h1_win}/{h1_win+h1_lose} = {h1_win/(h1_win+h1_lose)*100 if h1_win+h1_lose else 0:.1f}%')
    print(f'  让-2方: 赢{h2_win}/输{h2_lose}/走{h2_push}')
    print(f'  受让+1: 赢{r1_win}/输{r1_lose}/走{r1_push} → 赢盘率 {r1_win}/{r1_win+r1_lose} = {r1_win/(r1_win+r1_lose)*100 if r1_win+r1_lose else 0:.1f}%')
    if c15a: print(f'  C15a(<1.50让-1): ' + '; '.join(f'{h}@{o} {s} {v}' for h,o,s,v in c15a))
    if c15b: print(f'  C15b(1.50-2.00让-1): ' + '; '.join(f'{h}@{o} {s} {v}' for h,o,s,v in c15b))
    return dir_hit, n, draws, over25, c15a, c15b, h1_win, h1_lose

print()
dh1, n1, d1, o1, c15a1, c15b1, h1w1, h1l1 = analyze(NEW, '新增13场')
print()
dh2, n2, d2, o2, c15a2, c15b2, h1w2, h1l2 = analyze(SETTLED, '待开奖6场(验证)')

print()
print('===== 合计 19场 =====')
print(f'市场方向: {dh1+dh2}/{n1+n2} = {(dh1+dh2)/(n1+n2)*100:.1f}%')
print(f'平局: {d1+d2}/{n1+n2} = {(d1+d2)/(n1+n2)*100:.1f}%')
print(f'大球: {o1+o2}/{n1+n2} = {(o1+o2)/(n1+n2)*100:.1f}%')
print(f'让-1方赢盘率: {h1w1+h1w2}/{(h1w1+h1l1)+(h1w2+h1l2)}')

print()
print('===== C15a/C15b 累计更新 =====')
print(f'C15a 本批: 哈马比1.27未翻(打穿)/曼城1.36未翻(走盘) → 累计 7/19 = {7/19*100:.1f}% (前7/17=41.2%)')
print(f'C15b 本批: 马竞1.66翻/威尼斯1.92翻/吉马良斯1.52未翻 → 累计 19/37 = {19/37*100:.1f}% (前17/34=50%)')
print('净胜1球(让球走盘)场次: 亚特兰大2:1/赫塔费1:0/圣克拉拉1:0/吉马良斯1:0/曼城2:1/都灵1:2/弗洛西诺0:1/勒阿弗尔0:1 = 8场 (1球主义)')
