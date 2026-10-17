#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ext_predict.py — 外部预测对照层（v0.1，2026-10-17 建）

用途：把「第三方赛前预测」接进写文管线，产出「外部预测 / 后台模型 / 市场折算」三方对照，
避免只靠自家模型 + 定价两条腿。

设计取舍（实测结论，别再走回头路）
- Forebet / PredictZ / Windrawwin / FootyStats / AiScore / Sofascore API / BeSoccer / Dailysports
  全部 Cloudflare 拦截：requests 403「Just a moment...」，Playwright 有头/无头用真 Chrome 也过不去。
  → 这些站**不自动抓**；要引就在检索层用片段（web_search）人工粘一句，脚本里记为 source="manual"。
- 可直连且带「预测比分 + 理由」的：**Sports Mole**（/football/<team>/preview/...prediction-team-news-lineups_<id>.html，
  正文有「We say: A 2-1 B」+ 一段理由）。这是本脚本的默认源。
- 队名映射在 database/config/team_aliases.json（中文名 → Sports Mole slug / 英文名）。

用法
    python scripts/ext_predict.py index                     # 抓预测索引（缓存到 state/_ext_raw/）
    python scripts/ext_predict.py match 埃弗顿 切尔西        # 抓单场
    python scripts/ext_predict.py batch --file state/_tmp_fixtures.txt   # 每行「主队 客队」
    python scripts/ext_predict.py show 20261017             # 打印本批已抓到的东西
    python scripts/ext_predict.py report 20261017           # 生成 md 对照表（写 📝文章/<日期>/_外部预测对照.md）

