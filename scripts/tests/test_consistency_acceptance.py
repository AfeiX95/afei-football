# -*- coding: utf-8 -*-
"""验收硬约束的回归测试（用户 m01663/m01870 的「自动验收 + 负样本」要求）。

跑法：python -X utf8 -m pytest scripts/tests/test_consistency_acceptance.py -q

覆盖：
  C1 同场同比分只有一个概率
  C2 点估计落在自己的参数区间内；w=0 时不得伪造区间
  C3 文档比分概率 == λ_C top_scores
  C4 表头带模型版本 + 数据快照
  C5 融合「算式正确」：λ_C 恰好等于 w·λ_A+(1−w)·λ_B，且三向能由 λ_C 重算；边界 w=0/w=1/λ_A=λ_B
  C6 公开稿字段级溯源：claims 表里不得有 no_source / layer_mismatch
  C7 公开稿带版本与快照
  负样本：往副本里注入「层引错」「比分概率造假」「报告数字篡改」，检查器必须报错
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DAY = "20261027"
INTEL = ROOT / "state" / "intel" / DAY
ART = ROOT / "📝文章" / DAY
sys.path.insert(0, str(ROOT / "scripts"))

import model_v3 as mv3  # noqa: E402

BOOKS = json.loads((INTEL / f"_books_{DAY}.json").read_text(encoding="utf-8"))
MODEL = json.loads((INTEL / f"_model_{DAY}.json").read_text(encoding="utf-8"))
AUDIT = json.loads((INTEL / f"_audit_{DAY}.json").read_text(encoding="utf-8"))
REPORT = (ART / f"{DAY}_周二10场_内部分析报告.md").read_text(encoding="utf-8")
SECS = {m.group(1): m.group(0) for m in re.finditer(r"^### (\d{3}) .*?(?=^### |\Z)", REPORT, re.S | re.M)}
V3 = {n: mv3.build_single(DAY, n, AUDIT.get(n, {}).get("grade", "A")) for n in BOOKS}


def _three_c(r):
    return r.get("three_c") or r.get("three_fused")


def test_report_covers_all_matches():
    assert set(SECS) == set(BOOKS)


@pytest.mark.parametrize("num", sorted(BOOKS))
def test_same_score_never_has_two_probabilities(num):
    """C1：同场同比分只能一个概率（表与结论必须同源）"""
    seen: dict[str, float] = {}
    for m in re.finditer(r"(\d-\d)\s*(?:（[^）]*?|\s)\s*(\d+\.\d)%", SECS[num]):
        k, v = m.group(1), float(m.group(2))
        if k in seen:
            assert abs(seen[k] - v) <= 0.05, f"{num} {k}: {seen[k]}% vs {v}%"
        seen[k] = v


@pytest.mark.parametrize("num", sorted(BOOKS))
def test_point_estimate_inside_its_own_interval(num):
    """C2：点估计必须落在自己的参数区间内；w=0 场均无区间，且点值等于市场"""
    r = V3[num]
    point = _three_c(r)[0] * 100
    iv = r.get("interval_home")
    if not iv:
        assert r["w_data"] == 0, f"{num} 有权重却没有区间"
        lb = r["lam_market_joint"]
        ref = mv3.three_way((lb[0], lb[1]))[0] * 100
        assert abs(point - ref) < 1e-8, f"{num} w=0 时点估计应等于市场联合拟合 λ_B 的三向"
        return
    lo, hi = iv
    assert lo - 1.0 <= point <= hi + 1.0, f"{num} 点 {point:.1f}% ∉ [{lo:.0f}, {hi:.0f}]"
    assert hi > lo, f"{num} 区间宽度为 0"


@pytest.mark.parametrize("num", sorted(BOOKS))
def test_score_probabilities_match_model(num):
    """C3：文档里的比分概率必须等于 λ_C 的 top_scores"""
    ref = {k: round(v * 100, 1) for k, v in V3[num]["top_scores"]}
    for m in re.finditer(r"(\d-\d)\s*（[^）]*?(\d+\.\d)%", SECS[num]):
        k, v = m.group(1), float(m.group(2))
        if k in ref:
            assert abs(ref[k] - v) <= 0.05, f"{num} {k}: 文档 {v}% vs 模型 {ref[k]}%"


@pytest.mark.parametrize("num", sorted(BOOKS))
def test_section_header_has_version_and_snapshot(num):
    """C4：每场表头必须带模型版本与数据快照"""
    assert re.search(r"模型 v\d+\.\d+", SECS[num])
    assert re.search(r"快照 [0-9a-f]{12}", SECS[num])


@pytest.mark.parametrize("num", sorted(BOOKS))
def test_fusion_formula_is_exact(num):
    """C5：λ_C == w·λ_A+(1−w)·λ_B（1e-10），且三向能由 λ_C 重算（1e-8）"""
    r = V3[num]
    la, lb, lc, w = r["lam_data"], r["lam_market_joint"], r["lam_fused"], r["w_data"]
    if la is None:
        assert abs(w) < 1e-12 and abs(lc[0] - lb[0]) < 1e-12, f"{num} 无 λ_A 时应完全等于市场"
        return
    for i in (0, 1):
        exp = w * la[i] + (1 - w) * lb[i]
        assert abs(lc[i] - exp) < 1e-10, f"{num} λ_C[{i}] {lc[i]} ≠ {exp}"
    trip = mv3.three_way((lc[0], lc[1]))
    for a, b in zip(trip, _three_c(r)):
        assert abs(a - b) < 1e-8, f"{num} 三向重算不一致：{a} vs {b}"


def test_fuse_boundaries():
    """C5 边界：w=0 → λ_B；w=1 → λ_A；λ_A=λ_B → 两者相同"""
    la, lb = (1.6, 1.1), (1.2, 1.4)
    for grade, n in (("A", (10, 10)), ("B", (3, 4)), ("C", (1, 1))):
        lam, w = mv3.fuse(la, lb, grade, n)
        assert 0.0 < w <= 1.0
        for i in (0, 1):
            assert abs(lam[i] - (w * la[i] + (1 - w) * lb[i])) < 1e-12
    # 边界一：没有 λ_A → w=0，结果必须完全等于市场
    assert mv3.fuse(None, lb, "A", None) == (lb, 0.0)
    # 边界二：没有 λ_B → w=1，结果必须完全等于模型
    assert mv3.fuse(la, None, "A", (10, 10)) == (la, 1.0)
    # 边界三：λ_A == λ_B → 融合等于两者（与权重无关）
    assert mv3.fuse((1.3, 1.2), (1.3, 1.2), "A", (10, 10))[0] == (1.3, 1.2)
    same = mv3.fuse((1.3, 1.2), (1.3, 1.2), "A", (10, 10))[0]
    assert same == (1.3, 1.2), "λ_A=λ_B 时融合必须等于两者"


def test_public_claims_have_binding():
    """C6：公开稿字段级溯源表必须存在，且没有 no_source / layer_mismatch"""
    cp = INTEL / f"_claims_{DAY}.json"
    assert cp.exists(), "缺溯源表：先跑 python -X utf8 scripts/check_report_consistency.py"
    claims = json.loads(cp.read_text(encoding="utf-8"))
    assert claims
    bad = [c for c in claims if c["status"] in ("no_source", "layer_mismatch", "no_match")]
    assert not bad, "存在无出处或层引错的数字：" + "；".join(
        f"{c['match_id']} {c['value']}% {c['status']}" for c in bad[:5])
    for c in claims:
        if c["status"] in ("ok", "ambiguous"):
            assert c["bound_key"], f"{c['match_id']} {c['value']}% 未绑定指标键"
            assert c["model_version"] and c["snapshot_id"], "溯源缺版本号或快照"


def test_public_articles_carry_version_and_snapshot():
    """C7：公开稿必须带模型版本与数据快照"""
    pubs = [p for p in ART.glob("*.md") if "内部分析报告" not in p.name]
    assert pubs
    for p in pubs:
        t = p.read_text(encoding="utf-8")
        assert re.search(r"模型 v\d+\.\d+", t), p.name
        assert re.search(r"快照 [0-9a-f]{12}", t), p.name


# ---------------- 负样本：证明检查器真能抓错 ----------------
def _run_checker(intel: Path, art: Path):
    cmd = [sys.executable, "-X", "utf8", str(ROOT / "scripts" / "check_report_consistency.py"),
           DAY, "--intel", str(intel), "--art", str(art)]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def _sandbox(tmp_path: Path):
    intel = tmp_path / "intel"
    art = tmp_path / "art"
    intel.mkdir()
    art.mkdir()
    for f in INTEL.glob("*.json"):
        shutil.copy2(f, intel / f.name)
    for f in ART.glob("*.md"):
        shutil.copy2(f, art / f.name)
    return intel, art


def test_negative_wrong_layer_is_caught(tmp_path):
    """负样本 1：把 fused 层数值挂到「机构」下面，必须报 layer_mismatch"""
    intel, art = _sandbox(tmp_path)
    p = sorted(art.glob("*001+002+003*.md"))[0]
    t = p.read_text(encoding="utf-8")
    fused003 = _three_c(V3["003"])[0] * 100           # 47.0
    marker = "\n## 三场看完，看什么？"
    inject = f"\n按机构口径这场主胜只有 {fused003:.1f}%。\n"
    t2 = t.replace(marker, inject + marker)
    assert t2 != t, "注入失败：找不到插入锚点"
    p.write_text(t2, encoding="utf-8", newline="")
    r = _run_checker(intel, art)
    assert r.returncode == 1 and "层引错" in r.stdout, r.stdout[-500:]


def test_negative_bogus_score_probability_is_caught(tmp_path):
    """负样本 2：凭空写一个比分概率，必须报「无出处」"""
    intel, art = _sandbox(tmp_path)
    p = sorted(art.glob("*001+002+003*.md"))[0]
    t = p.read_text(encoding="utf-8")
    marker = "\n## 三场看完，看什么？"
    p.write_text(t.replace(marker, "\n比分上 2 比 1 占 22.2%。\n" + marker), encoding="utf-8", newline="")
    r = _run_checker(intel, art)
    assert r.returncode == 1 and "无出处" in r.stdout, r.stdout[-500:]


def test_negative_tampered_report_score_is_caught(tmp_path):
    """负样本 3：报告里把一个比分概率改掉，C3 必须报出来"""
    intel, art = _sandbox(tmp_path)
    rp = art / f"{DAY}_周二10场_内部分析报告.md"
    t = rp.read_text(encoding="utf-8")
    k, v = V3["003"]["top_scores"][0]
    kk = k.replace("-", "-")
    pat = re.compile(rf"{re.escape(kk)}（λ_C \d+\.\d%")
    assert pat.search(t), "报告里找不到该比分锚点"
    t2 = pat.sub(f"{kk}（λ_C 19.9%", t, count=1)
    rp.write_text(t2, encoding="utf-8", newline="")
    r = _run_checker(intel, art)
    assert r.returncode == 1 and ("[C1]" in r.stdout or "[C3]" in r.stdout), r.stdout[-500:]


def test_negative_missing_interval_is_not_faked(tmp_path):
    """负样本 4：w=0 的场若被写成有区间，C2 必须报（区间不得无源）"""
    intel, art = _sandbox(tmp_path)
    rp = art / f"{DAY}_周二10场_内部分析报告.md"
    t = rp.read_text(encoding="utf-8")
    sec = SECS["007"]
    bad = sec.replace("λ_C 参数区间不适用", "λ_C 参数区间 20–60%", 1)
    assert bad != sec
    rp.write_text(t.replace(sec, bad), encoding="utf-8", newline="")
    r = _run_checker(intel, art)
    assert r.returncode == 1 and "[C2]" in r.stdout, r.stdout[-500:]
