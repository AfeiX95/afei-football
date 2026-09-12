# -*- coding: utf-8 -*-
"""官网阵容抓取: inter.it + acmonza.com 渲染后提取球员名单(2026-08-22)
2026-09-12 更新: 改走公共封装 采集数据/browser.py
  - 必须旁路系统代理(--no-proxy-server), 否则 Chrome 报 ERR_CONNECTION_CLOSED
  - 浏览器用本机 Chrome/Edge, 不需要 playwright 自带 chromium
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, '采集数据'))
from browser import fetch  # noqa: E402

OUT_DIR = os.path.join(ROOT, '采集数据', '官网')

TARGETS = [
    ('inter', 'https://www.inter.it/en/teams/first-team', None),
    ('monza', 'https://www.acmonza.com/it/squadra/', None),
]

if __name__ == '__main__':
    out = {}
    for name, url, sel in TARGETS:
        print(f'== {name}: {url}', flush=True)
        try:
            html, text = fetch(url, wait_sel=sel, wait_ms=6000)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            out[name] = {'url': url, 'lines': lines}
            with open(os.path.join(OUT_DIR, f'{name}_rendered.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            print(f'   {len(html)}B html, {len(lines)} lines', flush=True)
        except Exception as e:
            print(f'   FAIL: {type(e).__name__} {e}', flush=True)
            out[name] = {'url': url, 'error': str(e)}
    with open(os.path.join(OUT_DIR, 'squads_raw.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('done')
