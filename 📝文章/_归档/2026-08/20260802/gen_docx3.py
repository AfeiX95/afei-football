# -*- coding: utf-8 -*-
import os
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

CHARTS = r"I:\阿飞说球\assets\charts\20260802"
OUTPUT = r"I:\阿飞说球\📝文章\20260802\大田市民vs光州FC_韩K联_图表版.docx"

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
h = heading("大田市民主场0胜 vs 光州FC客场0胜：韩K联最惨菜鸡互啄", level=0)
h.alignment = WD_ALIGN_PARAGRAPH.CENTER
para("阿飞赛博聊球 | 2026-08-02 韩K联第21轮", size=9, color=RGBColor(0x88,0x88,0x88), align=WD_ALIGN_PARAGRAPH.CENTER)
tags = "#韩K联 #大田市民 #光州FC #足球前瞻 #数据分析 #赛博聊球 #足球推荐 #体育头条 #保级战 #K联赛"
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run(tags); r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x1A,0x5C,0x9E)
para("数据不会说谎，但人会。", size=11, bold=True, italic=True, color=RGBColor(0x33,0x33,0x33), align=WD_ALIGN_PARAGRAPH.CENTER)
divider()

# 结论
heading("核心结论", level=2)
para("后台模型跑完这场韩K联保级区边缘战，发现一个惊人信号：市场严重高估大田市民主胜30个百分点。市场给1.40（隐含71.4%），模型只给41.5%。大田市民主场10场0胜（韩K联唯一），4人伤缺；光州FC虽然垫底但近4场3连不败。这不是强弱对话，这是两支同样不会赢球的球队在比谁更不差。", bold=True)
add_image(os.path.join(CHARTS, "11_大田vs光州_偏差图.png"), width=Inches(5.0))
caption("图1 市场定价 vs 后台模型偏差一览")
divider()

# 数据反差
heading("数据反差", level=1)
para("大田市民排名韩K联第9，但主场数据：10场0胜5平5负，胜率0%。韩K联唯一主场不胜球队。近5场联赛5连平。")
para("光州FC排名第12垫底，净胜球-34。但近4场1胜2平1负，状态回暖。赢指率60%。")
add_image(os.path.join(CHARTS, "13_大田vs光州_主客场对比.png"), width=Inches(5.0))
caption("图2 主客场核心数据对比")
tbl(["维度", "大田市民（主场）", "光州FC（客场）"], [
    ["赛季排名", "第9", "第12（垫底）"],
    ["主/客场战绩", "0胜5平5负", "0胜3平6负"],
    ["主/客场胜率", "0.0%", "0.0%"],
    ["场均进球", "0.70", "0.33"],
    ["场均失球", "1.40", "2.67"],
    ["赢指率", "0%", "33.3%"],
    ["近6场状态", "0胜4平2负", "0胜3平3负"],
])
divider()

# 伤停
heading("伤停对比", level=1)
tbl(["球队", "缺阵球员", "位置", "影响"], [
    ["大田市民", "石田雅俊", "影锋", "进攻核心"],
    ["大田市民", "河昌来", "中卫", "防线核心"],
    ["大田市民", "徐永在", "左后卫", "防线缺员"],
    ["大田市民", "严原上", "右边锋", "进攻缺员"],
    ["光州FC", "崔庆录", "前腰", "进攻核心+红牌停赛"],
])
para("大田4人伤缺 vs 光州1人停赛。双方核心都缺阵。", bold=True, color=RGBColor(0xCC,0x33,0x33))
divider()

# 雷达图
heading("六维能力对比", level=2)
add_image(os.path.join(CHARTS, "12_大田vs光州_雷达图.png"), width=Inches(5.0))
caption("图3 六维能力雷达图")
divider()

# H2H
heading("H2H历史交锋", level=1)
add_image(os.path.join(CHARTS, "14_大田vs光州_H2H.png"), width=Inches(5.0))
caption("图4 近10次交锋：红=大田胜，绿=光州胜，黄=平局")
para("近10次：大田3胜4平3负，光州3胜4平3负。完全五五开。上赛季大田客场5-0大胜光州。", bold=True)
divider()

# 模型
heading("模型推演", level=1)
tbl(["结果", "后台模型", "市场定价", "偏差"], [
    ["主胜", "41.5%", "71.4%（1.40）", "-29.9pp"],
    ["平局", "33.3%", "25.6%（3.90）", "+7.7pp"],
    ["客胜", "25.2%", "15.9%（6.30）", "+9.3pp"],
])
divider()

# 战意+冷门
heading("战意分析", level=2)
para("大田市民第9保级区边缘压力不大；光州FC第12垫底，保级压力巨大。光州再输与保级区差距扩至13分，基本宣告降级。光州背水一战。")
heading("冷门因素", level=2)
para("大田市民主场0胜+近5场5连平。光州FC近4场3连不败状态回暖。双方核心都缺阵。上赛季大田5-0光州的心理阴影仍在。")
divider()

# 最终判断
heading("最终判断", level=1)
tbl(["项目", "判断"], [
    ["胜平负", "主胜略优 > 平局 > 客胜"],
    ["让球-1", "客胜（光州FC受让）"],
    ["大小球", "小2.5"],
    ["首选比分", "1-1"],
    ["次选比分", "1-0"],
    ["留意比分", "0-0"],
    ["核心偏差", "主胜被高估-29.9pp"],
    ["信心指数", "3/5"],
])
divider()

# 互动+免责
para("大田市民主场0胜+5连平，这种「赢不了也输不起」的状态你怎么看？光州FC保级压力下能否爆冷？评论区留下你的预测比分，赛后我们用实战赛果复盘模型精度。")
divider()
heading("数据来源", level=2)
para("基础赛事数据取自竞彩官方及新球体育（titan007）。进球期望值、六维能力雷达图及市场偏差测算，均由阿飞个人足球数据模型独立推演生成。", size=9, color=RGBColor(0x88,0x88,0x88))
heading("免责声明", level=2)
para("行文仓促，里面的图片和数据都是从官方渠道和权威媒体上整过来的，侵删。这都是我个人图一乐的瞎琢磨，千万别当真，理智看球、购买合法体育彩票才是正道。", size=9, italic=True, color=RGBColor(0x99,0x99,0x99))

doc.save(OUTPUT)
print(f"Done -> {OUTPUT}")

