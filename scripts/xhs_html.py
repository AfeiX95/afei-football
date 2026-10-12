#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书图文卡片 · HTML + Chrome 渲染版
=====================================
两种风格（都用本地 Chrome headless 截图，零安装、不联网）：

  editorial  杂志风 —— 米白纸底 + 衬线大标题 + 细分隔线 + 网格分栏
  swiss      瑞士风 —— 白底 + 无衬线 + 纯黑粗线 + 大量强调色块

为什么不用 Playwright：本机没装，但 Chrome / Edge 已装，
`chrome --headless=new --screenshot` 的效果与 Playwright 截图等价，且更快（~1 秒/张 @2x）。

数据仍然走同一份 cards.json（字段见 📚知识库/写作指南/小红书图文卡片.md），
出图前照样过 📚知识库/模型脚本/check_article.py 的违规词表，命中即拒绝出图。

用法：
    python scripts/xhs_html.py --input "📝文章/20261014/小红书/cards.json" --style both --out "state/xhs_preview"
    python scripts/xhs_html.py --menu
"""

from __future__ import annotations

import argparse
import html as _html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xhs_cards import ROOT, audit, auto_cards, find_card_files, load_input, safe, write_caption  # noqa: E402

W, H, DPR = 1080, 1440, 2

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

SERIF_FONT = r"C:\Users\wuyan\.agents\skills\claude-design-card\assets\NotoSerifSC-Regular.ttf"

# 兜底自适应：内容偶尔写长了（页脚被裁），把整张卡等比缩一点点（最多 6%），
# 这样用户不用懂 CSS 也不会出废图。只在真的放不下时才触发。
AUTOFIT_JS = (
    "<script>(function(){var f=document.getElementById('fit'),c=f.firstElementChild,z=1.0,"
    "last=c.lastElementChild;while(z>0.94&&last.getBoundingClientRect().bottom>%d){z-=0.01;"
    "f.style.zoom=z;}})();</script>" % (H - 12)
)

# --------------------------------------------------------------------------- #
# 公共 CSS
# --------------------------------------------------------------------------- #
BASE_CSS = """
*,*::before,*::after{box-sizing:border-box;-webkit-font-smoothing:antialiased}
html,body{margin:0;padding:0}
body{width:%(w)dpx;height:%(h)dpx;overflow:hidden}
.card{position:relative;width:%(w)dpx;height:%(h)dpx;display:flex;flex-direction:column}
""" % {"w": W, "h": H}

# --------------------------------------------------------------------------- #
# 风格一：杂志风 editorial
# --------------------------------------------------------------------------- #
EDITORIAL_CSS = """
@font-face{font-family:"CardSerif";src:url("font-serif.ttf") format("truetype");font-weight:400 900;font-display:block}
body{background:#f3f0e8;color:#0a0a0b}
.ed{font-family:"Microsoft YaHei UI","Noto Sans SC","PingFang SC",sans-serif;padding:84px 80px 70px}
.ed .serif{font-family:"CardSerif","Noto Serif SC","Songti SC",SimSun,serif}
.ed .top{display:flex;justify-content:space-between;align-items:baseline;letter-spacing:.16em;
  font-size:27px;color:#9b5a2e;font-weight:700}
.ed .pager{letter-spacing:.06em;font-size:26px;color:#8d867c;font-weight:400}
.ed h1{margin:34px 0 0;font-size:96px;line-height:1.14;font-weight:900;letter-spacing:-.005em}
.ed h1 .vsx{font-family:"Microsoft YaHei UI",sans-serif;font-size:44px;font-weight:400;color:#9d968a;
  margin:0 20px;vertical-align:middle}
.ed .rule{height:3px;background:rgba(10,10,11,.26);margin:34px 0 0;flex:none}
.ed .stance{padding:28px 0 0}
.ed .stance .lab{font-size:25px;letter-spacing:.22em;color:#8d867c;font-weight:700}
.ed .stance .val{margin-top:14px;font-size:66px;line-height:1.18;font-weight:900;color:#9b5a2e}
.ed .sec{margin-top:36px}
.ed .sec .head{display:flex;justify-content:space-between;align-items:baseline;
  font-size:26px;font-weight:700;letter-spacing:.06em}
.ed .sec .head .right{font-size:24px;font-weight:400;color:#8d867c;letter-spacing:.04em}
.ed .grid3{display:flex;gap:38px;margin-top:20px}
.ed .cell{flex:1}
.ed .cl{font-size:25px;color:#6f6960}
.ed .cv{font-size:82px;font-weight:900;line-height:1.05;margin-top:8px;letter-spacing:-.02em}
.ed .cv .pct{font-size:44px;font-weight:700}
.ed .bar{height:10px;background:rgba(10,10,11,.10);margin-top:16px}
.ed .bar i{display:block;height:10px;background:#0a0a0b}
.ed .bar.mkt{background:rgba(10,10,11,.06);margin-top:8px}
.ed .bar.mkt i{background:#b9b2a6}
.ed .cm{font-size:25px;color:#8d867c;margin-top:10px}
.ed .scores{display:flex;gap:22px;margin-top:22px}
.ed .sc{flex:1;border-top:2px solid rgba(10,10,11,.5);padding-top:16px}
.ed .sc .sl{font-size:24px;color:#8d867c;letter-spacing:.1em}
.ed .sc .sv{font-size:56px;font-weight:900;margin-top:6px;letter-spacing:-.01em}
.ed .sc.first .sv{color:#9b5a2e}
.ed .notes{margin-top:auto;display:flex;flex-direction:column;gap:26px;padding-top:28px}
.ed .note{display:flex;gap:22px;border-top:2px solid rgba(10,10,11,.16);padding-top:22px}
.ed .note .nl{flex:0 0 96px;font-size:28px;font-weight:900;letter-spacing:.04em}
.ed .note .nl i{display:inline-block;width:16px;height:16px;background:#9b5a2e;margin-right:12px}
.ed .note .nl.sig i{background:#0a0a0b}
.ed .note p{margin:0;font-size:33px;line-height:1.55;color:#26241f}
.ed .foot{display:flex;justify-content:space-between;align-items:flex-end;margin-top:auto;
  border-top:3px solid rgba(10,10,11,.24);padding-top:26px;font-size:26px;color:#6f6960}
.ed .foot .r{text-align:right}
.ed .foot .tags{color:#9b5a2e;margin-top:8px}
/* 封面 */
.ed.cover{padding-top:96px}
.ed.cover h1{font-size:104px;line-height:1.16;margin-top:30px}
.ed.cover .sub{margin-top:26px;font-size:34px;line-height:1.5;color:#4a463f}
.ed.cover .items{margin-top:52px;border-top:2px solid rgba(10,10,11,.16)}
.ed.cover .it{display:flex;gap:26px;align-items:baseline;border-bottom:2px solid rgba(10,10,11,.10);
  padding:26px 0;font-size:40px;font-weight:700}
.ed.cover .it .n{flex:0 0 54px;font-size:32px;color:#9b5a2e;font-weight:900}
.ed.cover .tail{margin-top:auto;font-size:30px;line-height:1.6;color:#5c574f;
  border-left:8px solid #9b5a2e;padding-left:26px}
"""

# --------------------------------------------------------------------------- #
# 风格二：瑞士风 swiss
# --------------------------------------------------------------------------- #
SWISS_CSS = """
body{background:#f4f4f2;color:#000}
.sw{font-family:"Microsoft YaHei UI","Noto Sans SC","PingFang SC","Helvetica Neue",Arial,sans-serif;
  padding:66px 76px 54px}
.sw .top{display:flex;align-items:center;gap:22px;font-size:26px;letter-spacing:.12em;font-weight:700}
.sw .chip{background:#000;color:#fff;padding:12px 22px}
.sw .chip.no{background:#e8402a;color:#fff}
.sw .top .time{margin-left:auto;letter-spacing:.06em;font-weight:700}
.sw .top .pager{background:#000;color:#fff;padding:12px 20px;letter-spacing:.06em}
.sw h1{margin:34px 0 0;font-size:98px;line-height:1.02;font-weight:900;letter-spacing:-.02em}
.sw h1 .vsx{color:#e8402a;margin:0 16px;font-size:70px;vertical-align:2px}
.sw .thick{height:8px;background:#000;margin:30px 0 0;flex:none}
.sw .stance{margin-top:30px;display:flex;gap:24px;align-items:flex-start}
.sw .stance .tab{flex:0 0 14px;align-self:stretch;background:#e8402a}
.sw .stance .val{font-size:60px;line-height:1.14;font-weight:900;letter-spacing:-.01em}
.sw .stance .lab{font-size:24px;letter-spacing:.24em;font-weight:700;color:#6b6b6b;margin-bottom:10px}
.sw .sec{margin-top:36px}
.sw .sec .head{display:flex;justify-content:space-between;align-items:baseline;
  border-bottom:3px solid #000;padding-bottom:12px;font-size:27px;font-weight:900;letter-spacing:.1em}
.sw .sec .head .right{font-size:23px;font-weight:700;color:#6b6b6b;letter-spacing:.04em}
.sw .grid3{display:flex;margin-top:0}
.sw .cell{flex:1;padding:22px 18px 22px 0;border-right:1px solid rgba(0,0,0,.18)}
.sw .cell:last-child{border-right:0}
.sw .cell + .cell{padding-left:22px}
.sw .cl{font-size:24px;letter-spacing:.16em;font-weight:700;color:#6b6b6b}
.sw .cv{font-size:88px;font-weight:900;line-height:1;margin-top:12px;letter-spacing:-.03em}
.sw .cv .pct{font-size:44px;font-weight:700}
.sw .bar{height:16px;background:rgba(0,0,0,.14);margin-top:18px}
.sw .bar i{display:block;height:16px;background:#000}
.sw .bar.mkt{height:8px;background:rgba(0,0,0,.08);margin-top:10px}
.sw .bar.mkt i{background:#e8402a;height:8px}
.sw .cm{font-size:24px;color:#6b6b6b;margin-top:12px;letter-spacing:.04em}
.sw .scores{display:flex;gap:18px;margin-top:24px}
.sw .sc{flex:1;border:4px solid #000;padding:18px 20px}
.sw .sc .sl{font-size:23px;letter-spacing:.16em;font-weight:700;color:#6b6b6b}
.sw .sc .sv{font-size:58px;font-weight:900;margin-top:8px;letter-spacing:-.02em}
.sw .sc.first{background:#e8402a;border-color:#e8402a;color:#fff}
.sw .sc.first .sl{color:rgba(255,255,255,.85)}
.sw .notes{margin-top:auto;display:flex;flex-direction:column;gap:22px;padding-top:24px}
.sw .note{border-top:3px solid #000;padding-top:20px;display:flex;gap:22px}
.sw .note .nl{flex:0 0 auto;font-size:26px;font-weight:900;letter-spacing:.08em}
.sw .note .nl span{background:#000;color:#fff;padding:8px 14px}
.sw .note .nl.sig span{background:#e8402a}
.sw .note p{margin:0;font-size:33px;line-height:1.52}
.sw .foot{margin-top:auto;border-top:8px solid #000;padding-top:22px;display:flex;
  justify-content:space-between;align-items:flex-end;font-size:26px;font-weight:700;letter-spacing:.02em}
.sw .foot .r{text-align:right}
.sw .foot .tags{color:#e8402a;margin-top:8px}
/* 封面 */
.sw.cover h1{font-size:108px;line-height:1.06}
.sw.cover h1 .hl{background:#e8402a;color:#fff;padding:0 12px}
.sw.cover .sub{margin-top:28px;font-size:34px;line-height:1.5;color:#3d3d3d}
.sw.cover .items{margin-top:46px}
.sw.cover .it{display:flex;gap:24px;align-items:baseline;border-top:3px solid #000;padding:24px 0;font-size:39px;font-weight:900}
.sw.cover .it .n{flex:0 0 60px;font-size:30px;color:#e8402a}
.sw.cover .tail{margin-top:auto;border-top:3px solid #000;padding-top:22px;font-size:29px;line-height:1.6;color:#3d3d3d}
"""

STYLES = {"editorial": (EDITORIAL_CSS, "ed", "CardSerif"), "swiss": (SWISS_CSS, "sw", None)}


# --------------------------------------------------------------------------- #
# 工具
# --------------------------------------------------------------------------- #
def esc(t) -> str:
    return _html.escape(str(t if t is not None else ""))


def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    for name in ("chrome", "google-chrome", "chromium", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    return None


def bar_ratio(pct: float) -> float:
    """把百分数映射成 0-100 的条长（以三向最大值 80% 为满格，避免都顶格）。"""
    return max(4.0, min(100.0, pct / 80.0 * 100.0))


def probs_html(card: dict, cluster: str) -> str:
    mine = card.get("probs_mine") or [0, 0, 0]
    mkt = card.get("probs_mkt") or []
    labels = ["主胜", "平", "客胜"]
    cells = []
    for i, lab in enumerate(labels):
        mk = f'<div class="bar mkt"><i style="width:{bar_ratio(mkt[i]):.1f}%"></i></div>' if mkt else ""
        mk_txt = f'<div class="cm">机构 {mkt[i]:.1f}%</div>' if mkt else ""
        cells.append(
            f'<div class="cell"><div class="cl">{lab}</div>'
            f'<div class="cv">{mine[i]:.1f}<span class="pct">%</span></div>'
            f'<div class="bar"><i style="width:{bar_ratio(mine[i]):.1f}%"></i></div>{mk}{mk_txt}</div>'
        )
    right = '<span class="right">我 / 机构</span>' if mkt else ""
    return (f'<section class="sec"><div class="head"><span>三向概率</span>{right}</div>'
            f'<div class="grid3">{"".join(cells)}</div></section>')


def scores_html(card: dict) -> str:
    sc = card.get("score") or []
    labels = ["首选", "次选", "防范"]
    cells = []
    for i, lab in enumerate(labels):
        if i >= len(sc):
            break
        cls = "sc first" if i == 0 else "sc"
        cells.append(f'<div class="{cls}"><div class="sl">{lab}</div><div class="sv">{esc(sc[i])}</div></div>')
    if not cells:
        return ""
    return (f'<section class="sec"><div class="head"><span>高概率比分</span></div>'
            f'<div class="scores">{"".join(cells)}</div></section>')


def notes_html(card: dict, cluster: str) -> str:
    out = []
    if card.get("will"):
        out.append(f'<div class="note"><div class="nl will"><i></i>战意</div><p>{esc(card["will"])}</p></div>')
    if card.get("signal"):
        out.append(f'<div class="note"><div class="nl sig"><i></i>信号</div><p>{esc(card["signal"])}</p></div>')
    if card.get("note"):
        out.append(f'<div class="note"><div class="nl more"><i></i>补充</div><p>{esc(card["note"])}</p></div>')
    if not out:
        return ""
    if cluster == "sw":  # 瑞士风：标签做成黑/红块
        out = [o.replace('<div class="nl will"><i></i>战意</div>', '<div class="nl will"><span>战意</span></div>')
                .replace('<div class="nl sig"><i></i>信号</div>', '<div class="nl sig"><span>信号</span></div>')
                .replace('<div class="nl more"><i></i>补充</div>', '<div class="nl more"><span>补充</span></div>')
               for o in out]
    return f'<div class="notes">{"".join(out)}</div>'


def footer_html(card: dict) -> str:
    return ('<div class="foot"><div class="l">' + esc(card.get("source", "数据来源：中国体育官方数据平台")) +
            '</div><div class="r">' + esc(card.get("brand", "@阿飞·赛博聊球")) +
            f'<div class="tags">{esc(card.get("tags", ""))}</div></div></div>')


def card_html(card: dict, meta: dict, style: str, idx: int, total: int) -> str:
    css, cluster, _ = STYLES[style]
    merged = dict(meta)
    merged.update(card)
    top = (f'<div class="top"><span class="chip">{esc(card.get("league", ""))}</span>'
           f'<span class="chip no">{esc(card.get("no", ""))}</span>'
           f'<span class="time">{esc(card.get("kick", ""))}</span>'
           f'<span class="pager">{idx}/{total}</span></div>')
    if style == "editorial":
        top = (f'<div class="top"><span>{esc(card.get("league", ""))} · {esc(card.get("no", ""))} · '
               f'{esc(card.get("kick", ""))}</span><span class="pager">{idx}/{total}</span></div>')
    stance_lab = card.get("stance_label") or "我的判断"
    # 标题与「我的判断」之间的分隔：杂志风＝细线，瑞士风＝粗黑条
    sep = '<div class="rule"></div>' if style == "editorial" else '<div class="thick"></div>'
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{BASE_CSS}{css}</style></head><body>
<div id="fit"><div class="card {cluster}">
  {top}
  <h1 class="serif">{esc(card.get("home",""))}<span class="vsx">vs</span>{esc(card.get("away",""))}</h1>
  {sep}
  <div class="stance"><div class="lab">{esc(stance_lab)}</div><div class="val serif">{esc(card.get("stance",""))}</div></div>
  {probs_html(card, cluster)}
  {scores_html(card)}
  {notes_html(card, cluster)}
  {footer_html(merged)}
</div></div>{AUTOFIT_JS}</body></html>"""


def cover_html(meta: dict, items: list, total: int, style: str) -> str:
    css, cluster, _ = STYLES[style]
    title = meta.get("title", "")
    if style == "swiss":
        # 把「三场我全站对面」这类收口句刷成强调块：取冒号后的部分
        if "：" in title:
            a, b = title.split("：", 1)
            title_html = f'{esc(a)}：<span class="hl">{esc(b)}</span>'
        else:
            title_html = esc(title)
        tag = f'<div class="chip">{esc(meta.get("league", "足球"))}</div>'
        top = (f'<div class="top">{tag}<span class="time">{esc(meta.get("cover_kicker", ""))}</span>'
               f'<span class="pager">1/{total}</span></div>')
    else:
        title_html = esc(title)
        top = (f'<div class="top"><span>{esc(meta.get("cover_kicker", ""))}</span>'
               f'<span class="pager">1/{total}</span></div>')
    its = "".join(f'<div class="it"><span class="n">{i+1:02d}</span><span>{esc(t)}</span></div>'
                  for i, t in enumerate(items))
    tail = meta.get("cover_tail") or ("读图：概率左边「我」是后台模型算的，右边「机构」是官方定价折算；"
                                      "比分三档只给方向。右滑看每场判断 →")
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{BASE_CSS}{css}</style></head><body>
<div id="fit"><div class="card {cluster} cover">
  {top}
  <h1 class="serif">{title_html}</h1>
  <div class="sub">{esc(meta.get("subtitle", ""))}</div>
  <div class="items">{its}</div>
  <div class="tail">{esc(tail)}</div>
  {footer_html(meta)}
</div></div>{AUTOFIT_JS}</body></html>"""


def shot(html_path: Path, png_path: Path, chrome: str, scale: int = DPR) -> tuple[bool, str]:
    png_path = png_path.resolve()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    if png_path.exists():
        png_path.unlink()
    cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
           "--virtual-time-budget=1200",
           f"--force-device-scale-factor={scale}", f"--window-size={W},{H}",
           f"--screenshot={png_path}", html_path.resolve().as_uri()]
    r = subprocess.run(cmd, capture_output=True)
    err = (r.stderr or b"").decode("utf-8", "ignore").strip().splitlines()
    ok = png_path.exists() and png_path.stat().st_size > 0
    return ok, ("" if ok else ("rc=%s " % r.returncode + " | ".join(err[-3:])))


def bottom_margin(png: Path) -> int:
    """量出图底部留白（@2x 像素）。=0 说明页脚被裁掉了。"""
    try:
        from PIL import Image
        import numpy as np
        im = np.asarray(Image.open(png).convert("L")).astype(int)
        h, w = im.shape
        bg = int(np.bincount(im[0, :].ravel()).argmax())
        for y in range(h - 1, -1, -1):
            if im[y, 40:w - 40].min() < bg - 14:
                return h - 1 - y
        return h
    except Exception:
        return -1


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def playwright_ready() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except Exception:
        return False


def shoot_playwright(plans, scale: int = DPR) -> dict:
    """一个复用的 Chromium 渲染全部作业（比逐张起 CLI 进程快约 2 倍，且浏览器版本固定）。

    plans: [(name, html_path, png_path)] → {name: (ok, why)}
    """
    out: dict = {}
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        return {n: (False, f"没装 playwright（{e}）") for n, _, _ in plans}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=scale)
            page = ctx.new_page()
            for name, hp, png in plans:
                png = Path(png).resolve()
                png.parent.mkdir(parents=True, exist_ok=True)
                if png.exists():
                    png.unlink()
                page.goto(Path(hp).resolve().as_uri(), wait_until="load")
                page.wait_for_timeout(150)  # 等 AUTOFIT_JS 收尾
                page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": W, "height": H})
                out[name] = ((png.exists() and png.stat().st_size > 0), "截图为空")
            ctx.close()
            b.close()
    except Exception as e:  # 已渲染的保留，其余标失败
        out.update({n: (False, f"playwright 渲染失败：{e}") for n, _, _ in plans if n not in out})
    return out


def build(cards_path: Path, style: str, out_dir: Path, limit: int = 0, engine: str = "chrome") -> list[Path]:
    data, cards = load_input(str(cards_path))
    if limit:
        cards = cards[:limit]
    audit([data] + cards)  # 违规词门禁：命中即 sys.exit(2)

    if engine == "auto":
        engine = "playwright" if playwright_ready() else "chrome"
    chrome = find_chrome()
    if engine == "chrome" and not chrome:
        print("❌ 没找到 Chrome / Edge，无法截图（或改用 --engine playwright）。")
        sys.exit(3)
    print(f"  引擎：{engine}" + (f"（{chrome}）" if engine == "chrome" else "（playwright 内置 chromium，版本固定）"))

    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="xhs_html_", dir=str(Path(ROOT) / "state")))
    if style == "editorial" and os.path.exists(SERIF_FONT):
        shutil.copy2(SERIF_FONT, tmp / "font-serif.ttf")

    made: list[Path] = []
    total = len(cards) + 1
    jobs = [("01_封面", cover_html({**data, "matches": None}, data.get("cover_items") or [], total, style))]
    for i, m in enumerate(cards, start=2):
        name = f"{i:02d}_{safe(m.get('no') or '')}_{safe(m.get('home') or '')}vs{safe(m.get('away') or '')}"
        jobs.append((name, card_html(m, data, style, i, total)))

    plans = []
    for name, doc in jobs:
        hp = tmp / f"{name}.html"
        hp.write_text(doc, encoding="utf-8")
        plans.append((name, hp, out_dir / f"{name}.png"))

    res = (shoot_playwright(plans) if engine == "playwright"
           else {n: shot(hp, png, chrome) for n, hp, png in plans})
    for name, hp, png in plans:
        ok, why = res.get(name, (False, "未渲染"))
        note = ""
        if ok:
            bm = bottom_margin(png)
            if 0 <= bm < 24:
                note = f"  ⚠️ 底部仅 {bm}px@2x（页脚可能被裁，去 cards.json 精简文案）"
        print(("  ✅ " if ok else "  ❌ ") + png.name +
              (f"  {png.stat().st_size // 1024}KB" if ok else f"  {why}") + note)
        if ok:
            made.append(png)
    shutil.rmtree(tmp, ignore_errors=True)
    if made and style == "editorial":
        cap = write_caption(data, cards, out_dir)
        print("  📝 " + os.path.basename(cap))
    return made


def _ask(prompt: str, default: str = "") -> str:
    """输入；EOF（被管道/双击喂空）时退回默认值，不让菜单崩。"""
    try:
        return input(prompt).strip() or default
    except EOFError:
        return default


def cmd_menu() -> None:
    print("=" * 66)
    print("   阿飞说球 · 小红书卡片（HTML + 本机 Chrome 出图）")
    print("=" * 66)
    files = find_card_files()
    if not files:
        print("   没找到任何 cards.json。先让 agent 写一批，再回来。")
        _pause()
        return
    for i, f in enumerate(files, 1):
        print(f"   {i}   {f}")
    print("=" * 66)
    sel = _ask("选一批（序号，回车=最新）：", "1")
    try:
        cards_path = Path(files[int(sel) - 1])
    except Exception:
        print("序号不对。")
        _pause()
        return
    print("   1  按定版风格出正式图到 cards.json 同目录（杂志风 editorial）")
    print("   2  两版试版（editorial + swiss → 同级 试版/，换风格时才用）")
    mode = _ask("怎么出（回车=1）：", "1")
    if mode == "2":
        for st in ("editorial", "swiss"):
            print(f"\n【{st}】")
            build(cards_path, st, cards_path.parent / "试版" / st)
    else:
        made = build(cards_path, "editorial", cards_path.parent)
        print(f"\n完成 → {cards_path.parent}（共 {len(made)} 张）")
    _pause()


def _pause() -> None:
    try:
        input("\n按回车退出…")
    except EOFError:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="小红书卡片 HTML+Chrome 渲染")
    ap.add_argument("--input", default="", help="cards.json 路径")
    ap.add_argument("--style", default="both", choices=["editorial", "swiss", "both"])
    ap.add_argument("--out", default="", help="输出目录（默认 cards.json 同级 试版/<style>）")
    ap.add_argument("--limit", type=int, default=0, help="只出前 N 场")
    ap.add_argument("--engine", default="chrome", choices=["chrome", "playwright", "auto"],
                    help="渲染引擎：chrome=本机 Chrome 逐张截图（默认，零依赖）；"
                         "playwright=复用内置 chromium（快约 2 倍、版本固定）；auto=有 playwright 就用")
    ap.add_argument("--menu", action="store_true", help="交互菜单")
    a = ap.parse_args()

    if a.menu or not a.input:
        cmd_menu()
        return

    cards_path = Path(a.input)
    styles = ["editorial", "swiss"] if a.style == "both" else [a.style]
    for st in styles:
        if a.out:
            out = Path(a.out) / st if a.style == "both" else Path(a.out)
        else:
            # 单一风格（定版）= 就出在 cards.json 同目录（即 📝文章/<日期>/小红书/）
            out = cards_path.parent / ("试版" / st if a.style == "both" else "")
        print(f"\n【{st}】→ {out}")
        made = build(cards_path, st, out, a.limit, a.engine)
        print(f"  共 {len(made)} 张")


if __name__ == "__main__":
    main()
