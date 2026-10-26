# -*- coding: utf-8 -*-
"""模板 A · 每日赛事总览（8～20 场）。"""
from __future__ import annotations

from ..art import ball_svg, photo_bg, stadium_svg
from ..components import badge, corner_marks, disclaimer, hud_micro, kpi, logo_uri  # noqa: F401
from ..theme import BASE_CSS, COLORS, MONO, esc, md_date, short_date, uniq, weekday_cn

CSS = f"""
.hdr{{position:absolute;left:62px;right:62px;top:46px;display:flex;justify-content:space-between;
  align-items:center;font-size:19px;letter-spacing:.14em;color:{COLORS['muted']};font-weight:700}}
.hdr b{{color:{COLORS['green']}}}
.date{{position:absolute;left:62px;top:104px}}
.date b{{display:block;font-size:128px;line-height:.9;font-weight:900;letter-spacing:-.035em}}
.date b i{{color:{COLORS['green']};font-style:normal}}
.date span{{display:block;margin-top:12px;font-size:25px;font-weight:800;color:{COLORS['muted']};letter-spacing:.05em}}
.title{{position:absolute;left:62px;top:302px;font-size:86px;line-height:1.08;font-weight:900;letter-spacing:-.01em}}
.title em{{font-style:normal;color:{COLORS['green']}}}
.stat{{position:absolute;left:62px;top:520px;font-size:25px;font-weight:700;color:#A9BACE;letter-spacing:.04em}}
.stat b{{color:{COLORS['white']}}}
.slogan{{position:absolute;left:62px;top:566px;font-size:22px;font-weight:800;color:#4FB98E;letter-spacing:.16em}}
.kpis{{position:absolute;right:62px;top:104px;width:308px;display:grid;gap:14px}}
.kcard{{position:relative;border:1px solid rgba(0,240,120,.24);border-radius:14px;
  background:linear-gradient(180deg,rgba(10,26,38,.9),rgba(6,16,24,.86));padding:16px 18px}}
.knum b{{font-size:52px;font-weight:900;color:{COLORS['green']};line-height:1}}
.knum i{{font-size:21px;font-style:normal;color:{COLORS['muted']};font-weight:700;margin-left:5px}}
.kico{{position:absolute;right:16px;top:16px;opacity:.9}}
.klabel{{margin-top:6px;font-size:20px;color:#C6D4E4;font-weight:700;letter-spacing:.04em}}
.artwrap{{position:absolute;left:-40px;right:-40px;top:600px;height:590px;overflow:hidden}}
.photobg{{position:absolute;left:0;right:0;top:470px;height:820px;
  background-size:cover;background-position:center 22%;z-index:0}}
.photobg .pscrim{{position:absolute;inset:0;
  background:linear-gradient(180deg,{COLORS['background']} 0%,{COLORS['background']}bb 8%,transparent 30%,transparent 64%,{COLORS['background']}cc 90%,{COLORS['background']} 100%),
             linear-gradient(90deg,{COLORS['background']}dd 0%,{COLORS['background']}44 34%,transparent 62%)}}
.photobg.side{{left:30%;top:0;height:100%;background-position:center 42%}}
.photobg.side .pscrim{{background:linear-gradient(90deg,{COLORS['background']} 0%,{COLORS['background']}ee 14%,{COLORS['background']}77 34%,transparent 62%),
  linear-gradient(180deg,{COLORS['background']}cc 0%,transparent 18%,transparent 76%,{COLORS['background']}e0 100%)}}

.artwrap:after{{content:"";position:absolute;left:0;right:0;bottom:0;height:200px;background:linear-gradient(180deg,transparent,#071019 84%)}}
.ballwrap{{position:absolute;left:50%;margin-left:-88px;top:636px;opacity:.85}}
.artwrap.side{{left:auto;right:-30px;top:10px;width:1000px;height:1060px;-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 14%,#000 100%)}}
.ballwrap.side{{left:auto;right:300px;top:250px;margin-left:0}}
.leagues{{position:absolute;left:62px;right:62px;bottom:186px;font-size:19px;color:{COLORS['muted']};
  letter-spacing:.03em;font-weight:650;line-height:1.6}}
.leagues b{{color:{COLORS['green']};font-weight:800;margin-right:10px}}
.sched{{position:absolute;left:62px;right:62px;top:650px;display:grid;
  grid-template-columns:1fr 1fr;grid-template-rows:repeat(6,1fr);grid-auto-flow:column;
  gap:7px 18px;z-index:3}}
.srow{{display:flex;align-items:center;justify-content:space-between;gap:8px;height:48px;padding:0 12px;border-radius:8px;
  background:rgba(6,13,21,.92);border:1px solid rgba(0,240,120,.22);border-left:3px solid rgba(0,240,120,.66)}}
.srow .tm{{font-family:{MONO};font-size:16px;color:{COLORS['green']};width:54px;flex:0 0 auto;letter-spacing:.02em}}
.srow img{{width:30px;height:30px;object-fit:contain}}
.srow .hm,.srow .aw{{font-size:22px;font-weight:800;color:#E8F1FB;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.srow .hm{{width:auto;flex:0 0 auto}} .srow .aw{{width:auto;flex:0 0 auto}}
.srow .vs{{margin:0 2px}}
.srow .vs{{font-size:13px;flex:0 0 auto;font-weight:900;color:#5C7488;letter-spacing:.06em}}
.sched.wide{{top:auto;bottom:136px;left:900px;right:72px;display:grid;
  grid-template-columns:1fr 1fr;grid-template-rows:repeat(6,1fr);grid-auto-flow:column;gap:6px 12px}}
.sched.wide .srow{{height:46px;padding:0 12px}}
.sched.wide .hm,.sched.wide .aw{{font-size:19px}}
.split{{position:absolute;left:62px;right:62px;bottom:166px;height:1px;
  background:linear-gradient(90deg,rgba(0,240,120,.55),rgba(0,240,120,.08))}}
.foot{{position:absolute;left:62px;right:62px;bottom:84px;display:flex;justify-content:space-between;align-items:flex-end}}
.fb{{display:flex;align-items:center;gap:14px}}
.fb i{{display:block;width:7px;height:52px;background:{COLORS['green']};border-radius:2px}}
.fb b{{display:block;font-size:46px;font-weight:900;letter-spacing:.02em}}
.fb span{{display:block;margin-top:4px;font-size:18px;color:{COLORS['muted']};font-weight:700;letter-spacing:.12em}}
.ft{{font-size:18px;color:{COLORS['muted']};font-weight:700;letter-spacing:.08em}}
.legal{{position:absolute;left:62px;right:62px;bottom:34px;font-size:15px;color:#46566A;
  letter-spacing:.04em;font-weight:600}}
"""

