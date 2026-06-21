"""
蒙特卡洛模拟足球比赛结果
通过大量模拟计算各种结果的概率分布
"""
import random
import math
import json
from collections import Counter

def poisson_random(lam):
    """生成泊松分布随机数"""
    if lam <= 0:
        return 0
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

def simulate_match(home_avg, away_avg):
    """模拟一场比赛"""
    return poisson_random(home_avg), poisson_random(away_avg)

def run_simulation(home_avg, away_avg, n=50000):
    """
    蒙特卡洛模拟
    n=50000 表示模拟5万场比赛
    """
    outcomes = {"主胜": 0, "平局": 0, "客胜": 0}
    scorelines = Counter()
    total_goals = Counter()

    for _ in range(n):
        h, a = simulate_match(home_avg, away_avg)

        if h > a: outcomes["主胜"] += 1
        elif h == a: outcomes["平局"] += 1
        else: outcomes["客胜"] += 1

        scorelines[f"{h}:{a}"] += 1
        total_goals[h + a] += 1

    def pct(count): return round(count / n * 100, 2)

    return {
        "模拟场次": n,
        "胜平负概率": {k: f"{pct(v)}%" for k, v in outcomes.items()},
        "最可能比分": [
            {s: f"{pct(c)}%"}
            for s, c in scorelines.most_common(12)
        ],
        "总进球分布": {
            f"{k}球": f"{pct(v)}%"
            for k, v in sorted(total_goals.items())
            if v / n > 0.005  # 只显示概率>0.5%的
        }
    }

def run_simulation_with_seed(home_avg, away_avg, n=50000, seed=42):
    """带种子的模拟，结果可复现"""
    random.seed(seed)
    return run_simulation(home_avg, away_avg, n)

if __name__ == "__main__":
    result = run_simulation(1.8, 1.3, 50000)
    print(json.dumps(result, indent=2, ensure_ascii=False))
