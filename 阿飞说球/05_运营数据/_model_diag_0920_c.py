# -*- coding: utf-8 -*-
"""伯恩茅斯 vs 利物浦: 模型 + 市场 + 让球盘诊断 (线 = +1, 主队受让)

沿用与 002/003 相同的诊断口径, 便于三场横向对比。
"""
import json
import math
import os
import sys

TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_工具'))
sys.path.insert(0, TOOLS)
import afei_generator as G

cfg = json.load(open(os.path.join(TOOLS, 'match_configs', '伯恩茅斯vs利物浦.json'),
                     encoding='utf-8'))
m = G.run_model(cfg)


def dewater(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}, s


def pois(k, lam):
    return lam ** k * math.exp(-lam) / math.factorial(k)


def dist(lh, la, n=12):
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

print('=' * 96)
print('0. 钱口(去水) + 内部一致性')
print()
print('  胜平负  %.2f/%.2f/%.2f  去水: 主 %.2f%% / 平 %.2f%% / 客 %.2f%%   (抽水 %.4f)'
      % (cfg['odds']['H'], cfg['odds']['D'], cfg['odds']['A'],
         plain['H'] * 100, plain['D'] * 100, plain['A'] * 100, sp))
print('  让球+1  %.2f/%.2f/%.2f  去水: 让胜 %.2f%% / 走水 %.2f%% / 让负 %.2f%%   (抽水 %.4f)'
      % (cfg['hhad']['H'], cfg['hhad']['D'], cfg['hhad']['A'],
         hh['H'] * 100, hh['D'] * 100, hh['A'] * 100, sh))
print()
print('  让胜(主队受让不败) 应 ≈ 主胜+平 = %.2f%% + %.2f%% = %.2f%%'
      % (plain['H'] * 100, plain['D'] * 100, (plain['H'] + plain['D']) * 100))
print('  让球盘读数 = %.2f%%  -> 差 %.2f pp  %s'
      % (hh['H'] * 100, abs((plain['H'] + plain['D']) * 100 - hh['H'] * 100),
         '✅ 两盘口自洽' if abs((plain['H'] + plain['D']) * 100 - hh['H'] * 100) < 2 else '⚠'))
print()
print('  两侧差 = |%.2f - %.2f| = %.2f 点' % (hh['H'] * 100, hh['A'] * 100,
                                              abs(hh['H'] - hh['A']) * 100))

