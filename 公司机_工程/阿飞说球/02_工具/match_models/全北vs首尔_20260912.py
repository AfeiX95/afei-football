# -*- coding: utf-8 -*-
"""周六002 全北现代 vs 首尔FC — 真实口径模型 + 亚冠轮换敏感性

数据(用户提供竞彩页 2026-09-12):
  全北现代 第3名 | 28场 11胜10平7负 35/24 净+11 43分
    主 13场 7胜2平4负 20/13 | 客 15场 4胜8平3负 15/11
    近10场 3胜5平2负 进12失10; 竞彩场均口径 1.2 / 1.0
    近3轮: 09-09 客1:1江原 | 09-05 主2:0浦项 | 08-30 客1:1仁川
  首尔FC 第1名 | 28场 18胜5平5负 53/22 净+31 59分
    主 13场 8胜2平3负 22/10 | 客 15场 10胜3平2负 31/12
    近10场 5胜2平3负 进19失10; 竞彩场均口径 1.9 / 1.0
    近3轮: 09-08 客0:1蔚山(负) | 09-05 主1:0仁川(胜) | 08-30 客5:2光州(胜)
  交锋 近10场 全北 4胜4平2负; 最近一次 2026-08-01 全北主场 0:0
  伤停 全北: Dodô(中场, 1场) 伤; 首尔: 竞彩暂无数据
  射手 全北: Lee Seung-Woo 8球(24%) + 佩雷拉达席尔瓦 5球; 首尔: Klimala 10球(20%) + Jung Seung-Won 8球
  亚冠: 两队 09-16 都有首轮(全北主 vs 柏太阳神 / 首尔主 vs 万隆) → 本场后仅 4 天
  赔率(09-11 09:48) 胜平负 2.80/3.20/2.18; 让球(+1) 1.52/3.90/4.65
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, '阿飞说球', '02_工具'))
import afei_generator as G  # noqa: E402

ODDS = {'H': 2.80, 'D': 3.20, 'A': 2.18}
HH = {'H': 1.52, 'D': 3.90, 'A': 4.65}
LINE = +1   # 主队受让一球


def dw(o):
    inv = {k: 1 / v for k, v in o.items()}
    s = sum(inv.values())
    return {k: v / s * 100 for k, v in inv.items()}, s


def run(label, hgf, hga, agf, aga, hform, aform, home_mult=1.0, away_mult=1.0, home_adv=0.15):
    cfg = {
        'title': '周六002 全北现代vs首尔FC', 'competition': '韩职 2026赛季',
        'draw_to_penalties': False, 'promotion': 'win', 'odds': ODDS,
        'strategy': {'home_mult': home_mult, 'away_mult': away_mult, 'home_adv': home_adv,
                     'home_form': hform, 'away_form': aform},
        'teams': {'home': {'name': '全北现代', 'league': '韩职', 'gf': hgf, 'ga': hga},
                  'away': {'name': '首尔FC', 'league': '韩职', 'gf': agf, 'ga': aga}},
    }
    m = G.run_model(cfg)
    pm, S = dw(ODDS)
    qm, Sq = dw(HH)
    probs = m['probs']
    hw = sum(p for (h, a), p in probs.items() if (h - a) + LINE > 0) * 100
    hp = sum(p for (h, a), p in probs.items() if (h - a) + LINE == 0) * 100
    hl = sum(p for (h, a), p in probs.items() if (h - a) + LINE < 0) * 100
    top = sorted(probs.items(), key=lambda kv: -kv[1])[:6]
    print(f'\n【{label}】 主 {hgf:.3f}/{hga:.3f}  客 {agf:.3f}/{aga:.3f}  (mult {home_mult}/{away_mult})')
    print(f"  λ 主 {m['lam_h']:.3f} / 客 {m['lam_a']:.3f} → 期望总进球 {m['exp_goals']:.2f}")
    print(f"  模型 主 {m['pH']*100:.1f} / 平 {m['pD']*100:.1f} / 客 {m['pA']*100:.1f}")
    print(f"  市场 主 {pm['H']:.1f} / 平 {pm['D']:.1f} / 客 {pm['A']:.1f}   (返回率 {100/S:.1f}%)")
    print(f"  Edge 主 {(m['pH']*100-pm['H']):+.1f} / 平 {(m['pD']*100-pm['D']):+.1f} / 客 {(m['pA']*100-pm['A']):+.1f}")
    print(f"  让球(+1) 市场 让胜 {qm['H']:.1f} / 走水 {qm['D']:.1f} / 让负 {qm['A']:.1f}  (返回率 {100/Sq:.1f}%)")
    print(f"  让球(+1) 模型 让胜 {hw:.1f} / 走水 {hp:.1f} / 让负 {hl:.1f}")
    print(f"  总进球 0-1球 {m['p_0_1']*100:.1f}% | 2-3球 {m['p_2_3']*100:.1f}% | 4+球 {m['p_4p']*100:.1f}% | 大2.5 {m['p_over25']*100:.1f}%")
    print(f"  净胜球 恰1球 {m['p_net1']*100:.1f}% | 2球+ {m['p_net2']*100:.1f}%")
    print('  TOP比分 ' + ' | '.join(f'{h}-{a} {p*100:.1f}%' for (h, a), p in top))
    return dict(label=label, lam_h=m['lam_h'], lam_a=m['lam_a'], exp=m['exp_goals'],
                pH=m['pH'] * 100, pD=m['pD'] * 100, pA=m['pA'] * 100, hw=hw, hp=hp, hl=hl,
                over=m['p_over25'] * 100, p01=m['p_0_1'] * 100, p23=m['p_2_3'] * 100,
                p4=m['p_4p'] * 100, n1=m['p_net1'] * 100, n2=m['p_net2'] * 100)


res = []
res.append(run('A 竞彩近10场口径(1.2/1.0 vs 1.9/1.0)',
               1.2, 1.0, 1.9, 1.0, {'w': 3, 'd': 5, 'l': 2}, {'w': 5, 'd': 2, 'l': 3}))
res.append(run('B 赛季总口径(35/24/28 vs 53/22/28)',
               35 / 28, 24 / 28, 53 / 28, 22 / 28, {'w': 3, 'd': 5, 'l': 2}, {'w': 5, 'd': 2, 'l': 3}))
res.append(run('C 主客分离(全北主场20/13/13 vs 首尔客场31/12/15)',
               20 / 13, 13 / 13, 31 / 15, 12 / 15, {'w': 3, 'd': 5, 'l': 2}, {'w': 5, 'd': 2, 'l': 3}))
res.append(run('D 主客分离 + 亚冠轮换(全北-8% / 首尔-12%)',
               20 / 13, 13 / 13, 31 / 15, 12 / 15, {'w': 3, 'd': 5, 'l': 2}, {'w': 5, 'd': 2, 'l': 3},
               home_mult=0.92, away_mult=0.88))

print('\n' + '=' * 100)
print(f"{'口径':42s}{'λ主':>7s}{'λ客':>7s}{'期望':>7s}{'模型主/平/客':>20s}{'让胜/走/让负':>18s}")
for r in res:
    print(f"{r['label']:42s}{r['lam_h']:7.3f}{r['lam_a']:7.3f}{r['exp']:7.2f}"
          f"{r['pH']:8.1f}/{r['pD']:.1f}/{r['pA']:.1f}   {r['hw']:6.1f}/{r['hp']:.1f}/{r['hl']:.1f}")
json.dump(res, open(os.path.join(ROOT, '.uv-cache', 'm002.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
