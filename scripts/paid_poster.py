# -*- coding: utf-8 -*-
"""付费内部资料 · 海报款静态版（无 JS、无页签，每场一节到底）。

数据层复用 paid_cyber.py（λ 双法分析、Dixon-Coles、信心指数、变盘时间轴）。
本文件只负责渲染：纯 HTML + CSS，脚本标签为零，打印/另存 PDF 都不丢内容。

用法：
    python scripts/paid_poster.py                 # 默认读今天/最近的模型文本
    python scripts/paid_poster.py --model state/batch/_model_20261017_sat.txt --date-dir 20261017
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import paid_cyber as pc  # noqa: E402  数据层

DIRS = ["主胜", "平", "客胜"]
DIMS = [("样本厚度", "w1", 20, "主客分离样本 {n} 场"), ("双法收敛", "w2", 20, "两条 λ 平均相对差 {gap}%"),
        ("三方一致", "w3", 25, "市场/公开预报/接口算法同向 {a}/3"), ("分歧可控", "w4", 25, "胜平负最大偏差 {pp}pp"),
        ("比分集中", "w5", 10, "Top3 比分合计 {t3}%")]


# ── 小工具 ──────────────────────────────────────────────
def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def f(x, n: int = 1) -> str:
    try:
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return str(x)


def pct(x, n: int = 1) -> str:
    return f"{float(x):.{n}f}%"


def sign(x, n: int = 1, suffix: str = "") -> str:
    v = float(x)
    return f"{'+' if v >= 0 else '−'}{abs(v):.{n}f}{suffix}"


def cls(x, good_high: bool = True) -> str:
    """数值配色：与模型/定价差异相关。"""
    v = abs(float(x))
    return "r" if v >= 15 else ("a" if v >= 6 else "g")


def bar(label: str, val: float, ghost: float | None = None, tone: str = "h", sub: str = "") -> str:
    """模型实心条 + 与定价之间的斜纹差 + 定价位置的竖刻度。"""
    g = m = ""
    if ghost is not None:
        lo, hi = min(val, ghost), max(val, ghost)
        g = (f'<i class="ghost" style="left:{min(max(lo, 0), 100):.1f}%;'
             f'width:{min(max(hi - lo, 0), 100):.1f}%"></i>'
             f'<i class="mark" style="left:{min(max(ghost, 0), 100):.1f}%"></i>')
    return f"""<div class="bar"><span class="bl">{esc(label)}</span>
      <span class="bt"><i class="fill {tone}" style="width:{min(max(val,0),100):.1f}%"></i>{g}</span>
      <span class="bv"><b>{pct(val)}</b>{f'<i>{sub.strip()}</i>' if sub else ''}</span></div>"""


def rows_table(head: list[str], rows: list[list[str]], cls_: str = "") -> str:
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls_}"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'


def kv_table(rows: list[tuple[str, str]]) -> str:
    body = "".join(f"<tr><th>{esc(k)}</th><td>{v}</td></tr>" for k, v in rows)
    return f'<table class="kv"><tbody>{body}</tbody></table>'


# ── 各板块 ──────────────────────────────────────────────
def block_matrix(m: dict) -> str:
    mat = m["matrix"]
    maxp = max(max(r) for r in mat)
    cells = ['<div class="mx"><div class="mxh"></div>']
    cells += "".join(f'<div class="mxh">{j}</div>' for j in range(7))
    for i in range(7):
        cells.append(f'<div class="mxh">{i}</div>')
        for j in range(7):
            p = mat[i][j]
            t = p / maxp
            bg = f"rgba({int(240 - 100 * t)},{int(228 - 145 * t)},{int(206 - 171 * t)},{0.25 + 0.75 * t:.3f})"
            col = "#FFFDF7" if t > 0.55 else "#221E18"
            txt = "" if p < 0.5 else (f"{p:.0f}" if p >= 10 else f"{p:.1f}")
            cells.append(f'<div class="mxc" style="background:{bg};color:{col}">{txt}</div>')
    cells.append("</div>")
    return "".join(cells)


def block_goals(m: dict) -> str:
    raw = m.get("goals_dc") or m["goals"]
    g = list(raw[:7]) + [round(sum(raw[7:]), 1)]
    labels = ["0", "1", "2", "3", "4", "5", "6", "7+"]
    mx = max(g) or 1
    bars = "".join(
        f'<div class="gcol"><span class="gv">{f(v)}</span>'
        f'<i style="height:{max(4, v / mx * 96):.0f}px"></i><span class="gl">{labels[i]}</span></div>'
        for i, v in enumerate(g))
    return f'<div class="gchart">{bars}</div><div class="gax">总进球数分布（%）· 只算 90 分钟 · 7 球以上并入 7+</div>'


def section_match(m: dict, idx: int) -> str:
    c, k, v, st, tech = m["conf"], m["cold"], m["verdict"], m["steps"], m["tech"]
    lam = m["lam"]
    hp, hmk, hand = m["hp"], m["hmk"], m["hand"]
    handtxt = f"+{hand}" if hand and hand > 0 else str(hand)
    o = m.get("move") or {}

    # 头
    head = f"""
<header class="mhead">
  <div class="mno"><span>{esc(m['no'])}</span><span>{esc(m['league'])}</span><span>{esc(m['kick'])} 开赛</span>
    <span>λ 合计 {f(lam['total'], 2)}</span></div>
  <h2>{esc(m['home'])}<em>vs</em>{esc(m['away'])}</h2>
  <div class="msum">
    <div><b>模型方向</b>{esc(c['model_dir'])}<span class="sep">/</span><b>定价方向</b>{esc(c['market_dir'])}
      <span class="sep">/</span><b>让球</b>{handtxt}</div>
    <div class="conf"><span class="cnum">{c['total']}</span><span class="cgrade">{esc(c['grade'])}</span>
      <span class="cdim">五维加权 · 满分 100</span></div>
  </div>
</header>"""

    # 结论
    concl = f"""
<div class="grid3">
  <div class="vcard"><span class="vt">首选 · PRIMARY</span><b>{esc(v['first'])}</b>
    <span class="vs">比分 {esc(v['first_score'])} · 模型 {pct(v['first_p'])}</span></div>
  <div class="vcard v2"><span class="vt">次选 · SECOND</span><b>{esc(v['second'])}</b>
    <span class="vs">比分 {esc(v['second_score'])} · 模型 {pct(v['second_p'])}</span></div>
  <div class="vcard v3"><span class="vt">防范 · GUARD</span><b>{esc(v['guard'])}</b>
    <span class="vs">比分 {esc(v['guard_score'])} · {esc(v['guard_mode'])} {pct(v['guard_p'])}</span></div>
