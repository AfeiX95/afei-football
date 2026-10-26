# -*- coding: utf-8 -*-
"""赛博海报风封面（日期 + 赛事信息版）

按参考图的「大字标题 + 实拍球场 + 荧光绿 HUD」做两版：
  3:4  小红书封面（1080x1440）
  16:9 头条封面（1920x1080）
背景用本地已生成的球场照片（state/tmp/gen/），无照片时退回纯黑渐变。

用法：
  python -X utf8 scripts/cover/poster.py --ratio 3:4  --out "📝文章/20261023/封面_赛博"
  python -X utf8 scripts/cover/poster.py --ratio 16:9 --out "📝文章/20261023/封面_赛博"
"""
from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

GREEN = "#00F078"
CYAN = "#22E0E0"
BG = "#050B12"

KICK_SLOTS = ["13:00", "14:00", "19:30", "21:00", "22:00", "00:00", "00:30", "02:45"]

DEFAULT_MATCHES = [
    ("13:00", "首尔FC", "江原FC", "韩职"),
    ("14:00", "神户胜利", "町田泽维", "日职"),
    ("14:00", "鹿岛鹿角", "柏太阳神", "日职"),
    ("19:30", "维拉", "曼城", "英超"),
    ("00:00", "那不勒斯", "罗马", "意甲"),
    ("00:30", "切尔西", "热刺", "英超"),
    ("21:00", "科莫", "萨索洛", "意甲"),
    ("22:00", "阿森纳", "埃弗顿", "英超"),
]


def uri(p: Path) -> str:
    return p.resolve().as_uri().replace("&", "&quot;")


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def rows_html(matches, limit: int) -> str:
    out = []
    for t, h, a, lg in matches[:limit]:
        out.append(
            f'<div class="mrow"><span class="mt">{esc(t)}</span>'
            f'<span class="ml">{esc(lg)}</span>'
            f'<span class="mh">{esc(h)}</span><span class="mv">VS</span>'
            f'<span class="ma">{esc(a)}</span></div>'
        )
    return "".join(out)


