# -*- coding: utf-8 -*-
"""
内部分析报告生成器（合并模板脚手架）

用法：python -X utf8 scripts/build_internal_report.py 20261027
每批需按场重写 TITLE / P5 / BREAK / ACTION_HINT / ZQ 五个字典；盘口表、位移、跨盘自洽、λ、MC 与结论数全部由 _books/_data/_model 生成。

原始说明： · 合并模板（足彩盘口表 + 老六段结构，去重后七块）
一、盘口（欧赔/亚盘/大小 三套 + 位移 + 跨盘自洽）  二、模型（λ双法+泊松）
三、底层数据                                       四、外部预测与情报
五、技术面判断                                     六、综合分析（方向/比分/概率/打破/动作/足彩）
数据源：state/intel/20261027/_books|_data|_model|_af_pred
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
DAY = sys.argv[1] if len(sys.argv) > 1 else "20261027"
INTEL = ROOT / "state" / "intel" / DAY
OUT = ROOT / "📝文章" / DAY / f"{DAY}_周二10场_内部分析报告.md"

books = json.load(open(INTEL / f"_books_{DAY}.json", encoding="utf-8"))
data = json.load(open(INTEL / f"_data_{DAY}.json", encoding="utf-8"))
model = json.load(open(INTEL / f"_model_{DAY}.json", encoding="utf-8"))
af = json.load(open(INTEL / f"_af_pred_{DAY}.json", encoding="utf-8"))
AF = {r["num"][-3:]: r for r in af["rows"]}

sys.path.insert(0, str(ROOT / "scripts"))
import model_poisson_500 as mp          # noqa: E402
import model_v3 as mv3                 # noqa: E402
import settle                          # noqa: E402

AUDIT = {}
_ap = INTEL / f"_audit_{DAY}.json"
if _ap.exists():
    AUDIT = json.loads(_ap.read_text(encoding="utf-8"))
V3 = {_n: mv3.build_single(DAY, _n, AUDIT.get(_n, {}).get("grade", "A")) for _n in books}
VER = next(iter(V3.values())).get("model_version", "v3")
SNAP = next(iter(V3.values())).get("data_snapshot", "unknown")

TITLE = {
    "001": ("亚冠精英", "京都 vs 纽喷：主胜方向清，让球别碰"),
    "002": ("亚冠精英", "大田 vs 神户：两头都被抽干，不下手"),
    "003": ("亚冠精英", "国安 vs 全北：模型和定价吵起来了"),
    "004": ("德国杯", "汉堡 vs 法兰克福：退盘的那一边更可信"),
    "005": ("意甲", "萨索洛 vs 拉齐奥：拉齐奥的反客为主"),
    "006": ("瑞超", "AIK vs 埃尔夫斯堡：定价在客队，幅度不给"),
    "007": ("德国杯", "多特 vs 不莱梅：赢球容易，让球难"),
    "008": ("德国杯", "科隆 vs 柏林联合：盘口仲裁站在主队"),
    "009": ("意甲", "罗马 vs 卡利亚里：球半的价不值得"),
    "010": ("意甲", "都灵 vs 科莫：方向跟、让幅不跟"),
}

# 五、技术面（逐场手写；数字一律与「一」「二」同源，改数必同步改文）
P5 = {
"001": "这是本批基本面落差最大的一对，也是最容易把样本当结论的一对。纽喷小组赛 2 场丢 10 球（客场被鹿岛打了 1-7），全季样本只有 2 场，收缩后 A 模型仍给 80.8% 的主胜、比市场高 14.9pp——按「分歧≥10pp 先假定我方有缺口」的纪律，这份偏爱只能打折用，融合权重被样本折扣压到 0.13，最终三向 67.8/17.2/15.1。真正能拿出来说的是对手防线：京都自己小组赛 2 场只进 1 球，锋线并不硬，所以「对手比我弱得多」不等于「我很强」。球半/一 要求净胜两球，模型只给 46.3% 的覆盖率，两侧 EV 全负（-5.5 / -4.1），让球没有位置；有价的是另一边：京都主场丢球多、纽喷场均失球 3.2，大小 3.25 的大球 EV +6.6%，方向跟、大球薄取、让球不碰。",
"002": "这场是本批少见的「两头都被抽干」：模型 35.1/26.2/38.7 对市场 36.9/27.6/35.4，差不到 2pp；平手盘主队覆盖 35.1%，两侧 EV -8.5 / +0.9，客侧那 +0.9 连手续费都不够；大小 2.50 大 -7.1、小 -6.6，也全是负数。也就是说机构把这场定得很准，没有任何一处给我们便宜。两队小组赛都是 2 场、数据等级 A 但同主客样本只有 1 场，λ 的后验区间宽到 6%–47%，这种宽度不能支撑任何方向的加码——不站，就是这场最好的判断。",
"003": "本批分歧最大的一场：A 模型 78.1% 对市场 41.1%，差 37pp。按纪律先假定我方缺口——国安近 5 场全胜（含 3-1 浦项），全北近 5 场 1 胜 2 平 2 负，两边状态确实反着走，但两队小组赛都只有 2 场，全季样本不足以支撑这种偏爱，融合权重压到 0.13 后三向回到 46.7/25.6/27.8，主胜 46.7% 其实只比市场高 5pp 出头。让球平/半：模型覆盖 46.7%、主队 EV +2.1%、客队 -9.2%，看着像有价，但这点溢价完全来自被污染的 λ_A——同一盘改用「一、盘口」里只用欧赔拟合的 λ 定价，主队 EV 立刻转负。两个口径打架就不下手：方向取主胜（薄、听市场），让球不碰。",
"004": "真相和「状态好所以买」相反：法兰克福近 5 场 2 胜 1 平 2 负，还吃了 0-6 莱比锡、0-1 多特；可客赔从 2.39 被压到 2.17，亚盘由平手推到汉堡受让平/半——定价在往法兰克福加码，说明机构看的是主客分离，不是近 5 场。汉堡近 5 场 3 胜 1 平 1 负，主场能咬但挡不住。德国杯页无积分表，本场只有市场 λ（1.65/1.90），融合三向 33.9/21.9/44.1 就是市场口径，客胜 44.1% 比汉堡高 10pp。亚盘两侧 EV 全负（-4.2 / -5.9），大小 3.25 也是双负，这场只能取方向，不能要价。",
"005": "拉齐奥是本批最硬的一支：8 轮 7 胜 1 平不败、进 16 失 5，客场 4 场 8 进 1 失；萨索洛 2 胜 2 平 4 负，主场丢球偏多。让球从主让 0.25 摆到主受让 0.25（7 家 4 家动），方向和基本面同向。A 模型客胜 61.0%、市场 44.1%，Edge +16.9pp 是这批最大的一次分歧——但同主客样本只有 4 场，融合权重 0.39，最终客胜 52.0%。让球客侧 EV +9.5%，是本批唯一像样的让球溢价，可以拿；小球 2.75 的 EV 只有 +0.1%，拉齐奥客场场均失球 0.25 的故事已经被水位吃干净，不再标价。",
"006": "瑞超这场是纯结构盘：AIK 主场 12 场进 19 失 27，埃尔夫斯堡客场 12 场进 16 失 15；样本是这批最厚的，A 模型 31.5/24.5/44.0 与市场 31.5/25.0/43.6 几乎完全重合，Edge 只有 -0.3/-1.9/+2.2pp——模型和机构对这场没有分歧。让球 AIK 受让平/半，覆盖 56.4%，两侧 EV -6.9 / -3.8；大小 2.75 大 -9.7、小 -0.5，同样没有位置。这场唯一可做的是「客不败」这个方向本身，不适合在任何一盘上找价。",
"007": "多特 67.9% 的胜率市场与融合模型几乎重合，这在本批很少见。问题在让球：盘口给到一/球半，净胜两球才算赢，模型只给 46.2% 的覆盖率，两侧 EV -3.8 / -7.2。德国杯多特会换人，净胜两球的确定性并不比联赛高；而且这场是 B 档（500 的近期列表里同一场 2-2 重复出现，去重后样本只有 4 场），λ 只能走市场，主胜概率的区间宽到 31%–87%，没有资格在深盘上加码。方向照跟，让球放弃，大小 3.25 大球 -0.3%、小球 -9.0%，两边都不值得。",
"008": "德国杯页没有积分表，这场只能靠逐场：科隆近 5 场 1 胜 2 平 2 负（进 4 失 5），联合近 5 场 1 胜 2 平 2 负（进 3 失 11，含 0-7 拜仁、1-3 沙尔克）。盘口把答案给了：科隆让半球、水位从主队 0.80 抬到 0.855，融合（本场即市场）三向 51.4/24.5/24.1，模型 51.4% 与市场 51.2% 几乎一致——定价没有说谎，主胜是这场最合理的走向。半球两侧 EV 都是 -4.x%，只取足彩方向、不做让球；小球 2.75 的 EV +4.9% 是这一场真正的副产物。",
"009": "卡利亚里全季只进 6 球（8 场，场均 0.75），这是最硬的约束；罗马 8 轮 5 胜 3 平不败、主场 4 场 10 进 3 失，两边都认为主队要赢（模型 72.0%、市场 70.7%）。分歧在深度：球半要求净胜两球，模型只给 46.9% 的覆盖率，上盘 EV -10.1%，客队受让的下盘 EV +1.6%——正数但薄，够不上「有价」。水位 0.917/0.913 均衡，机构也没把上盘压到底，所以不是「反着买上盘」的理由。真正能拿的是大小：小球 2.75 的 EV +8.1%，与卡利亚里的进球结构同向。",
"010": "都灵 8 轮 4 胜 1 平 3 负、主场 4 场只进 6 失 7，赢法全靠「先进球再收缩」；科莫 8 轮 5 胜 2 平 1 负、进 14 失 7，客场 5 场 10 进 6 失。模型给客队 55.5%（市场 54.8%），定价和模型几乎同向；亚盘半/一，模型算出主队受让侧 EV -0.7%、客队让球侧 -6.1%——两侧都不值钱，所谓「跟方向不跟幅度」在这里的落地就是：方向跟客不败，让球盘一律不碰。小球 2.75 的 EV +5.0%，与都灵主场场均 1.5 球的结构一致，可以捎带。",
}

# 六、打破条件（逐场）
BREAK = {
"001": "纽喷先进球：京都小组赛 2 场只进 1 球，先失球几乎没有翻盘路径",
"002": "神户派全主力首发（轮换一取消，客队胜率立刻回到 45% 以上）",
"003": "全北先开糊：国安近 5 场全胜但 4 场失球，先失球就是另一套剧本",
"004": "汉堡先进球：法兰克福近 5 场两场被打崩（0-6、0-1），落后时的防线大开大合",
"005": "萨索洛先进球：拉齐奥客场 4 场只失 1 球，被追平的样本为零但先失球没试过",
"006": "AIK 主场打出高比分：他们主场 12 场丢 27 球，6 场失 2 球以上",
"007": "多特 60 分钟内没进球：换人之后节奏会掉，2-2 那场就是这么来的",
"008": "联合先开糊：他们近 5 场 3 个进球全在赢球那一场，先开糊=唯一路径",
"009": "卡利亚里先开糊：6 个进球换 4 个客场胜利，反击一旦打成罗马要被追分",
"010": "都灵先进球：模型给都灵 22.9%、科莫 55.5%，都灵的赢法只有「先进球然后收缩」这一种",
}

ACTION_HINT = {
"001": "主胜（跟方向，权重已按样本打折）；大小 3.25 大球（薄）；让球不碰",
"002": "不站方向；单盘也无位置（平手客 +0.9%、大小双负）",
"003": "主胜（薄，取折中）；让球不碰",
"004": "客胜（跟定价）；让球与大小都不碰",
"005": "客胜（本批最硬的方向）；拉齐奥让平/半 上盘（+9.5%）；小球不标价",
"006": "客不败；让球与大小都不碰",
"007": "主胜；让球（一/球半）不碰；大小不碰",
"008": "主胜；让球不碰；小球 2.75（+4.9%）",
"009": "主胜；让球两侧都不碰（下盘 +1.6% 太薄）；小球 2.75（+8.1%）",
"010": "客不败；让球不碰（主 -0.7/客 -6.1 皆无价）；小球 2.75（+5.0%）",
}
ZQ = {"001": "3", "002": "1", "003": "3", "004": "0", "005": "0",
      "006": "1/0", "007": "3", "008": "3", "009": "3", "010": "0"}


def line_txt(side, line):
    m = {1.5: "球半", 1.25: "一/球半", 1.0: "一球", 0.75: "半/一", 0.5: "半球",
         0.25: "平/半", 0.0: "平手"}
    v = m.get(abs(line), f"{abs(line)}")
    return f"{side} {v}" if side != "平手" else "平手"


def pct(x, n=1):
    return f"{x*100:.{n}f}%"


def pp(x, n=1):
    return f"{x*100:.{n}f}"


def build_table(b):
    rows = []
    names = ["皇冠", "Bet365", "易胜博", "威廉", "伟德", "Interwetten"]
    for nm in names:
        ah = b.get("ah", {}).get(nm)
        ou = b.get("ou", {}).get(nm)
        ox = b.get("ox", {}).get(nm)
        cells = [nm]
        for src, side in ((ah, "ah"), (ox, "ox"), (ou, "ou")):
            if not src:
                cells += ["—", "—"]
                continue
            for key in ("open", "close"):
                d = src[key]
                if side == "ox":
                    cells.append("/".join(f"{x:.2f}" for x in d))
                elif side == "ah":
                    ln = line_txt("主让" if d["line"] < 0 else ("平手" if d["line"] == 0 else "主受让"), d["line"])
                    cells.append(f"{ln} {d['home']:.2f}/{d['away']:.2f}")
                else:
                    cells.append(f"{abs(d['line']):.2f} {d['home']:.2f}/{d['away']:.2f}")
        rows.append("| " + " | ".join(cells) + " |")
    head = ("| 公司 | 亚盘·初盘 | 亚盘·即时 | 欧赔·初盘 | 欧赔·即时 | 大小·初盘 | 大小·即时 |\n"
            "|---|---|---|---|---|---|---|")
    return head + "\n" + "\n".join(rows)


def recent_line(rows):
    ms = rows["matches"]
    out = []
    for m in ms[:5]:
        out.append(f"{m['home']} {m['score']} {m['away']}")
    return "；".join(out)


def recent_10(rows):
    gf = ga = 0
    for m in rows["matches"][:10]:
        try:
            a, b = [int(x) for x in m["score"].split("-")]
        except Exception:
            continue
        # 500 每行的场地字段名是 venue（H/A）；旧代码读 side 永远取不到 → GF/GA 全反，已修
        venue = m.get("venue") or m.get("side")
        if venue == "H":
            gf += a
            ga += b
        else:
            gf += b
            ga += a
    n = min(10, len(rows["matches"]))
    return (gf / n if n else 0), (ga / n if n else 0), n


def sect3(num, row):
    sh, sa = row["season_home"], row["season_away"]
    t1, t2 = sh.get("total"), sa.get("total")
    h1, a2 = sh.get("home") or {}, sa.get("away") or {}
    gfh, gah, nh = recent_10(row["recent_home"])
    gfa, gaa, na = recent_10(row["recent_away"])
    h2h = (row.get("h2h") or {}).get("summary")
    parts = []
    if t1 and t2:
        parts.append(
            f"- 全季：{row['home']} {t1['p']} 场 {t1['w']}胜{t1['d']}平{t1['l']}负、进 {t1['gf']} 失 {t1['ga']}"
            f"（第 {t1['rank']}）；{row['away']} {t2['p']} 场 {t2['w']}胜{t2['d']}平{t2['l']}负、进 {t2['gf']} 失 {t2['ga']}（第 {t2['rank']}）")
        if h1.get("p") and a2.get("p"):
            parts.append(
                f"- 同主客：主队主场 {h1['p']} 场 进 {h1['gf']} 失 {h1['ga']}（场均 {h1['gf']/h1['p']:.2f}/{h1['ga']/h1['p']:.2f}）；"
                f"客队客场 {a2['p']} 场 进 {a2['gf']} 失 {a2['ga']}（场均 {a2['gf']/a2['p']:.2f}/{a2['ga']/a2['p']:.2f}）")
    else:
        parts.append("- 杯赛页无积分表：本场赛季分项缺源，λ 只用市场反推法，底层数据靠逐场与交锋补")
    au = AUDIT.get(num) or {}
    h5 = (au.get("recent_home") or {}).get("n5")
    a5 = (au.get("recent_away") or {}).get("n5")
    if h5 and a5:
        parts.append(f"- 近 5 场场均进/失（逐场比分重算，审计等级 {au.get('grade')}）："
                     f"主 {h5['gf_pg']:.2f}/{h5['ga_pg']:.2f}（{h5['w']}胜{h5['d']}平{h5['l']}负）；"
                     f"客 {a5['gf_pg']:.2f}/{a5['ga_pg']:.2f}（{a5['w']}胜{a5['d']}平{a5['l']}负）")
    else:
        parts.append(f"- 近 {nh} 场场均进/失：主 {gfh:.2f}/{gah:.2f}；客 {gfa:.2f}/{gaa:.2f}")
    parts.append(f"- 逐场（近 5）：主 {recent_line(row['recent_home'])}；客 {recent_line(row['recent_away'])}")
    if h2h:
        parts.append(f"- 交锋：近 {h2h['n']} 次 {h2h['text']}进 {h2h['gf']} 失 {h2h['ga']}，大球 {h2h['over']} 次、小球 {h2h['under']} 次")
    else:
        parts.append("- 交锋：本批未取到有效交锋表（缺源不写）")
    parts.append("- 缺源：伤停名单、天气、裁判、xG、逐场射门本批均未取到，不赋值、不估")
    return "\n".join(parts)


def sect4(num):
    a = AF.get(num)
    if not a:
        return "- 外部预测未取到（缺源不写）"
    lines = [
        f"- 外部模型倾向（api-football 免费层）：**{a.get('pred_winner') or '—'}**；原文建议：{a.get('pred_advice') or '—'}",
        "- 该层给出的三向百分比是模板值（多场同为 45/45/10 或 10/45/45，005 还是 0/50/50），**不采信、不进模型**，只保留倾向",
        "- 外媒稿：本批未取到可引媒体稿；伤停/天气/裁判/xG 同缺，本节不编",
    ]
    return "\n".join(lines)


def sect_pan(num, v, b):
    ox_open, ox_close = v["ox_open"], v["ox_close"]
    def mode(vals):
        if not vals:
            return None
        from collections import Counter
        return Counter([round(x, 2) for x in vals]).most_common(1)[0][0]

    ah_o, ah_c = mode(v["ah_open_lines"]), mode(v["ah_close_lines"])
    ou_o, ou_c = mode(v["ou_open_lines"]), mode(v["ou_close_lines"])
    lines = []
    m3 = v["market3"]
    lines.append(f"- 去水三向（{v['books_ox']} 家即时均值）：**{pct(m3[0])} / {pct(m3[1])} / {pct(m3[2])}**")
    dx = []
    if ox_open and ox_close:
        dx.append(f"欧赔 主 {ox_open[0]:.2f}→{ox_close[0]:.2f}、客 {ox_open[2]:.2f}→{ox_close[2]:.2f}")
    if ah_o is not None and ah_c is not None:
        dx.append(f"亚盘 {line_txt('主让' if ah_o < 0 else ('平手' if ah_o == 0 else '主受让'), ah_o)}"
                  f"→{line_txt('主让' if ah_c < 0 else ('平手' if ah_c == 0 else '主受让'), ah_c)}"
                  f"（众数线），即时水位 主 {v['ah_water'][0]:.3f} / 客 {v['ah_water'][1]:.3f}")
    if ou_o is not None and ou_c is not None:
        dx.append(f"大小 {abs(ou_o):.2f}→{abs(ou_c):.2f}")
    lines.append("- 位移：" + "；".join(dx))
    # 跨盘自洽：用欧赔+大小反推的 λ 给亚盘/大小定价
    coh = []
    if v["ev_ah_mkt"][0] is not None:
        coh.append(f"只用欧赔拟合的 λ（{v['lam_1x2'][0]:.2f}/{v['lam_1x2'][1]:.2f}，λ总 {sum(v['lam_1x2']):.2f}）给亚盘定价：主队 EV {v['ev_ah_mkt'][0]:+.1f}%、客队 {v['ev_ah_mkt'][1]:+.1f}%")
    if v["ev_ou_mkt"][0] is not None:
        coh.append(f"同一 λ 给大小定价：大 {v['ev_ou_mkt'][0]:+.1f}%、小 {v['ev_ou_mkt'][1]:+.1f}%")
    lines.append("- 跨盘自洽：" + "；".join(coh) + "（越接近 0 = 该盘与欧赔越一致；明显偏离就是单盘溢价所在）")
    if v["ou_implied_total"]:
        lines.append(f"- 大小盘水位反推的总进球期望 ≈ {v['ou_implied_total']:.2f}（与 λ总 {v['lam_total']:.2f} 对照用）")
    lines.append("- 本批竞彩五盘未开售：让球、总进球、半全场、波胆四盘无官方价，本节只做欧赔/亚盘/大小三套")
    if v["ou_line"] is None:
        lines.append("- 该场 500 未列大小盘（表格里为 —），大小球只能靠模型推算，无市场价可对照")
    return "\n".join(lines)


def sect_model(num, v):
    r = V3[num]
    la, lb, lc = r["lam_data"], r["lam_market"], r["lam_fused"]
    def f2(x):
        return "—" if x is None else f"{x[0]:.2f} / {x[1]:.2f}"
    lines = []
    lines.append(f"- 数据完整性等级 **{r['grade']}**（同主客样本：主 {r['n_eff'][0]} 场 / 客 {r['n_eff'][1]} 场）；"
                 f"预测证据等级 **{r['evidence_grade']}**")
    _oo, _tt, _jj = r.get('lam_odds_only'), r.get('lam_totals_only'), r.get('lam_market_joint')
    if _oo or _jj:
        lines.append(f"- 市场侧三套口径分开列（避免同名不同算法）：欧赔单腿 {f2(_oo)}；"
                     f"大小单腿 {f2(_tt)}；联合拟合 **{f2(_jj)}**（下面 B 用它）")
    lines.append(f"- **A 独立模型 λ** {f2(la)}（经验贝叶斯：同主客速率 × 对手防守指数^0.5，向全季池化值收缩，k={r['k']:.0f}）")
    lines.append(f"- **B 市场 λ（联合拟合）** {f2(lb)}（Poisson 网格同时拟合欧赔去水三向 + 大小水位隐含总进球）")
    lines.append(f"- **C 融合 λ** {f2(lc)}，λ总 {sum(lc):.2f}（权重：数据 {r['w_data']:.2f} / 市场 {1 - r['w_data']:.2f}）")
    for nt in r["notes"]:
        lines.append(f"- 口径提示：{nt}")
    ta, tb, tc = r["three_data"], r["three_b"], r["three_c"]
    e = r["edge_ab"]
    if ta and e:
        lines.append(f"- 三向：A 模型 **{pct(ta[0])} / {pct(ta[1])} / {pct(ta[2])}**　市场 {pct(tb[0])} / {pct(tb[1])} / {pct(tb[2])}"
                     f"　→　**Edge(A−市场) {e[0]:+.1f} / {e[1]:+.1f} / {e[2]:+.1f} pp**")
    else:
        lines.append(f"- 三向：市场 {pct(tb[0])} / {pct(tb[1])} / {pct(tb[2])}（A 模型缺同主客样本，本场不参与）")
    lines.append(f"- 融合三向（出结论用，λ_C）：**{pct(tc[0])} / {pct(tc[1])} / {pct(tc[2])}**")
    if ta and tb:
        _avg = pct((ta[0] + tb[0]) / 2)
        lines.append(f"- 融合发生在 **λ 层**，不是概率层平均：A 模型 {pct(ta[0])}、市场 {pct(tb[0])}，"
                     f"先把两边换成 λ 再按权重（数据侧 {r['w_data']:.2f}）加权，得到 λ_C 后重算三向 {pct(tc[0])}。"
                     f"概率各半平均是 {_avg}，只作对照，不是本报告的算法。")
    iv = r.get("interval_home")
    if iv:
        lo_, hi_ = iv
        meta = r.get("interval_meta") or {}
        lines.append(f"- **模型参数不确定性区间**（5%–95% 分位）：主胜 **{lo_:.0f}%–{hi_:.0f}%**（宽 {hi_ - lo_:.0f}pp）。"
                     f"口径：只对 λ_A 抽 Gamma 后验（shape=(n+k)·λ̂、rate=n+k，n+k = "
                     f"{(meta.get('n_eff') or [0, 0])[0]:.1f}/{(meta.get('n_eff') or [0, 0])[1]:.1f}），"
                     f"**市场 λ_B 当固定常数不抽**，每次抽样都重新融合成 λ_C 再算泊松，共 {meta.get('draws', 4000)} 次。"
                     f"它描述的是「参数估错会把胜率算到哪」，**不是**「90% 把握赛果落在这段里」——赛果的不确定性由三向概率自己表达。")
        _d = r.get("interval_home_data")
        if _d:
            lines.append(f"- 对照：只抽 λ_A（不用市场）的区间是 {_d[0]:.0f}%–{_d[1]:.0f}%，样本越薄越宽；市场若也给区间则需另接盘口分布，本版未做。")
    ah = r.get("ah") or {}
    if ah.get("line") is not None:
        d = ah["dist"]
        lines.append(f"- 亚盘 {line_txt(ah['side'], ah['line'])}（五状态）：全赢 {pct(d[settle.FULL_WIN])}、赢半 {pct(d[settle.HALF_WIN])}、"
                     f"走水 {pct(d[settle.PUSH])}、输半 {pct(d[settle.HALF_LOSS])}、全输 {pct(d[settle.FULL_LOSS])}"
                     f"　→ EV 主 {ah['ev'][0]:+.1f}% / 客 {ah['ev'][1]:+.1f}%（香港盘水位 {ah['water'][0]:.3f}/{ah['water'][1]:.3f}）")
    ou = r.get("ou") or {}
    if ou.get("line") is not None:
        d = ou["dist"]
        lines.append(f"- 大小 {abs(ou['line']):.2f}（五状态）：全大 {pct(d[settle.FULL_WIN])}、大赢半 {pct(d[settle.HALF_WIN])}、"
                     f"走水 {pct(d[settle.PUSH])}、大输半 {pct(d[settle.HALF_LOSS])}、全小 {pct(d[settle.FULL_LOSS])}"
                     f"　→ EV 大 {ou['ev'][0]:+.1f}% / 小 {ou['ev'][1]:+.1f}%")
    sc = "；".join(f"{k} {pct(p)}" for k, p in r["top_scores"][:6])
    lines.append(f"- 比分前六（λ_C）：{sc}")
    mc = r["mc"]
    if mc:
        lines.append(f"- 蒙特卡洛 10 万次（λ_C，固定种子可复现）：主 **{pct(mc['w'])} / 平 {pct(mc['d'])} / 客 {pct(mc['l'])}**"
                     f"；与解析解最大偏差 {r['mc_gap']:.2f} pp（抽样噪声量级，仅作复核）")
        g = mc["goals"]
        gk = {int(k): v for k, v in g.items()}
        lines.append("- 模拟进球分布：" + "、".join(f"{k}球 {pct(gk[k], 0)}" for k in (0, 1, 2, 3, 4) if k in gk)
                     + "、5+球 " + pct(sum(v for k, v in gk.items() if k >= 5), 0))
        lines.append(f"- 敏感性：λ 主客各 ±0.20 的 3×3 网格，主胜 {pct(r['sens'][0])} → {pct(r['sens'][1])}，摆动 {r['sens'][2]:.1f} pp")
    return "\n".join(lines)


def sect_end(num, v):
    r = V3[num]
    tc = r["three_c"]
    sc = r["top_scores"]  # 只认 λ_C，避免与「二、模型」比分表打架
    iv = r.get("interval_home")
    iv_txt = (f"λ_C 参数区间 {iv[0]:.0f}–{iv[1]:.0f}%" if iv else "λ_C 参数区间不适用（无独立模型，只给市场点值）")
    lines = [
        f"- 方向：{ACTION_HINT[num]}",
        f"- 比分：{sc[0][0]}（λ_C {pct(sc[0][1])}）／次选 {sc[1][0]}（{pct(sc[1][1])}）",
        f"- 概率口径（λ_C 融合，数据权重 {r['w_data']:.2f}）：主 {pct(tc[0], 0)} / 平 {pct(tc[1], 0)} / 客 {pct(tc[2], 0)}；"
        + iv_txt + f"；足彩 **{ZQ[num]}**",
        f"- 打破条件：{BREAK[num]}",
    ]
    return "\n".join(lines)


blocks = []
for num in sorted(books):
    b = books[num]
    row = data[b["id"]]
    v = model[num]
    lg, ttl = TITLE[num]
    head = (f"### {num} {lg}｜{b['match'].split(' ', 1)[-1]}｜{b['kickoff']}｜"
            f"亚盘 {line_txt(v['ah_side'], v['ah_line'])}\n\n"
            f"阿飞·内部研判　2026-10-26　分类：{lg}　90 分钟口径　"
            f"数据完整性 {V3[num]['grade']}／预测证据 {V3[num]['evidence_grade']}　模型 {VER}　快照 {SNAP}\n")
    body = f"""
