"""
AFEI v3.0 Adapter Layer v1.5
将14维分析文本输出 → 结构化JSON

P1字段完善：team_basic ✅ / market ✅ / injury ✅
"""

import re, json, math

# ===== 全局参数（从model-parameters.json同步）=====
INJURY_IMPACT = {
    "前锋": 0.15, "前锋核心": 0.18,
    "中场": 0.10, "中场核心": 0.15,
    "后卫": 0.07, "后卫核心": 0.10,
    "门将": 0.08
}

def parse_14dim_to_json(md_text, match_id=None):
    result = {
        "match_context": parse_context(md_text),
        "team_basic": parse_team_basic(md_text),
        "performance": parse_performance(md_text),
        "tactical": parse_tactical(md_text),
        "players": parse_players(md_text),
        "injury": parse_injury(md_text),
        "schedule": parse_schedule(md_text),
        "environment": parse_environment(md_text),
        "odds": parse_odds(md_text),
        "market": {},
        "model": parse_model(md_text),
        "prediction": {}
    }
    # market依赖odds和context，后处理
    result["market"] = parse_market(result["odds"], result["match_context"], result["model"])
    if match_id:
        result["match_context"]["match_id"] = match_id
    return result


# ===== Helper =====

def _find_first_num(text, default=None):
    m = re.search(r'(\d+(?:\.\d+)?)', text)
    return float(m.group(1)) if m else default

def _find_all_nums(text):
    return [float(x) for x in re.findall(r'(\d+(?:\.\d+)?)', text)]


# ===== Layer 0: Context =====

def parse_context(md):
    text = md[:2000]
    ctx = {
        "match_type": "normal_league", "match_importance": "normal",
        "data_confidence": 0.90, "market_efficiency": 0.75,
        "home_advantage_modifier": 1.05, "weight_profile": "normal",
        "derby": False, "is_qualifier": False, "season_phase": "mid_season"
    }
    if re.search(r'(资格赛|qualifier|qualifying)', text, re.IGNORECASE):
        ctx.update({"match_type": "qualifier", "data_confidence": 0.55, "market_efficiency": 0.60, "weight_profile": "qualifier", "is_qualifier": True})
    if re.search(r'(半决赛|决赛|淘汰赛|knockout|semi|final|cup)', text, re.IGNORECASE):
        ctx.update({"match_type": "cup_knockout", "market_efficiency": 0.80, "weight_profile": "cup"})
    if re.search(r'(德比|derby|恩怨)', text, re.IGNORECASE):
        ctx.update({"derby": True, "home_advantage_modifier": 1.03, "weight_profile": "derby"})
    if re.search(r'(争冠|保级|降级|6分战|关键战)', text, re.IGNORECASE):
        ctx["match_importance"] = "high"
    if re.search(r'(休赛期|间歇后|长间歇|复赛)', text, re.IGNORECASE):
        ctx["home_advantage_modifier"] = 1.02
    return ctx


# ===== P1: team_basic =====

def parse_team_basic(md):
    """
    从文本中提取两队排名/战绩/进球/失球。
    支持表格格式（| 排名 | 主队值 | 客队值 |）和文本格式。
    """
    data = {"home": {"name": "", "rank": 0, "points": 0}, "away": {"name": "", "rank": 0, "points": 0}}

    # 策略1：表格形式 "| 排名 | 第X | 第Y |" 或 "| 世界排名 | 第X | 第Y |"
    for line in md.split('\n'):
        if re.search(r'\|.*?排名', line):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) >= 3:
                vals = []
                for c in cells[1:3]:
                    m = re.search(r'第?(\d+)', c)
                    if m:
                        vals.append(int(m.group(1)))
                if len(vals) == 2:
                    data["home"]["rank"] = vals[0]
                    data["away"]["rank"] = vals[1]
                    break

    # 策略1b：表格形式 "| 项目 | 队名 (#X, 积分) | 队名 (#Y, 积分) |"
    if not data["home"]["rank"]:
        for line in md.split('\n'):
            all_matches = re.findall(r'\(#(\d+)', line)
            if len(all_matches) == 2:
                data["home"]["rank"] = int(all_matches[0])
                data["away"]["rank"] = int(all_matches[1])
                break

    # 策略2：竞彩格式 "排名: Group X 第X名"
    if not data["home"]["rank"]:
        m = re.search(r'排名.*?第(\d+)名', md[:1000])
        if m:
            data["home"]["rank"] = int(m.group(1))

    # 策略3：提取积分（仅限合理范围3-50分）
    for line in md.split('\n'):
        # 跳过含"90分钟"的行（世界杯/杯赛）
        if '90分钟' in line or '90分' in line.replace('钟',''):
            continue
        m = re.search(r'(\d+)\s*分', line)
        if m:
            pts = int(m.group(1))
            if 3 <= pts <= 50:
                if not data["home"]["points"]:
                    data["home"]["points"] = pts
                elif not data["away"]["points"]:
                    data["away"]["points"] = pts
                    break

    return data


