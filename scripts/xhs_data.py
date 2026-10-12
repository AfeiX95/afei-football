#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""给小红书卡片补齐「近期战绩对比」+「六维雷达对比」数据（scripts/xhs_html.py 渲染用）。

数据全部取自本机竞彩缓存 `state/_match_<sportteryMatchId>/`（`scripts/sporttery_fetch.py match <id>` 的产物）：
  feature.json → 主/客各自 10 场战绩、同主客战绩、场均进球、场均失球
  result.json  → 近 5 场战绩 + 逐场比分（算胜平负串）
  history.json → 交锋历史（够 3 场且两队胜率不同才启用，否则第 4 维退回「主客战力」）

六维雷达 6 个维度（0–100，**全部来自官方赛果数据，不含任何市场/机构信息**）：
  进攻能力 = 近 10 场场均进球 ÷ 3 × 100（封顶 100）
  中场控制力 = 50 + 近 5 场场均净胜球×14 + (不败率−0.5)×20（控场代理：本地缓存没有控球率/传球数据）
  防守能力 = (1 − 近 10 场场均失球 ÷ 3) × 100（下限 0）
  近期状态 = 近 5 场积分率 (3胜+平) / (3×场次) × 100
  主客战力 = 同主客场近 10 场胜率（官方已给 0–100 分）；有交锋数据时换成「交锋历史」= 该队交锋胜率
  进球稳定性 = 100 − 近 5 场进球的样本标准差 × 45（数据里没有射门/预期进球，用输出离散度刻画）
（文章那边 football-toutiao-html-generator 的 radar_dims 是另一套口径，卡片这里独立定义。）

> 2026-10-12 起**第 6 维不再是「市场支持」**：小红书首篇被判「财产安全风险/赌博」（坑#69），
> 机构三向折算属于线上彩票/购彩信息，卡片一律不出现市场数据。

用法：
  python scripts/xhs_data.py --input "📝文章/20261014/小红书/cards.json"     # 补齐并写回
  python scripts/xhs_data.py --input ... --force                           # 覆盖已有 form/radar
  python scripts/xhs_data.py --input ... --dry                             # 只看结果，不写文件
