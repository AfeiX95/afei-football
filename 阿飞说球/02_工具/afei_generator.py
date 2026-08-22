# -*- coding: utf-8 -*-
"""
AFEI 比赛分析通用生成器 v1.0
================================
用法:
    python afei_generator.py --config <match.json>

输入: JSON 配置文件(比赛数据 + 文章段落结构)
输出: 阿飞说球/04_赛事文章/<主队>vs<客队>/
    ├── charts/            (5张对比分析图,150dpi PNG)
    ├── <主队>vs<客队>_赛事前瞻.md
    └── <主队>vs<客队>_赛事前瞻.docx  (含图,头条号/Word双用)

特性:
    - 泊松模型数字自动计算,表格数字与图表永远一致(不手抄)
    - 倒金字塔文章骨架:信息卡 → 核心偏差 → 基本面 → 模型 → 胜负点 → 冷门路径
    - 模型输出(终端):胜平负/比分EV/Kelly仓位(仅供内部,不进文章,合规)
"""
import argparse
import json
import math
import os
import re
import sys
from itertools import product

# ---------------- 模型核心 ----------------
def poisson_pmf(k, lam):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def run_model(cfg):
    """L0→L4 完整模型,返回全部数值"""
    odds = cfg['odds']
    st = cfg['strategy']
    th, ta = cfg['teams']['home'], cfg['teams']['away']

    # L0.5 状态修正: 近5场 W+0.08 / D+0.02 / L-0.05 (±0.25)
    def form_adj(f):
        return f['w'] * 0.08 + f['d'] * 0.02 + f['l'] * (-0.05)

    h_form, a_form = form_adj(st['home_form']), form_adj(st['away_form'])

    # L1 xG → λ
    h_xgf = th['gf'] * 0.92 * st['home_mult']
    a_xgf = ta['gf'] * 0.92 * st['away_mult']
    h_xga = th['ga'] * 1.08
    a_xga = ta['ga'] * 1.08
    lam_h = (h_xgf + a_xga) / 2 + st['home_adv'] + h_form
    lam_a = (a_xgf + h_xga) / 2 + a_form

    # L1.5 杯赛次回合战意修正(2026-08-07 复盘: 维多利亚首回合2-0领先,次回合0-4被翻盘)
    # 首回合分差≥2球时: 领先方保守(λ×0.82), 落后方背水一战(λ×1.12)
    fls = cfg.get('first_leg_score')
    if fls and isinstance(fls, dict) and 'home' in fls and 'away' in fls:
        lead = fls['home'] - fls['away']
        if abs(lead) >= 2:
            if lead > 0:
                lam_h *= 0.82
                lam_a *= 1.12
            else:
                lam_a *= 0.82
                lam_h *= 1.12
            print(f"  ⚠ 战意修正: 首回合分差{abs(lead)}球,领先方进攻×0.82,落后方背水一战×1.12")

    # L1.6 防守惩罚: 对手场均失球≥1.6时, 本方攻击力×1.06(弱旅防线放大强队火力)
    if ta['ga'] >= 1.6:
        lam_h *= 1.06
    if th['ga'] >= 1.6:
        lam_a *= 1.06

    # 比分矩阵
    MAXG = 8
    probs = {(h, a): poisson_pmf(h, lam_h) * poisson_pmf(a, lam_a)
             for h, a in product(range(MAXG), repeat=2)}
    pH = sum(p for (h, a), p in probs.items() if h > a)
    pD = sum(p for (h, a), p in probs.items() if h == a)
    pA = sum(p for (h, a), p in probs.items() if h < a)

    # 市场去水
    inv = {k: 1 / v for k, v in odds.items()}
    S = sum(inv.values())
    pM = {k: v / S for k, v in inv.items()}

    # L2.5 竞彩市场校准(回测自动演进,见 00_引擎/backtest/)
    # 发现: 竞彩定价保守 → 平局/冷门隐含虚高, 热门隐含偏低
    # 注意: 回测对象是"让球盘", 校准系数只适用于让球盘(market_type=handicap);
    #       非让球欧赔(默认 european)用温和系数, 避免过度修正
    cal_cfg = cfg.get('market_calibration', {'enabled': True})
    pM_cal = dict(pM)
    if cal_cfg.get('enabled', True):
        market_type = cfg.get('market_type', 'european')
        if market_type == 'handicap':
            # 让球盘: 用每周回测演进系数(calibration_state.json)
            coef = {'draw': 0.85, 'hot': 1.08, 'cold': 0.90}
            try:
                state_path = os.path.normpath(os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), '..', '..',
                    '00_引擎', 'backtest', 'calibration_state.json'))
                if os.path.exists(state_path):
                    with open(state_path, encoding='utf-8') as _f:
                        _s = json.load(_f)
                    coef.update({k: _s['coef'][k] for k in coef if k in _s.get('coef', {})})
            except Exception:
                pass
        else:
            # 非让球欧赔: 温和系数(方向性修正, 防止让球盘结论过度外推)
            coef = {'draw': 0.90, 'hot': 1.05, 'cold': 0.95}
        for k in 'HDA':
            p = pM[k]
            if k == 'D':
                pM_cal[k] = min(max(p * coef['draw'], 0.03), 0.92)   # 平局虚高
            else:
                if p >= 0.40:
                    pM_cal[k] = min(max(p * coef['hot'], 0.03), 0.92)  # 热门被低估
                elif p < 0.30:
                    pM_cal[k] = min(max(p * coef['cold'], 0.03), 0.92) # 冷门虚高
                # 30~40% 区间基本校准, 不动
        # 归一化
        s = sum(pM_cal.values())
        pM_cal = {k: v / s for k, v in pM_cal.items()}

    # 区间/大小球/双单
    p_over25 = sum(p for (h, a), p in probs.items() if h + a > 2.5)
    p_0_1 = sum(p for (h, a), p in probs.items() if 0 <= h + a <= 1)
    p_2_3 = sum(p for (h, a), p in probs.items() if 2 <= h + a <= 3)
    p_4p = sum(p for (h, a), p in probs.items() if h + a >= 4)

    # 晋级推演(可配置)
    draw_pen = cfg.get('draw_to_penalties', True)
    promo = cfg.get('promotion', 'win')   # 'win'=赢球即晋级; 'win_by_2'=必须净胜2球+(两回合落后场景)
    p_net1 = sum(p for (h, a), p in probs.items() if h - a == 1)
    p_net2 = sum(p for (h, a), p in probs.items() if h - a >= 2)
    p_net2exact = sum(p for (h, a), p in probs.items() if h - a == 2)
    p_net3 = sum(p for (h, a), p in probs.items() if h - a >= 3)
    if promo == 'win_by_2':
        promote_h = (p_net2 - p_net2exact) + p_net2exact * 0.5
    elif promo == 'win_by_1':
        # 落后1球: 净胜2+直接晋级, 恰好净胜1→总比分平→加时/点球(五五开)
        promote_h = p_net2 + p_net1 * 0.5
    else:
        promote_h = pH + (pD * 0.5 if draw_pen else 0)
    promote_a = 1 - promote_h

    # 比分EV(内部参考)
    score_odds = {(int(s[0]), int(s[1])): float(s[2]) for s in cfg.get('score_odds', [])}
    evs = []
    for sc, p in probs.items():
        if sc in score_odds:
            o = score_odds[sc]
            evs.append((p * o - 1, sc, p, o))
    evs.sort(reverse=True)

    # Kelly(内部参考)
    kelly = {}
    for k in ('H', 'A'):
        o = odds[k]
        b = o - 1
        p = {'H': pH, 'A': pA}[k]
        f = (b * p - (1 - p)) / b
        kelly[k] = max(f * 0.5, 0)

    return {
        'lam_h': lam_h, 'lam_a': lam_a,
        'probs': probs,
        'pH': pH, 'pD': pD, 'pA': pA,
        'pM': pM, 'pM_cal': pM_cal,
        'p_over25': p_over25,
        'p_0_1': p_0_1, 'p_2_3': p_2_3, 'p_4p': p_4p,
        'promote_h': promote_h, 'promote_a': promote_a,
        'draw_pen': draw_pen,
        'p_net1': p_net1, 'p_net2': p_net2, 'p_net2exact': p_net2exact, 'p_net3': p_net3,
        # 让球盘维度(2026-08-22): 模型侧净胜球概率, 供 market_type=handicap 时与让球盘隐含对比
        # H=净胜3+(让球胜) D=恰好净胜2(让球平) A=净胜≤1(让球负)
        'hc': {'H': p_net3, 'D': p_net2exact, 'A': 1 - p_net2},
        'evs': evs, 'kelly': kelly,
        'exp_goals': lam_h + lam_a,
    }

