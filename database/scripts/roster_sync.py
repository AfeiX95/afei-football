# -*- coding: utf-8 -*-
"""
球员阵容同步器
从数据源抓取球队阵容，标记球员状态
"""
import json
import sys
import os
from datetime import datetime

ROSTER_DIR = r"I:\阿飞说球\database\cache\roster"

PLAYER_STATUS = {
    "available": "可用",
    "injured": "伤病",
    "suspended": "停赛",
    "doubtful": "伤疑",
    "transferred": "已转会",
}

def create_roster_template(team_name, players=None):
    if players is None:
        players = []
    roster = {
        "team": team_name,
        "last_synced": datetime.now().isoformat(),
        "squad_size": len(players),
        "available_count": sum(1 for p in players if p.get("status") == "available"),
        "injured_count": sum(1 for p in players if p.get("status") == "injured"),
        "suspended_count": sum(1 for p in players if p.get("status") == "suspended"),
        "squad": players,
    }
    return roster

def calculate_injury_impact(roster):
    total_impact = 0.0
    position_weight = {"前锋": 1.2, "中场": 1.0, "后卫": 0.9, "门将": 1.3}
    level_weight = {"S": 0.18, "A": 0.10, "B": 0.04, "C": 0.01}
    for player in roster.get("squad", []):
        if player.get("status") in ("injured", "suspended"):
            pos = player.get("position", "中场")
            level = player.get("impact_level", "B")
            pw = position_weight.get(pos, 1.0)
            lw = level_weight.get(level, 0.04)
            total_impact += pw * lw
    return round(min(total_impact, 0.4), 3)

def main():
    team = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    roster = create_roster_template(team)
    impact = calculate_injury_impact(roster)
    roster["injury_impact_lambda"] = impact
    os.makedirs(ROSTER_DIR, exist_ok=True)
    output_path = os.path.join(ROSTER_DIR, f"{team.replace(' ', '_')}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Roster saved: {output_path}")
    print(f"[INFO] Injury impact: lambda -{impact}")
    print(json.dumps(roster, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