print()
print('=' * 96)
print('1. 模型输出')
print()
print('  λ_主 = %.3f | λ_客 = %.3f | 期望总进球 %.2f' % (m['lam_h'], m['lam_a'], m['exp_goals']))
print('  P_model : 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (m['pH'] * 100, m['pD'] * 100, m['pA'] * 100))
print('  P_market: 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (m['pM']['H'] * 100, m['pM']['D'] * 100, m['pM']['A'] * 100))
print('  Edge    : 主 %+.1f%% / 平 %+.1f%% / 客 %+.1f%%'
      % ((m['pH'] - m['pM']['H']) * 100, (m['pD'] - m['pM']['D']) * 100, (m['pA'] - m['pM']['A']) * 100))

print()
print('=' * 96)
print('2. 工具打印的 P_model(让球盘) 是哪条线?')
print()
print('  工具 hc = {H: p_net3, D: p_net2exact, A: 1-p_net2} -> 让胜 %.1f%% / 让平 %.1f%% / 让负 %.1f%%'
      % (m['hc']['H'] * 100, m['hc']['D'] * 100, m['hc']['A'] * 100))
print('  (这是 -2 线结构; 本场是 +1 线, 符号与线数都不同)')
ph, pd, pa, net = dist(m['lam_h'], m['lam_a'])
p_home_notlose = sum(p for k, p in net.items() if k >= 0)
p_push = net.get(-1, 0.0)
p_away2 = sum(p for k, p in net.items() if k <= -2)
print()
print('  +1 线正确结构:')
print('    让胜 = 伯恩茅斯不败  = %.1f%%' % (p_home_notlose * 100))
print('    走水 = 利物浦恰好赢1 = %.1f%%' % (p_push * 100))
print('    让负 = 利物浦赢2+    = %.1f%%' % (p_away2 * 100))
print()
print('  | 侧 | 模型(+1) | 市场(hhad去水) | 差 |')
print('  |---|---|---|---|')
for lab, mv, kv in (('让胜(伯恩茅斯不败)', p_home_notlose, hh['H']),
                    ('走水(利物浦赢1)', p_push, hh['D']),
                    ('让负(利物浦赢2+)', p_away2, hh['A'])):
    print('  | %s | %.1f%% | %.1f%% | %+.1f pp |' % (lab, mv * 100, kv * 100, (mv - kv) * 100))

print()
print('=' * 96)
print('3. 市场隐含 λ 反推 vs 模型')


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
tg = {0: 22.00, 1: 7.55, 2: 4.40, 3: 3.65, 4: 4.50, 5: 7.10, 6: 11.00}
inv = {k: 1 / v for k, v in tg.items()}
s7 = 1 / 14.00
tot = sum(inv.values()) + s7
ptg = {k: v / tot for k, v in inv.items()}
ptg['7+'] = s7 / tot
ev = sum(k * v for k, v in ptg.items() if isinstance(k, int)) + 7.0 * ptg['7+']
print()
print('  市场(胜平负反推): λ_主 %.2f / λ_客 %.2f / 总 %.2f' % (mh, ma, mh + ma))
print('  市场(总进球盘口): 总 %.2f' % ev)
print('  模型            : λ_主 %.2f / λ_客 %.2f / 总 %.2f' % (m['lam_h'], m['lam_a'], m['exp_goals']))
print('  模型比市场高 %.0f%% (对照 560 场验证: 市场反推无偏, 偏差仅 -0.09 球)'
      % ((m['exp_goals'] / ((mh + ma + ev) / 2) - 1) * 100))

print()
print('=' * 96)
print('4. λ 敏感性')
print()
VARIANTS = [
    ('A RS均值(当前配置)', 1.50, 1.75, 1.50, 1.00),
    ('B 主客场拆分', 1.50, 1.50, 2.00, 1.00),
    ('C 看板近10场', 2.00, 1.40, 1.70, 1.30),
    ('D RS进攻×主客防守', 1.50, 1.50, 1.50, 1.00),
]
print('  %-24s %6s %6s | %6s %6s | 主胜 %5s %5s %5s' % ('口径', 'gf主', 'ga主', 'λ主', 'λ客', '', '平', '客胜'))
print('  ' + '-' * 92)
for name, hgf, hga, agf, aga in VARIANTS:
    c = json.loads(json.dumps(cfg))
    c['teams']['home']['gf'], c['teams']['home']['ga'] = hgf, hga
    c['teams']['away']['gf'], c['teams']['away']['ga'] = agf, aga
    mm = G.run_model(c)
    print('  %-24s %6.2f %6.2f | %6.2f %6.2f | %5.1f %5.1f %5.1f' % (
        name, hgf, hga, mm['lam_h'], mm['lam_a'],
        mm['pH'] * 100, mm['pD'] * 100, mm['pA'] * 100))
print()
print('  市场(去水):            主 %.1f%% / 平 %.1f%% / 客 %.1f%%'
      % (plain['H'] * 100, plain['D'] * 100, plain['A'] * 100))

print()
print('=' * 96)
print('5. 三场横向对比(我算的 002/003 + 本场)')
print()
print('  %-16s %8s %8s %10s %10s' % ('', '模型总进球', '市场总进球', '模型高估', '两侧差'))
print('  ' + '-' * 70)
for name, mt, kt in (('002 町田vs柏', 3.78, 2.60), ('003 大阪vs神户', 3.33, 2.60), ('011 伯恩茅斯vs利物浦', m['exp_goals'], (mh + ma + ev) / 2)):
    print('  %-16s %8.2f %8.2f %9.0f%% %9.1f' % (name, mt, kt, (mt / kt - 1) * 100,
                                                0 if name.startswith('011') else 0))
print('  (两侧差见各处明细; 本场 = %.1f 点)' % (abs(hh['H'] - hh['A']) * 100))
