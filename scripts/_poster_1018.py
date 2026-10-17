"""10/18 周日「全维度推演」海报版 HTML（25 场，可按模型完整度降级）"""
import html
import json
import re
from collections import defaultdict

SLATE = r"I:\阿飞说球\state\batch\_slate.json"
FULL = r"I:\阿飞说球\state\batch\_model_20261018_sun_full.txt"
EXT = r"I:\阿飞说球\state\records\_ext_20261018.json"
OUT = r"I:\阿飞说球\📝文章\20261018\周日全维度推演_海报版_20261018.html"

sl = json.load(open(SLATE, encoding="utf-8"))
rows = []
for g in sl["value"]["matchInfoList"]:
    for m in g.get("subMatchList", []):
        n = str(m.get("matchNum"))
        if not n.startswith("7"):
            continue
        t = m.get("matchTime") or ""
        day = "10/18" if int(t[:2]) >= 12 else "10/19"
        rows.append({
            "no": "周日" + n[1:],
            "home": m.get("homeTeamAbbName"), "away": m.get("awayTeamAbbName"),
            "league": m.get("leagueAbbName"), "kick": day + " " + t[:5],
            "mid": m.get("matchId"),
        })
ORDER = {r["no"]: i for i, r in enumerate(rows)}

txt = open(FULL, encoding="utf-8").read()
MODEL = {}
for b in re.split(r"={70,}", txt):
    m = re.search(r"(周[日六]\d{3})\s+(\S+) vs (\S+)", b)
    if not m:
        continue
    key = m.group(1)
    sp = re.search(r"胜平负\s+模型\s+([\d.]+)% / +([\d.]+)% / +([\d.]+)%\s+市场\(去水\)\s+([\d.]+)% / +([\d.]+)% / +([\d.]+)%", b)
    if not sp:
        MODEL[key] = {"na": True, "note": (re.search(r"备注：(.*)", b) or [None, ""])[1] if re.search(r"备注：(.*)", b) else ""}
        continue
    ed = re.search(r"Edge\(模型-市场\)\s*主\s*([+\-\d.]+)pp\s*平\s*([+\-\d.]+)pp\s*客\s*([+\-\d.]+)pp", b)
    lam = re.search(r"综合 λ\s+([\d.]+)\s+([\d.]+)", b)
    ou = re.search(r"大2\.5 ([\d.]+)%\s+大3\.5 ([\d.]+)%\s+双方进球 ([\d.]+)%", b)
    bg = re.search(r"固定奖金\s+([\d.]+) / ([\d.]+) / ([\d.]+)", b)
    st = re.search(r"胜率\(不含平\)：主 ([\d.]+)% / 客 ([\d.]+)%", b)
    top = re.findall(r"^\s+(\d-\d)\s+([\d.]+)%", b, re.M)
    note = re.search(r"备注：(.*)", b)
    handicap = re.search(r"让球\s*([+\-]?\d+)", b)
    MODEL[key] = {
        "mc": [float(x) for x in sp.groups()[:3]],
        "mk": [float(x) for x in sp.groups()[3:]],
        "edge": [float(x) for x in ed.groups()] if ed else [0.0, 0.0, 0.0],
        "lam": [float(lam.group(1)), float(lam.group(2))] if lam else [0.0, 0.0],
        "ou": [float(ou.group(1)), float(ou.group(3))] if ou else [0.0, 0.0],
        "bonus": [float(x) for x in bg.groups()] if bg else None,
        "st": [float(st.group(1)), float(st.group(2))] if st else None,
        "top": [(a, float(c)) for a, c in top[:8]],
        "handicap": handicap.group(1) if handicap else "",
        "note": note.group(1) if note else "",
        "na": False,
    }

ext = json.load(open(EXT, encoding="utf-8"))
EXTM = defaultdict(list)
for it in ext.get("items", []):
    EXTM[(it.get("home"), it.get("away"))].append(it)

# 匹配外部记录：按队名模糊
def ext_for(r):
    out = []
    for (h, a), lst in EXTM.items():
        if not h or not a:
            continue
        if h[:2] in r["home"] or r["home"][:2] in h:
            out += lst
    return out


def fmt(x):
    return "%.1f" % x


def dir_of(p):
    return ["主胜", "平", "客胜"][max(range(3), key=lambda i: p[i])]


