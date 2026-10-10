# -*- coding: utf-8 -*-
"""市场隐含 λ 反推 —— 定位"模型 Edge"的真实来源

方法(沿用 02_工具/match_models/切尔西vs赫尔城_敏感性网格 的口径):
  由市场胜平负去水概率反推 (λ_h, λ_a), 网格搜索最小化平方差。
  再与模型自己的 (λ_h, λ_a) 对比:
    · 若差在【净胜球结构】上 -> 是强弱判断分歧
    · 若差在【总进球】上     -> 是比赛节奏/进球量分歧(更容易是模型偏乐观)
"""
import json
import math
import os
import sys

TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '02_工具'))
sys.path.insert(0, TOOLS)
import afei_generator as G

cfg = json.load(open(os.path.join(TOOLS, 'match_configs', '町田泽维vs柏太阳神.json'),
                     encoding='utf-8'))
m = G.run_model(cfg)


def pois(k, lam):
    return lam ** k * math.exp(-lam) / math.factorial(k)


def probs_from(lam_h, lam_a, n=12):
    ph = pd = pa = 0.0
    net = {}
    tot = {}
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
            tot[h + a] = tot.get(h + a, 0) + p
    return ph, pd, pa, net, tot


def dewater(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}


mk = dewater(cfg['odds'])
target = (mk['H'], mk['D'], mk['A'])

best, best_err = None, 1e9
lh = 0.5
while lh <= 3.6:
    la = 0.2
    while la <= 3.0:
        ph, pd, pa, _, _ = probs_from(lh, la)
        err = (ph - target[0]) ** 2 + (pd - target[1]) ** 2 + (pa - target[2]) ** 2
        if err < best_err:
            best_err, best = err, (lh, la)
        la += 0.02
    lh += 0.02
mkt_h, mkt_a = best

print('=' * 92)
print('一、市场隐含 λ 反推 (由胜平负去水概率)')
print()
print('  市场胜平负去水: 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (
    mk['H'] * 100, mk['D'] * 100, mk['A'] * 100))
print('  反推结果: λ_主 = %.2f, λ_客 = %.2f, 期望总进球 = %.2f  (拟合误差 %.2e)' % (
    mkt_h, mkt_a, mkt_h + mkt_a, best_err))
ph, pd, pa, _, _ = probs_from(mkt_h, mkt_a)
print('  该 λ 复现的概率: 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (ph * 100, pd * 100, pa * 100))

print()
print('=' * 92)
print('二、模型 vs 市场: 分歧在净胜球还是总进球?')
print()
print('  %-12s %8s %8s %10s' % ('', 'λ_主', 'λ_客', '总进球'))
print('  %-12s %8.2f %8.2f %10.2f' % ('模型', m['lam_h'], m['lam_a'], m['exp_goals']))
print('  %-12s %8.2f %8.2f %10.2f' % ('市场(反推)', mkt_h, mkt_a, mkt_h + mkt_a))
print('  %-12s %+8.2f %+8.2f %+10.2f' % ('差', m['lam_h'] - mkt_h, m['lam_a'] - mkt_a,
                                       m['exp_goals'] - mkt_h - mkt_a))
print()
print('  ⚠️ 关键: 总进球上模型比市场高 %.2f 球 (%.0f%%), 净胜球差(λ主-λ客)模型 %.2f vs 市场 %.2f'
      % (m['exp_goals'] - mkt_h - mkt_a,
         (m['exp_goals'] / (mkt_h + mkt_a) - 1) * 100,
         m['lam_h'] - m['lam_a'], mkt_h - mkt_a))

print()
print('=' * 92)
print('三、用总进球盘口独立校验市场的 λ 总量 (不看胜平负, 换一个信息源)')
print()
# 总进球盘口 (2026-09-20 11:48)
tg = {0: 13.00, 1: 5.10, 2: 3.50, 3: 3.65, 4: 5.65, 5: 10.00, 6: 17.50}
inv = {k: 1 / v for k, v in tg.items()}
s = 1.0 / 27.00          # 7+ 那档
tot_inv = sum(inv.values()) + s
ptg = {k: v / tot_inv for k, v in inv.items()}
ptg['7+'] = s / tot_inv
ev = sum(k * v for k, v in ptg.items() if isinstance(k, int)) + 7.0 * ptg['7+']
print('  总进球盘口去水概率: ' + ' | '.join(
    ('%s: %.1f%%' % (k, v * 100)) for k, v in ptg.items()))
print('  => 市场隐含期望总进球 ≈ %.2f 球' % ev)
print()
print('  三个独立来源的"期望总进球":')
print('    胜平负反推  %.2f' % (mkt_h + mkt_a))
print('    总进球盘口  %.2f' % ev)
print('    模型        %.2f   <-- 高出 %.0f%%' % (
    m['exp_goals'], (m['exp_goals'] / ((mkt_h + mkt_a + ev) / 2) - 1) * 100))

print()
print('=' * 92)
print('四、结论')
print()
print('  模型与市场的分歧**主要不在"谁强", 而在"这场能进几个球"**:')
print('    · 模型 λ总量 %.2f, 市场 %.2f —— 模型把这场当成一场进球大战' % (
    m['exp_goals'], (mkt_h + mkt_a + ev) / 2))
print('    · 町田 主场 3 场只进 6 球(场均 2.0), 模型用的 2.71 是赛季均值,')
print('      而赛季均值被两场客场大胜(0:4 千叶、1:5 东京FC, 共 9 球)抬高')
print('    · λ 高 -> 主胜概率被推高 -> 造出 +20pp 的"Edge"')
print()
print('  按历史审计结论(560 场: 市场胜平负定价比例 ≈1.0, 基本有效),')
print('  这样一个 20 点的 Edge **更可能是模型偏乐观, 而不是真价值**。')
