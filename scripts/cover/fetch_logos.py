#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""下载队徽（维基百科条目主图），存到 assets/logos/，并写 logos.json 映射。

用法：
    python -X utf8 scripts/cover/fetch_logos.py            # 补全缺失的
    python -X utf8 scripts/cover/fetch_logos.py --force    # 全量重下

纪律：仅取维基共享资源/英文维基的条目主图（330px 缩略），本地留档；
     队徽是俱乐部商标，公开使用前请自行确认授权范围。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGO_DIR = ROOT / "assets" / "logos"
MAP_PATH = ROOT / "config" / "logos.json"
UA = {"User-Agent": "AfeiCoverBot/1.0 (local editorial use)"}
API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# 中文名 → 英文维基条目
TEAMS = {
    "布里斯班": "Brisbane Roar FC",
    "珀斯": "Perth Glory FC",
    "波鸿": "VfL Bochum",
    "沃夫斯堡": "VfL Wolfsburg",
    "埃夫斯堡": "IF Elfsborg",
    "马尔默": "Malmö FF",
    "前进之鹰": "Go Ahead Eagles",
    "特尔斯达": "SC Telstar",
    "布雷达": "NAC Breda",
    "赫拉克勒": "Heracles Almelo",
    "斯图加特": "VfB Stuttgart",
    "门兴": "Borussia Mönchengladbach",
    "都灵": "Torino FC",
    "蒙扎": "AC Monza",
    "布雷斯特": "Stade Brestois 29",
    "尼斯": "OGC Nice",
    "伊普斯": "Ipswich Town F.C.",
    "诺丁汉": "Nottingham Forest F.C.",
    "博尔顿": "Bolton Wanderers F.C.",
    "米堡": "Middlesbrough F.C.",
    "阿拉维斯": "Deportivo Alavés",
    "马拉加": "Málaga CF",
    "吉马良斯": "Vitória S.C.",
    "马里迪莫": "C.S. Marítimo",
}


def slug(name: str) -> str:
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5]+", "_", name).strip("_")
    return s or "team"


def fetch_one(zh: str, title: str, force: bool = False) -> dict:
    out = LOGO_DIR / (slug(zh) + ".png")
    if out.exists() and not force:
        return {"zh": zh, "title": title, "file": str(out.relative_to(ROOT)), "cached": True}
    url = API + urllib.parse.quote(title.replace(" ", "_"))
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
    except Exception as exc:  # noqa: BLE001
        return {"zh": zh, "title": title, "error": f"summary: {exc}"}
    thumb = (data.get("thumbnail") or {}).get("source") or ""
    if not thumb:
        return {"zh": zh, "title": title, "error": "no thumbnail on page"}
    try:
        req2 = urllib.request.Request(thumb, headers=UA)
        with urllib.request.urlopen(req2, timeout=30) as r2:
            blob = r2.read()
    except Exception as exc:  # noqa: BLE001
        return {"zh": zh, "title": title, "error": f"image: {exc}"}
    if len(blob) < 1500:
        return {"zh": zh, "title": title, "error": f"image too small ({len(blob)}B)"}
    LOGO_DIR.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    return {"zh": zh, "title": title, "file": str(out.relative_to(ROOT)), "bytes": len(blob)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    LOGO_DIR.mkdir(parents=True, exist_ok=True)
    ok, bad = {}, {}
    for zh, title in TEAMS.items():
        res = fetch_one(zh, title, a.force)
        if "error" in res:
            bad[zh] = res["error"]
            print(f"  [MISS] {zh:6s} {title}: {res['error']}")
        else:
            ok[zh] = {"title": title, "file": res["file"]}
            print(f"  [OK]   {zh:6s} {title} -> {res['file']}")
    MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    MAP_PATH.write_text(json.dumps({"logos": ok, "missing": bad}, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(f"\n{len(ok)} 张队徽，{len(bad)} 张缺失 -> {MAP_PATH.relative_to(ROOT)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
