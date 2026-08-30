# -*- coding: utf-8 -*-
"""生成: 芬超双场001+002_主队让1球全是坑_头条深度版.docx (R19 白底图规范)"""
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
    ax.set_ylim(0, 75)
    ax.set_ylabel("概率 (%)", fontsize=9)
    ax.set_title(title, fontsize=11, color="#1a237e", pad=8)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(fname, facecolor="white", bbox_inches="tight")
    plt.close(fig)

ch1 = os.path.join(CHART_DIR, "bar_m1.png")
ch2 = os.path.join(CHART_DIR, "bar_m2.png")
bar_chart("国际图尔 vs 库奥皮奥 · 胜平负概率（榜首战）", [41, 28, 31], [36, 29, 35], ch1)
bar_chart("赫尔火花 vs TPS图尔 · 胜平负概率", [47, 25, 28], [42, 25, 34], ch2)

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
r = p.add_run("芬超双场001+002：主队让1球全是坑，受让侧才安全")
set_cn_font(r, size=17, bold=True, color=C_DARK)
p.paragraph_format.space_after = Pt(4)

para(doc, "#国际图尔  #库奥皮奥  #赫尔火花  #TPS图尔  #芬超  #足球前瞻  #数据分析", size=9, color=C_GRAY,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

para(doc, "很多人看芬超凌晨双场，只看排名：国际图尔第2、赫尔火花第3，两个主队都被市场看好（41%/47%）。但后台模型跑完，发现两场有个共性：主队让1球都是坑。国际图尔让1球要净胜2球，双共识只有16-19%；赫尔火花更别指望大胜，净胜2球双共识22-24%，TPS还带了客场10%胜率的帽子来受让。", size=10.5)
para(doc, "结论先行：两场的钱不在\"主队赢两球\"，在受让一侧（库奥皮奥+1 63.8% / TPS+1 58.4%）。而这场的底色，一场是平局（国际图尔主场50%平率、交锋5平），一场是大球（赫尔火花主场场均2.0球）。", size=10.5, bold=True, color=C_DARK)

heading(doc, "第一场：国际图尔 vs 库奥皮奥 — 榜首战，主队让1球是伪热门")
para(doc, "很多人看到芬超榜首战（第2 vs 第1），以为主场作战的国际图尔占优。但拆开看：国际图尔主场确实不败率90%，可平率50%（10场平5场）；而库奥皮奥是它的压制者，近10次交锋4胜（国际图尔只赢1场）、平5场，客场胜率还有60%。", size=10.5)
para(doc, "⚔️ 战意：国际图尔39分落后榜首4分，主场榜首战必须抢分；库奥皮奥43分守榜首，10-16 还有欧协联正赛（vs 特拉布宗），有激励，但双线也可能分心。", size=10.5)
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
    ("国际图尔胜", "41%", "36%", "-5.0pp", C_MAIN),
    ("平局", "28%", "29%", "+1.5pp", C_DRAW),
    ("库奥皮奥胜", "31%", "35%", "+3.5pp", C_AWAY),
    ("大2.5", "≈63%", "42%", "-21pp", C_MAIN),
]
for i, (a, b, c_, d, tint) in enumerate(rows, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "💰 信号：市场41%主微热，模型跑完是五五开（36% vs 35%），库奥皮奥被低估3.5pp（H2H压制+榜首+客场60%胜率）。主队让1球要净胜2球，双共识只有16-19%（榜首战主让球=伪热门），库奥皮奥+1 63.8%是全场最干净信号。平局底色也浓：交锋5平/10 + 主场50%平率，1:1 直接顶成市场最低价。大小球模型42% vs 市场63%有分歧，双方场均才1.2/1.3球，不追大。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：芬媒常规叙事「榜首战+国际图尔主场不败 vs 库奥皮奥交锋压制」，近10次交锋5平支持拉锯。", size=10.5)
para(doc, "高概率比分：首选 1-1，次选 1-0，留意 0-1。", size=10.5, bold=True, color=C_DARK)

