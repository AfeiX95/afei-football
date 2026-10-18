#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""联赛排名与外部指标（R48 的 A 级补充，2026-10-19 起）

补的是缺源声明里最要紧的那一项：**联赛排名 + 场次 + 胜平负 + 进失球 + 积分**。
数据源＝中文维基百科赛季页里的积分榜表格（`variant=zh-cn` 输出简体，队名与竞彩
简称可直接对齐），比赛日天气走 open-meteo（零成本，需先在
`database/config/stadiums.json` 配城市）。

用法：
    python -X utf8 scripts/league_intel.py --date 20261019
    python -X utf8 scripts/league_intel.py --date 20261019 --no-net   # 只用缓存
    python -X utf8 scripts/league_intel.py --date 20261019 --md       # 同时出人读版

产出：
    state/intel/<日期>/_leagues_<日期>.json   机器读
    state/intel/<日期>/_leagues_<日期>.md     人读（--md）

纪律：
- 拿不到就写进 missing，**不猜、不估、不拿别的联赛顶替**。
- 维基是赛季累计表，赛中/赛后可能滞后一轮，只会更新到「已完赛场次」，不当实时用。
- 天气只在对阵主队已配置城市时才给，未配置一律留空。
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
CONFIG = ROOT / "database" / "config"
CACHE = STATE / "cache" / "_leagues"
UA = {"User-Agent": "afei-intel/1.0 (local research; contact: local)"}
TTL = 12 * 3600

ZH_API = "https://zh.wikipedia.org/w/api.php"
EN_API = "https://en.wikipedia.org/w/api.php"
GEO_API = "https://geocoding-api.open-meteo.com/v1/search"
METEO_API = "https://api.open-meteo.com/v1/forecast"


# ── 小工具 ──────────────────────────────────────────────────────────────
def jload(p: Path, default=None):
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def jdump(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def http_json(url: str, timeout: int = 45, retry: int = 3, params: dict | None = None):
    """requests 取 JSON。用 requests 是因为 urllib 在维基这种大 HTML 上有
    IncompleteRead（chunked 截断），换了之后没再复现。"""
    import requests  # 局部导入，脚本其余部分不依赖

    last = None
    for i in range(retry):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.2 * (i + 1))
    raise last


