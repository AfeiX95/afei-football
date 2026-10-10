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
                # ⚠️ 2026-09-23(坑#53): 必须 rstrip('\r\n') —— 只 rstrip('\n') 会把 CRLF 行尾的 \r 留在
                #    最后一个字段上, 于是 parts[9] == 'done\r' != 'done', **整行被静默跳过**(实测 10 行)。
                parts = line.rstrip('\r\n').split('\t')
                if len(parts) < 10 or parts[9] != 'done':
                    continue
                # ⚠️ 2026-09-23 修正(坑#52): 去重键必须用 (日期, 编号) —— 体彩**网页**用简称
                #    ("米尔顿"/"韩国亚"/"中国女"), fetch_results 的 **API** 用全称
                #    ("米尔顿凯恩斯"/"韩国亚运男足"/"中国女足"), 同一场会被算成两场(实测 24 组)。
                key = (parts[0], parts[1])          # (日期, 编号)
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
        net = (m['fh'] + m['hcap']) - m['fa']   # 2026-09-10 修正: 原为减号, 让球符号反了
        m['result'] = 'H' if net > 0 else ('D' if net == 0 else 'A')
        # 2026-09-10 口径修正: p 来自胜平负赔率, 校准必须配胜平负结果(不能用让球后结果)
        m['result_plain'] = 'H' if m['fh'] > m['fa'] else ('A' if m['fh'] < m['fa'] else 'D')
        inv = {k: 1 / v for k, v in m['odds'].items()}
        s = sum(inv.values())
        m['p'] = {k: v / s for k, v in inv.items()}
    return matches