# ===== P1: injury =====

def parse_injury(md):
    """
    从文本中提取伤停信息并量化影响。
    关键词匹配 + 位置权重。
    """
    result = {"home": {"players_out": 0, "key_player_missing": False, "impact_score": 0.0, "details": []},
              "away": {"players_out": 0, "key_player_missing": False, "impact_score": 0.0, "details": []}}

    impact = INJURY_IMPACT

    for side, label in [("home", "主队"), ("away", "客队")]:
        section = extract_section(md, "伤停") or md
        # 截取该侧附近文本
        pos = section.find(label)
        if pos >= 0:
            side_text = section[pos:pos+500]
        else:
            side_text = section[:1000]

        # 计数伤病关键词
        injury_words = ['伤缺', '受伤', '停赛', '缺阵', '伤停', '伤', 'out', 'injured', 'suspended']
        for w in injury_words:
            result[side]["players_out"] += side_text.lower().count(w.lower())

        # 检测核心球员缺阵
        core_words = ['核心', '主力', '头号', '最佳射手', '队长', '关键', '全勤']
        for w in core_words:
            if w in side_text:
                result[side]["key_player_missing"] = True
                break

        # 检测位置信息
        for pos_name, weight in impact.items():
            if pos_name in side_text:
                result[side]["impact_score"] += weight
                if result[side]["key_player_missing"]:
                    result[side]["impact_score"] += 0.03  # 核心加成
                result[side]["details"].append(pos_name)

        # 若没有具体位置信息但数量>0，给默认值
        if result[side]["players_out"] > 0 and result[side]["impact_score"] == 0:
            result[side]["impact_score"] = 0.05

        # 上限
        result[side]["impact_score"] = min(result[side]["impact_score"], 0.35)

    return result


# ===== P1: market =====

def parse_market(odds_data, context, model_data):
    """
    赔率市场异常检测。
    三条规则：过热 / 赔率反向移动 / 模型vs赔率冲突。
    """
    result = {
        "overheating": False, "overheating_score": 0.0,
        "consensus_level": 0.0, "trend_pattern": "unknown",
        "odds_model_conflict": False, "conflict_gap_pp": 0.0,
        "market_efficiency_score": context.get("market_efficiency", 0.75),
        "alerts": []
    }

    snapshots = odds_data.get("snapshots", [])
    mp = odds_data.get("implied_prob", {})
    model = model_data or {}

    if len(snapshots) < 1:
        return result

    latest = snapshots[-1]
    home_odds = latest.get("home", 2.0)
    market_home_pct = mp.get("home_pct", 50)
    model_home_pct = model.get("home_pct", 50)

    # 规则1：热门过热（赔率<1.40 且 模型胜率 < 市场隐含-10pp）
    if home_odds < 1.40:
        gap = market_home_pct - model_home_pct
        if gap > 10:
            result["overheating"] = True
            result["overheating_score"] = round(gap / 100, 2)
            result["alerts"].append("favorite_overheat")

    # 规则2：赔率与模型冲突（差异>15pp）- 仅当模型有有效值时
    if model_home_pct > 0 and market_home_pct > 0:
        conflict = abs(market_home_pct - model_home_pct)
        if conflict > 15:
            result["odds_model_conflict"] = True
            result["conflict_gap_pp"] = round(conflict, 1)
            result["alerts"].append("probability_gap_warning")

    # 规则3：赔率反向移动（热度 vs 走势）
    if len(snapshots) >= 2:
        first = snapshots[0]
        change = first.get("home", 2.0) - home_odds
        trend = "monotonic_down" if change > 0.02 else ("monotonic_up" if change < -0.02 else "stable")
        result["trend_pattern"] = trend
        # 如果主胜赔率下降但home_pct并没有显著优势 → 潜在过热
        if "monotonic_down" in trend and home_odds < 1.50:
            result["alerts"].append("favorite_overheat")

    # 共识度：最高概率 - 最低概率
    probs = [mp.get("home_pct", 0), mp.get("draw_pct", 0), mp.get("away_pct", 0)]
    result["consensus_level"] = round(max(probs) / (sum(probs) or 1), 2)

    return result


# ===== 其余字段（基本保持不变，小幅优化）=====

