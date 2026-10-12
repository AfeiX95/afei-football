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
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from xhs_cards import (ROOT, audit, auto_cards, caption_text, find_card_files,  # noqa: E402
                       load_input, safe, write_caption)

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
# 内容块扩展：核心矛盾 / 本次看点 / 近期战绩对比 / 六维雷达（2026-10-12 用户要求）
# --------------------------------------------------------------------------- #
EXTRA_CSS = """
/* 深读卡的小标题 */
.ed h2.sub2{margin:26px 0 0;font-size:54px;line-height:1.15;font-weight:900;letter-spacing:-.01em}
.ed h2.sub2 .vsx{font-family:"Microsoft YaHei UI",sans-serif;font-size:30px;font-weight:400;color:#9d968a;
  margin:0 14px;vertical-align:middle}
.sw h2.sub2{margin:28px 0 0;font-size:56px;line-height:1.08;font-weight:900;letter-spacing:-.02em}
.sw h2.sub2 .vsx{color:#e8402a;margin:0 12px;font-size:40px;vertical-align:4px}
.sw h2.sub2 .tag2{background:#e8402a;color:#fff;font-size:24px;padding:6px 14px;margin-left:18px;vertical-align:10px}
/* —— 核心矛盾 —— */
.ed .cq{margin-top:30px;border-left:9px solid #0a0a0b;padding:2px 0 2px 28px}
.ed .cq .lab{font-size:24px;letter-spacing:.2em;color:#8d867c;font-weight:700}
.ed .cq p{margin:12px 0 0;font-size:37px;line-height:1.48;font-weight:700;color:#141310}
.sw .cq{margin-top:28px;background:#000;color:#fff;padding:24px 26px 26px}
.sw .cq .lab{font-size:23px;letter-spacing:.22em;font-weight:900;color:#e8402a}
.sw .cq p{margin:12px 0 0;font-size:36px;line-height:1.42;font-weight:900}
/* —— 本次看点 —— */
.ed .focus{margin-top:32px;background:rgba(10,10,11,.05);border-left:9px solid #9b5a2e;padding:24px 28px 26px}
.ed .focus .lab{font-size:25px;font-weight:900;letter-spacing:.12em;color:#9b5a2e}
.ed .focus ul{margin:18px 0 0;padding:0;list-style:none}
.ed .focus li{display:flex;gap:18px;font-size:34px;line-height:1.45;color:#1f1d19;
  background:#fff;padding:22px 24px;border-left:6px solid #9b5a2e}
.ed .focus li + li{margin-top:14px}
.ed .focus li b{flex:0 0 34px;font-weight:900;color:#9b5a2e}
.sw .focus{margin-top:30px;border:4px solid #000;padding:22px 24px 24px}
.sw .focus .lab{font-size:24px;font-weight:900;letter-spacing:.16em}
.sw .focus ul{margin:18px 0 0;padding:0;list-style:none}
.sw .focus li{display:flex;gap:18px;font-size:34px;line-height:1.42;
  border:3px solid #000;padding:20px 22px}
.sw .focus li + li{margin-top:14px}
.sw .focus li b{flex:0 0 36px;font-weight:900;color:#e8402a}
/* —— 近期战绩对比 —— */
.ed .form{margin-top:34px}
.ed .radar{margin-top:36px}
.ed .head2{display:flex;justify-content:space-between;align-items:baseline;
  font-size:26px;font-weight:700;letter-spacing:.06em}
.ed .head2 .right{font-size:23px;font-weight:400;color:#8d867c;letter-spacing:.02em}
.ed .frow{display:flex;align-items:center;gap:16px;border-top:2px solid rgba(10,10,11,.16);
  padding:16px 0;flex-wrap:wrap}
.ed .frow .tn{flex:0 0 132px;font-size:31px;font-weight:900}
.ed .pills{display:flex;gap:7px;flex:none}
.ed .pill{width:34px;height:34px;font-size:21px;font-weight:900;
  display:flex;align-items:center;justify-content:center}
.ed .pill.w{background:#0a0a0b;color:#fff}
.ed .pill.d{background:#d5cec2;color:#3a362f}
.ed .pill.l{background:#9b5a2e;color:#fff}
.ed .frow .num{font-size:27px;font-weight:700;color:#26241f}
.ed .frow .sub{flex:1 0 100%;font-size:25px;color:#6f6960;margin-top:4px}
.sw .form{margin-top:32px}
.sw .radar{margin-top:34px}
.sw .head2{display:flex;justify-content:space-between;align-items:baseline;
  border-bottom:3px solid #000;padding-bottom:12px;font-size:27px;font-weight:900;letter-spacing:.1em}
.sw .head2 .right{font-size:22px;font-weight:700;color:#6b6b6b;letter-spacing:.02em}
.sw .frow{display:flex;align-items:center;gap:14px;border-bottom:1px solid rgba(0,0,0,.18);
  padding:16px 0;flex-wrap:wrap}
.sw .frow .tn{flex:0 0 132px;font-size:31px;font-weight:900}
.sw .pills{display:flex;gap:7px;flex:none}
.sw .pill{width:34px;height:34px;font-size:21px;font-weight:900;border:3px solid #000;
  display:flex;align-items:center;justify-content:center}
.sw .pill.w{background:#000;color:#fff}
.sw .pill.d{background:#fff;color:#000}
.sw .pill.l{background:#e8402a;border-color:#e8402a;color:#fff}
.sw .frow .num{font-size:27px;font-weight:900}
.sw .frow .sub{flex:1 0 100%;font-size:25px;color:#3d3d3d;margin-top:4px}
/* —— 六维雷达 —— */
.ed .radar .wrap{display:flex;gap:26px;align-items:center;margin-top:16px}
.ed .radar .lg{font-size:27px;line-height:2.0;color:#26241f}
.sw .radar .wrap{display:flex;gap:22px;align-items:center;margin-top:14px}
.sw .radar .lg{font-size:27px;font-weight:700;line-height:2.0}
.radar .lg i{display:inline-block;width:22px;height:22px;margin-right:12px;vertical-align:-2px}
"""


