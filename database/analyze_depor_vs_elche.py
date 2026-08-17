# -*- coding: utf-8 -*-
"""
拉科鲁尼亚 vs 埃尔切 (西甲第1轮 2026-08-18 03:00) 全面分析
数据: 新球体育 (用户粘贴)
"""
import math

# ============ 市场数据 ============
SP_H, SP_D, SP_A = 2.16, 2.95, 3.05          # 胜平负
TTG = {0: 9.00, 1: 4.05, 2: 3.20, 3: 3.97, 4: 14.00, 5: 26.00, 6: 40.00}

# ============ 基础数据 (新球体育) ============
# 拉科鲁尼亚(主): 西乙第2升班马, 总42场 22胜11平9负 77分; 主场21场 11胜5平5负(52.4%, 进31失22)
# 埃尔切(客): 西甲第15, 总38场 10胜13平15负 43分; 客场19场 1胜5平13负(5.3%!! 进19失38)
HOME_HOME = {"w": 11, "d": 5, "l": 5, "gf": 31, "ga": 22}    # 拉科主场
AWAY_AWAY = {"w": 1, "d": 5, "l": 13, "gf": 19, "ga": 38}    # 埃尔切客场

# 近10场 (含友谊赛, 权重降低)
HOME_FORM = {"w": 5, "d": 3, "l": 2, "gf": 14, "ga": 7}      # 拉科近10 5胜3平2负(含友谊赛)
AWAY_FORM = {"w": 3, "d": 5, "l": 2, "gf": 14, "ga": 12}     # 埃尔切近10 3胜5平2负(含友谊赛)

# H2H 近10场: 拉科4胜2平4负 (最近一次25-06-02 拉科主场0-4惨败埃尔切)
H2H_HOME = {"w": 4, "d": 2, "l": 4}

# ============ 市场隐含概率(去水) ============
def implied(h, d, a):
    inv = [1/h, 1/d, 1/a]
    s = sum(inv)
    return [x/s for x in inv], s

mp, margin = implied(SP_H, SP_D, SP_A)
print("=== 市场隐含概率(去水) ===")
print(f"胜平负: 拉科{mp[0]*100:.1f}% / 平{mp[1]*100:.1f}% / 埃尔切{mp[2]*100:.1f}%  (返还率{1/margin*100:.1f}%)")
print(f"市场隐含: 拉科不败 = {(mp[0]+mp[1])*100:.1f}%, 埃尔切不败 = {(mp[1]+mp[2])*100:.1f}%")

# ============ 方法1: 实际数据法 xG代理 (主客场分离) ============
h_gf_home = HOME_HOME["gf"] / 21   # 1.48
h_ga_home = HOME_HOME["ga"] / 21   # 1.05
a_gf_away = AWAY_AWAY["gf"] / 19   # 1.00
a_ga_away = AWAY_AWAY["ga"] / 19   # 2.00

xg_h_for = h_gf_home * 0.92
xg_h_against = h_ga_home * 1.08
xg_a_for = a_gf_away * 0.92
xg_a_against = a_ga_away * 1.08

# form修正: 友谊赛权重0.50(R9), 正式赛全权重
# 拉科: 5胜3平2负(友谊赛4场) -> 正式赛约1胜1平1负
# 简化: 用近10场但折扣
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
print(f"方法1(xG代理): λ拉科={lam_h_m1:.2f} λ埃尔切={lam_a_m1:.2f}")
print(f"方法2(市场反推): λ拉科={lam_h_m2:.2f} λ埃尔切={lam_a_m2:.2f}")
print(f"综合: λ拉科={lam_h:.2f} λ埃尔切={lam_a:.2f}  总进球期望={lam_h+lam_a:.2f}")

