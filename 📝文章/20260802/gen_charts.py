# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

# Try to find Chinese font
font_paths = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]
zh_font = None
for fp in font_paths:
    if os.path.exists(fp):
        zh_font = fm.FontProperties(fname=fp)
        break

if zh_font is None:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
else:
    plt.rcParams['font.family'] = 'sans-serif'

OUT = r"I:\阿飞说球\assets\charts\20260802"
os.makedirs(OUT, exist_ok=True)

# ===== Chart 1: 市场vs模型偏差 =====
fig, ax = plt.subplots(figsize=(8, 4.5))
categories = ['Home Win', 'Draw', 'Away Win']
market = [53.8, 29.0, 30.1]
model = [32.8, 27.5, 39.7]
x = np.arange(len(categories))
w = 0.35
bars1 = ax.bar(x - w/2, market, w, label='Market Price', color='#FF6B6B', alpha=0.85)
bars2 = ax.bar(x + w/2, model, w, label='Model Output', color='#4ECDC4', alpha=0.85)
ax.set_ylabel('Probability (%)', fontsize=11)
ax.set_title('Market vs Model: Ulsan HD vs FC Anyang', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=11)
ax.legend(fontsize=10)
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
            f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
            f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)
# Add deviation annotations
ax.annotate('-21.0pp', xy=(0, 53.8), xytext=(0.35, 58),
            fontsize=10, color='red', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='red'))
ax.annotate('+9.6pp', xy=(2, 39.7), xytext=(2.35, 44),
            fontsize=10, color='green', fontweight='bold',
            arrowprops=dict(arrowstyle='->', color='green'))
ax.set_ylim(0, 65)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "1_市场vs模型偏差.png"), dpi=150)
plt.close()
print("Chart 1 done")

# ===== Chart 2: 六维雷达图 =====
fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
dims = ['Form', 'Home/Away', 'Injuries', 'H2H', 'Defense', 'Momentum']
ulsan = [0.2, 0.3, 0.3, 0.2, 0.2, 0.15]  # 蔚山 (normalized 0-1, lower is worse)
anyang = [0.8, 0.75, 0.9, 0.7, 0.75, 0.85]  # FC安养
angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
ulsan += ulsan[:1]
anyang += anyang[:1]
angles += angles[:1]
ax.fill(angles, ulsan, alpha=0.25, color='#FF6B6B')
ax.plot(angles, ulsan, 'o-', linewidth=2, label='Ulsan HD', color='#FF6B6B')
ax.fill(angles, anyang, alpha=0.25, color='#4ECDC4')
ax.plot(angles, anyang, 'o-', linewidth=2, label='FC Anyang', color='#4ECDC4')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(dims, fontsize=11)
ax.set_ylim(0, 1)
ax.set_title('Six-Dimension Radar: Ulsan HD vs FC Anyang', fontsize=13, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "2_六维雷达图.png"), dpi=150)
plt.close()
print("Chart 2 done")

# ===== Chart 3: 主客场数据对比柱状图 =====
fig, axes = plt.subplots(1, 3, figsize=(12, 4.5))
categories = ['Win Rate', 'Goals/Game', 'Conceded/Game']
ulsan_vals = [40.0, 1.50, 1.70]
anyang_vals = [50.0, 1.60, 1.00]
colors = ['#FF6B6B', '#4ECDC4']
for i, (ax, cat) in enumerate(zip(axes, categories)):
    bars = ax.bar(['Ulsan HD', 'FC Anyang'], [ulsan_vals[i], anyang_vals[i]], color=colors, alpha=0.85)
    ax.set_title(cat, fontsize=11, fontweight='bold')
    ax.set_ylim(0, max(ulsan_vals[i], anyang_vals[i]) * 1.3)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.03,
                f'{bar.get_height():.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
fig.suptitle('Home/Away Data Comparison', fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "3_主客场数据对比.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Chart 3 done")

# ===== Chart 4: 胜平负饼图 =====
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
labels = ['Home Win', 'Draw', 'Away Win']
mkt_colors = ['#FF6B6B', '#FFD93D', '#4ECDC4']
mdl_colors = ['#FF6B6B', '#FFD93D', '#4ECDC4']
ax1.pie(market, labels=labels, colors=mkt_colors, autopct='%1.1f%%',
        startangle=90, textprops={'fontsize': 10})
ax1.set_title('Market Odds', fontsize=12, fontweight='bold')
ax2.pie(model, labels=labels, colors=mdl_colors, autopct='%1.1f%%',
        startangle=90, textprops={'fontsize': 10})
ax2.set_title('Model Output', fontsize=12, fontweight='bold')
fig.suptitle('Win-Draw-Lose Distribution', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUT, "4_胜平负饼图.png"), dpi=150)
plt.close()
print("Chart 4 done")

# ===== Chart 5: H2H交锋趋势 =====
fig, ax = plt.subplots(figsize=(8, 4.5))
h2h_dates = ['25-02', '25-04', '25-09', '25-11', '26-04']
h2h_results = [0, 1, 0, 0, 0]  # 0=Ulsan loss/draw, 1=Ulsan win
h2h_scores = ['0-1', '1-0', '0-0', '1-3', '1-1']
colors_h2h = ['#4ECDC4' if r == 0 else '#FF6B6B' for r in h2h_results]
bars = ax.bar(h2h_dates, [1]*5, color=colors_h2h, alpha=0.85, edgecolor='white', linewidth=2)
for i, (bar, score) in enumerate(zip(bars, h2h_scores)):
    ax.text(bar.get_x() + bar.get_width()/2., 0.5, score,
            ha='center', va='center', fontsize=12, fontweight='bold', color='white')
ax.set_ylim(0, 1.2)
ax.set_yticks([])
ax.set_title('H2H Last 5: Ulsan HD vs FC Anyang (Green=FC Anyang result)', fontsize=11, fontweight='bold')
ax.set_xlabel('Date')
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "5_H2H交锋趋势.png"), dpi=150)
plt.close()
print("Chart 5 done")

# ===== Chart 6: 综合对比汇总 =====
fig, ax = plt.subplots(figsize=(10, 5))
dims_summary = ['Win Rate\n(Home/Away)', 'Goals/Game', 'Conceded/Game', 'Win Rate\n(Recent 6)', 'H2H Win %', 'Clean Sheet %']
ulsan_s = [40, 1.50, 1.70, 16.7, 20, 10]
anyang_s = [50, 1.60, 1.00, 66.7, 40, 30]
x = np.arange(len(dims_summary))
w = 0.35
bars1 = ax.bar(x - w/2, ulsan_s, w, label='Ulsan HD', color='#FF6B6B', alpha=0.85)
bars2 = ax.bar(x + w/2, anyang_s, w, label='FC Anyang', color='#4ECDC4', alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(dims_summary, fontsize=9)
ax.set_title('Comprehensive Comparison: Ulsan HD vs FC Anyang', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
            f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=8)
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
            f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "6_综合对比汇总.png"), dpi=150)
plt.close()
print("Chart 6 done")

print("All 6 charts generated successfully!")
