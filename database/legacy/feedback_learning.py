"""
AFEI v3.0 Feedback Learning v1.0
赛后验证：结果记录 → 偏差分析 → 短周期修正 → 长周期校准

双周期：
  20场：检测偏差模式，自动调整个别规则系数
  100场：全面评估各维度贡献度，输出权重优化建议
"""

import json, os, glob, math
from datetime import datetime

FEEDBACK_DIR = os.path.join(os.path.dirname(__file__), "feedback", "matches")
SHORT_TERM_DIR = os.path.join(os.path.dirname(__file__), "feedback", "short_term")
LONG_TERM_DIR = os.path.join(os.path.dirname(__file__), "feedback", "long_term")
os.makedirs(FEEDBACK_DIR, exist_ok=True)
os.makedirs(SHORT_TERM_DIR, exist_ok=True)
os.makedirs(LONG_TERM_DIR, exist_ok=True)


# ===== 1. 结果记录 =====

def record_match(match_id, home_team, away_team, prediction, actual_score, features=None, context_type="normal_league"):
    """
    记录一场比赛的预测+赛后结果。

    prediction: Fusion Engine输出的prediction dict (home_pct/draw_pct/away_pct)
    actual_score: 实际比分字符串如 "2-1"
    features: 特征向量（可选，用于偏差归因）
    """
    h_goals, a_goals = map(int, actual_score.split("-"))
    if h_goals > a_goals:
        actual_winner = "home"
    elif h_goals == a_goals:
        actual_winner = "draw"
    else:
        actual_winner = "away"

    pred_winner = max(prediction, key=prediction.get)
    pred_winner = pred_winner.replace("_pct", "")

    record = {
        "match_id": match_id,
        "home_team": home_team,
        "away_team": away_team,
        "match_time": datetime.now().isoformat(),
        "context_type": context_type,
        "prediction": {"home_pct": prediction["home_pct"], "draw_pct": prediction["draw_pct"], "away_pct": prediction["away_pct"]},
        "actual": {"score": actual_score, "winner": actual_winner},
        "predicted_winner": pred_winner,
        "correct": pred_winner == actual_winner,
        "error": _analyze_error(prediction, actual_winner, features)
    }
    path = os.path.join(FEEDBACK_DIR, f"{match_id}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    print(f"✅ 记录保存: {path}")

    # 触发短周期检查
    _check_short_term()
    return record


def _analyze_error(prediction, actual_winner, features):
    """分析偏差原因"""
    h = prediction.get("home_pct", 33)
    d = prediction.get("draw_pct", 33)
    a = prediction.get("away_pct", 33)
    max_p = max(h, d, a)

    # 主要偏差原因
    if actual_winner == "home" and a == max_p:
        cause = "direction_wrong_favored_away"
    elif actual_winner == "away" and h == max_p:
        cause = "direction_wrong_favored_home"
    elif actual_winner == "draw" and max(h, a) > 45:
        cause = "draw_underestimated"
    elif actual_winner != "draw" and d > 35:
        cause = "draw_overestimated"
    else:
        cause = "direction_wrong"

    return {"primary_cause": cause, "confidence_error": abs(max_p - 50) / 5}


# ===== 2. 短周期修正（20场） =====

def _check_short_term():
    """检查最近20场的偏差模式"""
    records = _load_recent(20)
    if len(records) < 5:
        return

    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    accuracy = correct / total

    # 偏差归因
    causes = {}
    for r in records:
        cause = r.get("error", {}).get("primary_cause", "unknown")
        causes[cause] = causes.get(cause, 0) + 1

    report = {
        "window_size": total,
        "accuracy": round(accuracy, 3),
        "timestamp": datetime.now().isoformat(),
        "cause_distribution": causes,
        "alerts": []
    }

    # 检测异常
    for cause, count in causes.items():
        if count / total > 0.3:
            report["alerts"].append({
                "cause": cause,
                "frequency": round(count / total, 2),
                "suggestion": _suggestion_for_cause(cause)
            })

    path = os.path.join(SHORT_TERM_DIR, f"window_{total}matches_{datetime.now().strftime('%Y%m%d')}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 满20场触发长周期检查
    if total >= 20:
        _check_long_term()

    return report


def _suggestion_for_cause(cause):
    suggestions = {
        "direction_wrong_favored_away": "检查客队优势是否被过度修正",
        "direction_wrong_favored_home": "检查主队优势是否被过度修正",
        "draw_underestimated": "提高平局校准概率下限",
        "draw_overestimated": "降低平局校准概率上限",
        "direction_wrong": "检查基础特征权重是否合理"
    }
    return suggestions.get(cause, "无需特殊调整")


def _load_recent(n):
    """加载最近n场比赛记录"""
    paths = sorted(glob.glob(os.path.join(FEEDBACK_DIR, "*.json")), key=os.path.getmtime, reverse=True)
    records = []
    for p in paths[:n]:
        with open(p, 'r', encoding='utf-8') as f:
            records.append(json.load(f))
    return records


# ===== 3. 长周期校准（100场） =====

def _check_long_term():
    """100场长周期校准"""
    records = _load_recent(100)
    if len(records) < 100:
        return

    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))
    accuracy = correct / total

    # 分类统计
    by_type = {}
    for r in records:
        ct = r.get("context_type", "unknown")
        if ct not in by_type:
            by_type[ct] = {"total": 0, "correct": 0}
        by_type[ct]["total"] += 1
        if r.get("correct"):
            by_type[ct]["correct"] += 1

    for t, v in by_type.items():
        v["accuracy"] = round(v["correct"] / v["total"], 3) if v["total"] > 0 else 0

    calibration = {
        "total_matches": total,
        "overall_accuracy": round(accuracy, 3),
        "by_context_type": by_type,
        "timestamp": datetime.now().isoformat(),
        "weight_adjustment_suggestions": _suggest_weight_adjustments(by_type)
    }

    path = os.path.join(LONG_TERM_DIR, f"calibration_{datetime.now().strftime('%Y%m%d')}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(calibration, f, ensure_ascii=False, indent=2)

    # 输出校准报告
    print(f"\n📊 长周期校准报告 (100场)")
    print(f"  总体准确率: {accuracy:.1%}")
    for t, v in by_type.items():
        print(f"  {t}: {v['accuracy']:.1%} ({v['correct']}/{v['total']})")
    return calibration


def _suggest_weight_adjustments(by_type):
    """根据各类赛事准确率建议权重调整"""
    suggestions = {}
    for t, v in by_type.items():
        if v["total"] < 5:
            continue
        acc = v["accuracy"]
        if acc < 0.50:
            suggestions[t] = {"status": "需要调整", "current_accuracy": acc, "suggestion": "检查该类型权重配置"}
        elif acc < 0.65:
            suggestions[t] = {"status": "边缘", "current_accuracy": acc, "suggestion": "持续监控"}
        else:
            suggestions[t] = {"status": "良好", "current_accuracy": acc}
    return suggestions


# ===== 4. 快捷入口 =====

def get_summary():
    """获取当前反馈系统摘要"""
    records = _load_recent(1000)
    total = len(records)
    correct = sum(1 for r in records if r.get("correct"))

    # 最近20场
    recent = _load_recent(20)
    recent_correct = sum(1 for r in recent if r.get("correct"))

    return {
        "total_records": total,
        "overall_accuracy": round(correct / total, 3) if total > 0 else 0,
        "recent_20_accuracy": round(recent_correct / 20, 3) if len(recent) >= 20 else (recent_correct / len(recent) if recent else 0),
        "recent_20_count": len(recent),
        "last_updated": datetime.now().isoformat()
    }


if __name__ == "__main__":
    # 测试：模拟一场比赛记录
    test_pred = {"home_pct": 55.0, "draw_pct": 25.0, "away_pct": 20.0}
    record_match("test_001", "主队", "客队", test_pred, "2-1", context_type="normal_league")

    test_pred2 = {"home_pct": 38.0, "draw_pct": 30.0, "away_pct": 32.0}
    record_match("test_002", "法国", "西班牙", test_pred2, "0-2", context_type="cup_knockout")

    print("\n📊 反馈系统摘要:")
    print(json.dumps(get_summary(), ensure_ascii=False, indent=2))
