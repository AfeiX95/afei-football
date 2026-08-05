# -*- coding: utf-8 -*-
import os
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

CHARTS = r"I:\阿飞说球\assets\charts\20260731"
OUTPUT = r"I:\阿飞说球\📝文章\20260731\韩K联三场前瞻_图表版.docx"

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
    return p

def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.font.size = Pt(8)
    r.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
    r.font.name = "Microsoft YaHei"
    r.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

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
    return t

def divider():
    p = doc.add_paragraph()
    r = p.add_run("-" * 50)
    r.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    r.font.size = Pt(8)

# ===== TITLE =====
h = heading("韩K联三场前瞻：浦项主场零封密码，全北豪门光环褪色？", level=0)
h.alignment = WD_ALIGN_PARAGRAPH.CENTER
para("阿飞·赛博聊球 | 2026-08-01 韩K联第21轮", size=9, color=RGBColor(0x88, 0x88, 0x88), align=WD_ALIGN_PARAGRAPH.CENTER)
para("数据不会说谎，但人会。", size=11, bold=True, italic=True, color=RGBColor(0x33, 0x33, 0x33), align=WD_ALIGN_PARAGRAPH.CENTER)

# 10个话题标签
tags = "#韩K联 #浦项制铁 #全北现代 #FC首尔 #江原FC #足球前瞻 #数据分析 #赛博聊球 #足球推荐 #体育头条"
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run(tags)
r.font.name = "Microsoft YaHei"
r.font.size = Pt(9)
r.font.color.rgb = RGBColor(0x1A, 0x5C, 0x9E)
r.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

divider()

# ===== 核心结论 =====
heading("核心结论", level=2)
para("后台模型跑完三场韩K联，发现一个惊人信号：市场在浦项制铁这场存在24个百分点的偏差。浦项主场定价43.7%，模型只给19.1%。全北主场定价39.2%，模型给27.6%。两场加起来，市场高估主队超过30个百分点。")
add_image(os.path.join(CHARTS, "5_市场vs模型偏差.png"), width=Inches(5.0))
caption("图1 · 市场定价 vs 后台模型偏差一览")
para("韩K联这个联赛，控球率高的球队不一定赢球——浦项55.6%控球主场仅进4球，全北54.4%控球射正转化率仅36%。效率比控球重要，这是本轮最大的信号。", bold=True)
divider()

# ===== MATCH 1 =====
heading("第一场：浦项制铁 vs 金泉尚武", level=1)
para("伪控球 vs 平局大师 | 2026-08-01 18:30", size=9, color=RGBColor(0x88, 0x88, 0x88))

heading("数据反差", level=3)
para("浦项制铁主场控球率55.6%（不低），但9场主场只进了4个球，场均0.44。韩K联12支球队倒数第一。控球58%输全北0-2，控球63%输济州0-2，控球55%输FC安养0-1。控球越多输得越惨，这支球队的控球是伪控球。")
para("金泉尚武全赛季55%平局率（11/20），韩K联平局之王。H2H近10次交手浦项只赢2场输6场，主场近3次对金泉：0-0、1-2、0-3。浦项主场大球率0%，9场全部小球。")

heading("评分卡数据", level=3)
tbl(["维度", "浦项制铁（主）", "金泉尚武（客）"], [
    ["赛季排名", "第7", "第10"],
    ["赛季战绩", "8胜4平8负", "5胜9平6负"],
    ["主场/客场胜率", "55.6%", "36.4%"],
    ["场均进球", "1.78（主）", "1.00（客）"],
    ["场均失球", "1.11（主）", "0.55（客）"],
    ["平局率", "30%", "55%"],
    ["控球率", "55.6%", "44.5%"],
    ["赢指率", "41.9%", "26.5%"],
    ["大球率", "66.7%（主）", "30%"],
])

