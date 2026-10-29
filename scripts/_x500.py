# -*- coding: utf-8 -*-
"""500.com 反爬会话共用层（books_500.py / fenxi_500.py 用）

背景：2026-10-30 起 odds.500.com/fenxi/* 变成腾讯云 EdgeOne 防护
  第一层：987 字节 JS 挑战页（__tst_status / EO_Bot_Ssid，算个数就过）
  第二层：CAPTCHA 验证页（captcha.eo.gtimg.com/TEOCaptchaWidget.js，需要人点复选框）
票据 ticket_timeout=2592000，即 **人工过一次可复用 30 天**。

用法：
    python -X utf8 scripts/_x500.py gate      # 打开有头浏览器，人工点过验证码，落 cookie
    python -X utf8 scripts/_x500.py check     # 检查当前 cookie 是否还有效

脚本内：
    from _x500 import fetch, session_ok
    html = fetch("https://odds.500.com/fenxi/ouzhi-1450965.shtml")
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "state" / "tmp" / "500session.json"
DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
GATE_URL = "https://odds.500.com/fenxi/ouzhi-1450965.shtml"
MIN_BYTES = 5000          # 挑战页都是 <2.2KB，正常分析页都是 50KB+


def load_session() -> dict:
    try:
        return json.loads(SESSION.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_session(ua: str, cookie: str) -> None:
    SESSION.parent.mkdir(parents=True, exist_ok=True)
    SESSION.write_text(json.dumps({"ua": ua, "cookie": cookie,
                                   "saved": time.strftime("%Y-%m-%d %H:%M:%S")},
                                  ensure_ascii=False, indent=1), encoding="utf-8")


def headers() -> dict:
    s = load_session()
    h = {"User-Agent": s.get("ua") or DEFAULT_UA,
         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
         "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
         "Referer": "https://odds.500.com/"}
    if s.get("cookie"):
        h["Cookie"] = s["cookie"]
    return h


def _raw(url: str, enc: str, timeout: int) -> str:
    req = urllib.request.Request(url, headers=headers())
    return urllib.request.urlopen(req, timeout=timeout).read().decode(enc, "ignore")


def fetch(url: str, enc: str = "gb18030", timeout: int = 40,
          retries: int = 3, sleep: float = 2.0) -> str:
    """取页面；遇到反爬/验证码抛 RuntimeError（附解决命令），不返回半成品。"""
    last = ""
    for attempt in range(retries):
        try:
            body = _raw(url, enc, timeout)
            if len(body) >= MIN_BYTES:
                return body
            low = body[:2500]
            if "TEOCaptchaWidget" in low or "Security Verification" in low:
                last = "captcha（需要人工过一次验证码）"
            elif "__tst_status" in low:
                last = "js-challenge（挑战页 %d 字节）" % len(body)
            else:
                last = "短页 %d 字节" % len(body)
        except Exception as exc:  # noqa: BLE001
            last = "%s: %s" % (type(exc).__name__, exc)
        time.sleep(sleep * (attempt + 1))
    raise RuntimeError("500 拦截（%s）→ 先跑一次：python -X utf8 scripts/_x500.py gate"
                       % last)


def session_ok() -> tuple[bool, str]:
    try:
        body = _raw(GATE_URL, "gb18030", 40)
    except Exception as exc:  # noqa: BLE001
        return False, "%s: %s" % (type(exc).__name__, exc)
    if len(body) >= MIN_BYTES:
        return True, "有效（%d 字节，含 pl_table_data=%s）" % (len(body), "pl_table_data" in body)
    if "TEOCaptchaWidget" in body or "Security Verification" in body:
        return False, "captcha（需重新 gate）"
    return False, "js-challenge（需重新 gate）"


def gate(url: str = GATE_URL, timeout_s: int = 420) -> int:
    """打开有头 Chrome，等人工点过验证码，成功后落 state/tmp/500session.json"""
    from playwright.sync_api import sync_playwright

    print("即将打开 Chrome：%s" % url)
    print("👉 请在浏览器里完成验证（勾选复选框），成功后窗口会自动关闭。最多等 %d 秒。" % timeout_s)
    old = load_session().get("cookie")
    if old:
        print("   （带上旧 cookie 试一次先）")
    with sync_playwright() as p:
        browser = None
        for kwargs in ({"channel": "chrome", "headless": False},
                       {"headless": False}):
            try:
                browser = p.chromium.launch(**kwargs)
                print("   浏览器：%s" % ("本机 Chrome" if "channel" in kwargs else "playwright chromium"))
                break
            except Exception as exc:  # noqa: BLE001
                print("   启动失败(%s)：%s" % (kwargs.get("channel", "chromium"), exc))
        if browser is None:
            print("❌ 起不来浏览器")
            return 2
        ctx = browser.new_context(locale="zh-CN")
        if old:
            for part in old.split("; "):
                if "=" in part:
                    k, v = part.split("=", 1)
                    ctx.add_cookies([{"name": k.strip(), "value": v.strip(),
                                      "domain": ".500.com", "path": "/"}])
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        ua = page.evaluate("navigator.userAgent")
        ok, why = False, ""
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            try:
                body = page.content()
            except Exception as exc:  # noqa: BLE001
                print("   页面读取异常：%s" % exc)
                break
            if len(body) >= MIN_BYTES and "pl_table_data" in body:
                ok, why = True, "拿到赔率表（%d 字节）" % len(body)
                break
            why = ("验证码未过" if ("TEOCaptchaWidget" in body or "Security Verification" in body)
                   else "挑战页/短页 %d 字节" % len(body))
            page.wait_for_timeout(2000)
        if not ok:
            print("❌ 超时：%s" % why)
            browser.close()
            return 1
        cookies = [c for c in ctx.cookies() if "500.com" in (c.get("domain") or "")]
        cookie = "; ".join("%s=%s" % (c["name"], c["value"]) for c in cookies)
        save_session(ua, cookie)
        print("✅ %s" % why)
        print("   已存 %s（%d 个 cookie，UA 同步存下）" % (SESSION.relative_to(ROOT), len(cookies)))
        print("   Cookie: %s" % (cookie[:120] + ("..." if len(cookie) > 120 else "")))
        page.screenshot(path=str(ROOT / "state" / "tmp" / "500gate_ok.png"), full_page=False)
        browser.close()
    return 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "gate":
        return gate()
    ok, why = session_ok()
    s = load_session()
    print("会话文件：%s" % (SESSION.relative_to(ROOT) if SESSION.exists() else "（无）"))
    if s.get("saved"):
        print("上次保存：%s" % s["saved"])
    print("%s %s" % ("✅" if ok else "❌", why))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
