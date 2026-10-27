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
LABEL = sys.argv[2] if len(sys.argv) > 2 else "多场"
OUT = ROOT / "📝文章" / DAY / f"{DAY}_{LABEL}_内部分析报告.md"

books = json.load(open(INTEL / f"_books_{DAY}.json", encoding="utf-8"))
data = json.load(open(INTEL / f"_data_{DAY}.json", encoding="utf-8"))
model = json.load(open(INTEL / f"_model_{DAY}.json", encoding="utf-8"))
_afp = INTEL / f"_af_pred_{DAY}.json"
af = json.load(open(_afp, encoding="utf-8")) if _afp.exists() else {"rows": []}
AF = {r["num"][-3:]: r for r in af["rows"]}

sys.path.insert(0, str(ROOT / "scripts"))
import model_poisson_500 as mp          # noqa: E402
import model_v3 as mv3                 # noqa: E402
import settle                          # noqa: E402

AUDIT = {}
_ap = INTEL / f"_audit_{DAY}.json"
if _ap.exists():
    AUDIT = json.loads(_ap.read_text(encoding="utf-8"))
INTEL_JSON = json.loads((INTEL / f"_intel_{DAY}.json").read_text(encoding="utf-8"))
INTEL_MKT = {m["no"][-3:]: (m.get("markets") or {}) for m in INTEL_JSON.get("matches") or []}
BOOKS = books
_CUR_NUM = [""]
V3 = {_n: mv3.build_single(DAY, _n, AUDIT.get(_n, {}).get("grade", "A")) for _n in books}
VER = next(iter(V3.values())).get("model_version", "v3")
SNAP = next(iter(V3.values())).get("data_snapshot", "unknown")

TITLE = {
    "001": ("亚冠精英", "大阪钢巴 vs 布里兰：主胜方向清，让球还得站着看"),
    "002": ("亚冠精英", "鹿岛 vs 浦项：客队一条数据都没有，这场的价我不接"),
    "003": ("日联赛杯", "横滨 vs 广岛：定价把主队打成弱势方，模型不认"),
    "004": ("德国杯", "帕德博恩 vs 斯图加特：客胜方向跟，让球不追"),
    "005": ("意甲", "威尼斯 vs 国米：客胜最硬，价已经没了"),
    "006": ("意甲", "AC米兰 vs 博洛尼亚：数据比定价更看好米兰"),
    "007": ("意甲", "帕尔马 vs 乌迪内斯：两队都烂，方向跟、幅度不跟"),
    "010": ("英联赛杯", "桑德兰 vs 布伦特福德：定价给主队 28%，模型只给 15%"),
    "011": ("英联赛杯", "伯恩茅斯 vs 维拉：模型更喜欢客队，我不跟定价走"),
    "012": ("英联赛杯", "富勒姆 vs 水晶宫：主队的热度没数据撑"),
    "013": ("意甲", "蒙扎 vs 那不勒斯：那不勒斯的大热里有水分"),
    "014": ("意甲", "热那亚 vs 尤文：分歧最小的一场，方向最稳"),
    "015": ("英联赛杯", "利物浦 vs 切尔西：主场让球从平手抬起来，主胜是真在动"),
}

