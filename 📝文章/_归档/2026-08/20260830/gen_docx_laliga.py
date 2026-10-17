# -*- coding: utf-8 -*-
"""生成: 西甲双场006+012_奥萨苏纳怕闷平巴萨深盘求净3球_头条版.docx (R19 白底图规范)"""
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
CHART_DIR = os.path.join(BASE, "charts")
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

def bar_chart(title, cats, vals, highlight_idx, fname):
    x = list(range(len(cats)))
    colors = ["#9e9e9e"] * len(cats)
    colors[highlight_idx] = "#" + C_DRAW if highlight_idx == 1 else "#" + C_MAIN
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    bars = ax.bar(x, vals, width=0.55, color=colors, edgecolor="white")
    for b in bars:
        ax.annotate(f"{b.get_height():.0f}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=10)
    ax.set_ylim(0, max(vals) + 18)
    ax.set_ylabel("概率 (%)", fontsize=9)
    ax.set_title(title, fontsize=11, color="#1a237e", pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(fname, facecolor="white", bbox_inches="tight")
    plt.close(fig)

ch1 = os.path.join(CHART_DIR, "bar_m1.png")
ch2 = os.path.join(CHART_DIR, "bar_m2.png")
bar_chart("奥萨苏纳 vs 赫塔费 · 胜平负市场定价（平局高亮）", ["主胜", "平局", "客胜"], [45, 33, 22], 1, ch1)
bar_chart("巴萨 vs 巴列卡诺 · 让-2 三向（净胜3+ 高亮）", ["净胜3+", "净胜2", "≤净1/平负"], [45, 21, 34], 0, ch2)

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
r = p.add_run("西甲006+012：奥萨苏纳怕闷平，巴萨深盘求净3球")
set_cn_font(r, size=17, bold=True, color=C_DARK)
p.paragraph_format.space_after = Pt(4)

para(doc, "#奥萨苏纳  #赫塔费  #巴萨  #巴列卡诺  #西甲  #足球前瞻  #数据分析", size=9, color=C_GRAY,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

para(doc, "西甲这两场，一场是中游互搏，一场是豪门深盘，完全是两种玩法。奥萨苏纳对赫塔费，市场把平局顶成了全场级最低价，中游谁都不想输的典型闷局；巴萨对巴列卡诺，机构直接开到让2球，摆明了要赢三球才算数。", size=10.5)
para(doc, "结论先行：奥萨苏纳这场，别碰主队让1球（净胜2球双共识不到两成），平局小比分是主线；巴萨这场，深盘打出净胜2球有近7批6/8的惯性背书，但巴列卡诺+2 也别当便宜捡，净胜2球走盘的概率不低。", size=10.5, bold=True, color=C_DARK)

heading(doc, "第一场：奥萨苏纳 vs 赫塔费 — 中游互搏，平局土壤最厚")
para(doc, "奥萨苏纳第7对赫塔费第11，排名接近、状态平庸，市场给主队45.4%微热，但平局32.8%是全档最高，平价直接压到全场最低，机构已经把\"谁都不想输\"写在价格里了。", size=10.5)
doc.add_picture(ch1, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl = doc.add_table(rows=4, cols=3)
tbl.style = "Table Grid"; tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr = ["结果", "市场定价", "说明"]
for j, h in enumerate(hdr):
    c = tbl.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows = [
    ("奥萨苏纳胜", "45.4%", "主微热，主场略占优", C_MAIN),
    ("平局", "32.8%", "全场级最高（中游互搏闷局核心信号）", C_DRAW),
    ("赫塔费胜", "21.7%", "客队不热", C_AWAY),
]
for i, (a, b, c_, tint) in enumerate(rows, start=1):
    for j, v in enumerate([a, b, c_]):
        cell = tbl.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 1))
        if j < 2:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "⚔️ 战意：两支中游队，第7对第11，既没争冠压力也没保级恐慌，赢不赢都行，但主场不能难看，这种局最典型的结局就是 0:0 或 1:1。", size=10.5)
para(doc, "💰 信号：最关键的陷阱在主队让1球：奥萨苏纳要净胜2球，双共识只有19.1%（中游主队让球的老毛病，近两批10场全没打出来），赫塔费+1 有53.7%的保护。这场没有强队，没有深盘，只有一层厚厚的平局土壤，1:1 是市场最低价，别想太多。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：西甲中游互搏的常规叙事「谁都不想输」，两队排名接近、近况平庸，机构平局定价全场最低——闷平土壤是共识。", size=10.5)
para(doc, "高概率比分：首选 1-1，次选 1-0，留意 0-0。", size=10.5, bold=True, color=C_DARK)

heading(doc, "第二场：巴萨 vs 巴列卡诺 — 豪门深盘，大胜有惯性")
para(doc, "巴萨第3打巴列卡诺第15，机构没开胜平负单固，直接给让2球：巴萨净胜2球及以上合计66.5%，其中净胜3球45.4%，市场认为巴萨不仅赢，还得赢得漂亮。", size=10.5)
doc.add_picture(ch2, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl2 = doc.add_table(rows=4, cols=3)
tbl2.style = "Table Grid"; tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, h in enumerate(hdr):
    c = tbl2.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows2 = [
    ("巴萨净胜3+", "45.4%", "市场第一重心", C_MAIN),
    ("巴萨净胜2（走盘）", "21.1%", "刚好赢两球", C_DRAW),
    ("净胜1/平/负", "33.5%", "巴列卡诺+2 赢盘侧", C_AWAY),
]
for i, (a, b, c_, tint) in enumerate(rows2, start=1):
    for j, v in enumerate([a, b, c_]):
        cell = tbl2.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 1))
        if j < 2:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "⚔️ 战意：巴萨主场打下游，赢球是底线，净胜球关乎争冠小分；巴列卡诺客场目标就是少输，摆大巴是标准剧本。", size=10.5)
