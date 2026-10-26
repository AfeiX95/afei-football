# -*- coding: utf-8 -*-
"""配色、字体、共享 CSS 与小型格式化工具。"""
from __future__ import annotations

import datetime as _dt
import html as _html
import json
from pathlib import Path

COLORS = {
    "background": "#071019",
    "panel": "#091725",
    "green": "#00F078",
    "green_dark": "#005A40",
    "cyan": "#00D8D8",
    "white": "#F0F5FF",
    "muted": "#91A2BA",
    "home": "#183B63",
    "away": "#632334",
    "border": "#006D51",
}

FONT = '"Noto Sans SC","Microsoft YaHei","PingFang SC",sans-serif'
MONO = '"JetBrains Mono","Consolas","Menlo",monospace'

BASE_CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{COLORS['background']}}}
body{{font-family:{FONT};color:{COLORS['white']};-webkit-font-smoothing:antialiased}}
.root{{position:relative;width:var(--w);height:var(--h);overflow:hidden;
  background:
    radial-gradient(760px 420px at 12% 2%,rgba(0,240,120,.13),transparent 62%),
    radial-gradient(620px 460px at 92% 16%,rgba(0,216,216,.09),transparent 64%),
    repeating-linear-gradient(0deg,rgba(255,255,255,.035) 0 1px,transparent 1px 54px),
    repeating-linear-gradient(90deg,rgba(255,255,255,.035) 0 1px,transparent 1px 54px),
    {COLORS['background']}}}
.art{{position:absolute;inset:0;width:100%;height:100%;display:block}}
.ball{{display:block}}
.hud{{position:absolute;width:26px;height:26px}}
.hud.tl{{left:22px;top:22px}} .hud.tr{{right:22px;top:22px;transform:scaleX(-1)}}
.hud.bl{{left:22px;bottom:22px;transform:scaleY(-1)}} .hud.br{{right:22px;bottom:22px;transform:scale(-1,-1)}}
.mono{{font-family:{MONO};letter-spacing:.12em}}
.g{{color:{COLORS['green']}}}
.muted{{color:{COLORS['muted']}}}
.crest.logo img,.cr.logo img,.logo img{{width:100%;height:100%;object-fit:contain;display:block;padding:5%}}
.crest.logo,.cr.logo{{background:radial-gradient(circle at 50% 34%,rgba(255,255,255,.10),rgba(7,16,25,.66))}}
"""

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def esc(s) -> str:
    return _html.escape("" if s is None else str(s))


def weekday_cn(date_iso: str) -> str:
    d = _dt.date.fromisoformat(date_iso)
    return WEEKDAYS[d.weekday()]


def md_date(date_iso: str) -> str:
    d = _dt.date.fromisoformat(date_iso)
    return "%d.%02d" % (d.month, d.day)


def short_date(date_iso: str) -> str:
    d = _dt.date.fromisoformat(date_iso)
    return "%d/%02d" % (d.month, d.day)


def uniq(seq):
    out = []
    for x in seq:
        if x and x not in out:
            out.append(x)
    return out


def team_colors(name: str) -> tuple[str, str]:
    """队徽缺失时的降级方案：按队名哈希取一对稳定配色（深底 + 亮环）。"""
    h = 0
    for ch in str(name):
        h = (h * 131 + ord(ch)) % 360
    return "hsl(%d 55%% 22%%)" % h, "hsl(%d 82%% 62%%)" % h


def load_theme(path: str | Path | None = None) -> dict:
    if path and Path(path).exists():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return {"colors": COLORS, "font": FONT, "mono": MONO}
