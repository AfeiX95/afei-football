# -*- coding: utf-8 -*-
"""模板 B · 单场深度前瞻（1 场）。"""
from __future__ import annotations

from ..art import ball_svg, photo_bg, stadium_svg
from ..components import badge, corner_marks, disclaimer, panel, prob_bar, record_chips
from ..theme import BASE_CSS, COLORS, esc, md_date, weekday_cn

C_GREEN, C_CYAN, C_W, C_M = COLORS["green"], COLORS["cyan"], COLORS["white"], COLORS["muted"]

CSS = f"""
.hdr{{position:absolute;left:62px;right:62px;top:46px;display:flex;justify-content:space-between;
  align-items:center;font-size:19px;letter-spacing:.12em;font-weight:800;color:{C_M}}}
.hdr b{{color:{C_W};font-size:22px;letter-spacing:.04em}}
.hdr span{{color:{C_GREEN}}}
.meta{{position:absolute;left:62px;top:120px;display:flex;align-items:baseline;gap:22px}}
.meta b{{font-size:104px;line-height:.92;font-weight:900;letter-spacing:-.03em}}
.meta b i{{color:{C_GREEN};font-style:normal}}
.meta div{{display:grid;gap:6px}}
.meta span{{font-size:24px;font-weight:800;color:{C_W};letter-spacing:.05em}}
.meta em{{font-style:normal;font-size:19px;color:{C_M};font-weight:700;letter-spacing:.08em}}
.artwrap{{position:absolute;left:-60px;right:-60px;top:300px;height:560px;opacity:.9}}
.photobg{{position:absolute;inset:0;background-size:cover;background-position:center 34%;z-index:0}}
.photobg .pscrim{{position:absolute;inset:0;
  background:linear-gradient(180deg,{COLORS['background']}f2 0%,{COLORS['background']}bb 16%,{COLORS['background']}33 40%,{COLORS['background']}88 62%,{COLORS['background']}f7 82%,{COLORS['background']} 100%),
             linear-gradient(90deg,{COLORS['background']}cc 0%,{COLORS['background']}22 32%,transparent 58%)}}
.photobg.wide .pscrim{{background:linear-gradient(90deg,{COLORS['background']} 0%,{COLORS['background']}f2 22%,{COLORS['background']}99 44%,transparent 68%),
  linear-gradient(180deg,{COLORS['background']}e6 0%,transparent 24%,transparent 70%,{COLORS['background']}f0 92%,{COLORS['background']} 100%)}}
.vsrow{{position:absolute;left:62px;right:62px;top:286px;display:flex;align-items:center;justify-content:space-between}}
.vsrow .side{{display:flex;flex-direction:column;align-items:center;gap:14px;width:330px}}
.vsrow .vsmid{{font-size:62px;font-weight:900;font-style:italic;color:{C_GREEN};letter-spacing:.04em;
  text-shadow:0 0 26px rgba(0,240,120,.45)}}
.crest{{display:grid;place-items:center;border-radius:50%;font-weight:900;letter-spacing:.02em}}
.bname{{font-weight:900;text-align:center;letter-spacing:.02em}}
.bname2{{font-size:13px;color:{C_M};letter-spacing:.14em;text-align:center;margin-top:2px}}
.badge{{display:flex;flex-direction:column;align-items:center;gap:10px}}
.badge .crest{{box-shadow:0 0 0 6px rgba(0,0,0,.35),0 18px 40px rgba(0,0,0,.5)}}
.sect{{position:absolute;left:62px;right:62px}}
.sect .hd{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}}
.sect .hd b{{font-size:22px;font-weight:900;letter-spacing:.04em}}
.sect .hd b i{{display:inline-block;width:6px;height:20px;background:{C_GREEN};margin-right:10px;
  vertical-align:-3px;border-radius:1px}}
.sect .hd span{{font-size:15px;color:#4E6076;font-weight:700;letter-spacing:.1em}}
.panel{{border:1px solid rgba(0,240,120,.18);border-radius:14px;
  background:linear-gradient(180deg,rgba(9,23,37,.92),rgba(5,14,22,.9));padding:16px 18px}}
.row3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}}
.pair{{display:grid;gap:10px}}
.pair span{{font-size:15px;color:{C_M};font-weight:700;letter-spacing:.06em}}
.pair b{{font-size:24px;font-weight:900;color:{C_W}}}
.chips{{display:flex;gap:5px;margin-top:10px}}
.chips i{{width:15px;height:15px;border-radius:3px;display:block;background:#22415C}}
.chips i.w{{background:{C_GREEN}}} .chips i.d{{background:#4B6A85}} .chips i.l{{background:#8C3550}}
.pbar{{margin-bottom:10px}}
.pbar .pl{{display:flex;justify-content:space-between;font-size:16px;font-weight:800;color:#C7D5E5;margin-bottom:6px}}
.ptrack{{height:7px;border-radius:4px;background:#12222F;overflow:hidden}}
.pfill{{height:100%;border-radius:4px}}
ul.obs{{list-style:none;display:grid;gap:8px}}
ul.obs li{{font-size:18px;line-height:1.5;color:#D3DFEC;padding-left:16px;position:relative}}
ul.obs li:before{{content:"·";position:absolute;left:2px;color:{C_GREEN};font-weight:900}}
.verdict b{{display:block;font-size:34px;font-weight:900;color:{C_GREEN};letter-spacing:.02em}}
.verdict .sc{{margin-top:10px;font-size:19px;color:#D3DFEC;font-weight:700}}
.verdict .sc em{{font-style:normal;color:{C_W};font-weight:900}}
.verdict .cf{{margin-top:8px;font-size:16px;color:{C_M};font-weight:700}}
.foot{{position:absolute;left:62px;right:62px;bottom:64px;display:flex;justify-content:space-between;align-items:flex-end;color:#6B7C90;font-size:16px;font-weight:700}}
.fb{{display:flex;align-items:center;gap:14px}}
.fb i{{display:block;width:7px;height:52px;background:{C_GREEN};border-radius:2px}}
.fb b{{display:block;font-size:44px;font-weight:900}}
.fb span{{display:block;margin-top:4px;font-size:18px;color:{C_M};font-weight:700;letter-spacing:.12em}}
.ft{{font-size:18px;color:{C_M};font-weight:700}}
.legal{{position:absolute;left:62px;right:62px;bottom:34px;font-size:14px;color:#46566A;font-weight:600}}
"""

