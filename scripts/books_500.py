# -*- coding: utf-8 -*-
"""从 500.com 缓存页抽取代表公司的 亚盘 / 欧赔 / 大小 初盘与即时（缺失页自动补抓）

用法：
    python -X utf8 scripts/books_500.py --date 20261028
输出: state/intel/<date>/_books_<date>.json
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _x500  # noqa: E402  500 反爬会话（票据 state/tmp/500session.json，30 天有效）
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "state" / "tmp" / "500cache"
CACHE.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


def get(url: str, enc: str = "gb18030") -> str:
    return _x500.fetch(url, enc=enc)


def build_ids(day: str) -> dict:
    """用 500 首页的 tr(编号/id/gy) 与当日 _intel 的队名做最佳匹配，得到 {场次三位: (id, "联赛 主 vs 客", "MM-DD HH:MM")}"""
    import difflib

    # 用带日期的赛程页：index.php 只回当前在售的十余场，跨零点/次日盘直接取不到
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
            out[no3] = (mid, "%s %s vs %s" % (parts[0], parts[1], parts[2]), tm.group(1) if tm else "") 
            print("  %s → %s %s (score %.2f)" % (no3, mid, parts[1], best_score))
        else:
            print("  !! %s 未匹配到 500 id" % no3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    a = ap.parse_args()
    day = a.date
    out_dir = ROOT / "state" / "intel" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = build_ids(day)
    print("场次 %d" % len(ids))
    run(ids, out_dir / ("_books_%s.json" % day))


def lt(v):
        if v is None:
            return "-"
        if abs(v) < 0.01:
            return "平手"
        side = "主让" if v < 0 else "主受让"
        N = {0.25: "平/半", 0.5: "半球", 0.75: "半/一", 1.0: "一球", 1.25: "一/球半", 1.5: "球半",
             1.75: "球半/两", 2.0: "两球", 2.25: "两/两球半", 2.5: "两球半", 2.75: "两球半/三", 3.0: "三球"}
        return "%s %s" % (side, N.get(round(abs(v), 2), "%.2f" % abs(v)))


def run(IDS, OUT):
    ROW_ORDER = ["澳彩", "皇冠", "Bet365", "易胜博", "威廉", "立博", "伟德", "Interwetten"]


    def page(kind, mid):
        fp = CACHE / ("%s_%s.html" % (kind, mid))
        if fp.exists():
            return fp.read_text(encoding="gb18030", errors="ignore")
        url = "https://odds.500.com/fenxi/%s-%s.shtml" % (kind, mid)
        for attempt in range(4):
            try:
                # 反爬统一交给 _x500（票据 state/tmp/500session.json，30 天有效）
                body = _x500.fetch(url, enc="gb18030")
                fp.write_text(body, encoding="gb18030", errors="ignore")
                time.sleep(1.5)
                return body
            except Exception:  # noqa: BLE001
                time.sleep(5 * (attempt + 1))
        return ""


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


    def parse_handicap(kind, mid):
        t = page(kind, mid)
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


    def parse_1x2(mid):
        t = page("ouzhi", mid)
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


    res = {}
    for no, (mid, match, ko) in IDS.items():
        res[no] = {"match": match, "kickoff": ko, "id": mid,
                   "ah": parse_handicap("yazhi", mid),
                   "ou": parse_handicap("daxiao", mid),
                   "ox": parse_1x2(mid)}

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

if __name__ == "__main__":
    main()
