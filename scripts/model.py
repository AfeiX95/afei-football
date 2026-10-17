# -*- coding: utf-8 -*-
"""阿飞说球 · 后台模型（双方法 λ + 泊松 + 市场对照）

口径铁律：一律 **90 分钟常规时间**（竞彩官方页页脚背书）。
对外一律称「后台模型」，不出现算法名/赔率盘口语（见 R41）。

数据来源
--------
- `state/_match_<竞彩id>/feature.json` → 近10场战况 / 同主客战况 / 场均进失球
- `state/_match_<竞彩id>/history.json` → H2H（⚠️ 只回 5 场，不足看官方页）
- `state/_match_<竞彩id>/injury.json` → 伤停（`personName`）
- `state/_slate.json`                → 全盘口赔率（getMatchCalculatorV1）
- `MATCHES` 里手填：联赛主/客分离的进失球（官方页积分榜才有，API 不给）

先跑 `python scripts/sporttery_fetch.py slate <编号>` 与 `match <id>`。

用法
----
  python scripts/model.py 2041905 2041906 2041916
  python scripts/model.py --all          # MATCHES 里全部
"""
import sys, io, os, json, math, argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
# state 分层（2026-10-17）：契约文件留在 state/ 根，缓存与批次产物进子目录
STATE_MATCHES = os.path.join(STATE, "matches")   # state/matches/<竞彩id>/
STATE_BATCH = os.path.join(STATE, "batch")       # state/batch/_model_*.txt、_slate.json

