# -*- coding: utf-8 -*-
"""
阵型克制分析器
输入两队阵型，输出克制关系评分
"""
import json
import sys

# 克制矩阵：行克制列
FORMATION克制 = {
    ("4-3-3", "5-3-2"): +1,
    ("4-3-3", "4-4-2"): 0,
    ("4-3-3", "4-2-3-1"): -1,
    ("4-2-3-1", "4-3-3"): -1,
    ("4-2-3-1", "5-3-2"): 0,
    ("5-3-2", "4-3-3"): +1,
    ("5-3-2", "4-4-2"): +1,
    ("3-5-2", "4-4-2"): +1,
    ("4-4-2", "3-5-2"): -1,
    ("4-4-2", "4-3-3"): 0,
    ("4-1-4-1", "4-3-3"): 0,
    ("4-3-3", "4-1-4-1"): 0,
    ("3-4-3", "4-4-2"): +1,
    ("4-4-2", "3-4-3"): -1,
}

FORMATION_STYLE = {
    "4-3-3": "传控/高位逼抢",
    "4-2-3-1": "攻守平衡",
    "3-5-2": "中场厚度+两翼齐飞",
    "5-3-2": "低位防守反击",
    "4-4-2": "经典平衡",
    "3-4-3": "激进进攻",
    "4-1-4-1": "防守反击",
}

def analyze(home_formation, away_formation):
    key = (home_formation, away_formation)
    reverse_key = (away_formation, home_formation)

    if key in FORMATION克制:
        score = FORMATION克制[key]
    elif reverse_key in FORMATION克制:
        score = -FORMATION克制[reverse_key]
    else:
        score = 0

    home_style = FORMATION_STYLE.get(home_formation, "未知")
    away_style = FORMATION_STYLE.get(away_formation, "未知")

    result = {
        "home_formation": home_formation,
        "away_formation": away_formation,
        "home_style": home_style,
        "away_style": away_style,
        "matchup_score": score,
        "analysis": get_analysis(home_formation, away_formation, score),
    }
    return result

def get_analysis(home, away, score):
    if score >= +2:
        return f"{home} 完全克制 {away}，空间优势明显"
    elif score == +1:
        return f"{home} 对 {away} 有一定优势"
    elif score == 0:
        return f"{home} vs {away} 势均力敌，无明显克制"
    elif score == -1:
        return f"{home} 对 {away} 有一定劣势"
    else:
        return f"{home} 被 {away} 完全克制"

def main():
    home = sys.argv[1] if len(sys.argv) > 1 else "4-3-3"
    away = sys.argv[2] if len(sys.argv) > 2 else "4-4-2"
    result = analyze(home, away)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
