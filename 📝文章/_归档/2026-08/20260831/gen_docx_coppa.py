# -*- coding: utf-8 -*-
"""生成: 意大利杯005+006_防线五伤撞数据掺水_头条深度版.docx (R19 白底图规范)"""
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
CHART_DIR = os.path.join(BASE, "charts_coppa")
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

def bar_chart(title, cats, vals1, vals2, label1, label2, fname, ylim=80):
    x = list(range(len(cats)))
    w = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    b1 = ax.bar([i - w / 2 for i in x], vals1, width=w, color="#4fc3f7", label=label1, edgecolor="white")
    b2 = ax.bar([i + w / 2 for i in x], vals2, width=w, color="#37474f", alpha=0.78, label=label2, edgecolor="white")
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.0f}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=10)
    ax.set_ylim(0, ylim)
    ax.set_ylabel("概率 (%)", fontsize=9)
    ax.set_title(title, fontsize=11, color="#1a237e", pad=8)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(fname, facecolor="white", bbox_inches="tight")
    plt.close(fig)

ch1 = os.path.join(CHART_DIR, "coppa_005.png")
ch2 = os.path.join(CHART_DIR, "coppa_006.png")
# 005: 胜平负 市场 vs 模型(口径A)
bar_chart("005 萨索洛 vs 弗洛西诺 · 胜平负概率", ["萨索洛胜", "平局", "弗洛西诺胜"], [50, 26, 24], [15, 18, 67], "市场定价", "后台模型", ch1, ylim=80)
# 006: 双口径对比（乌迪内斯胜/平/威尼斯胜）
bar_chart("006 乌迪内斯 vs 威尼斯 · 双口径对比", ["乌迪内斯胜", "平局", "威尼斯胜"], [32, 23, 45], [70, 20, 11], "模型A(近10场)", "模型B(意甲)", ch2, ylim=80)

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
r = p.add_run("意大利杯005+006：一个防线伤到崩，一个对手数据全是水")
set_cn_font(r, size=17, bold=True, color=C_DARK)
p.paragraph_format.space_after = Pt(4)

para(doc, "#萨索洛  #弗洛西诺  #乌迪内斯  #威尼斯  #意大利杯  #足球前瞻  #数据分析",
     size=9, color=C_GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

para(doc, "意大利杯第二轮两场连轴转，牌面一个比一个好看：萨索洛主场、乌迪内斯主场，市场都往主队那边靠。可后台模型拆完，两场主队的热度全都有水分——一个自家防线伤到快没人了，一个对面球队的数据根本是\"掺了水\"的。", size=10.5)
para(doc, "结论先行：005 萨索洛这场，方向可以站弗洛西诺（客队 +1 是全场最干净的保护层）；006 乌迪内斯这场，主队能赢但别指望大胜，1:1 的平局底色比想象中浓。", size=10.5, bold=True, color=C_DARK)

heading(doc, "第一场：萨索洛 vs 弗洛西诺 — 主队防线五伤，客队刚血洗佛罗伦萨")
para(doc, "这场的问题出在萨索洛自己身上。表面看它是意甲球队坐镇主场，市场给了 50% 的主胜定价，热得理直气壮。但翻开伤停名单：4 名后卫加 1 名后腰全伤——坎德、瓦卢凯维奇、奥登塔尔、皮耶拉尼奥洛、博洛卡，防线等于重建。再翻近10场数据，进 37 球吓死人，可里面藏着一场 22:1 打业余队的灌水，剔掉之后场均进球从 3.7 掉到 1.6，所谓\"火力强\"纯属假象。", size=10.5)
para(doc, "⚔️ 战意：萨索洛后续联赛要连打博洛尼亚、尤文图斯、AC米兰，这场杯赛大概率轮换，主力不会硬拼；弗洛西诺赛程宽松得多，杯赛可以全力。一个是\"顾不上\"，一个是\"想赢\"，动机不在一个层级。", size=10.5)
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
    ("萨索洛胜", "50%", "15%", "-35pp", C_MAIN),
    ("平局", "26%", "18%", "-8pp", C_DRAW),
    ("弗洛西诺胜", "24%", "67%", "+43pp", C_AWAY),
    ("弗洛西诺+1", "48%", "85%", "+37pp", C_AWAY),
]
for i, (a, b, c_, d, tint) in enumerate(rows, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "💰 信号：模型把弗洛西诺客胜拉到 67%，比市场 24% 高出 43 个点，是本批最大翻转。但模型内部两个口径差了 28 个点（38.9% vs 67.1%），翻转幅度太大，不能当铁律押方向。真正干净的是受让侧：弗洛西诺+1 模型 85% vs 市场 48%，加上它同主客交锋 6胜4平0负客场不败、刚在客场 3:0 血洗佛罗伦萨，这场客队不输球才是主线。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：意大利媒体常规叙事「萨索洛杯赛轮换 vs 弗洛西诺状态火热」，伤停名单是赛前最大变量。", size=10.5)
para(doc, "高概率比分：首选 1-2，次选 1-1，留意 0-2。", size=10.5, bold=True, color=C_DARK)

