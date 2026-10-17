# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

OUT = r"I:\阿飞说球\assets\charts\20260802"
os.makedirs(OUT, exist_ok=True)

# Chart 1: Market vs Model
fig, ax = plt.subplots(figsize=(8, 4.5))
cats = ['Home Win', 'Draw', 'Away Win']
market = [32.2, 34.5, 46.3]
model = [28.5, 32.4, 39.1]
x = np.arange(len(cats))
w = 0.35
b1 = ax.bar(x - w/2, market, w, label='Market', color='#FF6B6B', alpha=0.85)
b2 = ax.bar(x + w/2, model, w, label='Model', color='#4ECDC4', alpha=0.85)
ax.set_ylabel('Probability (%)', fontsize=11)
ax.set_title('Market vs Model: Jeju SK vs Incheon Utd', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(cats, fontsize=11)
ax.legend(fontsize=10)
for bar in b1:
    ax.text(bar.get_x()+bar.get_width()/2., bar.get_height()+0.8, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)
for bar in b2:
    ax.text(bar.get_x()+bar.get_width()/2., bar.get_height()+0.8, f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=9)
ax.annotate('-7.2pp', xy=(2, 39.1), xytext=(2.35, 44), fontsize=10, color='green', fontweight='bold', arrowprops=dict(arrowstyle='->', color='green'))
ax.set_ylim(0, 55)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "7_济州vs仁川_偏差图.png"), dpi=150)
plt.close()
print("Chart 7 done")

# Chart 2: Radar
fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
dims = ['Form', 'Home/Away', 'Injuries', 'H2H', 'Defense', 'Momentum']
jeju = [0.5, 0.3, 0.8, 0.3, 0.65, 0.55]
incheon = [0.5, 0.65, 0.25, 0.7, 0.6, 0.45]
angles = np.linspace(0, 2*np.pi, len(dims), endpoint=False).tolist()
jeju += jeju[:1]; incheon += incheon[:1]; angles += angles[:1]
ax.fill(angles, jeju, alpha=0.25, color='#FF6B6B')
ax.plot(angles, jeju, 'o-', linewidth=2, label='Jeju SK', color='#FF6B6B')
ax.fill(angles, incheon, alpha=0.25, color='#4ECDC4')
ax.plot(angles, incheon, 'o-', linewidth=2, label='Incheon Utd', color='#4ECDC4')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(dims, fontsize=11)
ax.set_ylim(0, 1)
ax.set_title('Six-Dimension Radar: Jeju SK vs Incheon Utd', fontsize=13, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "8_济州vs仁川_雷达图.png"), dpi=150)
plt.close()
print("Chart 8 done")

# Chart 3: H2H bar
fig, ax = plt.subplots(figsize=(8, 4.5))
dates = ['22-09', '22-10', '23-03', '23-05', '23-09', '24-04', '24-06', '24-08', '24-10', '26-04']
results = [-1, -1, -1, 1, -1, 1, 1, -1, 1, -1]  # 1=Jeju win, -1=Incheon win
colors = ['#FF6B6B' if r == 1 else '#4ECDC4' for r in results]
scores = ['0-1', '3-1', '1-0', '2-0', '2-1', '0-1', '1-0', '0-1', '1-2', '1-0']
bars = ax.bar(dates, [1]*10, color=colors, alpha=0.85, edgecolor='white', linewidth=2)
for i, (bar, score) in enumerate(zip(bars, scores)):
    ax.text(bar.get_x()+bar.get_width()/2., 0.5, score, ha='center', va='center', fontsize=10, fontweight='bold', color='white')
ax.set_ylim(0, 1.2)
ax.set_yticks([])
ax.set_title('H2H Last 10: 0 Draws! Green=Incheon Win, Red=Jeju Win', fontsize=11, fontweight='bold')
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "9_济州vs仁川_H2H.png"), dpi=150)
plt.close()
print("Chart 9 done")

# Chart 4: Injury impact
fig, ax = plt.subplots(figsize=(8, 4.5))
teams = ['Jeju SK\n(1 player out)', 'Incheon Utd\n(5 players out)']
impact = [0.03, 0.35]
colors = ['#4ECDC4', '#FF6B6B']
bars = ax.bar(teams, impact, color=colors, alpha=0.85, width=0.5)
for bar in bars:
    ax.text(bar.get_x()+bar.get_width()/2., bar.get_height()+0.01, f'λ -{bar.get_height():.2f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
ax.set_ylabel('Injury Impact (λ)', fontsize=11)
ax.set_title('Injury Impact Comparison', fontsize=13, fontweight='bold')
ax.set_ylim(0, 0.5)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "10_济州vs仁川_伤停影响.png"), dpi=150)
plt.close()
print("Chart 10 done")

print("All 4 charts generated!")
