#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零依赖多搜索引擎交叉检索工具（融合 multi-search-engine v3.0.4 · 合规裁剪版）

定位：
- 解决赛前外媒前瞻（Sports Mole / Forebet / Goal）、球队伤停公告、冷门次级联赛情报单引擎漏检或 WAF 拦截痛点。
- 零第三方依赖（纯 Python 标准库），支持两套模式：
  1. 默认链接模式（零网络请求）：生成各引擎带高级搜索语法的直达 URL；
  2. `--fetch` 抓取聚合模式：跨多引擎抓取公开 SERP 摘要 → URL 追踪参数清洗去重 → 多引擎命中加权排序。

安全红线（严格遵循项目反爬与反验证码准则）：
- 遇到验证码页面（CAPTCHA / 安全验证 / Turnstile / 429）立即停止该引擎请求并标记 `BLOCKED_CAPTCHA`，
  绝不绕过、破解或重试验证码，自动退回直达链接供人工查看。

用法示例：
    python -X utf8 scripts/multi_search.py --list-engines
    python -X utf8 scripts/multi_search.py "Nottingham Forest vs Chelsea injury news" --preset media
    python -X utf8 scripts/multi_search.py "海登海姆 纽伦堡 伤停" --fetch --engines bing-cn,so360,sogou
    python -X utf8 scripts/multi_search.py "site:sportsmole.co.uk Chelsea preview" --fetch --engines bing-int,ddg-lite --json
"""
import argparse
import base64
import html
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)

STRIP_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "spm", "from", "ref", "fbclid", "gclid", "msclkid", "rsv_idx", "oq",
}

CAPTCHA_SIGNALS = (
    "captcha", "recaptcha", "hcaptcha", "cf-turnstile", "turnstile",
    "verify you are human", "unusual traffic", "安全验证", "人机验证",
    "请输入验证码", "访问过于频繁", "wappass.baidu.com", "antispider",
)

ENGINES: Dict[str, dict] = {
    "bing-cn": {
        "region": "cn",
        "desc": "Bing 国内版（中英双语稳定首选）",
        "url": "https://cn.bing.com/search?q={q}&count={n}",
    },
    "bing-int": {
        "region": "cn",
        "desc": "Bing 国际版 ensearch=1（国内直连搜海外外媒前瞻/SportsMole/Goal 首选）",
        "url": "https://cn.bing.com/search?q={q}&ensearch=1&count={n}",
    },
    "so360": {
        "region": "cn",
        "desc": "360 搜索（中文资讯补充，支持 data-mdurl 真实外链解包）",
        "url": "https://www.so.com/s?q={q}",
    },
    "sogou": {
        "region": "cn",
        "desc": "搜狗搜索（中文门户与体育资讯交叉核验）",
        "url": "https://www.sogou.com/web?query={q}",
    },
    "weixin": {
        "region": "cn",
        "desc": "搜狗微信搜索（跟队伤停汇总/赛前发布会编译）",
        "url": "https://weixin.sogou.com/weixin?type=2&query={q}",
    },
    "baidu": {
        "region": "cn",
        "desc": "百度搜索（易触发安全验证，仅作备选或直达链接）",
        "url": "https://www.baidu.com/s?wd={q}&rn={n}",
    },
    "ddg-lite": {
        "region": "global",
        "desc": "DuckDuckGo Lite（轻量静态 HTML，外媒/英文伤停核查）",
        "url": "https://lite.duckduckgo.com/lite/?q={q}",
    },
    "ecosia": {
        "region": "global",
        "desc": "Ecosia（Bing 底层海外源补充）",
        "url": "https://www.ecosia.org/search?method=index&q={q}",
    },
    "google": {
        "region": "global",
        "desc": "Google gbv=1（海外全网，遇验证立即停止并退回链接）",
        "url": "https://www.google.com/search?q={q}&num={n}&gbv=1&hl=en",
    },
}

PRESETS: Dict[str, List[str]] = {
    "cn": ["bing-cn", "so360", "sogou"],
    "media": ["bing-int", "bing-cn", "ddg-lite"],
    "injury": ["bing-int", "bing-cn", "so360", "weixin"],
    "all-cn": ["bing-cn", "bing-int", "so360", "sogou", "weixin"],
}


def normalize_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    u = html.unescape(raw_url.strip())
    if u.startswith("//"):
        u = "https:" + u
    try:
        p = urllib.parse.urlsplit(u)
        if p.scheme not in ("http", "https") or not p.netloc:
            return ""
        q_pairs = [
            (k, v)
            for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=False)
            if k.lower() not in STRIP_PARAMS and not k.lower().startswith("utm_")
        ]
        clean_q = urllib.parse.urlencode(q_pairs)
        path = p.path.rstrip("/") or "/"
        return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), path, clean_q, ""))
    except Exception:
        return ""


def strip_tags(s: str) -> str:
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def is_captcha_blocked(url_final: str, body: str) -> Optional[str]:
    low_u = (url_final or "").lower()
    low_b = (body or "")[:12000].lower()
    for sig in CAPTCHA_SIGNALS:
        if sig in low_u or sig in low_b:
            # Avoid false positive if normal article mentions "captcha" far down; check title/form cues
            if sig in low_u:
                return f"redirect:{sig}"
            title_m = re.search(r"<title[^>]*>(.*?)</title>", low_b, flags=re.S)
            t_txt = title_m.group(1) if title_m else ""
            if sig in t_txt or len(body) < 8000:
                return f"page:{sig}"
    return None


def fetch_html(url: str, timeout: int = 10, warmup_url: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
    """Returns (final_url, html_text, error_code)."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    hdrs = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    try:
        if warmup_url:
            wreq = urllib.request.Request(warmup_url, headers=hdrs)
            with opener.open(wreq, timeout=6) as _:
                pass
        req = urllib.request.Request(url, headers=hdrs)
        with opener.open(req, timeout=timeout) as resp:
            final_u = resp.geturl()
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            cap = is_captcha_blocked(final_u, text)
            if cap:
                return final_u, "", f"BLOCKED_CAPTCHA({cap})"
            return final_u, text, None
    except urllib.error.HTTPError as e:
        if e.code in (403, 429, 503):
            return url, "", f"HTTP_{e.code}_STOP"
        return url, "", f"HTTP_{e.code}"
    except Exception as e:
        return url, "", f"ERR:{type(e).__name__}"


