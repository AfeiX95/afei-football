"""
14维评分卡模型 v1.0
用法：修改 match_data 字典后运行，或在 execute_code 中调用 score_match()。

评分范围：-2 ~ +2
输出：修正后λ值 + 泊松概率矩阵 + MC模拟
"""
import math, random

# ============================================================
#  14维评分定义
# ============================================================
DIMENSIONS = {
    # 模块一：基础硬实力（40%）
    1:  {"name": "近期状态",   "module": "基础硬实力", "weight": 0.40, "max_delta": 0.10},
    2:  {"name": "主客场分离", "module": "基础硬实力", "weight": 0.40, "max_delta": 0.10},
    3:  {"name": "伤停影响",   "module": "基础硬实力", "weight": 0.40, "max_delta": 0.10},
    4:  {"name": "球员身价差", "module": "基础硬实力", "weight": 0.40, "max_delta": 0.05},
    # 模块二：技战术与风格（25%）
    5:  {"name": "阵型克制",   "module": "技战术风格", "weight": 0.25, "max_delta": 0.10},
    6:  {"name": "核心球员对位", "module": "技战术风格", "weight": 0.25, "max_delta": 0.05},
    7:  {"name": "进阶数据xG", "module": "技战术风格", "weight": 0.25, "max_delta": 0.10},
    8:  {"name": "H2H交锋",   "module": "技战术风格", "weight": 0.25, "max_delta": 0.10},
    # 模块三：战略与心理（20%）
    9:  {"name": "战意差",     "module": "战略心理",   "weight": 0.20, "max_delta": 0.10},
    10: {"name": "赛程疲劳",   "module": "战略心理",   "weight": 0.20, "max_delta": 0.05},
    11: {"name": "更衣室状态", "module": "战略心理",   "weight": 0.20, "max_delta": 0.05},
    12: {"name": "历史恩怨",   "module": "战略心理",   "weight": 0.20, "max_delta": 0.05},
    # 模块四：外部客观条件（15%）
    13: {"name": "天气与场地", "module": "外部条件",   "weight": 0.15, "max_delta": 0.05},
    14: {"name": "裁判因素",   "module": "外部条件",   "weight": 0.15, "max_delta": 0.05},
}

# ============================================================
#  核心函数
# ============================================================
def pmf(k, lam):
    """泊松PMF（迭代式，无阶乘溢出）"""
    p = math.exp(-lam)
    for i in range(1, k + 1):
        p *= lam / i
    return p

def calc_probs(lh, la):
    """泊松概率矩阵"""
    mx = max(8, int(math.ceil(max(lh, la) * 3)))
    w = d = l = tot = 0.0
    scores = []
    for h in range(mx + 1):
        for a in range(mx + 1):
            p = pmf(h, lh) * pmf(a, la)
            tot += p
            if h > a: w += p
            elif h == a: d += p
            else: l += p
            scores.append((h, a, p))
    scores.sort(key=lambda x: -x[2])
    return {
        'w': round(w / tot * 100, 1),
        'd': round(d / tot * 100, 1),
        'l': round(l / tot * 100, 1),
        'top10': [(f"{h}-{a}", round(p / tot * 100, 1)) for h, a, p in scores[:10]]
    }

def psample(lam):
    """泊松随机采样（逆CDF）"""
    L = math.exp(-lam)
    k = 0; p = 1
    while p > L:
        k += 1; p *= random.random()
    return k - 1

def mc_sim(lh, la, n=200000):
    """蒙特卡洛模拟"""
    w = d = l = o15 = o25 = o35 = 0
    sc = {}
    for _ in range(n):
        hg, ag = psample(lh), psample(la)
        if hg > ag: w += 1
        elif hg == ag: d += 1
        else: l += 1
        t = hg + ag
        if t >= 2: o15 += 1
        if t >= 3: o25 += 1
        if t >= 4: o35 += 1
        k = f"{hg}-{ag}"
        sc[k] = sc.get(k, 0) + 1
    top = sorted(sc.items(), key=lambda x: -x[1])[:10]
    return {
        'w': round(w/n*100, 1), 'd': round(d/n*100, 1), 'l': round(l/n*100, 1),
        'o15': round(o15/n*100, 1), 'o25': round(o25/n*100, 1), 'o35': round(o35/n*100, 1),
        'top10': [(s, round(c/n*100, 1)) for s, c in top]
    }

