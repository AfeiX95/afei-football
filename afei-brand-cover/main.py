# -*- coding: utf-8 -*-
"""AFEI 品牌固定封面：一条命令出 3:4 与 16:9 两张，不含日期/场次/球队。"""
from __future__ import annotations

import json
from pathlib import Path

from src import landscape, portrait

ROOT = Path(__file__).resolve().parent


def main() -> None:
    theme = json.loads((ROOT / "config/theme.json").read_text(encoding="utf-8"))
    assets = ROOT / "assets/background"
    out = ROOT / "output"

    p = portrait.render(theme, assets / "portrait_bg.png", out / "afei_cover_3x4.png")
    print(f"✅ {p.relative_to(ROOT)}  {theme['portrait']['w']}x{theme['portrait']['h']}")
    l = landscape.render(theme, assets / "landscape_bg.png", out / "afei_cover_16x9.png")
    print(f"✅ {l.relative_to(ROOT)}  {theme['landscape']['w']}x{theme['landscape']['h']}")


if __name__ == "__main__":
    main()