# --------------------------------------------------------------------------- #
# 单卡全信息版式（2026-10-12 用户要求：每场只要一张卡片体现所有分析信息）
# 思路＝两栏挤压：概率|比分并排、雷达|战意信号并排、看点两列，字号统一降到 76% 左右
# --------------------------------------------------------------------------- #
ALL_CSS = """
.card.all .row2{display:flex;gap:26px}
.card.all .row2 .c1{flex:1.55;min-width:0}
.card.all .row2 .c2{flex:1;min-width:0}
.card.all .tail2{align-items:flex-start}
.card.all .tail2 .c1{flex:0 0 500px}
.card.all .tail2 .c2{flex:1;min-width:0}
/* 单卡里雷达把图例挪到图下面横排（列宽只有 500，图例挤在右边会把队名折断） */
.card.all .radar .wrap{flex-direction:column;align-items:flex-start;gap:4px}
.card.all .radar .lg{display:flex;gap:26px;line-height:1.25}
.card.all .radar .lg>div{white-space:nowrap}
/* 杂志风 */
.ed.all{padding:44px 52px 34px}
.ed.all .top{font-size:23px}
.ed.all .pager{font-size:21px}
.ed.all h1{margin:12px 0 0;font-size:70px;line-height:1.06}
.ed.all h1 .vsx{font-size:32px;margin:0 13px}
.ed.all .rule{margin:12px 0 0;height:3px}
.ed.all .stance{display:flex;align-items:baseline;gap:16px;padding:10px 0 0}
.ed.all .stance .lab{font-size:20px;letter-spacing:.2em}
.ed.all .stance .val{margin-top:0;font-size:45px;line-height:1.06}
.ed.all .cq{margin-top:14px;border-left:6px solid #0a0a0b;padding:0 0 0 18px}
.ed.all .cq .lab{font-size:19px;letter-spacing:.18em}
.ed.all .cq p{margin:6px 0 0;font-size:26px;line-height:1.36;font-weight:700}
.ed.all .sec{margin-top:13px}
.ed.all .sec .head{font-size:21px}
.ed.all .sec .head .right{font-size:19px}
.ed.all .grid3{gap:22px;margin-top:8px}
.ed.all .cl{font-size:19px}
.ed.all .cv{font-size:44px;margin-top:0;letter-spacing:-.02em}
.ed.all .cv .pct{font-size:26px}
.ed.all .bar{height:7px;margin-top:6px}
.ed.all .bar.mkt{height:5px;margin-top:4px}
.ed.all .cm{font-size:19px;margin-top:3px}
.ed.all .scores{gap:13px;margin-top:8px}
.ed.all .sc{padding-top:8px;border-top-width:2px}
.ed.all .sc .sl{font-size:18px}
.ed.all .sc .sv{font-size:34px;margin-top:0}
.ed.all .form{margin-top:10px}
.ed.all .head2{font-size:21px}
.ed.all .head2 .right{font-size:18px}
.ed.all .frow{padding:6px 0;gap:11px;border-top-width:2px}
.ed.all .frow .tn{flex:0 0 104px;font-size:25px}
.ed.all .pills{gap:5px}
.ed.all .pill{width:25px;height:25px;font-size:16px}
.ed.all .frow .num{font-size:22px}
.ed.all .frow .sub{font-size:18px;margin-top:1px}
.ed.all .radar{margin-top:9px}
.ed.all .radar .wrap{gap:13px;margin-top:6px}
.ed.all .radar .lg{font-size:21px;line-height:1.8}
.ed.all .notes{margin-top:11px;gap:10px;padding-top:0}
.ed.all .note{gap:13px;padding-top:9px;border-top-width:2px}
.ed.all .note .nl{flex:0 0 72px;font-size:21px}
.ed.all .note .nl i{width:11px;height:11px;margin-right:6px}
.ed.all .note p{font-size:23px;line-height:1.38}
.ed.all .focus{margin-top:9px;padding:10px 15px 12px;border-left-width:6px}
.ed.all .focus .lab{font-size:20px;letter-spacing:.1em}
.ed.all .focus ul{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}
.ed.all .focus li{padding:9px 12px;font-size:21px;line-height:1.34;border-left-width:5px;gap:10px}
.ed.all .focus li b{flex:0 0 22px}
.ed.all .foot{font-size:21px;padding-top:9px;border-top-width:2px}
.ed.all .foot .tags{font-size:19px;margin-top:3px}
/* 瑞士风 */
.sw.all{padding:40px 52px 30px}
.sw.all .top{font-size:23px;gap:14px}
.sw.all .chip{padding:8px 14px}
.sw.all .top .pager{padding:8px 13px}
.sw.all h1{margin:11px 0 0;font-size:70px;line-height:1}
.sw.all h1 .vsx{font-size:46px;margin:0 11px}
.sw.all .thick{height:6px;margin:11px 0 0}
.sw.all .stance{margin-top:10px;gap:14px}
.sw.all .stance .tab{flex:0 0 10px}
.sw.all .stance .lab{font-size:19px;letter-spacing:.2em;margin-bottom:2px}
.sw.all .stance .val{font-size:43px;line-height:1.05}
.sw.all .cq{margin-top:12px;padding:12px 16px 13px}
.sw.all .cq .lab{font-size:19px;letter-spacing:.2em}
.sw.all .cq p{margin:6px 0 0;font-size:25px;line-height:1.32}
.sw.all .sec{margin-top:12px}
.sw.all .sec .head{border-bottom-width:3px;padding-bottom:7px;font-size:21px}
.sw.all .sec .head .right{font-size:18px}
.sw.all .cell{padding:8px 11px 8px 0}
.sw.all .cell + .cell{padding-left:12px}
.sw.all .cl{font-size:18px}
.sw.all .cv{font-size:44px;margin-top:1px}
.sw.all .cv .pct{font-size:26px}
.sw.all .bar{height:8px;margin-top:7px}
.sw.all .bar.mkt{height:5px;margin-top:4px}
.sw.all .cm{font-size:18px;margin-top:3px}
.sw.all .scores{gap:10px;margin-top:8px}
.sw.all .sc{border-width:3px;padding:7px 10px}
.sw.all .sc .sl{font-size:17px}
.sw.all .sc .sv{font-size:34px;margin-top:0}
.sw.all .form{margin-top:10px}
.sw.all .head2{font-size:21px;padding-bottom:2px}
.sw.all .head2 .right{font-size:18px}
.sw.all .frow{padding:5px 0;gap:9px}
.sw.all .frow .tn{flex:0 0 102px;font-size:25px}
.sw.all .pills{gap:5px}
.sw.all .pill{width:25px;height:25px;font-size:15px;border-width:2px}
.sw.all .frow .num{font-size:21px}
.sw.all .frow .sub{font-size:18px;margin-top:1px}
.sw.all .radar{margin-top:8px}
.sw.all .radar .wrap{gap:12px;margin-top:6px}
.sw.all .radar .lg{font-size:21px;line-height:1.75}
.sw.all .notes{margin-top:10px;gap:9px;padding-top:0}
.sw.all .note{padding-top:8px;gap:11px;border-top-width:2px}
.sw.all .note .nl{font-size:20px}
.sw.all .note .nl span{padding:4px 9px}
.sw.all .note p{font-size:23px;line-height:1.36}
.sw.all .focus{margin-top:8px;padding:9px 12px 10px;border-width:3px}
.sw.all .focus .lab{font-size:19px;letter-spacing:.14em}
.sw.all .focus ul{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
.sw.all .focus li{padding:8px 10px;font-size:21px;line-height:1.32;border-width:2px;gap:9px}
.sw.all .focus li b{flex:0 0 23px}
.sw.all .foot{font-size:20px;padding-top:8px;border-top-width:6px}
.sw.all .foot .tags{font-size:18px;margin-top:3px}
"""

