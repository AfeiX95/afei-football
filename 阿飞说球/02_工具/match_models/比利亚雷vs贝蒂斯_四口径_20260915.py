# -*- coding: utf-8 -*-
"""周一011 比利亚雷 vs 贝蒂斯 — 数据处理(2026-09-15 03:00)

⚠️ 本场特点:
  1. 主客分离: 比利亚雷主场1场(0胜1负2:3) / 贝蒂斯客场2场(1胜1负3:5) → 小样本
  2. ★ 赔率单向大幅移动: 主胜1.77→1.86(走弱) / 客胜3.45→3.17(收紧)
     让胜3.20→3.45(放开) / 让负1.82→1.72(收紧) → 市场在往"贝蒂斯不败"方向调
  3. 两队 09-09 都踢了欧冠: 比利亚雷客场2:3负多特 / 贝蒂斯客场3:2胜里尔
  4. 伤停对称且都是主力: 比利亚雷 Carlos Romero(后卫3场3首发); 贝蒂斯 Antony(前锋4场4首发)
  5. 贝蒂斯近10场 7胜1平2负(进18失11), 含 09-05 主场1:0 胜皇马
"""
import os
import sys
from itertools import product

ROOT = r'D:\Hermes\football'
sys.path.insert(0, os.path.join(ROOT, '阿飞说球', '02_工具'))
import afei_generator as G  # noqa: E402

ODDS = {'H': 1.86, 'D': 3.62, 'A': 3.17}
HH = {'H': 3.45, 'D': 3.87, 'A': 1.72}
LINE = -1

pm, Sm = G.handicap_dewater(ODDS)
qm, Sq = G.handicap_dewater(HH)
print(f'市场 胜平负 {ODDS["H"]}/{ODDS["D"]}/{ODDS["A"]} → '
      f'主 {pm["H"]:.1f} / 平 {pm["D"]:.1f} / 客 {pm["A"]:.1f} (返回率 {100/Sm:.1f}%)')
print(f'市场 让球(-1) {HH["H"]}/{HH["D"]}/{HH["A"]} → '
      f'让胜 {qm["H"]:.1f} / 走水 {qm["D"]:.1f} / 让负 {qm["A"]:.1f} (返回率 {100/Sq:.1f}%)')
judge, gap = G.handicap_side(qm)
print(f'★ 结构判读: 差 {gap:.1f} 点 → {judge}')
print('★ 赔率四次更新(09-12 → 09-14 13:32), 单向移动:')
print('   主胜 1.77→1.80→1.83→1.86 (走弱)')
print('   客胜 3.45→3.35→3.25→3.17 (收紧)')
print('   让胜 3.20→3.30→3.38→3.45 (放开) | 让负 1.82→1.78→1.75→1.72 (收紧)')
print('   半全场负负 6.00→6.00→5.75→5.75(收紧); 平负 8.75→8.50→8.50(收紧)')
print('总进球盘: 3球 3.60→3.50(收紧, 仍最低) | 0球 18.00→20.00(放开)')

def run(label, hgf, hga, agf, aga, hform, aform, hm=1.0, am=1.0):
    cfg = {'title': '周一011', 'competition': '西甲 2026/2027 第5轮',
           'draw_to_penalties': False, 'promotion': 'win', 'odds': ODDS,
           'strategy': {'home_mult': hm, 'away_mult': am, 'home_adv': 0.15,
                        'home_form': hform, 'away_form': aform},
           'teams': {'home': {'name': '比利亚雷', 'league': '西甲', 'gf': hgf, 'ga': hga},
                     'away': {'name': '贝蒂斯', 'league': '西甲', 'gf': agf, 'ga': aga}}}
    m = G.run_model(cfg)
    pr = m['probs']
    hw = sum(p for (h, a), p in pr.items() if (h - a) + LINE > 0) * 100
    hp = sum(p for (h, a), p in pr.items() if (h - a) + LINE == 0) * 100
    hl = sum(p for (h, a), p in pr.items() if (h - a) + LINE < 0) * 100
    print(f'\n【{label}】主 {hgf:.2f}/{hga:.2f}  客 {agf:.2f}/{aga:.2f}  mult {hm}/{am}')
    print(f"  λ 主 {m['lam_h']:.3f} / 客 {m['lam_a']:.3f} → 期望总进球 {m['exp_goals']:.2f}")
    print(f"  模型 主 {m['pH']*100:.1f} / 平 {m['pD']*100:.1f} / 客 {m['pA']*100:.1f}")
    print(f"  Edge 主 {(m['pH']*100-pm['H']):+.1f} / 平 {(m['pD']*100-pm['D']):+.1f} / 客 {(m['pA']*100-pm['A']):+.1f}")
    print(f"  让球(-1) 模型 让胜 {hw:.1f} / 走水 {hp:.1f} / 让负 {hl:.1f}")
    print(f"  总进球 0-1球 {m['p_0_1']*100:.1f}% | 2-3球 {m['p_2_3']*100:.1f}% | 4+球 {m['p_4p']*100:.1f}% | 大2.5 {m['p_over25']*100:.1f}%")
    top = sorted(pr.items(), key=lambda kv: -kv[1])[:5]
    print('  TOP比分 ' + ' | '.join(f'{h}:{a} {p*100:.1f}%' for (h, a), p in top))
    return dict(label=label, lam_h=m['lam_h'], lam_a=m['lam_a'], exp=m['exp_goals'],
                pH=m['pH']*100, pD=m['pD']*100, pA=m['pA']*100, hw=hw, hp=hp, hl=hl,
                over=m['p_over25']*100)

