#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""赛前盘口采集 · 处理 · 情报单

写文章 / 做小红书卡片之前统一跑这一条：把竞彩官方五套盘口（胜平负 / 让球 /
总进球 / 半全场 / 波胆）连同历史快照抓下来，去水算成真实概率，做跨盘一致性
与位移检查，再并进伤停 / 近期 / 交锋，最后落一份可以直接读的情报单。

用法：
    python -X utf8 scripts/prematch_intel.py                 # 今天（按 slate 的 businessDate）
    python -X utf8 scripts/prematch_intel.py --date 20261018
    python -X utf8 scripts/prematch_intel.py --no-fetch       # 只用已有缓存，不联网
    python -X utf8 scripts/prematch_intel.py --ext            # 顺带跑一次外部预测

产出：
    state/intel/<date>/_intel_<date>.json   机器可读，逐场结构化
    state/intel/<date>/_intel_<date>.md     人读的一页情报单（写稿前看这个）
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
CACHE = STATE / "cache"
MATCHES = STATE / "matches"
INTEL = STATE / "intel"
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import paid_cyber as pc  # noqa: E402  复用 read_json / devig / team_form / meetings / injuries

DIRS = ["主胜", "平", "客胜"]
TTG_KEYS = ["s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7"]
HAFU_KEYS = [
    ("hh", "胜胜"), ("hd", "胜平"), ("ha", "胜负"),
    ("dh", "平胜"), ("dd", "平平"), ("da", "平负"),
    ("ah", "负胜"), ("ad", "负平"), ("aa", "负负"),
]


# ────────────────────────────────────────────── 工具
def f(x, n: int = 1) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return "—"


def pct(x) -> str:
    return "—" if x is None else f"{x:.1f}%"


def payout_of(odds: list[float]) -> float:
    """返还率：三格（或多格）赔率倒数之和的倒数。"""
    s = sum(1.0 / o for o in odds if o and o > 1.0)
    return round(100.0 / s, 2) if s > 0 else 0.0


def devig(odds: list[float]) -> list[float]:
    """不去指定抽水，直接用各格倒数的占比归一——等价于按该盘自身返还率去水。"""
    inv = [1.0 / o if o and o > 1.0 else 0.0 for o in odds]
    s = sum(inv)
    return [round(100.0 * x / s, 1) for x in inv] if s > 0 else [0.0] * len(odds)


def _odds(row: dict, keys: tuple[str, ...]) -> list[float]:
    out = []
    for k in keys:
        v = row.get(k)
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            out.append(0.0)
    return out


def crs_label(key: str) -> str:
    """波胆键名 → 人读比分。s01s00 → 1-0；s-1sh/s-1sd/s-1sa 是三个「其他」。"""
    k = key.strip()
    special = {"s-1sh": "胜其他", "s-1sd": "平其他", "s-1sa": "负其他"}
    if k in special:
        return special[k]
    if len(k) == 6 and k[0] == "s" and k[3] == "s":
        try:
            return f"{int(k[1:3])}-{int(k[4:6])}"
        except ValueError:
            return k
    return k


def _stamp(row: dict) -> str:
    d = row.get("updateDate") or ""
    t = row.get("updateTime") or ""
    return f"{d} {t}".strip()


# ────────────────────────────────────────────── 盘口
def read_bonus(mid: str) -> dict:
    p = CACHE / f"_bonus_{mid}.json"
    if not p.exists():
        return {}
    try:
        return pc.read_json(p).get("value") or {}
    except Exception:  # noqa: BLE001
        return {}


