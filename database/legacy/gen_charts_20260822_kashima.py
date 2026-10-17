# -*- coding: utf-8 -*-
"""
周六001 鹿岛鹿角vs福冈黄蜂 白底图表生成 (R19规范)
输出: database/charts_20260822_kashima/
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

output_dir = r'I:\阿飞说球\database\charts_20260822_kashima'
os.makedirs(output_dir, exist_ok=True)


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
    print('Saved: %s' % filename)


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
        ax.annotate('%.1f%%' % h, xy=(b.get_x() + b.get_width()/2, h),
                    xytext=(0, 3), textcoords='offset points', ha='center', fontsize=11, color=C_TEXT)

    ax.legend(fontsize=11, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close()
    print('Saved: %s' % filename)


def score_bar(scores, title, filename):
    labels = [s[0] for s in scores]
    vals = [s[1] for s in scores]
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)

    colors = []
    for s in labels:
        h, a = int(s.split('-')[0]), int(s.split('-')[1])
        colors.append(C_BLUE if h > a else (C_YELLOW if h == a else C_RED))

    bars = ax.bar(labels, vals, color=colors, edgecolor='white')
    ax.set_ylabel('概率 (%)', fontsize=12, color=C_TEXT)
    ax.set_title(title, fontsize=14, color=C_TEXT, fontweight='bold')
    ax.set_ylim(0, max(vals) * 1.3)
    ax.grid(axis='y', color=C_GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(colors=C_TEXT, labelsize=12)

    for b in bars:
        h = b.get_height()
        ax.annotate('%.1f%%' % h, xy=(b.get_x() + b.get_width()/2, h),
                    xytext=(0, 3), textcoords='offset points', ha='center', fontsize=11, color=C_TEXT)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close()
    print('Saved: %s' % filename)


dims = ['近期状态', '进攻火力', '防守稳固', '交锋历史', '市场支持', '模型预测']

# ===== 鹿岛鹿角 vs 福冈黄蜂 =====
radar_chart([70, 75, 60, 40, 55, 53], [55, 55, 65, 55, 18, 19], dims,
            '鹿岛鹿角', '福冈黄蜂', '六维能力雷达图 | 鹿岛鹿角 vs 福冈黄蜂', 'radar_kashima.png')
bar_model_market([52.5, 29.0, 18.5], [55.1, 26.5, 18.5],
                 ['鹿岛鹿角胜', '平局', '福冈黄蜂胜'],
                 '模型 vs 市场 | 鹿岛鹿角 vs 福冈黄蜂', 'bar_kashima.png')
score_bar([('1-0', 12.6), ('1-1', 11.4), ('2-0', 10.7), ('2-1', 9.7), ('0-0', 7.4)],
          '高概率比分 Top5 | 鹿岛鹿角 vs 福冈黄蜂', 'score_kashima.png')

print('\n全部图表生成完成 → %s' % output_dir)
