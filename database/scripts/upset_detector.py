# -*- coding: utf-8 -*-
"""
冷门预警系统
结合模型输出+市场定价，识别潜在冷门信号
"""
import json
import sys

def detect_upset(model_probs, market_odds, team_info=None):
    home_mkt = 1.0 / market_odds["home"] * 100 if market_odds["home"] else 0
    draw_mkt = 1.0 / market_odds["draw"] * 100 if market_odds["draw"] else 0
    away_mkt = 1.0 / market_odds["away"] * 100 if market_odds["away"] else 0

    deviation_home = model_probs["home"] - home_mkt
    deviation_away = model_probs["away"] - away_mkt

    signals = []
    score = 0

    if abs(deviation_home) > 15:
        signals.append(f"主胜偏差{deviation_home:+.1f}pp")
        score += 30
    if abs(deviation_away) > 15:
        signals.append(f"客胜偏差{deviation_away:+.1f}pp")
        score += 30

    if market_odds["home"] and float(market_odds["home"]) < 1.50:
        signals.append(f"主胜低赔{market_odds['home']}，过热风险")
        score += 15

    if market_odds["away"] and float(market_odds["away"]) < 1.50:
        signals.append(f"客胜低赔{market_odds['away']}，过热风险")
        score += 15

    if team_info:
        if team_info.get("away_form_wins", 0) >= 3:
            signals.append("客队近3+连胜，状态火热")
            score += 15
        if team_info.get("home_form_wins", 0) <= 1:
            signals.append("主队近6场仅1胜，状态低迷")
            score += 15

    if score >= 60:
        level = "RED"
        emoji = "RED CIRCLE"
    elif score >= 30:
        level = "YELLOW"
        emoji = "YELLOW CIRCLE"
    else:
        level = "GREEN"
        emoji = "GREEN CIRCLE"

    return {
        "level": level,
        "score": score,
        "signals": signals,
        "market_implied": {"home": round(home_mkt, 1), "draw": round(draw_mkt, 1), "away": round(away_mkt, 1)},
        "deviation": {"home": round(deviation_home, 1), "away": round(deviation_away, 1)},
    }

def main():
    model = {"home": 32.8, "draw": 27.5, "away": 39.7}
    odds = {"home": 1.86, "draw": 3.45, "away": 3.32}
    info = {"away_form_wins": 3, "home_form_wins": 1}

    result = detect_upset(model, odds, info)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
