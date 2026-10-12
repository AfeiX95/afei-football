#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""给小红书卡片补齐「近期战绩对比」+「六维雷达对比」数据（scripts/xhs_html.py 渲染用）。

数据全部取自本机竞彩缓存 `state/_match_<sportteryMatchId>/`（`scripts/sporttery_fetch.py match <id>` 的产物）：
  feature.json → 主/客各自 10 场战绩、同主客战绩、场均进球、场均失球
  result.json  → 近 5 场战绩 + 逐场比分（算胜平负串）
  history.json → 交锋历史（够 3 场且两队胜率不同才启用，否则第 4 维退回「主客战力」）

六维雷达 6 个维度（0–100，名称与 📚知识库/skills/football-toutiao-html-generator 的 radar_dims 对齐）：
  近期状态 = 近 5 场积分率 (3胜+平) / (3×场次) × 100
  进攻火力 = 近 10 场场均进球 ÷ 3 × 100（封顶 100）
  防守稳固 = (1 − 近 10 场场均失球 ÷ 3) × 100（下限 0）
  主客战力 = 同主客场近 10 场胜率（官方已给 0–100 分）；有交锋数据时换成「交锋历史」= 该队交锋胜率
  市场支持 = 机构三向里该队的胜率
  模型预测 = 后台模型三向里该队的胜率

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
DIMS = ["近期状态", "进攻火力", "防守稳固", "主客战力", "市场支持", "模型预测"]
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
    seq = []
    for m in reversed(ml):
        gh, ga = int(num(m.get("homeTeamFullCourtGoalCnt"))), int(num(m.get("awayTeamFullCourtGoalCnt")))
        home = m.get("homeTeamId") == tid
        gf, gl = (gh, ga) if home else (ga, gh)
        seq.append("W" if gf > gl else ("D" if gf == gl else "L"))
    return {
        "l5": "%d胜%d平%d负" % (int(num(st.get("winGoalMatchCnt"))), int(num(st.get("drawMatchCnt"))),
                                int(num(st.get("lossGoalMatchCnt")))),
        "gf": int(num(st.get("goalCnt"))),
        "ga": int(num(st.get("lossGoalCnt"))),
        "net": int(num(st.get("netGoal"))),
        "seq": seq,
    }


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

    # 第 4 维：交锋历史够 3 场且两队胜率不同才启用
    hw, dr, aw_ = h2h_counts(hist, card.get("home", ""), card.get("away", ""))
    n_h2h = hw + dr + aw_
    use_h2h = n_h2h >= 3 and hw != aw_
    if use_h2h:
        dims = [DIMS[0], DIMS[1], DIMS[2], H2H_DIM, DIMS[4], DIMS[5]]
        d4h, d4a = clamp(hw / n_h2h * 100), clamp(aw_ / n_h2h * 100)
        h2h_txt = "近 %d 次交锋 %s %d胜%d平%d负" % (n_h2h, hm.get("statistics", {}).get("teamShortName", ""),
                                                    hw, dr, aw_)
    else:
        dims = list(DIMS)
        d4h = clamp(num(es.get("homeScoreRatio")))
        d4a = clamp(num(es.get("awayScoreRatio")))
        h2h_txt = ("近 %d 次交锋 %d胜%d平%d负（样本太少，雷达第 4 维用主客战力）" % (n_h2h, hw, dr, aw_)
                   if n_h2h else "")

    mkt = list(card.get("probs_mkt") or [0, 0, 0])
    mine = list(card.get("probs_mine") or [0, 0, 0])
    radar = {
        "dims": dims,
        "home": [recent_rate(hm), clamp(hf["pj"] / 3 * 100), clamp(100 - hf["sj"] / 3 * 100),
                 d4h, clamp(mkt[0]), clamp(mine[0])],
        "away": [recent_rate(aw), clamp(af["pj"] / 3 * 100), clamp(100 - af["sj"] / 3 * 100),
                 d4a, clamp(mkt[2]), clamp(mine[2])],
    }
    form = {"home": hf, "away": af, "h2h": h2h_txt, "h2h_n": n_h2h, "window": "近 5 场 / 同主客 10 场"}
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