"""
import argparse
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIMS = ["进攻能力", "中场控制力", "防守能力", "近期状态", "主客战力", "进球稳定性"]
H2H_DIM = "交锋历史"


def val(d: Path, name: str) -> dict:
    """读 sporttery_fetch.py 落盘的 <name>.json，取里面的 value 段。"""
    p = d / f"{name}.json"
    if not p.exists():
        return {}
    try:
        obj = json.load(io.open(p, encoding="utf-8"))
    except Exception:
        return {}
    v = obj.get("value")
    return v if isinstance(v, dict) else {}


def num(x, default=0.0) -> float:
    try:
        return float(str(x).replace("%", ""))
    except Exception:
        return default


def clamp(v: float) -> float:
    return max(0.0, min(100.0, round(v, 1)))


def recent_form(res_side: dict) -> dict:
    """近 5 场：胜平负、进失球、逐场结果串（旧→新，matchList 本身是新→旧）。"""
    st = res_side.get("statistics") or {}
    ml = res_side.get("matchList") or []
    tid = st.get("teamId")
    seq, gfl = [], []
    for m in reversed(ml):
        gh, ga = int(num(m.get("homeTeamFullCourtGoalCnt"))), int(num(m.get("awayTeamFullCourtGoalCnt")))
        home = m.get("homeTeamId") == tid
        gf, gl = (gh, ga) if home else (ga, gh)
        seq.append("W" if gf > gl else ("D" if gf == gl else "L"))
        gfl.append(gf)
    return {
        "l5": "%d胜%d平%d负" % (int(num(st.get("winGoalMatchCnt"))), int(num(st.get("drawMatchCnt"))),
                                int(num(st.get("lossGoalMatchCnt")))),
        "gf": int(num(st.get("goalCnt"))),
        "ga": int(num(st.get("lossGoalCnt"))),
        "net": int(num(st.get("netGoal"))),
        "seq": seq,
        "gfl": gfl,
        "n": int(num(st.get("totalLegCnt"))) or len(ml) or 1,
        "unbeaten": (num(st.get("winGoalMatchCnt")) + num(st.get("drawMatchCnt"))) /
                    max(1.0, float(int(num(st.get("totalLegCnt"))) or len(ml) or 1)),
    }


def control_rate(f: dict) -> float:
    """中场控制力（代理指标，0–100）。

    本地竞彩缓存没有控球率 / 传球成功率 / 射门等场面数据，这里用「近 5 场场均净胜球」
    与「不败率」折算控场倾向：净胜球是比赛被掌控的结果，不败率排掉「输球也刷净胜球」的噪声。
    """
    n = max(1.0, float(f.get("n") or 1))
    net_per = float(f.get("net") or 0) / n
    return clamp(50.0 + net_per * 14.0 + (float(f.get("unbeaten") or 0.5) - 0.5) * 20.0)


def stable_rate(f: dict) -> float:
    """进球稳定性（代理指标，0–100）：近 5 场进球数的离散度。

    数据里只有逐场进球，没有射门/预期进球；用「有进球的场次占比」＋「进球数的样本标准差」
    两个角度合成：场场能进且波动小 → 高分；忽高忽低或连续被零封 → 低分。
    只用离散度会在小样本上打到 0 分（如 0、0、0、6、5），所以掺一半「有球场次占比」兜底。
    """
    g = [float(x) for x in (f.get("gfl") or [])]
    if not g:
        return clamp(50.0)
    scored = sum(1 for x in g if x > 0) / float(len(g)) * 100.0
    if len(g) < 2:
        return clamp(scored)
    m = sum(g) / len(g)
    var = sum((x - m) ** 2 for x in g) / (len(g) - 1)
    steady = 100.0 - (var ** 0.5) * 30.0
    return clamp(0.5 * scored + 0.5 * steady)


def recent_rate(res_side: dict) -> float:
    """近 5 场积分率 0–100。"""
    st = res_side.get("statistics") or {}
    n = int(num(st.get("totalLegCnt"))) or len(res_side.get("matchList") or []) or 1
    pts = 3 * num(st.get("winGoalMatchCnt")) + num(st.get("drawMatchCnt"))
    return clamp(pts / (3.0 * n) * 100.0)


def h2h_counts(hist: dict, home_name: str, away_name: str):
    """从交锋 matchList 数出 (本场主队胜, 平, 本场客队胜)。

    用队名匹配（history 里的 teamId 与 result 的 teamId 不是同一套编号，实测对不上）。
    """
    def same(a, b):
        a, b = (a or "").strip(), (b or "").strip()
        return bool(a) and bool(b) and (a == b or a in b or b in a)

    ml = hist.get("matchList") or []
    hw = dr = aw = 0
    for m in ml:
        gh, ga = int(num(m.get("homeTeamFullCourtGoalCnt"))), int(num(m.get("awayTeamFullCourtGoalCnt")))
        if gh == ga:
            dr += 1
            continue
        winner = m.get("homeTeamShortName") if gh > ga else m.get("awayTeamShortName")
        if same(winner, home_name):
            hw += 1
        elif same(winner, away_name):
            aw += 1
    return hw, dr, aw


def build_one(card: dict, root: Path) -> dict:
    """算出一场的 form + radar；缺缓存的场次抛错，由调用方决定跳过还是中断。"""
    mid = card.get("sporttery_match_id") or card.get("matchId")
    if not mid:
        raise ValueError("缺 sporttery_match_id")
    d = root / "state" / f"_match_{mid}"
    if not d.exists():
        raise FileNotFoundError(f"没有本地缓存 {d}（先跑 python scripts/sporttery_fetch.py match {mid}）")
    feat, res, hist = val(d, "feature"), val(d, "result"), val(d, "history")
    eh, es = feat.get("eachHomeAway") or {}, feat.get("eachSameHomeAway") or {}
    ga, lg = feat.get("goalAvg") or {}, feat.get("lossGoalAvg") or {}
    hm, aw = res.get("home") or {}, res.get("away") or {}
    hf, af = recent_form(hm), recent_form(aw)
    hf["name"], af["name"] = card.get("home", "主队"), card.get("away", "客队")
    hf["ha"] = "主场 %d胜%d平%d负" % (int(num(eh.get("homeWinGoalMatchCnt"))),
                                      int(num(eh.get("homeDrawMatchCnt"))),
                                      int(num(eh.get("homeLossGoalMatchCnt"))))
    af["ha"] = "客场 %d胜%d平%d负" % (int(num(eh.get("awayWinGoalMatchCnt"))),
                                      int(num(eh.get("awayDrawMatchCnt"))),
                                      int(num(eh.get("awayLossGoalMatchCnt"))))
    hf["pj"], hf["sj"] = num(ga.get("homeGoalAvgCnt")), num(lg.get("homeLossGoalAvgCnt"))
    af["pj"], af["sj"] = num(ga.get("awayGoalAvgCnt")), num(lg.get("awayLossGoalAvgCnt"))

    # 第 5 维：交锋历史够 3 场且两队胜率不同才启用（否则用主客战力）
    hw, dr, aw_ = h2h_counts(hist, card.get("home", ""), card.get("away", ""))
    n_h2h = hw + dr + aw_
    use_h2h = n_h2h >= 3 and hw != aw_
    if use_h2h:
        dims = [DIMS[0], DIMS[1], DIMS[2], DIMS[3], H2H_DIM, DIMS[5]]
        d4h, d4a = clamp(hw / n_h2h * 100), clamp(aw_ / n_h2h * 100)
        h2h_txt = "近 %d 次交锋 %s %d胜%d平%d负" % (n_h2h, hm.get("statistics", {}).get("teamShortName", ""),
                                                    hw, dr, aw_)
    else:
        dims = list(DIMS)
        d4h = clamp(num(es.get("homeScoreRatio")))
        d4a = clamp(num(es.get("awayScoreRatio")))
        h2h_txt = ("近 %d 次交锋 %d胜%d平%d负（样本太少，雷达第 5 维用主客战力）" % (n_h2h, hw, dr, aw_)
                   if n_h2h else "")

    radar = {
        "dims": dims,
        "home": [clamp(hf["pj"] / 3 * 100), control_rate(hf), clamp(100 - hf["sj"] / 3 * 100),
                 recent_rate(hm), d4h, stable_rate(hf)],
        "away": [clamp(af["pj"] / 3 * 100), control_rate(af), clamp(100 - af["sj"] / 3 * 100),
                 recent_rate(aw), d4a, stable_rate(af)],
    }
    form = {"home": hf, "away": af, "h2h": h2h_txt, "h2h_n": n_h2h,
            "h2h_short": ("近 %d 次交锋 %d胜%d平%d负" % (n_h2h, hw, dr, aw_)) if n_h2h else "",
            "h2h_used": bool(use_h2h), "window": "近 5 场 / 同主客 10 场"}
    return {"form": form, "radar": radar, "match_dir": f"state/_match_{mid}"}


def enrich(cards_path: Path, force=False, dry=False) -> int:
    data = json.load(io.open(cards_path, encoding="utf-8"))
    cards = data.get("matches") or []
    ok = 0
    for i, c in enumerate(cards, 1):
        tag = "%s %s vs %s" % (c.get("no", ""), c.get("home", ""), c.get("away", ""))
        if c.get("form") and c.get("radar") and not force:
            print("  –  跳过（已有 form/radar）：" + tag)
            ok += 1
            continue
        try:
            got = build_one(c, ROOT)
        except Exception as e:
            print("  ❌ %s：%s" % (tag, e))
            continue
        c.update(got)
        r = got["radar"]
        print("  ✅ %s  form 已补  radar[%s]  主 %s  客 %s" %
              (tag, "/".join(r["dims"]), r["home"], r["away"]))
        ok += 1
    if dry:
        print("（--dry：没有写回文件）")
        return ok
    with io.open(cards_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("已写回 " + str(cards_path))
    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description="补齐卡片的近期战绩对比与六维雷达数据")
    ap.add_argument("--input", required=True, help="cards.json 路径")
    ap.add_argument("--force", action="store_true", help="覆盖已有的 form/radar")
    ap.add_argument("--dry", action="store_true", help="只打印，不写回")
    a = ap.parse_args()
    p = Path(a.input)
    if not p.exists():
        print("找不到 " + str(p))
        sys.exit(1)
    n = enrich(p, a.force, a.dry)
    print("完成：%d/%d 场" % (n, len(json.load(io.open(p, encoding="utf-8")).get("matches") or [])))
    sys.exit(0 if n else 2)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # 控制台默认 GBK，emoji/中文会炸
    main()
