"""
泊松分布 + 蒙特卡洛模拟 —— 弗赖堡 vs 布拉加 欧联半决赛次回合
================================================================
方法说明：
1. 基于两队本赛季欧联实际攻防数据，计算期望进球（xG）
2. 用泊松分布（Poisson Distribution）计算各比分概率
3. 用蒙特卡洛（Monte Carlo, 10万次）验证结果
4. 对比纯泊松 vs 蒙特卡洛的差异

数据来源：UEFA官网、WhoScored、FBref（联网核实）
"""

import numpy as np
from scipy.stats import poisson
from collections import Counter

# ============================================================
# 第一步：计算期望进球 (Expected Goals)
# ============================================================
#
# 弗赖堡本赛季欧联主场表现（截至半决赛次回合前）:
#   场次: 5场（3场小组赛+1/8次回合+1/4两回合，不含首回合客场）
#   进球: 14球  → 场均 2.80 球
#   失球: 2球   → 场均 0.40 球
#
# 注意：这里的主场数据包括了小组赛对阵较弱对手。
# 进入淘汰赛后对手更强，且半决赛压力更大。
# 我们取一个保守的 xG 值：1.80（削减退步）
#
# 布拉加本赛季欧联客场表现:
#   场次: 4场（小组赛3场+1/4次回合，不含资格赛）
#   进球: 4球   → 场均 1.00 球
#   失球: 3球   → 场均 0.75 球
#
# 但布拉加队长奥尔塔（4球4助）伤缺，客场攻击力再打折。
# 取 xG：0.85（剔除奥尔塔影响）

xG_home = 1.80  # 弗赖堡期望进球
xG_away = 0.85  # 布拉加期望进球

print("=" * 60)
print("第一步：期望进球（xG）估算")
print("=" * 60)
print(f"""
数据依据：
  弗赖堡欧联主场场均进球 2.80（实际）
  → 淘汰赛对手更强，保守取值: {xG_home}

  布拉加欧联客场场均进球 1.00（实际）
  → 队长奥尔塔（4球4助）缺阵，再打折: {xG_away}
""")

# ============================================================
# 第二步：泊松分布计算各比分概率
# ============================================================
# 泊松分布公式：P(X=k) = (λ^k * e^(-λ)) / k!
# 其中 λ = 期望进球数，k = 进球数
#
# 两队进球相互独立（泊松模型的基本假设），
# 某比分概率 = P(主队进k1球) × P(客队进k2球)

max_goals = 6  # 算到6球，之后的概率可以忽略

print("=" * 60)
print("第二步：泊松分布计算")
print("=" * 60)
print(f"""
泊松公式：P(k) = (λ^k × e^(-λ)) / k!

弗赖堡 λ = {xG_home}
  0球: ({xG_home}^0 × e^(-{xG_home})) / 0! = {poisson.pmf(0, xG_home):.4f}
  1球: ({xG_home}^1 × e^(-{xG_home})) / 1! = {poisson.pmf(1, xG_home):.4f}
  2球: ({xG_home}^2 × e^(-{xG_home})) / 2! = {poisson.pmf(2, xG_home):.4f}
  3球: ({xG_home}^3 × e^(-{xG_home})) / 3! = {poisson.pmf(3, xG_home):.4f}
  4球: ({xG_home}^4 × e^(-{xG_home})) / 4! = {poisson.pmf(4, xG_home):.4f}

布拉加 λ = {xG_away}
  0球: ({xG_away}^0 × e^(-{xG_away})) / 0! = {poisson.pmf(0, xG_away):.4f}
  1球: ({xG_away}^1 × e^(-{xG_away})) / 1! = {poisson.pmf(1, xG_away):.4f}
  2球: ({xG_away}^2 × e^(-{xG_away})) / 2! = {poisson.pmf(2, xG_away):.4f}
  3球: ({xG_away}^3 × e^(-{xG_away})) / 3! = {poisson.pmf(3, xG_away):.4f}
""")

# 计算各比分概率矩阵
score_matrix = {}
for h in range(max_goals + 1):
    for a in range(max_goals + 1):
        prob = poisson.pmf(h, xG_home) * poisson.pmf(a, xG_away)
        score_matrix[(h, a)] = prob

# 比分概率排序
sorted_scores = sorted(score_matrix.items(), key=lambda x: -x[1])

print("各比分概率（前十）:")
for (h, a), prob in sorted_scores[:10]:
    print(f"  {h}-{a}: {prob*100:.1f}%")

# 汇总比赛结果概率
win_home = sum(p for (h, a), p in score_matrix.items() if h > a)
draw = sum(p for (h, a), p in score_matrix.items() if h == a)
win_away = sum(p for (h, a), p in score_matrix.items() if h < a)

