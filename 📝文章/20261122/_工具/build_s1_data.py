# -*- coding: utf-8 -*-
"""20261122 批次专属工具：500 缺源时，用竞彩官方 webapi 真实数据补齐 S1 底层数据。

背景：本批 500.com 54 个页面全部被 EdgeOne 拦截（_books_ 里 ah/ou/ox 全空），
      _x500.py gate 需要 playwright（本机未装）。按 v3.2「不得跳过或凭记忆估算」，
      改用已落盘的官方 webapi 缓存（result / history / injury / head / feature），
      与 20261119 批次的既有做法一致：source 明确标注 fallback。

产出：
  state/intel/20261122/_data_20261122.json   底层战绩（key = 500 id，供 model_v3 读取）
  state/intel/20261122/_ext_20261122.json    S1 情报字段（利弊/体能/矛盾/胜负手/看点）
  📝文章/20261122/S1情报补齐清单_20261122.md  人读版：来源、覆盖率、缺口披露

纪律：所有字段由官方缓存中的真实数值生成；无源项一律留空并标注，不编造外媒观点、
      不估算赔率、不推断机构态度、不写「待补」式占位结论。
运行：python -X utf8 "I:/阿飞说球/📝文章/20261122/_工具/build_s1_data.py"
"""
import json, os, datetime
from pathlib import Path

ROOT = Path(r"I:\阿飞说球")
BASE = ROOT / "📝文章" / "20261122"
INTEL = ROOT / "state" / "intel" / "20261122"
MATCHES = ROOT / "state" / "matches"
DAY = "20261122"


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


books = jload(INTEL / f"_books_{DAY}.json")
slate = jload(ROOT / "state" / "batch" / "_slate.json")
intel_doc = jload(INTEL / f"_intel_{DAY}.json")
intel_by_no = {m["no"][-3:]: m for m in intel_doc["matches"]}
lg_raw = jload(INTEL / f"_leagues_{DAY}.json")
leagues = {k[-3:]: v for k, v in (lg_raw.get("matches") or {}).items()}

mid_by_no = {}
row_by_no = {}
for mi in slate["value"]["matchInfoList"]:
    for m in (mi.get("subMatchList") or []):
        if m.get("businessDate") == "2026-11-22":
            no = str(m.get("matchNumStr", ""))[-3:]
            mid_by_no[no] = str(m.get("matchId"))
            row_by_no[no] = m

TODAY = datetime.date(2026, 11, 22)


def official(mid, tag):
    p = MATCHES / mid / f"{tag}.json"
    if not p.exists():
        return {}
    try:
        return jload(p).get("value") or {}
    except Exception:
        return {}


def recent_block(mid, side, team):
    """从官方 result.json 的 home/away.matchList 提取逐场战绩，按 日期+主客 去重。"""
    val = official(mid, "result")
    rows = (val.get(side) or {}).get("matchList") or []
    out, seen = [], set()
    for r in rows:
        h = str(r.get("homeTeamShortName") or "")
        a = str(r.get("awayTeamShortName") or "")
        d = str(r.get("matchDate") or "")
        key = (d, h, a)
        if key in seen:
            continue
        seen.add(key)
        score = str(r.get("fullCourtGoal") or "").replace(":", "-")
        out.append({"home": h, "away": a,
                    "venue": "H" if h == team else "A",
                    "score": score, "date": d})
    return {"matches": out}


def gf_ga(matches, team):
    gf = ga = n = 0
    for m in matches:
        s = m.get("score") or ""
        if "-" not in s:
            continue
        try:
            x, y = [int(v) for v in s.split("-")[:2]]
        except ValueError:
            continue
        f, a = (x, y) if m.get("venue") == "H" else (y, x)
        gf += f
        ga += a
        n += 1
    return (round(gf / n, 2), round(ga / n, 2), n) if n else (None, None, 0)


def last_gap(matches):
    ds = sorted({m["date"] for m in matches if m.get("date")})
    if not ds:
        return None, 0
    try:
        last = datetime.date.fromisoformat(ds[-1])
        gap = (TODAY - last).days
    except ValueError:
        return None, 0
    n30 = sum(1 for d in ds if (TODAY - datetime.date.fromisoformat(d)).days <= 30)
    return gap, n30