# ---------------- 图表 ----------------
def make_charts(cfg, m, out_dir):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import numpy as np

    # 中文字体自动探测(2026-08-22:不再硬编码单一路径,跨机器/系统可用)
    _font_candidates = [
        r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\msyhbd.ttc',
        r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\simsun.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',  # Linux
        '/System/Library/Fonts/PingFang.ttc',                      # macOS
    ]
    for fp in _font_candidates:
        try:
            if os.path.exists(fp):
                fm.fontManager.addfont(fp)
        except Exception:
            pass
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['figure.dpi'] = 150

    th, ta = cfg['teams']['home'], cfg['teams']['away']
    r10 = cfg['recent10']
    probs = m['probs']
    made = []

    # 图1 胜平负构成
    if cfg['charts'].get('wdl', True):
        cats = [f"{th['name']}·近10场", f"{th['name']}·近10{th['special_label']}",
                f"{ta['name']}·近10场", f"{ta['name']}·近10{ta['special_label']}"]
        win = [r10['h_all'][0], r10['h_home'][0], r10['a_all'][0], r10['a_away'][0]]
        drw = [r10['h_all'][1], r10['h_home'][1], r10['a_all'][1], r10['a_away'][1]]
        los = [r10['h_all'][2], r10['h_home'][2], r10['a_all'][2], r10['a_away'][2]]
        fig, ax = plt.subplots(figsize=(8.5, 4.6))
        y = np.arange(len(cats))
        ax.barh(y, win, color='#2e9e5b', label='胜')
        ax.barh(y, drw, left=win, color='#f0a500', label='平')
        ax.barh(y, los, left=[a + b for a, b in zip(win, drw)], color='#d64541', label='负')
        for i, (w, d, l) in enumerate(zip(win, drw, los)):
            x = 0
            for v, c in [(w, '#fff'), (d, '#222'), (l, '#fff')]:
                if v > 6:
                    ax.text(x + v / 2, i, f'{v:.0f}%', ha='center', va='center', color=c, fontsize=10, fontweight='bold')
                x += v
        ax.set_yticks(y); ax.set_yticklabels(cats, fontsize=11)
        ax.set_xlim(0, 100); ax.set_xlabel('占比 (%)', fontsize=10)
        ax.set_title('近10场胜平负构成对比', fontsize=14, fontweight='bold', pad=12)
        ax.legend(loc='lower right', ncol=3, frameon=False, fontsize=10)
        ax.spines[['top', 'right']].set_visible(False)
        plt.tight_layout()
        fp = os.path.join(out_dir, 'chart1_近10场胜负构成.png')
        plt.savefig(fp); plt.close(); made.append(fp)

    # 图2 场均进失球(近10场 vs 近6场)
    if cfg['charts'].get('goals', True):
        fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.4))
        for ax, (name, gf, ga) in zip(axes, [
            (th['name'], [th['gf'], th['recent']['gf']], [th['ga'], th['recent']['ga']]),
            (ta['name'], [ta['gf'], ta['recent']['gf']], [ta['ga'], ta['recent']['ga']]),
        ]):
            gfc = ['近10场', '近6场']
            x = np.arange(2); w = 0.34
            b1 = ax.bar(x - w / 2, gf, w, color='#2e9e5b', label='场均进球')
            b2 = ax.bar(x + w / 2, ga, w, color='#d64541', label='场均失球')
            for b in list(b1) + list(b2):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.04,
                        f'{b.get_height():.2f}', ha='center', fontsize=9.5)
            ax.set_xticks(x); ax.set_xticklabels(gfc, fontsize=11)
            ax.set_ylim(0, 2.3); ax.set_title(name, fontsize=13, fontweight='bold')
            ax.spines[['top', 'right']].set_visible(False)
        axes[0].legend(frameon=False, fontsize=10, loc='upper right')
        fig.suptitle('场均进球 / 失球对比', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        fp = os.path.join(out_dir, 'chart2_场均进失球.png')
        plt.savefig(fp); plt.close(); made.append(fp)

    # 图3 泊松比分热力图
    if cfg['charts'].get('heatmap', True):
        M = 6
        mat = np.zeros((M, M))
        for h in range(M):
            for a in range(M):
                mat[h, a] = probs[(h, a)] * 100
        fig, ax = plt.subplots(figsize=(7.6, 6.2))
        im = ax.imshow(mat, cmap='YlGnBu', vmin=0, vmax=11)
        ax.set_xticks(range(M)); ax.set_yticks(range(M))
        ax.set_xticklabels([f'{i}球' for i in range(M)], fontsize=10)
        ax.set_yticklabels([f'{i}球' for i in range(M)], fontsize=10)
        ax.set_xlabel(f"{ta['name']} 进球", fontsize=11)
        ax.set_ylabel(f"{th['name']} 进球", fontsize=11)
        ax.set_title(f'泊松比分概率矩阵 (%)  λ主={m["lam_h"]:.2f} / λ客={m["lam_a"]:.2f}',
                     fontsize=13, fontweight='bold', pad=12)
        for h in range(M):
            for a in range(M):
                v = mat[h, a]
                if v >= 0.5:
                    ax.text(a, h, f'{v:.1f}', ha='center', va='center', fontsize=9,
                            color='white' if v > 5.5 else '#222')
        bh, ba = max(probs, key=lambda k: probs[k])
        ax.add_patch(plt.Rectangle((ba - 0.5, bh - 0.5), 1, 1, fill=False, edgecolor='#d64541', lw=2.5))
        ax.text(ba, bh, f'\n★ {bh}-{ba}', ha='center', va='top', color='#d64541', fontsize=12, fontweight='bold')
        fig.colorbar(im, ax=ax, shrink=0.85, label='概率 %')
        plt.tight_layout()
        fp = os.path.join(out_dir, 'chart3_泊松比分热力图.png')
        plt.savefig(fp); plt.close(); made.append(fp)

    # 图4 模型vs市场 + Edge
    if cfg['charts'].get('edge', True):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.4),
                                       gridspec_kw={'width_ratios': [1.15, 1]})
        labels = ['主胜', '平局', '客胜']
        if cfg.get('market_type') == 'handicap':
            # 让球盘: 模型侧用净胜球概率(2026-08-22 修正)
            hc = m['hc']
            model = [hc['H'] * 100, hc['D'] * 100, hc['A'] * 100]
            labels = ['让胜\n(净胜3+)', '让平\n(恰好净胜2)', '让负\n(净胜≤1)']
        else:
            model = [m['pH'] * 100, m['pD'] * 100, m['pA'] * 100]
        market = [m['pM']['H'] * 100, m['pM']['D'] * 100, m['pM']['A'] * 100]
        x = np.arange(3); w = 0.34
        b1 = ax1.bar(x - w / 2, model, w, color='#2e9e5b', label='模型概率')
        b2 = ax1.bar(x + w / 2, market, w, color='#7f8c8d', label='市场隐含')
        for b in list(b1) + list(b2):
            ax1.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.8,
                     f'{b.get_height():.1f}%', ha='center', fontsize=9.5)
        ax1.set_xticks(x); ax1.set_xticklabels(labels, fontsize=12)
        ax1.set_ylim(0, 68)
        ax1.set_title('模型概率 vs 市场隐含概率', fontsize=13, fontweight='bold')
        ax1.legend(frameon=False, fontsize=10)
        ax1.spines[['top', 'right']].set_visible(False)
        if cfg.get('market_type') == 'handicap':
            hc = m['hc']
            edges = [(hc['H'] - m['pM']['H']) * 100, (hc['D'] - m['pM']['D']) * 100,
                     (hc['A'] - m['pM']['A']) * 100]
            edge_labels = ['让胜', '让平', '让负']
        else:
            edges = [(m['pH'] - m['pM']['H']) * 100, (m['pD'] - m['pM']['D']) * 100,
                     (m['pA'] - m['pM']['A']) * 100]
            edge_labels = labels
        colors = ['#d64541' if e > 0 else '#95a5a6' for e in edges]
        bars = ax2.bar(edge_labels, edges, 0.5, color=colors)
        for b, e in zip(bars, edges):
            ax2.text(b.get_x() + b.get_width() / 2, e + (0.5 if e >= 0 else -1.6),
                     f'{e:+.1f}%', ha='center', fontsize=11, fontweight='bold')
        ax2.axhline(0, color='#333', lw=1)
        ax2.axhline(3, color='#f0a500', ls='--', lw=1.2)
        ax2.axhline(6, color='#2e9e5b', ls='--', lw=1.2)
        ax2.text(2.42, 3.3, '中价值线 +3%', fontsize=8.5, color='#b07d00', ha='right')
        ax2.text(2.42, 6.3, '强价值线 +6%', fontsize=8.5, color='#1d6e3f', ha='right')
        ax2.set_ylim(-10, 13)
        ax2.set_title('Edge 检测 (模型 − 市场)', fontsize=13, fontweight='bold')
        ax2.spines[['top', 'right']].set_visible(False)
        fig.suptitle(f"模型 vs 市场:{th['name']}主胜 Edge +{edges[0]:.1f}%",
                     fontsize=14, fontweight='bold', y=1.03)
        plt.tight_layout()
        fp = os.path.join(out_dir, 'chart4_模型vs市场Edge.png')
        plt.savefig(fp); plt.close(); made.append(fp)

    # 图5 晋级概率
    if cfg['charts'].get('promote', True):
        fig, ax = plt.subplots(figsize=(6.6, 4.6))
        if cfg.get('promotion', 'win') == 'win_by_2':
            p3plus = m['p_net2'] - m['p_net2exact']
            vals = [p3plus * 100, m['p_net2exact'] * 50, m['promote_a'] * 100]
            labs = [f"{th['name']}净胜2+直接晋级 {p3plus*100:.1f}%",
                    f"恰好净胜2→点球 {m['p_net2exact']*50:.1f}%",
                    f"{ta['name']}晋级 {m['promote_a']*100:.1f}%"]
        elif cfg.get('promotion', 'win') == 'win_by_1':
            vals = [m['p_net2'] * 100, m['p_net1'] * 50, m['promote_a'] * 100]
            labs = [f"{th['name']}净胜2+直接晋级 {m['p_net2']*100:.1f}%",
                    f"恰好净胜1→加时/点球 {m['p_net1']*50:.1f}%",
                    f"{ta['name']}晋级 {m['promote_a']*100:.1f}%"]
        elif m['draw_pen']:
            vals = [m['pH'] * 100, m['pD'] * 50, m['promote_a'] * 100]
            labs = [f"{th['name']}90分钟晋级 {m['pH']*100:.1f}%",
                    f'平局→点球胜 {m["pD"]*50:.1f}%',
                    f"{ta['name']}晋级 {m['promote_a']*100:.1f}%"]
        else:
            vals = [m['promote_h'] * 100, m['promote_a'] * 100]
            labs = [f"{th['name']}晋级 {m['promote_h']*100:.1f}%",
                    f"{ta['name']}晋级 {m['promote_a']*100:.1f}%"]
        cols = ['#2e9e5b', '#f0a500', '#d64541'][:len(vals)]
        wedges, _ = ax.pie(vals, colors=cols, startangle=90, counterclock=False,
                           wedgeprops=dict(width=0.42, edgecolor='white'))
        ax.text(0, 0.08, f"{m['promote_h']*100:.1f}%", ha='center', fontsize=26,
                fontweight='bold', color='#2e9e5b')
        ax.text(0, -0.22, f"{th['name']}总晋级概率", ha='center', fontsize=11, color='#555')
        ax.legend(wedges, labs, loc='center left', bbox_to_anchor=(1.0, 0.5),
                  frameon=False, fontsize=10.5)
        ax.set_title('晋级概率推演', fontsize=13, fontweight='bold', pad=14)
        plt.tight_layout()
        fp = os.path.join(out_dir, 'chart5_晋级概率.png')
        plt.savefig(fp); plt.close(); made.append(fp)

    # 图6 身价对比(2026-08-22 新增模块: 全队身价 + 队内标王)
    if cfg['charts'].get('value', False) and cfg.get('squad_value'):
        import re as _re
        def _sv_num(s):
            m = _re.search(r'([\d.]+)\s*([亿万])', str(s))
            if not m:
                return 0.0
            v = float(m.group(1))
            return v if m.group(2) == '亿' else v / 10000.0
        sv = cfg['squad_value']
        h_val, a_val = _sv_num(sv.get('home', '0')), _sv_num(sv.get('away', '0'))
        if h_val or a_val:
            fig, ax = plt.subplots(figsize=(7.8, 4.0))
            teams = [th['name'], ta['name']]
            vals = [h_val, a_val]
            bars = ax.bar(teams, vals, 0.45, color=['#2e9e5b', '#d64541'])
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v, f'{v:.2f}亿欧',
                        ha='center', va='bottom', fontsize=12, fontweight='bold')
            if sv.get('home_top'):
                ax.text(0, h_val * 0.55, sv['home_top'], ha='center', fontsize=10, color='#444')
            if sv.get('away_top'):
                ax.text(1, a_val * 0.55, sv['away_top'], ha='center', fontsize=10, color='#444')
            ax.set_ylim(0, max(vals) * 1.38)
            ax.set_ylabel('全队身价(欧元)')
            ax.set_title('全队身价对比', fontsize=13, fontweight='bold')
            ax.spines[['top', 'right']].set_visible(False)
            plt.tight_layout()
            fp = os.path.join(out_dir, 'chart6_身价对比.png')
            plt.savefig(fp); plt.close(); made.append(fp)

    # 图7 关键射手对比(2026-08-22 新增模块: 两队 top3 射手进球数)
    if cfg['charts'].get('scorers', False) and cfg.get('scorers'):
        sc = cfg['scorers']
        names, goals, colors = [], [], []
        for side, team, col in (('home', th['name'], '#2e9e5b'), ('away', ta['name'], '#d64541')):
            for p in sc.get(side, [])[:3]:
                names.append(f"{p['name']}({team})")
                goals.append(float(p.get('goals', 0)))
                colors.append(col)
        if names:
            fig, ax = plt.subplots(figsize=(7.8, 4.2))
            y = np.arange(len(names))[::-1]
            ax.barh(y, goals, 0.55, color=colors)
            for yi, g in zip(y, goals):
                ax.text(g + 0.1, yi, f'{g:g}', va='center', fontsize=10, fontweight='bold')
            ax.set_yticks(y); ax.set_yticklabels(names, fontsize=10)
            ax.set_xlabel('进球数(上赛季/近期)')
            ax.set_title('关键射手对比', fontsize=13, fontweight='bold')
            ax.spines[['top', 'right']].set_visible(False)
            plt.tight_layout()
            fp = os.path.join(out_dir, 'chart7_射手对比.png')
            plt.savefig(fp); plt.close(); made.append(fp)

    return made

