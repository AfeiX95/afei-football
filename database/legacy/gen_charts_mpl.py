import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os, sys

sys.stdout.reconfigure(encoding='utf-8')

# Try to find Chinese font
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

# Color scheme (白底版 R19: 头条docx图表背景一律白色)
C_BLUE = '#4fc3f7'
C_RED = '#ff6b6b'
C_YELLOW = '#ffd93d'
C_GREEN = '#4caf50'
C_BG = '#ffffff'      # 白底
C_TEXT = '#333333'    # 深色文字
C_GRID = '#dddddd'    # 浅灰网格
C_DARK = '#666666'

output_dir = r'I:\阿飞说球\📝文章\20260731\charts'
os.makedirs(output_dir, exist_ok=True)

# ============================================================
# 1. Six-dimension Radar Chart (Match 1)
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
    
    # Grid
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=8, color='#888')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dims, fontsize=11, color=C_TEXT)
    ax.spines['polar'].set_color(C_GRID)
    ax.tick_params(colors=C_GRID)
    ax.grid(color=C_GRID, linewidth=0.5)
    
    # Plot data
    ax.plot(angles, home_vals_plot, 'o-', linewidth=2, color=C_BLUE, label=home_name)
    ax.fill(angles, home_vals_plot, alpha=0.15, color=C_BLUE)
    ax.plot(angles, away_vals_plot, 'o-', linewidth=2, color=C_RED, label=away_name)
    ax.fill(angles, away_vals_plot, alpha=0.15, color=C_RED)
    
    # Data labels
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

# Match 1 Radar
dims = ['近期状态', '进攻火力', '防守稳固', '交锋历史', '市场支持', '模型预测']
radar_chart([60,78,50,25,70,55], [30,35,25,72,25,35], dims,
            '瓦勒伦加', '汉坎', '六维能力雷达图 | 瓦勒伦加 vs 汉坎', 'radar_m1.png')

# Match 2 Radar
radar_chart([95,95,95,75,90,75], [45,40,60,30,15,25], dims,
            '博德闪耀', '利勒斯特', '六维能力雷达图 | 博德闪耀 vs 利勒斯特', 'radar_m2.png')

# ============================================================
# 2. Bar Chart - Model vs Market (Match 1)
# ============================================================
def bar_chart(model_probs, market_probs, labels, title, filename):
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    
    x = np.arange(len(labels))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, model_probs, width, label='后台模型', color=C_BLUE, edgecolor='none', zorder=3)
    bars2 = ax.bar(x + width/2, market_probs, width, label='市场隐含', color=C_YELLOW, edgecolor='none', zorder=3)
    
    # Value labels
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{height:.1f}%',
                ha='center', va='bottom', fontsize=11, color=C_BLUE, fontweight='bold')
    for bar in bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{height:.1f}%',
                ha='center', va='bottom', fontsize=11, color=C_YELLOW, fontweight='bold')
    
    # Edge labels
    for i in range(len(labels)):
        edge = model_probs[i] - market_probs[i]
        color = C_GREEN if edge > 0 else C_RED
        sign = '+' if edge > 0 else ''
        ax.text(x[i], max(model_probs[i], market_probs[i]) + 4, f'Edge {sign}{edge:.1f}pp',
                ha='center', va='bottom', fontsize=10, color=color, fontweight='bold')
    
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12, color=C_TEXT)
    ax.set_ylabel('概率 (%)', fontsize=11, color=C_TEXT)
    ax.set_title(title, fontsize=14, color=C_TEXT, fontweight='bold')
    ax.tick_params(colors=C_TEXT)
    ax.spines['bottom'].set_color(C_GRID)
    ax.spines['left'].set_color(C_GRID)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=C_GRID, linewidth=0.5, alpha=0.5)
    ax.legend(fontsize=11, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)
    ax.set_ylim(0, max(max(model_probs), max(market_probs)) + 10)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close()
    print(f'Saved: {filename}')

# Match 1 Bar
bar_chart([48.6, 24.1, 27.2], [59.4, 21.3, 19.2],
          ['瓦勒伦加胜', '平局', '汉坎胜'],
          '模型 vs 市场概率 | 瓦勒伦加 vs 汉坎', 'bar_m1.png')

# Match 2 Bar
bar_chart([65.7, 19.6, 14.8], [75.7, 14.5, 9.8],
          ['博德闪耀胜', '平局', '利勒斯特胜'],
          '模型 vs 市场概率 | 博德闪耀 vs 利勒斯特', 'bar_m2.png')

