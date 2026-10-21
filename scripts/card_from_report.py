# -*- coding: utf-8 -*-
"""从内部全维度分析报告 → 小红书 D 版单场卡数据（cards.json）

口径
- **只读报告**：情报整理、结论/核心矛盾/看点、λ、近 5 场战绩、底档表，全部从
  `📝文章/<date>/<date>_周X<NN>场_内部分析报告.md` 里取，不另接数据源；
- 报告没有的字段（例如某场缺身价）就留空，卡面自然不画那块，不写「待补」；
- λ 直接用报告里的「综合 λ」，比分网格按泊松重算（报告只留 Top8，不够画热力）。

用法
    python -X utf8 scripts/card_from_report.py --report 📝文章/20261022/20261022_周四11场_内部分析报告.md \
        --out state/tmp/cards_thu.json
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from model import matrix, outcomes  # noqa: E402

HEAD_RE = re.compile(r"^## (周[一二三四五六日]\d{3}) (\S+) (.+?) vs (.+?)　(\S+ \S+)｜让球\s*([+-]?\d+)", re.M)
LAM_RE = re.compile(r"\*\*λ\*\*：主 ([\d.]+) / 客 ([\d.]+)")
L5_RE = re.compile(r"近5场 (\d+)胜(\d+)平(\d+)负（([^）]*)）")
ROW_RE = re.compile(r"^\| (周[一二三四五六日]\d{3}) \| (.+?) \| (.*?) \| (.*?) \| (.*?) \|", re.M)
LAM_ALT_RE = re.compile(r"λ 主 = \*\*([\d.]+)\*\*，λ 客 = \*\*([\d.]+)\*\*")
L5_ALT_RE = re.compile(r"\| 近 5 场进/失 \| ([\d.]+) / ([\d.]+) \| ([\d.]+) / ([\d.]+) \|")
MONEY_RE = re.compile(r"(\d+\.?\d*)\s*([亿万])?")


def parse_money(txt: str) -> tuple:
    """'2.70 亿欧' → ('2.7 亿欧', 2.7)；'5800 万欧' → ('5800 万欧', 0.58)"""
    t = (txt or "").strip()
    m = re.match(r"([\d.]+)\s*(亿|万)?", t)
    if not m:
        return "", None
    v = float(m.group(1))
    unit = m.group(2) or ""
    if unit == "万":
        v = v / 10000.0
    elif not unit and "M" in t.upper():
        v = v / 100.0
    return t, round(v, 2)


def poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam ** k / math.factorial(k)


def grid_of(lh: float, la: float, n: int = 5) -> list:
    """0..4 球 5×5 百分比（%），行=主队进球、列=客队进球。"""
    m = [[poisson(i, lh) * poisson(j, la) for j in range(5)] for i in range(5)]
    return [[round(p * 100, 1) for p in row] for row in m]


def parse_form(blk: str) -> dict:
    out = {}
    for side, name in (("主队", "home"), ("客队", "away")):
        m = None
        for cand in re.finditer(r"近5场 (\d+)胜(\d+)平(\d+)负（([^）]*)）", blk):
            pass
    return out


def parse_match(no: str, blk: str, row: dict) -> dict:
    card = {"no": no, "home": row["home"], "away": row["away"],
            "league": row["league"], "kick": row["kick"]}
    lm = LAM_RE.search(blk) or LAM_ALT_RE.search(blk)
    if lm:
        lh, la = float(lm.group(1)), float(lm.group(2))
        m6 = matrix(lh, la, 12)
        h, d, a = outcomes(m6)
        card["model"] = {"lam": [round(lh, 3), round(la, 3)],
                         "grid": grid_of(lh, la),
                         "wdl": [round(h * 100, 1), round(d * 100, 1), round(a * 100, 1)]}

    # 近 5 场：报告里两队各一段「近5场 x胜y平z负（逐场…）」
    forms = re.findall(r"近5场 (\d+)胜(\d+)平(\d+)负（([^）]*)）", blk)
    seqmap = {"胜": "W", "平": "D", "负": "L"}
    for idx, key in enumerate(("home", "away")):
        if idx >= len(forms):
            break
        w, dr, ls, detail = forms[idx]
        gf = ga = 0
        seq, gfl = [], []
        for item in detail.split("、"):
            sm = re.search(r"(\d+)\s*比\s*(\d+).*?(胜|平|负)\s*$", item)
            if not sm:
                continue
            x, y, r = int(sm.group(1)), int(sm.group(2)), sm.group(3)
            gf += x
            ga += y
            gfl.append(x)
            seq.append(seqmap.get(r, "D"))
        n = len(seq) or 5
        card.setdefault("form", {})[key] = {
            "l5": "%s胜%s平%s负" % (w, dr, ls), "seq": seq, "gf": gf, "ga": ga,
            "n": n, "gfl": gfl, "pj": round(gf / n, 1), "sj": round(ga / n, 1),
            "unbeaten": round((int(w) + int(dr)) / 5.0, 2),
        }
    # 同主客场战绩：从「同主客10场 主6胜0平4负 / 客4胜1平5负」拿
    hm = re.search(r"同主客10场 主(\d+)胜(\d+)平(\d+)负 / 客(\d+)胜(\d+)平(\d+)负", blk)
    if "form" not in card:
        am = L5_ALT_RE.search(blk)
        if am:
            card["form"] = {}
            for idx, key in enumerate(("home", "away")):
                pj, sj = float(am.group(1 + idx * 2)), float(am.group(2 + idx * 2))
                card["form"][key] = {"l5": "", "seq": [], "gfl": [],
                                     "n": 5, "gf": round(pj * 5), "ga": round(sj * 5),
                                     "pj": pj, "sj": sj, "unbeaten": None}
    if hm and card.get("form"):
        g = hm.groups()
        card["form"]["home"]["ha"] = "主场 %s胜%s平%s负" % g[0:3]
        card["form"]["away"]["ha"] = "客场 %s胜%s平%s负" % g[3:6]

    # 情报整理：主队 / 客队 / 其余（身价、交锋、伤停…）
    it = {"home_good": [], "home_bad": [], "away_good": [], "away_bad": [], "common": []}
    mi = blk.find("**情报整理")
    if mi >= 0:
        seg = blk[mi:blk.find("**模型自身的告警**", mi) if blk.find("**模型自身的告警**", mi) > 0 else mi + 900]
        for line in seg.split("\n"):
            line = line.strip()
            if not line.startswith("- "):
                continue
            body = line[2:].strip()
            if body.startswith("主队："):
                it["home_good"].append(body[3:].strip())
            elif body.startswith("客队："):
                it["away_good"].append(body[3:].strip())
            elif body.startswith("伤停："):
                it["common"].append("伤停 —— " + body[3:].strip())
            else:
                it["common"].append(body)
    if any(it.values()):
        card["intel"] = it

    # 六节：结论 / 核心矛盾 / 看点
    mi = blk.find("**核心矛盾**")
    if mi >= 0:
        seg = blk[mi + len("**核心矛盾**："):]
        end = seg.find("**看点**")
        card["narr"] = seg[:end if end > 0 else 400].strip().replace("\n", "").lstrip("：").strip()
    mp = blk.find("**看点**")
    if mp >= 0:
        seg = blk[mp + len("**看点**："):]
        card["point"] = seg.split("\n")[0].strip()
    mc = blk.find("**结论**")
    if mc >= 0:
        card["verdict_text"] = blk[mc + len("**结论**："):].split("\n")[0].strip()

    # 底档：排名 / 身价 / 倍数
    v = {}
    rk = row.get("rank") or ""
    if rk:
        parts = [x.strip() for x in rk.split("/")]
        if len(parts) == 2:
            a = re.sub(r"^.*?第", "第", parts[0]).split("·")[0].strip()
            b = re.sub(r"^.*?第", "第", parts[1]).split("·")[0].strip()
            v["rank_text"] = "%s · %s" % (a, b)
    va = row.get("value") or ""
    if va:
        parts = [x.strip() for x in va.split("/")]
        if len(parts) == 2:
            htxt, hm = parse_money(parts[0])
            atxt, am = parse_money(parts[1])
            if htxt:
                v["home_text"], v["home_m"] = htxt, hm
            if atxt:
                v["away_text"], v["away_m"] = atxt, am
            if hm and am:
                v["ratio"] = "%.2f 倍" % (max(hm, am) / min(hm, am))
    if v:
        # 报告零节已给倍数（按万/亿原值算）就照抄，别用卡面取整后的数字再算一遍
        v["ratio"] = (row.get("mult") or "").strip() or v.get("ratio") or ""
        card["value"] = v
    return card


def main() -> None:
    ap = argparse.ArgumentParser(description="内部报告 → 小红书 D 版卡数据")
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="", help="只取这些场次（逗号分隔）")
    a = ap.parse_args()

    s = io.open(a.report, encoding="utf-8").read()
    # 零节底档表（只在「零、球队底档」这一节里找，别把全批总结的同格式行覆盖进来）
    z = s.find("## 零、球队底档")
    zend = s.find(chr(10) + "## ", z + 5) if z >= 0 else -1
    zseg = s[z:zend] if z >= 0 else ""
    rows = {}
    for m in ROW_RE.finditer(zseg):
        rows[m.group(1)] = {"rank": m.group(3).strip(), "value": m.group(4).strip(),
                            "mult": m.group(5).strip()}
    cards = []
    heads = list(HEAD_RE.finditer(s))
    for i, m in enumerate(heads):
        no, league, home, away, kick, handi = m.groups()
        if a.only and no not in a.only.split(","):
            continue
        blk = s[m.end():heads[i + 1].start() if i + 1 < len(heads) else len(s)]
        row = {"home": home.strip(), "away": away.strip(), "league": league,
               "kick": kick, "handicap": handi, **rows.get(no, {})}
        cards.append(parse_match(no, blk, row))

    data = {"source": os.path.basename(a.report), "matches": cards}
    io.open(a.out, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, ensure_ascii=False, indent=2))
    print("✅ %d 场 → %s" % (len(cards), a.out))
    for c in cards:
        miss = [k for k in ("model", "form", "intel", "narr", "point", "value") if k not in c]
        print("  ·", c["no"], c["home"], "vs", c["away"], "缺:", ",".join(miss) or "无")


if __name__ == "__main__":
    main()
