# -*- coding: utf-8 -*-
# 解析竞彩网API今日场次：编号/联赛/主客队/开赛时间/销售状态
import json, sys, datetime

path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\wuyan\AppData\Local\Temp\jc_0824.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

value = data.get("value", {})
print("errorCode:", data.get("errorCode"), "| emptyFlag:", data.get("emptyFlag"))
print("businessDate:", value.get("businessDate"), "| matchCount:", value.get("matchCount"))
print("=" * 90)

matches = value.get("matchInfoList", [])
if not matches:
    # 兼容旧结构：subMatchList
    for sale in value.get("matchResult", []) or []:
        for m in sale.get("subMatchList", []):
            matches.append(m)

print("总场次数:", len(matches))
print("=" * 90)

# 字段探测：取第一场看有哪些字段
if matches:
    print("字段样例:", sorted(matches[0].keys())[:40])
    print("=" * 90)

for m in matches:
    num = m.get("matchNumStr") or m.get("matchNum") or m.get("matchId") or "?"
    league = m.get("leagueAllName") or m.get("leagueName") or m.get("leagueAbbName") or "?"
    home = m.get("homeTeamAllName") or m.get("homeTeamName") or m.get("homeTeamAbbName") or "?"
    away = m.get("awayTeamAllName") or m.get("awayTeamName") or m.get("awayTeamAbbName") or "?"
    mdate = m.get("matchDate", "")
    mtime = m.get("matchTime", "")
    status = m.get("matchStatus", "")
    single = m.get("single", "")
    # 简化时间：如果是纯时间格式，拼上matchDate
    t = mtime if len(mtime) > 8 else (mdate + " " + mtime).strip()
    print(f"{num} | {league} | {home} vs {away} | {t} | status={status} | single={single}")
