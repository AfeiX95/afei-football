# -*- coding: utf-8 -*-
"""
富川FC vs 全北现代 (周日003 韩职 2026-08-16 18:30) 市场vs模型分析
数据: 竞彩网固定奖金页 + 特征分析页 (用户粘贴)
"""
import math
import random

random.seed(42)

# ============ 市场数据 ============
SP_H, SP_D, SP_A = 4.35, 3.42, 1.65          # 胜平负
HH_H, HH_D, HH_A = 1.95, 3.35, 3.15          # 让球胜平负 (富川+1)
TTG = {0: 11.00, 1: 4.50, 2: 3.35, 3: 3.75, 4: 6.00, 5: 12.00, 6: 22.00, "7+": 33.00}

# ============ 基础数据 (竞彩网特征分析页) ============
# 富川FC (主): 排名11, 总22场 5胜9平8负, 主场11场 1胜5平5负(9%胜率, 进9失14)
# 全北现代(客): 排名3, 总22场 9胜7平6负, 客场11场 4胜5平2负(36.4%胜率, 进11失6)
HOME_HOME = {"w": 1, "d": 5, "l": 5, "gf": 9, "ga": 14}   # 富川主场
AWAY_AWAY = {"w": 4, "d": 5, "l": 2, "gf": 11, "ga": 6}   # 全北客场

# 近10场
HOME_FORM = {"w": 3, "d": 5, "l": 2, "gf": 15, "ga": 10}
AWAY_FORM = {"w": 3, "d": 4, "l": 3, "gf": 9, "ga": 8}

# H2H 近4场: 富川2胜2平0负 (2026-05-13 富川0-0全北, 2026-03-01 全北2-3富川, 2017杯全北0-0, 2016杯全北2-3)
H2H_HOME = {"w": 2, "d": 2, "l": 0}

# ============ 市场隐含概率(去水) ============
def implied(h, d, a):
    inv = [1/h, 1/d, 1/a]
    s = sum(inv)
    return [x/s for x in inv], s

mp, margin = implied(SP_H, SP_D, SP_A)
hp, hmargin = implied(HH_H, HH_D, HH_A)
print("=== 市场隐含概率(去水) ===")
print(f"胜平负: 富川{mp[0]*100:.1f}% / 平{mp[1]*100:.1f}% / 全北{mp[2]*100:.1f}%  (返还率{1/margin*100:.1f}%)")
print(f"让球+1: 富川{hp[0]*100:.1f}% / 平{hp[1]*100:.1f}% / 全北{hp[2]*100:.1f}%  (返还率{1/hmargin*100:.1f}%)")
print(f"市场隐含: 富川不败 = {(mp[0]+mp[1])*100:.1f}%, 全北不败 = {(mp[1]+mp[2])*100:.1f}%")

# ============ 方法1: 实际数据法 xG代理 ============
# 富川主场: 进9/11=0.82 失14/11=1.27; 全北客场: 进11/11=1.00 失6/11=0.55
K_LEAGUE_AVG = 1.25  # 韩职场均进球估计(每队)
h_gf_home = HOME_HOME["gf"] / 11
h_ga_home = HOME_HOME["ga"] / 11
a_gf_away = AWAY_AWAY["gf"] / 11
a_ga_away = AWAY_AWAY["ga"] / 11

# xG代理
xg_h_for = h_gf_home * 0.92
xg_h_against = h_ga_home * 1.08
xg_a_for = a_gf_away * 0.92
xg_a_against = a_ga_away * 1.08

# form修正: W+0.08 D+0.02 L-0.05, 上限±0.25
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
print(f"方法1(xG代理): λ富川={lam_h_m1:.2f} λ全北={lam_a_m1:.2f}")
print(f"方法2(市场反推): λ富川={lam_h_m2:.2f} λ全北={lam_a_m2:.2f}")
print(f"综合: λ富川={lam_h:.2f} λ全北={lam_a:.2f}  总进球期望={lam_h+lam_a:.2f}")

# ============ H2H修正 (v2.7) ============
# abs(主队H2H胜率-0.5) = abs(0.5-0.5)=0 < 0.25 不触发量化修正, 但富川H2H 2胜2平0负不败是强信号
h2h_rate = H2H_HOME["w"] / 4
print(f"\nH2H: 富川近4场2胜2平0负({h2h_rate*100:.0f}%胜率), 全北近4次对富川0胜")

