# -*- coding: utf-8 -*-
"""
欧冠附加赛两场模型推演 (2026-08-19 03:00)
周二004 费内巴切 vs 里昂 | 周二003 萨格勒布迪纳摩 vs 维京FK
模型: v2.9.0 14维评分卡 + 泊松/MC + C01-C27修正规则
"""
import math, random

def poisson_pmf(k, lam):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def simulate_monte_carlo(lam_h, lam_a, n=200000):
    results = {"home": 0, "draw": 0, "away": 0}
    scores = {}
    over25 = 0
    for _ in range(n):
        h = 0; p_h = math.exp(-lam_h); r = random.random(); cdf = p_h
        while cdf < r and h < 20:
            h += 1; p_h *= lam_h / h; cdf += p_h
        a = 0; p_a = math.exp(-lam_a); r2 = random.random(); cdf2 = p_a
        while cdf2 < r2 and a < 20:
            a += 1; p_a *= lam_a / a; cdf2 += p_a
        if h > a: results["home"] += 1
        elif h == a: results["draw"] += 1
        else: results["away"] += 1
        if h + a >= 3: over25 += 1
        k = f"{h}-{a}"
        scores[k] = scores.get(k, 0) + 1
    n_f = float(n)
    res = {k: round(v / n_f * 100, 1) for k, v in results.items()}
    top = sorted(scores.items(), key=lambda x: -x[1])[:12]
    top = [(s, round(p / n_f * 100, 1)) for s, p in top]
    return res, round(over25 / n_f * 100, 1), top

def handicap_probs(lam_h, lam_a, hcp, n=200000):
    """让球后胜平负"""
    res = {"home": 0, "draw": 0, "away": 0}
    for _ in range(n):
        h = 0; p_h = math.exp(-lam_h); r = random.random(); cdf = p_h
        while cdf < r and h < 20:
            h += 1; p_h *= lam_h / h; cdf += p_h
        a = 0; p_a = math.exp(-lam_a); r2 = random.random(); cdf2 = p_a
        while cdf2 < r2 and a < 20:
            a += 1; p_a *= lam_a / a; cdf2 += p_a
        adj = h + hcp
        if adj > a: res["home"] += 1
        elif adj == a: res["draw"] += 1
        else: res["away"] += 1
    n_f = float(n)
    return {k: round(v / n_f * 100, 1) for k, v in res.items()}

print("=" * 72)
print("周二004 费内巴切 vs 里昂 | 欧冠附加赛首回合 | 2026-08-19 03:00")
print("=" * 72)

# --- 费内巴切 λ 计算 ---
# 近10场: 进25失6 (场均 2.5/0.6); 主场 7胜3平0负
# 里昂近10场: 进25失22 (场均 2.5/2.2); 客场 2胜3平5负
# 欧冠专项: 费内巴切4场进5丢1 (1.25/0.25); 里昂R3 客1-2/主3-0
# 土超揭幕战爆冷 1-2负 (状态折价)
# 基础λ: 费内巴切攻2.3防0.7; 里昂攻1.5防1.8 (联赛强度调整: 法甲>土超但里昂客场弱)
# 校准: 欧冠正赛4场费内巴切仅进4球(1.0/场), 对五大联赛强队打折; 里昂法甲客场虽弱但攻强
lam_fb_h = 1.60   # 费内巴切主场期望进球 (欧冠正赛校准: 1.0/场 + 主场加成 + 联赛强度, 打八折)
lam_fb_a = 1.00   # 里昂客场期望进球 (法甲攻强, 客场疲软但非鱼腩)

print(f"\nλ输入: 费内巴切 {lam_fb_h} | 里昂 {lam_fb_a} | 期望总进球 {round(lam_fb_h+lam_fb_a,2)}")

# 14维修正 (评分卡 +7 → Δλ +0.068 主 / -0.070 客)
lam_h1 = round(lam_fb_h + 0.068 * lam_fb_h, 3)
lam_a1 = round(lam_fb_a - 0.070 * lam_fb_a, 3)