heading(doc, "第二场：赫尔火花 vs TPS图尔 — 主强客弱，大球才是主线")
para(doc, "很多人看到赫尔火花主场60%胜率、刚连续客场逆转国际图尔和赫尔辛基，觉得大胜稳了。但TPS虽然客场10场只赢1场（10%胜率），带着受让1球的保护，赫尔火花净胜2球的双共识只有22-24%，主队赢面清楚，赢两球难。", size=10.5)
para(doc, "⚔️ 战意：赫尔火花第3（35分）争冠组边缘，主场抢分；TPS第7中游无压力，客场目标就是不崩，近2个客场还回暖了（3:1瓦萨、1:1库奥皮奥）。", size=10.5)
doc.add_picture(ch2, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl2 = doc.add_table(rows=5, cols=4)
tbl2.style = "Table Grid"; tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, h in enumerate(hdr):
    c = tbl2.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows2 = [
    ("赫尔火花胜", "47%", "42%", "-5.0pp", C_MAIN),
    ("平局", "25%", "25%", "0pp", C_DRAW),
    ("TPS胜", "28%", "34%", "+5.7pp", C_AWAY),
    ("大2.5", "≈60%", "61%", "+1pp", C_MAIN),
]
for i, (a, b, c_, d, tint) in enumerate(rows2, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl2.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "💰 信号：方向看主（42% vs 47%一致），但主队让1球净胜2球双共识22-24%（中游主队让球陷阱，前面韩职/挪超都有教训），TPS+1 58.4%才是保护层。这场最干净的不是方向，是大球双共识：模型61%和市场60%罕见一致（赫尔火花主场场均进2.0球）。交锋历史上TPS压制过（近10次6胜），但2026年两次交手赫尔火花1胜1平已转向，旧账不用太当回事。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：芬媒叙事「赫尔火花主场强势 vs TPS客场惨淡」，近况热度盖过交锋旧账。", size=10.5)
para(doc, "高概率比分：首选 1-1，次选 2-1，留意 1-2。", size=10.5, bold=True, color=C_DARK)

heading(doc, "最终判断：芬超双场矩阵")
mt = doc.add_table(rows=3, cols=4)
mt.style = "Table Grid"; mt.alignment = WD_TABLE_ALIGNMENT.CENTER
mhdr = ["场次", "后台模型", "高概率比分", "核心信号"]
for j, h in enumerate(mhdr):
    c = mt.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
mrows = [
    ("国际图尔 vs 库奥皮奥", "五五开 36/29/35", "1-1 / 1-0 / 0-1", "库奥皮奥+1 63.8%；主让1球打穿16-19%；平局底色"),
    ("赫尔火花 vs TPS图尔", "主42% vs 市场47%", "1-1 / 2-1 / 1-2", "大球共识61%；TPS+1 58.4%；主让1球打穿22-24%"),
]
for i, row in enumerate(mrows, start=1):
    for j, v in enumerate(row):
        c = mt.rows[i].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
para(doc, "", size=4, space_after=2)
para(doc, "两场共同规律：主队让1球都是坑（净胜2球双共识16-24%），受让一侧（库奥皮奥+1 / TPS+1）是安全区；底色正好互补，一场平局一场大球。说白了，芬超这两场别贪\"主队大胜\"，拿好受让，看 1:1 和大球就够了。", size=10.5, bold=True)

heading(doc, "互动钩子", size=12)
para(doc, "芬超双场拆完了。榜首战你敢押国际图尔赢两球，还是信库奥皮奥客场带走？赫尔火花主场场均2球，TPS客场10%胜率，你赌大球还是受让？评论区留下你的预测比分，赛后我们用实战赛果复盘模型精度。", size=10.5)
para(doc, "难说。真说不好。", size=10.5, bold=True)
para(doc, "数据来源：懂球帝、ESPN、各队官网", size=8.5, color=C_GRAY)
para(doc, "注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。", size=8.5, color=C_GRAY)

out = os.path.join(BASE, "芬超双场001+002_主队让1球全是坑_头条深度版.docx")
doc.save(out)
print("SAVED:", out)
