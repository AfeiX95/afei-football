#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""历史方向审计（P1）

扫描 📚知识库/赛后校验/*.md，把「逐场行」抽成结构化记录，并分三级标注可恢复程度：
  L1  有模型首选概率 + 赛果 → 可算方向命中，**仍不足以做概率回测**（缺三向、缺赛前时间戳）
  L2  只有方向✅/❌ + 赛果 → 只能做方向命中率
  L3  只有批次汇总数字 → 只能做总量交叉核对

输出：
  📚知识库/赛后校验/历史方向审计_<today>.md
  state/ledger/history_audit.json

python scripts/history_audit.py [--dir 📚知识库/赛后校验]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))

RE_ID = re.compile(r"^\**\s*((?:周[一二三四五六日])?\s*\d{3})")
RE_SCORE = re.compile(r"(\d+)\s*[:：]\s*(\d+)")
RE_PICK_PROB = re.compile(r"([主客平HD])\s*\**\s*(\d{2,3}(?:\.\d)?)")
RE_AGG = re.compile(r"(\d+)\s*/\s*(\d+)\s*=\s*\**\s*(\d+(?:\.\d+)?)%")
LEAGUES = {
    "英超": "英超", "英冠": "英冠", "西甲": "西甲", "意甲": "意甲", "德甲": "德甲", "德乙": "德乙",
    "法甲": "法甲", "荷甲": "荷甲", "葡超": "葡超", "苏超": "苏超", "瑞超": "瑞超", "瑞甲": "瑞甲",
    "挪超": "挪超", "芬超": "芬超", "丹超": "丹超", "波甲": "波甲", "奥甲": "奥甲", "俄超": "俄超",
    "日职": "日职", "日乙": "日乙", "韩K": "韩K", "澳超": "澳超", "美职": "美职", "巴甲": "巴甲",
    "阿甲": "阿甲", "欧冠": "欧冠", "欧罗巴": "欧罗巴", "亚冠": "亚冠", "意乙": "意乙", "法乙": "法乙",
    "西乙": "西乙", "英甲": "英甲", "捷甲": "捷甲", "瑞士超": "瑞士超", "比甲": "比甲", "土超": "土超",
}


def pick_outcome(h: int, a: int) -> str:
    return "主" if h > a else ("客" if h < a else "平")


def parse_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    rows = []
    header: list[str] = []
    for ln in text.splitlines():
        if not ln.startswith("|") or ln.count("|") < 4:
            continue
        _cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if header == [] and any(k in ln for k in ("场次", "比分", "赛果")):
            header = _cells
            continue
        if re.match(r"^\|[\s:\-|]+\|?\s*$", ln):
            continue
        skip_idx = {i for i, h in enumerate(header) if any(k in h for k in ("半", "让", "大小", "盘口"))}
        if re.match(r"^\|[\s:\-|]+\|?\s*$", ln):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        mid_m = RE_ID.match(cells[0])
        if not mid_m:
            continue
        sc = None
        for i, c in enumerate(cells):
            if i in skip_idx:
                continue  # 表头标了半场/让球/大小的列不是全场比分
            m = RE_SCORE.search(c)
            if m and not sc:
                sc = (int(m.group(1)), int(m.group(2)))
        if not sc:
            continue
        mid = re.sub(r"\s+", "", mid_m.group(1))
        league = next((v for k, v in LEAGUES.items() if k in ln), None)
        pick, prob, hit = None, None, None
        for c in cells:
            m = RE_PICK_PROB.search(c)
            if m and pick is None and "比分" not in c:
                pick, prob = m.group(1), float(m.group(2))
            if hit is None and ("✅" in c or "❌" in c) and len(c) <= 4:
                hit = "✅" in c
        rows.append({
            "file": path.name, "match_id": mid, "league": league,
            "score_90": sc, "outcome": pick_outcome(*sc),
            "model_pick": pick, "model_prob": prob, "hit": hit,
        })
    agg = [{"hits": int(a), "n": int(b), "rate": float(c)} for a, b, c in RE_AGG.findall(text)]
    return {"file": path.name, "rows": rows, "aggregates": agg, "has_timestamp": bool(re.search(r"2026-\d{2}-\d{2}", text))}


