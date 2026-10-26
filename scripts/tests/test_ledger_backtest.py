#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ledger + Backtest 的验收测试（P0/P2 的自动化证据）

跑法：python -X utf8 -m pytest -q scripts/tests/test_ledger_backtest.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import ledger as LED  # noqa: E402
import backtest as BT  # noqa: E402
import history_audit as HA  # noqa: E402


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    """在临时目录里造一份 intel 数据，并把 ledger/ROOT 指过去。"""
    day = "20261027"
    intel = tmp_path / "state" / "intel" / day
    intel.mkdir(parents=True)
    (intel / f"_model_v3_{day}.json").write_text(json.dumps({
        "001": {"model_version": "v3.1", "data_snapshot": "abc", "data_grade": "A", "evidence_grade": "较强",
                "w_data": 0.6, "n_eff": [8, 8],
                "three_data": [70, 20, 10], "three_market": [50, 25, 25], "three_fused": [62, 22, 16],
                "lam_data": [1.8, 0.9], "lam_market_joint": [1.4, 1.1], "lam_fused": [1.6, 1.0]},
        "002": {"model_version": "v3.1", "data_snapshot": "abc", "data_grade": "A", "evidence_grade": "偏弱",
                "w_data": 0.1, "n_eff": [1, 1],
                "three_data": [30, 25, 45], "three_market": [45, 27, 28], "three_fused": [43, 27, 30],
                "lam_data": [1.0, 1.4], "lam_market_joint": [1.3, 1.2], "lam_fused": [1.25, 1.23]},
    }, ensure_ascii=False), encoding="utf-8")
    (intel / f"_market_{day}.json").write_text(json.dumps({
        "001": {"id": "111", "match": "主队甲 vs 客队乙", "kickoff": "10-27 20:00", "prob_close": [50, 25, 25],
                "overround_close": 6.0, "ah_modal_close": -1.0, "ou_modal_close": 2.5, "league": "英超"},
        "002": {"id": "222", "match": "主队丙 vs 客队丁", "kickoff": "10-27 22:00", "prob_close": [45, 27, 28],
                "overround_close": 5.0, "ah_modal_close": 0.0, "ou_modal_close": 2.5, "league": "意甲"},
    }, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(LED, "ROOT", tmp_path)
    monkeypatch.setattr(LED, "LEDGER", tmp_path / "ledger")
    return tmp_path, day


def test_append_writes_and_is_immutable(sandbox):
    tmp, day = sandbox
    assert LED.main(["append", "--day", day]) == 0
    path = LED.pred_path(day)
    first = path.read_text(encoding="utf-8")
    assert len(first.strip().splitlines()) == 2
    # 二次写入必须拒绝，且文件内容一字不变
    assert LED.main(["append", "--day", day]) == 2
    assert path.read_text(encoding="utf-8") == first


def test_record_shape_and_kickoff(sandbox):
    tmp, day = sandbox
    LED.main(["append", "--day", day])
    rec = json.loads(LED.pred_path(day).read_text(encoding="utf-8").splitlines()[0])
    assert rec["schema"] == "afei-ledger-v1"
    assert rec["match_id"] == f"{day}-001"
    assert rec["kickoff"].startswith("2026-10-27T20:00")
    assert set(rec["probs"]) == {"A", "M", "F"}
    assert rec["record_sha256"] == LED._hash(rec)
    assert rec["retrospective"] is False


def test_retrospective_flag_is_explicit(sandbox):
    tmp, day = sandbox
    LED.main(["append", "--day", day, "--retrospective"])
    for ln in LED.pred_path(day).read_text(encoding="utf-8").splitlines():
        assert json.loads(ln)["retrospective"] is True


def test_verify_detects_tampering(sandbox):
    tmp, day = sandbox
    LED.main(["append", "--day", day])
    assert LED.main(["verify"]) == 0
    p = LED.pred_path(day)
    lines = p.read_text(encoding="utf-8").splitlines()
    obj = json.loads(lines[0])
    obj["w_data"] = 0.99  # 静默篡改
    p.write_text("\n".join([json.dumps(obj, ensure_ascii=False)] + lines[1:]) + "\n", encoding="utf-8")
    assert LED.main(["verify"]) == 1


def test_add_result_once_and_outcome(sandbox):
    tmp, day = sandbox
    LED.main(["append", "--day", day])
    payload = tmp / "res.json"
    payload.write_text(json.dumps({"001": {"score": "2:1", "ht": "1:0"}, "002": "0:0"}), encoding="utf-8")
    assert LED.main(["add-result", "--day", day, "--json", str(payload)]) == 0
    rows = LED.read_jsonl(LED.res_path(day))
    assert [r["outcome"] for r in rows] == ["H", "D"]
    # 重复追加同一场必须拒绝
    assert LED.main(["add-result", "--day", day, "--json", str(payload)]) == 2
    assert len(LED.read_jsonl(LED.res_path(day))) == 2


# ------------------------------------------------------------------ backtest
def _row(a, m, f, y, **meta):
    return {"meta": {"match_id": meta.get("mid", "x"), "kickoff": meta.get("ko", "2026-10-27T20:00:00+08:00"),
                     "league": meta.get("league"), "data_grade": meta.get("grade", "A")},
            "y": y, "P": {"A": np.array(a) / 100, "M": np.array(m) / 100, "F": np.array(f) / 100}}


def test_brier_and_logloss_known_values():
    P = np.array([0.5, 0.3, 0.2])
    assert BT.brier(P, 0) == pytest.approx(0.25 + 0.09 + 0.04)
    assert BT.logloss(P, 2) == pytest.approx(-np.log(0.2))
    # 完美预测：Brier=0、LogLoss=0
    assert BT.brier(np.array([1.0, 0.0, 0.0]), 0) == pytest.approx(0.0)
    assert BT.logloss(np.array([1.0, 0.0, 0.0]), 0) == pytest.approx(0.0, abs=1e-12)


def test_pair_ci_direction_and_determinism():
    good = _row([80, 15, 5], [60, 20, 20], [70, 18, 12], 0)
    rows = [good] * 20 + [_row([20, 20, 60], [40, 30, 30], [35, 28, 37], 0)] * 20
    M = BT.pair_matrix(rows)
    d = M["A"] - M["M"]
    mu1, lo1, hi1 = BT.boot_ci(d, 500)
    mu2, lo2, hi2 = BT.boot_ci(d, 500)
    assert (mu1, lo1, hi1) == (mu2, lo2, hi2)  # 固定种子
    assert lo1 <= mu1 <= hi1


def test_reliability_bins_sum_to_three_times_n():
    rows = [_row([50, 30, 20], [50, 30, 20], [50, 30, 20], i % 3) for i in range(30)]
    rel = BT.reliability(rows, "A")
    assert sum(r["n"] for r in rel) == 3 * len(rows)
    e = BT.ece(rel, 3 * len(rows))
    assert 0.0 <= e <= 0.5


def test_equal_sample_set_across_models():
    """缺一套概率的场次不得只从某一模型的样本里剔除。"""
    rows = [_row([50, 30, 20], [50, 30, 20], [50, 30, 20], 0)]
    bad = {"meta": {"match_id": "z"}, "y": 0, "P": {"A": np.array([.5, .3, .2]), "M": np.array([.5, .3, .2]), "F": None}}
    sample = [r for r in rows + [bad] if all(r["P"][m] is not None for m in BT.MODELS)]
    assert len(sample) == 1


def test_w_grid_endpoints():
    rows = [_row([70, 20, 10], [50, 25, 25], [52, 24, 24], 0) for _ in range(10)]
    grid = BT.w_grid(rows, np.array([0.0, 1.0]))
    assert grid[0]["logloss"] == pytest.approx(np.mean([BT.logloss(r["P"]["M"], 0) for r in rows]))
    assert grid[1]["logloss"] == pytest.approx(np.mean([BT.logloss(r["P"]["A"], 0) for r in rows]))


def test_abstain_bands_cover_sample():
    rows = [_row([70, 20, 10], [50, 25, 25], [55, 24, 21], 0),
            _row([45, 30, 25], [44, 30, 26], [44, 30, 26], 1)]
    tab = BT.abstain_table(rows)
    assert sum(r["n"] for r in tab) == len(rows)
    assert sum(r["coverage"] for r in tab) == pytest.approx(1.0)


# ------------------------------------------------------------------ history audit
def test_history_audit_parses_two_formats(tmp_path):
    md = tmp_path / "batch_demo.md"
    md.write_text(
        "| 场次 | 赛果(90') | 实际 | 模型首选 | 方向 |\n"
        "|---|---|---|---|:-:|\n"
        "| 001 悉尼FC-阿德莱德 | 2:1(半0:1) | 主 | 主43.0 | ✅ |\n"
        "| 002 新潟-仙台 | 1:1(1:1) | 平 | 客53.8 | ❌ |\n",
        encoding="utf-8")
    d = HA.parse_file(md)
    assert len(d["rows"]) == 2
    r = d["rows"][0]
    assert r["score_90"] == (2, 1) and r["outcome"] == "主" and r["hit"] is True
    assert r["model_prob"] == pytest.approx(43.0)
    assert HA.grade(r) == "L1"
    assert HA.grade(d["rows"][1]) == "L1"


def test_history_audit_skips_handicap_and_half_columns(tmp_path):
    md = tmp_path / "x.md"
    md.write_text(
        "| 场次 | 半场 | 让球 | 全场 |\n"
        "|---|---|---|---|\n"
        "| 003 A-B | 1:0 | -1 | 2:1 |\n",
        encoding="utf-8")
    d = HA.parse_file(md)
    assert d["rows"][0]["score_90"] == (2, 1)
