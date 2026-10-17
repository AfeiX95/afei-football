# -*- coding: utf-8 -*-
"""竞彩网官方 webapi 取数器（2026-10-11 打通，配方见 📚知识库/数据源/API接口.md）。

🔑 关键：webapi.sporttery.cn 直连吃 567 的根因是**缺 Referer**——
   带 Chrome UA + `Referer: https://www.sporttery.cn/jc/jsq/zqspj/`，
   并先预热 `https://www.sporttery.cn/`，则全部端点 200。不需要 playwright。

用法
----
  # 在售全盘口总览（可按竞彩编号过滤；同时落盘 state/_slate.json）
  python scripts/sporttery_fetch.py slate 周日013 周日014 周日024

  # 按日期区间批量取「足球赛果开奖」（90 分钟全场比分；结果存 state/_results_<起>_<止>.json）
  # 可选 --num 只列指定竞彩编号
  python scripts/sporttery_fetch.py results 2026-09-19 2026-09-20
  python scripts/sporttery_fetch.py results 2026-10-06 2026-10-08 --num 周二006 周三005

  # 一次拉齐某场竞彩比赛的官方全量数据 → state/_match_<id>/*.json
  python scripts/sporttery_fetch.py match 2041894 2041895

  # 拉某队近 N 场逐场（gmTeamId，不是 uniformTeamId！）
  python scripts/sporttery_fetch.py form 553 554 --term 30

  # 拉固定奖金历史（参数必须恰好 clientCode=3001&matchId=<竞彩id>）
  python scripts/sporttery_fetch.py bonus 2041894 2041895

注意
----
- `football/*` 这一族用 `?source=web&sportteryMatchId=<竞彩id>`；用 `matchId` 会返回空值。
- `getMatchHeadV1.qry` 的 `matchId` 是**另一套「比赛id」**，与竞彩 id 不同，勿混。
- `getResultHistoryV1` 默认只回 **5 场**交锋；官方特征分析页给的是 8~10 场，缺的必须去页面上抄。
- `getMatchTablesV2` 常返回空 → 积分榜仍要靠官方页面（用户粘贴）。
- 射手姓名与伤停**能取**，字段是 `personName`（`getMatchPlayerV1` / `getInjurySuspensionV1`），
  旧记把它写成 `playerName` 是字段名写错。
"""
import sys, io, os, json, time, argparse, urllib.request, urllib.error, urllib.parse, http.cookiejar

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
REF = "https://www.sporttery.cn/jc/jsq/zqspj/"
REF_SGKJ = "https://www.sporttery.cn/jc/zqsgkj/"   # 赛果开奖页（results 模式必须用这个 Referer）
HOME = "https://www.sporttery.cn/"
HOST = "https://webapi.sporttery.cn"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "state")
# state 分层（2026-10-17）：见 docs/STRUCTURE.md
OUT_MATCHES = os.path.join(OUT, "matches")
OUT_BATCH = os.path.join(OUT, "batch")
OUT_CACHE = os.path.join(OUT, "cache")

# 比赛全量：路径 → 落盘文件名（全部实测 200，2026-10-11）
MATCH_EPS = [
    ("head",    "/gateway/uniform/football/getMatchHeadV1.qry"),
    ("feature", "/gateway/uniform/football/getMatchFeatureV1.qry"),
    ("result",  "/gateway/uniform/football/getMatchResultV1.qry"),
    ("history", "/gateway/uniform/football/getResultHistoryV1.qry"),
    ("injury",  "/gateway/uniform/football/getInjurySuspensionV1.qry"),
    ("player",  "/gateway/uniform/football/getMatchPlayerV1.qry"),
    ("future",  "/gateway/uniform/football/getFutureMatchesV1.qry"),
    ("tables",  "/gateway/uniform/football/getMatchTablesV2.qry"),
    ("score",   "/gateway/uniform/fb/getMatchScoreV1.qry"),
    ("event",   "/gateway/uniform/fb/getMatchEventV1.qry"),
]

_cj = http.cookiejar.CookieJar()
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))


def raw(url, referer=REF, cap=12_000_000, timeout=40):
    """返回 (status, bytes)。HTTPError 不抛，直接回状态码。"""
    rq = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer,
                                             "Accept": "application/json"})
    try:
        with _op.open(rq, timeout=timeout) as r:
            return r.status, r.read(cap)
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return "ERR", ("%s" % e).encode()


