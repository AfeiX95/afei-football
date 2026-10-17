# -*- coding: utf-8 -*-
"""生成: 日职三场002-004_克星局最硬魔咒局要防_头条深度版.docx (R19 白底图规范)"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

BASE = r"I:\阿飞说球\_tmp_docx_out"
CHART_DIR = os.path.join(BASE, "charts_wed3")
os.makedirs(CHART_DIR, exist_ok=True)

C_MAIN = "4fc3f7"
C_DRAW = "ffd93d"
C_AWAY = "ff6b6b"
C_DARK = "1a237e"
C_GRAY = "9e9e9e"

def set_cn_font(run, size=10.5, bold=False, color=None, name="微软雅黑"):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)

def shade_cell(cell, hexcolor):
    cell._tc.get_or_add_tcPr().append(parse_xml(r'<w:shd {} w:val="clear" w:fill="{}"/>'.format(nsdecls("w"), hexcolor)))

def para(doc, text, size=10.5, bold=False, color=None, align=None, space_after=6):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text)
    set_cn_font(r, size=size, bold=bold, color=color)
    return p

def heading(doc, text, size=14, color=C_DARK, space_before=10):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    set_cn_font(r, size=size, bold=True, color=color)
    return p

def bar_chart(title, market, model, fname):
    cats = ["主胜", "平局", "客胜"]
    x = [0, 1, 2]
    w = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    colors = ["#" + c for c in (C_MAIN, C_DRAW, C_AWAY)]
    b1 = ax.bar([i - w / 2 for i in x], market, width=w, color=colors, label="市场定价", edgecolor="white")
    b2 = ax.bar([i + w / 2 for i in x], model, width=w, color="#37474f", alpha=0.78, label="后台模型", edgecolor="white")
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.0f}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=10)
    ax.set_ylim(0, 78)
    ax.set_ylabel("概率 (%)", fontsize=9)
    ax.set_title(title, fontsize=11, color="#1a237e", pad=8)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(fname, facecolor="white", bbox_inches="tight")
    plt.close(fig)

ch1 = os.path.join(CHART_DIR, "bar_002.png")
ch2 = os.path.join(CHART_DIR, "bar_003.png")
ch3 = os.path.join(CHART_DIR, "bar_004.png")
bar_chart("002 樱花 vs 柏太阳神 · 胜平负概率", [29, 26, 45], [21, 21, 57], ch1)
bar_chart("003 水户 vs 鹿岛 · 胜平负概率", [23, 27, 50], [14, 18, 68], ch2)
bar_chart("004 町田 vs 川崎 · 胜平负概率", [52, 25, 24], [61, 22, 18], ch3)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin = sec.bottom_margin = Cm(2.0)

style = doc.styles["Normal"]
style.font.name = "微软雅黑"
style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
style.font.size = Pt(10.5)

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("日职三场002-004：克星局最硬，两场平局魔咒要防")
set_cn_font(r, size=17, bold=True, color=C_DARK)
p.paragraph_format.space_after = Pt(4)

para(doc, "#大阪樱花  #柏太阳神  #水户蜀葵  #鹿岛鹿角  #町田泽维  #川崎前锋  #日职  #足球前瞻  #数据分析",
     size=9, color=C_GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

para(doc, "三场日职同一时间开球，牌面看起来各有各的热门：柏太阳神客场被看好、鹿岛鹿角客场被看好、町田主场被看好。但后台模型拆完，这三场的\"热度成色\"完全不同，有一场是克星碾压的硬局，有两场埋着平局魔咒。", size=10.5)
para(doc, "结论先行：003 水户vs鹿岛是克星局（鹿岛对水户近10次交锋7胜3平、从没输过），方向最硬；002 樱花vs柏和 004 町田vs川崎都带平局魔咒，方向要打折，比分要带 1:1。", size=10.5, bold=True, color=C_DARK)

heading(doc, "三场全景速览")
mt = doc.add_table(rows=4, cols=6)
mt.style = "Table Grid"; mt.alignment = WD_TABLE_ALIGNMENT.CENTER
mhdr = ["场次", "对阵", "机构胜率", "后台模型", "价值偏差", "高概率比分"]
for j, h in enumerate(mhdr):
    c = mt.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
mrows = [
    ("002", "樱花 vs 柏太阳神", "柏 45%", "柏 57%", "+12pp", "1-2 / 1-1 / 0-2"),
    ("003", "水户 vs 鹿岛", "鹿岛 50%", "鹿岛 68%", "+18pp", "1-2 / 0-2 / 1-1"),
    ("004", "町田 vs 川崎", "町田 52%", "町田 61%", "+9pp", "2-1 / 1-1 / 1-0"),
]
for i, row in enumerate(mrows, start=1):
    for j, v in enumerate(row):
        c = mt.rows[i].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9, bold=(j in (3, 4)))

heading(doc, "第一场：大阪樱花 vs 柏太阳神 — 状态碾压，但历史交锋全是平局")
para(doc, "柏太阳神开季4连胜领跑日职，进10球失4球，客场2战全胜；樱花主场2战全胜，但整个赛季只进了3球，火力完全不在一个档次。市场给柏45%的胜率，后台模型给到57%，方向一致，只是模型更狠。", size=10.5)
para(doc, "⚔️ 战意：柏太阳神榜首位置要守，后续还有亚冠精英客场（客战全北），但那是两周后的事，本场没有留力的理由；樱花主场作战想止住颓势，战意不缺，缺的是进球的人，头号射手蒂亚戈4场0首发，全队才进3球。", size=10.5)
doc.add_picture(ch1, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl = doc.add_table(rows=5, cols=4)
tbl.style = "Table Grid"; tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr = ["结果", "市场定价", "后台模型", "偏差"]
for j, h in enumerate(hdr):
    c = tbl.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows = [
    ("樱花胜", "29%", "21%", "-8pp", C_MAIN),
    ("平局", "26%", "21%", "-5pp", C_DRAW),
    ("柏太阳神胜", "45%", "57%", "+12pp", C_AWAY),
    ("大2.5", "≈56%", "67%", "+11pp", C_MAIN),
]
for i, (a, b, c_, d, tint) in enumerate(rows, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "💰 信号：分歧在柏能不能净胜2球：模型给35%，市场只认22%，市场忌惮的是历史交锋，近10次两队交手樱花2胜5平3负，平局占了一半。说白了，柏赢球的面很大，但\"稳胜两球\"这层窗户纸，历史数据不支持。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：日媒常规叙事「榜首状态碾压 vs 主场韧性」，历史交锋的高平局率是最大的分歧点。", size=10.5)
para(doc, "高概率比分：首选 1-2，次选 1-1，留意 0-2。", size=10.5, bold=True, color=C_DARK)

heading(doc, "第二场：水户蜀葵 vs 鹿岛鹿角 — 克星局，10次交锋没输过")
para(doc, "这场是三场里最干净的。鹿岛鹿角第2、4连胜、客场2战全胜进6球；水户第11、主场0胜2平还没赢过球。更狠的是交锋数据：近10次鹿岛对水户7胜3平0负，水户一胜难求，主场对鹿岛也是0胜2平3负。这不是状态问题，是血脉压制。", size=10.5)
para(doc, "⚔️ 战意：鹿岛追榜首（少赛追柏），客场拿3分是底线；水户中游偏下，主场想保平争胜，但近10场对鹿岛一场没赢过，心理劣势摆在那。", size=10.5)
doc.add_picture(ch2, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl2 = doc.add_table(rows=5, cols=4)
tbl2.style = "Table Grid"; tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, h in enumerate(hdr):
    c = tbl2.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows2 = [
    ("水户胜", "23%", "14%", "-9pp", C_MAIN),
    ("平局", "27%", "18%", "-9pp", C_DRAW),
    ("鹿岛胜", "50%", "68%", "+18pp", C_AWAY),
    ("大2.5", "≈47%", "68%", "+21pp", C_MAIN),
]
for i, (a, b, c_, d, tint) in enumerate(rows2, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl2.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "💰 信号：模型鹿岛68% vs 市场50%，是本批最大偏差。鹿岛头号射手莱奥·塞阿拉4场进6球、占全队进球67%，这是把双刃剑：他正常发挥，水户扛不住；他被针对性盯防，鹿岛进攻会打折。让球层面鹿岛净胜2球模型给46%，市场只认24%，同样是本批最大分歧。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：日媒叙事「鹿岛客场火力 vs 水户主场不胜」，交锋0胜的克星属性让冷门想象空间很小。", size=10.5)
para(doc, "高概率比分：首选 1-2，次选 0-2，留意 1-1。", size=10.5, bold=True, color=C_DARK)

heading(doc, "第三场：町田泽维 vs 川崎前锋 — 主队最热，偏偏主场没赢过客队")
para(doc, "町田这场的牌面最好看：赛季不败、净胜10球、第3名，市场给52%主胜，模型给到61%。但有两块石头压着：一是町田的主场优势其实没数据撑腰，主场就踢了1场；二是交锋记录，町田主场对川崎0胜2平1负，近3次交手全是平局（1:1、1:1、2:2）。", size=10.5)
para(doc, "⚔️ 战意：町田第3想咬住前二，主场抢分意愿强；川崎1胜3平0负是不败的平局大师，客场2连平，客场目标就是带走1分，这种\"强队想赢、中游想平\"的对局，平局魔咒最容易应验。", size=10.5)
doc.add_picture(ch3, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl3 = doc.add_table(rows=5, cols=4)
tbl3.style = "Table Grid"; tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, h in enumerate(hdr):
    c = tbl3.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows3 = [
    ("町田胜", "52%", "61%", "+9pp", C_MAIN),
    ("平局", "25%", "22%", "-3pp", C_DRAW),
    ("川崎胜", "24%", "18%", "-6pp", C_AWAY),
    ("大2.5", "≈56%", "58%", "+2pp", C_MAIN),
]
for i, (a, b, c_, d, tint) in enumerate(rows3, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl3.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "💰 信号：町田方向模型+9pp有支持，但不够极端（对比鹿岛+18pp）。交锋近3次全平 + 川崎客场2连平，市场25%的平局定价不是白给的。模型自己也摇摆：让球净胜2球两个口径一个37%一个49%，说明町田大胜这件事，模型自己都拿不准。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：日媒叙事「不败黑马主场 vs 平局大师客场」，交锋惯性比纸面排名更值得警惕。", size=10.5)
para(doc, "高概率比分：首选 2-1，次选 1-1，留意 1-0。", size=10.5, bold=True, color=C_DARK)

heading(doc, "三场一句话总结")
st = doc.add_table(rows=4, cols=3)
st.style = "Table Grid"; st.alignment = WD_TABLE_ALIGNMENT.CENTER
shdr = ["场次", "核心逻辑", "方向倾向"]
for j, h in enumerate(shdr):
    c = st.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
srows = [
    ("樱花 vs 柏太阳神", "状态碾压 vs 交锋平局魔咒", "柏占优，防平"),
    ("水户 vs 鹿岛", "克星血脉压制 + 客场火力", "鹿岛最硬"),
    ("町田 vs 川崎", "主队最热但主场没赢过客队", "町田占优，防平"),
]
for i, row in enumerate(srows, start=1):
    for j, v in enumerate(row):
        c = st.rows[i].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 2))

para(doc, "三场看下来就一句话：克星局信数据（鹿岛），魔咒局信交锋（樱花和町田都别贪大胜）。鹿岛那场是本批最干净的方向，另外两场把 1:1 揣兜里比什么都稳。你们觉得，这三场哪场最容易出平局？评论区留个比分，赛后回来验证。", size=10.5, bold=True)
para(doc, "难说。真说不好。", size=10.5, bold=True)
para(doc, "数据来源：懂球帝、ESPN、各队官网", size=8.5, color=C_GRAY)
para(doc, "注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。", size=8.5, color=C_GRAY)

out = os.path.join(BASE, "日职三场002-004_克星局最硬魔咒局要防_头条深度版.docx")
doc.save(out)
print("SAVED:", out)
