#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""小红书信息卡的「后台模型」数据块：λ → 比分概率矩阵 → 抽样复核。

对外一律叫「后台模型」，卡片上不出现算法名（泊松/蒙特卡洛）与任何盘口语
（R41 + 三铁律第 2 条）。用法：

    python scripts/xhs_model.py --input "📝文章/20261014/小红书_第二批/cards.json"
    python scripts/xhs_model.py --input <cards.json> --force --n-mc 20000

口径（只吃公开赛果，**不做任何市场折算**）
----------------------------------------
- 输入：`cards.json` 里 `form.{home,away}.pj/sj` ＝ 同主客场均进球 / 场均失球
- λ 结构与 `scripts/model.py` 的方法一同口径：
      λ主 = (主队主场场均进 × 0.92 + 客队客场场均失 × 1.08) / 2
      λ客 = (客队客场场均进 × 0.92 + 主队主场场均失 × 1.08) / 2
- 比分矩阵 = 两支独立泊松（复用 `model.matrix` / `model.outcomes`）
- 抽样复核 = 按 λ 抽 `--n-mc` 次双方进球（种子＝竞彩 id，可复现），
  与解析矩阵比胜平负，偏差 > 1 个百分点就报 ⚠️

产物（写回 cards.json 的 `model` 字段）
--------------------------------------
  lam      [λ主, λ客]
  grid     6×6 比分概率（行＝主队进球 0..5，列＝客队进球 0..5）
  wdl      [主胜, 平, 客胜]（解析）
  wdl_mc   [主胜, 平, 客胜]（抽样）
  mc_delta 两者最大偏差（百分点）
  top      [["1-1", 0.113], …] 概率前五
  guess    "1 比 1"（矩阵最大格，正文文案用）
  n_mc     抽样次数
