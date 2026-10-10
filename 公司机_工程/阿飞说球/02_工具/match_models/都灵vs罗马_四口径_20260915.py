# -*- coding: utf-8 -*-
"""周一004 都灵 vs 罗马 — 数据核查 + 四口径 + 市场反推 + 敏感性(2026-09-15 00:30)

⚠️ 本场特点: **结构判读 = 无偏向(差 0.9 点)**, 与 003(差10.4点)完全相反
   两侧几乎持平 → 按纪律"不许硬选边", 主线只能落在走水/一球区间
⚠️ 口径核查: 都灵赛季主场仅 1 场(0胜0平1负 1:2); 罗马客场仅 1 场(1胜0平0负 4:0) → 小样本
⚠️ 赛程: 罗马 09-11 刚踢欧联杯客场(费内巴切1:1), 本场间隔 4 天; 都灵 09-05 后休 9 天
⚠️ 伤停不对称: 都灵 6 人(含主力中卫萨乌尔·科克 3场3首发); 罗马 1 人(K.科内 中场3场3首发)
"""
import json
import os
import sys
from itertools import product

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, '阿飞说球', '02_工具'))
import afei_generator as G  # noqa: E402

ODDS = {'H': 5.60, 'D': 4.05, 'A': 1.42}
HH = {'H': 2.45, 'D': 3.32, 'A': 2.38}      # 都灵受让 +1
LINE = +1

pm, Sm = G.handicap_dewater(ODDS)
qm, Sq = G.handicap_dewater(HH)
print(f'市场 胜平负 {ODDS["H"]}/{ODDS["D"]}/{ODDS["A"]} → '
      f'主 {pm["H"]:.1f} / 平 {pm["D"]:.1f} / 客 {pm["A"]:.1f} (返回率 {100/Sm:.1f}%)')
print(f'市场 让球(+1) {HH["H"]}/{HH["D"]}/{HH["A"]} → '
      f'让胜 {qm["H"]:.1f} / 走水 {qm["D"]:.1f} / 让负 {qm["A"]:.1f} (返回率 {100/Sq:.1f}%)')
judge, gap = G.handicap_side(qm)
print(f'★ 结构判读: 差 {gap:.1f} 点 → {judge}   ← 与 003(差10.4点/受让方不败)完全相反')
print('赔率异动(09-12 → 09-14 13:16): 主胜 5.20→5.60(走弱) | 客胜 1.47→1.42(收紧) | '
      '让胜 2.32→2.45 | 让负 2.48→2.38')
print('半全场异动: 负负 2.15→2.12(收紧) | 平负 4.50→4.20(收紧) → 市场更看好罗马半场即领先')


def run(label, hgf, hga, agf, aga, hform, aform, hm=1.0, am=1.0):
    cfg = {'title': '周一004', 'competition': '意甲 2026/2027 第4轮',
           'draw_to_penalties': False, 'promotion': 'win', 'odds': ODDS,
           'strategy': {'home_mult': hm, 'away_mult': am, 'home_adv': 0.15,
                        'home_form': hform, 'away_form': aform},
           'teams': {'home': {'name': '都灵', 'league': '意甲', 'gf': hgf, 'ga': hga},
                     'away': {'name': '罗马', 'league': '意甲', 'gf': agf, 'ga': aga}}}
    m = G.run_model(cfg)
    pr = m['probs']
    hw = sum(p for (h, a), p in pr.items() if (h - a) + LINE > 0) * 100
    hp = sum(p for (h, a), p in pr.items() if (h - a) + LINE == 0) * 100
    hl = sum(p for (h, a), p in pr.items() if (h - a) + LINE < 0) * 100
    print(f'\n【{label}】主 {hgf:.2f}/{hga:.2f}  客 {agf:.2f}/{aga:.2f}  mult {hm}/{am}')
    print(f"  λ 主 {m['lam_h']:.3f} / 客 {m['lam_a']:.3f} → 期望总进球 {m['exp_goals']:.2f}")
    print(f"  模型 主 {m['pH']*100:.1f} / 平 {m['pD']*100:.1f} / 客 {m['pA']*100:.1f}")
    print(f"  Edge 主 {(m['pH']*100-pm['H']):+.1f} / 平 {(m['pD']*100-pm['D']):+.1f} / 客 {(m['pA']*100-pm['A']):+.1f}")
    print(f"  让球(+1) 模型 让胜 {hw:.1f} / 走水 {hp:.1f} / 让负 {hl:.1f}")
    print(f"  总进球 0-1球 {m['p_0_1']*100:.1f}% | 2-3球 {m['p_2_3']*100:.1f}% | 4+球 {m['p_4p']*100:.1f}% | 大2.5 {m['p_over25']*100:.1f}%")
    top = sorted(pr.items(), key=lambda kv: -kv[1])[:5]
    print('  TOP比分 ' + ' | '.join(f'{h}:{a} {p*100:.1f}%' for (h, a), p in top))
    return dict(label=label, lam_h=m['lam_h'], lam_a=m['lam_a'], exp=m['exp_goals'],
                pH=m['pH']*100, pD=m['pD']*100, pA=m['pA']*100, hw=hw, hp=hp, hl=hl,
                over=m['p_over25']*100)