# 数据向单卡（2026-10-12 起小红书定版形态）：继承 .card.all 的紧凑排版，再放大字号把版面填满。
# 只出现官方赛果数据；判断/比分/让球球数/竞彩场次号/机构折算一律不放（坑#69）。
DATA_CSS = """
.card.data .row2 .c1{flex:0 0 500px}
.card.data .row2 .c2{flex:1;min-width:0}
/* 队名 4 个字（国际米兰/比利亚雷/埃因霍温）不能折行；「数据要点」标签也不能折 */
.card.data .frow .tn{flex:0 0 152px}
.card.data .note .nl{flex:0 0 118px}
.ed.data h1{font-size:76px}
.ed.data .cq .lab{color:#9b5a2e}
.ed.data .frow .tn{font-size:27px}
.ed.data .frow .num{font-size:24px}
.ed.data .frow .sub{font-size:19px}
.ed.data .note p{font-size:25px}
.ed.data .focus li{font-size:23px}
.ed.data .radar .lg{font-size:22px}
.ed.data .foot{font-size:22px}
/* 简报（100–200 字）：细发丝线 + 小标签，不复用「左粗条」以免和数据反差撞脸 */
.card.data .brief{margin-top:16px;padding-top:12px;border-top:1px solid rgba(10,10,11,.16)}
.card.data .brief .lab{font-size:21px;font-weight:700;letter-spacing:.16em}
.card.data .brief p{margin:7px 0 0;font-size:22px;line-height:1.5;text-align:justify}
.ed.data .brief .lab{color:#9b5a2e}
.sw.data .brief{border-top-width:3px;border-top-color:#0a0a0b}
.sw.data .brief .lab{color:#e8402a}
.sw.data .brief p{font-size:21px}
.sw.data h1{font-size:76px}
.sw.data .frow .tn{font-size:27px}
.sw.data .frow .num{font-size:23px}
.sw.data .frow .sub{font-size:19px}
.sw.data .note p{font-size:25px}
.sw.data .focus li{font-size:23px}
.sw.data .radar .lg{font-size:22px}
.sw.data .foot{font-size:21px}

/* ── 后台模型块：胜率条 + 比分概率热力图（2026-10-13 起并入同一张卡）──────
   用户 2026-10-12 拍板「模型结果要进卡片」，2026-10-13 再定「只出一张卡」，
   所以模型块不再单开一张，改成左右两栏：左栏＝六维雷达＋胜率条，右栏＝比分概率热力图。 */
.card.data .viz .c1{flex:0 0 448px}
.card.data .viz .c2{flex:1;min-width:0;padding-left:28px;border-left:1px solid rgba(10,10,11,.14)}
.card.data .viz .radar{margin-top:0;padding-top:0}
/* 雷达默认会撑满栏宽（448px 栏→340px 方图），并进单卡后必须按 size 收住，否则整行 590px */
.card.data .viz .radar .wrap svg{width:220px;height:220px;max-width:none;display:block;margin:0 auto}
.card.data .viz .wdl .head2{flex-wrap:nowrap;white-space:nowrap;margin-bottom:10px}
.card.data .viz .wdl .lab{letter-spacing:.08em}
.card.data .viz .wdl{margin-top:14px;padding-top:12px;border-top:1px solid rgba(10,10,11,.16)}
.card.data .heat{margin-top:0;padding-top:0;border-top:0}
.card.data .notesrow .c1,.card.data .notesrow .c2{flex:1 1 0;min-width:0}
.card.data .notesrow .c2{padding-left:28px;border-left:1px solid rgba(10,10,11,.14)}
.card.data .notesrow .note:first-child{margin-top:0}
/* 底部四格一行：看点①② ＋ 战意 ＋ 数据要点（省 ~180px，见 quad_row_html 注释） */
.card.data .quad{display:grid;gap:18px;margin-top:15px}
.card.data .quad .qcell{background:#fff;border-left:3px solid #9b5a2e;padding:9px 12px 10px;min-width:0}
.card.data .quad .qlab{font-size:16px;font-weight:700;letter-spacing:.08em;color:#9b5a2e;margin-bottom:5px}
.card.data .quad p{margin:0;font-size:20px;line-height:1.45;color:#14110d}
.card.data .wdl .hint,.card.data .heat .hint{font-size:18px;color:rgba(10,10,11,.55)}
.wbarwrap{position:relative;margin:14px 0 10px;height:var(--bar)}
.wbar{display:flex;height:var(--bar);overflow:hidden}
.wbar .seg{display:flex;align-items:center;justify-content:center;font-size:21px;font-weight:700;color:#fff;
  font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden}
.wbar .s1{background:#9b5a2e}
.wbar .s2{background:rgba(10,10,11,.36)}
.wbar .s3{background:#3f5f80}
/* 粗点线＝主胜与平的分界，上下都出头，一眼能看出优势在哪边 */
.wmark{position:absolute;top:-9px;bottom:-9px;width:6px;
  background:repeating-linear-gradient(to bottom,#14110d 0 9px,transparent 9px 15px)}
.wmark:after{content:"";position:absolute;left:-7px;top:-10px;border-left:10px solid transparent;
  border-right:10px solid transparent;border-top:11px solid #14110d}
.wlab{display:flex;justify-content:space-between;align-items:baseline;font-size:20px;margin-top:2px}
.wlab .m{font-size:18px;color:rgba(10,10,11,.55)}
/* 热力图：格数 N 由 λ 决定（λ 小画 5×5），列宽行内注入 */
.hgrid{display:grid;gap:3px;width:max-content;margin:12px auto 0}
/* 最高那格描黑框；类名别叫 top——模板里 `.ed.all .top` 是顶栏样式，会把字号顶回 23px */
.hcell{width:var(--cell);height:var(--cell);display:flex;align-items:center;justify-content:center;
  font-size:15px;font-variant-numeric:tabular-nums}
.hcell.hmax{box-shadow:inset 0 0 0 3px #14110d;font-weight:700}
.hcol{width:var(--cell);height:20px;display:flex;align-items:center;justify-content:center;
  font-size:16px;color:rgba(10,10,11,.58)}
.hrowlab{width:40px;height:var(--cell);display:flex;align-items:center;justify-content:flex-end;
  padding-right:7px;font-size:16px;color:rgba(10,10,11,.58)}
.hcorner{width:40px;height:20px}
.hax{display:flex;justify-content:center;gap:44px;font-size:17px;color:rgba(10,10,11,.55);margin-top:4px}
.hfoot{margin-top:8px;font-size:18px;color:rgba(10,10,11,.72);text-align:center}
.hnote{margin-top:6px;font-size:16px;line-height:1.45;color:rgba(10,10,11,.5);text-align:center}
.ed.data .wdl .lab,.ed.data .heat .lab{color:#9b5a2e;font-size:20px;font-weight:700;letter-spacing:.16em}
"""


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


