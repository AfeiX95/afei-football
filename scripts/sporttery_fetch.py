# -*- coding: utf-8 -*-
"""竞彩网官方 webapi 取数器（2026-10-11 打通，配方见 📚知识库/数据源/API接口.md）。

🔑 关键：webapi.sporttery.cn 直连吃 567 的根因是**缺 Referer**——
   带 Chrome UA + `Referer: https://www.sporttery.cn/jc/jsq/zqspj/`，
   并先预热 `https://www.sporttery.cn/`，则全部端点 200。不需要 playwright。

用法
----
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
- `getMatchTablesV2` 常返回空、`getMatchPlayerV1` 的 `playerName` 全为 null
  → 积分榜与射手姓名仍要靠官方页面（用户粘贴）。
"""
import sys, io, os, json, time, argparse, urllib.request, urllib.error, urllib.parse, http.cookiejar

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
REF = "https://www.sporttery.cn/jc/jsq/zqspj/"
HOME = "https://www.sporttery.cn/"
HOST = "https://webapi.sporttery.cn"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "state")

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


def get(path, params, outfile=None):
    st, b = raw(HOST + path + "?" + urllib.parse.urlencode(params))
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
        d = os.path.join(OUT, "_match_%s" % mid)
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
                    os.path.join(OUT, "_form%d_%s.json" % (term, tid)))
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


def main():
    ap = argparse.ArgumentParser(description="竞彩网官方 webapi 取数器")
    ap.add_argument("mode", choices=["match", "form", "bonus"])
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--term", type=int, default=10, help="form 模式的 termLimits（默认 10）")
    a = ap.parse_args()
    warmup()
    if a.mode == "match":
        cmd_match(a.ids)
    elif a.mode == "form":
        cmd_form(a.ids, a.term)
    else:
        cmd_bonus(a.ids)
    print("DONE")


if __name__ == "__main__":
    main()
