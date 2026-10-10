# -*- coding: utf-8 -*-
"""富勒姆 vs 曼联 —— 口径核对 + 打假 + 模型诊断 (2026-09-20 周日020)

线 = +1 (主队富勒姆受让一球)
"""
import io
import json
import math
import os
import sys

TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_工具'))

MATCHES = [
    # ---- 富勒姆 近10场 ----
    ('2026-09-16', '英联赛杯', '西汉姆联', 2, 3, '富勒姆'),
    ('2026-09-12', '英超', '利物浦', 0, 0, '富勒姆'),
    ('2026-09-05', '英超', '富勒姆', 2, 3, '水晶宫'),
    ('2026-08-30', '英超', '桑德兰', 1, 0, '富勒姆'),
    ('2026-08-28', '英联赛杯', '富勒姆', 3, 0, '温布尔登'),
    ('2026-08-25', '英超', '富勒姆', 2, 3, '切尔西'),
    ('2026-08-15', '俱乐部赛', '富勒姆', 1, 0, '斯图加特'),
    ('2026-08-13', '俱乐部赛', '马拉加', 2, 2, '富勒姆'),
    ('2026-08-08', '俱乐部赛', '富勒姆', 1, 2, '水晶宫'),
    ('2026-08-01', '俱乐部赛', '法伦斯', 1, 2, '富勒姆'),
    # ---- 曼联 近10场 ----
    ('2026-09-17', '英联赛杯', '曼联', 2, 3, '布赖顿'),
    ('2026-09-13', '英超', '曼联', 0, 1, '曼城'),
    ('2026-09-11', '欧冠', '曼联', 4, 0, '萨巴赫'),
    ('2026-09-06', '英超', '埃弗顿', 2, 2, '曼联'),
    ('2026-08-30', '英超', '曼联', 5, 2, '伊普斯'),
    ('2026-08-22', '英超', '赫尔城', 2, 0, '曼联'),
    ('2026-08-15', '俱乐部赛', '曼联', 2, 4, 'AC米兰'),
    ('2026-08-13', '俱乐部赛', '曼联', 1, 1, '利兹联'),
    ('2026-08-08', '俱乐部赛', '巴黎圣曼', 1, 1, '曼联'),
    ('2026-08-01', '俱乐部赛', '曼联', 2, 1, '马竞'),
]
RS = '2026-08-20'


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
    print('  %-28s %2d场 %d胜%d平%d负 | 进%2d失%2d | 场均进 %.2f 失 %.2f'
          % (label, s['n'], s['w'], s['d'], s['l'], s['gf'], s['ga'], s['gfp'], s['gap']))
    return s


print('#' * 104)
print('# 一、口径核对与打假')
print('#' * 104)
for team, expect in (('富勒姆', '0胜1平3负 4/7'), ('曼联', '1胜1平2负 7/7')):
    print('=' * 104)
    print(team + '   [积分榜校验目标: ' + expect + ']')
    print()
    line('近10场(看板口径)', for_team(team))
    rs = line('本赛季RS(可比口径)', for_team(team, {'英超'}, RS))
    print()
    line('  主场(RS)', [r for r in for_team(team, {'英超'}, RS) if r[2] == 'H'])
    line('  客场(RS)', [r for r in for_team(team, {'英超'}, RS) if r[2] == 'A'])
    print()
    print('  被剔除的场次:')
    for r in for_team(team):
        if r[1] != '英超' or r[0] < RS:
            print('    %s %-9s %s %d:%d' % (r[0], r[1], '主' if r[2] == 'H' else '客', r[3], r[4]))
    print()
    ok = ('%d胜%d平%d负 %d/%d' % (rs['w'], rs['d'], rs['l'], rs['gf'], rs['ga'])) == expect
    print('  校验: RS口径 %d胜%d平%d负 进%d失%d  <-> 积分榜 %s  %s'
          % (rs['w'], rs['d'], rs['l'], rs['gf'], rs['ga'], expect, '✅ 一致' if ok else '❌'))
    print()

