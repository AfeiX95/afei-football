# -*- coding: utf-8 -*-
"""500.com 单场「数据页」抓取器：赛前积分榜 / 全季主客分项统计 / 交战历史 / 近期战绩

用途：给内部报告与足彩式盘口分析提供基本面（排名、近5场、往绩、主客分项）。
输入：单场 500 id（从 `live.500.com/wanchang.php?e=<date>` 取 `tr id="a<id>"`）
输出：`state/intel/<date>/_data_<date>.json`（结构见 main）

用法：
    python -X utf8 scripts/fenxi_500.py --date 20261027 --ids 1474025,1473992
    python -X utf8 scripts/fenxi_500.py --date 20261027 --ids-file state/tmp/ids.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import _x500  # noqa: E402  500 反爬会话（票据 state/tmp/500session.json，30 天有效）
CACHE = ROOT / "state" / "tmp" / "500cache"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def fetch(mid: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    fp = CACHE / f"shuju_{mid}.html"
    if fp.exists() and fp.stat().st_size > 50000:
        return fp.read_text(encoding="gb18030", errors="ignore")
    url = f"https://odds.500.com/fenxi/shuju-{mid}.shtml"
    for attempt in range(4):
        try:
            # 反爬统一交给 _x500（票据 state/tmp/500session.json，30 天有效）
            body = _x500.fetch(url, enc="gb18030")
            fp.write_text(body, encoding="gb18030", errors="ignore")
            time.sleep(1.5)
            return body
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {mid} {exc}")
            time.sleep(4 * (attempt + 1))
    return ""


def plain(seg: str) -> str:
    seg = re.sub(r"<script.*?</script>", "", seg, flags=re.S)
    seg = re.sub(r"<br\s*/?>", "\n", seg)
    seg = re.sub(r"</t[dh]>", " | ", seg)
    seg = re.sub(r"</tr>", "\n", seg)
    seg = re.sub(r"<[^>]+>", "", seg)
    seg = seg.replace("&nbsp;", " ")
    seg = re.sub(r"[ \t\u00a0]+", " ", seg)
    return re.sub(r"\n\s*\n+", "\n", seg)


def parse_standings(txt: str) -> list[tuple[int, str, int]]:
    """赛前积分榜 -> [(排名, 队名, 积分)]"""
    out, seen = [], set()
    for m in re.finditer(r"\n\s*(\d{1,2}) \| ([^\|\n]{2,20}) \| (\d{1,3}) \|", txt):
        rank, team, pts = int(m.group(1)), m.group(2).strip(), int(m.group(3))
        if team in seen:
            continue
        seen.add(team)
        out.append((rank, team, pts))
    return out


def parse_season(txt: str) -> list[dict]:
    """全季分项统计（总/主/客）——页面上按「主队在前、客队在后」出现两组"""
    groups = []
    cur = {}
    for m in re.finditer(
        r"(总成绩|主场|客场) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (-?\d+) \| (\d+) \| (\d+) \| (\d+)%",
        txt,
    ):
        key = m.group(1)
        cur[key] = {
            "p": int(m.group(2)),
            "w": int(m.group(3)),
            "d": int(m.group(4)),
            "l": int(m.group(5)),
            "gf": int(m.group(6)),
            "ga": int(m.group(7)),
            "gd": int(m.group(8)),
            "pts": int(m.group(9)),
            "rank": int(m.group(10)),
            "wr": int(m.group(11)),
        }
        if key == "客场":
            groups.append(cur)
            cur = {}
    return groups


RES_MAP = {"胜": "W", "平": "D", "负": "L"}


import _names  # noqa: E402  队名归一与别名词典（database/config/team_aliases.json）


_name_hit = _names.name_hit



def parse_h2h(txt: str) -> dict:
    m = re.search(r"双方近(\d+)次交战，(.+?)进(\d+)球，失(\d+)球，大球(\d+)次，小球(\d+)次", txt)
    head = None
    if m:
        head = {
            "n": int(m.group(1)),
            "text": m.group(2).strip(),
            "gf": int(m.group(3)),
            "ga": int(m.group(4)),
            "over": int(m.group(5)),
            "under": int(m.group(6)),
        }
    rows = []
    for m in re.finditer(r"([^\|\n]{1,8}) \| (\d{2}-\d{2}-\d{2}) \| ([^\|]+?)VS([^\|]+?) \| ([^\|]*?) \|", txt):
        league, date, home, away, rest = (m.group(i).strip() for i in range(1, 6))
        rows.append({"league": league, "date": date, "home": home, "away": away, "extra": rest})
        if len(rows) >= 12:
            break
    return {"summary": head, "rows": rows}


def _split_lead_digits(run: str) -> tuple[str, int]:
    """把「队名自带数字 + 比分」拆开：962→('96',2)、212→('21',2)、1→('',1)"""
    if run.isdigit() and int(run) <= 12:
        return "", int(run)
    n = len(run)
    for k in range(min(n - 1, 3), 0, -1):
        tail = run[k:]
        if tail.isdigit() and int(tail) <= 12:
            return run[:k], int(tail)
    return "", int(run[-1] or 0)


def parse_recent(txt: str, team: str, n: int = 5) -> dict:
    """近 n 场（按日期倒序，含比分与赛果），从「近期战绩」段落里取含该队的、已完赛的行"""
    start = txt.find("近期战绩")
    seg = txt[start:] if start > 0 else txt
    pat = re.compile(
        r"\| (\d{2}-\d{2}-\d{2}) \| ([^\|]*?)(\d+):(\d+)([^\|]*?) \| ([^\|]*) \| "
        r"([^\|]*) \| ([^\|]*) \| ([^\|]*) \| ([^\|]*) \|"
    )
    picked = []
    for m in pat.finditer(seg):
        date, pre, lead, aw_raw, post, line, half, res, pan, ou = (
            m.group(i).strip() for i in range(1, 11)
        )
        # 队名自带数字（汉诺威96 / 阿贾克斯U21）会被并进比分，按「名字后缀优先」拆回
        name_digits, hs = _split_lead_digits(lead)
        home, away = f"{pre}{name_digits}".strip(), post.strip()
        aw = int(aw_raw) if aw_raw.isdigit() else -1
        if hs > 15 or aw < 0 or aw > 15:
            continue
        if not _name_hit(team, home) and not _name_hit(team, away):
            continue
        is_home = _name_hit(team, home)
        gf, ga = (hs, aw) if is_home else (aw, hs)
        out = "W" if gf > ga else ("D" if gf == ga else "L")
        picked.append(
            {
                "date": date,
                "home": home,
                "away": away,
                "score": f"{hs}-{aw}",
                "venue": "H" if is_home else "A",
                "result": out,
                "line": line,
                "half": half,
                "res_cn": res,
                "pan": pan,
                "ou": ou,
            }
        )
        if len(picked) >= n:
            break
    return {
        "matches": picked,
        "form": "".join(p["result"] for p in picked),
        "w": sum(1 for p in picked if p["result"] == "W"),
        "d": sum(1 for p in picked if p["result"] == "D"),
        "l": sum(1 for p in picked if p["result"] == "L"),
        "gf": sum(int(p["score"].split("-")[0]) if p["venue"] == "H" else int(p["score"].split("-")[1]) for p in picked),
        "ga": sum(int(p["score"].split("-")[1]) if p["venue"] == "H" else int(p["score"].split("-")[0]) for p in picked),
    }


def parse_fixture(txt: str) -> dict:
    """页面顶部对阵：'意甲 26/27第9轮 萨索洛VS拉齐奥'"""
    out: dict = {}
    m = re.search(r"([^\s\|()]{2,20})VS([^\s\|()]{2,20})\((\d{4})/(\d{4})([^)]*)\)", txt)
    if m:
        out["home"], out["away"] = m.group(1).strip(), m.group(2).strip()
        out["season"] = f"{m.group(3)}/{m.group(4)}"
        out["league"] = m.group(5).strip()
    r = re.search(r"(\d{2}/\d{2}[^\s\|]{0,10}第\d+轮)", txt)
    if r:
        out["round"] = r.group(1)
    return out


def analyse(mid: str) -> dict:
    txt = plain(fetch(mid))
    fx = parse_fixture(txt)
    home, away = fx.get("home", ""), fx.get("away", "")
    if not home or not away:
        m = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]{2,10})VS([\u4e00-\u9fa5A-Za-z0-9]{2,10})", txt)
        if m:
            home, away = m.group(1), m.group(2)
    season = parse_season(txt)

    def pack(g: dict) -> dict:
        return {"total": g.get("总成绩", {}), "home": g.get("主场", {}), "away": g.get("客场", {})}

    return {
        "id": mid,
        "round": fx.get("round", ""),
        "home": home,
        "away": away,
        "standings": parse_standings(txt),
        "season_home": pack(season[0]) if len(season) > 0 else {},
        "season_away": pack(season[1]) if len(season) > 1 else {},
        "h2h": parse_h2h(txt),
        "recent_home": parse_recent(txt, home) if home else {},
        "recent_away": parse_recent(txt, away) if away else {},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYYMMDD")
    ap.add_argument("--ids", default="", help="逗号分隔的 500 id")
    ap.add_argument("--ids-file", default="", help="每行一个 id")
    args = ap.parse_args()
    ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    if args.ids_file:
        ids += [x.strip() for x in Path(args.ids_file).read_text(encoding="utf-8").split() if x.strip()]
    out = {}
    for mid in ids:
        d = analyse(mid)
        out[mid] = d
        rh, ra = d.get("recent_home", {}), d.get("recent_away", {})
        sh, sa = d.get("season_home", {}).get("total", {}), d.get("season_away", {}).get("total", {})
        print(f"{mid} {d['home']} vs {d['away']} ({d['round']})")
        print(f"   主队本季 {sh.get('p','?')}场 {sh.get('w','?')}-{sh.get('d','?')}-{sh.get('l','?')} "
              f"进{sh.get('gf','?')}失{sh.get('ga','?')} 排名{sh.get('rank','?')} "
              f"({sh.get('pts','?')}分) | 近5 {rh.get('form','')} "
              f"({rh.get('w','?')}胜{rh.get('d','?')}平{rh.get('l','?')}负) "
              f"盘路:{''.join(p['pan'] or '?' for p in rh.get('matches', []))}")
        print(f"   客队本季 {sa.get('p','?')}场 {sa.get('w','?')}-{sa.get('d','?')}-{sa.get('l','?')} "
              f"进{sa.get('gf','?')}失{sa.get('ga','?')} 排名{sa.get('rank','?')} "
              f"({sa.get('pts','?')}分) | 近5 {ra.get('form','')} "
              f"({ra.get('w','?')}胜{ra.get('d','?')}平{ra.get('l','?')}负)")
        h = d["h2h"]["summary"]
        if h:
            print(f"   往绩 近{h['n']}次: {h['text']} 进{h['gf']}失{h['ga']} 大{h['over']}小{h['under']}")
    if out:
        day = args.date
        outp = ROOT / "state" / "intel" / day / f"_data_{day}.json"
        outp.parent.mkdir(parents=True, exist_ok=True)
        merged = {}
        if outp.exists():
            try:
                merged = json.loads(outp.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                merged = {}
        merged.update(out)
        outp.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
        print("→", outp)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
