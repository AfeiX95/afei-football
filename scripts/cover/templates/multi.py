# -*- coding: utf-8 -*-
"""模板 C · 多场矩阵前瞻（2～6 场）。"""
from __future__ import annotations

from ..art import stadium_svg
from ..components import badge, corner_marks, disclaimer, record_chips
from ..theme import BASE_CSS, COLORS, esc, md_date, uniq, weekday_cn

C_G, C_M, C_W = COLORS["green"], COLORS["muted"], COLORS["white"]

CSS = f"""
.hdr{{position:absolute;left:62px;right:62px;top:44px;display:flex;justify-content:space-between;
  align-items:center;font-size:18px;letter-spacing:.14em;color:{C_M};font-weight:800}}
.hdr span{{color:{C_G}}}
.date{{position:absolute;left:62px;top:96px;display:flex;align-items:flex-end;gap:14px}}
.date b{{font-size:96px;line-height:.9;font-weight:900;letter-spacing:-.03em}}
.date b i{{color:{C_G};font-style:normal}}
.date span{{font-size:24px;font-weight:800;color:{C_M};padding-bottom:10px;letter-spacing:.05em}}
.title{{position:absolute;left:62px;top:214px;font-size:66px;font-weight:900;letter-spacing:-.01em}}
.title em{{font-style:normal;color:{C_G}}}
.sub{{position:absolute;left:62px;top:300px;font-size:21px;font-weight:700;color:#4FB98E;letter-spacing:.14em}}
.artwrap{{position:absolute;left:-80px;right:-80px;top:-120px;height:520px;opacity:.42}}
.grid{{position:absolute;left:62px;right:62px;top:356px;display:grid;gap:16px}}
.card{{border:1px solid rgba(0,240,120,.18);border-radius:14px;
  background:linear-gradient(180deg,rgba(9,23,37,.94),rgba(5,14,22,.92));padding:14px 16px;
  display:flex;flex-direction:column;gap:10px}}
.card .top{{display:flex;justify-content:space-between;align-items:center}}
.card .tm{{font-size:14px;font-weight:800;color:{C_G};letter-spacing:.1em;
  border:1px solid rgba(0,240,120,.35);border-radius:6px;padding:2px 8px}}
.card .lg{{font-size:13px;color:#5A7186;font-weight:700;letter-spacing:.08em}}
.teams{{display:flex;align-items:center;justify-content:space-between;gap:8px}}
.teams .t{{display:flex;align-items:center;gap:8px;width:47%;min-width:0}}
.teams .t.r{{flex-direction:row-reverse;text-align:right}}
.cr{{display:grid;place-items:center;border-radius:50%;font-weight:900;flex:0 0 auto}}
.teams .n{{font-size:19px;font-weight:900;letter-spacing:.02em;line-height:1.2;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.vs{{font-size:17px;font-weight:900;font-style:italic;color:{C_G};opacity:.85}}
.dt{{display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;font-size:14px;color:#C4D2E2;font-weight:700}}
.dt span{{color:#5A7186;font-weight:700;margin-right:4px}}
.chips{{display:flex;gap:4px;margin-top:4px}}
.chips i{{width:11px;height:11px;border-radius:2px;display:block;background:#22415C}}
.chips i.w{{background:{C_G}}} .chips i.d{{background:#4B6A85}} .chips i.l{{background:#8C3550}}
.ins{{font-size:14px;line-height:1.45;color:#AFC0D2;border-top:1px dashed rgba(0,240,120,.16);padding-top:8px}}
.ins b{{color:{C_G};font-weight:900;margin-right:6px}}
.foot{{position:absolute;left:62px;right:62px;bottom:66px;display:flex;justify-content:space-between;align-items:flex-end}}
.fb{{display:flex;align-items:center;gap:12px}}
.fb i{{width:6px;height:44px;background:{C_G};border-radius:2px;display:block}}
.fb b{{display:block;font-size:40px;font-weight:900}}
.fb span{{display:block;margin-top:2px;font-size:16px;color:{C_M};font-weight:700;letter-spacing:.12em}}
.ft{{font-size:16px;color:{C_M};font-weight:700}}
.legal{{position:absolute;left:62px;right:62px;bottom:26px;font-size:13px;color:#46566A;font-weight:600}}
"""

