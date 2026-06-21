"""
泊松分布足球比分分析工具
用于计算比赛进球概率、最可能比分、胜负平概率
"""
import math
import json

def poisson_prob(k, lam):
    """泊松分布概率 P(X=k)"""
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

def match_outcome_probs(home_avg, away_avg, max_goals=8):
    """计算胜平负概率"""
    home_win = draw = away_win = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_prob(h, home_avg) * poisson_prob(a, away_avg)
            if h > a: home_win += p
            elif h == a: draw += p
            else: away_win += p
    return {"主胜": home_win, "平局": draw, "客胜": away_win}

def total_goals_probs(home_avg, away_avg, max_goals=10):
    """计算总进球数概率"""
    probs = {}
    for t in range(max_goals + 1):
        prob = 0.0
        for h in range(t + 1):
            a = t - h
            prob += poisson_prob(h, home_avg) * poisson_prob(a, away_avg)
        probs[f"{t}球"] = prob
    return probs

def top_scorelines(home_avg, away_avg, max_goals=6, top_n=10):
    """列出概率最高的比分"""
    scores = {}
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_prob(h, home_avg) * poisson_prob(a, away_avg)
            scores[f"{h}:{a}"] = p
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores[:top_n]

def expected_goals(home_avg, away_avg):
    """计算期望进球"""
    return {"主队期望进球": round(home_avg, 2), "客队期望进球": round(away_avg, 2)}

def full_analysis(home_team, away_team, home_avg, away_avg):
    """完整分析"""
    return {
        "比赛": f"{home_team} vs {away_team}",
        "期望进球": expected_goals(home_avg, away_avg),
        "胜平负概率": {k: f"{v*100:.1f}%" for k, v in match_outcome_probs(home_avg, away_avg).items()},
        "总进球概率": {k: f"{v*100:.1f}%" for k, v in total_goals_probs(home_avg, away_avg).items()},
        "最可能比分": [{s: f"{p*100:.1f}%"} for s, p in top_scorelines(home_avg, away_avg)]
    }

if __name__ == "__main__":
    # 测试用例
    result = full_analysis("切尔西", "阿森纳", 1.8, 1.3)
    print(json.dumps(result, indent=2, ensure_ascii=False))