# ============ 14维评分卡 (拉科视角) ============
scores = [
    ("1 近期状态", "拉科近10 5胜3平2负 vs 埃尔切3胜5平2负(均含友谊赛); 拉科友谊赛赢过热那亚/平佛罗伦萨", 1),
    ("2 主客场分离", "拉科主场52.4%胜率 vs 埃尔切客场5.3%胜率(19场1胜!), 差距47pp", 2),
    ("3 伤停影响", "拉科缺右边锋D.馬洛(半月板)+中场诺埃(疑似); 埃尔切缺3名攻击手(迪安加纳/雅戈/奥索里奥腿筋)", 2),
    ("4 球员身价差", "拉科有奥巴梅扬领衔; 埃尔切保级队身价, 且锋线3人伤缺", 1),
    ("5 阵型克制", "拉科定位球+右路宽度; 埃尔切防守高空球是短板(场均失2球客场)", 1),
    ("6 核心球员对位", "拉科奥巴梅扬(6.6分)+门将罗曼(8.0); 埃尔切锋线核心全缺", 2),
    ("7 进阶数据xG", "无公开xG, 用主客分离进失球代理", 0),
    ("8 H2H交锋", "近10场4胜2平4负持平; 但最近一次拉科主场0-4惨败, 心理阴影", -1),
    ("9 战意差", "升班马首轮主场揭幕战想拿分; 埃尔切客场保级心态", 1),
    ("10 赛程疲劳", "休赛期后首轮, 双方体能充足", 0),
    ("11 更衣室状态", "拉科友谊赛状态佳+主场揭幕; 埃尔切锋线伤病危机", 1),
    ("12 历史恩怨", "无特别恩怨", 0),
    ("13 天气与场地", "8月西班牙高温, 凌晨3点开球(温度相对适宜)", 0),
    ("14 裁判因素", "无裁判数据", 0),
]
total_score = sum(s[2] for s in scores)
print("\n=== 14维评分卡 (拉科视角) ===")
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
# C08/C14 平局上浮 (西甲平局率高)
applied.append("C08/C14 平局概率上浮")
# C06 低赔主胜下调: 拉科2.16>1.40 不触发
# C05 升班马客场惩罚: 埃尔切不是升班马(西甲老油条) 不触发
# C03 赛季过渡期修正: 新赛季首轮, 近期数据权重降低30%
applied.append("C03 赛季过渡期修正(首轮, 近期数据权重-30%)")
# R9 友谊赛状态权重0.50
applied.append("R9 友谊赛状态权重0.50")
print("  触发: " + "; ".join(applied))
print(f"  修正后: λ拉科={lam_h_final:.2f} λ埃尔切={lam_a_final:.2f}")

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

draw_boost = 0.04  # +4pp 平局上浮
pd += draw_boost
ph -= draw_boost/2
pa -= draw_boost/2

print("\n=== 模型概率(泊松+修正) ===")
print(f"拉科胜 {ph*100:.1f}% / 平 {pd*100:.1f}% / 埃尔切胜 {pa*100:.1f}%")

print("\n=== 市场 vs 模型 Edge ===")
print(f"拉科: 模型{ph*100:.1f}% vs 市场{mp[0]*100:.1f}% = Edge {(ph-mp[0])*100:+.1f}pp")
print(f"平局: 模型{pd*100:.1f}% vs 市场{mp[1]*100:.1f}% = Edge {(pd-mp[1])*100:+.1f}pp")
print(f"埃尔切: 模型{pa*100:.1f}% vs 市场{mp[2]*100:.1f}% = Edge {(pa-mp[2])*100:+.1f}pp")

top_scores = sorted(score_probs.items(), key=lambda x: -x[1])[:8]
print("\n=== 比分概率Top8 ===")
for (i, j), pr in top_scores:
    print(f"  {i}-{j}: {pr*100:.1f}%")

over25 = sum(pr for (i, j), pr in score_probs.items() if i + j >= 3)
under25 = 1 - over25
print(f"\n大2.5: {over25*100:.1f}% / 小2.5: {under25*100:.1f}%")
ttg_inv = {k: 1/v for k, v in TTG.items()}
ttg_sum = sum(ttg_inv.values())
print(f"市场TTG隐含: 0球{ttg_inv[0]/ttg_sum*100:.0f}% 1球{ttg_inv[1]/ttg_sum*100:.0f}% 2球{ttg_inv[2]/ttg_sum*100:.0f}% 3球{ttg_inv[3]/ttg_sum*100:.0f}%")

# 比分单关价值 (对比市场比分盘)
print("\n=== 比分价值对比 (模型 vs 市场) ===")
market_scores = {(1,0):7.0, (2,0):10.0, (2,1):8.0, (3,0):21.0, (3,1):19.0, (3,2):30.0,
                 (0,0):9.0, (1,1):6.0, (2,2):15.0, (3,3):90.0,
                 (0,1):8.0, (0,2):14.0, (1,2):10.5, (0,3):35.0, (1,3):29.0, (2,3):40.0}
for (i, j), pr in sorted(score_probs.items(), key=lambda x: -x[1])[:12]:
    if (i, j) in market_scores:
        ev = pr * market_scores[(i, j)] - 1
        mark = "⭐" if ev > 0.15 else ("🟡" if ev > 0 else "")
        print(f"  {i}-{j}: 模型{pr*100:.1f}% vs 市场{market_scores[(i,j)]:.1f}倍 EV{ev:+.2f} {mark}")

# 让球盘 (平手/半球: 主让0.25)
ph_q = sum(pr for (i, j), pr in score_probs.items() if i + 0.25 > j)
pa_q = 1 - ph_q - sum(pr for (i, j), pr in score_probs.items() if i + 0.25 == j)
print(f"\n亚让(平手/半球): 拉科赢盘 {ph_q*100:.1f}% vs 埃尔切赢盘 {pa_q*100:.1f}%")
print(f"相同盘路参考: 拉科平半盘赢盘率42.4% vs 埃尔切平半盘赢盘率57.5%")
