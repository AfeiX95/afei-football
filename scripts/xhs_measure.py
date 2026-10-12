#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""排版量尺：量小红书卡片中间 HTML 的真实内容高度（改版式前后都用它，别靠猜）。

用法：
  python scripts/xhs_measure.py <html目录>            # 量目录里全部 HTML（按文件名排序）
  python scripts/xhs_measure.py <html目录> --limit 3  # 只量前 3 张

HTML 从哪来：`python scripts/xhs_html.py --input ... --html-out <目录>`（渲染时另存中间 HTML）。
它会把 `#fit` 的自动缩放复位成 1，报「内容底 Npx（余/超出多少）」并逐块列高 —— 单卡上限 1440px。
需要 playwright（`pip install playwright && python -m playwright install chromium`）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JS = """() => {
  const fit = document.getElementById('fit');
  fit.style.zoom = 1;
  const c = document.querySelector('.card');
  const kids = [...c.children].map(e => {
    const r = e.getBoundingClientRect();
    return [(e.className && typeof e.className === 'string' ? e.className : e.tagName), Math.round(r.height)];
  });
  const bottom = [...c.children].reduce((a, e) => Math.max(a, e.offsetTop + e.offsetHeight), 0);
  return {h: c.scrollHeight, bottom: bottom, box: c.clientHeight, kids};
}"""


def main() -> None:
    args = [a for a in sys.argv[1:]]
    if not args or args[0].startswith("-"):
        sys.exit(__doc__.strip())
    d = Path(args[0])
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 99
    files = sorted(d.glob("*.html"))[:limit]
    if not files:
        sys.exit(f"没有 HTML：{d}（先跑 xhs_html.py --html-out {d}）")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("需要 playwright：python -m pip install playwright && python -m playwright install chromium")

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1440}, device_scale_factor=1)
        for f in files:
            pg.goto(f.resolve().as_uri())
            pg.wait_for_timeout(120)
            info = pg.evaluate(JS)
            room = info["box"] - info["bottom"]
            print(f"{f.name}：内容底 {info['bottom']}px（{'余 %dpx' % room if room >= 0 else '超出 %dpx' % -room}）")
            for name, h in info["kids"]:
                print(f"    {h:5d}  {name}")
        b.close()


if __name__ == "__main__":
    main()
