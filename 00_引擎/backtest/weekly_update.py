# -*- coding: utf-8 -*-
"""
每周回测校准自动演进 (cron 入口, no_agent)
流程: 抓取最近7天赛果 → 合并历史 → 重算校准 → EWMA更新系数 → 更新报告
输出: stdout 摘要(有新增/系数更新才输出, 无变化静默)
"""
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, 'calibration_state.json')
REPORT = os.path.join(BASE, 'BACKTEST_REPORT.md')
TOOL = os.path.normpath(os.path.join(BASE, '..', '..', '阿飞说球', '02_工具', 'afei_generator.py'))

def load_matches():
    """合并 backtest 下所有 matches_*.tsv, 去重"""
    seen, matches = set(), []
    for fn in sorted(os.listdir(BASE)):
        if not fn.startswith('matches_') or not fn.endswith('.tsv'):
            continue
        with open(os.path.join(BASE, fn), encoding='utf-8') as f:
            for line in f:
                parts = line.rstrip('\n').split('\t')
                if len(parts) < 10 or parts[9] != 'done':
                    continue
                key = (parts[0], parts[3])
                if key in seen:
                    continue
                seen.add(key)
                m = re.match(r'^(.*?)\(([+-]\d)\)VS(.*)$', parts[3])
                if not m:
                    continue
                try:
                    fh, fa = map(int, parts[5].split(':'))
                    oh, od, oa = float(parts[6]), float(parts[7]), float(parts[8])
                except (ValueError, IndexError):
                    continue
                matches.append({'date': parts[0], 'league': parts[2],
                                'hcap': int(m.group(2)), 'fh': fh, 'fa': fa,
                                'odds': {'H': oh, 'D': od, 'A': oa}})
    # 计算让球结果 + 隐含概率
    for m in matches:
        net = (m['fh'] - m['hcap']) - m['fa']
        m['result'] = 'H' if net > 0 else ('D' if net == 0 else 'A')
        inv = {k: 1 / v for k, v in m['odds'].items()}
        s = sum(inv.values())
        m['p'] = {k: v / s for k, v in inv.items()}
    return matches

