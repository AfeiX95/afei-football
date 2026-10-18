#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""当日赛程全盘分析报告（内部汇总）

把模型（λ 双法 / Dixon-Coles / 三档比分 / 信心 / 冷门指数）与盘口情报
（`state/intel/<date>/_intel_<date>.json` 五套盘去水 + 位移 + 跨盘一致性）
合成一份逐场带点评的报告。

用法：
    python -X utf8 scripts/slate_report.py --date 20261018
    python -X utf8 scripts/slate_report.py --date 20261018 --out 某路径.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import paid_cyber as pc  # noqa: E402
import paid_pdf as pp  # noqa: E402  复用版面层写好的研判文字（market_read / tactic_read / summary_read）

DIRS = ["主胜", "平", "客胜"]

_WD = "一二三四五六日"


def no_of(num: int) -> str:
    """matchNum → 竞彩编号。周一=1001…周日=7025，千位就是星期，后三位是场次号。"""
    n = int(num or 0)
    d = n // 1000
    return "周%s%03d" % (_WD[d - 1] if 1 <= d <= 7 else "日", n % 1000)




def f(x, n: int = 1) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return "—"


def strip_html(html: str) -> list[str]:
    """把 helper 吐出来的 <p>…</p> 拆成 markdown 段。"""
    if not html:
        return []
    parts = re.split(r"</p>", html)
    out = []
    for p in parts:
        s = re.sub(r"<[^>]+>", "", p).strip()
        if s:
            out.append(s)
    return out


def load_intel(date_tag: str) -> dict:
    p = STATE / "intel" / date_tag / f"_intel_{date_tag}.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text(encoding="utf-8"))
    return {m["no"]: m for m in (d.get("matches") or [])}


def slate_of(date_tag: str) -> dict:
    p = STATE / "batch" / "_slate.json"
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
            out[no_of(num)] = {
                "matchId": str(m.get("matchId")), "league": m.get("leagueAbbName", ""),
                "home": m.get("homeTeamAbbName", ""), "away": m.get("awayTeamAbbName", ""),
                "kick": (m.get("matchTime") or "")[:5],
            }
    return out


def mk_line(it: dict) -> str:
    """盘口面一行：定价三格去水 / 让球 / 大小球 / 返还率。"""
    mk = (it or {}).get("markets") or {}
    had, hh, ttg = mk.get("had"), mk.get("hhad"), mk.get("ttg")
    bits = []
    if had:
        bits.append("胜平负 " + " / ".join(f(o, 2) for o in had["odds"])
                    + "（去水 " + " / ".join(f"{x:.1f}%" for x in had["p"]) + "）")
    else:
        bits.append("胜平负未开售")
    if hh:
        bits.append(f"让球 {hh['line']} " + " / ".join(f(o, 2) for o in hh["odds"]))
    if ttg:
        big = sum(ttg["p"][3:])
        exp = sum(k * v / 100.0 for k, v in enumerate(ttg["p"]))
        bits.append(f"总进球盘隐含 {f(exp, 2)} 球、3 球以上 {big:.1f}%")
    if had:
        bits.append(f"返还率 {f(had['payout'], 2)}%")
    return join_zh(bits)


def mv_line(it: dict) -> str:
    mv = (it or {}).get("move") or []
    keep = [x for x in mv if "总进球" not in x]
    return join_zh([re.sub(r"[（(]\d+ 次[^）)]*[）)]", "", x) for x in keep])


def cross_line(it: dict) -> str:
    xs = ((it or {}).get("cross") or []) + ((it or {}).get("hot") or [])
    return join_zh(xs)


