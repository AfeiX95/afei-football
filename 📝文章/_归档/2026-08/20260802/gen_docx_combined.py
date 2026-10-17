# -*- coding: utf-8 -*-
import os
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

CHARTS = r"I:\阿飞说球\assets\charts\20260802"
OUTPUT = r"I:\阿飞说球\📝文章\20260802\韩K联三场合一_图表版.docx"

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Microsoft YaHei"
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
style.paragraph_format.space_after = Pt(4)
style.paragraph_format.line_spacing = 1.25
for s in doc.sections:
    s.top_margin = Cm(1.8); s.bottom_margin = Cm(1.8)
    s.left_margin = Cm(2.2); s.right_margin = Cm(2.2)

def heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs: r.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    return h
def para(text, bold=False, size=10.5, color=None, align=None, italic=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Microsoft YaHei"; r.font.size = Pt(size)
    r.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    if bold: r.bold = True
    if italic: r.italic = True
    if color: r.font.color.rgb = color
    if align: p.alignment = align
def add_image(path, width=Inches(5.5)):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(); r.add_picture(path, width=width)
def caption(text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); r.font.size = Pt(8); r.font.color.rgb = RGBColor(0x99,0x99,0x99)
def tbl(headers, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = "Light Grid Accent 1"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = h
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs: r.bold = True; r.font.size = Pt(9)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri+1].cells[ci]; cell.text = str(val)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs: r.font.size = Pt(9)
def divider():
    p = doc.add_paragraph(); r = p.add_run("-"*50)
    r.font.color.rgb = RGBColor(0xCC,0xCC,0xCC); r.font.size = Pt(8)

# TITLE
h = heading("韩K联三场前瞻：三场首选都是1-1，市场集体误判？", level=0)
h.alignment = WD_ALIGN_PARAGRAPH.CENTER
para("阿飞赛博聊球 | 2026-08-02 韩K联第21轮", size=9, color=RGBColor(0x88,0x88,0x88), align=WD_ALIGN_PARAGRAPH.CENTER)
tags = "#韩K联 #蔚山HD #FC安养 #济州SK #仁川联队 #大田市民 #光州FC #足球前瞻 #数据分析 #赛博聊球"
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run(tags); r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x1A,0x5C,0x9E)
para("数据不会说谎，但人会。", size=11, bold=True, italic=True, color=RGBColor(0x33,0x33,0x33), align=WD_ALIGN_PARAGRAPH.CENTER)
divider()

# 核心结论
heading("核心结论", level=2)
para("后台模型跑完今晚三场韩K联，发现一个罕见信号：三场比赛首选比分都是1-1。市场在三场比赛中都存在明显偏差——蔚山主胜被高估21个百分点，大田主胜被高估30个百分点，仁川客胜被高估7个百分点。三场都是中下游混战+伤停严重+双方都有致命弱点。", bold=True)
add_image(os.path.join(CHARTS, "15_三场偏差汇总.png"), width=Inches(5.5))
caption("图1 三场比赛市场偏差汇总（负值=市场高估）")
divider()

# 三场胜平负对比
heading("三场胜平负概率对比", level=2)
add_image(os.path.join(CHARTS, "16_三场胜平负对比.png"), width=Inches(6.0))
caption("图2 三场比赛：市场定价 vs 后台模型")
divider()

# 第一场
heading("第一场：蔚山HD vs FC安养 — 伪强队 vs 真黑马", level=1)
para("市场给蔚山1.86（隐含53.8%主胜），模型只给32.8%，偏差-21.0pp。")
para("蔚山HD主场40%胜率+场均失球1.70+中卫中锋双核缺阵=伪强队。FC安养客场50%胜率+90%赢指率+3连胜=真黑马。蔚山主场对FC安养近2次：0-0、0-1，合计0进球。")
tbl(["项目", "判断"], [
    ["胜平负", "客胜 > 平局 > 主胜"],
    ["让球-1", "客胜（FC安养受让）"],
    ["首选比分", "1-1"],
    ["次选比分", "1-2"],
    ["留意比分", "0-1"],
])
divider()

# 第二场
heading("第二场：济州SK vs 仁川联队 — 残阵对决", level=1)
para("市场给仁川客胜2.16（隐含46.3%），模型只给39.1%，偏差-7.2pp。")
para("济州SK主场防守稳固（场均失球1.09），赢指率70%。仁川联队5人伤缺（门将+锋线+中场核心+后腰+左后卫），阵容严重不整。H2H近10次交手无平局，但仁川缺阵可能打破规律。")
tbl(["项目", "判断"], [
    ["胜平负", "客胜略优 > 平局 > 主胜"],
    ["让球", "济州SK受让不败"],
    ["首选比分", "1-1"],
    ["次选比分", "1-0"],
    ["留意比分", "0-1"],
])
divider()

# 第三场
heading("第三场：大田市民 vs 光州FC — 菜鸡互啄", level=1)
para("市场给大田主胜1.40（隐含71.4%），模型只给41.5%，偏差-29.9pp。三场中偏差最大。")
para("大田市民主场0胜（10场0胜5平5负），韩K联唯一主场不胜球队。近5场5连平。4人伤缺。光州FC虽然垫底但近4场3连不败，保级压力下状态回暖。")
tbl(["项目", "判断"], [
    ["胜平负", "主胜略优 > 平局 > 客胜"],
    ["让球-1", "客胜（光州FC受让）"],
    ["首选比分", "1-1"],
    ["次选比分", "1-0"],
    ["留意比分", "0-0"],
])
divider()

# 比分预测矩阵
heading("比分预测矩阵", level=1)
add_image(os.path.join(CHARTS, "17_三场比分预测.png"), width=Inches(5.5))
caption("图3 三场比赛比分预测概率")
tbl(["场次", "首选", "次选", "留意", "偏差"], [
    ["蔚山 vs 安养", "1-1", "1-2", "0-1", "主胜-21.0pp"],
    ["济州 vs 仁川", "1-1", "1-0", "0-1", "客胜-7.2pp"],
    ["大田 vs 光州", "1-1", "1-0", "0-0", "主胜-29.9pp"],
])
para("三场共同规律：控球率高的球队不一定赢球，伤停严重的球队不一定输球，市场定价最离谱的往往是平局。", bold=True)
divider()

# 伤停对比
heading("伤停影响对比", level=2)
add_image(os.path.join(CHARTS, "18_三场伤停对比.png"), width=Inches(5.0))
caption("图4 三场比赛伤停影响对比（红色=高影响）")
divider()

# 互动+免责
para("仁川联队5人伤缺、蔚山双核缺阵、大田4人伤缺+主场0胜——今晚韩K联三场全是残阵对决。你还敢追主队大胜吗？评论区留下你的预测比分，赛后我们用实战赛果复盘模型精度。")
divider()
heading("数据来源", level=2)
para("基础赛事数据取自竞彩官方及新球体育（titan007）。进球期望值、六维能力雷达图及市场偏差测算，均由阿飞个人足球数据模型独立推演生成。", size=9, color=RGBColor(0x88,0x88,0x88))
heading("免责声明", level=2)
para("行文仓促，里面的图片和数据都是从官方渠道和权威媒体上整过来的，侵删。这都是我个人图一乐的瞎琢磨，千万别当真，理智看球、购买合法体育彩票才是正道。", size=9, italic=True, color=RGBColor(0x99,0x99,0x99))

doc.save(OUTPUT)
print(f"Done -> {OUTPUT}")
