"""
AFEI v3.0 Prediction Fusion Engine v1.0
融合模型概率 + 分析评分 + 市场评分 + 情报评分 → 最终预测

包含：
  - 多源评分加权融合
  - Score ↔ Probability 校准
  - 置信度计算
  - 风险标记
"""

import json, os, math

_PARAMS_PATH = os.path.join(os.path.dirname(__file__), "config", "fusion-parameters.json")
with open(_PARAMS_PATH, 'r', encoding='utf-8') as f:
    PARAMS = json.load(f)


def fuse(model_mc, features, context_type="normal_league"):
    """
    主入口：融合多源评分，输出最终预测。

    model_mc  : Model Engine的MC输出 (含home_pct/draw_pct/away_pct)
    features  : Feature Vector (含strength_gap等原始特征)
    context_type: 赛事类型 (normal_league/key_match/cup_knockout/derby/qualifier)
    """

    # Step 1: 计算四个评分
    scores = {
        "model": _model_score(model_mc),
        "analysis": _analysis_score(features),
        "market": _market_score(features),
        "intel": _intel_score(features)
    }

    # Step 2: 获取权重
    weights = PARAMS["fusion_weights"].get(context_type, PARAMS["fusion_weights"]["normal_league"])

    # Step 3: 加权融合 → 综合评分
    final_score = sum(scores[k] * weights[SCORE_KEYS[k]] for k in scores)

    # Step 4: 数据可信度折扣
    dc = features.get("data_confidence", 0.9)
    penalty = _confidence_penalty(dc)
    final_score *= penalty

    # Step 5: 校准 → 概率
    prob = _calibrate(final_score)

    # Step 6: 置信度
    confidence = _compute_confidence(scores, weights, dc, features)

    # Step 7: 风险标记
    risks = _detect_risks(features, model_mc)

    return {
        "fusion_version": PARAMS["calibration_version"],
        "context_type": context_type,
        "scores": scores,
        "final_score": round(final_score, 1),
        "data_confidence_penalty": round(penalty, 3),
        "prediction": {
            "home_pct": round(prob["home"] * 100, 1),
            "draw_pct": round(prob["draw"] * 100, 1),
            "away_pct": round(prob["away"] * 100, 1)
        },
        "confidence": round(confidence, 2),
        "risks": risks
    }


def _model_score(mc):
    """模型MC评分 (0-100)，基于主胜优势"""
    h = mc.get("home_pct", 33)
    d = mc.get("draw_pct", 33)
    a = mc.get("away_pct", 33)
    # 主胜概率越高分越高，平局浓度拉低分
    advantage = h - a
    raw = 50 + advantage * 0.5
    return max(10, min(90, round(raw)))


def _analysis_score(features):
    """分析评分 (0-100)，基于实力差+主客场+状态"""
    score = 50
    score += features.get("strength_gap", 0) * 30
    score += features.get("point_gap", 0) * 15
    score += features.get("home_advantage", 0) * 20
    score += features.get("form_gap", 0) * 20
    score -= features.get("injury_home", 0) * 30
    score += features.get("injury_away", 0) * 30
    return max(10, min(90, round(score)))


def _market_score(features):
    """市场评分 (0-100)，基于市场共识"""
    base = features.get("market_confidence", 0.5) * 100
    if features.get("market_warning", 0):
        base -= 20
    if features.get("is_qualifier", 0):
        base *= 0.8
    return max(10, min(90, round(base)))


def _intel_score(features):
    """情报评分 (0-100)，基于赛前变量"""
    score = 50
    if features.get("is_cup", 0):
        score += 5
    if features.get("is_derby", 0):
        score += 5
    if features.get("is_qualifier", 0):
        score -= 10
    # 伤停影响
    inj_gap = features.get("injury_gap", 0)
    score -= inj_gap * 50
    return max(10, min(90, round(score)))

SCORE_KEYS = {"model": "model", "analysis": "analysis", "market": "market", "intel": "info"}