def compute_coefs(matches):
    """方向分桶校准 → 推荐系数"""
    def bucket_ratio(kind, lo, hi):
        grp = [m for m in matches if lo <= m['p'][kind] < hi]
        if len(grp) < 8:
            return None
        hits = sum(1 for m in grp if m['result'] == kind)
        avg_p = sum(m['p'][kind] for m in grp) / len(grp)
        return hits / len(grp) / avg_p if avg_p > 0 else None

    # 平局: 隐含20-30% 的 ratio(历史 ~0.4)
    draw_r = bucket_ratio('D', 0.20, 0.30)
    # 热门(胜负方向 ≥40%): ratio(历史 ~1.3)
    hot_parts = []
    for k in 'HA':
        r = bucket_ratio(k, 0.40, 0.70)
        if r:
            hot_parts.append(r)
    hot_r = sum(hot_parts) / len(hot_parts) if hot_parts else None
    # 冷门(胜负方向 <30%): ratio(历史 ~0.5)
    cold_parts = []
    for k in 'HA':
        r = bucket_ratio(k, 0.0, 0.30)
        if r:
            cold_parts.append(r)
    cold_r = sum(cold_parts) / len(cold_parts) if cold_parts else None

    return {'draw': draw_r, 'hot': hot_r, 'cold': cold_r}

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def main():
    # 1. 抓取最近7天
    end = date.today().isoformat()
    begin = (date.today() - timedelta(days=7)).isoformat()
    sys.path.insert(0, BASE)
    from fetch_results import fetch_all, to_tsv_line
    try:
        new = fetch_all(begin, end, only_single=True)
    except Exception as e:
        print(f"⚠ 抓取失败: {e}")
        return 1

    tsv = os.path.join(BASE, f"matches_{begin.replace('-','')}_latest.tsv")
    existing = set()
    if os.path.exists(tsv):
        with open(tsv, encoding='utf-8') as f:
            for line in f:
                p = line.rstrip('\n').split('\t')
                if len(p) >= 6:
                    existing.add((p[0], p[3]))
    added = 0
    with open(tsv, 'a', encoding='utf-8') as f:
        for m in new:
            hva = f"{(m.get('allHomeTeam') or m.get('homeTeam'))}({m.get('goalLine', '0')})VS{(m.get('allAwayTeam') or m.get('awayTeam'))}"
            key = (m['matchDate'], hva)
            if key in existing:
                continue
            f.write(to_tsv_line(m) + '\n')
            added += 1
    if added:
        print(f"📥 本周新增 {added} 场赛果 ({begin} ~ {end})")

    # 2. 合并全部 + 重算校准
    matches = load_matches()
    n = len(matches)
    coefs = compute_coefs(matches)

    # 3. 读旧状态, EWMA 平滑更新
    old = {}
    if os.path.exists(STATE):
        with open(STATE, encoding='utf-8') as f:
            old = json.load(f)

    prev_coef = old.get('coef', {})
    new_state = {
        'updated_at': date.today().isoformat(),
        'sample_size': n,
        'coef': {
            'draw': round(clamp(0.7 * prev_coef.get('draw', 0.5) + 0.3 * coefs['draw'], 0.30, 0.90), 3) if coefs['draw'] else prev_coef.get('draw', 0.5),
            'hot': round(clamp(0.7 * prev_coef.get('hot', 1.10) + 0.3 * coefs['hot'], 1.00, 1.35), 3) if coefs['hot'] else prev_coef.get('hot', 1.10),
            'cold': round(clamp(0.7 * prev_coef.get('cold', 0.85) + 0.3 * coefs['cold'], 0.50, 0.95), 3) if coefs['cold'] else prev_coef.get('cold', 0.85),
        },
        'buckets': {
            'draw_20_30': round(coefs['draw'], 3) if coefs['draw'] else None,
            'hot_40_70': round(coefs['hot'], 3) if coefs['hot'] else None,
            'cold_0_30': round(coefs['cold'], 3) if coefs['cold'] else None,
        },
    }

    changed = (new_state['coef'] != prev_coef)
    with open(STATE, 'w', encoding='utf-8') as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)

    # 4. 更新报告
    lines = [f"# 竞彩市场校准回测报告",
             f"\n> 最近更新: {new_state['updated_at']} | 累计样本: {n} 场(每周自动演进)",
             f"> 数据源: 竞彩网API + 历史手工采集 | 脚本: fetch_results.py / weekly_update.py",
             f"> 当前校准系数(state): 平局×{new_state['coef']['draw']} / 热门(≥40%)×{new_state['coef']['hot']} / 冷门(<30%)×{new_state['coef']['cold']}",
             f"\n## 本周校准桶(原始 ratio)",
             f"- 平局 隐含20-30%: {new_state['buckets']['draw_20_30']}",
             f"- 热门 隐含40-70%: {new_state['buckets']['hot_40_70']}",
             f"- 冷门 隐含<30%: {new_state['buckets']['cold_0_30']}",
             "\n## 历史结论(见 git 记录/人工复核)",
             "1. 平局隐含虚高一半(×0.5才是真实概率)——竞彩平局赔率系统性偏低",
             "2. 热门方向被低估(隐含40-60%实际命中78-83%)——竞彩定价保守",
             "3. 冷门方向被高估(隐含<30%实际仅6-10%)",
             "\n## 用法",
             "afei_generator.py 校准模块自动读取 calibration_state.json(优先),无则用内置系数。",
             "工具: afei_generator.py --model-only 看 'Edge校准' 行。\n"]
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # 5. 输出摘要
    msg = []
    if added:
        msg.append(f"新增 {added} 场")
    if changed:
        msg.append(f"系数更新: 平局×{new_state['coef']['draw']} 热门×{new_state['coef']['hot']} 冷门×{new_state['coef']['cold']}(样本{n}场)")
    if msg:
        print(' | '.join(msg) + f" | 校准state已刷新: {STATE}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