def confidence(m, exts):
    score = 0
    score += 20 if m["lam"][0] else 10
    diff = abs(m["mc"][0] - m["mk"][0])
    score += 20 if diff < 3 else (14 if diff < 6 else (8 if diff < 10 else 3))
    mx = max(abs(e) for e in m["edge"])
    score += 25 if mx < 5 else (18 if mx < 10 else (10 if mx < 15 else 4))
    dirs = [dir_of(m["mc"]), dir_of(m["mk"])] + [e.get("predicted_dir") for e in exts if e.get("predicted_dir")]
    agree = sum(1 for d in dirs[1:] if d == dirs[0])
    score += int(25 * agree / max(1, len(dirs) - 1))
    score += 10 if m["top"] and sum(p for _, p in m["top"][:3]) >= 20 else 6
    return min(100, max(0, score))


def grade(s):
    if s >= 78:
        return "A · 主参考"
    if s >= 66:
        return "B · 打折用"
    if s >= 52:
        return "C · 一种视角"
    return "D · 只做记录"


def bars(m, exts):
    h = []
    h.append('<div class="cap">胜平负 · 固定奖金 %s（模型 / 定价去水同尺）</div>'
             % (" / ".join("%.2f" % b for b in m["bonus"]) if m["bonus"] else "未启用"))
    for i, lab in enumerate(["主胜", "平", "客胜"]):
        h.append(
            '<div class="bar"><span class="bl">%s</span>'
            '<span class="bt"><i class="fill h" style="width:%.1f%%"></i>'
            '<i class="ghost" style="left:%.1f%%;width:%.1f%%"></i>'
            '<i class="mark" style="left:%.1f%%"></i></span>'
            '<span class="bv"><b>%.1f%%</b><i>定价 %.1f%%</i></span></div>'
            % (lab, m["mc"][i], min(m["mc"][i], m["mk"][i]), abs(m["mc"][i] - m["mk"][i]), m["mk"][i],
               m["mc"][i], m["mk"][i]))
    return "\n".join(h)


def probs_table(m, exts):
    r = ['<table><thead><tr><th>参照系</th><th>方向 / 比分</th><th>口径说明</th></tr></thead><tbody>']
    r.append("<tr><td>后台模型（2 万次抽样）</td><td>%s %.1f%%</td><td>胜平负 %.1f / %.1f / %.1f%%；综合 λ %.2f 对 %.2f</td></tr>"
             % (dir_of(m["mc"]), max(m["mc"]), m["mc"][0], m["mc"][1], m["mc"][2], m["lam"][0], m["lam"][1]))
    r.append("<tr><td>官方固定奖金（去水）</td><td>%s %.1f%%</td><td>胜平负 %.1f / %.1f / %.1f%%；Edge 主 %+.1f / 平 %+.1f / 客 %+.1f 个百分点</td></tr>"
             % (dir_of(m["mk"]), max(m["mk"]), m["mk"][0], m["mk"][1], m["mk"][2],
                m["edge"][0], m["edge"][1], m["edge"][2]))
    seen = set()
    for e in exts:
        p = e.get("provider") or ""
        if p in seen:
            continue
        seen.add(p)
        r.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                 % (html.escape(p), html.escape(e.get("predicted") or e.get("predicted_dir") or "—"),
                    html.escape((e.get("note") or "")[:150])))
    r.append("</tbody></table>")
    return "\n".join(r)


