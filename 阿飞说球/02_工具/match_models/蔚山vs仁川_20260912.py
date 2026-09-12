# -*- coding: utf-8 -*-
"""周六001 蔚山现代 vs 仁川联 — 真实口径模型

数据(用户提供竞彩页 2026-09-12):
  蔚山现代 第2名 | 28场 13胜5平10负 42/37 净+5 44分
    主 14场 7胜1平6负 24/22  客 14场 6胜4平4负 18/15
    近10场 5胜1平4负 进15失10；场均(竞彩口径) 1.5 / 1.0
    近3轮: 09-08 主1:0首尔FC(W) | 09-05 客0:0济州SK(D) | 08-29 主3:1金泉(W)
  仁川联 第7名 | 27场 10胜7平10负 34/30 净+4 37分
    主 14场 5胜3平6负 16/15  客 13场 5胜4平4负 18/15
    近10场 3胜4平3负 进12失12；场均(竞彩口径) 1.2 / 1.2
    近3轮: 09-08 主2:1富川(W) | 09-05 客0:1首尔FC(L) | 08-30 主1:1全北(D)
  交锋 近10场 蔚山 3胜4平3负(平40%)；最近一次 2026-07-21 蔚山主场 1:2 负仁川
  伤停 蔚山: 尹正圭(后卫, 3场/2首发)、Pedrinho(前锋, 5场) 伤；仁川: 竞彩"暂无数据"(按坑#35不可采信)
  射手 蔚山: Yago Caju 13球(30%) + 李东京 9球9助；仁川: Mugoša 11球(33%) + 罗马尼奥利 6球
  赔率(09-12 10:20 更新) 胜平负 2.02/3.13/3.18；让球(-1) 4.20/3.70/1.61
"""
import json
import os
import sys
from itertools import product

ROOT = r'D:\Hermes\football'
sys.path.insert(0, os.path.join(ROOT, '阿飞说球', '02_工具'))
import afei_generator as G  # noqa: E402

ODDS = {'H': 2.02, 'D': 3.13, 'A': 3.18}
HH = {'H': 4.20, 'D': 3.70, 'A': 1.61}
LINE = -1


def dw(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s * 100 for k, v in inv.items()}, s


def run(label, hgf, hga, agf, aga, hform, aform, home_adv=0.15):
    cfg = {
        'title': '周六001 蔚山现代vs仁川联', 'competition': '韩职 2026赛季',
        'draw_to_penalties': False, 'promotion': 'win', 'odds': ODDS,
        'strategy': {'home_mult': 1.0, 'away_mult': 1.0, 'home_adv': home_adv,
                     'home_form': hform, 'away_form': aform},
        'teams': {'home': {'name': '蔚山现代', 'league': '韩职', 'gf': hgf, 'ga': hga},
                  'away': {'name': '仁川联', 'league': '韩职', 'gf': agf, 'ga': aga}},
    }
    m = G.run_model(cfg)
    pm, S = dw(ODDS)
    qm, Sq = dw(HH)
    probs = m['probs']
    hw = sum(p for (h, a), p in probs.items() if (h - a) + LINE > 0) * 100
    hp = sum(p for (h, a), p in probs.items() if (h - a) + LINE == 0) * 100
    hl = sum(p for (h, a), p in probs.items() if (h - a) + LINE < 0) * 100
    top = sorted(probs.items(), key=lambda kv: -kv[1])[:6]
    over = m['p_over25'] * 100
    print(f'\n【{label}】 主 gf/ga={hgf}/{hga}  客 gf/ga={agf}/{aga}')
    print(f"  λ 主 {m['lam_h']:.3f} / 客 {m['lam_a']:.3f} → 期望总进球 {m['exp_goals']:.2f}")
    print(f"  模型 主 {m['pH']*100:.1f} / 平 {m['pD']*100:.1f} / 客 {m['pA']*100:.1f}")
    print(f"  市场 主 {pm['H']:.1f} / 平 {pm['D']:.1f} / 客 {pm['A']:.1f}   (返回率 {100/S:.1f}%)")
    print(f"  Edge 主 {(m['pH']*100-pm['H']):+.1f} / 平 {(m['pD']*100-pm['D']):+.1f} / 客 {(m['pA']*100-pm['A']):+.1f}")
    print(f"  让球(-1) 市场 让胜 {qm['H']:.1f} / 走水 {qm['D']:.1f} / 让负 {qm['A']:.1f}  (返回率 {100/Sq:.1f}%)")
    print(f"  让球(-1) 模型 让胜 {hw:.1f} / 走水 {hp:.1f} / 让负 {hl:.1f}")
    print(f"  总进球 0-1球 {m['p_0_1']*100:.1f}% | 2-3球 {m['p_2_3']*100:.1f}% | 4+球 {m['p_4p']*100:.1f}% | 大2.5 {over:.1f}%")
    print(f"  净胜球 恰1球 {m['p_net1']*100:.1f}% | 2球+ {m['p_net2']*100:.1f}%")
    print('  TOP比分 ' + ' | '.join(f'{h}-{a} {p*100:.1f}%' for (h, a), p in top))
    return dict(label=label, lam_h=m['lam_h'], lam_a=m['lam_a'], exp=m['exp_goals'],
                pH=m['pH'] * 100, pD=m['pD'] * 100, pA=m['pA'] * 100,
                hw=hw, hp=hp, hl=hl, over=over, p01=m['p_0_1'] * 100, p23=m['p_2_3'] * 100,
                p4=m['p_4p'] * 100, n1=m['p_net1'] * 100, n2=m['p_net2'] * 100)


res = []
# A. 竞彩口径(近10场场均)
res.append(run('A 竞彩口径(近10场 1.5/1.0 vs 1.2/1.2)',
               1.5, 1.0, 1.2, 1.2, {'w': 5, 'd': 1, 'l': 4}, {'w': 3, 'd': 4, 'l': 3}))
# B. 赛季口径(积分榜总进失球/场次)
res.append(run('B 赛季口径(42/37/28 vs 34/30/27)',
               42 / 28, 37 / 28, 34 / 27, 30 / 27, {'w': 5, 'd': 1, 'l': 4}, {'w': 3, 'd': 4, 'l': 3}))
# C. 主客场分开口径(蔚山主场 vs 仁川客场)
res.append(run('C 主客分离(蔚山主场 24/22/14 vs 仁川客场 18/15/13)',
               24 / 14, 22 / 14, 18 / 13, 15 / 13, {'w': 5, 'd': 1, 'l': 4}, {'w': 3, 'd': 4, 'l': 3}))

print('\n' + '=' * 78)
print(f"{'口径':34s}{'λ主':>7s}{'λ客':>7s}{'期望':>7s}{'模型主/平/客':>20s}{'让胜/走/让负':>18s}")
for r in res:
    print(f"{r['label']:34s}{r['lam_h']:7.3f}{r['lam_a']:7.3f}{r['exp']:7.2f}"
          f"{r['pH']:8.1f}/{r['pD']:.1f}/{r['pA']:.1f}   {r['hw']:6.1f}/{r['hp']:.1f}/{r['hl']:.1f}")
json.dump(res, open(os.path.join(ROOT, '.uv-cache', 'm001.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
