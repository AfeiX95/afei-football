# -*- coding: utf-8 -*-
"""Playwright 无头抓取公共封装 (2026-09-12 建国)

为什么要这层封装(本机实测的两个坑):
  1. 本机 Chrome 默认走系统代理 → 访问 inter.it / titan007 报 ERR_CONNECTION_CLOSED;
     而 Python 直连(urllib/requests)是通的。必须加 --no-proxy-server 旁路代理。
  2. 沙箱下 chromium 官方浏览器下载器(spawn EPERM)装不上, 也不需要装:
     本机已有 Chrome 与 Edge, 用 channel='chrome' / 'msedge' 直接驱动即可。

用法:
    from browser import fetch, fetch_json
    html, text = fetch('https://www.inter.it/en/teams/first-team', wait_ms=4000)

注意: 需要项目的 .venv(playwright + requests), 用 pwsh 脚本
      `抓取【官网】.ps1` 或在 .venv 里运行本模块。
"""
import json

# 代理旁路: 缺了它本机 Chrome 打不开这些站
LAUNCH_ARGS = ['--no-sandbox', '--no-proxy-server',
               '--disable-features=NetworkServiceSandbox', '--disable-dev-shm-usage']
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0 Safari/537.36')
CHANNELS = ('chrome', 'msedge')   # 依次回退; chromium 未安装也不影响


def _launch(p):
    last = None
    for ch in CHANNELS:
        try:
            return p.chromium.launch(channel=ch, headless=True, args=LAUNCH_ARGS)
        except Exception as e:          # 该 channel 不存在 → 试下一个
            last = e
    raise RuntimeError(f'Chrome/Edge 均无法启动: {last}')


def fetch(url, wait_sel=None, wait_ms=4000, timeout=45000):
    """打开页面 → 返回 (渲染后 html, 可见文本)"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = _launch(p)
        try:
            pg = b.new_page(user_agent=UA)
            pg.goto(url, wait_until='domcontentloaded', timeout=timeout)
            pg.wait_for_timeout(wait_ms)
            if wait_sel:
                try:
                    pg.wait_for_selector(wait_sel, timeout=15000)
                except Exception:
                    pass
                pg.wait_for_timeout(1500)
            return pg.content(), pg.evaluate('() => document.body.innerText')
        finally:
            b.close()


def fetch_json(url, wait_ms=1500, timeout=45000, headers=None):
    """同源 fetch: 用浏览器上下文请求 JSON 接口(绕过 WAF/代理), 返回解析后的对象。

    适用: 需要浏览器指纹、且与站点同源的接口。
    注意: 跨域接口会被 CORS 拦(页面里 fetch 报 Failed to fetch) → 用 fetch_api()。
    """
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = _launch(p)
        try:
            ctx = b.new_context(user_agent=UA)
            if headers:
                ctx.set_extra_http_headers(headers)
            pg = ctx.new_page()
            pg.goto('https://www.sporttery.cn/', wait_until='domcontentloaded', timeout=timeout)
            pg.wait_for_timeout(wait_ms)
            body = pg.evaluate(
                """async (u) => {
                    const r = await fetch(u, {credentials: 'include'});
                    return {status: r.status, text: await r.text()};
                }""", url)
            if body['status'] != 200:
                raise RuntimeError(f'HTTP {body["status"]}')
            return json.loads(body['text'])
        finally:
            b.close()


def fetch_api(url, wait_ms=1200, timeout=45000, referer='https://www.sporttery.cn/'):
    """经浏览器网络栈直接请求接口(路由拦截取回响应体) → 解析 JSON。

    比 fetch_json 更强: 不受 CORS 限制, 带真实浏览器指纹与 Referer
    → 竞彩官方 webapi(getMatchCalculatorV1) 这类"requests 直连吃 567"的接口走这里。
    """
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = _launch(p)
        try:
            ctx = b.new_context(user_agent=UA, extra_http_headers={'Referer': referer})
            pg = ctx.new_page()
            pg.goto(referer, wait_until='domcontentloaded', timeout=timeout)
            pg.wait_for_timeout(wait_ms)
            resp = ctx.request.get(url, headers={'Referer': referer}, timeout=timeout)
            if resp.status != 200:
                raise RuntimeError(f'HTTP {resp.status}')
            return json.loads(resp.text())
        finally:
            b.close()

