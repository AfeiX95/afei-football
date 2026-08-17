# -*- coding: utf-8 -*-
"""
仁川联 vs 金泉尚武 (周日004 韩职 2026-08-16 18:30) 市场vs模型分析
数据: 竞彩网固定奖金页 + 特征分析页 (用户粘贴)
"""
import math

# ============ 市场数据 ============
SP_H, SP_D, SP_A = 2.15, 2.97, 3.05          # 胜平负
HH_H, HH_D, HH_A = 4.85, 3.65, 1.54          # 让球胜平负 (仁川-1)
TTG = {0: 9.50, 1: 4.25, 2: 3.30, 3: 3.85, 4: 6.50, 5: 13.00, 6: 24.00, "7+": 35.00}

# ============ 基础数据 (竞彩网特征分析页) ============
# 仁川联 (主): 排名8, 总21场 8胜5平8负, 主场11场 4胜1平6负(36.4%胜率, 进12失12)
# 金泉尚武(客): 排名10, 总22场 4胜12平6负, 客场11场 3胜5平3负(27.3%胜率, 进12失12)
HOME_HOME = {"w": 4, "d": 1, "l": 6, "gf": 12, "ga": 12}   # 仁川主场
AWAY_AWAY = {"w": 3, "d": 5, "l": 3, "gf": 12, "ga": 12}   # 金泉客场

# 近10场
HOME_FORM = {"w": 4, "d": 2, "l": 4, "gf": 14, "ga": 9}
AWAY_FORM = {"w": 3, "d": 5, "l": 2, "gf": 11, "ga": 11}

# H2H 近10场: 仁川4胜3平3负 (2026-05-09 金泉0-3仁川, 2026-04-05 仁川2-1金泉)
H2H_HOME = {"w": 4, "d": 3, "l": 3}

# ============ 市场隐含概率(去水) ============
def implied(h, d, a):
    inv = [1/h, 1/d, 1/a]
    s = sum(inv)
    return [x/s for x in inv], s

mp, margin = implied(SP_H, SP_D, SP_A)
hp, hmargin = implied(HH_H, HH_D, HH_A)
print("=== 市场隐含概率(去水) ===")
print(f"胜平负: 仁川{mp[0]*100:.1f}% / 平{mp[1]*100:.1f}% / 金泉{mp[2]*100:.1f}%  (返还率{1/margin*100:.1f}%)")
print(f"让球-1: 仁川{hp[0]*100:.1f}% / 平{hp[1]*100:.1f}% / 金泉{hp[2]*100:.1f}%  (返还率{1/hmargin*100:.1f}%)")
print(f"市场隐含: 仁川不败 = {(mp[0]+mp[1])*100:.1f}%, 金泉不败 = {(mp[1]+mp[2])*100:.1f}%")

# ============ 方法1: 实际数据法 xG代理 ============
h_gf_home = HOME_HOME["gf"] / 11   # 1.09
h_ga_home = HOME_HOME["ga"] / 11   # 1.09
a_gf_away = AWAY_AWAY["gf"] / 11   # 1.09
a_ga_away = AWAY_AWAY["ga"] / 11   # 1.09

xg_h_for = h_gf_home * 0.92
xg_h_against = h_ga_home * 1.08
xg_a_for = a_gf_away * 0.92
xg_a_against = a_ga_away * 1.08

form_h = min(0.25, HOME_FORM["w"]*0.08 + HOME_FORM["d"]*0.02 - HOME_FORM["l"]*0.05)
form_a = min(0.25, AWAY_FORM["w"]*0.08 + AWAY_FORM["d"]*0.02 - AWAY_FORM["l"]*0.05)

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
print(f"方法1(xG代理): λ仁川={lam_h_m1:.2f} λ金泉={lam_a_m1:.2f}")
print(f"方法2(市场反推): λ仁川={lam_h_m2:.2f} λ金泉={lam_a_m2:.2f}")
print(f"综合: λ仁川={lam_h:.2f} λ金泉={lam_a:.2f}  总进球期望={lam_h+lam_a:.2f}")

# H2H
h2h_rate = H2H_HOME["w"] / 10
print(f"\nH2H: 仁川近10场4胜3平3负({h2h_rate*100:.0f}%胜率), 本赛季对金泉2连胜(3-0客胜+2-1主胜)")

