# -*- coding: utf-8 -*-
"""生成: 周四005_图卢兹vs里尔_欧冠前夜大胜打问号_赛事前瞻.docx (R19 白底图规范)"""
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
CHART_DIR = os.path.join(BASE, "charts_thu005")
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

def bar_chart(title, cats, market, model, fname, ylim=75):
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

ch1 = os.path.join(CHART_DIR, "thu005_1x2.png")
ch2 = os.path.join(CHART_DIR, "thu005_h2h.png")
bar_chart("图卢兹 vs 里尔 · 胜平负概率", ["主胜", "平局", "客胜"], [29, 27, 44], [17, 22, 61], ch1)
# H2H: 里尔 7胜1平2负
fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=160)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
labels = ["里尔胜", "平局", "图卢兹胜"]
vals = [7, 1, 2]
bars = ax.bar(labels, vals, width=0.5, color=["#ff6b6b", "#ffd93d", "#4fc3f7"], alpha=0.85, edgecolor="white")
for b in bars:
    ax.annotate(f"{b.get_height():.0f}场", (b.get_x() + b.get_width() / 2, b.get_height()),
                ha="center", va="bottom", fontsize=9)
ax.set_ylim(0, 9)
ax.set_ylabel("近10次交锋 (场)", fontsize=9)
ax.set_title("H2H 近10次交锋 · 里尔 7胜1平2负（全法甲正赛）", fontsize=11, color="#1a237e", pad=8)
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
r = p.add_run("周四005法甲：里尔客战图卢兹，欧冠前夜大胜要打问号")
set_cn_font(r, size=17, bold=True, color=C_DARK)
p.paragraph_format.space_after = Pt(4)

para(doc, "#图卢兹  #里尔  #法甲  #足球前瞻  #数据分析",
     size=9, color=C_GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

para(doc, "图卢兹开场两轮不胜，主场还 0:2 输给里昂，这周碰上的偏偏是对自己 10 场没赢过的里尔。看纸面，里尔客场全胜、刚逼平巴黎圣曼，H2H 近10次 7胜1平2负还带一场 4:0，牌面一边倒。", size=10.5)
para(doc, "结论先行：方向站里尔客胜，模型 61% 对市场 44%，方向硬；但里尔 5 天后要打欧冠首轮，这场净胜两球和轮换都是变量，别把 0:4 的旧账当成必然重演。", size=10.5, bold=True, color=C_DARK)

heading(doc, "一、H2H 克星是真，但这场有场外变量")
para(doc, "里尔对图卢兹的压制不是印象流：近10次交手 7胜1平2负，全部是法甲正赛，没有热身赛掺水，去年 4 月还在图卢兹主场踢了个 0:4。图卢兹这边，联赛两轮 0 胜，主场 0:2 里昂，头号射手罗两场才进 1 球，进攻端撑不起场面。数据面，里尔方向没有悬念。", size=10.5)
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
    ("图卢兹胜", "29%", "17%", "-12pp", C_MAIN),
    ("平局", "27%", "22%", "-5pp", C_DRAW),
    ("里尔胜", "44%", "61%", "+17pp", C_AWAY),
    ("大2.5", "≈57%", "58%", "+1pp", C_MAIN),
]
for i, (a, b, c_, d, tint) in enumerate(rows, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "⚔️ 战意：里尔第3在追欧战区，但 5 天后欧冠小组赛首轮主场打贝蒂斯，主教练会不会为欧冠留一手、轮换吉鲁这批主力，是这场最大的问号；图卢兹保级区边缘无欧战分心，主场可以全力一搏。", size=10.5)
para(doc, "💰 信号：方向 +17pp 是本批较强信号，市场客胜定价没给满，模型看高一线。真正要留意的是让球：里尔净胜2球的概率模型给 37%，市场只认 21%，差距大，可 23% 的走盘风险卡在净胜1球上，欧冠前夜里尔一旦控制节奏收着踢，净胜2球就悬了。", size=10.5)
doc.add_picture(ch2, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
para(doc, "🌍 外部视角：综合数据倾向：法国媒体常规叙事「里尔状态火热 vs 图卢兹开局挣扎」，H2H 一边倒让主队爆冷想象空间很小，分歧全在里尔轮换幅度。", size=10.5)
para(doc, "高概率比分：首选 1-2，次选 0-2，留意 1-1。", size=10.5, bold=True, color=C_DARK)

heading(doc, "二、三个剧本：轮换幅度决定走向")
para(doc, "剧本A（五成半）：里尔全主力小胜收工。客场拿下 1-2 球，图卢兹进一个挽尊，比分 1-2 / 0-1，欧冠前夜不需要大胜证明自己。", size=10.5)
para(doc, "剧本B（两成半）：里尔轮换留力，图卢兹偷分。欧冠在即轮换三四人，客队攻坚乏力，1-1 甚至 0-0，图卢兹主场平局体质（市场 1:1 定价全场最低）借机发威。", size=10.5)
para(doc, "剧本C（两成）：里尔不留情面复刻 0:4。图卢兹防线太弱压不住，客队一波流带走，0-3 / 0-4，但概率低，主队主场不会像上次那么崩。", size=10.5)

mt = doc.add_table(rows=2, cols=5)
mt.style = "Table Grid"; mt.alignment = WD_TABLE_ALIGNMENT.CENTER
mhdr = ["维度", "方向", "门槛", "进球", "比分"]
for j, h in enumerate(mhdr):
    c = mt.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
mrow = ["判断", "里尔占优", "净胜2球谨慎", "中性", "1-2 / 0-2 / 1-1"]
for j, v in enumerate(mrow):
    c = mt.rows[1].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j in (1, 4)))

heading(doc, "三、让球和大球怎么选")
para(doc, "让球线主队+1：市场给图卢兹受让 55% 的保护，模型只有 39%，两边分歧明显。图卢兹+1 有支撑，说明市场认为里尔净胜2球不容易，加上欧冠轮换变量，这场里尔-1 的性价比一般，方向客胜比让球干净。大小球反而是全场最没分歧的一项，模型 58% 和市场 57% 几乎重合，跟不跟都行，不构成独立信号。", size=10.5)

para(doc, "这场说白了：里尔赢面硬，赢两球要打问号。方向跟客队，比分守 1-2 / 0-2，1:1 防一手，让球别贪。你觉得里尔会为欧冠轮换吗？评论区留个比分，赛后回来验证。", size=10.5, bold=True)
para(doc, "难说。真说不好。", size=10.5, bold=True)
para(doc, "数据来源：懂球帝、ESPN、各队官网", size=8.5, color=C_GRAY)
para(doc, "注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。", size=8.5, color=C_GRAY)

out = os.path.join(BASE, "周四005_图卢兹vs里尔_欧冠前夜大胜打问号_赛事前瞻.docx")
doc.save(out)
print("SAVED:", out)
