# -*- coding: utf-8 -*-
"""生成: 周四006_皇社vs塞尔塔_全队1球市场偏看大球谁错了_赛事前瞻.docx (R19 白底图规范)"""
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
CHART_DIR = os.path.join(BASE, "charts_thu006")
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

def bar_chart(title, cats, market, model, fname, ylim=70):
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

ch1 = os.path.join(CHART_DIR, "thu006_1x2.png")
ch2 = os.path.join(CHART_DIR, "thu006_over.png")
bar_chart("皇社 vs 塞尔塔 · 胜平负概率", ["主胜", "平局", "客胜"], [48, 26, 26], [50, 28, 22], ch1)
# 大小球分歧
fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=160)
fig.patch.set_facecolor("white")
ax.set_facecolor("white")
labels = ["市场定价", "后台模型", "两队联赛场均(×2.5基准)"]
vals = [57, 40, 33]
bars = ax.bar(labels, vals, width=0.5, color=["#4fc3f7", "#37474f", "#ffd93d"], alpha=0.85, edgecolor="white")
for b in bars:
    ax.annotate(f"{b.get_height():.0f}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                ha="center", va="bottom", fontsize=9)
ax.set_ylim(0, 70)
ax.set_ylabel("大2.5 概率 (%)", fontsize=9)
ax.set_title("大2.5 分歧 · 市场 57% vs 模型 40%", fontsize=11, color="#1a237e", pad=8)
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
r = p.add_run("周四006皇社vs塞尔塔：全队只进1球，市场偏看大球谁错了")
set_cn_font(r, size=16, bold=True, color=C_DARK)
p.paragraph_format.space_after = Pt(4)

para(doc, "#皇家社会  #塞尔塔  #西甲  #足球前瞻  #数据分析",
     size=9, color=C_GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

para(doc, "塞尔塔开季三场只进了 1 个球，进这球的还是 34 岁的老将阿斯帕斯。就这么一支球队，市场却把大球预期抬到 57%，后台模型跑完只剩 40%。到底是市场高估了这场能进球，还是模型漏了什么？", size=10.5)
para(doc, "结论先行：这场是典型的定价精准局，主队方向双方都认 48-50%，没有便宜可占；真正的分歧全在大球上，模型站在小球侧，两队联赛场均加起来才 1.3 球，这场闷局概率比想象中高。", size=10.5, bold=True, color=C_DARK)

heading(doc, "假象一：皇社近10场输麻了？那是热身赛的账")
para(doc, "翻近10场，皇家社会 3胜1平6负，看着像要崩。可拆开看：里面 7 场是俱乐部热身，输的对手包括波城FC、科隆、图卢兹，热身赛本来就练阵容试新人，战绩当不得真。真正的联赛口径是 3 轮 1胜2负：主场 2:1 西班牙人回暖，客场输皇马、贝蒂斯是赛程硬。别被热身赛的负场吓住，主场那场胜利才是最近的真实状态。", size=10.5)
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
    ("皇社胜", "48%", "50%", "+2pp", C_MAIN),
    ("平局", "26%", "28%", "+2pp", C_DRAW),
    ("塞尔塔胜", "26%", "22%", "-4pp", C_AWAY),
    ("大2.5", "≈57%", "40%", "-17pp", C_MAIN),
]
for i, (a, b, c_, d, tint) in enumerate(rows, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)

heading(doc, "假象二：塞尔塔防守能苟？进攻是真没有")
para(doc, "塞尔塔客场 0:0 闷平过巴伦西亚，看着像防守型球队。这话一半对：它确实能摆大巴，但代价是进攻彻底没了。联赛 3 场全队只进 1 球，而且这 1 球来自 34 岁、3 场只首发 1 次的阿斯帕斯，助攻也全靠罗曼一个人。锁死阿斯帕斯，塞尔塔基本没有第二套破门方案。指望这种球队打出大球，等于指望它突然会踢球了。", size=10.5)

heading(doc, "假象三：TTG 定价 2 球档很低？看两队场均再说")
para(doc, "市场大2.5 给到 57%，参考的是 H2H 最近一场 3:1。但把镜头拉远：皇社联赛 3 场进 3 球、塞尔塔 3 场进 1 球，合计场均 1.3 球；近10次交锋大球率也只有 40%。皇社主场小胜 + 塞尔塔摆大巴，最可能的画面是 1-0、1-1、0-0 这种闷局，而不是对攻大战。", size=10.5)
doc.add_picture(ch2, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

heading(doc, "这场的关键：方向没肉，小球才是差异点")
mt = doc.add_table(rows=5, cols=3)
mt.style = "Table Grid"; mt.alignment = WD_TABLE_ALIGNMENT.CENTER
mhdr = ["维度", "判断", "依据"]
for j, h in enumerate(mhdr):
    c = mt.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
mrows = [
    ("方向", "皇社小胜", "主场 1/1 + 塞尔塔客场无进球能力"),
    ("门槛", "净胜2球没戏", "皇社-1 净胜2球两边都只认 25%"),
    ("进球", "小球", "两队联赛场均合计 1.3 球"),
    ("比分", "1-0 / 1-1 / 0-0", "1-1 定价全场最低"),
]
for i, row in enumerate(mrows, start=1):
    for j, v in enumerate(row):
        c = mt.rows[i].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 1))
        if j < 2:
            shade_cell(c, ("4fc3f7", "ffd93d", "ffd93d", "ff6b6b")[i - 1])
para(doc, "高概率比分：首选 1-0，次选 1-1，留意 0-0。", size=10.5, bold=True, color=C_DARK)
para(doc, "皇社让一球要净胜两球，两边市场都只给 25% 的概率，这层门槛基本是摆设，不用碰。方向皇社 48-50% 定价精准，追了也没溢价。真正能说话的是小球：模型 40% vs 市场 57%，差 17 个点，是本场唯一的错位。但这种\"看小\"要打折看待，毕竟模型口径也打架，不重仓，当个方向参考。", size=10.5)
para(doc, "⚔️ 战意：皇社第13主场要止住客场连败颓势、抢分回中游；塞尔塔第17保级区边缘，客场目标就是苟 1 分，进攻不指望。两队 09-17/18 都有欧罗巴首轮，但距今两周，本场留力风险低，联赛抢分是真。", size=10.5)
para(doc, "💰 信号：方向皇社 48-50% 双方定价精准无溢价；让一球净胜2球两边都只认 25%，门槛无肉；唯一错位在大小球，市场 57% 偏大 vs 模型 40%，资金还小幅流向了主胜方向，市场并不慌。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：西班牙媒体常规叙事「皇社主场回暖 vs 塞尔塔锋线瘫痪」，普遍认为主队小胜、客队难进球，分歧只在比分大小。", size=10.5)
para(doc, "这场说白了：皇社赢面有但不大胜，塞尔塔大概率进球荒延续。你更信市场的大球，还是模型的闷局？评论区留个比分，赛后回来验证。", size=10.5, bold=True)
para(doc, "难说。真说不好。", size=10.5, bold=True)
para(doc, "数据来源：懂球帝、ESPN、各队官网", size=8.5, color=C_GRAY)
para(doc, "注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。", size=8.5, color=C_GRAY)

out = os.path.join(BASE, "周四006_皇社vs塞尔塔_全队1球市场偏看大球谁错了_赛事前瞻.docx")
doc.save(out)
print("SAVED:", out)