def unwrap_bing_ck(href: str) -> str:
    if "bing.com/ck/a" not in href:
        return href
    try:
        qs = urllib.parse.parse_qs(urllib.parse.urlsplit(href).query)
        u_val = (qs.get("u") or [""])[0]
        if u_val.startswith("a1"):
            b64 = u_val[2:]
            b64 += "=" * (-len(b64) % 4)
            dec = base64.urlsafe_b64decode(b64.encode("ascii")).decode("utf-8", errors="ignore")
            if dec.startswith("http"):
                return dec
    except Exception:
        pass
    return href


def parse_bing(body: str) -> List[dict]:
    out = []
    for blk in re.findall(r'<li[^>]+class="[^"]*\bb_algo\b[^"]*"[^>]*>(.*?)</li>', body, flags=re.S | re.I):
        m = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', blk, flags=re.S | re.I)
        if not m:
            continue
        href = unwrap_bing_ck(html.unescape(m.group(1)))
        title = strip_tags(m.group(2))
        if "support.microsoft.com" in href and "internet-explorer" in href:
            continue
        pm = re.search(r'<div[^>]+class="[^"]*\bb_caption\b[^"]*"[^>]*>(.*?)</div>', blk, flags=re.S | re.I)
        snip = strip_tags(pm.group(1)) if pm else strip_tags(blk)
        if href.startswith("http") and title:
            out.append({"url": href, "title": title, "snippet": snip[:220]})
    return out