def match_block(r, idx):
    m = MODEL.get(r["no"])
    exts = ext_for(r)
    head = ('<section class="match" id="m%d"><header class="mhead"><div class="mno">'
            '<span>%s</span><span>%s</span><span>%s</span></div>'
            '<h2>%s<em>vs</em>%s</h2>' % (idx, r["no"], r["league"], r["kick"], r["home"], r["away"]))
    if not m or m.get("na"):
        head += '</header><div class="grid3"><div class="vcard"><span class="vt">缺口</span><b>模型未覆盖</b>'
        head += '<span class="vs">%s</span></div></div>' % html.escape((m or {}).get("note") or "本场没有进入批量模型口径")
        head += '<p class="body">本场只列外部参照：%s</p></section>' % (
            "；".join("%s %s" % (e["provider"], e.get("predicted_dir") or e.get("predicted") or "—") for e in exts) or "无")
        return head
    conf = confidence(m, exts)
    head += '<div class="msum"><div><b>模型方向</b>%s<span class="sep">/</span><b>定价方向</b>%s</div>' \
            '<div class="conf"><span class="cnum">%d</span><span class="cgrade">%s</span></div></div>' % (
                dir_of(m["mc"]), dir_of(m["mk"]), conf, grade(conf))
    head += "</header>"
    order = sorted(range(3), key=lambda i: -m["mc"][i])
    labels = [("首选", "PRIMARY"), ("次选", "SECOND"), ("防范", "GUARD")]
    vc = []
    for k, i in enumerate(order):
        sc = ""
        for a, p in m["top"]:
            if (i == 0 and a.split("-")[0] > a.split("-")[1]) or (i == 2 and a.split("-")[0] < a.split("-")[1]) \
                    or (i == 1 and a.split("-")[0] == a.split("-")[1]):
                sc = a
                break
        vc.append('<div class="vcard v%d"><span class="vt">%s · %s</span><b>%s</b><span class="vs">比分 %s · 模型 %.1f%%</span></div>'
                  % (k + 1, labels[k][0], labels[k][1], ["主胜", "平", "客胜"][i], sc or "—", m["mc"][i]))
    body = '<div class="grid3">%s</div>' % "".join(vc)
    body += '<section class="s"><h3><i>01</i>结构与门槛</h3><div class="col2"><div>%s</div><div>%s</div></div></section>' \
            % (bars(m, exts), probs_table(m, exts))
    ou = ('<p class="body">大 2.5 球 <b>%.1f%%</b>；双方进球 <b>%.1f%%</b>；最可能比分 %s；λ 合计 %.2f。</p>'
          % (m["ou"][0], m["ou"][1], " / ".join("%s %.1f%%" % t for t in m["top"][:3]),
             m["lam"][0] + m["lam"][1]))
    body += '<section class="s"><h3><i>02</i>进球分布</h3>%s</section>' % ou
    if m.get("note"):
        body += '<section class="s"><h3><i>03</i>缺口与提醒</h3><p class="body">%s</p></section>' % html.escape(m["note"])
    mx = max(abs(e) for e in m["edge"])
    warn = ""
    if mx >= 10:
        warn += '<div>⚠️ 模型与定价最大分歧 %.1f 个百分点：按纪律先假定我方样本有缺口，不直接采信</div>' % mx
    body += ('<div class="oneline"><b>一句话</b><p>%s 对 %s：模型 %s %.1f%%，首选比分 %s；信心 %d/100（%s）。</p>%s</div>'
             % (r["home"], r["away"], dir_of(m["mc"]), max(m["mc"]),
                m["top"][0][0] if m["top"] else "—", conf, grade(conf),
                ('<div class="warns">%s</div>' % warn) if warn else ""))
    return head + body + "</div></section>"


# ---- 总览表
ov = ['<table><thead><tr><th>场次</th><th>对阵 / 开赛</th><th>模型 主/平/客</th>'
      '<th>定价去水</th><th>最大偏差</th><th>信心</th><th>外部</th></tr></thead><tbody>']
for r in rows:
    m = MODEL.get(r["no"])
    exts = ext_for(r)
    extxt = " / ".join(sorted({e.get("predicted_dir") or "—" for e in exts})) or "—"
    if not m or m.get("na"):
        ov.append('<tr><td><b>%s</b></td><td>%s vs %s<br><span class="dim2">%s · %s</span></td>'
                  '<td colspan="4" class="dim2">模型未覆盖（见分场说明）</td><td>%s</td></tr>'
                  % (r["no"], r["home"], r["away"], r["league"], r["kick"], extxt))
        continue
    mx = max(range(3), key=lambda i: abs(m["edge"][i]))
    ov.append('<tr><td><b>%s</b></td><td>%s vs %s<br><span class="dim2">%s · %s</span></td>'
              '<td>%.1f / %.1f / %.1f</td><td>%.1f / %.1f / %.1f</td><td>%s %+.1f</td><td>%d</td><td>%s</td></tr>'
              % (r["no"], r["home"], r["away"], r["league"], r["kick"],
                 m["mc"][0], m["mc"][1], m["mc"][2], m["mk"][0], m["mk"][1], m["mk"][2],
                 ["主胜", "平", "客胜"][mx], m["edge"][mx], confidence(m, exts), extxt))
ov.append("</tbody></table>")

ok = [r for r in rows if MODEL.get(r["no"]) and not MODEL[r["no"]].get("na")]
n_ext = len(ext.get("items", []))
big = sum(1 for r in ok if max(abs(x) for x in MODEL[r["no"]]["edge"]) >= 10)

