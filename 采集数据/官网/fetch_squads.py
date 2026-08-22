# -*- coding: utf-8 -*-
"""官网阵容抓取: inter.it + acmonza.com 渲染后提取球员名单(2026-08-22)"""
import json, re, sys
from playwright.sync_api import sync_playwright

def fetch(url, wait_sel=None, wait_ms=6000):
    with sync_playwright() as p:
        b = p.chromium.launch(channel='chrome', headless=True, args=['--no-sandbox'])
        pg = b.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36')
        pg.goto(url, wait_until='domcontentloaded', timeout=45000)
        pg.wait_for_timeout(wait_ms)
        if wait_sel:
            try:
                pg.wait_for_selector(wait_sel, timeout=15000)
            except Exception:
                pass
            pg.wait_for_timeout(2000)
        html = pg.content()
        text = pg.evaluate('() => document.body.innerText')
        b.close()
        return html, text

def extract_players(text):
    """从页面文本提取球员名单(名字+可能的号码)。"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return lines

if __name__ == '__main__':
    out = {}
    for name, url, sel in [
        ('inter', 'https://www.inter.it/en/teams/first-team', None),
        ('monza', 'https://www.acmonza.com/it/squadra/', None),
    ]:
        print(f'== {name}: {url}', flush=True)
        try:
            html, text = fetch(url, sel)
            lines = extract_players(text)
            out[name] = {'url': url, 'lines': lines}
            # 保存原始
            open(f'采集数据/官网/{name}_rendered.html', 'w', encoding='utf-8').write(html)
            print(f'   {len(html)}B html, {len(lines)} lines', flush=True)
        except Exception as e:
            print(f'   FAIL: {e}', flush=True)
            out[name] = {'url': url, 'error': str(e)}
    json.dump(out, open('采集数据/官网/squads_raw.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('done')
