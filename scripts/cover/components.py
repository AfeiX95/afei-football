# -*- coding: utf-8 -*-
"""可复用组件：队徽降级徽标、数据面板、KPI 卡、HUD 微面板、比分/概率条。"""
from __future__ import annotations

import json
from pathlib import Path

from .art import hud_frame
from .theme import COLORS, esc, team_colors

_PKG = Path(__file__).resolve().parent
_LOGOS = {}


def _logo_map() -> dict:
    if _LOGOS:
        return _LOGOS
    p = _PKG / "config" / "logos.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8")).get("logos", {})
            for zh, meta in data.items():
                f = _PKG / meta.get("file", "")
                if meta.get("file") and f.exists():
                    _LOGOS[zh] = f
        except (json.JSONDecodeError, OSError):
            pass
    return _LOGOS


def logo_uri(name: str) -> str:
    f = _logo_map().get(name)
    if not f:
        return ""
    return Path(f).as_uri().replace("&", "&quot;")


def badge(name: str, size: int = 132, sub: str = "", label: bool = True, cls: str = "crest",
          abbr_len: int = 0) -> str:
    """队徽占位：缩写 + 稳定配色（真实队徽缺失时的唯一降级口径，绝不伪造官方徽章）。"""
    bg, ring = team_colors(name)
    nm = name or "?"
    abbr = nm[:abbr_len] if abbr_len else (nm if len(nm) <= 4 else nm[:3])
    fs = int(size * (0.36 if len(abbr) <= 2 else (0.26 if len(abbr) == 3 else 0.20)))
    uri = logo_uri(nm)
    if uri:
        inner = f'<img src="{uri}" alt="">'
        crest = (f'<div class="{cls} logo" style="width:{size}px;height:{size}px;'
                 f'border:2px solid {ring}">{{}}</div>').format(inner)
    else:
        crest = (f'<div class="{cls}" style="width:{size}px;height:{size}px;'
                 f'background:radial-gradient(circle at 50% 30%,{ring}22,{bg});'
                 f'border:2px solid {ring};color:{ring};font-size:{fs}px">{esc(abbr)}</div>')
    if not label:
        return crest
    return (f'<div class="badge" style="width:{size}px">{crest}'
            f'<div class="bname" style="font-size:{int(size * 0.155)}px">{esc(name)}</div>'
            f'{f"<div class=bname2>{esc(sub)}</div>" if sub else ""}</div>')


def panel(inner: str, cls: str = "", style: str = "") -> str:
    return f'<div class="panel {cls}" style="{style}">{inner}</div>'


def kpi(value: str, unit: str, label: str, icon: str = "") -> str:
    ico = '<div class="kico">%s</div>' % icon if icon else ''
    return ('<div class="kcard"><div class="knum"><b>%s</b><i>%s</i></div>'
            '<div class="klabel">%s</div>%s</div>' % (esc(value), esc(unit), esc(label), ico))


def stat_pair(left_label: str, left_val: str, right_label: str, right_val: str) -> str:
    return (f'<div class="pair"><div><span>{esc(left_label)}</span><b>{esc(left_val)}</b></div>'
            f'<div><span>{esc(right_label)}</span><b>{esc(right_val)}</b></div></div>')


def prob_bar(label: str, pct: float, color: str) -> str:
    pct = max(0.0, min(100.0, float(pct or 0)))
    return (f'<div class="pbar"><div class="pl"><span>{esc(label)}</span><b style="color:{color}">{pct:.1f}%</b></div>'
            f'<div class="ptrack"><div class="pfill" style="width:{pct:.1f}%;background:{color}"></div></div></div>')


def record_chips(record: str) -> str:
    """把「5胜0平5负」拆成五个色块（超出 5 场即全部上色，不伪造逐场结果）。"""
    w = p = l = 0
    s = record or ""
    try:
        if "胜" in s:
            w = int(s.split("胜")[0].split()[-1])
        if "平" in s:
            p = int(s.split("胜")[-1].split("平")[0].split()[-1] or 0)
        if "负" in s:
            l = int(s.split("平")[-1].split("负")[0].split()[-1] or 0)
    except (ValueError, IndexError):
        return ""
    total = max(1, w + p + l)
    scale = 5 / total
    dots = []
    for cls, n in (("w", w), ("d", p), ("l", l)):
        for _ in range(max(0, round(n * scale))):
            dots.append(f'<i class="{cls}"></i>')
    return f'<div class="chips">{"".join(dots[:5])}</div>'


def hud_micro(lines: list[str]) -> str:
    body = "".join(f"<span>{esc(x)}</span>" for x in lines)
    return f'<div class="hudmp mono">{body}</div>'


def corner_marks() -> str:
    return hud_frame()


def footer(brand: str, sub: str, tail: str, note: str = "") -> str:
    return (f'<div class="foot"><div class="fb"><i></i><div><b>{esc(brand)}</b>'
            f'<span>{esc(sub)}</span></div></div>'
            f'<div class="ft">{esc(tail)}</div></div>'
            f'{f"<div class=legal>{esc(note)}</div>" if note else ""}')


DISCLAIMER = "公开赛事数据整理 · 个人观察　仅供交流参考，不构成任何购买建议，请理性看待比赛"


def disclaimer() -> str:
    return f'<div class="legal">{esc(DISCLAIMER)}</div>'


GREEN = COLORS["green"]
CYAN = COLORS["cyan"]
MUTED = COLORS["muted"]
