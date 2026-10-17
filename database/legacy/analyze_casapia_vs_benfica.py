# -*- coding: utf-8 -*-
"""
卡萨比亚 vs 本菲卡 (葡超第2轮 2026-08-18 03:15) 全面分析
数据: 新球体育 (用户粘贴)
"""
import math

# ============ 市场数据 ============
# 竞足: 胜平负未开售, 让球+2(卡萨比亚受让2球) 2.20/3.90/2.47
HH_H, HH_D, HH_A = 2.20, 3.90, 2.47          # 让球胜平负 (卡萨+2)
TTG = {0: 18.0, 1: 6.5, 2: 4.1, 3: 3.65, 4: 4.7, 5: 7.75, 6: 13.0, "7+": 17.0}

# ============ 基础数据 ============
# 卡萨比亚(主): 葡超16, 本赛季1场0分(0胜0平1负 0/1); 主场0场(本赛季首主)
# 本菲卡(客): 葡超9, 本赛季1场1分(0胜1平0负 2/2); 客场0场(本赛季首客)
# 近10场
HOME_FORM = {"w": 3, "d": 2, "l": 5, "gf": 8, "ga": 13}    # 卡萨比亚近10 (含友谊/葡甲)
AWAY_FORM = {"w": 5, "d": 3, "l": 2, "gf": 28, "ga": 12}   # 本菲卡近10 (含欧战/友谊)

# H2H 近9场: 卡萨比亚1胜3平5负 (11.1%胜率), 但主场近2次1胜1平不败
H2H_HOME = {"w": 1, "d": 3, "l": 5}

# ============ 市场隐含概率(去水) ============
def implied(h, d, a):
    inv = [1/h, 1/d, 1/a]
    s = sum(inv)
    return [x/s for x in inv], s

hp, hmargin = implied(HH_H, HH_D, HH_A)
print("=== 竞足让球+2 市场隐含 ===")
print(f"卡萨+2胜 {hp[0]*100:.1f}% / 让平(输2球) {hp[1]*100:.1f}% / 本菲卡-2胜 {hp[2]*100:.1f}% (返还率{1/hmargin*100:.1f}%)")

# 从比分盘反推胜平负隐含
# 本菲卡胜比分: 0:1=7,0:2=5.7,1:2=8,0:3=6.5,1:3=10,2:3=31,0:4=10,1:4=17,2:4=65,0:5=18,1:5=31,2:5=120,负其它=15
# 平: 0:0=18,1:1=11.5,2:2=31,3:3=200,平其它=850
# 卡萨胜: 1:0=30,2:0=120,2:1=35,3:0=550,3:1=200,3:2=175,4:0=1000,胜其它=650
home_scores = {1/30+1/120+1/35+1/550+1/200+1/175+1/1000+1/650}
draw_scores = {1/18+1/11.5+1/31+1/200+1/850}
away_scores = {1/7+1/5.7+1/8+1/6.5+1/10+1/31+1/10+1/17+1/65+1/18+1/31+1/120+1/15}
hs, ds, as_ = sum(home_scores), sum(draw_scores), sum(away_scores)
tot = hs + ds + as_
print("\n=== 比分盘反推胜平负 ===")
print(f"卡萨胜 {hs/tot*100:.1f}% / 平 {ds/tot*100:.1f}% / 本菲卡胜 {as_/tot*100:.1f}%")

# ============ λ估算 ============
# 卡萨比亚: 近10场均进0.8/失1.3; 主场样本少(近10同主客 进3失1 场均1.5)
# 本菲卡: 近10场均进2.8/失1.2; 客场场均进1.66/失1.33(同客3场)
# 方法1: 实际数据法
h_gf = 1.5   # 卡萨主场场均进球(同主客近10)
h_ga = 1.3   # 卡萨场均失球
a_gf = 1.66  # 本菲卡客场场均进球
a_ga = 1.2   # 本菲卡场均失球
xg_h_for = h_gf * 0.92
xg_h_against = h_ga * 1.08
xg_a_for = a_gf * 0.92
xg_a_against = a_ga * 1.08
form_h = min(0.25, HOME_FORM["w"]*0.08 + HOME_FORM["d"]*0.02 - HOME_FORM["l"]*0.05) * 0.7
form_a = min(0.25, AWAY_FORM["w"]*0.08 + AWAY_FORM["d"]*0.02 - AWAY_FORM["l"]*0.05) * 0.9
lam_h_m1 = (xg_h_for + xg_a_against) / 2 + form_h
lam_a_m1 = (xg_a_for + xg_h_against) / 2 + form_a

# 方法2: 市场反推 (用比分盘隐含)
mp_h, mp_d, mp_a = hs/tot, ds/tot, as_/tot
lam_h_m2 = 0.4 + mp_h * 3.2
lam_a_m2 = 0.2 + mp_a * 3.2

lam_h = (lam_h_m1 + lam_h_m2) / 2
lam_a = (lam_a_m1 + lam_a_m2) / 2
if abs(lam_h_m1 - lam_h_m2) > 0.5: lam_h = lam_h_m1
if abs(lam_a_m1 - lam_a_m2) > 0.5: lam_a = lam_a_m1