def notes_html(card: dict, cluster: str, labels: tuple = ("战意", "信号")) -> str:
    out = []
    if card.get("will"):
        out.append(f'<div class="note"><div class="nl will"><i></i>{labels[0]}</div><p>{esc(card["will"])}</p></div>')
    if card.get("signal"):
        out.append(f'<div class="note"><div class="nl sig"><i></i>{labels[1]}</div><p>{esc(card["signal"])}</p></div>')
    if card.get("note"):
        out.append(f'<div class="note"><div class="nl more"><i></i>补充</div><p>{esc(card["note"])}</p></div>')
    if not out:
        return ""
    if cluster == "sw":  # 瑞士风：标签做成黑/红块
        out = [o.replace(f'<div class="nl will"><i></i>{labels[0]}</div>',
                         f'<div class="nl will"><span>{labels[0]}</span></div>')
                .replace(f'<div class="nl sig"><i></i>{labels[1]}</div>',
                         f'<div class="nl sig"><span>{labels[1]}</span></div>')
                .replace('<div class="nl more"><i></i>补充</div>', '<div class="nl more"><span>补充</span></div>')
               for o in out]
    return f'<div class="notes">{"".join(out)}</div>'


def footer_html(card: dict) -> str:
    return ('<div class="foot"><div class="l">' + esc(card.get("source", "数据来源：中国体育官方数据平台")) +
            '</div><div class="r">' + esc(card.get("brand", "@阿飞·赛博聊球")) +
            f'<div class="tags">{esc(card.get("tags", ""))}</div></div></div>')


# --------------------------------------------------------------------------- #
# 内容块：核心矛盾 / 本次看点 / 近期战绩对比 / 六维雷达
# --------------------------------------------------------------------------- #
PILL = {"W": ("w", "胜"), "D": ("d", "平"), "L": ("l", "负")}


def radar_svg(radar: dict, cluster: str, size: int = 300, label_font: int = 23) -> str:
    """六维雷达对比（内联 SVG）：两队靠颜色 + 线粗区分，逐轴标出两个数值。"""
    import math  # 本文件其它绘图小工具也是局部导入，保持一致
    dims = list(radar.get("dims") or [])
    try:
        hv = [float(x) for x in (radar.get("home") or [])]
        av = [float(x) for x in (radar.get("away") or [])]
    except Exception:
        return ""
    n = len(dims)
    if n < 3 or len(hv) != n or len(av) != n:
        return ""
    if cluster == "sw":
        c_home, c_away = "#e8402a", "#000000"
        f_home, f_away = "rgba(232,64,42,.16)", "rgba(0,0,0,.08)"
        c_grid, c_lab, c_sep = "rgba(0,0,0,.22)", "#000000", "rgba(0,0,0,.4)"
    else:
        c_home, c_away = "#9b5a2e", "#3f5f80"
        f_home, f_away = "rgba(155,90,46,.16)", "rgba(63,95,128,.10)"
        c_grid, c_lab, c_sep = "rgba(10,10,11,.20)", "#26241f", "rgba(10,10,11,.32)"
    px, py = size + 300, size + 150   # 横向多留 300：六轴标签（5 个字）要比纵向更宽
    cx, cy, r = px / 2.0, py / 2.0 + 4, size / 2.0

    def axis(i):
        a = math.radians(-90 + 360.0 / n * i)
        return math.cos(a), math.sin(a)

    def pt(i, v):
        ca, sa = axis(i)
        rr = r * max(0.0, min(100.0, float(v))) / 100.0
        return cx + rr * ca, cy + rr * sa

    grid = ""
    for k in (0.2, 0.4, 0.6, 0.8, 1.0):
        pts = " ".join("%.1f,%.1f" % (cx + r * k * axis(i)[0], cy + r * k * axis(i)[1]) for i in range(n))
        grid += '<polygon points="%s" fill="none" stroke="%s" stroke-width="%d"/>' % (
            pts, c_grid, 2 if k == 1.0 else 1)
    for i in range(n):
        ca, sa = axis(i)
        grid += '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1"/>' % (
            cx, cy, cx + r * ca, cy + r * sa, c_grid)

    def polygon(vals, stroke, fill, width=4):
        pts = " ".join("%.1f,%.1f" % pt(i, v) for i, v in enumerate(vals))
        return ('<polygon points="%s" fill="%s" stroke="%s" stroke-width="%d" stroke-linejoin="round"/>'
                % (pts, fill, stroke, width))

    dots = ""
    for vals, col in ((hv, c_home), (av, c_away)):
        for i, v in enumerate(vals):
            x, y = pt(i, v)
            dots += '<circle cx="%.1f" cy="%.1f" r="5" fill="%s"/>' % (x, y, col)

    labels = ""
    for i, d in enumerate(dims):
        ca, sa = axis(i)
        lx, ly = cx + (r + 36) * ca, cy + (r + 36) * sa + 8
        anchor = "middle" if abs(ca) < 0.3 else ("start" if ca > 0 else "end")
        labels += ('<text x="%.1f" y="%.1f" text-anchor="%s" font-size="%d" font-weight="700" '
                   'fill="%s">%s</text>' % (lx, ly, anchor, label_font, c_lab, esc(d)))
        labels += ('<text x="%.1f" y="%.1f" text-anchor="%s" font-size="%d">'
                   '<tspan fill="%s" font-weight="700">%.0f</tspan>'
                   '<tspan fill="%s"> / </tspan>'
                   '<tspan fill="%s" font-weight="700">%.0f</tspan></text>'
                   % (lx, ly + 26, anchor, label_font - 2, c_home, hv[i], c_sep, c_away, av[i]))
    return ('<svg width="%d" height="%d" viewBox="0 0 %d %d" xmlns="http://www.w3.org/2000/svg">%s%s%s%s%s%s</svg>'
            % (px, py, px, py, grid, polygon(av, c_away, f_away, 3), polygon(hv, c_home, f_home, 5),
               dots, labels, ""))


def contradiction_html(card: dict, key: str = "contradiction", label: str = "核心矛盾") -> str:
    t = card.get(key) if card.get(key) else card.get("contradiction")
    if not t:
        return ""
    return ('<div class="cq"><div class="lab">%s</div><p>%s</p></div>'
            % (esc(card.get("contradiction_label") or label), esc(t)))


def focus_html(card: dict, label: str = "本次看点") -> str:
    fs = card.get("focus")
    if not fs:
        return ""
    if isinstance(fs, str):
        fs = [fs]
    items = "".join('<li><b>%02d</b><span>%s</span></li>' % (i + 1, esc(t)) for i, t in enumerate(fs))
    return '<section class="focus"><div class="lab">%s</div><ul>%s</ul></section>' % (esc(label), items)


