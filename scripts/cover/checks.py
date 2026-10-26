# -*- coding: utf-8 -*-
"""质量自检：日期一致性、场次/联赛计数、空值、概率口径、输出尺寸。

只做「代码能判定」的项，不猜内容好坏；不通过项以 ERROR 前缀输出，CLI 以非零码退出。
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from PIL import Image

WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def run_checks(data: dict, png: Path | None = None, ratio: str = "3:4") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []

    date_iso = data.get("date") or ""
    try:
        d = _dt.date.fromisoformat(date_iso)
        wd = WEEKDAYS[d.weekday()]
        out.append(("OK", "日期 %s → %s" % (date_iso, wd)))
        if data.get("weekday") and data["weekday"] != wd:
            out.append(("ERROR", "weekday 字段（%s）与日期推算（%s）不一致" % (data["weekday"], wd)))
    except ValueError:
        out.append(("ERROR", "date 缺省或不是 ISO 日期：%r" % date_iso))

    ms = data.get("matches") or []
    out.append(("OK" if ms else "ERROR", "场次 %d" % len(ms)))
    lgs = {m.get("league") for m in ms if m.get("league")}
    out.append(("OK", "联赛去重 %d 项：%s" % (len(lgs), "、".join(sorted(lgs)))))

    need = ["home", "away", "kickoff"]
    missing = []
    for i, m in enumerate(ms):
        for k in need:
            if not m.get(k):
                missing.append("#%d.%s" % (i, k))
    out.append(("OK" if not missing else "ERROR", "必填字段缺失：%s" % (", ".join(missing) or "无")))

    # 概率口径
    for i, m in enumerate(ms):
        p = m.get("probs") or {}
        if not p:
            continue
        s = sum(float(p.get(k) or 0) for k in ("home", "draw", "away"))
        if abs(s - 100) > 1.0:
            out.append(("WARN", "#%d 三项概率之和 %.1f%%（≠100）" % (i, s)))
    srcs = {m.get("prob_source") for m in ms if m.get("probs")}
    if len(srcs) > 1:
        out.append(("ERROR", "同一张图混用了不同概率口径：%s" % "、".join(sorted(x for x in srcs if x))))

    # 空值/占位
    joined = " ".join(str(m.get(k) or "") for m in ms for k in ("home", "away", "insight"))
    for token in ("待补", "未知", "TBD", "??"):
        if token in joined:
            out.append(("ERROR", "出现占位符 %r" % token))

    if png and png.exists():
        with Image.open(png) as im:
            w, h = im.size
            expect = (2160, 2880) if ratio == "3:4" else (3840, 2160)
            out.append(("OK" if (w, h) == expect else "ERROR",
                        "输出尺寸 %dx%d（期望 %dx%d）" % (w, h, expect[0], expect[1])))
    return out


def report(items: list[tuple[str, str]]) -> bool:
    bad = 0
    for level, msg in items:
        if level != "OK":
            bad += 1
        print("[%s] %s" % (level, msg))
    return bad == 0
