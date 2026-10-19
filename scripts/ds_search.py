#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ds_search.py — DeepSeek 自研搜索引擎的 Search / Fetch 薄封装（2026-10-20 建）

用途：给 `media_intel.py`（外媒与 AI 预测采集）提供取数层。官方文档：
    POST https://api.deepseek.com/v1/tools/search   {"query","count","need_content","ori_question"}
    POST https://api.deepseek.com/v1/tools/fetch    {"url"}
    Authorization: Bearer <DeepSeek API Key>

计费：按请求次数，Search 与 Fetch 都是 5 元 / 1000 次（失败、无结果不计费）。
      count 只决定返回条数，不影响单价 —— 所以「少发请求、多发条数」更省。
限速：每个账号 Search 100 QPS、Fetch 25 QPS。

Key 解析顺序（谁在前用谁）：
    1) 环境变量 DEEPSEEK_API_KEY
    2) state/api-keys.json 的 "deepseek"（字符串，或 {"key": "..."}）
    3) DSH 自己的密钥库 %USERPROFILE%\.dsh\.credentials.yaml 的 DEEPSEEK_API_KEY
       —— 用户在 DSH「插件管理 → 网页搜索」里配过的那把，直接复用，不再单存一份

用法
    python scripts/ds_search.py search "Arsenal vs Chelsea preview" --count 6
    python scripts/ds_search.py fetch https://example.com/article
    python scripts/ds_search.py test                       # 打一发最小请求验证 Key 与计费

    # 测试用：把端点指到本地假服务器
    DEEPSEEK_BASE=http://127.0.0.1:8765 python scripts/ds_search.py search "..."
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS_FILE = ROOT / "state" / "api-keys.json"
BASE = os.environ.get("DEEPSEEK_BASE", "https://api.deepseek.com").rstrip("/")
TIMEOUT = 30


def _dsh_credentials_key() -> str:
    """从 DSH 自己的密钥库取 DEEPSEEK_API_KEY（插件管理里配过就在这儿）。

    只认这一个键名，不做任何别的推断 —— 免得把别的服务的密钥当搜索额度花掉。
    """
    home = Path(os.environ.get("USERPROFILE") or os.path.expanduser("~"))
    cf = home / ".dsh" / ".credentials.yaml"
    if not cf.exists():
        return ""
    try:
        for line in cf.read_text(encoding="utf-8", errors="ignore").splitlines():
            t = line.strip()
            if t.startswith("DEEPSEEK_API_KEY:"):
                return t.split(":", 1)[1].strip().strip("'\"")
    except Exception:  # noqa: BLE001
        return ""
    return ""


def api_key() -> str:
    k = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if k:
        return k
    if KEYS_FILE.exists():
        try:
            data = json.loads(KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            data = {}
        v = data.get("deepseek")
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict):
            for f in ("key", "api_key", "token"):
                if isinstance(v.get(f), str) and v[f].strip():
                    return v[f].strip()
    k = _dsh_credentials_key()
    if k:
        return k
    raise SystemExit(
        "没有 DeepSeek API Key。三选一：\n"
        "  1) 环境变量 DEEPSEEK_API_KEY=sk-...\n"
        "  2) state/api-keys.json 里加 \"deepseek\": \"sk-...\"\n"
        "  3) 在 DSH 插件管理里配好网页搜索（自动读 ~/.dsh/.credentials.yaml）\n"
        "（Search/Fetch 按次计费 5 元/1000 次，失败与无结果不计费）"
    )


def _post(path: str, payload: dict) -> dict:
    try:
        import requests
    except ImportError:  # pragma: no cover
        raise SystemExit("需要 requests：pip install requests")
    url = f"{BASE}{path}"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"},
        json=payload,
        timeout=TIMEOUT,
    )
    if r.status_code == 402:
        raise SystemExit("402 余额不足：先充值再跑（Search/Fetch 5 元/1000 次）")
    if r.status_code == 429:
        raise SystemExit("429 触发 QPS 限制（Search 100 / Fetch 25），等一会再重试")
    if r.status_code >= 400:
        try:
            msg = r.json().get("error", {}).get("message", "")
        except Exception:  # noqa: BLE001
            msg = (r.text or "")[:200]
        raise SystemExit(f"HTTP {r.status_code}：{msg}")
    return r.json()


def search(query: str, count: int = 10, need_content: bool = False,
           ori_question: str | None = None) -> list[dict]:
    """返回 results 列表（每条含 title/url/snippet/summary/content/site_name/date/authority/rerank_score）。"""
    payload: dict = {"query": query, "count": max(1, min(50, int(count))),
                     "need_content": bool(need_content)}
    if ori_question:
        payload["ori_question"] = ori_question[:128]
    return list(_post("/v1/tools/search", payload).get("results") or [])


def fetch(url: str) -> dict:
    """返回 {"title","content"}；抓不到会抛 SystemExit（404 多为站点拦截或无正文）。"""
    return _post("/v1/tools/fetch", {"url": url})


def main() -> None:
    ap = argparse.ArgumentParser(description="DeepSeek Search / Fetch 薄封装")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="搜网页")
    s.add_argument("query")
    s.add_argument("--count", type=int, default=8)
    s.add_argument("--content", action="store_true", help="顺带取正文（更慢更大）")
    s.add_argument("--json", action="store_true", help="输出原始 JSON")

    f = sub.add_parser("fetch", help="抓单页为 Markdown")
    f.add_argument("url")
    f.add_argument("--chars", type=int, default=4000)

    sub.add_parser("test", help="最小请求，验证 Key")
    a = ap.parse_args()

    if a.cmd == "search":
        res = search(a.query, a.count, a.content, ori_question=a.query)
        if a.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return
        for i, r in enumerate(res, 1):
            print(f"{i}. [{r.get('rerank_score')}] {r.get('title')}")
            print(f"   {r.get('url')}  ({r.get('site_name')}, {r.get('date')}, auth={r.get('authority')})")
            print(f"   {(r.get('summary') or r.get('snippet') or '')[:180]}")
    elif a.cmd == "fetch":
        page = fetch(a.url)
        print(page.get("title") or "(无标题)")
        print((page.get("content") or "")[: a.chars])
    else:
        res = search("DeepSeek", count=1)
        print("✅ Key 可用，返回", len(res), "条")
        if res:
            print(res[0].get("title"), res[0].get("url"))


if __name__ == "__main__":
    main()