def team_line(it: dict) -> str:
    inf = (it or {}).get("intel") or {}
    hf, af = inf.get("home_form") or {}, inf.get("away_form") or {}
    meet = inf.get("meetings") or {}
    inj = inf.get("injuries") or []
    seen, uniq = set(), []
    for p_ in inj:
        nm = (p_.get("name") or "").strip()
        if nm and nm not in seen:
            seen.add(nm)
            uniq.append(p_)
    bits = []
    if hf.get("n") or af.get("n"):
        bits.append(f"近期 主 {hf.get('n', 0)} 场 {f(hf.get('gf_avg'), 2)}进{f(hf.get('ga_avg'), 2)}失 / "
                    f"客 {af.get('n', 0)} 场 {f(af.get('gf_avg'), 2)}进{f(af.get('ga_avg'), 2)}失")
    if meet.get("n"):
        bits.append(f"交锋 {meet['n']} 场 场均 {f(meet.get('avg_total'), 2)} 球、"
                    f"低比分 {f(meet.get('low2'), 0)}%、平局 {f(meet.get('draw'), 0)}%")
    bits.append(f"伤停 {len(uniq)} 人")
    return join_zh(bits)


def _line_prose(gl: int) -> str:
    """把让球线翻译成人话，内部报告可以直接这么写（R41 只约束公开稿）。"""
    if gl > 0:
        return f"主队受让 {gl} 球"
    if gl < 0:
        return f"主队让 {-gl} 球"
    return "平手盘"


def join_zh(items: list[str]) -> str:
    """把若干整句串成一行：去掉句末标点，用「；」连接，末尾补「。」"""
    out = []
    for s in items:
        s = (s or "").strip().rstrip("。；;，,")
        if s:
            out.append(s)
    return "；".join(out) + "。" if out else ""



def _wd_of(date_tag: str) -> str:
    """按排期给个星期标签，用 slate 里的编号前缀（周一=1001…周日=7025）。"""
    import json as _json
    sp = STATE / "batch" / "_slate.json"
    iso = f"{date_tag[:4]}-{date_tag[4:6]}-{date_tag[6:]}"
    try:
        d = _json.loads(sp.read_text(encoding="utf-8"))
        for b in d.get("value", {}).get("matchInfoList", []):
            for m in (b.get("subMatchList") or []):
                if m.get("businessDate") == iso:
                    return no_of(int(m.get("matchNum") or 7))[:2]
    except Exception:
        pass
    return "周日"