</div>"""

    # ① 盘口反常门槛
    hcap = f"""
<section class="s">
  <h3><i>01</i>盘口反常门槛 <span class="x">先看门槛，再看结论</span></h3>
  <div class="col2">
    <div>
      <div class="cap">胜平负 · 固定奖金 {f(m['odds'][0], 2)} / {f(m['odds'][1], 2)} / {f(m['odds'][2], 2)}（返奖率 {f(m['payout'])}%）</div>
      {bar('主胜', m['p'][0], m['mk'][0], 'h', f'　定价 {f(m["mk"][0])}%')}
      {bar('平', m['p'][1], m['mk'][1], 'd', f'　定价 {f(m["mk"][1])}%')}
      {bar('客胜', m['p'][2], m['mk'][2], 'a', f'　定价 {f(m["mk"][2])}%')}
      <p class="cap2">浅色实心＝后台模型概率；斜纹＝定价去水后概率（同一把尺）。三项偏差：
        <b>主 {sign(m['edge'][0], 1, 'pp')}</b> / 平 {sign(m['edge'][1], 1, 'pp')} / 客 <b>{sign(m['edge'][2], 1, 'pp')}</b></p>
    </div>
    <div>
      <div class="cap">让球（{handtxt}）· 模型 {pct(hp[0])} / {pct(hp[1])} / {pct(hp[2])}　定价 {pct(hmk[0])} / {pct(hmk[1])} / {pct(hmk[2])}
        {f"<br>固定奖金 {f((o.get('latest_hand') or {}).get('odds',[0,0,0])[0],2)} / {f((o.get('latest_hand') or {}).get('odds',[0,0,0])[1],2)} / {f((o.get('latest_hand') or {}).get('odds',[0,0,0])[2],2)}" if (o.get('latest_hand') or {}).get('odds') else ""}</div>
      {bar('让胜', hp[0], hmk[0], 'h', f'　定价 {f(hmk[0])}%')}
      {bar('让平', hp[1], hmk[1], 'd', f'　定价 {f(hmk[1])}%')}
      {bar('让负', hp[2], hmk[2], 'a', f'　定价 {f(hmk[2])}%')}
      <p class="cap2">去掉平局后的胜负拆分：主 {pct(m['win_nodraw'][0])} / 客 {pct(m['win_nodraw'][1])}。
        让球一侧最大偏差 <b>{sign(m['h_edge'][max(range(3), key=lambda i: abs(m['h_edge'][i]))], 1, 'pp')}</b>，
        方向落{esc(DIRS[max(range(3), key=lambda i: abs(m['h_edge'][i]))])}。</p>
    </div>
  </div>
</section>"""

    # ② 数理模型
    mathb = f"""
<section class="s">
  <h3><i>02</i>数理模型 <span class="x">双法 λ · 泊松矩阵 · Dixon-Coles 低比分校准</span></h3>
  <div class="col2">
    <div>
      <div class="cap">λ 两条路与修正</div>
      {kv_table([
        ('方法一 · 实际数据（主客分离 + 样本量权重）', f"{f(lam['l1'][0],3)} / {f(lam['l1'][1],3)}"),
        ('方法二 · 定价反推（比分矩阵反解）', f"{f(lam['l2'][0],3)} / {f(lam['l2'][1],3)}"),
        ('综合 λ（代入模型）', f"<b>{f(lam['fin'][0],3)} / {f(lam['fin'][1],3)}</b>"),
        ('修正明细', esc(m['intel'].get('fix') or '—')),
        ('伤停修正', esc(m['intel'].get('inj_text') or '无')),
      ])}
      <p class="cap2">两条 λ 差得越多，说明市场与赛果之间存在叙事溢价，或者我方样本有缺口；修正幅度一般不超过 ±0.25，修正越大越说明基础数据有偏。</p>
    </div>
    <div>
      <div class="cap">胜平负交叉核对</div>
      {rows_table(['口径', '主胜', '平', '客胜'], [
        ['官方模型（2 万次抽样）', pct(m['p'][0]), pct(m['p'][1]), pct(m['p'][2])],
        ['独立泊松（本页精确解）', pct(m['oc']['pois'][0]), pct(m['oc']['pois'][1]), pct(m['oc']['pois'][2])],
        ['Dixon-Coles（ρ=%s）' % f(DATARHO, 2), pct(m['oc']['dc'][0]), pct(m['oc']['dc'][1]), pct(m['oc']['dc'][2])],
      ])}
      <div class="cap" style="margin-top:16px">低比分校准（ρ 只动 0-0 / 1-0 / 0-1 / 1-1 四格）</div>
      {rows_table(['比分', '独立泊松', 'DC 修正', '变化'],
                  [[r['s'], pct(r['p_pois'], 2), pct(r['p_dc'], 2), sign(r['p_dc'] - r['p_pois'], 1, 'pp')] for r in m['low_delta']])}
      <p class="cap2">独立泊松假设两队进球互不相干，会低估平局与低比分；DC 用相关系数 ρ 把这四格重新加权再把整张表归一。ρ 取常用区间的中值保守值，本批每场样本不足，未做逐场拟合。</p>
    </div>
  </div>
  <div class="col2" style="margin-top:18px">
    <div>
      <div class="cap">比分概率矩阵（DC 修正后，0–6 球，实色越深概率越高）</div>
      {block_matrix(m)}
      <div class="gax">↓ 主队进球　→ 客队进球　ρ = {f(DATARHO, 2)}</div>
    </div>
    <div>
      <div class="cap">总进球分布与大小球</div>
      {block_goals(m)}
      {rows_table(['大小球 / 双方进球', '模型概率'], [
        ['大 1.5 球', pct(m['over']['1.5'])], ['大 2.5 球', pct(m['over']['2.5'])],
        ['大 3.5 球', pct(m['over']['3.5'])], ['双方进球', pct(m['btts'])],
      ])}
      <p class="cap2">市场侧大小球盘口未接入（无公开快照），这一组只有模型口径，不做交叉验证。</p>
    </div>
  </div>
</section>"""

    # ③ 高阶数据
    th, ta = tech['home'], tech['away']
    meet = tech.get('meet') or {}
    techb = f"""
