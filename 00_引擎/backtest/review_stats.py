# -*- coding: utf-8 -*-
"""
review_stats.py — 复盘统计周报 (模型自身精度 + 方向偏差信号) v1.0
=================================================================
输入: 00_引擎/backtest/reviews/*.json (review_match/review_weekly 留档)
流程: 每个留档 → 读 config 重算 run_model(与赛前一致) → 对实际比分累计指标
输出: REVIEW_REPORT.md + stdout(仅样本增加时输出, 静默模式)
指标: 方向命中率(模型 vs 市场) / Brier score / 首选比分 / 大小球
      / Edge(方向偏差≥3%)信号命中 / 分方向明细
注意: 样本<30 时报告标注"仅供参考"——小样本结论不可用于调参
"""
import json
import os
import re
import sys
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(BASE))
TOOL_DIR = os.path.join(PROJECT, '阿飞说球', '02_工具')
sys.path.insert(0, TOOL_DIR)

REVIEWS = os.path.join(BASE, 'reviews')
REPORT = os.path.join(BASE, 'REVIEW_REPORT.md')
MIN_SAMPLE = 30  # 低于此样本量: 结论仅供参考
EDGE_TH = 0.03   # Edge 信号阈值(与图表"中价值线 +3%"一致)


def load_reviews():
    out = []
    if not os.path.isdir(REVIEWS):
        return out
    for fn in sorted(os.listdir(REVIEWS)):
        if fn.endswith('.json'):
            with open(os.path.join(REVIEWS, fn), encoding='utf-8') as f:
                out.append(json.load(f))
    return out


def parse_score(s):
    sh, sa = map(int, s.replace('-', ':').split(':'))
    return sh, sa


