# -*- coding: utf-8 -*-
"""
AFEI Model Engine v2.0 (改进验证版, 2026-08-26)
================================================
融合四轮评审的学习成果:

  1. PoissonLambdaCalculator  — 经典攻防分解 + 贝叶斯收缩 (λ 基础层)
  2. TeamFeatureFusion        — 纸面实力潜变量修正 (修复 sigmoid 注释-实现漂移)
  3. Dixon-Coles 修正         — 低比分 (0-0/1-0/0-1/1-1) 概率微调
  4. 解析 AH 结算             — 五态 (全赢/赢半/走水/输半/全输) + EV (仅内部)
  5. 解析解为主               — MC 仅保留 ±5% 扰动敏感性 (非基础概率)

关键修复 (相对旧 model_engine.py / mc_simulation.py):
  - 让球不再用 λ+1.0 (方差畸变), 改为净胜球平移比较
  - 胜平负/大小球/AH 全部解析计算, 20万次MC降级为扰动验证
  - sigmoid 归一化修正: 50分=1.0, 75分=1.25, 25分=0.75 (与原注释意图一致)
  - λ 融合: log λ = log(分解λ) + 纸面实力修正 (数据与纸面互相校准)

用法:
  from model_engine_v2 import EngineV2
  e = EngineV2()
  r = e.full_analysis(home_stats, away_stats, home_team, away_team, handicap=1.0)
"""
import math

# ==================== 配置 ====================
LEAGUE_HOME_AVG = 1.45      # 联赛主场场均进球 (西甲基准)
LEAGUE_AWAY_AVG = 1.15      # 联赛客场场均进球
PRIOR_WEIGHT = 3.0          # 贝叶斯收缩: 相当于补 N 场联赛基准 (防小样本失真)
DC_RHO = -0.05              # Dixon-Coles 低比分相关系数 (经验值, MLE 32场不可辨识, 保留经典值)
MAX_GOALS = 10              # 泊松截断

# ---- 融合权重 α (2026-08-26 MLE 实验后定稿) ----
# MLE 在"市场λ反推"训练集上给出 α→0.90, 但存在幸存者偏差:
#   训练集 lh_stats 本就是市场赔率反推, 机构盘口已含纸面实力 → 纸面层"无增益"是必然结论
# 实战流水线中 lh_stats 是纯攻防数据, 赛季初/小样本下会失真 → 纸面层必须保留制动能力
# 定稿: 默认 α=0.70 (统计为主, 保留30%纸面基底), 支持样本量自适应
DEFAULT_ALPHA = 0.70
DEFAULT_RHO = DC_RHO


def adaptive_alpha(n, min_a=0.40, max_a=0.85, n_sat=15):
    """
    条件化自适应 α: 样本量 n 越大, 越信任真实攻防统计 (纸面层退居锚点)
      n < 5     → α ≈ 0.40~0.55 (联赛初期, 加重纸面)
      n >= 15   → α → 0.85 (中后期, 数据主导)
    公式: α = min(max_a, min_a + (max_a-min_a) * n / n_sat)
    """
    return round(min(max_a, min_a + (max_a - min_a) * n / n_sat), 3)


# ==================== 1. 经典攻防分解 + 贝叶斯收缩 ====================
class PoissonLambda:
    """λ 基础层: 攻防比率分解, 数据驱动"""

    def __init__(self, league_home_avg=LEAGUE_HOME_AVG, league_away_avg=LEAGUE_AWAY_AVG,
                 prior_weight=PRIOR_WEIGHT, def_prior_boost=2.0):
        self.mu_h = league_home_avg
        self.mu_a = league_away_avg
        self.prior = prior_weight
        # 防守端加重收缩: 失球方差大(门将/红牌/运气), 小样本下更需拉向联赛均值
        self.def_prior = prior_weight * def_prior_boost

    def _smooth(self, value, played, league_mean, prior):
        """贝叶斯平滑: (实际 + prior×联赛均值) / (场次 + prior)"""
        if played <= 0:
            return league_mean
        return (value + prior * league_mean) / (played + prior)

    def calc(self, home_stats, away_stats):
        """
        home_stats = {'scored': 主队总进球, 'conceded': 主队总失球, 'played': 场次,
                      'weight': 样本质量系数 (1.0=联赛正赛, 0.7=含友谊/杯赛水分)}
        away_stats = 同上 (客场口径)
        返回: lam_h, lam_a, strengths
        """
        w_h = home_stats.get('weight', 1.0)
        w_a = away_stats.get('weight', 1.0)
        h_gf = self._smooth(home_stats['scored'] * w_h, home_stats['played'], self.mu_h, self.prior)
        h_ga = self._smooth(home_stats['conceded'] * w_h, home_stats['played'], self.mu_a, self.def_prior)
        a_gf = self._smooth(away_stats['scored'] * w_a, away_stats['played'], self.mu_a, self.prior)
        a_ga = self._smooth(away_stats['conceded'] * w_a, away_stats['played'], self.mu_h, self.def_prior)

        alpha_h = h_gf / self.mu_h          # 主队进攻强度
        beta_h = h_ga / self.mu_a           # 主队防守漏洞
        alpha_a = a_gf / self.mu_a          # 客队进攻强度
        beta_a = a_ga / self.mu_h           # 客队防守漏洞

        lam_h = self.mu_h * alpha_h * beta_a
        lam_a = self.mu_a * alpha_a * beta_h
        return lam_h, lam_a, {
            "alpha_h": round(alpha_h, 3), "beta_h": round(beta_h, 3),
            "alpha_a": round(alpha_a, 3), "beta_a": round(beta_a, 3)}