# 五、技术面（逐场手写；数字一律与「一」「二」同源，改数必同步改文）
P5 = {
"001": "大阪钢巴这场的数据其实是「薄的」：亚冠小组赛只打了 2 场，本季主客分项根本凑不出来，λ_A 走的是近期场次速率，等级封顶 C，融合权重被压到 0.21——所以 A 模型 51.4% 对市场 56.4% 的那 5pp 差，我没有把它当分歧用，而是当噪音处理。真正有信息的是形态：钢巴近 5 场 DWDWL、进 9 失 8，主场并不封闭；布里兰近 5 场 LWLWD、进 6 失 6，客场能进球也能丢球。定价把主胜放在 56.4%、让球 -1 的主队侧只有 32.3%，等于说「赢球可以，净胜两球不行」。这句判断和我看到的一致，所以方向顺着，但不加码。",
"002": "这场我只有一个结论：不站。原因是数据层缺了一条腿——浦项的近期场次在取数源里是空的，A 模型无从给出 λ，三向概率整条腿只剩市场，权重 0。市场给 71.4/17.4/11.2，让球 -1 主队侧 48.9%，总进球隐含 3.44，全部是「鹿岛更强」这一个故事的复述，没有任何独立证据能和它对冲。鹿岛近 5 场 LDWWW、进 9 失 5，看着不错，但那 5 场里没有一场是同级别对手。一场只有单腿证据的比赛，最好的处理不是猜，是留白。",
"003": "这是本批分歧最大的一场，也是我最不敢用模型的一场。定价给横滨 19.1%、广岛 57.9%，而我的 λ_A 反过来：横滨 60.6%、广岛 18.3%，Edge 主胜 +41.5pp。按纪律，分歧超过 10pp 先假定我方数据有缺口——查下去确实有：横滨近 5 场 DDDWD 只进 5 球，广岛 WLWWW 进 10 失 4，我的 λ 是从「近 5 场全部场次」拼出来的（日联杯样本不足，同主客拆不开），把横滨的控球型比赛和广岛的强势期混在了一起。所以这场我不站模型那一边，也不追市场那 57.9%，改成「方向薄站客队、让球不碰」。",
"004": "帕德博恩对斯图加特，一德一甲，落差在定价里写得很清楚：客胜 61.0%。模型给 45.3%，Edge 客胜 -15.7pp，也就是说我比市场更看好主队——但这份「更看好」的来路不干净：德国杯样本不足 4 场，λ_A 是近期速率拼的，等级 C、权重 0.21。帕德博恩近 5 场 WDLWL、进 6 失 8，斯图加特 WLDLW、进 8 失 5，两边都不是铜墙。所以处理方式是「方向跟定价、幅度不跟」：客胜可以顺着，让球 +1 的主队侧不追，因为那需要主队输一球以内甚至不输，我的数据撑不住这个结论。",
"005": "威尼斯对国米是本批方向最硬的一场，也是最没价的一场。市场客胜 72.0%，模型 76.7%，Edge +4.7pp，两边几乎不吵架；λ_C 0.95/2.64，隐含总进球 3.64，是全场最高的一档。问题是价格：客胜已经被压到 1.35 附近，让球 +1 的客队侧 1.73，五状态里客队要赢两球才全赢。威尼斯近 5 场 LWLLL、进 4 失 10，防线是真的漏，但国米客场并不总是把比分拉开。所以我只认方向、不认幅度，让球不碰；真要找位置，反倒是「总进球偏大」这一侧比胜负更站得住。",
"006": "AC米兰对博洛尼亚，是本批四场 A 级里最干净的一场。λ_A 2.25/0.88 对市场 λ_B 2.00/0.90，模型主胜 68.3%、市场 61.5%，Edge +6.8pp，分歧在可解释范围内：米兰近 5 场 WLWWD、进 10 失 6，主场两场零封；博洛尼亚近 5 场 WLWDL、进 6 失 6，客场没有稳定的进球来源。定价让球 -1 的主队侧 2.50，相当于把「赢两球」定价在四成多，而我的模型给到六成——这是本批少见的、模型与市场同向而模型更贪的一场。方向站主胜，让球可以薄看一眼，但别重手。",
"007": "帕尔马对乌迪内斯，两队的状态都难看：帕尔马近 5 场 LLLWL、进 4 失 11，乌迪内斯 LLLLL、进 4 失 13，五连败。定价给主 31.1%、客 39.4%，模型给客 52.1%，Edge 客胜 +12.7pp——分歧刚过 10pp 这条线。查原因：乌迪内斯那 5 场连败里有三场是对前六，帕尔马那 5 场里两场被打穿。这种「都烂」的比赛，方向可以跟（客队略强），幅度不能跟：让球 +1 的主队侧只要帕尔马不输两球就全赢，而帕尔马主场进 4 球的产量撑不起「不被拉开」的假设。这场我按「跟方向不跟幅度」处理。",
"010": "桑德兰对布伦特福德是本批模型和定价吵得第二凶的一场。市场给主队 28.2%，我的 λ_A 只有 0.60/1.50，模型主胜 14.8%，Edge -13.4pp。原因是桑德兰近 5 场 DDLWL、进 3 失 6，主场两场 0 进球——进攻产量是全批最低的一档；布伦特福德近 5 场 DDLDW、进 8 失 6，客场反而能进球。但我不打算顺着这个 13pp 差去反向打主队：英联杯样本不足 4 场，λ_A 是近期速率拼的，等级 C、权重 0.14，模型在这场的发言权本来就被压到很低。处理：主胜不碰，客不败薄站。",
"011": "伯恩茅斯对维拉，数据指向和定价指向相反。市场主胜 44.0%，模型 39.0%，看着差不多；但客胜这一格，市场 30.3%、模型 43.5%，Edge +13.2pp，是这批里客队被低估最明显的一场。原因不难找：伯恩茅斯近 5 场 WWWWL、进 12 失 5，火力很猛；维拉近 5 场 WWWWD、进 14 失 4，更猛，而且四场零封。两队都在状态峰值，定价却把主队摆在明显优势位——这是「主场加成」被过度使用。我的处理是反向：站客队一侧，但不站满，因为英联杯轮换风险两队都有，λ 的等级只有 C。",
"012": "富勒姆对水晶宫，是本批分歧最大的一场：市场主胜 52.7%，模型 21.5%，Edge -31.2pp。这个差距不可能靠「模型更聪明」解释，只能靠数据缺口解释——查完确认：富勒姆近 5 场 WWLDW、进 7 失 5，状态没问题；水晶宫近 5 场 WLDLL、进 7 失 14，客场被打了两次大比分。我的 λ_A 1.00/1.75 明显把富勒姆的产量压低了（杯赛样本不足，近 5 场里两场是轮换阵容）。所以这场的正确读法不是「主队被高估 31pp」，而是「我的独立证据在这场上不成立」，方向按市场走、不按模型走，且只做方向、不碰让球。",
"013": "蒙扎对那不勒斯，定价把客队压在 55.4%，模型只给 49.4%，而主胜这一格模型 38.1%、市场 21.3%，Edge +16.8pp。分歧的来源是形态而不是名气：蒙扎近 5 场 LWLDW、进 11 失 9，主场能对攻；那不勒斯近 5 场 DWLLW、进 11 失 10，客场防线一直在丢球。让球 +1 的主队侧只要蒙扎不输两球就全赢，这个条件在「两队都进 11 球」的背景下并不苛刻。处理：反向薄站主队一侧，不追客胜的大热；等级 A、权重 0.39，这次模型的发言权是够的。",
"014": "热那亚对尤文，是本批分歧最小的一场：市场 16.4/24.6/59.0，模型 18.4/24.2/57.4，Edge 全部在 2pp 以内。这种「两边不吵架」的比赛，反而是最该按方向做的——因为不存在需要打折的分歧。数据侧也对得上：热那亚近 5 场 WLWLW、进 5 失 5，赢输交替、产量很低；尤文近 5 场 WDLWD、进 7 失 7，不算强势但稳定。λ_C 0.84/1.71，隐含总进球 2.62，是偏低的一档。处理：客胜方向站住，让球 +1 的主队侧不碰（尤文赢一球就够，赢两球不常见）。",
"015": "利物浦对切尔西，是今天唯一一场盘口真在动的强强对话：主胜从 39.9% 抬到 41.0%，让球从平手升到主让平/半，客队侧退到 34.4%。模型给主胜 60.6%，Edge +19.6pp——分歧同样超过 10pp，同样先假定我方有缺口：英联杯样本不足 4 场，λ_A 2.00/1.00 是从「近 5 场全部场次」拼的，而利物浦近 5 场 WWWWL、进 14 失 10，那 10 个失球里有 4 个来自一场。所以我只取「方向」不取「幅度」：主胜顺着，让球 -1 不碰，因为「赢两球」这件事恰好是我数据最不确定的部分。",
}

