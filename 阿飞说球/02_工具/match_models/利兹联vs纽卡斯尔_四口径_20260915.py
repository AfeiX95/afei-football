# -*- coding: utf-8 -*-
"""周一010 利兹联 vs 纽卡斯尔 — 数据处理(2026-09-15 03:00)

⚠️ 本场特点:
  1. 两队赛季战绩完全对称: 都是 1胜2平0负5分(利兹第11/纽卡第10), 但进失不同(3:2 vs 6:4)
  2. 主客分离: 利兹主场1场(0胜1平), 纽卡客场1场(1胜0负2:0) → 小样本
  3. 结构: 让球(-1)让胜34.4对让负44.4 → 差10.0点 → 受让方不败(与003/008同型)
  4. 利兹 09-10 英联赛杯 3:6 负切尔西(间隔5天); 纽卡 09-09 英联赛杯 1:0 胜米尔沃尔(间隔6天)
  5. 纽卡伤停4人含主力后卫 Dedić(3场3首发); 利兹3人含罗顿(2场2首发)
"""
import os
import sys
from itertools import product

ROOT = r'D:\Hermes\football'
sys.path.insert(0, os.path.join(ROOT, '阿飞说球', '02_工具'))
import afei_generator as G  # noqa: E402

ODDS = {'H': 2.17, 'D': 3.25, 'A': 2.77}
HH = {'H': 4.55, 'D': 4.00, 'A': 1.52}
LINE = -1

pm, Sm = G.handicap_dewater(ODDS)
qm, Sq = G.handicap_dewater(HH)
print(f'市场 胜平负 {ODDS["H"]}/{ODDS["D"]}/{ODDS["A"]} → '
      f'主 {pm["H"]:.1f} / 平 {pm["D"]:.1f} / 客 {pm["A"]:.1f} (返回率 {100/Sm:.1f}%)')
print(f'市场 让球(-1) {HH["H"]}/{HH["D"]}/{HH["A"]} → '
      f'让胜 {qm["H"]:.1f} / 走水 {qm["D"]:.1f} / 让负 {qm["A"]:.1f} (返回率 {100/Sq:.1f}%)')
judge, gap = G.handicap_side(qm)
print(f'★ 结构判读: 差 {gap:.1f} 点 → {judge}')
print('赔率异动(09-12 → 09-14 12:32): 主胜 2.15→2.17 | 平局 3.30→3.25 | 客胜 2.77 持平 | 让球盘未动')
print('比分盘最低: 1:1@6.75 < 2:1@7.50 < 1:2@9.00 < 1:0@9.50')
print('半全场最低: 胜胜 3.70 < 负负 4.80 < 平胜 5.50 < 平平 5.70 | 总进球3球最低3.65')

def run(label, hgf, hga, agf, aga, hform, aform, hm=1.0, am=1.0):
    cfg = {'title': '周一010', 'competition': '英超 2026/2027 第4轮',
           'draw_to_penalties': False, 'promotion': 'win', 'odds': ODDS,
           'strategy': {'home_mult': hm, 'away_mult': am, 'home_adv': 0.15,
                        'home_form': hform, 'away_form': aform},
           'teams': {'home': {'name': '利兹联', 'league': '英超', 'gf': hgf, 'ga': hga},
                     'away': {'name': '纽卡斯尔', 'league': '英超', 'gf': agf, 'ga': aga}}}
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
res.append(run('A 竞彩近10场口径(利兹1.9/1.1 vs 纽卡1.6/1.7)',
               1.9, 1.1, 1.6, 1.7, {'w': 6, 'd': 3, 'l': 1}, {'w': 4, 'd': 3, 'l': 3}))
res.append(run('B 赛季总口径(3/2/3 vs 6/4/3)',
               3/3, 2/3, 6/3, 4/3, {'w': 6, 'd': 3, 'l': 1}, {'w': 4, 'd': 3, 'l': 3}))
res.append(run('C 近10场主客分离(利兹主场1胜2平2负 vs 纽卡客场3胜2平5负)',
               1/5, 2/5, 3/10, 5/10, {'w': 6, 'd': 3, 'l': 1}, {'w': 4, 'd': 3, 'l': 3}))
res.append(run('D 赛季口径+双方杯赛后(主mult 0.96/客mult 0.96)',
               3/3, 2/3, 6/3, 4/3, {'w': 6, 'd': 3, 'l': 1}, {'w': 4, 'd': 3, 'l': 3}, hm=0.96, am=0.96))

def lam_from_market(mH, mD, mA):
    best, err = None, 1e9
    h = 0.3
    while h <= 3.0:
        a = 0.3
        while a <= 3.0:
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
print(f'\n市场反推 λ: 利兹 {lh0:.2f} / 纽卡 {la0:.2f} (拟合误差 {e0:.5f})')

print('\n=== λ±10% 六场景 ===')
print(f'{"场景":22s}{"λ利":>6s}{"λ纽":>6s}{"主胜":>7s}{"平":>6s}{"客胜":>7s}{"让胜":>7s}{"走水":>7s}{"让负":>7s}{"大2.5":>7s}')
for tag, mh, ma in [('基准', 1.0, 1.0), ('利兹+10%', 1.1, 1.0), ('利兹-10%', 0.9, 1.0),
                    ('纽卡+10%', 1.0, 1.1), ('纽卡-10%', 1.0, 0.9), ('双升(开)', 1.1, 1.1)]:
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
print(f"{'口径':46s}{'λ主':>7s}{'λ客':>7s}{'期望':>7s}{'模型主/平/客':>20s}{'让胜/走/让负':>18s}")
for r in res:
    print(f"{r['label']:46s}{r['lam_h']:7.3f}{r['lam_a']:7.3f}{r['exp']:7.2f}"
          f"{r['pH']:8.1f}/{r['pD']:.1f}/{r['pA']:.1f}   {r['hw']:6.1f}/{r['hp']:.1f}/{r['hl']:.1f}")
print(f"\n市场对照: 主 {pm['H']:.1f} / 平 {pm['D']:.1f} / 客 {pm['A']:.1f} | "
      f"让球(-1) 让胜 {qm['H']:.1f} / 走水 {qm['D']:.1f} / 让负 {qm['A']:.1f}")