def brief_html(card: dict, label: str = "简报") -> str:
    """100–200 字简报（`xhs_data.py` 从本地赛果缓存生成，可手写覆盖 cards.json 的 `brief`）。"""
    txt = (card.get("brief") or "").strip()
    if not txt:
        return ""
    return '<div class="brief"><div class="lab">%s</div><p>%s</p></div>' % (esc(label), esc(txt))


def form_html(card: dict, compact: bool = False) -> str:
    f = card.get("form") or {}
    h, a = f.get("home") or {}, f.get("away") or {}
    if not h or not a:
        return ""

    def row(t):
        pills = "".join('<span class="pill %s">%s</span>' % PILL.get(x, ("d", "平"))
                        for x in (t.get("seq") or []))
        sub = ("%s · 进 %.1f 失 %.1f · 近 5 场 %d 进 %d 失"
               % (t.get("ha", ""), float(t.get("pj", 0)), float(t.get("sj", 0)),
                  int(t.get("gf", 0)), int(t.get("ga", 0))))
        return ('<div class="frow"><div class="tn">%s</div><div class="pills">%s</div>'
                '<div class="num">%s</div><div class="sub">%s</div></div>'
                % (esc(t.get("name", "")), pills, esc(t.get("l5", "")), esc(sub)))

    if compact:
        # 单卡版式一行放不下长说明：交锋只留短句，且只有真进了雷达才写
        right = "近 5 场 · 左旧→右新"
        if f.get("h2h_used") and f.get("h2h_short"):
            right += " · " + f["h2h_short"]
    else:
        right = "近 5 场 · 左旧→右新" + (" · 交锋 %s" % f["h2h"] if f.get("h2h") else "")
    return ('<section class="form"><div class="head2"><span>近期战绩对比</span>'
            '<span class="right">%s</span></div>%s%s</section>' % (right, row(h), row(a)))


def radar_html(card: dict, cluster: str, size: int = 300, label_font: int = 23) -> str:
    svg = radar_svg(card.get("radar") or {}, cluster, size, label_font)
    if not svg:
        return ""
    c_home, c_away = (("#e8402a", "#000000") if cluster == "sw" else ("#9b5a2e", "#3f5f80"))
    lg = ('<div class="lg"><div><i style="background:%s"></i>%s</div>'
          '<div><i style="background:%s"></i>%s</div></div>'
          % (c_home, esc(card.get("home", "")), c_away, esc(card.get("away", ""))))
    return ('<section class="radar"><div class="head2"><span>六维雷达对比</span>'
            '<span class="right">0–100，越高越强</span></div><div class="wrap">%s%s</div></section>'
            % (svg, lg))


# --------------------------------------------------------------------------- #
# 后台模型块：胜率条 + 比分概率热力图（`xhs_model.py` 算好，卡片只负责画）
# --------------------------------------------------------------------------- #
TEMPLATES = ("A", "B", "C")
TPL_NAME = {"A": "数据页", "B": "模型页", "C": "对照页"}
TPL_HEAT = {"A": 46, "B": 48, "C": 44}       # 热力图单格边长
TPL_BAR = {"A": 42, "B": 46, "C": 38}        # 胜率条高度
TPL_RADAR = {"A": 220, "B": 205, "C": 235}
TPL_STATE = Path(ROOT) / "state" / "xhs_templates.json"


def pick_template(meta: dict, out_dir: Path) -> tuple:
    """每期换一套版式。`cards.json` 的 `template` 字段优先；否则按批次目录轮换并记账。

    轮换表写在 `state/xhs_templates.json`（{批次目录名: 模板, "_last": 模板}），
    所以同一批重出不会跳模板，换一批必然换一个。
    """
    t = str(meta.get("template") or "").strip().upper()
    if t in TEMPLATES:
        return t, "指定"
    key = Path(out_dir).name or "_"
    try:
        st = json.loads(TPL_STATE.read_text(encoding="utf-8"))
        if not isinstance(st, dict):
            st = {}
    except Exception:
        st = {}
    if st.get(key) in TEMPLATES:
        return st[key], "沿用"
    last = st.get("_last")
    try:
        nxt = TEMPLATES[(TEMPLATES.index(last) + 1) % len(TEMPLATES)]
    except ValueError:
        nxt = TEMPLATES[0]
    st[key] = nxt
    st["_last"] = nxt
    TPL_STATE.parent.mkdir(parents=True, exist_ok=True)
    TPL_STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return nxt, "轮换"


def wdl_html(card: dict, tpl: str = "A") -> str:
    """胜率条：左＝主队、右＝客队，中间一条粗点线（主胜/平的分界），三档都带百分比。"""
    md = card.get("model") or {}
    w = md.get("wdl") or []
    if len(w) != 3:
        return ""
    wh, wd, wa = [float(x) * 100 for x in w]
    delta = abs(float(md.get("mc_delta") or 0)) * 100
    n_mc = int(md.get("n_mc") or 0)
    hint = "抽样 %s 次，差 %.1f 个百分点" % (w3(n_mc), delta) if n_mc else ""
    seg = "".join('<div class="seg s%d" style="width:%.2f%%">%.1f%%</div>' % (i, v, v)
                  for i, v in enumerate((wh, wd, wa), 1))
    return ('<section class="wdl" style="--bar:%dpx">'
            '<div class="head2"><span class="lab">后台模型 · 胜率</span>'
            '<span class="hint">%s</span></div>'
            '<div class="wbarwrap"><div class="wbar">%s</div>'
            '<div class="wmark" style="left:%.2f%%"></div></div>'
            '<div class="wlab"><span>%s · 主胜</span><span class="m">平 %.1f%%</span>'
            '<span>%s · 客胜</span></div></section>'
            % (TPL_BAR.get(tpl, 46), esc(hint), seg, wh,
               esc(card.get("home", "")), wd, esc(card.get("away", ""))))


def w3(n: int) -> str:
    """20000 → 2 万；9000 → 9000。"""
    return ("%g 万" % (n / 10000.0)) if n >= 10000 else str(n)


