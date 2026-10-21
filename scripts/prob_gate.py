#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R54 概率同口径校验（写稿前必跑）

只看两件事：
1) 同一事件才许相减——模型与市场比的是「90 分钟主胜/平/客胜」，别拿让球格去比胜平负；
2) 让球与不让球之间的恒等式必须对得上（让球盘换回胜平负，差 >2.5pp 就报）。

用法：
    python -X utf8 scripts/prob_gate.py --date 20261022
    python -X utf8 scripts/prob_gate.py --date 20261022 --model state/batch/_model_20261022_thu.txt
    python -X utf8 scripts/prob_gate.py --date 20261022 --strict     # FAIL 时退出码 1

输出：逐场一张小表（胜平负和 / 让球和 / 换算差），末行给结论。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
TOL_SUM = 0.35      # 去水三格之和，允许的舍入抖动（百分点）
TOL_XFER = 2.5      # 让球 ↔ 不让球换算允许差（百分点）


def load_intel(date_tag: str) -> dict:
    p = STATE / "intel" / date_tag / f"_intel_{date_tag}.json"
    if not p.exists():
        sys.exit(f"没有情报单：{p}（先跑 prematch_intel.py）")
    return json.loads(p.read_text(encoding="utf-8"))


def parse_model(path: Path) -> dict:
    """从 model.py 落盘的 txt 里抽「胜平负 模型 a/b/c 市场(去水) d/e/f」与比分 Top。"""
    out, cur = {}, None
    if not path or not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(周[一二三四五六日]\d{3})\s+(\S+)\s+vs\s+(\S+)", line)
        if m:
            cur = m.group(1)
            out[cur] = {"home": m.group(2), "away": m.group(3)}
            continue
        if not cur:
            continue
        m = re.match(r"^\s*胜平负\s+模型\s+([\d.]+)%\s*/\s*([\d.]+)%\s*/\s*([\d.]+)%"
                     r"\s+市场\(去水\)\s+([\d.]+)%\s*/\s*([\d.]+)%\s*/\s*([\d.]+)%", line)
        if m:
            g = [float(x) for x in m.groups()]
            out[cur]["model"] = g[:3]
            out[cur]["market"] = g[3:]
    return out


def line_identity(line: str) -> tuple:
    """让球盘线的语义：返回 (符号, 绝对值)。+1 = 主队受让一球，-1 = 主队让一球。"""
    s = str(line or "0").replace("＋", "+").replace("－", "-").strip()
    m = re.match(r"^([+-]?)(\d+)$", s)
    if not m:
        return 0, 0
    sign = -1 if m.group(1) == "-" else 1
    return sign, int(m.group(2))


def check_one(it: dict, model: dict) -> dict:
    mk = it.get("markets") or {}
    no, home, away = it.get("no"), it.get("home"), it.get("away")
    rows = {"no": no, "home": home, "away": away, "sum_ok": None, "xfer_ok": None,
            "note": "", "gap": None, "level": "OK"}
    had, hh = mk.get("had"), mk.get("hhad")
    if not had or not hh:
        rows["note"] = "缺胜平负或让球，无法校验"
        rows["level"] = "SKIP"
        return rows

    H, D, A = had["p"]
    hH, hD, hA = hh["p"]
    sum_had = H + D + A
    sum_hh = hH + hD + hA
    ok_sum = abs(sum_had - 100) <= TOL_SUM and abs(sum_hh - 100) <= TOL_SUM
    rows["sum_ok"] = ok_sum

    sign, n = line_identity(hh.get("line"))
    if n != 1:
        rows["xfer_ok"] = None
        rows["note"] = f"让球 {hh.get('line')}，不是 ±1，本次不做换算（只查三格和）"
        rows["level"] = "OK" if ok_sum else "FAIL"
        return rows

    if sign < 0:      # 主队让一球：让胜 = 主队赢 2+，让平 = 正好赢 1
        implied = hH + hD
        target = H
    else:             # 主队受让一球：让胜 = 主队不败
        implied = hH
        target = H + D
    diff = implied - target
    rows["xfer_ok"] = abs(diff) <= TOL_XFER
    rows["note"] = (f"让球 {hh.get('line')}：让球侧换算 {implied:.1f}% vs 不让球 {target:.1f}%，"
                    f"差 {diff:+.1f}pp")
    rows["level"] = "OK" if (ok_sum and rows["xfer_ok"]) else "FAIL"

    md = model.get(no)
    if md and md.get("model") and md.get("market"):
        mh, mD, mA = md["model"]
        kh, kD, kA = md["market"]
        # 模型与市场必须同事件：这里是「90 分钟胜平负」两边都已去水
        rows["gap"] = round(mh - kh, 1)
        if abs((kh - H)) > TOL_SUM:
            rows["note"] += f"；模型文件里的市场主胜 {kh:.1f}% 与情报单 {H:.1f}% 不一致"
            rows["level"] = "WARN"
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="R54 概率同口径校验")
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--model", default="", help="model.py 落盘的 txt（可选，用来核对模型-市场差值）")
    ap.add_argument("--strict", action="store_true", help="有 FAIL 就返回退出码 1")
    a = ap.parse_args()

    intel = load_intel(a.date)
    model = parse_model(Path(a.model)) if a.model else {}
    rows = [check_one(it, model) for it in intel.get("matches", [])]

    print(f"R54 概率同口径校验 · {a.date} · {len(rows)} 场")
    print("-" * 96)
    print(f"{'场次':<9}{'主 vs 客':<26}{'三格和':<9}{'让球换算':<11}{'模型-市场':<11}备注")
    for r in rows:
        match = f"{r['home']} vs {r['away']}"[:24]
        s = "✅" if r["sum_ok"] else ("—" if r["sum_ok"] is None else "❌")
        x = "✅" if r["xfer_ok"] else ("—" if r["xfer_ok"] is None else "❌")
        g = "—" if r["gap"] is None else f"{r['gap']:+.1f}pp"
        print(f"{r['no']:<9}{match:<26}{s:<9}{x:<11}{g:<11}{r['note']}")

    fails = [r for r in rows if r["level"] == "FAIL"]
    warns = [r for r in rows if r["level"] == "WARN"]
    print("-" * 96)
    print(f"结论：OK {len(rows) - len(fails) - len(warns)} / WARN {len(warns)} / FAIL {len(fails)}"
          f"（三格和容差 {TOL_SUM}pp，让球换算容差 {TOL_XFER}pp）")
    if fails:
        print("⚠️ 有 FAIL：正文里不要把这两套盘的百分比当同一件事写，先把映射补齐再发。")
    if a.strict and fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