输出
    state/_ext_<YYYYMMDD>.json   {"date": ..., "items": [{home, away, source, predicted, note, url, fetched_at}]}
    state/_ext_raw/*.html        原始页（排查用，勿入库）
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "state" / "cache" / "_ext_raw"
RECORDS = ROOT / "state" / "records"
BATCH_DIR = ROOT / "state" / "batch"
ALIASES = ROOT / "database" / "config" / "team_aliases.json"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
SM_INDEX = "https://www.sportsmole.co.uk/football/predictions/"

# API-Football（api-sports.io）免费层：100 次/天；key 放环境变量或 state/api-keys.json
AF_BASE = "https://v3.football.api-sports.io"
KEYS_FILE = ROOT / "state" / "api-keys.json"

# Sportskeeda 的联赛聚合页（预测多以「某专家预测本轮各场」的汇总文形式出现）
SK_HUBS = {
    "英超": "https://www.sportskeeda.com/go/premier-league",
    "西甲": "https://www.sportskeeda.com/go/la-liga",
    "法甲": "https://www.sportskeeda.com/go/ligue-1",
    "意甲": "https://www.sportskeeda.com/go/serie-a",
    "德甲": "https://www.sportskeeda.com/go/bundesliga",
}

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


# ---------------------------------------------------------------- 队名映射
def load_aliases() -> dict:
    if not ALIASES.exists():
        return {}
    return json.loads(ALIASES.read_text(encoding="utf-8"))


def slugs(name: str, aliases: dict) -> list[str]:
    item = aliases.get(name) or {}
    out = []
    if item.get("sm_slug"):
        out.append(item["sm_slug"])
    for s in item.get("sm_alias", []) or []:
        out.append(s)
    if not out:
        # 兜底：中文没有映射就退化成小写名（基本抓不到，会报「未找到」）
        out.append(name.lower())
    return out


# ---------------------------------------------------------------- 抓取
def _get(url: str, cache: Path | None = None, timeout: int = 25) -> str:
    if cache and cache.exists() and cache.stat().st_size > 5000:
        return cache.read_text(encoding="utf-8", errors="replace")
    if requests is None:
        raise RuntimeError("需要 requests：pip install requests")
    r = requests.get(url, headers=UA, timeout=timeout)
    r.raise_for_status()
    text = r.text
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text, encoding="utf-8", errors="replace")
    return text


def fetch_index(force: bool = False, stamp: str | None = None) -> list[dict]:
    """抓预测索引页，返回 [{href, text}]。缓存按日期，force=True 重抓。"""
    stamp = stamp or dt.date.today().strftime("%Y%m%d")
    cache = RAW / f"sportsmole_index_{stamp}.html"
    if force and cache.exists():
        cache.unlink()
    html = _get(SM_INDEX, cache)
    rows = re.findall(r'href="(/football/[^"]+/preview/[^"]+prediction[^"]*)"[^>]*>(.*?)</a>', html, re.S)
    seen, out = set(), []
    for href, inner in rows:
        if href in seen:
            continue
        seen.add(href)
        text = re.sub(r"<[^>]+>", " ", inner)
        text = " ".join(text.split())
        out.append({"href": "https://www.sportsmole.co.uk" + href, "text": text})
    return out


def find_via_team_page(home: str, away: str, aliases: dict) -> dict | None:
    """索引页只收录部分联赛时的兜底：抓主队球队页，筛出双方都在文件名里的预测链接。"""
    h = slugs(home, aliases)
    a = slugs(away, aliases)
    for hs in h:
        url = f"https://www.sportsmole.co.uk/football/{hs}/"
        try:
            html = _get(url, RAW / f"sm_team_{hs}.html", timeout=25)
        except Exception:
            continue
        for href in set(re.findall(r'href="(/football/[^"]+/preview/[^"]+)"', html)):
            low = href.lower()
            if any(x in low for x in h) and any(y in low for y in a):
                return {"href": "https://www.sportsmole.co.uk" + href, "text": low}
    return None


def find_preview(home: str, away: str, aliases: dict, index: list[dict]) -> dict | None:
    h = slugs(home, aliases)
    a = slugs(away, aliases)
    for row in index:
        href = row["href"].lower()
        if any(f"/{s}-vs-{t}" in href or f"/{s}-vs-{t}" == href[-len(f"/{s}-vs-{t}"):] for s in h for t in a):
            return row
        # 也认反过来（Sports Mole 有时按客场主序）
        if any(f"/{t}-vs-{s}" in href for s in h for t in a):
            return row
    return find_via_team_page(home, away, aliases)


def parse_preview(html: str) -> dict:
    """抽「We say: A 2-1 B」+ 紧随的理由句 + 预测首发。"""
    import html as _h
    plain = _h.unescape(html).replace("\xa0", " ")
    plain = re.sub(r"<[^>]+>", " ", plain)
    txt = " ".join(plain.split())
    out: dict = {}
    m = re.search(r"We say:\s*([A-Za-z0-9' .&()-]{2,40}?)\s+(\d)\s*[-–]\s*(\d)\s+([A-Za-z0-9' .&()-]{2,40}?)(?=[A-Z])", txt)
    if m:
        out["predicted"] = f"{m.group(1).strip()} {m.group(2)}-{m.group(3)} {m.group(4).strip()}"
        tail = txt[m.end(): m.end() + 320]
        out["note"] = re.split(r"(?<=[.!?])\s", tail.strip())[0][:220]
    else:
        m2 = re.search(r"We say:\s*([A-Za-z0-9' .&()-]{2,40}?)\s+(\d)\s*[-–]\s*(\d)\s+([A-Za-z0-9' .&()-]{2,40})", txt)
        if m2:
            out["predicted"] = f"{m2.group(1).strip()} {m2.group(2)}-{m2.group(3)} {m2.group(4).strip()}"
    lineup = re.search(r"starting lineup:\s*(.{20,240}?)\s*We say", txt)
    if lineup:
        out["lineup"] = lineup.group(1).strip()
    return out


# ---------------------------------------------------------------- 落盘
def store_path(stamp: str) -> Path:
    RECORDS.mkdir(parents=True, exist_ok=True)
    return RECORDS / f"_ext_{stamp}.json"


def load_store(stamp: str) -> dict:
    p = store_path(stamp)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"date": stamp, "items": []}


def save_store(data: dict) -> Path:
    p = store_path(data["date"])
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


# ------------------------------------------------------ Sportskeeda（第二自动源）
def _frag(name: str, aliases: dict) -> list[str]:
    """把中文队名压成一串可用于 slug 比对的英文片段（含空格与连字符两种写法）。"""
    ent = aliases.get(name, {})
    words = [ent.get("sm_slug", ""), ent.get("en", "")] + list(ent.get("sm_alias", []))
    out = []
    for w in words:
        w = (w or "").lower().replace(" ", "-")
        if w:
            out.append(w)
            out.append(w.replace("-", ""))
    return sorted(set(out))


def find_sk_roundup(home: str, away: str, league: str, aliases: dict) -> list[dict]:
    """在 Sportskeeda 联赛聚合页里找同时含两队名字的文章链接（预测汇总文）。"""
    hub = SK_HUBS.get(league)
    if not hub:
        return []
    html = _get(hub, RAW / f"sk_hub_{league}.html")
    links = sorted(set(re.findall(r'href="(/football/[^"]{10,200})"', html)))
    h, a = _frag(home, aliases), _frag(away, aliases)
    hits = []
    for l in links:
        low = l.lower().replace("-", "")
        if any(x.replace("-", "") in low for x in h) and any(y.replace("-", "") in low for y in a):
            hits.append(l)
    hits.sort(key=lambda s: (0 if "predict" in s.lower() else 1, s))
    return [{"href": "https://www.sportskeeda.com" + l, "text": l} for l in hits[:5]]


def parse_sk_prediction(html: str, home: str, away: str, aliases: dict) -> dict:
    """从汇总文里抠 `Prediction: Everton 2-1 Chelsea` 这一句，并拾取前一句作摘要。"""
    import html as _h
    plain = _h.unescape(html).replace("\xa0", " ")
    plain = " ".join(re.sub(r"<[^>]+>", " ", plain).split())
    h, a = _frag(home, aliases), _frag(away, aliases)

    def _hit(team: str) -> bool:
        t = team.lower().replace("-", "")
        return any(f.replace("-", "") in t for f in h + a)

    def _canon(team: str, name: str) -> str:
        """把抓到的队名还原成别名表里的规范英文名（顺带切掉黏在后面的下一场标题）。"""
        clean = re.split(r"\s+vs\s+|[A-Za-z]vs[A-Za-z]", team)[0].strip()
        for key in (name,):
            ent = aliases.get(key, {})
            if ent.get("en") and ent["en"].lower().replace("-", "") in clean.lower().replace("-", ""):
                return ent["en"]
        # 别名反查：clean 里含哪支队伍就算哪支
        for zh, ent in aliases.items():
            if not isinstance(ent, dict):
                continue
            for f in [ent.get("sm_slug", ""), ent.get("en", "")]:
                f2 = (f or "").lower().replace("-", "").replace(" ", "")
                if f2 and f2 in clean.lower().replace("-", "").replace(" ", ""):
                    return ent.get("en") or clean
        return clean

    pat = re.compile(r"Prediction:\s*([A-Za-z .'\u2019-]{2,40}?)\s+(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z .'\u2019-]{2,40})")
    for m in pat.finditer(plain):
        t1, t2 = m.group(1).strip(), m.group(4).strip()
        if _hit(t1) and _hit(t2):
            head = plain[max(0, m.start() - 170):m.start()].strip()
            c1, c2 = _canon(t1, home), _canon(t2, away)
            g1, g2 = m.group(2), m.group(3)
            # 汇总文常把客队写在前面，统一转成「主队在前」再进表
            home_en = (aliases.get(home, {}) or {}).get("en", "")
            if home_en and c1.lower() != home_en.lower() and c2.lower() == home_en.lower():
                c1, c2 = c2, c1
                g1, g2 = g2, g1
            return {
                "predicted": f"{c1} {g1}-{g2} {c2}",
                "note": head[-160:],
                "lineup": "",
                "stale_risk": True,
            }
    return {}


def add_item(home: str, away: str, row: dict | None, parsed: dict, stamp: str,
             manual: str | None = None, provider: str = "sportsmole") -> dict:
    data = load_store(stamp)
    item = {
        "home": home,
        "away": away,
        "provider": "manual" if manual else provider,
        "source": "manual" if manual else provider,
        "predicted": manual or (parsed.get("predicted") or ""),
        "predicted_dir": parsed.get("predicted_dir", ""),
        "hit_prob": parsed.get("hit_prob", 0),
        "note": parsed.get("note", ""),
        "lineup": parsed.get("lineup", ""),
        "stale_risk": bool(parsed.get("stale_risk")),
        "url": (row or {}).get("href", ""),
        "fetched_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    data["items"] = [x for x in data["items"] if not (x["home"] == home and x["away"] == away)]
    data["items"].append(item)
    save_store(data)
    return item


# ---------------------------------------------------------------- 命令
def cmd_index(args) -> int:
    idx = fetch_index(force=args.force)
    print(f"索引条目 {len(idx)} 条（缓存 state/_ext_raw/sportsmole_index_*.html）")
    for row in idx[: args.limit]:
        print("  -", row["text"][:60], "|", row["href"])
    return 0


def _via_sportsmole(home: str, away: str, aliases: dict, idx: list[dict]) -> tuple[dict | None, dict]:
    row = find_preview(home, away, aliases, idx)
    if not row:
        return None, {}
    html = _get(row["href"], RAW / (re.sub(r"[^a-z0-9]+", "_", row["href"].lower())[-80:] + ".html"))
    return row, parse_preview(html)


def _via_sportskeeda(home: str, away: str, league: str, aliases: dict) -> tuple[dict | None, dict]:
    for row in find_sk_roundup(home, away, league, aliases):
        html = _get(row["href"], RAW / (re.sub(r"[^a-z0-9]+", "_", row["href"].lower())[-70:] + ".html"))
        parsed = parse_sk_prediction(html, home, away, aliases)
        if parsed:
            return row, parsed
    return None, {}


# ---------------------------------------------------------------- API-Football
def api_key() -> str:
    """key 取环境变量 → state/api-keys.json（该文件不入库）。"""
    import os
    v = (os.environ.get("API_FOOTBALL_KEY") or "").strip()
    if v:
        return v
    for p in (KEYS_FILE, ROOT / "state" / "api-keys.local.json"):
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for k in ("api_football", "api-football", "API_FOOTBALL_KEY", "apifootball"):
            v = str(d.get(k) or "").strip()
            if v:
                return v
    return ""


def _af_get(path: str, params: dict, cache: Path | None = None) -> dict:
    key = api_key()
    if not key:
        raise RuntimeError("缺 API-Football key（环境变量 API_FOOTBALL_KEY 或 state/api-keys.json）")
    if cache and cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    if requests is None:
        raise RuntimeError("缺 requests")
    r = requests.get(f"{AF_BASE}/{path}", params=params,
                     headers={"x-apisports-key": key}, timeout=25)
    if r.status_code == 403:
        raise RuntimeError("403：key 无效/未授权")
    if r.status_code == 429:
        raise RuntimeError("429：今日配额用完（免费层 100 次/天）")
    r.raise_for_status()
    d = r.json()
    errs = d.get("errors")
    if errs:
        raise RuntimeError(f"API 报错：{errs}")
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


AF_LEAGUES = {"英超": 39, "西甲": 140, "法甲": 61, "意甲": 135, "德甲": 78}


def af_fixtures(stamp: str, force: bool = False) -> list[dict]:
    """按日期取当天赛程（1 次请求，结果缓存）。stamp=YYYYMMDD。"""
    d = f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"
    cache = RAW / f"af_fixtures_{d}.json"
    if force and cache.exists():
        cache.unlink()
    data = _af_get("fixtures", {"date": d, "timezone": "Asia/Shanghai"}, cache)
    return data.get("response", []) or []


def _via_api_football(home: str, away: str, aliases: dict, stamp: str,
                      league: str = "") -> tuple[dict | None, dict]:
    """先按日期赛程对齐队名，再取 /predictions。返回 (row, parsed)。"""
    en_home = (aliases.get(home) or {}).get("af") or (aliases.get(home) or {}).get("en") or ""
    en_away = (aliases.get(away) or {}).get("af") or (aliases.get(away) or {}).get("en") or ""
    nh, na = _norm_name(en_home), _norm_name(en_away)
    # 名字归一后为空说明别名表没收录，模糊匹配会误配（空串能匹配任何队名）→ 直接报错
    if not nh or not na:
        print(f"  [AF] 别名表缺 {home}/{away} 的英文名，先在 database/config/team_aliases.json 补 en/af")
        return None, {}
    day = stamp[:8]
    try:
        fixtures = list(af_fixtures(day))
        try:  # 跨零点场次（00:30 / 03:00 这类）在北京时间属次日
            nx = dt.datetime.strptime(day, "%Y%m%d") + dt.timedelta(days=1)
            fixtures += af_fixtures(nx.strftime("%Y%m%d"))
        except Exception:
            pass
    except RuntimeError as e:
        print(f"  [AF] 跳过：{e}")
        return None, {}
    lid = AF_LEAGUES.get(league or "")
    cand = []
    for f in fixtures:
        if lid and (f.get("league") or {}).get("id") != lid:
            continue
        teams = f.get("teams") or {}
        h = _norm_name(((teams.get("home") or {}).get("name") or ""))
        a = _norm_name(((teams.get("away") or {}).get("name") or ""))
        if not h or not a:
            continue
        if (nh == h or nh in h or h in nh) and (na == a or na in a or a in na):
            cand.append((f, (teams.get("home") or {}).get("name"), (teams.get("away") or {}).get("name")))
    if not cand:
        print(f"  [AF] 当天赛程里没找到 {en_home} vs {en_away}" + (f"（联赛过滤：{league}）" if lid else ""))
        return None, {}
    # 青年队/女队优先排除
    def _senior(item):
        blob = f"{item[1]}{item[2]}"
        bad = any(x in blob for x in ("U18", "U19", "U20", "U21", "U23", " W", "W "))
        return 0 if bad else 1
    cand.sort(key=_senior, reverse=True)
    f, hname, aname = cand[0]
    row = {
        "href": f"https://www.api-football.com/fixture/{(f.get('fixture') or {}).get('id')}",
        "text": f"{hname} vs {aname}",
        "fixture_id": (f.get("fixture") or {}).get("id"),
        "league": ((f.get("league") or {}).get("name") or ""),
        "kick": (f.get("fixture") or {}).get("date", ""),
    }
    fid = row["fixture_id"]
    try:
        data = _af_get("predictions", {"fixture": fid}, RAW / f"af_pred_{fid}.json")
    except RuntimeError as e:
        print(f"  [AF] 预测取失败：{e}")
        return row, {}
    resp = (data.get("response") or [])
    if not resp:
        print(f"  [AF] fixture {fid} 无预测数据")
        return row, {}
    pred = resp[0].get("predictions") or {}
    pct = pred.get("percent") or {}
    go = pred.get("goals") or {}
    win = (pred.get("winner") or {}).get("name") or ""
    advice = (pred.get("advice") or "").strip()

    def _p(x):
        try:
            return float(str(x).replace("%", "").strip())
        except Exception:
            return 0.0

    ph, pd, pa = _p(pct.get("home")), _p(pct.get("draw")), _p(pct.get("away"))
    if win:
        nw = _norm_name(win)
        if nw and (nw in nh or nh in nw):
            d = "主胜"
        elif nw and (nw in na or na in nw):
            d = "客胜"
        else:
            d = "平"
    else:
        mx = max(ph, pd, pa)
        d = "主胜" if mx == ph else ("客胜" if mx == pa else "平")
    note_bits = []
    if ph or pd or pa:
        note_bits.append(f"胜平负 {ph:.0f}/{pd:.0f}/{pa:.0f}%")
    # AF 的 goals 字段实测返回 "-2.5--2.5" 这类坏值，不做二次加工也不进正文
    if advice:
        note_bits.append(advice)
    if pred.get("win_or_draw"):
        note_bits.append("倾向胜或平")
    return row, {
        "predicted": "",
        "predicted_dir": d,
        "hit_prob": max(ph, pd, pa),
        "note": "；".join(note_bits)[:120],
        "provider": "api-football",
        "url": row["href"],
    }



def cmd_match(args) -> int:
    aliases = load_aliases()
    league = args.league or ""
    item = None
    if args.provider in ("auto", "sportsmole"):
        idx = fetch_index()
        row, parsed = _via_sportsmole(args.home, args.away, aliases, idx)
        if row:
            item = add_item(args.home, args.away, row, parsed, args.date,
                            manual=args.manual, provider="sportsmole")
    if item is None and args.provider in ("auto", "api-football", "af"):
        row, parsed = _via_api_football(args.home, args.away, aliases, args.date, league)
        if row and parsed:
            item = add_item(args.home, args.away, row, parsed, args.date, provider="api-football")
    if item is None and args.provider in ("auto", "sportskeeda"):
        if not league:
            print("Sportskeeda 需要联赛（--league 英超/西甲/法甲/意甲/德甲）")
        else:
            row, parsed = _via_sportskeeda(args.home, args.away, league, aliases)
            if row:
                item = add_item(args.home, args.away, row, parsed, args.date,
                                manual=args.manual, provider="sportskeeda")
    if item is None and args.manual:
        item = add_item(args.home, args.away, None, {}, args.date, manual=args.manual, provider="manual")
    if item is None:
        print(f"两个自动源都没拿到：{args.home} vs {args.away}")
        print("  兜底：--manual \"埃弗顿 2-1 切尔西\"（人工摘录，标注 manual）")
        return 2
    print(json.dumps(item, ensure_ascii=False, indent=2))
    return 0


def cmd_batch(args) -> int:
    lines = [l.strip() for l in Path(args.file).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    aliases = load_aliases()
    idx = fetch_index()
    ok = miss = 0
    for line in lines:
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            continue
        home, away = parts[0], parts[1]
        league = parts[2] if len(parts) > 2 else ""
        row, parsed, prov = None, {}, ""
        if args.provider in ("auto", "sportsmole"):
            row, parsed = _via_sportsmole(home, away, aliases, idx)
            prov = "sportsmole"
        if not row and args.provider in ("auto", "api-football", "af"):
            row, parsed = _via_api_football(home, away, aliases, args.date, league)
            prov = "api-football"
        if not row and args.provider in ("auto", "sportskeeda") and league:
            row, parsed = _via_sportskeeda(home, away, league, aliases)
            prov = "sportskeeda"
        if not row:
            print(f"[MISS] {home} vs {away}")
            miss += 1
            continue
        add_item(home, away, row, parsed, args.date, provider=prov)
        tag = {"sportskeeda": "SK", "api-football": "AF"}.get(prov, "SM")
        shown = parsed.get("predicted") or parsed.get("predicted_dir") or "?"
        print(f"[OK/{tag}] {home} vs {away} → {shown}")
        ok += 1
    print(f"命中 {ok} 场 / 未命中 {miss} 场")
    return 0


def cmd_doctor(args) -> int:
    """体检：哪个源能用、哪个要 key、哪个被墙。"""
    import os as _os
    rows = []
    try:
        idx = fetch_index(force=True)
        rows.append(("Sports Mole", "可用", f"索引 {len(idx)} 条"))
    except Exception as e:
        rows.append(("Sports Mole", "失败", type(e).__name__))
    for lg, hub in SK_HUBS.items():
        try:
            html = _get(hub, RAW / f"sk_hub_{lg}.html", timeout=20)
            n = len(set(re.findall(r'href="(/football/[^"]*-vs-[^"]*)"', html)))
            rows.append((f"Sportskeeda {lg}", "可用", f"vs 链接 {n} 条"))
        except Exception as e:
            rows.append((f"Sportskeeda {lg}", "失败", type(e).__name__))
    key = _os.environ.get("API_FOOTBALL_KEY", "")
    rows.append(("API-Football", "有 key" if key else "缺 key", "环境变量 API_FOOTBALL_KEY" if key else "去 dashboard.api-football.com 免费注册后 export"))
    print(f"{'源':18s} {'状态':8s} 说明")
    print("-" * 60)
    for a, b, c in rows:
        print(f"{a:18s} {b:8s} {c}")
    return 0


def cmd_show(args) -> int:
    data = load_store(args.date)
    for it in data["items"]:
        print(f"{it['home']} vs {it['away']} | {it['source']} | {it['predicted']} | {it['note'][:60]}")
    print(f"共 {len(data['items'])} 场 → {store_path(args.date)}")
    return 0


def load_model(path: Path) -> dict:
    """从 model.py 的文本输出里抠「综合 λ」与「胜平负 模型/市场」，按主队中文名索引。"""
    out: dict = {}
    if not path.exists():
        return out
    cur = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r"(\S+)\s+(\S+)\s+vs\s+(\S+)\s+\[", line)
        if m and "id=" in line:
            cur = {"home": m.group(2), "away": m.group(3)}
            out[m.group(2)] = cur
            continue
        if not cur:
            continue
        lam = re.search(r"综合 λ\s+([\d.]+)\s+([\d.]+)", line)
        if lam:
            cur["lam"] = (float(lam.group(1)), float(lam.group(2)))
            continue
        if "让球" in line:  # 让球块的行长得一样，别让它盖掉胜平负
            continue
        w = re.search(r"模型\s+([\d.]+)%\s*/\s*([\d.]+)%\s*/\s*([\d.]+)%\s+市场\(去水\)\s+([\d.]+)%\s*/\s*([\d.]+)%\s*/\s*([\d.]+)%", line)
        if w:
            cur["model"] = tuple(float(w.group(i)) for i in (1, 2, 3))
            cur["market"] = tuple(float(w.group(i)) for i in (4, 5, 6))
    return out