<section class="s">
  <h3><i>03</i>高阶数据 <span class="x">上下半场结构 · 进失球离散度 · 交手土壤 · 未接入清单</span></h3>
  <div class="col2">
    <div>
      <div class="cap">上下半场进球结构（近 {th['n']} 场）</div>
      {rows_table(['球队', '上半场', '下半场', '上半场占比', '形态'], [
        [esc(m['home']), f"{th['goals_1h']} 球", f"{th['goals_2h']} 球", pct(th['share_1h']),
         '进球集中在后半段' if th['share_1h'] < 30 else '上下半场均衡'],
        [esc(m['away']), f"{ta['goals_1h']} 球", f"{ta['goals_2h']} 球", pct(ta['share_1h']),
         '进球集中在后半段' if ta['share_1h'] < 30 else '上下半场均衡'],
      ])}
      <p class="cap2">竞彩公开数据只有半场/全场比分，没有分钟级进球与跑动；用「上半场进球占比」当体能曲线代理：占比越低说明越依赖下半场，反过来 70 分钟后被追的风险越大。</p>
      <div class="cap" style="margin-top:16px">进失球离散度与零封率（近 {th['n']} 场）</div>
      {rows_table(['球队', '场均进', '场均失', '零封率', '进球 σ', '失球 σ', '形态'], [
        [esc(m['home']), f(th['gf_avg'], 2), f(th['ga_avg'], 2), pct(th['cs_rate'], 0), f(th['sd_for'], 2), f(th['sd_against'], 2),
         '输出稳定' if th['sd_for'] < 1.2 else '进球波动大'],
        [esc(m['away']), f(ta['gf_avg'], 2), f(ta['ga_avg'], 2), pct(ta['cs_rate'], 0), f(ta['sd_for'], 2), f(ta['sd_against'], 2),
         '输出稳定' if ta['sd_for'] < 1.2 else '进球波动大'],
      ])}
      <p class="cap2">σ 越大越不稳定；场均进失是粗糙口径，所以模型里用主客分离 + 样本量权重压噪音。</p>
    </div>
    <div>
      <div class="cap">交手记录的比分土壤（近 {meet.get('n', 0)} 次）</div>
      <div class="grid4 tight">
        <div class="mini"><span>总进球 ≤2 占比</span><b>{pct(meet.get('low2', 0), 0)}</b><i>低比分土壤</i></div>
        <div class="mini"><span>双方进球率</span><b>{pct(meet.get('btts', 0), 0)}</b><i>同时开火</i></div>
        <div class="mini"><span>平局率</span><b>{pct(meet.get('draw', 0), 0)}</b><i>胶着度</i></div>
        <div class="mini"><span>场均总进球</span><b>{f(meet.get('avg_total', 0), 2)}</b><i>节奏</i></div>
      </div>
      {rows_table(['日期', '比分', '联赛'], [[esc(r['d']), esc(r['m']), esc(r.get('league', ''))] for r in (meet.get('detail') or [])])}
      <p class="cap2">交手总局数偏干或偏湿，是低比分（0-0 / 1-0 / 1-1）概率上调的实证依据，也是 DC 修正方向与历史吻合的检验点。</p>
      <div class="cap" style="margin-top:16px">未接入的高阶指标</div>
      <ul class="gaps">
        <li><b>未接入</b><span> xG / xGA / npxG</span>剥离神仙球与门将超神，判断进攻真实质量与运气透支</li>
        <li><b>未接入</b><span> PPDA</span>高位逼抢强度：两支队 PPDA 差距大时，2-2 / 3-2 的开放比分概率会跳</li>
        <li><b>未接入</b><span> 定位球 xG</span>现代足球约 25–30% 进球来自定位球，缺了会低估弱队得分下限</li>
        <li><b>未接入</b><span> 射门 / 射正 / 角球</span>穿透到过程数据才看得见的效率差</li>
        <li><b>未接入</b><span> 场地与天气</span>暴雨、积水会强行拉低总进球</li>
        <li><b>未接入</b><span> 裁判尺度</span>场均出牌与点球倾向影响 0-0 与 1-0 的存活率</li>
      </ul>
      <p class="cap2">原因：竞彩官方公开页只有比分、半场比分、伤停与球员名单，不含过程数据；免费可得的 xG 源与竞彩队名映射尚未接通。本页用「半场结构 + 主客分离 + 交手中低比分频率」替代口径，缺口部分不算、不编数。</p>
    </div>
  </div>
</section>"""

    # ④ 基本面
    inj = m['intel'].get('inj') or []
    inj_rows = [[esc(i['team']), esc(i['name']), esc(i.get('pos') or ''), f"{i.get('apps', 0)} 场", esc(i['kind'])] for i in inj] or [['—', '两边伤停名单均为空', '—', '—', '—']]
    homes = [i for i in inj if i['team'] == m['home']]
    aways = [i for i in inj if i['team'] == m['away']]
    inj_note = f"名单口径：{esc(m['home'])} {len(homes)} 人、{esc(m['away'])} {len(aways)} 人（只收官方伤停与停赛表，不含赛前热身临时缺阵）。"
    baseb = f"""
<section class="s">
  <h3><i>04</i>基本面 <span class="x">阵容伤停 · 赛程战意 · 状态底子</span></h3>
  <div class="col2">
    <div>
      <div class="cap">伤停与缺阵</div>
      {rows_table(['球队', '球员', '位置', '本季出场', '性质'], inj_rows)}
      <p class="cap2" style="margin-top:6px">{inj_note}</p>
      <div class="cap" style="margin-top:16px">赛程与战意</div>
      <p class="body">{esc(m['intel'].get('note') or '—')}</p>
    </div>
    <div>
      <div class="cap">两队近 {th['n']} 场（左旧 → 右新）</div>
      {rows_table(['日期', '主队近况', '半场'], [[esc(r['d']), esc(r['m']), esc(r.get('ht') or '')] for r in th['results']])}
      <div class="cap" style="margin-top:12px">客队近况</div>
      {rows_table(['日期', '客队近况', '半场'], [[esc(r['d']), esc(r['m']), esc(r.get('ht') or '')] for r in ta['results']])}
    </div>
  </div>
