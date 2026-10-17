"""
AFEI v3.0 Model Engine v2.0
λ生成器 + Poisson比分矩阵 + Monte Carlo模拟

输入：Feature Vector JSON（Feature Extractor输出）
输出：模型概率 + 比分概率 + MC结果
"""

import json, math, random, os

_PARAMS_PATH = os.path.join(os.path.dirname(__file__), "config", "model-parameters.json")
with open(_PARAMS_PATH, 'r', encoding='utf-8') as f:
    PARAMS = json.load(f)

MP = PARAMS["lambda_formula"]
MC = PARAMS["mc_simulation"]
MAX_GOALS = PARAMS["poisson_max_goals"]


def lambda_home(features):
    """
    乘法因子公式：λ = base * (1 + Σ(因子贡献))
    """
    base = MP["base_lambda"]

    factors = [
        features.get("strength_gap", 0) * MP["strength_gap_weight"],
        features.get("point_gap", 0) * MP["point_gap_weight"],
        features.get("home_advantage", 0.08) * MP["home_advantage_weight"],
        features.get("form_gap", 0) * MP["form_weight"],
        features.get("injury_away", 0) * MP["injury_weight"],
        features.get("attack_home", 0) * MP["attack_weight"],
        features.get("defense_away", 0) * MP["defense_weight"],
    ]
    lam = base * (1 + sum(factors))
    lam = max(0.3, min(4.0, lam))

    if features.get("is_qualifier", 0):
        lam *= MP["qualifier_penalty"]
    return round(lam, 3)


def lambda_away(features):
    """客队λ，对称逻辑"""
    base = MP["base_lambda"]

    factors = [
        -features.get("strength_gap", 0) * MP["strength_gap_weight"],
        -features.get("point_gap", 0) * MP["point_gap_weight"],
        -features.get("home_advantage", 0.08) * MP["home_advantage_weight"] * 0.6,
        features.get("form_away", 0) * MP["form_weight"],
        features.get("injury_home", 0) * MP["injury_weight"],
        features.get("attack_away", 0) * MP["attack_weight"],
        features.get("defense_home", 0) * MP["defense_weight"] * 0.5,
    ]
    lam = base * (1 + sum(factors))
    lam = max(0.3, min(4.0, lam))

    if features.get("is_qualifier", 0):
        lam *= (1.0 - (1.0 - MP["qualifier_penalty"]) * 0.5)
    return round(lam, 3)


def poisson_prob(lam, k):
    """P(X=k) = λ^k · e^(-λ) / k!"""
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def score_matrix(Lh, La, max_g=MAX_GOALS):
    """
    生成比分概率矩阵。
    返回：sorted list of (score_str, probability)
    """
    matrix = {}
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            prob = poisson_prob(Lh, h) * poisson_prob(La, a)
            matrix[f"{h}-{a}"] = prob
    return sorted(matrix.items(), key=lambda x: -x[1])


def mc_simulate(Lh, La, n=MC["runs"]):
    """
    Monte Carlo模拟，支持扰动。
    返回：(home%, draw%, away%, over25%, expected_goals)
    """
    random.seed(MC["seed"])
    home_wins = draw = away_wins = 0
    total_goals = 0
    over25 = 0

    for _ in range(n):
        # 添加随机扰动±5%
        seed_h = Lh * random.uniform(0.95, 1.05)
        seed_a = La * random.uniform(0.95, 1.05)
        h = _poisson_sample(seed_h)
        a = _poisson_sample(seed_a)
        if h > a:
            home_wins += 1
        elif h == a:
            draw += 1
        else:
            away_wins += 1
        total = h + a
        total_goals += total
        if total > 2.5:
            over25 += 1

    nf = float(n)
    return {
        "home_pct": round(home_wins / nf * 100, 1),
        "draw_pct": round(draw / nf * 100, 1),
        "away_pct": round(away_wins / nf * 100, 1),
        "over25_pct": round(over25 / nf * 100, 1),
        "expected_goals": round(total_goals / nf, 2)
    }


def _poisson_sample(lam):
    """Poisson采样（Knuth乘法）"""
    L = math.exp(-lam)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def predict(features):
    """
    主入口：输入Feature Vector，输出完整模型预测。
    """
    Lh = lambda_home(features)
    La = lambda_away(features)
    scores = score_matrix(Lh, La)
    mc = mc_simulate(Lh, La)

    result = {
        "model_version": PARAMS["model_version"],
        "lambda": {"home": Lh, "away": La},
        "mc": mc,
        "scores": [{"score": s, "prob": round(p * 100, 1)} for s, p in scores[:10]],
        "top3_scores": [s for s, _ in scores[:3]]
    }
    return result


def predict_from_file(features_json_path):
    with open(features_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    feats = data.get("features", data)
    result = predict(feats)
    base, _ = os.path.splitext(features_json_path)
    out_path = f"{base}_model.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 模型输出: {out_path}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        predict_from_file(sys.argv[1])
    else:
        # 测试：哥德堡vs索尔纳
        test_feats = {
            "strength_gap": -0.1034, "point_gap": 0.1667,
            "home_advantage": 0.08, "form_gap": 0.0,
            "form_home": 0.0, "form_away": 0.0,
            "attack_home": 0.0, "attack_away": 0.0,
            "defense_home": 0.0, "defense_away": 0.0,
            "injury_home": 0.0, "injury_away": 0.0, "injury_gap": 0.0,
            "market_confidence": 0.41, "market_warning": 0.0,
            "is_cup": 0, "is_qualifier": 0, "is_derby": 0, "data_confidence": 0.9
        }
        result = predict(test_feats)
        print(f"λ: home={result['lambda']['home']} away={result['lambda']['away']}")
        print(f"MC: {result['mc']}")
        print(f"Top scores: {result['top3_scores']}")