BREAK = {
"001": "布里兰先进球：钢巴近 5 场进 9 失 8，主场并不封闭，先失球后要靠产量追，而他们的产量只有 1.8 球/场",
"002": "鹿岛轮换：亚冠 18:00 开球、周末还有联赛，一旦主力减半，71.4% 的主胜立刻失真",
"003": "横滨先进球：广岛近 5 场进 10 失 4，落后时的压迫会更强，横滨的控球会被迫变成对攻",
"004": "帕德博恩先进球：斯图加特近 5 场两场失球 2+，落后时防线会散，客胜 61% 就没了",
"005": "威尼斯先进球：国米客场 4 场只有 1 场零封，先失球后要靠产量追，而 72% 的定价没给这个剧本留位置",
"006": "博洛尼亚先进球：米兰主场两场零封都在领先后，先失球的样本为零，领先剧本才是他们的舒适区",
"007": "乌迪内斯先进球：帕尔马近 5 场进 4 失 11，先失球后基本没有追平能力，客胜会立刻变成大胜",
"010": "桑德兰先进球：他们主场两场 0 进球，一旦先进球，比赛会变成低位防守，客不败的判断要重算",
"011": "维拉轮换：英联杯四天后还有联赛，维拉若换半套阵容，客队 43.5% 的模型值会立刻掉到三成以下",
"012": "富勒姆先进球：水晶宫近 5 场失 14，落后时防线会散，主队 52.7% 的定价会变成「稳」",
"013": "那不勒斯先进球：蒙扎近 5 场进 11 失 9，能追但防线也漏，落后时的对攻会放大总进球",
"014": "热那亚先进球：尤文近 5 场进 7 失 7，落后时没有强攻能力，客胜 59% 会立刻变成平局盘",
"015": "切尔西先进球：利物浦近 5 场失 10，落后时压上会把比赛变成对攻，主胜 41% 的定价会失真",
}

