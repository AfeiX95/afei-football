# -*- coding: utf-8 -*-
"""曼城 vs 桑德兰: 模型 + 市场 + 让球盘诊断 (线 = -1, 主队让球)

本场是 选场分析 的"异常 1": 主胜 75%, 但让球盘"赢够"53%, 偏离 -1 基准 +26.0 点。
"""
import json
import math
import os
import sys

TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_工具'))
sys.path.insert(0, TOOLS)
import afei_generator as G

cfg = json.load(open(os.path.join(TOOLS, 'match_configs', '曼城vs桑德兰.json'), encoding='utf-8'))
m = G.run_model(cfg)


def dewater(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}, s


def pois(k, lam):
    return lam ** k * math.exp(-lam) / math.factorial(k)


def dist(lh, la, n=14):
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
print('  让球-1  %.2f/%.2f/%.2f  去水: 让胜 %.2f%% / 走水 %.2f%% / 让负 %.2f%%   (抽水 %.4f)'
      % (cfg['hhad']['H'], cfg['hhad']['D'], cfg['hhad']['A'],
         hh['H'] * 100, hh['D'] * 100, hh['A'] * 100, sh))
print()
print('  两侧差 = |%.2f - %.2f| = %.2f 点' % (hh['H'] * 100, hh['A'] * 100, abs(hh['H'] - hh['A']) * 100))
print()
print('  ⚠️ 关键结构: 主胜 %.1f%% (本批第 2 高), 但"赢两球以上"只有 %.1f%%' % (
    plain['H'] * 100, hh['H'] * 100))
print('     对照 -1 盘历史基准(让球方 27%%): 偏离 **%+.1f 点** —— 全批 30 场里最极端' % (
    (hh['H'] * 100 - 27)))
print()
print('  ⚠️ 另注: 胜平负 与 让球盘 无法互验 —— 让胜(赢2+)不能由 主胜/平/客 推出,')
print('     需要净胜球分布。所以本场的"赢够"问题只能靠模型或比分盘回答。')

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
print('2. 工具打印的 P_model(让球盘) vs -1 线正确值')
print()
print('  工具 hc = {H: p_net3, D: p_net2exact, A: 1-p_net2} -> 让胜 %.1f%% / 让平 %.1f%% / 让负 %.1f%%'
      % (m['hc']['H'] * 100, m['hc']['D'] * 100, m['hc']['A'] * 100))
ph, pd, pa, net = dist(m['lam_h'], m['lam_a'])
p_win2 = sum(p for k, p in net.items() if k >= 2)          # 主队赢2+ = 让胜(-1)
p_push = net.get(1, 0.0)                                   # 恰好赢1 = 走水
p_lose = 1 - p_win2 - p_push                               # 平或负 = 让负
print('  -1 线正确结构(让一球):')
print('    让胜 = 曼城赢2球以上 = %.1f%%' % (p_win2 * 100))
print('    走水 = 曼城恰好赢1球 = %.1f%%' % (p_push * 100))
print('    让负 = 曼城赢不到1球 = %.1f%%' % (p_lose * 100))
print()
print('  | 侧 | 模型(-1) | 市场(hhad去水) | 差 |')
print('  |---|---|---|---|')
for lab, mv, kv in (('让胜(曼城赢2+)', p_win2, hh['H']),
                    ('走水(恰好赢1)', p_push, hh['D']),
                    ('让负(赢不到1)', p_lose, hh['A'])):
    print('  | %s | %.1f%% | %.1f%% | %+.1f pp |' % (lab, mv * 100, kv * 100, (mv - kv) * 100))

print()
print('=' * 96)
print('3. 市场隐含 λ 反推 vs 模型')


def infer(mk, step=0.02):
    best, be = None, 1e9
    lh = 0.3
    while lh <= 4.0:
        la = 0.2
        while la <= 3.0:
            a, b, c, _ = dist(lh, la)
            e = (a - mk[0]) ** 2 + (b - mk[1]) ** 2 + (c - mk[2]) ** 2
            if e < be:
                be, best = e, (lh, la)
            la += step
        lh += step
    return best


mh, ma = infer((plain['H'], plain['D'], plain['A']))
tg = {0: 18.00, 1: 6.10, 2: 4.05, 3: 3.70, 4: 4.75, 5: 8.20, 6: 13.00}
inv = {k: 1 / v for k, v in tg.items()}
s7 = 1 / 17.00
tot = sum(inv.values()) + s7
ptg = {k: v / tot for k, v in inv.items()}
ptg['7+'] = s7 / tot
ev = sum(k * v for k, v in ptg.items() if isinstance(k, int)) + 7.0 * ptg['7+']
print()
print('  市场(胜平负反推): λ_主 %.2f / λ_客 %.2f / 总 %.2f' % (mh, ma, mh + ma))
print('  市场(总进球盘口): 总 %.2f' % ev)
print('  模型            : λ_主 %.2f / λ_客 %.2f / 总 %.2f' % (m['lam_h'], m['lam_a'], m['exp_goals']))
print('  模型比市场 %+.0f%%' % ((m['exp_goals'] / ((mh + ma + ev) / 2) - 1) * 100))

# 用市场 λ 算一遍"赢2+"，看市场对这题怎么定价
ph2, pd2, pa2, net2 = dist(mh, ma)
mw2 = sum(p for k, p in net2.items() if k >= 2)
print()
print('  ★ 用市场反推的 λ 单独算"曼城赢2+" = %.1f%%  (市场让球盘读数 %.1f%%)'
      % (mw2 * 100, hh['H'] * 100))
print('     -> 两个市场的隐含净胜球结构 %s' % ('自洽 ✅' if abs(mw2 * 100 - hh['H'] * 100) < 3 else '不一致 ⚠'))

print()
print('=' * 96)
print('4. λ 敏感性')
print()
VARIANTS = [
    ('A RS均值(当前配置)', 2.00, 0.50, 0.75, 1.25),
    ('B 主客场拆分', 1.50, 0.50, 1.00, 1.50),
    ('C 看板近10场', 2.20, 0.80, 1.00, 0.70),
    ('D RS进攻×主客防守', 2.00, 0.50, 0.75, 1.50),
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
print('5. 四场横向对比')
print()
print('  %-22s %9s %9s %8s %12s' % ('场次', '模型总进球', '市场总进球', '模型高估', '模型 Edge(客)'))
print('  ' + '-' * 70)
for name, mt, kt, edge in (('002 町田vs柏', 3.78, 2.60, '+17.1pp'),
                           ('003 大阪vs神户', 3.33, 2.60, '+17.1pp'),
                           ('011 伯恩茅斯vs利物浦', 3.63, 3.13, '+1.6pp'),
                           ('012 曼城vs桑德兰', m['exp_goals'], (mh + ma + ev) / 2,
                            '%+.1fpp' % ((m['pA'] - m['pM']['A']) * 100))):
    print('  %-22s %9.2f %9.2f %7.0f%% %12s' % (name, mt, kt, (mt / kt - 1) * 100, edge))