def warmup():
    """预热站点，拿 cookie。必须调用，否则 webapi 吃 567。"""
    raw(HOME, HOME)


def get(path, params, outfile=None, referer=REF):
    st, b = raw(HOST + path + "?" + urllib.parse.urlencode(params), referer)
    if outfile and st == 200 and len(b) > 100:
        with open(outfile, "wb") as f:
            f.write(b)
    return st, b


def summarize(b):
    try:
        v = json.loads(b.decode("utf-8")).get("value")
        if v is None:
            return "value=null"
        return "value=%dB%s" % (len(json.dumps(v, ensure_ascii=False)),
                                "  (空 {})" if v == {} else "")
    except Exception:
        return "非 JSON"


def cmd_match(ids, term=10):
    for mid in ids:
        d = os.path.join(OUT_MATCHES, str(mid))
        os.makedirs(d, exist_ok=True)
        print("=" * 70)
        print("MATCH", mid, "→", os.path.relpath(d, ROOT))
        for tag, path in MATCH_EPS:
            st, b = get(path, {"source": "web", "sportteryMatchId": mid},
                        os.path.join(d, tag + ".json"))
            print("  %-8s %-5s raw=%-9s %s" % (tag, st, len(b), summarize(b)))
            time.sleep(0.25)


def cmd_form(team_ids, term=10):
    """球队近 N 场逐场。⚠️ gmTeamId；teamMatchResult 字段不是主客标志。"""
    for tid in team_ids:
        st, b = get("/gateway/uniform/football/team/getMatchResultV1.qry",
                    {"gmTeamId": tid, "termLimits": term},
                    os.path.join(OUT_CACHE, "_form%d_%s.json" % (term, tid)))
        print("  team %-9s %-5s raw=%-9s %s" % (tid, st, len(b), summarize(b)))
        time.sleep(0.25)


def cmd_bonus(ids):
    """固定奖金历史。参数必须**恰好** clientCode=3001 + matchId，多给即 567/20013。"""
    for mid in ids:
        st, b = get("/gateway/uniform/football/getFixedBonusV1.qry",
                    {"clientCode": "3001", "matchId": mid},
                    os.path.join(OUT, "_bonus_%s.json" % mid))
        print("  bonus %-9s %-5s raw=%-9s %s" % (mid, st, len(b), summarize(b)))
        time.sleep(0.25)


def cmd_slate(nums=None, dump=True):
    """在售全盘口；nums 给竞彩编号（如 周日013）则只列这些场。"""
    st, b = get("/gateway/uniform/football/getMatchCalculatorV1.qry", {"channel": "c"},
                os.path.join(OUT_BATCH, "_slate.json") if dump else None)
    print("calculator %s raw=%d" % (st, len(b)))
    if st != 200:
        return
    val = json.loads(b.decode("utf-8")).get("value") or {}
    rows = []
    for mi in val.get("matchInfoList", []):
        for m in mi.get("subMatchList", []) or []:
            rows.append(m)
    if nums:
        want = set(nums)
        rows = [m for m in rows if str(m.get("matchNumStr", "")).strip() in want]
    print("命中 %d 场" % len(rows))
    for m in rows:
        had = m.get("had") or {}
        hh = m.get("hhad") or {}
        print("-" * 78)
        print("%s  %s %s  id=%s  [%s]" % (
            m.get("matchNumStr"), m.get("matchDate"), m.get("matchTime"),
            m.get("matchId"), m.get("matchStatus")))
        print("  %s %s  vs  %s %s   %s" % (
            m.get("homeTeamAbbName"), "(%s)" % m.get("homeRank", ""),
            m.get("awayTeamAbbName"), "(%s)" % m.get("awayRank", ""),
            m.get("leagueAbbName", "")))
        print("  队id home=%s away=%s | 单场id=%s" % (
            m.get("homeTeamId"), m.get("awayTeamId"), m.get("matchId")))
        print("  胜平负 %s / %s / %s      让球(%s) %s / %s / %s" % (
            had.get("h"), had.get("d"), had.get("a"),
            hh.get("goalLine"), hh.get("h"), hh.get("d"), hh.get("a")))
        crs = m.get("crs") or {}
        ttg = m.get("ttg") or {}
        if crs:
            print("  比分 " + "  ".join(
                "%s:%s=%s" % (k[1:3], k[4:6], v) for k, v in sorted(crs.items())
                if v not in (None, "", "0")))
        if ttg:
            print("  总进球 " + "  ".join("%s" % (ttg.get("s%d" % i), )
                                        for i in range(0, 8)))
    print("=" * 78)
    print("提示：本场全量官方数据再跑  python scripts/sporttery_fetch.py match <matchId>")


