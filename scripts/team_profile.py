# -*- coding: utf-8 -*-
"""球队底档：排名 / 身价 / 伤停（2026-10-20 建）

为什么要它
- 模型只吃「近 10 场进失 + 同主客战绩 + 交锋 + 伤停人数」，**不吃阵容档次**；
  13 场里皇马 vs 莱红牛、拜仁 vs 阿森纳这种「数据接近但档次差一档」的场，
  只靠小样本会被带偏（周三011 就是典型：模型把 LASK 抬成同档）。
- 所以单列一层底档：**排名 + 身价 + 伤停**，写报告和做卡片时作为独立因素引用，
  **不参与 λ 计算**（不再引入一个不可控参数）。

数据来源（2026-10-20 实测）
- 身价：懂球帝「数据」页的**球队身价表** ——
  `https://pc.dongqiudi.com/data?cid=<联赛id>&tab=team&type=market_value&expanded=1`
  （整张联赛表一次抓完，比逐队抓球队页稳：球队页的「球队信息」模块时有时无）
- 排名：`_leagues_<date>.json`（竞彩网积分榜，欧冠场次是联赛阶段排名）
- 伤停：`state/matches/<id>/injury.json`（空列表＝数据源没给，不是「无伤病」）

用法
    python -X utf8 scripts/team_profile.py --date 20261021 --discover   # 扫联赛 id + 建身价表
    python -X utf8 scripts/team_profile.py --date 20261021              # 13 场底档
    python -X utf8 scripts/team_profile.py --date 20261021 --only 周三007 周三010
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import ds_search  # noqa: E402

STATE = ROOT / "state"
TABLES = STATE / "cache" / "_dq_tables.json"     # {cid: {"_fetched": ts, "_items": {队名: 百万欧}}}
CIDMAP = STATE / "cache" / "_dq_cid.json"        # {联赛名: cid}

# 竞彩简称 → 懂球帝正式队名（逐个试出来的）
ALIAS = {
    "东京FC": "FC东京", "神户胜利": "神户胜利船", "莱红牛": "RB莱比锡", "皇马": "皇家马德里",
    "里斯本": "葡萄牙体育", "贝蒂斯": "皇家贝蒂斯", "毕尔巴鄂": "毕尔巴鄂竞技",
    "帕梅拉斯": "帕尔梅拉斯", "弗鲁米嫩": "弗鲁米嫩塞", "维拉": "阿斯顿维拉",
    "加拉塔萨": "加拉塔萨雷", "LASK林茨": "林茨", "大宫松鼠": "RB大宫松鼠",
    "拜仁": "拜仁慕尼黑",
    # 2026-10-22 周四（欧罗巴/解放者杯）补：竞彩缩写 → 懂球帝全名
    "格风暴": "格拉茨风暴", "萨迪纳摩": "萨格勒布迪纳摩", "克里特": "OFI克里特",
    "波兹南": "莱赫波兹南", "贝西克塔": "贝西克塔斯", "利勒斯特": "利勒斯特罗姆",
    "拉普大学": "拉普拉塔大学生", "弗拉门戈": "弗拉门戈",
}


def jload(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default if default is not None else {}


def jsave(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def clean(s: str) -> str:
    """懂球帝 markdown 里满屏反斜杠转义，先全删掉。"""
    return s.replace("\\", "").strip()


def to_million(num: str, unit: str) -> float | None:
    try:
        v = float(num)
    except ValueError:
        return None
    if unit == "万":
        return v / 100.0      # 万欧 → 百万欧
    if unit == "亿":
        return v * 100.0      # 亿欧 → 百万欧
    return None


def parse_value_table(content: str) -> dict:
    """懂球帝身价表 → {队名: 百万欧}。行长这样：`1 \\|  皇家马德里 \\| 15亿`"""
    out: dict = {}
    for line in (content or "").splitlines():
        s = clean(line)
        if not s or not s[0].isdigit():
            continue
        parts = [p.strip() for p in s.split("|")]
        if len(parts) < 3:
            continue
        name, val = parts[1], parts[2]
        import re as _re
        m = _re.match(r"^([\d.]+)\s*(万|亿)?$", val)
        if not m or not name:
            continue
        v = to_million(m.group(1), m.group(2) or "")
        if v:
            out[name] = v
    return out


def value_url(cid) -> str:
    return f"https://pc.dongqiudi.com/data?cid={cid}&tab=team&type=market_value&expanded=1"


def load_tables() -> dict:
    return jload(TABLES, {}) or {}


def fetch_table(cid, refresh: bool = False) -> dict:
    tables = load_tables()
    key = str(cid)
    if not refresh and tables.get(key) and tables[key].get("_items"):
        return tables[key]["_items"]
    try:
        content = ds_search.fetch(value_url(cid)).get("content") or ""
    except SystemExit:
        return {}
    items = parse_value_table(content)
    if items:
        tables[key] = {"_fetched": dt.datetime.now().isoformat(timespec="seconds"), "_items": items}
        jsave(TABLES, tables)
    return items


def discover(max_cid: int = 40) -> dict:
    """扫 cid 1..N，把每张能解析出球队身价的表都存下，供按队名查。"""
    cidmap = jload(CIDMAP, {}) or {}
    markers = [("西甲", "皇家马德里"), ("英超", "阿森纳"), ("日职", "川崎前锋"),
               ("解放者杯", "帕尔梅拉斯"), ("意甲", "国际米兰"), ("法甲", "巴黎圣日耳曼"),
               ("德甲", "拜仁慕尼黑"), ("荷甲", "费耶诺德"), ("葡超", "葡萄牙体育"),
               ("比甲", "布鲁日"), ("土超", "加拉塔萨雷"), ("奥甲", "林茨"),
               ("挪超", "维京"), ("欧冠", "顿涅茨克矿工")]
    for cid in range(1, max_cid + 1):
        items = fetch_table(cid)
        if not items:
            continue
        names = list(items)
        for lg, marker in markers:
            if lg in cidmap:
                continue
            if any(marker in n for n in names):
                cidmap[lg] = cid
        time.sleep(0.2)
    jsave(CIDMAP, cidmap)
    print("联赛 cid：", json.dumps(cidmap, ensure_ascii=False))
    print("身价表：", {k: len(v.get("_items") or {}) for k, v in load_tables().items()})
    return cidmap


def lookup_value(name: str) -> tuple:
    """在已抓到的各联赛身价表里按队名找。返回（百万欧, 命中的懂球帝队名）。"""
    key = ALIAS.get(name, name)
    for cid, blob in load_tables().items():
        items = blob.get("_items") or {}
        if key in items:
            return items[key], key
        for k, v in items.items():
            if key and (key in k or k in key):
                return v, k
    return None, None


def fmt_value(v) -> str:
    """百万欧 → 中文口径：1B = 10 亿欧，所以 亿欧 = v/100。"""
    if not v:
        return "—"
    return f"{v/100:.2f} 亿欧" if v >= 100 else f"{v:.0f}M 欧"


def ratio(h, a) -> str:
    if not h or not a:
        return "—"
    hi, lo = max(h, a), min(h, a)
    return f"{hi/lo:.2f} 倍" if lo else "—"


def standings_index(lg: dict) -> dict:
    """`_leagues_<date>.json` 里 home_rank/away_rank 是整行积分榜 dict（pos/pld/w/d/l/pts）。"""
    idx: dict = {}
    ms = lg.get("matches") or {}
    for m in (ms.values() if isinstance(ms, dict) else []):
        for side in ("home", "away"):
            name, row = m.get(side), m.get(f"{side}_rank")
            if name and isinstance(row, dict) and str(row.get("pos") or "").strip():
                idx[name] = row
    return idx


def rank_text(row) -> str:
    if not row:
        return "—"
    pos = str(row.get("pos") or "").strip()
    if not pos:
        return "—"
    pld, w, d, l, pts = (row.get(k) for k in ("pld", "w", "d", "l", "pts"))
    return f"第 {pos} · {pld} 场 {w}胜{d}平{l}负 {pts} 分"


def dq_standings(lg_name: str = "欧冠") -> dict:
    """懂球帝积分榜（`_dq_stand_<联赛>.json`，由 discover/refresh 落地）：{队名: 行}"""
    return jload(STATE / "cache" / f"_dq_stand_{lg_name}.json", {}) or {}


STAND_CIDS = {"欧冠": 6, "欧罗巴": 14, "巴甲": 19}
STAND_NAMES = {"欧冠": "欧冠", "欧罗巴": "欧罗巴"}


def parse_stand(content: str) -> dict:
    """把懂球帝「数据」页的积分榜解析成 {队名: 行}。

    两种版面都见过：`| 1 | 尤文图斯 | 2 | ... |`（反斜杠转义）和整段换行平铺
    （`1
尤文图斯
2
2
0
0
7\/1
+6
6`）——先洗反斜杠，再按有无 `|` 分派。
    """
    text = (content or "").replace("\\", "")
    out: dict = {}
    if "|" in text:
        for line in text.splitlines():
            line = line.strip()
            if "|" not in line:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            cells = [c for c in cells if c not in ("", "-")]
            if len(cells) < 8 or not cells[0].isdigit():
                continue
            row = _row_from_cells(cells)
            if row:
                out.setdefault(row[0], row[1])
        if out:
            return out
    toks = [t.strip() for t in text.splitlines() if t.strip()]
    try:
        i = toks.index("积分") + 1
    except ValueError:
        return out
    while i + 8 < len(toks):
        if not toks[i].isdigit():
            i += 1
            continue
        cells = [toks[i], toks[i + 1], toks[i + 2], toks[i + 3], toks[i + 4],
                 toks[i + 5], toks[i + 6], toks[i + 8]]
        row = _row_from_cells(cells)
        if not row:
            break
        out.setdefault(row[0], row[1])
        i += 9
    return out


def _row_from_cells(cells: list):
    try:
        pos = int(cells[0]); team = cells[1]
        pld, w, d, l = (int(cells[2]), int(cells[3]), int(cells[4]), int(cells[5]))
        gf, ga = (int(x) for x in cells[6].replace("／", "/").split("/"))
        pts = int(cells[-1])
    except (ValueError, IndexError):
        return None
    if not team:
        return None
    return team, {"pos": pos, "pld": pld, "w": w, "d": d, "l": l,
                  "gf": gf, "ga": ga, "pts": pts}


def ensure_standings(name: str = "欧罗巴", refresh: bool = False) -> dict:
    """按需抓一张懂球帝积分榜并落 `_dq_stand_<name>.json`（缓存 6 小时）。"""
    path = STATE / "cache" / f"_dq_stand_{name}.json"
    if not refresh and path.exists():
        blob = jload(path, {}) or {}
        if blob and (dt.datetime.now().timestamp() - float(blob.get("_fetched") or 0)) < 6 * 3600:
            return blob.get("items") or {}
    cid = STAND_CIDS.get(name)
    if not cid:
        return {}
    try:
        content = ds_search.fetch(f"https://pc.dongqiudi.com/data?cid={cid}").get("content") or ""
    except SystemExit:
        return {}
    items = parse_stand(content)
    if items:
        jsave(path, {"_fetched": dt.datetime.now().timestamp(), "cid": cid, "items": items})
    return items


def dq_rank(team: str, cache: dict) -> dict | None:
    """竞彩网榜没覆盖时（欧冠/日职多如此），退到懂球帝积分榜，按别名对齐。"""
    key = ALIAS.get(team, team)
    if key in cache:
        return cache[key]
    for k, v in cache.items():
        if key and (key in k or k in key):
            return v
    return None


INJ_WORDS = ("伤", "缺阵", "缺战", "停赛", "报销", "伤退", "受伤", "十字韧带", "肌腱", "红牌停")


def injury_news(date_tag: str) -> dict:
    """从已抓的外媒情报里捞伤停线索：{场次号: [句子]}。

    竞彩网 injury.json 对欧冠/日职基本是空名单（缺源），但媒体稿里常有
    「某队后防三人同时缺阵」这类定性信息 —— 这是本仓库唯一现成的伤停文字源。
    """
    blob = jload(STATE / "intel" / date_tag / f"_media_{date_tag}.json", {}) or {}
    out: dict = {}
    for it in (blob.get("items") or []):
        hits: list[str] = []
        for src in (it.get("sources") or []):
            text = " ".join(str(src.get(k) or "") for k in ("title", "summary", "fetch_head"))
            for sent in text.replace("！", "。").replace("?", "。").split("。"):
                sent = sent.strip()
                if sent and any(w in sent for w in INJ_WORDS) and len(sent) <= 90:
                    if sent not in hits:
                        hits.append(sent)
        if hits:
            out[it.get("no")] = hits[:3]
    return out


def injuries(match_id: str) -> dict:
    v = (jload(STATE / "matches" / str(match_id) / "injury.json", {}) or {}).get("value") or {}
    out = {}
    for side in ("home", "away"):
        lst = ((v.get(side) or {}).get("injuriesAndSuspensionsList") or [])
        names = [x.get("playerName") or x.get("name") for x in lst]
        out[side] = {"n": len(lst), "names": [n for n in names if n][:5]}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="球队底档：排名 / 身价 / 伤停")
    ap.add_argument("--date", required=True)
    ap.add_argument("--only", nargs="*", default=None, help="只跑这些场次号，如 周三007")
    ap.add_argument("--discover", action="store_true", help="扫懂球帝联赛 id 并建身价表")
    ap.add_argument("--max-cid", type=int, default=40)
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()

    if a.discover:
        discover(a.max_cid)

    ms = jload(STATE / "batch" / f"_matches_{a.date}.json", {}) or {}
    if not ms:
        raise SystemExit(f"没有 state/batch/_matches_{a.date}.json —— 先跑 model_autofill.py --date {a.date}")
    lg = jload(STATE / "intel" / a.date / f"_leagues_{a.date}.json", {}) or {}
    st = standings_index(lg)
    # 日职/日乙与欧冠的身价表不在 1..40 里，按需补抓；排名退到懂球帝积分榜
    for cid in (509, 510):
        if not load_tables().get(str(cid), {}).get("_items"):
            fetch_table(cid)
    dqst = dict(dq_standings("欧冠"))
    for _nm in ("欧罗巴", "巴甲"):
        dqst.update(ensure_standings(_nm))
    news = injury_news(a.date)

    items = []
    for mid, m in sorted(ms.items(), key=lambda kv: kv[1].get("no", "")):
        if a.only and m.get("no") not in a.only:
            continue
        rows = {}
        for side, team in (("home", m.get("home")), ("away", m.get("away"))):
            val, dq_name = lookup_value(team)
            rank = st.get(team) or dq_rank(team, dqst)
            inj = injuries(mid)[side]
            rows[side] = {"team": team, "dq_name": dq_name, "value_m": val, "value_text": fmt_value(val),
                          "rank": (rank.get("pos") if rank else None), "rank_text": rank_text(rank),
                          "inj_n": inj["n"], "inj_names": inj["names"]}
        items.append({"mid": mid, "no": m.get("no"), "league": m.get("league"),
                      "home": m.get("home"), "away": m.get("away"),
                      "injury_news": news.get(m.get("no")) or [],
                      "home_prof": rows["home"], "away_prof": rows["away"],
                      "value_ratio": ratio(rows["home"]["value_m"], rows["away"]["value_m"])})

    out_json = STATE / "intel" / a.date / f"_team_{a.date}.json"
    jsave(out_json, {"date": a.date, "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
                     "items": items})

    L = [f"# 球队底档 · 排名 / 身价 / 伤停（{a.date}）", "",
         "> 身价取懂球帝「数据」页的球队身价表（整张联赛表一次抓，不是逐队估算）；排名取竞彩网积分榜；",
         "> 伤停取官方登记（空＝数据源没给，不是「无伤病」）。**这一层不参与 λ 计算，只作定性因素。**", "",
         "| 场次 | 对阵 | 主队排名 | 主队身价 | 客队排名 | 客队身价 | 身价比 | 伤停（主/客） |",
         "|---|---|---|---|---|---|---|---|"]
    for it in items:
        h, w = it["home_prof"], it["away_prof"]
        L.append("| {no} | {h} vs {a} | {hr} | {hv} | {ar} | {av} | {rt} | {ih}/{iw} |".format(
            no=it["no"], h=it["home"], a=it["away"], hr=h["rank_text"], hv=h["value_text"],
            ar=w["rank_text"], av=w["value_text"], rt=it["value_ratio"],
            ih=(h["inj_n"] or "—"), iw=(w["inj_n"] or "—")))
    L += ["", "## 逐场补充", ""]
    for it in items:
        h, w = it["home_prof"], it["away_prof"]
        L.append(f"### {it['no']} {it['league']} {it['home']} vs {it['away']}")
        L.append(f"- 身价：{it['home']} {h['value_text']} vs {it['away']} {w['value_text']}（{it['value_ratio']}）")
        L.append(f"- 排名：{it['home']} {h['rank_text']}｜{it['away']} {w['rank_text']}")
        if h["inj_n"] or w["inj_n"]:
            L.append(f"- 伤停：{it['home']} {h['inj_n']} 人{'（' + '、'.join(h['inj_names']) + '）' if h['inj_names'] else ''}"
                     f"｜{it['away']} {w['inj_n']} 人{'（' + '、'.join(w['inj_names']) + '）' if w['inj_names'] else ''}")
        elif it.get("injury_news"):
            L.append("- 伤停：官方名单为空，媒体线索（需核原文）：" + "；".join(it["injury_news"][:2]))
        else:
            L.append("- 伤停：官方名单为空、媒体也没提（缺源，不做推断）")
        L.append("")
    out_md = out_json.with_suffix(".md")
    out_md.write_text("\n".join(L), encoding="utf-8")

    got = sum(1 for it in items if it["home_prof"]["value_m"] and it["away_prof"]["value_m"])
    print(f"✅ {out_json}\n✅ {out_md}")
    print(f"   场次 {len(items)} · 两队身价都取到 {got} 场")


if __name__ == "__main__":
    main()
