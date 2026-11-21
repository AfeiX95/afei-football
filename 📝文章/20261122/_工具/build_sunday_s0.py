# -*- coding: utf-8 -*-
"""20261122 批次专属工具：生成「周日赛程 · S0 锁定简报」。

数据源：竞彩网官方 webapi getMatchCalculatorV1.qry（在售全盘口，实时）
产物：
  📝文章/20261122/周日赛程_S0锁定简报.html   （A 层内部资料）
  📝文章/20261122/周日赛程_底表.json         （场次底表，供 S1 取数）
  📝文章/20261122/_工具/slate_raw_20261122.json（原始响应留档）

纪律：S0 只锁赛程与编号，不做方向判断、不写赔率数字、不生成 B 层公开稿。
运行：python -X utf8 "I:/阿飞说球/📝文章/20261122/_工具/build_sunday_s0.py"
"""
import sys, os, json, html, datetime, collections

BASE = r"I:\阿飞说球\📝文章\20261122"
TOOLS = os.path.join(BASE, "_工具")
ROOT = r"I:\阿飞说球"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sporttery_fetch as sf

os.makedirs(TOOLS, exist_ok=True)

sf.warmup()
st, b = sf.get("/gateway/uniform/football/getMatchCalculatorV1.qry", {"channel": "c"})
if st != 200:
    raise SystemExit("取数失败 HTTP %s" % st)
with open(os.path.join(TOOLS, "slate_raw_20261122.json"), "wb") as f:
    f.write(b)

val = json.loads(b.decode("utf-8")).get("value") or {}
rows = []
for mi in val.get("matchInfoList", []):
    rows.extend(mi.get("subMatchList", []) or [])

sun = [m for m in rows if str(m.get("matchNumStr", "")).startswith("周日")]
sun.sort(key=lambda m: str(m.get("matchNumStr", "")))
if not sun:
    raise SystemExit("在售盘口里没有周日场次，简报不生成")

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
week_counts = collections.Counter(str(m.get("matchNumStr", ""))[:2] for m in rows)
lg_counts = collections.Counter(str(m.get("leagueAbbName", "")) for m in sun)
selling = sum(1 for m in sun if str(m.get("matchStatus", "")) == "Selling")


def slot_of(m):
    d = str(m.get("matchDate", ""))
    t = str(m.get("matchTime", ""))
    if d == "2026-11-22" and t < "18:00:00":
        return "早场", "t-yellow"
    if d == "2026-11-22":
        return "晚场", "t-blue"
    return "次日凌晨", "t-green"


def clock(m):
    return str(m.get("matchTime", ""))[:5]


slim = []
for m in sun:
    s, _ = slot_of(m)
    slim.append({
        "no": str(m.get("matchNumStr", "")),
        "league": str(m.get("leagueAbbName", "")),
        "home": str(m.get("homeTeamAbbName", "")),
        "away": str(m.get("awayTeamAbbName", "")),
        "date": str(m.get("matchDate", "")),
        "time": str(m.get("matchTime", "")),
        "matchId": m.get("matchId"),
        "status": str(m.get("matchStatus", "")),
        "slot": s,
    })
with open(os.path.join(BASE, "周日赛程_底表.json"), "w", encoding="utf-8") as f:
    json.dump({"source": "sporttery getMatchCalculatorV1",
               "fetched_at": now, "date_tag": "20261122",
               "count": len(slim), "matches": slim},
              f, ensure_ascii=False, indent=2)