def parse_markets(mid: str) -> dict:
    """把五套盘拆成：最新赔率 / 去水概率 / 快照次数 / 首末位移。"""
    v = read_bonus(mid)
    hist = v.get("oddsHistory") or {}
    out: dict = {"available": bool(hist)}

    def series(key: str) -> list[dict]:
        arr = hist.get(key) or []
        return [r for r in arr if isinstance(r, dict)]

    # 胜平负
    had = series("hadList")
    if had:
        o = _odds(had[-1], ("h", "d", "a"))
        po = payout_of(o)
        out["had"] = {
            "n": len(had), "stamp": _stamp(had[-1]), "odds": o,
            "p": devig(o), "payout": po,
            "open_odds": _odds(had[0], ("h", "d", "a")),
            "open_p": devig(_odds(had[0], ("h", "d", "a"))),
            "open_stamp": _stamp(had[0]),
        }
    # 让球
    hhad = series("hhadList")
    if hhad:
        o = _odds(hhad[-1], ("h", "d", "a"))
        out["hhad"] = {
            "n": len(hhad), "stamp": _stamp(hhad[-1]), "odds": o,
            "line": hhad[-1].get("goalLine") or "",
            "p": devig(o), "payout": payout_of(o),
            "open_odds": _odds(hhad[0], ("h", "d", "a")),
            "open_p": devig(_odds(hhad[0], ("h", "d", "a"))),
            "open_line": hhad[0].get("goalLine") or "",
            "open_stamp": _stamp(hhad[0]),
        }
    # 总进球
    ttg = series("ttgList")
    if ttg:
        o = _odds(ttg[-1], tuple(TTG_KEYS))
        out["ttg"] = {
            "n": len(ttg), "stamp": _stamp(ttg[-1]), "odds": o,
            "p": devig(o), "payout": payout_of(o),
            "open_odds": _odds(ttg[0], tuple(TTG_KEYS)),
        }
    # 半全场
    hafu = series("hafuList")
    if hafu:
        keys = tuple(k for k, _ in HAFU_KEYS)
        o = _odds(hafu[-1], keys)
        out["hafu"] = {
            "n": len(hafu), "stamp": _stamp(hafu[-1]), "odds": o,
            "p": devig(o), "payout": payout_of(o),
            "labels": [lab for _, lab in HAFU_KEYS],
        }
    # 波胆
    crs = series("crsList")
    if crs:
        row = crs[-1]
        cells = []
        for k, val in row.items():
            if not k.startswith("s") or k.endswith("f") or k in ("s-1sd", "s-1sh", "s-1sa"):
                continue
            try:
                cells.append((k, float(val)))
            except (TypeError, ValueError):
                continue
        cells = [(k, o) for k, o in cells if o > 1.0]
        cells.sort(key=lambda x: x[1])
        inv = sum(1.0 / o for _, o in cells)
        out["crs"] = {
            "n": len(crs), "stamp": _stamp(crs[-1]),
            "cells": [(crs_label(k), o, round(100.0 / o / inv, 1) if inv else 0.0) for k, o in cells],
            "payout": round(100.0 / inv, 2) if inv else 0.0,
            "count": len(cells),
        }
    return out


def cross_check(mk: dict) -> list[str]:
    """跨盘一致性：让球盘与不让球盘之间是有恒等关系的，对不上就是定价内部有矛盾。"""
    ps: list[str] = []
    had, hh, ttg = mk.get("had"), mk.get("hhad"), mk.get("ttg")
    if had and hh:
        line = hh.get("line") or ""
        try:
            gl = int(line)
        except (TypeError, ValueError):
            gl = 0
        H, D, A = had["p"]
        hH, hD, hA = hh["p"]
        if gl == -1:
            ps.append(
                f"让球 -1 与不让球对照：不让球主胜 {pct(H)} 应与「让球主胜（赢 2 球及以上）"
                f"{pct(hH)} + 让球平（正好赢 1 球）{pct(hD)}」大致相等，实测差 "
                f"{f(H - (hH + hD), 1)}pp。"
                + ("两边对得上，定价内部自洽。" if abs(H - (hH + hD)) <= 2.5 else
                   "差得偏大，说明两套盘不是同一时间报的，或者定价本身有缝。")
            )
            ps.append(
                f"反过来看客队：不让球的「客胜 + 平」{pct(A + D)} 应接近让球客胜 {pct(hA)}，"
                f"实测差 {f((A + D) - hA, 1)}pp。"
            )
        elif gl == 1:
            ps.append(
                f"让球 +1 与不让球对照：让球主胜应约等于「不让球主胜 + 平」= {pct(H + D)}，"
                f"实测 {pct(hH)}，差 {f(hH - (H + D), 1)}pp。"
                + ("自洽。" if abs(hH - (H + D)) <= 2.5 else "有缝，别把两套盘当同一件事读。")
            )
        else:
            ps.append(
                f"让球盘开的是 {line or '未知'}，不是 ±1，跟不让球盘做不了直接换算；"
                f"只能读它自己的三格（主 {pct(hH)} / 平 {pct(hD)} / 客 {pct(hA)}）。"
            )
    if ttg:
        exp_goals = sum(k * p / 100.0 for k, p in enumerate(ttg["p"]))
        big = sum(ttg["p"][3:])
        ps.append(
            f"总进球盘隐含的期望总进球 {f(exp_goals, 2)}，"
            f"其中 3 球及以上合计 {pct(big)}、0–1 球合计 {pct(ttg['p'][0] + ttg['p'][1])}。"
        )
        if had:
            # 用不让球三格粗判强弱：主胜断层大时，总进球通常不会太小
            gap = had["p"][0] - had["p"][2]
            ps.append(
                f"不让球盘主客差 {f(gap, 1)}pp，"
                + ("一边倒，总进球偏低更常见（弱队摆低位、强队不必冒险）。" if abs(gap) >= 35 else
                   "两队接近，总分分布通常更散。" if abs(gap) <= 15 else
                   "有差距但不悬殊，总分居中更常见。")
            )
    return ps