**一、盘口**

{build_table(b)}

{sect_pan(num, v, b)}

**二、模型**

{sect_model(num, v)}

**三、底层数据**

{sect3(num, row)}

**四、外部预测与情报**

{sect4(num)}

**五、技术面判断**

{P5[num]}

**六、综合分析**

{sect_end(num, v)}
"""
    blocks.append(head + body)

HEAD = f"""# 2026-10-27 周二 10 场 · 内部分析报告

- 生成：2026-10-26 深夜（赛前）。口径：**竞彩只算 90 分钟**；德国杯三场 90 分钟平局要进加时，竞彩不计。
- 版本：**后台模型 {VER}**；数据快照 **{SNAP}**（`_books_/ _data_` 的 sha256 前 12 位，换数即变）。
- 盘口源：`odds.500.com/fenxi/{{yazhi,ouzhi,daxiao}}-<id>.shtml`（亚指/欧指/大小三表，初盘+即时）；基本面源 `shuju-<id>.shtml`。
- 公司可用性：亚指只有 易胜博/威廉/伟德/Interwetten（皇冠、Bet365 不在 500 亚指表）；欧指 6 家齐；大小只有 易胜博/威廉/伟德/Interwetten。**澳彩三表均无**，空白格即缺源。
- 模板说明：本报告 = 足彩盘口表 + 原有六段结构的合并版。去重后每场固定六块：①盘口（三套+位移+跨盘自洽）②模型（λ双法 + 泊松解析 + 蒙特卡洛10万次 + 敏感性）③底层数据 ④外部预测 ⑤技术面 ⑥综合分析（方向/比分/概率/打破/动作+足彩）。
- 模型口径（v3：三套 λ 分开算，不再「各半对冲」）
  - **A 独立模型**：λ_A = 经验贝叶斯收缩（同主客速率 × 对手防守指数^0.5，向全季池化值收缩，k=4；等级 B/C 时 k=6），权重按样本再打折。
  - **B 市场隐含**：Poisson 网格同时拟合欧赔去水三向 + 大小水位隐含总进球。
  - **C 融合**：λ_C = w·λ_A + (1−w)·λ_B，w = 等级权重（A 0.65 / B 0.50 / C 0.35）× min(1, 同主客最小样本/5)。
  - **融合只在 λ 层做，不在概率层加权平均**：所以「A 模型 78% / 市场 41% / 融合 47%」是正常的，47% 不是两数中位数。
  - **两种等级不混用**：数据完整性等级（同主客样本量、重复行、日期）与预测证据等级（融合时数据侧权重 ≥0.50 较强 / 0.25–0.50 中等 / <0.25 偏弱 / 0 只有市场）分开标。
  - **Edge 一律 A vs B**（独立信号对市场）；拿融合值比市场是循环论证，已废弃。
  - 结算：亚盘/大小全部走 **五状态**（全赢/赢半/走水/输半/全输），由 `scripts/settle.py` 折算，整数球、半球、四分之一球分别处理，水位按香港盘。
  - 不确定性：λ 后验 Gamma((n+k)·λ̂, n+k) 抽 4000 次，给主胜概率 5%–95% 区间；**点估计与区间必须同源**（都用 λ_C），λ_A 的区间只作对照。
  - 一致性硬约束（由 `scripts/check_report_consistency.py` 自动验）：同场同比分只能有一个概率；点估计必须落在自己的区间内；本文每个百分数必须能在 `_model_v3_<day>.json` 里找到出处。
  - 数据审计：每场近 5 场均进/失由 `scripts/audit_data.py` 从逐场比分重算，附等级 A/B/DATA_INVALID（旧版曾把场地字段读成 side 导致 GF/GA 全反，已修）。
