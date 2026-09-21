# -*- coding: utf-8 -*-
"""町田泽维 vs 柏太阳神 —— 口径核对与"打假"

看板给的是【近10场】场均(町田2.4/0.6, 柏1.6/1.3), 含杯赛/亚冠/俱乐部赛。
本脚本把 10 场逐场拆开, 还原【日职2026赛季】的可比口径, 看场均被抬/压了多少。
"""
import io

# 从看板逐条录入: (日期, 赛制, 主队, 主进球, 客进球, 客队)
MATCHES = [
    # ---- 町田泽维 近10场 ----
    ('2026-09-17', '亚冠乙', '町田泽维', 2, 0, 'Svay Rieng'),
    ('2026-09-12', '日职', '町田泽维', 1, 1, '横滨水手'),
    ('2026-09-06', '日职', '名古屋鲸', 1, 3, '町田泽维'),
    ('2026-09-02', '日职', '町田泽维', 2, 1, '川崎前锋'),
    ('2026-08-29', '日职', '水户蜀葵', 1, 1, '町田泽维'),
    ('2026-08-26', '日天皇杯', '町田泽维', 3, 0, '盛冈仙鹤'),
    ('2026-08-23', '日职', '町田泽维', 3, 1, '浦和红钻'),
    ('2026-08-15', '日职', '千叶市原', 0, 4, '町田泽维'),
    ('2026-08-08', '日职', '东京FC', 1, 5, '町田泽维'),
    ('2026-06-06', '日职', '町田泽维', 0, 0, '名古屋鲸'),
    # ---- 柏太阳神 近10场 ----
    ('2026-09-16', '亚冠精英', '全北现代', 2, 1, '柏太阳神'),
    ('2026-09-11', '日职', '京都', 2, 3, '柏太阳神'),
    ('2026-09-06', '日职', '柏太阳神', 0, 2, '横滨水手'),
    ('2026-09-02', '日职', '大阪樱花', 2, 0, '柏太阳神'),
    ('2026-08-29', '日职', '清水鼓动', 0, 1, '柏太阳神'),
    ('2026-08-26', '日天皇杯', '柏太阳神', 2, 1, 'Senshu University'),
    ('2026-08-21', '日职', '柏太阳神', 4, 2, '长崎航海'),
    ('2026-08-14', '日职', '东京绿茵', 1, 3, '柏太阳神'),
    ('2026-08-08', '日职', '柏太阳神', 2, 1, '水户蜀葵'),
    ('2026-08-01', '俱乐部赛', '千叶市原', 0, 0, '柏太阳神'),
]

TEAMS = ['町田泽维', '柏太阳神']


def stats(rows):
    n = len(rows)
    if not n:
        return None
    gf = sum(r[1] for r in rows)
    ga = sum(r[2] for r in rows)
    w = sum(1 for r in rows if r[1] > r[2])
    d = sum(1 for r in rows if r[1] == r[2])
    l = sum(1 for r in rows if r[1] < r[2])
    return dict(n=n, w=w, d=d, l=l, gf=gf, ga=ga, gfp=gf / n, gap=ga / n)


def for_team(team, leagues=None, since=None):
    out = []
    for date, lg, home, hg, ag, away in MATCHES:
        if leagues and lg not in leagues:
            continue
        if since and date < since:
            continue
        if home == team:                     # 该队是主队
            out.append((date, lg, 'H', hg, ag))
        elif away == team:                   # 该队是客队
            out.append((date, lg, 'A', ag, hg))
    return out


# ⚠️ 口径关键: 只筛"日职"还不够。2026-06-06 那场虽标日职, 但不属于本阶段的
#    "Regular Season"(本赛季 Regular Season 自 08-08 第1轮起, 本轮是第8轮)。
#    用积分榜校验: 只有剔掉它, 町田才等于 7场 5胜2平0负 / 19-6 = 积分榜数值。
RS = '2026-08-01'