def movement(mk: dict) -> list[str]:
    """位移：开盘 → 最新，几套盘各走了多少。"""
    ps: list[str] = []
    had, hh, ttg = mk.get("had"), mk.get("hhad"), mk.get("ttg")
    if had and had["n"] > 1:
        d = [had["p"][i] - had["open_p"][i] for i in range(3)]
        ps.append(
            f"胜平负 {had['open_stamp']} → {had['stamp']}（{had['n']} 次快照）："
            + " / ".join(f"{f(had['open_p'][i])}%→{f(had['p'][i])}%" for i in range(3))
            + f"，位移 " + " / ".join(f"{d[i]:+.1f}pp" for i in range(3))
            + ("，三格都没动。" if max(abs(x) for x in d) < 0.3 else "。")
        )
    elif had:
        ps.append(f"胜平负只有 1 次快照（{had['stamp']}），没有位移可看。")
    if hh:
        if hh["n"] > 1:
            d = [hh["p"][i] - hh["open_p"][i] for i in range(3)]
            line_chg = "，让球线变过：" + f"{hh['open_line']} → {hh['line']}" if hh["open_line"] != hh["line"] else ""
            ps.append(
                f"让球 {hh['open_stamp']} → {hh['stamp']}（{hh['n']} 次）："
                + " / ".join(f"{f(hh['open_p'][i])}%→{f(hh['p'][i])}%" for i in range(3))
                + f"，位移 " + " / ".join(f"{d[i]:+.1f}pp" for i in range(3)) + line_chg + "。"
            )
        else:
            ps.append(f"让球只有 1 次快照（{hh['stamp']}），线 {hh['line']} 没动过。")
    if ttg and ttg["n"] > 1:
        ch = [(k, ttg["open_odds"][k], ttg["odds"][k])
              for k in range(len(TTG_KEYS))
              if abs(ttg["open_odds"][k] - ttg["odds"][k]) > 1e-9]
        ps.append(
            "总进球 " + ("逐档调过：" + "、".join(f"{k} 球 {f(a, 2)}→{f(b, 2)}" for k, a, b in ch)
                        if ch else "各档都没动。")
        )
    return ps


def hot_cold(mk: dict) -> list[str]:
    ps: list[str] = []
    had = mk.get("had")
    if had:
        i = max(range(3), key=lambda k: had["p"][k])
        rest = sum(had["p"][k] for k in range(3) if k != i)
        ps.append(
            f"不让球盘最热是{DIRS[i]}（{pct(had['p'][i])}），另外两格合计 {pct(rest)}；"
            f"抽水 {f(100 - had['payout'], 1)} 个百分点（返还率 {f(had['payout'], 1)}%）。"
        )
    crs = mk.get("crs")
    if crs and crs["cells"]:
        k, o, p = crs["cells"][0]
        ps.append(
            f"波胆盘共 {crs['count']} 格，最低赔是 {k} "
            f"（{f(o, 2)}，去水后 {pct(p)}），说明定价把最可能的比分压在这一格上。"
        )
    hafu = mk.get("hafu")
    if hafu:
        i = max(range(len(hafu["p"])), key=lambda k: hafu["p"][k])
        ps.append(
            f"半全场最热组合是「{hafu['labels'][i]}」（{pct(hafu['p'][i])}）"
            + ("——半场就领先并保持到底，是定价认为最省事的一条路。" if hafu["labels"][i] == "胜胜" else "。")
        )
    return ps


