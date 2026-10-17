"""
AFEI v3.0 Schema Validator
检查Adapter输出的JSON是否满足12字段Schema的基础要求

规则：
- 必填字段缺失 → warning（不阻塞）
- 字段类型错误 → warning
- 值域越界 → warning
"""

import json
import sys

REQUIRED_TOP_FIELDS = [
    "match_context", "team_basic", "performance", "tactical",
    "players", "injury", "schedule", "environment",
    "odds", "market", "model", "prediction"
]

CONTEXT_REQUIRED = [
    "match_type", "data_confidence", "market_efficiency", "weight_profile"
]

PERFORMANCE_REQUIRED = ["home", "away"]

ODDS_REQUIRED = ["source", "snapshots", "implied_prob"]


def validate(json_data):
    warnings = []

    # 1. 检查顶层字段
    for field in REQUIRED_TOP_FIELDS:
        if field not in json_data:
            warnings.append(f"missing top-level field: {field}")
        elif json_data[field] is None or json_data[field] == {}:
            warnings.append(f"empty field: {field}")

    # 2. match_context
    ctx = json_data.get("match_context", {})
    for field in CONTEXT_REQUIRED:
        if field not in ctx:
            warnings.append(f"match_context missing: {field}")
    mt = ctx.get("match_type", "")
    if mt not in ["normal_league", "key_match", "cup_knockout", "derby", "qualifier", "friendly"]:
        warnings.append(f"match_context.match_type unknown: {mt}")
    dc = ctx.get("data_confidence", 0)
    if not (0 < dc <= 1):
        warnings.append(f"match_context.data_confidence out of range: {dc}")

    # 3. odds
    odds = json_data.get("odds", {})
    snapshots = odds.get("snapshots", [])
    if len(snapshots) < 1:
        warnings.append("odds.snapshots empty (need ≥1 timepoint)")
    implied = odds.get("implied_prob", {})
    total = implied.get("home_pct", 0) + implied.get("draw_pct", 0) + implied.get("away_pct", 0)
    if not (95 < total < 105):
        warnings.append(f"odds.implied_prob sum off: {total:.1f}%")

    # 4. performance
    perf = json_data.get("performance", {})
    for side in PERFORMANCE_REQUIRED:
        if side not in perf:
            warnings.append(f"performance missing: {side}")
        else:
            fs = perf[side].get("form_score", 0)
            if not (-0.25 <= fs <= 0.25):
                warnings.append(f"performance.{side}.form_score out of range: {fs}")

    # 5. market（如果已补齐）
    market = json_data.get("market", {})
    if market:
        if "overheating" not in market:
            warnings.append("market missing: overheating")
        if "market_efficiency_score" not in market:
            warnings.append("market missing: market_efficiency_score")

    # 6. model（如果已补齐）
    model = json_data.get("model", {})
    if model:
        for k in ["home_pct", "draw_pct", "away_pct"]:
            v = model.get(k, 0)
            if not (0 <= v <= 100):
                warnings.append(f"model.{k} out of range: {v}")

    return warnings


def validate_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    warnings = validate(data)
    if warnings:
        print(f"⚠️  {filepath}")
        for w in warnings[:10]:
            print(f"   - {w}")
        if len(warnings) > 10:
            print(f"   ... and {len(warnings)-10} more")
    else:
        print(f"✅  {filepath}")
    return warnings


if __name__ == "__main__":
    if len(sys.argv) > 1:
        validate_file(sys.argv[1])
    else:
        print("用法: python schema_validator.py <adapter_output.json>")
