# -*- coding: utf-8 -*-
"""周六029 桑德兰 vs 阿森纳 — 英超第4轮 2026-09-13 03:00
用户提供竞彩页完整数据(含伤停/赛程/赔率三次变动) → 四口径 + 市场反推 + 敏感性
"""
import json
import os
import sys
from itertools import product

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, '阿飞说球', '02_工具'))
import afei_generator as G  # noqa: E402

ODDS = {'H': 6.80, 'D': 4.05, 'A': 1.36}
HH = {'H': 2.57, 'D': 3.45, 'A': 2.22}   # 桑德兰受让 +1
LINE = +1


def dw(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s * 100 for k, v in inv.items()}, s


pm, S = dw(ODDS)
qm, Sq = dw(HH)
print(f"市场 胜平负 {ODDS['H']}/{ODDS['D']}/{ODDS['A']} → 主 {pm['H']:.1f} / 平 {pm['D']:.1f} / 客 {pm['A']:.1f} (返回率{100/S:.1f}%)")
print(f"市场 让球(+1) {HH['H']}/{HH['D']}/{HH['A']} → 让胜 {qm['H']:.1f} / 走水 {qm['D']:.1f} / 让负 {qm['A']:.1f} (返回率{100/Sq:.1f}%)")

# 赔率异动
print("\n赔率异动(09-11 → 09-12 12:20):")
print("  主胜 6.30 → 6.50 → 6.80 → 6.80 (走弱)")
print("  平局 3.90 → 3.98 → 4.05 → 4.05")
print("  客胜 1.40 → 1.38 → 1.36 → 1.36 (收紧)")
print("  让球 2.50/3.35/2.32 → 2.62/3.38/2.22 → 2.57/3.45/2.22")


def run(label, hgf, hga, agf, aga, hform, aform, hm=1.0, am=1.0):
    cfg = {'title': '周六029', 'competition': '英超 2026/2027 第4轮',
           'draw_to_penalties': False, 'promotion': 'win', 'odds': ODDS,
           'strategy': {'home_mult': hm, 'away_mult': am, 'home_adv': 0.15,
                        'home_form': hform, 'away_form': aform},
           'teams': {'home': {'name': '桑德兰', 'league': '英超', 'gf': hgf, 'ga': hga},
                     'away': {'name': '阿森纳', 'league': '英超', 'gf': agf, 'ga': aga}}}
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
    print(f"  净胜球(主视角) 恰1球负 {m['p_net1']*100:.1f}% | 客净胜2+ {sum(p for (h,a),p in pr.items() if a-h>=2)*100:.1f}%")
    top = sorted(pr.items(), key=lambda kv: -kv[1])[:6]
    print('  TOP比分 ' + ' | '.join(f'{h}:{a} {p*100:.1f}%' for (h, a), p in top))
    return dict(label=label, lam_h=m['lam_h'], lam_a=m['lam_a'], exp=m['exp_goals'],
                pH=m['pH']*100, pD=m['pD']*100, pA=m['pA']*100, hw=hw, hp=hp, hl=hl,
                over=m['p_over25']*100, p01=m['p_0_1']*100, p23=m['p_2_3']*100, p4=m['p_4p']*100,
                n1=m['p_net1']*100, a2=sum(p for (h,a),p in pr.items() if a-h>=2)*100)


res = []
res.append(run('A 竞彩近10场口径(1.6/1.0 vs 1.9/1.0)',
               1.6, 1.0, 1.9, 1.0, {'w': 6, 'd': 1, 'l': 3}, {'w': 6, 'd': 2, 'l': 2}))
res.append(run('B 赛季总口径(3/3/3 vs 6/1/3)',
               3/3, 3/3, 6/3, 1/3, {'w': 6, 'd': 1, 'l': 3}, {'w': 6, 'd': 2, 'l': 2}))
res.append(run('C 主客分离(桑德兰主场1/0/1 vs 阿森纳客场1/0/1)',
               1/1, 0/1, 1/1, 0/1, {'w': 6, 'd': 1, 'l': 3}, {'w': 6, 'd': 2, 'l': 2}))
