# -*- coding: utf-8 -*-
"""生成: 利物浦vs诺丁汉_头条深度版.docx (R19 白底图规范)"""
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
C_LIGHT = "f5f5f5"

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

# ===== 图表: 市场 vs 模型 胜平负 =====
cats = ["主胜", "平局", "客胜"]
market = [65, 20, 15]
model = [40, 29, 31]
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
ax.set_ylim(0, 85)
ax.set_ylabel("概率 (%)", fontsize=9)
ax.set_title("利物浦 vs 诺丁汉 · 胜平负概率", fontsize=11, color="#1a237e", pad=8)
ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.35)
fig.tight_layout()
ch = os.path.join(CHART_DIR, "bar_liv.png")
fig.savefig(ch, facecolor="white", bbox_inches="tight")
plt.close(fig)

# ===== 文档 =====
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
r = p.add_run("利物浦6伤停还64%热度？安菲尔德克星诺丁汉要搞事")
set_cn_font(r, size=17, bold=True, color=C_DARK)
p.paragraph_format.space_after = Pt(4)

para(doc, "#利物浦  #诺丁汉  #英超  #足球前瞻  #数据分析", size=9, color=C_GRAY,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

para(doc, "很多人看到利物浦在安菲尔德打诺丁汉，以为这是开季主场首秀的碾压局——机构也给主队开了 64.6% 的热度。但后台模型跑完，利物浦只有 39.9%：近10场 3胜4平3负、上季末 3 场不胜、6 人伤停里有 2 个门将；而诺丁汉是这支利物浦的主场克星——近 4 次做客安菲尔德 2 胜 2 负，2025 年 11 月在这里 0:3 完胜过。", size=10.5)
para(doc, "结论先行：利物浦的价里，一半是安菲尔德，一半是名字。最干净的不是方向，是净胜两球这个门槛——模型只给 18.2%，市场给了 40.3%。", size=10.5, bold=True, color=C_DARK)

heading(doc, "一、64.6% 的热度，是安菲尔德+名字，不是状态")
para(doc, "先看表象：利物浦主场首秀，身价和阵容评分都碾压诺丁汉，机构给 64.6% 主胜、净胜两球 40.3%——怎么看都是安菲尔德例行碾压。", size=10.5)
para(doc, "再看暗礁：① 状态——近10场 3胜4平3负，上季末联赛 3 场不胜（1:1布伦特、2:4维拉、1:1切尔西），热身还 2:4 输过利兹联（半场 2:0 被逆转）；② 伤停——6 人伤停里有 2 个门将（Woodman + 亚罗什）+ 3 个后卫 + 1 个前锋，防线是替补班底，门将位置双保险报废；③ 克星——利物浦主场对诺丁汉近 4 次 2胜2负，2025 年 11 月安菲尔德 0:3 惨败、2024 年 9 月 0:1；④ 诺丁汉客场不软——同主客（客）战况 6胜1平3负。", size=10.5)

tbl = doc.add_table(rows=5, cols=4)
tbl.style = "Table Grid"; tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr = ["维度", "利物浦（主）", "诺丁汉（客）", ""]
rows_data = [
    ("近10场", "3胜4平3负 进17失17", "5胜1平4负 进15失13", ""),
    ("场均进/失", "1.7 / 1.7", "1.5 / 1.3", ""),
    ("主场/客场交锋", "2胜2负（0:3/0:1两负）", "2胜2负", ""),
    ("伤停", "6人（含2门将）", "1人（后卫）", ""),
]
for j, h in enumerate(hdr[:3]):
    c = tbl.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
tbl.rows[0].cells[3].merge(tbl.rows[0].cells[3])
for i, (a, b, c_, _) in enumerate(rows_data, start=1):
    for j, v in enumerate([a, b, c_]):
        cell = tbl.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 0))
para(doc, "诺丁汉近一周对利兹两连败（联赛 0:1 + 联赛杯 0:2），当前状态也不热——但它的克星属性是历史惯性，不是临时状态。", size=8.5, color=C_GRAY)

