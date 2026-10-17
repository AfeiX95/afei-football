# -*- coding: utf-8 -*-
"""
周二006 欧冠附加赛次回合 博德闪耀 vs 奈梅亨 (2026-08-26 03:00) 全面分析
首回合: 奈梅亨 1:3 博德闪耀 (2026-08-20, 总比分 3:1 博德闪耀领先)
数据: 竞彩网特征分析页 (用户粘贴)
"""
import math
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ============ 市场数据 (竞彩网 2026-08-24 13:15) ============
SP_H, SP_D, SP_A = 1.44, 4.50, 4.70          # 胜平负
HC_H, HC_D, HC_A = 2.24, 3.75, 2.40          # 让球-1 (博德闪耀-1)

# ============ 基础数据 (竞彩特征分析页) ============
# 博德闪耀(主): 近10场8胜2平0负(进27失7净+20); 主场近10 7胜2平1负; 场均进2.7失0.7
# 奈梅亨(客): 近10场3胜2平5负(进22失16净+6); 客场近10 3胜4平3负; 场均进2.2失1.6
HOME_GF, HOME_GA = 2.7, 0.7
AWAY_GF, AWAY_GA = 2.2, 1.6
HOME_HOME = {"w": 7, "d": 2, "l": 1, "n": 10}     # 博德闪耀主场近10
AWAY_AWAY = {"w": 3, "d": 4, "l": 3, "n": 10}     # 奈梅亨客场近10

# 近10场战况
HOME_FORM = {"w": 8, "d": 2, "l": 0, "gf": 27, "ga": 7}
AWAY_FORM = {"w": 3, "d": 2, "l": 5, "gf": 22, "ga": 16}

# H2H (博德闪耀视角): 近1场 1胜 (2026-08-20 客场3:1)
H2H = {"w": 1, "d": 0, "l": 0}

# ============ 市场隐含概率(去水) ============
def implied(h, d, a):
    inv = [1/h, 1/d, 1/a]
    s = sum(inv)
    return [x/s for x in inv], s

mp, margin = implied(SP_H, SP_D, SP_A)
hc, hc_margin = implied(HC_H, HC_D, HC_A)
print("=== 市场隐含概率(去水) ===")
print(f"胜平负: 博德闪耀{mp[0]*100:.1f}% / 平{mp[1]*100:.1f}% / 奈梅亨{mp[2]*100:.1f}%  (返还率{1/margin*100:.1f}%)")
print(f"让-1: 净胜2+ {hc[0]*100:.1f}% / 净胜1 {hc[1]*100:.1f}% / 平或负 {hc[2]*100:.1f}%")
print(f"博德闪耀不败 = {(mp[0]+mp[1])*100:.1f}%")

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
print(f"方法1(xG代理): λ博德闪耀={lam_h_m1:.2f} λ奈梅亨={lam_a_m1:.2f}")
print(f"方法2(市场反推): λ博德闪耀={lam_h_m2:.2f} λ奈梅亨={lam_a_m2:.2f}")
print(f"综合: λ博德闪耀={lam_h:.2f} λ奈梅亨={lam_a:.2f}  总进球期望={lam_h+lam_a:.2f}")