def ttg_table(mk: dict) -> list[str]:
    ttg = mk.get("ttg")
    if not ttg:
        return []
    rows = ["| 总进球 | " + " | ".join(f"{k} 球" for k in range(8)) + " |",
            "|---|" + "---|" * 8]
    rows.append("| 去水概率 | " + " | ".join(pct(x) for x in ttg["p"]) + " |")
    rows.append("| 赔率 | " + " | ".join(f(o, 2) for o in ttg["odds"]) + " |")
    return rows


# ────────────────────────────────────────────── 情报
def intel_of(mid: str, home: str, away: str) -> dict:
    try:
        inj = pc.injuries(mid)
    except Exception:  # noqa: BLE001
        inj = []
    try:
        hf = pc.team_form(mid, home, "home")
        af = pc.team_form(mid, away, "away")
    except Exception:  # noqa: BLE001
        hf, af = {}, {}
    try:
        meet = pc.meetings(mid)
    except Exception:  # noqa: BLE001
        meet = {}
    return {"injuries": inj, "home_form": hf, "away_form": af, "meetings": meet}


def intel_md(inf: dict, home: str, away: str) -> list[str]:
    ps: list[str] = []
    inj = inf.get("injuries") or []
    # 官方缓存里同一个球员可能同时挂在主客两栏（重复登记），按名字去重
    seen, uniq = set(), []
    for p_ in inj:
        nm = (p_.get("name") or "").strip()
        if nm and nm in seen:
            continue
        seen.add(nm)
        uniq.append(p_)
    inj = uniq
    if inj:
        side = {"home": "主", "away": "客"}
        ps.append(f"**伤停 / 停赛 {len(inj)} 人**：" + "；".join(
            f"{side.get(p.get('side'), '')} {p.get('name')}（{p.get('pos')}"
            f"{'，停赛' if p.get('kind') == '停赛' else ''}，出场 {p.get('apps')} 场）"
            for p in inj[:8]) + ("…" if len(inj) > 8 else ""))
    else:
        ps.append("**伤停 / 停赛**：本期无登记（不是「无伤病」，只是数据源没给）。")
    hf, af, meet = inf.get("home_form") or {}, inf.get("away_form") or {}, inf.get("meetings") or {}
    if hf.get("n") or af.get("n"):
        ps.append(
            f"**近期**：{home} 近 {hf.get('n', 0)} 场 场进 {f(hf.get('gf_avg'), 2)} / 失 "
            f"{f(hf.get('ga_avg'), 2)}，零封率 {f(hf.get('cs_rate'), 0)}%，上半场进球占 "
            f"{f(hf.get('share_1h'), 0)}%；{away} 近 {af.get('n', 0)} 场 场进 {f(af.get('gf_avg'), 2)} / 失 "
            f"{f(af.get('ga_avg'), 2)}，零封率 {f(af.get('cs_rate'), 0)}%，上半场占 {f(af.get('share_1h'), 0)}%。"
        )
    if meet.get("n"):
        ps.append(
            f"**交锋**：{meet.get('n')} 场，场均 {f(meet.get('avg_total'), 2)} 球，"
            f"低比分（≤2 球）占 {f(meet.get('low2'), 0)}%，平局 {f(meet.get('draw'), 0)}%，"
            f"双方进球 {f(meet.get('btts'), 0)}%。"
        )
    return ps


MISSING = ("**缺源（本场不要凭印象补）**：联赛排名与战意（积分榜接口返回空壳）、"
           "xG / xGA / npxG、PPDA、定位球 xG、裁判尺度、天气与场地、轮换与欧战赛程。")