def parse_so360(body: str) -> List[dict]:
    out = []
    for blk in re.findall(r'<li[^>]+class="[^"]*\bres-list\b[^"]*"[^>]*>(.*?)</li>', body, flags=re.S | re.I):
        md = re.search(r'data-mdurl="([^"]+)"', blk)
        hm = re.search(r'<h3[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', blk, flags=re.S | re.I)
        if not hm:
            continue
        href = md.group(1) if md else hm.group(1)
        if "fanyi.so.com" in href or "baike.so.com" in href and "?src=onebox" in href:
            continue
        title = strip_tags(hm.group(2))
        snip = strip_tags(re.sub(r"<h3.*?>.*?</h3>", " ", blk, flags=re.S | re.I))
        if href.startswith("http") and title:
            out.append({"url": href, "title": title, "snippet": snip[:220]})
    return out


def parse_sogou(body: str) -> List[dict]:
    out = []
    for blk in re.findall(r'<div[^>]+class="[^"]*\b(?:vrwrap|rb)\b[^"]*"[^>]*>(.*?)</div>\s*</div>', body, flags=re.S | re.I):
        hm = re.search(r'<h3[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', blk, flags=re.S | re.I)
        if not hm:
            continue
        href = hm.group(1)
        if href.startswith("/link?"):
            href = "https://www.sogou.com" + href
        title = strip_tags(hm.group(2))
        snip = strip_tags(re.sub(r"<h3.*?>.*?</h3>", " ", blk, flags=re.S | re.I))
        if href.startswith("http") and title:
            out.append({"url": href, "title": title, "snippet": snip[:220]})
    return out


