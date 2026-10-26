# -*- coding: utf-8 -*-
"""check_report_consistency.py —— 报告与公开稿的一致性硬验收（评审 P0-3/P0-5/P0-6 落地）

用法：
    python -X utf8 scripts/check_report_consistency.py 20261027
    python -X utf8 scripts/check_report_consistency.py 20261027 --strict   # 任何 WARN 也算失败

检查项（全部可机器判、不靠人眼）：
    C1 同一场内，同一个比分只能出现一个概率（表与「六、综合分析」必须一致）
    C2 出结论用的点估计必须落在它自己的 5%–95% 区间内（点估计与区间同源）
    C3 文档里每个「比分 + 概率」必须能在 _model_v3 的 top_scores 里找到出处
    C4 每场表头必须带「模型 vX.X」与「快照 <12位hex>」
    C5 融合概率不得等于「A 与市场」的概率平均（防悄悄改成概率层加权）
    C6 公开稿里每个百分数必须能在 _model_v3 / _model 的字段里找到出处（容差 1pp）
    C7 公开稿必须带模型版本与数据快照标识
退出码：0 全过；1 有 ERROR；2 只有 WARN 且 --strict。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]

DAY = sys.argv[1] if len(sys.argv) > 1 else "20261027"
STRICT = "--strict" in sys.argv
INTEL = ROOT / "state" / "intel" / DAY
ART = ROOT / "📝文章" / DAY

errors: list[str] = []
warns: list[str] = []


def load(name):
    p = INTEL / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


model = load(f"_model_{DAY}.json")
books = load(f"_books_{DAY}.json")

sys.path.insert(0, str(ROOT / "scripts"))
import model_v3 as mv3  # noqa: E402

audit = load(f"_audit_{DAY}.json")
V3 = {n: mv3.build_single(DAY, n, audit.get(n, {}).get("grade", "A")) for n in books}

# ---------- 报告 ----------
rp = ART / f"{DAY}_周二10场_内部分析报告.md"
if not rp.exists():
    errors.append(f"报告缺失：{rp}")
    text = ""
else:
    text = rp.read_text(encoding="utf-8")

sections = re.split(r"^### ", text, flags=re.M)[1:] if text else []
SCORE_RE = re.compile(r"(\d-\d)\s*(?:（[^）]*?|\s)\s*(\d+\.\d)%")

for sec in sections:
    m = re.match(r"(\d{3})", sec)
    if not m:
        continue
    num = m.group(1)
    r = V3.get(num)
    if not r:
        errors.append(f"[C1] {num} 在 _model_v3 里没有对应记录")
        continue
    seen: dict[str, float] = {}
    for sm in SCORE_RE.finditer(sec):
        score, val = sm.group(1), float(sm.group(2))
        if score in seen and abs(seen[score] - val) > 0.05:
            errors.append(f"[C1] {num} 比分 {score} 出现两个概率：{seen[score]}% vs {val}%")
        seen[score] = val
        ref = {k: v * 100 for k, v in r["top_scores"]}
        if score in ref and abs(ref[score] - val) > 0.05:
            errors.append(f"[C3] {num} 比分 {score} 写 {val}%，_model_v3 里是 {ref[score]}%")
        if score not in ref:
            warns.append(f"[C3] {num} 比分 {score} 不在 λ_C 前八里（可能是作者倾向，请标注）")
    lo, hi = r["interval_home"]
    point = r["three_c"][0] * 100
    if not (lo - 1.0 <= point <= hi + 1.0):
        errors.append(f"[C2] {num} 点估计 {point:.1f}% 落在自己区间 {lo:.0f}–{hi:.0f}% 之外")
    if not re.search(r"模型 v\d+\.\d+", sec):
        errors.append(f"[C4] {num} 表头缺模型版本号")
    if not re.search(r"快照 [0-9a-f]{12}", sec):
        errors.append(f"[C4] {num} 表头缺数据快照标识")
    ta, tb, tc = r["three_data"], (r.get("three_market") or r.get("three_b")), (r.get("three_fused") or r.get("three_c"))
    if ta and tb and r["w_data"] > 0:
        avg = (ta[0] + tb[0]) / 2 * 100
        far_weight = abs(r["w_data"] - 0.5) > 0.15
        far_prob = abs(ta[0] - tb[0]) > 0.10
        if far_weight and far_prob and abs(tc[0] * 100 - avg) < 0.3:
            errors.append(f"[C5] {num} 融合主胜 {tc[0]*100:.1f}% 等于概率平均 {avg:.1f}%"
                          f"（权重 {r['w_data']:.2f}、A 与市场差 {abs(ta[0]-tb[0])*100:.0f}pp），疑似写成概率层加权")

# ---------- 公开稿 ----------
# 允许出现的百分数集合：来自模型 json 的所有概率字段（四舍五入到 1pp 容差）
allowed: list[float] = []
for num, r in V3.items():
    for key in ("three_data", "three_market", "three_fused"):
        for x in (r.get(key) or []):
            if not isinstance(x, (int, float)):
                continue
            allowed.append(x * 100)
    for _k, p in r["top_scores"]:
        allowed.append(p * 100)
    for key in ("ah", "ou"):
        blk = r.get(key) or {}
        for x in (blk.get("ev") or ()):
            if x is not None:
                allowed.append(abs(x))
        for x in (blk.get("dist") or ()):
            allowed.append(x * 100)
    allowed.extend(r["interval_home"])
    allowed.extend(r["interval_home_data"])
    mc = r.get("mc") or {}
    for key in ("w", "d", "l", "ah_win", "ah_push", "ah_loss", "ou_over", "ou_push", "ou_under"):
        if isinstance(mc.get(key), (int, float)):
            allowed.append(float(mc[key]) * 100)
    m0 = model.get(num) or {}
    for key in ("market3", "market3_raw"):
        for x in (m0.get(key) or []):
            allowed.append(x * 100)

allowed_sorted = sorted(x for x in allowed if isinstance(x, (int, float)))


def covered(p: float) -> bool:
    return any(abs(a - p) <= 1.0 for a in allowed_sorted)


pub = sorted(p for p in ART.glob("*.md") if "内部分析报告" not in p.name)
for p in pub:
    t = p.read_text(encoding="utf-8")
    if not re.search(r"模型 v\d+\.\d+", t):
        errors.append(f"[C7] {p.name} 缺模型版本号")
    if not re.search(r"快照 [0-9a-f]{12}", t):
        errors.append(f"[C7] {p.name} 缺数据快照标识")
    for sm in re.finditer(r"(\d+(?:\.\d)?)%", t):
        val = float(sm.group(1))
        if not covered(val):
            errors.append(f"[C6] {p.name} 的 {val}% 在模型数据里找不到出处（±1pp）")

# ---------- 输出 ----------
print(f"检查日：{DAY}　报告 {len(sections)} 场　公开稿 {len(pub)} 篇")
for w in warns:
    print("WARN  " + w)
for e in errors:
    print("ERROR " + e)
if not errors and not warns:
    print("全部通过：C1–C7 无异常")
if errors:
    sys.exit(1)
if warns and STRICT:
    sys.exit(2)
print(f"结论：ERROR {len(errors)} / WARN {len(warns)}")