print('=' * 104)
print('打假结论')
print()
print('  富勒姆: 看板 1.60/1.40  ->  RS 1.00/1.75')
print('    场均进球 1.60 -> 1.00  (被高估 %.0f%%!)  <-- 本批最大进攻失真' % ((1.60 / 1.00 - 1) * 100))
print('    场均失球 1.40 -> 1.75  (被美化 %.0f%%)' % ((1 - 1.40 / 1.75) * 100))
print('  曼联:   看板 1.90/1.70  ->  RS 1.75/1.75')
print('    场均进球 1.90 -> 1.75  (被高估 %.0f%%)' % ((1.90 / 1.75 - 1) * 100))
print('    场均失球 1.70 -> 1.75  (基本一致)')
print()
print('  ★ 富勒姆的形状(RS, 只有 4 场):')
print('     主场 2 场 0胜0平2负, 进4失6, 场均进 2.00 / 失 3.00  (2:3 切尔西、2:3 水晶宫)')
print('     客场 2 场 0胜1平1负, 进0失1, 场均进 0.00 / 失 0.50  (0:1 桑德兰、0:0 利物浦)')
print('     -> 联赛 4 个进球**全部来自主场**, 但主场两战**各丢 3 球**')

print()
print('#' * 104)
print('# 二、模型 + 市场 + 让球盘诊断')
print('#' * 104)
sys.path.insert(0, TOOLS)
import afei_generator as G

cfg = json.load(open(os.path.join(TOOLS, 'match_configs', '富勒姆vs曼联.json'), encoding='utf-8'))
m = G.run_model(cfg)


def dewater(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}, s


def pois(k, lam):
    return lam ** k * math.exp(-lam) / math.factorial(k)


def dist(lh, la, n=13):
    ph = pd = pa = 0.0
    net = {}
    for h in range(n):
        for a in range(n):
            p = pois(h, lh) * pois(a, la)
            if h > a:
                ph += p
            elif h == a:
                pd += p
            else:
                pa += p
            net[h - a] = net.get(h - a, 0) + p
    return ph, pd, pa, net


plain, sp = dewater(cfg['odds'])
hh, sh = dewater(cfg['hhad'])
print()
print('  胜平负  %.2f/%.2f/%.2f  去水: 主 %.2f%% / 平 %.2f%% / 客 %.2f%%   (抽水 %.4f)'
      % (cfg['odds']['H'], cfg['odds']['D'], cfg['odds']['A'],
         plain['H'] * 100, plain['D'] * 100, plain['A'] * 100, sp))
print('  让球+1  %.2f/%.2f/%.2f  去水: 让胜 %.2f%% / 走水 %.2f%% / 让负 %.2f%%   (抽水 %.4f)'
      % (cfg['hhad']['H'], cfg['hhad']['D'], cfg['hhad']['A'],
         hh['H'] * 100, hh['D'] * 100, hh['A'] * 100, sh))
print()
print('  让胜(富勒姆受让不败) 应 ≈ 主胜+平 = %.2f%%  vs 让球盘 %.2f%%  -> 差 %.2fpp %s'
      % ((plain['H'] + plain['D']) * 100, hh['H'] * 100,
         abs((plain['H'] + plain['D']) * 100 - hh['H'] * 100),
         '✅ 自洽' if abs((plain['H'] + plain['D']) * 100 - hh['H'] * 100) < 2 else '⚠'))
