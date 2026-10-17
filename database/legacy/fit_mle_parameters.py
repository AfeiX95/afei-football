# -*- coding: utf-8 -*-
"""
MLE 参数拟合: α (融合权重) + ρ (Dixon-Coles 修正)
=================================================
数据源: Batch#24 有赔率+赛果的场次 (analyze_market_vs_model_20260824.py 19场 + 用户赛果页 15场)
拟合方法: 网格粗扫 + 坐标下降精修 (纯 numpy, 无 scipy 依赖)

目标: 最大化赛果似然 L(α,ρ) = Π P(h_i,a_i | λ_stats, λ_power, α, ρ)

⚠️ 数据局限 (诚实标注):
  - 训练集仅 30 场 (Batch#24 共 64 场, 其余 34 场赔率/赛果未落盘)
  - λ_power (纸面实力) 无历史数据 → 用 "市场隐含λ" 作为 λ_stats 代理,
    λ_power 用 "积分榜排名差" 构造 (rank_gap 已知时可用, 否则默认 1.0)
  - 30 场拟合出的 α/ρ 是"基准参考值", 不是最终定稿参数
"""
import math
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ==================== 训练集 (编号, 主队, 让球, 客队, 胜,平,负, 全场比分) ====================
# Batch#24 新增 13 场
NEW = [
    ('周日027','桑托斯',-1,'米拉索尔', 1.66,3.45,4.22, '1:1'),
    ('周日026','新英格兰',-1,'纽约城', 2.11,3.35,2.80, '1:1'),
    ('周日025','波尔图',-2,'阿罗卡', 1.15,5.70,11.80, '2:0'),
    ('周日024','埃尔切',+1,'巴萨', 8.75,5.50,1.20, '0:5'),
    ('周日023','亚特兰大',-1,'萨索洛', 1.41,4.08,5.70, '2:1'),
    ('周日022','都灵',+1,'AC米兰', 4.18,3.32,1.70, '1:2'),
    ('周日021','赫塔费',-1,'桑坦德', 2.05,2.80,3.51, '1:0'),
    ('周日020','圣克拉拉',-1,'法马利康', 2.59,2.65,2.73, '1:0'),
    ('周日019','威尼斯',-1,'莱切', 1.92,2.85,3.88, '0:2'),
    ('周日018','弗洛西诺',+1,'尤文图斯', 7.20,4.65,1.29, '0:1'),
    ('周日017','纽卡斯尔',+1,'利物浦', 3.52,3.84,1.71, '2:2'),
    ('周日016','勒阿弗尔',+1,'摩纳哥', 3.48,3.35,1.84, '0:1'),
    ('周日015','马竞',-1,'比利亚雷', 1.66,3.55,4.08, '2:2'),
]
# Batch#24 待开奖 6 场
SETTLED = [
    ('周日014','坎布尔',+2,'费耶诺德', 12.00,6.90,1.11, '2:5'),
    ('周日013','哈马比',-1,'盖斯', 1.27,4.95,7.15, '2:0'),
    ('周日012','吉马良斯',-1,'葡国民', 1.52,3.65,5.05, '1:0'),
    ('周日011','不伦瑞克',+1,'柏林联合', 3.40,3.40,1.85, '2:4'),
    ('周日010','昂热',+1,'里尔', 4.85,3.35,1.60, '0:2'),
    ('周日009','曼城',-1,'伯恩茅斯', 1.36,4.55,5.75, '2:1'),
]
# 用户赛果页 (2026-08-25 20:58) 新增 15 场
USER_PAGE = [
    ('周二002','济州SK',-1,'浦项制铁', 2.13,2.98,3.08, '1:2'),
    ('周二001','金泉尚武',+1,'全北现代', 3.18,3.18,2.00, '0:0'),
    ('周一011','博塔弗戈',-1,'巴竞技', 2.21,2.90,3.02, '2:3'),
    ('周一010','马拉加',-1,'拉科', 2.28,2.70,3.12, '1:1'),
    ('周一009','吉维森特',-1,'卡萨皮亚', 1.53,3.40,5.50, '2:0'),
    ('周一008','富勒姆',+1,'切尔西', 3.90,3.55,1.69, '2:3'),
    ('周一007','兰斯',-1,'阿纳西', 1.62,3.45,4.50, '3:1'),
    ('周一006','罗马',-1,'佛罗伦萨', 1.56,3.55,4.85, '4:0'),
    ('周一005','吉达联合',-1,'拉斯决心', 1.35,4.45,6.10, '3:2'),
    ('周一004','奥萨苏纳',-1,'莱万特', 1.62,3.36,4.66, '0:0'),
    ('周一003','马尔默',+1,'佐加顿斯', 2.52,3.60,2.20, '0:3'),
    ('周一002','新未来SC',+1,'胡巴卡德', 5.00,4.45,1.42, '0:2'),
    ('周一001','博洛尼亚',-1,'拉齐奥', 2.08,2.85,3.36, '0:1'),
]
ALL = NEW + SETTLED + USER_PAGE

