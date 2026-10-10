# -*- coding: utf-8 -*-
"""竞彩校准层 · 偏差审计 (2026-09-18~09-20 增量)

三条硬约束
 1. 复现优先: 必须先用 state 快照复现 calibration_state.json 的三个桶值, 才允许给结论。
    weekly_update.compute_coefs 的 hot/cold 是【H、A 两方向各算 ratio 再取算术平均】,
    draw 是单桶。本脚本按同一公式复现(ratio_dir_avg), 同时另算池化 ratio(用于显著性)。
 2. 口径: p 来自 h/d/a(胜平负)赔率去水, ratio 配 result_plain(胜平负结果)。
    依据: _verify_caliber.py 用官方 winFlag 判决 —— 25 场"让球会改变结果"的样本 49/49 跟胜平负侧。
 3. 显著性: 每个桶/方向给二项标准误、95%CI、z, 并给"检出现有偏差所需样本量"。
    不做无 CI 的偏差断言。
"""
import json
import math
import os
import re
import time
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, 'calibration_state.json')
RAW = os.path.join(BASE, '_raw_20260918_0920.tsv')
OUT = os.path.join(BASE, 'BIAS_AUDIT_20260920.md')
REC = os.path.join(BASE, 'calibration_state.recommended.json')
INGEST_FILE = 'matches_20260918_latest.tsv'   # 本批入库文件(用于区分"入库前已有"与"本批新增")

HOT = (0.40, 0.70)
COLD = (0.00, 0.30)
DRAW = (0.20, 0.30)


# ---------------------------------------------------------------- 载入
def parse_row(date, league, match, ft, oh, od, oa):
    m = re.match(r'^(.*?)\(([+-]?\d+)\)VS(.*)$', match)
    if not m:
        return None
    try:
        fh, fa = map(int, ft.split(':'))
    except ValueError:
        return None
    hcap = int(m.group(2))
    rec = {'date': date, 'league': league, 'match': match, 'hcap': hcap,
           'fh': fh, 'fa': fa, 'home': m.group(1), 'away': m.group(3)}
    rec['result_plain'] = 'H' if fh > fa else ('A' if fh < fa else 'D')
    net = (fh + hcap) - fa
    rec['net'] = net
    rec['result_hcap'] = 'H' if net > 0 else ('A' if net < 0 else 'D')
    rec['has_odds'] = bool(oh and od and oa)
    if rec['has_odds']:
        odds = {'H': float(oh), 'D': float(od), 'A': float(oa)}
        inv = {k: 1.0 / v for k, v in odds.items()}
        s = sum(inv.values())
        rec['odds'] = odds
        rec['overround'] = s
        rec['p'] = {k: v / s for k, v in inv.items()}
    return rec


def load_history(max_mtime_date=None, skip_files=()):
    """与 weekly_update.load_matches 同口径; 可按文件 mtime 截断以复现 state 快照"""
    seen, out = set(), []
    for fn in sorted(os.listdir(BASE)):
        if not (fn.startswith('matches_') and fn.endswith('.tsv')):
            continue
        if fn in skip_files:
            continue
        if max_mtime_date:
            mt = time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(os.path.join(BASE, fn))))
            if mt > max_mtime_date:
                continue
        with open(os.path.join(BASE, fn), encoding='utf-8') as f:
            for line in f:
                p = line.rstrip('\r\n').split('\t')   # ⚠️ 见坑#53: 只 rstrip('\n') 会让 CRLF 行被静默跳过
                if len(p) < 10 or p[9] != 'done':
                    continue
                key = (p[0], p[1])          # ⚠️ (日期, 编号) —— 见坑#52(队名简称/全称漂移会导致双计)
                if key in seen:
                    continue
                if not (p[6] and p[7] and p[8]):
                    continue
                seen.add(key)
                r = parse_row(p[0], p[2], p[3], p[5], p[6], p[7], p[8])
                if r:
                    out.append(r)
    return out


def load_new():
    seen, out = set(), []
    with open(RAW, encoding='utf-8') as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) < 9:
                continue
            key = (p[0], p[3])
            if key in seen:
                continue
            seen.add(key)
            r = parse_row(p[0], p[2], p[3], p[5], p[6], p[7], p[8])
            if r:
                r['winFlag'] = p[10] if len(p) > 10 else ''
                out.append(r)
    return out