def build(ratio: str, date: str, weekday: str, matches, bg: Path | None, note: str) -> str:
    w, h = (1080, 1440) if ratio == "3:4" else (1920, 1080)
    portrait = ratio == "3:4"
    bg_css = f'background-image:url("{uri(bg)}")' if bg and bg.exists() else ""
    title_size = 150 if portrait else 118
    rows_limit = 4 if portrait else 6
    pad = 56 if portrait else 72

    wide_css = "" if portrait else f"""
    .title{{margin-top:14px}}
    .sub{{margin-top:12px;font-size:23px}}
    .meta{{margin-top:14px}}
    .date b{{font-size:44px}}
    .date span,.note{{font-size:21px}}
    .rows{{margin-top:14px;gap:10px}}
    .mrow{{grid-template-columns:88px 108px 1fr 56px 1fr;padding:11px 16px}}
    .mh,.ma{{font-size:22px}}
    .mt{{font-size:19px}}
    .ml{{font-size:16px}}
    .body{{display:flex;gap:44px;margin-top:6px}}
    .left{{flex:0 0 50%}}
    .right{{flex:1;padding-top:36px}}
    .rows{{margin-top:0}}
    .feats{{padding:10px 16px}}
    .ft{{font-size:20px}}
    .fd{{font-size:15px}}
    """

    css = f"""
    *{{box-sizing:border-box;margin:0;padding:0}}
    html,body{{width:{w}px;height:{h}px;overflow:hidden;background:{BG}}}
    body{{font-family:"Noto Sans SC","Microsoft YaHei",sans-serif;color:#EAF2FF}}
    .wrap{{position:relative;width:{w}px;height:{h}px;padding:{pad}px;display:flex;flex-direction:column}}
    .bg{{position:absolute;inset:0;{bg_css};background-size:cover;background-position:{'center 34%' if portrait else 'center 46%'}}}
    .bg::after{{content:"";position:absolute;inset:0;background:
      linear-gradient(180deg,{BG}f2 0%,{BG}b3 26%,{BG}26 48%,{BG}cc 82%,{BG} 100%)}}
    .grid{{position:absolute;inset:0;background-image:
      linear-gradient(rgba(0,240,120,.05) 1px,transparent 1px),
      linear-gradient(90deg,rgba(0,240,120,.05) 1px,transparent 1px);
      background-size:48px 48px;mix-blend-mode:screen;opacity:.5}}
    .scan{{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(0,240,120,.045) 0 1px,transparent 1px 4px);
      mix-blend-mode:screen;opacity:.35}}
    .col{{position:relative;z-index:3;display:flex;flex-direction:column;height:100%}}

    .top{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px}}
    .brand{{display:flex;gap:16px;align-items:flex-start}}
    .bar{{width:12px;height:64px;background:{GREEN};box-shadow:0 0 22px {GREEN}aa}}
    .bn{{font-size:{44 if portrait else 46}px;font-weight:900;letter-spacing:.02em;line-height:1.1}}
    .bs{{margin-top:8px;font-size:{24 if portrait else 26}px;color:#9FB2C8;font-weight:700;letter-spacing:.04em}}
    .quote{{text-align:right;font-size:{22 if portrait else 24}px;color:#B9CBDE;line-height:1.6;font-weight:600}}
    .quote em{{display:block;color:#5E7488;font-style:normal;font-size:.86em}}

    .title{{margin-top:{34 if portrait else 26}px}}
    .l1{{display:block;font-size:{title_size}px;font-weight:900;letter-spacing:-.01em;line-height:.98;
        color:#F4F8FF;text-shadow:0 0 30px rgba(0,240,120,.28),0 6px 0 rgba(0,0,0,.45);
        transform:skewX(-7deg);transform-origin:left center;padding-right:10px}}
    .l2{{display:block;font-size:{title_size}px;font-weight:900;line-height:.98;color:{GREEN};letter-spacing:.02em;
        text-shadow:0 0 34px rgba(0,240,120,.55),0 0 90px rgba(0,240,120,.28);
        transform:skewX(-7deg);transform-origin:left center;margin-top:{4 if portrait else 2}px}}
    .sub{{margin-top:{20 if portrait else 16}px;font-size:{26 if portrait else 28}px;font-weight:800;color:#DCE8F6;letter-spacing:.08em}}
    .sub i{{color:{GREEN};font-style:normal;margin:0 10px}}

    .meta{{margin-top:{22 if portrait else 18}px;display:flex;align-items:center;gap:{18 if portrait else 22}px}}
    .date{{display:flex;align-items:baseline;gap:12px;padding:{10 if portrait else 8}px {20 if portrait else 22}px;
        border:1px solid {GREEN}88;border-radius:10px;background:rgba(0,240,120,.10);
        box-shadow:0 0 26px rgba(0,240,120,.22) inset}}
    .date b{{font-size:{50 if portrait else 54}px;font-weight:900;color:{GREEN};letter-spacing:.02em}}
    .date span{{font-size:{24 if portrait else 26}px;font-weight:800;color:#DDF3E6}}
    .note{{font-size:{22 if portrait else 24}px;font-weight:700;color:#9FB2C8;letter-spacing:.04em}}

    .rows{{margin-top:{26 if portrait else 18}px;display:grid;grid-template-columns:1fr;gap:{10 if portrait else 8}px}}
    .mrow{{display:grid;grid-template-columns:{'74px 96px 1fr 52px 1fr' if portrait else '86px 110px 1fr 60px 1fr'};
        align-items:center;gap:10px;padding:{10 if portrait else 8}px 16px;border-radius:8px;
        background:linear-gradient(90deg,rgba(6,20,30,.86),rgba(6,20,30,.42));
        border-left:3px solid rgba(0,240,120,.72)}}
    .mt{{font-family:ui-monospace,Menlo,monospace;font-size:{20 if portrait else 21}px;color:{GREEN};font-weight:700}}
    .ml{{font-size:{17 if portrait else 18}px;color:#7E93A8;font-weight:700}}
    .mh{{font-size:{24 if portrait else 26}px;font-weight:900;color:#EEF5FF;text-align:right}}
    .ma{{font-size:{24 if portrait else 26}px;font-weight:900;color:#EEF5FF;text-align:left}}
    .mv{{font-size:{14 if portrait else 15}px;color:#5E7488;font-weight:900;text-align:center;letter-spacing:.08em}}

    .chips{{margin-top:{22 if portrait else 0}px;display:{'flex' if portrait else 'none'};flex-wrap:wrap;gap:10px;
        align-items:center}}
    .chip{{font-size:19px;font-weight:800;color:#BFE9D2;padding:7px 14px;border-radius:999px;
        border:1px solid rgba(0,240,120,.34);background:rgba(0,240,120,.07)}}
    .chips .lab{{font-size:18px;color:#7E93A8;font-weight:800;letter-spacing:.08em;margin-right:4px}}
    .spacer{{flex:1}}
    .feats{{display:flex;gap:{12 if portrait else 16}px;padding:{16 if portrait else 14}px {18 if portrait else 20}px;
        border:1px solid rgba(0,240,120,.5);border-radius:12px;background:rgba(4,14,20,.82);
        backdrop-filter:blur(6px)}}
    .feat{{flex:1;display:flex;gap:{12 if portrait else 14}px;align-items:center;
        border-right:1px solid rgba(0,240,120,.18);padding-right:{12 if portrait else 14}px}}
    .feat:last-child{{border-right:0;padding-right:0}}
    .fi{{color:{GREEN};flex:0 0 auto}}
    .ft{{font-size:{22 if portrait else 23}px;font-weight:900;color:#EAF2FF}}
    .fd{{font-size:{16 if portrait else 17}px;color:#8FA3B7;font-weight:700;margin-top:3px}}
    """

    icons = {
        "cal": '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>',
        "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
        "chart": '<path d="M4 20V9M10 20V4M16 20v-7M22 20H2"/>',
    }

    def feat(kind: str, t: str, d: str) -> str:
        return (f'<div class="feat"><svg class="fi" width="30" height="30" viewBox="0 0 24 24" fill="none" '
                f'stroke="currentColor" stroke-width="1.9" stroke-linecap="round">{icons[kind]}</svg>'
                f'<div><div class="ft">{esc(t)}</div><div class="fd">{esc(d)}</div></div></div>')

    title_block = (
        '<div class="title"><div class="l1">足球赛事</div><div class="l2">前瞻</div></div>'
        '<div class="sub">数据拆解<i>/</i>赛况分析<i>/</i>风险提示</div>'
        '<div class="meta">'
        f'<div class="date"><b>{esc(date)}</b><span>{esc(weekday)}</span></div>'
        f'<div class="note">{esc(note)}</div></div>'
    )
    if not portrait:
        body = ('<div class="body"><div class="left">' + title_block + '</div>'
                '<div class="right">' + rows_html(matches, rows_limit) + '</div></div>')
    else:
        chips = "".join(f'<span class="chip">{t}</span>' for t in KICK_SLOTS)
        body = (title_block + '<div class="rows">' + rows_html(matches, rows_limit) + '</div>'
                + '<div class="chips"><span class="lab">开球时段</span>' + chips + '</div>')

    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>{css}{wide_css}</style></head>
