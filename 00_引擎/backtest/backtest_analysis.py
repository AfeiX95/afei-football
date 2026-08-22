# -*- coding: utf-8 -*-
"""
竞彩让球胜平负回测 — 市场隐含概率校准分析
数据: 2026-07-07 ~ 2026-08-02 已开奖场次(竞彩网赛果)
"""
import re
import math
from collections import defaultdict

PATH = r'D:\Hermes\football\00_引擎\backtest\matches_20260707_0802.tsv'

def parse_line(line):
    parts = line.rstrip('\n').split('\t')
    if len(parts) < 10:
        return None
    date, no, league, hva, ht, ft, oh, od, oa, status = parts[:10]
    if status != 'done' or oh == '--' or oh == '-':
        return None
    m = re.match(r'^(.*?)\(([+-]\d)\)VS(.*)$', hva)
    if not m:
        return None
    home, hcap, away = m.group(1), int(m.group(2)), m.group(3)
    fh, fa = map(int, ft.split(':'))
    return {'date': date, 'league': league, 'home': home, 'away': away,
            'hcap': hcap, 'fh': fh, 'fa': fa,
            'odds': {'H': float(oh), 'D': float(od), 'A': float(oa)}}

def hcap_result(fh, fa, hcap):
    """让球后结果: 主队净胜 = fh - hcap - fa"""
    net = (fh - hcap) - fa
    return 'H' if net > 0 else ('D' if net == 0 else 'A')

def implied(odds):
    inv = {k: 1 / v for k, v in odds.items()}
    s = sum(inv.values())
    return {k: v / s for k, v in inv.items()}

# ============ 解析 ============
matches = []
with open(PATH, encoding='utf-8') as f:
    for line in f:
        m = parse_line(line)
        if m:
            m['result'] = hcap_result(m['fh'], m['fa'], m['hcap'])
            m['p'] = implied(m['odds'])
            matches.append(m)

print(f"有效场次: {len(matches)}")
from collections import Counter
print("联赛分布:", dict(Counter(m['league'] for m in matches)))
print("让球分布:", dict(Counter(m['hcap'] for m in matches)))

# ============ 1. 各方向整体校准 ============
print("\n" + "=" * 70)
print("【1】方向整体: 平均隐含概率 vs 实际频率")
print("=" * 70)
for k, name in [('H', '主胜(让球后)'), ('D', '平局(让球后)'), ('A', '客胜(让球后)')]:
    n = len(matches)
    hits = sum(1 for m in matches if m['result'] == k)
    avg_p = sum(m['p'][k] for m in matches) / n
    print(f"  {name}: 隐含均值 {avg_p*100:5.1f}% | 实际 {hits/n*100:5.1f}% | 偏差 {(hits/n-avg_p)*100:+5.1f}pp (n={n})")

# ============ 2. 按隐含概率分桶校准(三个方向合并) ============
print("\n" + "=" * 70)
print("【2】校准曲线: 隐含概率分桶 vs 实际频率 (所有方向事件合并)")
print("=" * 70)
buckets = [(0.0, 0.20), (0.20, 0.30), (0.30, 0.40), (0.40, 0.50),
           (0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 1.01)]
events = []
for m in matches:
    for k in 'HDA':
        events.append((m['p'][k], 1 if m['result'] == k else 0))
for lo, hi in buckets:
    grp = [e for e in events if lo <= e[0] < hi]
    if len(grp) < 5:
        continue
    avg_p = sum(e[0] for e in grp) / len(grp)
    freq = sum(e[1] for e in grp) / len(grp)
    print(f"  隐含{lo*100:3.0f}-{hi*100:3.0f}%: n={len(grp):4d} | 隐含均值 {avg_p*100:5.1f}% | 实际 {freq*100:5.1f}% | 偏差 {(freq-avg_p)*100:+5.1f}pp")

# ============ 3. 每场最热方向(市场最高隐含)命中率 ============
print("\n" + "=" * 70)
print("【3】每场最热方向(隐含最高)的命中率")
print("=" * 70)
for lo, hi in [(0.0, 0.35), (0.35, 0.45), (0.45, 0.55), (0.55, 0.65), (0.65, 1.01)]:
    grp = [m for m in matches if lo <= max(m['p'].values()) < hi]
    if not grp:
        continue
    hits = sum(1 for m in grp if m['result'] == max(m['p'], key=m['p'].get))
    avg_p = sum(max(m['p'].values()) for m in grp) / len(grp)
    print(f"  最热隐含{lo*100:3.0f}-{hi*100:3.0f}%: n={len(grp):3d} | 隐含均值 {avg_p*100:5.1f}% | 命中 {hits/len(grp)*100:5.1f}% | 偏差 {(hits/len(grp)-avg_p)*100:+5.1f}pp")

