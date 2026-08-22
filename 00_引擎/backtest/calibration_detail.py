# -*- coding: utf-8 -*-
"""细化回测: 按方向(H/D/A)分桶校准, 生成校准函数系数"""
import re
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
    return {'league': league, 'hcap': hcap, 'fh': fh, 'fa': fa,
            'odds': {'H': float(oh), 'D': float(od), 'A': float(oa)}}

def hcap_result(fh, fa, hcap):
    net = (fh - hcap) - fa
    return 'H' if net > 0 else ('D' if net == 0 else 'A')

matches = []
with open(PATH, encoding='utf-8') as f:
    for line in f:
        m = parse_line(line)
        if m:
            m['result'] = hcap_result(m['fh'], m['fa'], m['hcap'])
            inv = {k: 1 / v for k, v in m['odds'].items()}
            s = sum(inv.values())
            m['p'] = {k: v / s for k, v in inv.items()}
            matches.append(m)

print(f"有效场次: {len(matches)}\n")

# 按方向分桶校准
buckets = [(0.0, 0.20), (0.20, 0.30), (0.30, 0.40), (0.40, 0.50),
           (0.50, 0.60), (0.60, 0.70), (0.70, 1.01)]

print("=" * 78)
print("【方向分桶校准】每桶: 隐含均值 → 实际频率 (n, 偏差pp)")
print("=" * 78)
cal_points = {'H': [], 'D': [], 'A': []}
for k, name in [('H', '主胜'), ('D', '平局'), ('A', '客胜')]:
    print(f"\n-- {name}方向 --")
    for lo, hi in buckets:
        grp = [m for m in matches if lo <= m['p'][k] < hi]
        if len(grp) < 5:
            continue
        hits = sum(1 for m in grp if m['result'] == k)
        avg_p = sum(m['p'][k] for m in grp) / len(grp)
        freq = hits / len(grp)
        cal_points[k].append((round(avg_p, 3), round(freq, 3)))
        print(f"  隐含{lo*100:3.0f}-{hi*100:3.0f}%: n={len(grp):3d} | 隐含均值 {avg_p*100:5.1f}% | 实际 {freq*100:5.1f}% | 偏差 {(freq-avg_p)*100:+5.1f}pp")

# 生成校准函数(分段线性插值)
def make_cal(pts, lo_ext=0.02, hi_ext=0.95):
    pts = sorted(pts)
    def cal(p):
        p = min(max(p, lo_ext), hi_ext)
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            if x1 <= p <= x2:
                return y1 + (p - x1) * (y2 - y1) / (x2 - x1)
        return p
    return cal

print("\n" + "=" * 78)
print("【校准函数系数】(用于 afei_generator.py)")
print("=" * 78)
for k in 'HDA':
    pts = cal_points[k]
    # 两端延伸
    ext_lo = (0.02, max(pts[0][1] * 0.5, 0.02))
    ext_hi = (0.95, min(pts[-1][1] + (0.95 - pts[-1][0]) * 0.3, 0.96))
    full = [ext_lo] + pts + [ext_hi]
    print(f"\n{k}: {full}")
    # 验证抽样
    cal = make_cal(full)
    for p in [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75]:
        print(f"    cal({p:.2f}) = {cal(p):.3f}")

# 校准后整体 Edge 模拟: 假设模型=市场, 校准后 Edge 应为 0 附近
print("\n" + "=" * 78)
print("【验证】若模型概率=市场隐含, 校准后 Edge 应≈0(无系统性偏差)")
print("=" * 78)
for k in 'HDA':
    cal = make_cal([(0.02, 0.02)] + cal_points[k] + [(0.95, 0.95)])
    edges = [m['p'][k] - cal(m['p'][k]) for m in matches]
    avg_e = sum(edges) / len(edges)
    print(f"  {k}: 平均校准后Edge {avg_e*100:+.2f}pp (应≈0)")

# 平局方向的独立验证: 若将平局隐含×0.5, 是否消除偏差?
print("\n" + "=" * 78)
print("【平局专项】隐含×系数后 vs 实际")
print("=" * 78)
for coef in [0.4, 0.5, 0.6, 0.7]:
    d_events = [(m['p']['D'], 1 if m['result'] == 'D' else 0) for m in matches]
    # 按修正后隐含分桶
    tot_dev = 0
    cnt = 0
    for lo, hi in [(0.0, 0.20), (0.20, 0.25), (0.25, 0.30), (0.30, 1.01)]:
        grp = [(p * coef, hit) for p, hit in d_events if lo <= p * coef < hi]
        if len(grp) < 5:
            continue
        freq = sum(h for _, h in grp) / len(grp)
        avg_p = sum(p for p, _ in grp) / len(grp)
        tot_dev += (freq - avg_p) ** 2 * len(grp)
        cnt += len(grp)
    print(f"  平局隐含×{coef}: 加权均方偏差 {tot_dev/cnt*10000:.1f}")
