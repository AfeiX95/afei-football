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

TITLE = {
    "001": ("亚冠精英", "京都 vs 纽喷：主胜方向清，让球别碰"),
    "002": ("亚冠精英", "大田 vs 神户：方向不站，只有小球有价"),
    "003": ("亚冠精英", "国安 vs 全北：模型和定价吵起来了"),
    "004": ("德国杯", "汉堡 vs 法兰克福：退盘的那一边更可信"),
    "005": ("意甲", "萨索洛 vs 拉齐奥：拉齐奥的反客为主"),
    "006": ("瑞超", "AIK vs 埃尔夫斯堡：定价在客队，幅度不给"),
    "007": ("德国杯", "多特 vs 不莱梅：赢球容易，让球难"),
    "008": ("德国杯", "科隆 vs 柏林联合：盘口仲裁站在主队"),
    "009": ("意甲", "罗马 vs 卡利亚里：球半的价不值得"),
    "010": ("意甲", "都灵 vs 科莫：方向跟、让幅不跟"),
}

# 五、技术面（逐场手写：只写该场真正的问题）
P5 = {
"001": "这是本批基本面落差最大的一对，也是最容易被样本骗的一对：纽喷在亚冠的 2 场丢了 10 球（客场 1-7 鹿岛），样本法把这个窟窿直接搬进 λ，导致模型给出 78.4% 的主胜、比市场高 12.6pp——按「分歧≥10pp 先假定我方有缺口」的纪律，这个差价不能全信。京都自己在小组赛 2 场只进 1 球，锋线并不硬；真正的结论是「对手比我弱得多」而不是「我很强」。球半要求净胜两球，而京都的进球量撑不起这个门槛，所以方向可以跟、让球不能碰——「二」里那个 +15.9% 的亚盘 EV 全是这份被污染的 λ 造出来的，换成只用欧赔拟合的 λ 给同一盘定价，主队 EV 立刻转负（见「一」跨盘自洽）。",
"002": "三盘几乎没有分歧：模型 36.0/28.0/36.0 对市场 36.9/27.6/35.4，差不到 1pp；亚盘平手两侧 EV 都是负的（-5.0 / -2.5），等于机构把这个平手盘挂得很准。唯一有价的是大小盘——模型给小球 58.3%，水位隐含只有 50.8%，小球 EV +6.8%。这种盘没必要硬找方向。两队都是 2 场小组赛：大田 1 胜 1 平（主场 1-0 零封），神户 2 战全胜（客场 2-1 逆转），基本面分不出高下，神户的轮换是唯一的不确定量。",
"003": "本批分歧最大的一场：模型 63.2% 对市场 41.1%，差 22pp。按纪律先假定我方数据有缺口——国安近 5 场全胜（含 3-1 浦项、0-3 青岛海牛），全北近 5 场 1 胜 2 平 2 负（0-2 神户、1-2 大田），两边状态确实反着走，但全北的样本里有两场是亚冠客场，口径不一致。所以真实概率往中间收：主胜 52% 上下。让球给到平/半，模型算出主队覆盖 63.2%、EV +31.5%，可这个数全部来自模型对国安的偏爱；换成只用欧赔拟合的 λ，同一盘的主队 EV 是**负值**（见「一」跨盘自洽）。两个数打架，就不下注。",
"004": "真相和「状态好所以买」相反：法兰克福近 5 场 2 胜 1 平 2 负，还吃了 0-6 莱比锡、0-1 多特；可客赔从 2.39 被压到 2.17，亚盘从平手推到主受让平/半——定价在往法兰克福这边加码，说明机构看的是主客分离而不是近 5 场。汉堡近 5 场 3 胜 1 平 1 负（0-1 帕德博恩、2-3 霍芬海姆两场失守），主场能咬但挡不住。模型客胜 44.1% 对市场 42.6%，只多 1.5pp，亚盘两侧 EV 都是负的（-4.2 / -5.9），大小 3.25 也是双负。这场只能取方向，不能要价。",
"005": "拉齐奥是本批最硬的一支：8 轮 7 胜 1 平不败、进 16 失 5，客场 4 场 8 进 1 失；萨索洛 2 胜 2 平 4 负、进 12 失 16，主场 3 场只有 6 进 4 失。让球从主让 0.25 摆到主受让 0.25（7 家 4 家动）——这是本批最干净的一次定价搬家，方向和基本面同向。模型客胜 47.6% 对市场 44.1%，亚盘客侧 EV 只有 +2.2%（薄），真正的钱在大小盘：小球 EV +13.8%，与拉齐奥客场场均 0.25 失球、萨索洛主场场均 2 球的结构一致。",
"006": "瑞超这场是纯结构盘：AIK 主场 12 场进 19 失 27（场均 2.25），埃尔夫斯堡客场 12 场进 16 失 15，模型 λ 1.31/1.62 对应客队胜率 44.8%，比市场 41.8% 高 3pp——方向在客队，但幅度不够。让球给到 AIK 受让平/半，两侧 EV 都是负的（-8.8 / -1.9）；大小 2.75 大球 44.9% 对水位隐含 50.0%，同样负数。这场唯一可做的是「客不败」这个方向本身，不适合在让球上找价。",
"007": "多特 68% 的胜率市场与模型完全重合（差 0.1pp），这在本批里很少见——机构把这场定得很准。问题出在让球：球半要求净胜两球，模型只给 46.2% 的覆盖率，两侧 EV 都是负的（-3.8 / -7.3）。两队刚在多特主场踢成 2-2，德国杯这类比赛多特会换人，净胜两球的确定性并不比联赛高。方向照跟，让球放弃，大小 3.25 大球 EV -0.3% 也没有意义。",
"008": "德国杯页没有积分表，这场只能靠逐场：科隆近 5 场 1 胜 2 平 2 负（进 4 失 5，0-1 法兰克福、1-2 汉堡），联合近 5 场 1 胜 2 平 2 负（进 3 失 11，含 0-7 拜仁、1-3 沙尔克）。盘口把答案给了：科隆让半球、水位从主队 0.80 抬到 0.855，模型 51.4% 对市场 51.2% 几乎一致——定价没有说谎，主胜是这场最合理的走向。但半球的 EV 两边都是 -4.x%，所以只取足彩方向、不做让球；小球 2.75 的 EV +4.9% 是这一场真正的副产物。",
"009": "卡利亚里全季只进 6 球（8 场，场均 0.75），这是最硬的约束；罗马 8 轮 5 胜 3 平不败、主场 4 场 10 进 3 失，两边都认为主队要赢（模型 65.8%、市场 70.7%）。分歧在深度：球半要求净胜两球，模型只给 40.1% 的覆盖率，球半上盘 EV -23.0%，客队受让的下盘 EV +14.5%——这是本批最干净的一笔。水位 0.917/0.913 均衡，说明机构也没把上盘压到底。大小 2.75 的小球 EV +17.6%，与卡利亚里的进球结构同向，可以一起拿。",
"010": "都灵 8 轮 4 胜 1 平 3 负、主场 4 场只进 6 失 7，赢法全靠「先进球再收缩」；科莫 8 轮 5 胜 2 平 1 负、进 14 失 7，客场 5 场 10 进 6 失（3-1 佛罗伦萨、2-3 费耶诺德）。模型只给客队 51.7%（市场 54.8%），也就是说定价把科莫压得比模型更狠；亚盘半/一，模型算出主队受让侧 EV +5.1%、客队让球侧 -11.8%。这是「方向跟、幅度不跟」的样本：跟客不败，但只买都灵受让这一边，不买科莫的让球。大小 2.75 的小球 EV +5.3%，与都灵主场场均 1.5 球的结构一致，可以捎带。",
}

