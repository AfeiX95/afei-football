# -*- coding: utf-8 -*-
"""把 state/tmp/_sun_autofill.txt + injury 计数 + 比赛时间/让球 拼成 MATCHES 片段。"""
import sys, io, os, json, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "state")


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


slate = {}
for g in jload(os.path.join(S, "batch", "_slate.json"))["value"]["matchInfoList"]:
    for m in g.get("subMatchList", []) or []:
        slate[str(m.get("matchId"))] = m

txt = open(os.path.join(S, "tmp", "_sun_autofill.txt"), encoding="utf-8").read()
blocks = re.findall(r'\n    ("周日\d+": \{.*?\n    \},)', txt, re.S)
out = []
for b in blocks:
    no = re.search(r'"(周日\d+)"', b).group(1)
    line = b
    # 找 matchId
    mid = None
    for k, m in slate.items():
        if m.get("matchNumStr") == no:
            mid = k
            break
    inj = (jload(os.path.join(S, "matches", mid, "injury.json")).get("value") or {})
    ih = len((inj.get("home") or {}).get("injuriesAndSuspensionsList") or [])
    ia = len((inj.get("away") or {}).get("injuriesAndSuspensionsList") or [])
    m = slate[mid]
    hh = m.get("hhad") or {}
    hline = hh.get("goalLine", "")
    mt = m.get("matchTime", "")
    line = line.replace('"inj_home": 0, "inj_away": 0,', '"inj_home": %d, "inj_away": %d,' % (ih, ia))
    line = line.replace('"home_szn": (0, 0, 0), "away_szn": (0, 0, 0),', '"home_szn": (0, 0, 0), "away_szn": (0, 0, 0),')
    # 备注里补让球与开赛时间
    line = re.sub(r'(vs [^ ]+)(  \d\d:\d\d:\d\d)', r'\1  2026-10-18 \2 让球 %s' % hline, line, count=1)
    out.append((no, mid, line))
    print(no, mid, 'inj', ih, ia, 'line', hline, 'time', mt)
open(os.path.join(S, "tmp", "_sun_matches.txt"), "w", encoding="utf-8").write("\n".join(x[2] for x in out))
print("wrote", len(out))