# ==================== 市场 λ 反推 (从胜平负赔率 → λ_home/λ_away) ====================
def market_lambda(sh, sd, sa, max_g=10, tol=1e-9):
    """从去水胜平负概率反推泊松 λ 对 (数值求解, 最小化三分概率差)"""
    inv = [1/sh, 1/sd, 1/sa]; s = sum(inv)
    p_h, p_d, p_a = [x/s for x in inv]

    def pmf(lam, k):
        return math.exp(-lam) * lam**k / math.factorial(k)

    def probs(lh, la):
        ph = pd = pa = 0.0
        for h in range(max_g+1):
            for a in range(max_g+1):
                p = pmf(lh,h)*pmf(la,a)
                if h>a: ph+=p
                elif h==a: pd+=p
                else: pa+=p
        return ph, pd, pa

    def loss(lh, la):
        a,b,c = probs(lh, la)
        return (a-p_h)**2 + (b-p_d)**2 + (c-p_a)**2

    # 网格粗扫
    best = (1.0, 1.0, 1e9)
    for lh in np.arange(0.3, 3.6, 0.1):
        for la in np.arange(0.2, 3.0, 0.1):
            l = loss(lh, la)
            if l < best[2]: best = (lh, la, l)
    # 坐标下降精修
    lh, la, l = best
    for _ in range(200):
        improved = False
        for d in [0.01, 0.001]:
            for nlh in [lh-d, lh+d]:
                nl = loss(nlh, la)
                if nl < l: lh, l = nlh, nl; improved = True
            for nla in [la-d, la+d]:
                nl = loss(lh, nla)
                if nl < l: la, l = nla, nl; improved = True
        if not improved: break
    return lh, la, l

# ==================== Dixon-Coles τ 修正 ====================
def tau(h, a, lh, la, rho):
    if h == 0 and a == 0: return max(1e-6, 1.0 - lh*la*rho)
    if h == 1 and a == 0: return max(1e-6, 1.0 + la*rho)
    if h == 0 and a == 1: return max(1e-6, 1.0 + lh*rho)
    if h == 1 and a == 1: return max(1e-6, 1.0 - rho)
    return 1.0

def match_loglik(h, a, lh, la, rho):
    lh = max(1e-4, lh); la = max(1e-4, la)
    t = tau(h, a, lh, la, rho)
    return math.log(t) - lh + h*math.log(lh) - math.lgamma(h+1) \
                    - la + a*math.log(la) - math.lgamma(a+1)

# ==================== 拟合主流程 ====================
def build_dataset():
    """构造训练集: 每场 {赛果, λ_stats(市场反推), λ_power(排名代理)}"""
    data = []
    for num, home, hc, away, sh, sd, sa, full in ALL:
        h, a = map(int, full.split(':'))
        lh_m, la_m, err = market_lambda(sh, sd, sa)
        # λ_power: 无纸面数据 → 用市场 λ 的"平滑版"作为代理 (rank_gap 未知)
        # 真实拟合时替换为: LatentPower(阵容评分/身价/士气) 计算值
        lh_p = lh_m * 0.85 + 0.15   # 代理: 向均值收缩
        la_p = la_m * 0.85 + 0.15
        data.append({"num": num, "home": home, "hc": hc, "away": away,
                     "h": h, "a": a, "lh_stats": lh_m, "la_stats": la_m,
                     "lh_power": lh_p, "la_power": la_p,
                     "odds": (sh, sd, sa)})
    return data

def nll(alpha, rho, data):
    """负对数似然"""
    total = 0.0
    for m in data:
        lh = alpha*m["lh_stats"] + (1-alpha)*m["lh_power"]
        la = alpha*m["la_stats"] + (1-alpha)*m["la_power"]
        total -= match_loglik(m["h"], m["a"], lh, la, rho)
    return total

