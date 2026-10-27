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
    C5 融合实现正确性：λ_C == w·λ_A+(1−w)·λ_B，且三向概率能由 λ_C 重算还原
       （诊断项：融合是否恰好等于概率平均——只 WARN，不算错）
    C6 公开稿字段级溯源：每个百分数绑定 match_id/层/指标键/值，语境层不得与数值层冲突
    C7 版本与快照可追溯：内部报告必须带「模型 vX.X」与「快照 <12位hex>」；
       公开稿按 R41/R55 不得暴露内部口径，改为校验「公开数据来源声明 + 快照经
       _claims_<day>.json 绑定」（即通过 C6 的字段级溯源间接可查）
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
def _dirarg(flag):
    if flag in sys.argv:
        return Path(sys.argv[sys.argv.index(flag) + 1]).resolve()
    return None


INTEL = _dirarg("--intel") or ROOT / "state" / "intel" / DAY
ART = _dirarg("--art") or ROOT / "📝文章" / DAY
CLAIMS = INTEL / f"_claims_{DAY}.json"

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
_cands = sorted(ART.glob(f"{DAY}_*内部分析报告.md")) if ART.exists() else []
rp = _cands[0] if _cands else ART / f"{DAY}_内部分析报告.md"
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
    iv = r.get("interval_home")
    tp = r.get("three_c") or r.get("three_fused")
    point = tp[0] * 100 if tp else None
    if iv and point is not None:
        lo, hi = iv
        if not (lo - 1.0 <= point <= hi + 1.0):
            errors.append(f"[C2] {num} 点估计 {point:.1f}% 落在自己区间 {lo:.0f}–{hi:.0f}% 之外")
        # 报告里的区间文字必须与模型一致（不许手写/无源）
        for miv in re.finditer(r"参数区间 (\d+)–(\d+)%", sec):
            a, b = float(miv.group(1)), float(miv.group(2))
            if abs(a - round(lo)) > 0.5 or abs(b - round(hi)) > 0.5:
                errors.append(f"[C2] {num} 报告写区间 {a:.0f}–{b:.0f}%，模型是 {lo:.0f}–{hi:.0f}%")
    elif point is not None and not iv:
        if re.search(r"参数区间 \d+–\d+%", sec):
            errors.append(f"[C2] {num} 无参数区间（w=0），报告却写了区间")
        warns.append(f"[C2] {num} 无参数区间（w=0 或未拟出 λ_A），只能给市场点值，请确认报告里已写明")
    if not re.search(r"模型 v\d+\.\d+", sec):
        errors.append(f"[C4] {num} 表头缺模型版本号")
    if not re.search(r"快照 [0-9a-f]{12}", sec):
        errors.append(f"[C4] {num} 表头缺数据快照标识")
    # C5 融合实现：只验算式，不要求「融合 ≠ 概率平均」（用户 m01870）
    wv = float(r.get("w_data") or 0.0)
    la_ = r.get("lam_data") or r.get("lam_a")
    lb_ = r.get("lam_market_joint") or r.get("lam_market") or r.get("lam_b")
    lc_ = r.get("lam_fused") or r.get("lam_c")
    tc = r.get("three_c") or r.get("three_fused")
    if la_ and lb_ and lc_:
        exp = (wv * la_[0] + (1 - wv) * lb_[0], wv * la_[1] + (1 - wv) * lb_[1])
        if abs(lc_[0] - exp[0]) > 1e-9 or abs(lc_[1] - exp[1]) > 1e-9:
            errors.append(f"[C5] {num} λ_C ≠ w·λ_A+(1−w)·λ_B：{lc_} vs ({exp[0]:.6f}, {exp[1]:.6f})")
        try:
            trip = mv3.three_way((lc_[0], lc_[1]))
        except Exception as exc:  # noqa: BLE001
            trip = None
            errors.append(f"[C5] {num} 三向重算失败：{exc}")
        if trip and tc and max(abs(x - y) for x, y in zip(trip, tc)) > 1e-6:
            errors.append(f"[C5] {num} 三向概率无法由 λ_C 重算还原：表 {tc} vs 重算 {trip}")
        # 诊断：融合恰等于概率平均时只提示（合法，不是错误）
        ta0 = r.get("three_data") or []
        tb0 = r.get("three_b") or r.get("three_market") or []
        if ta0 and tb0 and tc and wv > 0 and abs(ta0[0] - tb0[0]) > 0.10 and abs(wv - 0.5) > 0.15:
            avg = (ta0[0] + tb0[0]) / 2 * 100
            if abs(tc[0] * 100 - avg) < 0.3:
                warns.append(f"[C5] {num} 融合主胜恰等于概率平均 {avg:.1f}%（诊断项，属合法巧合）")