# ============================================================
# 3. Pie Chart - Score Distribution (Match 1)
# ============================================================
def pie_chart(scores, probs, title, filename):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor(C_BG)
    
    colors = [C_BLUE, C_YELLOW, C_RED, C_GREEN, '#666666']
    
    # Left: Model probability pie
    model_labels = ['瓦勒伦加胜', '平局', '汉坎胜']
    model_vals = [48.6, 24.1, 27.2]
    model_colors = [C_BLUE, C_YELLOW, C_RED]
    
    wedges1, texts1, autotexts1 = ax1.pie(model_vals, labels=model_labels, autopct='%1.1f%%',
        colors=model_colors, startangle=90, textprops={'color': C_TEXT, 'fontsize': 11},
        pctdistance=0.75, wedgeprops=dict(linewidth=1, edgecolor=C_BG))
    for t in autotexts1:
        t.set_fontsize(10)
        t.set_fontweight('bold')
    ax1.set_title('模型概率分布', fontsize=13, color=C_TEXT, fontweight='bold')
    
    # Right: Score pie
    wedges2, texts2, autotexts2 = ax2.pie(probs, labels=scores, autopct='%1.1f%%',
        colors=colors, startangle=90, textprops={'color': C_TEXT, 'fontsize': 11},
        pctdistance=0.75, wedgeprops=dict(linewidth=1, edgecolor=C_BG))
    for t in autotexts2:
        t.set_fontsize(10)
        t.set_fontweight('bold')
    ax2.set_title('高概率比分', fontsize=13, color=C_TEXT, fontweight='bold')
    
    fig.suptitle(title, fontsize=14, color=C_TEXT, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close()
    print(f'Saved: {filename}')

# Match 1 Pie
pie_chart(['1-1', '2-1', '1-0', '2-0', '其他'], [11.3, 9.5, 9.6, 8.0, 61.6],
          '概率分布 & 高概率比分 | 瓦勒伦加 vs 汉坎', 'pie_m1.png')

# Match 2 Pie
pie_chart(['2-0', '1-0', '2-1', '1-1', '其他'], [11.0, 10.2, 9.9, 9.3, 59.6],
          '概率分布 & 高概率比分 | 博德闪耀 vs 利勒斯特', 'pie_m2.png')

# ============================================================
# 4. Line Chart - Odds Trend / Goal Distribution
# ============================================================
def line_chart(x_labels, data_sets, labels, colors, title, ylabel, filename):
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    
    for data, label, color in zip(data_sets, labels, colors):
        ax.plot(x_labels, data, 'o-', linewidth=2.5, markersize=8, color=color, label=label)
        # Annotate values
        for i, (x, y) in enumerate(zip(x_labels, data)):
            ax.annotate(f'{y:.1f}', (x, y), textcoords="offset points", xytext=(0, 12),
                       ha='center', fontsize=9, color=color, fontweight='bold')
    
    ax.set_title(title, fontsize=14, color=C_TEXT, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=11, color=C_TEXT)
    ax.tick_params(colors=C_TEXT)
    ax.spines['bottom'].set_color(C_GRID)
    ax.spines['left'].set_color(C_GRID)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color=C_GRID, linewidth=0.5, alpha=0.5)
    ax.legend(fontsize=11, facecolor=C_BG, edgecolor=C_GRID, labelcolor=C_TEXT)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches='tight', facecolor=C_BG)
    plt.close()
    print(f'Saved: {filename}')

# Goal distribution line chart
goals = ['0球', '1球', '2球', '3球', '4球', '5球', '6球', '7球']
m1_dist = [5.7, 16.5, 23.5, 22.2, 15.2, 8.5, 4.6, 2.8]
m2_dist = [4.8, 14.5, 22.3, 22.5, 16.1, 9.3, 5.4, 3.6]

line_chart(goals, [m1_dist, m2_dist],
           ['瓦勒伦加vs汉坎', '博德闪耀vs利勒斯特'],
           [C_BLUE, C_RED],
           '总进球概率分布 | 两场挪超', '概率 (%)', 'line_goals.png')

# Edge comparison bar chart (horizontal)
fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor(C_BG)
ax.set_facecolor(C_BG)

categories = ['瓦勒伦加胜\nEdge', '平局1\nEdge', '汉坎胜\nEdge',
              '博德闪耀胜\nEdge', '平局2\nEdge', '利勒斯特胜\nEdge',
              '让1球客胜\nEdge', '让2球客胜\nEdge']
edges = [-10.8, 2.8, 8.0, -10.0, 5.1, 5.0, 10.6, 11.8]
colors = [C_RED if e < 0 else C_GREEN for e in edges]

bars = ax.barh(categories, edges, color=colors, height=0.6, edgecolor='none')
for bar, val in zip(bars, edges):
    x = bar.get_width()
    sign = '+' if val > 0 else ''
    ax.text(x + (0.3 if val > 0 else -0.3), bar.get_y() + bar.get_height()/2,
            f'{sign}{val:.1f}pp', ha='left' if val > 0 else 'right',
            va='center', fontsize=11, color=C_TEXT, fontweight='bold')

ax.axvline(x=0, color=C_GRID, linewidth=1)
ax.set_title('Edge对比 | 两场挪超全维度', fontsize=14, color=C_TEXT, fontweight='bold')
ax.set_xlabel('Edge (pp)', fontsize=11, color=C_TEXT)
ax.tick_params(colors=C_TEXT)
ax.spines['bottom'].set_color(C_GRID)
ax.spines['left'].set_color(C_GRID)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.xaxis.grid(True, color=C_GRID, linewidth=0.5, alpha=0.5)
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'bar_edge.png'), dpi=150, bbox_inches='tight', facecolor=C_BG)
plt.close()
print('Saved: bar_edge.png')

print('\nAll charts generated!')