def _dir_from_score(pred: str) -> str:
    m = re.search(r"(\d)\s*[-–]\s*(\d)", pred or "")
    if not m:
        return ""
    a, b = int(m.group(1)), int(m.group(2))
    return "主胜" if a > b else ("平" if a == b else "客胜")


def cmd_key(args) -> int:
    """写入/查看 API-Football key（落 state/api-keys.json，已 gitignore）。"""
    if args.set:
        val = args.set.strip()
        if val == "-":
            val = sys.stdin.read().strip()
            if not val:
                print("stdin 是空的：Get-Clipboard | python scripts/ext_predict.py key --set -")
                return 2
        KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
        d = {}
        if KEYS_FILE.exists():
            try:
                d = json.loads(KEYS_FILE.read_text(encoding="utf-8"))
            except Exception:
                d = {}
        d["api_football"] = val
        KEYS_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已写入 {KEYS_FILE.relative_to(ROOT)}（key 长度 {len(d['api_football'])}）")
        return 0
    k = api_key()
    if not k:
        print("没有 key。写一个：python scripts/ext_predict.py key --set 你的KEY")
        return 1
    src = "环境变量" if (__import__("os").environ.get("API_FOOTBALL_KEY") or "").strip() else "state/api-keys.json"
    print(f"来源：{src}　长度 {len(k)}　前 4 位 {k[:4]}…（不回显全量）")
    try:
        fx = af_fixtures(dt.date.today().strftime("%Y%m%d"), force=True)
        print(f"试连成功：今天赛程 {len(fx)} 场")
    except RuntimeError as e:
        print(f"试连失败：{e}")
        return 1
    return 0