# ---------------- 文章渲染(md + docx) ----------------
CHART_FILES = {
    'wdl': 'chart1_近10场胜负构成.png',
    'goals': 'chart2_场均进失球.png',
    'heatmap': 'chart3_泊松比分热力图.png',
    'edge': 'chart4_模型vs市场Edge.png',
    'promote': 'chart5_晋级概率.png',
    'value': 'chart6_身价对比.png',
    'scorers': 'chart7_射手对比.png',
}

def _scorer_rows(cfg):
    """从 cfg['scorers'] 生成射手对比表格行(两队各取前3)。"""
    sc = cfg.get('scorers', {})
    rows = []
    for side, team in (('home', cfg['teams']['home']['name']),
                       ('away', cfg['teams']['away']['name'])):
        for p in sc.get(side, [])[:3]:
            rows.append([team, p['name'], p.get('goals', '-'),
                         p.get('assists', '-'), p.get('note', '')])
    return rows

def resolve_chart(key):
    return CHART_FILES.get(key, key)


def _fmt_kwargs(m):
    """模型数字 → 段落占位符格式化参数(唯一来源, para/chart/data_para 共用)。"""
    return dict(
        lam_h=f"{m['lam_h']:.2f}", lam_a=f"{m['lam_a']:.2f}",
        exp=f"{m['exp_goals']:.2f}",
        pH=f"{m['pH']*100:.1f}", pD=f"{m['pD']*100:.1f}", pA=f"{m['pA']*100:.1f}",
        mH=f"{m['pM']['H']*100:.1f}", mD=f"{m['pM']['D']*100:.1f}", mA=f"{m['pM']['A']*100:.1f}",
        mH_cal=f"{m['pM_cal']['H']*100:.1f}", mD_cal=f"{m['pM_cal']['D']*100:.1f}", mA_cal=f"{m['pM_cal']['A']*100:.1f}",
        edgeH_cal=f"{(m['pH']-m['pM_cal']['H'])*100:+.1f}",
        edgeD_cal=f"{(m['pD']-m['pM_cal']['D'])*100:+.1f}",
        edgeA_cal=f"{(m['pA']-m['pM_cal']['A'])*100:+.1f}",
        edgeH=f"{(m['pH']-m['pM']['H'])*100:+.1f}",
        edgeH_abs=f"{abs(m['pH']-m['pM']['H'])*100:.1f}",
        edgeA_abs=f"{abs(m['pA']-m['pM']['A'])*100:.1f}",
        pH2=f"{(m['pH']+m['pD'])*100:.1f}", pa2=f"{(m['pA']+m['pD'])*100:.1f}",
        p11=f"{m['probs'].get((1,1),0)*100:.1f}", p21=f"{m['probs'].get((2,1),0)*100:.1f}",
        p01a=f"{m['probs'].get((0,1),0)*100:.1f}", p10=f"{m['probs'].get((1,0),0)*100:.1f}",
        p12=f"{m['probs'].get((1,2),0)*100:.1f}",
        p_over=f"{m['p_over25']*100:.1f}", p_under=f"{(1-m['p_over25'])*100:.1f}",
        p01=f"{m['p_0_1']*100:.1f}", p23=f"{m['p_2_3']*100:.1f}", p4p=f"{m['p_4p']*100:.1f}",
        pA2=f"{(m['pA']+m['pD'])*100:.1f}",
        prom_h=f"{m['promote_h']*100:.1f}", prom_a=f"{m['promote_a']*100:.1f}",
        prom_90=f"{m['pH']*100:.1f}", prom_pen=f"{m['pD']*50:.1f}",
        net1=f"{m['p_net1']*100:.1f}", net2=f"{m['p_net2']*100:.1f}",
        net2exact=f"{m['p_net2exact']*100:.1f}", net3=f"{m['p_net3']*100:.1f}",
        # 让球盘占位符(2026-08-22): hcH/hcD/hcA=模型让球盘概率, net1_under=净胜≤1(让球负),
        # hc_edgeX_cal=让球盘Edge校准(带符号)
        hcH=f"{m['hc']['H']*100:.1f}", hcD=f"{m['hc']['D']*100:.1f}", hcA=f"{m['hc']['A']*100:.1f}",
        net1_under=f"{(1-m['p_net2'])*100:.1f}",
        hc_edgeH_cal=f"{(m['hc']['H']-m['pM_cal']['H'])*100:+.1f}",
        hc_edgeD_cal=f"{(m['hc']['D']-m['pM_cal']['D'])*100:+.1f}",
        hc_edgeA_cal=f"{(m['hc']['A']-m['pM_cal']['A'])*100:+.1f}",
    )