# ============ 4. 平局专项 ============
print("\n" + "=" * 70)
print("【4】平局专项: 平局隐含概率 vs 实际平局率")
print("=" * 70)
for lo, hi in [(0.0, 0.20), (0.20, 0.25), (0.25, 0.30), (0.30, 0.40), (0.40, 1.01)]:
    grp = [m for m in matches if lo <= m['p']['D'] < hi]
    if len(grp) < 5:
        continue
    hits = sum(1 for m in grp if m['result'] == 'D')
    avg_p = sum(m['p']['D'] for m in grp) / len(grp)
    print(f"  平局隐含{lo*100:3.0f}-{hi*100:3.0f}%: n={len(grp):3d} | 隐含均值 {avg_p*100:5.1f}% | 实际 {hits/len(grp)*100:5.1f}% | 偏差 {(hits/len(grp)-avg_p)*100:+5.1f}pp")

# ============ 5. 分联赛 ============
print("\n" + "=" * 70)
print("【5】分联赛: 最热方向命中率")
print("=" * 70)
by_league = defaultdict(list)
for m in matches:
    by_league[m['league']].append(m)
for lg, ms in sorted(by_league.items(), key=lambda x: -len(x[1])):
    if len(ms) < 5:
        continue
    hits = sum(1 for m in ms if m['result'] == max(m['p'], key=m['p'].get))
    print(f"  {lg}: n={len(ms):3d} | 最热命中 {hits/len(ms)*100:5.1f}% | 平均隐含 {sum(max(m['p'].values()) for m in ms)/len(ms)*100:5.1f}%")

# ============ 6. 让球数影响 ============
print("\n" + "=" * 70)
print("【6】让球数: 主让(-1) vs 主受让(+1) vs 深盘(±2)")
print("=" * 70)
for cap, label in [(-2, '-2 主让两球'), (-1, '-1 主让一球'), (1, '+1 主受让一球'), (2, '+2 主受让两球')]:
    ms = [m for m in matches if m['hcap'] == cap]
    if not ms:
        continue
    hits = sum(1 for m in ms if m['result'] == max(m['p'], key=m['p'].get))
    # 主队非让球胜率
    home_win = sum(1 for m in ms if m['fh'] > m['fa']) / len(ms)
    print(f"  {label}: n={len(ms):3d} | 最热命中 {hits/len(ms)*100:5.1f}% | 主队真实胜率 {home_win*100:5.1f}%")

# ============ 7. 双热门场(隐含>45%有两个方向) vs 单热门场 ============
print("\n" + "=" * 70)
print("【7】高平局隐含(>28%)场次: 主胜 vs 客胜 的表现")
print("=" * 70)
grp = [m for m in matches if m['p']['D'] >= 0.28]
if grp:
    h_hits = sum(1 for m in grp if m['result'] == 'H') / len(grp)
    a_hits = sum(1 for m in grp if m['result'] == 'A') / len(grp)
    d_hits = sum(1 for m in grp if m['result'] == 'D') / len(grp)
    print(f"  n={len(grp)} | 主胜 {h_hits*100:.1f}% (隐含均值 {sum(m['p']['H'] for m in grp)/len(grp)*100:.1f}%)"
          f" | 平 {d_hits*100:.1f}% (隐含 {sum(m['p']['D'] for m in grp)/len(grp)*100:.1f}%)"
          f" | 客胜 {a_hits*100:.1f}% (隐含 {sum(m['p']['A'] for m in grp)/len(grp)*100:.1f}%)")

# ============ 8. 世界杯/欧战(跨级赛事) vs 联赛 ============
print("\n" + "=" * 70)
print("【8】大赛(世界杯/欧战) vs 联赛: 最热方向命中率")
print("=" * 70)
for grp_name, pred in [('世界杯/欧战', lambda lg: lg in ('世界杯', '欧冠', '欧罗巴')),
                       ('北欧联赛(瑞/挪/芬)', lambda lg: lg in ('瑞超', '挪超', '芬超')),
                       ('韩职/巴甲/美职', lambda lg: lg in ('韩职', '巴甲', '美职'))]:
    ms = [m for m in matches if pred(m['league'])]
    if not ms:
        continue
    hits = sum(1 for m in ms if m['result'] == max(m['p'], key=m['p'].get))
    avg_p = sum(max(m['p'].values()) for m in ms) / len(ms)
    print(f"  {grp_name}: n={len(ms):3d} | 最热命中 {hits/len(ms)*100:5.1f}% vs 隐含 {avg_p*100:5.1f}% | 偏差 {(hits/len(ms)-avg_p)*100:+5.1f}pp")