heading("六维能力对比", level=3)
add_image(os.path.join(CHARTS, "1_六维雷达图.png"), width=Inches(5.0))
caption("图2 · 三场比赛六维能力雷达图")

heading("胜平负概率", level=3)
add_image(os.path.join(CHARTS, "2_胜平负概率柱状图.png"), width=Inches(5.0))
caption("图3 · 后台模型胜平负概率柱状对比")
add_image(os.path.join(CHARTS, "3_胜平负饼图.png"), width=Inches(4.5))
caption("图4 · 浦项 vs 金泉 胜平负概率分布")

heading("战意分析", level=3)
para("浦项第7中游无压力，金泉第10保级边缘但打法就是磨。双方都无生死战压力，反而更容易踢出闷平。金泉尚武是军队球队，阵容轮换大，打法保守但韧性足。")

heading("冷门因素", level=3)
para("浦项制铁「伪控球」+ 金泉尚武「平局大师」= 极大概率低比分闷平。市场给主胜43.7%严重高估。", bold=True)
para("模型结果：平局41.6%，客胜39.3%，主胜19.1%。大2.5球概率仅11.6%。", bold=True, color=RGBColor(0xCC, 0x33, 0x33))

heading("推荐比分", level=3)
para("首选 0-0 | 次选 0-1 | 留意 1-1", size=12, bold=True, color=RGBColor(0x1A, 0x5C, 0x9E))
divider()

# ===== MATCH 2 =====
heading("第二场：全北现代 vs FC首尔", level=1)
para("榜首大战，豪门光环褪色 | 2026-08-01 18:30", size=9, color=RGBColor(0x88, 0x88, 0x88))

heading("数据反差", level=3)
para("全北现代10次K联赛冠军，但本赛季主场统治力崩塌。最近2个主场：0-0大田、1-2江原。三条线缺阵（右后卫金太焕、中锋康帕尼奥、右边锋朴柱永），右路进攻和中锋支点直接砍掉。")
para("FC首尔客场80%胜率（10场8胜），射正转化率50%，全北主场射正转化率仅36%。控球率接近，但一个低效一个高效。")

heading("评分卡数据", level=3)
tbl(["维度", "全北现代（主）", "FC首尔（客）"], [
    ["联赛排名", "第2", "第1"],
    ["积分", "33分", "42分"],
    ["赛季战绩", "9胜6平5负", "13胜3平4负"],
    ["主/客胜率", "55.6%", "80.0%"],
    ["场均进球", "1.78", "1.90"],
    ["场均失球", "1.11", "0.90"],
    ["近期状态", "5胜3平2负", "5胜2平3负（2连败）"],
    ["缺阵人数", "3人", "1人"],
    ["H2H近10场", "5胜3平2负", "2胜3平5负"],
])

heading("控球效率分析", level=3)
add_image(os.path.join(CHARTS, "4_控球效率分析.png"), width=Inches(5.0))
caption("图5 · 控球率 vs 射正转化率对比（效率为王）")

heading("战意分析", level=3)
para("全北落后FC首尔9分，主场作战输了基本告别争冠。但压力可能成为负担。FC首尔领先9分心态放松，2连败后急需反弹。全北历史交锋占优（10场5胜），但近3次交锋FC首尔2胜1平形成压制。")

heading("冷门因素", level=3)
para("全北3人缺阵+主场哑火+FC首尔客场80%胜率= 客胜是最大概率结果。市场给主胜39.2%仍偏高。", bold=True)
para("模型结果：客胜52%，平局23%，主胜25%。大2.5球概率62%。", bold=True, color=RGBColor(0xCC, 0x33, 0x33))

heading("推荐比分", level=3)
para("首选 1-2 | 次选 1-1 | 留意 0-2", size=12, bold=True, color=RGBColor(0x1A, 0x5C, 0x9E))
divider()