def extract_section(md, section_name):
    patterns = [
        rf"##\s*{re.escape(section_name)}.*?\n(.*?)(?=\n##\s|\Z)",
        rf"##\s*一[、.].*?{re.escape(section_name)}.*?\n(.*?)(?=\n##|\Z)",
    ]
    for p in patterns:
        m = re.search(p, md, re.DOTALL)
        if m:
            return m.group(1).strip()
    return ""


def parse_performance(md):
    perf = {"home": {"form_score": 0.0, "trend": "stable"}, "away": {"form_score": 0.0, "trend": "stable"}}
    text = extract_section(md, "状态") or extract_section(md, "近况") or extract_section(md, "走势")
    if not text:
        text = md[:3000]
    for side, label in [("home", "主队"), ("away", "客队")]:
        for line in text.split('\n'):
            if label in line:
                m = re.search(r'(\d+)\s*胜.*?(\d+)\s*平.*?(\d+)\s*负', line)
                if m:
                    w, d, l = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    total = w + d + l
                    score = w * 0.08 + d * 0.02 + l * (-0.05)
                    score = max(-0.25, min(0.25, score))
                    perf[side]["form_score"] = round(score, 2)
                    perf[side]["trend"] = "up" if w/total > 0.5 else ("down" if l/total > 0.4 else "stable")
    return perf


def parse_tactical(md):
    return {"home_formation": "", "away_formation": "", "tactical_advantage": ""}


def parse_players(md):
    return {"home": [], "away": []}


def parse_schedule(md):
    return {"home_rest_days": 7, "away_rest_days": 7, "away_travel_km": 0, "home_double_week": False, "away_double_week": False}


def parse_environment(md):
    env = {"weather": {"temperature_c": 20, "rain_probability": 0.0, "wind_kmh": 0, "impact_on_goals": "neutral"},
           "pitch_type": "natural", "referee": {}}
    text = extract_section(md, "天气") or extract_section(md, "环境") or md[:3000]
    m = re.search(r'(\d+)°', text)
    if m:
        env["weather"]["temperature_c"] = int(m.group(1))
    if '雨' in text or 'rain' in text.lower():
        env["weather"]["rain_probability"] = 0.7
        env["weather"]["impact_on_goals"] = "negative"
    m = re.search(r'(人工草皮|人造草|artificial)', text, re.IGNORECASE)
    if m:
        env["pitch_type"] = "artificial"
    return env


def parse_odds(md):
    odds = {"source": "jingcai", "snapshots": [], "implied_prob": {"home_pct": 0, "draw_pct": 0, "away_pct": 0}}
    for line in md.split('\n'):
        m = re.findall(r'(\d+\.\d+)', line)
        if len(m) == 3 and all(1.50 <= float(x) <= 15.0 for x in m):
            h, d, a = float(m[0]), float(m[1]), float(m[2])
            t = 1/h + 1/d + 1/a
            if t > 0:
                odds["implied_prob"].update({
                    "home_pct": round((1/h)/t*100, 1),
                    "draw_pct": round((1/d)/t*100, 1),
                    "away_pct": round((1/a)/t*100, 1)
                })
            odds["snapshots"].append({"home": h, "draw": d, "away": a})
            break  # 只取第一个赔率快照
    return odds


def parse_model(md):
    model = {"lambda_home": 0, "lambda_away": 0, "home_pct": 0, "draw_pct": 0, "away_pct": 0, "over25_pct": 0, "scores": []}
    text = extract_section(md, "数学") or md
    for line in text.split('\n'):
        # λ值
        m = re.search(r'λ.*?(\d+\.\d+)', line)
        if m and not model["lambda_home"]:
            model["lambda_home"] = float(m.group(1))
        # MC概率（格式："主胜XX.X%"）
        for key, label in [("home_pct", "主胜"), ("draw_pct", "平"), ("away_pct", "客胜")]:
            m = re.search(rf'{label}[：:]?\s*(\d+\.?\d*)%', line)
            if m and not model[key]:
                model[key] = float(m.group(1))
    return model


def json_to_file(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


def adapter_pipeline(md_text, output_path=None, match_id=None):
    parsed = parse_14dim_to_json(md_text, match_id)
    if output_path:
        json_to_file(parsed, output_path)
        print(f"✅ Adapter输出: {output_path}")
    return parsed


if __name__ == "__main__":
    test = """
    ## 一、百家欧赔
    | 竞彩 | 2.35 | 3.10 | 2.75 |
    主队排名第6，主场4胜1平1负。
    客队排名第13，客场1胜1平6负。
    伤停：主力前锋伤缺，中场核心缺阵。
    """
    r = adapter_pipeline(test)
    print("team_basic:", json.dumps(r["team_basic"], ensure_ascii=False))
    print("injury:", json.dumps(r["injury"], ensure_ascii=False))
    print("market:", json.dumps(r["market"], ensure_ascii=False))
