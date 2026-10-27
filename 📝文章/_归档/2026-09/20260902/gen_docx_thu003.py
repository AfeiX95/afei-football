# -*- coding: utf-8 -*-
"""生成: 周四003_米亚尔比vs佐加顿斯_二番战能复制0-4吗_赛事前瞻.docx (R19 白底图规范)"""
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
CHART_DIR = os.path.join(BASE, "charts_thu003")
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

def bar_chart(title, cats, market, model, fname, ylim=80):
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

ch1 = os.path.join(CHART_DIR, "thu003_1x2.png")
ch2 = os.path.join(CHART_DIR, "thu003_over.png")
bar_chart("米亚尔比 vs 佐加顿斯 · 胜平负概率", ["主胜", "平局", "客胜"], [24, 23, 53], [18, 23, 59], ch1)
# 大小球分歧: 市场 vs 模型 vs H2H
fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=160)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
labels = ["市场定价", "后台模型", "H2H近10场"]
vals = [63, 53, 40]
bars = ax.bar(labels, vals, width=0.5, color=["#4fc3f7", "#37474f", "#ffd93d"], alpha=0.85, edgecolor="white")
for b in bars:
    ax.annotate(f"{b.get_height():.0f}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                ha="center", va="bottom", fontsize=9)
ax.set_ylim(0, 75)
ax.set_ylabel("大2.5 概率 (%)", fontsize=9)
ax.set_title("大2.5 三源分歧 · 市场跟随 4:0 惯性 vs 历史小球", fontsize=11, color="#1a237e", pad=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.35)
fig.tight_layout()
fig.savefig(ch2, facecolor="white", bbox_inches="tight")
plt.close(fig)

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
r = p.add_run("瑞超003佐加顿斯客战：0-4之后二番战，大胜还能复制吗")
set_cn_font(r, size=17, bold=True, color=C_DARK)
p.paragraph_format.space_after = Pt(4)

para(doc, "#米亚尔比  #佐加顿斯  #瑞超  #足球前瞻  #数据分析",
     size=9, color=C_GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

para(doc, "三天前佐加顿斯主场 4:0 把米亚尔比打得没脾气，三天后这俩又碰上了，还是米亚尔比主场。联赛里这么紧凑的二番战不常见，上一场的比分就像个倒计时炸弹：客队想再来一次，主队憋着复仇。", size=10.5)
para(doc, "结论先行：方向站佐加顿斯客胜，模型 59% 对市场 53%，方向扎实但幅度温和；真正要防的是\"刚赢 4:0 再来一场\"，净胜两球和大球预期都该打折，别拿上一场的剧本套这一场。", size=10.5, bold=True, color=C_DARK)

heading(doc, "一、三天二番战：0-4 的仇，主场还得了吗")
para(doc, "先看底子。佐加顿斯联赛第3（32分），客场 8 场 5胜1平2负、胜率 63%，近10场 6胜2平2负进23球只丢7球，头号射手利恩 18 场 13 球、中场赫格兰德一人送出全队 45% 的助攻，进攻多点开花还带组织核心。米亚尔比联赛第12（20分），主场 8 场只赢 3 场，近10场 2胜1平7负进9球丢18球：欧冠资格赛被布拉迪斯拉发淘汰、欧罗巴被萨尔茨堡双杀、联赛刚挨了佐加顿斯 4 球，双线溃败的士气，不是换个主场就能缓过来的。", size=10.5)
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
    ("米亚尔比胜", "24%", "18%", "-6pp", C_MAIN),
    ("平局", "23%", "23%", "0pp", C_DRAW),
    ("佐加顿斯胜", "53%", "59%", "+6pp", C_AWAY),
    ("大2.5", "≈63%", "53%", "-10pp", C_MAIN),
]
for i, (a, b, c_, d, tint) in enumerate(rows, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "⚔️ 战意：佐加顿斯第3在争欧战席位，无欧战分心、联赛可全力；米亚尔比 5 天后要打哥德堡的保级关键战，这场复仇战会不会拼尽全力，要打个问号，若主队战略性留力，客队反而更轻松。", size=10.5)
para(doc, "💰 信号：方向温和（+6pp），市场对客队定价没有明显过热，资金小幅流向佐加顿斯。真正的分歧在大小球：市场大2.5 高达 63%，明显在跟随上一场 4:0 的大胜惯性，可后台模型只给 53%，历史交锋近10场大球率更是只有 40%（场均 2.4 球），刚被血洗的主队主场多半会收缩摆大巴，市场这口大球汤，别急着喝。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：瑞典媒体常规叙事「佐加顿斯争欧战强势 vs 米亚尔比保级挣扎」，连续交锋让客队心理占优是最大共识。", size=10.5)
para(doc, "高概率比分：首选 1-2，次选 0-1，留意 1-1。", size=10.5, bold=True, color=C_DARK)

heading(doc, "二、二番战的三个剧本")
para(doc, "剧本A（六成）：客队小胜收工。佐加顿斯控住场面进 1-2 球，米亚尔比主场进一个挽尊，比分 0-1 / 1-2，上一场 4:0 让客队不用再证明自己，收着踢更常见。", size=10.5)
para(doc, "剧本B（两成半）：主队摆大巴偷平。米亚尔比被血洗后学乖了，主场全线收缩打反击，佐加顿斯攻坚乏力，1-1 / 0-0，历史交锋米亚尔比主场对佐加顿斯也常出 1:1。", size=10.5)
para(doc, "剧本C（一成半）：复仇战大爆发。主队破罐破摔对攻，双方都放开，2-2 甚至 3-2 的高比分，但米亚尔比近10场丢了 18 球，对攻等于送。", size=10.5)

mt = doc.add_table(rows=2, cols=5)
mt.style = "Table Grid"; mt.alignment = WD_TABLE_ALIGNMENT.CENTER
mhdr = ["维度", "方向", "门槛", "进球", "比分"]
for j, h in enumerate(mhdr):
    c = mt.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
mrow = ["判断", "佐加顿斯占优", "净胜2球谨慎", "倾向小比分", "1-2 / 0-1 / 1-1"]
for j, v in enumerate(mrow):
    c = mt.rows[1].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j in (1, 4)))

heading(doc, "三、佐加顿斯净胜两球，值不值得追")
para(doc, "让球线主队+1：市场给米亚尔比受让 46% 的保护，模型 41%，两边都承认主队+1 有支撑。换句话说，佐加顿斯净胜2球的概率模型只给 35%，还有 24% 的走盘风险卡在净胜1球上。上一场 4:0 是大胜没错，但二番战里主队不会用同一套姿势挨打，这场让球方向的性价比，明显不如干脆利落的方向客胜。", size=10.5)
doc.add_picture(ch2, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

para(doc, "这场说白了：佐加顿斯赢面清楚，赢两球难。方向跟客队，比分守 1-2 / 0-1，1:1 揣兜里防一手，大球那口汤别碰。你觉得这场二番战，佐加顿斯能复制 4:0 吗？评论区留个比分，赛后回来验证。", size=10.5, bold=True)
para(doc, "难说。真说不好。", size=10.5, bold=True)
para(doc, "数据来源：懂球帝、ESPN、各队官网", size=8.5, color=C_GRAY)
para(doc, "注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。", size=8.5, color=C_GRAY)

out = os.path.join(BASE, "周四003_米亚尔比vs佐加顿斯_二番战能复制0-4吗_赛事前瞻.docx")
doc.save(out)
print("SAVED:", out)