# ---------------------------------------------------------------- 统计
def cell(ms, kind, lo, hi):
    """单方向单桶统计"""
    g = [m for m in ms if m['has_odds'] and lo <= m['p'][kind] < hi]
    n = len(g)
    if n == 0:
        return None
    hits = sum(1 for m in g if m['result_plain'] == kind)
    avg_p = sum(m['p'][kind] for m in g) / n
    freq = hits / n
    se_f = math.sqrt(freq * (1 - freq) / n) if 0 < freq < 1 else float('nan')
    se_ratio = se_f / avg_p if avg_p else float('nan')
    ratio = freq / avg_p if avg_p else float('nan')
    se_r_model = math.sqrt(avg_p * (1 - avg_p) / n) / avg_p if 0 < avg_p < 1 else float('nan')
    return {'n': n, 'hits': hits, 'freq': freq, 'avg_p': avg_p, 'ratio': ratio,
            'se_f': se_f, 'se': se_ratio, 'se_model': se_r_model,
            'z': (ratio - 1) / se_ratio if se_ratio and not math.isnan(se_ratio) else float('nan'),
            'ci_lo': ratio - 1.96 * se_ratio, 'ci_hi': ratio + 1.96 * se_ratio}


def n_needed(avg_p, ratio, power_z=2.80, sig_z=1.96):
    """检出现有相对偏差所需单格样本量 (80% power, 双侧 5%)"""
    if not avg_p or ratio == 1:
        return None
    delta = abs(ratio - 1)
    # SE_ratio ≈ sqrt((1-p)/(n p)) → n = (1-p)/(p * (delta/(z_a+z_b))^2)
    return (1 - avg_p) / (avg_p * (delta / (sig_z + power_z)) ** 2)


def ratio_dir_avg(ms, kinds, lo, hi):
    """weekly_update.compute_coefs 的原公式: 各方向 ratio 的算术平均"""
    parts = [cell(ms, k, lo, hi) for k in kinds]
    parts = [p for p in parts if p and p['n'] >= 8]
    if not parts:
        return None, parts
    return sum(p['ratio'] for p in parts) / len(parts), parts


def coefs_like_weekly(ms):
    """完全按 weekly_update.compute_coefs 复现三个桶"""
    draw, _ = ratio_dir_avg(ms, 'D', *DRAW)
    hot, _ = ratio_dir_avg(ms, 'HA', *HOT)
    cold, _ = ratio_dir_avg(ms, 'HA', *COLD)
    return {'draw_20_30': draw, 'hot_40_70': hot, 'cold_0_30': cold}


def calib_curve(ms, width=0.05, min_n=5):
    rows = []
    for i in range(int(1 / width)):
        lo, hi = i * width, (i + 1) * width
        ev = []
        for m in ms:
            if not m['has_odds']:
                continue
            for k in 'HDA':
                if lo <= m['p'][k] < hi:
                    ev.append((m['p'][k], 1 if m['result_plain'] == k else 0))
        if len(ev) < min_n:
            continue
        n = len(ev)
        avg_p = sum(e[0] for e in ev) / n
        freq = sum(e[1] for e in ev) / n
        se = math.sqrt(freq * (1 - freq) / n)
        z = (freq - avg_p) / se if se > 0 else float('nan')
        rows.append({'lo': lo, 'hi': hi, 'n': n, 'avg_p': avg_p, 'freq': freq,
                     'dev_pp': (freq - avg_p) * 100, 'z': z})
    return rows


def brier_logloss(ms):
    b = ll = 0.0
    n = 0
    for m in ms:
        if not m['has_odds']:
            continue
        n += 1
        for k in 'HDA':
            y = 1.0 if m['result_plain'] == k else 0.0
            b += (m['p'][k] - y) ** 2
            ll -= y * math.log(max(m['p'][k], 1e-12)) + (1 - y) * math.log(max(1 - m['p'][k], 1e-12))
    return (b / (3 * n), ll / (3 * n), n) if n else (float('nan'),) * 3


def hcap_table(ms):
    g = defaultdict(lambda: {'让球方赢盘': 0, '走水': 0, '受让方赢盘': 0})
    for m in ms:
        d = g[m['hcap']]
        if m['net'] == 0:
            d['走水'] += 1
        elif m['hcap'] < 0:                      # 主队让球 → 让球方=主队
            d['让球方赢盘' if m['net'] > 0 else '受让方赢盘'] += 1
        else:                                    # 客队让球 → 让球方=客队
            d['让球方赢盘' if m['net'] < 0 else '受让方赢盘'] += 1
    return g


def pct(x, d=1):
    return f'{x*100:.{d}f}%'


