#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""概率评分台账：Brier / LogLoss（2026-10-11 新增）

为什么要有这个：只统计「方向命中率」会把概率信息全丢掉。
模型报 60% 和报 95% 命中同一场，命中率都记 1，得失分却完全不同 —— Brier / LogLoss 量的是这个。

本仓实测（公司侧 45 场复盘 `公司机_工程/00_引擎/backtest/REVIEW_REPORT.md`）：
    模型  方向 37.8% / Brier 0.695（比随机基线 0.667 还差）/ LogLoss ≈1.087
    市场  方向 46.7% / Brier 0.608
→ 方向以「市场定价 + 盘口结构」为主锚；模型概率只作内部分析，不得进正文（合规 + R37）。

台账：`📚知识库/赛后校验/prob_log.tsv`（制表符分隔，`#` 开头为注释，首行表头）
    日期  场次  模型主  模型平  模型客  市场主  市场平  市场客  实际
    - 概率填 0~1 小数，也接受百分数（60 或 60%）
    - 市场三列要么都填，要么都留空 / 写 `-`（该场没有市场数据）
    - 实际填 主 / 平 / 客（也接受 H / D / A 或 3 / 1 / 0）
    - 一行 = 一个时点的快照（见 14 维技能 1.5：不同时点不得混算）

用法：
    python scripts/calib_score.py                 # 默认台账
    python scripts/calib_score.py <path.tsv>
    python scripts/calib_score.py --json