CSS = """
:root{--bg:#F5F0E6;--panel:#FFFDF7;--ink:#221E18;--muted:#6A5E50;--dim:#8C7F6E;--line:rgba(60,45,30,.16);
--line2:rgba(60,45,30,.34);--brick:#8C3B23;--ochre:#A8762F;--navy:#3D5064;
--mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
--sans:"PingFang SC","Microsoft YaHei",system-ui,sans-serif;
--serif:"Songti SC","Source Han Serif SC",Georgia,serif}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.75 var(--sans)}
.wrap{max-width:1180px;margin:0 auto;padding:0 34px 70px}
.cover{padding:52px 0 26px;border-bottom:2px solid var(--ink);margin-bottom:26px}
.cover .kick{font-family:var(--mono);font-size:11px;letter-spacing:.3em;color:var(--brick)}
.cover h1{font-family:var(--serif);font-size:44px;margin:12px 0 8px}
.cover .sub{font-family:var(--serif);font-size:18px;color:#4A3E33}
.cover .meta{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin-top:12px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:22px 0 4px}
.kpi{border-left:2px solid var(--line2);padding-left:14px}
.kpi b{display:block;font-family:var(--mono);font-size:28px;color:var(--brick)}
.kpi span{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;color:var(--dim)}
.kpi i{display:block;font-style:normal;font-size:12px;color:var(--muted)}
h2.sec{font-family:var(--serif);font-size:23px;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line2)}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin:8px 0}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid rgba(60,45,30,.10);vertical-align:top}
thead th{font-family:var(--mono);font-size:10px;letter-spacing:.1em;color:var(--dim)}
.dim2{color:var(--dim);font-size:11px}
.match{border-top:1px solid var(--line2);margin-top:34px;padding-top:20px}
.mhead h2{font-family:var(--serif);font-size:30px;margin:6px 0}
.mhead h2 em{font-style:normal;font-size:15px;color:var(--dim);margin:0 10px;font-family:var(--mono)}
.mno{display:flex;gap:14px;font-family:var(--mono);font-size:11px;color:var(--dim);letter-spacing:.08em}
.msum{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:1px solid var(--line);padding-bottom:8px}
.msum .sep{color:var(--dim);margin:0 6px}
.conf .cnum{font-family:var(--mono);font-size:30px;color:var(--brick);margin-right:8px}
.conf .cgrade{font-family:var(--mono);font-size:12px;color:var(--muted)}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}
.vcard{border:1px solid var(--line2);background:var(--panel);padding:12px 14px}
.vcard .vt{font-family:var(--mono);font-size:10px;color:var(--dim);letter-spacing:.1em;display:block}
.vcard b{display:block;font-family:var(--serif);font-size:24px;margin:4px 0}
.vcard .vs{font-size:12px;color:var(--muted)}
.vcard.v1{border-left:3px solid var(--brick)}
.vcard.v2{border-left:3px solid var(--ochre)}
.vcard.v3{border-left:3px solid var(--navy)}
.s{margin:22px 0;border-top:1px dotted var(--line2);padding-top:12px}
.s h3{font-family:var(--serif);font-size:18px;margin:0 0 10px}
.s h3 i{font-style:normal;font-family:var(--mono);font-size:11px;color:var(--brick);margin-right:10px}
.s h3 .x{font-size:11px;color:var(--dim);margin-left:8px}
.col2{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.cap,.cap2{font-family:var(--mono);font-size:11px;color:var(--dim);letter-spacing:.05em;margin-bottom:6px}
.body{font-size:13.5px;margin:6px 0}
.bar{display:grid;grid-template-columns:46px 1fr 108px;gap:10px;align-items:center;margin:7px 0;font-size:12px}
.bar .bl{font-family:var(--mono);font-size:11px;color:var(--muted)}
.bar .bt{position:relative;height:14px;background:rgba(60,45,30,.07)}
.bar .fill{position:absolute;left:0;top:0;height:100%;background:rgba(140,59,35,.55)}
.bar .ghost{position:absolute;top:0;height:100%;background:rgba(61,80,100,.28)}
.bar .mark{position:absolute;top:-3px;width:2px;height:20px;background:var(--navy)}
.bar .bv{font-family:var(--mono);font-size:11px;text-align:right}
.bar .bv i{display:block;color:var(--dim);font-style:normal;font-size:10px}
.oneline{border:1px solid var(--line2);background:var(--panel);padding:14px 16px;margin-top:16px}
.oneline b{font-family:var(--mono);font-size:11px;color:var(--brick);letter-spacing:.1em}
.warns{margin-top:8px;font-size:12px;color:#7A3A22}
.appendix{margin-top:44px;border-top:2px solid var(--ink);padding-top:16px}
.appendix h3{font-family:var(--serif);font-size:17px;margin:18px 0 6px}
.appendix p,.appendix li{font-size:13px;color:#3A3129}
.foot{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10.5px;color:var(--dim);
margin-top:34px;border-top:1px solid var(--line2);padding-top:10px}
@media(max-width:760px){.col2,.grid3,.kpis{grid-template-columns:1fr}.cover h1{font-size:32px}}
"""

