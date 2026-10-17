# -*- coding: utf-8 -*-
import os
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

CHARTS = r"I:\阿飞说球\assets\charts\20260802"
OUTPUT = r"I:\阿飞说球\📝文章\20260802\蔚山HDvsFC安养_韩K联_图表版.docx"

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Microsoft YaHei"
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
style.paragraph_format.space_after = Pt(4)
style.paragraph_format.line_spacing = 1.25

for section in doc.sections:
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

def heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    return h

def para(text, bold=False, size=10.5, color=None, align=None, italic=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Microsoft YaHei"
    r.font.size = Pt(size)
    r.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    if bold: r.bold = True
    if italic: r.italic = True
    if color: r.font.color.rgb = color
    if align: p.alignment = align
    return p

def add_image(path, width=Inches(5.5)):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    r.add_picture(path, width=width)

def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.font.size = Pt(8)
    r.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

def tbl(headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = h
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri + 1].cells[ci]
            cell.text = str(val)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.size = Pt(9)

def divider():
    p = doc.add_paragraph()
    r = p.add_run("-" * 50)
    r.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    r.font.size = Pt(8)

def bullet(text):
    p = doc.add_paragraph(text, style="List Bullet")
    for r in p.runs:
        r.font.size = Pt(10)

# TITLE
h = heading("蔚山HD主场告急：40%胜率+双核缺阵，FC安养90%赢指率客场来袭", level=0)
h.alignment = WD_ALIGN_PARAGRAPH.CENTER
para("阿飞赛博聊球 | 2026-08-02 韩K联第21轮", size=9, color=RGBColor(0x88, 0x88, 0x88), align=WD_ALIGN_PARAGRAPH.CENTER)
tags = "#韩K联 #蔚山HD #FC安养 #足球前瞻 #数据分析 #赛博聊球 #足球推荐 #体育头条 #K联赛 #足球分析"
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run(tags)
r.font.size = Pt(9)
r.font.color.rgb = RGBColor(0x1A, 0x5C, 0x9E)
para("数据不会说谎，但人会。", size=11, bold=True, italic=True, color=RGBColor(0x33, 0x33, 0x33), align=WD_ALIGN_PARAGRAPH.CENTER)
divider()

# 核心结论
heading("核心结论", level=2)
para("后台模型跑完这场韩K联卡位战，发现一个惊人信号：市场严重高估蔚山HD主胜21个百分点。市场给蔚山1.86（隐含53.8%），模型只给32.8%。蔚山主场胜率仅40%，场均失球1.70，中卫+中锋双核缺阵，近6场仅1胜。FC安养客场50%胜率+90%赢指率，正处3连胜。", bold=True)
add_image(os.path.join(CHARTS, "1_市场vs模型偏差.png"), width=Inches(5.0))
caption("图1 市场定价 vs 后台模型偏差一览")
divider()

# 数据反差
heading("数据反差", level=1)
para("蔚山HD排名韩K联第4，但拆开看主场：10场4胜1平5负，胜率40%，场均失球1.70。蔚山主场对FC安养近2次：0-0、0-1，合计0进球。")
para("FC安养排名韩K联第5，客场数据恐怖：10场5胜4平1负，赢指率90%。近期3连胜，火力全开。")
heading("主客场数据对比", level=3)
add_image(os.path.join(CHARTS, "3_主客场数据对比.png"), width=Inches(5.5))
caption("图2 主客场核心数据对比")
tbl(["维度", "蔚山HD（主场）", "FC安养（客场）"], [
    ["赛季排名", "第4", "第5"], ["主/客场战绩", "4胜1平5负", "5胜4平1负"],
    ["主/客场胜率", "40.0%", "50.0%"], ["场均进球", "1.50", "1.60"],
    ["场均失球", "1.70", "1.00"], ["赢指率", "40%", "90%"],
    ["近6场状态", "1胜2平3负", "4胜1平1负"],
])
divider()

# 六维雷达图
heading("六维能力对比", level=2)
add_image(os.path.join(CHARTS, "2_六维雷达图.png"), width=Inches(5.0))
caption("图3 六维能力雷达图（FC安养全面占优）")
divider()

# H2H
heading("H2H历史交锋", level=2)
add_image(os.path.join(CHARTS, "5_H2H交锋趋势.png"), width=Inches(5.0))
caption("图4 近5次交锋结果（绿色=FC安养结果）")
tbl(["日期", "赛事", "主队", "比分", "客队", "结果"], [
    ["26-04-22", "韩K联", "FC安养", "1-1", "蔚山HD", "平局"],
    ["25-11-01", "韩K联", "FC安养", "3-1", "蔚山HD", "FC安养胜"],
    ["25-09-21", "韩K联", "蔚山HD", "0-0", "FC安养", "平局"],
    ["25-04-23", "韩K联", "FC安养", "0-1", "蔚山HD", "蔚山胜"],
    ["25-02-16", "韩K联", "蔚山HD", "0-1", "FC安养", "FC安养胜"],
])
para("近5场：蔚山1胜2平2负 | FC安养客场对蔚山2战全胜且零封", bold=True, color=RGBColor(0xCC, 0x33, 0x33))
divider()

# 14维评分卡
heading("14维评分卡", level=1)
tbl(["模块", "维度", "评分", "关键数据"], [
    ["硬实力", "近期状态", "-1", "近6场1胜16.7%"],
    ["硬实力", "主客分离", "-1", "主场40% vs 客场50%"],
    ["硬实力", "伤停", "-1", "中卫+中锋双核缺阵"],
    ["技战术", "进阶数据", "-1", "场均失球1.70"],
    ["技战术", "H2H", "-1", "近5次交手仅1胜"],
    ["战略", "更衣室", "-1", "杯赛被淘汰士气崩"],
    ["合计", "6维负分", "-0.30λ", "主面全面落后"],
])
heading("胜平负概率", level=3)
add_image(os.path.join(CHARTS, "4_胜平负饼图.png"), width=Inches(5.0))
caption("图5 市场定价 vs 后台模型概率分布")
tbl(["结果", "后台模型", "市场定价", "偏差"], [
    ["主胜", "32.8%", "53.8%（1.86）", "-21.0pp"],
    ["平局", "27.5%", "29.0%（3.45）", "-1.5pp"],
    ["客胜", "39.7%", "30.1%（3.32）", "+9.6pp"],
])
para("让球-1：FC安养客胜概率67.2%，市场给58.1%，偏差+9.1pp。", bold=True, color=RGBColor(0xCC, 0x33, 0x33))
divider()

# 战意+冷门
heading("战意分析", level=2)
para("两队仅差1分（31 vs 30），卡位战双方都需要分数。但心态完全不同：蔚山HD杯赛刚被淘汰，急需联赛止血但压力巨大；FC安养3连胜心态放松，客场作战反而没有包袱。压力在蔚山这边。")
heading("冷门因素", level=2)
bullet("蔚山主场对FC安养0进球：近2次主场0-0、0-1")
bullet("FC安养客场90%赢指率：韩K联最高")
bullet("让-1陷阱：蔚山开出让-1，但主场净胜球为-2")
bullet("杯赛被淘汰后心态崩溃")
divider()

# 综合对比
heading("综合对比汇总", level=2)
add_image(os.path.join(CHARTS, "6_综合对比汇总.png"), width=Inches(5.0))
caption("图6 六维度综合数据对比")
divider()

# 最终判断
heading("最终判断", level=1)
tbl(["项目", "判断"], [
    ["胜平负", "客胜 > 平局 > 主胜"],
    ["让球-1", "客胜（FC安养受让）"],
    ["大小球", "大2.5"],
    ["首选比分", "1-1"],
    ["次选比分", "1-2"],
    ["留意比分", "0-1"],
    ["核心偏差", "主胜被高估-21.0pp"],
    ["信心指数", "4/5"],
])
divider()

# 互动+免责
heading("互动钩子", level=2)
para("蔚山HD主场40%胜率+双核缺阵，这场还能撑住排名吗？FC安养客场90%赢指率这数据放出来，有没有颠覆你的判断？评论区留下你的预测比分，赛后我们用实战赛果复盘模型精度。")
divider()
heading("数据来源", level=2)
para("基础赛事数据取自竞彩官方及新球体育（titan007）。控球率、射门、射正等进阶数据均为赛季实时统计。进球期望值、六维能力雷达图及市场偏差测算，均由阿飞个人足球数据模型独立推演生成。", size=9, color=RGBColor(0x88, 0x88, 0x88))
heading("免责声明", level=2)
para("行文仓促，里面的图片和数据都是从官方渠道和权威媒体上整过来的，侵删。这都是我个人图一乐的瞎琢磨，千万别当真，理智看球、购买合法体育彩票才是正道。", size=9, italic=True, color=RGBColor(0x99, 0x99, 0x99))

doc.save(OUTPUT)
print(f"Done -> {OUTPUT}")