CSS_WIDE = """
.hdr{top:38px}
.date{top:92px}
.date b{font-size:112px}
.title{top:286px;font-size:74px}
.stat{top:452px}
.slogan{top:494px}
.kpis{right:auto;left:72px;top:548px;width:900px;display:flex;gap:16px}
.kpis .kcard{flex:1}
.knum b{font-size:44px}
.artwrap{left:auto;right:-60px;top:0;width:1080px;height:1080px;overflow:hidden}
.leagues{left:72px;bottom:150px;width:860px;font-size:18px}
.split{left:72px;right:1000px;bottom:126px}
.foot{left:72px;right:72px;bottom:70px}
.fb b{font-size:40px}
.legal{bottom:26px;left:72px;right:72px}
"""


def render(data: dict, ratio: str = "3:4") -> str:
    wide = ratio == "16:9"
    ms = data.get("matches") or []
    date_iso = data.get("date") or "2026-01-01"
    wd = data.get("weekday") or weekday_cn(date_iso)
    lgs = uniq([m.get("league") for m in ms])
    slots = uniq([(m.get("kickoff") or "") for m in ms if m.get("kickoff")])
    n = len(ms)
    w, h = (1920, 1080) if wide else (1080, 1440)
    times = sorted([m.get("kickoff") for m in ms if m.get("kickoff")])
    evening = [t for t in times if t >= "12:00"]
    if data.get("kick_day"):
        kick_day = data["kick_day"]
    elif evening and times and times[0] < "12:00":
        kick_day = "%s %s 起 跨夜" % (short_date(date_iso), evening[0])
    elif times:
        kick_day = "%s %s–%s" % (short_date(date_iso), times[0], times[-1])
    else:
        kick_day = short_date(date_iso)
    bg = (data.get("background") or {}).get("3x4" if not wide else "16x9") or ""
    brand = data.get("brand") or "阿飞 · 赛博聊球"
    slogan = data.get("subtitle") or "用数据拆解比赛"
    tail = data.get("tail") or "%d 场，先看账，再看球" % n
    icons = {
        "ball": '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="%s" stroke-width="1.6">'
                '<circle cx="12" cy="12" r="9"/><polygon points="12,5 17,9 15,15 9,15 7,9"/></svg>' % COLORS["green"],
        "clock": '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="%s" stroke-width="1.6">'
                 '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 3"/></svg>' % COLORS["green"],
        "layer": '<svg viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="%s" stroke-width="1.6">'
                 '<path d="M12 4l8 4-8 4-8-4z"/><path d="M4 12l8 4 8-4"/><path d="M4 16l8 4 8-4"/></svg>' % COLORS["green"],
    }
    kpis = (kpi(str(n), "场", "赛事拆解", icons["ball"]) +
            kpi(str(len(slots)), "段", "开球时段", icons["clock"]) +
            kpi(str(len(lgs)), "项", "联赛覆盖", icons["layer"]))
    d1, d2 = md_date(date_iso).split(".")
    if bg:
        art_html = photo_bg(bg, "side") if wide else photo_bg(bg)
    else:
        crop = (340, 330, 700, 760) if wide else (0, 445, 1080, 590)
        art_html = ('<div class="artwrap%s">%s</div>'
                    % (" side" if wide else "", stadium_svg(1080, 1440, crop=crop)))
    rows = []
    for m in ms:
        t = (m.get("kickoff") or "").strip() or "—"
        rows.append('<div class="srow"><span class="tm">%s</span>%s<span class="hm">%s</span>'
                    '<span class="vs">VS</span><span class="aw">%s</span>%s</div>'
                    % (esc(t), badge(m.get("home", ""), 20, label=False, cls="cr", abbr_len=1)
                       if logo_uri(m.get("home", "")) else "",
                       esc(m.get("home", "")), esc(m.get("away", "")),
                       badge(m.get("away", ""), 20, label=False, cls="cr", abbr_len=1)
                       if logo_uri(m.get("away", "")) else ""))
    sched_html = '<div class="sched%s">%s</div>' % (' wide' if wide else '', ''.join(rows))
    ball_html = "" if bg else '<div class="ballwrap%s">%s</div>' % (" side" if wide else "", ball_svg(176))
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><style>
:root{{--w:{w}px;--h:{h}px}}
{BASE_CSS}{CSS}{CSS_WIDE if wide else ''}
</style></head><body><div class="root">
{art_html}
{ball_html}
{corner_marks()}
<div class="hdr"><span><b>{n}</b> MATCHES // DATA CARD</span><span>{esc(brand)}</span></div>
<div class="date"><b>{d1}<i>.</i>{d2}</b><span>{esc(wd)} ｜ {esc(kick_day)}</span></div>
<div class="title"><em>{n} 场</em>足球<br>赛事前瞻</div>
<div class="stat"><b>{n} 场赛事</b> · <b>{len(slots)} 个开球时段</b> · <b>{len(lgs)} 项联赛</b></div>
<div class="slogan">公开数据 · 模型推演 · 风险校验</div>
<div class="kpis">{kpis}</div>
{sched_html}
<div class="leagues"><b>联赛</b>{esc(' · '.join(lgs))}</div>
<div class="split"></div>
<div class="foot">
  <div class="fb"><i></i><div><b>{esc(brand)}</b><span>{esc(slogan)}</span></div></div>
  <div class="ft">{esc(tail)}</div>
</div>
{disclaimer()}
</div></body></html>"""
