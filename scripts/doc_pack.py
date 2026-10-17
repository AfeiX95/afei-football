#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
doc_pack.py — 把 model.py 的文本输出编成「全维度拆解」样册 PDF（P0，2026-10-17）

用途：付费资料 P0 样册 = 当天全部场次的六维度拆解（λ / 胜平负 / 让球 / 总进球与大小球 /
比分分布 / 双方进球），文字可搜的 PDF，不是图片版。

数据源（都不重算，只整理）：
  --model  state/_model_YYYYMMDD_xxx.txt   model.py --all 的落盘输出（真源）
  --cards  📝文章/.../cards.json            可选：取近期战绩 / 六维雷达 / 简报（R1 基本面板块）

用法：
  python scripts/doc_pack.py
  python scripts/doc_pack.py --model state/_model_20261016_fri.txt \
      --cards "📝文章/20261016/小红书_周五八场/cards.json" \
      --out "📝文章/20261016/付费资料_全维度拆解_样册_v0.1.pdf"
  python scripts/doc_pack.py --html-only      # 只出 HTML，调版式用

实现要点：
  1. Chrome 的 --print-to-pdf 对中文路径不稳，HTML/PDF 全部先写 ASCII 临时目录，最后 copy 到目标路径
  2. 一场一页（CSS break-before: page），页脚页码由 @page 计数
  3. 不打分、不给方向、不出现下注动作词（付费资料风控口径见 付费资料_全维度拆解方案_构想.md）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
STATE_BATCH = STATE / "batch"   # 分层后模型文本落在 state/batch/

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

MONTHS = None  # 占位，避免误用


# ── 解析 model.py 文本 ────────────────────────────────────────────────────
RE_HEAD = re.compile(r"^(\S+?)\s{2}(.+?) vs (.+?)\s{3}\[([^\]]+)\]\s+id=(\d+)\s*$")
RE_L1 = re.compile(r"方法1 实际数据法\(主客分离\)\s+([\d.]+)\s+([\d.]+)")
RE_L2 = re.compile(r"方法2 市场反推法\s+([\d.]+)\s+([\d.]+)")
RE_LX = re.compile(r"综合 λ\s+([\d.]+)\s+([\d.]+)\s+双法一致:(\S+)")
RE_LT = re.compile(r"λ总 = ([\d.]+)")
RE_MIX = re.compile(r"分离/近10场混合: 主攻([\d.]+)\(联赛主场w=([\d.]+)\) 客防([\d.]+) 客攻([\d.]+) 主防([\d.]+)")
RE_FIX = re.compile(r"修正明细: form主([+-][\d.]+) form客([+-][\d.]+) \| H2H factor ([\d.]+) \((.+?)\)")
RE_INJ = re.compile(r"伤停 主(\d+)人/客(\d+)人")
RE_WDL = re.compile(
    r"胜平负\s+模型\s+([\d.]+)%\s*/\s*([\d.]+)%\s*/\s*([\d.]+)%\s+市场\(去水\)\s+"
    r"([\d.]+)%\s*/\s*([\d.]+)%\s*/\s*([\d.]+)%")
RE_EDGE_L = re.compile(r"Edge\(模型-市场\) 主\s+([+-][\d.]+)pp\s+平\s+([+-][\d.]+)pp\s+客\s+([+-][\d.]+)pp")
RE_ODD = re.compile(r"固定奖金\s+([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)\s+返还率 ([\d.]+)%")
RE_HCP = re.compile(
    r"让球\(([+-]\d+)\)\s+模型\s+([\d.]+)%\s*/\s*([\d.]+)%\s*/\s*([\d.]+)%\s+市场\(去水\)\s+"
    r"([\d.]+)%\s*/\s*([\d.]+)%\s*/\s*([\d.]+)%")
RE_EDGE_U = re.compile(r"^Edge\(模型-市场\)\s+([+-][\d.]+)pp\s+([+-][\d.]+)pp\s+([+-][\d.]+)pp\s*$")
RE_WR = re.compile(r"胜率\(不含平\)：主 ([\d.]+)% / 客 ([\d.]+)%")
RE_TG = re.compile(r"总进球\s+0:\s*([\d.]+)%\s+1:\s*([\d.]+)%\s+2:\s*([\d.]+)%\s+3:\s*([\d.]+)%\s+4:\s*([\d.]+)%\s+5:\s*([\d.]+)%\s+6:\s*([\d.]+)%\s+7\+:\s*([\d.]+)%")
RE_OU = re.compile(r"大1\.5 ([\d.]+)%\s+大2\.5 ([\d.]+)%\s+大3\.5 ([\d.]+)%\s+双方进球 ([\d.]+)%")
RE_CRS = re.compile(r"^\s+(\d)-(\d)\s+([\d.]+)%\s+(\S+)\s+(EV\s+[+-][\d.]+|—)\s*$")


