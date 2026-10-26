# -*- coding: utf-8 -*-
"""AFEI Football Cover System v1.0 · 命令行入口。

用法：
    python -X utf8 scripts/cover/main.py --type auto   --input <matches.json> --out <目录>
    python -X utf8 scripts/cover/main.py --type daily  --input <matches.json> --out <目录> --ratio 16:9
    python -X utf8 scripts/cover/main.py --type single --input <matches.json> --out <目录> --match 0
    python -X utf8 scripts/cover/main.py --batch      --input <matches.json> --out <目录>

设计边界（对应项目分层）：
  本系统只做「读 JSON → 排版 → 出图」，不搜索赛事、不算模型、不编数据；
  队徽缺失一律降级为「缩写 + 稳定配色」，绝不伪造官方徽章。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.cover import checks, render  # noqa: E402
from scripts.cover.templates import daily, multi, single  # noqa: E402

TEMPLATES = {"daily": daily, "single": single, "multi": multi}
NAMES = {"daily": "每日赛事总览", "single": "单场深度前瞻", "multi": "多场矩阵前瞻"}


def pick_template(n: int) -> str:
    if n <= 1:
        return "single"
    if n <= 6:
        return "multi"
    return "daily"


def load(path: str) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = Path.cwd() / p
    return json.loads(p.read_text(encoding="utf-8"))


def gen(data: dict, kind: str, out_dir: Path, ratio: str, match_idx: int = 0,
        quiet: bool = False) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    if kind == "single":
        ms = data.get("matches") or []
        if not ms:
            raise SystemExit("single 模板需要至少 1 场比赛")
        payload["matches"] = [ms[min(match_idx, len(ms) - 1)]]
    elif kind == "multi":
        payload["matches"] = (data.get("matches") or [])[:6]

    html = TEMPLATES[kind].render(payload, ratio)
    tag = {"3:4": "3x4", "16:9": "16x9"}[ratio]
    label = payload["date"]
    if kind == "single":
        m = payload["matches"][0]
        label = "%s_%s_vs_%s" % (label, m.get("home"), m.get("away"))
    stem = "AFEI_%s_%s_%s" % (kind, label.replace("-", ""), tag)
    png = out_dir / (stem + ".png")
    render.render_html(html, png, ratio=ratio)
    if not quiet:
        print("  ✅ %s  %s" % (png.name, NAMES[kind]))
    return [png]


def main() -> None:
    ap = argparse.ArgumentParser(description="AFEI Football Cover System v1.0")
    ap.add_argument("--type", choices=["auto", "daily", "single", "multi"], default="auto")
    ap.add_argument("--input", required=True, help="比赛数据 JSON")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--ratio", choices=["3:4", "16:9", "both"], default="3:4")
    ap.add_argument("--match", type=int, default=0, help="single 模板取第几场（0 起）")
    ap.add_argument("--batch", action="store_true", help="同时出 3:4 与 16:9")
    ap.add_argument("--check", action="store_true", help="只跑质量自检，不渲染")
    a = ap.parse_args()

    data = load(a.input)
    n = len(data.get("matches") or [])
    kind = pick_template(n) if a.type == "auto" else a.type
    out_dir = Path(a.out)

    items = checks.run_checks(data, None, "3:4")
    ok = checks.report(items)
    if a.check:
        raise SystemExit(0 if ok else 1)
    if not ok:
        print("　（自检有 ERROR，仍然渲染，请人工复核以上项）")

    if a.batch:
        # 三模板 × 两比例，共六张（A 全量 / B 第一场 / C 前六场）
        ms = data.get("matches") or []
        idx = next((i for i, m in enumerate(ms) if m.get("probs")), 0)
        jobs = [("daily", dict(data)),
                ("single", dict(data, matches=[ms[idx]])),
                ("multi", dict(data, matches=ms[:6]))]
        for k, dd in jobs:
            for r in ("3:4", "16:9"):
                if not dd.get("matches"):
                    continue
                pngs = gen(dd, k, out_dir, r, 0 if k == "single" else a.match)
                for png in pngs:
                    checks.report(checks.run_checks(dd, png, r))
        return

    ratios = ["3:4", "16:9"] if a.ratio == "both" else [a.ratio]
    print("模板：%s（%s，%d 场）" % (kind, NAMES[kind], n))
    for r in ratios:
        pngs = gen(data, kind, out_dir, r, a.match)
        for png in pngs:
            checks.report(checks.run_checks(
                dict(data, matches=(data["matches"][:1] if kind == "single" else
                                    (data["matches"][:6] if kind == "multi" else data["matches"]))),
                png, r))


if __name__ == "__main__":
    main()