para(doc, "💰 信号：深盘打出净胜2球有近7批6/8的惯性（皇马/拜仁/多特都是大胜局），而且强队让球的下修教训反复被证伪：巴萨上轮让1球净胜2球收场，皇马 4:1，机构这次开2球不是乱开。但要清醒：净胜2球走盘的概率21.1%不算低，巴萨若 2:0 收工（上轮毕尔巴鄂就是 2:0），深盘走盘不输不赢。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：西甲豪门主场打下游的标准剧本「大胜收官」，巴萨上轮已净胜2球（毕尔巴鄂），深盘惯性支持净胜3球方向。", size=10.5)
para(doc, "高概率比分：首选 3-0，次选 2-0，留意 3-1。", size=10.5, bold=True, color=C_DARK)

heading(doc, "最终判断：西甲双场矩阵")
mt = doc.add_table(rows=3, cols=3)
mt.style = "Table Grid"; mt.alignment = WD_TABLE_ALIGNMENT.CENTER
mhdr = ["场次", "核心信号", "高概率比分"]
for j, h in enumerate(mhdr):
    c = mt.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
mrows = [
    ("奥萨苏纳 vs 赫塔费", "平局32.8%全场级最高；主让1球净胜2球 19.1% 陷阱；赫塔费+1 53.7%", "1-1 / 1-0 / 0-0"),
    ("巴萨 vs 巴列卡诺", "深盘-2 净胜2+ 66.5%（近7批6/8）；净胜2走盘21.1%", "3-0 / 2-0 / 3-1"),
]
for i, row in enumerate(mrows, start=1):
    for j, v in enumerate(row):
        c = mt.rows[i].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 1))
para(doc, "", size=4, space_after=2)
para(doc, "两场完全是两种逻辑：一场在平局里找答案，一场在深盘里搏大胜。奥萨苏纳这场，闷平是主线，主队让1球别碰；巴萨这场，方向没悬念，纠结的只是净胜3球还是2球收工。", size=10.5, bold=True)

heading(doc, "互动钩子", size=12)
para(doc, "西甲双场拆完了。奥萨苏纳的闷平土壤你更信几分？巴萨这场你更看好净胜三球还是两球收工？评论区留下你的预测比分，赛后我们用实战赛果复盘模型精度。", size=10.5)
para(doc, "难说。真说不好。", size=10.5, bold=True)
para(doc, "数据来源：懂球帝、ESPN、各队官网", size=8.5, color=C_GRAY)
para(doc, "注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。", size=8.5, color=C_GRAY)

out = os.path.join(BASE, "西甲双场006+012_奥萨苏纳怕闷平巴萨深盘求净3球_头条版.docx")
doc.save(out)
print("SAVED:", out)