heading(doc, "二、机构定价 vs 后台模型")
doc.add_picture(ch, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl2 = doc.add_table(rows=6, cols=4)
tbl2.style = "Table Grid"; tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr2 = ["结果", "机构定价", "后台模型", "偏差"]
for j, h in enumerate(hdr2):
    c = tbl2.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows2 = [
    ("利物浦胜", "64.6%", "39.9%", "-24.7pp", C_MAIN),
    ("平局", "20.1%", "29.0%", "+8.9pp", C_DRAW),
    ("诺丁汉胜", "15.3%", "31.1%", "+15.8pp", C_AWAY),
    ("净胜2球", "40.3%", "18.2%", "-22.1pp", C_MAIN),
    ("大2.5", "≈62%", "42.4%", "-19.6pp", C_MAIN),
]
for i, (a, b, c_, d, tint) in enumerate(rows2, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl2.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "⚔️ 战意：利物浦开季主场首秀——豪门在主场的首战不能丢分，舆论压力实打实；诺丁汉刚被利兹双杀，客场急需止血。两边都想赢，但利物浦更输不起。", size=10.5)
para(doc, "💰 信号：市场的 64.6% 押的是「安菲尔德 + 名字」；模型的 39.9% 押的是「状态 + 伤停」——6 人伤停（含 2 门将）的折损显然没被价格消化干净，净胜两球 40.3% vs 18.2% 的差价就是证据。进球数也打架：模型 42.4% vs 市场六成大球——交锋近 9 场只有 3 场 ≥3 球、场均 2.0 球的小球惯性，诺丁汉客场又是求稳打法。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向——「利物浦=豪门主场首秀 + 6 人伤停」对「诺丁汉=利兹两连败 + 安菲尔德克星」，两组事实互相打架。说句不好听的，这场比赛的定价里，机构的记忆还停在利物浦是那支不败之师，模型看到的却是替补门将把守的防线。", size=10.5)

heading(doc, "三、走势推演与核心矩阵")
para(doc, "剧本A——利物浦替补防线撑住，主场气势压人（约40%）：门将危机未爆雷，利物浦压着打，诺丁汉缩防 → 1-0 / 2-1 收场，净胜两球门槛大概率走空。", size=10.5)
para(doc, "剧本B——上半场僵持，闷到中后段（约35%，模型最可能）：利物浦平局体质（近10场 4 平）+ 诺丁汉客场求稳 → 1-1 / 0-0，H2H 场均 2.0 球的小球惯性兑现。", size=10.5)
para(doc, "剧本C——诺丁汉反击偷分（约25%）：克星属性再现，利物浦压上后防空当被反击撕开，替补门将再背锅 → 0-1 / 1-2，2025 年 11 月的 0:3 剧本重演。", size=10.5)
para(doc, "高概率比分：1-1（13.7%）> 1-0（11.2%）> 0-0（9.9%）> 0-1（9.5%）", size=10.5, bold=True, color=C_DARK)

mt = doc.add_table(rows=2, cols=5)
mt.style = "Table Grid"; mt.alignment = WD_TABLE_ALIGNMENT.CENTER
mhdr = ["场次", "机构胜率", "模型胜率", "价值偏差", "比分前瞻"]
for j, h in enumerate(mhdr):
    c = mt.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
for j, v in enumerate(["利物浦vs诺丁汉", "64.6%", "39.9%", "-24.7pp", "1-1 / 1-0（防 0-1）"]):
    c = mt.rows[1].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9.5)
para(doc, "", size=4, space_after=2)
para(doc, "🎯 落脚：方向 利物浦打折看（模型 39.9% vs 机构 64.6%，中间值更可信）；门槛 净胜两球几乎没戏（受让方强支撑，模型 60.1% vs 34.8%）；进球 2-3 球偏谨慎（模型 42.4%）；比分 1-1 / 1-0（防 0-1）。", size=10.5, bold=True)

heading(doc, "互动钩子", size=12)
para(doc, "利物浦 64.6% 的热度你信吗？6 人伤停里有 2 个门将的利物浦，打安菲尔德克星诺丁汉，你赌净胜两球还是受让？评论区留下你的预测比分，赛后我们用实战赛果复盘模型精度。", size=10.5)
para(doc, "难说。真说不好。", size=10.5, bold=True)
para(doc, "数据来源：懂球帝、ESPN、各队官网", size=8.5, color=C_GRAY)
para(doc, "注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。", size=8.5, color=C_GRAY)

out = os.path.join(BASE, "利物浦vs诺丁汉_头条深度版.docx")
doc.save(out)
print("SAVED:", out)