CSS_WIDE = """
.hdr{top:34px}
.date{top:84px}
.date b{font-size:88px}
.title{top:190px;font-size:56px}
.sub{top:264px}
.artwrap{left:auto;right:-140px;top:-160px;width:1000px;height:640px;opacity:.4}
.grid{top:318px;left:72px;right:72px;gap:14px}
.card{padding:12px 14px;gap:8px}
.teams .n{font-size:17px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
.dt{font-size:13px}
.foot{bottom:56px;left:72px;right:72px}
.legal{bottom:22px;left:72px;right:72px}
"""


def _grid_css(n: int, wide: bool) -> str:
    if wide:
        cols = 3 if n > 4 else (2 if n > 1 else 1)
        rows = (n + cols - 1) // cols
        return (f".grid{{top:300px;bottom:236px;grid-template-columns:repeat({cols},1fr);"
                f"grid-template-rows:repeat({rows},1fr);grid-auto-rows:minmax(0,auto)}}")
    if n == 2:
        return ".grid{grid-template-columns:1fr;grid-auto-rows:250px}"
    if n == 3:
        return ".grid{grid-template-columns:1fr;grid-auto-rows:236px}"
    if n == 4:
        return ".grid{grid-template-columns:1fr 1fr;grid-auto-rows:262px}"
    if n == 5:
        return ".grid{grid-template-columns:1fr 1fr;grid-auto-rows:minmax(0,auto);bottom:250px;grid-template-rows:repeat(3,1fr)}"
    return ".grid{grid-template-columns:1fr 1fr;grid-auto-rows:minmax(0,auto);bottom:250px;grid-template-rows:repeat(3,1fr)}"


def _card(m: dict) -> str:
    home, away = m.get("home") or "主队", m.get("away") or "客队"
    hc = m.get("home_record") or "—"
    ac = m.get("away_record") or "—"
    return f"""<div class="card">
  <div class="top"><span class="tm">{esc(m.get('kickoff') or '—')}</span><span class="lg">{esc(m.get('league') or '')}</span></div>
  <div class="teams">
    <div class="t">{badge(home, 38, label=False, cls="cr", abbr_len=2)}
      <div class="n">{esc(home)}</div></div>
    <div class="vs">VS</div>
    <div class="t r">{badge(away, 38, label=False, cls="cr", abbr_len=2)}
      <div class="n">{esc(away)}</div></div>
  </div>
  <div class="dt">
    <div><span>主</span>{esc(hc)}</div>
    <div><span>客</span>{esc(ac)}</div>
    <div><span>场均进</span>{esc(m.get('home_goals_for') or '—')} / {esc(m.get('away_goals_for') or '—')}</div>
    <div><span>场均失</span>{esc(m.get('home_goals_against') or '—')} / {esc(m.get('away_goals_against') or '—')}</div>
  </div>
  <div class="ins"><b>矛盾</b>{esc(m.get('insight') or '数据不足，暂无可靠观察')}</div>
</div>"""


def render(data: dict, ratio: str = "3:4") -> str:
    wide = ratio == "16:9"
    ms = (data.get("matches") or [])[:6]
    date_iso = data.get("date") or "2026-01-01"
    wd = data.get("weekday") or weekday_cn(date_iso)
    w, h = (1920, 1080) if wide else (1080, 1440)
    brand = data.get("brand") or "阿飞 · 赛博聊球"
    slogan = data.get("subtitle") or "用数据拆解比赛"
    d1, d2 = md_date(date_iso).split(".")
    slots = uniq([m.get("kickoff") for m in ms if m.get("kickoff")])
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>
:root{{--w:{w}px;--h:{h}px}}
{BASE_CSS}{CSS}{CSS_WIDE if wide else ''}{_grid_css(len(ms), wide)}
</style></head><body><div class="root">
<div class="artwrap">{stadium_svg(1080, 1440, far_y=380, near_y=900, seed=31)}</div>
{corner_marks()}
<div class="hdr"><span>{esc(' · '.join(uniq([m.get('league') for m in ms])))}</span><span>阿飞 · 赛博聊球</span></div>
<div class="date"><b>{d1}<i>.</i>{d2}</b><span>{esc(wd)} ｜ {' / '.join(slots[:3])}{' …' if len(slots) > 3 else ''}</span></div>
<div class="title"><em>{len(ms)} 场</em>足球赛事前瞻</div>
<div class="sub">数据拆解 · 赛况分析 · 风险观察</div>
<div class="grid">{''.join(_card(m) for m in ms)}</div>
<div class="foot">
  <div class="fb"><i></i><div><b>{esc(brand)}</b><span>{esc(slogan)}</span></div></div>
  <div class="ft">{esc(data.get('tail') or '%d 场，先看账，再看球' % len(ms))}</div>
</div>
{disclaimer()}
</div></body></html>"""
