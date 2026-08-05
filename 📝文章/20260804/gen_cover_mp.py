# -*- coding: utf-8 -*-
"""欧冠资格赛两场 头条封面（matplotlib 深色头条风）"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DengXian", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

PANEL = "#1a1a2e"
PANEL2 = "#232345"
TXT = "#ffffff"
SUB = "#b8b8c8"
GOLD = "#ffd93d"
BLUE = "#4fc3f7"
RED = "#ff6b6b"
GRID = "#333333"

OUT = r"I:\阿飞说球\📝文章\20260804\covers"
os.makedirs(OUT, exist_ok=True)


def draw_card(ax, x, y, w, h, home, away, meta, line1, line2, lc1, lc2):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.6",
                         linewidth=1.2, edgecolor="#3a3a5c", facecolor=PANEL2, zorder=2)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 7.0, f"{home}  vs  {away}", ha="center", va="center",
            color=TXT, fontsize=21, fontweight="bold", zorder=3)
    ax.text(x + w / 2, y + h - 15.5, meta, ha="center", va="center",
            color=SUB, fontsize=12.5, zorder=3)
    ax.text(x + w / 2, y + 7.0, line1, ha="center", va="center",
            color=lc1, fontsize=13.5, fontweight="bold", zorder=3)
    ax.text(x + w / 2, y + 1.8, line2, ha="center", va="center",
            color=lc2, fontsize=12, zorder=3)


def cover(kind):
    if kind == "16x9":
        W, H = 100.0, 56.25
        figsize, dpi = (12.8, 7.2), 150
    elif kind == "1x1":
        W, H = 100.0, 100.0
        figsize, dpi = (8.0, 8.0), 150
    else:  # 3x4
        W, H = 75.0, 100.0
        figsize, dpi = (6.0, 8.0), 150

    fig = plt.figure(figsize=figsize, dpi=dpi, facecolor=PANEL)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    ax.set_facecolor(PANEL)

    # 左侧金色竖线 + 顶部细线装饰
    ax.plot([4.5, 4.5], [H - 6, 10], color=GOLD, linewidth=3, solid_capstyle="round")
    ax.plot([4.5, 30], [H - 3.2, H - 3.2], color=GOLD, linewidth=2.2, solid_capstyle="round")

    # 顶部标签
    ax.text(9, H - 8.6, "欧冠资格赛 · 第3轮首回合", ha="left", va="center",
            color=GOLD, fontsize=13.5, fontweight="bold")

    # 主标题
    if kind == "16x9":
        ax.text(9, H - 20.5, "主队全让一球", ha="left", va="center",
                color=TXT, fontsize=40, fontweight="bold")
        ax.text(9, H - 29.5, "市场真的高估了吗？", ha="left", va="center",
                color=GOLD, fontsize=40, fontweight="bold")
        ax.text(9, H - 36.0, "两场欧冠资格赛，后台模型拆给你看", ha="left", va="center",
                color=SUB, fontsize=15)
        # 两场卡片
        cw, ch, gap, cy = 38.5, 15.0, 5.0, 7.5
        draw_card(ax, 9, cy, cw, ch, "奥胡斯", "萨巴赫", "周四 00:30 · 中立场",
                  "平局 37.2% 全场最高", "主胜 29.8% vs 市场 56.5%", BLUE, RED)
        draw_card(ax, 9 + cw + gap, cy, cw, ch, "费内巴切", "格拉茨风暴", "周四 02:00 · 主场",
                  "净胜2球仅 32.2%", "主胜 52.7% vs 市场 71.4%", BLUE, RED)
        ax.text(W - 9, 2.2, "阿飞 · 赛博聊球", ha="right", va="center",
                color=SUB, fontsize=12.5)
    elif kind == "1x1":
        ax.text(9, H - 20.5, "主队全让一球，", ha="left", va="center",
                color=TXT, fontsize=38, fontweight="bold")
        ax.text(9, H - 29.5, "市场真的高估了吗？", ha="left", va="center",
                color=GOLD, fontsize=38, fontweight="bold")
        ax.text(9, H - 36.5, "欧冠资格赛两场前瞻 · 后台模型拆解", ha="left", va="center",
                color=SUB, fontsize=15)
        cw, ch, gap, cy = 38.5, 15.5, 5.0, 30.0
        draw_card(ax, 9, cy, cw, ch, "奥胡斯", "萨巴赫", "周四 00:30 · 中立场",
                  "平局 37.2% 全场最高", "主胜 29.8% vs 市场 56.5%", BLUE, RED)
        draw_card(ax, 9 + cw + gap, cy, cw, ch, "费内巴切", "格拉茨风暴", "周四 02:00 · 主场",
                  "净胜2球仅 32.2%", "主胜 52.7% vs 市场 71.4%", BLUE, RED)
        ax.text(9, 7.0, "数据会说话，但人会说谎。", ha="left", va="center",
                color=SUB, fontsize=15)
        ax.text(W - 9, 2.2, "阿飞 · 赛博聊球", ha="right", va="center",
                color=SUB, fontsize=13)
    else:  # 3x4
        ax.text(9, H - 20.5, "主队全让一球，", ha="left", va="center",
                color=TXT, fontsize=34, fontweight="bold")
        ax.text(9, H - 29.0, "市场真的高估了吗？", ha="left", va="center",
                color=GOLD, fontsize=34, fontweight="bold")
        ax.text(9, H - 35.0, "欧冠资格赛两场前瞻", ha="left", va="center",
                color=SUB, fontsize=14)
        cw, ch, cy = 57, 16.0, 44.0
        draw_card(ax, 9, cy, cw, ch, "奥胡斯", "萨巴赫", "周四 00:30 · 中立场",
                  "平局 37.2% 全场最高", "主胜 29.8% vs 市场 56.5%", BLUE, RED)
        draw_card(ax, 9, cy - ch - 4.5, cw, ch, "费内巴切", "格拉茨风暴", "周四 02:00 · 主场",
                  "净胜2球仅 32.2%", "主胜 52.7% vs 市场 71.4%", BLUE, RED)
        ax.text(9, 7.5, "数据会说话，但人会说谎。", ha="left", va="center",
                color=SUB, fontsize=14)
        ax.text(W - 9, 2.2, "阿飞 · 赛博聊球", ha="right", va="center",
                color=SUB, fontsize=12)

    fig.savefig(os.path.join(OUT, f"cover_{kind}.png"), facecolor=PANEL)
    plt.close(fig)
    print("saved", kind)


for k in ["16x9", "1x1", "3x4"]:
    cover(k)
