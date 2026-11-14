# -*- coding: utf-8 -*-
"""从 500.com 抽取代表公司的 亚盘 / 欧赔 / 大小 初盘与即时（并发抓取 + 本地解析）

用法：
    python -X utf8 scripts/books_500.py --date 20261028 [--workers 8]

设计（2026-11-07 提速版）：
  1. 先用 live.500.com 带日期页做队名匹配，得到 {场次: 500 mid}，并落 state/tmp/_ids_<day>.json
  2. 把 24 场 × 3 类页面（yazhi/daxiao/ouzhi）**一次性并发抓取**，缺缓存才发请求
  3. 全部落本地缓存后再解析（解析纯 CPU，毫秒级）
  单页失败只丢那一场的那一类表，不阻塞整批。
输出: state/intel/<date>/_books_<date>.json
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _x500  # noqa: E402  500 反爬会话（票据 state/tmp/500session.json，30 天有效）
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "state" / "tmp" / "500cache"
CACHE.mkdir(parents=True, exist_ok=True)
KINDS = ("yazhi", "daxiao", "ouzhi")


def get(url: str, enc: str = "gb18030") -> str:
    return _x500.fetch(url, enc=enc)


def build_ids(day: str) -> dict:
    """用 500 带日期赛程页的 tr(编号/id/gy) 与当日 _intel 的队名做最佳匹配
    返回 {场次三位: (id, "联赛 主 vs 客", "MM-DD HH:MM")}"""
    import difflib

    # index.php 只回当前在售的十余场，跨零点/次日盘直接取不到，必须带日期
    html = get("https://live.500.com/?e=%s-%s-%s" % (day[:4], day[4:6], day[6:]))
    rows = re.findall(r'<tr id="a(\d+)"[^>]*gy="([^"]*)"[^>]*>([\s\S]*?)</tr>', html)
    intel = json.loads((ROOT / "state" / "intel" / day / ("_intel_%s.json" % day)).read_text(encoding="utf-8"))
    want = [(m.get("no", "")[-3:], m.get("home") or "", m.get("away") or "",
             m.get("league") or "") for m in intel.get("matches") or []]
    out, taken = {}, set()
    for no3, home, away, league in want:
        best, best_score = None, 0.0
        for mid, gy, tr in rows:
            if mid in taken:
                continue
            parts = [x for x in gy.split(",") if x.strip()]
            if len(parts) < 3:
                continue
            _lg, h, a = parts[0], parts[1], parts[2]
            s = max(difflib.SequenceMatcher(None, home, h).ratio(),
                    difflib.SequenceMatcher(None, away, a).ratio())
            s += 0.05 if (league and (league[:2] in _lg or _lg[:2] in league)) else 0
            if s > best_score:
                best, best_score = (mid, gy, tr), s
        if best and best_score >= 0.6:
            mid, gy, tr = best
            taken.add(mid)
            tm = re.search(r'>(\d{2}-\d{2} \d{2}:\d{2})<', tr)
            parts = [x for x in gy.split(",") if x.strip()]
            out[no3] = (mid, "%s %s vs %s" % (parts[0], parts[1], parts[2]),
                        tm.group(1) if tm else "")
            print("  %s → %s %s (score %.2f)" % (no3, mid, parts[1], best_score))
        else:
            print("  !! %s 未匹配到 500 id" % no3)
    return out


def lt(v):
    if v is None:
        return "-"
    if abs(v) < 0.01:
        return "平手"
    side = "主让" if v < 0 else "主受让"
    N = {0.25: "平/半", 0.5: "半球", 0.75: "半/一", 1.0: "一球", 1.25: "一/球半", 1.5: "球半",
         1.75: "球半/两", 2.0: "两球", 2.25: "两/两球半", 2.5: "两球半", 2.75: "两球半/三", 3.0: "三球"}
    return "%s %s" % (side, N.get(round(abs(v), 2), "%.2f" % abs(v)))


def canon(name, country=""):
    n, c = name, country or ""
    if "门" in n or "澳门" in c:
        return "澳彩"
    if "冠" in n:
        return "皇冠"
    if n.startswith("易"):
        return "易胜博"
    if n.startswith("B"):
        return "Bet365"
    if n.startswith("威"):
        return "威廉"
    if n.startswith("立"):
        return "立博"
    if n.startswith("伟"):
        return "伟德"
    if n.startswith("I"):
        return "Interwetten"
    return n


def cells(chunk):
    return re.findall(r"<td[^>]*>(.*?)</td>", chunk, re.S)


def num(s):
    m = re.search(r"[0-9]+\.[0-9]+", s or "")
    return float(m.group(0)) if m else None


def parse_handicap(t):
    """亚盘/大小表：逐公司取 初盘(td0-2) 与 即时(ping/ref/ying)"""
    out = {}
    for chunk in t.split('<tr class="tr1"')[1:]:
        nm = re.search(r'title="([^"]+)"', chunk)
        tabs = re.findall(r'class="pl_table_data">(.*?)</table>', chunk, re.S)
        if not (nm and len(tabs) >= 2):
            continue
        inst, init = tabs[0], tabs[1]
        ping = re.search(r'class="ping">([0-9.]+)', inst)
        ying = re.search(r'class="ying">([0-9.]+)', inst)
        rc = re.search(r'ref="([-0-9.]+)"', inst)
        ro = re.search(r'ref="([-0-9.]+)"', init)
        td = cells(init)
        if not (ping and ying and rc and ro and len(td) >= 3):
            continue
        h_o, a_o = num(td[0]), num(td[2])
        if h_o is None or a_o is None:
            continue
        out.setdefault(canon(nm.group(1)), {
            "raw": nm.group(1),
            "open": {"home": h_o, "line": float(ro.group(1)), "away": a_o},
            "close": {"home": float(ping.group(1)), "line": float(rc.group(1)), "away": float(ying.group(1))},
        })
    return out


def parse_1x2(t):
    """欧赔表：每公司取前两行（初盘/即时）"""
    out = {}
    for chunk in t.split('<tr class="tr1"')[1:]:
        nm = re.search(r'class="tb_plgs" title="([^"]+)"', chunk)
        cty = re.search(r'class="guojia"[^>]*>(.*?)</span>', chunk, re.S)
        tabs = re.findall(r'class="pl_table_data">(.*?)</table>', chunk, re.S)
        if not (nm and tabs):
            continue
        trs = re.findall(r"<tr[^>]*>(.*?)</tr>", tabs[0], re.S)
        trip = []
        for tr in trs[:2]:
            vals = [num(re.sub(r"<[^>]+>", "", x)) for x in cells(tr)]
            if len(vals) >= 3 and None not in vals[:3]:
                trip.append(vals[:3])
        if len(trip) < 2:
            continue
        out.setdefault(canon(nm.group(1), re.sub(r"<[^>]+>", "", cty.group(1)) if cty else ""),
                       {"raw": nm.group(1), "open": trip[0], "close": trip[1]})
    return out


def run(IDS, OUT, workers=8):
    ROW_ORDER = ["澳彩", "皇冠", "Bet365", "易胜博", "威廉", "立博", "伟德", "Interwetten"]

    def fp(kind, mid):
        return CACHE / ("%s_%s.html" % (kind, mid))

    def ok(p):
        return p.exists() and p.stat().st_size >= 5000

    # ① 缺缓存的页面多轮补抓（500 的同 IP 瞬时失败很常见，单轮会有 3 成缺口）
    tasks = [(k, mid) for (mid, _m, _ko) in IDS.values() for k in KINDS]
    pending = [(k, m) for k, m in tasks if not ok(fp(k, m))]
    miss0 = len(pending)
    rnd = 0
    while pending and rnd < 4:
        rnd += 1
        urls = ["https://odds.500.com/fenxi/%s-%s.shtml" % (k, m) for k, m in pending]
        got = _x500.fetch_many(urls, workers=workers, retries=1, sleep=0.05)
        bad = []
        for (k, m), u in zip(pending, urls):
            v = got.get(u)
            if isinstance(v, str) and len(v) >= 5000:
                fp(k, m).write_text(v, encoding="gb18030", errors="ignore")
            else:
                bad.append((k, m))
        print("  第 %d 轮：待抓 %d → 成功 %d，剩 %d" % (rnd, len(pending), len(pending) - len(bad), len(bad)))
        pending = bad
        if pending:
            time.sleep(0.5 * rnd)
    if miss0:
        print("  页面 %d 个（缺缓存 %d）→ 补齐后仍缺 %d%s"
              % (len(tasks), miss0, len(pending),
                 ("：" + ",".join("%s-%s" % (k, m) for k, m in pending[:8])) if pending else ""))
    else:
        print("  页面 %d 个，全部命中缓存" % len(tasks))

    def text(kind, mid):
        p = fp(kind, mid)
        return p.read_text(encoding="gb18030", errors="ignore") if ok(p) else ""

    res = {}
    for no, (mid, match, ko) in IDS.items():
        res[no] = {"match": match, "kickoff": ko, "id": mid,
                   "ah": parse_handicap(text("yazhi", mid)),
                   "ou": parse_handicap(text("daxiao", mid)),
                   "ox": parse_1x2(text("ouzhi", mid))}

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    for no, r in res.items():
        have = [k for k in ROW_ORDER if k in r["ox"] or k in r["ah"] or k in r["ou"]]
        print("==", no, r["match"], "|", r["kickoff"], "| 可用:", ",".join(have))
        for k in ROW_ORDER:
            if k not in have:
                continue
            ah, ou, ox = r["ah"].get(k), r["ou"].get(k), r["ox"].get(k)
            print("   %-11s AH %s → %s | 1X2 %s → %s | OU %s → %s" % (
                k,
                lt(ah["open"]["line"]) if ah else "-", lt(ah["close"]["line"]) if ah else "-",
                "/".join("%.2f" % x for x in ox["open"]) if ox else "-",
                "/".join("%.2f" % x for x in ox["close"]) if ox else "-",
                ("%.2f" % abs(ou["open"]["line"])) if ou else "-",
                ("%.2f" % abs(ou["close"]["line"])) if ou else "-"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--workers", type=int, default=1,
                    help="并发抓取线程数（默认 1=串行；500 的 EdgeOne 对同 IP 并发敏感，>2 会整批返挑战页）")
    a = ap.parse_args()
    day = a.date
    out_dir = ROOT / "state" / "intel" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = build_ids(day)
    print("场次 %d" % len(ids))
    ids_fp = ROOT / "state" / "tmp" / ("_ids_%s.json" % day)
    ids_fp.write_text(json.dumps({k: {"id": v[0], "match": v[1], "kickoff": v[2]}
                                  for k, v in ids.items()}, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("  ids → %s" % ids_fp.relative_to(ROOT))
    run(ids, out_dir / ("_books_%s.json" % day), workers=a.workers)


if __name__ == "__main__":
    main()
