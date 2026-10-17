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
RAW = ROOT / "state" / "_ext_raw"
ALIASES = ROOT / "database" / "config" / "team_aliases.json"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
SM_INDEX = "https://www.sportsmole.co.uk/football/predictions/"

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
    return ROOT / "state" / f"_ext_{stamp}.json"


def load_store(stamp: str) -> dict:
    p = store_path(stamp)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"date": stamp, "items": []}


def save_store(data: dict) -> Path:
    p = store_path(data["date"])
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def add_item(home: str, away: str, row: dict | None, parsed: dict, stamp: str, manual: str | None = None) -> dict:
    data = load_store(stamp)
    item = {
        "home": home,
        "away": away,
        "source": "manual" if manual else "sportsmole",
        "predicted": manual or (parsed.get("predicted") or ""),
        "note": parsed.get("note", ""),
        "lineup": parsed.get("lineup", ""),
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


def cmd_match(args) -> int:
    aliases = load_aliases()
    idx = fetch_index()
    row = find_preview(args.home, args.away, aliases, idx)
    if not row:
        print(f"未找到 Sports Mole 预测页：{args.home} vs {args.away}")
        print("  可能原因：未开赛太早/索引未收录/队名没在 team_aliases.json 里")
        print("  兜底：把外部预测手写成 --manual \"埃弗顿 2-1 切尔西\"")
        return 2
    html = _get(row["href"], RAW / (re.sub(r"[^a-z0-9]+", "_", row["href"].lower())[-80:] + ".html"))
    parsed = parse_preview(html)
    item = add_item(args.home, args.away, row, parsed, args.date, manual=None)
    print(json.dumps(item, ensure_ascii=False, indent=2))
    return 0


def cmd_batch(args) -> int:
    lines = [l.strip() for l in Path(args.file).read_text(encoding="utf-8").splitlines() if l.strip()]
    aliases = load_aliases()
    idx = fetch_index()
    for line in lines:
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            continue
        home, away = parts[0], parts[1]
        row = find_preview(home, away, aliases, idx)
        if not row:
            print(f"[MISS] {home} vs {away}")
            continue
        html = _get(row["href"], RAW / (re.sub(r"[^a-z0-9]+", "_", row["href"].lower())[-80:] + ".html"))
        parsed = parse_preview(html)
        add_item(home, away, row, parsed, args.date)
        print(f"[OK]   {home} vs {away} → {parsed.get('predicted', '?')}")
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


def cmd_report(args) -> int:
    data = load_store(args.date)
    if not data["items"]:
        print("本批没有外部预测记录，先跑 match/batch")
        return 2
    model_path = Path(args.model) if args.model else None
    if model_path is None:
        cands = sorted(ROOT.joinpath("state").glob(f"_model_{args.date}*.txt"))
        model_path = cands[0] if cands else None
    model = load_model(model_path) if model_path else {}
    out_dir = ROOT / "📝文章" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# 外部预测对照（{args.date}）",
        "",
        "> 外部预测只作第三方参照，不改模型结论；引用时写「公开赛前预报」这类中性说法，不带操作建议。",
        "",
        "| 对阵 | 外部预测 | 外部方向 | 后台模型 主/平/客 | 市场折算 主/平/客 | 模型最靠前 | 摘要 |",
        "|:--|:--|:--|:--|:--|:--|:--|",
    ]
    flags = []
    for it in data["items"]:
        mm = model.get(it["home"], {})
        pred = it.get("predicted") or ""
        d = _dir_from_score(pred)
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
        lines.append(f"| {it['home']} vs {it['away']} | {pred} | {d or '—'} | {fmt(mdl)} | {fmt(mkt)} | {top or '—'} | {note} |")
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
    s = sub.add_parser("match", help="抓单场")
    s.add_argument("home")
    s.add_argument("away")
    s.add_argument("--manual", default=None)
    s.set_defaults(func=cmd_match)
    s = sub.add_parser("batch", help="批量（每行：主队 客队）")
    s.add_argument("--file", required=True)
    s.set_defaults(func=cmd_batch)
    s = sub.add_parser("show", help="打印本批记录")
    s.set_defaults(func=cmd_show)
    s = sub.add_parser("report", help="生成 md 对照表")
    s.add_argument("--model", default=None, help="模型文本路径（默认自动找 state/_model_<日期>*.txt）")
    s.set_defaults(func=cmd_report)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