def heat_html(card: dict, tpl: str = "A") -> str:
    """比分概率热力图：颜色越深概率越高；概率最高的那格描黑框。"""
    md = card.get("model") or {}
    g = md.get("grid") or []
    if len(g) != 6 or any(len(r) != 6 for r in g):
        return ""
    cell = TPL_HEAT.get(tpl, 52)
    lam = md.get("lam") or [0, 0]
    # λ 小就只画到 5 球：6 球那几格本来全是空格，画出来只占地方
    n = 5 if max(float(lam[0]), float(lam[1])) <= 2.6 else 6
    pmax = max(max(r[:n]) for r in g[:n]) or 1.0
    shown = sum(sum(r[:n]) for r in g[:n])
    ti, tj = 0, 0
    for i, row in enumerate(g[:n]):
        for j, p in enumerate(row[:n]):
            if p >= g[ti][tj]:
                ti, tj = i, j
    cells = ['<div class="hcorner"></div>']
    cells += ['<div class="hcol">%d</div>' % j for j in range(n)]
    for i, row in enumerate(g[:n]):
        cells.append('<div class="hrowlab">%d</div>' % i)
        for j, p in enumerate(row[:n]):
            al = 0.07 + 0.78 * (p / pmax)
            cls = "hcell hmax" if (i, j) == (ti, tj) else "hcell"
            txt = ("%.1f" % (p * 100)) if p >= 0.02 else ""
            cells.append('<div class="%s" style="background:rgba(155,90,46,%.3f);color:%s">%s</div>'
                         % (cls, al, "#fff" if al >= 0.55 else "#14110d", txt))
    top = md.get("top") or []
    foot = " · ".join("%s %.1f%%" % (t[0], float(t[1]) * 100) for t in top[:3])
    return ('<section class="heat" style="--cell:%dpx">'
            '<div class="head2"><span class="lab">后台模型 · 比分概率</span>'
            '<span class="hint">颜色越深，概率越高</span></div>'
            '<div class="hgrid" style="grid-template-columns:40px repeat(%d,var(--cell))">%s</div>'
            '<div class="hax"><span>↓ 主队进球</span><span>客队进球 →</span></div>'
            '<div class="hfoot">最高三格：%s</div>'
            '<div class="hnote">%d 球以内 %.1f%%；λ %.2f/%.2f，只算 90 分钟。</div></section>'
            % (cell, n, "".join(cells), esc(foot),
               n - 1, shown * 100, float(lam[0]), float(lam[1])))


def vizrow_html(card: dict, cluster: str, tpl: str = "A", heat_left: bool = False) -> str:
    """模型行：左栏＝六维雷达＋胜率条，右栏＝比分概率热力图（B 模板左右互换）。

    没跑过 xhs_model.py（卡片里没有 model）时退回「雷达｜战意与要点」，不影响出图。
    """
    rz = radar_html(card, cluster, TPL_RADAR.get(tpl, 220), 20)
    wd = wdl_html(card, tpl)
    ht = heat_html(card, tpl)
    if not ht:
        nt = notes_html(card, cluster, ("战意", "数据要点"))
        return ('<div class="row2 tail2"><div class="c1">%s</div><div class="c2">%s</div></div>'
                % (rz, nt)) if (rz and nt) else (rz + nt)
    l, r = (ht, rz + wd) if heat_left else (rz + wd, ht)
    return ('<div class="row2 tail2 viz"><div class="c1">%s</div><div class="c2">%s</div></div>'
            % (l, r))


def quad_row_html(card: dict, cluster: str) -> str:
    """底部四格一行：看点①② ＋ 战意 ＋ 数据要点。

    模型块占了雷达行之后，这四块如果各占一行会把卡撑到 1550px（超 110px）。
    压成一行四格后总高约 160px，整卡落回 1370px 左右（2026-10-13）。
    """
    cells = []
    fs = card.get("focus")
    if isinstance(fs, str):
        fs = [fs]
    for i, t in enumerate((fs or [])[:2]):
        if t:
            cells.append(("看点 %02d" % (i + 1), t))
    if card.get("will"):
        cells.append(("战意", card["will"]))
    key = card.get("signal") or card.get("note")
    if key:
        cells.append(("数据要点", key))
    if not cells:
        return ""
    out = "".join('<div class="qcell"><div class="qlab">%s</div><p>%s</p></div>'
                  % (esc(lb), esc(tx)) for lb, tx in cells)
    n = min(len(cells), 4)
    return '<section class="quad" style="grid-template-columns:repeat(%d,1fr)">%s</section>' % (n, out)


def all_card_html(card: dict, meta: dict, style: str, idx: int, total: int, variant: int = 0) -> str:
    """单卡全信息：一张卡装完一场的所有分析（立场·矛盾·概率·比分·战绩·雷达·看点·战意·信号）。

    版面是两栏挤压出来的：概率|比分并排、雷达|战意信号并排、看点两列。
    variant 让偶数场左右互换（概率↔比分、雷达行↔看点行），保证每期不是一张脸。
    """
    css, cluster, _ = STYLES[style]
    merged = dict(meta)
    merged.update(card)
    no, league, kick = card.get("no", ""), card.get("league", ""), card.get("kick", "")
    if style == "editorial":
        top = ('<div class="top"><span>%s · %s · %s</span><span class="pager">%d/%d</span></div>'
               % (esc(league), esc(no), esc(kick), idx, total))
    else:
        top = ('<div class="top"><span class="chip">%s</span><span class="chip no">%s</span>'
               '<span class="time">%s</span><span class="pager">%d/%d</span></div>'
               % (esc(league), esc(no), esc(kick), idx, total))
    sep = '<div class="rule"></div>' if style == "editorial" else '<div class="thick"></div>'
    vs = '%s<span class="vsx">vs</span>%s' % (esc(card.get("home", "")), esc(card.get("away", "")))
    head = '<h1 class="serif">%s</h1>' % vs if style == "editorial" else '<h1>%s</h1>' % vs
    st = ('<div class="stance"><div class="lab">%s</div><div class="val%s">%s</div></div>'
          % (esc(card.get("stance_label") or "我的判断"),
             " serif" if style == "editorial" else "", esc(card.get("stance", ""))))
    pr, sc = probs_html(card, cluster), scores_html(card)
    fm = form_html(card, compact=True)
    rz = radar_html(card, cluster, 200, 20)
    nt = notes_html(card, cluster)
    fc = focus_html(card)
    row1 = '<div class="row2"><div class="c1">%s</div><div class="c2">%s</div></div>' % (
        (sc, pr) if variant % 2 else (pr, sc))
    row2 = ('<div class="row2 tail2"><div class="c1">%s</div><div class="c2">%s</div></div>'
            % (rz, nt)) if (rz and nt) else (rz + nt)
    body = sep + st + contradiction_html(card) + row1 + fm + ((fc + row2) if variant % 2 else (row2 + fc))
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{BASE_CSS}{css}{EXTRA_CSS}{ALL_CSS}</style></head><body>
<div id="fit"><div class="card {cluster} all">
  {top}
  {head}
  {body}
  {footer_html(merged)}
