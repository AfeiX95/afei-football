# -*- coding: utf-8 -*-
"""从 _intel_<day>.json 生成 model_v3/build_single 需要的 _model_<day>.json

用途：竞彩官方盘口（胜平负 / 让球 / 总进球）→ 市场三向概率、亚盘线与水位。
口径与限制（都写进产物 notes，报告里也照抄）：
- market3：胜平负盘去水概率，归一化到 100%；
- ah_line：竞彩让球数取号，主让为负（-1 = 主让一球）、主受让为正；
- ah_water：竞彩让球盘的主/客十进制赔率减 1 得香港盘水位（近似，非亚盘水位本身）；
- ou_line：竞彩没有大小盘线，一律 None，不折 EV（大小五状态本批不出）；
- ou_implied_total：总进球盘（ttg）去水后的期望总进球。

用法：
    python -X utf8 scripts/market_from_intel.py --date 20261028
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]


def implied_total(ttg: dict) -> float | None:
    odds = ttg.get("odds") or []
    p = ttg.get("p") or []
    if not odds or not p or len(odds) != len(p):
        return None
    tot = sum(p)
    if tot <= 0:
        return None
    return round(sum(k * pk for k, pk in zip(range(len(p)), p)) / tot, 2)


def norm3(p: list[float]) -> list[float] | None:
    if not p or len(p) != 3:
        return None
    s = sum(p)
    if s <= 0:
        return None
    return [round(x / s, 4) for x in p]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    a = ap.parse_args()
    day = a.date
    d = ROOT / "state" / "intel" / day
    intel = json.loads((d / f"_intel_{day}.json").read_text(encoding="utf-8"))
    out = {}
    skipped = []
    for m in intel.get("matches") or []:
        mk = m.get("markets") or {}
        had = mk.get("had") or {}
        hhad = mk.get("hhad") or {}
        m3 = norm3(had.get("p") or [])
        if not m3:
            skipped.append((m.get("no"), "无胜平负去水概率"))
            continue
        raw_line = hhad.get("line")
        line = None
        side = None
        water = (0.0, 0.0)
        if raw_line not in (None, ""):
            try:
                line = float(raw_line)
            except ValueError:
                line = None
            if line is not None:
                side = "主让" if line < 0 else "主受让"
                o = hhad.get("odds") or []
                if len(o) == 3:
                    water = (round(o[0] - 1, 3), round(o[2] - 1, 3))
        ttg = mk.get("ttg") or {}
        rec = {
            "match": "%s %s vs %s" % (m.get("league"), m.get("home"), m.get("away")),
            "kickoff": m.get("kick"),
            "id": None,
            "market3": m3,
            "market_source": "竞彩胜平负去水（_intel had.p 归一化）",
            "jc_ah_line": (-abs(line) if (line is not None and side == "主让") else (abs(line) if line is not None else None)),
            "jc_ah_side": side,
            "jc_ah_water": water,
            "ah_line": None,
            "ah_side": None,
            "ah_water": (0.0, 0.0),
            "ah_line_src": "500 即时众数线（先占位，下面用 books 填）",
            "jc_ah_note": "竞彩让球线与其赔率减 1 的近似水位：只作竞彩口径参考，不参与五状态结算",
            "ou_line": None,
            "ou_water": (0.0, 0.0),
            "ou_note": "竞彩无大小盘线，不折 EV",
            "ou_implied_total": implied_total(ttg),
        }
        out[m.get("no", "")[-3:]] = rec
    # 补齐报告生成器要的 books 派生字段（欧赔众数、亚盘/大小线集合、水位）
    books_p0 = d / f"_books_{day}.json"
    if books_p0.exists():
        books0 = json.loads(books_p0.read_text(encoding="utf-8"))
        from collections import Counter

        def mode3(rows):
            rows = [r for r in rows if r and len(r) == 3]
            if not rows:
                return None
            return [Counter([round(x, 2) for x in r]).most_common(1)[0][0] for r in zip(*rows)]

        def lines(key, field):
            out_l = []
            for bk, v in (key or {}).items():
                seg = v.get(field) or {}
                if seg.get("line") is not None:
                    out_l.append(round(float(seg["line"]), 2))
            return out_l

        for k, r in out.items():
            b = books0.get(k) or {}
            ox = b.get("ox") or {}
            ah = b.get("ah") or {}
            ou = b.get("ou") or {}
            r["id"] = b.get("id")
            r["books_ox"] = len(ox)
            r["ox_open"] = mode3([v.get("open") for v in ox.values()])
            r["ox_close"] = mode3([v.get("close") for v in ox.values()])
            r["ah_open_lines"] = lines(ah, "open")
            r["ah_close_lines"] = lines(ah, "close")
            r["ou_open_lines"] = lines(ou, "open")
            r["ou_close_lines"] = lines(ou, "close")
            # 水位取众数线那本书的即时水位，取不到就用中位数
            pick = None
            if r["ah_close_lines"]:
                mode_line = Counter(r["ah_close_lines"]).most_common(1)[0][0]
                for bk, v in ah.items():
                    c = v.get("close") or {}
                    if c.get("line") is not None and round(float(c["line"]), 2) == mode_line:
                        pick = (round(float(c["home"]), 3), round(float(c["away"]), 3))
                        break
            # 亚盘：线 = 500 即时众数线，水位 = 同线那本书的即时水位（成对）
            if r["ah_close_lines"]:
                mode_line = Counter(r["ah_close_lines"]).most_common(1)[0][0]
                r["ah_line"] = float(mode_line)
                r["ah_side"] = "主让" if mode_line < 0 else ("平手" if mode_line == 0 else "主受让")
                r["ah_line_src"] = "500 即时众数线（%d 家同线）" % r["ah_close_lines"].count(mode_line)
            if r["ou_close_lines"]:
                mode_ou = Counter(r["ou_close_lines"]).most_common(1)[0][0]
                r["ou_line"] = abs(float(mode_ou))
                for bk, v in ou.items():
                    c = v.get("close") or {}
                    if c.get("line") is not None and round(float(c["line"]), 2) == mode_ou:
                        r["ou_water"] = (round(float(c.get("over") or c.get("home") or 0.0), 3),
                                         round(float(c.get("under") or c.get("away") or 0.0), 3))
                        break
            r["ah_water"] = pick or (0.0, 0.0)
            r["lam_1x2"] = [0.0, 0.0]
            r["lam_total"] = 0.0
            r["ev_ah_mkt"] = (None, None)
            r["ev_ou_mkt"] = (None, None)

    # 补齐 500 id（build_single 用 data[books[num]["id"]]）
    books_p = d / f"_books_{day}.json"
    if books_p.exists():
        books = json.loads(books_p.read_text(encoding="utf-8"))
        for k, r in out.items():
            if k in books:
                r["id"] = books[k].get("id")
    path = d / f"_model_{day}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("场次 %d → %s" % (len(out), path))
    for k in sorted(out):
        r = out[k]
        print("  %s %-34s 三向 %s 亚盘 %s%s" % (
            k, r["match"][:34],
            "/".join("%.1f" % (x * 100) for x in r["market3"]),
            r["ah_side"] or "-", "" if r["ah_line"] is None else "%+.2f" % r["ah_line"]))
    for no, why in skipped:
        print("  跳过 %s：%s" % (no, why))


if __name__ == "__main__":
    main()