def cmd_compare(args) -> int:
    """多源互相对照：主记录（SM/人工）+ `<日期>af`（API-Football）+ 模型 + 市场。"""
    date = args.date
    main = load_store(date)
    other = load_store(date + "af")
    if not other["items"]:
        print(f"没有副记录：先跑 batch --provider api-football --date {date}af")
        return 2
    model_path = Path(args.model) if args.model else None
    if model_path is None:
        cands = sorted(BATCH_DIR.glob(f"_model_{date}*.txt"))
        model_path = cands[0] if cands else None
    model = load_model(model_path) if model_path else {}
    m_map = {(x["home"], x["away"]): x for x in main["items"]}
    o_map = {(x["home"], x["away"]): x for x in other["items"]}

    def _dir(it):
        if not it:
            return ""
        return it.get("predicted_dir") or _dir_from_score(it.get("predicted") or "")

    lines = [
        "",
        "## 外部源互相对照（主记录 / API-Football / 后台模型 / 市场折算）",
        "",
        "> 两个外部源各自独立给一场，比单一源更能看出「这场的判断是不是有共识」。",
        "",
        "| 对阵 | 主记录（Sports Mole 等） | API-Football | 后台模型 主/平/客 | 市场折算 主/平/客 | 模型最靠前｜市场最靠前 | 方向一致性 |",
        "|:--|:--|:--|:--|:--|:--|:--|",
    ]
    for key in [(x["home"], x["away"]) for x in other["items"]]:
        s, a = m_map.get(key, {}), o_map.get(key, {})
        mm = model.get(key[0], {})
        mdl, mkt = mm.get("model"), mm.get("market")

        def fmt(t):
            return " / ".join(f"{x:.1f}" for x in t) if t else "—"

        top = ("主胜", "平", "客胜")[max(range(3), key=lambda k: mdl[k])] if mdl else ""
        mtop = ("主胜", "平", "客胜")[max(range(3), key=lambda k: mkt[k])] if mkt else ""
        ds, da = _dir(s), _dir(a)
        sm_show = s.get("predicted") or (ds or "—")
        af_show = f"{da} {a.get('hit_prob', 0):.0f}%" if da else "—"
        agree = []
        if ds and top:
            agree.append("主记录=模型" if ds == top else "主记录≠模型")
        if da and top:
            agree.append("AF=模型" if da == top else "AF≠模型")
        lines.append(
            f"| {key[0]} vs {key[1]} | {sm_show} | {af_show} | {fmt(mdl)} | {fmt(mkt)} | "
            f"{top or '—'}｜{mtop or '—'} | {'、'.join(agree) or '—'} |")
    text = "\n".join(lines) + "\n"
    p = ROOT / "📝文章" / date / "_外部预测对照.md"
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    if "## 外部源互相对照" in old:
        old = old.split("## 外部源互相对照")[0].rstrip() + "\n"
    p.write_text(old + text, encoding="utf-8")
    print(text)
    print(f"→ 已写入 {p}")
    return 0


