# -*- coding: utf-8 -*-
"""澳客网「竞彩数据」采集：必发盈亏 / 胜负指数 / 差异分析 / 最新伤停 / 凯利方差

为什么单独一个脚本
------------------
竞彩官方盘与第三方指数是两套东西：竞彩给「市场怎么定」，这一层给「钱往哪边压、庄家怕谁」。
它**不参与模型 λ**，只作为研判层的交叉证据（R41：公开稿不出现这些词）。

数据源（2026-10-20 实测：gb2312 页面，需 Referer，直连 urllib 可抓；ds_search.fetch 也能抓文本）
    https://www.okooo.com/jingcai/shuju/betfa/    必发盈亏（模拟盈亏 / 冷热 / 市场指数）
    https://www.okooo.com/jingcai/shuju/zhishu/   胜负指数（初始 / 最新 三向）
    https://www.okooo.com/jingcai/shuju/chayi/    差异分析（澳客人气比 vs 最新概率）
    https://www.okooo.com/jingcai/shuju/injured/  最新伤停（缺阵名单 + 原因）
    https://www.okooo.com/jingcai/shuju/peilv/    凯利方差（各公司凯利差平方）
备注：`/jingcai/shuju/<x>/dqjc/` 与不带 dqjc 等价；部分路径缺 Referer 会 405。
必发官网 bifaw.com 也能抓，但主页只吐两场、且无队名，**没有可用的比赛页 URL 规律** → 走澳客。

用法
    python -X utf8 scripts/okooo_intel.py --date 20261021
    python -X utf8 scripts/okooo_intel.py --date 20261021 --only 周三011 周三010
    python -X utf8 scripts/okooo_intel.py --date 20261021 --raw      # 只落原始 HTML，不解析
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTEL = ROOT / "state" / "intel"
BASE = "https://www.okooo.com"

PAGES = {
    "betfa": "/jingcai/shuju/betfa/",
    "zhishu": "/jingcai/shuju/zhishu/",
    "chayi": "/jingcai/shuju/chayi/",
    "injured": "/jingcai/shuju/injured/",
    "kelly": "/jingcai/shuju/peilv/",
}

UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"),
    "Referer": BASE + "/jingcai/shuju/betfa/",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
NO_RE = re.compile(r"周[一二三四五六日]\d{2,3}")


def fetch(path: str) -> str:
    req = urllib.request.Request(BASE + path, headers=UA)
    try:
        resp = urllib.request.urlopen(req, timeout=30)  # noqa: S310
    except urllib.error.URLError as exc:
        raise SystemExit(f"抓取失败 {path}：{exc}") from None
    with resp as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
    return raw.decode("gbk", "ignore")


def txt(s: str) -> str:
    s = TAG_RE.sub(" ", s or "")
    s = s.replace("&nbsp;", " ").replace("&darr;", "").replace("&uarr;", "")
    s = s.replace("&amp;", "&").replace("&permil;", "‰")
    return WS_RE.sub(" ", s).strip()


def blocks(html: str):
    """按比赛切块：每个 `magazineDateTit` 头切到下一个头（一页含多场）。"""
    marks = [m.start() for m in re.finditer(r'<div class="[^"]*magazineDateTit[^"]*"', html)]
    out = []
    for i, pos in enumerate(marks):
        end = marks[i + 1] if i + 1 < len(marks) else len(html)
        seg = html[pos:end]
        head_end = seg.find("<table")
        head = seg[:head_end] if head_end > 0 else seg[:2000]
        no = NO_RE.search(head)
        if not no:
            continue
        bs = [txt(x) for x in re.findall(r"<b>(.*?)</b>", head, re.S)]
        names = [txt(x) for x in re.findall(r"<span>(.*?)</span>", head, re.S) if txt(x)]
        away = [txt(x) for x in re.findall(r"<b>(.*?)</b>", head, re.S)]
        rows = []
        for r in re.findall(r"<tr[^>]*>(.*?)</tr>", seg, re.S):
            cells = [txt(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
            if cells:
                rows.append(cells)
        out.append({"no": no.group(0), "league": bs[1] if len(bs) > 1 else "",
                    "kick": bs[2] if len(bs) > 2 else "",
                    "home": names[0] if names else "",
                    "away": away[-1] if len(away) > 2 else (names[1] if len(names) > 1 else ""),
                    "rows": rows})
    return out


def clean_company(s: str) -> str:
    return s.replace("!", "").replace("#", "").strip()


def num(s: str):
    s = (s or "").replace(",", "").replace("%", "").replace("‰", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# 各页解析
# --------------------------------------------------------------------------- #
def opt_of(label: str):
    """把 主胜/胜、平局/平、客胜/负 归一成三向键。"""
    t = (label or "").strip()
    if t.startswith(("主胜", "胜")):
        return "主胜"
    if t.startswith(("平局", "平")):
        return "平局"
    if t.startswith(("客胜", "负")):
        return "客胜"
    return None


def parse_betfa(html: str) -> dict:
    """必发盈亏：成交额 / 冷热 / 市场指数 / 必发比例 / 99家概率 / 模拟盈亏。"""
    data = {}
    for b in blocks(html):
        got = {}
        for r in b["rows"]:
            key = opt_of(r[0]) if r else None
            if not key:
                continue
            # 列：选项|买家挂牌|价位|卖家挂牌|价位|成交额|冷热|市场指数|必发赔率|必发比例|99家赔率|99家概率|竞彩比例|模拟盈亏
            cells = r + [""] * (14 - len(r))
            got[key] = {
                "volume": num(cells[5]),
                "hot": num(cells[6]),
                "market_idx": num(cells[7]),
                "bf_odds": num(cells[8]),
                "bf_ratio": num(cells[9]),
                "avg_odds": num(cells[10]),
                "avg_prob": num(cells[11]),
                "pnl": num(cells[13]),
            }
        if got:
            data[b["no"]] = {"league": b["league"], "kick": b["kick"],
                             "home": b["home"], "away": b["away"], "odds": got}
    return data


def parse_zhishu(html: str) -> dict:
    """胜负指数：初始 / 最新 三向（0–1 附近的小数）。编号可能不在第一列，逐格找。"""
    data = {}
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        cells = [txt(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if len(cells) < 12:
            continue
        hit = next((NO_RE.search(c) for c in cells if NO_RE.search(c or "")), None)
        if not hit:
            continue
        vals = [num(x) for x in cells[6:12]]
        if any(v is None for v in vals):
            continue
        data[hit.group(0)] = {"league": cells[1], "kick": cells[2], "home": cells[3], "away": cells[5],
                              "init": vals[:3], "latest": vals[3:]}
    return data


def parse_chayi(html: str) -> dict:
    """差异分析：澳客人气比 vs 最新概率，差异绝对值 + 小澳提点。"""
    data = {}
    for b in blocks(html):
        got, tip = {}, ""
        for r in b["rows"]:
            key = opt_of(r[0]) if r else None
            if not key:
                continue
            cells = r + [""] * (7 - len(r))
            got[key] = {
                "popularity": num(cells[1]),
                "jc_odds": num(cells[2]),
                "prob": num(cells[3]),
                "diff": num(cells[4]),
            }
            if len(cells) > 5 and cells[5] and not tip:
                tip = cells[5]
        if got:
            data[b["no"]] = {"home": b["home"], "away": b["away"], "items": got, "tip": tip}
    return data


def parse_injured(html: str) -> dict:
    """最新伤停：分开主队 / 客队（页面用 float_l / float_r 两个 injuredBox 区分）。"""
    data = {}
    marks = [m.start() for m in re.finditer(r'<div class="[^"]*magazineDateTit[^"]*"', html)]
    for i, pos in enumerate(marks):
        end = marks[i + 1] if i + 1 < len(marks) else len(html)
        seg = html[pos:end]
        head = seg[:seg.find("<table")] if seg.find("<table") > 0 else seg[:2000]
        no = NO_RE.search(head)
        if not no:
            continue
        bs = [txt(x) for x in re.findall(r"<b>(.*?)</b>", head, re.S)]
        names = [txt(x) for x in re.findall(r"<span>(.*?)</span>", head, re.S) if txt(x)]
        away = [txt(x) for x in re.findall(r"<b>(.*?)</b>", head, re.S)]
        home_n = names[0] if names else ""
        away_n = away[-1] if len(away) > 2 else (names[1] if len(names) > 1 else "")

        boxes = [(m2.start(), m2.group(1)) for m2 in
                 re.finditer(r'<div class="([^"]*injuredBox[^"]*)"', seg)
                 if "Tit" not in m2.group(1)]
        parts = {}
        for idx, (pos2, cls) in enumerate(boxes):
            nxt = boxes[idx + 1][0] if idx + 1 < len(boxes) else len(seg)
            side = "away" if ("float_r" in cls or "injuredBox_r" in cls) else "home"
            parts.setdefault(side, seg[pos2:nxt])

        got = {}
        for side, chunk in parts.items():
            players = []
            for r in re.findall(r"<tr[^>]*>(.*?)</tr>", chunk, re.S):
                cells = [txt(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
                if len(cells) < 8 or not cells[2]:
                    continue
                if "首页" in cells[2] or "末页" in cells[2] or "共 " in cells[2]:
                    continue
                players.append({"pos": cells[1], "name": cells[2],
                                "status": cells[7], "reason": cells[8] if len(cells) > 8 else ""})
            if players:
                got[side] = players
        if got:
            data[no.group(0)] = {"home": home_n, "away": away_n, "sides": got}
    return data


def parse_kelly(html: str) -> dict:
    """凯利方差：每场取各家「最新凯利差平方」，算三向均值（越小＝越一致）。"""
    data = {}
    for b in blocks(html):
        acc = {"主胜": [], "平局": [], "客胜": []}
        kelly = {"主胜": [], "平局": [], "客胜": []}
        for r in b["rows"]:
            if len(r) < 13:
                continue
            name = clean_company(r[0])
            if not name or name == "公司名":
                continue
            for i, k in enumerate(("主胜", "平局", "客胜")):
                d = num(r[12 + i]) if len(r) > 12 + i else None
                if d is not None:
                    acc[k].append(d)
                kv = num(r[9 + i]) if len(r) > 9 + i else None
                if kv is not None:
                    kelly[k].append(kv)
        got = {}
        for k in acc:
            if acc[k]:
                got[k] = {"mean_sq": round(sum(acc[k]) / len(acc[k]), 2),
                          "max_sq": max(acc[k]), "mean_kelly": round(sum(kelly[k]) / len(kelly[k]), 3) if kelly[k] else None,
                          "n": len(acc[k])}
        if got:
            data[b["no"]] = {"home": b["home"], "away": b["away"], "items": got}
    return data


PARSERS = {"betfa": parse_betfa, "zhishu": parse_zhishu, "chayi": parse_chayi,
           "injured": parse_injured, "kelly": parse_kelly}


# --------------------------------------------------------------------------- #
# 输出
# --------------------------------------------------------------------------- #
def to_md(date_tag: str, data: dict, calls: int) -> str:
    L = [f"# 澳客竞彩数据 · {date_tag}", "",
         f"> 采集 {calls} 次（约 {calls * 0.0:.2f} 元）。**内部研判层**：按 R41，公开稿不写这些词、不引数字。",
         "> 必发盈亏＝按必发成交量模拟的主流公司盈亏（负数＝该结果打出庄家亏，越大越「庄家希望」）；",
         "> 冷热指数＝该选项成交热度相对 99 家平均概率的偏离；胜负指数＝欧赔三家合成指数；",
         "> 凯利差平方越小＝各家对该结果分歧越小。",
         "> 覆盖窗口：必发/凯利/伤停/胜负指数四页只列**开赛 24h 内**的场次，差异分析页窗口更大；"
         "缺的场次临场再抓一次即可。", ""]

    betfa, zhishu, chayi, inj, kelly = (data.get(k) or {} for k in ("betfa", "zhishu", "chayi", "injured", "kelly"))
    nos = sorted(set(betfa) | set(zhishu) | set(chayi) | set(inj) | set(kelly))
    for no in nos:
        b = betfa.get(no) or {}
        z = zhishu.get(no) or {}
        c = chayi.get(no) or {}
        i = inj.get(no) or {}
        k = kelly.get(no) or {}
        home = b.get("home") or z.get("home") or c.get("home") or i.get("home") or k.get("home") or ""
        away = b.get("away") or z.get("away") or c.get("away") or i.get("away") or k.get("away") or ""
        L.append(f"## {no} {b.get('league') or z.get('league') or ''} · {home} vs {away}".replace(" ·  ", " · "))
        L.append("")
        if b.get("odds"):
            o = b["odds"]
            live = any((v or {}).get("bf_ratio") is not None for v in o.values())
            if not live:
                avg = "；".join(f"{k2} {o[k2]['avg_prob']}%" for k2 in ("主胜", "平局", "客胜")
                               if (o.get(k2) or {}).get("avg_prob") is not None)
                L.append(f"- **必发**：未开盘（赛前 24h 内才有成交）｜99 家 {avg}")
            else:
                vol = sum(v.get("volume") or 0 for v in o.values())
                L.append(f"- **必发**（总额 {vol:,.0f}）：")
                for key in ("主胜", "平局", "客胜"):
                    v = o.get(key) or {}
                    hot = f"{v['hot']:+.0f}" if v.get("hot") is not None else "—"
                    pnl = f"{v['pnl']:+,.0f}" if v.get("pnl") is not None else "—"
                    L.append(f"  - {key}：比例 {v.get('bf_ratio')}%｜99 家 {v.get('avg_prob')}%"
                             f"｜冷热 {hot}｜市场指数 {v.get('market_idx')}｜模拟盈亏 {pnl}")
        if z.get("latest"):
            L.append(f"- **胜负指数**：初 {'/'.join(f'{x:.2f}' for x in z['init'])} → "
                     f"新 {'/'.join(f'{x:.2f}' for x in z['latest'])}")
        if c.get("items"):
            bits = [f"{k2} 人气 {v['popularity']}% vs 概率 {v['prob']}%（差 {v['diff']}）"
                    for k2, v in c["items"].items() if v.get("popularity") is not None]
            L.append("- **差异分析**：" + "；".join(bits) + (f"｜提点：{c['tip']}" if c.get("tip") else ""))
        if i.get("sides"):
            for side, label in (("home", home), ("away", away)):
                ps = (i["sides"] or {}).get(side) or []
                if ps:
                    names = "；".join(f"{p['name']}（{p['pos']}）" for p in ps[:8])
                    L.append(f"- **{label} 缺阵/成疑**（{len(ps)} 人）：{names}")
        if k.get("items"):
            bits = [f"{kk} 差平方均值 {v['mean_sq']}‰（最大 {v['max_sq']}，n={v['n']}）"
                    for kk, v in k["items"].items()]
            L.append("- **凯利方差**：" + "；".join(bits))
        L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="澳客竞彩数据采集（必发盈亏/胜负指数/差异/伤停/凯利）")
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--only", nargs="*", default=[], help="只保留这些场次号，如 周三011")
    ap.add_argument("--raw", action="store_true", help="只落原始 HTML")
    ap.add_argument("--sleep", type=float, default=0.6)
    a = ap.parse_args()

    out_dir = INTEL / a.date
    raw_dir = out_dir / "_okooo_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    data, calls = {}, 0
    for key, path in PAGES.items():
        try:
            html = fetch(path)
            calls += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ⚠️ {key} 抓取失败：{exc}")
            continue
        io.open(raw_dir / f"{key}.html", "w", encoding="utf-8").write(html)
        if a.raw:
            print(f"  · {key} 原始 {len(html):,} 字符")
        else:
            try:
                data[key] = PARSERS[key](html)
            except Exception as exc:  # noqa: BLE001
                print(f"  ⚠️ {key} 解析失败：{exc}")
        time.sleep(a.sleep)

    if a.raw:
        print(f"原始 HTML → {raw_dir}")
        return

    # 默认只留本批场次（_matches_<date>.json 的键），页面本身混着周一周二
    keep_set = set(a.only)
    if not keep_set:
        mp = ROOT / "state" / "batch" / f"_matches_{a.date}.json"
        if mp.exists():
            try:
                raw = json.loads(mp.read_text(encoding="utf-8"))
                keep_set = {str(v.get("no") or k) for k, v in raw.items()}
            except Exception:  # noqa: BLE001
                keep_set = set()

    if keep_set:
        keep = keep_set
        data = {k: {no: v for no, v in (d or {}).items() if no in keep} for k, d in data.items()}

    payload = {"date": a.date, "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "calls": calls, **data}
    (out_dir / f"_okooo_{a.date}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = to_md(a.date, data, calls)
    (out_dir / f"_okooo_{a.date}.md").write_text(md, encoding="utf-8")
    nos = sorted(set().union(*[set(d or {}) for d in data.values()])) if data else []
    print(f"✅ {out_dir / f'_okooo_{a.date}.md'}｜{len(nos)} 场｜采集 {calls} 次")


if __name__ == "__main__":
    main()
