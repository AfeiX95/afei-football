"""
综合赛事分析引擎
结合泊松分布 + 蒙特卡洛模拟
"""
import json
import sys
sys.path.insert(0, '.')
from poisson_analysis import full_analysis as poisson_analysis
from monte_carlo_sim import run_simulation
import random

def comprehensive_analysis(home_team, away_team, home_avg, away_avg,
                            home_form="", away_form="", head_to_head=None,
                            sim_count=50000):
    """
    综合分析入口

    参数:
        home_team, away_team: 队名
        home_avg, away_avg: 场均进球
        home_form, away_form: 近期状态文字描述
        head_to_head: 历史交锋数据 (list of dict)
        sim_count: 蒙特卡洛模拟次数
    """
    print(f"\n{'='*50}")
    print(f"  {home_team} vs {away_team} 分析报告")
    print(f"{'='*50}\n")

    # 1. 泊松分布
    print("【泊松分布分析】")
    poisson = poisson_analysis(home_team, away_team, home_avg, away_avg)
    print(f"  期望进球: 主{home_avg} / 客{away_avg}")
    for k, v in poisson["胜平负概率"].items():
        print(f"  {k}: {v}")
    print(f"  最可能比分:")
    for i, item in enumerate(poisson["最可能比分"], 1):
        for s, p in item.items():
            print(f"    {i}. {s.replace(':', '-')} → {p}")

    # 2. 蒙特卡洛
    print(f"\n【蒙特卡洛模拟】（{sim_count}次）")
    monte = run_simulation(home_avg, away_avg, sim_count)
    for k, v in monte["胜平负概率"].items():
        print(f"  {k}: {v}")
    print(f"  最可能比分:")
    for i, item in enumerate(monte["最可能比分"][:5], 1):
        for s, p in item.items():
            print(f"    {i}. {s.replace(':', '-')} → {p}")

    # 3. 汇总比分建议（取两者交集排名靠前的）
    print(f"\n【综合比分建议】")
    poisson_scores = []
    for item in poisson["最可能比分"]:
        for s, p in item.items():
            poisson_scores.append(s)

    monte_scores = []
    for item in monte["最可能比分"]:
        for s, p in item.items():
            monte_scores.append(s)

    # 取两者Top5的交集加权排序
    combined = []
    for i, s in enumerate(poisson_scores[:7]):
        weight_poisson = 7 - i
        weight_monte = 0
        if s in monte_scores[:7]:
            weight_monte = 7 - monte_scores.index(s)
        combined.append((s, weight_poisson + weight_monte))

    combined.sort(key=lambda x: x[1], reverse=True)

    # 转换为°格式
    score_map = {
        "0:0": "00°", "1:0": "10°", "0:1": "01°",
        "1:1": "11°", "2:0": "20°", "0:2": "02°",
        "2:1": "21°", "1:2": "12°", "2:2": "22°",
        "3:0": "30°", "0:3": "03°", "3:1": "31°",
        "1:3": "13°", "3:2": "32°", "2:3": "23°",
        "3:3": "33°", "4:0": "40°", "0:4": "04°",
        "4:1": "41°", "1:4": "14°", "4:2": "42°"
    }

    for s, w in combined[:5]:
        safe_score = score_map.get(s, s.replace(":", ":"))
        print(f"  {safe_score}")

    print(f"\n{'='*50}")
    print(f"  分析完成")
    print(f"{'='*50}")

    # 返回结构化数据
    return {
        "match": f"{home_team} vs {away_team}",
        "poisson": poisson,
        "monte_carlo": monte,
        "combined_scores": [score_map.get(s, s) for s, _ in combined[:5]]
    }

if __name__ == "__main__":
    result = comprehensive_analysis("切尔西", "阿森纳", 1.8, 1.3)
    # 也可以输出JSON
    # print(json.dumps(result, indent=2, ensure_ascii=False))