# 六、打破条件（逐场）
BREAK = {
"001": "纽喷先进球：京都小组赛 2 场只进 1 球，先失球几乎没有翻盘路径",
"002": "神户派全主力首发（轮换一取消，客队胜率立刻回到 45% 以上）",
"003": "全北先开糊：国安近 5 场全胜但 4 场失球，先失球就是另一套剧本",
"004": "汉堡先进球：法兰克福近 5 场两场被打崩（0-6、0-1），落后时的防线是大开大合",
"005": "萨索洛先进球：拉齐奥客场 4 场只失 1 球，被追平的样本为零但先失球没试过",
"006": "AIK 主场打出高比分：他们主场 12 场丢 27 球，6 场失 2 球以上",
"007": "多特 60 分钟内没进球：换人之后节奏会掉，2-2 那场就是这么来的",
"008": "联合先开糊：他们近 5 场 3 个进球全在赢球那一场，先开糊=唯一路径",
"009": "卡利亚里先开糊：6 个进球换 4 个客场胜利，反击一旦打成罗马要被追分",
"010": "都灵先进球：模型给都灵 24.6%、科莫 51.7%，都灵的赢法只有「先进球然后收缩」这一种",
}

ACTION_HINT = {
"001": "主胜（方向跟）；让球不碰",
"002": "方向不站；只买小球 2.5",
"003": "主胜（薄，取折中）；让球不碰",
"004": "客胜（跟定价）；让球不碰",
"005": "客胜（方向最硬）；拉齐奥让平/半 上盘（薄）；小球 2.75",
"006": "客不败；让球与大小都不碰",
"007": "主胜；让球不碰",
"008": "主胜；让球不碰；小球 2.75",
"009": "主胜；卡利亚里受让球半 下盘；小球 2.75",
"010": "客不败；都灵受让半/一 下盘；小球 2.75",
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
        side = m.get("side")
        if side == "home":
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
    ld = v["lam_data"]
    lm = v["lam_mkt"]
    lam = v["lam"]
    m3, k3, e3 = v["model3"], v["market3"], v["edge3"]
    lines = []
    if ld:
        lines.append(f"- λ 样本法 {ld[0]:.2f} / {ld[1]:.2f}（主场进球+客场失球），λ 市场反推 {lm[0]:.2f} / {lm[1]:.2f}（拟合欧赔三向 + 大小隐含总进球）")
    else:
        lines.append(f"- λ 市场反推 {lm[0]:.2f} / {lm[1]:.2f}（该场缺主客分离样本，样本法不可用）")
    lines.append(f"- 综合 λ **{lam[0]:.2f} / {lam[1]:.2f}**，λ总 {v['lam_total']:.2f}")
    lines.append(f"- 三向：模型 **{pct(m3[0])} / {pct(m3[1])} / {pct(m3[2])}**　vs　市场 {pct(k3[0])} / {pct(k3[1])} / {pct(k3[2])}"
                 f"　→　Edge {e3[0]:+.1f} / {e3[1]:+.1f} / {e3[2]:+.1f} pp")
    if v["ah_line"] is not None:
        lines.append(f"- 亚盘 {line_txt(v['ah_side'], v['ah_line'])}：模型覆盖 {pct(v['ah_home'])}、走水 {pct(v['ah_push'])}、不覆盖 {pct(v['ah_away'])}"
                     f"；水位 {v['ah_water'][0]:.3f}/{v['ah_water'][1]:.3f} → EV 主 {v['ev_ah'][0]:+.1f}% / 客 {v['ev_ah'][1]:+.1f}%")
    if v["ou_line"] is not None:
        lines.append(f"- 大小 {v['ou_line']:.2f}：模型 大 {pct(v['ou_over'])}、走水 {pct(v['ou_push'])}、小 {pct(v['ou_under'])}"
                     f"；水位 大 {v['ou_water'][0]:.3f}/小 {v['ou_water'][1]:.3f} → EV 大 {v['ev_ou'][0]:+.1f}% / 小 {v['ev_ou'][1]:+.1f}%")
        lines.append(f"- 进球分布：大 1.5 {pct(v['over15'],0)}、大 2.5 {pct(v['over25'],0)}、大 3.5 {pct(v['over35'],0)}、双方进球 {pct(v['btts'],0)}")
    sc = "；".join(f"{k} {pct(p)}" for k, p in v["top_scores"][:6])
    lines.append(f"- 比分前六：{sc}")
    mc = v.get("mc")
    if mc:
        lines.append(f"- 蒙特卡洛 10 万次（Poisson 抽样）：主 **{pct(mc['w'])} / 平 {pct(mc['d'])} / 客 {pct(mc['l'])}**"
                     f"；与解析解最大偏差 {v['mc_gap']:.2f} pp（抽样噪声量级）")
        ou_s = (f"｜大小 大 {pct(mc['o'])}、走水 {pct(mc['p'])}、小 {pct(mc['u'])}"
                if mc.get("o") is not None else "")
        lines.append(f"- 模拟口径复核：亚盘覆盖 {pct(mc['ah_w'])}、走水 {pct(mc['ah_p'])}、不覆盖 {pct(mc['ah_l'])}"
                     f"{ou_s}｜主队零封 {pct(mc['zero'][0],0)}、客队零封 {pct(mc['zero'][1],0)}")
        g = mc["goals"]
        lines.append("- 模拟进球分布：" + "、".join(f"{k}球 {pct(g[k],0)}" for k in ("0", "1", "2", "3", "4") if k in g)
                     + "、5+球 " + pct(sum(g[k] for k in g if int(k) >= 5), 0))
        lines.append(f"- 敏感性：λ 主客各 ±0.20 的 3×3 网格，主胜 {pct(v['sens'][0])} → {pct(v['sens'][1])}，摆动 {v['sens'][2]:.1f} pp")
    return "\n".join(lines)


def sect_end(num, v):
    m3, k3 = v["model3"], v["market3"]
    mid = [(x + y) / 2 for x, y in zip(m3, k3)]
    lines = [
        f"- 方向：{ACTION_HINT[num]}",
        f"- 比分：{v['top_scores'][0][0]}（模型 {pct(v['top_scores'][0][1])}）／次选 {v['top_scores'][1][0]}（{pct(v['top_scores'][1][1])}）",
        f"- 概率口径（模型与市场各半）：主 {pct(mid[0],0)} / 平 {pct(mid[1],0)} / 客 {pct(mid[2],0)}；足彩 **{ZQ[num]}**",
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
            f"阿飞·内部研判　2026-10-26　分类：{lg}　90 分钟口径\n")
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
- 盘口源：`odds.500.com/fenxi/{{yazhi,ouzhi,daxiao}}-<id>.shtml`（亚指/欧指/大小三表，初盘+即时）；基本面源 `shuju-<id>.shtml`。
- 公司可用性：亚指只有 易胜博/威廉/伟德/Interwetten（皇冠、Bet365 不在 500 亚指表）；欧指 6 家齐；大小只有 易胜博/威廉/伟德/Interwetten。**澳彩三表均无**，空白格即缺源。
- 模板说明：本报告 = 足彩盘口表 + 原有六段结构的合并版。去重后每场固定六块：①盘口（三套+位移+跨盘自洽）②模型（λ双法 + 泊松解析 + 蒙特卡洛10万次 + 敏感性）③底层数据 ④外部预测 ⑤技术面 ⑥综合分析（方向/比分/概率/打破/动作+足彩）。
- 模型口径：λ 样本法 =（主队主场场均进球 + 客队客场场均失球）/2，夹取 [0.2,3.2]；λ 市场反推 = 在 Poisson 网格上同时拟合欧赔去水三向与大小水位隐含总进球；综合两法等权。三向/亚盘/大小/比分概率均由综合 λ 的独立 Poisson 解算，亚盘按整数球、半球、四分之一球分别处理走水。
- 纪律：模型与市场分歧 ≥10pp 的场次，按「先假定我方数据有缺口」处理，概率取两者折中，不直接采信模型。
- 本文是内部稿：含盘口、去水、机构口径，**公开稿按 R41 去盘口语**，两篇前瞻另出。

"""

DEC = """
## 决策层汇总

| 场 | 站位 | 市场动作 | 折中概率（主/平/客） | 足彩 |
|---|---|---|---|---|
"""
rows = []
for num in sorted(books):
    v = model[num]
    mid = [(x + y) / 2 for x, y in zip(v["model3"], v["market3"])]
    act = ACTION_HINT[num].split("；")
    rows.append(f"| {num} {books[num]['match'].split(' ', 1)[-1].replace(' vs ', '–')} | {act[0]} | "
                f"{'；'.join(act[1:]) or '—'} | {mid[0]*100:.0f}/{mid[1]*100:.0f}/{mid[2]*100:.0f} | {ZQ[num]} |")
DEC += "\n".join(rows) + "\n\n"

# —— 数据驱动的三条盘点 ——
POLLUTED = {"001", "003"}  # λ 被薄样本/热身/杯赛污染，模型 EV 不采信
buy_ah, bad_ah = [], []
for num in sorted(books):
    v = model[num]
    for side, ev in (("主", v["ev_ah"][0]), ("客", v["ev_ah"][1])):
        if ev is not None and ev >= 3:
            (bad_ah if num in POLLUTED else buy_ah).append(f"{num} {side}侧 {ev:+.1f}%")
DEC += f"- 亚盘溢价（模型口径，≥+3% 才算买入）：{'、'.join(buy_ah) if buy_ah else '无'}\n"
DEC += (f"- 模型给价但不采信（λ 被污染，正文已弃手）：{'、'.join(bad_ah) if bad_ah else '无'}"
        "——这几场换成只用欧赔拟合的 λ 定价后 EV 转负，属模型自嗨\n")

buy_ou = []
for num in sorted(books):
    v = model[num]
    for side, ev in (("大", v["ev_ou"][0]), ("小", v["ev_ou"][1])):
        if ev is not None and ev >= 3 and num not in POLLUTED:
            buy_ou.append(f"{num} {side}球 {ev:+.1f}%")
DEC += f"- 大小盘溢价（≥+3%）：{'、'.join(buy_ou) if buy_ou else '无'}\n"

coh_ok, coh_bad = [], []
for num in sorted(books):
    v = model[num]
    a, b = v["ev_ah_mkt"]
    if a is None:
        continue
    worst = abs(a)
    (coh_ok if worst <= 5 else coh_bad).append(f"{num} 主{a:+.1f}/客{b:+.1f}")
DEC += (f"- 三盘自洽（只用欧赔拟合的 λ 给亚盘定价，|EV|≤5% 视为与欧赔一致）：一致的 {'、'.join(coh_ok) or '无'}；"
        f"偏离明显的 {'、'.join(coh_bad) or '无'}——偏离即该盘自己带着溢价，已在各场「一」里标出\n")
DEC += ("- 立场分布（R49）：顺定价 5 场（004/005/006/007/008）／跟方向不跟幅度 3 场（001/009/010）／"
        "折中 1 场（003）／不站方向只站单盘 1 场（002）\n")
DEC += ("- 深盘弃手：001 一/球半、007 球半、009 球半 三处全部不碰让球上盘，009 只取受让下盘。\n")
text = HEAD + "\n" + "\n\n".join(blocks) + "\n" + DEC
OUT.write_text(text, encoding="utf-8")
print("→", OUT, len(text), "chars")