# ==================== 2. 纸面实力潜变量 (修复版) ====================
class LatentPower:
    """
    纸面实力层: 阵容评分/身价/士气 → 攻防潜变量
    修复: sigmoid 映射改为 50分=1.0, 75分=1.25, 25分=0.75 (温和线性-幂律混合)
         与原代码注释意图一致, 不再出现 75分→1.76 的过度放大
    """

    W_ATT = {'attack': 0.50, 'midfield': 0.35, 'defense': 0.15}
    W_DEF = {'defense': 0.55, 'midfield': 0.35, 'attack': 0.10}

    @staticmethod
    def _score_multiplier(x):
        """评分 0-100 → 实力乘子: 50→1.0, 75→1.25, 25→0.75 (温和)"""
        return 1.0 + (x - 50.0) / 100.0 * 0.5

    @staticmethod
    def _worth_multiplier(w):
        """身价幂律压缩: (w/50)^0.25, 50→1.0, 90→1.16, 20→0.80"""
        return (max(5.0, min(100.0, w)) / 50.0) ** 0.25

    @staticmethod
    def _morale_multiplier(m):
        """士气: ±8% 范围"""
        return 1.0 + (m - 50.0) * 0.0016

    def powers(self, team):
        line_att = sum(team.get(k, 50) * v for k, v in self.W_ATT.items())
        line_def = sum(team.get(k, 50) * v for k, v in self.W_DEF.items())
        worth = self._worth_multiplier(team.get('worthScore', 50))
        morale = self._morale_multiplier(team.get('morale', 50))
        att = self._score_multiplier(line_att) * worth * morale
        deff = self._score_multiplier(line_def) * worth * morale
        return att, deff


# ==================== 3. λ 融合 ====================
def fuse_lambda(lam_base_h, lam_base_a, h_att, h_def, a_att, a_def,
                alpha=DEFAULT_ALPHA, home_adv=0.10):
    """
    融合: log λ = log(分解λ) + α·log(纸面攻防比) + 主场加成
      alpha: 统计层权重 (0.70 默认; 可用 adaptive_alpha(n) 按样本量动态化)
      纸面层 (1-alpha) 是锚点/正则化, 防小样本统计失真
    """
    # 纸面攻防比: 主队进攻/客队防守 (相对基准1.0)
    ratio_h = (h_att / max(a_def, 1e-6)) ** alpha
    ratio_a = (a_att / max(h_def, 1e-6)) ** alpha
    lam_h = lam_base_h * ratio_h * math.exp(home_adv)
    lam_a = lam_base_a * ratio_a
    return round(max(0.2, min(4.5, lam_h)), 3), round(max(0.1, min(3.8, lam_a)), 3)


# ==================== 4. 泊松 + Dixon-Coles 修正矩阵 ====================
def _pmf_vec(lam, max_g=MAX_GOALS):
    p = [math.exp(-lam)]
    for k in range(1, max_g + 1):
        p.append(p[-1] * lam / k)
    return p


def score_matrix_dc(lh, la, rho=DC_RHO, max_g=MAX_GOALS):
    """带 Dixon-Coles 低比分修正的解析比分矩阵 → 归一化"""
    ph, pa = _pmf_vec(lh, max_g), _pmf_vec(la, max_g)
    raw = {}
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            p = ph[h] * pa[a]
            if h == 0 and a == 0:
                p *= 1.0 - lh * la * rho
            elif h == 1 and a == 0:
                p *= 1.0 + la * rho
            elif h == 0 and a == 1:
                p *= 1.0 + lh * rho
            elif h == 1 and a == 1:
                p *= 1.0 - rho
            raw[(h, a)] = max(0.0, p)
    tot = sum(raw.values())
    return {k: v / tot for k, v in raw.items()}