CSS = """
  :root{
    --bg:#12161D; --panel:#1B212B; --panel2:#232B38; --line:#313B4C;
    --text:#E6EAF2; --muted:#9AA7BD; --accent:#7AA2F7; --accent2:#A8C0FF;
    --green:#56C08D; --red:#E47070; --yellow:#E0B25A;
  }
  *{box-sizing:border-box}
  body{margin:0;padding:32px 20px 60px;background:var(--bg);color:var(--text);
       font-family:system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.6}
  .wrap{max-width:1120px;margin:0 auto}
  header{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:22px}
  h1{font-size:27px;margin:0 0 8px}
  .sub{color:var(--muted);font-size:14px;margin:0}
  .badge{display:inline-block;margin-left:10px;padding:3px 10px;border:1px solid var(--accent);
         border-radius:999px;color:var(--accent2);font-size:12px;vertical-align:middle}
  h2{font-size:19px;margin:32px 0 12px;padding-left:11px;border-left:3px solid var(--accent)}
  p{font-size:14px;margin:8px 0}
  .muted{color:var(--muted);font-size:13px}
  .status{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:16px 0 24px}
  .st{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:13px 16px}
  .st b{display:block;color:var(--accent2);font-size:12px;margin-bottom:4px}
  .st span{font-size:16px;font-weight:600}
  .st small{display:block;color:var(--muted);font-size:12px;margin-top:4px}
  .warn{padding:13px 17px;border-left:3px solid var(--yellow);background:rgba(224,178,90,.09);
        border-radius:0 8px 8px 0;font-size:13px;color:#EED9A9;margin:14px 0}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:12px 0}
  table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13px}
  th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
  th{background:var(--panel2);color:var(--accent2);font-weight:600;white-space:nowrap}
  tr:nth-child(even) td{background:rgba(255,255,255,.015)}
  .tag{display:inline-block;padding:1px 7px;border-radius:5px;font-size:11px;white-space:nowrap}
  .t-green{background:rgba(86,192,141,.15);color:var(--green)}
  .t-red{background:rgba(228,112,112,.15);color:var(--red)}
  .t-yellow{background:rgba(224,178,90,.15);color:var(--yellow)}
  .t-blue{background:rgba(122,162,247,.15);color:var(--accent2)}
  .grp td{background:rgba(122,162,247,.08)!important;color:var(--accent2);font-weight:600}
  ul{margin:8px 0 0 18px;padding:0;font-size:13px;color:var(--muted)}
  li{margin:5px 0}
  footer{margin-top:42px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
  @media print{body{background:#fff;color:#111}.card,.st{background:#fff;border-color:#ccc}
    th{background:#eee;color:#111}.muted,footer,ul{color:#555}h2{border-color:#4472C4}}
"""

n_slot = collections.Counter(x["slot"] for x in slim)
GROUPS = [
    ("早场", "早场 13:00 ｜ 韩职 %d 场（S1 需重点补齐官方资讯）" % n_slot.get("早场", 0)),
    ("晚场", "晚场 19:15–23:15 ｜ 意甲 / 西甲 / 德甲 / 荷甲 / 英冠（%d 场）" % n_slot.get("晚场", 0)),
    ("次日凌晨", "次日凌晨 00:30–04:00 ｜ 英超双红会、意甲与西甲收尾（%d 场）" % n_slot.get("次日凌晨", 0)),
]

out = []
out.append('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">')
out.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
out.append('<title>周日赛程 · S0 锁定简报（2026-11-22）</title>')
out.append('<style>' + CSS + '</style>\n</head>\n<body>\n<div class="wrap">')
out.append('<header><h1>周日赛程 · S0 锁定简报 <span class="badge">2026-11-22 ｜ 工作流 v2.0</span></h1>')
out.append('<p class="sub">按「内部分析工作流」S0 阶段输出：只锁赛程与编号，不做方向判断、不写赔率数字 ｜ 数据来源：竞彩网官方在售全盘口 webapi，抓取 %s</p></header>' % now)

out.append('<div class="status">')
out.append('<div class="st"><b>竞彩周日（编号日期 261122）</b><span>%d 场</span><small>11-22 13:00 至 11-23 04:00</small></div>' % len(sun))
out.append('<div class="st"><b>在售状态</b><span>%d / %d Selling</span><small>场次状态取自官方盘口，非人工判定</small></div>' % (selling, len(sun)))
out.append('<div class="st"><b>同盘在售其它批次</b><span>周六 %d · 周一 %d</span><small>同一响应内共 %d 场</small></div>' % (week_counts.get("周六", 0), week_counts.get("周一", 0), len(rows)))
out.append('<div class="st"><b>传足期号</b><span>待核对</span><small>本简报未取官方奖期通知，不编造</small></div>')
out.append('</div>')