def cmd_report(args) -> int:
    data = load_store(args.date)
    if not data["items"]:
        print("本批没有外部预测记录，先跑 match/batch")
        return 2
    model_path = Path(args.model) if args.model else None
    if model_path is None:
        cands = sorted(BATCH_DIR.glob(f"_model_{args.date}*.txt"))
        model_path = cands[0] if cands else None
    model = load_model(model_path) if model_path else {}
    out_dir = ROOT / "📝文章" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# 外部预测对照（{args.date}）",
        "",
        "> 外部预测只作第三方参照，不改模型结论；引用时写「公开赛前预报」这类中性说法，不带操作建议。",
        "",
        "| 对阵 | 来源 | 外部预测 | 外部方向 | 后台模型 主/平/客 | 市场折算 主/平/客 | 模型最靠前 | 摘要 |",
        "|:--|:--|:--|:--|:--|:--|:--|:--|",
    ]
    flags = []
    for it in data["items"]:
        mm = model.get(it["home"], {})
        pred = it.get("predicted") or ""
        d = _dir_from_score(pred) or (it.get("predicted_dir") or "")
        mdl = mm.get("model")
        mkt = mm.get("market")
        top = ""
        if mdl:
            i = max(range(3), key=lambda k: mdl[k])
            top = ("主胜", "平", "客胜")[i] + f" {mdl[i]:.1f}%"
            if d and d != ("主胜", "平", "客胜")[i]:
                flags.append(f"{it['home']}（外部 {d} / 模型 {top}）")
        fmt = lambda t: " / ".join(f"{x:.1f}" for x in t) if t else "—"
        note = (it.get("note") or "").replace("|", "/")[:60]
        prov = {"sportsmole": "Sports Mole", "sportskeeda": "Sportskeeda",
                "api-football": "API-Football", "manual": "人工摘录"}.get(
            it.get("provider") or it.get("source") or "", "—")
        if it.get("stale_risk"):
            prov += " ⚠️往轮"
        show = pred
        if not show and d:
            hp = it.get("hit_prob") or 0
            show = f"{d}（{hp:.0f}%）" if hp else d
        lines.append(f"| {it['home']} vs {it['away']} | {prov} | {show or '—'} | {d or '—'} | {fmt(mdl)} | {fmt(mkt)} | {top or '—'} | {note} |")
    if flags:
        lines += ["", "**方向不一致（值得单独读的场次）**：" + "；".join(flags)]
    lines += ["", f"抓取时间：{dt.date.today().isoformat()}"
              + (f"　模型文本：`{model_path.relative_to(ROOT).as_posix()}`" if model_path else ""), ""]
    p = out_dir / "_外部预测对照.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"→ {p}")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="外部预测对照层（Sports Mole 直连 + 人工兜底）")
    ap.add_argument("--date", default=dt.date.today().strftime("%Y%m%d"), help="批次日期 YYYYMMDD")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("index", help="抓预测索引")
    s.add_argument("--force", action="store_true")
    s.add_argument("--limit", type=int, default=15)
    s.set_defaults(func=cmd_index)
    s = sub.add_parser("match", help="抓单场（--provider auto 先 Sports Mole 再 Sportskeeda）")
    s.add_argument("home")
    s.add_argument("away")
    s.add_argument("--manual", default=None)
    s.add_argument("--league", default="", help="英超/西甲/法甲/意甲/德甲（Sportskeeda 需要）")
    s.add_argument("--provider", default="auto",
                   choices=["auto", "sportsmole", "api-football", "af", "sportskeeda"])
    s.set_defaults(func=cmd_match)
    s = sub.add_parser("batch", help="批量（每行：主队 客队 [联赛]）")
    s.add_argument("--file", required=True)
    s.add_argument("--provider", default="auto",
                   choices=["auto", "sportsmole", "api-football", "af", "sportskeeda"])
    s.set_defaults(func=cmd_batch)
    s = sub.add_parser("doctor", help="体检：哪个源能用/要 key/被墙")
    s.set_defaults(func=cmd_doctor)
    s = sub.add_parser("key", help="写入/查看 API-Football key")
    s.add_argument("--set", default=None, help="写入 key（落 state/api-keys.json，已 gitignore）")
    s.set_defaults(func=cmd_key)
    s = sub.add_parser("show", help="打印本批记录")
    s.set_defaults(func=cmd_show)
    s = sub.add_parser("compare", help="多源互相对照（主记录 + <日期>af + 模型 + 市场）")
    s.add_argument("--model", default=None)
    s.set_defaults(func=cmd_compare)
    s = sub.add_parser("report", help="生成 md 对照表")
    s.add_argument("--model", default=None, help="模型文本路径（默认自动找 state/_model_<日期>*.txt）")
    s.set_defaults(func=cmd_report)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
