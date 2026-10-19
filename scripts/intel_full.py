# -*- coding: utf-8 -*-
"""周二（或任意批次）内部全维度报告：盘口五套 → 泊松 → 蒙特卡洛 → 外媒与 AI → 技术面 → 收敛。

用法：
    python -X utf8 scripts/intel_full.py --date 20261020 --weekday 周二 --model state/batch/_model_20261020_tue.txt

设计要点（2026-10-19 用户 m07919 定）：
  1. 三档＝三个赛果按模型概率从高到低各占一格（修掉「首选主胜/次选客胜/防范客胜」的同向 bug）；
  2. 泊松给解析解，蒙特卡洛给「抽样验证 + 参数扰动下的稳定率」，两者各司其职；
  3. 外媒与全球 AI 预测单独一节，读数全部带来源链接，源之间打架就照实写；
  4. 每场六块固定顺序，全批总结放最后。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import paid_cyber as pc  # noqa: E402

STATE = ROOT / "state"
DIRS_CN = ["主胜", "平", "客胜"]

OUT = ROOT / "📝文章"
LAB = ["主胜", "平", "客胜"]


# ────────────────────────── 蒙特卡洛 ──────────────────────────
def mc_main(lh: float, la: float, n: int = 100_000, seed: int = 20261020) -> dict:
    """纯泊松抽样，用来验证解析解的实现有没有写错。"""
    rng = np.random.default_rng(seed)
    hg = rng.poisson(lh, n)
    ag = rng.poisson(la, n)
    win = hg > ag
    draw = hg == ag
    loss = hg < ag
    out = [win.mean() * 100, draw.mean() * 100, loss.mean() * 100]
    tot = hg + ag
    pair = hg * 100 + ag
    codes, counts = np.unique(pair, return_counts=True)
    order = np.argsort(-counts)[:5]
    top = [{"s": f"{int(c // 100)}-{int(c % 100)}", "p": counts[i] / n * 100} for i in order for c in [codes[i]]]
    return {
        "n": n,
        "out": out,
        "over25": float((tot >= 3).mean() * 100),
        "btts": float(((hg > 0) & (ag > 0)).mean() * 100),
        "top": top,
    }


def mc_stability(lh: float, la: float, groups: int = 200, per: int = 2000,
                 band: float = 0.12, seed: int = 20261020) -> dict:
    """λ 在 ±12% 上扰动，看首选方向 / 首选比分能稳住多少组。

    这是蒙特卡洛真正带来、解析解给不了的东西：模型参数本身有不确定性，
    稳不住的方向不该在公开稿里站。
    """
    rng = np.random.default_rng(seed)
    lab_ok = 0
    score_ok: dict[str, int] = {}
    for _ in range(groups):
        k1 = rng.uniform(1 - band, 1 + band)
        k2 = rng.uniform(1 - band, 1 + band)
        h = rng.poisson(lh * k1, per)
        a = rng.poisson(la * k2, per)
        n_win, n_draw, n_loss = (h > a).sum(), (h == a).sum(), (h < a).sum()
        idx = int(np.argmax([n_win, n_draw, n_loss]))
        if idx == 0:
            lab_ok += 1
        pair = h * 100 + a
        codes, counts = np.unique(pair, return_counts=True)
        top_pair = int(codes[int(np.argmax(counts))])
        key = f"{top_pair // 100}-{top_pair % 100}"
        score_ok[key] = score_ok.get(key, 0) + 1
    top_scores = sorted(score_ok.items(), key=lambda kv: -kv[1])[:3]
    return {
        "groups": groups, "per": per, "band": band,
        "dir_stable": lab_ok / groups * 100,
        "scores": [(s, c / groups * 100) for s, c in top_scores],
    }


# ────────────────────────── 取数 ──────────────────────────
def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def f(v, nd: int = 1) -> str:
    return "—" if v is None else f"{v:.{nd}f}"


def pct(v) -> str:
    return "—" if v is None else f"{v:.1f}%"


def sec_market(m: dict, it: dict) -> list[str]:
    L = ["### 一、盘口（五套 + 位移 + 跨盘一致性）", ""]
    mk = it.get("markets") or {}
    if not mk.get("available"):
        L += ["- 本场拿不到盘口快照。", ""]
        return L
    had = mk.get("had") or {}
    hh = mk.get("hhad") or {}
    if had:
        L.append(f"- **胜平负**：{had['odds'][0]:.2f} / {had['odds'][1]:.2f} / {had['odds'][2]:.2f}"
                 f"（{had['n']} 次快照，{had['stamp']}，返还率 {f(had['payout'], 2)}%）→ 去水 "
                 f"{' / '.join(pct(x) for x in had['p'])}")
    else:
        L.append("- **胜平负**：本场无固定奖金（未开售或已封盘），跨盘一致性做不了。")
    if hh:
        L.append(f"- **让球 {hh.get('line')}**：{hh['odds'][0]:.2f} / {hh['odds'][1]:.2f} / {hh['odds'][2]:.2f}"
                 f"（{hh['n']} 次）→ 去水 {' / '.join(pct(x) for x in hh['p'])}")
    ttg = mk.get("ttg") or {}
    if ttg:
        L.append("")
        L.append("| 总进球 | " + " | ".join(f"{i} 球" for i in range(8)) + " |")
        L.append("|---" * 9 + "|")
        L.append("| 去水概率 | " + " | ".join(pct(x) for x in ttg["p"]) + " |")
        L.append("| 赔率 | " + " | ".join(f"{o:.2f}" for o in ttg["odds"]) + " |")
    for line in (it.get("hot") or [])[:2]:
        L.append(f"- {line}")
    mv = it.get("move") or []
    if mv:
        L += ["", "**位移**", ""]
        for line in mv[:2]:
            L.append(f"- {line}")
    cr = it.get("cross") or []
    if cr:
        L += ["", "**跨盘校验**", ""]
        for line in cr[:3]:
            L.append(f"- {line}")
    L.append("")
    return L


def sec_poisson(m: dict) -> list[str]:
    L = ["### 二、泊松分布（解析解）", ""]
    lam = m["lam"]
    L.append(f"- **λ**：主 {f(lam['fin'][0], 2)} / 客 {f(lam['fin'][1], 2)}，合计 {f(lam['total'], 2)}"
             f"（实际数据法 {f(lam['l1'][0], 2)}/{f(lam['l1'][1], 2)}；市场反推法 {f(lam['l2'][0], 2)}/{f(lam['l2'][1], 2)}）")
    oc = m.get("oc") or {}
    if oc:
        L.append(f"- **三向**：纯泊松 {' / '.join(pct(x) for x in oc['pois'])}"
                 f"　→　Dixon-Coles 修正后 {' / '.join(pct(x) for x in oc['dc'])}")
    L.append(f"- **总进球**：大 1.5 {pct(m['over'].get('1.5'))}、大 2.5 {pct(m['over'].get('2.5'))}、"
             f"大 3.5 {pct(m['over'].get('3.5'))}；双方进球 {pct(m.get('btts'))}")
    g = m.get("goals_dc") or []
    if g:
        L.append("")
        L.append("| 总进球 | " + " | ".join(f"{i}" for i in range(len(g))) + " |")
        L.append("|---" * (len(g) + 1) + "|")
        L.append("| 去水概率 | " + " | ".join(pct(x) for x in g) + " |")
    top = (m.get("top") or [])[:8]
    if top:
        L += ["", "**比分网格 Top8（Dixon-Coles 修正后）**", "",
              "| 比分 | 模型概率 | 官方定价 | 溢价 |", "|---|---|---|---|"]
        for t in top:
            L.append(f"| {t['s']} | {pct(t['p'])} | {f(t.get('odd'), 2)} | {t.get('ev'):+.2f} |" if t.get("odd") is not None
                     else f"| {t['s']} | {pct(t['p'])} | — | — |")
    ld = m.get("low_delta") or []
    if ld:
        bits = "；".join(f"{d['s']} {pct(d['p_pois'])}→{pct(d['p_dc'])}（{d['p_dc'] - d['p_pois']:+.1f}pp）" for d in ld[:4])
        L += ["", f"- **低比分修正**（Dixon-Coles ρ 把 0-0/1-0/0-1/1-1 四格往真实方向拨）：{bits}"]
    L.append("")
    return L


def sec_mc(m: dict, a: dict, b: dict) -> list[str]:
    L = ["### 三、蒙特卡洛", ""]
    L.append(f"**A · 纯泊松抽样 {a['n']:,} 次**（用来验证解析解的实现有没有写错——两者应当几乎重合）")
    L.append("")
    L.append("| 指标 | 蒙特卡洛 | 解析解 | 差 |")
    L.append("|---|---|---|---|")
    oc = m.get("oc") or {}
    for i, k in enumerate(LAB):
        ref = oc.get("pois", [None] * 3)[i]
        L.append(f"| {k} | {pct(a['out'][i])} | {pct(ref)} | {a['out'][i] - ref:+.2f}pp |")
    L.append(f"| 大 2.5 球 | {pct(a['over25'])} | {pct(m['over'].get('2.5'))} | "
             f"{a['over25'] - m['over'].get('2.5', 0):+.2f}pp |")
    L.append(f"| 双方进球 | {pct(a['btts'])} | {pct(m.get('btts'))} | "
             f"{a['btts'] - (m.get('btts') or 0):+.2f}pp |")
    gap = max(abs(a["out"][i] - (oc.get("pois") or [0, 0, 0])[i]) for i in range(3))
    if gap > 0.5:
        L.append("")
        L.append(f"- 口径差说明：解析解的比分矩阵截断在 6 球（7×7），大于 6 球的状态被压回边界；"
                 f"蒙特卡洛不截断，所以强队一侧会略高（本次最大差 {gap:.2f}pp）。"
                 "这是两种算法的边界差，不是哪一边算错了。")
    L.append("")
    L.append(f"比分抽样 Top5：{'；'.join(t['s'] + ' ' + pct(t['p']) for t in a['top'])}")
    L.append("")
    L.append(f"**B · λ 扰动 ±{b['band'] * 100:.1f}%，{b['groups']} 组 × {b['per']:,} 次**"
             "（参数本身有不确定性，稳不住的方向不站）")
    L.append("")
    L.append(f"- 首选方向稳定率：**{b['dir_stable']:.1f}%**（{int(b['dir_stable'] / 100 * b['groups'])}/{b['groups']} 组仍把"
             f"{m['verdict']['first']}排在第一位）")
    L.append(f"- 首选比分稳定率：{'；'.join(s + ' ' + f'{p:.1f}%' for s, p in b['scores'])}"
             f"　—　模型首选是 {m['verdict']['first_score']}"
             f"（{next((p for s, p in b['scores'] if s == m['verdict']['first_score']), 0.0):.1f}%）")
    L.append("")
    return L


def sec_ext(no: str, ext: dict) -> list[str]:
    L = ["### 四、外媒与全球 AI 预测", ""]
    srcs = ((ext.get("matches") or {}).get(no) or {}).get("sources") or []
    if not srcs:
        L += ["- 本场没有搜到可用的外媒或 AI 模型读数（无源不写，留空不编）。", ""]
        return L
    L.append("| 来源 | 类型 | 倾向 | 读数 |")
    L.append("|---|---|---|---|")
    kind_cn = {"ai": "统计/AI 模型", "media": "媒体前瞻", "market": "预测市场/报价", "vote": "用户投票"}
    for s in srcs:
        L.append(f"| [{s['src']}]({s['url']}) | {kind_cn.get(s['kind'], s['kind'])} | {s.get('lean', '—')} | {s['read']} |")
    L.append("")
    leans: dict[str, int] = {}
    for s in srcs:
        if s.get("lean") and s["lean"] != "—":
            leans[s["lean"]] = leans.get(s["lean"], 0) + 1
    if leans:
        top = sorted(leans.items(), key=lambda kv: -kv[1])
        L.append(f"- **各家倾向分布**：{'；'.join(f'{k} {v} 家' for k, v in top)}（共 {len(srcs)} 源）")
        L.append("")
    return L


def sec_tech(m: dict, lg: dict) -> list[str]:
    L = ["### 五、技术面", ""]
    tech = m.get("tech") or {}
    rows = []
    for side, cn in (("home", "主队"), ("away", "客队")):
        t = tech.get(side) or {}
        if not t:
            continue
        rows.append(f"| {cn} | {t.get('n', '—')} | {f(t.get('gf_avg'))} | {f(t.get('ga_avg'))} | "
                    f"{pct(t.get('cs_rate'))} | {pct(t.get('share_1h'))} |")
    if rows:
        L.append("| | 样本 | 场均进 | 场均失 | 零封率 | 上半场进球占比 |")
        L.append("|---|---|---|---|---|---|")
        L += rows
    intel = m.get("intel") or {}
    if intel.get("note"):
        L += ["", f"- **数据口径**：{intel['note']}"]
    inj = intel.get("inj") or []
    if inj:
        side_cn = {"home": "主", "away": "客"}
        L.append(f"- **伤停 / 停赛 {len(inj)} 人**：" + "；".join(
            f"{side_cn.get(i.get('side', ''), '')} {i.get('name', '')}（{i.get('pos', '')}）"
            for i in inj[:6]))
    else:
        L.append("- **伤停**：官方名单为空（缺源，不做推断）")
    def rank_line(r: dict | None) -> str:
        if not r:
            return "—"
        gd = (r.get("gd") or "").replace("&#8722;", "-")
        return (f"第 {r.get('pos')}（{r.get('pld')} 场 {r.get('w')}胜{r.get('d')}平{r.get('l')}负，"
                f"{r.get('gf')} 进 {r.get('ga')} 失 {gd}，{r.get('pts')} 分）")
    if lg.get("home_rank") or lg.get("away_rank"):
        L.append(f"- **积分榜**：主队 {lg.get('home')} {rank_line(lg.get('home_rank'))}；"
                 f"客队 {lg.get('away')} {rank_line(lg.get('away_rank'))}")
    wx = lg.get("weather") or {}
    if wx:
        L.append(f"- **比赛时刻天气**：{wx.get('time', '—')} 当地 {f(wx.get('temp'))}°C、"
                 f"风 {f(wx.get('wind'))} km/h、降水 {f(wx.get('rain'))} mm")
    if m.get("warn"):
        L += ["", "**模型自身的告警**"]
        for w in m["warn"]:
            L.append(f"- {w}")
    L.append("")
    return L


def sec_converge(m: dict, it: dict) -> list[str]:
    L = ["### 六、收敛", ""]
    v = m["verdict"]
    sc = v["scenario"]
    L.append("比分按**剧本**给：主剧本两格（怎么赢最可能），其他剧本一格（不按主剧本走会是什么样）。")
    L.append("")
    main_p_s = "、".join(
        f"{s} {pct(p)}" for s, p in zip(sc["main_scores"], sc["main_scores_p"])
    )
    L.append(f"| 剧本 | 覆盖方向 | 合计概率 | 比分 |")
    L.append("|---|---|---|---|")
    L.append(f"| **{sc['main']}** | {' + '.join(sc['main_sides'])} | {pct(sc['main_p'])} | {main_p_s} |")
    L.append(f"| {sc['alt']}（其他） | {sc['alt']} | {pct(sc['alt_p'])} | "
             f"{sc['alt_score']} {pct(sc['alt_score_p'])} |")
    L.append("")
    if sc["main_merged"]:
        gap = abs(sorted(m["p"], reverse=True)[0] - sorted(m["p"], reverse=True)[1])
        L.append(f"- 前两路只差 {gap:.1f}pp，写死单一赛果会过窄，所以主剧本按「{sc['main']}」处理，"
                 f"两个比分分别取赢和平各自的最高一格。")
    L.append("**三个赛果的概率排序**（辅助读数，不是三个建议）")
    L.append("")
    L.append("| 序 | 方向 | 模型概率 | 定价同一格 |")
    L.append("|---|---|---|---|")
    mk_p = m["mk"]
    for name, dk in (("1", "first"), ("2", "second"), ("3", "guard")):
        d = v[dk]
        L.append(f"| {name} | {d} | {pct(v[dk + '_p'])} | {pct(mk_p[LAB.index(d)])} |")
    L.append("")
    hot_note = "，与模型首选同格" if v["hot_is_first"] else f"，模型只给 {pct(v['market_hot_model_p'])}"
    L.append(f"- 定价最热的是 **{v['market_hot']}**（{pct(v['market_hot_mk_p'])}）{hot_note}。")
    cold = m.get("cold") or {}
    if cold:
        L.append(f"- 冷门指数 {f(cold.get('index'), 1)}：定价最热那格在模型里只剩 {pct(cold.get('fav_model'))}。")
    conf = m.get("conf") or {}
    if conf:
        L.append(f"- 信心 {conf.get('total')}/100（{conf.get('grade')}）：样本 {conf.get('n_sample')} 场、"
                 f"三方一致 {conf.get('agree')}/3、最大分歧 {f(conf.get('maxpp'))}pp、比分集中度 {pct(conf.get('top3'))}。")
    L.append("")
    return L


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--weekday", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--ext", default=None, help="state/records/_ext_ai_<date>.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--nums", nargs="*", default=None, help="只出这些场次，如 周二001")
    a = ap.parse_args()

    data = pc.build(Path(a.model), a.date)
    ms = data["matches"]
    if a.nums:
        want = set(a.nums)
        ms = [m for m in ms if m["no"] in want]

    intel_p = STATE / "intel" / a.date / f"_intel_{a.date}.json"
    intel = load_json(intel_p) if intel_p.exists() else {"matches": []}
    by_no = {x["no"]: x for x in intel.get("matches") or []}

    lg_p = STATE / "intel" / a.date / f"_leagues_{a.date}.json"
    lg_all = load_json(lg_p) if lg_p.exists() else {"matches": []}
    lg_by = lg_all.get("matches") or {}

    ext_p = Path(a.ext) if a.ext else STATE / "records" / f"_ext_ai_{a.date}.json"
    ext = load_json(ext_p) if ext_p.exists() else {"matches": {}}

    L = [f"# {a.weekday}档 · 全维度内部分析报告（{a.date}）", "",
         "> **口径**：90 分钟常规时间，加时与点球不计。所有概率均按各自盘口返还率去水后重算。",
         "> **顺序**：盘口 → 泊松 → 蒙特卡洛 → 外媒与 AI → 技术面 → 收敛。全批总结放在最后。",
         "> **比分口径**：按剧本给比分——主剧本两格（怎么赢最可能），其他剧本一格（不按主剧本走长什么样）。"
         "主剧本与次选差距在 10pp 以内且能合成「某队不败」时，主剧本按不败写，比分取赢和平各自最高一格。", ""]

    for m in ms:
        it = by_no.get(m["no"]) or {}
        lg = lg_by.get(m["no"]) or {}
        a_ = mc_main(m["lam"]["fin"][0], m["lam"]["fin"][1])
        b_ = mc_stability(m["lam"]["fin"][0], m["lam"]["fin"][1])
        L.append(f"## {m['no']} {m['league']} {m['home']} vs {m['away']}　{m['kick']}｜让球 {m['hand']}")
        L.append("")
        L += sec_market(m, it)
        L += sec_poisson(m)
        L += sec_mc(m, a_, b_)
        L += sec_ext(m["no"], ext)
        L += sec_tech(m, lg)
        L += sec_converge(m, it)

    # ── 全批总结（放最后）
    L += ["## 全批总结", ""]
    L.append("| 场次 | 对阵 | 模型三向 | 定价三向 | 最大分歧 | 首选方向稳定率 | 各家外媒/AI 倾向 |")
    L.append("|---|---|---|---|---|---|---|")
    for m in ms:
        b_ = mc_stability(m["lam"]["fin"][0], m["lam"]["fin"][1])
        srcs = ((ext.get("matches") or {}).get(m["no"]) or {}).get("sources") or []
        leans: dict[str, int] = {}
        for s in srcs:
            if s.get("lean") and s["lean"] != "—":
                leans[s["lean"]] = leans.get(s["lean"], 0) + 1
        lean_s = "；".join(f"{k}{v}" for k, v in sorted(leans.items(), key=lambda kv: -kv[1])) or "—"
        L.append(f"| {m['no']} | {m['home']} vs {m['away']} | {' / '.join(pct(x) for x in m['p'])} | "
                 f"{' / '.join(pct(x) for x in m['mk'])} | {max(abs(x) for x in m['edge']):.1f}pp | "
                 f"{b_['dir_stable']:.0f}% | {lean_s} |")
    L.append("")

    # ── 站位建议（按「分歧在哪个轴 × 稳定率 × 外媒同侧」机械判定，不凭感觉）
    # 2026-10-19 改版：旧规则只看分歧大小，把「同向分歧（只是幅度差）」误判成「方向被打脸」，
    # 差点把 007 那类正确的稿子改坏。现在先分同向/反向，再各自裁决。
    L += ["## 站位建议（机械判定，不是推荐）", ""]
    L.append("第一步不是看分歧大小，而是看**分歧在哪个轴上**：同向分歧（模型与定价 argmax 一致，只是幅度差）"
             "跟方向就能用；反向分歧（argmax 相反）要先问「谁更可能错」，再用外媒/AI 与稳定性裁决。"
             "稳定率低于 50% 的一律不碰方向。")
    L.append("")
    L.append("| 站法 | 触发条件 |")
    L.append("|:--|:--|")
    L.append("| 跟模型方向 | 同向、分歧 <15pp、稳定率 ≥80% |")
    L.append("| 跟方向不跟幅度 | 同向但分歧 ≥15pp |")
    L.append("| 跟定价方向 | 反向，但外媒/AI 至少两家站定价侧 |")
    L.append("| 让球观察（±1 盘才成立） | 定价胜平负给得高，但让一球那格明显低（它在说赢不出净胜球）；或给了客胜却让受让主队最高（让球盘自己不信客队能赢） |")
    L.append("| 方向不站，只谈总进球 | 稳定率 <50%，或两边读数打平到没有差价 |")
    L.append("")
    L.append("| 场次 | 同向/反向 | 最大分歧 | 首选方向稳定率 | 外媒/AI 与谁同侧 | 判定 |")
    L.append("|---|---|---|---|---|---|")

    def _argmax(xs) -> int:
        return max(range(3), key=lambda i: xs[i])

    for m in ms:
        b_ = mc_stability(m["lam"]["fin"][0], m["lam"]["fin"][1])
        gap = max(abs(x) for x in m["edge"])
        v = m["verdict"]
        m_pick = _argmax(m["mk"])
        model_i, mk_i = _argmax(m["p"]), m_pick
        same_axis = "同向" if model_i == mk_i else "**反向**"
        srcs = ((ext.get("matches") or {}).get(m["no"]) or {}).get("sources") or []
        model_side = sum(1 for s in srcs if s.get("lean") == v["first"])
        mk_side = sum(1 for s in srcs if s.get("lean") == v["market_hot"])
        if model_side > mk_side:
            side, adj = f"模型（{model_side} 家）", "，外媒同侧加一档"
        elif mk_side > model_side:
            side, adj = f"定价（{mk_side} 家）", "，外媒反向减一档"
        else:
            side, adj = ("两边都不靠" if not srcs else "两家打平"), ""
        stable = b_["dir_stable"]

        # m 是 paid_cyber 的场次字典（没有 markets）；让球三向与线都在 intel 记录里
        it_ = by_no.get(m["no"]) or {}
        hh = (it_.get("markets") or {}).get("hhad") or {}
        hs = hh.get("p") or []
        line = hh.get("line") if hh.get("line") is not None else m.get("hand")
        gate_flip = len(hs) == 3 and _argmax(hs) != mk_i

        # 让球那格的观察：只在恰好 ±1 的盘上成立。深盘（如 +2）讲的是「差几个球」，
        # 跟胜平负的「谁赢」不是同一件事，硬套会误判（周二002 就被套过一次）。
        mg = ""
        try:
            line_abs = abs(int(str(line).replace("+", "").strip()))
        except (TypeError, ValueError):
            line_abs = 0
        if len(hs) == 3 and line_abs == 1:
            if str(line).strip().startswith("-") and mk_i == 0 and m["mk"][0] >= 50 and hs[0] < 40:
                mg = (f"定价给{DIRS_CN[mk_i]} {f(m['mk'][0])}%，但让一球那格只有 {f(hs[0])}%，"
                      "它自己在说赢不出净胜球，受让一侧不吃亏")
            elif str(line).strip().startswith("+") and mk_i == 2 and _argmax(hs) == 0 and hs[0] >= 50:
                mg = (f"定价给{DIRS_CN[mk_i]} {f(m['mk'][mk_i])}%，但让球盘把主队受让不败"
                      f"放到 {f(hs[0])}%、是让球三格最高的一格，两边不是同一件事")

        # 方向怎么站：先看稳定性，再看分歧落在哪个轴
        if stable < 50:
            dir_txt = f"方向不站，只谈总进球（稳定率 {stable:.0f}%）"
        elif model_i == mk_i:
            dir_txt = (f"可站模型方向 {v['first']}{adj}" if gap < 15
                       else f"跟方向不跟幅度（同向、分歧 {gap:.1f}pp）")
        else:
            if mk_side > model_side:
                dir_txt = f"跟定价方向 {DIRS_CN[mk_i]}（反向，外媒 {mk_side} 家站定价）"
            elif model_side > mk_side:
                dir_txt = f"可站模型方向 {v['first']}{adj}（反向，但外媒 {model_side} 家站模型）"
            else:
                dir_txt = "方向不站（反向且无第三方裁决）"
        verdict_txt = dir_txt + (f"｜让球观察：{mg}" if mg else "")
        L.append(f"| {m['no']} | {same_axis} | {gap:.1f}pp | {stable:.0f}% | {side} | {verdict_txt} |")
    L.append("")
    L.append("**两条读表提醒**：")
    L.append("")
    L.append("- 「让球观察」不是站方向——读的是**定价自己承认或自相矛盾**的那一格，"
             "说的是「定价知道主队赢不出净胜球」，不是「主队赢不了」。")
    L.append("- 「方向不站」不等于这场没话说：总进球期望、双方进球、比分剧本照样能给，只是不认方向。")
    L.append("")

    # 文件名不能写死「欧冠」——这一批可能是意甲/英超/巴甲混编
    leagues = {m["league"] for m in ms}
    label = "欧冠" if leagues == {"欧冠"} else ""
    out = Path(a.out) if a.out else OUT / a.date / (
        f"{a.date}_{a.weekday}{label}{len(ms)}场_内部分析报告.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"✅ {out}  {len(''.join(L))} 字符 / {len(L)} 行")


if __name__ == "__main__":
    main()