def meetings_block(mid):
    val = official(mid, "history")
    rows = val.get("matchList") or []
    out, draw, low, btts, tot = [], 0, 0, 0, []
    for r in rows:
        s = str(r.get("fullCourtGoal") or "")
        if ":" not in s:
            continue
        try:
            x, y = [int(v) for v in s.split(":")[:2]]
        except ValueError:
            continue
        draw += int(x == y)
        low += int(x + y <= 2)
        btts += int(x > 0 and y > 0)
        tot.append(x + y)
        out.append({"d": r.get("matchDate"),
                    "m": "%s %s %s" % (r.get("homeTeamShortName", ""), s,
                                       r.get("awayTeamShortName", "")),
                    "league": r.get("tournamentShortName", "")})
    return out, {"n": len(tot),
                 "draw_pct": round(draw / len(tot) * 100) if tot else None,
                 "low_pct": round(low / len(tot) * 100) if tot else None,
                 "btts_pct": round(btts / len(tot) * 100) if tot else None,
                 "avg_total": round(sum(tot) / len(tot), 2) if tot else None}


def injuries_of(mid):
    val = official(mid, "injury")
    out = []
    for side in ("home", "away"):
        blk = val.get(side) or {}
        for p in (blk.get("injuriesAndSuspensionsList") or []):
            name = p.get("personName") or p.get("playerName") or ""
            if name:
                out.append({"side": side, "team": blk.get("teamShortName", ""), "name": name})
    seen, uniq = set(), []
    for p in out:
        k = (p["side"], p["name"])
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    return uniq