退出码：0 = 正常（台账为空也算正常）；1 = 台账有格式错误行
"""
import io
import json
import math
import os
import sys

try:                                    # GBK 控制台打印中文/emoji 会 UnicodeEncodeError
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.join(ROOT, "📚知识库", "赛后校验", "prob_log.tsv")
CLASSES = ("主", "平", "客")
ALIAS = {"h": "主", "d": "平", "a": "客", "3": "主", "1": "平", "0": "客"}
UNIFORM_BRIER = 2.0 / 3.0
UNIFORM_LOGLOSS = math.log(3.0)


def parse_p(s):
    s = (s or "").strip()
    if s in ("", "-", "—", "NA", "na", "N/A"):
        return None
    pct = s.endswith("%")
    if pct:
        s = s[:-1]
    try:
        v = float(s)
    except ValueError:
        raise ValueError("不是数字：%s" % s)
    if pct or v > 1.0:
        v /= 100.0
    if not (0.0 <= v <= 1.0):
        raise ValueError("概率越界：%s" % s)
    return v


def parse_actual(s):
    s = (s or "").strip()
    if s in CLASSES:
        return s
    if s.lower() in ALIAS:
        return ALIAS[s.lower()]
    raise ValueError("实际结果无法识别：%s" % s)


def read_rows(path):
    rows, bad = [], []
    with io.open(path, "r", encoding="utf-8-sig") as f:
        for ln, raw in enumerate(f, 1):
            line = raw.rstrip("\n").rstrip("\r")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            cells = [c.strip() for c in line.split("\t")]
            if cells[0] in ("日期", "date"):
                continue                                    # 表头
            if len(cells) < 9:
                bad.append((ln, "列数 %d < 9（需要：日期/场次/模型主平客/市场主平客/实际）" % len(cells)))
                continue
            try:
                model = [parse_p(c) for c in cells[2:5]]
                mkt = [parse_p(c) for c in cells[5:8]]
                actual = parse_actual(cells[8])
            except ValueError as e:
                bad.append((ln, str(e)))
                continue
            if any(p is None for p in model):
                bad.append((ln, "模型三个概率必填"))
                continue
            if all(p is None for p in mkt):
                mkt = None
            elif any(p is None for p in mkt):
                bad.append((ln, "市场概率要么三列都填，要么都留空"))
                continue
            rows.append({"line": ln, "date": cells[0], "match": cells[1],
                         "model": model, "market": mkt, "actual": actual})
    return rows, bad


def norm(probs):
    s = float(sum(probs))
    if abs(s - 1.0) > 0.02:
        raise ValueError("三向概率和 %.3f 偏离 1 超过 2%%" % s)
    return [p / s for p in probs]


def score(probs, actual):
    idx = CLASSES.index(actual)
    brier = sum((p - (1.0 if i == idx else 0.0)) ** 2 for i, p in enumerate(probs))
    logloss = -math.log(max(probs[idx], 1e-15))
    top = CLASSES[max(range(3), key=lambda i: probs[i])]
    return brier, logloss, top


def summarize(rows, key):
    use = [r for r in rows if (r["market"] is not None if key == "market" else True)]
    if not use:
        return None
    briers, lls, hits, skipped = [], [], 0, 0
    for r in use:
        try:
            p = norm(r[key])
        except ValueError:
            skipped += 1
            continue
        b, l, top = score(p, r["actual"])
        briers.append(b)
        lls.append(l)
        hits += (top == r["actual"])
    n = len(briers)
    if not n:
        return None
    return {"n": n, "skipped": skipped, "direction": hits / float(n),
            "brier": sum(briers) / n, "logloss": sum(lls) / n}


def fmt(block):
    if not block:
        return "  （无可用行）"
    return ("  n=%-4d 方向 %5.1f%%   Brier %.3f   LogLoss %.3f%s"
            % (block["n"], block["direction"] * 100, block["brier"], block["logloss"],
               ("（另有 %d 行概率和不等于 1，已跳过）" % block["skipped"]) if block["skipped"] else ""))


def main():
    argv = sys.argv[1:]
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    path = argv[0] if argv else DEFAULT
    if not os.path.exists(path):
        print("[FAIL] 台账不存在：%s" % path)
        return 1

    rows, bad = read_rows(path)
    model = summarize(rows, "model")
    market = summarize(rows, "market")

    if as_json:
        print(json.dumps({"path": path, "rows": len(rows), "bad": bad,
                          "model": model, "market": market,
                          "baseline": {"brier": UNIFORM_BRIER, "logloss": UNIFORM_LOGLOSS}},
                         ensure_ascii=False, indent=2))
        return 1 if bad else 0

    print("概率评分台账（Brier / LogLoss）")
    print("台账：%s" % path)
    print("有效行：%d　坏行：%d" % (len(rows), len(bad)))
    print("")
    print("[模型]")
    print(fmt(model))
    print("[市场]")
    print(fmt(market))
    print("[基准] 均匀三分类：Brier %.3f / LogLoss %.3f（比这还差 = 概率没有信息量）"
          % (UNIFORM_BRIER, UNIFORM_LOGLOSS))
    print("")

    if not rows:
        print("⚠️ 台账暂无数据。Batch#37 及以前没有留下概率快照，不回填（避免事后编造）；")
        print("   从 Batch#38 起每批把模型与市场概率落进 prob_log.tsv（见 football-calibration-batch 记录规范）。")
    else:
        if model and model["brier"] > UNIFORM_BRIER:
            print("🔴 模型 Brier 劣于随机基线——按实测惯例，方向仍以市场定价 + 盘口结构为主锚。")
        if model and market:
            gap = model["brier"] - market["brier"]
            who = "模型更优" if gap < 0 else "市场更优"
            print("📊 Brier：模型 %.3f vs 市场 %.3f（%s，差 %.3f）"
                  % (model["brier"], market["brier"], who, abs(gap)))
            gap_d = model["direction"] - market["direction"]
            print("📊 方向命中：模型 %.1f%% vs 市场 %.1f%%（差 %+.1fpp）"
                  % (model["direction"] * 100, market["direction"] * 100, gap_d * 100))
        elif model:
            print("ℹ️ 台账里没有市场概率行，无法与市场对照（市场概率是这套评分的基准，尽量一起记）。")

    if bad:
        print("")
        print("[坏行]")
        for ln, why in bad:
            print("  L%-4d %s" % (ln, why))
        print("→ 请修好台账再跑；坏行不参与评分。")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
