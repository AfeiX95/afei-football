# -*- coding: utf-8 -*-
"""周六报告 → 小红书 D 版 cards.json（周六版解析适配）

周六报告格式：
    ### 周六001 韩职 首尔FC vs 江原FC　13:00 开赛
    **预测**：首选 **客胜** 39.8% · 0-1　｜　次选 主胜 33.7% · 1-0　｜　防范 平 26.5% · 1-1
    **模型**：λ 主 1.22 / 客 1.35（…）；…；综合 1.22 + 1.35 = 2.58
    **球队**：近期 主 5 场 1.00进1.80失 / 客 5 场 0.80进0.80失；交锋 5 场 场均 3.20 球、低比分 40%、平局 40%；伤停 0 人。

用法：
    python -X utf8 scripts/mk_sat_cards.py --report <报告> --out <json> [--only 001,003,...]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from model import matrix  # noqa: E402

HEAD = re.compile(r"^### (周六\d{3})\s+(\S+)\s+(.+?)\s+vs\s+(.+?)　(\d{2}:\d{2}) 开赛", re.M)
PRED = re.compile(r"首选 \*\*(.+?)\*\* ([\d.]+)%\s*·\s*([\d-]+)")
PRED2 = re.compile(r"次选 \*?([^\s*]+)\*?\s*([\d.]+)%")
PRED3 = re.compile(r"防范 \*?([^\s*]+)\*?\s*([\d.]+)%")
LAM = re.compile(r"λ 主 ([\d.]+) / 客 ([\d.]+)")
FORM = re.compile(r"近期 主 \d+ 场 ([\d.]+)进([\d.]+)失 / 客 \d+ 场 ([\d.]+)进([\d.]+)失")
H2H = re.compile(r"交锋 (\d+) 场 场均 ([\d.]+) 球")
LOW = re.compile(r"低比分 (\d+)%")
INJ = re.compile(r"伤停 ([^；。\n]+)")

CN = {"主胜": "home", "客胜": "away", "平": "draw", "平局": "draw"}


def _num(x):
    try:
        return float(x)
    except Exception:  # noqa: BLE001
        return None


def parse(report: str) -> list[dict]:
    blocks = []
    ms = list(HEAD.finditer(report))
    for i, m in enumerate(ms):
        start = m.start()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(report)
        body = report[start:end]
        no, league, home, away, kick = m.groups()
        lam = LAM.search(body)
        if not lam:
            continue
        lh, la = float(lam.group(1)), float(lam.group(2))
        wdl = {}
        for side, pct in re.findall(r"(主胜|客胜|平|平局) ([\d.]+)%", body):
            k = CN.get(side)
            if k and k not in wdl:
                wdl[k] = float(pct)
        if len(wdl) < 3:
            continue
        fm = FORM.search(body)
        hh = H2H.search(body)
        lo = LOW.search(body)
        inj = INJ.search(body)
        pred = PRED.search(body)
        blocks.append({
            "no": no, "league": league, "home": home.strip(), "away": away.strip(),
            "kick": kick, "lam": (lh, la), "wdl": wdl,
            "form": tuple(float(x) for x in fm.groups()) if fm else None,
            "h2h": (int(hh.group(1)), float(hh.group(2))) if hh else None,
            "low": int(lo.group(1)) if lo else None,
            "inj": (inj.group(1).strip() if inj else ""),
            "pick": (pred.group(1), float(pred.group(2)), pred.group(3)) if pred else None,
        })
    return blocks


def _clamp(x, lo=12, hi=94):
    return max(lo, min(hi, round(x)))


def _intel_lines(card: dict) -> list:
    f = card.get("form", {}) or {}
    h, a = f.get("home", {}) or {}, f.get("away", {}) or {}
    out = []
    if h.get("l5") or a.get("l5"):
        out.append("近 5 场：主 %s ／ 客 %s" % (h.get("l5") or "—", a.get("l5") or "—"))
    if h.get("pj") is not None and a.get("pj") is not None:
        out.append("场均进失：主 %s 进 / %s 失 ・ 客 %s 进 / %s 失"
                   % (h.get("pj"), h.get("sj"), a.get("pj"), a.get("sj")))
    h2h = (card.get("form", {}) or {}).get("h2h") or {}
    if isinstance(h2h, dict) and h2h.get("n"):
        out.append("交锋 %s 场 · 场均 %s 球%s" % (
            h2h.get("n"), h2h.get("avg_goals") or "—",
            (" · " + h2h.get("note")) if h2h.get("note") else ""))
    v = card.get("value") or {}
    if v.get("home_text") and v.get("away_text"):
        out.append("账面：主 %s ／ 客 %s（差 %s）" % (v["home_text"], v["away_text"], v.get("ratio") or v.get("ratio_text") or "—"))
    return out[:4]


def _radar(b: dict) -> dict:
    lh, la = b["lam"]
    hf, ha, af, aa = b["form"] or (1.4, 1.2, 1.1, 1.3)

    def side(pj, sj):
        atk = _clamp(18 + pj * 30)
        dfn = _clamp(96 - sj * 26)
        mid = _clamp((atk + dfn) / 2)
        form = _clamp(50 + (pj - sj) * 22)
        ha_v = _clamp(52 + (pj - sj) * 14)
        stab = _clamp(96 - abs(pj - sj) * 16)
        return [atk, mid, dfn, form, ha_v, stab]

    return {"dims": ["进攻", "中场控制", "防守", "近期状态", "主客场", "进球稳定"],
            "home": side(hf, ha), "away": side(af, aa)}


def to_card(b: dict, narr: dict, point: dict) -> dict:
    lh, la = b["lam"]
    g = matrix(lh, la)
    grid = [[round(g[i][j] * 100, 2) for j in range(5)] for i in range(5)]
    form = {"home": {}, "away": {}}
    if b["form"]:
        hf, ha, af, aa = b["form"]
        form["home"].update({"pj": hf, "sj": ha, "gf": round(hf * 5, 1), "ga": round(ha * 5, 1),
                             "n": 5, "ha": "近 5 场"})
        form["away"].update({"pj": af, "sj": aa, "gf": round(af * 5, 1), "ga": round(aa * 5, 1),
                             "n": 5, "ha": "近 5 场"})
    h2h = {}
    if b["h2h"]:
        n, avg = b["h2h"]
        h2h = {"n": n, "avg_goals": avg, "note": ("低比分 %d%%" % b["low"]) if b["low"] else ""}
    common = []
    if b["inj"]:
        common.append("伤停：%s" % b["inj"])
    if h2h:
        common.append("交锋 %d 场 · 场均 %.2f 球" % (h2h["n"], h2h["avg_goals"]))
    card = {
        "no": b["no"], "league": b["league"], "home": b["home"], "away": b["away"],
        "kick": b["kick"],
        "model": {"lam": [lh, la], "grid": grid,
                  "wdl": [b["wdl"].get("home", 0), b["wdl"].get("draw", 0), b["wdl"].get("away", 0)]},
        "radar": _radar(b),
        "form": form, "h2h": h2h,
        "intel": {"common": common},
        "narr": narr.get(b["no"], ""),
        "point": point.get(b["no"], ""),
        "pie_mode": "form", "pie_title": "赛果构成",
        "pie_note": "已发生数据",
    }
    extra = _intel_lines(card)
    merged = []
    for line in extra + common:
        if line not in merged:
            merged.append(line)
    if merged:
        card["intel"]["common"] = merged[:4]
    return card


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    report = io.open(a.report, encoding="utf-8").read()
    blocks = parse(report)
    if a.only:
        keep = {"周六" + x.strip() for x in a.only.split(",") if x.strip()}
        blocks = [b for b in blocks if b["no"] in keep]
    cards = [to_card(b, {}, {}) for b in blocks]
    data = {"meta": {"date": "10.24", "weekday": "周六",
                     "kick_day": "10/24 13:00 起", "tail": "十二场，先看账，再看球"},
            "matches": cards}
    io.open(a.out, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
    print("✅ %d 场 → %s" % (len(cards), a.out))


if __name__ == "__main__":
    main()