def cmd_results(begin, end=None, nums=None):
    """批量取「足球赛果开奖」（90 分钟全场比分），按日期区间。

    端点 getUniformMatchResultV1.qry，来自 /jc/zqsgkj/ 的 jc_sgkj_gz.js。
    ⚠️ 8 个必填参缺任一 → errorCode=P0001；日期必须 YYYY-MM-DD；
       Referer 必须是 zqsgkj 页；务必先 warmup()。
    """
    end = end or begin
    params = {"matchBeginDate": begin, "matchEndDate": end, "leagueId": "",
              "pageSize": 100, "pageNo": 1, "isFix": 0, "matchPage": 1, "pcOrWap": 1}
    out = os.path.join(OUT_CACHE, "_results_%s_%s.json" % (begin, end))
    st, b = get("/gateway/uniform/football/getUniformMatchResultV1.qry",
                params, out, referer=REF_SGKJ)
    if st != 200:
        print("  HTTP %s 取数失败" % st)
        return
    js = json.loads(b.decode("utf-8"))
    # 坑：errorCode 有时是字符串 "0"、有时是整数 0，一律按字符串比
    if str(js.get("errorCode", "0")) != "0":
        print("  errorCode=%s %s" % (js.get("errorCode"), js.get("errorMessage")))
        return
    val = js.get("value") or {}
    rows = val.get("matchResult") or []
    print("  %s ~ %s  raw=%dB  total=%s  lastUpdate=%s\n  → %s" % (
        begin, end, len(b), val.get("total"), val.get("lastUpdateTime"),
        os.path.relpath(out, ROOT)))
    if nums:
        want = set(nums)
        rows = [m for m in rows if str(m.get("matchNumStr", "")).strip() in want]
    print("  列出 %d 行%s" % (len(rows), "（已按编号过滤）" if nums else ""))
    for m in rows:
        st_txt = "待开奖" if str(m.get("matchResultStatus")) == "1" else "已完成"
        print("  %-8s %-10s %-6s %s(%s) vs %s   半 %-4s 全 %-4s [%s]" % (
            m.get("matchNumStr", ""), m.get("matchDate", ""), m.get("leagueNameAbbr", ""),
            m.get("homeTeam", ""), m.get("goalLine", ""), m.get("awayTeam", ""),
            m.get("sectionsNo1") or "-", m.get("sectionsNo999") or "-", st_txt))
    print("=" * 78)
    print("提示：口径只认 sectionsNo999（90 分钟）；编号跨批次会重排，认比赛只认队名。")


def main():
    ap = argparse.ArgumentParser(description="竞彩网官方 webapi 取数器")
    ap.add_argument("mode", choices=["slate", "match", "form", "bonus", "results"])
    ap.add_argument("ids", nargs="*",
                    help="match/bonus=竞彩id；form=gmTeamId；slate=竞彩编号(可选)；results=起始日期 [结束日期]")
    ap.add_argument("--term", type=int, default=10, help="form 模式的 termLimits（默认 10）")
    ap.add_argument("--num", nargs="*", default=None, help="results 模式：只列这些竞彩编号（如 周二006）")
    a = ap.parse_args()
    warmup()
    if a.mode == "slate":
        cmd_slate(a.ids or None)
    elif a.mode == "match":
        cmd_match(a.ids)
    elif a.mode == "form":
        cmd_form(a.ids, a.term)
    elif a.mode == "results":
        if not a.ids:
            ap.error("results 模式需要日期，如 results 2026-10-06 2026-10-08")
        cmd_results(a.ids[0], a.ids[1] if len(a.ids) > 1 else None, a.num)
    else:
        cmd_bonus(a.ids)
    print("DONE")


if __name__ == "__main__":
    main()