# ── 手填区：联赛「主/客分离」进失球（来源＝竞彩官方特征分析页的积分榜）──────────
# league = (场次, 进球, 失球)
MATCHES = {
    # ── 2026-10-17 周六（头条 3+2+1：英超 3 / 西甲 2 / 法甲 1）────────────────
    # 主/客分离进失球＝result.json 逐场按场地过滤（窗口＝近 5 场）；
    # lam_m1 已按 w=min(n,5)/5 混入 feature.json 近 10 场场均；含欧冠/欧联/杯赛的场次在 note 里标注。
    "2042024": {  # 周六007 埃弗顿 vs 切尔西  2026-10-17 19:30
        "no": "周六007", "league": "英超",
        "home": "埃弗顿", "away": "切尔西",
        "home_home": (3, 4, 2), "away_away": (2, 1, 5),
        "home_szn": (3, 2, 1, 0), "away_szn": (2, 0, 0, 2),
        "inj_home": 0, "inj_away": 2,
        "note": "主队主场 3 场不败（1 比 0 伊普斯、1 比 0 伍尔弗[联赛杯]、2 比 2 曼联）却只进 4 球；客队客场 2 场全败只进 1 球（0 比 3 布伦特、1 比 2 阿森纳）；近10场场均进失 主1.7/0.7 客2.9/2.0（客队进球数明显高于失球）；同主客10场 主5胜3平2负 / 客1胜3平6负；交锋近 5 次 埃弗顿 1胜1平3负；让球 +1",
    },
    "2042035": {  # 周六018 布伦特 vs 利物浦  2026-10-17 22:00
        "no": "周六018", "league": "英超",
        "home": "布伦特", "away": "利物浦",
        "home_home": (2, 4, 1), "away_away": (2, 7, 3),
        "home_szn": (2, 1, 1, 0), "away_szn": (2, 2, 0, 0),
        "inj_home": 7, "inj_away": 9,
        "note": "主队主场 2 场不败（3 比 0 胜切尔西、1 比 1 桑德兰）；客队客场 2 场全胜进 7 球（含 10 比 15 欧冠 6 比 3 LASK，要打折）；近10场场均进失 主3.1/1.0 客2.0/1.2；同主客10场 主4胜5平1负 / 客4胜1平5负；交锋近 5 次 布伦特 1胜1平3负；伤停 主 7 人 / 客 9 人（名单偏长，需看是否主力）",
    },
    "2042036": {  # 周六019 曼城 vs 伊普斯  2026-10-17 22:00
        "no": "周六019", "league": "英超",
        "home": "曼城", "away": "伊普斯",
        "home_home": (3, 12, 7), "away_away": (2, 3, 3),
        "home_szn": (3, 2, 0, 1), "away_szn": (2, 1, 0, 1),
        "inj_home": 1, "inj_away": 0,
        "note": "主队主场 3 场进 12 球但含 10 比 15 欧冠 2 比 4 负巴黎（主场 5 比 3 桑德兰、5 比 0 诺维奇）；客队客场 2 场进 3 球（3 比 2 胜水晶宫、0 比 1 负埃弗顿）；近10场场均进失 主2.5/1.2 客2.1/1.9；同主客10场 主7胜1平2负 / 客4胜2平4负；交锋近 2 次曼城全胜（6 比 0、4 比 1）；让球 -2、主胜定价 1.12",
    },
    "2042039": {  # 周六022 斯特拉斯 vs 巴黎圣曼  2026-10-17 23:15
        "no": "周六022", "league": "法甲",
        "home": "斯特拉斯", "away": "巴黎圣曼",
        "home_home": (2, 3, 2), "away_away": (3, 7, 3),
        "home_szn": (2, 1, 1, 0), "away_szn": (3, 3, 0, 0),
        "inj_home": 5, "inj_away": 1,
        "note": "主队主场 2 场不败（1 比 1 摩纳哥、2 比 1 朗斯）；客队客场 3 场全胜（含 10 比 15 欧冠 4 比 2 曼城，要打折）；近10场场均进失 主1.4/2.2 客2.3/1.3；同主客10场 主3胜1平6负 / 客4胜3平3负；交锋近 5 次 斯特拉斯 1胜1平3负；伤停 主 5 人 / 客 1 人",
    },
    "2042043": {  # 周六026 贝蒂斯 vs 巴萨  2026-10-18 00:30
        "no": "周六026", "league": "西甲",
        "home": "贝蒂斯", "away": "巴萨",
        "home_home": (3, 9, 4), "away_away": (3, 11, 4),
        "home_szn": (3, 3, 0, 0), "away_szn": (3, 3, 0, 0),
        "inj_home": 1, "inj_away": 2,
        "note": "两队主客分离样本都是 3 场全胜：主队含 10 比 15 欧联 3 比 2 波尔图、5 比 2 奥萨苏纳；客队含 10 比 14 欧冠 4 比 1 加拉塔萨雷；近10场场均进失 主2.0/1.3 客4.3/0.9（客队进球数极端）；同主客10场 主9胜1平0负 / 客7胜1平2负；交锋近 5 次 贝蒂斯 0胜2平3负",
    },
    "2042046": {  # 周六029 巴伦西亚 vs 毕尔巴鄂  2026-10-18 03:00
        "no": "周六029", "league": "西甲",
        "home": "巴伦西亚", "away": "毕尔巴鄂",
        "home_home": (2, 2, 8), "away_away": (2, 2, 2),
        "home_szn": (2, 0, 0, 2), "away_szn": (2, 1, 0, 1),
        "inj_home": 3, "inj_away": 5,
        "note": "主队主场 2 场全败失 8 球（2 比 3 皇家社会、0 比 5 巴萨）→ λ 主队偏低；客队客场 2 场 1 胜 1 负（2 比 0 塞尔塔、0 比 2 巴萨）；近10场场均进失 主0.8/1.8 客1.4/1.0；同主客10场 主2胜2平6负 / 客6胜0平4负；交锋近 5 次 巴伦西亚 2胜0平3负；伤停 主 3 人 / 客 5 人",
    },
    # ── 2026-10-18 周日 亚洲三场（日职 1 / 韩职 2）──────────────────────────
    "2042048": {  # 周日001 町田泽维 vs 福冈黄蜂  2026-10-18 15:00
        "no": "周日001", "league": "日职",
        "home": "町田泽维", "away": "福冈黄蜂",
        "home_home": (3, 4, 5), "away_away": (2, 2, 3),
        "home_szn": (3, 1, 1), "away_szn": (1, 1, 3),
        "inj_home": 0, "inj_away": 0,
        "note": "主队主场 3 场 4 进 5 失（0 比 0 京都、2 比 1 枥木城、2 比 4 柏太阳神），客场两场 1 比 0 各胜一场（含 10 比 15 亚冠二级 1 比 0 淡宾尼士，含加时需打折）；客队客场 2 场 2 进 3 失（0 比 1 横滨FC、1 比 1 Osaka）；近10场场均进失 主1.5/0.9 客0.8/1.3；近5场 主 3胜1平1负 / 客 1胜1平3负；无伤停；让球 -1",
    },
    "2042049": {  # 周日002 江原FC vs 仁川联  2026-10-18 15:30
        "no": "周日002", "league": "韩职",
        "home": "江原FC", "away": "仁川联",
        "home_home": (4, 3, 3), "away_away": (2, 1, 2),
        "home_szn": (1, 2, 2), "away_szn": (2, 2, 1),
        "inj_home": 0, "inj_away": 0,
        "note": "主队主场 4 场 3 进 3 失（2 比 0 富川、0 比 0 仁川、0 比 1 济州、1 比 2 Crown），主场进球效率偏低；客队客场 2 场 1 进 2 失（0 比 0 江原、1 比 2 蔚山）；近10场场均进失 主1.1/0.8 客1.1/0.9，两队几乎同构；近5场 主 1胜2平2负 / 客 2胜2平1负；交锋 9 月 27 日 0 比 0；无伤停；让球 -1",
    },
    "2042050": {  # 周日003 首尔FC vs 金泉尚武  2026-10-18 15:30
        "no": "周日003", "league": "韩职",
        "home": "首尔FC", "away": "金泉尚武",
        "home_home": (2, 2, 2), "away_away": (2, 2, 0),
        "home_szn": (2, 0, 3), "away_szn": (1, 3, 1),
        "inj_home": 0, "inj_away": 0,
        "note": "主队主场样本仅 2 场 2 进 2 失，客场 0 比 3 墨胜利、1 比 0 万隆（亚冠二级）；客队客场 2 场 2 进 0 失（0 比 2 富川胜、0 比 0 浦项），客场防守是联赛最好一档；近10场场均进失 主1.9/1.1 客0.9/1.1；近5场 主 2胜0平3负 / 客 1胜3平1负；无伤停；让球 -1",
    },
}