res = []
res.append(run('A 竞彩近10场口径(1.1/0.9 vs 2.3/1.5)',
               1.1, 0.9, 2.3, 1.5, {'w': 5, 'd': 1, 'l': 4}, {'w': 5, 'd': 3, 'l': 2}))
res.append(run('B 赛季总口径(4/5/3 vs 10/1/3)',
               4/3, 5/3, 10/3, 1/3, {'w': 5, 'd': 1, 'l': 4}, {'w': 5, 'd': 3, 'l': 2}))
res.append(run('C 近10场主客分离(都灵主场5/2/3 vs 罗马客场5/3/2)',
               5/10, 3/10, 5/10, 2/10, {'w': 5, 'd': 1, 'l': 4}, {'w': 5, 'd': 3, 'l': 2}))
res.append(run('D 赛季口径+双方欧战疲劳(客mult 0.94)',
               4/3, 5/3, 10/3, 1/3, {'w': 5, 'd': 1, 'l': 4}, {'w': 5, 'd': 3, 'l': 2}, am=0.94))


def lam_from_market(mH, mD, mA):
    best, err = None, 1e9
    h = 0.3
    while h <= 3.0:
        a = 0.4
        while a <= 3.4:
            pr = {(x, y): G.poisson_pmf(x, h) * G.poisson_pmf(y, a) for x, y in product(range(8), repeat=2)}
            pH = sum(p for (x, y), p in pr.items() if x > y)
            pD = sum(p for (x, y), p in pr.items() if x == y)
            pA = sum(p for (x, y), p in pr.items() if x < y)
            e = (pH - mH) ** 2 + (pD - mD) ** 2 + (pA - mA) ** 2
            if e < err:
                err, best = e, (h, a)
            a += 0.02
        h += 0.02
    return best, err


(lh0, la0), e0 = lam_from_market(pm['H'] / 100, pm['D'] / 100, pm['A'] / 100)
print(f'\n市场反推 λ: 都灵 {lh0:.2f} / 罗马 {la0:.2f} (拟合误差 {e0:.5f})')

print('\n=== λ±10% 六场景 ===')
print(f'{"场景":22s}{"λ都":>6s}{"λ罗":>6s}{"主胜":>7s}{"平":>6s}{"客胜":>7s}{"让胜":>7s}{"走水":>7s}{"让负":>7s}{"大2.5":>7s}')
for tag, mh, ma in [('基准', 1.0, 1.0), ('都灵+10%', 1.1, 1.0), ('都灵-10%', 0.9, 1.0),
                    ('罗马+10%', 1.0, 1.1), ('罗马-10%(疲劳)', 1.0, 0.9), ('双升(开)', 1.1, 1.1)]:
    lh, la = lh0 * mh, la0 * ma
    pr = {(x, y): G.poisson_pmf(x, lh) * G.poisson_pmf(y, la) for x, y in product(range(8), repeat=2)}
    pH = sum(p for (x, y), p in pr.items() if x > y) * 100
    pD = sum(p for (x, y), p in pr.items() if x == y) * 100
    pA = sum(p for (x, y), p in pr.items() if x < y) * 100
    hw = sum(p for (x, y), p in pr.items() if (x - y) + LINE > 0) * 100
    hp = sum(p for (x, y), p in pr.items() if (x - y) + LINE == 0) * 100
    hl = sum(p for (x, y), p in pr.items() if (x - y) + LINE < 0) * 100
    ov = sum(p for (x, y), p in pr.items() if x + y > 2.5) * 100
    print(f'{tag:22s}{lh:6.2f}{la:6.2f}{pH:7.1f}{pD:6.1f}{pA:7.1f}{hw:7.1f}{hp:7.1f}{hl:7.1f}{ov:7.1f}')

print('\n' + '=' * 100)
print(f"{'口径':44s}{'λ主':>7s}{'λ客':>7s}{'期望':>7s}{'模型主/平/客':>20s}{'让胜/走/让负':>18s}")
for r in res:
    print(f"{r['label']:44s}{r['lam_h']:7.3f}{r['lam_a']:7.3f}{r['exp']:7.2f}"
          f"{r['pH']:8.1f}/{r['pD']:.1f}/{r['pA']:.1f}   {r['hw']:6.1f}/{r['hp']:.1f}/{r['hl']:.1f}")
print(f"\n市场对照: 主 {pm['H']:.1f} / 平 {pm['D']:.1f} / 客 {pm['A']:.1f} | "
      f"让球(+1) 让胜 {qm['H']:.1f} / 走水 {qm['D']:.1f} / 让负 {qm['A']:.1f}")
