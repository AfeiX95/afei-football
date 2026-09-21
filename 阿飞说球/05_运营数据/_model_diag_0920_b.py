# -*- coding: utf-8 -*-
"""大阪钢巴 vs 神户胜利: 模型 + 市场 + 让球盘结构诊断

本场让球线 = **+1(主队受让一球)**, 与 町田vs柏(-1) 是镜像。
要回答:
  Q1 工具打印的 P_model(让球盘) 是哪条线?
  Q2 +1 线的正确结构是什么?
  Q3 模型与市场的分歧在"谁强"还是"进几个球"?
"""
import json
import math
import os
import sys

TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_工具'))
sys.path.insert(0, TOOLS)
import afei_generator as G

cfg = json.load(open(os.path.join(TOOLS, 'match_configs', '大阪钢巴vs神户胜利.json'),
                     encoding='utf-8'))
m = G.run_model(cfg)


def dewater(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}, s


def pois(k, lam):
    return lam ** k * math.exp(-lam) / math.factorial(k)


def dist(lam_h, lam_a, n=12):
    ph = pd = pa = 0.0
    net = {}
    for h in range(n):
        for a in range(n):
            p = pois(h, lam_h) * pois(a, lam_a)
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
print('0. 钱口(去水)')
print()
print('  胜平负  %.2f/%.2f/%.2f  去水: 主 %.2f%% / 平 %.2f%% / 客 %.2f%%   (抽水 %.4f)'
      % (cfg['odds']['H'], cfg['odds']['D'], cfg['odds']['A'],
         plain['H'] * 100, plain['D'] * 100, plain['A'] * 100, sp))
print('  让球+1  %.2f/%.2f/%.2f  去水: 让胜 %.2f%% / 走水 %.2f%% / 让负 %.2f%%   (抽水 %.4f)'
      % (cfg['hhad']['H'], cfg['hhad']['D'], cfg['hhad']['A'],
         hh['H'] * 100, hh['D'] * 100, hh['A'] * 100, sh))
print()
print('  内部一致性交叉验证:')
print('    让胜(主队受让不败) 应 ≈ 主胜+平 = %.2f%% + %.2f%% = %.2f%%'
      % (plain['H'] * 100, plain['D'] * 100, (plain['H'] + plain['D']) * 100))
print('    让球盘读到的让胜 = %.2f%%  -> 差 %.2f pp(两个盘口独立抽水, <2pp 属正常)'
      % (hh['H'] * 100, (plain['H'] + plain['D']) * 100 - hh['H'] * 100))
print('    走水(客队恰好赢1) 应 ≈ 客胜 - 客胜2+ ; 让球盘走水 = %.2f%%' % (hh['D'] * 100))