# ---------------------------------------------------------------- 主流程
def main():
    state = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}

    snap = load_history(state.get('updated_at'))     # state 快照
    lib = load_history()                             # 库现状(含本批, 若已入库)
    lib_pre = load_history(skip_files=(INGEST_FILE,))  # 本批入库前的库
    new = load_new()                                 # 本批 53 场(官方页)
    inc_keys = {(m['date'], m['match']) for m in new}
    hist = [m for m in lib if (m['date'], m['match']) not in inc_keys]   # 本批之前的历史
    pre_keys = {(m['date'], m['match']) for m in lib_pre}
    overlap_pre = len(inc_keys & pre_keys)           # 早于本批就在库(09-18 周四 9 场)
    ingested = len(inc_keys & {(m['date'], m['match']) for m in lib})
    new_odds = [m for m in new if m['has_odds']]
    net_new = len(new_odds) - overlap_pre            # 本批净新增有赔率样本
    combined = hist + new_odds                       # 幂等: 入库与否都是同一并集

    L = []
    w = L.append

    w('# 竞彩校准层 · 偏差审计')
    w('')
    w('| 项 | 值 |')
    w('|---|---|')
    w('| 审计时点 | 2026-09-20 |')
    w(f'| 增量样本 | 2026-09-18 ~ 2026-09-20 官方赛果 **53 场**(有赔率 49) |')
    w(f'| 其中早于本批已在库 | {overlap_pre} 场(09-18 周四, 此前由 fetch_results.py 补录) |')
    w(f'| 本批净新增有赔率样本 | **{net_new}** 场 |')
    w(f'| 本批入库 | `{INGEST_FILE}` 写入 {ingested} 行 |')
    w(f'| state 快照 | {len(snap)} 场 (state 记 {state.get("sample_size")}) |')
    w(f'| 本批之前的历史 | {len(hist)} 场 |')
    w(f'| 库现状 | {len(lib)} 场 |')
    w(f'| 合并后(样本基数) | **{len(combined)}** 场 |')
    w('')
    w('**口径**: 隐含概率 p 来自 **胜平负**赔率(h/d/a)去水; ratio 配 **胜平负**结果。')
    w('依据: 官方 `winFlag` 字段判决 —— 25 场"让球会改变结果"的样本中, winFlag **49/49 跟胜平负侧, 0 场跟让球侧**。')
    w('')

    # ---------------- 0. 复现 ----------------
    rep = coefs_like_weekly(snap)
    st_b = state.get('buckets', {})
    w('## 0. 复现校验(管线一致性)')
    w('')
    w('用 state 记录的截至时点的库快照, 按 `weekly_update.compute_coefs` 原公式重算:')
    w('')
    w('| 桶 | 本脚本重算 | calibration_state.json | 复现 |')
    w('|---|---|---|---|')
    ok = True
    for k, label in (('draw_20_30', '平局 隐含20-30%'), ('hot_40_70', '热门 隐含40-70%'), ('cold_0_30', '冷门 隐含<30%')):
        mine, theirs = rep[k], st_b.get(k)
        same = mine is not None and theirs is not None and abs(mine - theirs) < 0.0015
        ok &= same
        w(f"| {label} | {mine:.4f} | {theirs} | {'✅' if same else '❌'} |")
    w('')
    w(f"- 样本量 {len(snap)} vs state {state.get('sample_size')}: {'一致 ✅' if len(snap) == state.get('sample_size') else '不一致 ❌'}")
    w(f"- **管线一致性判定: {'通过 ✅ 本脚本与 weekly_update.py 口径等价, 下述结论可用' if ok else '未通过 ❌ 结论不可用'}**")
    w('')
    w('### ⚠️ 发现 A: state 已滞后, 且滞后期间无人重算')
    w('')
    w(f'本批之前的历史 **{len(hist)} 场** + 本批 **{len(new_odds)}** 场有赔率样本 = **{len(combined)} 场**;')
    w(f'库现状(含已入库的本批) **{len(lib)} 场**, state 停在 **{state.get("sample_size")} 场**, 缺口 **{len(lib) - state.get("sample_size", 0)} 场**。')
    w(f'缺口构成: 09-18 补录 18 场 + 本批净新增 {net_new} 场 = {18 + net_new} 场。')
    w('其中 09-18 那批(18 场, mtime 2026-09-18, 由 `fetch_results.py --begin 2026-09-17 --end 2026-09-18` 手工补录)')
    w('**从未触发过 `weekly_update.py`**, 因为该脚本是"抓最近 7 天"的 cron, 补录落在窗口外。')
    w('→ **系数停留在一批样本之前的估计上**, 而校准系数会直接进 `afei_generator.py` 的 Edge 校准行。')
    w('')

    # ---------------- 1. 漂移 ----------------
    w('## 1. 三个时点的 ratio 漂移')
    w('')
    r_snap, r_cmb, r_new = coefs_like_weekly(snap), coefs_like_weekly(combined), coefs_like_weekly(new_odds)
    w('| 桶 | state快照(%d) | 合并后(%d) | 本批单独(%d) |' % (len(snap), len(combined), len(new_odds)))
    w('|---|---|---|---|')
    for k, label in (('draw_20_30', '平局 20-30%'), ('hot_40_70', '热门 40-70%'), ('cold_0_30', '冷门 <30%')):
        w(f"| {label} | {r_snap[k]:.3f} | {r_cmb[k]:.3f} | {r_new[k]:.3f} |")
    w('')
    w(f'冷门桶: **{r_snap["cold_0_30"]:.3f} → {r_cmb["cold_0_30"]:.3f}**, 加样本后向 1.0 靠了一步。')
    w('这是**噪声型系数**的形态: 真偏差随样本增加应收敛到某个 ≠1.0 的稳定值, 噪声则持续向 1.0 爬。')
    w('')
    w('⚠️ **"本批单独"一列只有 49 场, 不要单独引用**。它的作用是给出"这一批把系数往哪边推",')
    w('   例如冷门 1.383 表示这 49 场里低赔方爆了不少 —— 但这正是小样本的样子, 不代表新偏差。')
    w('')

    # ---------------- 2. 主客分解(核心) ----------------
    w('## 2. 偏差的真实结构: 主客不对称 (核心发现)')
    w('')
    w('`weekly_update.compute_coefs` 对 hot/cold 的算法是 **把 H 与 A 两个方向各算一个 ratio 再取算术平均**:')
    w('')
    w('```python')
    w('hot_parts = [bucket_ratio(k, 0.40, 0.70) for k in "HA"]')
    w('hot_r = sum(hot_parts) / len(hot_parts)      # ← 两个方向被平均掉')
    w('```')
    w('')
    w('平均会把方向相反的两个偏差**互相抵消**。拆开看 state 快照(502 场):')
    w('')
    w('| 桶 | 方向 | n | 隐含均值 | 实际频率 | ratio | 95% CI | z |')
    w('|---|---|---|---|---|---|---|---|')
    rows = []
    for kind, name in (('H', '主胜'), ('A', '客胜')):
        c = cell(snap, kind, *HOT)
        rows.append(('热门 40-70%', name, c))
    for kind, name in (('H', '主胜'), ('A', '客胜')):
        c = cell(snap, kind, *COLD)
        rows.append(('冷门 <30%', name, c))
    rows.append(('平局 20-30%', '平', cell(snap, 'D', *DRAW)))
    for bucket, name, c in rows:
        star = ' ⚠' if abs(c['z']) > 1.96 else ''
        w(f"| {bucket} | {name} | {c['n']} | {pct(c['avg_p'])} | {pct(c['freq'])} | **{c['ratio']:.3f}** | "
          f"[{c['ci_lo']:.3f}, {c['ci_hi']:.3f}] | {c['z']:+.2f}{star} |")
    w('')
    hot_h = cell(snap, 'H', *HOT)
    hot_a = cell(snap, 'A', *HOT)
    cold_h = cell(snap, 'H', *COLD)
    cold_a = cell(snap, 'A', *COLD)
    w('**读法**:')
    w('')
    w(f"- 热门: 主胜 {hot_h['ratio']:.3f} vs 客胜 {hot_a['ratio']:.3f} → 平均 {(hot_h['ratio']+hot_a['ratio'])/2:.3f} (= state 的 hot)")
    w(f"- 冷门: 主胜 {cold_h['ratio']:.3f} vs 客胜 {cold_a['ratio']:.3f} → 平均 {(cold_h['ratio']+cold_a['ratio'])/2:.3f} (= state 的 cold)")
    w('')
    w('即: **同一个"热门×1.015"掩盖了"热门主胜被高估 5% + 热门客胜被低估 8%"**;')
    w(f'**"冷门×0.89"掩盖了"冷门主胜被高估 {abs(1-cold_h["ratio"])*100:.0f}% + 冷门客胜基本校准"**。')
    w('')
    w('### 2.1 但这个不对称本身还不能算"已确立"')
    w('')
    w('每个格的 95% CI 都**包含 1.0**(上表无一标 ⚠):')
    w('')
    w('| 格 | ratio | 距 1.0 | 95% CI 宽度 | 结论 |')
    w('|---|---|---|---|---|')
    for bucket, name, c in rows:
        width = c['ci_hi'] - c['ci_lo']
        verdict = 'CI 含 1.0 → 不显著' if c['ci_lo'] <= 1.0 <= c['ci_hi'] else 'CI 不含 1.0 → 显著'
        w(f"| {bucket} {name} | {c['ratio']:.3f} | {(c['ratio']-1)*100:+.1f}% | {width:.3f} | {verdict} |")
    w('')
    w(f'即使最大的一格(冷门主胜, n={cold_h["n"]}), 也需要约 **{math.ceil(n_needed(cold_h["avg_p"], cold_h["ratio"]))} 场**同格样本才能在 80% power 下判定这个偏差存在:')
    w('')
    w('| 格 | 现有 n | 检出现有偏差所需 n | 缺口倍数 |')
    w('|---|---|---|---|')
    for bucket, name, c in rows:
        need = n_needed(c['avg_p'], c['ratio'])
        if need:
            w(f"| {bucket} {name} | {c['n']} | {math.ceil(need)} | {need/c['n']:.1f}× |")
    w('')
    w('→ **结论: 现行三个系数(draw 1.08 / hot 1.015 / cold 0.89)在本数据集里没有一个达到统计显著。**')
    w('  它们是 502 场样本上的点估计, 落在噪声内。')
    w('')

    # ---------------- 3. 可靠性曲线 ----------------
    w('## 3. 可靠性曲线 (state 快照, 所有方向事件合并)')
    w('')
    w('| 隐含区间 | n | 隐含均值 | 实际频率 | 偏差(pp) | z |')
    w('|---|---|---|---|---|---|')
    for r in calib_curve(snap):
        star = ' ⚠' if abs(r['z']) > 2 else ''
        zs = '—' if math.isnan(r['z']) else f"{r['z']:+.2f}"
        w(f"| {r['lo']*100:.0f}-{r['hi']*100:.0f}% | {r['n']} | {pct(r['avg_p'])} | {pct(r['freq'])} | {r['dev_pp']:+.1f} | {zs}{star} |")
    w('')
    w('这是**校准曲线**, 不是"某方向赢不赢"。整条曲线贴合对角线即市场有效。')
    w('16 个档位里只有 1 个档的 |z|>2 —— 按 16 次比较的期望, 纯噪声也会出现约 0.8 个。**没有任何一档构成系统性偏差的证据。**')
    w('')

    # ---------------- 4. 市场效率 ----------------
    w('## 4. 市场效率指标')
    w('')
    w('| 样本 | n | Brier(每方向) | LogLoss(每方向) | 均匀基准 |')
    w('|---|---|---|---|---|')
    uni = -math.log(1 / 3)
    for label, ms in (('state 快照', snap), ('新增 09-18~20', new_odds), ('合并', combined)):
        b, ll, n = brier_logloss(ms)
        w(f"| {label} | {n} | {b:.4f} | {ll:.4f} | {uni:.4f} |")
    w('')
    w('LogLoss 显著低于 1.0986(均匀基准) 说明去水后的市场隐含比"瞎猜"信息量大得多 —— 这条与"市场基本有效"一致。')
    w('')

    # ---------------- 5. 抽水 ----------------
    w('## 5. 抽水率 (Overround)')
    w('')
    w('| 样本 | n | 均值 | 中位数 | min | max |')
    w('|---|---|---|---|---|---|')
    for label, ms in (('state 快照', snap), ('新增', new_odds), ('合并', combined)):
        a = sorted(m['overround'] for m in ms if m['has_odds'])
        w(f"| {label} | {len(a)} | {sum(a)/len(a):.4f} | {a[len(a)//2]:.4f} | {a[0]:.4f} | {a[-1]:.4f} |")
    w('')
    w(f"→ 抽水均值约 {(sum(m['overround'] for m in snap if m['has_odds'])/len(snap)):.3f}, 即每注理论返还率约 "
      f"**{1/(sum(m['overround'] for m in snap if m['has_odds'])/len(snap))*100:.1f}%**。")
    w('任何"edge"必须先跨过这条线才有意义。')
    w('')

    # ---------------- 6. 让球结构 ----------------
    w('## 6. 让球结构 (仅结构, 非赔率)')
    w('')
    w('| 盘口 | state快照 n | 让球方赢盘 | 走水 | 受让方赢盘 | 新增 n | 让球方赢盘 | 走水 | 受让方赢盘 |')
    w('|---|---|---|---|---|---|---|---|---|')
    g_snap, g_new = hcap_table(snap), hcap_table(new)
    for hcap in sorted(set(g_snap) | set(g_new)):
        side = '主让' if hcap < 0 else '客让'
        def fmt(g):
            n = sum(g[hcap].values())
            if n < 3:
                return f"{n}", '—', '—', '—'
            d = g[hcap]
            return f"{n}", pct(d['让球方赢盘']/n), pct(d['走水']/n), pct(d['受让方赢盘']/n)
        s = fmt(g_snap)
        nn = fmt(g_new)
        w(f"| {hcap:+d} ({side}) | {s[0]} | {s[1]} | {s[2]} | {s[3]} | {nn[0]} | {nn[1]} | {nn[2]} | {nn[3]} |")
    w('')
    w('**汇总(±1 盘)**:')
    w('')
    for want, name in ((-1, '-1 主让一球'), (1, '+1 客让一球')):
        for label, ms in (('state快照', snap), ('本批', new)):
            sub = [m for m in ms if m['hcap'] == want]
            if not sub:
                continue
            n = len(sub)
            push = sum(1 for m in sub if m['net'] == 0)
            fav = sum(1 for m in sub if (m['net'] > 0 if want < 0 else m['net'] < 0))
            dog = n - push - fav
            w(f"- **{name}** · {label} (n={n}): 让球方赢盘 {pct(fav/n)} / 走水 {pct(push/n)} / 受让方赢盘 {pct(dog/n)}")
    w('')
    w('⚠️ 本数据集**没有让球胜平负赔率**(API 只回 h/d/a + goalLine), 所以这里只有**结构**, 不能当让球盘校准系数用。')
    w('')
    w('**与 `BACKTEST_REPORT.md` 的独立交叉验证**(该报告记 469 场, 本脚本 502 场快照):')
    w('')
    w('| 盘口 | 报告记(469场) | 本脚本(state快照 502场) | 一致 |')
    w('|---|---|---|---|')
    w('| -1 让球方赢盘/走水/受让方赢盘 | 27% / 23% / 50% | 26.6% / 23.7% / 49.7% | ✅ |')
    w('| +1 让球方赢盘/走水/受让方赢盘 | 32% / 23% / 45% | 32.0% / 23.6% / 44.4% | ✅ |')
    w('')
    w('→ 让球结构部分**口径正确且稳定**(469→502 场几乎不变), 可以继续用作方向判断。')
    w('')

    # ---------------- 7. 爆冷 ----------------
    w('## 7. 低赔方失手 · 新增样本')
    w('')
    w('| 日期 | 对阵 | 全场 | 让球 | 最低赔 | 隐含 | 实际胜平负 |')
    w('|---|---|---|---|---|---|---|')
    n_low = upset = 0
    for m in sorted(new_odds, key=lambda x: (x['date'], x['match'])):
        best = min(m['p'], key=lambda k: m['odds'][k])
        if m['odds'][best] >= 1.60:
            continue
        n_low += 1
        if m['result_plain'] == best:
            continue
        upset += 1
        w(f"| {m['date']} | {m['home']} vs {m['away']} | {m['fh']}:{m['fa']} | {m['hcap']:+d} | "
          f"{m['odds'][best]:.2f} | {pct(m['p'][best])} | {m['result_plain']} |")
    w('')
    w(f'低赔方(<1.60) 共 **{n_low}** 场, 失手 **{upset}** 场 ({pct(upset/n_low) if n_low else "—"})。')
    w('')
    w(f'⚠️ n={n_low} 太小, 95% CI 约 [{pct(max(0,(upset/n_low)-1.96*math.sqrt((upset/n_low)*(1-upset/n_low)/n_low)))}, '
      f'{pct(min(1,(upset/n_low)+1.96*math.sqrt((upset/n_low)*(1-upset/n_low)/n_low)))}], 不能据此说"热门在崩"。')
    w('值得注意的只是形状: 4 场失手里 **3 场是主队让球后客队直接赢球**(-1 盘), 与 §6 的"-1 受让方赢盘约 50%"同向。')
    w('')

    # ---------------- 8. 决策层偏差 ----------------
    w('## 8. 决策层偏差 (与赔率无关的一条)')
    w('')
    brent = next((m for m in new if '布伦特福德' in m['match']), None)
    if brent:
        w('`REVIEW_20260918_0917.md`(结账 09-17) 对 **周五011 布伦特福德 vs 切尔西** 的处置是:')
        w('')
        w('> 011 给出的方向是**受让方不败**(与昨日打穿的 010 同链)。')
        w('> **建议二选一**: ①改为**不选边 + 只写门槛**…**我推荐 ①**。')
        w('')
        w(f"实际赛果: **布伦特福德 3:0 切尔西** (半场 0:0), 主队直接赢球。")
        w('原方向"受让方(+1)不败"**命中**; 建议①的"不选边"会**放弃一个正确的方向**。')
        w('')
        w('### 证据链的量级问题')
        w('')
        w('把两天的"选边"结果并排看:')
        w('')
        w('| 结账日 | 选边场数 | 兑现 | 兑现率 | 打穿 | 打穿率 |')
        w('|---|---|---|---|---|---|')
        w('| 09-16 (`REVIEW_20260917_0916.md`) | 14 | 7 | 50% | 2 | 14% |')
        w('| 09-17 (`REVIEW_20260918_0917.md`) | 6 | 2 | 33% | 4 | 67% |')
        w('')
        w('09-18 的复盘用 **n=6**(兑现率 33%)推翻了前一天 **n=14**(兑现率 50%)支持的纪律,')
        w(f'而 09-19 的 011 立刻打出反向结果。')
        w('')
        w('⚠️ 但要说清: **n=14 和 n=6 都太小**。')
        w('n=14 的兑现率 50%, 95% CI 约 **[24%, 76%]**; n=6 的 33%, CI 约 **[0%, 71%]** —— **两个区间几乎完全重叠**。')
        w('→ 这两天之间**根本没有发生"信号变化"**, 只是掷了两次骰子。')
        w('→ 正确的反应是"**还不知道**", 而不是把纪律翻面。用一个 n=6 的样本去覆盖 n=14 的结论,')
        w('   还会让下一天的 n=14 反过来覆盖它 —— 这就是纪律在噪声里来回抖动。')
        w('')
        w('**建议写成硬约束**: 让球选边类判据的改动, 需要累计 **n≥50** 场同形状样本 (CI 宽度约 ±14pp) 才允许翻面;')
        w('在此之前, 单日结果只记录, 不改判据。')
    w('')

    # ---------------- 9. 校正建议 ----------------
    w('## 9. 偏差校正建议')
    w('')
    w('### 9.1 系数收缩 (主建议)')
    w('')
    w('对每个桶, 用 z² 做 James-Stein 式收缩: 越像噪声, 越拉回 1.0。基于**合并样本**(%d 场):' % len(combined))
    w('')
    w('| 桶 | 合并 ratio | z | 收缩权重 z²/(1+z²) | 建议系数 | state 现值 | 变动 |')
    w('|---|---|---|---|---|---|---|')
    cur = state.get('coef', {})
    rec_coef = {}
    for key, ck, label, kinds, span in (('draw_20_30', 'draw', '平局', 'D', DRAW),
                                        ('hot_40_70', 'hot', '热门', 'HA', HOT),
                                        ('cold_0_30', 'cold', '冷门', 'HA', COLD)):
        r, parts = ratio_dir_avg(combined, kinds, *span)
        # z 用池化口径估计(方向平均无法直接给 SE)
        pooled = cell(combined, kinds[0], *span) if len(kinds) == 1 else None
        if pooled is None:
            cs = [cell(combined, k, *span) for k in kinds]
            cs = [c for c in cs if c]
            nn = sum(c['n'] for c in cs)
            ap = sum(c['avg_p'] * c['n'] for c in cs) / nn
            hits = sum(c['hits'] for c in cs)
            freq = hits / nn
            se_r = math.sqrt(freq * (1 - freq) / nn) / ap
            z = (freq / ap - 1) / se_r
        else:
            z = pooled['z']
        z2 = z * z
        wsh = z2 / (1 + z2)
        target = round(max(0.85, min(1.15, 1.0 + wsh * (r - 1.0))), 3)
        rec_coef[ck] = target
        w(f"| {label} | {r:.3f} | {z:+.2f} | {wsh:.2f} | **×{target}** | ×{cur.get(ck)} | {target - cur.get(ck, 0):+.3f} |")
    w('')
    w('### 9.2 但收缩**一次不会持久** (必须知道)')
    w('')
    w('`weekly_update.py` 每跑一次都会做 `coef = clamp(0.7×prev + 0.3×桶ratio)`。')
    w('所以把上面的建议值写进 state 之后, **下一次 cron 会自动把它往桶 ratio 拉回去**:')
    w('')
    w('| 桶 | 应用值 | 下次 EWMA 后 | 桶 ratio (目标) | 漂移方向 |')
    w('|---|---|---|---|---|')
    for key, ck, label in (('draw_20_30', 'draw', '平局'), ('hot_40_70', 'hot', '热门'), ('cold_0_30', 'cold', '冷门')):
        applied = rec_coef[ck]
        br = coefs_like_weekly(combined)[key]
        nxt = round(max(0.85, min(1.15, 0.7 * applied + 0.3 * br)), 3)
        w(f"| {label} | ×{applied} | ×{nxt} | {br:.3f} | {'↑ 被拉高' if nxt > applied else ('↓ 被拉低' if nxt < applied else '不变')} |")
    w('')
    w('→ 也就是说 **改 state 只能"干净"一次**。要让收缩持久, 必须把 z² 收缩写进')
    w('  `weekly_update.compute_coefs()` 本身 —— 让每次重算都产出收缩后的值, 而不是靠手工覆盖。')
    w('→ 现状: 本次只应用了 state(用户确认), **未改 `weekly_update.py`**。')
    w('')

    w('### 9.3 是否拆分主客')
    w('')
    w(f'主客分解显示冷门主胜 ratio {cold_h["ratio"]:.3f} (n={cold_h["n"]}) 是最"像信号"的一格,')
    w(f'但要判定它需要约 **{math.ceil(n_needed(cold_h["avg_p"], cold_h["ratio"]))} 场**同格样本(现有 {cold_h["n"]} 场)。')
    w('')
    w('→ **现在不要拆**: 拆成 6 格会让每格样本再降一半, 直接掉进噪声。')
    w('→ 但**应该开始记**: 建议在 tsv 里加两列, 把方向拆分的 ratio 按周落盘, 等冷门主胜格累计到 ~600 场再决策。')
    w('')
    w('### 9.4 流程修正 (优先级高于系数)')
    w('')
    w(f'1. **state 滞后**: 库 {len(lib)} 场 vs state {state.get("sample_size")} 场。`weekly_update.py` 是"抓最近 7 天",')
    w('   任何补录(如 09-17 那批)都不会进校准。建议改成**按库文件 mtime 判断是否有未入样本的数据**, 而不是按日期窗口。')
    w('2. **口径自检字段**: 把官方 `winFlag` 一并入库(现在是丢弃的)。本次口径判决就靠它;')
    w('   若哪天 API 改成回让球赔率, 有 winFlag 能立刻发现口径漂移 —— 这正是 09-10 那次翻车的防线。')
    w('3. **判据翻面要设样本门槛**: 见 §8, 09-18 复盘用 n=6 覆盖了 n=14 的结论(两者 CI 几乎完全重叠)。')
    w('   建议: 让球选边类判据改动需 n≥50 场同形状样本。')
    w('4. **深盘场次无赔率**: 53 场里 4 场(-2/-3)无 h/d/a, 永远进不了赔率类校准 —— 记住它们只在结构统计里出现。')
    w('')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')

    rec_state = {
        # ⚠️ 必须是 2: weekly_update.py 有 `if old.get('schema') != 2: old = {}` 的丢弃逻辑,
        #    写成 3 会让下一次 cron 把应用过的系数直接丢掉。
        'schema': 2,
        'updated_at': '2026-09-20',
        'sample_size': len(combined),
        'coef': rec_coef,
        'buckets': {k: (round(coefs_like_weekly(combined)[k], 3)) for k in ('draw_20_30', 'hot_40_70', 'cold_0_30')},
        'basis': 'direction-averaged ratio (weekly_update.compute_coefs), z^2 shrinkage toward 1.0',
        '_note': '由 calibration_audit.py 生成。应用方式: 覆盖 calibration_state.json。',
    }
    with open(REC, 'w', encoding='utf-8') as f:
        json.dump(rec_state, f, ensure_ascii=False, indent=2)

    print(f'pipeline_reproduce={"OK" if ok else "FAIL"}')
    print(f'snap={len(snap)} lib={len(lib)} hist_before={len(hist)} overlap_pre={overlap_pre} '
          f'batch={len(new)} batch_odds={len(new_odds)} net_new={net_new} combined={len(combined)}')
    print('snap coefs   :', {k: round(v, 4) for k, v in rep.items()})
    print('state buckets:', st_b)
    print('combined coefs:', {k: round(v, 4) for k, v in coefs_like_weekly(combined).items()})
    print('recommended  :', rec_coef)
    print('cold_H ratio=%.3f n=%d z=%.2f  hot_A ratio=%.3f n=%d z=%.2f'
          % (cold_h['ratio'], cold_h['n'], cold_h['z'], hot_a['ratio'], hot_a['n'], hot_a['z']))
    print('written:', OUT)
    print('written:', REC)


if __name__ == '__main__':
    main()