def _safe_fill(text, kwargs):
    """占位符填充: 能填就填, 失败(如文本含字面量花括号)则原样返回。"""
    if '{' not in text:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return text


PLACEHOLDER_RE = re.compile(r'\{[a-zA-Z_][a-zA-Z_0-9]*\}')


def scan_leftover_placeholders(md_path, docx_path):
    """出稿后强制扫描: md + docx(含表格) 是否残留 {xxx} 占位符, 有则报错。"""
    import docx as _docx
    bad = []
    with open(md_path, encoding='utf-8') as f:
        md_text = f.read()
    for m in PLACEHOLDER_RE.finditer(md_text):
        bad.append((os.path.basename(md_path), m.group()))
    d = _docx.Document(docx_path)
    for p in d.paragraphs:
        for m in PLACEHOLDER_RE.finditer(p.text):
            bad.append((os.path.basename(docx_path), m.group()))
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                for m in PLACEHOLDER_RE.finditer(c.text):
                    bad.append((os.path.basename(docx_path), m.group()))
    if bad:
        seen = sorted(set(bad))
        print('❌ 出稿拦截: 检测到未替换的模板占位符, 禁止发布!')
        for fn, ph in seen:
            print(f'   {fn}: {ph}')
        print('   原因: config sections 中 para/chart 段落写了 {占位符}, 请改用 data_para 类型,')
        print('   或删除占位符。修复 config 后重新生成。')
        return False
    return True


