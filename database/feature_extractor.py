"""
AFEI v3.0 Feature Extractor v1.0
把Adapter JSON（原始数据层）→ Feature Vector JSON（特征层）

只做转换，不做预测，不设定权重。
"""

import json, math, os

# 加载参数
_PARAMS_PATH = os.path.join(os.path.dirname(__file__), "config", "feature-parameters.json")
with open(_PARAMS_PATH, 'r', encoding='utf-8') as f:
    PARAMS = json.load(f)

N = PARAMS["normalization"]
LA = PARAMS["league_averages"]


def extract(adapter_json):
    """
    主入口：输入Adapter JSON，输出Feature Vector JSON。
    """
    ctx = adapter_json.get("match_context", {})
    tb = adapter_json.get("team_basic", {})
    perf = adapter_json.get("performance", {})
    inj = adapter_json.get("injury", {})
    mkt = adapter_json.get("market", {})
    env = adapter_json.get("environment", {})

    features = {
        # 实力
        "strength_gap": _strength_gap(tb),
        "point_gap": _point_gap(tb),

        # 主客场
        "home_advantage": _home_advantage(tb),

        # 状态
        "form_home": _form_score(perf, "home"),
        "form_away": _form_score(perf, "away"),
        "form_gap": 0.0,  # 后计算

        # 攻防（占位，等team_basic完备后激活）
        "attack_home": 0.0,
        "attack_away": 0.0,
        "defense_home": 0.0,
        "defense_away": 0.0,

        # 伤停
        "injury_home": _injury_score(inj, "home"),
        "injury_away": _injury_score(inj, "away"),
        "injury_gap": 0.0,  # 后计算

        # 市场
        "market_confidence": _market_confidence(mkt),
        "market_warning": 1.0 if mkt.get("alerts") else 0.0,

        # 环境
        "is_cup": 1.0 if ctx.get("match_type") == "cup_knockout" else 0.0,
        "is_qualifier": 1.0 if ctx.get("is_qualifier") else 0.0,
        "is_derby": 1.0 if ctx.get("derby") else 0.0,
        "data_confidence": ctx.get("data_confidence", 0.9),
    }

    # 计算衍生特征
    features["form_gap"] = round(features["form_home"] - features["form_away"], 4)
    features["injury_gap"] = round(features["injury_home"] - features["injury_away"], 4)

    return {
        "feature_version": PARAMS["feature_version"],
        "features": features
    }


def _strength_gap(tb):
    h = tb.get("home", {}).get("rank", 0)
    a = tb.get("away", {}).get("rank", 0)
    if h and a:
        gap = a - h
        return round(gap / N["max_rank_gap"], 4)
    return 0.0


def _point_gap(tb):
    h = tb.get("home", {}).get("points", 0)
    a = tb.get("away", {}).get("points", 0)
    if h or a:
        gap = h - a
        return round(gap / N["max_point_gap"], 4)
    return 0.0


def _home_advantage(tb):
    """基于主场vs客场排名推算主场优势，联动对手排名"""
    h_rank = tb.get("home", {}).get("rank", 0)
    a_rank = tb.get("away", {}).get("rank", 0)
    if h_rank and a_rank:
        gap = a_rank - h_rank
        # 排名差越大，主场优势越被对方排名削弱
        # 当主队排名高且对手弱时(gap大)，主场优势被加强
        base = 0.08
        if gap >= 8:
            base += 0.08  # 主场对弱队加成
        elif gap >= 4:
            base += 0.04
        return round(base + max(0, gap) * 0.005, 4)
    return 0.08  # 默认主场优势


def _form_score(perf, side):
    s = perf.get(side, {}).get("form_score", 0)
    return round(max(-N["form_max"], min(N["form_max"], s)), 4)


def _injury_score(inj, side):
    s = inj.get(side, {}).get("impact_score", 0)
    return round(min(N["injury_max"], s), 4)


def _market_confidence(mkt):
    """市场共识度：越高=市场越一致=信息越充分"""
    cl = mkt.get("consensus_level", 0.5)
    if mkt.get("overheating"):
        cl *= 0.8  # 过热时降权
    return round(cl, 4)


# ===== 快捷入口 =====

def extract_from_file(adapter_json_path):
    with open(adapter_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    result = extract(data)
    base, _ = os.path.splitext(adapter_json_path)
    out_path = f"{base}_features.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Features输出: {out_path}")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        extract_from_file(sys.argv[1])
    else:
        # 测试
        test = {
            "team_basic": {"home": {"rank": 6, "points": 24}, "away": {"rank": 13, "points": 14}},
            "performance": {"home": {"form_score": 0.11}, "away": {"form_score": -0.02}},
            "injury": {"home": {"impact_score": 0.05}, "away": {"impact_score": 0.12}},
            "market": {"consensus_level": 0.68, "overheating": False, "alerts": []},
            "match_context": {"match_type": "normal_league", "data_confidence": 0.9}
        }
        r = extract(test)
        print(json.dumps(r, ensure_ascii=False, indent=2))