# ============ 14维评分卡 (富川视角, -2~+2) ============
scores = [
    ("1 近期状态", "富川近10 3胜5平2负 vs 全北3胜4平3负, 均低迷", 0),
    ("2 主客场分离", "富川主场9%胜率(1/11) vs 全北客场36.4%, 主队-27pp", -1),
    ("3 伤停影响", "双方暂无伤停数据", 0),
    ("4 球员身价差", "全北韩职豪门, 身价显著占优", -1),
    ("5 阵型克制", "无明确战术克制数据", 0),
    ("6 核心球员对位", "全北中场李承佑6球组织核心; 富川锋线Jefferson6球", -1),
    ("7 进阶数据xG", "无公开xG, 用进失球代理", 0),
    ("8 H2H交锋", "富川近4场2胜2平0负全北不败, 强信号", 2),
    ("9 战意差", "富川24分保级区边缘主场抢分; 全北34分争冠集团", 1),
    ("10 赛程疲劳", "双方08-08后休整, 08-19均有杯赛, 无一周双赛", 0),
    ("11 更衣室状态", "富川近2轮不败(0-0光州+3-0江原); 全北近2轮1负1平", 1),
    ("12 历史恩怨", "无德比/复仇情节", 0),
    ("13 天气与场地", "8月韩国高温, 18:30开球, 夏季傍晚炎热", -1),
    ("14 裁判因素", "无裁判数据", 0),
]
total_score = sum(s[2] for s in scores)
print("\n=== 14维评分卡 (富川视角) ===")
for name, reason, sc in scores:
    print(f"  {name}: {sc:+d}  ({reason})")
print(f"  合计: {total_score:+d}")

# λ修正: Δλ = 评分×0.04 (对应±0.4总量), 客队取反向60%
delta_h = total_score * 0.04
delta_a = -delta_h * 0.6
lam_h_final = max(0.3, min(3.5, lam_h + delta_h))
lam_a_final = max(0.1, min(2.5, lam_a + delta_a))

# 修正规则叠加 (C01-C23, 适用K联赛部分)
print("\n=== 修正规则触发 ===")
applied = []
# C08/C14 平局上浮
applied.append("C08/C14 平局概率上浮(K联赛平局率高30-50%)")
# R3/R15 K联赛平局与λ收紧
applied.append("R15 韩职λ系数收紧×0.85")
lam_h_final *= 0.85
lam_a_final *= 0.85
# C01 五五开平局上浮: 本场非五五开(SP 4.35 vs 1.65), 不触发
# R16 强队低赔主胜下调: 全北客胜1.65>1.50, 不触发
# 平局基础概率
draw_boost = 0.06  # +6pp 平局上浮

print("  触发: " + "; ".join(applied))
print(f"  修正后: λ富川={lam_h_final:.2f} λ全北={lam_a_final:.2f}")

# ============ 泊松概率矩阵 ============
def poisson_pmf(lam, k):
    return math.exp(-lam) * lam**k / math.factorial(k)

MAXG = 8
p_h = [poisson_pmf(lam_h_final, k) for k in range(MAXG)]
p_a = [poisson_pmf(lam_a_final, k) for k in range(MAXG)]

# 归一化
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

pd += draw_boost  # 平局上浮
ph -= draw_boost/2
pa -= draw_boost/2

print("\n=== 模型概率(泊松+修正) ===")
print(f"富川胜 {ph*100:.1f}% / 平 {pd*100:.1f}% / 全北胜 {pa*100:.1f}%")

# Edge
print("\n=== 市场 vs 模型 Edge ===")
print(f"富川: 模型{ph*100:.1f}% vs 市场{mp[0]*100:.1f}% = Edge {(ph-mp[0])*100:+.1f}pp")
print(f"平局: 模型{pd*100:.1f}% vs 市场{mp[1]*100:.1f}% = Edge {(pd-mp[1])*100:+.1f}pp")
print(f"全北: 模型{pa*100:.1f}% vs 市场{mp[2]*100:.1f}% = Edge {(pa-mp[2])*100:+.1f}pp")

# 比分Top5
top_scores = sorted(score_probs.items(), key=lambda x: -x[1])[:8]
print("\n=== 比分概率Top8 ===")
for (i, j), pr in top_scores:
    print(f"  {i}-{j}: {pr*100:.1f}%")

# 大小球
over25 = sum(pr for (i, j), pr in score_probs.items() if i + j >= 3)
under25 = 1 - over25
print(f"\n大2.5: {over25*100:.1f}% / 小2.5: {under25*100:.1f}%")
# 市场TTG反推
ttg_inv = {k: 1/v for k, v in TTG.items()}
ttg_sum = sum(ttg_inv.values())
print(f"市场TTG隐含: 0球{ttg_inv[0]/ttg_sum*100:.0f}% 1球{ttg_inv[1]/ttg_sum*100:.0f}% 2球{ttg_inv[2]/ttg_sum*100:.0f}% 3球{ttg_inv[3]/ttg_sum*100:.0f}% 4球{ttg_inv[4]/ttg_sum*100:.0f}%")

# 让球+1 模型概率
ph_plus = sum(pr for (i, j), pr in score_probs.items() if i + 1 > j)
pd_plus = sum(pr for (i, j), pr in score_probs.items() if i + 1 == j)
pa_plus = 1 - ph_plus - pd_plus
print(f"\n让球+1模型: 富川 {ph_plus*100:.1f}% / 平 {pd_plus*100:.1f}% / 全北 {pa_plus*100:.1f}%")
print(f"让球+1市场: 富川 {hp[0]*100:.1f}% / 平 {hp[1]*100:.1f}% / 全北 {hp[2]*100:.1f}%")
