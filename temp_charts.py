# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

# --- Font setup ---
font_paths = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]
font_prop = None
for fp in font_paths:
    if os.path.exists(fp):
        font_prop = fm.FontProperties(fname=fp, size=12)
        plt.rcParams['font.family'] = font_prop.get_name()
        break
if font_prop is None:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

out_dir = r"I:\阿fei说球\assets\charts\20260731"
os.makedirs(out_dir, exist_ok=True)

# =============================================
# Chart 1: 六维雷达图 - 三场对比
# =============================================
categories = ['近期状态', '主客场', '进攻能力', '防守能力', 'H2H心理', '战意']

# 浦项 vs 金泉
pohang = [3, 3, 1, 4, 2, 3]  # 浦项
gimcheon = [2, 3, 4, 3, 5, 3]  # 金泉

# 全北 vs FC首尔
jeonbuk = [4, 4, 4, 3, 4, 5]
fcseoul = [4, 5, 5, 5, 4, 4]

# 江原 vs 富川
gangwon = [5, 5, 4, 5, 4, 4]
bucheon = [1, 2, 2, 2, 2, 2]

def radar_chart(ax, team1, team2, name1, name2, title, color1, color2):
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
    team1_plot = team1 + [team1[0]]
    team2_plot = team2 + [team2[0]]
    angles += angles[:1]
    
    ax.fill(angles, team1_plot, alpha=0.2, color=color1)
    ax.plot(angles, team1_plot, 'o-', linewidth=2, color=color1, label=name1)
    ax.fill(angles, team2_plot, alpha=0.2, color=color2)
    ax.plot(angles, team2_plot, 's-', linewidth=2, color=color2, label=name2)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=font_prop, size=11)
    ax.set_ylim(0, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(['1', '2', '3', '4', '5'], size=9)
    ax.set_title(title, fontproperties=font_prop, size=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), prop=font_prop, fontsize=10)
    ax.grid(True, alpha=0.3)

fig, axes = plt.subplots(1, 3, figsize=(20, 7), subplot_kw=dict(polar=True))
radar_chart(axes[0], pohang, gimcheon, '浦项制铁', '金泉尚武', '浦项 vs 金泉\n六维对比', '#e74c3c', '#3498db')
radar_chart(axes[1], jeonbuk, fcseoul, '全北现代', 'FC首尔', '全北 vs FC首尔\n六维对比', '#2ecc71', '#e67e22')
radar_chart(axes[2], gangwon, bucheon, '江原FC', '富川FC', '江原 vs 富川\n六维对比', '#9b59b6', '#95a5a6')

fig.suptitle('韩K联第21轮 — 六维雷达图对比', fontproperties=font_prop, size=18, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '1_六维雷达图.png'), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Chart 1 OK: 六维雷达图")

# =============================================
# Chart 2: 三场概率对比柱状图
# =============================================
matches = ['浦项 vs 金泉', '全北 vs FC首尔', '江原 vs 富川']
home_probs = [19.1, 25, 63]
draw_probs = [41.6, 23, 26]
away_probs = [39.3, 52, 11]

x = np.arange(len(matches))
width = 0.25

fig, ax = plt.subplots(figsize=(12, 6))
bars1 = ax.bar(x - width, home_probs, width, label='主胜', color='#e74c3c', alpha=0.85)
bars2 = ax.bar(x, draw_probs, width, label='平局', color='#f39c12', alpha=0.85)
bars3 = ax.bar(x + width, away_probs, width, label='客胜', color='#3498db', alpha=0.85)

for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                   xytext=(0, 5), textcoords="offset points", ha='center', va='bottom',
                   fontproperties=font_prop, fontsize=11, fontweight='bold')