</section>"""

    # ⑤ 盘口定价与变盘
    pool = o.get('pool') or []
    pool_rows = []
    for r in pool[:12]:
        pct_pool = {x['s']: x for x in m['top']}
        tag = '主推首选' if r['s'] == v['first_score'] else ('主推次选' if r['s'] == v['second_score'] else
              ('防冷比分' if r['s'] == v['guard_score'] else '—'))
        t = pct_pool.get(r['s'])
        ev = sign(t['ev'], 2, '') if (t and 'ev' in t) else '—'
        pool_rows.append([f"<b>{esc(r['s'])}</b>", f(r['odd'], 2), pct(r['p']), esc(r['dir']), ev, tag])

    spf_rows = [[esc(r['t']), f(r['h'], 2), f(r['d'], 2), f(r['a'], 2)] for r in (o.get('spf') or [])]
    hand_rows = [[esc(r['t']), f(r['h'], 2), f(r['d'], 2), f(r['a'], 2), esc(r.get('line') or '')] for r in (o.get('hand') or [])]

    move_html = ""
    if pool or spf_rows:
        latest = o.get('latest_spf') or {}
        open_ = o.get('open_spf') or {}
        latestp = latest.get('p') or [0, 0, 0]
        notes = "".join(f"<li>{esc(n)}</li>" for n in (o.get('notes') or []))
        gl = o.get('goals') or {}
        goals_rows = []
        if gl:
            for i in range(7):
                chg = (gl['odds_new'][i] - gl['odds_old'][i])
                goals_rows.append([f"{i} 球", f(gl['odds_old'][i], 2), f(gl['odds_new'][i], 2),
                                   sign(chg, 2, '') if abs(chg) >= 0.01 else '—',
                                   pct(gl['p_old'][i]), pct(gl['p_new'][i]),
                                   sign(gl['model'][i] - gl['p_new'][i], 1, 'pp')])
        ht = o.get('htft') or {}
        ht_rows = []
        if ht:
            raw = [(m['payout'] / 100.0) / r['new'] for r in ht['rows']]
            tot = sum(raw) or 1.0
            for r, w in zip(ht['rows'], raw):
                ht_rows.append([esc(r['k']), f(r['old'], 2), f(r['new'], 2),
                                sign(r['chg'], 2, '') if abs(r['chg']) >= 0.01 else '—', pct(w / tot * 100)])
        move_html = f"""
<section class="s">
  <h3><i>05</i>盘口定价与变盘 <span class="x">三层定价交叉 · 波胆池 · 时间轴 · 半全场剧本</span></h3>
  <div class="col2">
    <div>
      <div class="cap">固定奖金时间轴（胜平负，返奖率 {f(m['payout'])}% 归一）</div>
      {rows_table(['时点', '主胜', '平', '客胜'], spf_rows) if spf_rows else '<p class="body">本场只有开盘一次快照，没有位移可读。</p>'}
      <div class="cap" style="margin-top:14px">让球（{handtxt}）时间轴</div>
      {rows_table(['时点', '让胜', '让平', '让负', '盘口'], hand_rows) if hand_rows else '<p class="body">—</p>'}
      <p class="cap2">开盘 {f(open_.get('odds', [0,0,0])[0],2)}/{f(open_.get('odds', [0,0,0])[1],2)}/{f(open_.get('odds', [0,0,0])[2],2)}
        → 最新 {f(latest.get('odds', [0,0,0])[0],2)}/{f(latest.get('odds', [0,0,0])[1],2)}/{f(latest.get('odds', [0,0,0])[2],2)}；
        去水后最新 {pct(latestp[0])} / {pct(latestp[1])} / {pct(latestp[2])}。</p>
      {"".join([f'<ul class="notes">{notes}</ul>']) if notes else ""}
    </div>
    <div>
      <div class="cap">波胆池：定价错在哪（按赔率从低到高）</div>
      {rows_table(['比分', '定价', '隐含', '方向', '溢价', '与模型结论'], pool_rows) if pool_rows else '<p class="body">本批未采到比分池定价。</p>'}
      <p class="cap2">溢价 = 模型概率 × 定价 − 1；为正表示这一格模型估值高于定价。溢价为负的格子说明定价偏虚，不做主推。</p>
    </div>
  </div>
  <div class="col2" style="margin-top:18px">
    <div>
      <div class="cap">总进球定价 vs 模型（初盘 {esc(gl.get('t_old','')) } → 最新 {esc(gl.get('t_new',''))}）</div>
      {rows_table(['进球数', '初盘', '最新', '变化', '定价隐含（初）', '定价隐含（新）', '模型 − 定价'], goals_rows) if goals_rows else '<p class="body">—</p>'}
    </div>
    <div>
      <div class="cap">半全场：剧本的方向（初盘 {esc(ht.get('t_old',''))} → 最新 {esc(ht.get('t_new',''))}）</div>
      {rows_table(['半场/全场', '初盘', '最新', '变化', '隐含'], ht_rows) if ht_rows else '<p class="body">—</p>'}
      <div class="cap" style="margin-top:14px">剧本切换条件</div>
      <ul class="notes">
        <li>上半场：比分往 2-1 / 2-2 走：模型大 2.5 球 {pct(m['over']['2.5'])}、双方进球 {pct(m['btts'])}，两队都能进球的场次里，零封是最先被排除的结果。</li>
        <li>半场 0-0：拿模型平局 {pct(m['p'][1])} 与定价 {pct(m['mk'][1])} 对照，谁高谁更怕闷。</li>
        <li>客队先：定价最热的那格是 {esc(k['fav'])}（{pct(k['fav_mk'])}），防冷比分 {esc(v['guard_score'])}；若先进球后仍要防被拖回平局，模型平局 {pct(m['p'][1])} 是唯一能救回的格子。</li>
        <li>主队先：让球（{handtxt}）模型 {pct(hp[0])} vs 定价 {pct(hmk[0])}，模型比定价更信任这个剧本；追主队要接受赢球不穿盘的结果。</li>
      </ul>
    </div>
  </div>
</section>"""

    # ⑥ 推演闭环
    ex = "".join(f"<tr><td>{esc(x['k'])}</td><td><span class='pill r'>{esc(x['kind'])}</span></td><td>{esc(x['why'])}</td></tr>"
                 for x in (st.get('exclude') or []))
    rich = "".join(f"<tr><td>{esc(x['k'])}</td><td><span class='pill a'>{esc(x['kind'])}</span></td><td>{esc(x['why'])}</td></tr>"
                   for x in (st.get('rich') or []))
    conclb = f"""
