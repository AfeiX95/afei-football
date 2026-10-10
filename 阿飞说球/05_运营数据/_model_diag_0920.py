# -*- coding: utf-8 -*-
"""町田泽维 vs 柏太阳神: 模型口径诊断 + 敏感性

要回答三件事:
  Q1 打印的 P_model(让球盘) 到底是哪条线的结构?
  Q2 Edge校准(让球盘) 拿什么市场概率做基准?
  Q3 λ 对 gf/ga 口径选择有多敏感? (赛季均值 vs 主客场拆分)
"""
import json
import math
import os
import sys

TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_工具'))
sys.path.insert(0, TOOLS)
import afei_generator as G

CFG = os.path.join(TOOLS, 'match_configs', '町田泽维vs柏太阳神.json')
cfg = json.load(open(CFG, encoding='utf-8'))
m = G.run_model(cfg)


def dewater(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}, s


print('=' * 92)
print('Q1  打印的 P_model(让球盘) 是哪条线?')
print()
print('  模型净胜球分布:')
print('    p_net1   = P(净胜恰好1) = %.1f%%' % (m['p_net1'] * 100))
print('    p_net2   = P(净胜≥2)    = %.1f%%' % (m['p_net2'] * 100))
print('    p_net2exact = P(恰好2)  = %.1f%%' % (m['p_net2exact'] * 100))
print('    p_net3   = P(净胜≥3)    = %.1f%%' % (m['p_net3'] * 100))
print()
print('  代码里 hc = {H: p_net3, D: p_net2exact, A: 1-p_net2}')
print('    -> H=净胜≥3 / D=恰好净胜2 / A=净胜≤1')
print('    -> 这正是【-2 线】的结构(让两球: 赢3+算赢盘, 恰好赢2走水, 其余输盘)')
print('  本场 handicap_line = %s' % cfg['handicap_line'])
print()
print('  按 -2 线打印 = 让胜 %.1f%% / 让平 %.1f%% / 让负 %.1f%%' % (
    m['hc']['H'] * 100, m['hc']['D'] * 100, m['hc']['A'] * 100))
print('  ⚠️ 但本场是 -1 线, 正确结构应是:')
h1, d1, a1 = m['p_net2'], m['p_net1'], 1 - m['p_net2'] - m['p_net1']
print('      让胜=P(净胜≥2)=%.1f%% / 走水=P(恰好1)=%.1f%% / 让负=P(净胜≤0)=%.1f%%' % (
    h1 * 100, d1 * 100, a1 * 100))
print()
print('  => 打印值(22.3/18.1/59.6)与 -1 线正确值(%.1f/%.1f/%.1f)差得很远。' % (
    h1 * 100, d1 * 100, a1 * 100))

print()
print('=' * 92)
print('Q2  Edge校准(让球盘) 的基准市场是哪个?')
print()
plain, sp = dewater(cfg['odds'])
hh, sh = dewater(cfg['hhad'])
print('  配置 odds (胜平负) 去水: 主%.1f%% / 平%.1f%% / 客%.1f%%   (抽水 %.4f)' % (
    plain['H'] * 100, plain['D'] * 100, plain['A'] * 100, sp))
print('  配置 hhad (让球-1) 去水: 让胜%.1f%% / 走水%.1f%% / 让负%.1f%%   (抽水 %.4f)' % (
    hh['H'] * 100, hh['D'] * 100, hh['A'] * 100, sh))
print()
print('  代码: Edge校准(让球盘) = hc[...] - m["pM_cal"][...]')
print('  而 pM_cal 由 cfg["odds"](胜平负, 非让球) 构建 -> %.1f/%.1f/%.1f' % (
    m['pM_cal']['H'] * 100, m['pM_cal']['D'] * 100, m['pM_cal']['A'] * 100))
print()
print('  ⚠️ 所以那一行是: 模型的【让球盘】结构 减去 市场的【胜平负】概率 —— 口径错配。')
print('     (与 2026-09-10 修掉的"让球后结果 x 胜平负赔率"是同一类错误)')
print()
print('  正确对比(都用 -1 线):')
print('    | 侧 | 模型(-1) | 市场(hhad去水) | 差 |')
print('    |---|---|---|---|')
for lab, mv, kv in (('让胜(主队赢2+)', h1, hh['H']), ('走水(主队恰好赢1)', d1, hh['D']),
                    ('让负(主队赢不到1)', a1, hh['A'])):
    print('    | %s | %.1f%% | %.1f%% | %+.1f pp |' % (lab, mv * 100, kv * 100, (mv - kv) * 100))

print()
print('=' * 92)
print('Q3  λ 对 gf/ga 口径的敏感性')
print()
VARIANTS = [
    ('A 赛季均值(当前配置)', 2.71, 0.86, 1.86, 1.43),
    ('B 主客场拆分', 2.00, 1.00, 1.75, 1.25),
    ('C 看板近10场', 2.40, 0.60, 1.60, 1.30),
    ('D 赛季进攻x主客防守均值', 2.71, 1.00, 1.86, 1.25),
]
print('  %-26s %7s %7s %8s | %6s %6s | 主胜%% %5s %5s' % (
    '口径', 'gf主', 'ga主', 'gf客/ga客', 'λ主', 'λ客', '平', '客胜'))
print('  ' + '-' * 92)
for name, hgf, hga, agf, aga in VARIANTS:
    c = json.loads(json.dumps(cfg))
    c['teams']['home']['gf'], c['teams']['home']['ga'] = hgf, hga
    c['teams']['away']['gf'], c['teams']['away']['ga'] = agf, aga
    mm = G.run_model(c)
    print('  %-26s %7.2f %7.2f  %5.2f/%.2f | %6.2f %6.2f | %5.1f %5.1f %5.1f' % (
        name, hgf, hga, agf, aga, mm['lam_h'], mm['lam_a'],
        mm['pH'] * 100, mm['pD'] * 100, mm['pA'] * 100))
print()
print('  市场(去水): 主%.1f%% / 平%.1f%% / 客%.1f%%' % (
    plain['H'] * 100, plain['D'] * 100, plain['A'] * 100))