# ---------- 公开稿：字段级溯源（C6/C7，用户 m01870） ----------
LAYERS = {
    "market": ("机构", "定价", "市场", "盘口", "门槛", "盘面"),
    "data": ("我们那本账", "自己那本账", "我们的账", "后台模型", "数据侧", "战绩", "我们给的"),
    "fused": ("合成", "融合", "落在", "落回", "合起来", "最终"),
}
# 子句级线索：命中就不做层校验（比分概率与 EV 天然属 fused 层）
SCORE_HINT = re.compile(r"\d\s*(?:比|-)\s*\d")
EV_HINT = re.compile(r"空间|价可捡|溢")
MC_KEYS = ("w", "d", "l", "ah_win", "ah_push", "ah_loss", "ou_over", "ou_push", "ou_under")


def build_registry():
    """可引用指标表：(场次, 指标键) -> (百分数, 所属层)"""
    reg = {}
    for num, r in V3.items():
        for layer, keys in (("data", ("three_data",)), ("market", ("three_b", "three_market")),
                            ("fused", ("three_c", "three_fused"))):
            vals = next((r[k] for k in keys if r.get(k)), []) or []
            for name, idx in (("home_win", 0), ("draw", 1), ("away_win", 2)):
                if idx < len(vals) and isinstance(vals[idx], (int, float)):
                    reg[(num, f"{layer}.{name}")] = (float(vals[idx]) * 100, layer)
        for sc, pr in r["top_scores"]:
            reg[(num, f"fused.score.{sc}")] = (float(pr) * 100, "fused")
        for tag in ("ah", "ou"):
            blk = r.get(tag) or {}
            dist = blk.get("dist")
            if isinstance(dist, dict):
                for st, x in dist.items():
                    if isinstance(x, (int, float)):
                        reg[(num, f"fused.{tag}.{st}")] = (abs(float(x)) * 100, "fused")
            ev = blk.get("ev") or ()
            for side, x in zip(("home", "away") if tag == "ah" else ("over", "under"), ev):
                if isinstance(x, (int, float)):
                    reg[(num, f"fused.{tag}.ev_{side}")] = (abs(float(x)), "fused")
        mc = r.get("mc") or {}
        for k in MC_KEYS:
            if isinstance(mc.get(k), (int, float)):
                reg[(num, f"mc.{k}")] = (abs(float(mc[k])) * 100, "fused")
        iv = r.get("interval_home")
        if iv:
            reg[(num, "fused.interval_lo")] = (float(iv[0]), "fused")
            reg[(num, "fused.interval_hi")] = (float(iv[1]), "fused")
    return reg


DELIMS = "。！？；，、·\n"


def clause_layers(text, pos):
    """取该百分数所在子句，返回离它最近的层词所属层（等距则并列）。"""
    lo = max(0, pos - 60)
    hi = min(len(text), pos + 60)
    left = max((text.rfind(d, lo, pos) for d in DELIMS), default=-1)
    right = min([x for x in (text.find(d, pos, hi) for d in DELIMS) if x != -1] or [hi])
    clause = text[left + 1:right]
    base = left + 1
    hits = []
    for layer, words in LAYERS.items():
        for w in words:
            st = clause.find(w)
            while st != -1:
                hits.append((abs(base + st + len(w) / 2 - pos), layer))
                st = clause.find(w, st + 1)
    if not hits:
        return []
    hits.sort()
    best = hits[0][0]
    return sorted({ly for d, ly in hits if d - best < 6})


reg = build_registry()
pub = sorted(pp for pp in ART.glob("*.md") if "内部分析报告" not in pp.name)
claims = []
if not rp.exists():
    pass
elif not re.search(r"模型 v\d+\.\d+", text):
    errors.append(f"[C7] {rp.name} 缺模型版本号")
elif not re.search(r"快照 [0-9a-f]{12}", text):
    errors.append(f"[C7] {rp.name} 缺数据快照标识")