- 纪律：模型与市场分歧 ≥10pp 的场次，按「先假定我方数据有缺口」处理——本次落地为「融合权重按样本打折」，不直接采信模型，也不无脑信市场。
- 本文是内部稿：含盘口、去水、机构口径，**公开稿按 R41 去盘口语**，两篇前瞻另出。

"""

DEC = """
## 决策层汇总

| 场 | 数据完整性 | 预测证据 | 站位 | 市场动作 | 融合概率（主/平/客） | 足彩 |
|---|---|---|---|---|---|
"""
rows = []
for num in sorted(books):
    r = V3[num]
    tc = r["three_c"]
    act = ACTION_HINT[num].split("；")
    rows.append(f"| {num} {books[num]['match'].split(' ', 1)[-1].replace(' vs ', '–')} | {r['grade']} | "
                f"{r['evidence_grade']} | {act[0]} | {'；'.join(act[1:]) or '—'} | "
                f"{tc[0]*100:.0f}/{tc[1]*100:.0f}/{tc[2]*100:.0f} | {ZQ[num]} |")
DEC += "\n".join(rows) + "\n\n"

# —— 数据驱动的盘点（全部取 V3 的五状态 EV，阈值 +3%） ——
buy_ah, buy_ou = [], []
for num in sorted(books):
    r = V3[num]
    if r["ah"]["ev"][0] is not None:
        for side, ev in (("主", r["ah"]["ev"][0]), ("客", r["ah"]["ev"][1])):
            if ev is not None and ev >= 3:
                buy_ah.append(f"{num} {side}侧 {ev:+.1f}%")
    if r["ou"]["ev"][0] is not None:
        for side, ev in (("大", r["ou"]["ev"][0]), ("小", r["ou"]["ev"][1])):
            if ev is not None and ev >= 3:
                buy_ou.append(f"{num} {side}球 {ev:+.1f}%")
DEC += f"- 亚盘溢价（五状态 EV，≥+3% 才算买入）：{'、'.join(buy_ah) if buy_ah else '无——本批让球盘整体被抽干'}\n"
DEC += f"- 大小盘溢价（≥+3%）：{'、'.join(buy_ou) if buy_ou else '无'}\n"
DEC += "- 亚盘两侧都没到买入线的场次（读作「这两个方向都不给价，别硬找」）："
DEC += "、".join(f"{n}" for n in sorted(books)
                 if V3[n]["ah"]["ev"][0] is not None and max(V3[n]["ah"]["ev"]) < 3) + "\n"

coh_ok, coh_bad = [], []
for num in sorted(books):
    v = model[num]
    a, b = v["ev_ah_mkt"]
    if a is None:
        continue
    worst = abs(a)
    (coh_ok if worst <= 5 else coh_bad).append(f"{num} 主{a:+.1f}/客{b:+.1f}")
DEC += (f"- 三盘自洽（只用欧赔拟合的 λ 给亚盘定价，|EV|≤5% 视为一致）：一致的 {'、'.join(coh_ok) or '无'}；"
        f"偏离明显的 {'、'.join(coh_bad) or '无'}——偏离即该盘自带溢价\n")
DEC += ("- 立场分布（R49）：顺定价 4 场（004/005/007/008）／跟方向不跟幅度 4 场（001/006/009/010）／"
        "折中 1 场（003）／不站 1 场（002）\n")
DEC += ("- 深盘一律不碰让球上盘：001 一/球半、007 一/球半、009 球半三处上盘 EV 全负；"
        "本批唯一像样的让球价是 005 客侧 +9.5%。\n")
text = HEAD + "\n" + "\n\n".join(blocks) + "\n" + DEC
OUT.write_text(text, encoding="utf-8")
print("→", OUT, len(text), "chars")