def render_md(cfg, m, out_dir, out_name):
    th, ta = cfg['teams']['home'], cfg['teams']['away']
    lines = [cfg['title'], '',
             ' '.join(cfg['tags']), '',
             f"【对阵】{th['name']}(主) vs {ta['name']}(客)— {th['league']} vs {ta['league']}",
             f"【赛事】{cfg['competition']}({cfg.get('first_leg', '')})",
             f"【时间】{cfg['match_time']}",
             f"【场地】{cfg['venue']}",
             f"【天气】{cfg['weather']}", '']
    for sec in cfg['sections']:
        t = sec['type']
        if t == 'dash':
            lines += ['——', '']
        elif t == 'para':
            # 普通段落: 若误写占位符也自动填数(防呆), 无占位符则原样
            lines += [_safe_fill(sec['text'], _fmt_kwargs(m)), '']
        elif t == 'model_table':
            lines += ['| 结果 | 后台模型 | 欧赔 | 市场概率 |', '|:----|:--------:|:---:|:--------:|',
                      f"| 主胜 | {m['pH']*100:.1f}% | {cfg['odds']['H']:.2f} | {m['pM']['H']*100:.1f}% |",
                      f"| 平局 | {m['pD']*100:.1f}% | {cfg['odds']['D']:.2f} | {m['pM']['D']*100:.1f}% |",
                      f"| 客胜 | {m['pA']*100:.1f}% | {cfg['odds']['A']:.2f} | {m['pM']['A']*100:.1f}% |", '']
        elif t == 'score_table':
            top = sorted(m['probs'].items(), key=lambda kv: -kv[1])[:6]
            lines += ['| 比分 | 概率 | 参考赔率 |', '|:---:|:----:|:-------:|']
            so = {(int(s[0]), int(s[1])): float(s[2]) for s in cfg.get('score_odds', [])}
            for (h, a), p in top:
                o = so.get((h, a), '-')
                lines.append(f"| {h}-{a} | {p*100:.1f}% | {o if isinstance(o, str) else f'{o:.2f}'} |")
            lines.append('')
        elif t == 'chart':
            cap = _safe_fill(sec.get('caption', ''), _fmt_kwargs(m))
            lines += [f"![{cap}](charts/{resolve_chart(sec['chart'])})",
                      f"*{cap}*", '']
        elif t == 'data_para':
            # 数据型段落:自动填模型数字
            text = _safe_fill(sec['text'], _fmt_kwargs(m))
            lines += [text, '']
        elif t == 'scorer_table':
            # 关键射手对比表(2026-08-22 新增模块)
            rows = _scorer_rows(cfg)
            if rows:
                lines += ['| 球队 | 球员 | 进球 | 助攻 | 备注 |', '|:----:|:----:|:---:|:---:|:----|']
                for r in rows:
                    lines.append('| ' + ' | '.join(str(x) for x in r) + ' |')
                lines.append('')
        elif t == 'value_para':
            # 身价对比段(2026-08-22 新增模块)
            sv = cfg.get('squad_value')
            if sv:
                lines += [f"【身价天平】{th['name']}全队身价{sv.get('home', '—')} vs {ta['name']}全队身价{sv.get('away', '—')}, 差{sv.get('ratio', '—')}倍。队内标王: {sv.get('home_top', '—')} vs {sv.get('away_top', '—')}。来源: {sv.get('source', '德转/雷速')}。", '']
        elif t == 'player_matchup':
            # 关键球员对位(2026-08-22 新增模块): [主球员, 客球员, 分析]
            for h, a, note in cfg.get('player_matchup', []):
                lines += [f"{h} vs {a}——{note}", '']
        elif t == 'hook':
            lines += [sec['text'], '']
    lines += ['数据不会说谎,但人会。——阿飞·赛博聊球', '']
    lines += [cfg.get('ending_hook', ''), '']
    lines += [cfg.get('ending_line', ''), '']
    lines += ['【数据来源】基础数据取自竞彩官方及海外主流体育数据库,由阿飞个人足球数据模型独立推演。', '']
    lines += ['【免责声明】本文为个人数据模型推演,属体育赛事分析交流,不构成任何购彩及投注建议,请理性看待,适度娱乐。', '']
    if cfg.get('illustration'):
        # 2026-08-22 修复:illustration 为 dict 时遍历出键名(en/cn)的 bug
        lines += ['', '=== 配图关键词(供编辑检索,勿发布) ===', '']
        ill = cfg['illustration']
        if isinstance(ill, dict):
            for s in ill.values():      # {en:..., cn:...} 取关键词串
                lines += [s, '']
        else:
            for s in ill:               # 兼容 list 结构
                lines += [s, '']
    md_path = os.path.join(out_dir, out_name)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return md_path

