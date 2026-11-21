# -*- coding: utf-8 -*-
"""20261122 批次专属工具：补齐 v3.1 模型需要的赛季主客分项（底层数据）。

数据来源（全部是真实可核对的已有缓存，不估算）：
  1. `state/intel/20261122/_leagues_20261122.json` 的 home_rank / away_rank
     —— 维基积分榜：pld / w / d / l / gf / ga / pts / pos，作为 season_*.total（全季基线）。
  2. `state/matches/<matchId>/result.json` 的逐场比分
     —— 按「本队是主队还是客队」分组，算出 season_home.home / season_away.away
        的 p / gf / ga（同主客速率）。

口径声明（重要）：分主客分项来自官方 **近 5 场逐场比分**，不是全季分项；
model_v3.data_lam 会把 n_h / n_a 作为样本量并自动向全季池化值收缩、按样本打折，
因此不会人为抬高证据等级。缺 _leagues_ 积分榜的场次保持空结构，继续走退化路径。

运行：python -X utf8 "I:/阿飞说球/📝文章/20261122/_工具/build_season_splits.py"
"""
import json
from pathlib import Path

ROOT = Path(r"I:\阿飞说球")
BASE = ROOT / "📝文章" / "20261122"
INTEL = ROOT / "state" / "intel" / "20261122"
MATCHES = ROOT / "state" / "matches"
DAY = "20261122"


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def jdump(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def as_int(x, default=0):
    try:
        return int(str(x).strip())
    except (TypeError, ValueError):
        return default


def total_of(rank):
    """维基积分榜行 → model_v3 需要的 total 结构。"""
    if not rank:
        return {}
    p = as_int(rank.get("pld"))
    gf, ga = as_int(rank.get("gf")), as_int(rank.get("ga"))
    if p < 4 or not rank.get("gf") or not rank.get("ga"):
        return {}
    return {
        "p": p, "w": as_int(rank.get("w")), "d": as_int(rank.get("d")),
        "l": as_int(rank.get("l")), "gf": gf, "ga": ga, "gd": gf - ga,
        "pts": as_int(rank.get("pts")), "rank": as_int(rank.get("pos")),
        "source": "维基积分榜（经 _leagues_ 缓存）",
    }


def split_of(rows, team):
    """官方逐场比分按主/客场分组，返回 {home:{p,gf,ga}, away:{...}}。"""
    out = {"home": {"p": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0},
           "away": {"p": 0, "gf": 0, "ga": 0, "w": 0, "d": 0, "l": 0}}
    seen = set()
    for r in rows or []:
        h = str(r.get("homeTeamShortName") or "")
        a = str(r.get("awayTeamShortName") or "")
        d = str(r.get("matchDate") or "")
        key = (d, h, a)
        if key in seen:
            continue
        seen.add(key)
        s = str(r.get("fullCourtGoal") or "")
        if ":" not in s:
            continue
        try:
            x, y = [int(v) for v in s.split(":")[:2]]
        except ValueError:
            continue
        is_home = (h == team)
        gf, ga = (x, y) if is_home else (y, x)
        slot = out["home" if is_home else "away"]
        slot["p"] += 1
        slot["gf"] += gf
        slot["ga"] += ga
        if gf > ga:
            slot["w"] += 1
        elif gf == ga:
            slot["d"] += 1
        else:
            slot["l"] += 1
    for slot in out.values():
        slot["gd"] = slot["gf"] - slot["ga"]
        slot["pts"] = 3 * slot["w"] + slot["d"]
        slot["source"] = "竞彩官方 webapi 近 5 场逐场比分（非全季分项）"
    return out


data = jload(INTEL / f"_data_{DAY}.json")
books = jload(INTEL / f"_books_{DAY}.json")
leagues_raw = jload(INTEL / f"_leagues_{DAY}.json")
leagues = {k[-3:]: v for k, v in (leagues_raw.get("matches") or {}).items()}
slate = jload(ROOT / "state" / "batch" / "_slate.json")
num2mid = {
    str(m["matchNumStr"])[-3:]: str(m.get("matchId"))
    for mi in slate["value"]["matchInfoList"]
    for m in (mi.get("subMatchList") or [])
    if m.get("businessDate") == "2026-11-22"
}

report = []
for no in sorted(books):
    key = books[no]["id"]
    row = data.get(key)
    if not row:
        continue
    lg = leagues.get(no) or {}
    th = total_of(lg.get("home_rank"))
    ta = total_of(lg.get("away_rank"))
    mid = num2mid.get(no)
    res = jload(MATCHES / mid / "result.json").get("value") or {} if mid else {}
    hm = (res.get("home") or {}).get("matchList") or []
    am = (res.get("away") or {}).get("matchList") or []
    sh_splits = split_of(hm, row["home"])
    sa_splits = split_of(am, row["away"])

    if th and ta and sh_splits["home"]["p"] and sa_splits["away"]["p"]:
        row["season_home"] = {"total": th, **sh_splits}
        row["season_away"] = {"total": ta, **sa_splits}
        row["season_source"] = (
            "total=维基积分榜全季（%d / %d 场）；分主客速率=竞彩官方近 5 场逐场比分"
            "（主 %d 场 / 客 %d 场，非全季分项，模型按样本收缩）"
            % (th["p"], ta["p"], sh_splits["home"]["p"], sa_splits["away"]["p"]))
        status = "已补"
    else:
        row["season_home"] = {}
        row["season_away"] = {}
        row["season_source"] = "维基积分榜或官方逐场比分缺源，保持空结构，模型走退化路径"
        status = "缺源（退化）"
    report.append((no, row["home"], row["away"], status,
                   th.get("p", 0), ta.get("p", 0),
                   sh_splits["home"]["p"], sa_splits["away"]["p"]))

jdump(INTEL / f"_data_{DAY}.json", data)

ok = sum(1 for r in report if r[3] == "已补")
lines = [
    "# 底层数据补齐清单 · 2026-11-22（赛季主客分项）",
    "",
    "> 生成：`📝文章/20261122/_工具/build_season_splits.py`。目标：让 `model_v3.data_lam`",
    "> 能读到 `season_home/season_away` 的 `total`（全季）与 `home/away`（分主客速率）。",
    "",
    "## 一、数据来源与口径",
    "",
    "| 字段 | 来源 | 口径 |",
    "|:--|:--|:--|",
    "| `season_*.total` 的 p/w/d/l/gf/ga/pts/rank | `state/intel/20261122/_leagues_20261122.json`（维基积分榜缓存） | 全季联赛积分榜，真实数值 |",
    "| `season_home.home` / `season_away.away` 的 p/gf/ga | `state/matches/<id>/result.json`（竞彩官方 webapi 逐场比分） | **近 5 场**按主客分组计算，不是全季分项 |",
    "",
    "**口径声明**：分主客分项窗口只有近 5 场，`n_h`/`n_a` 普遍为 1–4 场。`model_v3.data_lam`",
    "会把这两个数当样本量，向全季池化值收缩并提示「同主客样本不足……融合权重按样本打折」。",
    "因此补齐的是**结构缺失**，不是把证据等级硬抬上去；最终权重仍由模型自己按样本决定（R60）。",
    "",
    "## 二、逐场覆盖",
    "",
    "| 场次 | 对阵 | 状态 | 全季 p（主/客） | 分主客样本（主/客） |",
    "|:--|:--|:--|:--|:--|",
]
for no, h, a, status, ph, pa, nh, na in report:
    lines.append("| 周日%s | %s vs %s | %s | %d / %d | %d / %d |" % (no, h, a, status, ph, pa, nh, na))
lines += [
    "",
    "- **补齐 %d/18 场**；其余 %d 场因维基积分榜缺该联赛表或字段不全，保持空结构、继续走退化路径。" % (ok, 18 - ok),
    "- 官方 `tables.json`（`getMatchTablesV2`）18 场全是空壳，本项目既有数据缺口仍在；本次改用维基积分榜 + 官方逐场比分绕过，未改项目真源。",
    "",
    "## 三、xG / 高阶指标",
    "",
    "- **未取到可核对的 xG / xGA / npxG / PPDA / 定位球 xG / 失球时间分布**：外围检索返回的都是赔率、赛果与文字情报，没有逐场 xG 数值。",
    "- 按纪律不估算、不用「场均进球」冒充 xG，这部分仍列为缺口（与 `open_items` 里「战术层与失球时间分布缺口」一致）。",
    "- `feature.json` 里的 `goalAvg` 是近 10 场场均进球、`eachHomeAway` 是胜负平场数，均非 xG，未混入模型。",
    "",
    "## 四、纪律",
    "",
    "- 未改 `scripts/model_v3.py` 等主干脚本，未手动调整融合权重或把握分级。",
    "- 90 分钟常规时间口径；本文为 A 层内部资料，永不上平台；仅作数据观察与思路参考，不构成投注建议。",
]
(BASE / "底层数据补齐_20261122.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("OK 赛季主客分项补齐 %d/18 场 → _data_%s.json + 人读清单" % (ok, DAY))
