# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

font_paths = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]
for fp in font_paths:
    if os.path.exists(fp):
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
        break
plt.rcParams['axes.unicode_minus'] = False

OUT = r"I:\阿飞说球\assets\charts\20260802"
os.makedirs(OUT, exist_ok=True)

# Chart 15: 三场偏差汇总
fig, ax = plt.subplots(figsize=(10, 5))
matches = ['蔚山HD vs\nFC安养', '济州SK vs\n仁川联队', '大田市民 vs\n光州FC']
dev_home = [-21.0, -3.7, -29.9]
dev_away = [9.6, -7.2, 9.3]
x = np.arange(len(matches))
w = 0.35
b1 = ax.bar(x - w/2, dev_home, w, label='主胜偏差', color='#FF6B6B', alpha=0.85)
b2 = ax.bar(x + w/2, dev_away, w, label='客胜偏差', color='#4ECDC4', alpha=0.85)
ax.axhline(y=0, color='black', linewidth=0.8)
ax.set_ylabel('偏差 (百分点)', fontsize=11)
ax.set_title('三场比赛市场偏差汇总（负值=市场高估）', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(matches, fontsize=10)
ax.legend(fontsize=10)
for bar in b1:
    h = bar.get_height()
    ax.text(bar.get_x()+bar.get_width()/2., h + (1 if h >= 0 else -2.5), f'{h:+.1f}', ha='center', va='bottom' if h >= 0 else 'top', fontsize=9, fontweight='bold')
for bar in b2:
    h = bar.get_height()
    ax.text(bar.get_x()+bar.get_width()/2., h + (1 if h >= 0 else -2.5), f'{h:+.1f}', ha='center', va='bottom' if h >= 0 else 'top', fontsize=9, fontweight='bold')
ax.set_ylim(-35, 15)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "15_三场偏差汇总.png"), dpi=150)
plt.close()
print("Chart 15 done")

# Chart 16: 三场胜平负概率对比
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
match_data = [
    ("蔚山HD vs FC安养", [32.8, 27.5, 39.7], [53.8, 29.0, 30.1]),
    ("济州SK vs 仁川联队", [28.5, 32.4, 39.1], [32.2, 34.5, 46.3]),
    ("大田市民 vs 光州FC", [41.5, 33.3, 25.2], [71.4, 25.6, 15.9]),
]
cats = ['主胜', '平局', '客胜']
for idx, (title, model, market) in enumerate(match_data):
    ax = axes[idx]
    x = np.arange(len(cats))
    w = 0.35
    ax.bar(x - w/2, market, w, label='市场', color='#FF6B6B', alpha=0.85)
    ax.bar(x + w/2, model, w, label='模型', color='#4ECDC4', alpha=0.85)
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=9)
    ax.set_ylim(0, 80)
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=0.3)
    if idx == 0:
        ax.set_ylabel('概率 (%)', fontsize=10)
fig.suptitle('三场比赛胜平负概率：市场 vs 模型', fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "16_三场胜平负对比.png"), dpi=150, bbox_inches='tight')
plt.close()
print("Chart 16 done")

# Chart 17: 三场比分预测矩阵
fig, ax = plt.subplots(figsize=(10, 5))
matches_short = ['蔚山vs安养', '济州vs仁川', '大田vs光州']
scores = ['1-1', '1-2', '1-0', '0-1', '0-0', '1-0']
probs = [
    [10.6, 10.4, 10.2],
    [10.8, 10.2, 10.2],
    [12.0, 10.5, 10.7],
]
x = np.arange(len(matches_short))
w = 0.25
colors = ['#FF6B6B', '#4ECDC4', '#FFD93D']
for i in range(3):
    offset = (i - 1) * w
    bars = ax.bar(x + offset, [p[i] for p in probs], w, label=f'{"首选" if i==0 else "次选" if i==1 else "留意"}', color=colors[i], alpha=0.85)
    for bar in bars:
        ax.text(bar.get_x()+bar.get_width()/2., bar.get_height()+0.2, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=8)
ax.set_ylabel('概率 (%)', fontsize=11)
ax.set_title('三场比赛比分预测概率', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(matches_short, fontsize=10)
ax.legend(fontsize=10)
ax.set_ylim(0, 15)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "17_三场比分预测.png"), dpi=150)
plt.close()
print("Chart 17 done")

# Chart 18: 三场伤停对比
fig, ax = plt.subplots(figsize=(8, 5))
teams = ['蔚山HD\n(2人伤缺)', 'FC安养\n(0人)', '济州SK\n(1人伤缺)', '仁川联队\n(5人伤缺)', '大田市民\n(4人伤缺)', '光州FC\n(1人停赛)']
impact = [0.23, 0.0, 0.03, 0.35, 0.28, 0.08]
colors = ['#FF6B6B' if i > 0.1 else '#4ECDC4' for i in impact]
bars = ax.bar(teams, impact, color=colors, alpha=0.85, width=0.6)
for bar in bars:
    h = bar.get_height()
    if h > 0:
        ax.text(bar.get_x()+bar.get_width()/2., h+0.01, f'λ -{h:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax.set_ylabel('伤停影响 (λ)', fontsize=11)
ax.set_title('三场比赛伤停影响对比', fontsize=13, fontweight='bold')
ax.set_ylim(0, 0.45)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "18_三场伤停对比.png"), dpi=150)
plt.close()
print("Chart 18 done")

print("All combined charts generated!")