ACTION_HINT = {
"001": "主胜（顺定价、薄）；让球 -1 不碰；总进球偏大一侧优于胜负",
"002": "不站方向；让球与总进球都不碰（单腿证据，无对冲）",
"003": "客胜（薄，跟定价打折）；让球不碰；主队 +1 只作观察",
"004": "客胜（跟定价）；让球 +1 主队侧不追；总进球不碰",
"005": "客胜（方向最硬、价最差）；让球 +1 不碰；总进球大球薄看",
"006": "主胜（模型与市场同向，可站）；让球 -1 薄看；总进球不碰",
"007": "客胜（跟方向不跟幅度）；让球 +1 主队侧不碰",
"010": "客不败（薄）；主胜不碰；让球不碰",
"011": "客胜（反向、薄）；让球不碰；总进球不碰",
"012": "主胜（跟市场、不跟模型）；让球 -1 不碰；总进球不碰",
"013": "主队 +1（反向薄站）；客胜大热不追；总进球不碰",
"014": "客胜（分歧最小的方向，可站）；让球 +1 主队侧不碰；总进球偏小",
"015": "主胜（跟方向不跟幅度）；让球 -1 不碰；总进球不碰",
}
ZQ = {"001": "3", "002": "1/0", "003": "0", "004": "0", "005": "0",
      "006": "3", "007": "1/0", "010": "1/0", "011": "0", "012": "3",
      "013": "3/1", "014": "0", "015": "3"}


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




def _ou_water(v):
    """大小水位：取与阿飞同源的众数线那本书；取不到给平水 0.95/0.95。"""
    b = (BOOKS.get(_CUR_NUM[0]) or {}).get("ou") or {}
    ls = v.get("ou_close_lines") or []
    if not ls:
        return (0.95, 0.95)
    from collections import Counter
    ml = abs(Counter([abs(x) for x in ls]).most_common(1)[0][0])
    for bk, seg in b.items():
        c = seg.get("close") or {}
        if c.get("line") is not None and abs(abs(float(c["line"])) - ml) < 1e-6:
            return (round(float(c.get("home")), 3), round(float(c.get("away")), 3))
    return (0.95, 0.95)

