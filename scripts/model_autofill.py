# -*- coding: utf-8 -*-
"""按日期自动生成外挂场次表 state/batch/_matches_<日期>.json

model.py 会把它并入 MATCHES（见 `_load_auto_matches()`），所以每天不用再手改
那份 600 行的手写 dict。

口径
- 主客分离（home_home / away_away）= 本赛季**同立场**场次：取 result.json 里
  home.matchList / away.matchList，再按「这条记录里本队是不是主队」过滤；
- 近 5 场（note 里的逐场）= 全赛事（含杯赛/洲际赛），逐场标出赛事名；
- feature.json 给近 10 场均进/均失与同主客战绩；history.json 给交锋（官方只回 5 场）；
- 伤停人数取 injury.json（同一球员主客重复登记的按名字去重）。

用法
    python -X utf8 scripts/model_autofill.py --date 20261019
    python -X utf8 scripts/model_autofill.py --date 20261019 --dry   # 只打印不写盘
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
MATCHES = os.path.join(STATE, "matches")
BATCH = os.path.join(STATE, "batch")


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def score(s):
    try:
        a, b = str(s or "0:0").replace("：", ":").split(":")
        return int(a), int(b)
    except Exception:  # noqa: BLE001
        return 0, 0


def side_block(mid, side):
    v = (jload(os.path.join(MATCHES, mid, "result.json")) or {}).get("value") or {}
    blk = v.get(side) or {}
    return blk.get("matchList") or [], blk.get("otherMatchList") or []


def brief(r, me):
    a, b = score(r.get("fullCourtGoal"))
    is_home = str(r.get("homeTeamShortName")) == me
    my, op = (a, b) if is_home else (b, a)
    opp = r.get("awayTeamShortName") if is_home else r.get("homeTeamShortName")
    lm = r.get("tournamentShortName") or ""
    return ("%s%s %d比%d%s %s" % (r.get("matchDate", "")[5:], "主" if is_home else "客",
                                  my, op, opp, lm)), my, op, is_home


def inj_counts(mid):
    """伤停人数（去重：官方缓存会把同一球员同时挂在主客两栏）。"""
    p = os.path.join(MATCHES, mid, "injury.json")
    if not os.path.exists(p):
        return 0, 0, []
    v = (jload(p) or {}).get("value") or {}
    seen, names = set(), []
    n = {"home": 0, "away": 0}
    for side in ("home", "away"):
        for it in ((v.get(side) or {}).get("injuriesAndSuspensionsList") or []):
            nm = (it.get("personName") or "").strip()
            if nm and nm in seen:
                continue
            if nm:
                seen.add(nm)
                names.append("%s%s" % ("主" if side == "home" else "客", nm))
            n[side] += 1
    return n["home"], n["away"], names


def summarize(mid, home, away):
    fe = (jload(os.path.join(MATCHES, mid, "feature.json")) or {}).get("value") or {}
    hi = (jload(os.path.join(MATCHES, mid, "history.json")) or {}).get("value") or {}
    ga = fe.get("goalAvg") or {}
    lg = fe.get("lossGoalAvg") or {}
    eh = fe.get("eachHomeAway") or {}
    parts = []
    seps = {}
    for side, me, label, key in (("home", home, "主队", "主场"), ("away", away, "客队", "客场")):
        ml, oth = side_block(mid, side)
        sel = []
        for r in ml:
            t, my, op, is_home = brief(r, me)
            if (is_home and side == "home") or ((not is_home) and side == "away"):
                sel.append((t, my, op))
        g = sum(x[1] for x in sel)
        a = sum(x[2] for x in sel)
        seps[side] = [len(sel), g, a]
        f5 = []
        wc = {"胜": 0, "平": 0, "负": 0}
        for r in ml[:5]:
            t, my, op, _ = brief(r, me)
            w = "胜" if my > op else ("平" if my == op else "负")
            wc[w] += 1
            f5.append(t + " " + w)
        parts.append("%s%s %d 场 进 %d 失 %d%s；近5场 %d胜%d平%d负（%s）；其它赛事 %d 场%s"
                     % (label, key, len(sel), g, a,
                        ("｜" + "、".join(x[0] for x in sel)) if sel else "",
                        wc["胜"], wc["平"], wc["负"], "、".join(f5),
                        len(oth), ("（" + "、".join(brief(r, me)[0] for r in oth[:4]) + "）") if oth else ""))
    st = hi.get("statistics") or {}
    ml = hi.get("matchList") or []
    h2h = "、".join("%s %s（%s主）" % (r.get("matchDate", ""), r.get("fullCourtGoal"),
                                      r.get("homeTeamShortName")) for r in ml[:5]) or "无"
    note = ("近10场均进失 主%s/%s 客%s/%s；同主客10场 主%d胜%d平%d负 / 客%d胜%d平%d负；"
            % (ga.get("homeGoalAvgCnt"), lg.get("homeLossGoalAvgCnt"),
               ga.get("awayGoalAvgCnt"), lg.get("awayLossGoalAvgCnt"),
               eh.get("homeWinGoalMatchCnt", 0), eh.get("homeDrawMatchCnt", 0),
               eh.get("homeLossGoalMatchCnt", 0), eh.get("awayWinGoalMatchCnt", 0),
               eh.get("awayDrawMatchCnt", 0), eh.get("awayLossGoalMatchCnt", 0))
            + "；".join(parts)
            + "；交锋%s场 %s胜%s平%s负：%s"
            % (st.get("totalLegCnt"), st.get("winGoalMatchCnt"), st.get("drawMatchCnt"),
               st.get("lossGoalMatchCnt"), h2h))
    return seps, note


def no_of(num: int) -> str:
    """matchNum → 竞彩编号：周一=1xxx…周日=7xxx，取后三位。"""
    return "%03d" % (num if num < 1000 else num % 1000)


def main() -> None:
    ap = argparse.ArgumentParser(description="按日期生成外挂场次表")
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--dry", action="store_true", help="只打印，不写盘")
    a = ap.parse_args()
    iso = "%s-%s-%s" % (a.date[:4], a.date[4:6], a.date[6:])
    d = jload(os.path.join(BATCH, "_slate.json"))["value"]

    out, missing, n = {}, [], 0
    for g in d.get("matchInfoList", []):
        if g.get("businessDate") not in (iso, None):
            continue
        for m in g.get("subMatchList", []):
            if m.get("businessDate") != iso:
                continue
            mid = str(m.get("matchId"))
            num = m.get("matchNum") or 0
            no = "周%s%s" % ("一二三四五六日"[min(max((num // 1000) - 1, 0), 6)], no_of(num))
            if not os.path.exists(os.path.join(MATCHES, mid, "result.json")):
                missing.append("%s %s" % (no, mid))
                continue
            seps, note = summarize(mid, m.get("homeTeamAbbName"), m.get("awayTeamAbbName"))
            ih, ia, names = inj_counts(mid)
            if names:
                note += "；伤停 主%d人/客%d人（%s）" % (ih, ia, "、".join(names[:8]))
            else:
                note += "；伤停 主0人/客0人"
            gl = (m.get("hhad") or {}).get("goalLine")
            if gl:
                note += "；让球 %s" % gl
            out[mid] = {
                "no": no, "league": m.get("leagueAbbName"),
                "home": m.get("homeTeamAbbName"), "away": m.get("awayTeamAbbName"),
                "home_home": tuple(seps["home"]), "away_away": tuple(seps["away"]),
                "home_szn": (0, 0, 0), "away_szn": (0, 0, 0),
                "inj_home": ih, "inj_away": ia,
                "note": note.replace("\n", " "),
            }
            n += 1

    if missing:
        print("⚠️ 缺缓存 %d 场（先跑 sporttery_fetch.py match <id>）：%s" % (len(missing), "、".join(missing)))
    if not out:
        raise SystemExit("没有可用场次")
    p = os.path.join(BATCH, "_matches_%s.json" % a.date)
    if a.dry:
        print(json.dumps(out, ensure_ascii=False, indent=1)[:1500])
    else:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print("✅ %s  %d 场" % (p, n))
    for k, v in out.items():
        print("  %s %s %s vs %s  主%s 客%s" % (v["no"], v["league"], v["home"], v["away"],
                                              v["home_home"], v["away_away"]))


if __name__ == "__main__":
    main()
