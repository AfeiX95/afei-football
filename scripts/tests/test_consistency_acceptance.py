# -*- coding: utf-8 -*-
"""验收硬约束的回归测试（用户 m01663 的「自动验收」要求）。

跑法：python -m pytest scripts/tests/test_consistency_acceptance.py -q
前提：20261027 批次的 _books/_data/_model/_audit 与报告、两篇公开稿都在仓里。
"""
from __future__ import annotations

import json
import re
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
DATA = json.loads((INTEL / f"_data_{DAY}.json").read_text(encoding="utf-8"))
MODEL = json.loads((INTEL / f"_model_{DAY}.json").read_text(encoding="utf-8"))
AUDIT = json.loads((INTEL / f"_audit_{DAY}.json").read_text(encoding="utf-8"))
REPORT = (ART / f"{DAY}_周二10场_内部分析报告.md").read_text(encoding="utf-8")
SECS = {m.group(1): m.group(0) for m in re.finditer(r"^### (\d{3}) .*?(?=^### |\Z)", REPORT, re.S | re.M)}
V3 = {n: mv3.build_single(DAY, n, AUDIT.get(n, {}).get("grade", "A")) for n in BOOKS}


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
    """C2：出结论用的点估计必须落在自己的 5–95% 区间内（区间与点估计同源）"""
    r = V3[num]
    lo, hi = r["interval_home"]
    point = r["three_c"][0] * 100
    assert lo - 1.0 <= point <= hi + 1.0, f"{num} 点 {point:.1f}% ∉ [{lo:.0f}, {hi:.0f}]"


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


def test_fusion_is_not_probability_average():
    """C5：融合值不得等于「A 与市场」的概率平均（防悄悄改成概率层加权）"""
    for num, r in V3.items():
        ta, tb = r.get("three_data"), r.get("three_market") or r.get("three_b")
        if not ta or not tb or not r["w_data"]:
            continue
        if abs(r["w_data"] - 0.5) <= 0.15 or abs(ta[0] - tb[0]) <= 0.10:
            continue
        avg = (ta[0] + tb[0]) / 2 * 100
        assert abs(r["three_c"][0] * 100 - avg) > 0.3, f"{num} 融合≈概率平均"


def test_every_public_percentage_is_traceable():
    """C6：公开稿里每个百分数必须能在模型数据里找到出处（±1pp）"""
    allowed: list[float] = []
    for num, r in V3.items():
        for key in ("three_data", "three_market", "three_fused", "three_b", "three_c"):
            for x in (r.get(key) or []):
                if isinstance(x, (int, float)):
                    allowed.append(x * 100)
        allowed += [p * 100 for _k, p in r["top_scores"]]
        allowed += list(r["interval_home"]) + list(r["interval_home_data"])
        for key in ("ah", "ou"):
            blk = r.get(key) or {}
            allowed += [abs(x) for x in (blk.get("ev") or ()) if x is not None]
            allowed += [x * 100 for x in (blk.get("dist") or {}).values()]
        mc = r.get("mc") or {}
        allowed += [float(v) * 100 for v in mc.values() if isinstance(v, (int, float))]
        m0 = MODEL.get(num) or {}
        allowed += [x * 100 for x in (m0.get("market3") or [])]
    for p in ART.glob("*.md"):
        if "内部分析报告" in p.name:
            continue
        t = p.read_text(encoding="utf-8")
        for m in re.finditer(r"(\d+(?:\.\d)?)%", t):
            val = float(m.group(1))
            assert any(abs(a - val) <= 1.0 for a in allowed), f"{p.name} 的 {val}% 无出处"


def test_public_articles_carry_version_and_snapshot():
    """C7：公开稿必须带模型版本与数据快照"""
    pubs = [p for p in ART.glob("*.md") if "内部分析报告" not in p.name]
    assert pubs
    for p in pubs:
        t = p.read_text(encoding="utf-8")
        assert re.search(r"模型 v\d+\.\d+", t), p.name
        assert re.search(r"快照 [0-9a-f]{12}", t), p.name