</div></div>{AUTOFIT_JS}</body></html>"""


def data_card_html(card: dict, meta: dict, style: str, idx: int, total: int, variant: int = 0,
                   tpl: str = "A") -> str:
    """数据向单卡（2026-10-12 小红书判罚后的定版形态）。

    只放**官方赛果数据**：数据反差 / 近期战绩对比 / 六维雷达对比 / 数据看点 / 战意·数据要点。
    刻意不出现：立场判断、推荐比分、让球球数、竞彩场次号、机构折算（坑#69 / 坑#70）。
    tpl 决定块序：A 数据页＝反差·战绩·简报·雷达·看点；B＝简报提到战绩前、雷达压轴；
    C＝简报打头、看点在雷达前。variant 再让偶数场把最后两个块互换。
    """
    css, cluster, _ = STYLES[style]
    merged = dict(meta)
    merged.update(card)
    league, kick = card.get("league", ""), card.get("kick", "")
    # 顶栏不写竞彩场次号（「周二004」是指向购彩渠道的信息）
    if style == "editorial":
        top = ('<div class="top"><span>%s · %s</span><span class="pager">%d/%d</span></div>'
               % (esc(league), esc(kick), idx, total))
    else:
        top = ('<div class="top"><span class="chip">%s</span><span class="time">%s</span>'
               '<span class="pager">%d/%d</span></div>'
               % (esc(league), esc(kick), idx, total))
    sep = '<div class="rule"></div>' if style == "editorial" else '<div class="thick"></div>'
    vs = '%s<span class="vsx">vs</span>%s' % (esc(card.get("home", "")), esc(card.get("away", "")))
    head = '<h1 class="serif">%s</h1>' % vs if style == "editorial" else '<h1>%s</h1>' % vs
    cq = contradiction_html(card, key="contrast", label="数据反差")
    fm = form_html(card, compact=True)
    bf = brief_html(card)
    # 2026-10-13 用户定：模型块（胜率条 + 比分概率热力图）并进同一张卡，不再单开一张；
    # 看点/战意/要点压成底部一行四格，否则整卡会顶到 1550px（超出 1440 画布）
    viz = vizrow_html(card, cluster, tpl, heat_left=(tpl == "B"))
    qd = quad_row_html(card, cluster)
    blocks = {"cq": cq, "fm": fm, "bf": bf, "viz": viz, "qd": qd}
    order = {"A": ("cq", "fm", "viz", "bf", "qd"),
             "B": ("cq", "bf", "fm", "viz", "qd"),
             "C": ("bf", "cq", "viz", "fm", "qd")}.get(
        tpl, ("cq", "fm", "viz", "bf", "qd"))
    if variant % 2:
        order = order[:-2] + (order[-1], order[-2])
    body = sep + "".join(blocks[k] for k in order)
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{BASE_CSS}{css}{EXTRA_CSS}{ALL_CSS}{DATA_CSS}</style></head><body>
<div id="fit"><div class="card {cluster} all data tpl{tpl}">
  {top}
  {head}
  {body}
  {footer_html(merged)}
</div></div>{AUTOFIT_JS}</body></html>"""


def model_card_html(card: dict, meta: dict, style: str, idx: int, total: int, variant: int = 0,
                    tpl: str = "A") -> str:
    """后台模型卡（2026-10-12 用户拍板新增）：胜率条 + 比分概率热力图 + 简报。

    和数据卡同源（都只吃公开赛果、不做市场折算），单独一张是因为热力图＋胜率条约 600px，
    塞进数据卡必然超一屏高度被裁。没有 `model` 数据时自动退回数据卡。
    """
    wd, ht = wdl_html(card, tpl), heat_html(card, tpl)
    if not (wd or ht):
        return data_card_html(card, meta, style, idx, total, variant, tpl)
    css, cluster, _ = STYLES[style]
    merged = dict(meta)
    merged.update(card)
    league, kick = card.get("league", ""), card.get("kick", "")
    if style == "editorial":
        top = ('<div class="top"><span>%s · %s · 后台模型</span><span class="pager">%d/%d</span></div>'
               % (esc(league), esc(kick), idx, total))
    else:
        top = ('<div class="top"><span class="chip">%s</span><span class="chip no">后台模型</span>'
               '<span class="time">%s</span><span class="pager">%d/%d</span></div>'
               % (esc(league), esc(kick), idx, total))
    sep = '<div class="rule"></div>' if style == "editorial" else '<div class="thick"></div>'
    vs = '%s<span class="vsx">vs</span>%s' % (esc(card.get("home", "")), esc(card.get("away", "")))
    head = '<h1 class="serif">%s</h1>' % vs if style == "editorial" else '<h1>%s</h1>' % vs
    cq = contradiction_html(card, key="contrast", label="数据反差")
    bf = brief_html(card)
    blocks = {"cq": cq, "wdl": wd, "heat": ht, "bf": bf}
    order = {"A": ("cq", "wdl", "heat", "bf"),
             "B": ("bf", "cq", "wdl", "heat"),
             "C": ("cq", "heat", "wdl", "bf")}.get(tpl, ("cq", "wdl", "heat", "bf"))
    if variant % 2:
        order = order[:-2] + (order[-1], order[-2])
    body = sep + "".join(blocks[k] for k in order)
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{BASE_CSS}{css}{EXTRA_CSS}{ALL_CSS}{DATA_CSS}</style></head><body>
<div id="fit"><div class="card {cluster} all data model tpl{tpl}">
  {top}
  {head}
  {body}
  {footer_html(merged)}