# ── 工具 ────────────────────────────────────────────────────────────────────
def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def poisson(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def matrix(lh, la, n=12):
    return [[poisson(i, lh) * poisson(j, la) for j in range(n)] for i in range(n)]


def outcomes(m):
    h = d = a = 0.0
    for i, row in enumerate(m):
        for j, p in enumerate(row):
            if i > j:
                h += p
            elif i == j:
                d += p
            else:
                a += p
    return h, d, a


def handicap(m, line):
    h = d = a = 0.0
    for i, row in enumerate(m):
        for j, p in enumerate(row):
            x = i + line - j
            if x > 0:
                h += p
            elif x == 0:
                d += p
            else:
                a += p
    return h, d, a


def totals(m, k):
    return sum(m[i][j] for i in range(len(m)) for j in range(len(m[i])) if i + j > k)


def devig(o):
    inv = [1 / x for x in o]
    s = sum(inv)
    return [x / s for x in inv], s


def lam_m1(m, fe):
    """方法1 实际数据法（xG 代理 0.92 / 1.08），主客分离 + 近10场加权稳定。

    ⚠️ 联赛主/客场样本常只有 2~3 场，单用会失真 → 按样本量加权混入近10场场均。
    """
    ga = fe.get("goalAvg") or {}
    lg = fe.get("lossGoalAvg") or {}
    hh, aa = m["home_home"], m["away_away"]
    w1 = min(hh[0], 5) / 5.0
    w2 = min(aa[0], 5) / 5.0
    f_home = w1 * (hh[1] / hh[0]) + (1 - w1) * float(ga.get("homeGoalAvgCnt") or 0)
    d_away = w2 * (aa[2] / aa[0]) + (1 - w2) * float(lg.get("awayLossGoalAvgCnt") or 0)
    f_away = w2 * (aa[1] / aa[0]) + (1 - w2) * float(ga.get("awayGoalAvgCnt") or 0)
    d_home = w1 * (hh[2] / hh[0]) + (1 - w1) * float(lg.get("homeLossGoalAvgCnt") or 0)
    return (f_home * 0.92 + d_away * 1.08) / 2, (f_away * 0.92 + d_home * 1.08) / 2, \
           (f_home, d_away, f_away, d_home, w1, w2)


def lam_m2(o):
    """方法2 市场反推法（去水 → λ），钳制见 skill。"""
    f, _ = devig(o)
    lh = min(max(0.4 + f[0] * 3.2, 0.3), 3.5)
    la = min(max(0.2 + f[2] * 3.2, 0.1), 2.5)
    return lh, la


def form_adj(rec):
    """近10场 胜/平/负 → form 修正，上限 ±0.25。"""
    v = rec[0] * 0.08 + rec[1] * 0.02 - rec[2] * 0.05
    return max(-0.25, min(0.25, v))


def h2h_adj(win_rate, n):
    """H2H 修正：|rate-0.5|>0.25 且 n>=5 才触发。"""
    if n < 5 or abs(win_rate - 0.5) <= 0.25:
        return 1.0
    if win_rate <= 0.25:
        return 0.88 + win_rate / 0.25 * 0.12
    return 1.00 + (win_rate - 0.75) / 0.25 * 0.08


# ── 单场 ────────────────────────────────────────────────────────────────────
def run(mid, slate):
    m = MATCHES.get(mid)
    if not m:
        print("!! %s 不在 MATCHES 里" % mid)
        return
    d = os.path.join(STATE_MATCHES, str(mid))
    fe = (jload(os.path.join(d, "feature.json")) or {}).get("value") or {}
    hi = (jload(os.path.join(d, "history.json")) or {}).get("value") or {}
    inj = (jload(os.path.join(d, "injury.json")) or {}).get("value") or {}
    od = (slate.get(mid) or {})

    hd = od.get("had") or {}
    had = [float(hd["h"]), float(hd["d"]), float(hd["a"])]
    hh = od.get("hhad") or {}
    hline = float(hh.get("goalLine", 0) or 0)
    hhad = [float(hh["h"]), float(hh["d"]), float(hh["a"])]

    # λ 方法1（主客分离+近10场加权 + form + H2H + 伤停）
    l1h, l1a, bl = lam_m1(m, fe)
    eh = fe.get("eachHomeAway") or {}
    fh = (eh.get("homeWinGoalMatchCnt", 0), eh.get("homeDrawMatchCnt", 0), eh.get("homeLossGoalMatchCnt", 0))
    fa = (eh.get("awayWinGoalMatchCnt", 0), eh.get("awayDrawMatchCnt", 0), eh.get("awayLossGoalMatchCnt", 0))
    afh, afa = form_adj(fh), form_adj(fa)
    l1h += afh
    l1a += afa

    st = hi.get("statistics") or {}
    hw = st.get("winGoalMatchCnt", 0) or 0
    dw = st.get("drawMatchCnt", 0) or 0
    lw = st.get("lossGoalMatchCnt", 0) or 0
    tot = st.get("totalLegCnt", 0) or 5
    # ⚠️ API 有时只回 totalLegCnt、胜/平/负三项全 0（数据缺失）。此时 win_rate=0 会被
    # h2h_adj 判成「主队交锋吃亏」→ 主队 λ×0.88、客队 λ×(2−0.88)，凭空挪 12%。必须跳过。
    if (hw + dw + lw) == 0:
        f_h2h = 1.0
        h2h_tag = "统计缺失→不修正"
    else:
        f_h2h = h2h_adj(hw / tot, tot)
        h2h_tag = "API近%s场 %s胜%s平%s负" % (tot, hw, dw, lw)
    # H2H：主队在交锋里吃亏 → 主队 λ 打折不涨（skill 只量化主队一侧）；
    # 客队取镜像 (2−factor)，保持 λ 总和不变，只挪比重。
    l1h *= f_h2h
    l1a *= (2 - f_h2h)

    # 伤停：主队伤停多 → 主队进攻 ↓、主队防守 ↓（客队 λ ↑）
    injk = (m["inj_home"] - m["inj_away"]) * 0.01
    injk = max(-0.10, min(0.10, injk))
    l1h *= (1 - injk)
    l1a *= (1 + injk)

    # λ 方法2
    l2h, l2a = lam_m2(had)

    # 综合
    def mix(a, b):
        return a if abs(a - b) > 0.5 else (a + b) / 2
    lh, la = mix(l1h, l2h), mix(l1a, l2a)

    M = matrix(lh, la)
    MH, MD, MA = outcomes(M)
    MF, _ = devig(had)
    KM = "√" if abs(l1h - l2h) <= 0.5 and abs(l1a - l2a) <= 0.5 else "×偏xG"

    print("=" * 78)
    print("%s  %s vs %s   [%s]  id=%s" % (m["no"], m["home"], m["away"], m["league"], mid))
    print("  备注：%s" % m["note"])
    print("-" * 78)
    print("  λ 双方法表                     主队      客队")
    print("    方法1 实际数据法(主客分离)   %.3f     %.3f" % (l1h, l1a))
    print("    方法2 市场反推法             %.3f     %.3f" % (l2h, l2a))
    print("    综合 λ                       %.3f     %.3f   双法一致:%s" % (lh, la, KM))
    print("    进球期望合计 λ总 = %.3f" % (lh + la))
    print("    分离/近10场混合: 主攻%.2f(联赛主场w=%.1f) 客防%.2f 客攻%.2f 主防%.2f"
          % (bl[0], bl[4], bl[1], bl[2], bl[3]))
    print("    修正明细: form主%+.3f form客%+.3f | H2H factor %.3f (%s)"
          % (afh, afa, f_h2h, h2h_tag))
    print("              伤停 主%s人/客%s人 → λ主×(1%+.3f)  λ客×(1%+.3f)"
          % (m["inj_home"], m["inj_away"], -injk, injk))
    print("-" * 78)
    print("  胜平负         模型 %5.1f%% / %5.1f%% / %5.1f%%      市场(去水) %5.1f%% / %5.1f%% / %5.1f%%"
          % (MH * 100, MD * 100, MA * 100, MF[0] * 100, MF[1] * 100, MF[2] * 100))
    print("  Edge(模型-市场) 主 %+5.1fpp            平 %+5.1fpp            客 %+5.1fpp"
          % ((MH - MF[0]) * 100, (MD - MF[1]) * 100, (MA - MF[2]) * 100))
    print("  固定奖金        %.2f / %.2f / %.2f        返还率 %.1f%%"
          % (had[0], had[1], had[2], sum(1 / x for x in had) ** -1 * 100))
    print("-" * 78)
    fh_, fd_, fa_ = handicap(M, hline)
    hf, _ = devig(hhad)
    print("  让球(%+.0f)     模型 %5.1f%% / %5.1f%% / %5.1f%%      市场(去水) %5.1f%% / %5.1f%% / %5.1f%%"
          % (hline, fh_ * 100, fd_ * 100, fa_ * 100, hf[0] * 100, hf[1] * 100, hf[2] * 100))
    print("  Edge(模型-市场) %+5.1fpp        %+5.1fpp        %+5.1fpp"
          % ((fh_ - hf[0]) * 100, (fd_ - hf[1]) * 100, (fa_ - hf[2]) * 100))
    print("  胜率(不含平)：主 %.1f%% / 客 %.1f%%" % (MH / (MH + MA) * 100, MA / (MH + MA) * 100))
    print("-" * 78)
    print("  总进球    0:%5.1f%%  1:%5.1f%%  2:%5.1f%%  3:%5.1f%%  4:%5.1f%%  5:%5.1f%%  6:%5.1f%%  7+:%5.1f%%"
          % tuple((sum(M[i][j] for i in range(12) for j in range(12) if i + j == k) * 100)
                  for k in range(8)))
    print("  大1.5 %.1f%%   大2.5 %.1f%%   大3.5 %.1f%%    双方进球 %.1f%%"
          % (totals(M, 1) * 100, totals(M, 2) * 100, totals(M, 3) * 100,
             sum(M[i][j] for i in range(1, 12) for j in range(1, 12)) * 100))
    print("-" * 78)
    crs = (od.get("crs") or {})
    flat = sorted(((M[i][j], i, j) for i in range(6) for j in range(6)), reverse=True)
    print("  比分 Top8（模型概率 / 官方定价 / 溢价EV）")
    for p, i, j in flat[:8]:
        key = "s%02ds%02d" % (i, j)
        o = crs.get(key)
        try:
            o = float(o)
        except (TypeError, ValueError):
            o = None
        ev = ("EV %+.2f" % (p * o - 1)) if o else "—"
        print("    %d-%d   %5.1f%%   %s   %s" % (i, j, p * 100, ("%.2f" % o) if o else "  — ", ev))

    # ── Step 8B 置信度三重检查 ───────────────────────────────────────────
    print("  置信度三重检查（Step 8B）")
    warn = []
    for side, p, e in (("主", MH, MH - MF[0]), ("客", MA, MA - MF[2])):
        if p < 0.40 and e > 0.08:
            warn.append("🔴 %s队叙事驱动风险（胜率%.1f%%<40%% 且 Edge%+.1fpp>8pp）→ 置信度减半"
                        % (side, p * 100, e * 100))
    if had[0] < 1.40:
        warn.append("🔴 主队过热预警（%.2f<1.40）→ 主队胜率-2pp、平局+1.5pp" % had[0])
    if had[2] < 1.40:
        warn.append("🔴 客队过热预警（%.2f<1.40）→ 客队胜率-2pp、平局+1.5pp" % had[2])
    big = max(abs(MH - MF[0]), abs(MA - MF[2]))
    if big > 0.10:
        warn.append("⚠️ 模型/市场≥10pp 分歧：按 skill「国内联赛定价更精准」原则，先假定我方数据有缺口，不直接采信")
    if min(m["home_home"][0], m["away_away"][0]) < 3:
        warn.append("⚠️ 主/客分离样本≤2 场，口径A偏薄（已按样本量混入近10场）")
    for w in warn or ["✅ 无预警"]:
        print("    " + w)
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    ids = list(MATCHES) if a.all else a.ids
    sp = os.path.join(STATE_BATCH, "_slate.json")
    slate = {}
    if os.path.exists(sp):
        val = jload(sp).get("value") or {}
        for mi in val.get("matchInfoList", []):
            for x in mi.get("subMatchList", []) or []:
                slate[str(x.get("matchId"))] = x
    else:
        print("⚠️ 没有 state/_slate.json —— 先跑 sporttery_fetch.py slate")
    for mid in ids:
        run(mid, slate)


if __name__ == "__main__":
    main()