print(f"\n=== λ估算 ===")
print(f"方法1: λ卡萨={lam_h_m1:.2f} λ本菲卡={lam_a_m1:.2f}")
print(f"方法2: λ卡萨={lam_h_m2:.2f} λ本菲卡={lam_a_m2:.2f}")
print(f"综合: λ卡萨={lam_h:.2f} λ本菲卡={lam_a:.2f} 总进球期望={lam_h+lam_a:.2f}")

# ============ 14维评分卡 (卡萨比亚视角) ============
scores = [
    ("1 近期状态", "卡萨近10 3胜2平5负(含友谊连败) vs 本菲卡5胜3平2负(含欧战大胜)", -1),
    ("2 主客场分离", "卡萨本赛季首主; 本菲卡首客; 卡萨主场H2H近2次1胜1平不败", 1),
    ("3 伤停影响", "卡萨后卫古拉特疑似伤缺; 本菲卡中场奥尔斯内斯伤缺(轮换削弱)", 0),
    ("4 球员身价差", "本菲卡葡超豪门身价碾压, 欧战常客", -2),
    ("5 阵型克制", "卡萨边路传中争顶 vs 本菲卡控球中路渗透", -1),
    ("6 核心球员对位", "本菲卡锋线状态火热(近10场28球, 6-1/5-0大胜); 卡萨进攻乏力(场均0.8球)", -2),
    ("7 进阶数据xG", "本菲卡场均2.8球 vs 卡萨0.8球, 差距巨大", -2),
    ("8 H2H交锋", "近9场卡萨1胜3平5负(11%胜率); 但主场近2次1胜1平不败(25-01 3-1赢!)", 1),
    ("9 战意差", "卡萨保级压力主场求破局; 本菲卡3天后欧战(08-21对奥胡斯)可能留力", 1),
    ("10 赛程疲劳", "本菲卡08-14欧战+08-18葡超+08-21欧战, 一周双赛+留力风险", 1),
    ("11 更衣室状态", "卡萨友谊赛连败士气低; 本菲卡欧战晋级士气高", -1),
    ("12 历史恩怨", "无特别恩怨", 0),
    ("13 天气与场地", "8月葡萄牙高温, 凌晨3:15开球相对凉快", 0),
    ("14 裁判因素", "无裁判数据", 0),
]
total_score = sum(s[2] for s in scores)
print("\n=== 14维评分卡 (卡萨比亚视角) ===")
for name, reason, sc in scores:
    print(f"  {name}: {sc:+d}  ({reason})")
print(f"  合计: {total_score:+d}")

delta_h = total_score * 0.04
delta_a = -delta_h * 0.6
lam_h_final = max(0.3, min(3.5, lam_h + delta_h))
lam_a_final = max(0.1, min(2.5, lam_a + delta_a))

# 修正规则
print("\n=== 修正规则触发 ===")
applied = []
applied.append("C03 赛季过渡期修正(联赛前2轮)")
applied.append("R12 欧战资格赛+联赛双线, 本菲卡留力风险")
applied.append("R9 友谊赛状态权重0.50")
lam_h_final *= 0.90  # 卡萨保级队主队保守微调
lam_a_final *= 0.92  # 本菲卡留力+客场首次作战
print("  触发: " + "; ".join(applied))
print(f"  修正后: λ卡萨={lam_h_final:.2f} λ本菲卡={lam_a_final:.2f}")

# ============ 泊松概率 ============
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

draw_boost = 0.05
pd += draw_boost; ph -= draw_boost/2; pa -= draw_boost/2

print("\n=== 模型概率(泊松+修正) ===")
print(f"卡萨胜 {ph*100:.1f}% / 平 {pd*100:.1f}% / 本菲卡胜 {pa*100:.1f}%")

print("\n=== 市场 vs 模型 Edge ===")
print(f"卡萨: 模型{ph*100:.1f}% vs 市场{mp_h*100:.1f}% = Edge {(ph-mp_h)*100:+.1f}pp")
print(f"平局: 模型{pd*100:.1f}% vs 市场{mp_d*100:.1f}% = Edge {(pd-mp_d)*100:+.1f}pp")
print(f"本菲卡: 模型{pa*100:.1f}% vs 市场{mp_a*100:.1f}% = Edge {(pa-mp_a)*100:+.1f}pp")

top_scores = sorted(score_probs.items(), key=lambda x: -x[1])[:8]
print("\n=== 比分概率Top8 ===")
for (i, j), pr in top_scores:
    print(f"  {i}-{j}: {pr*100:.1f}%")

over25 = sum(pr for (i, j), pr in score_probs.items() if i + j >= 3)
print(f"\n大2.5: {over25*100:.1f}% / 小2.5: {(1-over25)*100:.1f}%")

# 让球+2 (卡萨受让2球)
ph_plus = sum(pr for (i, j), pr in score_probs.items() if i + 2 > j)
pd_plus = sum(pr for (i, j), pr in score_probs.items() if i + 2 == j)
pa_plus = 1 - ph_plus - pd_plus
print(f"\n让球+2模型: 卡萨 {ph_plus*100:.1f}% / 让平 {pd_plus*100:.1f}% / 本菲卡-2 {pa_plus*100:.1f}%")
print(f"让球+2市场: 卡萨 {hp[0]*100:.1f}% / 让平 {hp[1]*100:.1f}% / 本菲卡-2 {hp[2]*100:.1f}%")

# 盘路参考
print(f"\n盘路: 本菲卡客场让球半/两球赢盘率41.7%(10/14输); 卡萨主场受让球半/两球赢盘率66.7%")
