#!/usr/bin/env python3
"""
蒙特卡洛足球比赛模拟 — 10万次泊松采样
使用方式：在 execute_code 中执行此脚本，传入主客队λ值
"""

import math, random, json

def poisson_sample(lmbda):
    """泊松采样（反函数法）"""
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

def simulate_match(home_lambda, away_lambda, iterations=100000):
    """
    模拟单场比赛
    
    参数:
        home_lambda: 主队期望进球
        away_lambda: 客队期望进球
        iterations: 模拟次数（默认10万）
    
    返回:
        results: {'1':主胜%, 'X':平%, '2':客胜%}
        goals_total: {0球%: ..., 1球%: ..., ...}
        top_scores: [('1-0', 12.5%), ('2-0', 11.2%), ...]
    """
    results = {"1": 0, "X": 0, "2": 0}
    goals_total = {g: 0 for g in range(9)}
    scores = {}
    
    for _ in range(iterations):
        h = poisson_sample(home_lambda)
        a = poisson_sample(away_lambda)
        g = h + a
        
        if h > a:
            results["1"] += 1
        elif h == a:
            results["X"] += 1
        else:
            results["2"] += 1
        
        goals_total[min(g, 8)] += 1
        
        score_key = f"{h}-{a}"
        scores[score_key] = scores.get(score_key, 0) + 1
    
    # 归一化
    for k in results:
        results[k] = round(results[k] / iterations * 100, 1)
    for k in goals_total:
        goals_total[k] = round(goals_total[k] / iterations * 100, 1)
    
    # Top比分
    top_scores = sorted(scores.items(), key=lambda x: -x[1])[:5]
    top_scores = [(s, round(p / iterations * 100, 1)) for s, p in top_scores]
    
    return results, goals_total, top_scores


# ====== 使用示例 ======
if __name__ == '__main__':
    # 阿根廷 λ=1.80 vs 奥地利 λ=0.85
    hl, al = 1.80, 0.85
    r, g, ts = simulate_match(hl, al, 100000)
    
    print(f"主队 λ={hl}  客队 λ={al}")
    print()
    print(f"主队胜: {r['1']}%")
    print(f"平局:   {r['X']}%")
    print(f"客队胜: {r['2']}%")
    print()
    
    # 总进球分布
    for i in range(9):
        if g[i] > 0.5:
            print(f"  {i}球: {g[i]}%")
    
    # 大小球
    over25 = sum(g[i] for i in range(3, 9))
    print(f"\n大2.5球: {over25}%")
    print(f"小2.5球: {100 - over25:.1f}%")
    
    print(f"\n最可能比分 Top 5:")
    for s, p in ts:
        print(f"  {s}  {p}%")
    
    print(f"\n--- 敏感性分析 ---")
    for label, hl2, al2 in [("保守(-0.2)", hl-0.2, al-0.2), ("基准", hl, al), ("激进(+0.2)", hl+0.2, al+0.2)]:
        r2, _, _ = simulate_match(hl2, al2, 100000)
        print(f"  {label}: 主队{r2['1']}%  平{r2['X']}%  客队{r2['2']}%")