# ===== MATCH 3 =====
heading("第三场：江原FC vs 富川FC", level=1)
para("主场碾压局 | 2026-08-01 18:30", size=9, color=RGBColor(0x88, 0x88, 0x88))

heading("数据反差", level=3)
para("江原FC主场控球率61.3%，场均仅失0.44球。9场主场4场零封（2-0金泉、2-0蔚山、2-0大田、3-0光州）。韩K联主场防守第一。富川FC近5场0胜4连败，客场场均仅进0.90球。")

heading("评分卡数据", level=3)
tbl(["维度", "江原FC（主）", "富川FC（客）"], [
    ["联赛排名", "第3", "第11"],
    ["积分", "32分", "20分"],
    ["赛季战绩", "8胜8平4负", "4胜8平8负"],
    ["主/客胜率", "55.6%", "18.2%"],
    ["场均进球", "1.89（主）", "0.90（客）"],
    ["场均失球", "0.44（主）", "1.60（客）"],
    ["近6场状态", "3胜1平2负", "0胜1平5负"],
    ["近期走势", "4场零封主场", "4连败"],
])

heading("综合对比汇总", level=3)
add_image(os.path.join(CHARTS, "6_综合对比汇总.png"), width=Inches(5.0))
caption("图6 · 三场比赛核心数据综合对比")

heading("战意分析", level=3)
para("江原第3争冠组有动力，富川第11保级压力大但近期状态极差（0胜4负），有心无力。江原8月11日有亚冠精英赛，可能部分轮换——这是最大冷门触发器。")

heading("冷门因素", level=3)
para("江原亚冠分心可能轮换是最大冷门触发器。但主场4场零封的惯性太强，富川难进球。", bold=True)
para("模型结果：主胜63%，平局26%，客胜11%。大2.5球概率25%。", bold=True, color=RGBColor(0xCC, 0x33, 0x33))

heading("推荐比分", level=3)
para("首选 1-0 | 次选 2-0 | 留意 0-0", size=12, bold=True, color=RGBColor(0x1A, 0x5C, 0x9E))
divider()

# ===== FINAL =====
heading("最终判断：比分预测矩阵", level=1)
tbl(["场次", "后台模型", "首选", "次选", "留意", "偏差信号"], [
    ["浦项 vs 金泉", "平局42%+客胜39%", "0-0", "0-1", "1-1", "主胜被高估-24.6pp"],
    ["全北 vs FC首尔", "客胜52%", "1-2", "1-1", "0-2", "主胜被高估-11.6pp"],
    ["江原 vs 富川", "主胜63%", "1-0", "2-0", "0-0", "偏差较小"],
])
para("")
para("三场比赛共同规律：控球率高的球队不一定赢球。浦项55.6%控球主场仅进4球，全北54.4%控球射正转化率仅36%。韩K联这个联赛，效率比控球重要得多。", bold=True, size=11)
divider()

# ===== 互动 + 免责 =====
heading("互动钩子", level=2)
para("三场韩K联拆完了。浦项主场伪控球这数据放出来，有没有颠覆你的判断？全北主场10次冠军的豪门光环，这轮还能撑住吗？评论区留下你的预测比分，赛后我们用实战赛果复盘模型精度。")
divider()

heading("数据来源", level=2)
para("基础赛事数据取自竞彩官方及新球体育（titan007）。控球率、射门、射正等进阶数据均为赛季实时统计。进球期望值、六维能力雷达图及市场偏差测算，均由阿飞个人足球数据模型独立推演生成。", size=9, color=RGBColor(0x88, 0x88, 0x88))

heading("免责声明", level=2)
para("行文仓促，里面的图片和数据都是从官方渠道和权威媒体上整过来的，侵删。这都是我个人图一乐的瞎琢磨，千万别当真，理智看球、购买合法体育彩票才是正道。", size=9, italic=True, color=RGBColor(0x99, 0x99, 0x99))

doc.save(OUTPUT)
print(f"Done -> {OUTPUT}")

