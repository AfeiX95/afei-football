# -*- coding: utf-8 -*-
"""日职揭幕两场图表：横滨水手vs鹿岛鹿角 / 大阪钢巴vs浦和红钻"""
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
C_HOME = "#4fc3f7"
C_AWAY = "#ff6b6b"
C_OK = "#7ed957"
C_BAD = "#ff6b6b"

OUT = r"I:\阿飞说球\📝文章\20260807\charts\mp"
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
    ax.plot(angles, h, color=C_HOME, linewidth=2.2)
    ax.fill(angles, h, color=C_HOME, alpha=0.15)
    ax.plot(angles, a, color=C_AWAY, linewidth=2.2)
    ax.fill(angles, a, color=C_AWAY, alpha=0.15)
    ax.scatter(angles[:-1], home, color=C_HOME, s=20, zorder=5)
    ax.scatter(angles[:-1], away, color=C_AWAY, s=20, zorder=5)
    fig.suptitle(title, color=TXT, fontsize=15, fontweight="bold", y=0.95)
    ax.legend([home_name, away_name], loc="lower center", bbox_to_anchor=(0.5, -0.14),
              ncol=2, frameon=False, fontsize=12, labelcolor=[C_HOME, C_AWAY])
    fig.tight_layout(rect=[0, 0.04, 1, 0.93])
    fig.savefig(os.path.join(OUT, fname), facecolor=PANEL)
    plt.close(fig)


def bar_compare(model, ref, ref_label, title, fname):
    labels = ["主胜", "平局", "客胜"]
    x = np.arange(3)
    w = 0.34
    fig, ax = plt.subplots(figsize=(7.4, 5.0), dpi=160, facecolor=PANEL)
    ax.bar(x - w / 2, model, w, color=C_MODEL, label="后台模型", zorder=3)
    ax.bar(x + w / 2, ref, w, color=C_MARKET, label=ref_label, zorder=3)
    for i in range(3):
        ax.text(x[i] - w / 2, model[i] + 1.5, f"{model[i]:.1f}%",
                ha="center", color=C_MODEL, fontsize=11, fontweight="bold")
        ax.text(x[i] + w / 2, ref[i] + 1.5, f"{ref[i]:.1f}%",
                ha="center", color=C_MARKET, fontsize=11)
        edge = model[i] - ref[i]
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


def donut(ax, data, labels, colors, center_text):
    wedges, _ = ax.pie(data, colors=colors, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.40, edgecolor=PANEL, linewidth=2))
    ax.text(0, 0, center_text, ha="center", va="center", color=TXT, fontsize=12.5, fontweight="bold")
    for w, v in zip(wedges, data):
        ang = (w.theta2 + w.theta1) / 2
        x = np.cos(np.deg2rad(ang)) * 1.18
        y = np.sin(np.deg2rad(ang)) * 1.18
        ax.text(x, y, f"{v}%", ha="center", va="center", color=TXT, fontsize=11, fontweight="bold")
    ax.legend(labels, loc="center left", bbox_to_anchor=(0.98, 0.5), frameon=False, fontsize=10)


def pie_chart(data, labels, title, fname, center):
    fig, ax = plt.subplots(figsize=(6.8, 4.9), dpi=160, facecolor=PANEL)
    ax.set_facecolor(PANEL)
    colors = ["#4fc3f7", "#ffd93d", "#ff6b6b"]
    donut(ax, data, labels, colors, center)
    ax.set_title(title, color=TXT, fontsize=15, fontweight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), facecolor=PANEL)
    plt.close(fig)


def signals(rows, title, fname):
    rows = [(t, v) for t, v in rows if v is not None]
    ys = np.arange(len(rows))[::-1]
    fig, ax = plt.subplots(figsize=(7.4, max(2.6, len(rows) * 0.62)), dpi=160, facecolor=PANEL)
    for y, (t, v) in zip(ys, rows):
        c = C_OK if v >= 0 else C_BAD
        ax.barh(y, abs(v), color=c, alpha=0.85, height=0.58, zorder=3)
        ax.text(abs(v) + 0.5, y, f"{v:+d}", va="center", color=c, fontsize=10, fontweight="bold")
        ax.text(-0.5, y, t, va="center", ha="right", color=TXT, fontsize=10.5)
    ax.set_yticks([])
    ax.set_xlim(-28, 28)
    ax.axvline(0, color=GRID, linewidth=0.9)
    ax.set_xticks([-20, -10, 0, 10, 20])
    ax.set_xticklabels(["-20", "-10", "0", "+10", "+20"], color=SUB, fontsize=9)
    style_ax(ax)
    ax.set_title(title, color=TXT, fontsize=14.5, fontweight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), facecolor=PANEL)
    plt.close(fig)


# ============ 第一场 横滨水手 vs 鹿岛鹿角 ============
radar([78, 72, 65, 75, 75, 60], [70, 74, 62, 60, 72, 55],
      "横滨水手", "鹿岛鹿角",
      ["进攻", "防守", "状态", "交锋", "战意", "阵容完整度"],
      "六维战力对比：横滨交锋占优 鹿岛客场疲软", "m1_radar.png")

bar_compare([37.4, 30.0, 32.6], [22.7, 26.7, 50.6], "市场定价(3.90/3.32/1.75)",
            "胜平负概率：模型 vs 市场定价", "m1_bar.png")

pie_chart([33, 35, 32], ["横滨胜", "平局", "鹿岛胜"],
          "修正后概率：平局第一", "m1_pie.png", "平35%")

signals([("鹿岛近3客不胜+0-5惨案", 15), ("鹿岛2主力伤停", 12), ("横滨主场交锋4胜1平", 14),
         ("市场客胜定价50.6%过热", -13), ("横滨缺主力前锋", -8), ("高温30°C或拖慢节奏", -5)],
        "信号图：鹿岛客场成色不足", "m1_signals.png")

# ============ 第二场 大阪钢巴 vs 浦和红钻 ============
radar([80, 68, 70, 45, 60, 70], [62, 82, 68, 85, 78, 70],
      "大阪钢巴", "浦和红钻",
      ["进攻", "防守", "状态", "交锋", "战意", "阵容完整度"],
      "六维战力对比：浦和防守+交锋双压制", "m2_radar.png")

bar_compare([43.5, 28.2, 28.4], [32, 33, 35], "综合修正(H2H+分心)",
            "胜平负概率：基础模型 vs 综合修正", "m2_bar.png")

pie_chart([32, 33, 35], ["钢巴胜", "平局", "浦和胜"],
          "修正后概率：浦和略占优", "m2_pie.png", "浦和35%")

signals([("钢巴主场对浦和近10场1胜7负", 18), ("钢巴4天后踢亚冠附加赛", 13),
         ("浦和场均失球0.7防守顶级", 12), ("浦和近6场5场不败", 10),
         ("钢巴场均进球2.1火力猛", -9), ("浦和客场近10场4胜4负波动大", -6)],
        "信号图：交锋克星+赛程分心", "m2_signals.png")

print("charts done")