res.append(run('D 主客分离+阿森纳跨赛事疲劳(客mult 0.94)',
               1/1, 0/1, 1/1, 0/1, {'w': 6, 'd': 1, 'l': 3}, {'w': 6, 'd': 2, 'l': 2}, am=0.94))

# 市场反推 λ
def lam_from_market(mH, mD, mA):
    best, best_err = None, 1e9
    h = 0.3
    while h <= 3.2:
        a = 0.4
        while a <= 3.4:
            probs = {(x, y): G.poisson_pmf(x, h) * G.poisson_pmf(y, a) for x, y in product(range(8), repeat=2)}
            pH = sum(p for (x, y), p in probs.items() if x > y)
            pD = sum(p for (x, y), p in probs.items() if x == y)
            pA = sum(p for (x, y), p in probs.items() if x < y)
            err = (pH - mH) ** 2 + (pD - mD) ** 2 + (pA - mA) ** 2
            if err < best_err:
                best_err, best = err, (h, a)
            a += 0.02
        h += 0.02
    return best, best_err


(lh0, la0), e0 = lam_from_market(pm['H'] / 100, pm['D'] / 100, pm['A'] / 100)
print(f'\n市场反推 λ: 桑德兰 {lh0:.2f} / 阿森纳 {la0:.2f} (误差 {e0:.5f})')

print('\n=== λ±10% 五场景 ===')
print(f'{"场景":24s}{"λ桑":>6s}{"λ阿":>6s}{"主胜":>7s}{"平":>6s}{"客胜":>7s}{"让胜":>7s}{"走水":>7s}{"让负":>7s}{"大2.5":>7s}')
for tag, mh, ma in [('基准', 1.0, 1.0), ('桑德兰+10%', 1.1, 1.0), ('桑德兰-10%', 0.9, 1.0),
                    ('阿森纳+10%', 1.0, 1.1), ('阿森纳-10%(疲劳)', 1.0, 0.9), ('双升(开)', 1.1, 1.1)]:
    lh, la = lh0 * mh, la0 * ma
    probs = {(x, y): G.poisson_pmf(x, lh) * G.poisson_pmf(y, la) for x, y in product(range(8), repeat=2)}
    pH = sum(p for (x, y), p in probs.items() if x > y) * 100
    pD = sum(p for (x, y), p in probs.items() if x == y) * 100
    pA = sum(p for (x, y), p in probs.items() if x < y) * 100
    hw = sum(p for (x, y), p in probs.items() if (x - y) + LINE > 0) * 100
    hp = sum(p for (x, y), p in probs.items() if (x - y) + LINE == 0) * 100
    hl = sum(p for (x, y), p in probs.items() if (x - y) + LINE < 0) * 100
    ov = sum(p for (x, y), p in probs.items() if x + y > 2.5) * 100
    print(f'{tag:24s}{lh:6.2f}{la:6.2f}{pH:7.1f}{pD:6.1f}{pA:7.1f}{hw:7.1f}{hp:7.1f}{hl:7.1f}{ov:7.1f}')

print('\n' + '=' * 96)
print(f"{'口径':40s}{'λ主':>7s}{'λ客':>7s}{'期望':>7s}{'模型主/平/客':>20s}{'让胜/走/让负':>18s}")
for r in res:
    print(f"{r['label']:40s}{r['lam_h']:7.3f}{r['lam_a']:7.3f}{r['exp']:7.2f}"
          f"{r['pH']:8.1f}/{r['pD']:.1f}/{r['pA']:.1f}   {r['hw']:6.1f}/{r['hp']:.1f}/{r['hl']:.1f}")
print(f"\n市场对照: 主 {pm['H']:.1f} / 平 {pm['D']:.1f} / 客 {pm['A']:.1f} | 让球(+1) 让胜 {qm['H']:.1f} / 走水 {qm['D']:.1f} / 让负 {qm['A']:.1f}")
