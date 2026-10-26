#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AFEI Predictions Ledger v1（P0）

赛前预测不可变账本：一次写入、失败即拒、逐条哈希；结果单独追加。

存储（state/ledger/）：
  predictions/<YYYYMMDD>.jsonl   每行一条赛前记录（含 record_sha256）
  results/<YYYYMMDD>.jsonl       每行一条赛后结果（含 record_sha256）
  stance/<YYYYMMDD>.json         （可选）人工决策层：{"005": {"stance": "顺定价", "abstained": false}}

命令：
  python scripts/ledger.py append --day 20261027 [--retrospective] [--dry-run]
  python scripts/ledger.py add-result --day 20261027 --json results.json [--retrospective]
  python scripts/ledger.py verify
  python scripts/ledger.py status

规则（写死在代码里，测试覆盖）：
  1. 同一 match_id 已存在时拒绝再写（不可静默覆盖）
  2. 缺 record_sha256 或哈希不符 → verify 失败
  3. prediction_timestamp 晚于 kickoff → 记录标记 post_kickoff=true（不进样本外检验）
  4. --retrospective 的记录一律 retrospective=true，不得冒充赛前冻结
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = Path(os.environ.get("AFEI_LEDGER_ROOT") or (ROOT / "state" / "ledger"))
TZ = timezone(timedelta(hours=8))
MODELS = ("A", "M", "F")