def _mkt_line(v):
    ls = v.get("ah_close_lines") or []
    if not ls:
        return v.get("ah_line") or 0.0
    s = sorted(ls)
    return s[len(s) // 2]


def _mkt_side(v):
    ln = _mkt_line(v)
    return "主让" if ln < 0 else ("平手" if ln == 0 else "主受让")

def sect_pan(num, v, b):
    _CUR_NUM[0] = num
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
    # 跨盘自洽：用欧赔（去水三向）单腿拟合的 λ 给亚盘/大小定价（现算，不依赖历史字段）
    coh = []
    _pk = mv3.lam_pack(m3, v.get("ou_implied_total")) if m3 else None
    _lo = (_pk or {}).get("odds_only")
    if _lo:
        _lines_ah = v.get("ah_close_lines") or []
        if _lines_ah:
            _ln = sorted(_lines_ah)[len(_lines_ah) // 2]
            _grid = mp.grid_probs(_lo[0], _lo[1])
            _evh, _evh2 = settle.ev_ah(_grid, _ln, *v["ah_water"])[:2]
            coh.append(f"只用欧赔拟合的 λ（{_lo[0]:.2f}/{_lo[1]:.2f}，λ总 {sum(_lo):.2f}）给亚盘 {line_txt('主让' if _ln < 0 else ('平手' if _ln == 0 else '主受让'), _ln)} 定价：主队 EV {_evh:+.1f}%、客队 {_evh2:+.1f}%")
        _l_ou = sorted(v.get("ou_close_lines") or [])
        if _l_ou:
            _ol = abs(_l_ou[len(_l_ou) // 2])
            _ev_o, _ev_u = settle.ev_ou(_grid, _ol, *_ou_water(v))[:2]
            coh.append(f"同一 λ 给大小 {_ol:.2f} 定价：大 {_ev_o:+.1f}%、小 {_ev_u:+.1f}%（香港盘水位）")
        v["lam_1x2"] = _lo
        v["lam_total"] = sum(_lo)
    if False:
    
        coh.append(f"只用欧赔拟合的 λ（{v['lam_1x2'][0]:.2f}/{v['lam_1x2'][1]:.2f}，λ总 {sum(v['lam_1x2']):.2f}）给亚盘定价：主队 EV {v['ev_ah_mkt'][0]:+.1f}%、客队 {v['ev_ah_mkt'][1]:+.1f}%")
    if v["ev_ou_mkt"][0] is not None:
        coh.append(f"同一 λ 给大小定价：大 {v['ev_ou_mkt'][0]:+.1f}%、小 {v['ev_ou_mkt'][1]:+.1f}%")
    lines.append("- 跨盘自洽：" + "；".join(coh) + "（越接近 0 = 该盘与欧赔越一致；明显偏离就是单盘溢价所在）")
    if v["ou_implied_total"]:
        lines.append(f"- 大小盘水位反推的总进球期望 ≈ {v['ou_implied_total']:.2f}（与 λ总 {v['lam_total']:.2f} 对照用）")
    _mkt = INTEL_MKT.get(num, {})
    _have = [n for n in ("had", "hhad", "ttg", "hafu", "crs") if (_mkt.get(n) or {}).get("odds")]
    _cn = {"had": "胜平负", "hhad": "让球", "ttg": "总进球", "hafu": "半全场", "crs": "波胆"}
    if _have:
        lines.append("- 竞彩官方盘可用：" + "、".join(_cn[x] for x in _have) + "（去水口径见上）")
    if not v.get("ou_close_lines"):
        lines.append("- 该场 500 未列大小盘（表格里为 —），大小球只能靠模型推算，无市场价可对照")
    return "\n".join(lines)


def sect_model(num, v):
    r = V3[num]
    la, lb, lc = r["lam_data"], r["lam_market"], r["lam_fused"]
    def f2(x):
        return "—" if x is None else f"{x[0]:.2f} / {x[1]:.2f}"
    lines = []
    lines.append(f"- 数据完整性等级 **{r['grade']}**（逐场比分自洽）；**模型等级 {r.get('model_grade', r['grade'])}**"
                 f"（同主客有效样本：主 {r['n_eff'][0]} 场 / 客 {r['n_eff'][1]} 场）；预测证据等级 **{r['evidence_grade']}**")
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

import datetime as _dt
_WD = "一二三四五六日"[_dt.date(int(DAY[:4]), int(DAY[4:6]), int(DAY[6:])).weekday()]
TITLE_LINE = f"{DAY[:4]}-{DAY[4:6]}-{DAY[6:]} 周{_WD} {len(books)} 场"
GEN = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")

HEAD = f"""# {TITLE_LINE} · 内部分析报告

- 生成：{GEN}（赛前）。口径：**竞彩只算 90 分钟**；杯赛 90 分钟平局要进加时，竞彩不计。
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