def parse_model_txt(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    # 按 78 个 = 的横线切块
    blocks: list[list[str]] = []
    cur: list[str] = []
    for line in text.splitlines():
        if line.startswith("=" * 78):
            if cur:
                blocks.append(cur)
            cur = []
            continue
        cur.append(line)
    if cur:
        blocks.append(cur)

    out: list[dict] = []
    for blk in blocks:
        head = next((ln for ln in blk if RE_HEAD.match(ln.strip())), None)
        if not head:
            continue
        h = RE_HEAD.match(head.strip())
        m: dict = {
            "no": h.group(1), "home": h.group(2).strip(), "away": h.group(3).strip(),
            "league": h.group(4), "mid": h.group(5),
            "note": "", "warn": [], "scores": [],
        }
        joined = "\n".join(blk)
        for ln in blk:
            s = ln.strip()
            if s.startswith("备注："):
                m["note"] = s[len("备注："):].strip()
            elif (g := RE_L1.search(s)):
                m["l1h"], m["l1a"] = float(g.group(1)), float(g.group(2))
            elif (g := RE_L2.search(s)):
                m["l2h"], m["l2a"] = float(g.group(1)), float(g.group(2))
            elif (g := RE_LX.search(s)):
                m["lh"], m["la"], m["agree"] = float(g.group(1)), float(g.group(2)), g.group(3)
            elif (g := RE_LT.search(s)):
                m["lam_total"] = float(g.group(1))
            elif (g := RE_MIX.search(s)):
                m["mix"] = [float(g.group(i)) for i in range(1, 6)]
            elif (g := RE_FIX.search(s)):
                m["form_adj"] = [float(g.group(1)), float(g.group(2))]
                m["h2h_f"], m["h2h_tag"] = float(g.group(3)), g.group(4)
            elif (g := RE_INJ.search(s)):
                m["inj"] = [int(g.group(1)), int(g.group(2))]
            elif (g := RE_WDL.search(s)):
                m["wdl_model"] = [float(g.group(i)) for i in (1, 2, 3)]
                m["wdl_market"] = [float(g.group(i)) for i in (4, 5, 6)]
            elif (g := RE_EDGE_L.search(s)):
                m["wdl_edge"] = [float(g.group(i)) for i in (1, 2, 3)]
            elif (g := RE_ODD.search(s)):
                m["odds"] = [float(g.group(i)) for i in (1, 2, 3)]
                m["payout"] = float(g.group(4))
            elif (g := RE_HCP.search(s)):
                m["hline"] = int(g.group(1))
                m["hcp_model"] = [float(g.group(i)) for i in (2, 3, 4)]
                m["hcp_market"] = [float(g.group(i)) for i in (5, 6, 7)]
            elif (g := RE_EDGE_U.match(s.replace("Edge(模型-市场)", "Edge(模型-市场)"))):
                # 无标签的 Edge 行 = 让球那行（胜平负那行带 主/平/客 标签）
                if "hcp_edge" not in m:
                    m["hcp_edge"] = [float(g.group(i)) for i in (1, 2, 3)]
            elif (g := RE_WR.search(s)):
                m["winrate"] = [float(g.group(1)), float(g.group(2))]
            elif (g := RE_TG.search(s)):
                m["tg"] = [float(g.group(i)) for i in range(1, 9)]
            elif (g := RE_OU.search(s)):
                m["ou"] = [float(g.group(i)) for i in range(1, 5)]
            elif (g := RE_CRS.match(ln)):
                m["scores"].append({
                    "i": int(g.group(1)), "j": int(g.group(2)), "p": float(g.group(3)),
                    "odd": g.group(4), "ev": g.group(5),
                })
        # 8B 提示：从「置信度三重检查」之后、空行之前
        tail = joined.split("置信度三重检查", 1)
        if len(tail) == 2:
            for ln in tail[1].splitlines()[1:]:
                s = ln.strip()
                if not s:
                    break
                m["warn"].append(s)
        out.append(m)
    return out


# ── 合并 cards.json（基本面） ─────────────────────────────────────────────
def load_cards(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    d = json.loads(path.read_text(encoding="utf-8"))
    by_no = {}
    for c in d.get("matches", []):
        by_no[c.get("no", "")] = c
    return by_no


# ── HTML ────────────────────────────────────────────────────────────────
CSS = """
@page { size: A4; margin: 10mm 10mm 12mm 10mm; }
@page :first { margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: "Microsoft YaHei","PingFang SC","Noto Sans SC",sans-serif;
       color: #1b1b1b; font-size: 9.2pt; line-height: 1.42; }
.cover { height: 297mm; padding: 26mm 20mm; background: #10202f; color: #fff; page-break-after: always; }
.cover .kicker { display:inline-block; background:#b8322a; padding:2mm 5mm; font-size:9.5pt; letter-spacing:.12em; }
.cover .date { margin-top:16mm; font-size:13pt; color:#e8b4ae; letter-spacing:.08em; }
.cover h1 { margin:4mm 0 0; font-size:34pt; line-height:1.18; font-weight:900; }
.cover .sub { margin-top:6mm; font-size:12pt; color:#cfd8e3; }
.cover .rule { margin:9mm 0 0; height:1.2mm; background:#b8322a; width:46mm; }
.cover .meta { position:absolute; bottom:22mm; left:20mm; right:20mm; font-size:9pt; color:#9fb0c2;
               border-top:.3mm solid #33506b; padding-top:4mm; }
.cover .list { margin-top:10mm; font-size:10.5pt; color:#e6edf5; }
.cover .list div { padding:1.4mm 0; border-bottom:.2mm solid #2a425a; }
.cover .list b { color:#e8b4ae; font-weight:700; }
.cover .stats { display:grid; grid-template-columns:repeat(4,1fr); gap:5mm; margin-top:14mm; }
.cover .stats div { border-top:.7mm solid #b8322a; padding-top:2.2mm; }
.cover .stats b { display:block; font-size:22pt; line-height:1; color:#f3f7fb; }
.cover .stats span { font-size:8pt; color:#93a7ba; letter-spacing:.06em; }

section.read { page-break-after: always; }
h2.sec { font-size:14pt; margin:0 0 4mm; padding-bottom:1.5mm; border-bottom:.7mm solid #10202f; }
.read p { margin:0 0 2.4mm; }
.read .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:4mm 8mm; }
.read .card { border:.25mm solid #d3d9df; border-left:1.2mm solid #b8322a; padding:3mm 4mm; }
.read .card h3 { margin:0 0 1.6mm; font-size:10.5pt; }
.read .card p { margin:0 0 1.2mm; font-size:9pt; color:#333; }
.read .card .k { color:#7a4a46; }

section.mt { page-break-after: always; }
.mt-head { display:flex; align-items:baseline; gap:4mm; border-bottom:.7mm solid #10202f; padding-bottom:1.6mm; }
.mt-head .no { font-size:11pt; font-weight:800; color:#b8322a; }
.mt-head .league { font-size:9pt; background:#10202f; color:#fff; padding:.6mm 2mm; }
.mt-head .vs { font-size:15pt; font-weight:900; }
.mt-head .kick { margin-left:auto; font-size:9pt; color:#555; }
.note { margin:1.3mm 0 1.9mm; font-size:7.7pt; color:#444; background:#f4f1ec; padding:1.3mm 2.2mm;
        border-left:1mm solid #b8a48a; }
h4 { margin:1.7mm 0 .8mm; font-size:9.8pt; color:#10202f; }
h4 span.tag { font-weight:400; font-size:8.4pt; color:#777; margin-left:2mm; }
table { width:100%; border-collapse:collapse; font-size:8.7pt; }
th, td { border-bottom:.2mm solid #dcdfe3; padding:.8mm 1.3mm; text-align:right; }
th:first-child, td:first-child { text-align:left; }
thead th { background:#f1f3f5; font-weight:700; color:#333; }
td.hl { font-weight:800; color:#b8322a; }
td.pos { color:#1c6b3c; }
td.neg { color:#a3352c; }
.bars { display:grid; grid-template-columns:repeat(8,1fr); gap:1mm; margin-top:1.4mm; }
.bar { text-align:center; font-size:7.4pt; }
.bar .b { background:#dfe6ec; height:9mm; position:relative; display:flex; align-items:flex-end; }
.bar .b i { display:block; width:100%; background:#456f92; }
.bar.top .b i { background:#b8322a; }
.bar .v { margin-top:.8mm; font-weight:700; }
.ou { display:grid; grid-template-columns:repeat(4,1fr); gap:2mm; margin-top:2mm; }
.ou div { border:.25mm solid #d3d9df; padding:1.1mm 1.6mm; font-size:8.6pt; }
.ou b { color:#10202f; font-size:10.5pt; }
.warn { margin-top:1.6mm; font-size:7.9pt; color:#7a352d; background:#fbf5f3; padding:1.2mm 2mm;
        border-left:.9mm solid #b8322a; }
.two { display:grid; grid-template-columns:1fr 1fr; gap:4mm; }
.radar tbody td { font-size:8.8pt; }
footer.end { page-break-before: always; }
footer.end h2 { font-size:14pt; border-bottom:.7mm solid #10202f; padding-bottom:1.5mm; }
footer.end p { font-size:9pt; color:#333; }
.mono { font-variant-numeric: tabular-nums; }

/* 屏幕阅读：把每一节当一张白页，居中留白；打印时走上面的 @page */
@media screen {
  body { background:#e9edf1; padding:8mm 0; }
  .cover, section.read, section.mt, footer.end {
    display:block; width:210mm; margin:0 auto 6mm; background:#fff; padding:14mm 13mm;
    box-shadow:0 1px 3px rgba(16,32,47,.14), 0 8px 24px rgba(16,32,47,.08);
  }
  .cover { height:auto; padding:26mm 20mm; page-break-after:auto; }
  section.read, section.mt { page-break-after:auto; }
  footer.end { page-break-before:auto; }
}
@media print {
  body { background:#fff; }
  section.mt { page-break-after: always; }
}
"""


def fmt_edge(v: float) -> str:
    cls = "pos" if v > 0 else ("neg" if v < 0 else "")
    return f'<td class="{cls}">{v:+.1f}pp</td>'


def render(matches: list[dict], cards: dict, meta: dict) -> str:
    parts: list[str] = []
    parts.append(f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{meta['title']}</title><style>{CSS}</style></head><body>""")

    # 封面
    items = "".join(
        f'<div><b>{i + 1:02d}</b>　{m["home"]} vs {m["away"]}</div>' for i, m in enumerate(matches))
    parts.append(f"""
<div class="cover">
  <div class="kicker">{meta['kicker']}</div>
  <div class="date">{meta['date']}</div>
  <h1>{meta['h1']}</h1>
  <div class="sub">{meta['sub']}</div>
  <div class="rule"></div>
  <div class="list">{items}</div>
  <div class="stats">
    <div><b>8</b><span>场次</span></div>
    <div><b>6</b><span>类分布</span></div>
    <div><b>5</b><span>维修正</span></div>
    <div><b>90′</b><span>统计口径</span></div>
  </div>
  <div class="meta">{meta['foot']}</div>
</div>""")

    # 读法页
    parts.append("""
<section class="read">
<h2 class="sec">这册怎么读</h2>
<p>每场一页，六块内容：<b>基本面</b>（近期战绩与六维雷达）→ <b>进球期望 λ</b> → <b>胜平负</b> → <b>让球</b> →
<b>总进球与大小球</b> → <b>比分分布</b>。所有概率都是同一套进球分布算出来的，因此六块互相自洽，不会出现
「胜平负说一边倒、比分又说平局最多」这种自相矛盾。</p>
<div class="grid2">
  <div class="card"><h3>① 进球期望 λ</h3>
    <p><span class="k">怎么读：</span>λ 是两队的期望进球数，λ总 决定比赛「开放」还是「闷」。1.5 以下偏闷，2.8 以上偏开放。</p>
    <p><span class="k">两套算法：</span>方法1 用真实主客数据，方法2 用市场反推；综合 λ 在两者差 ≤0.5 时取平均，否则取方法1。</p>
    <p><span class="k">失效条件：</span>主客分离样本 ≤2 场时方法1 偏薄（文末《数据提示》会列），此时 λ 更依赖联赛先验。</p></div>
  <div class="card"><h3>② 胜平负</h3>
    <p><span class="k">怎么读：</span>模型三项加起来是 100%，市场去掉抽水后也是 100%——两边可以直接比。</p>
    <p><span class="k">Edge：</span>模型减市场。正数＝模型认为这事更容易发生，负数＝更难。</p>
    <p><span class="k">失效条件：</span>双方分歧 ≥10pp 时，国内联赛的经验是先怀疑自己的数据缺口（文末《数据提示》会列）。</p></div>
  <div class="card"><h3>③ 让球</h3>
    <p><span class="k">怎么读：</span>让球线由市场给出（如 -1），模型按同一套分布算「让球后的胜平负」。</p>
    <p><span class="k">为什么要看：</span>它比胜平负更早暴露「一边倒但不悬殊」的比赛。</p>
    <p><span class="k">失效条件：</span>让球线变动而模型 λ 没动，说明是市场情绪而非数据变化，此时两者不可直接对照。</p></div>
  <div class="card"><h3>④ 总进球与大小球</h3>
    <p><span class="k">怎么读：</span>0-7+ 的分布决定大小球三档；大 2.5 是最常用的分界线。</p>
    <p><span class="k">看形状：</span>峰值落在 2-3 是常态；峰值落在 0-1 说明这场进球会很难看。</p>
    <p><span class="k">失效条件：</span>λ总 接近 3 时，大 2.5 天然接近五五开，这一档的区分度最低。</p></div>
  <div class="card"><h3>⑤ 比分分布</h3>
    <p><span class="k">怎么读：</span>只列概率最高的 8 个比分，「官方定价」与「溢价」是市场对同一比分的定价与偏离。</p>
    <p><span class="k">看结构：</span>平局比分（1-1、0-0）挤在顶部，说明这场难分胜负；一边倒的比分扎堆，说明实力差被确认。</p>
    <p><span class="k">失效条件：</span>单场比分概率最高也只有 10-13%，不要把它读成「结论」。</p></div>
  <div class="card"><h3>⑥ 双方进球</h3>
    <p><span class="k">怎么读：</span>两队都至少进一球的概率。低于 50% 通常意味着一方被完全压制。</p>
    <p><span class="k">配合看：</span>与总进球一起看——双方进球高但总进球低，说明是 1-1、2-1 这类紧凑比分。</p>
    <p><span class="k">失效条件：</span>一方主力前锋缺阵时，这一项对伤停信息最敏感。</p></div>
</div>
<h2 class="sec" style="margin-top:6mm">这些数字是怎么来的</h2>
<ol style="font-size:9.2pt;margin:0;padding-left:5mm;line-height:1.62">
  <li><b>先定 λ。</b>两队的期望进球数：一套用主客分开的真实数据算（含近 10 场、状态、交手、伤停修正），
  一套从市场定价反推；两者差在 0.5 以内取平均，否则以实际数据法为准。</li>
  <li><b>再铺分布。</b>用两个 λ 构造一张进球矩阵（主队 i 球 × 客队 j 球，各自截断到 12 球），
  矩阵里每个格子就是「这个比分」的概率。</li>
  <li><b>然后切成六块。</b>胜平负＝按 i&gt;j、i=j、i&lt;j 求和；让球＝把格子按让球线平移后再加；
  总进球＝按 i+j 求和；大小球＝对总进球求和取阈值；双方进球＝去掉 i=0 与 j=0 的格子；比分＝直接取格子。</li>
  <li><b>最后对市场。</b>市场三项按 1/定价 归一化去水（把抽水摊掉），模型减市场就是 Edge。</li>
</ol>
<p style="margin-top:4mm;font-size:9pt"><b>本册不做什么：</b>不给方向、不写推荐、不出现任何操作动作；
单场最高概率的比分也只有 10%-13%，它描述的是「哪种走向更常见」，不是「会发生什么」。</p>
<p style="margin-top:2.4mm;font-size:8.8pt;color:#666">口径：只算 90 分钟常规时间；概率由进球分布（泊松结构，截断 12 球）计算，
同一场所有维度共用一份分布。定价与溢价来自公开赛果数据，仅作对照。</p>
</section>""")

    # 每场
    warn_rows: list[str] = []
    for m in matches:
        c = cards.get(m["no"], {})
        form = c.get("form") or {}
        radar = c.get("radar") or {}
        hf, af = form.get("home") or {}, form.get("away") or {}

        lam_total = m.get("lam_total") or ((m.get("lh") or 0) + (m.get("la") or 0))
        agree = "一致" if m.get("agree", "√") == "√" else "不一致（取方法1）"
        mix = m.get("mix") or [0, 0, 0, 0, 0]
        fa = m.get("form_adj") or [0, 0]
        inj = m.get("inj") or [0, 0]

        # 基本面
        basic = ""
        if hf or af:
            basic = f"""
<div class="two">
  <table><thead><tr><th>近期（近 5 场）</th><th>主 {hstr(m['home'])}</th><th>客 {hstr(m['away'])}</th></tr></thead><tbody>
    <tr><td>战绩</td><td>{hf.get('l5','—')}</td><td>{af.get('l5','—')}</td></tr>
    <tr><td>进 / 失（净）</td><td>{hf.get('gf','—')} / {hf.get('ga','—')}（{hf.get('net','—')}）</td>
        <td>{af.get('gf','—')} / {af.get('ga','—')}（{af.get('net','—')}）</td></tr>
    <tr><td>联赛主客</td><td>{hf.get('ha','—')}</td><td>{af.get('ha','—')}</td></tr>
  </tbody></table>
  <table class="radar"><thead><tr><th>六维雷达（0-100）</th><th>主</th><th>客</th></tr></thead><tbody>
    {''.join(f"<tr><td>{d}</td><td>{radar['home'][k]:.1f}</td><td>{radar['away'][k]:.1f}</td></tr>"
             for k, d in enumerate(radar.get('dims', [])) if k < len(radar.get('home', []))) }
  </tbody></table>
</div>"""
        brief = c.get("brief") or ""

        # 总进球条
        tg = m.get("tg") or []
        tmax = max(tg) if tg else 1
        bars = ""
        if tg:
            peak = max(range(len(tg)), key=lambda i: tg[i])
            cells = []
            for k, v in enumerate(tg):
                hgt = max(1.0, v / tmax * 100)
                cls = "bar top" if k == peak else "bar"
                label = "7+" if k == 7 else str(k)
                cells.append(f'<div class="{cls}"><div class="b"><i style="height:{hgt:.0f}%"></i></div>'
                             f'<div class="v">{v:.1f}%</div><div>{label} 球</div></div>')
            bars = f'<div class="bars">{"".join(cells)}</div>'

        ou = m.get("ou") or [0, 0, 0, 0]
        ou_html = f"""
<div class="ou">
  <div>大 1.5<br><b>{ou[0]:.1f}%</b></div>
  <div>大 2.5<br><b>{ou[1]:.1f}%</b></div>
  <div>大 3.5<br><b>{ou[2]:.1f}%</b></div>
  <div>双方进球<br><b>{ou[3]:.1f}%</b></div>
</div>""" if ou else ""

        # 比分表
        srows = "".join(
            f"<tr><td>{s['i']}-{s['j']}</td><td class=\"hl\">{s['p']:.1f}%</td><td>{s['odd']}</td>"
            f"<td>{s['ev']}</td></tr>" for s in (m.get("scores") or [])[:8])
        scores_html = f"""
<table><thead><tr><th>比分</th><th>模型概率</th><th>官方定价</th><th>溢价</th></tr></thead>
<tbody>{srows}</tbody></table>""" if srows else ""

        warn_html = ""
        if m.get("warn"):
            for w in m["warn"]:
                warn_rows.append(f"<tr><td>{m['no']}</td><td>{m['home']} vs {m['away']}</td>"
                                 f"<td style=\"text-align:left\">{w}</td></tr>")

        parts.append(f"""
<section class="mt">
  <div class="mt-head">
    <span class="no">{m['no']}</span>
    <span class="league">{m['league']}</span>
    <span class="vs">{m['home']} <span style="font-size:10pt;color:#b8322a">vs</span> {m['away']}</span>
    <span class="kick">id {m['mid']}</span>
  </div>
  {f'<div class="note">{m["note"]}</div>' if m.get("note") else ''}

  <h4>基本面<span class="tag">走势与六维雷达，只作背景</span></h4>
  {basic or '<p style="font-size:9pt;color:#777">（本场无独立战绩档案，看下方分布）</p>'}

  <h4>① 进球期望 λ<span class="tag">两套算法与综合值</span></h4>
  <table><thead><tr><th>项目</th><th>主队</th><th>客队</th><th>说明</th></tr></thead><tbody>
    <tr><td>方法1 实际数据法</td><td>{m.get('l1h', 0):.3f}</td><td>{m.get('l1a', 0):.3f}</td><td>主客分离 + 近 10 场</td></tr>
    <tr><td>方法2 市场反推法</td><td>{m.get('l2h', 0):.3f}</td><td>{m.get('l2a', 0):.3f}</td><td>从胜平负反推</td></tr>
    <tr><td><b>综合 λ</b></td><td class="hl">{m.get('lh', 0):.3f}</td><td class="hl">{m.get('la', 0):.3f}</td>
        <td>双法{agree}；λ总 <b>{lam_total:.3f}</b></td></tr>
    <tr><td>修正与底数</td><td colspan="3" style="font-size:8.4pt;line-height:1.35">form 主 {fa[0]:+.3f} / 客 {fa[1]:+.3f}　
        交锋 {m.get('h2h_f', 1):.3f}（{m.get('h2h_tag', '—')}）　伤停 主 {inj[0]} / 客 {inj[1]}　
        底数 主攻 {mix[0]:.2f}(主场w{mix[1]:.1f}) 客防 {mix[2]:.2f} 客攻 {mix[3]:.2f} 主防 {mix[4]:.2f}</td></tr>
  </tbody></table>

  <h4>② 胜平负<span class="tag">模型与市场去水后可直比</span></h4>
  <table><thead><tr><th>口径</th><th>主胜</th><th>平</th><th>客胜</th></tr></thead><tbody>
    <tr><td>模型</td><td>{m['wdl_model'][0]:.1f}%</td><td>{m['wdl_model'][1]:.1f}%</td><td>{m['wdl_model'][2]:.1f}%</td></tr>
    <tr><td>市场（去水）</td><td>{m['wdl_market'][0]:.1f}%</td><td>{m['wdl_market'][1]:.1f}%</td><td>{m['wdl_market'][2]:.1f}%</td></tr>
    <tr><td>Edge（模型−市场）</td>{fmt_edge(m['wdl_edge'][0])}{fmt_edge(m['wdl_edge'][1])}{fmt_edge(m['wdl_edge'][2])}</tr>
    <tr><td>固定奖金 / 返还率</td><td colspan="3">{m.get('odds', [0,0,0])[0]:.2f} / {m.get('odds', [0,0,0])[1]:.2f} /
        {m.get('odds', [0,0,0])[2]:.2f}　返还率 {m.get('payout', 0):.1f}%</td></tr>
  </tbody></table>

  <h4>③ 让球<span class="tag">让球线由市场给出</span></h4>
  <table><thead><tr><th>让球 {m.get('hline', 0):+d}</th><th>让胜</th><th>让平</th><th>让负</th></tr></thead><tbody>
    <tr><td>模型</td><td>{m['hcp_model'][0]:.1f}%</td><td>{m['hcp_model'][1]:.1f}%</td><td>{m['hcp_model'][2]:.1f}%</td></tr>
    <tr><td>市场（去水）</td><td>{m['hcp_market'][0]:.1f}%</td><td>{m['hcp_market'][1]:.1f}%</td><td>{m['hcp_market'][2]:.1f}%</td></tr>
    <tr><td>Edge（模型−市场）</td>{fmt_edge(m.get('hcp_edge', [0,0,0])[0])}{fmt_edge(m.get('hcp_edge', [0,0,0])[1])}{fmt_edge(m.get('hcp_edge', [0,0,0])[2])}</tr>
    <tr><td>胜率（不含平）</td><td colspan="3">主 {m.get('winrate', [0,0])[0]:.1f}% / 客 {m.get('winrate', [0,0])[1]:.1f}%</td></tr>
  </tbody></table>

  <div class="two">
    <div>
      <h4>④ 总进球与大小球<span class="tag">同一份分布的边缘</span></h4>
      {bars}
      {ou_html}
    </div>
    <div>
      <h4>⑤ 比分分布<span class="tag">概率最高的八个</span></h4>
      {scores_html}
    </div>
  </div>
</section>""")

    # 尾页
    warn_table = ""
    if warn_rows:
        warn_table = f"""
  <h2 style="margin-top:6mm">数据提示（逐场）</h2>
  <p style="font-size:8.8pt;color:#444">这些是模型自检给出的薄弱点，只影响该场某几个维度的可信度，不改变数字本身。</p>
  <table><thead><tr><th>编号</th><th>对阵</th><th style="text-align:left">提示</th></tr></thead>
  <tbody>{''.join(warn_rows)}</tbody></table>"""
    parts.append(f"""
<footer class="end">
  {warn_table}
  <h2 style="margin-top:6mm">口径与说明</h2>
  <p><b>统计范围。</b>所有结果只统计 90 分钟常规时间，加时与点球不计。</p>
  <p><b>概率来源。</b>用两队期望进球 λ 构造进球分布（泊松结构，单侧截断到 12 球），
  胜平负、让球、总进球、双方进球、比分五类全部由这一份分布推导，所以彼此自洽。
  λ 由两套算法给出：实际主客数据法与市场反推法，两者差 ≤0.5 时取平均，否则以实际数据法为准。</p>
  <p><b>定价与溢价。</b>「官方定价」「固定奖金」「返还率」取自公开赛果数据，只作对照，不代表任何操作建议。</p>
  <p><b>本册不构成任何投注建议。</b>它只是把公开数据整理成可读的分布：既没有方向推荐，也不预测赛果。
  单场最高概率的比分通常只有 10%-13%，任何一项都不该被读成结论。</p>
  <p><b>可复现。</b>本册所有数字由同一套脚本生成，输入与输出都留档，可逐项复核。</p>
  <p style="margin-top:6mm;color:#777;font-size:8.6pt">{meta['foot']}</p>
</footer>
</body></html>""")
    return "\n".join(parts)


def hstr(name: str) -> str:
    return name


# ── Chrome 打印 ─────────────────────────────────────────────────────────
def find_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    return None


def html_to_pdf(html_path: Path, pdf_path: Path) -> tuple[bool, str]:
    chrome = find_chrome()
    if not chrome:
        return False, "找不到 chrome.exe"
    cmd = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", "--virtual-time-budget=15000",
        f"--print-to-pdf={pdf_path}", html_path.as_uri(),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = pdf_path.exists() and pdf_path.stat().st_size > 10000
    return ok, (p.stderr or p.stdout or "")[-600:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=str(STATE_BATCH / "_model_20261016_fri.txt"))
    ap.add_argument("--cards", default=str(ROOT / "📝文章/20261016/小红书_周五八场/cards.json"))
    ap.add_argument("--out", default=str(ROOT / "📝文章/20261016/付费资料_全维度拆解_样册_v0.1.pdf"))
    ap.add_argument("--html-only", action="store_true")
    a = ap.parse_args()

    model_path = Path(a.model)
    if not model_path.exists():
        print(f"❌ 找不到模型输出：{model_path}")
        print("   先跑：python scripts/model.py --all > state/_model_<日期>_<星期>.txt")
        return 2
    matches = parse_model_txt(model_path)
    if not matches:
        print("❌ 解析不到任何场次，检查模型文本格式")
        return 2
    missing = [m["no"] for m in matches
               if not all(k in m for k in ("wdl_model", "hcp_model", "tg", "ou", "scores", "lh"))]
    print(f"解析 {len(matches)} 场：" + " ".join(m["no"] for m in matches))
    if missing:
        print("⚠️ 这些场次字段不全：" + " ".join(missing))

    cards = load_cards(Path(a.cards))
    print(f"基本面合并：cards.json 命中 {len(cards)} 场")

    meta = {
        "title": "周五八场 · 全维度拆解（样册 v0.1）",
        "kicker": "赛后数据整理 · 样册",
        "date": "2026.10.16 周五 · 八场",
        "h1": "八场 · 全维度拆解",
        "sub": "进球期望 λ ｜ 胜平负 ｜ 让球 ｜ 总进球与大小球 ｜ 比分分布 ｜ 双方进球",
        "foot": "@阿飞·赛博聊球　·　样册 v0.1　·　只做数据整理，不构成投注建议",
    }

    html = render(matches, cards, meta)
    out_pdf = Path(a.out)

    tmpdir = Path(tempfile.mkdtemp(prefix="docpack_"))
    try:
        hp = tmpdir / "pack.html"
        hp.write_text(html, encoding="utf-8")
        print(f"HTML：{hp.stat().st_size / 1024:.1f} KB")
        if a.html_only:
            target = out_pdf.with_suffix(".html")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(hp, target)
            print(f"✅ 只出 HTML：{target}")
            return 0
        pp = tmpdir / "pack.pdf"
        ok, msg = html_to_pdf(hp, pp)
        if not ok:
            print("❌ PDF 生成失败：" + msg)
            return 3
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pp, out_pdf)
        # HTML 同步落盘：排布方便，改版式后刷新浏览器即可看效果
        out_html = out_pdf.with_suffix(".html")
        shutil.copyfile(hp, out_html)
        print(f"✅ PDF：{out_pdf}  {out_pdf.stat().st_size / 1024:.1f} KB")
        print(f"✅ HTML：{out_html}  {out_html.stat().st_size / 1024:.1f} KB（浏览器直接打开）")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