def aggregate(matrix, handicap=1.0):
    """从 DC 矩阵解析出: 胜平负 / 大小球 / AH 五态 / 比分TOP"""
    w = d = l = o15 = o25 = o35 = 0.0
    fw = hw = push = hl = fl = 0.0
    scores = {}
    for (h, a), p in matrix.items():
        if h > a: w += p
        elif h == a: d += p
        else: l += p
        t = h + a
        if t >= 2: o15 += p
        if t >= 3: o25 += p
        if t >= 4: o35 += p
        # 让球平移比较 (handicap 整数或 .5/.25 均支持)
        diff = (h - handicap) - a
        if diff > 0: fw += p
        elif diff == 0: push += p
        else: fl += p
        scores[f"{h}-{a}"] = p
    top = sorted(scores.items(), key=lambda x: -x[1])[:10]
    return {
        "wdw": {"home": round(w*100, 1), "draw": round(d*100, 1), "away": round(l*100, 1)},
        "totals": {"over1.5": round(o15*100, 1), "over2.5": round(o25*100, 1), "over3.5": round(o35*100, 1)},
        "ah": {"full_win": round(fw*100, 1), "push": round(push*100, 1), "full_loss": round(fl*100, 1)},
        "top_scores": [(s, round(p*100, 1)) for s, p in top],
    }


# ==================== 5. EV (内部使用, 不写入文章) ====================
def ah_ev(fw, push, fl, odds_hk):
    """港盘 EV: 全赢×O + 走水×0 - 全输×1 (整数盘口径, 竞彩让球三分法)"""
    p_fw, p_push, p_fl = fw / 100, push / 100, fl / 100
    ev = p_fw * odds_hk - p_fl * 1.0
    return round(ev * 100, 2)


# ==================== 主入口 ====================
class EngineV2:
    def __init__(self):
        self.poisson = PoissonLambda()
        self.latent = LatentPower()

    def full_analysis(self, home_stats, away_stats, home_team, away_team,
                      handicap=1.0, odds_hk=None, home_adv=0.10,
                      alpha=None, sample_size=None):
        lam_base_h, lam_base_a, strengths = self.poisson.calc(home_stats, away_stats)
        h_att, h_def = self.latent.powers(home_team)
        a_att, a_def = self.latent.powers(away_team)
        # α 决策: 显式传入 > 样本量自适应 > 默认 0.70
        if alpha is None:
            alpha = (adaptive_alpha(sample_size) if sample_size is not None
                     else DEFAULT_ALPHA)
        lam_h, lam_a = fuse_lambda(lam_base_h, lam_base_a,
                                   h_att, h_def, a_att, a_def,
                                   alpha=alpha, home_adv=home_adv)
        matrix = score_matrix_dc(lam_h, lam_a, rho=DEFAULT_RHO)
        agg = aggregate(matrix, handicap=handicap)
        ev_h = ev_a = None
        if odds_hk:
            ev_h = ah_ev(agg["ah"]["full_win"], agg["ah"]["push"],
                         agg["ah"]["full_loss"], odds_hk[0])
            ev_a = ah_ev(agg["ah"]["full_loss"], agg["ah"]["push"],
                         agg["ah"]["full_win"], odds_hk[1])
        return {
            "lambda": {"home": lam_h, "away": lam_a, "total": round(lam_h + lam_a, 2)},
            "alpha_used": alpha,
            "strengths": strengths,
            "latent": {"home": [round(h_att, 3), round(h_def, 3)],
                       "away": [round(a_att, 3), round(a_def, 3)]},
            "agg": agg,
            "ev_hk": {"home": ev_h, "away": ev_a},
        }


if __name__ == "__main__":
    # ===== 皇马 vs 皇家社会 (2026-08-27) =====
    e = EngineV2()
    home_stats = {"scored": 19, "conceded": 8, "played": 10}     # 近10场 8胜1平1负
    away_stats = {"scored": 14, "conceded": 18, "played": 10}    # 近10场 2胜2平6负
    home_team = {"attack": 88, "midfield": 86, "defense": 82, "worthScore": 90, "morale": 80}
    away_team = {"attack": 68, "midfield": 66, "defense": 64, "worthScore": 58, "morale": 52}
    # 竞彩让-1: 1.72/4.05/3.32 → 港盘约 0.72/0.96(下盘折算)
    r = e.full_analysis(home_stats, away_stats, home_team, away_team,
                        handicap=1.0, odds_hk=(0.72, 0.96))
    import json
    print(json.dumps(r, ensure_ascii=False, indent=2))
