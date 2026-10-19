#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""media_intel.py — 外媒与 AI 预测采集（2026-10-20 建，接 DeepSeek Search/Fetch）

为什么建：2026-10-19 卡片的「媒体」行是人工读 7 场深报抄下来的，深报没覆盖的场次只能写
「暂无前瞻源」。这套脚本把「搜 → 抓 → 落单」自动化，产出 `_media_<date>.md`，写卡片和
头条稿时直接引用。

取数层是 `scripts/ds_search.py`（DeepSeek 自研搜索，Search/Fetch 各 5 元/1000 次）。
队名要靠 `database/config/team_aliases.json` 的 `en` 转英文再搜，中文队名搜外媒基本无效。

用法
    python -X utf8 scripts/media_intel.py --date 20261021                    # 默认 2 搜/场
    python -X utf8 scripts/media_intel.py --date 20261021 --injuries         # 加一轮伤停
    python -X utf8 scripts/media_intel.py --date 20261021 --limit 3 --fetch-top 1
    python -X utf8 scripts/media_intel.py --date 20261021 --dry              # 只打印检索词

产出
    state/intel/<date>/_media_<date>.json   原始结果（含 url/summary/date/authority/score）
    state/intel/<date>/_media_<date>.md     人读版：每场来源表 + 倾向线索 + 比分线索

⚠️ 这是**内部**情报单：里面有外媒原始预测比分与倾向词。公开稿按 R41 转写——不当结论引用、
不加比分串、不写百分比；卡片上的「媒体」行只写「几家、几家给哪边」。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ds_search  # noqa: E402

STATE = ROOT / "state"
INTEL = STATE / "intel"
ALIASES = ROOT / "database" / "config" / "team_aliases.json"

MIN_SCORE = 1.2          # rerank_score 门槛，低于此基本是噪音
PER_MATCH_KEEP = 5       # 每场最多留几条源
COST_PER_CALL = 0.005    # 元/次（5 元 / 1000 次）

# 倾向词（英/中）：只做「线索」，不下结论
HOME_WORDS = ("back the home", "home win", "favour the home", "favor the home", "home side should",
              "hosts to win", "hosts should", "主队占优", "看好主队", "主胜",
              "主场优势", "占据主动", "主场作战", "压制对手", "主场不败")
AWAY_WORDS = ("back the away", "away win", "favour the away", "favor the away", "visitors to win",
              "visitors should", "away side should", "客队占优", "看好客队", "客胜",
              "客场作战", "客场反击", "客队有机会", "客场取分")
DRAW_WORDS = ("draw is likely", "could end level", "share the spoils", "draw looks",
              "平局", "握手言和", "五五开")
GOALS_WORDS = ("over 2.5", "high-scoring", "goals at both ends", "both teams to score",
               "大球", "双方进球", "进球多")

SCORE_PAT = re.compile(
    r"(?:we say|prediction[:\s]|predicted score|tips?[:\s]|预计|预测|比分)[^\d\n]{0,14}?"
    r"(\d{1,2})\s*[-–:比]\s*(\d{1,2})", re.I)