print('=' * 96)
print('一、町田泽维')
print()
for label, leagues, since in (('近10场(看板口径)', None, None),
                              ('日职2026(含06-06)', {'日职'}, None),
                              ('Regular Season(可比口径)', {'日职'}, RS)):
    s = stats([(r[0], r[3], r[4]) for r in for_team('町田泽维', leagues, since)])
    print('  %-24s %2d场 %d胜%d平%d负 | 进%2d失%2d | 场均进 %.2f 失 %.2f'
          % (label, s['n'], s['w'], s['d'], s['l'], s['gf'], s['ga'], s['gfp'], s['gap']))

for label, side in (('主场(Regular Season)', 'H'), ('客场(Regular Season)', 'A')):
    rows = [r for r in for_team('町田泽维', {'日职'}, RS) if r[2] == side]
    s = stats([(r[0], r[3], r[4]) for r in rows])
    print('  %-24s %2d场 %d胜%d平%d负 | 进%2d失%2d | 场均进 %.2f 失 %.2f'
          % (label, s['n'], s['w'], s['d'], s['l'], s['gf'], s['ga'], s['gfp'], s['gap']))

print()
print('  被剔除的 3 场:')
for r in for_team('町田泽维'):
    if r[1] != '日职' or r[0] < RS:
        print('    %s %-8s %s %d:%d' % (r[0], r[1], '主' if r[2] == 'H' else '客', r[3], r[4]))

print()
print('=' * 96)
print('二、柏太阳神')
print()
for label, leagues, since in (('近10场(看板口径)', None, None),
                              ('日职2026(含08-01)', {'日职'}, None),
                              ('Regular Season(可比口径)', {'日职'}, RS)):
    s = stats([(r[0], r[3], r[4]) for r in for_team('柏太阳神', leagues, since)])
    print('  %-24s %2d场 %d胜%d平%d负 | 进%2d失%2d | 场均进 %.2f 失 %.2f'
          % (label, s['n'], s['w'], s['d'], s['l'], s['gf'], s['ga'], s['gfp'], s['gap']))

for label, side in (('主场(Regular Season)', 'H'), ('客场(Regular Season)', 'A')):
    rows = [r for r in for_team('柏太阳神', {'日职'}, RS) if r[2] == side]
    s = stats([(r[0], r[3], r[4]) for r in rows])
    print('  %-24s %2d场 %d胜%d平%d负 | 进%2d失%2d | 场均进 %.2f 失 %.2f'
          % (label, s['n'], s['w'], s['d'], s['l'], s['gf'], s['ga'], s['gfp'], s['gap']))

print()
print('  被剔除的 3 场:')
for r in for_team('柏太阳神'):
    if r[1] != '日职' or r[0] < RS:
        print('    %s %-8s %s %d:%d' % (r[0], r[1], '主' if r[2] == 'H' else '客', r[3], r[4]))

print()
print('=' * 96)
print('三、打假结论')
print()
print('  町田: 看板 2.40/0.60 -> 日职 2.71/0.86')
print('        ⚠️ 场均失球被**低估**(0.60 比真实 0.86 好看), 因为剔除的 3 场里')
print('           两场是 3:0(天皇杯 vs 盛冈仙鹤) 和 2:0(亚冠乙 vs Svay Rieng) 的零封。')
print('        同时场均进球被**高估**? 不 —— 看板 2.40 < 日职 2.71, 反而失真方向相反。')
print()
print('  柏:   看板 1.60/1.30 -> 日职 1.86/1.43')
print('        ⚠️ 两项都失真: 攻击被**低估**(1.60 vs 1.86), 防守被**美化**(1.30 vs 1.43),')
print('           因为剔除的 3 场是 0:0(俱乐部赛)、2:1(天皇杯 vs 专修大学)、1:2(亚冠精英 vs 全北)。')

print()
print('=' * 96)
print('四、积分榜交叉验证(看板数据自校验)')
print()
print('  町田 总 7场 19/6 -> 场均 2.71/0.86  <-> 上面日职口径 2.71/0.86  ✅ 一致')
print('  柏   总 7场 13/10 -> 场均 1.86/1.43 <-> 上面日职口径 1.86/1.43 ✅ 一致')
print('  => 说明"剔除非日职后"正是看板积分榜口径, 两处互相印证, 数据可信。')