<section class="s">
  <h3><i>06</i>推演闭环 <span class="x">定格局 → 定总量 → 跑矩阵 → 做排除 → 出结论</span></h3>
  <div class="col2">
    <div>
      <ol class="steps">
        <li><b>定格局</b><span>胜平负方向</span><p>{esc(st['pattern'])}</p></li>
        <li><b>定总量</b><span>总进球区间</span><p>{esc(st['total'])}</p></li>
        <li><b>跑矩阵</b><span>概率排序</span><p>{esc(st['matrix'])}</p></li>
        <li><b>做排除</b><span>情景证伪</span><p>把与方向、总量相悖的比分先划掉，剩下的才是候选；被定价严重高估的格子一并降权。见右侧清单。</p></li>
      </ol>
    </div>
    <div>
      <div class="cap">排除与降权清单</div>
      <table><tbody>{ex}{rich}</tbody></table>
      <p class="cap2">总进球 5 球以上模型合计 {pct(st.get('tail5', 0))}；平局一格 {pct(st.get('draw_p', 0))}。与主推/次选/防冷重复的比分已从降权清单里删掉。</p>
      <div class="cap" style="margin-top:14px">防冷触发条件</div>
      <p class="body">模型推 <b>{esc(v['first'])}</b>（{pct(v['first_p'])}），定价最热是 <b>{esc(k['fav'])}</b>（{pct(k['fav_mk'])}），
        冷门指数 <b>{f(k['index'], 0)}</b>＝定价最热那一格之外、模型给出的概率之和。分歧 {f(abs(c['maxpp']))} 个百分点：
        {esc('超过 15，先假定我方数据有缺口，只做方向参考' if abs(c['maxpp']) >= 15 else '在可控范围内，方向可用、幅度打折')}。
        若 {esc(k['fav'])} 站住，比分大概率是 {esc(v['guard_score'])}；反过来若这一格被拖住，模型最可能接上的是 {esc(k['main_cold'])} {pct(k['main_cold_p'])}。</p>
    </div>
  </div>
</section>"""

    # ⑦ 外媒 × AI
    sm = (m.get('ext') or {}).get('sm') or {}
    af = (m.get('ext') or {}).get('af') or {}
    extb = f"""
<section class="s">
  <h3><i>07</i>外媒 × AI <span class="x">公开赛前预报 · 数据接口算法 · 后台模型 · 官方定价</span></h3>
  {rows_table(['来源', '方向', '给出的结论 / 原文摘要'], [
    ['后台模型 v2.10', esc(c['model_dir']), f"主 {pct(m['p'][0])} / 平 {pct(m['p'][1])} / 客 {pct(m['p'][2])}；比分最靠前 {esc(m['top'][0]['s'])}（{pct(m['top'][0]['p'])}）"],
    ['官方固定奖金（去水）', esc(c['market_dir']), f"主 {pct(m['mk'][0])} / 平 {pct(m['mk'][1])} / 客 {pct(m['mk'][2])}；返奖率 {f(m['payout'])}%"],
    ['公开赛前预报（Sports Mole）', esc(sm.get('predicted') or '—'), esc(sm.get('note') or '—')],
    ['数据接口算法（API-Football）', esc(af.get('predicted_dir') or '—'), esc(af.get('note') or '免费层只给方向，百分比字段为坏值不采信')],
  ])}
  <div class="col2" style="margin-top:14px">
    <div>
      <div class="cap">预报方给的阵容</div>
      <p class="body">{esc(sm.get('lineup') or '未提供')}</p>
      <p class="cap2">预计首发为预报方口径；与官方伤停名单冲突时以赛前公布名单为准。</p>
    </div>
    <div>
      <div class="cap">四口径一致度</div>
      <p class="body">同向 <b>{c['agree']}/3</b>（市场 / 公开预报 / 接口算法三者与模型同向的条数）。
        外部两源只做参照系：公开预报给的是比分与理由，接口算法只给方向，它们不改变模型结论，只用来标出「三家站成几排」。</p>
      <p class="cap2">来源：{esc(sm.get('url') or '—')}</p>
    </div>
  </div>
</section>"""

    # 一句话结论
    tail = f"""
<div class="oneline">
  <b>一句话结论</b>
  <p>{esc(m['home'])} 对 {esc(m['away'])}：模型 {esc(c['model_dir'])} {pct(max(m['p']))}，
    首选比分 {esc(v['first_score'])}；信心 {c['total']}/100（{esc(c['grade'])}）；
    最大风险是模型与定价差 {f(abs(c['maxpp']))}pp 这件事本身，防冷看 {esc(v['guard_score'])}。</p>
  <div class="warns">{"".join(f"<div>⚠️ {esc(w)}</div>" for w in (m.get('warn') or []))}</div>
</div>"""

    # 页末：综合分析
    final = f"""
<div class="final">
  <div class="fhd"><span>综合分析</span><i>页末 · 推演闭环 / 四口径对照 / 一句话结论</i></div>
  {conclb}{extb}{tail}
</div>"""

    return f'<section class="match" id="m{idx}">{head}{concl}{hcap}{mathb}{techb}{baseb}{move_html}{final}</section>'


# ── 整页 ──────────────────────────────────────────────
CSS = """
:root{--bg:#F5F0E6;--bg2:#FBF7EE;--panel:#FFFDF7;--ink:#221E18;--muted:#6A5E50;--dim:#8C7F6E;
  --line:rgba(60,45,30,.16);--line2:rgba(60,45,30,.34);--brick:#8C3B23;--ochre:#A8762F;--navy:#3D5064;
  --red:#9E2B21;--green:#3F6B4A;
  --mono:"IBM Plex Mono","JetBrains Mono",ui-monospace,Consolas,monospace;
  --sans:"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",system-ui,sans-serif;
  --serif:"Songti SC","Source Han Serif SC","Noto Serif CJK SC",Georgia,serif}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.75 var(--sans)}
.wrap{max-width:1180px;margin:0 auto;padding:0 34px 70px}
/* 封面 */
.cover{padding:56px 0 30px;border-bottom:2px solid var(--ink);margin-bottom:30px}
.cover .kick{font-family:var(--mono);font-size:11px;letter-spacing:.3em;color:var(--brick);margin-bottom:14px}
.cover h1{font-family:var(--serif);font-size:46px;line-height:1.2;margin:0 0 10px;letter-spacing:.01em}
.cover .sub{font-family:var(--serif);font-size:19px;color:#4A3E33;margin-bottom:20px}
.cover .meta{font-family:var(--mono);font-size:11.5px;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:26px 0 6px}
.kpi{border-left:2px solid var(--line2);padding-left:14px}
.kpi b{display:block;font-family:var(--mono);font-size:30px;line-height:1.1;color:var(--brick)}
.kpi span{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;color:var(--dim)}
.kpi i{display:block;font-style:normal;font-size:12px;color:var(--muted);margin-top:4px}
.toc{display:grid;grid-template-columns:repeat(2,1fr);gap:4px 26px;margin-top:24px}
.toc a{display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px dotted rgba(60,45,30,.22);
  color:var(--ink);text-decoration:none;font-size:13.5px}
.toc a:hover{color:var(--brick)}
.toc a span{font-family:var(--mono);font-size:11px;color:var(--dim)}
/* 总览表 */
h2.sec{font-family:var(--serif);font-size:24px;margin:34px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line2)}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin:8px 0 4px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid rgba(60,45,30,.10);vertical-align:top}
thead th{font-family:var(--mono);font-size:10px;letter-spacing:.1em;color:var(--dim);font-weight:400;
  border-bottom:1px solid var(--line2);white-space:nowrap}