data_out, ext_out, audit_lines = {}, {}, []
for no in sorted(books):
    b = books[no]
    mid = mid_by_no.get(no)
    row = row_by_no.get(no, {})
    home = str(row.get("homeTeamAbbName") or "")
    away = str(row.get("awayTeamAbbName") or "")
    league = str(row.get("leagueAbbName") or "")
    if not mid:
        audit_lines.append("| %s | 无官方 matchId，跳过 |" % no)
        continue

    rh = recent_block(mid, "home", home)
    ra = recent_block(mid, "away", away)
    meets, mstat = meetings_block(mid)
    inj = injuries_of(mid)
    abs_home = [p["name"] for p in inj if p["side"] == "home"]
    abs_away = [p["name"] for p in inj if p["side"] == "away"]
    head = official(mid, "head")
    lg = leagues.get(no) or {}

    data_out[b["id"]] = {
        "no": "周日" + no, "league": league, "home": home, "away": away,
        "source": "竞彩官方 webapi 近5场/交锋（500 缺源 fallback）",
        "season_home": {}, "season_away": {},
        "recent_home": rh, "recent_away": ra, "meetings": meets,
    }

    hgf, hga, hn = gf_ga(rh["matches"], home)
    agf, aga, an = gf_ga(ra["matches"], away)
    hgap, h30 = last_gap(rh["matches"])
    agap, a30 = last_gap(ra["matches"])
    inj_h = sum(1 for p in inj if p["side"] == "home")
    inj_a = sum(1 for p in inj if p["side"] == "away")

    pros_home, cons_home, pros_away, cons_away = [], [], [], []
    if hgf is not None:
        pros_home.append("官方近况 %d 场场均进 %.2f 球" % (hn, hgf))
    if hga is not None:
        cons_home.append("官方近况 %d 场场均失 %.2f 球" % (hn, hga))
    if agf is not None:
        pros_away.append("官方近况 %d 场场均进 %.2f 球" % (an, agf))
    if aga is not None:
        cons_away.append("官方近况 %d 场场均失 %.2f 球" % (an, aga))
    if inj_h:
        cons_home.append("官方伤停登记 %d 人" % inj_h)
    if inj_a:
        cons_away.append("官方伤停登记 %d 人" % inj_a)
    if mstat["n"]:
        if mstat["draw_pct"] is not None and mstat["draw_pct"] >= 40:
            line = "交锋近 %d 次平局占 %d%%，排名与账面优势未必兑现" % (mstat["n"], mstat["draw_pct"])
            cons_home.append(line)
            pros_away.append(line)
        if mstat["low_pct"] is not None and mstat["low_pct"] >= 60:
            cons_home.append("交锋近 %d 次低比分（≤2 球）占 %d%%" % (mstat["n"], mstat["low_pct"]))
            cons_away.append("交锋近 %d 次低比分（≤2 球）占 %d%%" % (mstat["n"], mstat["low_pct"]))
    rank_ok = bool(lg.get("home_rank") and lg.get("away_rank"))
    if rank_ok:
        pros_home.append("官方/维基积分榜主队第 %s、客队第 %s" % (lg.get("home_rank"), lg.get("away_rank")))

    fatigue = "主队距上一场 %s 天（近 30 天 %d 场）；客队距上一场 %s 天（近 30 天 %d 场）" % (
        hgap if hgap is not None else "未知", h30,
        agap if agap is not None else "未知", a30)
    phase = head.get("phaseName") or ""
    gw = head.get("gameweek") or ""
    season = head.get("seasonName") or ""
    note = "%s 赛季 %s 第 %s 轮" % (season, league, gw) if gw else "%s 赛季 %s" % (season, league)
    if phase:
        note += " · 赛事页阶段标注「%s」" % phase

    m3 = (intel_by_no.get(no) or {}).get("markets", {}).get("had", {}).get("p")
    if m3:
        gap_pp = round(abs(m3[0] - m3[2]), 1)
        core = ("官方胜平负去水 %.1f/%.1f/%.1f，主客差 %.1fpp；"
                "主队近况 %.2f/%.2f、客队 %.2f/%.2f。账面差距与实际赢球条件需分开读。"
                % (m3[0], m3[1], m3[2], gap_pp,
                   hgf or 0, hga or 0, agf or 0, aga or 0))
    else:
        core = "官方未开胜平负（只有让球盘），无市场三向基准，本场不做方向结论。"

    if mstat["n"] and mstat["draw_pct"] is not None and mstat["draw_pct"] >= 40:
        key = ("交锋风格克制：近 %d 次交锋平局占 %d%%、低比分占 %s%%，"
               "历史对位可能让纸面实力差失效" % (mstat["n"], mstat["draw_pct"], mstat["low_pct"]))
    elif hgap is not None and agap is not None and abs(hgap - agap) >= 5:
        key = "赛程休整差：主队休整 %d 天、客队 %d 天，体能窗口不同步" % (hgap, agap)
    elif inj_h + inj_a >= 3:
        key = "阵容变化：官方登记伤停主队 %d 人、客队 %d 人，需等临场首发确认" % (inj_h, inj_a)
    elif not m3:
        key = "定价缺口：官方只开让球、无胜平负，市场基准缺失"
    else:
        key = ("近期转化率与失球结构：主队 %.2f/%.2f、客队 %.2f/%.2f，"
               "创造机会与临门一脚的表现可能让纸面数字失效" % (hgf or 0, hga or 0, agf or 0, aga or 0))

    mk = (intel_by_no.get(no) or {}).get("markets", {})
    crs = (mk.get("crs") or {}).get("cells") or []
    hafu = (mk.get("hafu") or {}).get("p") or []
    watch = []
    if crs:
        watch.append("官方波胆定价最低格 %s" % crs[0][0])
    if hafu:
        labels = (mk.get("hafu") or {}).get("labels") or []
        watch.append("半全场最热 %s %.1f%%" % (labels[0] if labels else "首格", hafu[0]))
    if mstat["n"]:
        watch.append("交锋近 %d 次场均 %.2f 球、双方进球 %s%%" % (
            mstat["n"], mstat["avg_total"] or 0, mstat["btts_pct"]))
    weather = lg.get("weather") or {}
    if weather:
        watch.append("比赛时刻天气已采（见 _leagues_）")

    ext_out[no] = {
        "note": note,
        "pros_home": pros_home or ["官方近期进失球数据见第三节，未取到额外有利情报"],
        "cons_home": cons_home or ["官方未登记额外不利情报（不等于无隐患）"],
        "pros_away": pros_away or ["官方近期进失球数据见第三节，未取到额外有利情报"],
        "cons_away": cons_away or ["官方未登记额外不利情报（不等于无隐患）"],
        "fatigue": fatigue,
        "motivation": "官方赛事页仅提供轮次与阶段（%s），不含战意标注；战意不做推断" % (phase or "未标注"),
        "abs_home": abs_home,
        "abs_away": abs_away,
        "ai_preds": [],
        "media": "未取到可核对的外媒 / 预测市场 / 第三方 AI 观点（缺源不编）",
        "core_conflict": core,
        "key_factor": key,
        "watchpoints": "；".join(watch) if watch else "官方波胆与半全场结构未取到",
        "resonance": "数据不足：500 百家欧赔与外媒/AI 预测未取到，无法判定多维共振",
        "flags": ["500 缺源 fallback"],
        "src": [
            {"d": "2026-11-21", "t": "竞彩官方 webapi：result 近况 / history 交锋 / injury 伤停 / head 赛事背景"},
            {"d": "2026-11-21", "t": "_leagues_ 积分榜与比赛时刻天气（14/18 场有排名、3 场有天气）"},
            {"d": "2026-11-21", "t": "_intel_ 官方五套盘口去水与跨盘自洽"},
        ],
    }
    audit_lines.append("| 周日%s | %s vs %s | 近况 %d/%d 场 · 交锋 %d 场 · 伤停 %d 人 · 排名 %s · 三向 %s |" % (
        no, home, away, hn, an, mstat["n"], len(inj),
        "有" if rank_ok else "缺", "有" if m3 else "缺"))