def render_docx(cfg, m, out_dir, out_name):
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn

    th, ta = cfg['teams']['home'], cfg['teams']['away']
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(11)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    def set_font(run, size=11, bold=False, color=None, name='微软雅黑'):
        run.font.name = name
        run.font.size = Pt(size)
        run.font.bold = bold
        if color:
            run.font.color.rgb = RGBColor(*color)
        run._element.rPr.rFonts.set(qn('w:eastAsia'), name)

    def add_title(text):
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(text), size=16, bold=True)

    def add_tags(text):
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(4)
        set_font(p.add_run(text), size=11, bold=True, color=(0x1a, 0x73, 0xe8))

    def add_info_card(lines):
        for line in lines:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.3
            # 信息卡行加粗(头条排版: 【】标签醒目)
            set_font(p.add_run(line), size=10.5, bold=True, color=(0x44, 0x44, 0x44))

    def add_dash():
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run('——'), size=11, color=(0x99, 0x99, 0x99))

    # 小节标题模式(头条排版: 编号/对决/回/幕/写在前面/尾声/冷门开关等短标题行自动加粗)
    SECTION_TITLE_RE = re.compile(
        r'^(写在前面|一、|二、|三、|四、|五、|六、|七、|八、|第一回|第二回|第三回|第四回|第五回|'
        r'第一幕|第二幕|第三幕|对决[一二三四五六]|开篇|尾声|终场|冷门开关|胜负手|决胜点|'
        r'结案陈词|模型推理|线索[一二]|疑点|结语|局势定性|一句话)'
    )

    def add_para(text, bold=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.4
        stripped = text.strip()
        is_title = bool(SECTION_TITLE_RE.match(stripped)) and len(stripped) <= 40
        if is_title:
            # 小节标题: 黑体加粗 + 略大字号
            set_font(p.add_run(text), size=12, bold=True, color=(0x1a, 0x1a, 0x1a))
            return
        # 段首引导词加粗(如"冷门开关:""决胜点:""写在前面:")——引导词+正文混排场景
        m = re.match(r'^(写在前面|冷门开关|胜负手|决胜点|开篇|尾声|终场|结案陈词|局势定性|一句话)[:：]', stripped)
        if m:
            head = stripped[:m.end()]
            body = stripped[m.end():]
            set_font(p.add_run(head), bold=True)
            set_font(p.add_run(body), bold=bold)
        else:
            set_font(p.add_run(text), bold=bold)

    def add_table(headers, rows):
        t = doc.add_table(rows=1 + len(rows), cols=len(headers))
        t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, h in enumerate(headers):
            c = t.cell(0, j); c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_font(c.paragraphs[0].add_run(h), bold=True)
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                c = t.cell(i + 1, j); c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                set_font(c.paragraphs[0].add_run(str(v)))
        doc.add_paragraph()

    def add_chart(key, caption):
        fp = os.path.join(out_dir, 'charts', resolve_chart(key))
        if not os.path.exists(fp):
            return
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(fp, width=Inches(5.6))
        cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(cap.add_run(caption), size=9, color=(0x77, 0x77, 0x77))

    # 头部
    add_title(cfg['title'])
    add_tags(' '.join(cfg['tags']))
    add_info_card([
        f"【对阵】{th['name']}(主) vs {ta['name']}(客)— {th['league']} vs {ta['league']}",
        f"【赛事】{cfg['competition']}({cfg.get('first_leg', '')})",
        f"【时间】{cfg['match_time']}",
        f"【场地】{cfg['venue']}",
        f"【天气】{cfg['weather']}",
    ])

    for sec in cfg['sections']:
        t = sec['type']
        if t == 'dash':
            add_dash()
        elif t == 'para':
            # 普通段落: 若误写占位符也自动填数(防呆), 无占位符则原样
            add_para(_safe_fill(sec['text'], _fmt_kwargs(m)))
        elif t == 'model_table':
            add_table(['结果', '后台模型', '欧赔', '市场概率'],
                      [['主胜', f"{m['pH']*100:.1f}%", f"{cfg['odds']['H']:.2f}", f"{m['pM']['H']*100:.1f}%"],
                       ['平局', f"{m['pD']*100:.1f}%", f"{cfg['odds']['D']:.2f}", f"{m['pM']['D']*100:.1f}%"],
                       ['客胜', f"{m['pA']*100:.1f}%", f"{cfg['odds']['A']:.2f}", f"{m['pM']['A']*100:.1f}%"]])
        elif t == 'score_table':
            top = sorted(m['probs'].items(), key=lambda kv: -kv[1])[:6]
            so = {(int(s[0]), int(s[1])): float(s[2]) for s in cfg.get('score_odds', [])}
            rows = []
            for (h, a), p in top:
                o = so.get((h, a), '-')
                rows.append([f'{h}-{a}', f'{p*100:.1f}%', o if isinstance(o, str) else f'{o:.2f}'])
            add_table(['比分', '概率', '参考赔率'], rows)
        elif t == 'chart':
            add_chart(sec['chart'], _safe_fill(sec.get('caption', ''), _fmt_kwargs(m)))
        elif t == 'data_para':
            text = _safe_fill(sec['text'], _fmt_kwargs(m))
            add_para(text)
        elif t == 'scorer_table':
            # 关键射手对比表(2026-08-22 新增模块)
            rows = _scorer_rows(cfg)
            if rows:
                add_table(['球队', '球员', '进球', '助攻', '备注'], rows)
        elif t == 'value_para':
            # 身价对比段(2026-08-22 新增模块)
            sv = cfg.get('squad_value')
            if sv:
                add_para(f"【身价天平】{th['name']}全队身价{sv.get('home', '—')} vs {ta['name']}全队身价{sv.get('away', '—')}, 差{sv.get('ratio', '—')}倍。队内标王: {sv.get('home_top', '—')} vs {sv.get('away_top', '—')}。来源: {sv.get('source', '德转/雷速')}。")
        elif t == 'player_matchup':
            # 关键球员对位(2026-08-22 新增模块)
            for h, a, note in cfg.get('player_matchup', []):
                add_para(f"{h} vs {a}——{note}")
        elif t == 'hook':
            add_para(sec['text'])

    for line in ['数据不会说谎,但人会。——阿飞·赛博聊球', '',
                 cfg.get('ending_hook', ''), '',
                 cfg.get('ending_line', ''), '',
                 '【数据来源】基础数据取自竞彩官方及海外主流体育数据库,由阿飞个人足球数据模型独立推演。',
                 '【免责声明】本文为个人数据模型推演,属体育赛事分析交流,不构成任何购彩及投注建议,请理性看待,适度娱乐。']:
        if line:
            add_para(line)

    docx_path = os.path.join(out_dir, out_name)
    doc.save(docx_path)
    return docx_path

# ---------------- 主流程 ----------------
def main():
    ap = argparse.ArgumentParser(description='AFEI 比赛分析通用生成器')
    ap.add_argument('--config', required=True, help='JSON 配置文件路径')
    ap.add_argument('--model-only', action='store_true', help='只跑模型+打印,不生成文件')
    ap.add_argument('--kb', type=int, nargs='?', const=5, default=5, metavar='TOPK',
                    help='检索历史案例参考(知识库, 仅终端提示, 不写入文章), 默认5条, 如 --kb 3')
    args = ap.parse_args()

    with open(args.config, encoding='utf-8') as f:
        cfg = json.load(f)

    # 标题质量校验(头条爆款规范): 禁止俗语 + 长度控制
    title = cfg.get('title', '')
    banned = ['主场龙', '客场虫', '强强对话', '谁能笑到最后', '激情碰撞', '巅峰对决', '王者对决',
              '狭路相逢', '火星撞地球', '生死战一触即发', '鹿死谁手']
    hits = [w for w in banned if w in title]
    if hits:
        print(f"⚠ 标题含俗语({','.join(hits)})——无信息增量,头条展现会受影响。")
        print(f"  建议公式: 「赛事+极端数据/偏差值+市场预期冲突」, 如「意甲首轮:国米让2球深盘,盘口数据已亮翻车信号」")
    if len(title) > 30:
        print(f"⚠ 标题 {len(title)} 字,超头条 SEO 上限 30 字,建议压缩。")

    th, ta = cfg['teams']['home'], cfg['teams']['away']
    m = run_model(cfg)

    print('=' * 58)
    print(f"【模型】{th['name']} vs {ta['name']} | {cfg['competition']}")
    print(f"  λ_home={m['lam_h']:.3f} | λ_away={m['lam_a']:.3f} | 期望总进球 {m['exp_goals']:.2f}")
    print(f"  P_model: 主胜{m['pH']*100:.1f}% / 平{m['pD']*100:.1f}% / 客胜{m['pA']*100:.1f}%")
    print(f"  P_market: 主胜{m['pM']['H']*100:.1f}% / 平{m['pM']['D']*100:.1f}% / 客胜{m['pM']['A']*100:.1f}%")
    print(f"  Edge: 主{(m['pH']-m['pM']['H'])*100:+.1f}% / 平{(m['pD']-m['pM']['D'])*100:+.1f}% / 客{(m['pA']-m['pM']['A'])*100:+.1f}%")
    print(f"  P_market校准: 主{m['pM_cal']['H']*100:.1f}% / 平{m['pM_cal']['D']*100:.1f}% / 客{m['pM_cal']['A']*100:.1f}%")
    if cfg.get('market_type') == 'handicap':
        # 让球盘: Edge 用净胜球维度对比(2026-08-22 修正, 避免标准胜平负vs让球盘的假Edge)
        hc = m['hc']
        print(f"  P_model(让球盘): 让胜{hc['H']*100:.1f}% / 让平{hc['D']*100:.1f}% / 让负{hc['A']*100:.1f}%")
        print(f"  Edge校准(让球盘): 让胜{(hc['H']-m['pM_cal']['H'])*100:+.1f}% / 让平{(hc['D']-m['pM_cal']['D'])*100:+.1f}% / 让负{(hc['A']-m['pM_cal']['A'])*100:+.1f}%  ← 价值判断用此")
    else:
        print(f"  Edge校准: 主{(m['pH']-m['pM_cal']['H'])*100:+.1f}% / 平{(m['pD']-m['pM_cal']['D'])*100:+.1f}% / 客{(m['pA']-m['pM_cal']['A'])*100:+.1f}%  ← 价值判断用此")
    print(f"  大2.5球 {m['p_over25']*100:.1f}% | 晋级(主) {m['promote_h']*100:.1f}%")
    print(f"  比分EV Top3: " + ' | '.join(
        f"{s[1][0]}-{s[1][1]} EV={s[0]:+.2f}" for s in m['evs'][:3]))
    print(f"  Kelly: " + ' | '.join(f"{k}@{cfg['odds'][k]:.2f} {v*100:.1f}%" for k, v in m['kelly'].items() if v > 0))
    print('=' * 58)

    # 历史案例参考(知识库检索, 仅供写稿参考, 不写入文章)
    if args.kb:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from kb.kb_core import kb_search, match_query
            query = match_query(th['name'], ta['name'], th['league'],
                                cfg['competition'], '盘口 数据 历史交锋')
            hits = kb_search(query, topk=args.kb)
            if hits:
                print(f"\n【历史案例参考】知识库检索 top{args.kb} (写稿参考, 不进文章):")
                for i, h in enumerate(hits, 1):
                    t = h['text'].replace('\n', ' ')
                    if len(t) > 90:
                        t = t[:90] + '…'
                    print(f"  [{i}] 相关度{h['score']:.3f} | {h['match']} | {h['section']}")
                    print(f"      {t}")
                    print(f"      来源: 04_赛事文章/{h['source']}")
            else:
                print("\n【历史案例参考】知识库索引不存在, 先运行: python kb/build_kb.py")
        except Exception as e:
            print(f"\n【历史案例参考】检索失败: {e}")

    if args.model_only:
        return

    # 输出目录: 04_赛事文章/<YYYY-MM>/<主队>vs<客队> (按产出月份自动归档)
    from datetime import date
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           '04_赛事文章', date.today().strftime('%Y-%m'),
                           f"{th['name']}vs{ta['name']}")
    charts_dir = os.path.join(out_dir, 'charts')
    os.makedirs(charts_dir, exist_ok=True)

    made = make_charts(cfg, m, charts_dir)
    print(f'  图表 {len(made)} 张 → {charts_dir}')

    out_name = f"{th['name']}vs{ta['name']}_赛事前瞻"
    md_path = render_md(cfg, m, out_dir, out_name + '.md')
    print('  MD →', md_path)
    try:
        docx_path = render_docx(cfg, m, out_dir, out_name + '.docx')
        print('  DOCX →', docx_path)
    except PermissionError:
        docx_path = render_docx(cfg, m, out_dir, out_name + '_new.docx')
        print('  ⚠ 原docx被占用(可能正被Word打开),已另存 →', docx_path)

    # 出稿拦截: 残留模板占位符 = 带病出稿, 禁止发布
    if not scan_leftover_placeholders(md_path, docx_path):
        sys.exit(1)
if __name__ == '__main__':
    main()
