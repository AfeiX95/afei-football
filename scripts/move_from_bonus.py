#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把竞彩「固定奖金」历史（getFixedBonusV1）转成赛博版变盘页吃的 _move_<日期>.json

用法：
    python scripts/move_from_bonus.py                     # 扫 state/cache/_bonus_*.json 全部转
    python scripts/move_from_bonus.py 2042024 2042035     # 只转指定场次
    python scripts/move_from_bonus.py --date 20261017     # 指定输出日期（默认取最后一条快照的日期）

数据来源：`python scripts/sporttery_fetch.py bonus <竞彩id>...`（端点 getFixedBonusV1.qry，
参数必须恰好 clientCode=3001 + matchId）。每个 pool 都是「逐次变盘」的数组：
    hadList  h/d/a            —— 胜平负
    hhadList h/d/a + goalLine —— 让球
    ttgList  s0..s7           —— 总进球
    hafuList hh/hd/ha/dh/dd/da/ah/ad/aa —— 半全场（半场×全场）
    crsList  sXXsYY           —— 波胆（只有当前一版，没有历史）

产出 `state/records/_move_<日期>.json`：spf / hand 保留完整时间轴，goals / htft 给出初盘与最新，
score_pool 给当前波胆全盘，notes 自动写三到四条读数（不编）。
"""
import argparse
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "state", "cache")
RECORDS = os.path.join(ROOT, "state", "records")

HAFU = {"hh": "胜胜", "hd": "胜平", "ha": "胜负", "dh": "平胜", "dd": "平平",
        "da": "平负", "ah": "负胜", "ad": "负平", "aa": "负负"}


def load(path):
    with io.open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def stamp(row):
    return "%s %s" % ((row.get("updateDate") or "")[5:], (row.get("updateTime") or "")[:5])


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def conv_spf(rows):
    out = []
    for r in rows or []:
        h, d, a = num(r.get("h")), num(r.get("d")), num(r.get("a"))
        if None in (h, d, a):
            continue
        out.append({"t": stamp(r), "h": h, "d": d, "a": a})
    return out


def conv_hand(rows):
    out = []
    for r in rows or []:
        h, d, a = num(r.get("h")), num(r.get("d")), num(r.get("a"))
        if None in (h, d, a):
            continue
        out.append({"t": stamp(r), "h": h, "d": d, "a": a, "line": r.get("goalLine", "")})
    return out


def conv_goals(rows):
    rows = [r for r in (rows or []) if num(r.get("s0"))]
    if not rows:
        return None
    def pack(r):
        return {str(i): num(r.get("s%d" % i)) for i in range(7)}
    return {"t_old": stamp(rows[0]), "t_new": stamp(rows[-1]), "old": pack(rows[0]), "new": pack(rows[-1])}


def conv_htft(rows):
    rows = [r for r in (rows or []) if num(r.get("aa"))]
    if not rows:
        return None
    keys = ["hh", "hd", "dh", "dd", "da", "ah", "ad", "aa"]
    def pack(r):
        return {HAFU[k]: num(r.get(k)) for k in keys if num(r.get(k))}
    return {"t_old": stamp(rows[0]), "t_new": stamp(rows[-1]), "old": pack(rows[0]), "new": pack(rows[-1])}


def conv_pool(rows):
    if not rows:
        return {}
    r = rows[0]
    out = {}
    for k, v in r.items():
        if not k.startswith("s") or not k.endswith(tuple("0123456789")):
            continue
        if "s" not in k[1:]:
            continue
        body = k[1:]
        if body.count("s") != 1:
            continue
        home, away = body.split("s")
        o = num(v)
        if o and o > 0:
            out["%d-%d" % (int(home), int(away))] = o
    return out


def notes_for(mid, spf, hand, goals, htft, pool):
    out = []
    if len(spf) >= 2:
        a0, a1 = spf[0]["a"], spf[-1]["a"]
        h0, h1 = spf[0]["h"], spf[-1]["h"]
        out.append("胜平负共 %d 次变动：开盘 %.2f/%.2f/%.2f → 最新 %.2f/%.2f/%.2f（主胜 %+.2f、客胜 %+.2f）。"
                   % (len(spf), spf[0]["h"], spf[0]["d"], spf[0]["a"], spf[-1]["h"], spf[-1]["d"], spf[-1]["a"],
                      h1 - h0, a1 - a0))
        if len(spf) >= 3:
            lo = min(spf, key=lambda r: r["a"])
            out.append("客胜最低点出现在 %s（%.2f），也就是这次变盘的情绪高点，之后往回走。"
                       % (lo["t"], lo["a"]) if lo is not spf[-1] else "")
            out = [x for x in out if x]
    if len(hand) >= 2:
        out.append("让球(%s) %d 次变动：让胜 %.2f→%.2f、让负 %.2f→%.2f。"
                   % (hand[-1].get("line", ""), len(hand), hand[0]["h"], hand[-1]["h"], hand[0]["a"], hand[-1]["a"]))
    if goals:
        g0, g1 = goals["old"], goals["new"]
        movers = [(i, g0[str(i)], g1[str(i)]) for i in range(7) if g0[str(i)] and g1[str(i)] and g0[str(i)] != g1[str(i)]]
        low = min(((i, g1[str(i)]) for i in range(7) if g1[str(i)]), key=lambda kv: kv[1])
        out.append("总进球 %s：%d 球调到最低赔 %.2f（最热一格）；1 球 %.2f→%.2f、2 球 %.2f→%.2f。"
                   % (goals["t_new"], low[0], low[1], g0["1"] or 0, g1["1"] or 0, g0["2"] or 0, g1["2"] or 0))
        if len(movers) >= 3:
            out.append("同盘 %d 格变动，说明定价在「几个球」上做过一轮重估。" % len(movers))
    if htft:
        h0, h1 = htft["old"], htft["new"]
        bits = []
        for k in ("平负", "平平", "平胜", "负负"):
            if h0.get(k) and h1.get(k):
                bits.append("%s %.2f→%.2f" % (k, h0[k], h1[k]))
        out.append("半全场 %s：%s。" % (htft["t_new"], "、".join(bits)))
    if pool:
        low = min(pool.items(), key=lambda kv: kv[1])
        out.append("波胆全盘 %d 格，最低赔是 %s（%.2f）；波胆只有当前版本，没有历史位移。" % (len(pool), low[0], low[1]))
    return [x for x in out if x]


def convert(paths, date_tag):
    matches = {}
    for p in paths:
        d = load(p)
        v = d.get("value") or {}
        oh = v.get("oddsHistory") or {}
        mid = str(oh.get("matchId") or os.path.basename(p).replace("_bonus_", "").replace(".json", ""))
        spf = conv_spf(oh.get("hadList"))
        hand = conv_hand(oh.get("hhadList"))
        goals = conv_goals(oh.get("ttgList"))
        htft = conv_htft(oh.get("hafuList"))
        pool = conv_pool(oh.get("crsList"))
        name = "%s vs %s" % (oh.get("homeTeamAbbName", "?"), oh.get("awayTeamAbbName", "?"))
        matches[mid] = {
            "name": name,
            "league": oh.get("leagueAbbName", ""),
            "auto": True,
            "spf": spf, "hand": hand, "goals": goals, "htft": htft, "score_pool": pool,
            "notes": notes_for(mid, spf, hand, goals, htft, pool),
        }
    out = {
        "_note": "自动生成：竞彩官方固定奖金历史（getFixedBonusV1，clientCode=3001+matchId）。"
                 "spf/hand 为完整时间轴，goals/htft 给初盘与最新，score_pool 只有当前盘。"
                 "手工补录的场次（无 auto 字段）优先级更高，勿覆盖。",
        "date": date_tag,
        "captured_at": max([m["spf"][-1]["t"] for m in matches.values() if m.get("spf")] or [""]),
        "source": "竞彩官方固定奖金变盘记录（webapi.sporttery.cn /gateway/uniform/football/getFixedBonusV1.qry）",
        "matches": matches,
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="竞彩 matchId；留空则扫全部 state/cache/_bonus_*.json")
    ap.add_argument("--date", default="", help="输出日期（默认取最新快照那天的 YYYYMMDD）")
    ap.add_argument("--out", default="", help="输出路径（默认 state/records/_move_<日期>.json）")
    a = ap.parse_args()

    if a.ids:
        paths = [os.path.join(CACHE, "_bonus_%s.json" % i) for i in a.ids]
        paths = [p for p in paths if os.path.exists(p)]
    else:
        paths = sorted(glob.glob(os.path.join(CACHE, "_bonus_*.json")))
    if not paths:
        print("没有找到 _bonus_*.json；先跑 python scripts/sporttery_fetch.py bonus <id>...")
        return 1

    date_tag = a.date
    if not date_tag:
        date_tag = "20261017"
    out_path = a.out or os.path.join(RECORDS, "_move_%s.json" % date_tag)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 已有文件里的手工补录场次保留
    old = {}
    if os.path.exists(out_path):
        try:
            old = (load(out_path).get("matches") or {})
        except Exception:  # noqa: BLE001
            old = {}
    data = convert(paths, date_tag)
    for mid, mv in old.items():
        if not mv.get("auto"):
            data["matches"][mid] = mv
            print("保留手工记录", mid, mv.get("name", ""))
    with io.open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("→ %s · %d 场" % (os.path.relpath(out_path, ROOT), len(data["matches"])))
    for mid, mv in data["matches"].items():
        print("  %s %-22s spf=%-2d hand=%-2d goals=%s htft=%s pool=%d"
              % (mid, mv.get("name", ""), len(mv.get("spf") or []), len(mv.get("hand") or []),
                 "有" if mv.get("goals") else "无", "有" if mv.get("htft") else "无",
                 len(mv.get("score_pool") or [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
