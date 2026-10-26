# -*- coding: utf-8 -*-
"""把 _market_20261027.json 生成可读 md（含每家亚盘线分布与走线明细）"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "state" / "intel" / "20261027"
d = json.loads((OUT / "_market_20261027.json").read_text(encoding="utf-8"))

NAMES = {0.25: "平手/半球", 0.5: "半球", 0.75: "半球/一球", 1.0: "一球", 1.25: "一球/球半",
         1.5: "球半", 1.75: "球半/两球", 2.0: "两球", 2.25: "两球/两球半", 2.5: "两球半"}


def line_txt(ref):
    """ref: 负=主队让球，正=主队受让；恰好落在常见盘口上给中文，否则给「均值」"""
    if ref is None:
        return "-"
    v = round(abs(ref), 2)
    if v < 0.01:
        return "平手"
    side = "主让" if ref < 0 else "主受让"
    if v in NAMES:
        return "%s %s" % (side, NAMES[v])
    return "%s 均%.2f" % (side, v)


def f(v, n=2):
    return "-" if v is None else ("%." + str(n) + "f") % v


L = []
L.append("# 2026-10-27 批次 · 站外欧赔与亚洲盘")
L.append("")
L.append("**来源**：500 彩票网「百家欧指 / 亚指对比」逐场页（每场 15 家欧赔公司、3–7 家亚指公司）；"
         "意甲三场用 betexplorer.com 交叉核对一致（都灵-科莫 4.68/3.80/1.74 vs 本表 4.53/3.85/1.72）。"
         "抓取时间 2026-10-26 深夜，均为赛前即时。")
L.append("")
L.append("**口径**：欧赔 = 各公司算术平均（初盘 / 即时）；去水 = 1/赔率归一化后的百分比。"
         "亚盘 ref：负值 = 主队让球，正值 = 主队受让；水位为即时（主 / 客），水位低的一侧是被买的一侧。")
L.append("")
L.append("## 一、总表")
L.append("")
L.append("| 编号 | 对阵 | 开球 | 初盘 1X2 | 即时 1X2 | 即时去水(主/平/客) | 亚盘初盘(均) | 亚盘即时(均) | 即时最常见线 | 走线/家数 | 水位(主/客) |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|")
for no in sorted(d):
    r = d[no]
    L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %d/%d | %s / %s |" % (
        no, r["match"], r["kickoff"], "/".join(f(x) for x in r["ox_open"]),
        "/".join(f(x) for x in r["ox_close"]), "/".join("%.1f%%" % x for x in r["prob_close"]),
        line_txt(r["ah_avg_open"]), line_txt(r["ah_avg_close"]), line_txt(r["ah_modal_close"]),
        r["ah_moved"], r["books_ah"], f(r["ah_water"][0], 3), f(r["ah_water"][1], 3)))

L.append("")
L.append("## 二、逐场：亚盘线分布（即时）+ 欧赔位移")
L.append("")
for no in sorted(d):
    r = d[no]
    ah, ox = r["detail_ah"], r["detail_1x2"]
    L.append("### %s %s（%s）" % (no, r["match"], r["kickoff"]))
    L.append("")
    if ox:
        L.append("- 欧赔均值：初盘 %s → 即时 %s（主 %s→%s，客 %s→%s）" % (
            "/".join(f(x) for x in r["ox_open"]), "/".join(f(x) for x in r["ox_close"]),
            f(r["ox_open"][0]), f(r["ox_close"][0]), f(r["ox_open"][2]), f(r["ox_close"][2])))
        L.append("- 去水概率：初盘 %s → 即时 %s" % (
            "/".join("%.1f%%" % x for x in r["prob_open"]), "/".join("%.1f%%" % x for x in r["prob_close"])))
    if ah:
        cnt = Counter(b["close"]["ref"] for b in ah)
        dist = "，".join("%s×%d" % (line_txt(k), v) for k, v in sorted(cnt.items(), key=lambda x: -x[1]))
        L.append("- 即时线分布（%d 家）：%s" % (len(ah), dist))
        moves = ["%s %s→%s" % (b["book"], f(b["open"]["ref"]), f(b["close"]["ref"]))
                 for b in ah if b["open"]["ref"] != b["close"]["ref"]]
        L.append("- 走线：%s" % ("；".join(moves) if moves else "无位移"))
        wh, wa = r["ah_water"]
        L.append("- 平均水位：主 %s / 客 %s（低水一侧 = %s）" % (
            f(wh, 3), f(wa, 3), "主队" if (wh or 1) < (wa or 1) else "客队"))
    L.append("")

(OUT / "_market_20261027.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("wrote", OUT / "_market_20261027.md")

