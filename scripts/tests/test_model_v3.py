# -*- coding: utf-8 -*-
"""model_v3 / audit_data 的回归测试（评审 P0-7：先写断言再改代码）"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import model_v3 as mv3  # noqa: E402
import audit_data as ad  # noqa: E402


def _rows(*pairs):
    """构造 500 风格的近期行（venue = H/A）"""
    return [{"date": d, "home": h, "away": a, "score": s, "venue": v} for d, h, a, s, v in pairs]


def test_team_rows_counts_goals_by_venue():
    """主队视角：venue=H 取左，venue=A 取右（旧 bug：读 side 恒为空，GF/GA 全反）；返回按日期倒序"""
    rows = _rows(("26-10-01", "A队", "B队", "3-1", "H"),
                 ("26-10-02", "C队", "A队", "2-0", "A"))
    res = ad.team_rows(rows, "A队")
    assert [r["date"] for r in res] == ["26-10-02", "26-10-01"]
    assert [r["gf"] for r in res] == [0, 3]
    assert [r["ga"] for r in res] == [2, 1]


def test_dedupe_removes_repeated_fixture():
    """同场重复行只留一条，并回报重复（007 曾因此判 DATA_INVALID）"""
    rows = _rows(("26-10-10", "多特", "不莱梅", "2-2", "A"),
                 ("26-10-10", "多特", "不莱梅", "2-2", "A"),
                 ("26-10-24", "美因茨", "不莱梅", "2-3", "A"))
    keep, dups = ad.dedupe(ad.team_rows(rows, "不莱梅"))
    assert len(keep) == 2
    assert len(dups) == 1


def test_fuse_weight_discounted_by_sample():
    """融合权重 = 等级权重 × min(1, 样本/5)"""
    la, lb = (2.0, 1.0), (1.0, 1.0)
    _, w = mv3.fuse(la, lb, "A", (5, 5))
    assert abs(w - 0.65) < 1e-9
    lam2, w2 = mv3.fuse(la, lb, "A", (1, 1))
    assert abs(w2 - 0.13) < 1e-9
    assert 1.0 < lam2[0] < 2.0


def test_fuse_without_data_lam_falls_back_to_market():
    lam, w = mv3.fuse(None, (1.5, 1.2), "A", None)
    assert lam == (1.5, 1.2) and w == 0.0


def test_data_lam_shrinks_toward_season_prior():
    """同主客样本极小时，λ_A 应被先验拉回，而不是照抄小样本极值"""
    row = {"season_home": {"total": {"p": 2, "gf": 2, "ga": 1, "rank": 5},
                           "home": {"p": 1, "gf": 5, "ga": 0}},
           "season_away": {"total": {"p": 2, "gf": 4, "ga": 1, "rank": 3},
                           "away": {"p": 1, "gf": 2, "ga": 1}}}
    r = mv3.data_lam(row, "A")
    assert r is not None
    assert r["lam"][0] < 5.0            # 收缩后低于小样本极值
    assert r["notes"] and "样本不足" in r["notes"][0]


def test_uncertainty_widens_with_thin_sample():
    lo1, hi1 = mv3.uncertainty((2.0, 1.0), (2, 2))
    lo2, hi2 = mv3.uncertainty((2.0, 1.0), (20, 20))
    assert (hi1 - lo1) > (hi2 - lo2)


def test_edge_is_data_minus_market_pp():
    e = mv3.edge((2.0, 1.0), (0.5, 0.25, 0.25))
    assert len(e) == 3
    assert abs(sum(e)) < 1e-6           # 两边都是完整分布，差值之和应为 0
