import json, math, random

def poisson_pmf(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def simulate_monte_carlo(lam_h, lam_a, n=100000):
    results = {"home": 0, "draw": 0, "away": 0}
    scores = {}
    goals_dist = {g: 0 for g in range(11)}
    for _ in range(n):
        h = 0
        p_h = math.exp(-lam_h)
        r = random.random()
        cdf = p_h
        while cdf < r and h < 20:
            h += 1
            p_h *= lam_h / h
            cdf += p_h
        a = 0
        p_a = math.exp(-lam_a)
        r2 = random.random()
        cdf2 = p_a
        while cdf2 < r2 and a < 20:
            a += 1
            p_a *= lam_a / a
            cdf2 += p_a
        if h > a:
            results["home"] += 1
        elif h == a:
            results["draw"] += 1
        else:
            results["away"] += 1
        tg = min(h + a, 10)
        goals_dist[tg] += 1
        k = f"{h}-{a}"
        scores[k] = scores.get(k, 0) + 1
    n_f = float(n)
    for k in results:
        results[k] = round(results[k] / n_f * 100, 1)
    for k in goals_dist:
        goals_dist[k] = round(goals_dist[k] / n_f * 100, 1)
    top = sorted(scores.items(), key=lambda x: -x[1])[:15]
    top = [(s, round(p / n_f * 100, 1)) for s, p in top]
    return results, goals_dist, top

# ====================
# Match 1: 瓦勒伦加 vs 汉坎
# ====================
print("=" * 70)
print("周五001 瓦勒伦加 vs 汉坎 | 挪超第16轮 | 2026-08-01 01:00")
print("=" * 70)

# Lambda calculation (league-average weighted approach)
# Vålerenga home: 15 goals in 7 home games = 2.14 avg
# HamKam away: 7 goals in 7 away games = 1.00 avg
# League avg (estimate): ~1.45 goals per team per game
# Adjusted: blend team + league avg (2/3 team, 1/3 league)
league_avg = 1.45
lam_h_raw = (2 * 2.14 + 1 * 1.00) / 3  # offensive blend
lam_a_raw = (2 * 1.00 + 1 * 1.29) / 3  # defensive blend (HKG away scoring vs VAL home conceding)

# H2H correction: HamKam won 1-0 in reverse fixture (May 2026)
# Recent H2H: 2W 4D 3L for Vålerenga - HamKam is a bogey team
# Correction: slightly boost HamKam
lam_h = round(lam_h_raw * 0.95, 3)  # slight discount for H2H weakness
lam_a = round(lam_a_raw * 1.08, 3)  # slight boost for H2H success

print(f"\nLambda计算:")
print(f"  瓦勒伦加主场进球: 15/7 = 2.14")
print(f"  汉坎客场进球: 7/7 = 1.00")
print(f"  瓦勒伦加主场失球: 9/7 = 1.29")
print(f"  汉坎客场失球: 15/7 = 2.14")
print(f"  λ主(修正后) = {lam_h}")
print(f"  λ客(修正后) = {lam_a}")
print(f"  期望总进球: {round(lam_h + lam_a, 2)}")

results1, goals1, scores1 = simulate_monte_carlo(lam_h, lam_a, 200000)

print(f"\n--- 胜平负概率 ---")
print(f"  主胜(瓦勒伦加): {results1['home']}%")
print(f"  平局: {results1['draw']}%")
print(f"  客胜(汉坎): {results1['away']}%")

# Market odds
had_h, had_d, had_a = 1.49, 4.15, 4.60
total_juice = 1/had_h + 1/had_d + 1/had_a
mkt_h = round((1/had_h) / total_juice * 100, 1)
mkt_d = round((1/had_d) / total_juice * 100, 1)
mkt_a = round((1/had_a) / total_juice * 100, 1)

print(f"\n--- 竞彩去水概率 ---")
print(f"  主胜: {mkt_h}% (赔率{had_h})")
print(f"  平局: {mkt_d}% (赔率{had_d})")
print(f"  客胜: {mkt_a}% (赔率{had_a})")

edge_h = round(results1['home'] - mkt_h, 1)
edge_d = round(results1['draw'] - mkt_d, 1)
edge_a = round(results1['away'] - mkt_a, 1)
print(f"\n--- Edge ---")
print(f"  主胜Edge: {edge_h}pp")
print(f"  平局Edge: {edge_d}pp")
print(f"  客胜Edge: {edge_a}pp")

print(f"\n--- 大小球 ---")
print(f"  ≤2球: {goals1[0]+goals1[1]+goals1[2]}%")
print(f"  >2.5球: {round(goals1[3]+goals1[4]+goals1[5]+goals1[6]+goals1[7]+goals1[8]+goals1[9]+goals1[10],1)}%")
print(f"  >3.5球: {round(goals1[4]+goals1[5]+goals1[6]+goals1[7]+goals1[8]+goals1[9]+goals1[10],1)}%")

print(f"\n--- 比分TOP15 ---")
for s, p in scores1:
    print(f"  {s}: {p}%")

# 让球分析
print(f"\n--- 让球分析 (让1球) ---")
# After adjusting for -1 goal handicap
results_hh1, goals_hh1, scores_hh1 = simulate_monte_carlo(lam_h, lam_a + 1.0, 200000)
print(f"  让1球主胜: {results_hh1['home']}%")
print(f"  让1球平局: {results_hh1['draw']}%")
print(f"  让1球客胜: {results_hh1['away']}%")
hhad_h, hhad_d, hhad_a = 2.43, 3.65, 2.25
total_hh = 1/hhad_h + 1/hhad_d + 1/hhad_a
mkt_hh_h = round((1/hhad_h) / total_hh * 100, 1)
mkt_hh_d = round((1/hhad_d) / total_hh * 100, 1)
mkt_hh_a = round((1/hhad_a) / total_hh * 100, 1)
print(f"  市场去水: 主{mkt_hh_h}% / 平{mkt_hh_d}% / 客{mkt_hh_a}%")
print(f"  Edge: 主{round(results_hh1['home']-mkt_hh_h,1)}pp / 平{round(results_hh1['draw']-mkt_hh_d,1)}pp / 客{round(results_hh1['away']-mkt_hh_a,1)}pp")


# ====================
# Match 2: 博德闪耀 vs 利勒斯特
# ====================
print("\n\n" + "=" * 70)
print("周五002 博德闪耀 vs 利勒斯特 | 挪超第16轮 | 2026-08-01 03:00")
print("=" * 70)

# Bodø/Glimt home: 20 goals in 7 home games = 2.86
# Lillestrøm away: 8 goals in 7 away games = 1.14
# Bodø/Glimt home conceding: 2/7 = 0.29
# Lillestrøm away conceding: 5/7 = 0.71

lam_h2_raw = (2 * 2.86 + 1 * 1.14) / 3  # offensive blend
lam_a2_raw = (2 * 1.14 + 1 * 0.29) / 3  # defensive blend

# Bodø/Glimt has CL qualifying in 5 days (Aug 5) - rotation risk
# Correction: slight attack discount
lam_h2 = round(lam_h2_raw * 0.93, 3)  # CL rotation
lam_a2 = round(lam_a2_raw * 1.05, 3)

print(f"\nLambda计算:")
print(f"  博德闪耀主场进球: 20/7 = 2.86")
print(f"  利勒斯特客场进球: 8/7 = 1.14")
print(f"  博德闪耀主场失球: 2/7 = 0.29")
print(f"  利勒斯特客场失球: 5/7 = 0.71")
print(f"  λ主(修正后) = {lam_h2} (含欧冠轮换折扣)")
print(f"  λ客(修正后) = {lam_a2}")
print(f"  期望总进球: {round(lam_h2 + lam_a2, 2)}")

results2, goals2, scores2 = simulate_monte_carlo(lam_h2, lam_a2, 200000)

print(f"\n--- 胜平负概率 ---")
print(f"  主胜(博德闪耀): {results2['home']}%")
print(f"  平局: {results2['draw']}%")
print(f"  客胜(利勒斯特): {results2['away']}%")

had_h2, had_d2, had_a2 = 1.17, 6.10, 9.00
total_juice2 = 1/had_h2 + 1/had_d2 + 1/had_a2
mkt_h2 = round((1/had_h2) / total_juice2 * 100, 1)
mkt_d2 = round((1/had_d2) / total_juice2 * 100, 1)
mkt_a2 = round((1/had_a2) / total_juice2 * 100, 1)

print(f"\n--- 竞彩去水概率 ---")
print(f"  主胜: {mkt_h2}% (赔率{had_h2})")
print(f"  平局: {mkt_d2}% (赔率{had_d2})")
print(f"  客胜: {mkt_a2}% (赔率{had_a2})")

edge_h2 = round(results2['home'] - mkt_h2, 1)
edge_d2 = round(results2['draw'] - mkt_d2, 1)
edge_a2 = round(results2['away'] - mkt_a2, 1)
print(f"\n--- Edge ---")
print(f"  主胜Edge: {edge_h2}pp")
print(f"  平局Edge: {edge_d2}pp")
print(f"  客胜Edge: {edge_a2}pp")

print(f"\n--- 大小球 ---")
print(f"  ≤2球: {goals2[0]+goals2[1]+goals2[2]}%")
print(f"  >2.5球: {round(goals2[3]+goals2[4]+goals2[5]+goals2[6]+goals2[7]+goals2[8]+goals2[9]+goals2[10],1)}%")
print(f"  >3.5球: {round(goals2[4]+goals2[5]+goals2[6]+goals2[7]+goals2[8]+goals2[9]+goals2[10],1)}%")

print(f"\n--- 比分TOP15 ---")
for s, p in scores2:
    print(f"  {s}: {p}%")

# 让2球分析
print(f"\n--- 让球分析 (让2球) ---")
results_hh2, goals_hh2, scores_hh2 = simulate_monte_carlo(lam_h2, lam_a2 + 2.0, 200000)
print(f"  让2球主胜: {results_hh2['home']}%")
print(f"  让2球平局: {results_hh2['draw']}%")
print(f"  让2球客胜: {results_hh2['away']}%")
hhad_h2, hhad_d2, hhad_a2 = 2.45, 4.20, 2.07
total_hh2 = 1/hhad_h2 + 1/hhad_d2 + 1/hhad_a2
mkt_hh_h2 = round((1/hhad_h2) / total_hh2 * 100, 1)
mkt_hh_d2 = round((1/hhad_d2) / total_hh2 * 100, 1)
mkt_hh_a2 = round((1/hhad_a2) / total_hh2 * 100, 1)
print(f"  市场去水: 主{mkt_hh_h2}% / 平{mkt_hh_d2}% / 客{mkt_hh_a2}%")
print(f"  Edge: 主{round(results_hh2['home']-mkt_hh_h2,1)}pp / 平{round(results_hh2['draw']-mkt_hh_d2,1)}pp / 客{round(results_hh2['away']-mkt_hh_a2,1)}pp")