print('  两侧差 = %.2f 点' % (abs(hh['H'] - hh['A']) * 100))
print('  偏离 +1 基准(受让方 45%%): %+.1f 点' % (hh['H'] * 100 - 45))
print()
print('  模型: λ_主 %.3f / λ_客 %.3f / 总 %.2f' % (m['lam_h'], m['lam_a'], m['exp_goals']))
print('  P_model : 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (m['pH'] * 100, m['pD'] * 100, m['pA'] * 100))
print('  P_market: 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (m['pM']['H'] * 100, m['pM']['D'] * 100, m['pM']['A'] * 100))
print('  Edge    : 主 %+.1f%% / 平 %+.1f%% / 客 %+.1f%%'
      % ((m['pH'] - m['pM']['H']) * 100, (m['pD'] - m['pM']['D']) * 100, (m['pA'] - m['pM']['A']) * 100))
print()
print('  工具 hc(写死-2线) -> 让胜 %.1f%% / 让平 %.1f%% / 让负 %.1f%%'
      % (m['hc']['H'] * 100, m['hc']['D'] * 100, m['hc']['A'] * 100))
ph, pd, pa, net = dist(m['lam_h'], m['lam_a'])
p_nl = sum(p for k, p in net.items() if k >= 0)
p_push = net.get(-1, 0.0)
p_a2 = sum(p for k, p in net.items() if k <= -2)
print('  +1 线正确值     -> 让胜 %.1f%% / 走水 %.1f%% / 让负 %.1f%%'
      % (p_nl * 100, p_push * 100, p_a2 * 100))
print()
print('  | 侧 | 模型(+1) | 市场 | 差 |')
print('  |---|---|---|---|')
for lab, mv, kv in (('让胜(富勒姆不败)', p_nl, hh['H']), ('走水', p_push, hh['D']), ('让负(曼联赢2+)', p_a2, hh['A'])):
    print('  | %s | %.1f%% | %.1f%% | %+.1f pp |' % (lab, mv * 100, kv * 100, (mv - kv) * 100))


def infer(mk, step=0.02):
    best, be = None, 1e9
    lh = 0.3
    while lh <= 3.4:
        la = 0.3
        while la <= 3.4:
            a, b, c, _ = dist(lh, la)
            e = (a - mk[0]) ** 2 + (b - mk[1]) ** 2 + (c - mk[2]) ** 2
            if e < be:
                be, best = e, (lh, la)
            la += step
        lh += step
    return best


mh, ma = infer((plain['H'], plain['D'], plain['A']))
tg = {0: 20.00, 1: 6.70, 2: 4.20, 3: 3.70, 4: 4.50, 5: 7.50, 6: 12.50}
inv = {k: 1 / v for k, v in tg.items()}
s7 = 1 / 17.00
tot = sum(inv.values()) + s7
ptg = {k: v / tot for k, v in inv.items()}
ptg['7+'] = s7 / tot
ev = sum(k * v for k, v in ptg.items() if isinstance(k, int)) + 7.0 * ptg['7+']
print()
print('  市场反推 λ: %.2f / %.2f / 总 %.2f   |  总进球盘口 %.2f   |  模型 %.2f (%+.0f%%)'
      % (mh, ma, mh + ma, ev, m['exp_goals'],
         (m['exp_goals'] / ((mh + ma + ev) / 2) - 1) * 100))

print()
print('  λ 敏感性:')
VARIANTS = [('A RS均值(当前)', 1.00, 1.75, 1.75, 1.75),
            ('B 主客场拆分', 2.00, 3.00, 1.00, 2.00),
            ('C 看板近10场', 1.60, 1.40, 1.90, 1.70),
            ('D RS进攻×主客防守', 1.00, 3.00, 1.75, 2.00)]
print('  %-22s %6s %6s | %6s %6s | 主胜 %5s %5s %5s' % ('口径', 'gf主', 'ga主', 'λ主', 'λ客', '', '平', '客胜'))
for name, hgf, hga, agf, aga in VARIANTS:
    c = json.loads(json.dumps(cfg))
    c['teams']['home']['gf'], c['teams']['home']['ga'] = hgf, hga
    c['teams']['away']['gf'], c['teams']['away']['ga'] = agf, aga
    mm = G.run_model(c)
    print('  %-22s %6.2f %6.2f | %6.2f %6.2f | %5.1f %5.1f %5.1f' % (
        name, hgf, hga, mm['lam_h'], mm['lam_a'], mm['pH'] * 100, mm['pD'] * 100, mm['pA'] * 100))
print('  %-22s %6s %6s | %6.2f %6.2f | %5.1f %5.1f %5.1f' % ('市场', '—', '—', mh, ma,
                                                             plain['H'] * 100, plain['D'] * 100, plain['A'] * 100))
