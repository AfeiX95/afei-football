# -*- coding: utf-8 -*-
"""江原FC vs 大阪钢巴 赛事前瞻图表生成"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

OUT = r"I:\阿飞说球\20260811"
C_HOME = '#C8102E'   # 江原红
C_AWAY = '#1A3A6B'   # 钢巴蓝
C_DRAW = '#8C8C8C'   # 平灰
C_ACC  = '#F2A900'   # 强调金

# ============ 图1: 胜负概率对比（模型 vs 市场） ============
labels = ['江原FC', '平局', '大阪钢巴']
model  = [39.7, 26.0, 34.2]
market = [36.6, 29.1, 34.3]
colors = [C_HOME, C_DRAW, C_AWAY]

fig, ax = plt.subplots(figsize=(7.2, 3.6))
x = np.arange(3); w = 0.34
b1 = ax.bar(x - w/2, model, w, label='后台模型', color=colors, alpha=0.92)
b2 = ax.bar(x + w/2, market, w, label='市场定价', color=colors, alpha=0.38, hatch='//')
for b in list(b1)+list(b2):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.7, f'{b.get_height():.1f}%',
            ha='center', fontsize=9.5, fontweight='bold', color='#222')
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=11)
ax.set_ylim(0, 48)
ax.set_ylabel('概率 (%)', fontsize=10)
ax.set_title('江原FC vs 大阪钢巴 · 90分钟赛果概率（模型 vs 市场）', fontsize=12, fontweight='bold', pad=10)
ax.legend(fontsize=9.5, loc='upper right', framealpha=0.9)
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y', ls='--', alpha=0.3)
plt.tight_layout()
plt.savefig(fr'{OUT}\chart1_胜平负概率对比.png', bbox_inches='tight')
plt.close()

# ============ 图2: 比分概率Top8 ============
scores = [('1-1',12.4),('1-0',9.6),('0-1',8.6),('2-1',8.5),('1-2',7.9),('0-0',6.9),('2-0',6.8),('0-2',5.8)]
names  = [s[0] for s in scores]
probs  = [s[1] for s in scores]
bar_colors = []
for s in scores:
    h, a = map(int, s[0].split('-'))
    if h > a: bar_colors.append(C_HOME)
    elif h < a: bar_colors.append(C_AWAY)
    else: bar_colors.append(C_DRAW)

fig, ax = plt.subplots(figsize=(7.2, 3.6))
bars = ax.barh(names[::-1], probs[::-1], color=bar_colors[::-1], alpha=0.88, height=0.62)
for b in bars:
    ax.text(b.get_width()+0.15, b.get_y()+b.get_height()/2, f'{b.get_width():.1f}%',
            va='center', fontsize=9.5, fontweight='bold', color='#222')
ax.set_xlabel('概率 (%)', fontsize=10)
ax.set_title('最可能比分 Top8（10万次模拟）', fontsize=12, fontweight='bold', pad=10)
ax.set_xlim(0, 15)
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='x', ls='--', alpha=0.3)
plt.tight_layout()
plt.savefig(fr'{OUT}\chart2_比分概率分布.png', bbox_inches='tight')
plt.close()

# ============ 图3: 大小球 + 双方进球 ============
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))

ax = axes[0]
vals = [49.9, 50.1]
wedges, _, autotexts = ax.pie(vals, labels=['大2.5球\n49.9%', '小2.5球\n50.1%'],
        colors=[C_AWAY, C_ACC], startangle=90, counterclock=False,
        autopct='', wedgeprops=dict(width=0.42, edgecolor='white'))
for t in autotexts: t.set_fontsize(0)
for t in ax.texts: t.set_fontsize(10); t.set_fontweight('bold')
ax.set_title('大小球（临界）', fontsize=11, fontweight='bold')

ax = axes[1]
vals2 = [54.4, 45.6]
wedges, _, autotexts = ax.pie(vals2, labels=['双方进球\n54.4%', '一方零封\n45.6%'],
        colors=[C_HOME, '#B0B0B0'], startangle=90, counterclock=False,
        autopct='', wedgeprops=dict(width=0.42, edgecolor='white'))
for t in ax.texts: t.set_fontsize(10); t.set_fontweight('bold')
ax.set_title('进球分布', fontsize=11, fontweight='bold')

fig.suptitle('进球结构预判', fontsize=12, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(fr'{OUT}\chart3_大小球与进球.png', bbox_inches='tight')
plt.close()

# ============ 图4: 近10场状态对比 ============
fig, ax = plt.subplots(figsize=(7.2, 3.0))
teams = ['江原FC', '大阪钢巴']
wins  = [4, 6]; draws = [3, 1]; losses = [3, 3]
x = np.arange(2)
b1 = ax.bar(x, wins, 0.42, label='胜', color=C_HOME, alpha=0.9)
b2 = ax.bar(x, draws, 0.42, bottom=wins, label='平', color=C_DRAW, alpha=0.9)
b3 = ax.bar(x, losses, 0.42, bottom=np.array(wins)+np.array(draws), label='负', color=C_AWAY, alpha=0.75)
for i in range(2):
    ax.text(x[i], wins[i]/2, f'{wins[i]}胜', ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    ax.text(x[i], wins[i]+draws[i]/2, f'{draws[i]}平', ha='center', va='center', fontsize=10, color='white', fontweight='bold')
    ax.text(x[i], wins[i]+draws[i]+losses[i]/2, f'{losses[i]}负', ha='center', va='center', fontsize=10, color='white', fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(teams, fontsize=11)
ax.set_ylabel('场次', fontsize=10)
ax.set_title('近10场战绩对比（含杯赛/热身）', fontsize=12, fontweight='bold', pad=10)
ax.set_ylim(0, 11)
ax.legend(fontsize=9.5, loc='upper right', ncol=3)
ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y', ls='--', alpha=0.3)
plt.tight_layout()
plt.savefig(fr'{OUT}\chart4_近10场状态对比.png', bbox_inches='tight')
plt.close()

print("图表生成完成:")
import os
for f in os.listdir(OUT):
    if f.startswith('chart'):
        print(" ", f, os.path.getsize(fr'{OUT}\{f}')//1024, "KB")