# ────────────────────────────────────────────── 汇总
def build_one(no: str, s: dict, fetch: bool, verbose: bool = True) -> dict:
    mid = str(s["matchId"])
    mk = parse_markets(mid)
    inf = intel_of(mid, s["home"], s["away"])
    rec = {
        "no": no, "matchId": mid, "league": s["league"],
        "home": s["home"], "away": s["away"], "kick": s["kick"],
        "markets": mk,
        "cross": cross_check(mk),
        "move": movement(mk),
        "hot": hot_cold(mk),
        "intel": inf,
    }
    if verbose:
        flag = "有盘口" if mk.get("available") else "无盘口数据"
        print(f"  {no}  {s['home']} vs {s['away']}  [{flag}]")
    return rec


def to_md(recs: list[dict], date_tag: str) -> str:
    out = [f"# 赛前情报单 · {date_tag[:4]}-{date_tag[4:6]}-{date_tag[6:]}", ""]
    have = sum(1 for r in recs if r["markets"].get("available"))
    out.append(f"共 {len(recs)} 场，拿到盘口 {have} 场，无盘口 {len(recs) - have} 场。"
               "写稿前先读这一份；盘口只作研判依据，公开稿不写盘口口径（R41）。")
    out.append("")
    for r in recs:
        mk = r["markets"]
        out.append(f"---")
        out.append("")
        out.append(f"## {r['no']} {r['league']} {r['home']} vs {r['away']}　{r['kick']}")
        out.append("")
        if not mk.get("available"):
            out.append("**盘口**：本场没有拿到任何盘口快照（未开售或抓取失败），"
                       "只能靠球队面数据研判，不要写「定价如何」。")
            out.append("")
        else:
            out.append("### 一、盘口快照")
            out.append("")
            had = mk.get("had")
            if not had:
                out.append("- **胜平负**：本场没有胜平负固定奖金（未开售或已封盘），"
                           "只有让球 / 总进球可读，跨盘一致性做不了。")
            if had:
                out.append(f"- **胜平负**（{had['stamp']}，共 {had['n']} 次快照，返还率 "
                           f"{f(had['payout'], 2)}%）："
                           + " / ".join(f"{f(had['odds'][i], 2)}" for i in range(3))
                           + "　→　去水 " + " / ".join(pct(had["p"][i]) for i in range(3)))
            hh = mk.get("hhad")
            if hh:
                out.append(f"- **让球 {hh['line']}**（{hh['stamp']}，共 {hh['n']} 次）："
                           + " / ".join(f"{f(hh['odds'][i], 2)}" for i in range(3))
                           + "　→　去水 " + " / ".join(pct(hh["p"][i]) for i in range(3)))
            if mk.get("ttg"):
                out.append("")
                out.extend(ttg_table(mk))
            hafu = mk.get("hafu")
            if hafu:
                top = sorted(range(len(hafu["p"])), key=lambda k: -hafu["p"][k])[:4]
                out.append("")
                out.append("- **半全场前四**：" + "；".join(
                    f"{hafu['labels'][k]} {pct(hafu['p'][k])}" for k in top))
            crs = mk.get("crs")
            if crs and crs["cells"]:
                out.append("- **波胆最小六格**：" + "；".join(
                    f"{k} {f(o, 2)}（{pct(p)}）"
                    for k, o, p in crs["cells"][:6]))
            out.append("")
            if r["move"]:
                out.append("### 二、位移")
                out.append("")
                out.extend(f"- {x}" for x in r["move"])
                out.append("")
            if r["cross"] or r["hot"]:
                out.append("### 三、跨盘一致性与冷热")
                out.append("")
                out.extend(f"- {x}" for x in (r["cross"] + r["hot"]))
                out.append("")
        out.append("### 四、球队情报")
        out.append("")
        out.extend(f"- {x}" for x in intel_md(r["intel"], r["home"], r["away"]))
        out.append(f"- {MISSING}")
        out.append("")
        out.append("### 五、写稿前的取用纪律")
        out.append("")
        out.append("- 盘口读数只作**背后研判依据**，公开稿里换成「公开数据口径」，不写赔率/盘口这些词（R41）。")
        out.append("- 让球盘与不让球盘对不上时，两套盘不要当同一件事读，取更保守的那一侧。")
        out.append("- 位移只能说明「定价动过」，不能说明「为什么动」，不编资金流向。")
        out.append("- 缺源项一律不赋值，公开稿里直接省略，不写「待补」。")
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="赛前盘口采集 · 处理 · 情报单")
    ap.add_argument("--date", default=None, help="YYYYMMDD，缺省取 slate 里最近的 businessDate")
    ap.add_argument("--no-fetch", action="store_true", help="只用已有缓存，不联网抓")
    ap.add_argument("--ext", action="store_true", help="顺带跑一次外部预测采集")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    slate_p = STATE / "batch" / "_slate.json"
    if not slate_p.exists():
        raise SystemExit("没有 state/batch/_slate.json，先跑 python scripts/sporttery_fetch.py slate")
    sd = json.loads(slate_p.read_text(encoding="utf-8"))

    rows = []
    for b in sd.get("value", {}).get("matchInfoList", []):
        for m in (b.get("subMatchList") or []):
            rows.append(m)
    if not rows:
        raise SystemExit("slate 里没有场次")

    date_tag = a.date
    if not date_tag:
        bd = sorted({(m.get("businessDate") or "").replace("-", "") for m in rows if m.get("businessDate")})
        if not bd:
            raise SystemExit("slate 里没有 businessDate，用 --date 指定")
        date_tag = bd[-1]
    iso = f"{date_tag[:4]}-{date_tag[4:6]}-{date_tag[6:]}"

    slate: dict = {}
    for m in rows:
        if m.get("businessDate") and m["businessDate"] != iso:
            continue
        num = m.get("matchNum", 0)
        no = "周日%03d" % (num if num < 1000 else num - 7000)
        slate[no] = {
            "matchId": m.get("matchId"), "league": m.get("leagueAbbName", ""),
            "home": m.get("homeTeamAbbName", ""), "away": m.get("awayTeamAbbName", ""),
            "kick": (m.get("matchTime") or "")[:5],
        }
    if not slate:
        raise SystemExit(f"slate 里没有 businessDate={iso} 的场次")

    print(f"赛前情报 · {iso} · {len(slate)} 场")

    if not a.no_fetch:
        ids = [str(v["matchId"]) for v in slate.values()]
        cmds = [
            [sys.executable, "-X", "utf8", str(SCRIPTS / "sporttery_fetch.py"), "bonus", *ids],
            [sys.executable, "-X", "utf8", str(SCRIPTS / "sporttery_fetch.py"), "match", *ids],
        ]
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=600)
                tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
                print(f"  抓取 {Path(cmd[3]).name if len(cmd) > 3 else ''} {cmd[-1] if cmd else ''}"
                      .replace("  ", " "), "→", tail[0][:70])
            except Exception as exc:  # noqa: BLE001
                print(f"  ⚠️ 抓取失败（继续用缓存）：{exc}")
        try:
            subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "move_from_bonus.py"),
                            "--date", date_tag], cwd=str(ROOT), capture_output=True, text=True, timeout=300)
            print("  已刷新 state/records/_move_<date>.json")
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠️ 位移处理失败：{exc}")

    if a.ext:
        try:
            subprocess.run([sys.executable, "-X", "utf8", str(SCRIPTS / "ext_predict.py"), "batch"],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=900)
            print("  已跑一次外部预测采集")
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠️ 外部预测失败：{exc}")

    recs = [build_one(no, s, not a.no_fetch, verbose=not a.quiet)
            for no, s in sorted(slate.items())]

    outdir = INTEL / date_tag
    outdir.mkdir(parents=True, exist_ok=True)
    jp = outdir / f"_intel_{date_tag}.json"
    jp.write_text(json.dumps({"date": date_tag, "matches": recs}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    mp = outdir / f"_intel_{date_tag}.md"
    mp.write_text(to_md(recs, date_tag), encoding="utf-8")
    have = sum(1 for r in recs if r["markets"].get("available"))
    print(f"\n✅ {jp}\n✅ {mp}\n   盘口覆盖 {have}/{len(recs)} 场 · {mp.stat().st_size} 字节")


if __name__ == "__main__":
    main()
