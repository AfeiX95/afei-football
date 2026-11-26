#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 层内部校准与赛果复盘可视化看板生成器（融合 data-visualization + football-bayes 校准理念）

定位与合规边界：
- **严格归属 A 层内部复盘工具**（产物写至 `state/cache/calib_dashboard.html`，受 `.gitignore`/安全闸保护，永不作为 B 层头条公开交付物上传；B 层公开稿仍只出 `.md`）。
- **零第三方依赖**：纯 Python 标准库读取本地真源，生成单文件离线交互式 SVG + HTML5 响应式深色看板（无需联网加载外部 CDN，任何机器双击即开）。

读取数据源：
1. `📚知识库/赛后校验/prob_log.tsv` — 模型 vs 市场三向概率与实际赛果（Brier / LogLoss / 可靠性校准曲线 / Edge 分桶实证）
2. `state/model-state.json` — 累计校准批次、总场次与命中率
3. `state/cache/_review_sfc_*.json`（最新一份）— 传足近 100 期 / 近 30 期 3/1/0 分布与五档奖金成色
4. `state/cache/_review_jc_*.json`（最新一份）— 竞彩近 30 天各联赛热门兑现率 vs 平局率散点分布

用法：
    python -X utf8 scripts/calib_dashboard.py
    python -X utf8 scripts/calib_dashboard.py --out state/cache/calib_dashboard.html