tbody tr:hover td{background:rgba(140,59,35,.035)}
table.kv th{width:44%;font-family:var(--mono);font-size:11px;color:var(--muted);font-weight:400;letter-spacing:.02em}
table.kv td{font-family:var(--mono);font-size:12px}
.num,.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
/* 单场 */
.match{margin-top:46px;padding-top:26px;border-top:2px solid var(--ink);break-after:page}
.final{margin:26px 0 0;border:1px solid var(--line2);border-left:4px solid var(--brick);background:#FBF6EC;padding:18px 20px 6px}
.final .fhd{display:flex;align-items:baseline;gap:12px;border-bottom:1px solid var(--line2);padding-bottom:8px;margin-bottom:6px}
.final .fhd span{font-family:var(--serif);font-size:19px;font-weight:700;color:var(--ink);letter-spacing:.02em}
.final .fhd i{font-style:normal;font-family:var(--mono);font-size:10.5px;color:var(--dim);letter-spacing:.06em}
.final .card{background:var(--panel)}
.mhead .mno{display:flex;gap:16px;flex-wrap:wrap;font-family:var(--mono);font-size:11px;letter-spacing:.1em;color:var(--dim)}
.mhead h2{font-family:var(--serif);font-size:38px;line-height:1.2;margin:10px 0 12px;font-weight:700}
.mhead h2 em{font-style:normal;color:var(--brick);font-size:19px;margin:0 14px;vertical-align:4px}
.msum{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap;
  padding-bottom:14px;border-bottom:1px solid var(--line)}
.msum b{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;color:var(--dim);margin-right:6px}
.msum .sep{color:var(--line2);margin:0 8px}
.conf{text-align:right}
.cnum{font-family:var(--mono);font-size:34px;line-height:1;color:var(--brick)}
.cgrade{font-family:var(--mono);font-size:12px;color:var(--muted);margin-left:8px;letter-spacing:.08em}
.cdim{display:block;font-family:var(--mono);font-size:9.5px;color:var(--dim);letter-spacing:.14em;margin-top:4px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0 20px}
.vcard{border:1px solid var(--line);background:var(--panel);border-top:2px solid var(--brick);padding:13px 15px}
.vcard.v2{border-top-color:var(--ochre)} .vcard.v3{border-top-color:var(--navy)}
.vcard .vt{display:block;font-family:var(--mono);font-size:10px;letter-spacing:.16em;color:var(--dim);margin-bottom:6px}
.vcard b{display:block;font-family:var(--serif);font-size:24px;line-height:1.3}
.vcard .vs{display:block;font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-top:6px}
/* 段 */
.s{margin:26px 0 0;padding-top:18px;border-top:1px solid var(--line)}
.s h3{font-family:var(--mono);font-size:12px;letter-spacing:.16em;color:var(--brick);margin:0 0 14px;
  display:flex;align-items:center;gap:10px;font-weight:400}
.s h3 i{font-style:normal;font-family:var(--mono);font-size:10px;color:var(--dim);letter-spacing:.06em;
  border:1px solid var(--line);padding:1px 6px}
.s h3 .x{margin-left:auto;font-size:10px;color:var(--dim);letter-spacing:.08em}
.col2{display:grid;grid-template-columns:1fr 1fr;gap:26px}
.col2>*{min-width:0}
.cap{font-family:var(--mono);font-size:11px;letter-spacing:.1em;color:var(--brick);margin:0 0 8px}
.cap2{font-size:12px;color:var(--muted);line-height:1.7;margin:8px 0 0}
.body{font-size:13px;line-height:1.78;margin:0}
/* 条形 */
.bar{display:grid;grid-template-columns:52px 1fr 104px;align-items:center;gap:10px;margin:6px 0}
.bar .bl{font-family:var(--mono);font-size:11.5px;color:var(--muted)}
.bar .bt{position:relative;display:block;height:18px;background:rgba(60,45,30,.08)}
.bar .bt .fill{position:absolute;left:0;top:0;bottom:0;display:block}
.fill.h{background:var(--brick)} .fill.d{background:var(--ochre)} .fill.a{background:var(--navy)}
.bar .bt .ghost{position:absolute;top:0;bottom:0;
  background:repeating-linear-gradient(45deg,rgba(60,45,30,.42),rgba(60,45,30,.42) 3px,transparent 3px,transparent 7px)}
.bar .bt .mark{position:absolute;top:-3px;bottom:-3px;width:2px;background:#221E18;opacity:.72}
.bar .bv{font-family:var(--mono);font-size:11px;color:var(--ink);text-align:right;line-height:1.25}
.bar .bv b{display:block}
.bar .bv i{display:block;font-style:normal;font-size:10px;color:var(--dim)}
/* 矩阵 */
.mx{display:grid;grid-template-columns:26px repeat(7,1fr);gap:1px;max-width:460px}
.mxh{font-family:var(--mono);font-size:10px;color:var(--dim);display:flex;align-items:center;justify-content:center}
.mxc{font-family:var(--mono);font-size:11px;text-align:center;padding:9px 0;border:1px solid rgba(255,255,255,.55)}
/* 柱图 */
.gchart{display:flex;align-items:flex-end;gap:8px;height:150px;margin:6px 0 4px}
.gcol{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:4px;height:100%}
.gcol i{display:block;width:100%;background:linear-gradient(180deg,var(--brick),#D2A78A)}
.gcol .gv{font-family:var(--mono);font-size:10px;color:var(--muted)}
.gcol .gl{font-family:var(--mono);font-size:10px;color:var(--dim)}
.gax{font-family:var(--mono);font-size:10px;color:var(--dim)}
/* 小卡 */
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.grid4.tight .mini{padding:9px 10px}
.mini{border:1px solid var(--line);background:var(--panel);padding:10px 12px}
.mini span{display:block;font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;color:var(--dim)}
.mini b{display:block;font-family:var(--mono);font-size:20px;line-height:1.4}
.mini i{font-style:normal;font-size:10.5px;color:var(--muted)}
/* 列表 */
ul.gaps{list-style:none;margin:0;padding:0}
ul.gaps li{display:flex;gap:9px;align-items:baseline;padding:6px 0;border-bottom:1px dotted rgba(60,45,30,.18);font-size:12px}
ul.gaps b{font-family:var(--mono);font-size:9.5px;color:var(--red);border:1px solid rgba(158,43,33,.32);
  padding:1px 5px;background:rgba(158,43,33,.05);white-space:nowrap}
ul.gaps span{font-family:var(--mono);font-size:11px;color:var(--ink);white-space:nowrap}
ul.notes{margin:8px 0 0;padding-left:18px;font-size:12px;color:var(--muted);line-height:1.75}
ul.notes li{margin:3px 0}
ol.steps{list-style:none;margin:0;padding:0;counter-reset:st}
ol.steps li{border-bottom:1px solid var(--line);padding:10px 0 12px}
ol.steps li b{font-family:var(--serif);font-size:16px;display:block}
ol.steps li span{font-family:var(--mono);font-size:10px;letter-spacing:.1em;color:var(--dim)}
ol.steps li p{margin:6px 0 0;font-size:13px;line-height:1.78}
/* 结论条 */
.oneline{margin:22px 0 0;border:1px solid var(--line2);background:var(--panel);padding:16px 18px}
.oneline>b{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;color:var(--brick)}
.oneline p{margin:8px 0 0;font-size:13.5px;line-height:1.8}
.warns{margin-top:10px;font-size:12px;color:var(--muted)}
.warns div{padding:4px 0}
/* 附录 */
.appendix{margin-top:56px;padding-top:26px;border-top:2px solid var(--ink);font-size:12.5px;color:var(--muted)}
.appendix h3{font-family:var(--mono);font-size:11px;letter-spacing:.14em;color:var(--brick);margin:20px 0 8px;font-weight:400}
.appendix ol{padding-left:20px;line-height:1.8}
.pill{font-family:var(--mono);font-size:9.5px;letter-spacing:.06em;padding:1px 5px;border:1px solid var(--line2);white-space:nowrap}
.pill.r{color:var(--red);border-color:rgba(158,43,33,.34);background:rgba(158,43,33,.06)}
.pill.a{color:#8A5A17;border-color:rgba(168,118,47,.36);background:rgba(168,118,47,.08)}
.pill.g{color:var(--green);border-color:rgba(63,107,74,.34)}
.foot{margin-top:34px;padding-top:14px;border-top:1px solid var(--line);font-family:var(--mono);
  font-size:10px;color:var(--dim);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
@media (max-width:880px){
  .wrap{padding:0 18px 50px}
  .col2{grid-template-columns:1fr;gap:18px}
  .grid3,.grid4,.kpis{grid-template-columns:1fr 1fr}
  .cover h1{font-size:34px}
  .mhead h2{font-size:28px}
}
@media print{
  @page{size:A4;margin:14mm}
  body{background:#fff;font-size:10.5pt}
  .wrap{max-width:none;padding:0}
  .match{page-break-before:always;border-top:none;padding-top:0;margin-top:0}
  .cover{page-break-after:always}
  .col2{grid-template-columns:1fr 1fr}
  .vcard,.mini,.oneline{background:#fff}
  a{color:inherit;text-decoration:none}
}
"""


def render(data: dict) -> str:
    global DATARHO
    meta = data["meta"]
    ms = data["matches"]
    DATARHO = meta["rho"]
    day = meta["date"]
    dd = f"{day[:4]}.{day[4:6]}.{day[6:]}"
    avg_conf = sum(x["conf"]["total"] for x in ms) / len(ms)
    n_disp = sum(1 for x in ms if abs(x["conf"]["maxpp"]) >= 10)
    n_agree3 = sum(1 for x in ms if x["conf"]["agree"] == 3)

    toc = "".join(
        f'<a href="#m{i}"><b>{esc(x["no"])}　{esc(x["home"])} vs {esc(x["away"])}</b>'
        f'<span>{esc(x["kick"])} · {x["conf"]["total"]} · {esc(x["conf"]["grade"].split(" · ")[0])}</span></a>'
        for i, x in enumerate(ms))

    overview_rows = []
    for x in ms:
        e = max(range(3), key=lambda i: abs(x["edge"][i]))
        overview_rows.append([
            f'<b>{esc(x["no"])}</b>', f'{esc(x["home"])} vs {esc(x["away"])}<br><span class="dim2">{esc(x["league"])} · {esc(x["kick"])}</span>',
            f'{f(x["p"][0])} / {f(x["p"][1])} / {f(x["p"][2])}',
            f'{f(x["mk"][0])} / {f(x["mk"][1])} / {f(x["mk"][2])}',
            f'{esc(DIRS[e])} {sign(x["edge"][e])}',
            f'{x["conf"]["total"]}', f'{f(x["cold"]["index"], 0)}',
        ])
    overview = rows_table(['场次', '对阵 / 开赛', '模型 主/平/客', '定价 主/平/客（去水）', '最大偏差', '信心', '冷门'], overview_rows)

    body = "".join(section_match(x, i) for i, x in enumerate(ms))

    appendix = f"""
<section class="appendix">
  <h2 class="sec">附 · 方法论、口径与免责</h2>
  <h3>一、进球期望（λ）两条路，再取一个值</h3>
  <ol>
    <li>实际数据法：分开算主队主场、客队客场的攻防效率；样本不足（≤3 场）时按样本量权重混入近十场，避免前三轮就把一支球队定死。</li>
    <li>定价反推法：从官方固定奖金反解出一条隐含的比分分布，得到第二条 λ。两条路差得多，说明市场与赛果之间存在叙事溢价，或者我方样本有缺口。</li>
    <li>取综合 λ 后按状态、交锋、伤停做很小的修正（一般不超过 ±0.25），修正越大越说明基础数据有偏。</li>
  </ol>
  <h3>二、概率与比分</h3>
  <p>用泊松分布做 2 万次蒙特卡洛抽样，得到胜平负、让球、总进球与比分矩阵，抽样误差控制在 0.5 个百分点以内，所以正文百分比保留一位小数。所有结果只统计 90 分钟常规时间，加时与点球不计。</p>
  <h3>三、Dixon-Coles 低比分校准</h3>
  <p>独立泊松假设两队进球互不相干，会低估 0-0 / 1-0 / 0-1 / 1-1 这类低比分。本页用相关系数 ρ = {f(DATARHO, 2)} 对四格加权后再整表归一，只用于展示「低比分被拉起多少」，不替换官方模型 2 万次抽样作为主口径；矩阵与胜平负给了三种口径的交叉核对。</p>
  <h3>四、去水与溢价</h3>
  <p>官方固定奖金三项隐含概率之和通常超过 100%，超出部分是结构成本（每场不同）。按比例归一后得到「去水后概率」，才能与模型概率放在同一把尺子上比较。溢价 EV = 模型概率 × 固定奖金 − 1，为正表示这一格模型估值高于定价，但溢价为正不等于值得下注，样本薄时它同样会错。</p>
  <h3>五、信心指数五项</h3>
  <ul class="notes">
    <li>样本厚度（20 分）：主客分离样本场数，两场以内只能算参考。</li>
    <li>双法收敛（20 分）：两条 λ 的相对差，差得多说明两套证据打架。</li>
    <li>三方一致（25 分）：官方定价方向、公开预报、接口算法三条线里，有几条与模型同向。</li>
    <li>分歧可控（25 分）：胜平负最大偏差，超过 10 个百分点按「先假定我方有缺口」处理，扣分。</li>
    <li>比分集中（10 分）：Top3 比分概率之和，集中度低意味着结果更随机、比分推荐更不可靠。</li>
  </ul>
  <p>怎么读总分：A（≥78）结构与证据互相印证，可作为方向主参考；B（66–77）方向可信但幅度要打折；C（52–65）只能当一种视角；D（&lt;52）证据不足，本份只做记录不做参考。</p>
  <h3>六、冷门指数</h3>
  <p>定价最热那一格之外，模型给出的概率之和。数值越大，说明市场押的那一头越站不住，越值得留一手防守比分。</p>
  <h3>七、本批口径</h3>
  <ul class="notes">
    <li>覆盖 {len(ms)} 场，日期 {dd}，全部为公开赛程与公开定价数据；后台模型 v2.10。</li>
    <li>外部预报只取公开赛前预报的比分与理由，以及数据接口算法的方向；接口免费层的百分比字段有坏值（固定 10/45/45、进球 −2.5），不采信、不展示。</li>
    <li>变盘时间轴取自竞彩官网「固定奖金」栏的历史快照；只有采到 ≥2 个时点的场次才给位移判读，其余只写「市场一开始就这么看」。</li>
    <li>让球盘口若临场调整，让球一侧的偏差结论需要重算；本份不含临场首发变动后的重算。</li>
    <li>市场侧大小球盘口、xG/xGA/npxG、PPDA、射门射正角球、场地天气、裁判尺度目前都未接入，相关结论只用模型口径或标注为缺口。</li>
  </ul>
  <h3>免责与使用范围</h3>
  <p>本资料为内部复盘材料，用于检验模型口径与记录判断过程，不作公开投放、不对外销售、不作为任何形式的购买建议。文中百分比均为模型估值或定价隐含概率，不是承诺；足球比赛受红牌、伤退、天气、判罚等随机因素影响，任何概率都可能不成立。请理性看球。数据来源：公开赛果数据（竞彩官方定价、公开赛程与伤停、公开赛前预报）。生成 {esc(meta['stamp'])} · 内部资料。</p>
</section>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{dd} {len(ms)} 场全维度推演 · 阿飞·赛博聊球</title>
<style>{CSS}</style>
</head><body>
<div class="wrap">
<section class="cover">
  <div class="kick">付费内部资料 · 全维度推演 · 海报款</div>
  <h1>{dd} 六场</h1>
  <div class="sub">盘口结构 · 数理模型 · 高阶数据 · 推演闭环</div>
  <div class="meta">生成 {esc(meta['stamp'])} · 模型 {esc(meta['model'])} · 抽样 {meta['samples']:,} 次 · ρ = {f(meta['rho'], 2)}
    · 每场按「门槛 → 数理 → 高阶 → 基本面 → 盘口 → 闭环 → 外媒」七段顺序读到底</div>
  <div class="kpis">
    <div class="kpi"><b>{len(ms)}</b><span>覆盖场次</span><i>{' / '.join(dict.fromkeys(x['league'] for x in ms))}</i></div>
    <div class="kpi"><b>{avg_conf:.0f}</b><span>平均信心指数</span><i>满分 100 · 五维加权</i></div>
    <div class="kpi"><b>{n_disp}</b><span>场次分歧 ≥10pp</span><i>模型与定价的最大差距</i></div>
    <div class="kpi"><b>{n_agree3}</b><span>场次三方同向</span><i>模型 / 定价 / 外部源</i></div>
  </div>
  <div class="toc">{toc}</div>
</section>

<h2 class="sec">总览 · 六场一页看完</h2>
{overview}
<p class="cap2">定价为官方固定奖金去水后的隐含概率（按返奖率归一）。冷门指数＝定价最热那一格之外、模型给出的概率之和，数字越大，市场热的那头越站不住。
  最大偏差取胜平负三项里绝对值最大的一格，偏差超过 15 个百分点时按纪律先假定我方样本有缺口，只做方向参考。</p>

{body}

{appendix}

<div class="foot"><span>阿飞 · 赛博聊球 · 内部资料 · {dd} · 六场全维度推演</span>
  <span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div>
</div>
</body></html>
"""


DATARHO = -0.08


def main() -> None:
    ap = argparse.ArgumentParser(description="海报款静态内部资料（无 JS）")
    ap.add_argument("--model", default=None, help="模型文本路径")
    ap.add_argument("--date-dir", default=None, help="输出日期目录名 YYYYMMDD")
    ap.add_argument("--out", default=None, help="输出 HTML 路径")
    a = ap.parse_args()

    if a.model:
        model_path = Path(a.model).resolve()
        date_tag = a.date_dir or model_path.stem.split("_")[2][:8]
    else:
        bdir = Path.cwd() / "state" / "batch"
        cands = sorted(bdir.glob("_model_*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not cands:
            raise SystemExit("找不到模型文本，请用 --model 指定")
        model_path = cands[0]
        date_tag = a.date_dir or model_path.stem.split("_")[2][:8]

    data = pc.build(model_path, date_tag)
    html = render(data)
    out = Path(a.out) if a.out else (Path.cwd() / "📝文章" / date_tag / f"六场全维度推演_海报版_{date_tag}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="\n").write(html)
    print(f"✅ {out} {out.stat().st_size / 1024:.0f}KB · {len(data['matches'])} 场 · 无 JS")


if __name__ == "__main__":
    main()
