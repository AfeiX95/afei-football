# -*- coding: utf-8 -*-
"""情报抓取总入口（2026-10-20 起）：澳客指数 / 懂球帝底档 / 单场深度页。

为什么另起一个脚本
- `okooo_intel.py` 走 urllib 直连 HTML，本机 IP 反复被抓后会被阿里云 WAF 拦（返回
  16037 字节的挑战页 或 405），只能靠服务端抓取（`ds_search.fetch`）绕开。
- 服务端抓取回来的是 **Markdown**（列会被合并、空单元格会丢），所以解析逻辑必须按
  「值形态」而不是「列号」来认。

用法
    python -X utf8 scripts/intel_fetch.py --date 20261021
    python -X utf8 scripts/intel_fetch.py --date 20261021 --sources betfa,zhishu
    python -X utf8 scripts/intel_fetch.py --date 20261021 --match 1347463
    python -X utf8 scripts/intel_fetch.py --date 20261021 --league 17

产出
    state/intel/<date>/_raw/<源>.md      原始 Markdown（失败时回落到同目录旧缓存）
    state/intel/<date>/_fetch_<date>.md  汇总（含「源状态」表：抓成功/失败原因）
    state/intel/<date>/_fetch_<date>.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import ds_search  # noqa: E402

STATE = os.path.join(ROOT, "state")
INTEL = os.path.join(STATE, "intel")
BATCH = os.path.join(STATE, "batch")

NO_RE = re.compile(r"周[一二三四五六日]\d{3}")
TRIES = 3
SLEEP = 6.0
BLOCK_HINTS = ("滑动验证", "aliyun_waf", "405", "请求已被拦截")

# 竞彩指数页（服务端抓取用 .cn + /dqjc/ 后缀，实测这条路径最稳）
JINGCAI = {
    "betfa": "https://www.okooo.cn/jingcai/shuju/betfa/dqjc/",
    "zhishu": "https://www.okooo.cn/jingcai/shuju/zhishu/dqjc/",
    "pankou": "https://www.okooo.cn/jingcai/shuju/pankou/dqjc/",
    "peilv": "https://www.okooo.cn/jingcai/shuju/peilv/dqjc/",
    "chayi": "https://www.okooo.cn/jingcai/shuju/chayi/dqjc/",
    "injured": "https://www.okooo.cn/jingcai/shuju/injured/dqjc/",
    "paixu": "https://www.okooo.cn/jingcai/shuju/paixu/dqjc/",
}

# 单场深度页（澳客 id 从竞彩页里的 /soccer/match/<id>/ 链接取得；没有就手动给）
MATCH_PAGES = {
    "formation": "https://www.okooo.cn/soccer/match/{mid}/formation/",
    "sfzs": "https://www.okooo.cn/soccer/match/{mid}/sfzs/",
    "trends": "https://www.okooo.cn/soccer/match/{mid}/trends/",
    "feature": "https://www.okooo.cn/soccer/match/{mid}/feature/",
}

LEAGUE_PAGES = {
    "league_injured": "https://www.okooo.cn/soccer/league/{lid}/injured/",
}


# --------------------------------------------------------------------------- #
# 抓取（带重试 + 落缓存）
# --------------------------------------------------------------------------- #
def raw_dir(date_tag: str) -> str:
    d = os.path.join(INTEL, date_tag, "_raw")
    os.makedirs(d, exist_ok=True)
    return d


def grab(name: str, url: str, date_tag: str, force: bool = False) -> dict:
    """抓一个源：成功写缓存；失败回落旧缓存并标记 stale。"""
    path = os.path.join(raw_dir(date_tag), name + ".md")
    if os.path.exists(path) and not force:
        age = time.time() - os.path.getmtime(path)
        if age < 900:  # 15 分钟内不重复抓
            return {"name": name, "url": url, "ok": True, "cached": True,
                    "content": open(path, encoding="utf-8").read(), "note": "缓存"}
    err = ""
    for i in range(TRIES):
        try:
            page = ds_search.fetch(url)
            body = page.get("content") or ""
            if len(body) < 200:
                raise SystemExit(f"内容过短（{len(body)} 字）")
            if any(k in body[:1200] for k in BLOCK_HINTS):
                raise SystemExit("被 WAF 拦（滑动验证/405）——本机 IP 已被限流，隔一段时间再抓")
            open(path, "w", encoding="utf-8", newline="\n").write(body)
            return {"name": name, "url": url, "ok": True, "cached": False,
                    "content": body, "note": f"{len(body)} 字"}
        except SystemExit as exc:
            err = str(exc)
            time.sleep(SLEEP * (i + 1))
    if os.path.exists(path):
        body = open(path, encoding="utf-8").read()
        return {"name": name, "url": url, "ok": False, "cached": True, "content": body,
                "note": f"抓取失败，用旧缓存：{err[:80]}"}
    return {"name": name, "url": url, "ok": False, "cached": False, "content": "",
            "note": f"失败：{err[:120]}"}


# --------------------------------------------------------------------------- #
# Markdown 解析（betfa）
# --------------------------------------------------------------------------- #
def clean_md(md: str) -> str:
    """服务端抓回来的 Markdown 会转义 `|` `-` `.` `:` `(` 等，先整体去反斜杠再解析。"""
    return (md or "").replace("\\", "")


def split_matches(md: str) -> list[dict]:
    """按「场次头」切块。Markdown 里形如 `周三001J联赛10-21 18:00` + `东京FC(-1)VS柏太阳神`。"""
    md = clean_md(md)
    out = []
    marks = [m for m in re.finditer(r"(周[一二三四五六日]\d{3})", md)]
    for i, m in enumerate(marks):
        start = m.start()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(md)
        seg = md[start:end]
        lines = [ln.strip() for ln in seg.splitlines() if ln.strip()]
        head = lines[0] if lines else ""
        vs_line = next((ln for ln in lines[:4] if "VS" in ln or "vs" in ln), "")
        home = away = handi = ""
        if vs_line:
            parts = re.split(r"[Vv][Ss]", vs_line, maxsplit=1)
            left = re.sub(r"[\[\]]", "", parts[0]).strip()
            right = parts[1].strip() if len(parts) > 1 else ""
            mh = re.search(r"\(([+\-]?\d+)\)", left)
            handi = mh.group(1) if mh else ""
            home = re.sub(r"\([+\-]?\d+\)", "", left).strip()
            away = re.sub(r"\([+\-]?\d+\)", "", right).strip()
        league = re.sub(r"^周[一二三四五六日]\d{3}", "", head)
        league = re.sub(r"\d{2}-\d{2}\s*\d{2}:\d{2}.*$", "", league).strip()
        out.append({"no": m.group(1), "head": head, "league": league,
                    "home": home, "away": away, "handi": handi, "seg": seg})
    return out


def parse_betfa(md: str) -> dict:
    """必发九列（有成交时）或三列（未开盘时）。返回 {场次: {选项: {...}}}。"""
    data = {}
    for blk in split_matches(md):
        rows = {}
        for ln in blk["seg"].splitlines():
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not cells or cells[0] not in ("主胜", "平局", "客胜"):
                continue
            cells = [c for c in cells]
            if len(cells) >= 9:  # 有成交：成交额 冷热 市场指数 必发赔率 必发比例 99赔 99概 盈亏
                try:
                    rows[cells[0]] = {
                        "volume": float(cells[1].replace(",", "")),
                        "hot": float(cells[2]),
                        "market_idx": float(cells[3]),
                        "bf_odds": float(cells[4]),
                        "bf_ratio": float(cells[5].replace("%", "")),
                        "avg_odds": float(cells[6]),
                        "avg_prob": float(cells[7].replace("%", "")),
                        "pnl": float(cells[8].replace(",", "")),
                    }
                except ValueError:
                    pass
            elif len(cells) >= 3:  # 未开盘：只有 99 家赔率/概率
                try:
                    rows[cells[0]] = {"volume": None, "bf_ratio": None,
                                      "avg_odds": float(cells[1]),
                                      "avg_prob": float(cells[2].replace("%", ""))}
                except ValueError:
                    pass
        if rows:
            data[blk["no"]] = {"league": blk["league"], "home": blk["home"],
                               "away": blk["away"], "handi": blk["handi"], "odds": rows}
    return data


def parse_formation(md: str) -> dict:
    """阵容实力页：两队身价/平均年龄/平均身高 + 锋线中文数据。只取能确定的句子。"""
    md = clean_md(md)
    out = {}
    m = re.search(r"主队身价([\d.]+)亿?元?[^|]*\|[^|]*客队身价([\d.]+)亿?元?", md)
    if not m:
        m2 = re.findall(r"身价[\s\\]*([\d.]+)亿", md)
        if len(m2) >= 2:
            out["home_value"] = m2[0] + "亿"
            out["away_value"] = m2[1] + "亿"
    for key, pat in (("home_avg_age", r"平均(\d+)岁"), ("home_avg_h", r"平均身高(\d+)cm")):
        mm = re.search(pat, md)
        if mm:
            out[key] = mm.group(1)
    return out


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def load_batch(date_tag: str) -> set:
    p = os.path.join(BATCH, f"_matches_{date_tag}.json")
    if not os.path.exists(p):
        return set()
    try:
        raw = json.loads(open(p, encoding="utf-8").read())
        return {str(v.get("no") or k) for k, v in raw.items()}
    except Exception:  # noqa: BLE001
        return set()


def main() -> None:
    ap = argparse.ArgumentParser(description="情报抓取总入口")
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--sources", default="betfa", help="竞彩指数页，逗号分隔：" + ",".join(JINGCAI))
    ap.add_argument("--match", default="", help="澳客单场 id（逗号分隔），抓阵容/首发/走势/特征")
    ap.add_argument("--league", default="", help="澳客联赛 id（逗号分隔），抓联赛伤停")
    ap.add_argument("--force", action="store_true", help="忽略 15 分钟缓存")
    a = ap.parse_args()

    tag = a.date
    batch = load_batch(tag)
    status, data = [], {}
    for name in [x.strip() for x in a.sources.split(",") if x.strip()]:
        url = JINGCAI.get(name)
        if not url:
            continue
        r = grab(name, url, tag, a.force)
        status.append(r)
        if name == "betfa" and r["content"]:
            data["betfa"] = parse_betfa(r["content"])
        print(f"  {name:8s} {'✅' if r['ok'] else '⚠️'} {r['note']}")

    for mid in [x for x in a.match.split(",") if x.strip()]:
        for kind, tpl in MATCH_PAGES.items():
            r = grab(f"match_{mid}_{kind}", tpl.format(mid=mid), tag, a.force)
            status.append(r)
            if kind == "formation" and r["content"]:
                data.setdefault("formation", {})[mid] = parse_formation(r["content"])
            print(f"  {mid}/{kind:10s} {'✅' if r['ok'] else '⚠️'} {r['note']}")

    for lid in [x for x in a.league.split(",") if x.strip()]:
        for kind, tpl in LEAGUE_PAGES.items():
            r = grab(f"league_{lid}_{kind}", tpl.format(lid=lid), tag, a.force)
            status.append(r)
            print(f"  league{lid}/{kind:14s} {'✅' if r['ok'] else '⚠️'} {r['note']}")

    # ---- 汇总 ----
    out_dir = os.path.join(INTEL, tag)
    os.makedirs(out_dir, exist_ok=True)
    L = [f"# 情报抓取 · {tag}", "",
         f"> 生成 {dt.datetime.now():%Y-%m-%d %H:%M}；渠道 `ds_search.fetch`（服务端抓取，绕开本机 WAF）。",
         "> 内部研判层：按 R41 不进公开稿。抓不到就写失败原因，不猜。", "",
         "## 源状态", "", "| 源 | 结果 | 说明 |", "|:--|:--|:--|"]
    for s in status:
        L.append(f"| {s['name']} | {'✅' if s['ok'] else '⚠️ 失败'} | {s['note'][:90]} |")
    L.append("")

    bf = data.get("betfa") or {}
    if bf and batch:
        bf = {k: v for k, v in bf.items() if k in batch}
    if bf:
        L.append(f"## 必发盈亏（{len(bf)} 场）")
        L.append("")
        for no in sorted(bf):
            b = bf[no]
            live = any(v.get("bf_ratio") is not None for v in b["odds"].values())
            tag_s = f"## {no} {b['league']} · {b['home']} vs {b['away']}" + (f"（让 {b['handi']}）" if b["handi"] else "")
            L.append(tag_s)
            L.append("")
            if not live:
                avg = "；".join(f"{k} {v.get('avg_prob')}%" for k, v in b["odds"].items())
                L.append(f"- 必发未开盘｜99 家 {avg}")
            else:
                for k, v in b["odds"].items():
                    L.append(f"- {k}：成交 {v['volume']:,.0f}｜冷热 {v['hot']:+.0f}｜市场指数 {v['market_idx']}"
                             f"｜比例 {v['bf_ratio']}%｜99 家 {v['avg_prob']}%｜盈亏 {v['pnl']:+,.0f}")
            L.append("")
        if batch:
            miss = sorted(batch - set(bf))
            if miss:
                L.append(f"> 本批缺场次（页面没列出）：{'、'.join(miss)}")
                L.append("")

    for mid, f in (data.get("formation") or {}).items():
        L.append(f"## 阵容实力 · 澳客 {mid}")
        L.append("")
        L.append("```")
        L.append(json.dumps(f, ensure_ascii=False, indent=2))
        L.append("```")
        L.append("")

    md_path = os.path.join(out_dir, f"_fetch_{tag}.md")
    json_path = os.path.join(out_dir, f"_fetch_{tag}.json")
    open(md_path, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    open(json_path, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"date": tag, "generated": f"{dt.datetime.now():%Y-%m-%d %H:%M}",
                    "status": [{k: v for k, v in s.items() if k != "content"} for s in status],
                    "betfa": bf, "formation": data.get("formation") or {}},
                   ensure_ascii=False, indent=2))
    ok = sum(1 for s in status if s["ok"])
    print(f"\n📝 {md_path}｜源 {ok}/{len(status)} 成功")


if __name__ == "__main__":
    main()