def strip_tags(s: str) -> str:
    s = re.sub(r"<style.*?</style>", "", s, flags=re.S | re.I)
    s = re.sub(r"<script.*?</script>", "", s, flags=re.S | re.I)
    s = re.sub(r"<sup.*?</sup>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    for a, b in (("&amp;", "&"), ("&nbsp;", " "), ("&#160;", " "),
                 ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def norm_team(s: str) -> str:
    """队名归一：去注释、去俱乐部后缀、去标点空格。"""
    s = re.sub(r"[（(].*?[)）]", "", s)
    s = strip_tags(s)
    for junk in ("足球俱乐部", "足球俱樂部", "俱乐部", "俱樂部", "足球会", "足球會",
                 "一队", "一隊", "B队", "足球隊", "足球队", "队", "隊",
                 "FC", "F.C.", "CF", "SC", "AFC"):
        s = s.replace(junk, "")
    return re.sub(r"[\s\-·、,，.。'’]", "", s).lower()


T2S = {
    "義": "意", "國": "国", "級": "级", "聯": "联", "賽": "赛", "職": "职", "業": "业",
    "韓": "韩", "蘭": "兰", "爾": "尔", "歐": "欧", "軍": "军", "隊": "队", "場": "场",
    "體": "体", "會": "会", "開": "开", "與": "与", "個": "个", "點": "点", "進": "进",
    "勝": "胜", "負": "负", "積": "积", "總": "总", "數": "数", "預": "预", "準": "准",
    "維": "维", "亞": "亚", "羅": "罗", "馬": "马",
}


def simp(s: str) -> str:
    return "".join(T2S.get(ch, ch) for ch in s)


def season_tags(date_tag: str) -> dict:
    y = int(date_tag[:4])
    m = int(date_tag[4:6])
    start = y if m >= 7 else y - 1
    return {"split": f"{start}年至{start + 1}年", "calendar": f"{y}年", "y": y,
            "en_split": f"{start}–{str(start + 1)[2:]}", "en_cal": f"{y}"}


def zh_candidates(prefix: str, zh_name: str) -> list[str]:
    """赛季页标题候选。维基标题常是「简体国名 + 繁体级别」混写
    （实测 2026年至2027年意大利足球甲級聯賽），写死一种必挂，全试一遍。"""
    out = [prefix + zh_name]
    if "足球" in zh_name:
        c, tier = zh_name.split("足球", 1)
        out.append(prefix + simp(c) + "足球" + tier)
        out.append(prefix + simp(c) + "足球" + simp(tier))
    out.append(prefix + simp(zh_name))
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def page_exists(title: str, api: str = ZH_API) -> bool:
    d = http_json(api, params={"action": "query", "titles": title, "format": "json",
                               "formatversion": "2", "redirects": "1"}, timeout=30)
    pages = (d.get("query") or {}).get("pages") or [{}]
    return not pages[0].get("missing", False)


def resolve_page(zh_name: str, kind: str, tags: dict, no_net: bool) -> tuple[str | None, str]:
    """联赛中文名 → 赛季页标题。先按候选逐个探测（确定性），探测不到才退回搜索。"""
    cache_p = CACHE / "_pages.json"
    cache = jload(cache_p, {}) or {}
    prefix = tags["calendar"] if kind == "calendar" else tags["split"]
    key = f"{kind}|{zh_name}|{prefix}"
    if key in cache:
        return cache[key].get("title"), cache[key].get("why", "cache")
    if no_net:
        return None, "no-net 且无缓存"

    cands = zh_candidates(prefix, zh_name)
    for c in cands:
        try:
            if page_exists(c):
                cache[key] = {"title": c, "why": f"候选命中 {c}"}
                jdump(cache_p, cache)
                return c, cache[key]["why"]
        except Exception:  # noqa: BLE001
            continue

    need = ([zh_name.split("足球", 1)[0], zh_name.split("足球", 1)[1]]
            if "足球" in zh_name else [zh_name])
    try:
        d = http_json(ZH_API, params={"action": "query", "list": "search",
                                      "srsearch": prefix + zh_name, "srlimit": 5,
                                      "format": "json", "formatversion": "2"})
        picks = [x["title"] for x in (d.get("query", {}).get("search") or [])
                 if prefix in x["title"] and all(k in x["title"] for k in need)]
    except Exception:  # noqa: BLE001
        picks = []
    pick = picks[0] if picks else None
    cache[key] = {"title": pick,
                  "why": f"搜索兜底 {pick}" if pick else f"候选全不存在且搜索无果 {cands}"}
    jdump(cache_p, cache)
    return pick, cache[key]["why"]


def en_title(meta: dict, tags: dict) -> str | None:
    en = meta.get("en")
    if not en:
        return None
    return f"{tags['en_split']} {en}" if meta["kind"] == "split" else f"{tags['en_cal']} {en}"


Z_COLS = {
    "排名": "pos", "名次": "pos", "队伍": "team", "球队": "team", "球隊": "team",
    "賽": "pld", "赛": "pld", "場": "pld", "场": "pld", "場數": "pld", "场数": "pld",
    "勝": "w", "胜": "w", "和": "d", "平": "d", "負": "l", "负": "l",
    "得": "gf", "進": "gf", "进": "gf", "進球": "gf", "进球": "gf", "得球": "gf",
    "失": "ga", "失球": "ga", "差": "gd", "淨": "gd", "净": "gd", "淨勝": "gd",
    "分": "pts", "積分": "pts", "积分": "pts", "分數": "pts", "分数": "pts",
}
EN_COLS = {"Pos": "pos", "Team": "team", "Pld": "pld", "W": "w", "D": "d",
           "L": "l", "GF": "gf", "GA": "ga", "GD": "gd", "Pts": "pts"}


def fetch_table(title: str, no_net: bool, api: str = ZH_API) -> tuple[list | None, str]:
    """抓赛季页积分表 → [{pos,team,pld,w,d,l,gf,ga,gd,pts}]"""
    CACHE.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(f"{api}|{title}".encode("utf-8")).hexdigest()[:12]
    cache_p = CACHE / f"{h}.json"
    cached = jload(cache_p)
    if cached and time.time() - cached.get("ts", 0) < TTL:
        return cached["rows"], f"缓存 {time.strftime('%m-%d %H:%M', time.localtime(cached['ts']))}"
    if no_net:
        return (cached["rows"] if cached else None), "no-net 且无缓存"

    params = {"action": "parse", "page": title, "prop": "text",
              "format": "json", "formatversion": "2", "redirects": "1"}
    if api == ZH_API:
        params["variant"] = "zh-cn"
    try:
        d = http_json(api, params=params, timeout=60)
    except Exception as exc:  # noqa: BLE001
        return (cached["rows"] if cached else None), f"抓取失败 {type(exc).__name__}"
    if "error" in d:
        return (cached["rows"] if cached else None), f"页面不存在：{d['error'].get('info')}"

    html = d["parse"]["text"]
    tables = re.findall(r"<table[^>]*wikitable.*?</table>", html, re.S)
    rows = None
    for tb in tables:
        trs = re.findall(r"<tr.*?</tr>", tb, re.S)
        if len(trs) < 8:
            continue
        grid = [[strip_tags(c) for c in re.findall(r"<t[hd].*?</t[hd]>", tr, re.S)] for tr in trs]
        head = grid[0]
        idx: dict[str, int] = {}
        for i, cell in enumerate(head):
            c = cell.strip()
            first = c.split(" ")[0].split("(")[0].strip()
            key = EN_COLS.get(first) or Z_COLS.get(first) or Z_COLS.get(c[:2])
            if key and key not in idx:
                idx[key] = i
        if not {"team", "pts"} <= set(idx):
            continue
        out = []
        for r in grid[1:]:
            if len(r) <= max(idx.values()):
                continue

            def g(k):
                i = idx.get(k)
                return r[i] if i is not None and i < len(r) else ""
            team = g("team")
            if not team or team in ("队伍 ＼ 轮数",) or "＼" in team:
                continue
            pts = g("pts")
            if not re.fullmatch(r"\d+", pts or ""):
                continue
            out.append({"pos": g("pos"), "team": team, "pld": g("pld"), "w": g("w"),
                        "d": g("d"), "l": g("l"), "gf": g("gf"), "ga": g("ga"),
                        "gd": g("gd"), "pts": pts})
        if len(out) >= 8:
            rows = out
            break
    if rows:
        jdump(cache_p, {"ts": time.time(), "title": title, "rows": rows})
        return rows, "抓取成功"
    return (cached["rows"] if cached else None), "没解析到积分表"


def fetch_table_en(title: str, no_net: bool) -> tuple[list | None, str]:
    """英文维基积分表（zh 没有对应赛季页时兜底）。"""
    return fetch_table(title, no_net, api=EN_API)


def match_row(name_cn: str, rows: list, aliases: dict | None = None) -> tuple[dict | None, str]:
    """中文队名 → 积分表行。

    候选名按优先级排队：配置里显式给的维基中文名 → 英文维基名 → API-Football 名 →
    竞彩简称本身。每一层先试「完全相等」，再试「互相包含」，最后才 fuzzy。
    """
    alias = (aliases or {}).get(name_cn) or {}
    names = [alias.get(k) for k in ("wiki", "zh", "en_wiki", "af", "en") if alias.get(k)]
    names.append(name_cn)

    normed = [(r, norm_team(r["team"])) for r in rows]
    for nm in names:
        n = norm_team(nm)
        if not n:
            continue
        for r, tn in normed:
            if tn == n:
                return r, f"精确({nm}→{r['team']})"

    for nm in names:
        n = norm_team(nm)
        if len(n) < 3:
            continue
        for r, tn in normed:
            if n in tn or tn in n:
                return r, f"包含({nm}→{r['team']})"

    for nm in names:
        n = norm_team(nm)
        if len(n) < 4:
            continue
        cands = difflib.get_close_matches(n, [tn for _, tn in normed], n=1, cutoff=0.78)
        if cands:
            for r, tn in normed:
                if tn == cands[0]:
                    return r, f"近似({nm}→{r['team']})"
    return None, "无匹配"


# ── 天气 ────────────────────────────────────────────────────────────────
def weather_of(city: str, cc: str, iso_time: str) -> dict | None:
    geo_p = CACHE / "_geo.json"
    geo = jload(geo_p, {}) or {}
    key = f"{city}|{cc}"
    if key not in geo:
        q = urllib.parse.urlencode({"name": city, "count": 5, "language": "en"})
        try:
            d = http_json(GEO_API + "?" + q, timeout=20)
        except Exception:  # noqa: BLE001
            return None
        hit = None
        for r in d.get("results") or []:
            if (r.get("country_code") or "").upper() == cc.upper():
                hit = r
                break
        if not hit:
            return None
        geo[key] = {"lat": hit["latitude"], "lon": hit["longitude"]}
        jdump(geo_p, geo)
    g = geo[key]
    q = urllib.parse.urlencode({"latitude": g["lat"], "longitude": g["lon"],
                                "hourly": "temperature_2m,precipitation,wind_speed_10m",
                                "forecast_days": 4, "timezone": "Asia/Shanghai"})
    try:
        d = http_json(METEO_API + "?" + q, timeout=20)
    except Exception:  # noqa: BLE001
        return None
    hrs = (d.get("hourly") or {}).get("time") or []
    if iso_time not in hrs:
        return None
    i = hrs.index(iso_time)
    h = d["hourly"]
    return {"time": iso_time,
            "temp": h.get("temperature_2m", [None] * (i + 1))[i],
            "rain": h.get("precipitation", [None] * (i + 1))[i],
            "wind": h.get("wind_speed_10m", [None] * (i + 1))[i]}


# ── 主流程 ──────────────────────────────────────────────────────────────
def no_of(num: int) -> str:
    """竞彩编号：千位为星期（周一=1…周日=7），后三位为场次号。"""
    wk = "一二三四五六日"[num // 1000 - 1] if 1 <= num // 1000 <= 7 else "?"
    return f"周{wk}{num % 1000:03d}"


def load_slate(date_tag: str, nums: list[str] | None = None,
               weekday: str | None = None) -> dict:
    """取当期场次。

    注意：竞彩 `matchDate` 对**跨零点场次是次日**（10/19 00:30 的球挂 10-19，
    但属于「周日」期；「周一」期 00:30 的球挂 10-20）。所以按日期捞容易捞错批，
    优先用 --nums（竞彩编号）或 --weekday（周字）过滤。
    """
    p = STATE / "batch" / "_slate.json"
    d = jload(p, {}) or {}
    want = f"{date_tag[:4]}-{date_tag[4:6]}-{date_tag[6:]}"
    out = {}
    for grp in (d.get("value") or {}).get("matchInfoList") or []:
        for m in grp.get("subMatchList") or []:
            no = no_of(int(m["matchNum"]))
            if nums:
                if no not in nums:
                    continue
            elif weekday:
                if not no.startswith(weekday):
                    continue
            elif (m.get("matchDate") or "") != want:
                continue
            out[no] = {
                "no": no,
                "league": m.get("leagueAbbName") or "",
                "home": m.get("homeTeamAbbName") or "",
                "away": m.get("awayTeamAbbName") or "",
                "date": (m.get("matchDate") or "")[:10],
                "time": m.get("matchTime") or "",
            }
    return out


def build(date_tag: str, no_net: bool = False, nums: list[str] | None = None,
          weekday: str | None = None) -> dict:
    cfg = jload(CONFIG / "league_sources.json", {}) or {}
    stad = jload(CONFIG / "stadiums.json", {}) or {}
    team_alias = jload(CONFIG / "team_aliases.json", {}) or {}
    tags = season_tags(date_tag)
    slate = load_slate(date_tag, nums, weekday)

    leagues: dict[str, dict] = {}
    missing: list[str] = []
    cache_by_league: dict[str, list | None] = {}

    for lg in sorted({m["league"] for m in slate.values()}):
        meta = cfg.get(lg)
        if not meta:
            missing.append(f"{lg}：未在 league_sources.json 里配置")
            cache_by_league[lg] = None
            continue
        title, why = resolve_page(meta["zh"], meta["kind"], tags, no_net)
        rows, how, src = None, "", ""
        if title:
            rows, how = fetch_table(title, no_net)
            src = "zh.wikipedia"
        if not rows:
            et = en_title(meta, tags)
            if et:
                r2, h2 = fetch_table_en(et, no_net)
                if r2:
                    rows, how, src, title = r2, h2, "en.wikipedia", et
                else:
                    how = f"{how}；英文页也没取到（{h2}）"
        cache_by_league[lg] = rows
        if rows:
            leagues[lg] = {"page": title, "source": src, "fetched": how, "rows": rows}
        else:
            leagues[lg] = {"page": title or "", "source": "无", "fetched": how or why, "rows": []}
            missing.append(f"{lg}：积分表没取到（{how or why}）")

    matches = {}
    for no, m in slate.items():
        rows = cache_by_league.get(m["league"]) or []
        rec = {"no": no, "league": m["league"], "date": m.get("date", ""), "time": m["time"],
               "home": m["home"], "away": m["away"]}
        for side in ("home", "away"):
            if rows:
                row, why = match_row(m[side], rows, team_alias)
                rec[side + "_rank"] = row if row else None
                rec[side + "_why"] = why
            else:
                rec[side + "_rank"] = None
                rec[side + "_why"] = "该联赛无积分表"
        s = stad.get(m["home"])
        hhmm = (m["time"] or "")[:5]
        mdate = m.get("date") or ""
        if s and re.fullmatch(r"\d{2}:\d{2}", hhmm) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", mdate):
            iso = f"{mdate}T{hhmm[:2]}:00"
            rec["weather"] = weather_of(s["city"], s["cc"], iso)
        else:
            rec["weather"] = None
        matches[no] = rec

    data = {"date": date_tag, "season": tags, "leagues": leagues,
            "matches": matches, "missing": missing,
            "generated": time.strftime("%Y-%m-%d %H:%M")}
    return data


def to_md(data: dict) -> str:
    L = [f"# 联赛排名与外部指标 ｜ {data['date']}", ""]
    L.append("> 来源：中文维基百科赛季页积分榜（`variant=zh-cn`）＋ open-meteo 比赛时刻天气。")
    L.append("> **赛季累计表**，只更新到已完赛场次；赛中/赛后可能滞后一轮，不当实时用。")
    L.append("> 拿不到的联赛写进文末 missing，**不猜、不估、不拿别的联赛顶替**。")
    L.append("")
    L.append("## 一、本批各场排名对照")
    L.append("")
    L.append("| 场次 | 联赛 | 比赛日 | 时间 | 主队 | 排名/场次/胜平负/进失/积分 | 客队 | 排名 |")
    L.append("|---|---|---|---|---|---|---|---|")
    for no, m in sorted(data["matches"].items()):
        def s(r):
            if not r:
                return "—"
            return (f"第{r['pos']}／{r['pld']}场 {r['w']}-{r['d']}-{r['l']}／"
                    f"{r['gf']}进{r['ga']}失／{r['pts']}分")
        L.append(f"| {no} | {m['league']} | {m.get('date', '')} | {m['time']} | {m['home']} "
                 f"| {s(m['home_rank'])} | {m['away']} | {s(m['away_rank'])} |")
    L.append("")

    L.append("## 二、按联赛的完整积分榜")
    L.append("")
    for lg, info in data["leagues"].items():
        L.append(f"### {lg}（{info['page']}）")
        L.append("")
        if not info["rows"]:
            L.append("_积分表未取到。_")
            L.append("")
            continue
        L.append("| 名次 | 球队 | 场次 | 胜 | 平 | 负 | 进 | 失 | 净 | 积分 |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in info["rows"]:
            L.append(f"| {r['pos']} | {r['team']} | {r['pld']} | {r['w']} | {r['d']} | {r['l']} "
                     f"| {r['gf']} | {r['ga']} | {r['gd']} | {r['pts']} |")
        L.append("")

    wx = [(no, m) for no, m in sorted(data["matches"].items()) if m.get("weather")]
    if wx:
        L.append("## 三、比赛时刻天气")
        L.append("")
        L.append("| 场次 | 主队城市 | 气温 | 降水 | 风速 |")
        L.append("|---|---|---|---|---|")
        for no, m in wx:
            w = m["weather"]
            L.append(f"| {no} | {m['home']} | {w['temp']}°C | {w['rain']} mm | {w['wind']} km/h |")
        L.append("")

    if data["missing"]:
        L.append("## 四、缺源")
        L.append("")
        for x in data["missing"]:
            L.append(f"- {x}")
        L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="联赛排名与外部指标（R48 · A 级）")
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--no-net", action="store_true", help="只用缓存，不联网")
    ap.add_argument("--md", action="store_true", help="同时输出人读版 md")
    ap.add_argument("--nums", nargs="+", default=None,
                    help="限定竞彩编号，如 周一001 周一002（跨零点批次必用）")
    ap.add_argument("--weekday", default=None,
                    help="按周字过滤，如 周一（比按日期稳，跨零点场次 matchDate 是次日）")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    data = build(a.date, a.no_net, a.nums, a.weekday)
    out_dir = STATE / "intel" / a.date
    jp = out_dir / f"_leagues_{a.date}.json"
    jdump(jp, data)
    if not a.quiet:
        ok = sum(1 for m in data["matches"].values() if m.get("home_rank") and m.get("away_rank"))
        print(f"✅ {jp}")
        print(f"   排名覆盖 {ok}/{len(data['matches'])} 场 · 联赛 {len(data['leagues'])} 个"
              f" · 缺源 {len(data['missing'])} 条")
    if a.md:
        mp = out_dir / f"_leagues_{a.date}.md"
        mp.write_text(to_md(data), encoding="utf-8")
        if not a.quiet:
            print(f"✅ {mp}")


if __name__ == "__main__":
    main()
