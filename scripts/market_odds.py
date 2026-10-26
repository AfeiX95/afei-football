# -*- coding: utf-8 -*-
"""500.com 欧赔 + 亚盘 抓取（周二 2026-10-27 档 10 场）
缓存按 (类型, 比赛id) 命名；带 429 退避。
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"I:\阿飞说球")
OUT = ROOT / "state" / "intel" / "20261027"
CACHE = ROOT / "state" / "tmp" / "500cache"
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

IDMAP = {
    "001": ("1474025", "京都不死鸟 vs 纽卡斯尔喷气机", "10-27 18:00"),
    "002": ("1473992", "大田市民 vs 神户胜利船", "10-27 18:00"),
    "003": ("1473897", "北京国安 vs 全北现代", "10-27 20:15"),
    "004": ("1490697", "汉堡 vs 法兰克福", "10-28 01:00"),
    "005": ("1414253", "萨索洛 vs 拉齐奥", "10-28 01:30"),
    "006": ("1362815", "AIK索尔纳 vs 埃尔夫斯堡", "10-28 02:00"),
    "007": ("1490695", "多特蒙德 vs 云达不莱梅", "10-28 03:45"),
    "008": ("1490693", "科隆 vs 柏林联合", "10-28 03:45"),
    "009": ("1414173", "罗马 vs 卡利亚里", "10-28 03:45"),
    "010": ("1414221", "都灵 vs 科莫", "10-28 03:45"),
}


def page(kind, mid):
    """kind: yazhi | ouzhi"""
    fp = CACHE / ("%s_%s.html" % (kind, mid))
    if fp.exists():
        return fp.read_text(encoding="gb18030", errors="ignore")
    url = "https://odds.500.com/fenxi/%s-%s.shtml" % (kind, mid)
    last = None
    for attempt in range(5):
        try:
            body = urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                          timeout=40).read().decode("gb18030", "ignore")
            fp.write_text(body, encoding="gb18030", errors="ignore")
            time.sleep(1.5)
            return body
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (attempt + 1))
    print("FETCHFAIL", kind, mid, type(last).__name__)
    return ""


def plain(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def num(s):
    m = re.search(r"[0-9]+\.[0-9]+", s or "")
    return float(m.group(0)) if m else None


def parse_ah(mid):
    """每行按 (即时表, 初盘表) 成对读取；初盘的让球值取 ref 属性，不取中文盘口文字。"""
    t = page("yazhi", mid)
    books = []
    for chunk in t.split('<tr class="tr1"')[1:]:
        m = re.search(r'title="([^"]+)"', chunk)
        tabs = re.findall(r'class="pl_table_data">(.*?)</table>', chunk, re.S)
        if not (m and len(tabs) >= 2):
            continue
        inst, init = tabs[0], tabs[1]
        ping = re.search(r'class="ping">([0-9.]+)', inst)
        ying = re.search(r'class="ying">([0-9.]+)', inst)
        ref_c = re.search(r'ref="([-0-9.]+)"', inst)
        td = re.findall(r"<td[^>]*>(.*?)</td>", init, re.S)
        ref_o = re.search(r'ref="([-0-9.]+)"', init)
        if not (ping and ying and ref_c and ref_o and len(td) >= 3):
            continue
        h_o, a_o = num(td[0]), num(td[2])
        if h_o is None or a_o is None:
            continue
        books.append({"book": m.group(1),
                      "open": {"home": h_o, "ref": float(ref_o.group(1)), "away": a_o},
                      "close": {"home": float(ping.group(1)), "ref": float(ref_c.group(1)),
                                "away": float(ying.group(1))}})
    return books


def parse_1x2(mid):
    t = page("ouzhi", mid)
    books = []
    for chunk in t.split('<tr class="tr1"')[1:]:
        m = re.search(r'class="tb_plgs" title="([^"]+)"', chunk)
        tabs = re.findall(r'class="pl_table_data">(.*?)</table>', chunk, re.S)
        if not (m and tabs):
            continue
        trs = re.findall(r"<tr[^>]*>(.*?)</tr>", tabs[0], re.S)
        triples = []
        for tr in trs[:2]:
            vals = [num(plain(x)) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(vals) >= 3 and None not in vals[:3]:
                triples.append(vals[:3])
        if len(triples) == 2:
            books.append({"book": m.group(1), "open": triples[0], "close": triples[1]})
    return books


def avg(vals):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def devig(tri):
    inv = [1 / x for x in tri]
    s = sum(inv)
    return [round(i / s * 100, 1) for i in inv], round((s - 1) * 100, 2)


def main():
    res = {}
    for no, (mid, match, ko) in IDMAP.items():
        ah = parse_ah(mid)
        ox = parse_1x2(mid)
        ox_open = [avg([b["open"][i] for b in ox]) for i in range(3)] if ox else []
        ox_close = [avg([b["close"][i] for b in ox]) for i in range(3)] if ox else []
        p_close = devig(ox_close)[0] if ox_close else []
        p_open = devig(ox_open)[0] if ox_open else []
        ol = [b["open"]["ref"] for b in ah]
        cl = [b["close"]["ref"] for b in ah]
        res[no] = {"match": match, "kickoff": ko, "id": mid, "books_1x2": len(ox), "books_ah": len(ah),
                   "ox_open": ox_open, "ox_close": ox_close, "prob_open": p_open, "prob_close": p_close,
                   "overround_close": devig(ox_close)[1] if ox_close else None,
                   "ah_modal_open": max(set(ol), key=ol.count) if ol else None,
                   "ah_modal_close": max(set(cl), key=cl.count) if cl else None,
                   "ah_avg_open": avg(ol), "ah_avg_close": avg(cl),
                   "ah_water": [avg([b["close"]["home"] for b in ah]), avg([b["close"]["away"] for b in ah])],
                   "ah_moved": len([1 for b in ah if b["open"]["ref"] != b["close"]["ref"]]),
                   "detail_ah": ah, "detail_1x2": ox}
        print(no, match, "1X2:", len(ox), "AH:", len(ah),
              "| 即时去水", "/".join("%.1f" % x for x in p_close) if p_close else "-")

    (OUT / "_market_20261027.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    def f(v, n=2):
        return "-" if v is None else ("%." + str(n) + "f") % v

    L = ["# 2026-10-27 外部市场：欧赔（多公司均值）与亚盘（即时 / 初盘）", "",
         "来源 500彩票网；欧赔 = 多公司算术平均；(去水) = 1/odds 归一化概率；亚盘 ref：负数=主队受让，正数=主队让球。", "",
         "| 编号 | 对阵 | 开球 | 公司数(欧/亚) | 初盘 1X2 | 即时 1X2 | 即时去水(主/平/客) | 亚盘初盘 | 亚盘即时 | 走线/公司数 | 即时水位(主/客) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for no, r in res.items():
        L.append("| %s | %s | %s | %d/%d | %s | %s | %s | %s | %s | %d/%d | %s |" % (
            no, r["match"], r["kickoff"], r["books_1x2"], r["books_ah"],
            "/".join(f(x) for x in r["ox_open"]), "/".join(f(x) for x in r["ox_close"]),
            "/".join("%.1f%%" % x for x in r["prob_close"]),
            f(r["ah_avg_open"]), f(r["ah_avg_close"]), r["ah_moved"], r["books_ah"],
            "/".join(f(x, 3) for x in r["ah_water"])))
    (OUT / "_market_20261027.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print()
    print("\n".join(L[4:]))


if __name__ == "__main__":
    main()