<body><div class="wrap">
  <div class="bg"></div><div class="grid"></div><div class="scan"></div>
  <div class="col">
    <div class="top">
      <div class="brand"><div class="bar"></div>
        <div><div class="bn">阿飞 · 赛博聊球</div><div class="bs">用数据拆解比赛</div></div>
      </div>
      <div class="quote">数据不会说谎，<br>但人会。<em>—— 阿飞</em></div>
    </div>
    {body}
    <div class="spacer"></div>
    <div class="feats">
      {feat("cal", "每日更新", "精选多场赛事分析")}
      {feat("target", "公开口径", "公开数据 + 结构推演")}
      {feat("chart", "理性分析", "拒绝情绪化判断")}
    </div>
  </div>
</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratio", choices=["3:4", "16:9"], default="3:4")
    ap.add_argument("--out", required=True)
    ap.add_argument("--date", default="10.24")
    ap.add_argument("--weekday", default="周五")
    ap.add_argument("--note", default="27 场在售 · 早场日韩 + 夜场焦点")
    ap.add_argument("--bg", default="")
    ap.add_argument("--matches", default="")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    w, h = (1080, 1440) if a.ratio == "3:4" else (1920, 1080)

    def sort_key(m):
        t = m[0]
        return (1 if t < "12:00" else 0, t)

    if a.matches:
        data = json.loads(Path(a.matches).read_text(encoding="utf-8"))
        matches = [(m["kick"], m["home"], m["away"], m["league"]) for m in data]
        matches.sort(key=sort_key)
    else:
        matches = sorted(DEFAULT_MATCHES, key=sort_key)

    if a.bg:
        bg = Path(a.bg)
    else:
        bg = ROOT / ("state/tmp/gen/stadium_v1.png" if a.ratio == "3:4" else "state/tmp/gen/stadium_wide.png")

    html_text = build(a.ratio, a.date, a.weekday, matches, bg, a.note)
    tmp = Path(tempfile.mkdtemp(prefix="poster_"))
    src = tmp / "p.html"
    src.write_text(html_text, encoding="utf-8")
    png = out / f"封面_{a.ratio.replace(':', 'x')}.png"
    cmd = [CHROME, "--headless=new", "--hide-scrollbars", "--disable-gpu",
           "--allow-file-access-from-files", "--force-device-scale-factor=2",
           f"--window-size={w},{h}", f"--screenshot={png.resolve()}", "--virtual-time-budget=3000",
           src.as_uri()]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not png.exists():
        print("渲染失败：", (r.stderr or b"").decode("utf-8", "ignore")[-600:])
        return 1
    print(f"✅ {png.name}  {png.stat().st_size // 1024}KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
