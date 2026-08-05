# -*- coding: utf-8 -*-
"""
球队战术档案生成器
从近N场比赛数据中提取战术特征，生成球队战术档案
"""
import json
import sys
import os

PROFILES_DIR = r"I:\阿飞说球\database\cache\tactical_profiles"

def analyze_possession(matches):
    poss = [m.get("home_possession", 50) if m.get("is_home") else 100 - m.get("away_possession", 50) for m in matches]
    avg = sum(poss) / len(poss) if poss else 50
    if avg > 55:
        return "传控型", avg
    elif avg < 45:
        return "防反型", avg
    else:
        return "平衡型", avg

def analyze_formation(matches):
    formations = [m.get("formation", "未知") for m in matches]
    from collections import Counter
    freq = Counter(formations)
    primary = freq.most_common(1)[0][0] if freq else "未知"
    return primary, dict(freq)

def generate_profile(team_name, matches):
    style, possession_avg = analyze_possession(matches)
    primary_formation, formation_history = analyze_formation(matches)
    profile = {
        "team": team_name,
        "last_updated": "2026-08-02",
        "primary_formation": primary_formation,
        "formation_history": formation_history,
        "style_profile": {
            "style": style,
            "possession_avg": round(possession_avg, 1),
        },
        "matches_analyzed": len(matches),
    }
    return profile

def main():
    team = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    sample_matches = [
        {"formation": "4-3-3", "home_possession": 52, "is_home": True},
        {"formation": "4-3-3", "home_possession": 48, "is_home": True},
        {"formation": "4-2-3-1", "home_possession": 55, "is_home": True},
    ]
    profile = generate_profile(team, sample_matches)
    os.makedirs(PROFILES_DIR, exist_ok=True)
    output_path = os.path.join(PROFILES_DIR, f"{team.replace(' ', '_')}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    print(json.dumps(profile, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