# C22 平局封顶: 市场主胜 2.00 (非<1.60, 不触发C22平局封顶)
# C15 让-1陷阱: 市场盘口半球(非让-1), 不触发C15
# C21 收紧: 卢卡库未100%, 不满足"顶级豪门+近10不败+无欧战分心", 不触发
print(f"14维修正后: λ主 {lam_h1} | λ客 {lam_a1}")

res1, over1, scores1 = simulate_monte_carlo(lam_h1, lam_a1)
print(f"\n--- 胜平负概率 (模型) ---")
print(f"  费内巴切胜: {res1['home']}%")
print(f"  平局: {res1['draw']}%")
print(f"  里昂胜: {res1['away']}%")
print(f"  大2.5: {over1}%")
print(f"  比分Top: {scores1}")

print(f"\n--- 市场对比 ---")
print(f"  欧赔隐含: 主46.1% / 平26.1% / 客27.8%")
print(f"  亚盘半球: 主~50-55%")
print(f"  模型: 主{res1['home']}% / 平{res1['draw']}% / 客{res1['away']}%")

print("=" * 72)
print("周二003 萨格勒布迪纳摩 vs 维京FK | 欧冠附加赛首回合 | 2026-08-19 03:00")
print("=" * 72)

# --- 萨格勒布 λ 计算 ---
# 近10场: 进23失6 (场均 2.3/0.6); 主场 7胜3平0负
# 维京近10场: 进20失12 (场均 2.0/1.2); 客场 6胜2平2负
# 联赛强度: 克甲≈挪超 (两小联赛互搏, C07不适用)
# 克甲新赛季前4轮 (C27 大球上浮适用)
# 3名新援不报名 (阵容深度打折)
# 基础λ: 萨格勒布攻2.1防0.6; 维京攻0.9防1.2
# 校准: 萨格勒布欧冠Q1对图恩2场仅2球, 克媒称"轻微热门"非碾压; 维京挪超中上游客场不弱
# 二次校准: 3新援不报名 + 克甲强度低 + 维京客场6胜2平2负 → 主胜压到60-65%档
lam_dz_h = 1.65   # 萨格勒布主场期望进球 (欧冠校准: 对图恩1.0/场, 主场加成, 再打折)
lam_dz_a = 0.95   # 维京客场期望进球 (挪超客场6胜2平2负, 非鱼腩)

print(f"\nλ输入: 萨格勒布 {lam_dz_h} | 维京 {lam_dz_a} | 期望总进球 {round(lam_dz_h+lam_dz_a,2)}")

# 14维修正 (评分卡 +7 → Δλ +0.178 主 / -0.180 客)
lam_h2 = round(lam_dz_h + 0.178 * lam_dz_h, 3)
lam_a2 = round(lam_dz_a - 0.180 * lam_dz_a, 3)

# C27 赛季初大球上浮: 大2.5 +10-15pp (克甲前4轮)
# C15 让-1陷阱: 待市场盘口确认; 若萨格勒布让-1且定价<2.00 需评估
print(f"14维修正后: λ主 {lam_h2} | λ客 {lam_a2}")

res2, over2, scores2 = simulate_monte_carlo(lam_h2, lam_a2)
print(f"\n--- 胜平负概率 (模型, C27大球+12pp) ---")
print(f"  萨格勒布胜: {res2['home']}%")
print(f"  平局: {res2['draw']}%")
print(f"  维京胜: {res2['away']}%")
print(f"  大2.5 (原始): {over2}% → 加C27后 ~{min(over2+12, 85)}%")
print(f"  比分Top: {scores2}")

print(f"\n--- 市场对比 ---")
print(f"  MatchPulse: 大2.5 62%")
print(f"  克媒定性: 迪纳摩轻微热门")
print(f"  模型: 主{res2['home']}% / 平{res2['draw']}% / 客{res2['away']}%")