def load_aliases() -> dict:
    try:
        return json.loads(ALIASES.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def en_of(name: str, aliases: dict) -> str:
    row = aliases.get(name) or {}
    return (row.get("en") or row.get("af") or name).strip()


def load_matches(date_tag: str) -> dict:
    p = STATE / "batch" / f"_matches_{date_tag}.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    raise SystemExit(f"缺 {p}；先跑 python -X utf8 scripts/prematch_intel.py --date {date_tag}")


def hit_words(text: str, words: tuple[str, ...]) -> list[str]:
    low = (text or "").lower()
    return [w for w in words if w.lower() in low]


def scan_scores(text: str) -> list[str]:
    out = []
    for m in SCORE_PAT.finditer(text or ""):
        a, b = m.group(1), m.group(2)
        if int(a) <= 9 and int(b) <= 9:
            out.append(f"{a} 比 {b}")
    seen = []
    for s in out:
        if s not in seen:
            seen.append(s)
    return seen[:3]


def collect(no: str, row: dict, aliases: dict, count: int, injuries: bool,
            fetch_top: int, verbose: bool = True) -> dict:
    home, away = row.get("home", ""), row.get("away", "")
    he, ae = en_of(home, aliases), en_of(away, aliases)
    queries = [
        ("preview", f'"{he} vs {ae}" preview prediction lang:en'),
        ("zh", f"{home} {away} 前瞻 预测 lang:zh"),
    ]
    if injuries:
        queries.append(("injury", f'"{he}" "{ae}" team news injury lang:en'))

    sources: list[dict] = []
    seen_urls: set[str] = set()
    for kind, q in queries:
        if verbose:
            print(f"  · {no} {kind}: {q}")
        try:
            res = ds_search.search(q, count=count, ori_question=f"{home} vs {away}")
        except SystemExit as exc:
            raise SystemExit(f"检索失败：{exc}")
        for r in res:
            url = r.get("url") or ""
            if not url or url in seen_urls:
                continue
            if (r.get("rerank_score") or 0) < MIN_SCORE:
                continue
            seen_urls.add(url)
            text = f"{r.get('title') or ''} {r.get('summary') or r.get('snippet') or ''}"
            tag, hits, neg = side_of(text)
            sources.append({
                "kind": kind,
                "title": r.get("title"),
                "url": url,
                "site": r.get("site_name"),
                "date": r.get("date"),
                "authority": r.get("authority"),
                "score": r.get("rerank_score"),
                "summary": r.get("summary") or r.get("snippet") or "",
                "side": tag,
                "neg": neg,
                "hits": hits[:3],
                "scores": scan_scores(text),
            })
    sources.sort(key=lambda s: -(s.get("score") or 0))
    sources = sources[:PER_MATCH_KEEP]

    # 只对「预测型」源抓正文（新闻站抓正文收益小，还多花一次钱）
    fetched = 0
    if fetch_top:
        for src in sources:
            if fetched >= fetch_top:
                break
            low = (src.get("url") or "").lower()
            if not any(k in low for k in ("prediction", "preview", "sportsmole", "sportskeeda")):
                continue
            try:
                page = ds_search.fetch(src["url"])
                body = (page.get("content") or "").strip()
                if body:
                    src["fetch_ok"] = True
                    src["fetch_head"] = body[:700]
                    src["scores"] = list(dict.fromkeys(src["scores"] + scan_scores(body)))[:3]
                    fetched += 1
            except SystemExit:
                src["fetch_ok"] = False

    cover = {"n": len(sources), "auth3": sum(1 for x in sources if (x.get("authority") or 0) >= 3),
             "zh": sum(1 for x in sources if re.search(r"[一-鿿]", x.get("summary") or "")),
             "home_mentions": sum(1 for x in sources if home and home in (x.get("summary") or "")),
             "away_mentions": sum(1 for x in sources if away and away in (x.get("summary") or ""))}
    tally = {"home": 0, "away": 0, "draw": 0, "goals": 0, "none": 0, "neg": 0}
    for src in sources:
        tally[src.get("side") or "none"] += 1
        if src.get("side") and src.get("neg"):
            tally["neg"] += 1
    scores: list[str] = []
    for src in sources:
        for sc in src.get("scores") or []:
            if sc not in scores:
                scores.append(sc)
    return {"no": no, "league": row.get("league"), "home": home, "away": away,
            "home_en": he, "away_en": ae, "queries": [q for _, q in queries],
            "sources": sources, "tally": tally, "cover": cover, "scores": scores[:3],
            "fetched": fetched}


NEG_WORDS = ("unlikely", "not expected", "no chance", "doubt", "ruled out", "improbable",
             "难说", "不太可能", "未必", "存疑")


def side_of(text: str) -> tuple:
    """把一条源判成 home/away/draw/goals/None —— 只给线索，不当结论。

    优先级：主 > 客 > 平 > 进球（一条源只算一个方向，免得计数重复）。
    带否定词（unlikely / doubt …）的句子容易把「说客队赢不了」记成「偏客队」，
    所以第三项返回 neg 标记，落单时单列成「疑似否定，需人工核对」。
    """
    low = (text or "").lower()
    neg = any(w in low for w in NEG_WORDS)
    for tag, words in (("home", HOME_WORDS), ("away", AWAY_WORDS),
                       ("draw", DRAW_WORDS), ("goals", GOALS_WORDS)):
        hits = hit_words(text, words)
        if hits:
            return tag, hits, neg
    return None, [], neg


def to_md(items: list[dict], date_tag: str, calls: int) -> str:
    L = [f"# 外媒与 AI 预测 · {date_tag[:4]}-{date_tag[4:6]}-{date_tag[6:]}", ""]
    L.append(f"> 检索 {calls} 次（约 {calls * COST_PER_CALL:.2f} 元）。"
             "**内部情报**：原始预测倾向与比分只在这里，公开稿按 R41 转写，不当结论引用、不写比分串与百分比。")
    L.append("")
    for it in items:
        L.append(f"## {it['no']} {it['league']} · {it['home']} vs {it['away']}")
        L.append("")
        if not it["sources"]:
            L.append("_暂无前瞻源（检索为空）——卡片写「暂无前瞻源」，不要编。_")
            L.append("")
            continue
        L.append("| # | 站点 | 日期 | 权威 | 分数 | 标题 |")
        L.append("|:--|:--|:--|:--|:--|:--|")
        for i, s in enumerate(it["sources"], 1):
            date = (s.get("date") or "")[:10]
            site = (s.get("site") or "—").replace("|", "/")
            title = (s.get("title") or "").replace("|", "/")[:58]
            L.append(f"| {i} | {site} | {date} | {s.get('authority')} | {s.get('score')} | {title} |")
        L.append("")
        for i, s in enumerate(it["sources"], 1):
            sm = (s.get("summary") or "").replace("\n", " ")[:220]
            L.append(f"- **[{i}]** {sm} ⋯ [原文]({s['url']})")
        t = it["tally"]
        L.append("")
        L.append(f"**线索计数**（{len(it['sources'])} 条源：主 {t['home']} / 客 {t['away']} / "
                 f"平 {t['draw']} / 进球 {t['goals']} / 无信号 {t['none']}"
                 + (f" / 疑似否定 {t['neg']}" if t['neg'] else "") + "）")
        c = it.get("cover") or {}
        if c.get("n"):
            L.append(f"**覆盖度**：{c['n']} 家（权威 3 以上 {c.get('auth3', 0)} 家，中文源 {c.get('zh', 0)} 家，"
                     f"提主队 {c.get('home_mentions', 0)} 家 / 提客队 {c.get('away_mentions', 0)} 家）")
        for i, src in enumerate(it["sources"], 1):
            if src.get("side"):
                mark = "（疑似否定，请核原文）" if src.get("neg") else ""
                L.append(f"  - [{i}] {src['side']}{mark} ← {'/'.join(src['hits'])}")
        if it["scores"]:
            L.append("**比分线索**（内部参考，公开稿不得照搬）：" + "；".join(it["scores"]))
        if it.get("fetched"):
            L.append(f"（已抓正文 {it['fetched']} 篇）")
        for i, src in enumerate(it["sources"], 1):
            if src.get("fetch_head"):
                L.append("")
                L.append(f"**正文 [{i}]** {src['fetch_head']} ⋯ [原文]({src['url']})")
        L.append("")
    return "\n".join(L)


def media_row(it: dict) -> str:
    """cv 的「媒体」行：只写家数与方向分布，不写谁赢。"""
    t = it.get("tally") or {}
    n = len(it.get("sources") or [])
    if not n:
        return "暂无前瞻源"
    c = it.get("cover") or {}
    bits = [f"{n} 家"]
    if t.get("home"):
        bits.append(f"主 {t['home']}")
    if t.get("away"):
        bits.append(f"客 {t['away']}")
    if t.get("draw"):
        bits.append(f"平 {t['draw']}")
    if t.get("goals"):
        bits.append(f"进球 {t['goals']}")
    if c.get("auth3"):
        bits.append(f"权威 3 以上 {c['auth3']} 家")
    if not any(t.get(k) for k in ("home", "away", "draw", "goals")):
        bits.append("无明确倾向")
    row = " · ".join(bits)
    if t.get("neg"):
        row += f"（{t['neg']} 条疑似否定）"
    return row


def apply_cards(cards_path: str, payload: dict) -> int:
    import json
    with open(cards_path, "r", encoding="utf-8-sig") as f:
        cards = json.load(f)
    by_no = {it["no"]: it for it in payload.get("items", [])}
    hit = 0
    for m in cards.get("matches", []):
        it = by_no.get(m.get("no"))
        if not it:
            continue
        cv = m.get("cv") or []
        row = ["媒体", media_row(it)]
        cv = [row] + [r for r in cv if r and r[0] != "媒体"]
        m["cv"] = cv
        hit += 1
    with open(cards_path, "w", encoding="utf-8", newline="") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    return hit


def main() -> None:
    ap = argparse.ArgumentParser(description="外媒与 AI 预测采集（DeepSeek Search/Fetch）")
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 场（0=全部）")
    ap.add_argument("--count", type=int, default=8, help="每次检索返回条数（默认 8，单价不变）")
    ap.add_argument("--injuries", action="store_true", help="额外检索一轮伤停/team news")
    ap.add_argument("--fetch-top", type=int, default=0, help="预留：抓取正文条数（当前只做探测）")
    ap.add_argument("--only", default="", help="只跑这些场次号，逗号分隔，如 周二001,周二006")
    ap.add_argument("--apply-cards", default="",
                    help="把线索计数回填到该 cards.json 每场的 cv[0]（媒体行），技术/综合不动")
    ap.add_argument("--dry", action="store_true", help="只打印检索计划，不联网")
    a = ap.parse_args()

    aliases = load_aliases()
    rows = load_matches(a.date)
    wanted = {x.strip() for x in a.only.split(",") if x.strip()}
    items_key = sorted(rows.items(), key=lambda kv: (kv[1].get("no") or "", kv[0]))
    if wanted:
        items_key = [kv for kv in items_key if kv[1].get("no") in wanted]
    if a.limit:
        items_key = items_key[: a.limit]

    print(f"外媒情报 · {a.date} · {len(items_key)} 场 · 每场 "
          f"{2 + (1 if a.injuries else 0)} 次检索")
    if a.dry:
        for _mid, row in items_key:
            he, ae = en_of(row.get("home", ""), aliases), en_of(row.get("away", ""), aliases)
            print(f"  {row.get('no')} {row.get('home')} vs {row.get('away')}")
            print(f'    "{he} vs {ae}" preview prediction lang:en')
            print(f'    {row.get("home")} {row.get("away")} 前瞻 预测 lang:zh')
            if a.injuries:
                print(f'    "{he}" "{ae}" team news injury lang:en')
        return

    items, calls = [], 0
    for _mid, row in items_key:
        it = collect(row.get("no", ""), row, aliases, a.count, a.injuries, a.fetch_top)
        calls += len(it["queries"])
        items.append(it)
        print(f"  ✅ {it['no']} {it['home']} vs {it['away']}：{len(it['sources'])} 条源")

    out_dir = INTEL / a.date
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"_media_{a.date}.json").write_text(
        json.dumps({"date": a.date, "fetched_at": dt.datetime.now().isoformat(timespec="seconds"),
                    "calls": calls, "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    md_p = out_dir / f"_media_{a.date}.md"
    md_p.write_text(to_md(items, a.date, calls), encoding="utf-8")
    print(f"\n📝 {md_p.relative_to(ROOT)}")
    print(f"   检索 {calls} 次 ≈ {calls * COST_PER_CALL:.2f} 元")

    if a.apply_cards:
        payload = {"items": items}
        n = apply_cards(a.apply_cards, payload)
        print(f"   已回填 cv 媒体行：{n} 场 → {a.apply_cards}")


if __name__ == "__main__":
    main()