print()
print('=' * 96)
print('1. 模型输出(λ 由 Regular Season 口径驱动)')
print()
print('  λ_主 = %.3f | λ_客 = %.3f | 期望总进球 %.2f' % (m['lam_h'], m['lam_a'], m['exp_goals']))
print('  P_model : 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (m['pH'] * 100, m['pD'] * 100, m['pA'] * 100))
print('  P_market: 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (m['pM']['H'] * 100, m['pM']['D'] * 100, m['pM']['A'] * 100))
print('  Edge    : 主 %+.1f%% / 平 %+.1f%% / 客 %+.1f%%'
      % ((m['pH'] - m['pM']['H']) * 100, (m['pD'] - m['pM']['D']) * 100, (m['pA'] - m['pM']['A']) * 100))

print()
print('=' * 96)
print('2. ⚠️ 工具打印的 P_model(让球盘) 是哪条线?')
print()
print('  p_net1=P(净胜恰好1)=%.1f%%  p_net2=P(净胜>=2)=%.1f%%  p_net2exact=P(恰好2)=%.1f%%  p_net3=P(净胜>=3)=%.1f%%'
      % (m['p_net1'] * 100, m['p_net2'] * 100, m['p_net2exact'] * 100, m['p_net3'] * 100))
print('  工具 hc = {H: p_net3, D: p_net2exact, A: 1-p_net2}  ->  让胜 %.1f%% / 让平 %.1f%% / 让负 %.1f%%'
      % (m['hc']['H'] * 100, m['hc']['D'] * 100, m['hc']['A'] * 100))
print('  这是【-2 线】(净胜≥3/恰好2/≤1)的结构 —— **与 +1 线完全无关**')
print()
ph, pd, pa, net = dist(m['lam_h'], m['lam_a'])
p_home_notlose = sum(p for k, p in net.items() if k >= 0)     # 主队不败
p_push = net.get(-1, 0.0)                                     # 客队恰好赢1
p_away2 = sum(p for k, p in net.items() if k <= -2)           # 客队赢2+
print('  +1 线正确结构(主队受让一球):')
print('    让胜 = 主队不败(赢或平) = %.1f%%' % (p_home_notlose * 100))
print('    走水 = 客队恰好赢1球    = %.1f%%' % (p_push * 100))
print('    让负 = 客队赢2球以上    = %.1f%%' % (p_away2 * 100))
print()
print('  | 侧 | 模型(+1) | 市场(hhad去水) | 差 |')
print('  |---|---|---|---|')
for lab, mv, kv in (('让胜(主队不败)', p_home_notlose, hh['H']),
                    ('走水(客恰好赢1)', p_push, hh['D']),
                    ('让负(客赢2+)', p_away2, hh['A'])):
    print('  | %s | %.1f%% | %.1f%% | %+.1f pp |' % (lab, mv * 100, kv * 100, (mv - kv) * 100))

print()
print('=' * 96)
print('3. 市场隐含 λ 反推 vs 模型')
print()

def infer(mk, step=0.02):
    best, be = None, 1e9
    lh = 0.3
    while lh <= 3.2:
        la = 0.3
        while la <= 3.2:
            a, b, c, _ = dist(lh, la)
            e = (a - mk[0]) ** 2 + (b - mk[1]) ** 2 + (c - mk[2]) ** 2
            if e < be:
                be, best = e, (lh, la)
            la += step
        lh += step
    return best


mh, ma = infer((plain['H'], plain['D'], plain['A']))
print('  市场(胜平负反推): λ_主 %.2f / λ_客 %.2f / 总 %.2f' % (mh, ma, mh + ma))
print('  模型            : λ_主 %.2f / λ_客 %.2f / 总 %.2f' % (m['lam_h'], m['lam_a'], m['exp_goals']))
print('  差              : %+.2f / %+.2f / %+.2f'
      % (m['lam_h'] - mh, m['lam_a'] - ma, m['exp_goals'] - mh - ma))

# 总进球盘口独立校验
tg = {0: 11.00, 1: 4.70, 2: 3.45, 3: 3.70, 4: 5.75, 5: 11.00, 6: 21.00}
inv = {k: 1 / v for k, v in tg.items()}
s7 = 1 / 35.00
tot = sum(inv.values()) + s7
ptg = {k: v / tot for k, v in inv.items()}
ptg['7+'] = s7 / tot
ev = sum(k * v for k, v in ptg.items() if isinstance(k, int)) + 7.0 * ptg['7+']
print()
print('  总进球盘口(09-18 09:45)隐含期望总进球 = %.2f' % ev)
print('  => 三个"期望总进球": 胜平负反推 %.2f | 总进球盘口 %.2f | 模型 %.2f'
      % (mh + ma, ev, m['exp_goals']))
print('     模型比市场高 %.0f%% (对照 560 场验证: 市场反推无偏, 偏差仅 -0.09 球)'
      % ((m['exp_goals'] / ((mh + ma + ev) / 2) - 1) * 100))

print()
print('=' * 96)
print('4. λ 敏感性(换个 gf/ga 口径会怎样)')
print()
VARIANTS = [
    ('A RS均值(当前配置)', 1.14, 1.86, 1.57, 0.71),
    ('B 主客场拆分', 1.33, 1.67, 1.00, 0.33),
    ('C 看板近10场', 1.40, 1.40, 1.50, 0.90),
    ('D RS进攻×主客防守', 1.14, 1.67, 1.57, 0.33),
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