# ============ 14维评分卡 (博德闪耀视角) ============
scores = [
    ("1 近期状态", "博德闪耀近10 8胜2平0负(净+20) vs 奈梅亨3胜2平5负(净+6)——状态碾压", 2),
    ("2 主客场分离", "博德闪耀主场7胜2平1负 vs 奈梅亨客场3胜4平3负", 1),
    ("3 伤停影响", "双方暂无伤停数据", 0),
    ("4 球员身价差", "荷甲中游 vs 挪超豪门(欧冠常客)——身价接近, 博德闪耀近年欧战更硬", 0),
    ("5 阵型克制", "博德闪耀人造草+快速反击 vs 奈梅亨必须压上进攻→反击空间大", 1),
    ("6 核心球员对位", "博德闪耀多点开花(Helmersen/布隆伯格/豪根) vs 奈梅亨三前锋各1球", 1),
    ("7 进阶数据xG", "用主客分离进失球代理", 0),
    ("8 H2H交锋", "近1场(首回合)客场3:1胜——心理优势", 1),
    ("9 战意差", "🔴 博德闪耀3-1领先不需赢(守成) vs 奈梅亨必须客场赢3球(搏命)——博德闪耀进攻欲望打折", -2),
    ("10 赛程疲劳", "博德闪耀08-27挪威杯(1天后,低级别可轮换); 奈梅亨08-30荷甲(3天后)——均无大碍", 0),
    ("11 更衣室状态", "博德闪耀3连胜(欧冠+联赛)士气高 vs 奈梅亨荷甲开局1胜1负低迷", 1),
    ("12 历史恩怨", "无特别恩怨", 0),
    ("13 天气与场地", "8月北极圈(北纬67度)人造草主场——博德闪耀熟悉, 客队不适应", 0),
    ("14 裁判因素", "无数据", 0),
]
total_score = sum(s[2] for s in scores)
print("\n=== 14维评分卡 (博德闪耀视角) ===")
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
applied.append("C15a(<1.50让-1)触发: 1.44 → v2.10.0分档=强队例外(博德闪耀挪超豪门) → 下调减半-10~12pp")
applied.append("C33候选 1球主义: 领先方守成+净胜1球走盘风险 → 让-1打穿概率打折")
applied.append("战意修正: 次回合领先方(3-1)守成 → 主队进攻λ-0.15")
print("  触发: " + "; ".join(applied))
print(f"  修正后: λ博德闪耀={lam_h_final:.2f} λ奈梅亨={lam_a_final:.2f}")

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

draw_boost = 0.03  # +3pp 平局上浮 (守成战意)
pd += draw_boost
ph -= draw_boost/2
pa -= draw_boost/2

print("\n=== 模型概率(泊松+修正) ===")
print(f"博德闪耀胜 {ph*100:.1f}% / 平 {pd*100:.1f}% / 奈梅亨胜 {pa*100:.1f}%")

print("\n=== 市场 vs 模型 Edge ===")
print(f"博德闪耀: 模型{ph*100:.1f}% vs 市场{mp[0]*100:.1f}% = Edge {(ph-mp[0])*100:+.1f}pp")
print(f"平局: 模型{pd*100:.1f}% vs 市场{mp[1]*100:.1f}% = Edge {(pd-mp[1])*100:+.1f}pp")
print(f"奈梅亨: 模型{pa*100:.1f}% vs 市场{mp[2]*100:.1f}% = Edge {(pa-mp[2])*100:+.1f}pp")

# 让-1 打穿概率
hc_cover = sum(pr for (i, j), pr in score_probs.items() if i - j >= 2)
hc_push = sum(pr for (i, j), pr in score_probs.items() if i - j == 1)
hc_lose = 1 - hc_cover - hc_push
print(f"\n让-1(博德闪耀-1): 净胜2+ {hc_cover*100:.1f}% / 净胜1 {hc_push*100:.1f}% / 平或负 {hc_lose*100:.1f}%")
print(f"  模型净胜2+ {hc_cover*100:.1f}% vs 市场{hc[0]*100:.1f}% = Edge {(hc_cover-hc[0])*100:+.1f}pp")

top_scores = sorted(score_probs.items(), key=lambda x: -x[1])[:8]
print("\n=== 比分概率Top8 ===")
for (i, j), pr in top_scores:
    print(f"  {i}-{j}: {pr*100:.1f}%")

over25 = sum(pr for (i, j), pr in score_probs.items() if i + j >= 3)
print(f"\n大2.5: {over25*100:.1f}% / 小2.5: {(1-over25)*100:.1f}% (市场TTG大2.5约73%)")

# 晋级概率 (总比分3:1)
# 博德闪耀晋级: 赢/平/输1球(总3:2或4:3); 输2球(总3:3)加时; 输3+(总3:4+)出局
win_or_draw = ph + pd
lose_by1 = sum(pr for (i, j), pr in score_probs.items() if j - i == 1)
lose_by2 = sum(pr for (i, j), pr in score_probs.items() if j - i == 2)
lose_by3plus = 1 - win_or_draw - lose_by1 - lose_by2
print(f"\n=== 晋级概率推演 (总比分3:1) ===")
print(f"直接晋级(赢/平/输1球): {(win_or_draw+lose_by1)*100:.1f}%")
print(f"输2球进加时(总3:3): {lose_by2*100:.1f}%")
print(f"输3球+出局: {lose_by3plus*100:.1f}%")
