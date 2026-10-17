# -*- coding: utf-8 -*-
"""欧冠资格赛两场 图表（matplotlib 深色头条风 -> PNG）"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DengXian", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

PANEL = "#1a1a2e"      # 图表面板底色
TXT = "#e0e0e0"
SUB = "#aaaaaa"
GRID = "#333333"
C_MODEL = "#4fc3f7"    # 后台模型
C_MARKET = "#ffd93d"   # 市场定价
C_AWAY = "#ff6b6b"
C_OTHER = "#555555"

OUT = r"I:\阿飞说球\📝文章\20260804\charts\mp"
os.makedirs(OUT, exist_ok=True)


def style_ax(ax):
    ax.set_facecolor(PANEL)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(colors=SUB)


def radar(home, away, home_name, away_name, dims, title, fname):
    n = len(dims)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]
    h = home + home[:1]
    a = away + away[:1]
    fig = plt.figure(figsize=(7.4, 5.4), dpi=160, facecolor=PANEL)
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor(PANEL)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_rlabel_position(18)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100"], color=SUB, fontsize=9)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dims, color=SUB, fontsize=11)
    ax.grid(color=GRID, linewidth=0.7)
    ax.spines["polar"].set_color(GRID)
    ax.plot(angles, h, color=C_MODEL, linewidth=2.2)
    ax.fill(angles, h, color=C_MODEL, alpha=0.15)
    ax.plot(angles, a, color=C_AWAY, linewidth=2.2)
    ax.fill(angles, a, color=C_AWAY, alpha=0.15)
    ax.scatter(angles[:-1], home, color=C_MODEL, s=20, zorder=5)
    ax.scatter(angles[:-1], away, color=C_AWAY, s=20, zorder=5)
    fig.suptitle(title, color=TXT, fontsize=15, fontweight="bold", y=0.95)
    ax.legend([home_name, away_name], loc="lower center", bbox_to_anchor=(0.5, -0.14),
              ncol=2, frameon=False, fontsize=12,
              labelcolor=[C_MODEL, C_AWAY])
    fig.tight_layout(rect=[0, 0.04, 1, 0.93])
    fig.savefig(os.path.join(OUT, fname), facecolor=PANEL)
    plt.close(fig)


def bar_compare(model, odds, title, fname):
    inv = [1.0 / o for o in odds]
    market = [100.0 * x / sum(inv) for x in inv]
    labels = ["主胜", "平局", "客胜"]
    x = np.arange(3)
    w = 0.34
    fig, ax = plt.subplots(figsize=(7.4, 5.0), dpi=160, facecolor=PANEL)
    ax.bar(x - w / 2, model, w, color=C_MODEL, label="后台模型", zorder=3)
    ax.bar(x + w / 2, market, w, color=C_MARKET, label="市场定价", zorder=3)
    for i in range(3):
        ax.text(x[i] - w / 2, model[i] + 1.5, f"{model[i]:.1f}%",
                ha="center", color=C_MODEL, fontsize=11, fontweight="bold")
        ax.text(x[i] + w / 2, market[i] + 1.5, f"{market[i]:.1f}%",
                ha="center", color=C_MARKET, fontsize=11)
        edge = model[i] - market[i]
        ax.text(x[i], -8, f"{edge:+.1f}pp", ha="center",
                color=C_MODEL if edge > 0 else C_AWAY, fontsize=10.5, fontweight="bold")
    ax.axhline(0, color=GRID, linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=TXT, fontsize=12.5)
    ax.set_ylim(-16, 84)
    style_ax(ax)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False, fontsize=11.5)
    ax.set_title(title, color=TXT, fontsize=15, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), facecolor=PANEL)
    plt.close(fig)


def donut(ax, data, labels, colors, center_text, legend_col=1):
    wedges, _ = ax.pie(data, colors=colors, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.40, edgecolor=PANEL, linewidth=2))
    ax.text(0, 0, center_text, ha="center", va="center", color=TXT, fontsize=12.5, fontweight="bold")
    for w, v in zip(wedges, data):
        ang = np.deg2rad((w.theta1 + w.theta2) / 2)
        x = np.cos(ang) * 0.80
        y = np.sin(ang) * 0.80
        ax.text(x, y, f"{v:.1f}%", ha="center", va="center",
                color="#0f0f1a", fontsize=10.5, fontweight="bold")
    ax.legend(labels, loc="lower center", bbox_to_anchor=(0.5, -0.32),
              ncol=legend_col, frameon=False, fontsize=10.5)


def pie_dual(model, scores, title, fname):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.6, 4.6), dpi=160, facecolor=PANEL)
    donut(ax1, model, ["主队胜", "平局", "客队胜"], [C_MODEL, C_MARKET, C_AWAY], "胜平负分布", legend_col=3)
    s_labels = [s[0] for s in scores]
    s_colors = [C_MODEL, C_MARKET, C_AWAY, C_OTHER]
    donut(ax2, [s[1] for s in scores], s_labels, s_colors, "高概率比分", legend_col=2)
    fig.suptitle(title, color=TXT, fontsize=15, fontweight="bold", y=0.98)
    fig.tight_layout(rect=[0, 0.10, 1, 0.94])
    fig.savefig(os.path.join(OUT, fname), facecolor=PANEL)
    plt.close(fig)


def signals(items, title, fname):
    y = np.arange(len(items))[::-1]
    h = 0.32
    fig, ax = plt.subplots(figsize=(7.4, 3.8), dpi=160, facecolor=PANEL)
    ax.barh(y + h / 2, [m for _, m, _ in items], h, color=C_MODEL, label="后台模型", zorder=3)
    ax.barh(y - h / 2, [k for _, _, k in items], h, color=C_MARKET, label="市场定价", zorder=3)
    for i, (lab, m, k) in enumerate(items):
        ax.text(m + 1.5, y[i] + h / 2, f"{m:.1f}%", va="center",
                color=C_MODEL, fontsize=11, fontweight="bold")
        ax.text(k + 1.5, y[i] - h / 2, f"{k:.1f}%", va="center",
                color=C_MARKET, fontsize=11)
    ax.set_yticks(y)
    ax.set_yticklabels([i[0] for i in items], color=TXT, fontsize=12.5)
    ax.set_xlim(0, 78)
    style_ax(ax)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6, alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=11.5)
    ax.set_title(title, color=TXT, fontsize=15, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), facecolor=PANEL)
    plt.close(fig)


DIMS = ["近期状态", "进攻火力", "防守稳固", "交锋历史", "市场支持", "模型预测"]

# 场1 奥胡斯 vs 萨巴赫
radar([50, 62, 45, 50, 57, 30], [67, 50, 78, 50, 19, 33],
      "奥胡斯", "萨巴赫", DIMS, "六维战力对比雷达图", "m1_radar.png")
bar_compare([29.8, 37.2, 33.0], [1.57, 3.65, 4.60],
            "后台模型 vs 市场定价（主胜高估26.7pp）", "m1_bar.png")
pie_dual([29.8, 37.2, 33.0], [("0-0", 19.5), ("1-0", 17.8), ("0-1", 14.0), ("其他", 48.7)],
         "模型概率分布 & 高概率比分", "m1_pie.png")
signals([("让球负（主队-1）", 58.5, 42.5), ("大2.5（总进球≥3）", 24.0, 53.0)],
        "关键预期对比：让球与大小球", "m1_signals.png")

# 场2 费内巴切 vs 格拉茨风暴
radar([60, 75, 65, 55, 71, 53], [70, 55, 68, 45, 11, 19],
      "费内巴切", "格拉茨风暴", DIMS, "六维战力对比雷达图", "m2_radar.png")
bar_compare([52.7, 27.9, 19.4], [1.24, 5.05, 8.0],
            "后台模型 vs 市场定价（主胜高估18.7pp）", "m2_bar.png")
pie_dual([52.7, 27.9, 19.4], [("1-0", 19.4), ("2-0", 14.6), ("0-0", 13.0), ("其他", 53.0)],
         "模型概率分布 & 高概率比分", "m2_pie.png")
signals([("净胜2球以上", 32.2, 48.9), ("大2.5（总进球≥3）", 34.0, 57.5)],
        "关键预期对比：净胜与大小球", "m2_signals.png")

print("DONE")
for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)))