def compute_coefs(matches):
    """方向分桶校准 → 推荐系数(**2026-09-21 起按 z² 收缩**)

    每个桶先算"方向平均 ratio", 再按 James-Stein 式权重 w = z²/(1+z²) 向 1.0 收缩:
      越像噪声(z 小)越拉回 1.0; 真偏差(z 大)保留。
    由来: BIAS_AUDIT_20260920 §1/§9.1 —— 三个系数在 560 场样本上**没有一个统计显著**(CI 含 1.0),
          属噪声型点估计; §9.2 指出只改 state 会被下次 EWMA 拉回, 必须写进本函数才持久。

    返回: {draw,hot,cold} = **收缩后**的值(EWMA 的输入); 另附 raw / z / n 供追溯。

    ⚠️ 聚合 SE 的取舍(2026-09-21 实测定): hot/cold 是"H、A 两方向 ratio 取平均", 平均值的 SE 用
    **独立合并** sqrt(Σse_i²)/k。560 场复算得 z = draw +0.557 / hot +0.467 / cold -0.746;
    其中 **draw 与 BIAS_AUDIT §9.1 手算的 +0.56 一致**, hot/cold 比审计的 +0.19/-0.49 **收缩更少**
    (审计未公开其聚合 SE 算法, 疑含方向异质性修正)。raw ratio 与审计完全一致(1.0482/1.022/0.9288),
    所以差异只在收缩权重上; 两种权重都远小于 1, 都属"与 1.0 无法区分"的区间。
    """
    def bucket_stat(kind, lo, hi):
        grp = [m for m in matches if lo <= m['p'][kind] < hi]
        n = len(grp)
        if n < 8:
            return None
        hits = sum(1 for m in grp if m['result_plain'] == kind)   # 2026-09-10: 必须配胜平负结果
        avg_p = sum(m['p'][kind] for m in grp) / n
        if avg_p <= 0:
            return None
        ratio = hits / n / avg_p
        phat = hits / n
        se = math.sqrt(phat * (1 - phat) / n) / avg_p             # ratio 的标准误
        return {'ratio': ratio, 'n': n, 'se': se, 'z': (ratio - 1) / se if se > 0 else 0.0}

    def shrink(parts):
        parts = [p for p in parts if p]
        if not parts:
            return None, None, None, 0
        ratio = sum(p['ratio'] for p in parts) / len(parts)
        se = math.sqrt(sum(p['se'] ** 2 for p in parts)) / len(parts)
        z = (ratio - 1) / se if se > 0 else 0.0
        w = z * z / (1 + z * z)
        return 1 + (ratio - 1) * w, ratio, z, sum(p['n'] for p in parts)

    d_s, d_r, d_z, d_n = shrink([bucket_stat('D', 0.20, 0.30)])
    h_s, h_r, h_z, h_n = shrink([bucket_stat(k, 0.40, 0.70) for k in 'HA'])
    c_s, c_r, c_z, c_n = shrink([bucket_stat(k, 0.0, 0.30) for k in 'HA'])
    return {'draw': d_s, 'hot': h_s, 'cold': c_s,
            'raw': {'draw': d_r, 'hot': h_r, 'cold': c_r},
            'z': {'draw': d_z, 'hot': h_z, 'cold': c_z},
            'n': {'draw': d_n, 'hot': h_n, 'cold': c_n}}

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
                    existing.add((p[0], p[1]))    # (日期, 编号), 见坑#52
    added = 0
    with open(tsv, 'a', encoding='utf-8', newline='\n') as f:
        for m in new:
            hva = f"{(m.get('allHomeTeam') or m.get('homeTeam'))}({m.get('goalLine', '0')})VS{(m.get('allAwayTeam') or m.get('awayTeam'))}"
            key = (m['matchDate'], m.get('matchNumStr', ''))   # (日期, 编号), 见坑#52
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

    # 2026-09-10 口径修正: v1 state 由"让球后结果 × 胜平负赔率"错配导出(且让球符号写反), 全部作废重算
    if old.get('schema') != 2:
        if old:
            print("♻ 检测到旧口径 state(schema<2), 已丢弃并按修正口径重算")
        old = {}

    prev_coef = old.get('coef', {})
    # ⚠️ 2026-09-23(坑#54): 同一批样本重复跑会把 EWMA 反复推进(实测连跑两次: 1.018 → 1.014, 样本没变)。
    #    → 样本量未变 = 没有新赛果 → 不再 EWMA, 沿用上次系数(桶值/raw/z 仍重算, 这部分是幂等的)。
    same_batch = bool(old) and old.get('sample_size') == n
    if same_batch:
        print(f"⚠ 样本量与上次相同({n} 场): 跳过 EWMA, 沿用上次系数 {prev_coef}")
    new_state = {
        'schema': 2,
        'updated_at': date.today().isoformat(),
        'sample_size': n,
        'coef': {
            'draw': prev_coef.get('draw', 1.0) if same_batch else (round(clamp(0.7 * prev_coef.get('draw', 1.0) + 0.3 * coefs['draw'], 0.85, 1.15), 3) if coefs['draw'] else prev_coef.get('draw', 1.0)),
            'hot': prev_coef.get('hot', 1.0) if same_batch else (round(clamp(0.7 * prev_coef.get('hot', 1.0) + 0.3 * coefs['hot'], 0.85, 1.15), 3) if coefs['hot'] else prev_coef.get('hot', 1.0)),
            'cold': prev_coef.get('cold', 1.0) if same_batch else (round(clamp(0.7 * prev_coef.get('cold', 1.0) + 0.3 * coefs['cold'], 0.85, 1.15), 3) if coefs['cold'] else prev_coef.get('cold', 1.0)),
        },
        'buckets': {   # 收缩后的桶值(= EWMA 的输入)
            'draw_20_30': round(coefs['draw'], 3) if coefs['draw'] else None,
            'hot_40_70': round(coefs['hot'], 3) if coefs['hot'] else None,
            'cold_0_30': round(coefs['cold'], 3) if coefs['cold'] else None,
        },
        'buckets_raw': {   # 未收缩的原始 ratio(追溯用)
            'draw_20_30': round(coefs['raw']['draw'], 4) if coefs['raw']['draw'] else None,
            'hot_40_70': round(coefs['raw']['hot'], 4) if coefs['raw']['hot'] else None,
            'cold_0_30': round(coefs['raw']['cold'], 4) if coefs['raw']['cold'] else None,
        },
        'z2_shrink': {     # z 与收缩权重(诊断用)
            'draw': round(coefs['z']['draw'], 3) if coefs['z']['draw'] is not None else None,
            'hot': round(coefs['z']['hot'], 3) if coefs['z']['hot'] is not None else None,
            'cold': round(coefs['z']['cold'], 3) if coefs['z']['cold'] is not None else None,
        },
        'basis': 'direction-averaged ratio + z^2 shrinkage (compute_coefs)',
    }

    changed = (new_state['coef'] != prev_coef)
    with open(STATE, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)

    # 4. 更新报告
    lines = [f"# 竞彩市场校准回测报告",
             f"\n> 最近更新: {new_state['updated_at']} | 累计样本: {n} 场(每周自动演进)",
             f"> 数据源: 竞彩网API + 历史手工采集 | 脚本: fetch_results.py / weekly_update.py",
             f"> 当前校准系数(state): 平局×{new_state['coef']['draw']} / 热门(≥40%)×{new_state['coef']['hot']} / 冷门(<30%)×{new_state['coef']['cold']}",
             f"\n## 本周校准桶(原始 ratio)",
             f"- 平局 隐含20-30%: {new_state['buckets']['draw_20_30']} | 原始 {new_state['buckets_raw']['draw_20_30']} | z {new_state['z2_shrink']['draw']}",
             f"- 热门 隐含40-70%: {new_state['buckets']['hot_40_70']} | 原始 {new_state['buckets_raw']['hot_40_70']} | z {new_state['z2_shrink']['hot']}",
             f"- 冷门 隐含<30%: {new_state['buckets']['cold_0_30']} | 原始 {new_state['buckets_raw']['cold_0_30']} | z {new_state['z2_shrink']['cold']}",
             "\n## 历史结论(2026-09-10 口径修正后重写, 旧结论全部作废)",
             "0. ⚠️ 2026-09-10 口径修正: 旧结论(draw×0.5 / hot×1.35 / cold×0.5)作废。",
             "   旧脚本用【让球后结果】配【胜平负赔率隐含概率】, 且让球公式符号写反(fh-hcap 应为 fh+hcap),",
             "   双重错误叠加 → 产出伪信号(仅修正符号后同一数据即得 draw0.947 / hot0.564 / cold2.180, 结论完全反转=无意义)。",
             "1. 修正口径(胜平负结果 vs 胜平负隐含)在全量469场 ratio≈1.0(0.95~1.10): 竞彩胜平负定价基本有效,",
             "   不要指望从胜平负赔率里挖系统性偏差; 系数应稳定在1.0附近。",
             "2. 让球盘校准本数据集无法做: 赛果API只返回胜平负赔率(h/d/a)+goalLine, 不返回让球盘赔率。",
             "   要做让球盘校准必须先另存让球胜平负赔率(hhad), 否则不要声称有让球盘系数。",
             "3. 让球盘真实结构(修正后469场): 让-1 让球方赢盘27%/走水23%/受让方赢盘50%; 让+1 让球方赢盘32%/走水23%/受让方赢盘45%。",
             "   → 受让方不败约68~77%, 让球方赢盘仅27~32%(可用作方向判断; 赢盘与走水赔付不同, 不可合成单一投注项)。",
             "\n## 用法",
             "afei_generator.py 校准模块自动读取 calibration_state.json(优先),无则用内置系数。",
             "工具: afei_generator.py --model-only 看 'Edge校准' 行。\n"]
    with open(REPORT, 'w', encoding='utf-8', newline='\n') as f:
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