def fit(data):
    """网格粗扫 + 坐标下降: α∈[0.1,0.9], ρ∈[-0.15,0.05]"""
    best = None
    for alpha in np.arange(0.10, 0.91, 0.05):
        for rho in np.arange(-0.15, 0.06, 0.01):
            v = nll(alpha, rho, data)
            if best is None or v < best[2]: best = (alpha, rho, v)
    alpha, rho, v = best
    # 精修
    for _ in range(100):
        improved = False
        for d in [0.01, 0.001]:
            for na in [alpha-d, alpha+d]:
                if 0.10 <= na <= 0.90 and nll(na, rho, data) < v:
                    alpha, v = na, nll(na, rho, data); improved = True
            for nr in [rho-d, rho+d]:
                if -0.15 <= nr <= 0.05 and nll(alpha, nr, data) < v:
                    rho, v = nr, nll(alpha, nr, data); improved = True
        if not improved: break
    return alpha, rho, v

def rps_score(data, alpha, rho):
    """Ranked Probability Score (胜平负三分)"""
    total = 0.0
    for m in data:
        lh = alpha*m["lh_stats"] + (1-alpha)*m["lh_power"]
        la = alpha*m["la_stats"] + (1-alpha)*m["la_power"]
        ph = pd = pa = 0.0
        for h in range(11):
            for a in range(11):
                p = math.exp(-lh)*lh**h/math.factorial(h) * math.exp(-la)*la**a/math.factorial(a)
                p *= tau(h, a, lh, la, rho)
                if h>a: ph+=p
                elif h==a: pd+=p
                else: pa+=p
        s = ph+pd+pa
        ph, pd, pa = ph/s, pd/s, pa/s
        actual = [1,0,0] if m["h"]>m["a"] else ([0,1,0] if m["h"]==m["a"] else [0,0,1])
        c_pred = np.cumsum([ph,pd,pa]); c_act = np.cumsum(actual)
        total += np.sum((c_pred-c_act)**2)/2
    return total/len(data)

if __name__ == "__main__":
    print("="*66)
    print("MLE 拟合: α (融合权重) + ρ (Dixon-Coles 修正)")
    print(f"训练集: {len(ALL)} 场 (Batch#24 19场 + 用户赛果页 13场)")
    print("="*66)
    data = build_dataset()

    # 拟合
    alpha_opt, rho_opt, nll_opt = fit(data)
    print(f"\n最优参数: α = {alpha_opt:.3f}  ρ = {rho_opt:.3f}  NLL = {nll_opt:.2f}")

    # 对比: 经验参数 vs MLE
    print("\n-- 参数对比 --")
    for name, a, r in [("经验参数(v2)", 0.30, -0.05), ("MLE最优", alpha_opt, rho_opt),
                       ("纯统计(α=1)", 1.00, rho_opt)]:
        n = nll(a, r, data)
        rps = rps_score(data, a, r)
        print(f"  {name:12s}: α={a:.3f} ρ={r:.3f} → NLL={n:.2f}  RPS={rps:.4f}")

    # ρ 灵敏度
    print("\n-- ρ 扫描 (固定 α 最优值) --")
    for rho in [-0.15, -0.10, -0.05, 0.0, 0.05]:
        print(f"  ρ={rho:+.2f}: NLL={nll(alpha_opt, rho, data):.2f}")

    # 输出到 state
    import json, os
    state = {"mle_fit": {
        "date": "2026-08-26", "train_size": len(ALL),
        "alpha_opt": round(alpha_opt, 4), "rho_opt": round(rho_opt, 4),
        "nll_opt": round(nll_opt, 2),
        "nll_exp": round(nll(0.30, -0.05, data), 2),
        "rps_opt": round(rps_score(data, alpha_opt, rho_opt), 4),
        "rps_exp": round(rps_score(data, 0.30, -0.05), 4),
        "note": "λ_power 用市场λ平滑代理(缺纸面评分历史); 30场小样本, 参考值非定稿"
    }}
    path = os.path.join(os.path.dirname(__file__), "..", "state", "model-state.json")
    path = os.path.abspath(path)
    with open(path, 'r', encoding='utf-8') as f:
        cur = json.load(f)
    cur["mle_fit"] = state["mle_fit"]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已写入 {path}")