CSS_WIDE = """
.hdr{top:36px}
.meta{top:104px}
.meta b{font-size:92px}
.artwrap{left:auto;right:-40px;top:40px;width:940px;height:1000px;-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 16%,#000 100%)}
.vsrow{top:120px;height:300px}
.vsrow{left:72px;right:990px;top:250px}
.vsrow .side{width:300px}
#sect-data{top:640px;left:72px;right:72px}
#sect-ana{top:812px;left:72px;right:72px}
.foot{bottom:64px;left:72px;right:72px}
.legal{bottom:24px;left:72px;right:72px}
"""


def render(data: dict, ratio: str = "3:4") -> str:
    wide = ratio == "16:9"
    ms = data.get("matches") or []
    m = ms[0] if ms else {}
    date_iso = data.get("date") or "2026-01-01"
    wd = data.get("weekday") or weekday_cn(date_iso)
    w, h = (1920, 1080) if wide else (1080, 1440)
    bg = (data.get("background") or {}).get("16x9" if wide else "3x4") or ""
    brand = data.get("brand") or "阿飞 · 赛博聊球"
    slogan = data.get("subtitle") or "用数据拆解比赛"
    home, away = m.get("home") or "主队", m.get("away") or "客队"
    probs = m.get("probs") or {}
    pick = m.get("pick") or {}
    h2h = m.get("h2h") or {}
    d1, d2 = md_date(date_iso).split(".")
    prob_src = m.get("prob_source") or "模型概率"
    p_home = probs.get("home", 0)
    p_draw = probs.get("draw", 0)
    p_away = probs.get("away", 0)
    obs = m.get("observations") or []
    if not obs:
        obs = [m.get("insight") or "数据不足，暂无可靠观察。"]
    obs_html = "".join(f"<li>{esc(x)}</li>" for x in obs[:3])
    conf = pick.get("confidence") or ""
    score_ref = pick.get("score_ref") or "—"
    score_risk = pick.get("score_risk") or "—"
    if bg:
        art_html = photo_bg(bg, "wide" if wide else "")
    else:
        art_html = ('<div class="artwrap">%s</div>'
                    % stadium_svg(1080, 1440, far_y=560, near_y=1180, seed=23))
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>
:root{{--w:{w}px;--h:{h}px}}
{BASE_CSS}{CSS}{CSS_WIDE if wide else ''}
</style></head><body><div class="root">
{art_html}
{corner_marks()}
<div class="hdr"><span><b>{esc(brand)}</b><br><span>{esc(slogan)}</span></span>
  <span>{esc(m.get('league') or '')} · 第 {esc(m.get('round') or '—')} 轮</span></div>
