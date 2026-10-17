# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

font_paths = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]
zh_font = None
for fp in font_paths:
    if os.path.exists(fp):
        zh_font = fm.FontProperties(fname=fp)
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
        break
plt.rcParams['axes.unicode_minus'] = False

OUT = r"I:\阿飞说球\assets\charts\20260802"
os.makedirs(OUT, exist_ok=True)

# Chart 11: 市场vs模型偏差
fig, ax = plt.subplots(figsize=(8, 4.5))
cats = ['主胜', '平局', '客胜']
market = [71.4, 25.6, 15.9]
model = [41.5, 33.3, 25.2]
x = np.arange(len(cats))
w = 0.35
b1 = ax.bar(x - w/2, market, w, label='市场定价', color='#FF6B6B', alpha=0.85)
b2 = ax.bar(x + w/2, model, w, label='后台模型', color='#4ECDC4', alpha=0.85)
ax.set_ylabel('概率 (%)', fontsize=11, fontproperties=zh_font)
ax.set_title('大田市民 vs 光州FC — 市场 vs 模型偏差', fontsize=13, fontweight='bold', fontproperties=zh_font)
ax.set_xticks(x)
ax.set_xticklabels(cats, fontsize=11, fontproperties=zh_font)
ax.legend(fontsize=10, prop=zh_font)
for bar in b1:
    ax.text(bar.get_x()+bar.get_width()/2., bar.get_height()+0.8, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)
for bar in b2:
    ax.text(bar.get_x()+bar.get_width()/2., bar.get_height()+0.8, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)
ax.annotate('-29.9pp', xy=(0, 41.5), xytext=(0.35, 55), fontsize=11, color='red', fontweight='bold', arrowprops=dict(arrowstyle='->', color='red'))
ax.annotate('+7.7pp', xy=(1, 33.3), xytext=(1.35, 38), fontsize=10, color='green', fontweight='bold', arrowprops=dict(arrowstyle='->', color='green'))
ax.set_ylim(0, 80)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "11_大田vs光州_偏差图.png"), dpi=150)
plt.close()
print("Chart 11 done")

# Chart 12: 雷达图
fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
dims = ['近期状态', '主客分离', '伤停影响', 'H2H交锋', '防守能力', '走势动能']
dctm = [0.2, 0.1, 0.35, 0.55, 0.4, 0.2]
gwangju = [0.2, 0.1, 0.6, 0.45, 0.15, 0.45]
angles = np.linspace(0, 2*np.pi, len(dims), endpoint=False).tolist()
dctm += dctm[:1]; gwangju += gwangju[:1]; angles += angles[:1]
ax.fill(angles, dctm, alpha=0.25, color='#FF6B6B')
ax.plot(angles, dctm, 'o-', linewidth=2, label='大田市民', color='#FF6B6B')
ax.fill(angles, gwangju, alpha=0.25, color='#4ECDC4')
ax.plot(angles, gwangju, 'o-', linewidth=2, label='光州FC', color='#4ECDC4')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(dims, fontsize=11, fontproperties=zh_font)
ax.set_ylim(0, 1)
ax.set_title('六维能力对比：大田市民 vs 光州FC', fontsize=13, fontweight='bold', pad=20, fontproperties=zh_font)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10, prop=zh_font)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "12_大田vs光州_雷达图.png"), dpi=150)
plt.close()
print("Chart 12 done")

# Chart 13: 主场/客场数据对比
fig, ax = plt.subplots(figsize=(8, 4.5))
dims = ['胜率(%)', '场均进球', '场均失球', '赢指率(%)']
dctm_v = [0, 0.70, 1.40, 0]
gwangju_v = [0, 0.33, 2.67, 33.3]
x = np.arange(len(dims))
w = 0.35
b1 = ax.bar(x - w/2, dctm_v, w, label='大田市民（主场）', color='#FF6B6B', alpha=0.85)
b2 = ax.bar(x + w/2, gwangju_v, w, label='光州FC（客场）', color='#4ECDC4', alpha=0.85)
ax.set_title('主客场核心数据对比', fontsize=13, fontweight='bold', fontproperties=zh_font)
ax.set_xticks(x)
ax.set_xticklabels(dims, fontsize=10, fontproperties=zh_font)
ax.legend(fontsize=10, prop=zh_font)
for bar in b1:
    ax.text(bar.get_x()+bar.get_width()/2., bar.get_height()+0.3, f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=9)
for bar in b2:
    ax.text(bar.get_x()+bar.get_width()/2., bar.get_height()+0.3, f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=9)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "13_大田vs光州_主客场对比.png"), dpi=150)
plt.close()
print("Chart 13 done")

# Chart 14: H2H
fig, ax = plt.subplots(figsize=(8, 4.5))
dates = ['23-06', '23-08', '24-05', '24-06', '24-09', '24-11', '25-03', '25-06', '25-08', '26-05']
results = [0, -1, -1, 1, 1, 0, 0, 0, -1, 1]
colors = ['#FF6B6B' if r == 1 else '#4ECDC4' if r == -1 else '#FFD93D' for r in results]
scores = ['1-1', '3-0', '2-1', '2-1', '2-0', '0-0', '1-1', '2-2', '2-0', '0-5']
bars = ax.bar(dates, [1]*10, color=colors, alpha=0.85, edgecolor='white', linewidth=2)
for i, (bar, score) in enumerate(zip(bars, scores)):
    ax.text(bar.get_x()+bar.get_width()/2., 0.5, score, ha='center', va='center', fontsize=9, fontweight='bold', color='white')
ax.set_ylim(0, 1.2)
ax.set_yticks([])
ax.set_title('近10次交锋：红=大田胜，绿=光州胜，黄=平局', fontsize=11, fontweight='bold', fontproperties=zh_font)
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "14_大田vs光州_H2H.png"), dpi=150)
plt.close()
print("Chart 14 done")

print("All 4 charts with Chinese labels generated!")
