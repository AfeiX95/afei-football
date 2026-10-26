#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AFEI Backtest v1（P2/P3）

对 A（独立模型）/ M（市场）/ F（当前 v3.1 融合）做同集合同口径回测：
  - Multiclass Brier / Log Loss
  - 分类别可靠性曲线 + ECE（每场×每类为一格）
  - 成对损失差（F−M / A−M / A−F）+ bootstrap 95% CI
  - 分联赛、分数据等级分组
  - P3 探索：w 网格（train 上选 w、test 上报成绩）；弃权策略（按 |A−M| 分档）
默认只统计「未跨开球、非补录、三套概率齐全、结果已出」的场次，全部口径写进报告头。

python scripts/backtest.py [--ledger state/ledger] [--out state/ledger/backtest_x.md]
                          [--include-retrospective] [--train-frac 0.6] [--boot 2000]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
MODELS = ("A", "M", "F")
OUT_IDX = {"H": 0, "D": 1, "A": 2}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def load_sample(ledger: Path, include_retro: bool = False) -> tuple[list[dict], dict]:
    preds, results = [], {}
    for p in sorted((ledger / "predictions").glob("*.jsonl")):
        preds += read_jsonl(p)
    for p in sorted((ledger / "results").glob("*.jsonl")):
        for r in read_jsonl(p):
            results[r["match_id"]] = r

    rows, drop = [], {"no_result": 0, "post_kickoff": 0, "retrospective": 0, "missing_probs": 0}
    for p in preds:
        res = results.get(p["match_id"])
        if not res:
            drop["no_result"] += 1
            continue
        if p.get("post_kickoff"):
            drop["post_kickoff"] += 1
            continue
        if p.get("retrospective") and not include_retro:
            drop["retrospective"] += 1
            continue
        if any(not p["probs"].get(m) for m in MODELS):
            drop["missing_probs"] += 1
            continue
        y = OUT_IDX.get(res["outcome"])
        if y is None:
            drop["missing_probs"] += 1
            continue
        rows.append({"meta": p, "y": y, "P": {m: np.asarray(p["probs"][m], dtype=float) / 100.0 for m in MODELS}})
    rows.sort(key=lambda r: r["meta"].get("kickoff") or r["meta"]["match_id"])
    return rows, drop


def brier(P: np.ndarray, y: int) -> float:
    onehot = np.zeros(3)
    onehot[y] = 1.0
    return float(np.sum((P - onehot) ** 2))


def logloss(P: np.ndarray, y: int) -> float:
    return float(-np.log(max(P[y], 1e-12)))


def pair_matrix(rows: list[dict]) -> dict[str, np.ndarray]:
    return {m: np.array([logloss(r["P"][m], r["y"]) for r in rows]) for m in MODELS}