out.append('<div class="warn"><strong>时点提醒：</strong>周日 %d 场里，有 %d 场实际开球落在 11-23 凌晨（编号靠后段），但仍属竞彩「周日」批次；另有 %d 场早场于 11-22 13:00 开球。周六批次尚余 %d 场在售（多为凌晨场次），与周日盘同屏显示，别混批。开售状态、让球结构与场次条数以官方页面实时显示为准。</div>' % (len(sun), n_slot.get("次日凌晨", 0), n_slot.get("早场", 0), week_counts.get("周六", 0)))

out.append('<h2>1. 竞彩周日 %d 场（编号 261122）</h2>' % len(sun))
out.append('<table><thead><tr><th>编号</th><th>联赛</th><th>对阵</th><th>开赛（北京时间）</th><th>时段</th><th>竞彩 id</th></tr></thead><tbody>')
for key, label in GROUPS:
    grp = [x for x in slim if x["slot"] == key]
    if not grp:
        continue
    out.append('<tr class="grp"><td colspan="6">%s</td></tr>' % html.escape(label))
    for x in grp:
        cls = {"早场": "t-yellow", "晚场": "t-blue", "次日凌晨": "t-green"}[key]
        out.append('<tr><td>%s</td><td>%s</td><td>%s VS %s</td><td>%s %s</td>'
                   '<td><span class="tag %s">%s</span></td><td>%s</td></tr>' % (
                       html.escape(x["no"]), html.escape(x["league"]),
                       html.escape(x["home"]), html.escape(x["away"]),
                       html.escape(x["date"]), html.escape(x["time"][:5]),
                       cls, key, str(x["matchId"])))
out.append('</tbody></table>')
out.append('<p class="muted">联赛分布：%s。场次条数、队名简称与开球时间均按官方在售盘口原样呈现，未做人工改写。</p>' % "、".join("%s %d" % (k, v) for k, v in lg_counts.most_common()))

out.append('<h2>2. 时段与联赛结构（客观统计）</h2>')
out.append('<table><thead><tr><th>时段</th><th>场数</th><th>涉及联赛</th></tr></thead><tbody>')
for key, _ in GROUPS:
    grp = [x for x in slim if x["slot"] == key]
    if not grp:
        continue
    lgs = collections.Counter(x["league"] for x in grp)
    out.append('<tr><td>%s</td><td>%d</td><td>%s</td></tr>' % (
        key, len(grp), "、".join("%s %d" % (k, v) for k, v in lgs.most_common())))
out.append('</tbody></table>')

out.append('<h2>3. S0 未关闭项（进入 S1 前补齐）</h2>')
out.append('<ul>')
for item in [
    "官方奖期通知与传足期号（本简报未取到，需核对后再锁定）",
    "临场首发与伤停名单、逐场天气、二次定盘与盘口位移",
    "积分榜进失球、≥6 场完整交锋（官方 webapi 取不到，按既有口径另补）",
    "外媒观点与独立模型概率（当前批次尚未采集）",
    "进入 S1 前须刷新 state/batch/_slate.json：python -X utf8 scripts/sporttery_fetch.py slate",
]:
    out.append('<li>%s</li>' % html.escape(item))
out.append('</ul>')

out.append('<footer>本简报为 A 层内部资料，不上平台；<strong>暂不出稿</strong>，本批次未生成任何 B 层公开稿。'
           '未改动 AGENTS.md、docs/、scripts/ 主干、state/model-state.json 等项目真源。'
           '全部内容仅作数据观察与思路参考，不构成投注建议。</footer>')
out.append('</div>\n</body>\n</html>')

with open(os.path.join(BASE, "周日赛程_S0锁定简报.html"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("OK 周日 %d 场 | 抓取 %s | 简报与底表已写入 %s" % (len(sun), now, BASE))
