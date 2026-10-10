# -*- coding: utf-8 -*-
"""周六012 切尔西 vs 赫尔城 — 英超第4轮 2026-09-12 22:00
用户提供竞彩页完整数据(含伤停9人/赛季0失球) → 四口径模型 + 市场结构
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, '阿飞说球', '02_工具'))
import afei_generator as G  # noqa: E402

ODDS = {'H': 1.11, 'D': 6.60, 'A': 13.00}
HH = {'H': 2.32, 'D': 3.95, 'A': 2.25}
LINE = -2


def dw(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s * 100 for k, v in inv.items()}, s


def run(label, hgf, hga, agf, aga, hform, aform, hm=1.0, am=1.0, adv=0.15):
    cfg = {'title': '周六012', 'competition': '英超 2026/2027 第4轮',
           'draw_to_penalties': False, 'promotion': 'win', 'odds': ODDS,
           'strategy': {'home_mult': hm, 'away_mult': am, 'home_adv': adv,
                        'home_form': hform, 'away_form': aform},
           'teams': {'home': {'name': '切尔西', 'league': '英超', 'gf': hgf, 'ga': hga},
                     'away': {'name': '赫尔城', 'league': '英超', 'gf': agf, 'ga': aga}}}
    m = G.run_model(cfg)
    pr = m['probs']
    hw = sum(p for (h, a), p in pr.items() if (h - a) + LINE > 0) * 100
    hp = sum(p for (h, a), p in pr.items() if (h - a) + LINE == 0) * 100
    hl = sum(p for (h, a), p in pr.items() if (h - a) + LINE < 0) * 100
    pm, S = dw(ODDS)
    qm, Sq = dw(HH)
    print(f'\n【{label}】主 {hgf:.2f}/{hga:.2f}  客 {agf:.2f}/{aga:.2f}  mult {hm}/{am}')
    print(f"  λ 主 {m['lam_h']:.3f} / 客 {m['lam_a']:.3f} → 期望总进球 {m['exp_goals']:.2f}")
    print(f"  模型 主 {m['pH']*100:.1f} / 平 {m['pD']*100:.1f} / 客 {m['pA']*100:.1f}")
    print(f"  Edge 主 {(m['pH']*100-pm['H']):+.1f} / 平 {(m['pD']*100-pm['D']):+.1f} / 客 {(m['pA']*100-pm['A']):+.1f}")
    print(f"  让球(-2) 模型 让胜 {hw:.1f} / 走水 {hp:.1f} / 让负 {hl:.1f}")
    print(f"  总进球 0-1球 {m['p_0_1']*100:.1f}% | 2-3球 {m['p_2_3']*100:.1f}% | 4+球 {m['p_4p']*100:.1f}% | 大2.5 {m['p_over25']*100:.1f}%")
    print(f"  净胜球 恰1球 {m['p_net1']*100:.1f}% | 恰2球 {m['p_net2exact']*100:.1f}% | 2球+ {m['p_net2']*100:.1f}%")
    top = sorted(pr.items(), key=lambda kv: -kv[1])[:6]
    print('  TOP比分 ' + ' | '.join(f'{h}:{a} {p*100:.1f}%' for (h, a), p in top))
    return dict(label=label, lam_h=m['lam_h'], lam_a=m['lam_a'], exp=m['exp_goals'],
                pH=m['pH']*100, pD=m['pD']*100, pA=m['pA']*100, hw=hw, hp=hp, hl=hl,
                over=m['p_over25']*100, p01=m['p_0_1']*100, p23=m['p_2_3']*100, p4=m['p_4p']*100,
                n1=m['p_net1']*100, n2e=m['p_net2exact']*100, n2=m['p_net2']*100)


pm, S = dw(ODDS)
qm, Sq = dw(HH)
print(f"市场: 胜平负 {ODDS['H']}/{ODDS['D']}/{ODDS['A']} → {pm['H']:.1f}/{pm['D']:.1f}/{pm['A']:.1f} (返回率{100/S:.1f}%)")
print(f"市场: 让球(-2) {HH['H']}/{HH['D']}/{HH['A']} → 让胜{qm['H']:.1f}/走水{qm['D']:.1f}/让负{qm['A']:.1f} (返回率{100/Sq:.1f}%)")

res = []
res.append(run('A 竞彩近10场口径(2.6/1.7 vs 1.1/0.4)',
               2.6, 1.7, 1.1, 0.4, {'w': 6, 'd': 1, 'l': 3}, {'w': 5, 'd': 4, 'l': 1}))
res.append(run('B 赛季总口径(8/7/3 vs 3/0/3)',
               8/3, 7/3, 3/3, 0/3, {'w': 6, 'd': 1, 'l': 3}, {'w': 5, 'd': 4, 'l': 1}))
res.append(run('C 主客分离(切尔西主场4/3/1 vs 赫尔城客场1/0/1)',
               4/1, 3/1, 1/1, 0/1, {'w': 6, 'd': 1, 'l': 3}, {'w': 5, 'd': 4, 'l': 1}))
res.append(run('D 主客分离+赫尔城伤停9人上调(客mult 1.06)',
               4/1, 3/1, 1/1, 0/1, {'w': 6, 'd': 1, 'l': 3}, {'w': 5, 'd': 4, 'l': 1}, am=1.06))
res.append(run('E 正式比赛口径(剔除切尔西4场热身/赫尔城4场热身)',
               2.4, 1.6, 0.9, 0.4, {'w': 6, 'd': 1, 'l': 3}, {'w': 5, 'd': 4, 'l': 1}))

print('\n' + '=' * 100)
print(f"{'口径':40s}{'λ主':>7s}{'λ客':>7s}{'期望':>7s}{'模型主/平/客':>20s}{'让胜/走/让负':>18s}")
for r in res:
    print(f"{r['label']:40s}{r['lam_h']:7.3f}{r['lam_a']:7.3f}{r['exp']:7.2f}"
          f"{r['pH']:8.1f}/{r['pD']:.1f}/{r['pA']:.1f}   {r['hw']:6.1f}/{r['hp']:.1f}/{r['hl']:.1f}")
print('\n市场对照: 主 79.8 / 平 13.4 / 客 6.8 | 让球(-2) 让胜 38.2 / 走水 22.4 / 让负 39.4')
json.dump(res, open(os.path.join(ROOT, '.uv-cache', 'm012.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
