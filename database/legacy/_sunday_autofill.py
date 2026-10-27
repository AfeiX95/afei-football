# -*- coding: utf-8 -*-
"""周日 2026-10-18 全盘 25 场：从本地竞彩缓存汇总 MATCHES 字段（草稿，联网零次）。

口径
- 主客分离 = 本赛季同立场场次（result.json 的 home.matchList / away.matchList，已剔除其它赛事）；
- 近 5 场 = 全赛事（含杯赛/亚冠），会在 note 里逐场标出；
- feature.json 给近 10 场均进/均失；history.json 给交锋（官方只回 5 场）。
输出：state/tmp/_sun_autofill.txt（可直接贴进 scripts/model.py 的 MATCHES）
"""
import sys, io, os, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def score(s):
    try:
        a, b = str(s or "0:0").replace("：", ":").split(":")
        return int(a), int(b)
    except Exception:
        return 0, 0


def side_block(mid, side):
    v = (jload(os.path.join(STATE, "matches", mid, "result.json")) or {}).get("value") or {}
    blk = v.get(side) or {}
    return blk.get("matchList") or [], blk.get("otherMatchList") or []


def brief(r, me):
    a, b = score(r.get("fullCourtGoal"))
    is_home = str(r.get("homeTeamShortName")) == me
    my, op = (a, b) if is_home else (b, a)
    opp = r.get("awayTeamShortName") if is_home else r.get("homeTeamShortName")
    lm = r.get("tournamentShortName") or ""
    return ("%s%s %d比%d%s %s" % (r.get("matchDate", "")[5:], "主" if is_home else "客", my, op, opp, lm)), my, op, is_home


def summarize(mid, no, league, home, away):
    fe = (jload(os.path.join(STATE, "matches", mid, "feature.json")) or {}).get("value") or {}
    hi = (jload(os.path.join(STATE, "matches", mid, "history.json")) or {}).get("value") or {}
    ga = fe.get("goalAvg") or {}
    lg = fe.get("lossGoalAvg") or {}
    eh = fe.get("eachHomeAway") or {}
    parts = []

    seps = {}
    for side, me, label, key in (("home", home, "主队", "主场"), ("away", away, "客队", "客场")):
        ml, oth = side_block(mid, side)
        sel = []
        for r in ml:               # 同立场
            t, my, op, is_home = brief(r, me)
            if (is_home and side == "home") or ((not is_home) and side == "away"):
                sel.append((t, my, op))
        g = sum(x[1] for x in sel)
        a = sum(x[2] for x in sel)
        seps[side] = (len(sel), g, a)
        f5 = []
        for r in ml[:5]:
            t, my, op, is_home = brief(r, me)
            w = "胜" if my > op else ("平" if my == op else "负")
            f5.append((t + " " + w))
        wc = {"胜": 0, "平": 0, "负": 0}
        for r in ml[:5]:
            t, my, op, is_home = brief(r, me)
            wc["胜" if my > op else ("平" if my == op else "负")] += 1
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
               eh.get("homeWinGoalMatchCnt", 0), eh.get("homeDrawMatchCnt", 0), eh.get("homeLossGoalMatchCnt", 0),
               eh.get("awayWinGoalMatchCnt", 0), eh.get("awayDrawMatchCnt", 0), eh.get("awayLossGoalMatchCnt", 0))
            + "；".join(parts)
            + "；交锋%s场 %s胜%s平%s负：%s"
            % (st.get("totalLegCnt"), st.get("winGoalMatchCnt"), st.get("drawMatchCnt"),
               st.get("lossGoalMatchCnt"), h2h))
    return seps, note


def main():
    d = jload(os.path.join(STATE, "batch", "_slate.json"))["value"]
    out = []
    for g in d.get("matchInfoList", []):
        if g.get("businessDate") != "2026-10-18":
            continue
        for m in g.get("subMatchList", []):
            mid = str(m.get("matchId"))
            no = m.get("matchNumStr")
            if not os.path.exists(os.path.join(STATE, "matches", mid, "result.json")):
                out.append('    # !! %s %s 缺缓存' % (no, mid))
                continue
            s, note = summarize(mid, no, m.get("leagueAbbName"), m.get("homeTeamAbbName"), m.get("awayTeamAbbName"))
            out.append('    "%s": {  # %s %s vs %s  %s'
                       % (no, no, m.get("homeTeamAbbName"), m.get("awayTeamAbbName"), m.get("matchTime")))
            out.append('        "no": "%s", "league": "%s",' % (no, m.get("leagueAbbName")))
            out.append('        "home": "%s", "away": "%s",' % (m.get("homeTeamAbbName"), m.get("awayTeamAbbName")))
            out.append('        "home_home": %s, "away_away": %s,' % (s["home"], s["away"]))
            out.append('        "home_szn": (0, 0, 0), "away_szn": (0, 0, 0),')
            out.append('        "inj_home": 0, "inj_away": 0,')
            out.append('        "note": "%s",' % note.replace('"', "'").replace("\n", " "))
            out.append('    },')
    txt = "\n".join(out)
    p = os.path.join(STATE, "tmp", "_sun_autofill.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write(txt)
    print("done →", p, len(txt), "chars")


if __name__ == "__main__":
    main()