H = []
H.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">')
H.append("<title>2026.10.18 周日 %d 场全维度推演 · 阿飞·赛博聊球</title>" % len(rows))
H.append("<style>%s</style></head><body><div class=\"wrap\">" % CSS)
H.append('<section class="cover"><div class="kick">付费内部资料 · 全维度推演 · 海报款</div>')
H.append("<h1>2026.10.18 周日 %d 场</h1>" % len(rows))
H.append('<div class="sub">赛程覆盖 · 数理模型 · 定价结构 · 外部参照 · 缺口标注</div>')
H.append('<div class="meta">生成 2026-10-18 02:0x · 模型 v2.10 · 抽样 2 万次 · 每场按「结构 → 进球 → 缺口」三段读</div>')
H.append('<div class="kpis">'
         '<div class="kpi"><b>%d</b><span>赛程场次</span><i>10/18 15:00 起 · 跨零点 8 场</i></div>'
         '<div class="kpi"><b>%d</b><span>模型覆盖</span><i>其余场次标注缺口</i></div>'
         '<div class="kpi"><b>%d</b><span>场次分歧 ≥10 个百分点</span><i>先假定样本缺口</i></div>'
         '<div class="kpi"><b>%d</b><span>外部预测条数</span><i>公开预报 + 接口算法</i></div></div>'
         % (len(rows), len(ok), big, n_ext))
H.append("</section>")
H.append('<h2 class="sec">总览 · 一页看完</h2>')
H.append("\n".join(ov))
for i, r in enumerate(rows):
    H.append(match_block(r, i))
H.append('<section class="appendix"><h2 class="sec">附 · 方法论、口径与免责</h2>')
H.append("<h3>一、进球期望与概率</h3><p>主队主场、客队客场分开算攻防效率，样本不足按样本量混入近十场；再从官方固定奖金反解一条隐含分布做交叉。综合后按 2 万次抽样得到胜平负、总进球与比分矩阵，抽样误差控制在 0.5 个百分点以内。只统计 90 分钟常规时间。</p>")
H.append("<h3>二、偏差与纪律</h3><p>模型概率与官方固定奖金去水（按返奖率归一）后的隐含概率放在同一把尺子上比较，单格差距≥10 个百分点时先假定我方样本有缺口，只做方向参考、不做强度结论。</p>")
H.append("<h3>三、信心指数</h3><p>样本厚度 20 分、双法收敛 20 分、三方一致 25 分、分歧可控 25 分、比分集中 10 分。A（≥78）可作主参考，B（66–77）方向可信幅度打折，C（52–65）只当一种视角，D（&lt;52）只做记录。</p>")
H.append("<h3>四、本批口径</h3><ul>")
H.append("<li>覆盖 %d 场赛程，模型完整覆盖 %d 场，其余场次在分场处标注原因。</li>" % (len(rows), len(ok)))
H.append("<li>外部参照共 %d 条公开预报/接口记录，只作参照系，不改变模型结论。</li>" % n_ext)
H.append("<li>积分榜（tables）当日接口为空，排名类论据本批不写；大小球、xG 等高级数据未接入。</li>")
H.append("<li>让球若临场调整，让球一侧的偏差结论需要重算；本份不含临场首发变动后的重算。</li></ul>")
H.append("<h3>免责与使用范围</h3><p>本资料为内部复盘材料，用于检验模型口径与记录判断过程，不作公开投放、不对外销售、不作为任何形式的购买建议。百分比均为估值，不是承诺。数据来源：公开赛果数据。内部资料。</p>")
H.append("</section>")
H.append('<div class="foot"><span>阿飞 · 赛博聊球 · 内部资料 · 2026.10.18 · 周日全维度推演</span>'
         '<span>仅统计 90 分钟常规时间 · 不构成任何购买建议</span></div></div></body></html>')

htmlout = "\n".join(H)
open(OUT, "w", encoding="utf-8").write(htmlout)
print("written", OUT, len(htmlout), "bytes; rows", len(rows), "model_ok", len(ok), "big", big, "ext", n_ext)