ax.set_ylabel('概率 (%)', fontproperties=font_prop, size=13)
ax.set_title('韩K联第21轮 — 三场胜平负概率对比', fontproperties=font_prop, size=16, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(matches, fontproperties=font_prop, size=12)
ax.legend(prop=font_prop, fontsize=12)
ax.set_ylim(0, 75)
ax.grid(axis='y', alpha=0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, '2_胜平负概率柱状图.png'), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Chart 2 OK: 胜平负概率柱状图")

# =============================================
# Chart 3: 三场饼图
# =============================================
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
pie_data = [
    ([19.1, 41.6, 39.3], '浦项 vs 金泉', ['#e74c3c', '#f39c12', '#3498db']),
    ([25, 23, 52], '全北 vs FC首尔', ['#2ecc71', '#f39c12', '#e67e22']),
    ([63, 26, 11], '江原 vs 富川', ['#9b59b6', '#f39c12', '#95a5a6']),
]

for i, (sizes, title, colors) in enumerate(pie_data):
    labels = ['主胜', '平局', '客胜']
    explode = (0.05, 0.05, 0.05)
    wedges, texts, autotexts = axes[i].pie(sizes, explode=explode, labels=labels, 
                                           colors=colors, autopct='%1.1f%%',
                                           shadow=True, startangle=90,
                                           textprops={'fontproperties': font_prop, 'size': 12})
    for autotext in autotexts:
        autotext.set_fontproperties(font_prop)
        autotext.set_fontsize(13)
        autotext.set_fontweight('bold')
    axes[i].set_title(title, fontproperties=font_prop, size=14, fontweight='bold')

fig.suptitle('韩K联第21轮 — 胜平负概率饼图', fontproperties=font_prop, size=18, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '3_胜平负饼图.png'), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Chart 3 OK: 胜平负饼图")

# =============================================
# Chart 4: 控球率vs进球效率散点+折线图
# =============================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

# 左图: 控球率 vs 场均进球
teams = ['浦项(主)', '金泉(客)', '全北(主)', 'FC首尔(客)', '江原(主)', '富川(客)']
possession = [55.6, 47.8, 54.4, 54.0, 61.3, 45.0]
goals = [0.44, 1.10, 1.78, 1.90, 1.56, 0.90]
colors = ['#e74c3c', '#3498db', '#2ecc71', '#e67e22', '#9b59b6', '#95a5a6']

for i in range(len(teams)):
    ax1.scatter(possession[i], goals[i], c=colors[i], s=200, zorder=5, edgecolors='black', linewidth=1)
    ax1.annotate(teams[i], (possession[i], goals[i]), 
                textcoords="offset points", xytext=(10, 5),
                fontproperties=font_prop, fontsize=10, fontweight='bold')

# 添加趋势线
z = np.polyfit(possession, goals, 1)
p = np.poly1d(z)
x_line = np.linspace(40, 65, 100)
ax1.plot(x_line, p(x_line), '--', color='gray', alpha=0.5, label='趋势线')

ax1.set_xlabel('控球率 (%)', fontproperties=font_prop, size=13)
ax1.set_ylabel('场均进球', fontproperties=font_prop, size=13)
ax1.set_title('控球率 vs 场均进球效率', fontproperties=font_prop, size=14, fontweight='bold')
ax1.legend(prop=font_prop)
ax1.grid(True, alpha=0.3)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# 右图: 场均射门 vs 场均射正
shots = [7.0, 8.0, 12.1, 10.0, 13.2, 8.0]
on_target = [3.7, 3.2, 4.9, 3.8, 4.4, 3.0]

for i in range(len(teams)):
    ax2.scatter(shots[i], on_target[i], c=colors[i], s=200, zorder=5, edgecolors='black', linewidth=1)
    ax2.annotate(teams[i], (shots[i], on_target[i]),
                textcoords="offset points", xytext=(10, 5),
                fontproperties=font_prop, fontsize=10, fontweight='bold')

# 射正转化率等值线
for rate in [0.3, 0.4, 0.5]:
    x_rate = np.linspace(5, 15, 100)
    ax2.plot(x_rate, x_rate * rate, '--', color='gray', alpha=0.3)
    ax2.annotate(f'{rate*100:.0f}%', (14, 14*rate), fontproperties=font_prop, fontsize=9, color='gray')

ax2.set_xlabel('场均射门', fontproperties=font_prop, size=13)
ax2.set_ylabel('场均射正', fontproperties=font_prop, size=13)
ax2.set_title('场均射门 vs 射正（含转化率等值线）', fontproperties=font_prop, size=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

fig.suptitle('韩K联第21轮 — 控球效率分析', fontproperties=font_prop, size=18, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '4_控球效率分析.png'), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Chart 4 OK: 控球效率分析")

# =============================================
# Chart 5: 市场vs模型偏差对比图
# =============================================
fig, ax = plt.subplots(figsize=(12, 6))

match_labels = ['浦项主胜', '浦项平局', '浦项客胜', '全北主胜', '全北平局', '全北客胜', '江原主胜', '江原平局', '江原客胜']
market = [43.7, 29.1, 27.3, 39.2, 32.1, 41.7, 55.0, 28.0, 17.0]
model = [19.1, 41.6, 39.3, 25, 23, 52, 63, 26, 11]
edge = [m - mk for m, mk in zip(model, market)]

x = np.arange(len(match_labels))
width = 0.35

bars1 = ax.bar(x - width/2, market, width, label='市场隐含概率', color='#3498db', alpha=0.8)
bars2 = ax.bar(x + width/2, model, width, label='后台模型概率', color='#e74c3c', alpha=0.8)

# 标注偏差
for i in range(len(match_labels)):
    diff = edge[i]
    color = '#27ae60' if diff > 0 else '#c0392b'
    ax.annotate(f'{diff:+.1f}pp', xy=(x[i], max(market[i], model[i]) + 2),
               ha='center', fontproperties=font_prop, fontsize=9, fontweight='bold', color=color)

ax.set_ylabel('概率 (%)', fontproperties=font_prop, size=13)
ax.set_title('市场定价 vs 后台模型 — 偏差分析', fontproperties=font_prop, size=16, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(match_labels, fontproperties=font_prop, size=10, rotation=30, ha='right')
ax.legend(prop=font_prop, fontsize=12)
ax.set_ylim(0, 75)
ax.grid(axis='y', alpha=0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, '5_市场vs模型偏差.png'), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Chart 5 OK: 市场vs模型偏差")

# =============================================
# Chart 6: 综合对比汇总图
# =============================================
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 左上: 大小球概率
ax = axes[0][0]
match_names = ['浦项vs金泉', '全北vsFC首尔', '江原vs富川']
over_25 = [11.6, 62, 25]
under_25 = [88.4, 38, 75]
x = np.arange(len(match_names))
ax.barh(x, over_25, 0.4, label='大2.5球', color='#e74c3c', alpha=0.8)
ax.barh(x, [-u for u in under_25], 0.4, label='小2.5球', color='#3498db', alpha=0.8)
ax.set_yticks(x)
ax.set_yticklabels(match_names, fontproperties=font_prop, size=12)
ax.set_xlabel('概率 (%)', fontproperties=font_prop, size=12)
ax.set_title('大2.5球概率', fontproperties=font_prop, size=14, fontweight='bold')
ax.legend(prop=font_prop, fontsize=11)
ax.axvline(x=0, color='black', linewidth=0.5)
ax.grid(axis='x', alpha=0.3)

# 右上: 双方进球概率
ax = axes[0][1]
btts_yes = [18.3, 63, 25]
btts_no = [81.7, 37, 75]
colors_yes = ['#2ecc71', '#2ecc71', '#2ecc71']
colors_no = ['#e74c3c', '#e74c3c', '#e74c3c']
bars = ax.bar(match_names, btts_yes, color=colors_yes, alpha=0.8, label='双方进球')
ax.bar(match_names, btts_no, bottom=btts_yes, color=colors_no, alpha=0.4, label='单方或无进球')
for i, v in enumerate(btts_yes):
    ax.text(i, v/2, f'{v:.0f}%', ha='center', fontproperties=font_prop, fontsize=12, fontweight='bold', color='white')
ax.set_ylabel('概率 (%)', fontproperties=font_prop, size=12)
ax.set_title('双方进球概率', fontproperties=font_prop, size=14, fontweight='bold')
ax.legend(prop=font_prop, fontsize=11)
ax.set_ylim(0, 110)

# 左下: 首选比分概率
ax = axes[1][0]
scores = ['0-0\n(浦项)', '1-2\n(全北)', '1-0\n(江原)', '0-1\n(浦项)', '1-1\n(全北)', '2-0\n(江原)']
probs = [31.0, 9.5, 23.2, 23.0, 10.4, 16.2]
colors_bar = ['#e74c3c', '#2ecc71', '#9b59b6', '#e74c3c', '#2ecc71', '#9b59b6']
bars = ax.bar(scores, probs, color=colors_bar, alpha=0.85, edgecolor='black', linewidth=0.5)
for bar, prob in zip(bars, probs):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{prob:.1f}%',
           ha='center', fontproperties=font_prop, fontsize=11, fontweight='bold')
ax.set_ylabel('概率 (%)', fontproperties=font_prop, size=12)
ax.set_title('首选比分概率TOP6', fontproperties=font_prop, size=14, fontweight='bold')
ax.set_xticklabels(scores, fontproperties=font_prop, size=10)
ax.grid(axis='y', alpha=0.3)

# 右下: K联赛效率象限图
ax = axes[1][1]
teams_q = ['浦项(主)', '金泉(客)', '全北(主)', 'FC首尔(客)', '江原(主)', '富川(客)']
efficiency = [0.44/55.6*100, 1.10/47.8*100, 1.78/54.4*100, 1.90/54.0*100, 1.56/61.3*100, 0.90/45.0*100]
defense = [0.78, 1.20, 1.11, 0.90, 0.44, 1.10]
colors_q = ['#e74c3c', '#3498db', '#2ecc71', '#e67e22', '#9b59b6', '#95a5a6']

for i in range(len(teams_q)):
    ax.scatter(efficiency[i], defense[i], c=colors_q[i], s=250, zorder=5, edgecolors='black', linewidth=1)
    ax.annotate(teams_q[i], (efficiency[i], defense[i]),
               textcoords="offset points", xytext=(10, 5),
               fontproperties=font_prop, fontsize=10, fontweight='bold')

# 象限线
ax.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
ax.axvline(x=2.5, color='gray', linestyle='--', alpha=0.5)
ax.text(3.5, 0.4, '高效进攻+强防守', fontproperties=font_prop, fontsize=9, color='green', alpha=0.7)
ax.text(0.5, 0.4, '低效进攻+强防守', fontproperties=font_prop, fontsize=9, color='orange', alpha=0.7)
ax.text(3.5, 1.3, '高效进攻+弱防守', fontproperties=font_prop, fontsize=9, color='blue', alpha=0.7)
ax.text(0.5, 1.3, '低效进攻+弱防守', fontproperties=font_prop, fontsize=9, color='red', alpha=0.7)

ax.set_xlabel('进攻效率 (进球/控球率×100)', fontproperties=font_prop, size=12)
ax.set_ylabel('场均失球', fontproperties=font_prop, size=12)
ax.set_title('攻防效率象限图', fontproperties=font_prop, size=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

fig.suptitle('韩K联第21轮 — 综合数据对比', fontproperties=font_prop, size=18, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(out_dir, '6_综合对比汇总.png'), dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("Chart 6 OK: 综合对比汇总")

print("\n=== All 6 charts saved to:", out_dir, "===")
