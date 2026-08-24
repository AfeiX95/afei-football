# -*- coding: utf-8 -*-
"""
周二005 欧冠附加赛次回合 LASK林茨 vs 凯尔特人 (2026-08-26 03:00) 全面分析
首回合: 凯尔特人 3:0 LASK林茨 (2026-08-20, 总比分 3:0 凯尔特人领先)
数据: 竞彩网特征分析页 (用户粘贴)
"""
import math
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ============ 市场数据 (竞彩网 2026-08-24 13:15) ============
SP_H, SP_D, SP_A = 1.80, 3.70, 3.30          # 胜平负
HC_H, HC_D, HC_A = 3.25, 3.75, 1.80          # 让球-1 (LASK林茨-1)

# ============ 基础数据 (竞彩特征分析页) ============
# LASK林茨(主): 近10场6胜0平4负(进25失10净+15); 主场近10 6胜2平2负; 场均进2.5失1.0
# 凯尔特人(客): 近10场6胜3平1负(进24失11净+13); 客场近10 6胜2平2负; 场均进2.4失1.1
HOME_GF, HOME_GA = 2.5, 1.0
AWAY_GF, AWAY_GA = 2.4, 1.1
HOME_HOME = {"w": 6, "d": 2, "l": 2, "n": 10}     # LASK主场近10
AWAY_AWAY = {"w": 6, "d": 2, "l": 2, "n": 10}     # 凯尔特人客场近10

# 近10场战况
HOME_FORM = {"w": 6, "d": 0, "l": 4, "gf": 25, "ga": 10}
AWAY_FORM = {"w": 6, "d": 3, "l": 1, "gf": 24, "ga": 11}

# H2H (LASK视角): 近1场 0胜1负 (2026-08-20 客场0:3)
H2H = {"w": 0, "d": 0, "l": 1}

# ============ 市场隐含概率(去水) ============
def implied(h, d, a):
    inv = [1/h, 1/d, 1/a]
    s = sum(inv)
    return [x/s for x in inv], s

mp, margin = implied(SP_H, SP_D, SP_A)
hc, hc_margin = implied(HC_H, HC_D, HC_A)
print("=== 市场隐含概率(去水) ===")
print(f"胜平负: LASK林茨{mp[0]*100:.1f}% / 平{mp[1]*100:.1f}% / 凯尔特人{mp[2]*100:.1f}%  (返还率{1/margin*100:.1f}%)")
print(f"让-1: 净胜2+ {hc[0]*100:.1f}% / 净胜1 {hc[1]*100:.1f}% / 平或负 {hc[2]*100:.1f}%")
print(f"LASK不败 = {(mp[0]+mp[1])*100:.1f}%")

# ============ 方法1: 实际数据法 xG代理 ============
xg_h_for = HOME_GF * 0.92
xg_h_against = HOME_GA * 1.08
xg_a_for = AWAY_GF * 0.92
xg_a_against = AWAY_GA * 1.08

form_h = min(0.25, (HOME_FORM["w"]*0.08 + HOME_FORM["d"]*0.02 - HOME_FORM["l"]*0.05)) * 0.7
form_a = min(0.25, (AWAY_FORM["w"]*0.08 + AWAY_FORM["d"]*0.02 - AWAY_FORM["l"]*0.05)) * 0.7

lam_h_m1 = (xg_h_for + xg_a_against) / 2 + form_h
lam_a_m1 = (xg_a_for + xg_h_against) / 2 + form_a

# ============ 方法2: 市场反推法 ============
lam_h_m2 = 0.4 + mp[0] * 3.2
lam_a_m2 = 0.2 + mp[2] * 3.2

# ============ 综合λ ============
lam_h = (lam_h_m1 + lam_h_m2) / 2
lam_a = (lam_a_m1 + lam_a_m2) / 2
if abs(lam_h_m1 - lam_h_m2) > 0.5:
    lam_h = lam_h_m1
if abs(lam_a_m1 - lam_a_m2) > 0.5:
    lam_a = lam_a_m1

print("\n=== λ估算 ===")
print(f"方法1(xG代理): λLASK={lam_h_m1:.2f} λ凯尔特人={lam_a_m1:.2f}")
print(f"方法2(市场反推): λLASK={lam_h_m2:.2f} λ凯尔特人={lam_a_m2:.2f}")
print(f"综合: λLASK={lam_h:.2f} λ凯尔特人={lam_a:.2f}  总进球期望={lam_h+lam_a:.2f}")

