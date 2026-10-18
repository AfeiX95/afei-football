#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""付费内部资料 · 一册 PDF（每场一页，10 种排版随机分配）。

设计意图
  付费资料是「一个人一晚上要读完 25 场」的东西。全用一套模板，读到第 8 场眼睛就
  开始跳行了。所以本文件做 10 套互不相同的版式，每次生成随机把 10 套铺满全场次：
  同一场的图表面板位置、色彩语言、阅读动线每次都变，但每一页的信息量按七段口径
  （门槛 → 数理 → 高阶 → 基本面 → 人员 → 结论 → 缺口）是一个不落。

数据层
  直接复用 paid_cyber.build()（λ 双法、Dixon-Coles、信心五维、冷门指数、定价轨迹），
  本文件只做版面。未开售/已封盘的场次（如 024 皇马-塞维利亚）没有固定奖金就没有
  模型，单独出一页「数据缺口页」，只写可核实的技术面与人员面，不用估算值冒充。

用法
  python scripts/paid_pdf.py                                  # 今天这批，随机版式
  python scripts/paid_pdf.py --model state/batch/_model_20261018_sun_all.txt --date 20261018
  python scripts/paid_pdf.py --seed 7                          # 固定随机种子，可复现
  python scripts/paid_pdf.py --list                            # 只看版式分配表，不出 PDF
  python scripts/paid_pdf.py --engine chromium|print           # chromium=Playwright 直出
