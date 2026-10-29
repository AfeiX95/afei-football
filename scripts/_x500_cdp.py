# -*- coding: utf-8 -*-
"""500.com 票据获取（CDP 版，绕开沙箱「子进程管道」限制）

playwright 在这台机器上起不来浏览器（asyncio 建管道被沙箱拒 WinError 5），
所以改成：用 DEVNULL 脱离进程拉起本机 Chrome（不开管道）→ 通过 CDP over WebSocket
读页面状态和 cookie。

用法：
    python -X utf8 scripts/_x500_cdp.py            # 拉浏览器 → 等人工过验证码 → 落 cookie
    python -X utf8 scripts/_x500_cdp.py --port 9333 --timeout 300
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "state" / "tmp" / "500session.json"
PROFILE = ROOT / "state" / "tmp" / "chrome500"
GATE_URL = "https://odds.500.com/fenxi/ouzhi-1450965.shtml"
CHROMES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def _devnull_kwargs() -> dict:
    kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL, close_fds=True)
    if sys.platform == "win32":
        kw["creationflags"] = (subprocess.DETACHED_PROCESS
                               | subprocess.CREATE_NEW_PROCESS_GROUP)
    return kw


def launch(port: int, url: str) -> str:
    exe = next((p for p in CHROMES if Path(p).exists()), None)
    if not exe:
        raise SystemExit("找不到 Chrome/Edge")
    PROFILE.mkdir(parents=True, exist_ok=True)
    args = [exe,
            "--remote-debugging-port=%d" % port,
            "--user-data-dir=%s" % PROFILE,
            "--no-first-run", "--no-default-browser-check",
            "--disable-blink-features=AutomationControlled",
            "--window-size=1280,900",
            url]
    subprocess.Popen(args, **_devnull_kwargs())
    print("已拉起：%s（profile=%s）" % (Path(exe).name, PROFILE.relative_to(ROOT)))
    return exe


def targets(port: int) -> list:
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/json/list" % port, timeout=5) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except Exception:  # noqa: BLE001
        return []


def wait_endpoint(port: int, timeout: float = 40.0) -> dict:
    t0 = time.time()
    while time.time() - t0 < timeout:
        ts = [t for t in targets(port) if t.get("type") == "page"]
        hit = [t for t in ts if "500.com" in (t.get("url") or "")]
        if hit:
            return hit[0]
        if ts:
            # 页面先开在 about:blank 的情况：取第一个页面，稍后自行导航
            return ts[0]
        time.sleep(1.0)
    raise SystemExit("Chrome 调试端口 %d 没起来（%d 秒）" % (port, timeout))


def ws_call(ws, mid: int, method: str, params: dict | None = None) -> dict:
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        msg = json.loads(ws.recv())
        if msg.get("id") == mid:
            return msg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9333)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--url", default=GATE_URL)
    ap.add_argument("--reuse", action="store_true", help="不新开浏览器，连已在跑的端口")
    a = ap.parse_args()

    if not a.reuse:
        launch(a.port, a.url)
    tgt = wait_endpoint(a.port)
    print("页面：%s" % (tgt.get("url") or "")[:90])
    print("👉 如果窗口里出现「正在验证连接安全性」，请勾选复选框。最多等 %d 秒。" % a.timeout)

    from websockets.sync.client import connect
    ws_url = tgt["webSocketDebuggerUrl"]
    ok, why, ua = False, "", ""
    with connect(ws_url, max_size=40 * 1024 * 1024, open_timeout=20) as ws:
        mid = 0
        t0 = time.time()
        while time.time() - t0 < a.timeout:
            mid += 1
            r = ws_call(ws, mid, "Runtime.evaluate",
                        {"expression": "JSON.stringify({n:document.documentElement.outerHTML.length,"
                                       "t:(document.documentElement.outerHTML.indexOf('pl_table_data')>=0),"
                                       "c:(document.documentElement.outerHTML.indexOf('TEOCaptchaWidget')>=0),"
                                       "u:navigator.userAgent,h:location.href})",
                         "returnByValue": True})
            try:
                v = json.loads(r["result"]["result"]["value"])
            except Exception:  # noqa: BLE001
                v = {}
            ua = v.get("u") or ua
            if v.get("t"):
                ok, why = True, "拿到赔率表（%d 字节）" % v.get("n", 0)
                break
            why = ("验证码未过" if v.get("c") else "挑战页/短页 %d 字节" % v.get("n", 0))
            if int(time.time() - t0) % 10 < 2:
                print("   … %s（%ds）" % (why, int(time.time() - t0)))
            time.sleep(2.0)

        if ok:
            mid += 1
            r = ws_call(ws, mid, "Storage.getCookies")
            cookies = (r.get("result") or {}).get("cookies") or []
            mine = [c for c in cookies if "500.com" in (c.get("domain") or "")]
            cookie = "; ".join("%s=%s" % (c["name"], c["value"]) for c in mine)
            SESSION.parent.mkdir(parents=True, exist_ok=True)
            SESSION.write_text(json.dumps({"ua": ua, "cookie": cookie,
                                           "saved": time.strftime("%Y-%m-%d %H:%M:%S")},
                                          ensure_ascii=False, indent=1), encoding="utf-8")
            print("✅ %s" % why)
            print("   存下 %d 个 cookie → %s" % (len(mine), SESSION.relative_to(ROOT)))
            for c in mine:
                print("     %-16s %s" % (c["name"], str(c["value"])[:40]))
        else:
            print("❌ 超时：%s" % why)
        try:
            ws_call(ws, mid + 1, "Browser.close")
        except Exception:  # noqa: BLE001
            pass
    print("退出码 0" if ok else "退出码 1")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