# ============ 14维评分卡 (LASK林茨视角) ============
scores = [
    ("1 近期状态", "LASK近10 6胜0平4负 vs 凯尔特人6胜3平1负——凯尔特人更稳(不败率90%)", -1),
    ("2 主客场分离", "LASK主场6胜2平2负 vs 凯尔特人客场6胜2平2负——持平", 0),
    ("3 伤停影响", "双方暂无伤停数据", 0),
    ("4 球员身价差", "凯尔特人苏超豪门(欧冠常客) vs LASK奥甲——凯尔特人占优", -1),
    ("5 阵型克制", "LASK必须压上攻3球 vs 凯尔特人3-0领先守成反击(苏超5:1基马诺克)——反击犀利", -1),
    ("6 核心球员对位", "LASK Durán 2球(67%占比)单点依赖 vs 凯尔特人多点进攻", 0),
    ("7 进阶数据xG", "用主客分离进失球代理", 0),
    ("8 H2H交锋", "首回合客场0:3惨败——心理阴影", -1),
    ("9 战意差", "LASK主场必须3-0+翻盘(搏命) vs 凯尔特人3-0领先(输3球才加时)——LASK主场战意强但任务艰巨", 1),
    ("10 赛程疲劳", "LASK 08-30奥甲(4天后); 凯尔特人08-29苏超(3天后)——均无大碍", 0),
    ("11 更衣室状态", "LASK 0:3惨败后士气受挫(-1); 凯尔特人苏超开局全胜士气高(+1)——对冲", 0),
    ("12 历史恩怨", "无", 0),
    ("13 天气与场地", "奥地利主场", 0),
    ("14 裁判因素", "无数据", 0),
]
total_score = sum(s[2] for s in scores)
print("\n=== 14维评分卡 (LASK林茨视角) ===")
for name, reason, sc in scores:
    print(f"  {name}: {sc:+d}  ({reason})")
print(f"  合计: {total_score:+d}")

# λ修正
delta_h = total_score * 0.04
delta_a = -delta_h * 0.6
lam_h_final = max(0.3, min(3.5, lam_h + delta_h))
lam_a_final = max(0.1, min(2.5, lam_a + delta_a))

# 修正规则叠加
print("\n=== 修正规则触发 ===")
applied = []
applied.append("C15b(1.50-2.00让-1)触发: 1.80 → 主胜-10~15pp")
applied.append("战意修正: 落后方(0:3)主场搏命λ+0.1 / 领先方(3:0)客场守成λ-0.1")
applied.append("C33候选 1球主义: 领先方守成+净胜1球走盘风险观察")
print("  触发: " + "; ".join(applied))
print(f"  修正后: λLASK={lam_h_final:.2f} λ凯尔特人={lam_a_final:.2f}")

# ============ 泊松概率矩阵 ============
def poisson_pmf(lam, k):
    return math.exp(-lam) * lam**k / math.factorial(k)

MAXG = 8
p_h = [poisson_pmf(lam_h_final, k) for k in range(MAXG)]
p_a = [poisson_pmf(lam_a_final, k) for k in range(MAXG)]
s_h, s_a = sum(p_h), sum(p_a)
p_h = [x/s_h for x in p_h]
p_a = [x/s_a for x in p_a]

ph, pd, pa = 0.0, 0.0, 0.0
score_probs = {}
for i in range(MAXG):
    for j in range(MAXG):
        pr = p_h[i] * p_a[j]
        score_probs[(i, j)] = pr
        if i > j: ph += pr
        elif i == j: pd += pr
        else: pa += pr

draw_boost = 0.03
pd += draw_boost
ph -= draw_boost/2
pa -= draw_boost/2

print("\n=== 模型概率(泊松+修正) ===")
print(f"LASK胜 {ph*100:.1f}% / 平 {pd*100:.1f}% / 凯尔特人胜 {pa*100:.1f}%")

print("\n=== 市场 vs 模型 Edge ===")
print(f"LASK: 模型{ph*100:.1f}% vs 市场{mp[0]*100:.1f}% = Edge {(ph-mp[0])*100:+.1f}pp")
print(f"平局: 模型{pd*100:.1f}% vs 市场{mp[1]*100:.1f}% = Edge {(pd-mp[1])*100:+.1f}pp")
print(f"凯尔特人: 模型{pa*100:.1f}% vs 市场{mp[2]*100:.1f}% = Edge {(pa-mp[2])*100:+.1f}pp")

# 让-1 打穿
hc_cover = sum(pr for (i, j), pr in score_probs.items() if i - j >= 2)
hc_push = sum(pr for (i, j), pr in score_probs.items() if i - j == 1)
hc_lose = 1 - hc_cover - hc_push
print(f"\n让-1(LASK-1): 净胜2+ {hc_cover*100:.1f}% / 净胜1 {hc_push*100:.1f}% / 平或负 {hc_lose*100:.1f}%")
print(f"  模型净胜2+ {hc_cover*100:.1f}% vs 市场{hc[0]*100:.1f}% = Edge {(hc_cover-hc[0])*100:+.1f}pp")

top_scores = sorted(score_probs.items(), key=lambda x: -x[1])[:8]
print("\n=== 比分概率Top8 ===")
for (i, j), pr in top_scores:
    print(f"  {i}-{j}: {pr*100:.1f}%")

over25 = sum(pr for (i, j), pr in score_probs.items() if i + j >= 3)
print(f"\n大2.5: {over25*100:.1f}% / 小2.5: {(1-over25)*100:.1f}% (市场TTG大2.5约64%)")

# 晋级概率 (总比分 0:3)
# LASK晋级: 赢4+球(总4:3+)直接晋级; 赢3球(总3:3)加时
win_by3 = sum(pr for (i, j), pr in score_probs.items() if i - j == 3)
win_by4plus = sum(pr for (i, j), pr in score_probs.items() if i - j >= 4)
print(f"\n=== 晋级概率推演 (总比分0:3, LASK视角) ===")
print(f"LASK直接晋级(赢4球+): {win_by4plus*100:.2f}%")
print(f"LASK赢3球进加时(总3:3): {win_by3*100:.2f}%")
print(f"凯尔特人直接晋级: {(1-win_by3-win_by4plus)*100:.1f}%")