</div></div>{AUTOFIT_JS}</body></html>"""


def card_html(card: dict, meta: dict, style: str, idx: int, total: int,
              kind: str = "data", variant: int = 0, tpl: str = "A") -> str:
    """kind=data 数据向单卡（只放官方赛果数据）；kind=model 后台模型卡（胜率条＋比分概率热力图）；
    kind=all 全信息单卡（含立场/推荐比分，慎用）；kind=judge/form/read 旧三卡。
    variant 让同一批里奇数/偶数张互换块序；tpl 是本期版式（A/B/C）。"""
    if kind == "data":
        return data_card_html(card, meta, style, idx, total, variant, tpl)
    if kind == "model":
        return model_card_html(card, meta, style, idx, total, variant, tpl)
    if kind == "all":
        return all_card_html(card, meta, style, idx, total, variant)
    css, cluster, _ = STYLES[style]
    merged = dict(meta)
    merged.update(card)
    no, league, kick = card.get("no", ""), card.get("league", ""), card.get("kick", "")
    label = {"judge": "判断", "form": "战绩", "read": "深读"}.get(kind, "")
    if style == "editorial":
        tail = (" · " + label) if label else ""
        top = ('<div class="top"><span>%s · %s · %s%s</span><span class="pager">%d/%d</span></div>'
               % (esc(league), esc(no), esc(kick), tail, idx, total))
    else:
        tag = esc(no) + (" " + label if label else "")
        top = ('<div class="top"><span class="chip">%s</span><span class="chip no">%s</span>'
               '<span class="time">%s</span><span class="pager">%d/%d</span></div>'
               % (esc(league), tag, esc(kick), idx, total))
    # 标题与正文之间的分隔：杂志风＝细线，瑞士风＝粗黑条
    sep = '<div class="rule"></div>' if style == "editorial" else '<div class="thick"></div>'
    vs = '%s<span class="vsx">vs</span>%s' % (esc(card.get("home", "")), esc(card.get("away", "")))
    if kind == "judge":
        head = '<h1 class="serif">%s</h1>' % vs
        st = ('<div class="stance"><div class="lab">%s</div><div class="val serif">%s</div></div>'
              % (esc(card.get("stance_label") or "我的判断"), esc(card.get("stance", ""))))
        cq = contradiction_html(card)
        pr, sc = probs_html(card, cluster), scores_html(card)
        body = sep + st + cq + (sc + pr if variant % 2 == 1 else pr + sc)
    elif kind == "form":
        head = '<h2 class="sub2">%s</h2>' % vs
        fm, fc = form_html(card), focus_html(card)
        body = sep + (fc + fm if variant % 2 == 1 else fm + fc)
    else:
        head = '<h2 class="sub2">%s</h2>' % vs
        rz, nt = radar_html(card, cluster), notes_html(card, cluster)
        body = sep + (nt + rz if variant % 2 == 1 else rz + nt)
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>{BASE_CSS}{css}{EXTRA_CSS}</style></head><body>
<div id="fit"><div class="card {cluster}">
  {top}
  {head}
  {body}
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
                                      "六维雷达两条线分别是两队。每场一张卡：判断 · 三向概率 · 比分 · "
                                      "近期战绩 · 本次看点 · 战意信号 · 六维雷达都在里面 →")
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


def build(cards_path: Path, style: str, out_dir: Path, limit: int = 0, engine: str = "chrome",
          kind: str = "data", keep: Path | None = None) -> list[Path]:
    data, cards = load_input(str(cards_path))
    if limit:
        cards = cards[:limit]
    audit([data] + cards)  # 违规词门禁：命中即 sys.exit(2)

    # 有 sporttery_match_id 但缺雷达/战绩的，就地按本地竞彩缓存补算（不改写 cards.json）
    try:
        import xhs_data
        miss = [c for c in cards if c.get("sporttery_match_id") and not (c.get("radar") and c.get("form"))]
        for c in miss:
            c.update(xhs_data.build_one(c, Path(ROOT)))
        if miss:
            print(f"  数据：{len(miss)} 场按本地缓存补算雷达/战绩")
    except Exception as e:  # 缓存缺失不该阻断出图
        print(f"  ⚠️ 雷达/战绩补算失败（{e.__class__.__name__}: {e}），对应块留白")

    # 发布前风控硬门禁（坑#69）：方向 / 让球球数 / 具体比分 / 竞彩场次号 / 机构折算 → 拒绝出图
    if kind in ("data", "dm", "model"):
        try:
            import xhs_riskcheck
            hits = xhs_riskcheck.scan_cards(data, cards)
        except ImportError:
            hits = []
        if hits:
            print("❌ 风控自检拦停：%d 处命中（数据向卡片只放官方赛果数据）" % len(hits))
            for name, frag, where, why in hits[:12]:
                print("   · [%s] %s  ← %s" % (name, frag, where))
            print("   完整报告：python scripts/xhs_riskcheck.py <cards.json>")
            sys.exit(2)

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
    ALL_KINDS = [("judge", "判断"), ("form", "战绩"), ("read", "深读")]
    if kind in ("all", "data", "model"):     # 单卡：每场一张，文件名不带后缀（model 会带 _模型）
        kinds = [(kind, "")] if kind != "model" else [("model", "模型")]
    elif kind in ("dm", "data+model"):       # 每场两张：数据卡 + 后台模型卡（2026-10-13 起并成一张，此模式留作备用）
        kinds = [("data", ""), ("model", "模型")]
    elif kind in ("full", "both"):           # 每场三张（判断/战绩/深读）
        kinds = ALL_KINDS
    else:
        kinds = [k for k in ALL_KINDS if k[0] == kind] or ALL_KINDS[:1]
    per = len(kinds)
    total = len(cards) * per + 1
    tpl, how = pick_template(data, out_dir)
    print("  版式：%s · %s（%s；cards.json 写 \"template\" 可指定）" % (tpl, TPL_NAME[tpl], how))
    jobs = [("01_封面", cover_html({**data, "matches": None}, data.get("cover_items") or [], total, style))]
    n = 1
    for i, m in enumerate(cards):
        base = safe("%s_%svs%s" % (m.get("no") or "", m.get("home") or "", m.get("away") or ""))
        for k, suffix in kinds:
            n += 1
            name = ("%02d_%s" % (n, base)) if not suffix else ("%02d_%s_%s" % (n, base, suffix))
            jobs.append((name, card_html(m, data, style, n, total, k, i, tpl)))

    plans = []
    if keep:
        keep.mkdir(parents=True, exist_ok=True)
        if (tmp / "font-serif.ttf").exists():
            shutil.copy2(tmp / "font-serif.ttf", keep / "font-serif.ttf")
    for name, doc in jobs:
        hp = tmp / f"{name}.html"
        hp.write_text(doc, encoding="utf-8")
        if keep:
            (keep / f"{name}.html").write_text(doc, encoding="utf-8")
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
    shutil.rmtree(tmp, ignore_errors=True)  # HTML/字体已按需复制到 --html-out，临时目录总是清掉
    if made and style == "editorial":
        data["per_match_cards"] = per
        data["card_mode"] = "data" if kind in ("data", "dm", "model") else kind
        cap = caption_text(data, cards)
        # 正文也要过闸：2026-10-13 实测判点在正文文字（同一张卡把正文改纯技术面后一次通过），
        # 所以除了通用词表，再过一遍「正文专属」规则（禁比分猜测/概率数字）
        try:
            import xhs_riskcheck
            hits = xhs_riskcheck.scan_text(cap, "文案正文")
            hits += xhs_riskcheck.scan_caption(cap)
        except ImportError:
            hits = []
        if hits:
            print("❌ 文案没过风控（%d 处）：" % len(hits))
            for name, frag, where, why in hits[:12]:
                print("   · [%s] %s  ← %s" % (name, frag, where))
            sys.exit(2)
        (out_dir / "文案.md").write_text(cap, encoding="utf-8")
        print("  📝 文案.md · 版式 " + tpl)
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
    ap.add_argument("--kind", default="data",
                    choices=["data", "dm", "model", "all", "full", "judge", "form", "read"],
                    help="每场出几张：data=单卡（默认：数据＋后台模型胜率/比分概率热力图，小红书定版）、"
                         "dm=数据卡＋后台模型卡两张、model=只出模型卡、"
                         "all=全信息单卡（含立场/推荐比分，小红书会判违规，慎用）、"
                         "full=判断卡+战绩卡+深读卡、judge/form/read=只出对应卡")
    ap.add_argument("--html-out", default="", help="另存中间 HTML 到该目录（排版诊断用）")
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
        made = build(cards_path, st, out, a.limit, a.engine, a.kind,
                     Path(a.html_out) if a.html_out else None)
        print(f"  共 {len(made)} 张")


if __name__ == "__main__":
    main()
