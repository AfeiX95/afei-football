# -*- coding: utf-8 -*-
"""大阪钢巴 vs 神户胜利 —— 口径核对与打假 (2026-09-20 周日003)

看板 特征分析 给的是【近10场】场均(大阪1.4/1.4, 神户1.5/0.9)。
本脚本逐场拆开, 还原【Regular Season】可比口径, 并用看板自己的积分榜交叉校验。
另: 本场让球线是 **+1(主队受让)** —— 与 町田vs柏(-1) 是镜像, 结构判读要按符号翻转。
"""
import io

# (日期, 赛制, 主队, 主进球, 客进球, 客队)
MATCHES = [
    # ---- 大阪钢巴 近10场 ----
    ('2026-09-15', '亚冠精英', '大阪钢巴', 4, 1, 'CAND'),
    ('2026-09-12', '日职', '大阪钢巴', 0, 2, '东京FC'),
    ('2026-09-06', '日职', '千叶市原', 2, 0, '大阪钢巴'),
    ('2026-09-02', '日职', '长崎航海', 2, 2, '大阪钢巴'),
    ('2026-08-29', '日职', '大阪钢巴', 0, 0, '广岛三箭'),
    ('2026-08-26', '日天皇杯', '大阪钢巴', 2, 0, 'Biwako Shiga'),
    ('2026-08-22', '日职', '名古屋鲸', 3, 1, '大阪钢巴'),
    ('2026-08-15', '日职', '水户蜀葵', 1, 1, '大阪钢巴'),
    ('2026-08-11', '亚冠精英', '江原FC', 0, 0, '大阪钢巴'),
    ('2026-08-07', '日职', '大阪钢巴', 4, 3, '浦和红钻'),
    # ---- 神户胜利 近10场 ----
    ('2026-09-16', '亚冠精英', '曼谷港务', 1, 2, '神户胜利'),
    ('2026-09-11', '日职', '神户胜利', 2, 1, '鹿岛鹿角'),
    ('2026-09-06', '日职', '神户胜利', 3, 1, '长崎航海'),
    ('2026-09-02', '日职', '东京绿茵', 0, 2, '神户胜利'),
    ('2026-08-29', '日职', '神户胜利', 1, 0, '大阪樱花'),
    ('2026-08-26', '日天皇杯', '神户胜利', 2, 1, 'Veroskronos Tsuno'),
    ('2026-08-22', '日职', '横滨水手', 1, 0, '神户胜利'),
    ('2026-08-15', '日职', '神户胜利', 2, 2, '东京FC'),
    ('2026-08-08', '日职', '福冈黄蜂', 0, 1, '神户胜利'),
    ('2026-06-06', '日职', '鹿岛鹿角', 2, 0, '神户胜利'),
]

RS = '2026-08-01'      # Regular Season 起点(本轮第8轮, 第1轮 08-07/08-08)


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
        if home == team:
            out.append((date, lg, 'H', hg, ag))
        elif away == team:
            out.append((date, lg, 'A', ag, hg))
    return out


def line(label, rows):
    s = stats([(r[0], r[3], r[4]) for r in rows])
    print('  %-26s %2d场 %d胜%d平%d负 | 进%2d失%2d | 场均进 %.2f 失 %.2f'
          % (label, s['n'], s['w'], s['d'], s['l'], s['gf'], s['ga'], s['gfp'], s['gap']))
    return s


for team, expect in (('大阪钢巴', '1胜3平3负 8/13'), ('神户胜利', '5胜1平1负 11/5')):
    print('=' * 100)
    print(team + '   [积分榜校验目标: ' + expect + ']')
    print()
    line('近10场(看板口径)', for_team(team))
    line('日职2026(含06-06)', for_team(team, {'日职'}))
    rs = line('Regular Season(可比口径)', for_team(team, {'日职'}, RS))
    print()
    line('  主场(RS)', [r for r in for_team(team, {'日职'}, RS) if r[2] == 'H'])
    line('  客场(RS)', [r for r in for_team(team, {'日职'}, RS) if r[2] == 'A'])
    print()
    print('  被剔除的场次:')
    for r in for_team(team):
        if r[1] != '日职' or r[0] < RS:
            print('    %s %-9s %s %d:%d' % (r[0], r[1], '主' if r[2] == 'H' else '客', r[3], r[4]))
    print()
    print('  校验: RS口径 %d胜%d平%d负 进%d失%d  <-> 积分榜 %s  %s'
          % (rs['w'], rs['d'], rs['l'], rs['gf'], rs['ga'], expect,
             '✅ 一致' if ('%d胜%d平%d负 %d/%d' % (rs['w'], rs['d'], rs['l'], rs['gf'], rs['ga'])) == expect else '❌'))
    print()

print('=' * 100)
print('打假结论')
print()
print('  大阪钢巴: 看板 1.40/1.40  ->  RS 1.14/1.86')
print('    场均进球 1.40 -> 1.14  (被高估 %.0f%%)' % ((1.40 / 1.14 - 1) * 100))
print('    场均失球 1.40 -> 1.86  (被美化 %.0f%%)' % ((1 - 1.40 / 1.86) * 100))
print('    原因: 近10场里的 3 场非联赛贡献 进6失1 —— 4:1 CAND(亚冠)、2:0 Biwako Shiga(天皇杯低级别)、0:0 江原(亚冠)')
print()
print('  神户胜利: 看板 1.50/0.90  ->  RS 1.57/0.71')
print('    场均进球 1.50 -> 1.57  (被低估 %.0f%%)' % ((1.57 / 1.50 - 1) * 100))
print('    场均失球 0.90 -> 0.71  (被**高估** %.0f%% = 真实防守更好)' % ((1 - 0.71 / 0.90) * 100))
print('    原因: 近10场里的 06-06 鹿岛2:0、09-16 亚冠1:2、天皇杯2:1 都被计入')
print()
print('  => 与上一场(町田vs柏)同一个方向: **看板把弱队抬高、把强队压低**。')
print('     本场幅度更大: 大阪失球被美化 25%, 神户失球被高估 21%。')