heading(doc, "第二场：乌迪内斯 vs 威尼斯 — 主队能赢，但别指望大胜")
para(doc, "乌迪内斯这场更像\"看着稳\"：意甲开局 3:2 逆转蒙扎、1:1 逼平科莫，1胜1平拿分势头不错；威尼斯呢，升班马意甲两连败、一球没进。市场给乌迪内斯 45% 主胜，合理。但后台模型跑出两套相反的结果：拿近10场算，威尼斯反而占优；拿意甲新赛季算，乌迪内斯 70% 大优。", size=10.5)
para(doc, "⚔️ 战意：乌迪内斯后续联赛要打拉齐奥、国际米兰，这场杯赛可能轮换主力；威尼斯意甲垫底处境，杯赛反而是找回信心的机会。单场淘汰，两边都有晋级动力，但乌迪内斯的投入度要打个问号。", size=10.5)
doc.add_picture(ch2, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl2 = doc.add_table(rows=5, cols=5)
tbl2.style = "Table Grid"; tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr2 = ["结果", "市场定价", "模型A", "模型B", "判断"]
for j, h in enumerate(hdr2):
    c = tbl2.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows2 = [
    ("乌迪内斯胜", "45%", "32%", "70%", "打折看主胜", C_MAIN),
    ("平局", "28%", "23%", "20%", "平局有底色", C_DRAW),
    ("威尼斯胜", "27%", "45%", "11%", "翻转不可信", C_AWAY),
    ("乌迪内斯-1", "22%", "16%", "46%", "不碰", C_AWAY),
]
for i, (a, b, c_, d, e_, tint) in enumerate(rows2, start=1):
    for j, v in enumerate([a, b, c_, d, e_]):
        cell = tbl2.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 4))
        if j < 4:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "💰 信号：威尼斯近10场 5胜2平3负、进27球，看着生猛，实际是意乙收官加热身灌水堆出来的（8:0、4:2 这种比分），意甲两连败零进球才是真实水平。所以模型A翻转威尼斯不能信，方向还是看乌迪内斯，但打折。关键在让球：乌迪内斯要净胜2球，模型两个口径一个 16% 一个 46%，自己都拿不准；威尼斯客场平率 60%（同主客 2胜6平2负），平局 28% 的定价不是白给的。说白了，乌迪内斯赢面清楚，赢两球难。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：意大利媒体叙事「乌迪内斯状态回暖 vs 威尼斯升班马挣扎」，杯赛轮换是最大变数。", size=10.5)
para(doc, "高概率比分：首选 1-1，次选 2-1，留意 1-0。", size=10.5, bold=True, color=C_DARK)

heading(doc, "两场一句话总结")
st = doc.add_table(rows=3, cols=3)
st.style = "Table Grid"; st.alignment = WD_TABLE_ALIGNMENT.CENTER
shdr = ["场次", "核心逻辑", "方向倾向"]
for j, h in enumerate(shdr):
    c = st.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
srows = [
    ("萨索洛 vs 弗洛西诺", "防线五伤 + 客队刚血洗佛罗伦萨", "弗洛西诺+1 最稳"),
    ("乌迪内斯 vs 威尼斯", "主队能赢但样本打架 + 平局底色", "乌迪内斯打折胜"),
]
for i, row in enumerate(srows, start=1):
    for j, v in enumerate(row):
        c = st.rows[i].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 2))

para(doc, "两场意大利杯放一起看就一句话：主队的热度都得打折扣。萨索洛是自家防线伤了，弗洛西诺+1 是全场最干净的数字；乌迪内斯是赢面清楚但赢两球难，1:1 揣兜里。你们觉得这两场哪场更容易爆冷？评论区留个比分，赛后回来验证。", size=10.5, bold=True)
para(doc, "难说。真说不好。", size=10.5, bold=True)
para(doc, "数据来源：懂球帝、ESPN、各队官网", size=8.5, color=C_GRAY)
para(doc, "注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。", size=8.5, color=C_GRAY)

out = os.path.join(BASE, "意大利杯005+006_防线五伤撞数据掺水_头条深度版.docx")
doc.save(out)
print("SAVED:", out)