"""
import argparse
import io
import json
import math
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import matrix, outcomes  # noqa: E402  复用后台模型的矩阵与汇总

ROOT = Path(__file__).resolve().parent.parent

N_MC = 20000
XG_ATT, XG_DEF = 0.92, 1.08   # 与 model.lam_m1 同口径（进攻/防守的进失球校准）
LAM_MIN, LAM_MAX = 0.20, 4.00
GRID = 6                      # 卡片只画 0..5 球
TOP_N = 5
MC_TOL = 0.010                # 解析 vs 抽样 的胜平负容差（1 个百分点）


def lam_from_form(form: dict):
    """同主客场均进失球 → (λ主, λ客)。缺数据返回 None。"""
    h = (form or {}).get("home") or {}
    a = (form or {}).get("away") or {}
    fh, dh = float(h.get("pj") or 0), float(h.get("sj") or 0)   # 主队 主场场均进 / 失
    fa, da = float(a.get("pj") or 0), float(a.get("sj") or 0)   # 客队 客场场均进 / 失
    if not (fh or fa):
        return None

    def cl(v):
        return min(max(v, LAM_MIN), LAM_MAX)

    return cl((fh * XG_ATT + da * XG_DEF) / 2.0), cl((fa * XG_ATT + dh * XG_DEF) / 2.0)


def _pois(rnd: random.Random, lam: float) -> int:
    """Knuth 法抽一个泊松数（进球数）。"""
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        k += 1
        p *= rnd.random()
        if p <= L:
            return k - 1


def mc_wdl(lh: float, la: float, n: int, seed: int):
    """抽样 n 次，返回 (([主胜,平,客胜]), 比分计数 dict)。"""
    rnd = random.Random(seed)
    h = d = a = 0
    cnt = {}
    for _ in range(n):
        i, j = _pois(rnd, lh), _pois(rnd, la)
        cnt[(i, j)] = cnt.get((i, j), 0) + 1
        if i > j:
            h += 1
        elif i == j:
            d += 1
        else:
            a += 1
    return [h / n, d / n, a / n], cnt


def seed_of(card: dict) -> int:
    m = str(card.get("sporttery_match_id") or "")
    if m.isdigit():
        return int(m)
    s = ("%s%s" % (card.get("home", ""), card.get("away", ""))).encode("utf-8")
    return sum(s) * 131 + len(s)


def build(card: dict, n_mc: int = N_MC) -> dict | None:
    lam = lam_from_form(card.get("form") or {})
    if not lam:
        return None
    lh, la = lam
    m = matrix(lh, la, 12)
    g = [[m[i][j] for j in range(GRID)] for i in range(GRID)]
    wdl = outcomes(m)
    cells = sorted(((p, i, j) for i, row in enumerate(g) for j, p in enumerate(row)),
                   key=lambda t: -t[0])
    wd_mc, cnt = mc_wdl(lh, la, n_mc, seed_of(card))
    delta = max(abs(wdl[0] - wd_mc[0]), abs(wdl[1] - wd_mc[1]), abs(wdl[2] - wd_mc[2]))
    # 抽样里最常见的比分（跟矩阵最大格一般一致，不一致时也能一眼看出来）
    top = [["%d-%d" % (i, j), round(p, 4)] for p, i, j in cells[:TOP_N]]
    gi, gj = cells[0][1], cells[0][2]
    return {
        "lam": [round(lh, 2), round(la, 2)],
        "grid": [[round(x, 4) for x in row] for row in g],
        "wdl": [round(x, 4) for x in wdl],
        "wdl_mc": [round(x, 4) for x in wd_mc],
        "mc_delta": round(delta, 4),
        "top": top,
        "guess": "%d 比 %d" % (gi, gj),
        "guess_p": round(cells[0][0], 4),
        "top_mc": ["%d-%d" % k for k, _ in sorted(cnt.items(), key=lambda kv: -kv[1])[:3]],
        "n_mc": n_mc,
    }


def attach(cards_path: Path, force: bool = False, n_mc: int = N_MC) -> int:
    data = json.load(io.open(cards_path, encoding="utf-8"))
    cards = data.get("matches") or []
    ok = 0
    for c in cards:
        tag = "%s %s vs %s" % (c.get("no", ""), c.get("home", ""), c.get("away", ""))
        if c.get("model") and not force:
            print("  –  跳过（已有 model）：" + tag)
            ok += 1
            continue
        got = build(c, n_mc)
        if not got:
            print("  ❌ %s：form 里没有同主客场均进失球，算不了" % tag)
            continue
        c["model"] = got
        w, d, a = got["wdl"]
        wm, dm, am = got["wdl_mc"]
        flag = "" if got["mc_delta"] <= MC_TOL else "  ⚠️ 抽样与解析偏差偏大"
        print("  ✅ %s  λ %.2f/%.2f  主胜 %.1f%% 平 %.1f%% 客胜 %.1f%%  "
              "最大概率比分 %s(%.1f%%)  抽样 %d 次 Δ%.3f%s"
              % (tag, got["lam"][0], got["lam"][1], w * 100, d * 100, a * 100,
                 got["top"][0][0], got["top"][0][1] * 100, n_mc, got["mc_delta"], flag))
        print("      抽样复核：主胜 %.1f%% 平 %.1f%% 客胜 %.1f%%  抽样最常见比分 %s"
              % (wm * 100, dm * 100, am * 100, " / ".join(got["top_mc"])))
        ok += 1
    with io.open(cards_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("已写回 " + str(cards_path))
    return ok


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="给信息卡补「后台模型」块（比分概率矩阵 + 抽样复核）")
    ap.add_argument("--input", required=True, help="cards.json 路径")
    ap.add_argument("--force", action="store_true", help="覆盖已有的 model")
    ap.add_argument("--n-mc", type=int, default=N_MC, help="抽样次数（默认 20000）")
    a = ap.parse_args()
    p = Path(a.input)
    if not p.exists():
        print("找不到 " + str(p))
        sys.exit(1)
    print("【后台模型】→ " + str(p))
    attach(p, a.force, a.n_mc)


if __name__ == "__main__":
    main()