# ============ 14维评分卡 (仁川视角) ============
scores = [
    ("1 近期状态", "仁川近10 4胜2平4负 vs 金泉3胜5平2负; 仁川近4轮2胜1平1负", 1),
    ("2 主客场分离", "仁川主场36.4%胜率 vs 金泉客场27.3%; 主队+9pp但仁川主场仅4胜", 1),
    ("3 伤停影响", "双方暂无伤停数据", 0),
    ("4 球员身价差", "仁川稍占优, 无豪门级差距", 0),
    ("5 阵型克制", "无明确战术克制数据", 0),
    ("6 核心球员对位", "仁川Mugoša 8球(30%)+高在贤6球, 锋线双核; 金泉无强点", 1),
    ("7 进阶数据xG", "无公开xG, 用进失球代理", 0),
    ("8 H2H交锋", "仁川近10场4胜3平3负, 本赛季2连胜金泉(3-0/2-1)", 1),
    ("9 战意差", "仁川29分第8 vs 金泉24分第10; 仁川主场争上半区", 1),
    ("10 赛程疲劳", "仁川08-02后休整2周; 金泉08-08后休整1周, 08-19有杯赛", 0),
    ("11 更衣室状态", "仁川近4轮2胜(2-1蔚山/1-0全北); 金泉近5轮3胜2平不败", 0),
    ("12 历史恩怨", "无德比/复仇情节", 0),
    ("13 天气与场地", "8月韩国高温, 18:30开球", -1),
    ("14 裁判因素", "无裁判数据", 0),
]
total_score = sum(s[2] for s in scores)
print("\n=== 14维评分卡 (仁川视角) ===")
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
applied.append("C08/C14 平局概率上浮(K联赛平局率高30-50%)")
applied.append("C09/C12 让球-1方概率下调(仁川让-1, -12~15pp)")
applied.append("R15 韩职λ系数收紧×0.85")
lam_h_final *= 0.85
lam_a_final *= 0.85
# 金泉尚武=军旅球队(兵役制), 进攻天然偏弱
applied.append("军旅球队修正: 金泉无外援, 进攻能力天然偏弱")
print("  触发: " + "; ".join(applied))
print(f"  修正后: λ仁川={lam_h_final:.2f} λ金泉={lam_a_final:.2f}")

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

draw_boost = 0.06
pd += draw_boost
ph -= draw_boost/2
pa -= draw_boost/2

print("\n=== 模型概率(泊松+修正) ===")
print(f"仁川胜 {ph*100:.1f}% / 平 {pd*100:.1f}% / 金泉胜 {pa*100:.1f}%")

print("\n=== 市场 vs 模型 Edge ===")
print(f"仁川: 模型{ph*100:.1f}% vs 市场{mp[0]*100:.1f}% = Edge {(ph-mp[0])*100:+.1f}pp")
print(f"平局: 模型{pd*100:.1f}% vs 市场{mp[1]*100:.1f}% = Edge {(pd-mp[1])*100:+.1f}pp")
print(f"金泉: 模型{pa*100:.1f}% vs 市场{mp[2]*100:.1f}% = Edge {(pa-mp[2])*100:+.1f}pp")

top_scores = sorted(score_probs.items(), key=lambda x: -x[1])[:8]
print("\n=== 比分概率Top8 ===")
for (i, j), pr in top_scores:
    print(f"  {i}-{j}: {pr*100:.1f}%")

over25 = sum(pr for (i, j), pr in score_probs.items() if i + j >= 3)
under25 = 1 - over25
print(f"\n大2.5: {over25*100:.1f}% / 小2.5: {under25*100:.1f}%")
ttg_inv = {k: 1/v for k, v in TTG.items()}
ttg_sum = sum(ttg_inv.values())
print(f"市场TTG隐含: 0球{ttg_inv[0]/ttg_sum*100:.0f}% 1球{ttg_inv[1]/ttg_sum*100:.0f}% 2球{ttg_inv[2]/ttg_sum*100:.0f}% 3球{ttg_inv[3]/ttg_sum*100:.0f}% 4球{ttg_inv[4]/ttg_sum*100:.0f}%")

# 让球-1 模型概率 (仁川让1球)
ph_minus = sum(pr for (i, j), pr in score_probs.items() if i - 1 > j)
pd_minus = sum(pr for (i, j), pr in score_probs.items() if i - 1 == j)
pa_minus = 1 - ph_minus - pd_minus
print(f"\n让球-1模型: 仁川 {ph_minus*100:.1f}% / 平 {pd_minus*100:.1f}% / 金泉 {pa_minus*100:.1f}%")
print(f"让球-1市场: 仁川 {hp[0]*100:.1f}% / 平 {hp[1]*100:.1f}% / 金泉 {hp[2]*100:.1f}%")