for pp in pub:
    t = pp.read_text(encoding="utf-8")
    # 公开稿：R41/R55 禁内部口径 → 只要求公开来源声明；快照通过 _claims 绑定
    if not re.search(r"(公开赛事数据|官方赛程|公开数据)", t):
        errors.append(f"[C7] {pp.name} 缺公开数据来源声明")
    if not pp.name.endswith(".md"):
        continue
    if not CLAIMS.exists():
        errors.append(f"[C7] {pp.name} 无 _claims_{DAY}.json，公开稿百分数不可追溯")
    else:
        cj = json.loads(CLAIMS.read_text(encoding="utf-8"))
        rows = cj if isinstance(cj, list) else (cj.get("claims") or cj.get("items") or [])
        files = {c.get("file") or c.get("article") for c in rows if isinstance(c, dict)}
        files.discard(None)
        if files and not any(pp.name == f or (f and f.endswith(pp.name)) for f in files):
            warns.append(f"[C7] {pp.name} 未出现在 _claims_{DAY}.json 的溯源清单里")
    # 场次锚点：公开稿用队名而不是编号 → 按队名最近出现处定位（用户 m01870 的字段级溯源）
    marks = []
    for n2, bk in books.items():
        mm2 = str(bk.get("match") or "")
        if " vs " not in mm2:
            continue
        for name in mm2.split(" vs ", 1):
            name = name.strip()
            start_league = name.split(" ")[0]
            for hit in re.finditer(re.escape(start_league), t):
                marks.append((hit.start(), n2))
    marks.sort()
    first_head = min([x.start() for x in re.finditer(r"^## ", t, re.M)] or [len(t)])
    for sm in re.finditer(r"(\d+(?:\.\d)?)%", t):
        val = float(sm.group(1))
        num = None
        for pos, n in marks:
            if pos < sm.start():
                num = n
        rec = {
            "article": pp.name,
            "offset": sm.start(),
            "value": val,
            "match_id": num,
            "model_version": (V3.get(num) or {}).get("model_version"),
            "snapshot_id": (V3.get(num) or {}).get("data_snapshot"),
            "candidates": [],
            "implied_layers": [],
            "bound_key": None,
            "status": "ok",
        }
        if not num or num not in V3:
            rec["status"] = "no_match"
            claims.append(rec)
            if sm.start() < first_head:
                rec["status"] = "preamble"
                warns.append(f"[C6] {pp.name} 导语区的 {val}% 无场次锚点（若为汇总口径请人工确认）")
            else:
                errors.append(f"[C6] {pp.name} 的 {val}% 前面找不到任何队名锚点（无法溯源到具体场次）")
            continue
        cands = [(k, v, layer) for (n2, k), (v, layer) in reg.items() if n2 == num and abs(v - val) <= 0.55]
        ctx = t[max(0, sm.start() - 18): sm.start() + 18]
        implied = ["fused"] if SCORE_HINT.search(ctx) else clause_layers(t, sm.start())
        rec["candidates"] = [{"key": k, "value": round(v, 3), "layer": layer} for k, v, layer in cands]
        rec["implied_layers"] = implied
        if not cands:
            rec["status"] = "no_source"
            errors.append(f"[C6] {num} 的 {val}% 在模型数据里没有 ±0.55pp 内的任何指标（无出处）")
        else:
            in_layer = [c for c in cands if c[2] in implied] if implied else cands
            if implied and not in_layer:
                rec["status"] = "layer_mismatch"
                errors.append(
                    f"[C6] {num} 的 {val}% 语境指向 {'/'.join(implied)} 层，但只有 "
                    f"{'/'.join(sorted({c[2] for c in cands}))} 层有同值指标（数字真、层引错）")
            else:
                pick = (in_layer or cands)[0]
                rec["bound_key"] = pick[0]
                if len({c[2] for c in (in_layer or cands)}) > 1:
                    rec["status"] = "ambiguous"
                    warns.append(f"[C6] {num} 的 {val}% 同时能对上多层："
                                 f"{sorted({c[2] for c in (in_layer or cands)})}（语境可再明确）")
        claims.append(rec)

out_claims = INTEL / f"_claims_{DAY}.json"
try:
    out_claims.write_text(json.dumps(claims, ensure_ascii=False, indent=1), encoding="utf-8", newline="")
except Exception as exc:  # noqa: BLE001
    warns.append(f"[C6] 溯源表写盘失败：{exc}")

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
