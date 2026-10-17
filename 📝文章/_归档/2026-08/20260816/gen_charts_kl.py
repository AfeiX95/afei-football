# -*- coding: utf-8 -*-
"""20260816 两场韩职合辑 图表（matplotlib 深色头条风 -> PNG）"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DengXian", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

PANEL = "#1a1a2e"
TXT = "#e0e0e0"
SUB = "#aaaaaa"
GRID = "#333333"
C_MODEL = "#4fc3f7"
C_MARKET = "#ffd93d"
C_AWAY = "#ff6b6b"
C_OTHER = "#555555"

OUT = r"I:\阿飞说球\charts_20260816"
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
              ncol=2, frameon=False, fontsize=12, labelcolor=[C_MODEL, C_AWAY])
    fig.tight_layout(rect=[0, 0.04, 1, 0.93])
    fig.savefig(os.path.join(OUT, fname), facecolor=PANEL)
    plt.close(fig)


def bar_compare(model, market, labels, title, fname):
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


def signals(rows, title, fname):
    """信号条：方向 | 描述 | 强度(0-100)"""
    fig, ax = plt.subplots(figsize=(8.2, 4.8), dpi=160, facecolor=PANEL)
    ax.set_facecolor(PANEL)
    ax.set_xlim(0, 100)
    ax.set_ylim(len(rows), 0)
    for i, (label, strength) in enumerate(rows):
        color = C_MODEL if strength >= 60 else (C_MARKET if strength >= 40 else C_AWAY)
        ax.barh(i + 0.4, strength, height=0.6, color=color, alpha=0.85, zorder=3)
        ax.text(2, i + 0.4, label, va="center", ha="left", color="#0f0f1a",
                fontsize=10.5, fontweight="bold", zorder=5)
        ax.text(strength + 2, i + 0.4, f"{strength}", va="center", ha="left",
                color=TXT, fontsize=10.5, fontweight="bold")
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(colors=SUB)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.set_axisbelow(True)
    ax.set_title(title, color=TXT, fontsize=15, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), facecolor=PANEL)
    plt.close(fig)


# ================= 第一场：富川FC vs 全北现代 =================
# 六维: 近期状态 进攻火力 防守稳固 交锋历史 市场支持 模型预测
radar([45, 40, 45, 90, 20, 35], [35, 35, 55, 10, 54, 45],
      "富川FC", "全北现代",
      ["近期状态", "进攻火力", "防守稳固", "交锋历史", "市场支持", "模型预测"],
      "六维能力雷达图 | 富川FC vs 全北现代", "m1_radar.png")

bar_compare([24.1, 36.8, 39.1], [20.4, 25.9, 53.7],
            ["富川胜", "平局", "全北胜"],
            "模型 vs 市场概率 | 富川FC vs 全北现代", "m1_bar.png")

pie_dual([24.1, 36.8, 39.1],
         [("1-1", 13.2), ("0-0", 14.2), ("0-1", 15.9), ("1-0", 11.8)],
         "概率分布 & 高概率比分 | 富川FC vs 全北现代", "m1_pie.png")

signals([("H2H克星: 富川近4次对全北不败", 90),
         ("平局价值: 模型36.8% vs 市场25.9%", 78),
         ("全北被高估14.6pp", 72),
         ("富川+1不败 82.4%", 70),
         ("小球倾向 68.9%", 55)],
        "核心信号 | 富川FC vs 全北现代", "m1_signals.png")

# ================= 第二场：仁川联 vs 金泉尚武 =================
radar([50, 55, 50, 60, 41, 45], [45, 40, 45, 40, 29, 30],
      "仁川联", "金泉尚武",
      ["近期状态", "进攻火力", "防守稳固", "交锋历史", "市场支持", "模型预测"],
      "六维能力雷达图 | 仁川联 vs 金泉尚武", "m2_radar.png")

bar_compare([43.9, 33.1, 22.9], [41.2, 29.8, 29.0],
            ["仁川胜", "平局", "金泉胜"],
            "模型 vs 市场概率 | 仁川联 vs 金泉尚武", "m2_bar.png")

pie_dual([43.9, 33.1, 22.9],
         [("1-0", 13.2), ("1-1", 12.7), ("0-0", 9.4), ("2-1", 8.9)],
         "概率分布 & 高概率比分 | 仁川联 vs 金泉尚武", "m2_pie.png")

signals([("金泉平局体质: 赛季55%平率", 80),
         ("H2H: 仁川本赛季2连胜金泉", 72),
         ("让球-1: 仁川打穿仅~20%", 68),
         ("金泉被高估6.1pp", 55),
         ("小球倾向 58%", 45)],
        "核心信号 | 仁川联 vs 金泉尚武", "m2_signals.png")

print("All charts generated!")