(INTEL / f"_data_{DAY}.json").write_text(
    json.dumps(data_out, ensure_ascii=False, indent=1), encoding="utf-8")
(INTEL / f"_ext_{DAY}.json").write_text(
    json.dumps(ext_out, ensure_ascii=False, indent=1), encoding="utf-8")

lines = [
    "# S1 情报补齐清单 · 2026-11-22（周日 18 场）",
    "",
    "> 生成：`📝文章/20261122/_工具/build_s1_data.py`；只使用竞彩官方 webapi 已落盘的真实数据。",
    "",
    "## 一、数据源与缺源事实",
    "",
    "| 项 | 状态 | 说明 |",
    "|:--|:--|:--|",
    "| 竞彩官方五套盘口 | 已取 18/18 场 | `_intel_20261122.json`，其中 003 / 006 只开让球、无胜平负 |",
    "| 官方近况 / 交锋 / 伤停 | 已取 | `state/matches/<matchId>/` 的 result / history / injury |",
    "| 联赛排名与天气 | 14/18 场 | `_leagues_20261122.json`，4 场缺源 |",
    "| 500 百家亚盘 / 欧赔 / 大小 | **未取到** | 54 个页面全部被 EdgeOne 拦截；`_x500.py gate` 需 playwright（本机未装） |",
    "| 外媒 / 预测市场 / 第三方 AI | **未取到** | 无可核对来源，按纪律留空，不编造 |",
    "| 战术层 / xG / 失球时间分布 | **未取到** | 项目既有数据缺口（见 open_items） |",
    "",
    "## 二、逐场覆盖",
    "",
    "| 场次 | 对阵 | 官方数据覆盖 |",
    "|:--|:--|:--|",
    *audit_lines,
    "",
    "## 三、口径声明",
    "",
    "- `_data_20261122.json` 的 `source` 明确标注「竞彩官方 webapi 近5场/交锋（500 缺源 fallback）」，与 20261119 批次既有做法一致；赛季主客分项留空，模型走 `data_lam` 的近况退化路径。",
    "- `_ext_20261122.json` 的利弊情报、体能、核心矛盾、胜负手均由官方数值生成；`ai_preds` 留空、`media` 明标未取到、`motivation` 不推断战意。",
    "- 未估算任何赔率、未补写外盘欧赔、未推断机构态度或资金流向；90 分钟常规时间口径。",
    "- 003 / 006 因官方无胜平负定价，无法建立市场三向基准，列入 D 级（证据不足跳过），不进 v3.2 报告逐场拆解。",
    "",
    "## 四、免责",
    "",
    "全部内容仅作数据观察与思路参考，不构成投注建议。",
]
(BASE / "S1情报补齐清单_20261122.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print("OK _data_ %d 场 / _ext_ %d 场 / S1 清单已写入" % (len(data_out), len(ext_out)))