print(f"""
比赛结果概率（泊松分布）:
  弗赖堡胜: {win_home*100:.1f}%
  平局:     {draw*100:.1f}%
  布拉加胜: {win_away*100:.1f}%
""")

# ============================================================
# 第三步：蒙特卡洛模拟
# ============================================================
# 从泊松分布中随机采样，模拟比赛10万次

np.random.seed(42)
n_simulations = 100000

home_goals_sim = np.random.poisson(xG_home, n_simulations)
away_goals_sim = np.random.poisson(xG_away, n_simulations)

results = Counter()
for h, a in zip(home_goals_sim, away_goals_sim):
    if h > a:
        results["home_win"] += 1
    elif h == a:
        results["draw"] += 1
    else:
        results["away_win"] += 1

# 最常出现的比分
score_counter = Counter()
for h, a in zip(home_goals_sim, away_goals_sim):
    score_counter[(h, a)] += 1

print("=" * 60)
print(f"第三步：蒙特卡洛模拟（{n_simulations:,} 次）")
print("=" * 60)
print(f"""
模拟逻辑:
  for i in range({n_simulations:,}):
      home_goals = random.poisson(λ={xG_home})  → 从泊松分布采样
      away_goals = random.poisson(λ={xG_away})
      if home_goals > away_goals → 弗赖堡胜
      if home_goals == away_goals → 平局
      if home_goals < away_goals → 布拉加胜

比赛结果概率（蒙特卡洛）:
  弗赖堡胜: {results['home_win']/n_simulations*100:.1f}%
  平局:     {results['draw']/n_simulations*100:.1f}%
  布拉加胜: {results['away_win']/n_simulations*100:.1f}%
""")

# 最可能比分
print("最可能比分（蒙特卡洛，前十）:")
for (h, a), count in score_counter.most_common(10):
    print(f"  {h}-{a}: {count/n_simulations*100:.1f}%")

# 计算总进球分布
total_goals = home_goals_sim + away_goals_sim
over_under = Counter()
for tg in total_goals:
    if tg >= 3:
        over_under["over_2.5"] += 1
    else:
        over_under["under_2.5"] += 1

print(f"""
大小球概率（蒙特卡洛）:
  大2.5球: {over_under['over_2.5']/n_simulations*100:.1f}%
  小2.5球: {over_under['under_2.5']/n_simulations*100:.1f}%
""")

# ============================================================
# 第四步：晋级概率（结合首回合2-1）
# ============================================================
# 首回合布拉加 2-1 弗赖堡
# 弗赖堡赢1球 → 加时
# 弗赖堡赢2球+ → 直接晋级
# 布拉加赢或平 → 直接晋级

advance_freiburg_direct = sum(p for (h, a), p in score_matrix.items()
                               if h - a >= 2)  # 净胜2球+
advance_freiburg_ot = sum(p for (h, a), p in score_matrix.items()
                           if h - a == 1)  # 净胜1球 → 加时
advance_braga = sum(p for (h, a), p in score_matrix.items()
                     if h - a <= 0)  # 布拉加不败

# 加时赛假设50%/50%（简化）
advance_freiburg_total = advance_freiburg_direct + advance_freiburg_ot * 0.5

print("=" * 60)
print("第四步：晋级概率（结合首回合结果2-1）")
print("=" * 60)
print(f"""
首回合：布拉加 2-1 弗赖堡 → 弗赖堡需净胜2球直接晋级

弗赖堡晋级概率（含加时50%假设）:
  常规时间净胜2球+: {advance_freiburg_direct*100:.1f}%
  常规时间净胜1球（进加时）: {advance_freiburg_ot*100:.1f}%
  总晋级概率: {advance_freiburg_total*100:.1f}%

布拉加晋级概率:
  打平或赢直接晋级: {advance_braga*100:.1f}%
""")

# ============================================================
# 第五步：敏感性分析
# ============================================================
print("=" * 60)
print("第五步：敏感性分析（xG变动对结果的影响）")
print("=" * 60)
print("""
xG取值本身有主观成分，看看不同xG下结果如何变化：
""")

xG_home_variants = [1.6, 1.8, 2.0]
xG_away_variants = [0.7, 0.85, 1.0]

for xh in xG_home_variants:
    for xa in xG_away_variants:
        ph = sum(poisson.pmf(h, xh) * poisson.pmf(a, xa)
                 for h in range(7) for a in range(7) if h > a)
        pd = sum(poisson.pmf(h, xh) * poisson.pmf(a, xa)
                 for h in range(7) for a in range(7) if h == a)
        pa = sum(poisson.pmf(h, xh) * poisson.pmf(a, xa)
                 for h in range(7) for a in range(7) if h < a)
        print(f"  xG=({xh:.1f},{xa:.1f}) → 主胜{ph*100:.1f}% / 平{pd*100:.1f}% / 客胜{pa*100:.1f}%")