def boot_ci(d: np.ndarray, n: int = 2000, seed: int = 20261027) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    if len(d) == 0:
        return (float("nan"),) * 3
    idx = rng.integers(0, len(d), size=(n, len(d)))
    means = d[idx].mean(axis=1)
    return float(d.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def reliability(rows: list[dict], model: str, bins: int = 10) -> list[dict]:
    cells = []
    for r in rows:
        for k in range(3):
            cells.append((r["P"][model][k], 1.0 if k == r["y"] else 0.0))
    out = []
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        sel = [(p, y) for p, y in cells if (lo <= p < hi) or (b == bins - 1 and p == 1.0)]
        if not sel:
            continue
        conf = float(np.mean([p for p, _ in sel]))
        acc = float(np.mean([y for _, y in sel]))
        out.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": len(sel), "conf": conf, "acc": acc})
    return out


def ece(rel: list[dict], total: int) -> float:
    return float(sum(r["n"] / total * abs(r["acc"] - r["conf"]) for r in rel)) if total else float("nan")


def group_stats(rows: list[dict], key: str) -> dict:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        g = str(r["meta"].get(key) or "—")
        groups.setdefault(g, []).append(r)
    out = {}
    for g, rs in sorted(groups.items()):
        out[g] = {"n": len(rs), **{f"brier_{m}": float(np.mean([brier(r["P"][m], r["y"]) for r in rs])) for m in MODELS}}
    return out


def w_grid(rows: list[dict], grid: np.ndarray) -> list[dict]:
    res = []
    for w in grid:
        losses = [logloss(w * r["P"]["A"] + (1 - w) * r["P"]["M"], r["y"]) for r in rows]
        briers = [brier(w * r["P"]["A"] + (1 - w) * r["P"]["M"], r["y"]) for r in rows]
        res.append({"w": round(float(w), 2), "n": len(rows), "logloss": float(np.mean(losses)), "brier": float(np.mean(briers))})
    return res


def abstain_table(rows: list[dict], cuts=(0, 5, 10, 15, 25)) -> list[dict]:
    """按 |A−M|（主胜概率差，pp）分档：覆盖率与弃权场次的损失。"""
    out = []
    diffs = [abs(r["P"]["A"][0] - r["P"]["M"][0]) * 100 for r in rows]
    for lo, hi in zip(cuts, cuts[1:] + (999,)):
        sel = [r for r, d in zip(rows, diffs) if lo <= d < hi]
        if not sel:
            continue
        out.append({
            "band": f"{lo}–{hi if hi < 999 else '∞'}pp", "n": len(sel),
            "coverage": len(sel) / len(rows),
            "brier_F": float(np.mean([brier(r["P"]["F"], r["y"]) for r in sel])),
            "brier_M": float(np.mean([brier(r["P"]["M"], r["y"]) for r in sel])),
        })
    return out


def build_report(rows: list[dict], drop: dict, train_frac: float, boot: int) -> str:
    L = []
    L.append("# AFEI 回测报告（A / M / F 同口径）\n")
    L.append(f"- 生成：{datetime.now(TZ).isoformat(timespec='minutes')}　脚本：`scripts/backtest.py`")
    L.append(f"- 样本：**{len(rows)} 场**（未跨开球、非补录、三套概率齐、结果已出）")
    L.append(f"- 剔除：无结果 {drop['no_result']} / 跨开球 {drop['post_kickoff']} / 补录 {drop['retrospective']} / 概率缺失 {drop['missing_probs']}")
    if len(rows) == 0:
        L.append("\n> **样本不足**：当前账本没有可回测的已完成场次。本报告只证明管线可跑；任何 alpha 结论都还不成立。\n")
        return "\n".join(L)

    L.append("\n## 一、总体\n")
    L.append("| 模型 | 口径 | Brier↓ | LogLoss↓ | ECE↓ |")
    L.append("|---|---|--:|--:|--:|")
    label = {"A": "A 独立模型（λ_A）", "M": "M 市场去水", "F": "F 当前融合 v3.1"}
    for m in MODELS:
        b = float(np.mean([brier(r["P"][m], r["y"]) for r in rows]))
        ll = float(np.mean([logloss(r["P"][m], r["y"]) for r in rows]))
        rel = reliability(rows, m)
        L.append(f"| {label[m]} | 三向 | {b:.4f} | {ll:.4f} | {ece(rel, 3*len(rows)):.4f} |")

    L.append("\n## 二、成对损失差（LogLoss，F/M 同一批场次）\n")
    M = pair_matrix(rows)
    L.append("| 对比 | 均值差 | 95% CI（bootstrap） | 读法 |")
    L.append("|---|--:|---|---|")
    for a, b in (("F", "M"), ("A", "M"), ("A", "F")):
        mu, lo, hi = boot_ci(M[a] - M[b], boot)
        verdict = "跨 0，无结论" if lo <= 0 <= hi else ("显著更差" if mu > 0 else "显著更好")
        L.append(f"| {a} − {b} | {mu:+.4f} | [{lo:+.4f}, {hi:+.4f}] | {verdict} |")

    L.append("\n## 三、可靠性（预测概率 vs 实际频率，十档）\n")
    for m in MODELS:
        L.append(f"\n**{m}**\n")
        L.append("| 区间 | 格数 | 平均预测 | 实际频率 |")
        L.append("|---|--:|--:|--:|")
        for r in reliability(rows, m):
            L.append(f"| {r['bin']} | {r['n']} | {r['conf']*100:.1f}% | {r['acc']*100:.1f}% |")

    L.append("\n## 四、分组（Brier）\n")
    for key, name in (("league", "联赛"), ("data_grade", "数据等级")):
        g = group_stats(rows, key)
        if len(g) <= 1:
            continue
        L.append(f"\n**按{name}**\n")
        L.append("| 分组 | n | Brier A | Brier M | Brier F |")
        L.append("|---|--:|--:|--:|--:|")
        for k, v in g.items():
            L.append(f"| {k} | {v['n']} | {v['brier_A']:.4f} | {v['brier_M']:.4f} | {v['brier_F']:.4f} |")

    n_train = max(1, int(len(rows) * train_frac))
    train, test = rows[:n_train], rows[n_train:]
    L.append(f"\n## 五、P3 探索：融合权重 w（A 权重）\n")
    L.append(f"- 时间顺序切分：train = 前 {len(train)} 场，test = 后 {len(test)} 场（禁止用 test 调参）")
    if len(train) < 30 or len(test) < 30:
        L.append(f"- **样本不足**（train {len(train)} / test {len(test)}，各需 ≥30），本轮只列 train 曲线供参考，不作为结论。")
    grid = np.round(np.arange(0, 1.01, 0.1), 2)
    tr = w_grid(train, grid)
    L.append("\n| w（A 权重） | train LogLoss | train Brier |")
    L.append("|--:|--:|--:|")
    for r in tr:
        L.append(f"| {r['w']} | {r['logloss']:.4f} | {r['brier']:.4f} |")
    if len(test) >= 30:
        best = min(tr, key=lambda r: r["logloss"])["w"]
        cur = float(np.mean([logloss(r["P"]["F"], r["y"]) for r in test]))
        alt = float(np.mean([logloss(best * r["P"]["A"] + (1 - best) * r["P"]["M"], r["y"]) for r in test]))
        L.append(f"\n- train 最优 w = **{best}**；test 上 当前融合 {cur:.4f} vs 该 w {alt:.4f}（差 {alt-cur:+.4f}）")

    L.append("\n## 六、P3 探索：弃权分档（按 |A−M| 主胜差）\n")
    L.append("| 档 | n | 覆盖率 | Brier F | Brier M |")
    L.append("|---|--:|--:|--:|--:|")
    for r in abstain_table(rows):
        L.append(f"| {r['band']} | {r['n']} | {r['coverage']*100:.0f}% | {r['brier_F']:.4f} | {r['brier_M']:.4f} |")

    L.append("\n## 七、结论纪律\n")
    L.append("- 未取得足够样本外证据前，不宣称 A 有 alpha；本节只报告数字。")
    L.append("- 权重/弃权阈值的调整只能依据 train 段，test 段只用于报告。")
    L.append("- 跨 0 的置信区间一律读作「无结论」。")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default=str(ROOT / "state" / "ledger"))
    ap.add_argument("--out", default="")
    ap.add_argument("--include-retrospective", action="store_true")
    ap.add_argument("--train-frac", type=float, default=0.6)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args(argv)

    rows, drop = load_sample(Path(args.ledger), args.include_retrospective)
    md = build_report(rows, drop, args.train_frac, args.boot)
    out = Path(args.out) if args.out else ROOT / "state" / "ledger" / f"backtest_{datetime.now(TZ):%Y%m%d}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8", newline="\n")
    print(md[:1200])
    print(f"\n…已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
