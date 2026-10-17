# -*- coding: utf-8 -*-
"""
欧冠附加赛两场 白底图表生成 (R19规范: 白底/蓝黄红/深色文字)
周二004 费内巴切vs里昂 + 周二003 萨格勒布vs维京
输出: 📝文章/20260819/charts/mp/
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os, sys

sys.stdout.reconfigure(encoding='utf-8')

chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']
font_found = None
for f in chinese_fonts:
    try:
        fp = fm.findfont(fm.FontProperties(family=f))
        if fp and 'LastResort' not in fp:
            font_found = f
            break
    except:
        pass

if font_found:
    plt.rcParams['font.sans-serif'] = [font_found, 'DejaVu Sans']
else:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

C_BLUE = '#4fc3f7'
C_RED = '#ff6b6b'
C_YELLOW = '#ffd93d'
C_GREEN = '#4caf50'
C_BG = '#ffffff'
C_TEXT = '#333333'
C_GRID = '#dddddd'
C_DARK = '#666666'

output_dir = r'I:\阿飞说球\database\charts_uefa_20260819'
os.makedirs(output_dir, exist_ok=True)

# ============================================================
# 1. 六维雷达图
# ============================================================
def radar_chart(home_vals, away_vals, dims, home_name, away_name, title, filename):
    n = len(dims)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]
    home_vals_plot = home_vals + home_vals[:1]
    away_vals_plot = away_vals + away_vals[:1]

    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=8, color='#888')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dims, fontsize=11, color=C_TEXT)
    ax.spines['polar'].set_color(C_GRID)
    ax.tick_params(colors=C_GRID)
    ax.grid(color=C_GRID, linewidth=0.5)

    ax.plot(angles, home_vals_plot, 'o-', linewidth=2, color=C_BLUE, label=home_name)
    ax.fill(angles, home_vals_plot, alpha=0.15, color=C_BLUE)
    ax.plot(angles, away_vals_plot, 'o-', linewidth=2, color=C_RED, label=away_name)
    ax.fill(angles, away_vals_plot, alpha=0.15, color=C_RED)

    for i in range(n):
        angle = angles[i]
        ax.annotate(f'{home_vals[i]}', xy=(angle, home_vals[i]), fontsize=8, color=C_BLUE, ha='center', va='bottom')
        ax.annotate(f'{away_vals[i]}', xy=(angle, away_vals[i]), fontsize=8, color=C_RED, ha='center', va='top')

    ax.set_title(title, fontsize=14, color=C_TEXT, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close()
    print(f'Saved: {filename}')

dims = ['近期状态', '进攻火力', '防守稳固', '交锋历史', '市场支持', '模型预测']

# 费内巴切 vs 里昂
radar_chart([80, 72, 88, 35, 55, 56], [60, 70, 40, 40, 46, 20], dims,
            '费内巴切', '里昂', '六维能力雷达图 | 费内巴切 vs 里昂', 'radar_m1.png')

# 萨格勒布 vs 维京
radar_chart([85, 70, 90, 30, 62, 65], [65, 62, 55, 35, 55, 14], dims,
            '萨格勒布迪纳摩', '维京', '六维能力雷达图 | 萨格勒布迪纳摩 vs 维京', 'radar_m2.png')

# ============================================================
# 2. 模型 vs 市场 概率柱状图
# ============================================================
def bar_model_market(model, market, labels, title, filename):
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    b1 = ax.bar(x - width/2, model, width, label='后台模型', color=C_BLUE, edgecolor='white')
    b2 = ax.bar(x + width/2, market, width, label='市场定价', color=C_YELLOW, edgecolor='white')

    ax.set_ylabel('概率 (%)', fontsize=12, color=C_TEXT)
    ax.set_title(title, fontsize=14, color=C_TEXT, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12, color=C_TEXT)
    ax.set_ylim(0, max(max(model), max(market)) * 1.25)
    ax.grid(axis='y', color=C_GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(colors=C_TEXT)

    for b in list(b1) + list(b2):
        h = b.get_height()
        ax.annotate(f'{h:.1f}%', xy=(b.get_x() + b.get_width()/2, h),
                    xytext=(0, 3), textcoords='offset points', ha='center', fontsize=11, color=C_TEXT)

    ax.legend(fontsize=11, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close()
    print(f'Saved: {filename}')

# 费内巴切: 模型 55.8/23.9/20.2 vs 市场欧赔 46.1/26.1/27.8
bar_model_market([55.8, 23.9, 20.2], [46.1, 26.1, 27.8],
                 ['费内巴切胜', '平局', '里昂胜'],
                 '模型 vs 市场 | 费内巴切 vs 里昂', 'bar_m1.png')

# 萨格勒布: 模型 64.8/21.0/14.2 vs 克媒定性约60/25/15
bar_model_market([64.8, 21.0, 14.2], [60.0, 25.0, 15.0],
                 ['萨格勒布胜', '平局', '维京胜'],
                 '模型 vs 市场 | 萨格勒布迪纳摩 vs 维京', 'bar_m2.png')

# ============================================================
# 3. 比分概率 Top5 柱状图
# ============================================================
def score_bar(scores, title, filename):
    labels = [s[0] for s in scores]
    vals = [s[1] for s in scores]
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    colors = [C_BLUE if int(s.split('-')[0]) > int(s.split('-')[1]) else
              (C_YELLOW if int(s.split('-')[0]) == int(s.split('-')[1]) else C_RED) for s in labels]

    bars = ax.bar(labels, vals, color=colors, edgecolor='white')
    ax.set_ylabel('概率 (%)', fontsize=12, color=C_TEXT)
    ax.set_title(title, fontsize=14, color=C_TEXT, fontweight='bold')
    ax.set_ylim(0, max(vals) * 1.3)
    ax.grid(axis='y', color=C_GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(colors=C_TEXT, labelsize=12)

    for b in bars:
        h = b.get_height()
        ax.annotate(f'{h:.1f}%', xy=(b.get_x() + b.get_width()/2, h),
                    xytext=(0, 3), textcoords='offset points', ha='center', fontsize=11, color=C_TEXT)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close()
    print(f'Saved: {filename}')

score_bar([('1-0', 12.3), ('1-1', 11.4), ('2-0', 10.4), ('2-1', 9.7), ('0-0', 7.2)],
          '高概率比分 Top5 | 费内巴切 vs 里昂', 'score_m1.png')
score_bar([('1-0', 12.9), ('2-0', 12.3), ('1-1', 9.9), ('2-1', 9.7), ('3-0', 8.0)],
          '高概率比分 Top5 | 萨格勒布迪纳摩 vs 维京', 'score_m2.png')

# ============================================================
# 4. 让球/大小球信号图 (费内巴切)
# ============================================================
def signal_chart(items, title, filename):
    labels = [i[0] for i in items]
    vals = [i[1] for i in items]
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    bars = ax.barh(labels, vals, color=[C_GREEN if v >= 50 else C_RED for v in vals], edgecolor='white')
    ax.set_xlabel('概率 (%)', fontsize=12, color=C_TEXT)
    ax.set_title(title, fontsize=14, color=C_TEXT, fontweight='bold')
    ax.set_xlim(0, max(vals) * 1.25)
    ax.grid(axis='x', color=C_GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(colors=C_TEXT, labelsize=11)

    for b in bars:
        w = b.get_width()
        ax.annotate(f'{w:.1f}%', xy=(w, b.get_y() + b.get_height()/2),
                    xytext=(5, 0), textcoords='offset points', va='center', fontsize=11, color=C_TEXT)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close()
    print(f'Saved: {filename}')

# 费内巴切: 让球半球上盘 + 大2.5 + 主胜 + 平局 + 客胜
signal_chart([('费内巴切胜(模型)', 55.8), ('大2.5(模型)', 49.1),
              ('亚盘半球上盘(市场)', 53.0), ('里昂胜(模型)', 20.2)],
             '信号一览 | 费内巴切 vs 里昂', 'signals_m1.png')
signal_chart([('萨格勒布胜(模型)', 64.8), ('大2.5(模型C27)', 63.2),
              ('大2.5(MatchPulse)', 62.0), ('维京胜(模型)', 14.2)],
             '信号一览 | 萨格勒布迪纳摩 vs 维京', 'signals_m2.png')

print('\n全部图表生成完成 →', output_dir)