# ---------------------------------------------------------------- 基础工具
def _canon(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(obj: dict) -> str:
    body = {k: v for k, v in obj.items() if k != "record_sha256"}
    return hashlib.sha256(_canon(body).encode("utf-8")).hexdigest()


def pred_path(day: str) -> Path:
    return LEDGER / "predictions" / f"{day}.jsonl"


def res_path(day: str) -> Path:
    return LEDGER / "results" / f"{day}.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            out.append(json.loads(ln))
    return out


def _append(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(_canon(rec) + "\n")


def _iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts if ts is not None else datetime.now(TZ).timestamp(), TZ).isoformat(timespec="seconds")


# ---------------------------------------------------------------- 组装记录
def _load(day: str, name: str) -> dict:
    p = ROOT / "state" / "intel" / day / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _kickoff(day: str, mkt: dict) -> tuple[str | None, float | None]:
    raw = (mkt or {}).get("kickoff")  # "10-27 18:00"
    if not raw:
        return None, None
    try:
        mmdd, hm = raw.split()
        m, d = mmdd.split("-")
        dt = datetime.strptime(f"{day[:4]}-{m}-{d} {hm}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        return dt.isoformat(timespec="seconds"), dt.timestamp()
    except Exception:
        return None, None


def build_records(day: str, retrospective: bool = False) -> list[dict]:
    model = _load(day, f"_model_v3_{day}.json") or _load(day, f"_model_{day}.json")
    market = _load(day, f"_market_{day}.json")
    stance = {}
    sp = LEDGER / "stance" / f"{day}.json"
    if sp.exists():
        stance = json.loads(sp.read_text(encoding="utf-8"))
    mt = (ROOT / "state" / "intel" / day / f"_model_v3_{day}.json")
    art_mtime = mt.stat().st_mtime if mt.exists() else None

    recs = []
    for key, mv in model.items():
        if not isinstance(mv, dict):
            continue
        mid = key if not key.isdigit() else key
        mkt = market.get(key) or {}
        ko_iso, ko_ts = _kickoff(day, mkt)
        pred_ts = _iso(art_mtime) if art_mtime else _iso()
        probs = {m: mv.get({"A": "three_data", "M": "three_market", "F": "three_fused"}[m]) for m in MODELS}
        lams = {m: mv.get({"A": "lam_data", "M": "lam_market_joint", "F": "lam_fused"}[m]) for m in MODELS}
        miss = []
        if any(v is None for v in probs.values()):
            miss.append("probs")
        if not ko_iso:
            miss.append("kickoff")
        if not mkt.get("ox_close"):
            miss.append("odds")
        st = stance.get(key) or {}
        rec = {
            "schema": "afei-ledger-v1",
            "kind": "prediction",
            "match_id": f"{day}-{key}",
            "day": day,
            "source_id": (mkt or {}).get("id"),
            "league": (mkt or {}).get("league"),
            "match": (mkt or {}).get("match"),
            "home": (mkt or {}).get("home"),
            "away": (mkt or {}).get("away"),
            "kickoff": ko_iso,
            "prediction_timestamp": pred_ts,
            "ledger_written_at": _iso(),
            "model_version": mv.get("model_version"),
            "data_snapshot_id": mv.get("data_snapshot"),
            "probs": probs,
            "lam": lams,
            "w_data": mv.get("w_data"),
            "n_eff": mv.get("n_eff"),
            "data_grade": mv.get("data_grade") or mv.get("grade"),
            "evidence_grade": mv.get("evidence_grade"),
            "odds": {
                "source": "500.com 15 家即时均值（去水见 _market）",
                "market_probs_close": (mkt or {}).get("prob_close"),
                "overround_close": (mkt or {}).get("overround_close"),
                "ah_line": (mkt or {}).get("ah_modal_close") or (mkt or {}).get("ah_modal_open"),
                "ou_line": (mkt or {}).get("ou_modal_close") or (mkt or {}).get("ou_modal_open"),
                "fetched_at": pred_ts,
            },
            "stance": st.get("stance"),
            "abstained": bool(st.get("abstained", False)),
            "retrospective": bool(retrospective),
            "post_kickoff": bool(ko_ts and (art_mtime or 0) > ko_ts),
            "missing_fields": miss,
            "flags": [],
        }
        if rec["abstained"]:
            rec["flags"].append("abstained")
        if not st:
            rec["flags"].append("stance_missing")
        rec["record_sha256"] = _hash(rec)
        recs.append(rec)
    return recs


# ---------------------------------------------------------------- 命令
def cmd_append(args) -> int:
    recs = build_records(args.day, args.retrospective)
    if not recs:
        print(f"无模型数据：state/intel/{args.day}/_model_v3_{args.day}.json")
        return 1
    path = pred_path(args.day)
    existing = {r["match_id"] for r in read_jsonl(path)}
    dup = [r["match_id"] for r in recs if r["match_id"] in existing]
    if dup:
        print(f"拒绝写入：{len(dup)} 条已存在（账本不可覆盖）→ {', '.join(dup[:5])}")
        return 2
    if args.dry_run:
        print(f"[dry-run] 将写入 {len(recs)} 条 → {path}")
        for r in recs[:3]:
            print(" ", _canon({k: r[k] for k in ("match_id", "probs", "w_data", "data_grade")})[:180])
        return 0
    for r in recs:
        _append(path, r)
    n_pk = sum(1 for r in recs if r["post_kickoff"])
    n_retro = sum(1 for r in recs if r["retrospective"])
    print(f"写入 {len(recs)} 条 → {path.relative_to(ROOT)}（post_kickoff={n_pk} retrospective={n_retro}）")
    return 0


def cmd_add_result(args) -> int:
    payload = json.loads(Path(args.json).read_text(encoding="utf-8")) if args.json != "-" else json.load(sys.stdin)
    path = res_path(args.day)
    existing = {r["match_id"] for r in read_jsonl(path)}
    n = 0
    for key, val in payload.items():
        mid = f"{args.day}-{key}"
        if mid in existing:
            print(f"拒绝：{mid} 结果已存在")
            return 2
        score = val.get("score") if isinstance(val, dict) else str(val)
        ht = val.get("ht") if isinstance(val, dict) else None
        try:
            h, a = [int(x) for x in str(score).replace("：", ":").split(":")]
        except Exception:
            print(f"比分无法解析：{mid} → {score}")
            return 1
        rec = {
            "schema": "afei-ledger-v1",
            "kind": "result",
            "match_id": mid,
            "day": args.day,
            "score_90": [h, a],
            "score_ht": ht,
            "outcome": "H" if h > a else ("A" if h < a else "D"),
            "source": args.source,
            "retrospective": bool(args.retrospective),
            "ingested_at": _iso(),
        }
        rec["record_sha256"] = _hash(rec)
        _append(path, rec)
        n += 1
    print(f"追加结果 {n} 条 → {path.relative_to(ROOT)}")
    return 0


def cmd_verify(args) -> int:
    bad = 0
    files = sorted((LEDGER / "predictions").glob("*.jsonl")) + sorted((LEDGER / "results").glob("*.jsonl"))
    if not files:
        print("账本为空。")
        return 0
    for p in files:
        seen, prev_ok = set(), True
        for i, rec in enumerate(read_jsonl(p), 1):
            mid = rec.get("match_id")
            if rec.get("record_sha256") != _hash(rec):
                print(f"哈希不符 {p.name}:{i} {mid}")
                bad += 1
            if mid in seen:
                print(f"重复 match_id {p.name}:{i} {mid}")
                bad += 1
            seen.add(mid)
        print(f"{p.relative_to(LEDGER)}：{len(seen)} 条，{p.stat().st_size} 字节")
    print("校验通过" if bad == 0 else f"校验失败：{bad} 处问题")
    return 0 if bad == 0 else 1


def cmd_status(args) -> int:
    pdir, rdir = LEDGER / "predictions", LEDGER / "results"
    tot = res = retro = post = abst = 0
    for p in sorted(pdir.glob("*.jsonl")):
        recs = read_jsonl(p)
        r = read_jsonl(rdir / f"{p.stem}.jsonl")
        tot += len(recs)
        res += len({x["match_id"] for x in r})
        retro += sum(1 for x in recs if x.get("retrospective"))
        post += sum(1 for x in recs if x.get("post_kickoff"))
        abst += sum(1 for x in recs if x.get("abstained"))
        print(f"{p.stem}: 预测 {len(recs):>3} 条，结果 {len(r):>3} 条")
    print(f"合计：预测 {tot} 条（retrospective {retro} / post_kickoff {post} / 弃权 {abst}），结果 {res} 条")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="AFEI Predictions Ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("append") ; a.add_argument("--day", required=True) ; a.add_argument("--retrospective", action="store_true") ; a.add_argument("--dry-run", action="store_true")
    r = sub.add_parser("add-result") ; r.add_argument("--day", required=True) ; r.add_argument("--json", required=True) ; r.add_argument("--source", default="竞彩官网赛果开奖") ; r.add_argument("--retrospective", action="store_true")
    sub.add_parser("verify")
    sub.add_parser("status")

    args = ap.parse_args(argv)
    return {"append": cmd_append, "add-result": cmd_add_result, "verify": cmd_verify, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
