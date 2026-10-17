# -*- coding: utf-8 -*-
"""
08-28 西甲两场 (巴萨vs毕尔巴鄂 + 塞尔塔vs奥萨苏纳) 白底图表 (R19)
输出: database/charts_20260828_laliga/
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
C_BG = '#ffffff'
C_TEXT = '#333333'
C_GRID = '#dddddd'

output_dir = r'I:\阿飞说球\database\charts_20260828_laliga'
os.makedirs(output_dir, exist_ok=True)


def radar_chart(home_vals, away_vals, dims, home_name, away_name, title, filename):
    n = len(dims)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]
    hv = home_vals + home_vals[:1]
    av = away_vals + away_vals[:1]
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
    ax.plot(angles, hv, 'o-', linewidth=2, color=C_BLUE, label=home_name)
    ax.fill(angles, hv, alpha=0.15, color=C_BLUE)
    ax.plot(angles, av, 'o-', linewidth=2, color=C_RED, label=away_name)
    ax.fill(angles, av, alpha=0.15, color=C_RED)
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

# ===== 巴萨 vs 毕尔巴鄂 =====
radar_chart([75, 85, 75, 95, 74, 64], [45, 50, 55, 5, 26, 36], dims,
            '巴萨', '毕尔巴鄂', '六维能力雷达图 | 巴萨 vs 毕尔巴鄂', 'radar_barca.png')
bar_model_market([63.5, 21.1, 15.4], [73.8, 16.1, 10.1],
                 ['巴萨胜', '平局', '毕尔巴鄂胜'],
                 '模型 vs 市场（热度撑不起净胜2球）| 巴萨 vs 毕尔巴鄂', 'bar_barca.png')
score_bar([('2-0', 10.6), ('1-1', 10.0), ('2-1', 9.9), ('1-0', 9.7), ('3-0', 7.4)],
          '高概率比分 Top5 | 巴萨 vs 毕尔巴鄂', 'score_barca.png')

# ===== 塞尔塔 vs 奥萨苏纳 =====
radar_chart([70, 55, 60, 50, 50, 51], [35, 50, 45, 50, 50, 49], dims,
            '塞尔塔', '奥萨苏纳', '六维能力雷达图 | 塞尔塔 vs 奥萨苏纳', 'radar_celta.png')
bar_model_market([51.1, 30.0, 18.9], [49.8, 28.6, 21.6],
                 ['塞尔塔胜', '平局', '奥萨苏纳胜'],
                 '模型 vs 市场（小球双共识）| 塞尔塔 vs 奥萨苏纳', 'bar_celta.png')
score_bar([('1-0', 17.1), ('0-0', 14.1), ('1-1', 12.8), ('2-0', 11.7), ('0-1', 8.7)],
          '高概率比分 Top5 | 塞尔塔 vs 奥萨苏纳', 'score_celta.png')

print('\n全部图表生成完成 → %s' % output_dir)