def parse_ddg_lite(body: str) -> List[dict]:
    out = []
    links = re.findall(r'<a[^>]+class="[^"]*result-link[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, flags=re.S | re.I)
    snips = re.findall(r'<td[^>]+class="[^"]*result-snippet[^"]*"[^>]*>(.*?)</td>', body, flags=re.S | re.I)
    for idx, (href, t_raw) in enumerate(links):
        if "uddg=" in href:
            qs = urllib.parse.parse_qs(urllib.parse.urlsplit(href).query)
            if qs.get("uddg"):
                href = qs["uddg"][0]
        snip = strip_tags(snips[idx]) if idx < len(snips) else ""
        title = strip_tags(t_raw)
        if href.startswith("http") and title:
            out.append({"url": href, "title": title, "snippet": snip[:220]})
    return out


def parse_generic(body: str) -> List[dict]:
    out = []
    for hm in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', body, flags=re.S | re.I):
        href, title = hm.group(1), strip_tags(hm.group(2))
        if len(title) < 8 or any(x in href for x in ("bing.com", "baidu.com/s?", "google.com/search", "javascript:")):
            continue
        out.append({"url": href, "title": title, "snippet": ""})
        if len(out) >= 15:
            break
    return out


PARSERS = {
    "bing-cn": parse_bing,
    "bing-int": parse_bing,
    "so360": parse_so360,
    "sogou": parse_sogou,
    "weixin": parse_sogou,
    "ddg-lite": parse_ddg_lite,
}


def build_links(query: str, engine_names: List[str], max_results: int = 10) -> List[dict]:
    q_enc = urllib.parse.quote_plus(query)
    links = []
    for name in engine_names:
        cfg = ENGINES.get(name)
        if not cfg:
            continue
        links.append({
            "engine": name,
            "region": cfg["region"],
            "desc": cfg["desc"],
            "search_url": cfg["url"].format(q=q_enc, n=max_results),
        })
    return links


def run_cross_search(query: str, engine_names: List[str], max_results: int = 8, delay: float = 1.2) -> dict:
    links = build_links(query, engine_names, max_results)
    merged: Dict[str, dict] = {}
    engine_status: Dict[str, str] = {}

    for idx, item in enumerate(links):
        eng = item["engine"]
        if idx > 0 and delay > 0:
            time.sleep(delay)
        _, html_text, err = fetch_html(item["search_url"])
        if err:
            engine_status[eng] = err
            continue
        parser = PARSERS.get(eng, parse_generic)
        rows = parser(html_text)[:max_results]
        if not rows and eng not in PARSERS:
            rows = parse_generic(html_text)[:max_results]
        engine_status[eng] = f"OK({len(rows)})"
        for rank, r in enumerate(rows, 1):
            norm = normalize_url(r["url"]) or r["url"]
            if norm not in merged:
                merged[norm] = {
                    "url": norm,
                    "title": r["title"],
                    "snippet": r["snippet"],
                    "engines": [eng],
                    "hit_count": 1,
                    "best_rank": rank,
                }
            else:
                cur = merged[norm]
                if eng not in cur["engines"]:
                    cur["engines"].append(eng)
                    cur["hit_count"] += 1
                cur["best_rank"] = min(cur["best_rank"], rank)
                if len(r["snippet"]) > len(cur["snippet"]):
                    cur["snippet"] = r["snippet"]

    ranked = sorted(merged.values(), key=lambda x: (-x["hit_count"], x["best_rank"]))
    return {
        "query": query,
        "engines_requested": engine_names,
        "engine_status": engine_status,
        "total_unique": len(ranked),
        "results": ranked,
        "fallback_links": links,
    }


def main():
    ap = argparse.ArgumentParser(description="阿飞说球 · 零依赖多搜索引擎交叉检索工具")
    ap.add_argument("query", nargs="?", default="", help="搜索关键词（支持 site: / intitle: / filetype:）")
    ap.add_argument("--list-engines", action="store_true", help="列出全部支持的搜索引擎与预设组")
    ap.add_argument("--preset", choices=sorted(PRESETS.keys()), default="media", help="引擎预设组（默认 media）")
    ap.add_argument("--engines", default="", help="逗号分隔指定引擎，覆盖 --preset")
    ap.add_argument("--fetch", action="store_true", help="联网拉取各引擎公开摘要并交叉去重排序（默认仅生成直达链接）")
    ap.add_argument("--max", type=int, default=8, help="单引擎最大提取条数（默认 8）")
    ap.add_argument("--delay", type=float, default=1.2, help="多引擎请求礼貌间隔秒数（默认 1.2s）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = ap.parse_args()

    if args.list_engines:
        print("=== 支持的公开搜索引擎 ===")
        for k, v in ENGINES.items():
            print(f"  {k:<10} [{v['region']:<6}] {v['desc']}")
        print("\n=== 常用场景预设 (--preset) ===")
        for k, v in PRESETS.items():
            print(f"  {k:<10} -> {', '.join(v)}")
        return

    if not args.query.strip():
        ap.print_help()
        sys.exit(1)

    eng_list = [x.strip() for x in args.engines.split(",") if x.strip()] if args.engines else PRESETS[args.preset]
    invalid = [x for x in eng_list if x not in ENGINES]
    if invalid:
        print(f"未知引擎: {invalid}；请运行 --list-engines 查看可用名称", file=sys.stderr)
        sys.exit(2)

    if not args.fetch:
        links = build_links(args.query, eng_list, args.max)
        if args.json:
            print(json.dumps({"query": args.query, "mode": "links_only", "links": links}, ensure_ascii=False, indent=2))
            return
        print(f"查询词: {args.query} （零网络直达链接模式，加 --fetch 可自动聚合摘要）")
        for x in links:
            print(f"  [{x['engine']}] {x['search_url']}")
        return

    res = run_cross_search(args.query, eng_list, max_results=args.max, delay=args.delay)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    print(f"=== 多引擎交叉检索：{res['query']} ===")
    st_str = " | ".join(f"{k}:{v}" for k, v in res["engine_status"].items())
    print(f"引擎状态: {st_str}  ｜ 去重后共 {res['total_unique']} 条")
    print("-" * 72)
    if not res["results"]:
        print("未提取到有效条目（若遇验证拦截绝不强穿，请使用下方直达链接查看）：")
        for x in res["fallback_links"]:
            print(f"  [{x['engine']}] {x['search_url']}")
        return
    for i, r in enumerate(res["results"][:15], 1):
        tag = f"★×{r['hit_count']}({','.join(r['engines'])})"
        print(f"{i:2d}. {tag} {r['title']}")
        print(f"    URL : {r['url']}")
        if r["snippet"]:
            print(f"    摘要: {r['snippet']}")


if __name__ == "__main__":
    main()