"""
import argparse
import datetime as dt
import glob
import html
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PROB_LOG = ROOT / "📚知识库" / "赛后校验" / "prob_log.tsv"
MODEL_STATE = ROOT / "state" / "model-state.json"
CACHE_DIR = ROOT / "state" / "cache"


def parse_prob(val: str):
    if not val:
        return None
    s = val.strip().rstrip("%")
    if not s or s in ("—", "-"):
        return None
    try:
        x = float(s)
        return x / 100.0 if x > 1.0001 else x
    except Exception:
        return None


def load_prob_log():
    rows = []
    if not PROB_LOG.exists():
        return rows
    for raw in PROB_LOG.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("日期"):
            continue
        parts = line.split("\t")
        if len(parts) < 9:
            continue
        mh, md, ma = parse_prob(parts[2]), parse_prob(parts[3]), parse_prob(parts[4])
        bh, bd, ba = parse_prob(parts[5]), parse_prob(parts[6]), parse_prob(parts[7])
        act = parts[8].strip()
        if mh is None or md is None or ma is None or act not in ("主", "平", "客"):
            continue
        ms = mh + md + ma
        if ms <= 0:
            continue
        mh, md, ma = mh / ms, md / ms, ma / ms
        mkt = None
        if bh is not None and bd is not None and ba is not None and (bh + bd + ba) > 0:
            bs = bh + bd + ba
            mkt = (bh / bs, bd / bs, ba / bs)
        rows.append({
            "date": parts[0].strip(),
            "match": parts[1].strip(),
            "model": (mh, md, ma),
            "market": mkt,
            "actual": act,
        })
    return rows


def compute_prob_metrics(rows):
    idx_map = {"主": 0, "平": 1, "客": 2}
    brier_m, ll_m, dir_m = [], [], 0
    brier_b, ll_b, dir_b, n_both = [], [], 0, 0
    # 5 calibration bins on 3*N outcome predictions
    bins_m = [{"lo": i * 0.2, "hi": (i + 1) * 0.2, "preds": [], "hits": []} for i in range(5)]
    bins_b = [{"lo": i * 0.2, "hi": (i + 1) * 0.2, "preds": [], "hits": []} for i in range(5)]
    # Edge buckets on top model side: <2pp, 2-5pp, 5-10pp, >=10pp
    edge_buckets = [
        {"label": "|Edge| < 2pp", "lo": 0.0, "hi": 0.02, "n": 0, "m_hit": 0, "b_hit": 0},
        {"label": "2–5pp（R61弱词区）", "lo": 0.02, "hi": 0.05, "n": 0, "m_hit": 0, "b_hit": 0},
        {"label": "5–10pp（有效分歧）", "lo": 0.05, "hi": 0.10, "n": 0, "m_hit": 0, "b_hit": 0},
        {"label": "≥10pp（强背离区）", "lo": 0.10, "hi": 1.00, "n": 0, "m_hit": 0, "b_hit": 0},
    ]

    # Rolling 20-match Brier
    rolling = []

    for i, r in enumerate(rows):
        y = [0.0, 0.0, 0.0]
        yi = idx_map[r["actual"]]
        y[yi] = 1.0
        mp = r["model"]
        bm = sum((mp[k] - y[k]) ** 2 for k in range(3))
        brier_m.append(bm)
        ll_m.append(-math.log(max(mp[yi], 1e-6)))
        m_top = max(range(3), key=lambda k: mp[k])
        if m_top == yi:
            dir_m += 1
        for k in range(3):
            bi = min(4, int(mp[k] * 5))
            bins_m[bi]["preds"].append(mp[k])
            bins_m[bi]["hits"].append(y[k])

        if r["market"]:
            bp = r["market"]
            n_both += 1
            bb = sum((bp[k] - y[k]) ** 2 for k in range(3))
            brier_b.append(bb)
            ll_b.append(-math.log(max(bp[yi], 1e-6)))
            b_top = max(range(3), key=lambda k: bp[k])
            if b_top == yi:
                dir_b += 1
            for k in range(3):
                bi = min(4, int(bp[k] * 5))
                bins_b[bi]["preds"].append(bp[k])
                bins_b[bi]["hits"].append(y[k])
            edge_abs = abs(mp[m_top] - bp[m_top])
            for eb in edge_buckets:
                if eb["lo"] <= edge_abs < eb["hi"]:
                    eb["n"] += 1
                    if m_top == yi:
                        eb["m_hit"] += 1
                    if b_top == yi:
                        eb["b_hit"] += 1
                    break

        if i + 1 >= 15:
            win_m = sum(brier_m[max(0, i - 19):i + 1]) / len(brier_m[max(0, i - 19):i + 1])
            win_b = (sum(brier_b[max(0, len(brier_b) - 20):]) / min(20, len(brier_b))) if brier_b else None
            rolling.append({"idx": i + 1, "date": r["date"], "brier_m": round(win_m, 4), "brier_b": round(win_b, 4) if win_b else None})

    def summarize_bins(b_list):
        out = []
        for b in b_list:
            n = len(b["preds"])
            out.append({
                "range": f"{int(b['lo']*100)}–{int(b['hi']*100)}%",
                "n": n,
                "pred": round(sum(b["preds"]) / n, 3) if n else None,
                "actual": round(sum(b["hits"]) / n, 3) if n else None,
            })
        return out

    return {
        "n_total": len(rows),
        "n_both": n_both,
        "brier_model": round(sum(brier_m) / len(brier_m), 4) if brier_m else None,
        "brier_market": round(sum(brier_b) / len(brier_b), 4) if brier_b else None,
        "logloss_model": round(sum(ll_m) / len(ll_m), 4) if ll_m else None,
        "logloss_market": round(sum(ll_b) / len(ll_b), 4) if ll_b else None,
        "top1_model_pct": round(100.0 * dir_m / len(rows), 1) if rows else None,
        "top1_market_pct": round(100.0 * dir_b / n_both, 1) if n_both else None,
        "bins_model": summarize_bins(bins_m),
        "bins_market": summarize_bins(bins_b),
        "edge_buckets": edge_buckets,
        "rolling": rolling,
    }


def load_latest_sfc():
    files = sorted(glob.glob(str(CACHE_DIR / "_review_sfc_*.json")))
    if not files:
        return None
    p = Path(files[-1])
    rows = json.loads(p.read_text(encoding="utf-8"))
    if not rows:
        return None

    def stat_slice(sub):
        c = Counter()
        tiers = Counter()
        for r in sub:
            for ch in (r.get("lotteryDrawResult") or "").split():
                c[ch] += 1
            p1 = r.get("prizeLevelList") or []
            first = next((x for x in p1 if x.get("prizeLevel") == "一等奖"), {})
            cnt = int(str(first.get("stakeCount") or "0").replace(",", "") or 0)
            amt = int(float(str(first.get("stakeAmount") or "0").replace(",", "") or 0))
            if cnt == 0:
                tiers["滚存(0注)"] += 1
            elif amt >= 5_000_000:
                tiers["500万封顶"] += 1
            elif amt >= 1_000_000:
                tiers["100-500万"] += 1
            elif amt >= 50_000:
                tiers["5-100万"] += 1
            else:
                tiers["5万以下火锅"] += 1
        tot = c["3"] + c["1"] + c["0"]
        return {
            "issues": len(sub),
            "p3": round(100.0 * c["3"] / tot, 1) if tot else 0,
            "p1": round(100.0 * c["1"] / tot, 1) if tot else 0,
            "p0": round(100.0 * c["0"] / tot, 1) if tot else 0,
            "tiers": dict(tiers),
        }

    return {
        "file": p.name,
        "latest_issue": rows[0].get("lotteryDrawNum"),
        "s30": stat_slice(rows[:30]),
        "s100": stat_slice(rows[:100]),
    }


def load_latest_jc():
    files = sorted(glob.glob(str(CACHE_DIR / "_review_jc_*.json")))
    if not files:
        return None
    p = Path(files[-1])
    rows = json.loads(p.read_text(encoding="utf-8"))
    lg_stat = defaultdict(lambda: {"n": 0, "draw": 0, "fav_n": 0, "fav_hit": 0, "cold": 0})
    for m in rows:
        sec = m.get("sectionsNo999") or ""
        if ":" not in sec:
            continue
        try:
            gh, ga = [int(x) for x in sec.split(":")]
        except Exception:
            continue
        res = "3" if gh > ga else ("1" if gh == ga else "0")
        lg = m.get("matchName") or "其他"
        st = lg_stat[lg]
        st["n"] += 1
        if res == "1":
            st["draw"] += 1
        try:
            sp = {"3": float(m["h"]), "1": float(m["d"]), "0": float(m["a"])}
            st["fav_n"] += 1
            fav_k = min(sp, key=lambda k: sp[k])
            if res == fav_k:
                st["fav_hit"] += 1
            if sp[res] >= 3.5:
                st["cold"] += 1
        except Exception:
            pass

    leagues = []
    for lg, st in lg_stat.items():
        if st["fav_n"] >= 8:
            leagues.append({
                "league": lg,
                "n": st["n"],
                "fav_pct": round(100.0 * st["fav_hit"] / st["fav_n"], 1),
                "draw_pct": round(100.0 * st["draw"] / st["n"], 1),
                "cold_pct": round(100.0 * st["cold"] / st["fav_n"], 1),
            })
    leagues.sort(key=lambda x: -x["n"])
    return {"file": p.name, "total_matches": len(rows), "leagues": leagues[:16]}


def svg_calibration(bins_m, bins_b) -> str:
    w, h, pad = 460, 300, 46
    pw, ph = w - pad * 2, h - pad * 2
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" height="290">']
    # Grid + diagonal
    for i in range(6):
        v = i * 0.2
        x = pad + v * pw
        y = h - pad - v * ph
        parts.append(f'<line x1="{pad}" y1="{y:.1f}" x2="{w-pad}" y2="{y:.1f}" stroke="#2a3447" stroke-width="1"/>')
        parts.append(f'<text x="{pad-8}" y="{y+4:.1f}" fill="#8b9bb4" font-size="11" text-anchor="end">{int(v*100)}%</text>')
        parts.append(f'<text x="{x:.1f}" y="{h-pad+18}" fill="#8b9bb4" font-size="11" text-anchor="middle">{int(v*100)}%</text>')
    parts.append(f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{pad}" stroke="#64748b" stroke-dasharray="5,4" stroke-width="1.5"/>')

    def poly(bins, color, label):
        pts = []
        circles = []
        for b in bins:
            if b["pred"] is None or b["actual"] is None or b["n"] < 3:
                continue
            x = pad + b["pred"] * pw
            y = h - pad - b["actual"] * ph
            pts.append(f"{x:.1f},{y:.1f}")
            tip = f"{label} [{b['range']}] 样本={b['n']} 预测均值={b['pred']*100:.1f}% 实际打出={b['actual']*100:.1f}%"
            circles.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}"><title>{html.escape(tip)}</title></circle>')
        if len(pts) >= 2:
            parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{" ".join(pts)}"/>')
        parts.extend(circles)

    poly(bins_b, "#f59e0b", "市场去水")
    poly(bins_m, "#38bdf8", "v3.1融合模型")
    parts.append(f'<text x="{w/2}" y="{h-6}" fill="#94a3b8" font-size="11" text-anchor="middle">预测概率分箱均值 → 越贴近斜虚线代表概率校准越准（悬停圆点看明细）</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_league_scatter(leagues) -> str:
    if not leagues:
        return '<p class="muted">暂无竞彩联赛缓存数据（运行 scripts/results_review.py 后自动点亮）</p>'
    w, h, pad = 480, 300, 46
    pw, ph = w - pad * 2, h - pad * 2
    # x: fav_pct (25%..75%), y: draw_pct (10%..45%)
    x_min, x_max = 25.0, 75.0
    y_min, y_max = 10.0, 45.0
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" height="290">']
    for xv in (30, 40, 50, 60, 70):
        x = pad + (xv - x_min) / (x_max - x_min) * pw
        parts.append(f'<line x1="{x:.1f}" y1="{pad}" x2="{x:.1f}" y2="{h-pad}" stroke="#232d3f" stroke-width="1"/>')
        parts.append(f'<text x="{x:.1f}" y="{h-pad+18}" fill="#8b9bb4" font-size="11" text-anchor="middle">{xv}%</text>')
    for yv in (15, 25, 35, 45):
        y = h - pad - (yv - y_min) / (y_max - y_min) * ph
        parts.append(f'<line x1="{pad}" y1="{y:.1f}" x2="{w-pad}" y2="{y:.1f}" stroke="#232d3f" stroke-width="1"/>')
        parts.append(f'<text x="{pad-8}" y="{y+4:.1f}" fill="#8b9bb4" font-size="11" text-anchor="end">{yv}%</text>')

    for lg in leagues:
        fx = max(x_min, min(x_max, lg["fav_pct"]))
        fy = max(y_min, min(y_max, lg["draw_pct"]))
        x = pad + (fx - x_min) / (x_max - x_min) * pw
        y = h - pad - (fy - y_min) / (y_max - y_min) * ph
        r = max(5.0, min(13.0, math.sqrt(lg["n"]) * 1.35))
        color = "#f43f5e" if lg["fav_pct"] < 43 else ("#10b981" if lg["fav_pct"] >= 53 else "#a78bfa")
        tip = f"{lg['league']} ({lg['n']}场)：最低SP热门兑现 {lg['fav_pct']}% ｜ 平局率 {lg['draw_pct']}% ｜ 冷门率(SP≥3.5) {lg['cold_pct']}%"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" fill-opacity="0.78" stroke="#0f172a" stroke-width="1.2"><title>{html.escape(tip)}</title></circle>')
        parts.append(f'<text x="{x:.1f}" y="{y-r-3:.1f}" fill="#cbd5e1" font-size="10" text-anchor="middle">{html.escape(lg["league"])}</text>')

    parts.append(f'<text x="{w/2}" y="{h-6}" fill="#94a3b8" font-size="11" text-anchor="middle">横轴：热门兑现率（越左越冷=红）｜ 纵轴：90分钟平局率 ｜ 气泡大小：场次数</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def render_html(ms: dict, pm: dict, sfc: Optional[dict], jc: Optional[dict]) -> str:
    cal = ms.get("calibration") or {}
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    svg_cal = svg_calibration(pm["bins_model"], pm["bins_market"])
    svg_jc = svg_league_scatter(jc["leagues"] if jc else [])

    edge_rows_html = ""
    for eb in pm["edge_buckets"]:
        n = eb["n"]
        mp_str = f"{100.0 * eb['m_hit'] / n:.1f}%" if n else "—"
        bp_str = f"{100.0 * eb['b_hit'] / n:.1f}%" if n else "—"
        edge_rows_html += f"<tr><td>{eb['label']}</td><td>{n}</td><td>{mp_str}</td><td>{bp_str}</td></tr>"

    sfc_html = '<p class="muted">暂无传足历史缓存</p>'
    if sfc:
        s30, s100 = sfc["s30"], sfc["s100"]
        tier_order = ["滚存(0注)", "500万封顶", "100-500万", "5-100万", "5万以下火锅"]
        t_bars = ""
        for tk in tier_order:
            c30 = s30["tiers"].get(tk, 0)
            c100 = s100["tiers"].get(tk, 0)
            w30 = int(c30 / max(1, s30["issues"]) * 100)
            t_bars += (
                f'<div class="bar-row"><span class="bar-lbl">{tk}</span>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{w30}%"></div></div>'
                f'<span class="bar-val">近30期 {c30}期 / 近100期 {c100}期</span></div>'
            )
        sfc_html = f"""
        <div class="pill-row">
          <span class="pill">最新开奖：{sfc['latest_issue']} 期</span>
          <span class="pill">近30期 3/1/0：{s30['p3']}% / {s30['p1']}% / {s30['p0']}%</span>
          <span class="pill">近100期基线：{s100['p3']}% / {s100['p1']}% / {s100['p0']}%</span>
        </div>
        {t_bars}
        """

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>阿飞说球 · A层模型校准与赛果复盘看板</title>
<style>
  :root {{
    --bg: #0b1120; --card: #151f32; --border: #26334d;
    --txt: #e2e8f0; --muted: #94a3b8; --accent: #38bdf8; --amber: #f59e0b; --green: #10b981;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 24px; font-family: "Microsoft YaHei", system-ui, sans-serif; background: var(--bg); color: var(--txt); }}
  .header {{ display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 20px; flex-wrap: wrap; gap: 8px; }}
  .badge-warn {{ background: #7f1d1d; color: #fecaca; font-size: 12px; padding: 4px 10px; border-radius: 999px; font-weight: 600; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin-bottom: 20px; }}
  .kpi {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }}
  .kpi .lbl {{ font-size: 12px; color: var(--muted); }}
  .kpi .val {{ font-size: 24px; font-weight: 700; margin: 6px 0 2px; color: var(--accent); }}
  .kpi .sub {{ font-size: 12px; color: var(--muted); }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); gap: 18px; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 18px; }}
  .card h3 {{ margin: 0 0 12px; font-size: 15px; display: flex; justify-content: space-between; align-items: center; }}
  .legend {{ font-size: 12px; font-weight: normal; color: var(--muted); }}
  .dot {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }}
  th, td {{ padding: 8px 10px; border-bottom: 1px solid var(--border); text-align: left; }}
  th {{ color: var(--muted); font-weight: 600; }}
  .pill-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }}
  .pill {{ background: #1e293b; border: 1px solid var(--border); padding: 4px 10px; border-radius: 6px; font-size: 12px; }}
  .bar-row {{ display: flex; align-items: center; gap: 10px; margin: 9px 0; font-size: 12px; }}
  .bar-lbl {{ width: 95px; color: var(--muted); flex-shrink: 0; }}
  .bar-track {{ flex: 1; height: 10px; background: #0f172a; border-radius: 5px; overflow: hidden; }}
  .bar-fill {{ height: 100%; background: linear-gradient(90deg, #38bdf8, #818cf8); }}
  .bar-val {{ width: 165px; text-align: right; color: #cbd5e1; flex-shrink: 0; }}
  .muted {{ color: var(--muted); font-size: 13px; }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <h2 style="margin:0;font-size:20px;">阿飞说球 · A层模型校准与宏观赛果复盘看板</h2>
      <div class="muted" style="margin-top:4px;">生成时间：{now_str} ｜ 90分钟常规时间口径 ｜ 离线零依赖单文件看板</div>
    </div>
    <span class="badge-warn">🔒 A层内部留存 · 严禁上传公开平台</span>
  </div>

  <div class="kpis">
    <div class="kpi">
      <div class="lbl">累计批次校准总场次</div>
      <div class="val">{cal.get('total_matches', '—')} 场</div>
      <div class="sub">Batch #{cal.get('last_batch', '—')} ｜ 方向命中 {cal.get('direction_correct', '—')} 场 ({cal.get('direction_rate_pct', '—')}%)</div>
    </div>
    <div class="kpi">
      <div class="lbl">概率评分台账 (prob_log)</div>
      <div class="val">{pm['n_total']} 场</div>
      <div class="sub">双边对照样本 {pm['n_both']} 场 ｜ 首选命中 {pm['top1_model_pct']}% vs 市场 {pm['top1_market_pct']}%</div>
    </div>
    <div class="kpi">
      <div class="lbl">Brier Score（越低越准）</div>
      <div class="val" style="color:var(--green)">{pm['brier_model']}</div>
      <div class="sub">市场去水基准：{pm['brier_market']}（随机均分=0.6667）</div>
    </div>
    <div class="kpi">
      <div class="lbl">LogLoss 对数损失（越低越准）</div>
      <div class="val" style="color:var(--amber)">{pm['logloss_model']}</div>
      <div class="sub">市场去水基准：{pm['logloss_market']}（随机均分=1.0986）</div>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h3>
        <span>1. 模型 vs 市场 概率可靠性校准曲线</span>
        <span class="legend"><i class="dot" style="background:#38bdf8"></i>v3.1融合 <i class="dot" style="background:#f59e0b;margin-left:8px;"></i>市场去水</span>
      </h3>
      {svg_cal}
    </div>

    <div class="card">
      <h3>
        <span>2. 竞彩各联赛 热门兑现率 vs 平局率分布</span>
        <span class="legend">{jc['file'] if jc else '未加载'}</span>
      </h3>
      {svg_jc}
    </div>

    <div class="card">
      <h3>
        <span>3. Edge(模型−市场) 分歧幅度实证表（核验 R61 5pp 门槛）</span>
        <span class="legend">按模型最高概率项分桶</span>
      </h3>
      <table>
        <thead><tr><th>分歧区间 |Edge|</th><th>场次数</th><th>模型首选命中率</th><th>市场首选命中率</th></tr></thead>
        <tbody>{edge_rows_html}</tbody>
      </table>
      <p class="muted" style="margin-top:10px;">注：当 |Edge| &lt; 5pp 时模型与市场实质同向或微差，公开稿严守 R61 禁用「严重低估/明显偏差」等强词。</p>
    </div>

    <div class="card">
      <h3>
        <span>4. 传统足彩 14 场 3/1/0 分布与五档奖金成色节奏</span>
        <span class="legend">{sfc['file'] if sfc else '未加载'}</span>
      </h3>
      {sfc_html}
    </div>
  </div>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="生成 A 层内部校准与复盘可视化 HTML 看板")
    ap.add_argument("--out", default=str(CACHE_DIR / "calib_dashboard.html"), help="输出 HTML 路径（默认 state/cache/calib_dashboard.html）")
    args = ap.parse_args()

    ms = json.loads(MODEL_STATE.read_text(encoding="utf-8")) if MODEL_STATE.exists() else {}
    prob_rows = load_prob_log()
    pm = compute_prob_metrics(prob_rows)
    sfc = load_latest_sfc()
    jc = load_latest_jc()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_html(ms, pm, sfc, jc), encoding="utf-8")
    print(f"[OK] A层校准看板已生成: {out_path}")
    print(f"     prob_log={pm['n_total']}场 | Brier(模型/市场)={pm['brier_model']}/{pm['brier_market']} | 传足缓存={'有' if sfc else '无'} | 竞彩缓存={'有' if jc else '无'}")


if __name__ == "__main__":
    main()