def build(date_tag: str) -> str:
    slate = slate_of(date_tag)
    intel = load_intel(date_tag)
    model_path = STATE / "batch" / f"_model_{date_tag}_sun_all.txt"
    if not model_path.exists():
        cands = sorted((STATE / "batch").glob(f"_model_{date_tag}*.txt"))
        if not cands:
            raise SystemExit(f"找不到 {date_tag} 的模型文本")
        model_path = cands[-1]
    data = pc.build(model_path, date_tag)
    ms = {m["no"]: m for m in data["matches"]}

    order = sorted(slate.keys())
    wd = order[0][:2] if order else "周日"
    WD_LABEL = wd
    have_model = sum(1 for no in order if no in ms)
    L = []
    L.append(f"# {date_tag[:4]}-{date_tag[4:6]}-{date_tag[6:]} {WD_LABEL} 全盘分析报告")
    L.append("")
    L.append(f"- 场次：**{len(order)} 场**（有模型 {have_model} 场，"
             f"无模型 {len(order) - have_model} 场）")
    mv_name = data["meta"].get("model", "")
    ver = f"（{mv_name}）" if mv_name and mv_name != model_path.name else ""
    L.append(f"- 数据源：模型 `{model_path.name}`{ver}"
             f" + 盘口情报 `state/intel/{date_tag}/_intel_{date_tag}.md`")
    L.append("- 口径：**只统计 90 分钟常规时间**，加时与点球不计入任何一格")
    L.append("- 性质：内部研判汇总，含盘口读数；公开稿按 R41 换成非盘口语，不直接外发")
    L.append("")
    L.append("**缺源声明**：联赛排名与战意（积分榜接口返回空壳）、xG / xGA / npxG、PPDA、"
             "定位球 xG、裁判尺度、天气与场地、轮换与欧战赛程——本期均无数据源，一律不赋值。")
    L.append("")

    # 总览表
    L.append("## 一、全盘总览")
    L.append("")
    L.append("| # | 场次 | 联赛 | 开赛 | 定价去水（主/平/客） | 模型（主/平/客） | 最大偏差 | 信心 | 首选比分 |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for i, no in enumerate(order, 1):
        s = slate[no]
        m = ms.get(no)
        it = intel.get(no) or {}
        had = ((it.get("markets") or {}).get("had")) or {}
        mk = " / ".join(f"{x:.1f}%" for x in had["p"]) if had else "未开售"
        if m:
            L.append(f"| {i:02d} | {no} {s['home']} vs {s['away']} | {s['league']} | {s['kick']} | "
                     f"{mk} | " + " / ".join(f"{x:.1f}%" for x in m["p"])
                     + f" | {pc_sg(pp.maxpp(m))}pp | {f((m.get('conf') or {}).get('total'), 0)} | "
                     f"{(m.get('verdict') or {}).get('first_score') or '—'} |")
        else:
            L.append(f"| {i:02d} | {no} {s['home']} vs {s['away']} | {s['league']} | {s['kick']} | "
                     f"{mk} | 无胜平负固定奖金 · 模型跳过 | — | — | — |")
    L.append("")

    # 逐场
    L.append("## 二、逐场预测与点评")
    L.append("")
    for no in order:
        s = slate[no]
        m = ms.get(no)
        it = intel.get(no) or {}
        L.append(f"### {no} {s['league']} {s['home']} vs {s['away']}　{s['kick']} 开赛")
        L.append("")
        if not m:
            L.append("**预测**：本场没有胜平负固定奖金（未开售或已封盘），模型按纪律跳过 —— "
                     "不出入球期望、不出胜平负概率、不出比分矩阵，**不拿估算值冒充模型读数**。")
            L.append("")
            L.append(f"**盘口**：{mk_line(it) or '无盘口快照'}")
            L.append(f"**球队**：{team_line(it)}")
            L.append("")
            mk0 = (it.get("markets") or {})
            hh0, ttg0 = mk0.get("hhad") or {}, mk0.get("ttg") or {}
            meet0 = ((it.get("intel") or {}).get("meetings") or {})
            bits = []
            if hh0.get("line"):
                try:
                    gl = int(hh0["line"])
                except (TypeError, ValueError):
                    gl = None
                if gl is not None:
                    bits.append(f"让球开到 {hh0['line']}（{_line_prose(gl)}）")
            if ttg0.get("p"):
                exp0 = sum(k * v / 100.0 for k, v in enumerate(ttg0["p"]))
                bits.append(f"总进球盘隐含 {f(exp0, 2)} 球、3 球以上 "
                            f"{sum(ttg0['p'][3:]):.1f}%")
            if meet0.get("n"):
                bits.append(f"而两队 {meet0['n']} 场交锋场均只有 {f(meet0.get('avg_total'), 2)} 球、"
                            f"低比分占 {f(meet0.get('low2'), 0)}%")
            tail = ""
            if ttg0.get("p") and meet0.get("n") and (meet0.get("low2") or 0) >= 60:
                tail = ("——盘口把总分顶得高，历史交锋却偏低比分，两者对不上；"
                        "这种时候别顺着总分预期走，先看这场的进球到底从哪来。")
            L.append("**点评**：这场只能做球队面判断，不能做概率判断。开售后用 "
                     f"`python scripts/model.py {no}` 单独补算，补算完这一节要重写。"
                     + ("目前盘口面能读出的是：" + "；".join(bits) + tail if bits else ""))
            L.append("")
            continue
        v = m.get("verdict") or {}
        conf = m.get("conf") or {}
        lam = m.get("lam") or {}
        L.append(f"**预测**：首选 **{v.get('first')}** {f(v.get('first_p'))}% · {v.get('first_score')}"
                 f"　｜　次选 {v.get('second')} {f(v.get('second_p'))}% · {v.get('second_score')}"
                 f"　｜　防范 {v.get('guard')} {f(v.get('guard_p'))}% · {v.get('guard_score')}")
        L.append("")
        L.append(f"**盘口**：{mk_line(it)}")
        L.append("")
        L.append(f"**模型**：λ 主 {f((lam.get('l1') or [0, 0])[0], 2)} / "
                 f"客 {f((lam.get('l1') or [0, 0])[1], 2)}（实际数据法）；"
                 f"反推 {f((lam.get('l2') or [0, 0])[0], 2)} / {f((lam.get('l2') or [0, 0])[1], 2)}；"
                 f"综合 {f((lam.get('fin') or [0, 0])[0], 2)} + {f((lam.get('fin') or [0, 0])[1], 2)} "
                 f"= {f(lam.get('total'), 2)}；信心 {f(conf.get('total'), 0)}/100（{conf.get('grade') or '—'}）")
        L.append("")
        cl = cross_line(it)
        if cl:
            L.append(f"**盘口结构**：{cl}")
            L.append("")
        mv = mv_line(it)
        if mv:
            L.append(f"**位移**：{mv}")
            L.append("")
        L.append(f"**球队**：{team_line(it)}")
        L.append("")
        mk_ps = strip_html(pp.market_read(m))
        tc_ps = strip_html(pp.tactic_read(m))
        sm_ps = strip_html(pp.summary_read(m))
        L.append("**盘口解读**：" + join_zh(mk_ps))
        L.append("")
        L.append("**战术与走向**：" + join_zh(tc_ps))
        L.append("")
        if sm_ps:
            L.append("**风险与收口**：" + join_zh(sm_ps))
            L.append("")

    # ── 本批共性（自动汇总，全部由上面算出来的数产出）
    from collections import Counter

    have = [ms[no] for no in order if no in ms]
    L.append("---")
    L.append("")
    L.append("## 三、本批共性（自动汇总）")
    L.append("")
    if have:
        dirs = Counter((m.get("verdict") or {}).get("first") or "—" for m in have)
        score = Counter((m.get("verdict") or {}).get("first_score") or "—" for m in have)
        confs = [((m.get("conf") or {}).get("total") or 0) for m in have]
        devs = sorted(have, key=lambda m: -abs(pp.maxpp(m)))
        L.append(f"- **首选方向分布**：" + "、".join(f"{k} {v} 场" for k, v in dirs.most_common()))
        top2 = score.most_common(2)
        L.append(f"- **首选比分的集中度**：" + "、".join(f"{k} 出现 {v} 次" for k, v in top2)
                 + f"——{len(have)} 场里有 {sum(v for _, v in top2)} 场的首选比分落在这两格，"
                 "说明比分是概率网格的产物、彼此高度相似，**不能当成 24 个独立判断**。")
        L.append(f"- **信心分布**：最高 {max(confs):.0f}、最低 {min(confs):.0f}、"
                 f"中位 {sorted(confs)[len(confs) // 2]:.0f}；"
                 f"A 档 {sum(1 for c in confs if c >= 78)} 场、"
                 f"B 档 {sum(1 for c in confs if 66 <= c < 78)} 场、"
                 f"C 档 {sum(1 for c in confs if 52 <= c < 66)} 场、"
                 f"D 档 {sum(1 for c in confs if c < 52)} 场。")
        L.append("- **分歧最大的五场**（偏差越大越要按「只当方向参考」处理）：" + "；".join(
            f"{m['no']} {m['home']}vs{m['away']} {pp.maxpp(m):+.1f}pp" for m in devs[:5]) + "。")
        # 盘口自洽率
        ok = bad = 0
        for no in order:
            xs = ((intel.get(no) or {}).get("cross") or [])
            for x in xs:
                if "实测差" in x:
                    num = re.search(r"实测差 (-?\d+\.\d+)pp", x)
                    if num:
                        if abs(float(num.group(1))) <= 2.5:
                            ok += 1
                        else:
                            bad += 1
        if ok + bad:
            L.append(f"- **让球盘与不让球盘的自洽率**：{ok} 组对得上、{bad} 组对不上"
                     "（阈值 ±2.5pp）；对不上的场次两套盘不能当同一件事读。")
        mv_big = []
        for no in order:
            xs = ((intel.get(no) or {}).get("move") or [])
            for x in xs:
                if "位移" in x and "胜平负" in x:
                    nums = re.findall(r"([+\-]\d+\.\d)pp", x)
                    if nums:
                        mv_big.append((no, no and slate[no]["home"], max(abs(float(v)) for v in nums)))
        mv_big.sort(key=lambda x: -x[2])
        if mv_big:
            L.append("- **胜平负位移最大的三场**：" + "；".join(
                f"{a} 最大 {c:.1f}pp" for a, _, c in mv_big[:3])
                + "。位移只说明定价动过，不解释动的理由。")
    # 偏差体检：≥15pp 的场次逐场看「模型看高的是哪一格，那一方近期什么样」
    bigs = [m for m in have if abs(pp.maxpp(m)) >= 15]
    if bigs:
        L.append("- **偏差体检（≥15pp，逐场看模型看高哪一格）**：")
        L.append("")
        for m in sorted(bigs, key=lambda x: -abs(pp.maxpp(x))):
            d = pp.maxpp(m)
            i = max(range(3), key=lambda k: (m["p"][k] - m["mk"][k]))
            _tech = m.get("tech") or {}
            form = (_tech.get("home") or {}, _tech.get("away") or {})
            mine = form[0] if DIRS[i] == "主胜" else form[1] if DIRS[i] == "客胜" else ({}, {})
            other = form[1] if DIRS[i] == "主胜" else form[0] if DIRS[i] == "客胜" else ({}, {})
            L.append(f"  - {m['no']} {m['home']} vs {m['away']}：模型看高 **{DIRS[i]}** "
                     f"（模型 {f(m['p'][i])}% vs 定价 {f(m['mk'][i])}%，差 {d:+.1f}pp）；"
                     f"该方近期 {f(mine.get('gf_avg'), 2)}进{f(mine.get('ga_avg'), 2)}失，"
                     f"对面 {f(other.get('gf_avg'), 2)}进{f(other.get('ga_avg'), 2)}失。"
                     if DIRS[i] != "平" else
                     f"  - {m['no']} {m['home']} vs {m['away']}：模型看高 **平**（差 {d:+.1f}pp）。")
        L.append("")
        n_away = sum(1 for m in bigs if DIRS[max(range(3), key=lambda k: m["p"][k] - m["mk"][k])] == "客胜")
        L.append(f"  - **本批 {len(bigs)} 场大偏差里，模型看高客胜的有 {n_away} 场**。"
                 "模型只吃「近期进失 + 同主客战绩 + 交锋 + 伤停」，**不看阵容档次与身价**，"
                 "所以遇到「强队近期状态差」的场子，它一定往状态好的那一边压，"
                 "而定价压的是球队本身的实力基线。这类偏差不代表模型发现了好东西，"
                 "大概率是方法学缺口的同一副面孔（重读 open_items 里「后台模型方法学缺口」那条）。")
        L.append("")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 四、使用说明")
    L.append("")
    L.append("1. 首选 / 次选 / 防范是**概率序**：首选是模型概率最高的方向，次选是第二高，"
             "防范是「方向反过来时最可能的退路」。三档比分互不重复、方向与标签一致。")
    L.append("2. 最大偏差 ≥15pp 标红格：按纪律先假定我方样本有缺口，**只当方向参考、不当结论**；"
             "6–15pp 方向可信、幅度打折；<6pp 两边结构基本重合，没有可做的差价。")
    L.append("3. 盘口位移只说明「定价动过」，**不能说明「为什么动」**——本报告不写资金流向这类推断。")
    L.append("4. 让球盘与不让球盘对不上（差 >2.5pp）时，两套盘不要当同一件事读，取更保守的一侧。")
    L.append("5. 缺源项一律留空，不写「待补 / 查不到 / 不编造」。")
    L.append("")
    return "\n".join(L)


def pc_sg(x) -> str:
    if x is None:
        return "—"
    return f"{x:+.1f}"


def main() -> None:
    ap = argparse.ArgumentParser(description="当日赛程全盘分析报告")
    ap.add_argument("--date", default="20261018")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    md = build(a.date)
    out = Path(a.out) if a.out else (ROOT / "📝文章" / a.date / f"{a.date}_{_wd_of(a.date)}全盘分析报告.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"✅ {out}  {len(md)} 字符 / {md.count(chr(10)) + 1} 行")


if __name__ == "__main__":
    main()