<div class="meta"><b>{d1}<i>.</i>{d2}</b><div>
  <span>{esc(wd)} {esc(m.get('kickoff') or '')}</span>
  <em>{esc(m.get('league') or '')}{(' · 第 ' + esc(str(m.get('round'))) + ' 轮') if m.get('round') else ''}</em>
</div></div>
<div class="vsrow">
  <div class="side">{badge(home, 110 if wide else 150, m.get('home_en') or '')}</div>
  <div class="vsmid">VS</div>
  <div class="side">{badge(away, 110 if wide else 150, m.get('away_en') or '')}</div>
</div>
<div class="sect" id="sect-data" style="top:{'560' if wide else '880'}px">
  <div class="hd"><b><i></i>近期与交锋</b><span>已发生结果 · 不做预测</span></div>
  <div class="row3">
    {panel('<span class="mono" style="font-size:14px;color:#5A7186">主队 · 近 5 场</span>'
           f'<div style="font-size:30px;font-weight:900;margin:6px 0">{esc(m.get("home_record") or "—")}</div>'
           + record_chips(m.get("home_record") or "")
           + f'<div style="margin-top:10px;font-size:17px;color:#CBD8E6;font-weight:700">'
             f'场均进 {esc(m.get("home_goals_for") or "—")} · 失 {esc(m.get("home_goals_against") or "—")}</div>')}
    {panel('<span class="mono" style="font-size:14px;color:#5A7186">历史交锋</span>' +
           (f'<div style="font-size:30px;font-weight:900;margin:6px 0">{int(h2h.get("n") or 0)} 场</div>'
            f'<div style="font-size:17px;color:#CBD8E6;font-weight:700">场均进球 {esc(h2h.get("avg_goals") or "—")}</div>'
            f'<div style="margin-top:10px;font-size:16px;color:#5A7186;font-weight:700">{esc(h2h.get("note") or "")}</div>')
           if h2h.get("n") else
           '<div style="font-size:22px;font-weight:800;color:#7C8EA3;margin-top:26px">暂无可靠数据</div>')}
    {panel('<span class="mono" style="font-size:14px;color:#5A7186">客队 · 近 5 场</span>'
           f'<div style="font-size:30px;font-weight:900;margin:6px 0">{esc(m.get("away_record") or "—")}</div>'
           + record_chips(m.get("away_record") or "")
           + f'<div style="margin-top:10px;font-size:17px;color:#CBD8E6;font-weight:700">'
             f'场均进 {esc(m.get("away_goals_for") or "—")} · 失 {esc(m.get("away_goals_against") or "—")}</div>')}
  </div>
</div>
<div class="sect" id="sect-ana" style="top:{'800' if wide else '1130'}px">
  <div class="hd"><b><i></i>观察与判断</b><span>概率口径：{esc(prob_src)}</span></div>
  <div class="row3">
    {panel(prob_bar("主胜", p_home, C_GREEN) + prob_bar("平局", p_draw, "#4B6A85") + prob_bar("客胜", p_away, "#8C3550"))}
    {panel(f'<ul class="obs">{obs_html}</ul>')}
    {panel(f'<div class="verdict"><b>{esc(pick.get("dir") or "暂无明确倾向")}</b>'
           f'<div class="sc">参考比分 <em>{esc(score_ref)}</em>　防范 <em>{esc(score_risk)}</em></div>'
           f'<div class="cf">{("信心 " + esc(conf)) if conf else "信心：低（数据不足）"}</div></div>')}
  </div>
</div>
<div class="foot">
  <div class="ft">{esc(data.get('tail') or '')}</div>
</div>
{disclaimer()}
</div></body></html>"""
