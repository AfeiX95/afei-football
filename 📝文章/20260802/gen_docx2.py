# -*- coding: utf-8 -*-
import os
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

CHARTS = r"I:\阿飞说球\assets\charts\20260802"
OUTPUT = r"I:\阿飞说球\📝文章\20260802\济州SKvs仁川联队_韩K联_图表版_v2.docx"

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
    for r in h.runs: r.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
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
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = h
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True; r.font.size = Pt(9)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri+1].cells[ci]
            cell.text = str(val)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs: r.font.size = Pt(9)

def divider():
    p = doc.add_paragraph()
    r = p.add_run("-" * 50)
    r.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    r.font.size = Pt(8)

def bullet(text):
    p = doc.add_paragraph(text, style="List Bullet")
    for r in p.runs: r.font.size = Pt(10)

# TITLE
h = heading("济州SK主场铁幕 vs 仁川联队5人伤缺：韩K联最纠结对决", level=0)
h.alignment = WD_ALIGN_PARAGRAPH.CENTER
para("阿飞赛博聊球 | 2026-08-02 韩K联第21轮", size=9, color=RGBColor(0x88,0x88,0x88), align=WD_ALIGN_PARAGRAPH.CENTER)
tags = "#韩K联 #济州SK #仁川联队 #足球前瞻 #数据分析 #赛博聊球 #足球推荐 #体育头条 #K联赛 #足球分析"
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run(tags)
r.font.size = Pt(9)
r.font.color.rgb = RGBColor(0x1A, 0x5C, 0x9E)
para("数据不会说谎，但人会。", size=11, bold=True, italic=True, color=RGBColor(0x33,0x33,0x33), align=WD_ALIGN_PARAGRAPH.CENTER)
divider()

# 结论
heading("核心结论", level=2)
para("后台模型跑完这场韩K联中游卡位战，发现一个关键信号：仁川联队客胜被高估7个百分点。市场给2.16（隐含46.3%），模型只给39.1%。仁川联队5人伤缺（含门将+锋线+中场核心），阵容严重不整。济州SK虽然主场胜率仅27.3%，但防守稳固（场均失球1.09），赢指率70%。这不是强弱对话，这是双方都有致命弱点的残阵对决。", bold=True)
add_image(os.path.join(CHARTS, "7_济州vs仁川_偏差图.png"), width=Inches(5.0))
caption("图1 市场定价 vs 后台模型偏差一览")
divider()

# 数据反差
heading("数据反差", level=1)
para("济州SK主场胜率27.3%（倒数），场均进球0.82。但防守不差：场均失球1.09，近6场赢指率66.7%。")
para("仁川联队客场44.4%胜率+66.7%赢指率，但5人伤缺彻底改变格局。门将+锋线+中场核心同时缺阵。")
tbl(["维度", "济州SK（主场）", "仁川联队（客场）"], [
    ["赛季排名", "第8", "第6"],
    ["主/客场战绩", "3胜4平4负", "4胜3平2负"],
    ["主/客场胜率", "27.3%", "44.4%"],
    ["场均进球", "0.82", "1.44"],
    ["场均失球", "1.09", "1.00"],
    ["赢指率", "45.5%", "66.7%"],
    ["近6场状态", "2胜3平1负", "3胜1平2负"],
])
divider()

# 伤停
heading("伤停对比", level=1)
add_image(os.path.join(CHARTS, "10_济州vs仁川_伤停影响.png"), width=Inches(5.0))
caption("图2 伤停影响对比（仁川5人缺阵影响巨大）")
tbl(["球队", "缺阵球员", "位置", "影响"], [
    ["济州SK", "李昌珉", "中前卫", "轮换，影响小"],
    ["仁川联队", "穆格沙", "中锋", "锋线核心"],
    ["仁川联队", "李太熙", "门将", "最后防线"],
    ["仁川联队", "政原进", "前腰", "进攻组织"],
    ["仁川联队", "文智焕", "后腰", "中场屏障"],
    ["仁川联队", "杨承元", "左后卫", "防线缺员"],
])
para("仁川5人伤缺 vs 济州1人缺阵。阵容完整度差距悬殊。", bold=True, color=RGBColor(0xCC,0x33,0x33))
divider()

# H2H
heading("H2H历史交锋", level=1)
add_image(os.path.join(CHARTS, "9_济州vs仁川_H2H.png"), width=Inches(5.0))
caption("图3 近10次交锋：0平局！绿色=仁川胜，红色=济州胜")
para("近10次交手：济州4胜0平6负，仁川6胜4负。非胜即负的对决！", bold=True, color=RGBColor(0xCC,0x33,0x33))
divider()

# 雷达图
heading("六维能力对比", level=2)
add_image(os.path.join(CHARTS, "8_济州vs仁川_雷达图.png"), width=Inches(5.0))
caption("图4 六维能力雷达图（仁川H2H占优但伤停拖累）")
divider()

# 模型
heading("模型推演", level=1)
tbl(["结果", "后台模型", "市场定价", "偏差"], [
    ["主胜", "28.5%", "32.2%（3.11）", "-3.7pp"],
    ["平局", "32.4%", "34.5%（2.90）", "-2.1pp"],
    ["客胜", "39.1%", "46.3%（2.16）", "-7.2pp"],
])
divider()

# 战意+冷门
heading("战意分析", level=2)
para("两队仅差1分（27 vs 28），中游卡位战。双方都有动力，但仁川联队5人伤缺可能让他们更保守。")
heading("冷门因素", level=2)
bullet("仁川5人伤缺：门将+锋线+中场核心同时缺阵")
bullet("济州SK主场防守：场均失球1.09，近6场赢指率66.7%")
bullet("H2H无平局规律：近10次0平局，但仁川缺阵可能打破")
bullet("济州SK赢指率70%：机构长期低估")
divider()

# 最终判断
heading("最终判断", level=1)
tbl(["项目", "判断"], [
    ["胜平负", "客胜略优 > 平局 > 主胜"],
    ["让球", "济州SK受让不败"],
    ["大小球", "小2.5"],
    ["首选比分", "1-1"],
    ["次选比分", "1-0"],
    ["留意比分", "0-1"],
    ["核心偏差", "客胜被高估-7.2pp"],
    ["信心指数", "3/5"],
])
divider()

# 排比看点
para("仁川联队5人伤缺后，客场还能保持44.4%的胜率吗？济州SK主场27.3%胜率，这场能否打破「主场虫」标签？近10次交手无平局，残阵对决会不会首次出现平局？", bold=True, size=11)
divider()

# 互动+免责
para("仁川联队5人伤缺这数据放出来，你还敢看好他们客场吗？济州SK主场赢指率70%但胜率只有27%，这种矛盾你怎么看？评论区留下你的预测比分，赛后我们用实战赛果复盘模型精度。")
divider()
heading("数据来源", level=2)
para("基础赛事数据取自竞彩官方及新球体育（titan007）。进球期望值、六维能力雷达图及市场偏差测算，均由阿飞个人足球数据模型独立推演生成。", size=9, color=RGBColor(0x88,0x88,0x88))
heading("免责声明", level=2)
para("行文仓促，里面的图片和数据都是从官方渠道和权威媒体上整过来的，侵删。这都是我个人图一乐的瞎琢磨，千万别当真，理智看球、购买合法体育彩票才是正道。", size=9, italic=True, color=RGBColor(0x99,0x99,0x99))

doc.save(OUTPUT)
print(f"Done -> {OUTPUT}")