"""
from __future__ import annotations

import argparse
import io
import json
import math
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import paid_cyber as pc  # noqa: E402
import paid_report as pr  # noqa: E402

DIRS = ["主胜", "平", "客胜"]

# ────────────────────────────────────────────── 小工具
def e(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def f(x, n: int = 1) -> str:
    try:
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return "—"


def sg(x, n: int = 1) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "—"
    return f"{'+' if v >= 0 else '−'}{abs(v):.{n}f}"


def tone(x) -> str:
    """偏差配色：≥15pp 红、≥6pp 橙、其余绿。"""
    v = abs(float(x))
    return "r" if v >= 15 else ("a" if v >= 6 else "g")


def vg(v) -> str:
    """防范档的括注。

    退路机制下防范常常「与次选同向、只是换一个比分」，直接并列会被读成
    「本场给了两个方向」；这里把它标明是同向备选，与真正换了方向的
    「定价热格」区分开。
    """
    if v.get("guard") == v.get("second"):
        return "同向备选比分"
    return v.get("guard_mode") or ""


def vline(v) -> str:
    """一行式三档结论：首选／次选／防范，带方向与概率。"""
    g = vg(v)
    tail = f"（{e(g)}）" if g else ""
    return (f'<b>{e(v["first"])}</b> {f(v["first_p"])}% → {e(v["first_score"])}；'
            f'次选 <b>{e(v["second"])}</b> {f(v["second_p"])}% → {e(v["second_score"])}；'
            f'防范 <b>{e(v["guard"])}</b> {f(v["guard_p"])}% → {e(v["guard_score"])}{tail}')


def edge(m) -> list:
    return m.get("edge") or [m["p"][i] - m["mk"][i] for i in range(3)]


def maxpp(m) -> float:
    return max(abs(x) for x in edge(m))


def bars(m, w: int = 100, ghost: bool = True) -> str:
    """三格概率条：模型实心 + 定价位置的竖线。"""
    out = []
    for i, d in enumerate(DIRS):
        p, k = m["p"][i], m["mk"][i]
        d_ = edge(m)[i]
        out.append(
            f'<div class="brow"><span class="bl">{d}</span>'
            f'<span class="bt"><i class="bf" style="width:{p:.1f}%"></i>'
            + (f'<i class="bg2" style="left:{min(max(k,0),100):.1f}%"></i>' if ghost else "")
            + f'</span><span class="bv">{p:.1f}<em>%</em></span>'
            f'<span class="bd {tone(d_)}">{sg(d_)}</span>'
            f'<span class="bm">定价 {k:.1f}%</span></div>'
        )
    return "".join(out)


def goal_chart(m, h: int = 60) -> str:
    g = m.get("goals_dc") or []
    mx = max(g) if g else 100
    cols = []
    for i, v in enumerate(g[:8]):
        hp = max(2.0, v / mx * 100) if mx else 2
        cols.append(
            f'<div class="gc"><i style="height:{hp * h / 100:+.1f}px"></i>'
            f'<b>{f(v)}</b><s>{i}</s></div>'
        )
    return f'<div class="gchart" style="height:{h}px">{"".join(cols)}</div>'


def matrix_svg(m, size: int = 300) -> str:
    mat = m.get("matrix") or []
    if not mat:
        return ""
    cells = [(i, j, mat[i][j]) for i in range(min(7, len(mat))) for j in range(min(7, len(mat[0])))]
    mx = max(c[2] for c in cells) or 1
    n = 7
    cw = size / (n + 1)
    parts = []
    for i in range(n):
        parts.append(f'<text class="mx-h" x="{cw * (i + 1.5):.1f}" y="{cw * 0.75:.1f}">{i}</text>')
        parts.append(f'<text class="mx-v" x="{cw * 0.5:.1f}" y="{cw * (i + 1.75):.1f}">{i}</text>')
    for i, j, v in cells:
        op = 0.06 + (v / mx) * 0.88
        parts.append(
            f'<rect x="{cw * (j + 1) + 1:.1f}" y="{cw * (i + 1) + 1:.1f}" width="{cw - 2:.1f}" height="{cw - 2:.1f}" '
            f'fill="currentColor" fill-opacity="{op:.2f}" rx="2"/>'
        )
        if v >= mx * 0.30:
            parts.append(
                f'<text class="mx-n" x="{cw * (j + 1.5):.1f}" y="{cw * (i + 1.62):.1f}">{f(v, 1)}</text>'
            )
    return (
        f'<svg class="mx" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
        + "".join(parts) + "</svg>"
    )


def radar_svg(m, size: int = 260) -> str:
    """六维：主胜/平/客胜/大2.5/双方进球/比分集中（模型 vs 定价）。"""
    conf = m.get("conf") or {}
    t3 = float(conf.get("top3") or 0)
    pct = [(m["p"][0], m["mk"][0]), (m["p"][1], m["mk"][1]), (m["p"][2], m["mk"][2]),
           (m["over"]["2.5"], m["over"]["2.5"]), (m["btts"], m["btts"]),
           (t3 * 2.0, t3 * 2.0)]
    labels = ["主胜", "平", "客胜", "大2.5", "双方进球", "比分集中"]
    cx = cy = size / 2
    R = size * 0.34
    pts_m, pts_k = [], []
    for i, (a, b) in enumerate(pct):
        ang = -math.pi / 2 + i * math.pi * 2 / 6
        ra = R * min(1.0, a / 100)
        rk = R * min(1.0, b / 100)
        pts_m.append((cx + ra * math.cos(ang), cy + ra * math.sin(ang)))
        pts_k.append((cx + rk * math.cos(ang), cy + rk * math.sin(ang)))
    poly = lambda ps: " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)
    rings = "".join(
        f'<circle cx="{cx}" cy="{cy}" r="{R * k / 4:.1f}" fill="none" stroke="currentColor" stroke-opacity=".14"/>'
        for k in (1, 2, 3, 4)
    )
    spokes = []
    for i, lab in enumerate(labels):
        ang = -math.pi / 2 + i * math.pi * 2 / 6
        x2, y2 = cx + R * math.cos(ang), cy + R * math.sin(ang)
        lx, ly = cx + (R + 26) * math.cos(ang), cy + (R + 26) * math.sin(ang)
        spokes.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="currentColor" stroke-opacity=".14"/>')
        anchor = "middle" if abs(math.cos(ang)) < 0.3 else ("start" if math.cos(ang) > 0 else "end")
        spokes.append(f'<text class="rd-l" x="{lx:.1f}" y="{ly + 4:.1f}" text-anchor="{anchor}">{lab}</text>')
    return (
        f'<svg class="rd" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
        + rings + "".join(spokes)
        + f'<polygon class="rd-k" points="{poly(pts_k)}"/>'
        + f'<polygon class="rd-m" points="{poly(pts_m)}"/>'
        + "</svg>"
    )


def inj_rows(m, limit: int = 7) -> str:
    inj = (m.get("intel") or {}).get("inj") or []
    if not inj:
        return '<div class="none">无伤停与停赛登记</div>'
    side = {"home": "主", "away": "客"}
    rows = []
    for p in inj[:limit]:
        rows.append(
            f'<div class="ij"><b class="s{side.get(p["side"], "")}">{side.get(p["side"], "")}</b>'
            f'<span>{e(p["name"])}</span><em>{e(p["pos"])}</em>'
            f'<s>{p["kind"]}</s><u>{p["apps"]}场</u></div>'
        )
    if len(inj) > limit:
        rows.append(f'<div class="ij more">另有 {len(inj) - limit} 人…</div>')
    return "".join(rows)


def recent_rows(m, limit: int = 4) -> str:
    t = m.get("tech") or {}
    out = []
    for side, lab in (("home", "主"), ("away", "客")):
        blk = t.get(side) or {}
        for r in (blk.get("results") or [])[:limit]:
            out.append(
                f'<div class="rc"><b class="s{lab}">{lab}</b><span>{e(r.get("d"))}</span>'
                f'<em>{e(r.get("m"))}</em><s>{e(r.get("ht") or "")}</s></div>'
            )
    return "".join(out)


def score_rows(m, n: int = 6) -> str:
    top = (m.get("top") or [])[:n]
    if not top:
        return ""
    rows = []
    for t in top:
        ev = t.get("ev")
        evc = "g" if (ev is not None and ev >= 0) else "m"
        rows.append(
            f'<div class="sr"><b>{t["s"]}</b><span><i style="width:{min(100, t["p"] * 5):.1f}%"></i></span>'
            f'<em>{f(t["p"])}%</em>'
            + (f'<s>{f(t.get("odd"), 2)}</s><u class="{evc}">{sg(ev, 2)}</u>' if t.get("odd") else "")
            + "</div>"
        )
    return "".join(rows)


def hand_rows(m) -> str:
    """让球胜平负：模型 / 定价 / 偏差三行。

    让球是另一套口径（让 -1 后主胜要赢 2 球），与不让球的胜平负并列看，
    才能看出「分歧落在谁赢还是赢几个」。
    """
    hp, hmk = m.get("hp"), m.get("hmk")
    if not hp or not hmk:
        return '<div class="none">本场无让球固定奖金</div>'
    he = m.get("h_edge") or [hp[i] - hmk[i] for i in range(3)]
    out = [f'<div class="hrow hh"><span>让球 {m.get("hand", 0):+d}</span>'
           f'<b>模型</b><b>定价</b><b>偏差</b></div>']
    for i, d in enumerate(DIRS):
        out.append(
            f'<div class="hrow"><span>{d}</span>'
            f'<b>{f(hp[i])}%</b><b>{f(hmk[i])}%</b>'
            f'<b class="{tone(he[i])}">{sg(he[i])}</b></div>'
        )
    return "".join(out)


def nodraw_bar(m) -> str:
    """去掉平局后的胜负拆分（让球盘常用来判「谁更可能赢」）。"""
    w = m.get("win_nodraw")
    if not w:
        return '<div class="none">—</div>'
    return (
        '<div class="nd"><div class="ndb">'
        f'<i style="width:{min(100, w[0]):.1f}%"></i></div>'
        f'<div class="ndt"><b>主 {f(w[0])}%</b><s>客 {f(w[1])}%</s></div></div>'
    )


def dc_compare(m) -> str:
    """泊松 vs Dixon-Coles：四格低比分修正量 + 胜平负两法之差。

    这一块的作用是让读者看见 ρ 修正到底动了哪里，
    而不是只拿到一个「已经修好」的矩阵。
    """
    ld = m.get("low_delta") or []
    oc = m.get("oc") or {}
    rows = []
    for r in ld:
        d = r["p_dc"] - r["p_pois"]
        rows.append(
            f'<div class="dcr"><b>{r["s"]}</b><span>{f(r["p_pois"])}%</span>'
            f'<s>→</s><em>{f(r["p_dc"])}%</em>'
            f'<u class="{tone(d)}">{sg(d, 2)}</u></div>'
        )
    head = ""
    if oc.get("pois") and oc.get("dc"):
        dp = [oc["dc"][i] - oc["pois"][i] for i in range(3)]
        head = (f'<div class="dch">胜平负两法差 '
                + " / ".join(f'<u class="{tone(dp[i])}">{sg(dp[i], 1)}</u>' for i in range(3))
                + "</div>")
    return head + "".join(rows)


def ext_block(m) -> str:
    """外部预测对照：只有抓到源才写，抓不到就整块省略（不写「待补」）。

    多源合并时 note 用「 ｜ 」拼接，同一条会被重复抓两遍（同一 provider 两次返回
    同一句），这里先去重，否则页面上会出现「同一句话连着说两遍」。
    """
    ext = m.get("ext") or {}
    sm, af = ext.get("sm"), ext.get("af")
    src = sm or af
    if not src:
        return ""
    lines = []
    note = (src.get("note") or "").strip()
    if note:
        seen, keep = set(), []
        for seg in note.split("｜"):
            s = seg.strip()
            # 同一句在不同 provider 返回里可能只差标点（「，」vs「；」、空格位），
            # 比较时抹掉非字母数字字符，才认得出是同一句。
            key = "".join(ch for ch in s.lower() if ch.isalnum() or ch == "%")
            if s and key and key not in seen:
                seen.add(key)
                keep.append(s)
        lines.append(f'<div class="exn">{e(" ｜ ".join(keep))}</div>')
    if src.get("predicted_dir"):
        lines.append(
            f'<div class="exd">外部倾向 <b>{e(src["predicted_dir"])}</b>'
            f'{" · 命中概率 " + f(src.get("hit_prob")) + "%" if src.get("hit_prob") else ""}'
            f' · {e(src.get("provider") or "")}</div>'
        )
    return "".join(lines)


def flag_rows(m, limit: int = 0) -> str:
    """降权与溢价提示（steps.exclude / steps.rich）。

    这两组是模型自己标出来的「不建议主推」的格子，属于付费资料里
    最该给付费方看的部分 —— 只报好听的比分等于藏了一半结论。
    limit>0 时总条数截到这个数（版面紧的时候用）。
    """
    st = m.get("steps") or {}
    ne = 2 if not limit else max(1, min(2, limit // 2 or 1))
    nr = 3 if not limit else max(0, limit - ne)
    out = []
    for r in (st.get("exclude") or [])[:ne]:
        out.append(f'<div class="fl"><b class="r">{e(r.get("kind") or "剔除")}</b>'
                   f'<span>{e(r.get("k") or "")}</span><em>{e(r.get("why") or "")}</em></div>')
    for r in (st.get("rich") or [])[:nr]:
        out.append(f'<div class="fl"><b class="a">{e(r.get("kind") or "降权")}</b>'
                   f'<span>{e(r.get("k") or "")}</span><em>{e(r.get("why") or "")}</em></div>')
    return "".join(out) or '<div class="none">本场无需降权的格子</div>'


def tech_pair(m) -> str:
    """主客技术面对照（近况样本、半场占位、波动）。"""
    tech = m.get("tech") or {}
    h, a = tech.get("home") or {}, tech.get("away") or {}
    rows = [
        ("样本场次", h.get("n"), a.get("n"), 0),
        ("场均进球", h.get("gf_avg"), a.get("gf_avg"), 2),
        ("场均失球", h.get("ga_avg"), a.get("ga_avg"), 2),
        ("零封率", h.get("cs_rate"), a.get("cs_rate"), 0),
        ("上半场占比", h.get("share_1h"), a.get("share_1h"), 0),
        ("进球波动", h.get("sd_for"), a.get("sd_for"), 2),
    ]
    out = ['<div class="tp tp-h"><span></span><b>主</b><b>客</b></div>']
    for lab, hv, av, nd in rows:
        out.append(
            f'<div class="tp"><span>{lab}</span><b>{f(hv, nd)}</b><b>{f(av, nd)}</b></div>'
        )
    return "".join(out)


# ══════════════════════════════════════════════ 研判文字层
# 这一层只做一件事：把已经算好的数字翻译成人话。所有句子都必须能指着某个
# 具体读数，不写「状态不错」「士气高涨」这种没有数据支撑的话。
def _hand_word(hand: int) -> str:
    if hand > 0:
        return f"主队受让 {hand} 球"
    if hand < 0:
        return f"主队让 {-hand} 球"
    return "平手盘"


def _shape(lam_total: float) -> str:
    if lam_total >= 3.5:
        return "对攻形态"
    if lam_total >= 2.8:
        return "开放形态"
    if lam_total >= 2.1:
        return "中性形态"
    return "闷战形态"


def _rest_days(m) -> str:
    """距上一场的天数——赛程密度是影响赛果的实打实变量，能从缓存算出来就得给。"""
    tech = m.get("tech") or {}
    try:
        from datetime import date
        kick = m.get("kick") or ""
        dm = kick.split(" ")[0]
        mo, dd = dm.split("/")
        year = "2026"
        if int(mo) < 6:
            year = "2027"
        kd = date(int(year), int(mo), int(dd))
        out = []
        for side, lab in (("home", "主"), ("away", "客")):
            res = (tech.get(side) or {}).get("results") or []
            if not res:
                continue
            d = res[0].get("d") or ""
            try:
                y, mm, dd2 = d.split("-")
                rd = date(int(y), int(mm), int(dd2))
                out.append(f"{lab} {(kd - rd).days} 天")
            except Exception:  # noqa: BLE001
                continue
        return " · ".join(out) or "—"
    except Exception:  # noqa: BLE001
        return "—"


def market_read(m) -> str:
    """盘口分析解读：把让球盘、大小球盘、抽水、冷热四件事讲成一段话。"""
    hp, hmk = m.get("hp"), m.get("hmk")
    he = m.get("h_edge") or []
    eg = edge(m)
    kill = max(range(3), key=lambda k: abs(eg[k]))
    over, btts = m.get("over") or {}, m.get("btts")
    cold = m.get("cold") or {}
    lam_t = (m.get("lam") or {}).get("total") or 0
    ps = []

    # 一、让球盘
    if hp and hmk:
        hk = max(range(3), key=lambda k: abs(he[k]))
        ps.append(
            f"让球盘是{_hand_word(m['hand'])}。同一场比赛换成让球口径后，"
            f"模型给让球主胜 {f(hp[0])}%、平 {f(hp[1])}%、客胜 {f(hp[2])}%，"
            f"定价给 {f(hmk[0])}% / {f(hmk[1])}% / {f(hmk[2])}%。"
            f"两边分歧最深的一格是{DIRS[hk]}（{sg(he[hk])}pp）。"
        )
    else:
        ps.append(f"本场没有可用的让球固定奖金，让球口径只能缺着，不做估算。")

    # 二、让球与不让球的错位说明什么
    if hp and hmk:
        tight = abs(hp[0] - hmk[0]) <= 3 and abs(hp[2] - hmk[2]) <= 3
        ps.append(
            "让球一侧两边贴得近，说明盘口在「谁赢」这件事上没给出额外信息，"
            "分歧集中在不让球的胜平负上。"
            if tight else
            f"让球一侧两边拉得开（最大 {sg(he[max(range(3), key=lambda k: abs(he[k]))])}pp），"
            "说明定价对「赢几个」有自己的判断，跟它对「谁赢」的判断不是一回事。"
        )

    # 三、大小球盘
    if over:
        gap = (over.get("2.5") or 0) - 50
        ps.append(
            f"大小球上，模型给大 2.5 球 {f(over.get('2.5'))}%、大 3.5 球 {f(over.get('3.5'))}%、"
            f"双方进球 {f(btts)}%，λ 合计 {f(lam_t, 2)}，属于{_shape(lam_t)}。"
            + ("总量明显偏大，比分区间要往 2 球以上铺。" if gap >= 12 else
               "总量明显偏小，比分区间要往 2 球以内收。" if gap <= -12 else
               "总量居中，大小球这一格没有可做的差价。")
        )

    # 四、抽水与冷热
    po = m.get("payout")
    if po:
        ps.append(
            f"返还率 {f(po, 1)}%，抽水约 {f(100 - po, 1)} 个百分点，属于"
            + ("偏低（抽水偏重，定价对玩家的容错更小）。" if po < 88 else
               "中等水平。" if po < 92 else "偏高（抽水轻，定价更接近真实概率）。")
        )
    if cold:
        ps.append(
            f"冷门指数 {f(cold.get('index'))}：定价最热的一格是{cold.get('fav')}"
            f"（定价 {f(cold.get('fav_mk'))}%），模型只给 {f(cold.get('fav_model'))}%。"
            + ("最热那一头在模型里站不住，这是本场最值得盯的错位。" if (cold.get("index") or 0) >= 55 else
               "最热那一头模型也认，冷门指数不高。" if (cold.get("index") or 0) <= 30 else
               "最热那一头模型部分认，差距不算悬殊。")
        )

    # 五、定价变动（缓存里有开盘/最新与逐盘 notes，能读到什么就写什么）
    mv = m.get("move") or {}
    lh, oh = mv.get("latest_hand") or {}, mv.get("open_hand") or {}
    hist = mv.get("hand") or []
    if len(hist) >= 2 and lh and oh:
        ps.append(
            f"让球盘的定价从 {oh.get('t')} 的 "
            + " / ".join(f"{f(x, 2)}" for x in (oh.get("odds") or []))
            + f" 走到 {lh.get('t')} 的 "
            + " / ".join(f"{f(x, 2)}" for x in (lh.get("odds") or []))
            + "，中间有实际位移。")
    elif lh:
        ps.append(
            f"让球盘当前定价 {lh.get('t')}："
            + " / ".join(f"{f(x, 2)}" for x in (lh.get("odds") or []))
            + f"（去水后 {f((lh.get('p') or [0, 0, 0])[0])}% / "
            f"{f((lh.get('p') or [0, 0, 0])[1])}% / {f((lh.get('p') or [0, 0, 0])[2])}%）。"
        )
    g = mv.get("goals") or {}
    if g.get("odds_old") and g.get("odds_new"):
        o, nn = g["odds_old"], g["odds_new"]
        ch = [(k, o[k], nn[k]) for k in range(min(len(o), len(nn))) if abs(o[k] - nn[k]) > 1e-9]
        if ch:
            ps.append(
                f"总进球盘在 {g.get('t_old')} → {g.get('t_new')} 之间调过 "
                + "、".join(f"{k} 球 {f(a_, 2)}→{f(b_, 2)}" for k, a_, b_ in ch)
                + "，说明定价在「几个球」上做过一轮重估。")
        else:
            ps.append(f"总进球盘从 {g.get('t_old')} 到 {g.get('t_new')} 没有实质位移，几个球这一档是稳的。")
    notes = [x for x in (mv.get("notes") or []) if "波胆" in x or "半全场" in x][:2]
    for x in notes:
        ps.append(x)
    if not any(k in ps[-1] for k in ("让球盘",)) and not lh:
        ps.append("本期没有抓到完整的定价变动记录，这一块只能按静态结构读，不做「资金流向」这类推断。")

    return "".join(f"<p>{e(x)}</p>" for x in ps[:3])


def tactic_read(m) -> str:
    """战术风格与比赛走向：攻防强度、节奏、稳定性、交锋形态，最后落到走向。"""
    tech = m.get("tech") or {}
    h, a = tech.get("home") or {}, tech.get("away") or {}
    meet = tech.get("meet") or {}
    lam = m.get("lam") or {}
    lam_h = (lam.get("fin") or [0, 0])[0]
    lam_a = (lam.get("fin") or [0, 0])[1]
    lam_t = lam.get("total") or 0
    v = m.get("verdict") or {}
    ps = []

    ps.append(
        f"主队近 {h.get('n', 0)} 场场均 {f(h.get('gf_avg'), 2)} 进 {f(h.get('ga_avg'), 2)} 失，"
        f"零封率 {f(h.get('cs_rate'), 0)}%，进球波动（标准差）{f(h.get('sd_for'), 2)}；"
        f"客队近 {a.get('n', 0)} 场场均 {f(a.get('gf_avg'), 2)} 进 {f(a.get('ga_avg'), 2)} 失，"
        f"零封率 {f(a.get('cs_rate'), 0)}%，波动 {f(a.get('sd_for'), 2)}。"
    )
    # 攻防强度差 → 谁压谁
    dh = (h.get("gf_avg") or 0) - (a.get("ga_avg") or 0)
    da = (a.get("gf_avg") or 0) - (h.get("ga_avg") or 0)
    if dh - da >= 0.6:
        ps.append(f"主队进攻对客队防守占 {sg(dh, 2)} 球的净优势，客队进攻对主队防守只有 {sg(da, 2)}，"
                  "这一场是单边压制形态，主队场面上更主动。")
    elif da - dh >= 0.6:
        ps.append(f"客队进攻对主队防守占 {sg(da, 2)} 球的净优势，主队进攻对客队防守只有 {sg(dh, 2)}，"
                  "客队会在场面上更主动，主队多被动应付。")
    else:
        ps.append(f"两队攻防对位几乎对称（主 {sg(dh, 2)} / 客 {sg(da, 2)}），"
                  "谁也没有明显的结构优势，比赛容易在均势里拖延。")

    # 节奏：上半场进球占比
    sh, sa = h.get("share_1h"), a.get("share_1h")
    if sh is not None and sa is not None:
        avg1h = (sh + sa) / 2
        ps.append(
            f"节奏上，主队进球里 {f(sh, 0)}% 发生在上半场，客队 {f(sa, 0)}%，平均 {f(avg1h, 0)}%。"
            + ("两队都开场就开火，前 45 分钟就会分出声，比分容易早定。" if avg1h >= 55 else
               "两队都靠后程发力，上半场多半闷住，下半场才是分水岭。" if avg1h <= 45 else
               "上下半场进球分布均匀，没有明显的发力时段。")
        )

    # 稳定性
    sdh, sda = h.get("sd_for"), a.get("sd_for")
    if sdh is not None and sda is not None:
        ps.append(
            f"波动上，主队 {f(sdh, 2)}、客队 {f(sda, 2)}。"
            + ("两边波动都不小，单场结果的可预测性本来就偏低，比分区间要放宽。" if max(sdh, sda) >= 1.6 else
               "两边波动都小，进攻输出稳定，比分区间可以收窄。" if max(sdh, sda) <= 1.0 else
               "一边稳一边飘，飘的那一边是这场的主要不确定性。")
        )

    # 交锋形态
    if meet.get("n"):
        ps.append(
            f"交锋 {meet.get('n')} 场，场均 {f(meet.get('avg_total'), 2)} 球，"
            f"低比分（≤2 球）占 {f(meet.get('low2'), 0)}%，平局 {f(meet.get('draw'), 0)}%，"
            f"双方进球 {f(meet.get('btts'), 0)}%。"
            + ("这对冤家互相看得死，别按场均总进球的直觉往大球走。" if (meet.get("low2") or 0) >= 55 else
               "交锋偏开放，历史对决里进球不少。" if (meet.get("low2") or 0) <= 25 else
               "交锋形态居中，历史样本没给出明显偏向。")
        )

    # 走向
    ps.append(
        f"综合 λ 主 {f(lam_h, 2)} + 客 {f(lam_a, 2)} = {f(lam_t, 2)}，这是{_shape(lam_t)}。"
        f"走向上，模型首选{v.get('first') or '—'}（{f(v.get('first_p'))}%），"
        f"比分落在 {v.get('first_score') or '—'}；次选 {v.get('second') or '—'} "
        f"（{f(v.get('second_p'))}%）对应 {v.get('second_score') or '—'}。"
        + ("换言之，这场更可能是主队控制节奏、把比分压在一个球以内。" if lam_t <= 2.6 else
           "换言之，这场更可能是两队互有攻守、比分往上走。" if lam_t >= 3.3 else
           "换言之，这场不会一边倒，但也说不上是大开大合。")
    )
    return "".join(f"<p>{e(x)}</p>" for x in ps[:3])


def media_compare(m) -> str:
    """三方对照：我方后台模型 / 去水定价 / 外部媒体与 AI。"""
    p, mk = m.get("p"), m.get("mk")
    v = m.get("verdict") or {}
    ext = m.get("ext") or {}
    src = ext.get("sm") or ext.get("af") or {}
    eg = edge(m)
    rows = []
    if p:
        i = max(range(3), key=lambda k: p[k])
        rows.append(("我方后台模型", f"{DIRS[i]} {f(p[i])}%", f"首选比分 {v.get('first_score') or '—'}"))
    if mk:
        i = max(range(3), key=lambda k: mk[k])
        rows.append(("去水定价", f"{DIRS[i]} {f(mk[i])}%", "无抽水后的市场概率"))
    if src:
        rows.append(("外部媒体 / AI", src.get("predicted_dir") or "—",
                     f"命中概率 {f(src.get('hit_prob'))}% · {src.get('provider') or ''}"
                     if src.get("hit_prob") else (src.get("provider") or "")))
    out = []
    for a_, b_, c_ in rows:
        extra = ""
        if c_ and c_ not in ("无抽水后的市场概率",):
            extra = f' <i>{e(c_[:18])}</i>'
        out.append(f'<div class="mcr"><span>{e(a_)}</span><b>{e(b_)}{extra}</b></div>')
    note = (src.get("note") or "").strip()
    if note:
        seen, keep = set(), []
        for seg in note.split("｜"):
            s = seg.strip()
            key = "".join(ch for ch in s.lower() if ch.isalnum() or ch == "%")
            if s and key and key not in seen:
                seen.add(key)
                keep.append(s)
        # 一页只有三分之一宽给这一块，长备注会把整栏顶高，截到 60 字够读了
        merged = " ｜ ".join(keep)
        if len(merged) > 60:
            merged = merged[:60].rstrip() + "…"
        out.append(f'<p class="mc-n">{e(merged)}</p>')
    if len(rows) >= 2 and p and mk:
        kill = max(range(3), key=lambda k: abs(eg[k]))
        out.append(
            f'<p class="mc-n">差得最开的是{DIRS[kill]}：我方 {f(p[kill])}% vs 定价 {f(mk[kill])}%。'
            + ("外部同侧，只差幅度。" if src and (src.get("predicted_dir") or "") == DIRS[kill] else
               "外部未同侧支持，按我方独立判断记。")
            + "</p>")
    return "".join(out)


def factor_rows(m) -> str:
    """影响赛果的因素清单：能算的给数，没源的明写缺源，不含糊。"""
    tech = m.get("tech") or {}
    h, a = tech.get("home") or {}, tech.get("away") or {}
    inj = (m.get("intel") or {}).get("inj") or []
    meet = tech.get("meet") or {}
    conf = m.get("conf") or {}
    items = [
        ("主场优势", "有", f"主队近期主场 {h.get('n', 0)} 场样本"),
        ("赛程间隔", "有", _rest_days(m)),
        ("伤停规模", "有", f"{len(inj)} 人（含停赛）"),
        ("让球设置", "有", _hand_word(m["hand"])),
        ("抽水水平", "有", f"返还率 {f(m.get('payout'), 1)}%"),
        ("交锋形态", "有" if meet.get("n") else "无", 
         f"{meet.get('n', 0)} 场 · 低比分 {f(meet.get('low2'), 0)}%" if meet.get("n") else "无交锋样本"),
        ("进球波动", "有", f"主 {f(h.get('sd_for'), 2)} / 客 {f(a.get('sd_for'), 2)}"),
        ("数据样本厚度", "有", f"主 {h.get('n', 0)} 场 / 客 {a.get('n', 0)} 场，信心 {f(conf.get('total'), 0)}/100"),
        ("联赛排名 / 战意", "缺源", "积分榜接口本期返回空壳，不给排名与战意赋值"),
        ("xG / xGA / npxG", "缺源", "无数据源"),
        ("PPDA / 压迫强度", "缺源", "无数据源"),
        ("定位球 xG / 裁判 / 天气", "缺源", "均无数据源"),
        ("轮换与欧战赛程", "缺源", "不做猜测"),
    ]
    have = sum(1 for _, s, _ in items if s == "有")
    out = [f'<div class="fxh">已核实 {have} 项 · 缺源 {len(items) - have} 项（缺源不进结论）</div>']
    for name, st, note in items:
        cls = "ok" if st == "有" else "no"
        out.append(f'<div class="fx"><span>{e(name)}</span><b class="{cls}">{e(st)}</b>'
                   f'<em>{e(note)}</em></div>')
    return "".join(out)


def summary_read(m) -> str:
    """总结分析：一段收口。方向、比分、风险点三件事都要落地。"""
    v = m.get("verdict") or {}
    conf = m.get("conf") or {}
    st = m.get("steps") or {}
    cold = m.get("cold") or {}
    ex = (st.get("exclude") or [])[:1]
    ps = []
    ps.append(
        f"把上面的数合起来看：模型首选{v.get('first') or '—'}（{f(v.get('first_p'))}%），"
        f"次选{v.get('second') or '—'}（{f(v.get('second_p'))}%），"
        f"方向反过来时最可能的退路是{v.get('guard') or '—'}（{f(v.get('guard_p'))}%）。"
        f"比分上首选 {v.get('first_score') or '—'}、次选 {v.get('second_score') or '—'}、"
        f"防范 {v.get('guard_score') or '—'}。"
    )
    ps.append(
        f"这场能不能信，看的是信心 {f(conf.get('total'), 0)}/100"
        f"（{conf.get('grade') or '—'}）：样本 {conf.get('n_sample', 0)} 场、三方同向 "
        f"{conf.get('agree', 0)}/3、比分集中度 {f(conf.get('top3'), 1)}%。"
        + ("分数偏低，主要不是方向不明，而是样本太薄与两法不收敛，读的时候把幅度打对折。" 
           if (conf.get("total") or 0) < 45 else
           "分数中等偏上，方向可以采信，幅度仍要留余量。" if (conf.get("total") or 0) < 70 else
           "分数偏高，方向与幅度都可以按读数采信。")
    )
    if cold:
        ps.append(
            f"风险点一：冷门指数 {f(cold.get('index'))}，定价最热的{cold.get('fav')}"
            f"在模型里只有 {f(cold.get('fav_model'))}%，热的那一头未必稳。"
        )
    if ex:
        ps.append(f"风险点二：模型自己标了「{ex[0].get('kind') or '剔除'}」——{ex[0].get('k') or ''}，"
                  f"理由是不建议主推，这一类格子即便概率好看也别当首选。")
    ps.append(
        "风险点三：联赛排名、xG 系、裁判尺度、天气这些因素本期都没有数据源，"
        "不在结论里计权。等这些补齐，同一场比赛的读数会变，所以本页只对应当前这一版数据。"
    )
    return "".join(f"<p>{e(x)}</p>" for x in ps[:2])


CSS_BASE = """
@page { size:A4; margin:0; }
*{margin:0;padding:0;box-sizing:border-box;}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact;}
body{font-family:"Microsoft YaHei","PingFang SC","Noto Sans SC",sans-serif;color:#15181d;}
.page{width:210mm;height:297mm;overflow:hidden;position:relative;page-break-after:always;background:#fff;}
.page:last-child{page-break-after:auto;}
.brow{display:flex;align-items:center;gap:6px;}
.bl{width:34px;font-size:11px;color:#5b6472;flex:none;}
.bt{position:relative;flex:1;height:11px;background:#eceff3;border-radius:2px;overflow:hidden;}
.bf{position:absolute;left:0;top:0;height:100%;background:currentColor;border-radius:2px;}
.bg2{position:absolute;top:-2px;height:15px;width:2px;background:#15181d;}
.bv{width:46px;text-align:right;font-size:12px;font-weight:700;font-variant-numeric:tabular-nums;flex:none;}
.bv em{font-size:8px;font-style:normal;opacity:.5;margin-left:1px;}
.bd{width:44px;text-align:right;font-size:10.5px;font-weight:700;font-variant-numeric:tabular-nums;flex:none;}
.bm{width:56px;text-align:right;font-size:9px;color:#8b93a0;flex:none;}
.g,.bd.g,.sr u.g{color:#0f8a5f;} .a,.bd.a,.sr u.a{color:#c9761a;} .r,.bd.r,.sr u.r{color:#c9322b;}
.gchart{display:flex;align-items:flex-end;gap:4px;}
.gc{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;}
.gc i{width:100%;background:currentColor;border-radius:1px;display:block;}
.gc b{font-size:8.5px;font-weight:600;margin-top:2px;font-variant-numeric:tabular-nums;}
.gc s{font-size:8px;color:#98a0ad;text-decoration:none;}
.mx text{font-variant-numeric:tabular-nums;}
.mx-h,.mx-v{font-size:9px;fill:currentColor;opacity:.45;text-anchor:middle;}
.mx-n{font-size:7.6px;fill:currentColor;text-anchor:middle;font-weight:600;}
.rd circle,.rd line{color:rgba(128,128,128,.4);}
.rd-m{fill:currentColor;fill-opacity:.22;stroke:currentColor;stroke-width:1.6;}
.rd-k{fill:none;stroke:#c9322b;stroke-width:1.2;stroke-dasharray:3 3;}
.rd-l{font-size:9px;fill:currentColor;opacity:.62;}
.ij,.rc{display:flex;align-items:center;gap:6px;font-size:10px;line-height:1.7;}
.ij b,.rc b{width:15px;height:15px;border-radius:50%;display:grid;place-items:center;font-size:8.5px;color:#fff;flex:none;}
.ij b.s主,.rc b.s主{background:#2b5c98;} .ij b.s客,.rc b.s客{background:#a8453c;}
.ij span,.rc em{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.ij em,.rc s{font-size:9px;color:#8b93a0;font-style:normal;flex:none;text-decoration:none;}
.ij s{font-size:8.5px;color:#c9322b;flex:none;}
.ij u{font-size:8.5px;color:#8b93a0;text-decoration:none;flex:none;}
.rc span{font-size:8.5px;color:#98a0ad;flex:none;}
.rc s{font-size:8.5px;}
.sr{display:flex;align-items:center;gap:6px;font-size:10px;line-height:1.65;font-variant-numeric:tabular-nums;}
.sr b{width:30px;font-weight:700;flex:none;}
.sr span{flex:1;height:6px;background:#eceff3;border-radius:2px;overflow:hidden;}
.sr span i{display:block;height:100%;background:currentColor;}
.sr em{width:40px;text-align:right;font-weight:600;flex:none;font-style:normal;}
.sr s{width:36px;text-align:right;color:#8b93a0;flex:none;text-decoration:none;}
.sr u{width:40px;text-align:right;flex:none;text-decoration:none;font-size:9.5px;}
.none{font-size:9.5px;color:#98a0ad;}
/* 让球胜平负 / 净胜拆分 / 双法对照 / 降权提示 / 技术面对照 */
.hrow{display:flex;align-items:center;gap:4px;font-size:10px;line-height:1.7;font-variant-numeric:tabular-nums;}
.hrow span{width:38px;flex:none;color:#5b6472;}
.hrow b{flex:1;text-align:right;font-weight:600;}
.hrow.hh{font-size:8.5px;color:#8b93a0;border-bottom:1px dotted #dfe4ea;}
.hrow.hh b{font-weight:600;}
.nd{margin-top:1.5mm;}
.ndb{height:8px;background:#eceff3;border-radius:2px;overflow:hidden;}
.ndb i{display:block;height:100%;background:currentColor;}
.ndt{display:flex;justify-content:space-between;font-size:9.5px;margin-top:1mm;font-variant-numeric:tabular-nums;}
.ndt s{text-decoration:none;color:#8b93a0;}
.dch{font-size:9px;color:#8b93a0;margin-bottom:1mm;}
.dcr{display:flex;align-items:center;gap:5px;font-size:10px;line-height:1.65;font-variant-numeric:tabular-nums;}
.dcr b{width:28px;flex:none;}
.dcr span{flex:1;text-align:right;color:#8b93a0;}
.dcr s{text-decoration:none;color:#c9d2df;}
.dcr em{flex:1;font-style:normal;text-align:right;font-weight:600;}
.dcr u{width:44px;text-align:right;text-decoration:none;}
.exn{font-size:9.5px;line-height:1.7;color:#4a5261;}
.exd{font-size:9px;color:#8b93a0;margin-top:1mm;}
.fl{display:flex;gap:5px;font-size:9px;line-height:1.6;align-items:flex-start;margin-bottom:.8mm;}
.fl b{flex:none;font-size:8px;padding:0 3px;border-radius:2px;background:#f0f2f5;}
.fl b.a{background:#fdf3e6;color:#c9761a;}
.fl span{flex:none;font-weight:600;}
.fl em{flex:1;font-style:normal;color:#7b8493;}
.tp{display:flex;font-size:9.5px;line-height:1.65;font-variant-numeric:tabular-nums;}
.tp span{flex:1;color:#5b6472;}
.tp b{width:44px;text-align:right;font-weight:600;}
.tp.tp-h{font-size:8.5px;color:#8b93a0;border-bottom:1px dotted #dfe4ea;}
.tp.tp-h b{font-weight:600;}
"""


# ══════════════════════════════════════════════ 1 数据仪表盘
def lay_dashboard(m, i) -> str:
    css = """
    .pg1{background:#eef1f5;padding:11mm 11mm 9mm;display:flex;flex-direction:column;color:#20252e;}
    .pg1 .hd{display:flex;align-items:flex-end;justify-content:space-between;border-bottom:2px solid #20252e;padding-bottom:3mm;}
    .pg1 .no{font-size:34px;font-weight:800;letter-spacing:-1px;line-height:1;}
    .pg1 .no em{font-size:12px;font-weight:500;font-style:normal;letter-spacing:0;margin-left:6px;color:#5b6472;}
    .pg1 .mt{text-align:right;font-size:10px;color:#5b6472;line-height:1.6;}
    .pg1 .mt b{display:block;font-size:13px;color:#20252e;font-weight:700;}
    .pg1 .vs{display:flex;align-items:center;gap:4mm;margin:5mm 0 4mm;}
    .pg1 .tn{font-size:27px;font-weight:800;letter-spacing:-.5px;flex:1;line-height:1.15;}
    .pg1 .tn.away{text-align:right;}
    .pg1 .vv{font-size:11px;font-weight:700;color:#9aa3b0;flex:none;padding:0 1mm;}
    .pg1 .body{flex:1;display:grid;grid-template-columns:1.62fr 1fr;gap:4mm;min-height:0;}
    .pg1 .col{display:flex;flex-direction:column;gap:2.2mm;}
    .pg1 .card{background:#fff;border-radius:3mm;padding:3.2mm;box-shadow:0 1px 3px rgba(20,30,50,.08);}
    .pg1 .ct{font-size:9px;font-weight:700;letter-spacing:1.5px;color:#8b93a0;margin-bottom:2.5mm;text-transform:uppercase;}
    .pg1 .wdl{color:#20252e;
    }
    .pg1 .gwrap{color:#5b7fa8;}
    .pg1 .cf{display:flex;align-items:center;gap:3mm;}
    .pg1 .big{font-size:44px;font-weight:800;line-height:.92;letter-spacing:-2px;font-variant-numeric:tabular-nums;}
    .pg1 .big em{font-size:12px;font-style:normal;font-weight:500;color:#8b93a0;letter-spacing:0;}
    .pg1 .dims{font-size:9px;color:#7b8493;line-height:1.85;flex:1;}
    .pg1 .dims s{text-decoration:none;display:inline-block;width:13px;height:5px;border-radius:1px;background:#c9d2df;margin-right:4px;vertical-align:middle;}
    .pg1 .dims s.on{background:#2b5c98;}
    .pg1 .kpi2{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px;font-size:10px;}
    .pg1 .kpi2 div{display:flex;justify-content:space-between;border-bottom:1px dotted #dfe4ea;padding-bottom:2px;}
    .pg1 .kpi2 b{font-variant-numeric:tabular-nums;}
    .pg1 .verd{background:#20252e;color:#eef1f5;border-radius:3mm;padding:4mm;margin-top:auto;}
    .pg1 .card.ext .exn{max-height:16mm;overflow:hidden;}
    .pg1 .verd .vt{font-size:9px;letter-spacing:1.5px;color:#8b93a0;margin-bottom:2mm;}
    .pg1 .verd .vm{font-size:11px;line-height:1.75;}
    .pg1 .verd .vm b{color:#fff;}
    .pg1 .verd .sc3{display:flex;gap:2mm;margin-top:2.5mm;}
    .pg1 .verd .sc3 div{flex:1;background:#2e3542;border-radius:2mm;padding:2mm;text-align:center;}
    .pg1 .verd .sc3 s{display:block;font-size:8px;color:#9aa3b0;text-decoration:none;margin-bottom:1px;}
    .pg1 .verd .sc3 b{font-size:15px;font-weight:800;font-variant-numeric:tabular-nums;}
    .pg1 .ft{display:flex;justify-content:space-between;font-size:8px;color:#9aa3b0;margin-top:3mm;}
    """
    v = m["verdict"]
    conf = m.get("conf") or {}
    dims = "".join(
        f'<div><s class="{"on" if (conf.get(k) or 0) >= 17 else ""}"></s>{lab} {f(conf.get(k), 0)}</div>'
        for k, lab in (("w1", "样本厚度"), ("w2", "双法收敛"), ("w3", "三方一致"),
                       ("w4", "分歧可控"), ("w5", "比分集中"))
    )
    html = f"""
<section class="page pg1">
  <div class="hd">
    <div class="no">{e(m["no"][2:])}<em>{e(m["league"])} · 让球 {m["hand"]:+d}</em></div>
    <div class="mt"><b>{e(m["kick"])}</b>第 {i} 页 · 全维度推演</div>
  </div>
  <div class="vs">
    <div class="tn">{e(m["home"])}</div><div class="vv">VS</div><div class="tn away">{e(m["away"])}</div>
  </div>
  <div class="body">
    <div class="col">
      <div class="card wdl"><div class="ct">胜平负 · 模型实心 / 定价竖线</div>{bars(m)}</div>
      <div class="card"><div class="ct">进球分布 λ总 {f(m["lam"]["total"], 2)}</div>
        <div class="gwrap">{goal_chart(m, 52)}</div></div>
      <div class="card"><div class="ct">比分 Top5 · 模型概率 / 官方定价 / 溢价</div>{score_rows(m, 5)}</div>
      <div class="card"><div class="ct">让球胜平负 · 让 {m["hand"]:+d}</div>{hand_rows(m)}</div>
      <div class="card"><div class="ct">双法修正 · 泊松 → Dixon-Coles</div>{dc_compare(m)}</div>
      <div class="card"><div class="ct">近期走形 · 主 / 客各 2 场</div>{recent_rows(m, 2)}</div>
      <div class="card ext"><div class="ct">外部对照</div>{ext_block(m) or '<div class="none">本场没有可用外部源</div>'}</div>
    </div>
    <div class="col">
      <div class="card"><div class="ct">信心指数</div>
        <div class="cf"><div class="big">{f(conf.get("total"), 0)}<em>/100</em></div>
          <div class="dims">{dims}</div></div>
      </div>
      <div class="card"><div class="ct">阀门</div>
        <div class="kpi2">
          <div><span>大2.5</span><b>{f(m["over"]["2.5"])}%</b></div>
          <div><span>双方进球</span><b>{f(m["btts"])}%</b></div>
          <div><span>大3.5</span><b>{f(m["over"]["3.5"])}%</b></div>
          <div><span>最大偏差</span><b class="{tone(maxpp(m))}">{sg(maxpp(m))}pp</b></div>
          <div><span>返还率</span><b>{f(m.get("payout"), 1)}%</b></div>
          <div><span>冷门指数</span><b>{f(m["cold"]["index"])}</b></div>
        </div>
      </div>
      <div class="card"><div class="ct">技术面 · 主客对照</div>{tech_pair(m)}</div>
      <div class="card"><div class="ct">人员面 · {len((m.get("intel") or {}).get("inj") or [])} 人</div>{inj_rows(m, 4)}</div>
      <div class="card"><div class="ct">降权与剔除</div>{flag_rows(m)}</div>
      <div class="verd"><div class="vt">结论</div>
        <div class="vm"><b>{e(v["first"])}</b> 概率 {f(v["first_p"])}%，主推比分 <b>{e(v["first_score"])}</b>；
          次选 {e(v["second"])} {f(v["second_p"])}%，防范 {e(v["guard"])} {f(v["guard_p"])}%。</div>
        <div class="sc3">
          <div><s>首选</s><b>{e(v["first_score"])}</b></div>
          <div><s>次选</s><b>{e(v["second_score"])}</b></div>
          <div><s>防范</s><b>{e(v["guard_score"])}</b></div>
        </div></div>
    </div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料</span><span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 2 报纸头版
def lay_newspaper(m, i) -> str:
    css = """
    .pg2{background:#f5f2e9;color:#1a1a17;padding:9mm 12mm 10mm;display:flex;flex-direction:column;
         font-family:"SimSun","Songti SC","Noto Serif SC",serif;}
    .pg2 .mast{display:flex;align-items:baseline;justify-content:space-between;
               border-top:3px solid #1a1a17;border-bottom:1px solid #1a1a17;padding:2mm 0;}
    .pg2 .mast .l{font-size:26px;font-weight:800;letter-spacing:6px;}
    .pg2 .mast .r{font-size:9px;letter-spacing:1px;}
    .pg2 .dateline{display:flex;justify-content:space-between;font-size:8.5px;
                   border-bottom:1px solid #1a1a17;padding:1.2mm 0;letter-spacing:.5px;margin-bottom:4mm;}
    .pg2 h1{font-size:38px;line-height:1.12;font-weight:800;letter-spacing:-1px;margin-bottom:2mm;}
    .pg2 h1 em{display:block;font-size:15px;font-weight:400;font-style:normal;letter-spacing:2px;color:#6a6a60;margin:1mm 0;}
    .pg2 .dek{font-size:12px;line-height:1.7;border-left:3px solid #1a1a17;padding-left:3mm;margin:3mm 0 4mm;color:#3a3a35;}
    .pg2 .cols{flex:1;display:grid;grid-template-columns:1fr 1fr 1fr;gap:0;min-height:0;
               border-top:1px solid #1a1a17;padding-top:3mm;}
    .pg2 .cols > div{padding:0 3mm;border-right:1px solid #c9c6b8;font-size:10px;line-height:1.85;text-align:justify;}
    .pg2 .cols > div:first-child{padding-left:0;}
    .pg2 .cols > div:last-child{border-right:0;padding-right:0;}
    .pg2 .ct2{font-size:9px;font-weight:700;letter-spacing:2px;border-bottom:1px solid #1a1a17;
              padding-bottom:1mm;margin-bottom:1.5mm;display:block;}
    .pg2 table{width:100%;border-collapse:collapse;font-size:9.5px;margin:1mm 0 2mm;}
    .pg2 table td{padding:1px 0;border-bottom:1px dotted #c9c6b8;font-variant-numeric:tabular-nums;}
    .pg2 table td:last-child{text-align:right;font-weight:700;}
    .pg2 .drop::first-letter{font-size:30px;font-weight:800;float:left;line-height:.9;padding:1mm 1.5mm 0 0;}
    .pg2 .band{margin-top:3mm;border-top:2px solid #1a1a17;border-bottom:2px solid #1a1a17;
               padding:2.5mm 0;display:flex;justify-content:space-between;align-items:center;}
    .pg2 .band .b3{display:flex;gap:6mm;}
    .pg2 .band .b3 div{text-align:center;}
    .pg2 .band .b3 s{display:block;font-size:8px;text-decoration:none;letter-spacing:1px;color:#6a6a60;}
    .pg2 .band .b3 b{font-size:22px;font-weight:800;font-variant-numeric:tabular-nums;}
    .pg2 .band .b3 u{display:block;font-size:8.5px;text-decoration:none;}
    .pg2 .pgnum{font-size:9px;letter-spacing:1px;}
    """
    v = m["verdict"]
    st = m.get("steps") or {}
    tech = m.get("tech") or {}
    meet = tech.get("meet") or {}
    inj = (m.get("intel") or {}).get("inj") or []
    inj_txt = "；".join(f'{p["name"]}（{p["team"]}·{p["pos"]}·{p["kind"]}）' for p in inj[:4]) or "双方伤停名单均为空。"
    trs = "".join(
        f'<tr><td>{"主胜" if k == 0 else ("平" if k == 1 else "客胜")}</td>'
        f'<td>{f(m["p"][k])}%</td><td>{f(m["mk"][k])}%</td>'
        f'<td class="{tone(edge(m)[k])}">{sg(edge(m)[k])}</td></tr>' for k in range(3)
    )
    html = f"""
<section class="page pg2">
  <div class="mast"><div class="l">赛博聊球</div><div class="r">全维度推演 · 内部资料 · 第 {i} 版</div></div>
  <div class="dateline"><span>{e(m["no"])} · {e(m["league"])} · 让球 {m["hand"]:+d}</span><span>开赛 {e(m["kick"])} · 仅统计 90 分钟</span></div>
  <h1>{e(m["home"])}<em>对</em>{e(m["away"])}</h1>
  <div class="dek">{e(st.get("pattern") or "")}</div>
  <div class="cols">
    <div>
      <span class="ct2">一 · 数理</span>
      <div class="drop">{e(st.get("total") or "")}</div>
      <span class="ct2" style="margin-top:2mm">进球分布</span>
      <table>
        {"".join(f'<tr><td>{k} 球</td><td>{f(v_)}%</td></tr>' for k, v_ in list(enumerate(m.get("goals_dc") or []))[:6])}
      </table>
    </div>
    <div>
      <span class="ct2">二 · 结构</span>
      <table>
        <tr><td>模型</td><td>{f(m["p"][0])}</td><td>{f(m["p"][1])}</td><td>{f(m["p"][2])}</td></tr>
        <tr><td>定价</td><td>{f(m["mk"][0])}</td><td>{f(m["mk"][1])}</td><td>{f(m["mk"][2])}</td></tr>
        <tr><td>偏差</td><td class="{tone(edge(m)[0])}">{sg(edge(m)[0])}</td>
            <td class="{tone(edge(m)[1])}">{sg(edge(m)[1])}</td>
            <td class="{tone(edge(m)[2])}">{sg(edge(m)[2])}</td></tr>
      </table>
      <span class="ct2">三 · 矩阵</span>
      <div>{e(st.get("matrix") or "")}</div>
      <span class="ct2" style="margin-top:2mm">四 · 近况</span>
      主队近 {tech.get("home", {}).get("n", 0)} 场场均 {f(tech.get("home", {}).get("gf_avg"), 2)} 进
      {f(tech.get("home", {}).get("ga_avg"), 2)} 失、零封率 {f(tech.get("home", {}).get("cs_rate"), 0)}%；
      客队近 {tech.get("away", {}).get("n", 0)} 场场均 {f(tech.get("away", {}).get("gf_avg"), 2)} 进
      {f(tech.get("away", {}).get("ga_avg"), 2)} 失、零封率 {f(tech.get("away", {}).get("cs_rate"), 0)}%。
      交锋 {meet.get("n", 0)} 场，场均 {f(meet.get("avg_total"), 2)} 球，平局占 {f(meet.get("draw"), 0)}%。
    </div>
    <div>
      <span class="ct2">五 · 人员</span>
      <div>{e(inj_txt)}</div>
      <span class="ct2" style="margin-top:2mm">六 · 冷门</span>
      定价最热是 <b>{e(m["cold"]["fav"])}</b> {f(m["cold"]["fav_mk"])}%，
      模型只给 {f(m["cold"]["fav_model"])}%；冷门指数 {f(m["cold"]["index"])}，
      次冷落在 <b>{e(m["cold"]["main_cold"])}</b> {f(m["cold"]["main_cold_p"])}%。
      <span class="ct2" style="margin-top:2mm">七 · 缺口</span>
      {"没有 xG、PPDA、定位球 xG 与裁判尺度的数据源，本页一律留空，不用估算值冒充。" if not m.get("warn") else e("；".join(m.get("warn") or []))}
    </div>
  </div>
  <div class="band">
    <div class="b3">
      <div><s>首选</s><b>{e(v["first"])}</b><u>{e(v["first_score"])} · {f(v["first_p"])}%</u></div>
      <div><s>次选</s><b>{e(v["second"])}</b><u>{e(v["second_score"])} · {f(v["second_p"])}%</u></div>
      <div><s>防范</s><b>{e(v["guard"])}</b><u>{e(v["guard_score"])} · {f(v["guard_p"])}%</u></div>
    </div>
    <div class="pgnum">— {i:02d} —</div>
  </div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 3 比分矩阵
def lay_matrix(m, i) -> str:
    css = """
    .pg3{background:#101720;color:#dfe7f1;padding:11mm;display:flex;flex-direction:column;}
    .pg3 .top{display:flex;justify-content:space-between;align-items:flex-start;
              border-bottom:1px solid rgba(220,235,255,.18);padding-bottom:3mm;}
    .pg3 .top .l .n{font-size:11px;letter-spacing:3px;opacity:.55;}
    .pg3 .top .l h1{font-size:29px;font-weight:700;letter-spacing:.5px;margin-top:1mm;line-height:1.2;}
    .pg3 .top .l h1 s{text-decoration:none;opacity:.35;font-size:17px;margin:0 2mm;font-weight:400;}
    .pg3 .top .r{text-align:right;font-size:10px;opacity:.7;line-height:1.7;}
    .pg3 .top .r b{display:block;font-size:19px;color:#7fc7ff;font-weight:700;}
    .pg3 .grid2{flex:1;display:grid;grid-template-columns:1fr 66mm;gap:7mm;margin-top:5mm;min-height:0;}
    .pg3 .mwrap{display:flex;flex-direction:column;}
    .pg3 .mcap{font-size:9px;letter-spacing:2px;opacity:.5;margin-bottom:3mm;}
    .pg3 .mxbox{color:#7fc7ff;display:flex;justify-content:center;}
    .pg3 .mxbox .mx{color:#7fc7ff;}
    .pg3 .mxbox text{fill:#cfe4fa;}
    .pg3 .mx-h,.pg3 .mx-v{fill:#7fc7ff;opacity:.55;}
    .pg3 .mx-n{fill:#08121c;font-weight:700;}
    .pg3 .note{font-size:9.5px;line-height:1.9;opacity:.72;margin-top:3mm;}
    .pg3 .side{display:flex;flex-direction:column;gap:3mm;}
    .pg3 .blk{border:1px solid rgba(220,235,255,.16);border-radius:2mm;padding:3mm;}
    .pg3 .blk .t{font-size:8.5px;letter-spacing:2px;opacity:.5;margin-bottom:2mm;}
    .pg3 .prob{display:flex;gap:2mm;}
    .pg3 .prob div{flex:1;text-align:center;}
    .pg3 .prob b{display:block;font-size:19px;font-weight:700;font-variant-numeric:tabular-nums;}
    .pg3 .prob s{display:block;font-size:8.5px;opacity:.55;text-decoration:none;margin-bottom:1mm;}
    .pg3 .prob u{display:block;font-size:9px;text-decoration:none;margin-top:1mm;}
    .pg3 .lam{display:flex;align-items:baseline;gap:3mm;font-variant-numeric:tabular-nums;}
    .pg3 .lam b{font-size:22px;color:#7fc7ff;}
    .pg3 .lam em{font-style:normal;font-size:10px;opacity:.5;}
    .pg3 .tl{font-size:10px;line-height:1.9;font-variant-numeric:tabular-nums;}
    .pg3 .tl div{display:flex;justify-content:space-between;border-bottom:1px dotted rgba(220,235,255,.13);}
    .pg3 .tl b{color:#7fc7ff;font-weight:600;}
    .pg3 .ft{margin-top:auto;display:flex;justify-content:space-between;font-size:8px;opacity:.35;}
    .pg3 .brow .bt{background:rgba(220,235,255,.12);}
    .pg3 .brow .bg2{background:#dfe7f1;}
    .pg3 .hrow span,.pg3 .hrow.hh{color:#9fb4cc;}
    .pg3 .hrow.hh{border-bottom-color:rgba(220,235,255,.16);}
    .pg3 .dcr span,.pg3 .dcr s,.pg3 .dch{color:#9fb4cc;}
    .pg3 .dcr em{color:#dfe7f1;}
    .pg3 .fl b{background:rgba(220,235,255,.12);color:#dfe7f1;}
    .pg3 .fl b.a{background:rgba(201,118,26,.22);color:#ffc98a;}
    .pg3 .fl b.r{background:rgba(201,50,43,.22);color:#ff9b95;}
    .pg3 .fl span{color:#dfe7f1;}
    .pg3 .fl em{color:#9fb4cc;}
    .pg3 .none{color:#7d90a6;}
    .pg3 .ij span,.pg3 .rc em{color:#dfe7f1;}
    .pg3 .sr span{background:rgba(220,235,255,.12);}
    """
    v = m["verdict"]
    html = f"""
<section class="page pg3">
  <div class="top">
    <div class="l"><div class="n">{e(m["no"])} · {e(m["league"])}</div>
      <h1>{e(m["home"])}<s>vs</s>{e(m["away"])}</h1></div>
    <div class="r"><b>{e(m["kick"])}</b>让球 {m["hand"]:+d} · 第 {i} 页</div>
  </div>
  <div class="grid2">
    <div class="mwrap">
      <div class="mcap">比分概率矩阵 · 行＝主队进球 · 列＝客队进球 · 颜色深＝概率高</div>
      <div class="mxbox">{matrix_svg(m, 380)}</div>
      <div class="note">矩阵走的是 Dixon-Coles 修正后的联合分布（低比分格按 ρ = {f(pc.RHO, 2)} 修正），
        比纯独立泊松更贴近真实赛果的 0-0 / 1-1 偏厚。左侧侧栏的 λ 是综合值，
        与方法1（实际数据）与方法2（市场反推）分开列出；两法相差越大，本页的绝对值越只能当方向读。</div>
    </div>
    <div class="side">
      <div class="blk"><div class="t">胜平负 · 模型 / 定价</div>
        <div class="prob">
          <div><s>主胜</s><b>{f(m["p"][0])}</b><u class="{tone(edge(m)[0])}">{sg(edge(m)[0])}pp</u></div>
          <div><s>平</s><b>{f(m["p"][1])}</b><u class="{tone(edge(m)[1])}">{sg(edge(m)[1])}pp</u></div>
          <div><s>客胜</s><b>{f(m["p"][2])}</b><u class="{tone(edge(m)[2])}">{sg(edge(m)[2])}pp</u></div>
        </div></div>
      <div class="blk"><div class="t">λ 双法</div>
        <div class="lam"><b>{f(m["lam"]["fin"][0], 2)}</b><em>+</em><b>{f(m["lam"]["fin"][1], 2)}</b><em>= {f(m["lam"]["total"], 2)}</em></div>
        <div class="tl" style="margin-top:2mm">
          <div><span>方法1 实际数据</span><b>{f((m["lam"].get("l1") or [0,0])[0], 2)} / {f((m["lam"].get("l1") or [0,0])[1], 2)}</b></div>
          <div><span>方法2 市场反推</span><b>{f((m["lam"].get("l2") or [0,0])[0], 2)} / {f((m["lam"].get("l2") or [0,0])[1], 2)}</b></div>
        </div></div>
      <div class="blk"><div class="t">关键比分 Top6</div>{score_rows(m, 6)}</div>
      <div class="blk"><div class="t">让球 {m["hand"]:+d} · 模型 / 定价 / 偏差</div>{hand_rows(m)}</div>
      <div class="blk"><div class="t">泊松 vs Dixon-Coles</div>{dc_compare(m)}</div>
      <div class="blk"><div class="t">人员 · {len((m.get("intel") or {}).get("inj") or [])} 人</div>{inj_rows(m, 5)}</div>
      <div class="blk"><div class="t">降权与剔除</div>{flag_rows(m)}</div>
      <div class="blk"><div class="t">结论 · 首选 / 次选 / 防范</div>
        <div class="tl">
          <div><span>{e(v["first"])}</span><b>{e(v["first_score"])} · {f(v["first_p"])}%</b></div>
          <div><span>{e(v["second"])}</span><b>{e(v["second_score"])} · {f(v["second_p"])}%</b></div>
          <div><span>{e(v["guard"])}</span><b>{e(v["guard_score"])} · {f(v["guard_p"])}%</b></div>
        </div></div>
    </div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料</span><span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 4 对半分栏
def lay_split(m, i) -> str:
    css = """
    .pg4{display:flex;color:#1b1f26;background:#fff;}
    .pg4 .L{width:76mm;background:#22405f;color:#eaf1f8;padding:13mm 8mm 10mm;display:flex;flex-direction:column;}
    .pg4 .L .no{font-size:10px;letter-spacing:3px;opacity:.65;}
    .pg4 .L .k{font-size:23px;font-weight:700;margin-top:2mm;line-height:1.15;}
    .pg4 .L .hm{margin-top:auto;}
    .pg4 .L .hm .t{font-size:10px;letter-spacing:2px;opacity:.55;margin-bottom:1mm;}
    .pg4 .L .hm .n{font-size:32px;font-weight:800;line-height:1.08;letter-spacing:-.5px;}
    .pg4 .L .hm .n.c{opacity:.75;}
    .pg4 .L .bs{margin:7mm 0;height:2px;background:linear-gradient(90deg,#7fb2e0,transparent);}
    .pg4 .L .qf{font-size:10px;line-height:1.9;opacity:.8;}
    .pg4 .L .qf b{color:#fff;}
    .pg4 .L .vs{font-size:10px;letter-spacing:5px;opacity:.5;margin:3mm 0;}
    .pg4 .R{flex:1;padding:12mm 11mm 10mm;display:flex;flex-direction:column;}
    .pg4 .R .rh{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid #22405f;padding-bottom:2mm;}
    .pg4 .R .rh h2{font-size:13px;font-weight:700;letter-spacing:1px;color:#22405f;}
    .pg4 .R .rh span{font-size:9px;color:#8b93a0;}
    .pg4 .R .kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:2mm;margin:4mm 0;}
    .pg4 .R .kpis div{border:1px solid #e2e7ee;border-radius:2mm;padding:2.5mm;text-align:center;}
    .pg4 .R .kpis s{display:block;font-size:8px;color:#8b93a0;text-decoration:none;margin-bottom:1mm;}
    .pg4 .R .kpis b{font-size:17px;font-weight:700;font-variant-numeric:tabular-nums;}
    .pg4 .R .sec{margin-bottom:3.5mm;}
    .pg4 .R .sec .st{font-size:8.5px;letter-spacing:2px;color:#8b93a0;margin-bottom:1.5mm;}
    .pg4 .R .wdl{color:#22405f;}
    .pg4 .R .verd{margin-top:auto;background:#f2f5f9;border-left:3px solid #22405f;padding:3mm;}
    .pg4 .R .verd .t{font-size:8.5px;letter-spacing:2px;color:#8b93a0;margin-bottom:1.5mm;}
    .pg4 .R .verd .m{font-size:10.5px;line-height:1.8;}
    .pg4 .R .verd .sc{display:flex;gap:2mm;margin-top:2mm;}
    .pg4 .R .verd .sc div{flex:1;background:#fff;border-radius:1.5mm;padding:1.5mm;text-align:center;}
    .pg4 .R .verd .sc s{display:block;font-size:7.5px;color:#8b93a0;text-decoration:none;}
    .pg4 .R .verd .sc b{font-size:14px;font-variant-numeric:tabular-nums;}
    .pg4 .R .ft{display:flex;justify-content:space-between;font-size:8px;color:#a6aeb9;margin-top:3mm;}
    .pg4 .L .ov{font-size:9px;line-height:1.8;opacity:.72;margin-top:4mm;}
    .pg4 .L .ov b{opacity:1;color:#fff;}
    .pg4 .L .ov .row{display:flex;justify-content:space-between;border-bottom:1px dotted rgba(234,241,248,.18);padding:1px 0;}
    """
    v = m["verdict"]
    conf = m.get("conf") or {}
    st = m.get("steps") or {}
    html = f"""
<section class="page pg4">
  <div class="L">
    <div class="no">{e(m["no"])} · {e(m["league"])}</div>
    <div class="k">{e(m["kick"])}</div>
    <div class="vs">V S</div>
    <div class="hm">
      <div class="t">主队</div><div class="n">{e(m["home"])}</div>
      <div class="t" style="margin-top:5mm">客队</div><div class="n c">{e(m["away"])}</div>
    </div>
    <div class="bs"></div>
    <div class="qf">信心 <b>{f(conf.get("total"), 0)}</b>/100 · {e(conf.get("grade") or "")}<br>
      最大偏差 <b>{sg(maxpp(m))}pp</b> · 返还率 <b>{f(m.get("payout"), 1)}%</b><br>
      冷门指数 <b>{f(m["cold"]["index"])}</b> · 让球 {m["hand"]:+d}</div>
    <div class="ov">
      <div class="row"><span>λ 主 / 客</span><b>{f(m["lam"]["fin"][0], 2)} / {f(m["lam"]["fin"][1], 2)}</b></div>
      <div class="row"><span>合计</span><b>{f(m["lam"]["total"], 2)}</b></div>
      <div class="row"><span>大 3.5</span><b>{f(m["over"]["3.5"])}%</b></div>
      <div class="row"><span>去掉平局</span><b>主 {f((m.get("win_nodraw") or [0, 0])[0])}%</b></div>
      <div class="row"><span>冷门最热</span><b>{e(m["cold"]["fav"])}</b></div>
    </div>
  </div>
  <div class="R">
    <div class="rh"><h2>三向概率与阀门</h2><span>实心＝模型 · 竖线＝定价</span></div>
    <div class="kpis">
      <div><s>大 2.5 球</s><b>{f(m["over"]["2.5"])}<em style="font-size:9px">%</em></b></div>
      <div><s>双方进球</s><b>{f(m["btts"])}<em style="font-size:9px">%</em></b></div>
      <div><s>λ 合计</s><b>{f(m["lam"]["total"], 2)}</b></div>
    </div>
    <div class="sec wdl"><div class="st">胜 平 负</div>{bars(m)}</div>
    <div class="sec"><div class="st">进球分布</div><div style="color:#22405f">{goal_chart(m, 46)}</div></div>
    <div class="sec"><div class="st">比分 Top4 · 概率 / 定价 / 溢价</div>{score_rows(m, 4)}</div>
    <div class="sec"><div class="st">让球 {m["hand"]:+d} · 模型 / 定价 / 偏差</div>{hand_rows(m)}</div>
    <div class="sec"><div class="st">双法修正 · 泊松 → Dixon-Coles</div>{dc_compare(m)}</div>
    <div class="sec"><div class="st">技术面 · 主客对照</div>{tech_pair(m)}</div>
    <div class="sec"><div class="st">人员面</div>{inj_rows(m, 3)}</div>
    <div class="sec"><div class="st">降权与剔除</div>{flag_rows(m)}</div>
    <div class="verd"><div class="t">结论</div>
      <div class="m">{e(v["first"])} 是模型首选（{f(v["first_p"])}%），
        次选 {e(v["second"])} {f(v["second_p"])}%；若要防一手，落在 {e(v["guard"])} {f(v["guard_p"])}%（{e(vg(v))}）。</div>
      <div class="sc"><div><s>首选</s><b>{e(v["first_score"])}</b></div>
        <div><s>次选</s><b>{e(v["second_score"])}</b></div>
        <div><s>防范</s><b>{e(v["guard_score"])}</b></div></div></div>
    <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料 · 第 {i} 页</span><span>仅统计 90 分钟常规时间</span></div>
  </div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 5 时间轴
def lay_timeline(m, i) -> str:
    css = """
    .pg5{background:#fbfaf7;color:#22201c;padding:11mm 12mm 9mm;display:flex;flex-direction:column;}
    .pg5 .hd{display:flex;align-items:center;gap:4mm;border-bottom:1px solid #ddd8cc;padding-bottom:3mm;}
    .pg5 .hd .badge{background:#22201c;color:#fbfaf7;font-size:9px;letter-spacing:2px;padding:1.5mm 3mm;}
    .pg5 .hd h1{font-size:24px;font-weight:700;letter-spacing:-.3px;flex:1;line-height:1.2;}
    .pg5 .hd h1 s{text-decoration:none;color:#a8a296;font-weight:400;font-size:15px;margin:0 2mm;}
    .pg5 .hd .km{font-size:10px;color:#6b665c;text-align:right;line-height:1.6;}
    .pg5 .body{flex:1;display:grid;grid-template-columns:1fr 52mm;gap:6mm;margin-top:4mm;min-height:0;}
    .pg5 .spine{position:relative;padding-left:9mm;}
    .pg5 .spine::before{content:"";position:absolute;left:2.6mm;top:2mm;bottom:2mm;width:1px;background:#ddd8cc;}
    .pg5 .nd{position:relative;margin-bottom:4mm;}
    .pg5 .nd::before{content:"";position:absolute;left:-7.4mm;top:1.4mm;width:6px;height:6px;border-radius:50%;
                     background:#fbfaf7;border:1.5px solid #22201c;}
    .pg5 .nd .tt{font-size:8.5px;letter-spacing:2px;color:#a8a296;margin-bottom:1mm;}
    .pg5 .nd .h{font-size:12.5px;font-weight:700;margin-bottom:1mm;line-height:1.4;}
    .pg5 .nd .b{font-size:10px;line-height:1.9;color:#4a463e;text-align:justify;}
    .pg5 .nd.hl::before{background:#b8853c;border-color:#b8853c;width:8px;height:8px;left:-7.9mm;}
    .pg5 .nd.hl .h{color:#8c5f1d;}
    .pg5 .side{display:flex;flex-direction:column;gap:2.5mm;}
    .pg5 .cb{border:1px solid #ddd8cc;background:#fff;padding:3mm;border-radius:1mm;}
    .pg5 .cb .t{font-size:8px;letter-spacing:2px;color:#a8a296;margin-bottom:1.5mm;}
    .pg5 .cb .big{font-size:26px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;}
    .pg5 .cb .big em{font-size:10px;font-style:normal;color:#a8a296;font-weight:400;}
    .pg5 .cb .row{display:flex;justify-content:space-between;font-size:9.5px;
                  border-bottom:1px dotted #e6e1d6;padding:1px 0;font-variant-numeric:tabular-nums;}
    .pg5 .cb .row b{font-weight:700;}
    .pg5 .ft{display:flex;justify-content:space-between;font-size:8px;color:#b3ad a0;color:#b3ada0;margin-top:3mm;}
    .pg5 .wdl{color:#22201c;}
    """
    v = m["verdict"]
    st = m.get("steps") or {}
    tech = m.get("tech") or {}
    meet = tech.get("meet") or {}
    mv = m.get("move") or {}
    spf = mv.get("spf_move") or []
    spf_txt = ""
    if mv.get("open_spf") and mv.get("latest_spf"):
        o, l = mv["open_spf"]["odds"], mv["latest_spf"]["odds"]
        spf_txt = "开盘 " + " / ".join(f(x, 2) for x in o) + " → 最新 " + " / ".join(f(x, 2) for x in l)
    html = f"""
<section class="page pg5">
  <div class="hd">
    <div class="badge">{e(m["no"])}</div>
    <h1>{e(m["home"])}<s>对</s>{e(m["away"])}</h1>
    <div class="km">{e(m["league"])} · 让球 {m["hand"]:+d}<br>{e(m["kick"])} 开赛</div>
  </div>
  <div class="body">
    <div class="spine">
      <div class="nd"><div class="tt">00 · 门槛</div>
        <div class="h">{e(m.get("payout") and ("返还率 " + f(m.get("payout"), 1) + "%") or "官方定价已取")}　最大偏差 {sg(maxpp(m))}pp</div>
        <div class="b">{e(spf_txt or "该场没有可用的定价变动记录，只按静态结构与模型对照。")}</div></div>
      <div class="nd"><div class="tt">01 · 数理</div>
        <div class="h">λ 主 {f(m["lam"]["fin"][0], 2)} / 客 {f(m["lam"]["fin"][1], 2)}，合计 {f(m["lam"]["total"], 2)}</div>
        <div class="b">{e(st.get("total") or "")}</div></div>
      <div class="nd hl"><div class="tt">02 · 结构</div>
        <div class="h">模型与定价的最大错位在 {e(DIRS[max(range(3), key=lambda k: abs(edge(m)[k]))])}</div>
        <div class="b">{e(st.get("pattern") or "")}</div></div>
      <div class="nd"><div class="tt">03 · 矩阵</div>
        <div class="h">比分集中度 {f((m.get("conf") or {}).get("top3"), 1)}%（Top3 合计）</div>
        <div class="b">{e(st.get("matrix") or "")}</div></div>
      <div class="nd"><div class="tt">04 · 基本面</div>
        <div class="h">主队零封率 {f(tech.get("home", {}).get("cs_rate"), 0)}%　客队 {f(tech.get("away", {}).get("cs_rate"), 0)}%</div>
        <div class="b">主队近 {tech.get("home", {}).get("n", 0)} 场场均 {f(tech.get("home", {}).get("gf_avg"), 2)} 进
          {f(tech.get("home", {}).get("ga_avg"), 2)} 失，上半场进球占 {f(tech.get("home", {}).get("share_1h"), 0)}%；
          客队近 {tech.get("away", {}).get("n", 0)} 场场均 {f(tech.get("away", {}).get("gf_avg"), 2)} 进
          {f(tech.get("away", {}).get("ga_avg"), 2)} 失，上半场占 {f(tech.get("away", {}).get("share_1h"), 0)}%。
          交锋 {meet.get("n", 0)} 场场均 {f(meet.get("avg_total"), 2)} 球、平局 {f(meet.get("draw"), 0)}%、双方进球 {f(meet.get("btts"), 0)}%。</div></div>
      <div class="nd hl"><div class="tt">05 · 结论</div>
        <div class="h">{e(v["first"])} {f(v["first_p"])}% · 首选比分 {e(v["first_score"])}</div>
        <div class="b">次选 {e(v["second"])} {f(v["second_p"])}%（{e(v["second_score"])}），防范 {e(v["guard"])} {f(v["guard_p"])}%（{e(v["guard_score"])}）。</div></div>
      <div class="nd"><div class="tt">06 · 近期走形</div>
        <div class="h">主队近 {tech.get("home", {}).get("n", 0)} 场 / 客队近 {tech.get("away", {}).get("n", 0)} 场</div>
        <div class="b">{recent_rows(m, 3)}</div></div>
      <div class="nd"><div class="tt">07 · 让球另一套口径</div>
        <div class="h">让 {m["hand"]:+d} 之后，三格概率换了一副样子</div>
        <div class="b">{hand_rows(m)}</div></div>
      <div class="nd"><div class="tt">08 · 不建议主推的格子</div>
        <div class="h">模型自己标出来的降权与剔除</div>
        <div class="b">{flag_rows(m)}</div></div>
      <div class="nd"><div class="tt">09 · 交锋与形态</div>
        <div class="h">这对冤家 {meet.get("n", 0)} 场里，低比分（≤2 球）占 {f(meet.get("low2"), 0)}%</div>
        <div class="b">场均 {f(meet.get("avg_total"), 2)} 球、平局 {f(meet.get("draw"), 0)}%、双方进球 {f(meet.get("btts"), 0)}%。
          {"；".join(f'{e(d.get("d"))} {e(d.get("m"))}' for d in (meet.get("detail") or [])[:3])}。</div></div>
    </div>
    <div class="side">
      <div class="cb"><div class="t">信心</div>
        <div class="big">{f((m.get("conf") or {}).get("total"), 0)}<em>/100</em></div>
        <div class="row"><span>{e((m.get("conf") or {}).get("grade") or "")}</span><b>样本 {(m.get("conf") or {}).get("n_sample", 0)} 场</b></div></div>
      <div class="cb wdl"><div class="t">胜平负</div>{bars(m, ghost=False)}</div>
      <div class="cb"><div class="t">进球分布</div><div>{goal_chart(m, 44)}</div></div>
      <div class="cb"><div class="t">去掉平局后</div>{nodraw_bar(m)}</div>
      <div class="cb"><div class="t">双法修正</div>{dc_compare(m)}</div>
      <div class="cb"><div class="t">人员 · {len((m.get("intel") or {}).get("inj") or [])} 人</div>{inj_rows(m, 4)}</div>
      <div class="cb"><div class="t">比分</div>
        {"".join(f'<div class="row"><span>{t["s"]}</span><b>{f(t["p"])}%</b></div>' for t in (m.get("top") or [])[:5])}</div>
      <div class="cb"><div class="t">外部对照</div>{ext_block(m) or '<div class="none">本场没有可用外部源</div>'}</div>
    </div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料 · 第 {i} 页</span><span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 6 大字海报
def lay_poster(m, i) -> str:
    css = """
    .pg6{background:#0d0d0f;color:#f2efe9;padding:14mm 13mm 11mm;display:flex;flex-direction:column;}
    .pg6 .rule{height:1px;background:linear-gradient(90deg,#b8853c,rgba(184,133,60,.05));margin:3mm 0;}
    .pg6 .kh{display:flex;justify-content:space-between;font-size:9px;letter-spacing:4px;color:#b8853c;}
    .pg6 .mid{flex:1;display:flex;flex-direction:column;justify-content:center;}
    .pg6 .tn{font-size:52px;font-weight:800;line-height:1.02;letter-spacing:-2px;}
    .pg6 .tn:last-of-type{text-align:right;color:#b8853c;}
    .pg6 .vsm{display:flex;align-items:center;gap:5mm;margin:5mm 0;}
    .pg6 .vsm .ln{flex:1;height:1px;background:rgba(242,239,233,.16);}
    .pg6 .vsm s{font-size:11px;letter-spacing:6px;color:#8a857c;text-decoration:none;}
    .pg6 .band{display:flex;gap:0;border-top:1px solid rgba(242,239,233,.14);border-bottom:1px solid rgba(242,239,233,.14);}
    .pg6 .band div{flex:1;padding:4mm 3mm;border-right:1px solid rgba(242,239,233,.1);}
    .pg6 .band div:last-child{border-right:0;}
    .pg6 .band s{display:block;font-size:8px;letter-spacing:2px;color:#8a857c;text-decoration:none;margin-bottom:1mm;}
    .pg6 .band b{font-size:27px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1;}
    .pg6 .band u{display:block;font-size:9px;color:#b8853c;text-decoration:none;margin-top:1.5mm;}
    .pg6 .sc3{display:flex;gap:4mm;margin-top:5mm;}
    .pg6 .sc3 div{flex:1;border:1px solid rgba(184,133,60,.4);padding:3mm;text-align:center;}
    .pg6 .sc3 s{display:block;font-size:8px;letter-spacing:2px;color:#8a857c;text-decoration:none;margin-bottom:1.5mm;}
    .pg6 .sc3 b{font-size:24px;font-weight:800;font-variant-numeric:tabular-nums;}
    .pg6 .foot{margin-top:5mm;display:flex;justify-content:space-between;font-size:8px;letter-spacing:1px;color:#5f5c56;}
    .pg6 .xt{display:grid;grid-template-columns:1fr 1fr;gap:0 8mm;margin-top:6mm;}
    .pg6 .xt .t{font-size:8px;letter-spacing:2.5px;color:#b8853c;margin-bottom:2mm;
                border-bottom:1px solid rgba(242,239,233,.12);padding-bottom:1mm;}
    .pg6 .xt .ln2{display:flex;justify-content:space-between;font-size:9.5px;line-height:1.95;
                  border-bottom:1px dotted rgba(242,239,233,.1);font-variant-numeric:tabular-nums;}
    .pg6 .xt .ln2 b{color:#f2efe9;}
    .pg6 .xt .ln2 span{color:#8a857c;}
    """
    v = m["verdict"]
    conf = m.get("conf") or {}
    html = f"""
<section class="page pg6">
  <div class="kh"><span>{e(m["no"])} · {e(m["league"])}</span><span>全维度推演</span></div>
  <div class="rule"></div>
  <div class="mid">
    <div class="tn">{e(m["home"])}</div>
    <div class="vsm"><span class="ln"></span><s>V S</s><span class="ln"></span></div>
    <div class="tn">{e(m["away"])}</div>
    <div style="margin-top:6mm;font-size:10px;line-height:1.9;color:#b7b2a8;max-width:150mm">
      {e((m.get("steps") or {}).get("pattern") or "")}
    </div>
  </div>
  <div class="band">
    <div><s>主胜</s><b>{f(m["p"][0])}</b><u>定价 {f(m["mk"][0])}% · {sg(edge(m)[0])}</u></div>
    <div><s>平</s><b>{f(m["p"][1])}</b><u>定价 {f(m["mk"][1])}% · {sg(edge(m)[1])}</u></div>
    <div><s>客胜</s><b>{f(m["p"][2])}</b><u>定价 {f(m["mk"][2])}% · {sg(edge(m)[2])}</u></div>
  </div>
  <div class="sc3">
    <div><s>首选</s><b>{e(v["first_score"])}</b></div>
    <div><s>次选</s><b>{e(v["second_score"])}</b></div>
    <div><s>防范</s><b>{e(v["guard_score"])}</b></div>
  </div>
  <div class="xt">
    <div>
      <div class="t">阀门与让球</div>
      <div class="ln2"><span>大 2.5 / 3.5</span><b>{f(m["over"]["2.5"])}% / {f(m["over"]["3.5"])}%</b></div>
      <div class="ln2"><span>双方进球</span><b>{f(m["btts"])}%</b></div>
      <div class="ln2"><span>λ 合计</span><b>{f(m["lam"]["total"], 2)}</b></div>
      {"".join(f'<div class="ln2"><span>让 {m["hand"]:+d} · {d}</span><b class="{tone((m.get("h_edge") or [0,0,0])[k])}">{f((m.get("hp") or [0,0,0])[k])}% · {sg((m.get("h_edge") or [0,0,0])[k])}</b></div>' for k, d in enumerate(DIRS)) if m.get("hp") else '<div class="ln2"><span>让球</span><b>本场无固定奖金</b></div>'}
      <div class="ln2"><span>去掉平局（主 / 客）</span><b>{f((m.get("win_nodraw") or [0,0])[0])}% / {f((m.get("win_nodraw") or [0,0])[1])}%</b></div>
    </div>
    <div>
      <div class="t">技术面与双法</div>
      <div class="ln2"><span>场均进 主 / 客</span><b>{f((m.get("tech") or {}).get("home", {}).get("gf_avg"), 2)} / {f((m.get("tech") or {}).get("away", {}).get("gf_avg"), 2)}</b></div>
      <div class="ln2"><span>场均失 主 / 客</span><b>{f((m.get("tech") or {}).get("home", {}).get("ga_avg"), 2)} / {f((m.get("tech") or {}).get("away", {}).get("ga_avg"), 2)}</b></div>
      <div class="ln2"><span>零封率 主 / 客</span><b>{f((m.get("tech") or {}).get("home", {}).get("cs_rate"), 0)}% / {f((m.get("tech") or {}).get("away", {}).get("cs_rate"), 0)}%</b></div>
      {"".join(f'<div class="ln2"><span>{r["s"]} 泊松 → DC</span><b>{f(r["p_pois"])}% → {f(r["p_dc"])}%</b></div>' for r in (m.get("low_delta") or []))}
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;font-size:9.5px;color:#8a857c;margin-top:4mm">
    <span>λ {f(m["lam"]["fin"][0], 2)} + {f(m["lam"]["fin"][1], 2)} = {f(m["lam"]["total"], 2)}</span>
    <span>信心 {f(conf.get("total"), 0)} · {e(conf.get("grade") or "")}</span>
    <span>大2.5 {f(m["over"]["2.5"])}% · 双方进球 {f(m["btts"])}%</span>
  </div>
  <div class="foot"><span>阿飞 · 赛博聊球 · 内部资料 · 第 {i} 页</span><span>{e(m["kick"])} 开赛 · 仅统计 90 分钟</span></div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 7 账本表格
def lay_ledger(m, i) -> str:
    css = """
    .pg7{background:#fff;color:#14161a;padding:10mm 11mm 8mm;display:flex;flex-direction:column;
         font-family:"Cascadia Mono","Consolas","Microsoft YaHei",monospace;}
    .pg7 .th{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2px solid #14161a;padding-bottom:2mm;}
    .pg7 .th h1{font-size:19px;font-weight:700;letter-spacing:0;}
    .pg7 .th h1 s{text-decoration:none;color:#9aa0aa;margin:0 2mm;}
    .pg7 .th .r{font-size:9px;color:#6a7078;text-align:right;line-height:1.6;}
    .pg7 .th .r b{color:#14161a;}
    .pg7 table{width:100%;border-collapse:collapse;font-size:9.5px;margin-top:3mm;}
    .pg7 table td,.pg7 table th{padding:1.35mm 2mm;border-bottom:1px solid #e8eaee;vertical-align:top;
                                font-variant-numeric:tabular-nums;}
    .pg7 table th{background:#f3f4f6;font-size:8.5px;letter-spacing:1.5px;color:#6a7078;font-weight:600;text-align:left;}
    .pg7 table tr:nth-child(even) td{background:#fafbfc;}
    .pg7 table td.k{width:26mm;color:#6a7078;font-size:9px;}
    .pg7 table td.v{font-weight:700;}
    .pg7 .sub{display:grid;grid-template-columns:1fr 1fr;gap:0 6mm;margin-top:3mm;}
    .pg7 .sub table{margin-top:0;}
    .pg7 .verd{margin-top:auto;border:2px solid #14161a;padding:3mm;display:flex;align-items:center;gap:4mm;}
    .pg7 .verd .t{font-size:8px;letter-spacing:2px;color:#6a7078;}
    .pg7 .verd .m{font-size:10px;line-height:1.75;flex:1;}
    .pg7 .verd .sc{display:flex;gap:3mm;}
    .pg7 .verd .sc div{text-align:center;}
    .pg7 .verd .sc s{display:block;font-size:7.5px;color:#9aa0aa;text-decoration:none;}
    .pg7 .verd .sc b{font-size:16px;}
    .pg7 .ft{display:flex;justify-content:space-between;font-size:8px;color:#a4aab4;margin-top:2.5mm;}
    """
    v = m["verdict"]
    st = m.get("steps") or {}
    tech = m.get("tech") or {}
    meet = tech.get("meet") or {}
    conf = m.get("conf") or {}
    inj = (m.get("intel") or {}).get("inj") or []
    rows = "".join(
        f'<tr><td class="k">{"主胜" if k==0 else ("平" if k==1 else "客胜")}</td>'
        f'<td class="v">{f(m["p"][k])}%</td><td>{f(m["mk"][k])}%</td>'
        f'<td class="{tone(edge(m)[k])}">{sg(edge(m)[k])}pp</td>'
        f'<td>{f((m.get("odds") or [0,0,0])[k], 2)}</td></tr>' for k in range(3)
    )
    hs, as_ = tech.get("home", {}) or {}, tech.get("away", {}) or {}
    html = f"""
<section class="page pg7">
  <div class="th">
    <h1>{e(m["home"])}<s>vs</s>{e(m["away"])}</h1>
    <div class="r"><b>{e(m["no"])} · {e(m["league"])}</b><br>{e(m["kick"])} 开赛 · 让球 {m["hand"]:+d} · 第 {i} 页</div>
  </div>
  <table>
    <tr><th>项</th><th>模型</th><th>定价</th><th>偏差</th><th>固定奖金</th></tr>
    {rows}
    <tr><td class="k">λ 主 / 客</td><td class="v">{f(m["lam"]["fin"][0], 2)}</td><td class="v">{f(m["lam"]["fin"][1], 2)}</td>
        <td>合计 {f(m["lam"]["total"], 2)}</td><td>返还率 {f(m.get("payout"), 1)}%</td></tr>
    <tr><td class="k">大 2.5 / 3.5</td><td class="v">{f(m["over"]["2.5"])}%</td><td class="v">{f(m["over"]["3.5"])}%</td>
        <td>双方进球 {f(m["btts"])}%</td><td>大 1.5 {f(m["over"]["1.5"])}%</td></tr>
    <tr><td class="k">信心五维</td><td class="v">{f(conf.get("total"), 0)}</td>
        <td>{e(conf.get("grade") or "")}</td>
        <td>样本 {conf.get("n_sample", 0)} · 三方 {conf.get("agree", 0)}/3</td>
        <td>比分集中 {f(conf.get("top3"), 1)}%</td></tr>
    <tr><td class="k">冷门指数</td><td class="v">{f(m["cold"]["index"])}</td>
        <td>最热 {e(m["cold"]["fav"])} {f(m["cold"]["fav_mk"])}%</td>
        <td>模型给 {f(m["cold"]["fav_model"])}%</td>
        <td>次冷 {e(m["cold"]["main_cold"])} {f(m["cold"]["main_cold_p"])}%</td></tr>
  </table>
  <div class="sub">
    <table>
      <tr><th>比分 Top6</th><th>概率</th><th>定价</th><th>溢价</th></tr>
      {"".join(f'<tr><td class="k">{t["s"]}</td><td class="v">{f(t["p"])}%</td>'
               f'<td>{f(t.get("odd"), 2) if t.get("odd") else "—"}</td>'
               f'<td class="{"g" if (t.get("ev") or -1) >= 0 else "m"}">{sg(t.get("ev"), 2) if t.get("ev") is not None else "—"}</td></tr>'
               for t in (m.get("top") or [])[:6])}
    </table>
    <table>
      <tr><th>基本面</th><th>主队</th><th>客队</th><th>交锋</th></tr>
      <tr><td class="k">场均进</td><td class="v">{f(hs.get("gf_avg"), 2)}</td><td class="v">{f(as_.get("gf_avg"), 2)}</td>
          <td>{meet.get("n", 0)} 场</td></tr>
      <tr><td class="k">场均失</td><td class="v">{f(hs.get("ga_avg"), 2)}</td><td class="v">{f(as_.get("ga_avg"), 2)}</td>
          <td>均 {f(meet.get("avg_total"), 2)} 球</td></tr>
      <tr><td class="k">零封率</td><td class="v">{f(hs.get("cs_rate"), 0)}%</td><td class="v">{f(as_.get("cs_rate"), 0)}%</td>
          <td>平 {f(meet.get("draw"), 0)}%</td></tr>
      <tr><td class="k">上半场占比</td><td class="v">{f(hs.get("share_1h"), 0)}%</td><td class="v">{f(as_.get("share_1h"), 0)}%</td>
          <td>双方进球 {f(meet.get("btts"), 0)}%</td></tr>
      <tr><td class="k">样本场次</td><td>{hs.get("n", 0)}</td><td>{as_.get("n", 0)}</td>
          <td>低比分 {f(meet.get("low2"), 0)}%</td></tr>
    </table>
  </div>
  <div class="sub" style="margin-top:0">
    <table>
      <tr><th>让球 {m["hand"]:+d}</th><th>模型</th><th>定价</th><th>偏差</th></tr>
      {"".join(f'<tr><td class="k">{d}</td><td class="v">{f((m.get("hp") or [0,0,0])[k])}%</td>'
               f'<td>{f((m.get("hmk") or [0,0,0])[k])}%</td>'
               f'<td class="{tone((m.get("h_edge") or [0,0,0])[k])}">{sg((m.get("h_edge") or [0,0,0])[k])}</td></tr>'
               for k, d in enumerate(DIRS)) if m.get("hp") else
       '<tr><td class="k" colspan="4">本场无让球固定奖金</td></tr>'}
    </table>
    <table>
      <tr><th>双法对照</th><th>泊松</th><th>DC</th><th>修正</th></tr>
      {"".join(f'<tr><td class="k">{r["s"]}</td><td class="v">{f(r["p_pois"])}%</td><td>{f(r["p_dc"])}%</td>'
               f'<td class="{tone(r["p_dc"] - r["p_pois"])}">{sg(r["p_dc"] - r["p_pois"], 2)}</td></tr>'
               for r in (m.get("low_delta") or []))}
      <tr><td class="k">去平胜负</td><td class="v">{f((m.get("win_nodraw") or [0,0])[0])}%</td>
          <td>{f((m.get("win_nodraw") or [0,0])[1])}%</td><td>主 / 客</td></tr>
    </table>
  </div>
  <table style="margin-top:3mm">
    <tr><th>人员</th><th>队</th><th>位置</th><th>性质</th><th>出场</th></tr>
    {"".join(f'<tr><td class="k">{e(p["name"])}</td><td>{e(p["team"])}</td><td>{e(p["pos"])}</td>'
             f'<td>{e(p["kind"])}</td><td>{p["apps"]}</td></tr>' for p in inj[:6])
     or '<tr><td class="k" colspan="5">无伤停与停赛登记</td></tr>'}
  </table>
  <table style="margin-top:3mm">
    <tr><th>模型不建议主推的格子</th><th>类型</th><th>理由</th></tr>
    {"".join(f'<tr><td class="k">{e(r.get("k") or "")}</td><td>{e(r.get("kind") or "")}</td>'
             f'<td style="font-size:9px">{e(r.get("why") or "")}</td></tr>'
             for r in ((st.get("exclude") or []) + (st.get("rich") or []))[:4])
     or '<tr><td class="k" colspan="3">本场无需降权的格子</td></tr>'}
  </table>
  <div class="sub" style="margin-top:3mm">
    <table>
      <tr><th>近期走形 · 主队</th><th>日期</th><th>比分</th></tr>
      {"".join(f'<tr><td class="k">{e(r.get("m"))}</td><td>{e(r.get("d"))}</td><td>{e(r.get("ht") or "")}</td></tr>'
               for r in ((tech.get("home") or {}).get("results") or [])[:4])
       or '<tr><td class="k" colspan="3">无近期记录</td></tr>'}
    </table>
    <table>
      <tr><th>近期走形 · 客队</th><th>日期</th><th>比分</th></tr>
      {"".join(f'<tr><td class="k">{e(r.get("m"))}</td><td>{e(r.get("d"))}</td><td>{e(r.get("ht") or "")}</td></tr>'
               for r in ((tech.get("away") or {}).get("results") or [])[:4])
       or '<tr><td class="k" colspan="3">无近期记录</td></tr>'}
    </table>
  </div>
  <div class="verd">
    <div class="t">结论</div>
    <div class="m">{e(v["first"])} {f(v["first_p"])}% 为首选；次选 {e(v["second"])} {f(v["second_p"])}%；
      防范 {e(v["guard"])} {f(v["guard_p"])}%（{e(vg(v))}）。</div>
    <div class="sc"><div><s>首选</s><b>{e(v["first_score"])}</b></div>
      <div><s>次选</s><b>{e(v["second_score"])}</b></div>
      <div><s>防范</s><b>{e(v["guard_score"])}</b></div></div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料</span><span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 8 杂志跨页
def lay_magazine(m, i) -> str:
    css = """
    .pg8{background:#fff;color:#1c1b19;padding:0;display:flex;flex-direction:column;
         font-family:"Georgia","SimSun","Songti SC",serif;}
    .pg8 .hero{background:#1c1b19;color:#fff;padding:12mm 13mm 10mm;position:relative;}
    .pg8 .hero .k{font-size:8.5px;letter-spacing:4px;color:#c2a06a;}
    .pg8 .hero h1{font-size:33px;line-height:1.14;font-weight:400;margin-top:2.5mm;letter-spacing:-.5px;}
    .pg8 .hero h1 em{font-style:italic;color:#c2a06a;font-size:19px;margin:0 2mm;}
    .pg8 .hero .sub{font-size:10px;line-height:1.85;color:#b8b3aa;margin-top:3mm;max-width:150mm;}
    .pg8 .hero .pg{position:absolute;right:13mm;bottom:10mm;font-size:46px;color:rgba(255,255,255,.09);
                   font-weight:700;line-height:1;}
    .pg8 .body{flex:1;display:grid;grid-template-columns:1fr 56mm;min-height:0;}
    .pg8 .art{padding:7mm 6mm 8mm 13mm;display:block;}
    .pg8 .art .lede{font-size:13px;line-height:1.85;text-align:justify;}
    .pg8 .art .lede::first-letter{font-size:46px;font-weight:700;float:left;line-height:.82;padding:1.5mm 2mm 0 0;color:#1c1b19;}
    .pg8 .art .cols{column-count:2;column-gap:6mm;column-fill:auto;font-size:10px;line-height:1.9;text-align:justify;
                    margin-top:3mm;color:#3a3936;}
    .pg8 .art .pull{margin:3mm 0;border-top:1px solid #1c1b19;border-bottom:1px solid #1c1b19;
                    padding:2.5mm 0;font-size:13px;line-height:1.6;color:#1c1b19;font-style:italic;}
    .pg8 .rail{background:#f4f2ed;padding:9mm 6mm;display:flex;flex-direction:column;gap:3mm;
               border-left:1px solid #e4e0d6;font-family:"Microsoft YaHei",sans-serif;}
    .pg8 .rail .t{font-size:8px;letter-spacing:2.5px;color:#a09a8c;margin-bottom:1mm;}
    .pg8 .rail .big{font-size:23px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;}
    .pg8 .rail .big em{font-size:9px;font-style:normal;color:#a09a8c;font-weight:400;}
    .pg8 .rail .row{display:flex;justify-content:space-between;font-size:9.5px;
                    border-bottom:1px dotted #ded9cc;padding:1.2px 0;font-variant-numeric:tabular-nums;}
    .pg8 .rail .row b{font-weight:700;}
    .pg8 .wdl{color:#1c1b19;}
    /* 窄侧栏（44mm 内宽）放不下标准概率条的四列固定宽度，收窄成三列：
       定价那列在右边「阀门」块里已经单列过，这里省掉不丢信息。 */
    .pg8 .wdl .bl{width:22px;font-size:9.5px;}
    .pg8 .wdl .bv{width:34px;font-size:10.5px;}
    .pg8 .wdl .bd{width:34px;font-size:9px;}
    .pg8 .wdl .bm{display:none;}
    .pg8 .ft{background:#1c1b19;color:#8a857c;padding:2mm 13mm;display:flex;justify-content:space-between;font-size:8px;}
    .pg8 .art .sec{margin-top:3.5mm;}
    .pg8 .art .t2{font-size:8px;letter-spacing:2.5px;color:#a09a8c;margin-bottom:1.5mm;
                  border-bottom:1px solid #e4e0d6;padding-bottom:1mm;}
    .pg8 .art .rc span{color:#8b8a84;}
    .pg8 .art .hrow span{color:#6b675e;}
    .pg8 .art .hrow.hh{border-bottom-color:#e4e0d6;}
    .pg8 .art .two2{display:grid;grid-template-columns:1fr 1fr;gap:0 6mm;}
    .pg8 .art .two2 .row{display:flex;justify-content:space-between;font-size:9px;line-height:1.75;
                         border-bottom:1px dotted #e4e0d6;font-variant-numeric:tabular-nums;}
    .pg8 .art .two2 .row b{font-weight:700;}
    """
    v = m["verdict"]
    st = m.get("steps") or {}
    tech = m.get("tech") or {}
    meet = tech.get("meet") or {}
    conf = m.get("conf") or {}
    html = f"""
<section class="page pg8">
  <div class="hero">
    <div class="k">{e(m["no"])} · {e(m["league"])} · {e(m["kick"])}</div>
    <h1>{e(m["home"])}<em>v</em><br>{e(m["away"])}</h1>
    <div class="sub">{e(st.get("total") or "")}</div>
    <div class="pg">{i:02d}</div>
  </div>
  <div class="body">
    <div class="art">
      <div class="lede">{e(st.get("pattern") or "")}</div>
      <div class="pull">首选 <b>{e(v["first"])}</b> {f(v["first_p"])}%，
        比分落在 <b>{e(v["first_score"])}</b>；次选 {e(v["second"])} {f(v["second_p"])}%，
        若风向反过来，最可能的退路是 {e(v["guard"])}（{e(v["guard_score"])}）。</div>
      <div class="cols">{e(st.get("matrix") or "")}
        主队近 {tech.get("home", {}).get("n", 0)} 场场均 {f(tech.get("home", {}).get("gf_avg"), 2)} 进
        {f(tech.get("home", {}).get("ga_avg"), 2)} 失，零封率 {f(tech.get("home", {}).get("cs_rate"), 0)}%，
        上半场进球占 {f(tech.get("home", {}).get("share_1h"), 0)}%。
        客队近 {tech.get("away", {}).get("n", 0)} 场场均 {f(tech.get("away", {}).get("gf_avg"), 2)} 进
        {f(tech.get("away", {}).get("ga_avg"), 2)} 失，零封率 {f(tech.get("away", {}).get("cs_rate"), 0)}%。
        两队交锋 {meet.get("n", 0)} 场，场均 {f(meet.get("avg_total"), 2)} 球，
        低比分（≤2 球）占 {f(meet.get("low2"), 0)}%，平局 {f(meet.get("draw"), 0)}%。</div>
      <div class="sec" style="margin-top:3mm">
        <div class="t2">让球 {m["hand"]:+d} 另一套口径</div>{hand_rows(m)}</div>
      <div class="sec">
        <div class="t2">双法修正</div>{dc_compare(m)}</div>
      <div class="sec">
        <div class="t2">近期走形</div>{recent_rows(m, 4)}</div>
      <div class="sec" style="margin-bottom:0">
        <div class="t2">模型不建议主推的格子</div>{flag_rows(m)}</div>
      <div class="sec">
        <div class="t2">交锋 {meet.get("n", 0)} 场与伤停</div>
        <div class="two2">
          <div>
            <div class="row"><span>场均总进球</span><b>{f(meet.get("avg_total"), 2)}</b></div>
            <div class="row"><span>≤2 球占比</span><b>{f(meet.get("low2"), 0)}%</b></div>
            <div class="row"><span>平局占比</span><b>{f(meet.get("draw"), 0)}%</b></div>
            <div class="row"><span>双方进球占比</span><b>{f(meet.get("btts"), 0)}%</b></div>
            {"".join(f'<div class="row"><span>{e(d.get("d"))}</span><span>{e(d.get("m"))}</span></div>' for d in (meet.get("detail") or [])[:3])}
          </div>
          <div>{inj_rows(m, 6)}</div>
        </div>
      </div>
    </div>
    <div class="rail">
      <div><div class="t">信心指数</div><div class="big">{f(conf.get("total"), 0)}<em> / 100</em></div>
        <div class="row"><span>{e(conf.get("grade") or "")}</span><b>{sg(maxpp(m))}pp</b></div></div>
      <div class="wdl"><div class="t">胜平负</div>{bars(m, ghost=False)}</div>
      <div><div class="t">阀门</div>
        <div class="row"><span>大 2.5</span><b>{f(m["over"]["2.5"])}%</b></div>
        <div class="row"><span>双方进球</span><b>{f(m["btts"])}%</b></div>
        <div class="row"><span>λ 合计</span><b>{f(m["lam"]["total"], 2)}</b></div>
        <div class="row"><span>冷门指数</span><b>{f(m["cold"]["index"])}</b></div>
        <div class="row"><span>去掉平局</span><b>主 {f((m.get("win_nodraw") or [0, 0])[0])}%</b></div></div>
      <div><div class="t">进球分布</div><div>{goal_chart(m, 42)}</div></div>
      <div><div class="t">比分 Top4</div>
        {"".join(f'<div class="row"><span>{t["s"]}</span><b>{f(t["p"])}%</b></div>' for t in (m.get("top") or [])[:4])}</div>
      <div><div class="t">人员 · {len((m.get("intel") or {}).get("inj") or [])} 人</div>{inj_rows(m, 4)}</div>
      <div><div class="t">外部对照</div>{ext_block(m) or '<div class="none">本场没有可用外部源</div>'}</div>
    </div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料</span><span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 9 数据终端
def lay_terminal(m, i) -> str:
    css = """
    .pg9{background:#07100c;color:#8ef0b6;padding:10mm 11mm 8mm;display:flex;flex-direction:column;
         font-family:"Cascadia Mono","Consolas","Microsoft YaHei",monospace;font-size:10px;}
    .pg9 .bar{display:flex;justify-content:space-between;font-size:8.5px;color:#3f6b53;
              border-bottom:1px solid #1c3a2a;padding-bottom:2mm;letter-spacing:1px;}
    .pg9 .h1{font-size:15px;font-weight:700;color:#d2ffe6;margin:3mm 0 1mm;letter-spacing:.5px;}
    .pg9 .h1 s{color:#4f8b6c;text-decoration:none;margin:0 2mm;}
    .pg9 .p{color:#4f8b6c;}
    .pg9 .body{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:5mm;margin-top:3mm;min-height:0;}
    .pg9 .body>div{display:flex;flex-direction:column;min-height:0;}
    .pg9 .blk{margin-bottom:3mm;}
    .pg9 .blk .t{color:#3f6b53;font-size:8.5px;letter-spacing:1.5px;margin-bottom:1mm;}
    .pg9 .ln{display:flex;justify-content:space-between;border-bottom:1px dotted #17372a;
             padding:1.1px 0;font-variant-numeric:tabular-nums;line-height:1.75;}
    .pg9 .ln b{color:#d2ffe6;font-weight:600;}
    .pg9 .kv{color:#8ef0b6;}
    .pg9 .r{color:#ff8f8f;} .pg9 .g{color:#8ef0b6;} .pg9 .a{color:#ffd28f;}
    .pg9 .bar2{color:#2f8f5f;}
    .pg9 .ascii{color:#2f8f5f;font-size:9px;letter-spacing:1px;margin:2mm 0;}
    .pg9 .verd{border:1px solid #2f8f5f;padding:2.5mm;margin-top:auto;background:rgba(47,143,95,.07);}
    .pg9 .verd .t{color:#4f8b6c;font-size:8.5px;letter-spacing:2px;margin-bottom:1.5mm;}
    .pg9 .verd .m{color:#d2ffe6;font-size:10px;line-height:1.85;}
    .pg9 .ft{display:flex;justify-content:space-between;font-size:8px;color:#2b5541;margin-top:3mm;}
    .pg9 .wdl{color:#8ef0b6;}
    .pg9 .wdl .bt{background:#12251c;}
    .pg9 .wdl .bg2{background:#d2ffe6;}
    .pg9 .hrow span,.pg9 .hrow.hh{color:#4f8b6c;}
    .pg9 .hrow.hh{border-bottom-color:#17372a;}
    .pg9 .dcr span,.pg9 .dcr s,.pg9 .dch{color:#3f6b53;}
    .pg9 .dcr em{color:#d2ffe6;}
    .pg9 .fl b{background:#12251c;color:#8ef0b6;}
    .pg9 .fl b.a{background:#2a2412;color:#ffd28f;}
    .pg9 .fl b.r{background:#2a1616;color:#ff8f8f;}
    .pg9 .fl span{color:#d2ffe6;}
    .pg9 .fl em{color:#4f8b6c;}
    .pg9 .none{color:#3f6b53;}
    """
    v = m["verdict"]
    st = m.get("steps") or {}
    conf = m.get("conf") or {}
    tech = m.get("tech") or {}
    meet = tech.get("meet") or {}
    html = f"""
<section class="page pg9">
  <div class="bar"><span>AFEI·TERMINAL — MATCH DUMP</span><span>{e(m["no"])} / {e(m["league"])} / {e(m["kick"])} / PAGE {i:02d}</span></div>
  <div class="h1"><span class="p">&gt;</span> {e(m["home"])}<s>vs</s>{e(m["away"])}</div>
  <div style="color:#4f8b6c;font-size:9px">让球 {m["hand"]:+d} · 返还率 {f(m.get("payout"), 1)}% · 抽样 {pc.SAMPLES:,} · rho {f(pc.RHO, 2)}</div>
  <div class="ascii">────────────────────────────────────────────────────────────</div>
  <div class="body">
    <div>
      <div class="blk"><div class="t">[ 胜平负 / model · price · edge ]</div>{bars(m)}</div>
      <div class="blk"><div class="t">[ lambda ]</div>
        <div class="ln"><span>L1 actual</span><b>{f((m["lam"].get("l1") or [0,0])[0], 2)} + {f((m["lam"].get("l1") or [0,0])[1], 2)}</b></div>
        <div class="ln"><span>L2 implied</span><b>{f((m["lam"].get("l2") or [0,0])[0], 2)} + {f((m["lam"].get("l2") or [0,0])[1], 2)}</b></div>
        <div class="ln"><span>L_final</span><b>{f(m["lam"]["fin"][0], 2)} + {f(m["lam"]["fin"][1], 2)} = {f(m["lam"]["total"], 2)}</b></div></div>
      <div class="blk"><div class="t">[ goals distribution ]</div><div>{goal_chart(m, 48)}</div>
        <div class="ln"><span>O2.5 / O3.5 / BTTS</span><b>{f(m["over"]["2.5"])}% / {f(m["over"]["3.5"])}% / {f(m["btts"])}%</b></div></div>
      <div class="blk"><div class="t">[ score grid top6 ]</div>{score_rows(m, 6)}</div>
      <div class="blk"><div class="t">[ handicap / model · price · edge ]</div>{hand_rows(m)}</div>
      <div class="blk"><div class="t">[ poisson vs dixon-coles ]</div>{dc_compare(m)}</div>
      <div class="blk"><div class="t">[ recent form — home / away ]</div>{recent_rows(m, 4)}</div>
      <div class="blk"><div class="t">[ external ]</div>{ext_block(m) or '<div style="color:#4f8b6c">无可用外部源</div>'}</div>
    </div>
    <div>
      <div class="blk"><div class="t">[ confidence ]</div>
        <div class="ln"><span>total</span><b>{f(conf.get("total"), 0)} / 100</b></div>
        <div class="ln"><span>grade</span><b>{e(conf.get("grade") or "")}</b></div>
        <div class="ln"><span>weights w1..w5</span><b>{f(conf.get("w1"), 0)} {f(conf.get("w2"), 0)} {f(conf.get("w3"), 0)} {f(conf.get("w4"), 0)} {f(conf.get("w5"), 0)}</b></div>
        <div class="ln"><span>sample / agree</span><b>{conf.get("n_sample", 0)} 场 / {conf.get("agree", 0)} of 3</b></div>
        <div class="ln"><span>max edge</span><b class="{tone(maxpp(m))}">{sg(maxpp(m))}pp</b></div></div>
      <div class="blk"><div class="t">[ form / home · away ]</div>
        <div class="ln"><span>GF avg</span><b>{f(tech.get("home", {}).get("gf_avg"), 2)} · {f(tech.get("away", {}).get("gf_avg"), 2)}</b></div>
        <div class="ln"><span>GA avg</span><b>{f(tech.get("home", {}).get("ga_avg"), 2)} · {f(tech.get("away", {}).get("ga_avg"), 2)}</b></div>
        <div class="ln"><span>clean sheet</span><b>{f(tech.get("home", {}).get("cs_rate"), 0)}% · {f(tech.get("away", {}).get("cs_rate"), 0)}%</b></div>
        <div class="ln"><span>1H share</span><b>{f(tech.get("home", {}).get("share_1h"), 0)}% · {f(tech.get("away", {}).get("share_1h"), 0)}%</b></div>
        <div class="ln"><span>sample n</span><b>{tech.get("home", {}).get("n", 0)} · {tech.get("away", {}).get("n", 0)}</b></div></div>
      <div class="blk"><div class="t">[ h2h ]</div>
        <div class="ln"><span>matches</span><b>{meet.get("n", 0)}</b></div>
        <div class="ln"><span>avg total / draw / btts</span><b>{f(meet.get("avg_total"), 2)} / {f(meet.get("draw"), 0)}% / {f(meet.get("btts"), 0)}%</b></div>
        <div class="ln"><span>low score &lt;=2</span><b>{f(meet.get("low2"), 0)}%</b></div></div>
      <div class="blk"><div class="t">[ unavailable ]</div>
        <div style="color:#4f8b6c;line-height:1.85">xG / xGA / npxG / PPDA / set-piece xG / referee leniency — 无数据源，留空不估。</div></div>
      <div class="blk"><div class="t">[ downgrade flags ]</div>{flag_rows(m)}</div>
      <div class="verd"><div class="t">&gt;&gt; VERDICT</div>
        <div class="m">[{e(v["first"])} {f(v["first_p"])}%] primary → {e(v["first_score"])}<br>
          [{e(v["second"])} {f(v["second_p"])}%] secondary → {e(v["second_score"])}<br>
          [{e(v["guard"])} {f(v["guard_p"])}%] guard → {e(v["guard_score"])}</div></div>
    </div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料</span><span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 10 六维对比
def lay_radar(m, i) -> str:
    css = """
    .pg10{background:#fff;color:#1a1c22;padding:11mm 12mm 9mm;display:flex;flex-direction:column;}
    .pg10 .hd{display:flex;justify-content:space-between;align-items:flex-end;
              background:#1a1c22;color:#fff;margin:-11mm -12mm 0;padding:9mm 12mm 6mm;}
    .pg10 .hd .l .k{font-size:8.5px;letter-spacing:3px;color:#8f97a6;}
    .pg10 .hd .l h1{font-size:25px;font-weight:700;margin-top:1.5mm;line-height:1.2;}
    .pg10 .hd .l h1 s{text-decoration:none;color:#8f97a6;font-size:15px;margin:0 2mm;font-weight:400;}
    .pg10 .hd .r{text-align:right;font-size:9.5px;color:#b8bfcc;line-height:1.7;}
    .pg10 .hd .r b{color:#fff;font-size:11px;}
    .pg10 .body{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:6mm;margin-top:5mm;min-height:0;}
    .pg10 .rdw{display:flex;flex-direction:column;align-items:center;}
    .pg10 .rdw .cap{font-size:8.5px;letter-spacing:2px;color:#8f97a6;margin-bottom:1mm;align-self:flex-start;}
    .pg10 .rd{color:#2f5fa8;}
    .pg10 .legend{display:flex;gap:4mm;font-size:9px;color:#6b7280;margin-top:1mm;}
    .pg10 .legend s{display:inline-block;width:11px;height:8px;text-decoration:none;margin-right:3px;vertical-align:middle;}
    .pg10 .legend s.m{background:rgba(47,95,168,.28);border:1px solid #2f5fa8;}
    .pg10 .legend s.k{background:none;border:1px dashed #c9322b;}
    .pg10 .side{display:flex;flex-direction:column;gap:2mm;}
    .pg10 .blk{border:1px solid #e4e7ec;border-radius:2mm;padding:2.4mm;}
    .pg10 .blk .t{font-size:8.5px;letter-spacing:2px;color:#8f97a6;margin-bottom:2mm;}
    .pg10 .trio{display:grid;grid-template-columns:repeat(3,1fr);gap:1mm;text-align:center;}
    .pg10 .trio s{display:block;font-size:8px;color:#8f97a6;text-decoration:none;}
    .pg10 .trio b{font-size:19px;font-weight:700;font-variant-numeric:tabular-nums;}
    .pg10 .trio u{display:block;font-size:9px;text-decoration:none;}
    .pg10 .wdl{color:#1a1c22;}
    .pg10 .verd{margin-top:auto;background:#1a1c22;color:#fff;border-radius:2mm;padding:3.5mm;}
    .pg10 .verd .t{font-size:8px;letter-spacing:2px;color:#8f97a6;margin-bottom:1.5mm;}
    .pg10 .verd .sc{display:flex;gap:2mm;margin-top:2.5mm;}
    .pg10 .verd .sc div{flex:1;background:#2b2f38;border-radius:1.5mm;padding:2mm;text-align:center;}
    .pg10 .verd .sc s{display:block;font-size:7.5px;color:#8f97a6;text-decoration:none;}
    .pg10 .verd .sc b{font-size:15px;font-variant-numeric:tabular-nums;}
    .pg10 .ft{display:flex;justify-content:space-between;font-size:8px;color:#a4aab4;margin-top:3mm;}
    """
    v = m["verdict"]
    conf = m.get("conf") or {}
    html = f"""
<section class="page pg10">
  <div class="hd">
    <div class="l"><div class="k">{e(m["no"])} · {e(m["league"])} · 让球 {m["hand"]:+d}</div>
      <h1>{e(m["home"])}<s>vs</s>{e(m["away"])}</h1></div>
    <div class="r"><b>{e(m["kick"])}</b><br>信心 {f(conf.get("total"), 0)} · {e(conf.get("grade") or "")}<br>第 {i} 页</div>
  </div>
  <div class="body">
    <div class="rdw">
      <div class="cap">六维对照 · 实心＝模型 · 虚线＝定价</div>
      {radar_svg(m, 300)}
      <div class="legend"><span><s class="m"></s>模型</span><span><s class="k"></s>定价</span></div>
      <div style="font-size:9.5px;line-height:1.9;color:#4b5563;margin-top:3mm;align-self:flex-start">
        六个维度里偏差最深的一格是
        <b class="{tone(maxpp(m))}">{e(DIRS[max(range(3), key=lambda k: abs(edge(m)[k]))])}</b>
        的 {sg(maxpp(m))}pp。比值越靠近圆心说明越靠近均线，两个多边形重合度越高，
        这一场的可读性就越强；多边形被拉开的地方，就是本场全部的分歧来源。
      </div>
      <div style="align-self:stretch;margin-top:4mm">
        <div class="t" style="font-size:8.5px;letter-spacing:2px;color:#8f97a6;margin-bottom:1.5mm">技术面 · 主客对照</div>
        {tech_pair(m)}
        <div class="t" style="font-size:8.5px;letter-spacing:2px;color:#8f97a6;margin:3mm 0 1.5mm">近期走形</div>
        {recent_rows(m, 3)}
      </div>
    </div>
    <div class="side">
      <div class="blk"><div class="t">三向概率</div>
        <div class="trio">
          <div><s>主胜</s><b>{f(m["p"][0])}</b><u class="{tone(edge(m)[0])}">{sg(edge(m)[0])}</u></div>
          <div><s>平</s><b>{f(m["p"][1])}</b><u class="{tone(edge(m)[1])}">{sg(edge(m)[1])}</u></div>
          <div><s>客胜</s><b>{f(m["p"][2])}</b><u class="{tone(edge(m)[2])}">{sg(edge(m)[2])}</u></div>
        </div></div>
      <div class="blk wdl"><div class="t">与定价的距离</div>{bars(m)}</div>
      <div class="blk"><div class="t">五维信心拆分</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1mm 6mm;font-size:9.5px">
          <div style="display:flex;justify-content:space-between"><span>样本厚度</span><b>{f(conf.get("w1"), 0)}/20</b></div>
          <div style="display:flex;justify-content:space-between"><span>双法收敛</span><b>{f(conf.get("w2"), 0)}/20</b></div>
          <div style="display:flex;justify-content:space-between"><span>三方一致</span><b>{f(conf.get("w3"), 0)}/25</b></div>
          <div style="display:flex;justify-content:space-between"><span>分歧可控</span><b>{f(conf.get("w4"), 0)}/25</b></div>
          <div style="display:flex;justify-content:space-between"><span>比分集中</span><b>{f(conf.get("w5"), 0)}/10</b></div>
          <div style="display:flex;justify-content:space-between"><span>三方同向</span><b>{conf.get("agree", 0)}/3</b></div>
        </div></div>
      <div class="blk"><div class="t">比分 Top4</div>{score_rows(m, 3)}</div>
      <div class="blk"><div class="t">让球 {m["hand"]:+d} · 模型 / 定价 / 偏差</div>{hand_rows(m)}</div>
      <div class="blk"><div class="t">泊松 vs Dixon-Coles</div>{dc_compare(m)}</div>
      <div class="blk"><div class="t">人员 · {len((m.get("intel") or {}).get("inj") or [])} 人</div>{inj_rows(m, 2)}</div>
      <div class="blk"><div class="t">降权与剔除</div>{flag_rows(m)}</div>
      <div class="verd"><div class="t">结论</div>
        <div style="font-size:10.5px;line-height:1.8">{e(v["first"])} {f(v["first_p"])}% 首选，
          次选 {e(v["second"])} {f(v["second_p"])}%，防范 {e(v["guard"])} {f(v["guard_p"])}%。</div>
        <div class="sc"><div><s>首选</s><b>{e(v["first_score"])}</b></div>
          <div><s>次选</s><b>{e(v["second_score"])}</b></div>
          <div><s>防范</s><b>{e(v["guard_score"])}</b></div></div></div>
    </div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料</span><span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 0 综合研判（每期统一模板）
def lay_dossier(m, i) -> tuple:
    """每期固定用这一套：盘口解读 → 数据底稿 → 战术走向 → 技术人员 →
    媒体与 AI 对照 → 影响因素清单 → 总结分析。字体按 A4 阅读距离放大到 11.5px 起。"""
    css = """
    .dz{background:#fff;color:#1a1d23;padding:7mm 10mm 5mm;display:flex;flex-direction:column;
        font-size:10.5px;line-height:1.6;}
    .dz .hd{display:flex;justify-content:space-between;align-items:flex-end;
            border-bottom:2.5px solid #1a1d23;padding-bottom:2mm;}
    .dz .hd .l{display:flex;align-items:baseline;gap:3mm;}
    .dz .hd .no{font-size:34px;font-weight:800;line-height:.9;letter-spacing:-1px;font-variant-numeric:tabular-nums;}
    .dz .hd .lg{font-size:11px;color:#5b6472;}
    .dz .hd .r{font-size:10.5px;color:#5b6472;text-align:right;line-height:1.55;}
    .dz .tn{display:flex;align-items:center;gap:4mm;margin-top:2mm;}
    .dz .tn b{font-size:24px;font-weight:800;letter-spacing:-.5px;}
    .dz .tn b.aw{margin-left:auto;text-align:right;}
    .dz .tn s{font-size:12px;color:#9aa3b0;text-decoration:none;letter-spacing:3px;flex:none;}
    .dz .meta{display:flex;gap:5mm;margin-top:2mm;font-size:10.5px;color:#5b6472;}
    .dz .meta i{font-style:normal;color:#1a1d23;font-weight:700;font-variant-numeric:tabular-nums;}
    .dz .band{display:grid;gap:4mm;margin-top:2mm;}
    .dz .band.a{grid-template-columns:1.62fr 1fr 1fr;}
    .dz .band.b{grid-template-columns:1fr 1fr;}
    .dz .band.c{grid-template-columns:1fr 1fr 1fr;}
    .dz .band.e{grid-template-columns:1fr;}
    .dz .bk{border-top:1.5px solid #1a1d23;padding-top:1.5mm;min-width:0;}
    .dz h3{font-size:11.5px;font-weight:800;letter-spacing:1.2px;color:#1a1d23;margin-bottom:1.2mm;}
    .dz h3 em{font-style:normal;font-weight:400;font-size:9.5px;color:#8b93a0;letter-spacing:0;margin-left:1.5mm;}
    .dz p{margin-bottom:1.1mm;text-align:justify;color:#2a2f38;}
    .dz p:last-child{margin-bottom:0;}
    .dz .two{column-count:2;column-gap:5mm;}
    .dz .two p{margin-bottom:1.2mm;break-inside:avoid;}
    .dz .kv{display:flex;flex-direction:column;gap:.6mm;font-variant-numeric:tabular-nums;}
    .dz .kv .r{display:flex;justify-content:space-between;font-size:10.5px;
              border-bottom:1px dotted #e4e7ec;padding:.2mm 0;}
    .dz .kv .r b{font-weight:700;}
    .dz .big{font-size:32px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;}
    .dz .big em{font-size:11px;font-style:normal;color:#8b93a0;font-weight:400;}
    .dz .dims{display:grid;grid-template-columns:1fr 1fr;gap:0 3mm;font-size:9.5px;color:#6b7280;}
    .dz .dims .d{display:flex;align-items:center;gap:2mm;}
    .dz .dims .d i{height:4px;background:#1a1d23;border-radius:1px;display:inline-block;}
    .dz .dims .d b{margin-left:auto;font-variant-numeric:tabular-nums;}
    /* 放大版通用小组件：所有 helper 的固定像素宽在这里统一放宽 */
    .dz .bl{width:38px;font-size:11.5px;}
    .dz .bt{height:14px;}
    .dz .bv{width:48px;font-size:13.5px;}
    .dz .bd{width:42px;font-size:12px;}
    .dz .bm{width:52px;font-size:9.5px;white-space:nowrap;overflow:hidden;}
    .dz .gc b{font-size:9.5px;} .dz .gc s{font-size:9px;}
    .dz .sr{font-size:12px;line-height:1.75;} .dz .sr b{width:34px;} .dz .sr span{height:8px;}
    .dz .sr em{width:48px;} .dz .sr s{width:42px;} .dz .sr u{width:48px;font-size:11px;}
    .dz .ij{font-size:11.5px;} .dz .ij b{width:17px;height:17px;font-size:9.5px;}
    .dz .ij em,.dz .ij s,.dz .ij u{font-size:10.5px;}
    .dz .hrow{font-size:11.5px;} .dz .hrow span{width:46px;} .dz .hrow.hh{font-size:10px;}
    .dz .dcr{font-size:11.5px;} .dz .dcr b{width:32px;} .dz .dcr u{width:52px;}
    .dz .dch{font-size:10.5px;}
    .dz .tp{font-size:11.5px;} .dz .tp b{width:52px;} .dz .tp.tp-h{font-size:10px;}
    .dz .fl{font-size:10.5px;} .dz .fl b{font-size:9.5px;}
    .dz .none{font-size:10.5px;}
    /* 媒体与 AI 三方对照（窄栏两列行，不做三列表格） */
    .dz .mcr{display:flex;gap:2mm;font-size:10.5px;line-height:1.7;
             border-bottom:1px dotted #e4e7ec;padding:.6mm 0;}
    .dz .mcr span{width:26mm;flex:none;color:#3f4650;}
    .dz .mcr b{flex:1;font-weight:600;text-align:right;min-width:0;}
    .dz .mcr b i{font-style:normal;font-weight:400;color:#8b93a0;font-size:9.5px;}
    .dz .mc-n{font-size:10px;line-height:1.65;color:#4a5261;margin-top:1.2mm;text-align:justify;}
    /* 影响因素清单：两栏排，避免一列 15 行拖长 */
    .dz .fxh{font-size:10px;color:#8b93a0;margin-bottom:1.2mm;}
    .dz .fxwrap{column-count:2;column-gap:4mm;}
    .dz .fx{display:flex;gap:1.5mm;font-size:10.5px;line-height:1.6;
            border-bottom:1px dotted #eceff3;padding:.5mm 0;break-inside:avoid;}
    .dz .fx span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#3f4650;}
    .dz .fx b{width:8mm;flex:none;font-weight:700;font-size:9.5px;}
    .dz .fx b.ok{color:#0f8a5f;} .dz .fx b.no{color:#b0b6bf;}
    .dz .fx em{display:none;}
    /* 总结 */
    .dz .dsum{column-count:2;column-gap:7mm;}
    .dz .dsum p{font-size:10.5px;line-height:1.66;margin-bottom:1.4mm;break-inside:avoid;}
    .dz .sc3{display:flex;gap:2mm;margin-top:1.6mm;}
    .dz .sc3 div{flex:1;border:1.5px solid #1a1d23;padding:1mm 2mm;text-align:center;}
    .dz .sc3 s{display:block;font-size:9px;color:#8b93a0;text-decoration:none;margin-bottom:.3mm;}
    .dz .sc3 b{font-size:16px;font-weight:800;font-variant-numeric:tabular-nums;}
    .dz .ft{display:flex;justify-content:space-between;font-size:9px;color:#a4aab4;
            margin-top:auto;padding-top:2mm;border-top:1px solid #e4e7ec;}
    """
    v = m.get("verdict") or {}
    conf = m.get("conf") or {}
    lam = m.get("lam") or {}
    over = m.get("over") or {}
    cold = m.get("cold") or {}
    tech = m.get("tech") or {}
    w = conf.get("w1"), conf.get("w2"), conf.get("w3"), conf.get("w4"), conf.get("w5")
    dims = "".join(
        f'<div class="d"><span>{lab}</span><i style="width:{max(1, round(8 * (val or 0) / 25))}mm"></i>'
        f'<b>{val or 0}</b></div>'
        for lab, val in zip(("样本厚度", "双法收敛", "三方一致", "分歧可控", "比分集中"), w)
    )
    scorers = (m.get("scorers") or [])[:3]
    sc_html = "".join(
        f'<div class="ij"><b class="s{ "主" if s["team"] == m["home"] else "客"}">'
        f'{ "主" if s["team"] == m["home"] else "客"}</b><span>{e(s["name"])}</span>'
        f'<em>{e(s["team"])}</em><s>{s["goal"]} 球</s><u>{s["assist"]} 助</u></div>'
        for s in scorers
    ) or '<div class="none">球员榜本期无进球/助攻记录</div>'

    html = f"""
<section class="page dz">
  <div class="hd">
    <div class="l"><div class="no">{e(m["no"][2:])}</div>
      <div class="lg">{e(m["league"])} · {_hand_word(m["hand"])}</div></div>
    <div class="r">{e(m["kick"])} 开赛 · 第 {i} 页<br>
      返还率 {f(m.get("payout"), 1)}% · λ 合计 {f(lam.get("total"), 2)}</div>
  </div>
  <div class="tn"><b>{e(m["home"])}</b><s>VS</s><b class="aw">{e(m["away"])}</b></div>
  <div class="meta"><span>模型首选 <i>{e(v.get("first"))}</i> {f(v.get("first_p"))}%</span>
    <span>首选比分 <i>{e(v.get("first_score"))}</i></span>
    <span>信心 <i>{f(conf.get("total"), 0)}</i>/100</span>
    <span>冷门指数 <i>{f(cold.get("index"))}</i></span></div>

  <div class="band a">
    <div class="bk"><h3>胜平负 · 模型实心 / 定价竖线</h3>{bars(m)}</div>
    <div class="bk"><h3>开赛条件<em>大小球与抽水</em></h3>
      <div class="kv">
        <div class="r"><span>大 2.5 球</span><b>{f(over.get("2.5"))}%</b></div>
        <div class="r"><span>大 3.5 球</span><b>{f(over.get("3.5"))}%</b></div>
        <div class="r"><span>双方进球</span><b>{f(m.get("btts"))}%</b></div>
        <div class="r"><span>最大偏差</span><b class="{tone(maxpp(m))}">{sg(maxpp(m))}pp</b></div>
      </div></div>
    <div class="bk"><h3>信心五维<em>合计 100</em></h3>
      <div style="display:flex;align-items:baseline;gap:3mm">
        <div class="big">{f(conf.get("total"), 0)}<em>/100</em></div>
        <div style="font-size:11px;color:#6b7280">{e(conf.get("grade") or "")}</div>
      </div>
      <div class="dims" style="margin-top:1.5mm">{dims}</div></div>
  </div>

  <div class="band b">
    <div class="bk"><h3>盘口分析解读<em>让球 · 大小球 · 抽水 · 冷热 · 变动</em></h3>
      <div class="two">{market_read(m)}</div></div>
    <div class="bk"><h3>战术风格与比赛走向<em>攻防对位 · 节奏 · 波动 · 交锋形态</em></h3>
      <div class="two">{tactic_read(m)}</div></div>
  </div>

  <div class="band c">
    <div class="bk"><h3>数据底稿<em>λ 双法 · 低比分修正</em></h3>
      <div class="kv">
        <div class="r"><span>λ 主 · 实际 / 反推</span><b>{f((lam.get("l1") or [0, 0])[0], 2)} / {f((lam.get("l2") or [0, 0])[0], 2)}</b></div>
        <div class="r"><span>λ 客 · 实际 / 反推</span><b>{f((lam.get("l1") or [0, 0])[1], 2)} / {f((lam.get("l2") or [0, 0])[1], 2)}</b></div>
        <div class="r"><span>综合 λ 主 / 客 / 合计</span><b>{f((lam.get("fin") or [0, 0])[0], 2)} / {f((lam.get("fin") or [0, 0])[1], 2)} / {f(lam.get("total"), 2)}</b></div>
      </div>
      <div style="margin-top:2mm">{dc_compare(m)}</div></div>
    <div class="bk"><h3>比分分布<em>进球数 · 概率 / 定价 / 溢价</em></h3>
      <div style="color:#3f4650;margin-bottom:2mm">{goal_chart(m, 34)}</div>
      {score_rows(m, 4)}</div>
    <div class="bk"><h3>技术面<em>主客对照</em></h3>{tech_pair(m)}
      <div style="margin-top:2mm;font-size:10px;color:#8b93a0;letter-spacing:1px">
        伤停与停赛 · {len((m.get("intel") or {}).get("inj") or [])} 人</div>
      <div style="margin-top:1mm">{inj_rows(m, 2)}</div></div>
  </div>

  <div class="band c">
    <div class="bk"><h3>得分点与降权提示<em>模型不建议主推的格子</em></h3>
      {sc_html}
      <div style="margin-top:2mm">{flag_rows(m, 2)}</div></div>
    <div class="bk"><h3>国内外媒体与 AI 对照<em>我方模型 / 去水定价 / 外部源</em></h3>
      {media_compare(m)}</div>
    <div class="bk"><h3>影响赛果的因素清单<em>有源才算，缺源明写</em></h3>
      <div class="fxwrap">{factor_rows(m)}</div></div>
  </div>

  <div class="band e">
    <div class="bk"><h3>总结分析<em>方向 · 比分 · 风险点</em></h3>
      <div class="dsum">{summary_read(m)}</div>
      <div class="sc3">
        <div><s>首选比分</s><b>{e(v.get("first_score"))}</b></div>
        <div><s>次选比分</s><b>{e(v.get("second_score"))}</b></div>
        <div><s>防范比分</s><b>{e(v.get("guard_score"))}</b></div>
      </div></div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 付费内部资料</span>
    <span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</section>"""
    return css, html


LAYOUTS = [
    ("dossier", "综合研判", lay_dossier),
    ("dashboard", "数据仪表盘", lay_dashboard),
    ("newspaper", "报纸头版", lay_newspaper),
    ("matrix", "比分矩阵", lay_matrix),
    ("split", "对半分栏", lay_split),
    ("timeline", "时间轴", lay_timeline),
    ("poster", "大字海报", lay_poster),
    ("ledger", "账本表格", lay_ledger),
    ("magazine", "杂志跨页", lay_magazine),
    ("terminal", "数据终端", lay_terminal),
    ("radar", "六维对比", lay_radar),
]


# ══════════════════════════════════════════════ 封面 / 总览 / 附录 / 缺口页
def page_cover(ms, meta) -> tuple:
    css = """
    .pc{background:#0d0d0f;color:#f2efe9;padding:20mm 16mm;display:flex;flex-direction:column;}
    .pc .k{font-size:9px;letter-spacing:6px;color:#b8853c;}
    .pc h1{font-size:56px;font-weight:800;line-height:1;letter-spacing:-2px;margin-top:6mm;}
    .pc h1 em{display:block;font-size:22px;font-weight:400;letter-spacing:8px;color:#8a857c;margin-top:4mm;font-style:normal;}
    .pc .ln{height:1px;background:linear-gradient(90deg,#b8853c,rgba(184,133,60,.08));margin:8mm 0;}
    .pc .sub{font-size:12px;line-height:2;color:#b7b2a8;max-width:150mm;}
    .pc .kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:auto;
             border-top:1px solid rgba(242,239,233,.14);border-bottom:1px solid rgba(242,239,233,.14);}
    .pc .kpi div{padding:5mm 3mm;border-right:1px solid rgba(242,239,233,.1);}
    .pc .kpi div:last-child{border-right:0;}
    .pc .kpi b{display:block;font-size:30px;font-weight:800;line-height:1;font-variant-numeric:tabular-nums;}
    .pc .kpi s{display:block;font-size:8.5px;letter-spacing:1.5px;color:#8a857c;text-decoration:none;
               margin-top:2mm;text-transform:uppercase;}
    .pc .foot{display:flex;justify-content:space-between;font-size:8.5px;color:#5f5c56;margin-top:6mm;letter-spacing:1px;}
    .pc .mid{display:grid;grid-template-columns:1fr 1fr;gap:10mm;margin-top:9mm;}
    .pc .mid .t{font-size:8.5px;letter-spacing:3px;color:#b8853c;margin-bottom:3mm;}
    .pc .lg{font-size:10px;line-height:2.1;}
    .pc .lg .r{display:flex;align-items:center;gap:2mm;}
    .pc .lg .r span{width:34mm;color:#b7b2a8;}
    .pc .lg .r i{height:6px;background:#b8853c;border-radius:1px;display:inline-block;}
    .pc .lg .r b{margin-left:auto;color:#f2efe9;font-variant-numeric:tabular-nums;}
    .pc .top{font-size:9.5px;line-height:1.85;}
    .pc .top .r{display:flex;justify-content:space-between;border-bottom:1px dotted rgba(242,239,233,.13);padding:1.4px 0;}
    .pc .top .r em{color:#8a857c;font-style:normal;}
    .pc .top .r b{font-variant-numeric:tabular-nums;}
    .pc .top .r b.r{color:#ff9b95;} .pc .top .r b.a{color:#ffc98a;}
    .pc .how{display:grid;grid-template-columns:repeat(3,1fr);gap:0 8mm;margin-top:9mm;
             border-top:1px solid rgba(242,239,233,.13);padding-top:6mm;}
    .pc .how .c{font-size:9.5px;line-height:1.9;color:#8f8b83;}
    .pc .how .c b{display:block;color:#f2efe9;font-size:11px;margin-bottom:2mm;letter-spacing:.5px;}
    .pc .how .c u{color:#b8853c;text-decoration:none;}
    """
    leagues = list(dict.fromkeys(x["league"] for x in ms))
    lay_names = ", ".join(n for _, n, _ in LAYOUTS)
    lg_cnt = {}
    for x in ms:
        lg_cnt[x["league"]] = lg_cnt.get(x["league"], 0) + 1
    lg_max = max(lg_cnt.values()) if lg_cnt else 1
    lg_html = "".join(
        f'<div class="r"><span>{e(k)}</span>'
        f'<i style="width:{max(4, round(28 * v / lg_max))}mm"></i><b>{v} 场</b></div>'
        for k, v in sorted(lg_cnt.items(), key=lambda kv: -kv[1])
    )
    scored = [x for x in ms if x.get("p")]
    top_dev = sorted(scored, key=lambda x: -abs(maxpp(x)))[:7]
    top_html = "".join(
        f'<div class="r"><span>{e(x["home"])[:6]} <em>vs</em> {e(x["away"])[:6]}</span>'
        f'<b class="{tone(maxpp(x))}">{sg(maxpp(x))}pp</b></div>'
        for x in top_dev
    )
    html = f"""
<section class="page pc">
  <div class="k">付费内部资料 · 全维度推演</div>
  <h1>{meta["date"][:4]}.{meta["date"][4:6]}.{meta["date"][6:]}<em>周 日 · 全 盘</em></h1>
  <div class="ln"></div>
  <div class="sub">一册 {len(ms)} 场，每场一页到底。数据层走 λ 双法（实际数据法 / 市场反推法）、
    Dixon-Coles 低比分修正、信心五维与冷门指数；版式层准备了 {len(LAYOUTS)} 套互不相同的版面
    （{lay_names}），每次生成随机铺排，读起来不会一路同一个模子。
    公开稿里不能写的口径，这一册里全部展开；但缺的料仍然写缺，不做估算值冒充。</div>
  <div class="mid">
    <div><div class="t">联赛分布</div><div class="lg">{lg_html}</div></div>
    <div><div class="t">本册分歧最大的 7 场</div><div class="top">{top_html}</div></div>
  </div>
  <div class="kpi">
    <div><b>{len(ms)}</b><s>覆盖场次</s></div>
    <div><b>{len(leagues)}</b><s>联赛数</s></div>
    <div><b>{len(LAYOUTS)}</b><s>版式池</s></div>
    <div><b>{meta.get("avg_conf", 0):.0f}</b><s>平均信心</s></div>
  </div>
  <div class="how">
    <div class="c"><b>这本册子怎么用</b>
      先看第 02 页总览，把 <u>偏差 ≥15pp</u> 的场次挑出来；再到对应页看那一格是
      「我方样本缺口」还是「定价在押别的可能」。前者只当方向，后者才值得细读。
      剩下的场次两边结构基本重合，翻过即可。</div>
    <div class="c"><b>每页固定出现的四样</b>
      一、三向概率与偏差；二、λ 双法（实际数据法 / 市场反推法）与合计；
      三、首选 / 次选 / 防范三档比分；四、模型自己标出的降权与剔除。
      版式会换，这四样在 25 页里一个不落。</div>
    <div class="c"><b>缺的料写缺</b>
      xG、xGA、npxG、PPDA、定位球 xG、裁判尺度——没有数据源就留空，不填估算值。
      未开售的场次单出「数据缺口页」，只列能核实的近期得失与人员面，
      不拿主观估价冒充模型读数。</div>
  </div>
  <div class="foot"><span>阿飞 · 赛博聊球 · 内部资料</span><span>生成 {meta["stamp"]} · 模型 {meta["model"]}</span></div>
</section>"""
    return css, html


def page_overview(ms, meta) -> tuple:
    css = """
    .po{background:#f6f7f9;color:#1a1c22;padding:11mm 12mm 9mm;display:flex;flex-direction:column;}
    .po .hd{display:flex;justify-content:space-between;align-items:flex-end;
            border-bottom:2px solid #1a1c22;padding-bottom:2mm;}
    .po .hd h2{font-size:21px;font-weight:800;letter-spacing:-.3px;}
    .po .hd .r{font-size:9px;color:#6b7280;text-align:right;line-height:1.6;}
    .po table{width:100%;border-collapse:collapse;font-size:9px;margin-top:3mm;}
    .po th{background:#1a1c22;color:#fff;font-size:8px;letter-spacing:1.2px;padding:1.6mm 1.5mm;text-align:left;font-weight:600;}
    .po td{padding:1.5mm 1.5mm;border-bottom:1px solid #e4e7ec;font-variant-numeric:tabular-nums;vertical-align:middle;}
    .po tr:nth-child(even) td{background:#fff;}
    .po td.n{font-weight:700;color:#6b7280;}
    .po td.m{font-weight:600;}
    .po td.hand{color:#8f97a6;text-align:center;}
    .po td.cf b{font-size:10px;}
    .po .mini{display:inline-block;height:5px;border-radius:1px;background:#d7dbe2;vertical-align:middle;}
    .po .mini i{display:block;height:5px;border-radius:1px;}
    .po .note{font-size:9px;line-height:1.9;color:#6b7280;margin-top:3mm;}
    .po .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:0 6mm;margin-top:4mm;}
    .po .stats .t{font-size:8px;letter-spacing:2px;color:#8f97a6;margin-bottom:1.5mm;
                  border-bottom:1px solid #d7dbe2;padding-bottom:1mm;}
    .po .stats .r{display:flex;align-items:center;gap:2mm;font-size:9px;line-height:1.8;
                  font-variant-numeric:tabular-nums;}
    .po .stats .r span{width:22mm;color:#5b6472;}
    .po .stats .r i{height:6px;background:#1a1c22;border-radius:1px;}
    .po .stats .r b{margin-left:auto;font-weight:700;}
    .po .ft{display:flex;justify-content:space-between;font-size:8px;color:#a4aab4;margin-top:auto;padding-top:3mm;}
    """
    rows = []
    for ms_i, m in enumerate(ms, 1):
        cf = (m.get("conf") or {}).get("total")
        cfc = "g" if (cf or 0) >= 65 else ("a" if (cf or 0) >= 50 else "r")
        rows.append(
            f'<tr><td class="n">{ms_i:02d}</td><td class="m">{e(m["no"])}</td><td>{e(m["kick"])}</td>'
            f'<td>{e(m["league"])}</td><td>{e(m["home"])} vs {e(m["away"])}</td>'
            f'<td class="hand">{m["hand"]:+d}</td>'
            + (f'<td>{f(m["p"][0])}</td><td>{f(m["p"][1])}</td><td>{f(m["p"][2])}</td>'
               f'<td class="{tone(maxpp(m))}">{sg(maxpp(m))}</td>'
               f'<td class="cf"><b class="{cfc}">{f(cf, 0)}</b></td>'
               f'<td>{e(m["verdict"]["first_score"])}</td>'
               if m.get("p") else
               '<td colspan="6" style="color:#c9322b">未开售/已封盘 · 无固定奖金 · 模型跳过</td>')
            + "</tr>"
        )
    # 三张分布小图：信心档、最大偏差落点、首选方向
    cf_cnt = {"A · 高（≥75）": 0, "B · 中高（65–75）": 0, "C · 中（50–65）": 0, "D · 谨慎（<50）": 0}
    dev_cnt = {"≥15pp": 0, "6–15pp": 0, "<6pp": 0}
    first_cnt = {d: 0 for d in DIRS}
    for x in ms:
        if not x.get("p"):
            continue
        c = (x.get("conf") or {}).get("total") or 0
        if c >= 75:
            cf_cnt["A · 高（≥75）"] += 1
        elif c >= 65:
            cf_cnt["B · 中高（65–75）"] += 1
        elif c >= 50:
            cf_cnt["C · 中（50–65）"] += 1
        else:
            cf_cnt["D · 谨慎（<50）"] += 1
        a = abs(maxpp(x))
        dev_cnt["≥15pp" if a >= 15 else ("6–15pp" if a >= 6 else "<6pp")] += 1
        fd = (x.get("verdict") or {}).get("first")
        if fd in first_cnt:
            first_cnt[fd] += 1
    cf_dist = list(cf_cnt.items())
    dev_dist = list(dev_cnt.items())
    first_dist = list(first_cnt.items())
    cf_max = max(cf_cnt.values()) if cf_cnt else 1
    dev_max = max(dev_cnt.values()) if dev_cnt else 1
    first_max = max(first_cnt.values()) if first_cnt else 1
    html = f"""
<section class="page po">
  <div class="hd"><h2>总览 · {len(ms)} 场一页看完</h2>
    <div class="r">模型概率 / 定价概率 / 最大偏差 / 信心 / 首选比分<br>{meta["date"][:4]}.{meta["date"][4:6]}.{meta["date"][6:]} · 仅统计 90 分钟</div></div>
  <table>
    <tr><th>#</th><th>场次</th><th>开赛</th><th>联赛</th><th>对阵</th><th>让</th>
      <th>主胜</th><th>平</th><th>客胜</th><th>偏差</th><th>信心</th><th>首选</th></tr>
    {"".join(rows)}
  </table>
  <div class="note">偏差取三格里绝对值最大的一格，单位是百分点；≥15pp 标红（按纪律先假定我方样本有缺口，只做方向参考），
    6–15pp 标橙（方向可信、幅度打折），小于 6pp 标绿（两边结构基本重合）。
    信心是五维加权结果：样本厚度 20 + 双法收敛 20 + 三方一致 25 + 分歧可控 25 + 比分集中 10。
    未开售的场次不编模型，直接在表里标缺口。</div>
  <div class="stats">
    <div><div class="t">信心分布</div>
      {"".join(f'<div class="r"><span>{lab}</span><i style="width:{max(3, round(24 * v / max(1, cf_max)))}mm"></i><b>{v} 场</b></div>'
               for lab, v in cf_dist)}
    </div>
    <div><div class="t">最大偏差落点</div>
      {"".join(f'<div class="r"><span>{d}</span><i style="width:{max(3, round(24 * c / max(1, dev_max)))}mm"></i><b>{c} 场</b></div>'
               for d, c in dev_dist)}
    </div>
    <div><div class="t">首选方向</div>
      {"".join(f'<div class="r"><span>{d}</span><i style="width:{max(3, round(24 * c / max(1, first_max)))}mm"></i><b>{c} 场</b></div>'
               for d, c in first_dist)}
      <div class="r" style="margin-top:1.5mm"><span>未开售</span><b>{sum(1 for x in ms if not x.get("p"))} 场</b></div>
    </div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料</span><span>第 02 页 · 共 {len(ms) + 3} 页</span></div>
</section>"""
    return css, html


def page_missing(m, i) -> tuple:
    """未开售/已封盘：没有固定奖金就没有模型，只写能核实的技术面与人员面。"""
    css = """
    .pm{background:#fff;color:#1a1c22;padding:12mm 13mm 10mm;display:flex;flex-direction:column;}
    .pm .hd{border-bottom:2px solid #c9322b;padding-bottom:3mm;}
    .pm .hd .k{font-size:8.5px;letter-spacing:3px;color:#c9322b;}
    .pm .hd h1{font-size:27px;font-weight:800;margin-top:1.5mm;line-height:1.2;}
    .pm .hd h1 s{text-decoration:none;color:#b8bfcc;font-size:16px;margin:0 2mm;font-weight:400;}
    .pm .alert{background:#fdf3f2;border-left:3px solid #c9322b;padding:3.5mm;margin:5mm 0;font-size:11px;line-height:1.9;}
    .pm .grid{display:grid;grid-template-columns:1fr 1fr;gap:5mm;flex:1;min-height:0;}
    .pm .blk .t{font-size:8.5px;letter-spacing:2px;color:#8f97a6;margin-bottom:2mm;
                border-bottom:1px solid #e4e7ec;padding-bottom:1mm;}
    .pm .row{display:flex;justify-content:space-between;font-size:10px;line-height:1.9;
             border-bottom:1px dotted #e4e7ec;font-variant-numeric:tabular-nums;}
    .pm .row b{font-weight:700;}
    .pm .txt{font-size:10px;line-height:1.9;color:#4b5563;}
    .pm .ft{display:flex;justify-content:space-between;font-size:8px;color:#a4aab4;margin-top:4mm;}
    """
    tech = m.get("tech") or {}
    meet = tech.get("meet") or {}
    hs, as_ = tech.get("home", {}) or {}, tech.get("away", {}) or {}
    scorers = m.get("scorers") or []
    inj = (m.get("intel") or {}).get("inj") or []
    sc_html = "".join(
        f'<div class="row"><span>{e(s["team"][:1])} {e(s["name"])}</span><b>{s["goal"]} 球 / {s["assist"]} 助</b></div>'
        for s in scorers[:6]
    ) or '<div class="txt">无球员数据</div>'
    html = f"""
<section class="page pm">
  <div class="hd"><div class="k">{e(m["no"])} · {e(m["league"])} · {e(m["kick"])}</div>
    <h1>{e(m["home"])}<s>vs</s>{e(m["away"])}</h1></div>
  <div class="alert"><b>数据缺口页。</b>该场暂无胜平负固定奖金（未开售 / 已封盘），没有去水定价就无法反推，
    模型按纪律跳过，不出 λ、不出胜平负概率、不出比分矩阵——不拿估算值冒充。
    以下只列能在官方数据里核实到的技术面与人员面，供你人工判断时当底稿。</div>
  <div class="grid">
    <div>
      <div class="blk"><div class="t">近期得失（主队近 {hs.get("n", 0)} 场 / 客队近 {as_.get("n", 0)} 场）</div>
        <div class="row"><span>场均进球</span><b>{f(hs.get("gf_avg"), 2)} / {f(as_.get("gf_avg"), 2)}</b></div>
        <div class="row"><span>场均失球</span><b>{f(hs.get("ga_avg"), 2)} / {f(as_.get("ga_avg"), 2)}</b></div>
        <div class="row"><span>零封率</span><b>{f(hs.get("cs_rate"), 0)}% / {f(as_.get("cs_rate"), 0)}%</b></div>
        <div class="row"><span>上半场进球占比</span><b>{f(hs.get("share_1h"), 0)}% / {f(as_.get("share_1h"), 0)}%</b></div>
        <div class="row"><span>进球标准差</span><b>{f(hs.get("sd_for"), 2)} / {f(as_.get("sd_for"), 2)}</b></div>
        <div class="row"><span>失球标准差</span><b>{f(hs.get("sd_against"), 2)} / {f(as_.get("sd_against"), 2)}</b></div>
      </div>
      <div class="blk" style="margin-top:4mm"><div class="t">近期逐场（主 / 客）</div>{recent_rows(m, 5)}</div>
      <div class="blk" style="margin-top:4mm"><div class="t">交锋 {meet.get("n", 0)} 场</div>
        <div class="row"><span>场均总进球</span><b>{f(meet.get("avg_total"), 2)}</b></div>
        <div class="row"><span>≤2 球占比</span><b>{f(meet.get("low2"), 0)}%</b></div>
        <div class="row"><span>平局占比</span><b>{f(meet.get("draw"), 0)}%</b></div>
        <div class="row"><span>双方进球占比</span><b>{f(meet.get("btts"), 0)}%</b></div>
        <div style="margin-top:2mm">{"".join(f'<div class="row"><span>{e(d.get("d"))}</span><span>{e(d.get("m"))}</span></div>' for d in (meet.get("detail") or [])[:8])}</div>
      </div>
    </div>
    <div>
      <div class="blk"><div class="t">主要得分点（出场 / 进球 / 助攻）</div>{sc_html}</div>
      <div class="blk" style="margin-top:4mm"><div class="t">伤停与停赛 · {len(inj)} 人</div>{inj_rows(m, 10)}</div>
      <div class="blk" style="margin-top:4mm"><div class="t">人工研判时先看这三件事</div>
        <div class="txt">一，主客场均得失差：两队差出 0.8 球以上，多半能用进球方向替代胜平负方向。<br>
          二，上半场进球占比：占比高说明开场就开火，占比低说明后程才分胜负，两种形态对应的比分区间完全不同。<br>
          三，交锋里的低比分占比：≥50% 说明这对冤家互相看得死，别按场均总进球的直觉走。</div></div>
      <div class="blk" style="margin-top:4mm"><div class="t">开售后的补算流程</div>
        <div class="txt">
          一，拿到胜平负固定奖金后先用官方口径去水，得到无抽水的三格定价；<br>
          二，从去水定价反解两队的期望进球（方法2 市场反推法），得到 λ 客；<br>
          三，与本次已算好的方法1（实际数据法）按样本厚度加权，得到综合 λ；<br>
          四，走 Dixon-Coles 修正出 49 格比分矩阵，再取首选 / 次选 / 防范三档。<br>
          命令：<b>python scripts/model.py {e(m["no"])}</b>，重出后本页作废，模型页替换。
        </div></div>
      <div class="blk" style="margin-top:4mm"><div class="t">本页刻意不写的东西</div>
        <div class="txt">
          胜平负概率、比分矩阵、λ、信心指数、冷门指数、首选 / 次选 / 防范——全部不写。
          这几格都必须以去水定价为锚，没有锚就只能靠主观估，估出来的数与真实模型页长得一样、
          性质完全不同，混在一册里会让人误当模型读数用。缺口就标成缺口。
        </div></div>
      <div class="blk" style="margin-top:4mm"><div class="t">口径</div>
        <div class="txt">90 分钟常规时间口径；加时与点球不计。缺 xG / xGA / npxG / PPDA / 定位球 xG / 裁判尺度数据源，
        一律留空。等该场开售拿到固定奖金后可用 <b>python scripts/model.py {e(m["no"])}</b> 单独补算，本页即作废。</div></div>
    </div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料 · 第 {i} 页</span><span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</section>"""
    return css, html


def page_appendix(ms, meta, n_pages) -> tuple:
    css = """
    .pa{background:#f6f7f9;color:#1a1c22;padding:12mm 14mm 10mm;display:flex;flex-direction:column;}
    .pa h2{font-size:20px;font-weight:800;border-bottom:2px solid #1a1c22;padding-bottom:2mm;margin-bottom:4mm;}
    .pa h3{font-size:11px;font-weight:700;margin:4mm 0 1.5mm;color:#1a1c22;}
    .pa p{font-size:9.5px;line-height:1.95;color:#3f4650;text-align:justify;}
    .pa .two{display:grid;grid-template-columns:1fr 1fr;gap:0 8mm;}
    .pa .kv{font-size:9.5px;line-height:2;font-variant-numeric:tabular-nums;}
    .pa .kv div{display:flex;justify-content:space-between;border-bottom:1px dotted #d7dbe2;}
    .pa .ft{margin-top:auto;padding-top:4mm;border-top:1px solid #d7dbe2;
            display:flex;justify-content:space-between;font-size:8px;color:#a4aab4;}
    .pa .gloss{display:grid;grid-template-columns:1fr 1fr;gap:0 8mm;font-size:9px;line-height:1.8;color:#3f4650;}
    .pa .gloss div{border-bottom:1px dotted #d7dbe2;padding:1mm 0;text-align:justify;}
    .pa .gloss b{color:#1a1c22;margin-right:1.5mm;}
    """
    lay_list = "".join(
        f'<div><span>{k + 1:02d} · {e(n)}</span><b>{e(fid)}</b></div>'
        for k, (fid, n, _) in enumerate(LAYOUTS)
    )
    html = f"""
<section class="page pa">
  <h2>附 · 方法论、口径与缺口</h2>
  <div class="two">
    <div>
      <h3>一 · λ 双法与收敛</h3>
      <p>方法1「实际数据法」按主客分离样本算进攻与防守强度，样本薄时按权重混入近 10 场；
        方法2「市场反推法」从去水定价反解两队期望进球。综合 λ 取两者按样本厚度加权。
        两法相对差越大，绝对值的可信度越低——这就是信心五维里「双法收敛」占 20 分的理由。</p>
      <h3>二 · Dixon-Coles 修正</h3>
      <p>纯独立泊松会低估 0-0 / 1-1 / 0-1 / 1-0 这四个低比分格。本册固定 ρ = {f(pc.RHO, 2)}
        （文献区间 −0.05 至 −0.15，取中值偏保守），对四格做 τ 修正后再归一。
        本批样本量不足以逐场拟合 ρ，逐场拟出来的数看着更精确，其实是过拟合。</p>
      <h3>三 · 信心五维</h3>
      <div class="kv">
        <div><span>样本厚度</span><b>20</b></div>
        <div><span>双法收敛</span><b>20</b></div>
        <div><span>三方一致（模型 / 定价 / 外部源）</span><b>25</b></div>
        <div><span>分歧可控</span><b>25</b></div>
        <div><span>比分集中</span><b>10</b></div>
      </div>
      <h3>四 · 冷门指数</h3>
      <p>定价最热的那一格之外，模型给出的概率之和。数字越大，说明定价热的那一头在模型里越站不住；
        本册把「次冷」也标出来，因为真正被低估的常常不是最热之外的第一格，而是第二格。</p>
      <h3>五 · 偏差怎么读</h3>
      <p>偏差＝模型概率减去去水定价概率，单位是百分点。≥15pp 的格子按纪律先假定我方样本有缺口，
        只当方向参考，不当结论；6–15pp 方向可信但幅度要打折；小于 6pp 说明两边结构基本重合，
        这一格没有可做的差价。整册的红/橙/绿三色就是按这个阈值上色的，跟概率大小无关。</p>
      <h3>六 · 三档比分的取法</h3>
      <p>首选＝模型概率最高的那一格；次选＝概率第二高的那一格（不是「除首选外按序号取第一个」，
        那是旧版的一个错，会把第二高漏掉）；防范＝若方向反过来最可能的退路。
        三档在全部 49 个比分格里按方向取，取不到的格子宁可空着，也不跨方向硬塞。</p>
    </div>
    <div>
      <h3>七 · 本册版式池（{len(LAYOUTS)} 套，每次随机铺排）</h3>
      <div class="kv">{lay_list}</div>
      <h3>八 · 明确不做的</h3>
      <p>xG、xGA、npxG、PPDA、定位球 xG、裁判尺度、天气——都没有数据源。凡是这类格子，
        本册一律留空并在页内标注缺口，不用估算值、不用"参考区间"填满版面。
        接口坏值（10/45/45 这种二选一表述、进球 −2.5 这种负数）一律不采信。</p>
      <h3>九 · 未开售场次</h3>
      <p>没有固定奖金就没有去水定价，方法2 无从反推，模型按纪律直接跳过，
        单出一页「数据缺口页」，只写可核实的近期得失、交锋、得分点与伤停。</p>
      <h3>十 · 口径</h3>
      <p>本册只统计 90 分钟常规时间；加时与点球不计入任何一格。
        所有概率是模型与定价的对照读数，不是对未来赛果的承诺，也不构成任何购买建议。
        内部资料，请勿外传。</p>
    </div>
  </div>
  <h3 style="margin-top:5mm">十一 · 本册每一格在说什么（术语对照）</h3>
  <div class="gloss">
    <div><b>λ 主 / 客</b>两队各自的期望进球数，比分矩阵就是由这两个数生成的。</div>
    <div><b>λ 合计</b>两队期望进球之和，等于全场期望总进球，直接决定大小球方向。</div>
    <div><b>双法</b>方法1 用实际数据算，方法2 从去水定价反解，两法差越大绝对值越不可信。</div>
    <div><b>去水</b>把三格定价里的抽水按比例扣掉，还原成真实概率，与返还率互补。</div>
    <div><b>偏差（pp）</b>模型概率减去去水定价概率，百分点。正数表示模型比定价看得更高。</div>
    <div><b>溢价</b>模型概率乘固定奖金再减 1，正数表示按模型读数这一注长期不亏。</div>
    <div><b>让球</b>让 -1 意味着主队要先赢 1 球才回到同一起跑线，三格概率整体后移。</div>
    <div><b>去掉平局</b>把平局概率按比例分给胜负两边，用来回答「谁更可能赢」。</div>
    <div><b>Dixon-Coles</b>对 0-0 / 1-0 / 0-1 / 1-1 四格做低比分修正，纯泊松会低估这四格。</div>
    <div><b>冷门指数</b>定价最热那格之外模型给的概率之和，越大说明热的那头越站不住。</div>
    <div><b>信心五维</b>样本厚度 20 + 双法收敛 20 + 三方一致 25 + 分歧可控 25 + 比分集中 10。</div>
    <div><b>降权 / 剔除</b>模型自己标出的不建议主推的格子，附理由，含尾部太薄与方向相悖两类。</div>
    <div><b>首选 / 次选 / 防范</b>模型概率第一、第二高的方向各取一格，外加方向反过来时的退路。</div>
    <div><b>比分集中度</b>Top3 比分概率之和，越高说明这场越像「就那两三个比分」。</div>
    <div><b>零封率</b>该队近期比赛里没让对手进球的场次占比，用来判防守稳定性。</div>
    <div><b>上半场占比</b>该队进球里发生在上半场的比例，高的队开场就开火，低的队后程发力。</div>
  </div>
  <div class="ft"><span>阿飞 · 赛博聊球 · 内部资料 · {meta["date"]}</span>
    <span>共 {n_pages} 页 · 生成 {meta["stamp"]} · 模型 {meta["model"]}</span></div>
</section>"""
    return css, html


# ══════════════════════════════════════════════ 装配
def build_pages(data: dict, slate: dict, seed=None, verbose=True, only=None, only_layout=None,
                one=True):
    ms = data["matches"]
    for m in ms:
        if "scorers" not in m and m.get("mid"):
            m["scorers"] = _scorers(str(m["mid"]))
    # 缺口场次（有赛程、无模型）
    have = {m["no"] for m in ms}
    gaps = []
    for no, s in slate.items():
        if no in have:
            continue
        mid = s["matchId"]
        gaps.append({
            "no": no, "league": s["league"], "home": s["home"], "away": s["away"],
            "mid": str(mid), "kick": pc.kick_of(mid) or s["kick"],
            "hand": 0, "p": None, "mk": None,
            "tech": {
                "home": pc.team_form(str(mid), s["home"], "home"),
                "away": pc.team_form(str(mid), s["away"], "away"),
                "meet": pc.meetings(str(mid)),
            },
            "intel": {"inj": pc.injuries(str(mid))},
            "scorers": _scorers(str(mid)),
        })

    # 按开赛时间排序，缺口页插回原位
    def sortkey(x):
        k = x.get("kick") or "10/18 00:00"
        day, hm = k.split(" ")
        h, mi = hm.split(":")
        return (0 if day.startswith("10/18") else 1, int(h), int(mi), x["no"])

    allm = sorted(ms + gaps, key=sortkey)

    # 只出单场单页（给用户看效果用）：--only 周日012 [--only-layout 1..10]
    if only:
        key = only.strip()
        hit = [x for x in allm if x["no"] == key or x["no"].replace("周日", "") == key]
        if not hit:
            raise SystemExit(f"赛程里没有 {key}；可选：" + "、".join(x["no"] for x in allm))
        src = hit[0]
        if src.get("p") is None:
            css, html = page_missing(src, 1)
            lay_name = "数据缺口页"
        else:
            li = (int(only_layout) - 1) if only_layout else 0
            if not (0 <= li < len(LAYOUTS)):
                raise SystemExit(f"--only-layout 取 1–{len(LAYOUTS)}")
            fid, name, fn = LAYOUTS[li]
            css, html = fn(src, 1)
            lay_name = f"{li + 1:02d} {name}"
        print(f"  单页样例：{src['no']} {src['home']} vs {src['away']} → {lay_name}")
        return [(css, html)], [(src["no"], src["home"], src["away"], lay_name)], dict(data["meta"])

    rnd = random.Random(seed)
    # 版式分配：每一步在「不等于上一页」的版式里随机抽——
    # 25 场铺 10 套版式，纯洗牌必然出现连号，连着读就又变成一个模子；
    # 同时记录各版式用量，优先补给用得少的那几套，保证 10 套都露脸。
    pool, used = [], {}
    for _ in range(len(allm)):
        cand = [k for k in range(len(LAYOUTS))
                if (not pool or k != pool[-1])]
        lo = min(used.get(k, 0) for k in cand)
        cand = [k for k in cand if used.get(k, 0) <= lo + 1]
        pick = rnd.choice(cand)
        pool.append(pick)
        used[pick] = used.get(pick, 0) + 1

    pages, assign = [], []
    for idx, m in enumerate(allm, 1):
        if m.get("p") is None:
            css, html = page_missing(m, idx)
            assign.append((m["no"], m["home"], m["away"], "数据缺口页"))
        else:
            # 每期统一一套模板：默认全部走 0 号「综合研判」；
            # 想回到 10 套版式轮换要显式加 --pool。
            li = pool[idx - 1] if one else 0
            fid, name, fn = LAYOUTS[li]
            css, html = fn(m, idx)
            assign.append((m["no"], m["home"], m["away"], f"{li:02d} {name}"))
        pages.append((css, html))

    meta = dict(data["meta"])
    meta["avg_conf"] = (
        sum((m.get("conf") or {}).get("total") or 0 for m in ms) / len(ms) if ms else 0
    )
    n_pages = len(allm) + 3

    head = [page_cover(allm, meta), page_overview(allm, meta)]
    tail = [page_appendix(allm, meta, n_pages)]
    if verbose:
        for k, (no, h, a, lay) in enumerate(assign, 1):
            print(f"  p{k + 2:02d}  {no}  {h} vs {a}  →  {lay}")
    return head + pages + tail, assign, meta


def _scorers(mid: str) -> list:
    try:
        v = pc.read_json(pc.MATCHES / mid / "player.json").get("value", {}) or {}
    except Exception:  # noqa: BLE001
        return []
    out = []
    for side in ("home", "away"):
        blk = v.get(side) or {}
        team = blk.get("teamShortName", "")
        for p in (blk.get("playerList") or []):
            try:
                g = int(p.get("goalCnt") or 0)
                a = int(p.get("assistCnt") or 0)
            except (TypeError, ValueError):
                continue
            if g > 0 or a > 0:
                out.append({"team": team, "name": p.get("personName", ""), "goal": g, "assist": a,
                            "apps": p.get("appearanceCnt", 0)})
    out.sort(key=lambda x: (-x["goal"], -x["assist"]))
    return out


def render_pdf(pages, out: Path, title: str, engine: str = "chromium") -> None:
    body = "\n".join(h for _, h in pages)
    css_all = CSS_BASE + "\n" + "\n".join(c for c, _ in pages)
    doc = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{title}</title><style>{css_all}</style></head><body>{body}</body></html>"""
    tmp = ROOT / "state" / "tmp" / (out.stem + ".html")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(doc, encoding="utf-8")

    if engine == "print":
        print(f"  HTML 已生成：{tmp}\n  用浏览器打开后 Ctrl+P → 另存为 PDF（A4、无边距、勾选背景图形）")
        return

    from playwright.sync_api import sync_playwright

    out.parent.mkdir(parents=True, exist_ok=True)
    raw = out.with_name(out.stem + ".raw.pdf")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.goto(tmp.as_uri(), wait_until="load")
        pg.emulate_media(media="print")
        pg.pdf(path=str(raw), format="A4", print_background=True,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        b.close()

    # 补文档属性（Chromium 只写 Creator/Producer，title/author 为空），顺手压一遍
    cli = Path(r"C:\Program Files\PdfCraft\pdfcraft-cli.exe")
    if cli.exists():
        r = subprocess.run(
            [str(cli), "edit", str(raw), "--out", str(out),
             "--title", title, "--author", "阿飞 · 赛博聊球"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode == 0 and out.exists():
            raw.unlink(missing_ok=True)
        else:
            print(f"  ⚠️ 属性写入失败，保留原文件：{(r.stderr or r.stdout or '')[:200]}")
            raw.replace(out)
    else:
        raw.replace(out)

    print(f"✅ {out}  {out.stat().st_size / 1024:.0f}KB · {len(pages)} 页")


def main() -> None:
    ap = argparse.ArgumentParser(description="付费内部资料·一册 PDF（每场一页，10 种排版随机）")
    ap.add_argument("--model", default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--seed", type=int, default=None, help="固定随机种子可复现版式")
    ap.add_argument("--list", action="store_true", help="只打印版式分配表")
    ap.add_argument("--only", default=None, help="只出这一场（如 周日012 或 012），用于单页预览")
    ap.add_argument("--only-layout", default=None, help="配合 --only，指定用第几套版式（1-11）")
    ap.add_argument("--pool", action="store_true",
                    help="回到 10 套版式随机轮换；默认全册统一用「综合研判」一套模板")
    ap.add_argument("--engine", default="chromium", choices=["chromium", "print"])
    a = ap.parse_args()

    date_tag = a.date or "20261018"
    model_path = Path(a.model) if a.model else (pc.BATCH / f"_model_{date_tag}_sun_all.txt")
    if not model_path.exists():
        cands = sorted(pc.BATCH.glob(f"_model_{date_tag}*.txt"))
        if not cands:
            raise SystemExit(f"找不到 {date_tag} 的模型文本，用 --model 指定")
        model_path = cands[-1]

    data = pc.build(model_path, date_tag)
    slate = _load_slate(date_tag)
    print(f"数据源 {model_path.name} · 模型 {len(data['matches'])} 场 · 赛程 {len(slate)} 场")

    seed = a.seed if a.seed is not None else random.randrange(1, 10 ** 6)
    pages, assign, meta = build_pages(data, slate, seed=seed,
                                      only=a.only, only_layout=a.only_layout,
                                      one=not a.pool)
    print(f"随机种子 {seed} · 共 {len(pages)} 页（封面 + 总览 + {len(assign)} 场 + 附录）")
    if a.list:
        return

    out = Path(a.out) if a.out else (
        ROOT / "📝文章" / date_tag /
        (f"{date_tag}_{a.only}_单页样例.pdf" if a.only
         else f"{date_tag}_全盘付费资料_{len(assign)}场.pdf"))
    render_pdf(pages, out, f"{date_tag} 全盘付费资料 · 阿飞·赛博聊球", a.engine)


def _load_slate(date_tag: str) -> dict:
    p = pc.STATE / "batch" / "_slate.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    iso = f"{date_tag[:4]}-{date_tag[4:6]}-{date_tag[6:]}"
    out = {}
    for b in d.get("value", {}).get("matchInfoList", []):
        for m in (b.get("subMatchList") or []):
            if m.get("businessDate") and m["businessDate"] != iso:
                continue
            num = m.get("matchNum", 0)
            no = "周日%03d" % (num if num < 1000 else num - 7000)
            out[no] = {
                "matchId": m.get("matchId"), "league": m.get("leagueAbbName", ""),
                "home": m.get("homeTeamAbbName", ""), "away": m.get("awayTeamAbbName", ""),
                "kick": (m.get("matchTime") or "")[:5],
            }
    return out


if __name__ == "__main__":
    main()