res = []
res.append(run('A 竞彩近10场口径(比利亚雷1.5/1.8 vs 贝蒂斯1.8/1.1)',
               1.5, 1.8, 1.8, 1.1, {'w': 3, 'd': 2, 'l': 5}, {'w': 7, 'd': 1, 'l': 2}))
res.append(run('B 赛季总口径(6/8/4 vs 5/5/4)',
               6/4, 8/4, 5/4, 5/4, {'w': 3, 'd': 2, 'l': 5}, {'w': 7, 'd': 1, 'l': 2}))
res.append(run('C 近10场主客分离(比利亚雷主场8胜0平2负 vs 贝蒂斯客场5胜1平4负)',
               8/10, 2/10, 5/10, 4/10, {'w': 3, 'd': 2, 'l': 5}, {'w': 7, 'd': 1, 'l': 2}))
res.append(run('D 赛季口径+双方欧冠后(主mult 0.96/客mult 0.96)',
               6/4, 8/4, 5/4, 5/4, {'w': 3, 'd': 2, 'l': 5}, {'w': 7, 'd': 1, 'l': 2}, hm=0.96, am=0.96))

def lam_from_market(mH, mD, mA):
    best, err = None, 1e9
    h = 0.3
    while h <= 3.2:
        a = 0.3
        while a <= 3.2:
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
print(f'\n市场反推 λ: 比利亚雷 {lh0:.2f} / 贝蒂斯 {la0:.2f} (拟合误差 {e0:.5f})')

print('\n=== λ±10% 六场景 ===')
print(f'{"场景":24s}{"λ比":>6s}{"λ贝":>6s}{"主胜":>7s}{"平":>6s}{"客胜":>7s}{"让胜":>7s}{"走水":>7s}{"让负":>7s}{"大2.5":>7s}')
for tag, mh, ma in [('基准', 1.0, 1.0), ('比利亚雷+10%', 1.1, 1.0), ('比利亚雷-10%', 0.9, 1.0),
                    ('贝蒂斯+10%', 1.0, 1.1), ('贝蒂斯-10%', 1.0, 0.9), ('双升(开)', 1.1, 1.1)]:
    lh, la = lh0 * mh, la0 * ma
    pr = {(x, y): G.poisson_pmf(x, lh) * G.poisson_pmf(y, la) for x, y in product(range(8), repeat=2)}
    pH = sum(p for (x, y), p in pr.items() if x > y) * 100
    pD = sum(p for (x, y), p in pr.items() if x == y) * 100
    pA = sum(p for (x, y), p in pr.items() if x < y) * 100
    hw = sum(p for (x, y), p in pr.items() if (x - y) + LINE > 0) * 100
    hp = sum(p for (x, y), p in pr.items() if (x - y) + LINE == 0) * 100
    hl = sum(p for (x, y), p in pr.items() if (x - y) + LINE < 0) * 100
    ov = sum(p for (x, y), p in pr.items() if x + y > 2.5) * 100
    print(f'{tag:24s}{lh:6.2f}{la:6.2f}{pH:7.1f}{pD:6.1f}{pA:7.1f}{hw:7.1f}{hp:7.1f}{hl:7.1f}{ov:7.1f}')

print('\n' + '=' * 100)
print(f"{'口径':48s}{'λ主':>7s}{'λ客':>7s}{'期望':>7s}{'模型主/平/客':>20s}{'让胜/走/让负':>18s}")
for r in res:
    print(f"{r['label']:48s}{r['lam_h']:7.3f}{r['lam_a']:7.3f}{r['exp']:7.2f}"
          f"{r['pH']:8.1f}/{r['pD']:.1f}/{r['pA']:.1f}   {r['hw']:6.1f}/{r['hp']:.1f}/{r['hl']:.1f}")
print(f"\n市场对照: 主 {pm['H']:.1f} / 平 {pm['D']:.1f} / 客 {pm['A']:.1f} | "
      f"让球(-1) 让胜 {qm['H']:.1f} / 走水 {qm['D']:.1f} / 让负 {qm['A']:.1f}")