def _calibrate(score):
    """Score → 概率映射（插值）"""
    mapping = PARAMS["score_probability_mapping"]
    if score >= mapping[0]["score"]:
        return {"home": mapping[0]["win_prob"], "draw": mapping[0]["draw_prob"], "away": mapping[0]["loss_prob"]}
    if score <= mapping[-1]["score"]:
        return {"home": mapping[-1]["win_prob"], "draw": mapping[-1]["draw_prob"], "away": mapping[-1]["loss_prob"]}
    for i in range(len(mapping) - 1):
        hi, lo = mapping[i], mapping[i + 1]
        if lo["score"] <= score <= hi["score"]:
            ratio = (score - lo["score"]) / (hi["score"] - lo["score"])
            return {
                "home": lo["win_prob"] + ratio * (hi["win_prob"] - lo["win_prob"]),
                "draw": lo["draw_prob"] + ratio * (hi["draw_prob"] - lo["draw_prob"]),
                "away": lo["loss_prob"] + ratio * (hi["loss_prob"] - lo["loss_prob"])
            }
    return {"home": 0.34, "draw": 0.33, "away": 0.33}


def _compute_confidence(scores, weights, data_confidence, features):
    """综合置信度"""
    # 评分一致性：评分越接近→置信度越高
    vals = list(scores.values())
    spread = max(vals) - min(vals)
    consistency = max(0, 1 - spread / 100)

    # 数据质量
    dq = data_confidence

    # 市场对齐
    ma = 1.0 if not features.get("market_warning", 0) else 0.6

    cf = PARAMS["confidence_factors"]
    confidence = (
        consistency * 0.3 +
        dq * cf["data_quality_weight"] +
        ma * cf["market_alignment_weight"]
    )
    return max(0.3, min(0.95, confidence))


def _detect_risks(features, mc):
    """检测风险"""
    risks = []
    if features.get("market_warning", 0):
        risks.append("market_overheat")
    if features.get("is_qualifier", 0):
        risks.append("limited_data")
    if features.get("data_confidence", 1) < 0.6:
        risks.append("low_data_confidence")
    # 三向过于接近
    h, d, a = mc.get("home_pct", 33), mc.get("draw_pct", 33), mc.get("away_pct", 33)
    if max(h, d, a) - min(h, d, a) < 10:
        risks.append("highly_balanced")
    return risks


def fuse_from_files(model_json_path, features_json_path=None):
    """从文件加载并融合"""
    with open(model_json_path, 'r', encoding='utf-8') as f:
        model_data = json.load(f)
    mc = model_data.get("mc", model_data)

    feats = {}
    if features_json_path:
        with open(features_json_path, 'r', encoding='utf-8') as f:
            feat_data = json.load(f)
        feats = feat_data.get("features", feat_data)

    result = fuse(mc, feats)
    base = os.path.splitext(model_json_path)[0]
    out_path = f"{base}_fusion.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Fusion输出: {out_path}")
    return result


def _confidence_penalty(data_confidence):
    """数据可信度折扣"""
    table = PARAMS["data_confidence_penalty"]
    dc_str = str(data_confidence)
    if dc_str in table:
        return table[dc_str]
    if data_confidence >= 0.85:
        return 1.0
    if data_confidence >= 0.60:
        return 0.85
    if data_confidence >= 0.40:
        return 0.75
    return 0.50


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        fuse_from_files(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        # 测试：哥德堡vs索尔纳
        test_mc = {"home_pct": 37.2, "draw_pct": 25.3, "away_pct": 37.4}
        test_feats = {
            "strength_gap": -0.1034, "point_gap": 0.1667,
            "home_advantage": 0.08, "form_gap": 0.0,
            "injury_home": 0.0, "injury_away": 0.0, "injury_gap": 0.0,
            "market_confidence": 0.41, "market_warning": 0.0,
            "data_confidence": 0.9,
            "is_cup": 0, "is_qualifier": 0, "is_derby": 0
        }
        r = fuse(test_mc, test_feats, "normal_league")
        print(json.dumps(r, ensure_ascii=False, indent=2))