def main():
    from afei_generator import run_model

    revs = load_reviews()
    n = len(revs)
    if n == 0:
        print('⚠ 暂无复盘留档 (先跑 review_match.py / review_weekly.py)')
        return 0

    # 静默判断: 样本数较上次报告未增加则只更新报告不输出
    prev_n = None
    if os.path.exists(REPORT):
        m = re.search(r'复盘样本[:：]\s*(\d+)', open(REPORT, encoding='utf-8').read())
        if m:
            prev_n = int(m.group(1))

    # ---------------- 累计指标 ----------------
    S = {'n': 0, 'model_hit': 0, 'mkt_hit': 0, 'score_hit': 0,
         'over_hit': 0, 'edge_n': 0, 'edge_hit': 0, 'edge_sum': 0.0,
         'brier_m': 0.0, 'brier_k': 0.0,
         'dir': {'H': [0, 0], 'D': [0, 0], 'A': [0, 0]}}  # 按实际结果分桶 [模型命中, 总数]
    lines_detail = []
    skipped = 0
    for r in revs:
        # 轻量版复盘(纯赛果, 无赛前 config)无法重算模型 → 跳过, 不计入统计
        cfg_path = r.get('config')
        if not cfg_path or not os.path.exists(cfg_path):
            skipped += 1
            continue
        cfg = json.load(open(cfg_path, encoding='utf-8'))
        m = run_model(cfg)
        sh, sa = parse_score(r['score'])
        a = 'H' if sh > sa else ('D' if sh == sa else 'A')
        p = {'H': m['pH'], 'D': m['pD'], 'A': m['pA']}
        pk = m['pM']
        md = max(p, key=p.get)
        kd = max(pk, key=pk.get)
        top = max(m['probs'], key=lambda k: m['probs'][k])
        S['n'] += 1
        S['model_hit'] += (md == a)
        S['mkt_hit'] += (kd == a)
        S['score_hit'] += ((sh, sa) == top)
        S['over_hit'] += ((sh + sa > 2.5) == (m['p_over25'] > 0.5))
        o = {'H': 0, 'D': 0, 'A': 0}
        o[a] = 1
        S['brier_m'] += sum((p[k] - o[k]) ** 2 for k in 'HDA')
        S['brier_k'] += sum((pk[k] - o[k]) ** 2 for k in 'HDA')
        S['dir'][a][1] += 1
        if md == a:
            S['dir'][a][0] += 1
        eh = m['pH'] - m['pM_cal']['H']
        ea = m['pA'] - m['pM_cal']['A']
        if abs(eh) >= EDGE_TH or abs(ea) >= EDGE_TH:
            ev, ed = (eh, 'H') if eh >= ea else (ea, 'A')
            S['edge_n'] += 1
            S['edge_sum'] += abs(ev)
            S['edge_hit'] += (ed == a)
        lines_detail.append(
            f"- {r['match']} ({r['date']}) 实际{sh}-{sa}: 模型指向{'主胜' if md=='H' else '平局' if md=='D' else '客胜'}"
            f"({'✔' if md==a else '✘'}) | 市场指向{'主胜' if kd=='H' else '平局' if kd=='D' else '客胜'}"
            f"({'✔' if kd==a else '✘'})")

    # ---------------- 渲染报告 ----------------
    n = S['n']   # 分母只用可重算场次(完整版); 轻量版已计入 skipped
    if n == 0:
        print(f'⚠ {len(revs)} 篇留档中无可重算场次(均无赛前 config), 跳过统计')
        return 0

    def pct(x, y):
        return f'{x/y*100:.1f}%' if y else '-'

    lines = [f"# 模型复盘统计报告",
             f"\n> 更新: {date.today().isoformat()} | 复盘样本: {n} 场(每周自动累积, 来自 review_weekly)",
             f"> 留档总数: {len(revs)} 篇 | 跳过轻量版(纯赛果, 无赛前 config 无法重算): {skipped} 篇",
             f"> 数据源: 赛后真实赛果(竞彩API) vs 赛前模型/市场概率 | 脚本: review_stats.py",
             f"> {'⚠ 样本 < %d, 结论仅供参考, 用于校准建议积累至 %d+ 场' % (MIN_SAMPLE, MIN_SAMPLE) if n < MIN_SAMPLE else '✅ 样本量充足, 结论可参考' }",
             f"\n## 方向命中率(最高概率方向与实际结果一致)",
             f"- 泊松模型: {S['model_hit']}/{S['n']} ({pct(S['model_hit'], S['n'])})",
             f"- 市场隐含: {S['mkt_hit']}/{S['n']} ({pct(S['mkt_hit'], S['n'])})",
             f"- 模型-市场差: {pct(S['model_hit']-S['mkt_hit'], S['n'])} 个百分点",
             f"\n## Brier score(越低越准; 三分类随机基线≈0.667)",
             f"- 泊松模型: {S['brier_m']/S['n']:.3f}",
             f"- 市场隐含: {S['brier_k']/S['n']:.3f}",
             f"\n## 首选比分 / 大小球",
             f"- 首选比分命中: {S['score_hit']}/{S['n']} ({pct(S['score_hit'], S['n'])})",
             f"- 大小球方向命中: {S['over_hit']}/{S['n']} ({pct(S['over_hit'], S['n'])})",
             f"\n## Edge 信号(方向偏差≥{EDGE_TH*100:.0f}%, 中价值线)",
             f"- 有信号场次: {S['edge_n']}/{S['n']} | 平均Edge幅度: {S['edge_sum']/S['edge_n']*100:+.1f}%" if S['edge_n'] else "- 有信号场次: 0",
             f"- 信号方向兑现: {S['edge_hit']}/{S['edge_n']} ({pct(S['edge_hit'], S['edge_n'])})" if S['edge_n'] else "",
             f"\n## 分方向明细(模型预测方向命中, 按实际结果分桶)",
             f"- 实际主胜: 模型命中 {S['dir']['H'][0]}/{S['dir']['H'][1]} ({pct(*S['dir']['H'])})",
             f"- 实际平局: 模型命中 {S['dir']['D'][0]}/{S['dir']['D'][1]} ({pct(*S['dir']['D'])})",
             f"- 实际客胜: 模型命中 {S['dir']['A'][0]}/{S['dir']['A'][1]} ({pct(*S['dir']['A'])})",
             f"\n## 逐场明细",
             *lines_detail,
             "\n> 说明: 模型概率=泊松+战意/防守修正; 市场隐含=欧赔去水; Edge=模型-市场校准概率差。",
             "> 待积累: 模型概率校准(Platt/Isotonic)需 ≥50 场后再引入。"]
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # ---------------- stdout(静默模式) ----------------
    if prev_n is not None and prev_n >= n:
        return 0
    msg = [f"📊 复盘统计: 样本{n}场(新) | 模型方向命中{pct(S['model_hit'], S['n'])} vs 市场{pct(S['mkt_hit'], S['n'])}",
           f"   Brier: 模型{S['brier_m']/S['n']:.3f} / 市场{S['brier_k']/S['n']:.3f}"]
    if S['edge_n']:
        msg.append(f"   Edge信号{S['edge_n']}场: 兑现{S['edge_hit']} ({pct(S['edge_hit'], S['edge_n'])})")
    print('\n'.join(msg) + f" | 报告: {REPORT}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