# ============================================================
#  评分卡主函数
# ============================================================
def score_match(home_name, away_name, lambda1_base, lambda2_base, scores):
    """
    14维评分卡 → 修正λ值 → 概率矩阵

    参数:
        home_name: 主队名
        away_name: 客队名
        lambda1_base: 主队基础λ（泊松模型）
        lambda2_base: 客队基础λ
        scores: dict {维度编号: 评分}，评分 ∈ {-2,-1,0,+1,+2}

    返回:
        dict with 修正后λ、概率、比分、评分明细
    """
    # 逐维计算修正量
    details = []
    total_delta1 = 0.0
    for dim_id, score in scores.items():
        dim = DIMENSIONS[dim_id]
        delta = score * dim['max_delta'] * dim['weight']
        total_delta1 += delta
        details.append({
            'id': dim_id,
            'name': dim['name'],
            'module': dim['module'],
            'score': score,
            'max_delta': dim['max_delta'],
            'weight': dim['weight'],
            'delta': round(delta, 4)
        })

    # 客队修正取反向60%
    total_delta2 = -total_delta1 * 0.6

    # 约束：总修正量 ≤ 0.4
    if abs(total_delta1) > 0.4:
        scale = 0.4 / abs(total_delta1)
        total_delta1 *= scale
        total_delta2 *= scale
        for d in details:
            d['delta'] = round(d['delta'] * scale, 4)

    # 最终λ值
    lh = max(0.3, min(3.5, lambda1_base + total_delta1))
    la = max(0.1, min(2.5, lambda2_base + total_delta2))

    # 概率计算
    pois = calc_probs(lh, la)
    monte = mc_sim(lh, la)

    return {
        'home': home_name,
        'away': away_name,
        'lambda_base': [round(lambda1_base, 2), round(lambda2_base, 2)],
        'delta': [round(total_delta1, 3), round(total_delta2, 3)],
        'lambda_final': [round(lh, 2), round(la, 2)],
        'poisson': pois,
        'mc': monte,
        'zero_home': round(math.exp(-la) * 100, 1),
        'zero_away': round(math.exp(-lh) * 100, 1),
        'details': details
    }

# ============================================================
#  格式化输出
# ============================================================
def print_report(result):
    print(f"\n{'='*50}")
    print(f"  {result['home']} vs {result['away']} · 14维评分卡输出")
    print(f"{'='*50}")

    print(f"\n【λ值修正】")
    print(f"  基础λ: 主{result['lambda_base'][0]} / 客{result['lambda_base'][1]}")
    print(f"  修正量: 主{result['delta'][0]:+.3f} / 客{result['delta'][1]:+.3f}")
    print(f"  最终λ: 主{result['lambda_final'][0]} / 客{result['lambda_final'][1]}")

    print(f"\n【14维评分明细】")
    print(f"  {'#':>2} {'维度':<10} {'模块':<8} {'评分':>4} {'修正量':>8}")
    print(f"  {'─'*42}")
    for d in result['details']:
        score_str = f"{d['score']:+d}" if d['score'] != 0 else " 0"
        print(f"  {d['id']:>2} {d['name']:<10} {d['module']:<8} {score_str:>4} {d['delta']:>+8.4f}")

    print(f"\n【泊松概率】")
    print(f"  {result['home']}胜 {result['poisson']['w']}%  平 {result['poisson']['d']}%  {result['away']}胜 {result['poisson']['l']}%")

    print(f"\n【蒙特卡洛20万次】")
    print(f"  {result['home']}胜 {result['mc']['w']}%  平 {result['mc']['d']}%  {result['away']}胜 {result['mc']['l']}%")
    print(f"  大1.5 {result['mc']['o15']}%  大2.5 {result['mc']['o25']}%  大3.5 {result['mc']['o35']}%")
    print(f"  零封: {result['home']} {result['zero_home']}%  {result['away']} {result['zero_away']}%")

    print(f"\n【比分Top10】")
    for i, (s, c) in enumerate(result['mc']['top10']):
        print(f"  {i+1:>2}. {s:<6} {c}%")

# ============================================================
#  示例：库奥皮奥 vs 萨巴赫
# ============================================================
if __name__ == "__main__":
    # 基础λ（泊松模型，FIFA 60/70）
    L1_BASE = 2.04
    L2_BASE = 0.95

    # 14维评分（-2 ~ +2）
    scores = {
        1:  +1,   # 近期状态：库奥皮奥近10场6胜2平2负，状态不错
        2:  +2,   # 主客场分离：主场60%胜率 vs 客队客场33%，差值>50%
        3:  -1,   # 伤停：布尔基（首发后卫）伤缺
        4:  0,    # 球员身价：两队身价接近
        5:  0,    # 阵型克制：信息不足
        6:  0,    # 核心对位：信息不足
        7:  0,    # xG数据：暂无
        8:  -1,   # H2H：近1场0-1负，样本小但方向不利
        9:  +1,   # 战意：必须赢2球翻盘，生死战
        10: 0,    # 赛程：双方间隔合理
        11: +1,   # 更衣室：近3场2胜1负，状态正向
        12: 0,    # 历史恩怨：无特殊恩怨
        13: 0,    # 天气：7月芬兰，条件正常
        14: 0,    # 裁判：信息不足
    }

    result = score_match("库奥皮奥", "萨巴赫", L1_BASE, L2_BASE, scores)
    print_report(result)
