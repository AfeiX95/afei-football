# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
data = json.load(open(r"I:\阿飞说球\temp_jc_20260805.json", encoding="utf-8"))
val = data.get("value", {})
print("期次 | 开球时间 | 赛事 | 对阵 | 胜/平/负 | 隐含H/D/A | 让球线")
for day in val.get("matchInfoList", []):
    for sub in day.get("subMatchList", []):
        had = sub.get("had", {})
        hhad = sub.get("hhad", {})
        h, d, a = float(had["h"]), float(had["d"]), float(had["a"])
        t = 1/h + 1/d + 1/a
        ph, pd, pa = (1/h)/t*100, (1/d)/t*100, (1/a)/t*100
        gl = hhad.get("goalLine", "")
        print(f"{sub.get('matchNumStr')} | {sub.get('matchDate')[5:]} {sub.get('matchTime')} | {sub.get('leagueAbbName')} | {sub.get('homeTeamAbbName')} vs {sub.get('awayTeamAbbName')} | {h}/{d}/{a} | {ph:.1f}/{pd:.1f}/{pa:.1f} | 让{gl} {hhad.get('h')}/{hhad.get('d')}/{hhad.get('a')}")
        ttg = sub.get("ttg", {})
        print(f"   总进球: " + " ".join(f"{k}={v}" for k,v in ttg.items() if v))