def grade(r: dict) -> str:
    if r["model_prob"] is not None and r["hit"] is not None:
        return "L1"
    if r["model_pick"] is not None and r["hit"] is not None:
        return "L2"
    if r["hit"] is not None:
        return "L2"
    return "L3"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "📚知识库" / "赛后校验"))
    args = ap.parse_args(argv)

    files = [p for p in sorted(Path(args.dir).glob("*.md")) if not p.name.startswith("历史方向审计_")]
    parsed, rows = [], []
    for p in files:
        d = parse_file(p)
        d["rows"] = [{**r, "level": grade(r)} for r in d["rows"]]
        parsed.append({"file": d["file"], "rows": len(d["rows"]), "agg": len(d["aggregates"]), "ts": d["has_timestamp"]})
        rows += d["rows"]

    # 去重：同场次+同比分视为同一场（多份文件重复引用）
    seen, uniq = set(), []
    for r in rows:
        k = (r["match_id"], tuple(r["score_90"]))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    raw_n, rows = len(rows), uniq

    def rate(sel):
        h = sum(1 for r in sel if r["hit"])
        return h, len(sel), (h / len(sel) * 100 if sel else 0.0)

    by_level: dict[str, list] = {}
    for r in rows:
        by_level.setdefault(r["level"], []).append(r)
    by_pick: dict[str, list] = {}
    for r in rows:
        by_pick.setdefault(str(r["model_pick"]), []).append(r)
    by_league: dict[str, list] = {}
    for r in rows:
        by_league.setdefault(str(r["league"] or "未标注"), []).append(r)

    hit_all = rate([r for r in rows if r["hit"] is not None])
    actual_home = sum(1 for r in rows if r["outcome"] == "主")
    actual_draw = sum(1 for r in rows if r["outcome"] == "平")
    picked = [r for r in rows if r["model_pick"] is not None]
    pick_home = sum(1 for r in picked if r["model_pick"] in ("主", "H"))

    L = []
    L.append("# 历史方向审计（474 场口径交叉核对）\n")
    L.append(f"- 生成：{datetime.now(TZ).isoformat(timespec='minutes')}　脚本：`scripts/history_audit.py`")
    L.append(f"- 扫描：{len(files)} 个文件，抽出逐场行 {raw_n} 条，去重后 **{len(rows)} 条**")
    L.append("- 口径：只认「表格里有场次编号 + 90 分钟全场比分」的行（半场/让球/大小列跳过）；同场次+同比分视为同一场去重")
    L.append("\n## 一、可恢复程度分级\n")
    L.append("| 级别 | 含义 | 条数 | 能否用于 |")
    L.append("|---|---|--:|---|")
    L.append(f"| L1 | 有模型首选概率 + 赛果 | {len(by_level.get('L1', []))} | 方向命中率；**不足以做概率回测**（缺三向/缺赛前时间戳） |")
    L.append(f"| L2 | 只有 ✅/❌ + 赛果 | {len(by_level.get('L2', []))} | 方向命中率 |")
    L.append(f"| L3 | 无判定 | {len(by_level.get('L3', []))} | 仅核对 |")
    L.append(f"\n- 有模型 picks、可算方向命中：**{hit_all[0]}/{hit_all[1]} = {hit_all[2]:.1f}%**")
    L.append(f"- 其中实际主胜 {actual_home} 场、平局 {actual_draw} 场；模型选主 {pick_home} 场"
             f"（在有预测侧的 {len(picked)} 场里占 {pick_home/max(1,len(picked))*100:.0f}%）→ 检查是否存在系统性偏主")

    L.append("\n## 二、按预测类别\n")
    L.append("| 预测 | 命中 | 样本 | 命中率 |")
    L.append("|---|--:|--:|--:|")
    for k, sel in sorted(by_pick.items()):
        h, n, rt = rate(sel)
        L.append(f"| {k} | {h} | {n} | {rt:.1f}% |")

    L.append("\n## 三、按联赛（仅统计被识别到联赛名的行）\n")
    L.append("| 联赛 | 命中 | 样本 | 命中率 |")
    L.append("|---|--:|--:|--:|")
    for k, sel in sorted(by_league.items(), key=lambda kv: -len(kv[1])):
        h, n, rt = rate(sel)
        if k == "未标注" and n < 5:
            continue
        L.append(f"| {k} | {h} | {n} | {rt:.1f}% |")

    L.append("\n## 四、每份文件的抽取情况\n")
    L.append("| 文件 | 逐场行 | 汇总数字 | 含日期 |")
    L.append("|---|--:|--:|:-:|")
    for d in sorted(parsed, key=lambda x: -x["rows"]):
        L.append(f"| {d['file']} | {d['rows']} | {d['agg']} | {'是' if d['ts'] else '否'} |")

    L.append("\n## 五、结论与边界（必须一起读）\n")
    L.append("1. 这份审计只回答「历史上的方向判定有没有被系统性记录错了」，**不回答 A 是否优于市场**。")
    L.append("2. 历史记录普遍缺：赛前三向概率、赛前时间戳、市场同场基线 → 不能进概率回测，也不能计算 Brier/LogLoss。")
    L.append("3. 方向命中率混着「可站/不站/难度分层」不同口径，不能直接跨批相加；本表的百分比只做交叉核对。")
    L.append("4. 若要检验 Alpha，唯一合法路径是 ledger 里赛前冻结的记录（见 `docs/LEDGER.md`）。")

    out_md = Path(args.dir) / f"历史方向审计_{datetime.now(TZ):%Y%m%d}.md"
    out_md.write_text("\n".join(L), encoding="utf-8", newline="\n")
    js = ROOT / "state" / "ledger" / "history_audit.json"
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(json.dumps({"generated": datetime.now(TZ).isoformat(timespec="seconds"),
                              "files": parsed, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("\n".join(L[:40]))
    print(f"\n…已写入 {out_md} 与 {js}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
