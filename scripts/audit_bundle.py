# -*- coding: utf-8 -*-
"""audit_bundle.py —— 单场端到端审计包（模型/数据/市场/校验/决策/公开稿 六项同源导出）

用法：
    python -X utf8 scripts/audit_bundle.py 20261027            # 默认导出 001、003
    python -X utf8 scripts/audit_bundle.py 20261027 002 007    # 指定场次

产物：state/intel/<day>/_audit_bundle_<num>.md（每场一份）
设计：六项都从同一批落盘文件生成，不手抄；校验项当场重算，不复用报告里的文字。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
DAY = sys.argv[1] if len(sys.argv) > 1 else "20261027"
NUMS = [a for a in sys.argv[2:] if re.fullmatch(r"\d{3}", a)] or ["001", "003"]
INTEL = ROOT / "state" / "intel" / DAY
sys.path.insert(0, str(ROOT / "scripts"))
import model_v3 as mv3  # noqa: E402

books = json.loads((INTEL / f"_books_{DAY}.json").read_text(encoding="utf-8"))
data = json.loads((INTEL / f"_data_{DAY}.json").read_text(encoding="utf-8"))
model = json.loads((INTEL / f"_model_{DAY}.json").read_text(encoding="utf-8"))
audit = json.loads((INTEL / f"_audit_{DAY}.json").read_text(encoding="utf-8"))
rep = ROOT / "📝文章" / DAY / f"{DAY}_周二10场_内部分析报告.md"
rep_text = rep.read_text(encoding="utf-8") if rep.exists() else ""


def f2(x):
    return "—" if x is None else f"{x[0]:.2f} / {x[1]:.2f}"


def pct(x, n=1):
    return "—" if x is None else f"{x * 100:.{n}f}%"


def section(num):
    m = re.search(rf"^### {num} .*?(?=^### |\Z)", rep_text, re.S | re.M)
    return m.group(0) if m else ""


for num in NUMS:
    b = books[num]
    row = data[b["id"]]
    m0 = model[num]
    grade = audit.get(num, {}).get("grade", "A")
    r = mv3.build_single(DAY, num, grade)
    out = [f"# {num} {b['match']}　端到端审计包",
           f"生成：`scripts/audit_bundle.py {DAY} {num}`　模型 {r['model_version']}　数据快照 {r['data_snapshot']}",
           ""]

    # 1 模型输出
    out += ["## 1. 模型输出（可复现）", "",
            f"- 四套 λ：数据 A {f2(r['lam_data'])}；欧赔单腿 {f2(r.get('lam_odds_only'))}；"
            f"大小单腿 {f2(r.get('lam_totals_only'))}；市场联合 {f2(r.get('lam_market_joint'))}；融合 C {f2(r['lam_fused'])}",
            f"- 融合权重：数据侧 {r['w_data']:.2f}（k={r['k']:.0f}，同主客样本 主 {r['n_eff'][0]} / 客 {r['n_eff'][1]}）",
            f"- 数据完整性 **{r['data_grade']}**；预测证据 **{r['evidence_grade']}**",
            f"- 三向：A {pct((r['three_data'] or [None]*3)[0])}/{pct((r['three_data'] or [None,None,None])[1])}/"
            f"{pct((r['three_data'] or [None,None,None])[2])}　市场 {pct(m0['market3'][0])}/{pct(m0['market3'][1])}/{pct(m0['market3'][2])}"
            f"　融合 **{pct(r['three_c'][0])}/{pct(r['three_c'][1])}/{pct(r['three_c'][2])}**",
            f"- Edge(A−市场)：{('—' if not r.get('edge_ab') else '/'.join(f'{x:+.1f}' for x in r['edge_ab']))} pp",
            f"- 主胜区间：融合 λ_C **{r['interval_home'][0]:.0f}–{r['interval_home'][1]:.0f}%**；"
            f"数据 λ_A {r['interval_home_data'][0]:.0f}–{r['interval_home_data'][1]:.0f}%（仅对照）",
            f"- 比分前六（λ_C）：" + "；".join(f"{k} {pct(p)}" for k, p in r["top_scores"][:6]),
            f"- 亚盘 {r['ah']['line']}：EV 主 {r['ah']['ev'][0]:+.1f}% / 客 {r['ah']['ev'][1]:+.1f}%（五状态 "
            + ("—" if not isinstance(r['ah']['dist'], dict) else "/".join(
                f"{k}={pct(v)}" for k, v in r['ah']['dist'].items())) + "）",
            f"- 大小 {r['ou']['line']}：EV 大 {r['ou']['ev'][0]:+.1f}% / 小 {r['ou']['ev'][1]:+.1f}%"
            if r['ou']['line'] is not None else "- 大小：无盘口",
            f"- MC 10 万次：主 {pct(r['mc']['w'])} / 平 {pct(r['mc']['d'])} / 客 {pct(r['mc']['l'])}（与解析解最大偏差 {r['mc_gap']:.2f}pp）",
            ""]

    # 2 数据
    a = audit.get(num, {})
    rh, ra = a.get("recent_home", {}).get("n5", {}), a.get("recent_away", {}).get("n5", {})
    sh, sa = row["season_home"], row["season_away"]

    def rec(d):
        return f"{d.get('w', 0)}胜{d.get('d', 0)}平{d.get('l', 0)}负"

    out += ["## 2. 数据（审计重算，非手抄）", "",
            f"- 全季：主 {sh['total'].get('p')} 场 进 {sh['total'].get('gf')} 失 {sh['total'].get('ga')}；"
            f"客 {sa['total'].get('p')} 场 进 {sa['total'].get('gf')} 失 {sa['total'].get('ga')}",
            f"- 同主客：主 主场 {sh['home'].get('p')} 场 场均 {sh['home'].get('gf', 0) / max(1, sh['home'].get('p', 1)):.2f}/"
            f"{sh['home'].get('ga', 0) / max(1, sh['home'].get('p', 1)):.2f}；"
            f"客 客场 {sa['away'].get('p')} 场 场均 {sa['away'].get('gf', 0) / max(1, sa['away'].get('p', 1)):.2f}/"
            f"{sa['away'].get('ga', 0) / max(1, sa['away'].get('p', 1)):.2f}",
            f"- 近 5 场（审计等级 {a.get('grade', '—')}）：主 {rh.get('gf_pg')}/{rh.get('ga_pg')}（{rec(rh)}）；"
            f"客 {ra.get('gf_pg')}/{ra.get('ga_pg')}（{rec(ra)}）",
            f"- 审计差异（旧报告 → 真值）：{'；'.join(a.get('diffs') or []) or '无'}",
            ]

    # 3 市场
    out += ["## 3. 市场（逐公司 × 三市场原始值，来自 _books）", "",
            "| 公司 | 亚盘 初→即时（主/线/客） | 欧赔 初→即时（主/平/客） | 大小 初→即时（大/线/小） |",
            "|---|---|---|---|"]
    names = []
    for key in ("ah", "ox", "ou"):
        for n in (b.get(key) or {}):
            if n not in names:
                names.append(n)
    def fmt(v):
        if v is None:
            return "—"
        if isinstance(v, dict):
            if "line" in v:
                return f"{v.get('home', 0):.2f}/{v.get('line', 0):+.2f}/{v.get('away', 0):.2f}"
            return "/".join(f"{x:.2f}" for x in v.values() if isinstance(x, (int, float)))
        if isinstance(v, (list, tuple)):
            return "/".join(f"{x:.2f}" for x in v if isinstance(x, (int, float)))
        return str(v)

    for n in names:
        def cell(key):
            blk = (b.get(key) or {}).get(n)
            if not blk:
                return "—"
            return f"{fmt(blk.get('open'))} → {fmt(blk.get('close'))}"
        out.append(f"| {n} | {cell('ah')} | {cell('ox')} | {cell('ou')} |")
    out += ["", f"- 去水三向（{m0.get('books_ox')} 家即时均值）：{pct(m0['market3'][0])}/{pct(m0['market3'][1])}/{pct(m0['market3'][2])}",
            f"- 水位反推总进球：{m0.get('ou_implied_total')}", ""]

    # 4 校验
    lo, hi = r["interval_home"]
    point = r["three_c"][0] * 100
    ref = {k: v * 100 for k, v in r["top_scores"]}
    sec = section(num)
    seen = {}
    dup = []
    for sm in re.finditer(r"(\d-\d)\s*(?:（[^）]*?|\s)\s*(\d+\.\d)%", sec):
        k, v = sm.group(1), float(sm.group(2))
        if k in seen and abs(seen[k] - v) > 0.05:
            dup.append(f"{k}: {seen[k]} vs {v}")
        seen[k] = v
    mism = [f"{k} {v}%≠{ref[k]}%" for k, v in seen.items() if k in ref and abs(ref[k] - v) > 0.05]
    _tb = r.get("three_market") or r.get("three_b")
    avg = ((r["three_data"][0] + _tb[0]) / 2 * 100) if (r.get("three_data") and _tb) else None
    out += ["## 4. 校验（当场重算，不看报告文字）", "",
            f"- C1 同比分唯一概率：{'通过' if not dup else '失败 ' + '；'.join(dup)}",
            f"- C2 点估计落在自身区间：{point:.1f}% ∈ [{lo:.0f}%, {hi:.0f}%] → {'通过' if lo - 1 <= point <= hi + 1 else '失败'}",
            f"- C3 文档比分概率 = λ_C 值：{'通过' if not mism else '失败 ' + '；'.join(mism)}",
            f"- C5 融合≠概率平均：融合 {point:.1f}% vs 平均 {avg:.1f}%（权重 {r['w_data']:.2f}，差 {abs(point - avg):.1f}pp）"
            if avg is not None else "- C5 不适用（无 A 模型）",
            ""]

    # 5 决策
    out += ["## 5. 决策（报告「六、综合分析」原文，与上面同源）", "", "```",
            (re.search(r"\*\*六、综合分析\*\*\n\n(.*?)(?=\n\n\n|\Z)", sec, re.S).group(1).strip()
             if re.search(r"\*\*六、综合分析\*\*\n\n(.*?)(?=\n\n\n|\Z)", sec, re.S) else "（报告里未找到）"),
            "```", ""]

    # 6 公开稿
    out += ["## 6. 公开稿落点", "",
            f"- 报告内出现该场的公开口径句：{'有' if sec else '无'}；公开稿百分数由 `scripts/check_report_consistency.py` C6 回溯校验",
            ""]

    p = INTEL / f"_audit_bundle_{num}.md"
    p.write_text("\n".join(out), encoding="utf-8")
    print("→", p.name, len("\n".join(out)), "chars")
