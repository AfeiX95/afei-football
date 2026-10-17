# -*- coding: utf-8 -*-
"""江原FC vs 大阪钢巴 赛事前瞻 Word版（含图表）"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"I:\阿飞说球\20260811\周二001_江原FCVS大阪钢巴_赛事前瞻.docx"
IMG = r"I:\阿飞说球\20260811"

doc = Document()

# ---------- 全局默认字体 ----------
style = doc.styles['Normal']
style.font.name = '微软雅黑'
style.font.size = Pt(11)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

def set_cn(run, name='微软雅黑', size=11, bold=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)

def para(text, size=11, bold=False, color=None, align=None, space_after=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_cn(r, size=size, bold=bold, color=color)
    if align: p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p

def heading(text, level=1):
    p = doc.add_paragraph()
    r = p.add_run(text)
    if level == 1:
        set_cn(r, size=16, bold=True, color=(0x1A, 0x1A, 0x2E))
    elif level == 2:
        set_cn(r, size=13, bold=True, color=(0xC8, 0x10, 0x2E))
    else:
        set_cn(r, size=12, bold=True, color=(0x33, 0x33, 0x33))
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    return p

def shade_cell(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), hexcolor)
    tcPr.append(shd)

def make_table(headers, rows, widths=None, header_bg='1A3A6B'):
    t = doc.add_table(rows=len(rows)+1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        c = t.cell(0, j)
        c.text = ''
        r = c.paragraphs[0].add_run(h)
        set_cn(r, size=10.5, bold=True, color=(0xFF, 0xFF, 0xFF))
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade_cell(c, header_bg)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i+1, j)
            c.text = ''
            r = c.paragraphs[0].add_run(str(v))
            set_cn(r, size=10.5)
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    return t

def add_img(path, width_cm=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    r.add_picture(path, width=Cm(width_cm))
    p.paragraph_format.space_after = Pt(4)
    return p

# ================= 标题 =================
heading('8月11日亚冠附加赛江原VS钢巴：五五开的韩日对决', 1)
para('#亚冠精英 #江原FC #大阪钢巴 · 2026-08-11 18:30 · 韩国江陵竞技场 · 外围赛',
     size=9.5, color=(0x88, 0x88, 0x88), align=WD_ALIGN_PARAGRAPH.LEFT)

# ================= SCA开篇 =================
para('很多人一看韩职第4对阵日职中游，以为江原主场稳了。但拆开两队近一个月的数据，这场更像五五开——江原联赛两连败，后卫线伤了一半；钢巴上赛季刚捧起亚冠二级冠军奖杯，锋线火力全开。后台模型跑完10万次模拟：江原胜率39.7%，钢巴胜率34.2%，剩下26%留给平局。')

# ================= 战意 =================
heading('⚔️ 战意', 2)
para('先说江原。韩职争冠落后首尔11分，基本没戏，亚冠成了本赛季最大的目标。上赛季第一次踢亚冠精英就进了16强，主场2胜2平1负、不败率80%。这场输了会转战亚冠二级，但主场作战，没有理由不拼。战意拉满。')
para('再说钢巴。2008年亚冠冠军，上赛季又拿了亚冠二级冠军，但新赛制下亚冠乙冠军只保一个附加赛席位——必须赢下这一场才能重返精英正赛。全队的目标很明确：90分钟内解决战斗。')

# ================= 数据表 =================
heading('📊 两队数据对比', 2)
make_table(
    ['维度', '江原FC', '大阪钢巴'],
    [
        ['联赛定位', '韩职第4（21轮32分）', '日职过渡赛季第9'],
        ['近10场战绩', '4胜3平3负', '6胜1平3负'],
        ['进/失球', '进11球 失9球', '进24球 失13球'],
        ['场均进球', '1.1个', '2.0个（剔除热身泡沫）'],
        ['场均失球', '0.9个', '1.3个'],
        ['主/客场表现', '主场4胜4平2负', '客场5胜3平2负'],
        ['伤停情况', '多名主力后卫伤缺', '防线+主力门将伤停'],
        ['核心球员', '金大元（近4场2球2助）', '杰巴利+胡梅特双枪'],
        ['近期状态', '近2轮联赛连败', '新赛季首轮4-3胜10人浦和'],
    ],
    widths=[3.2, 6.1, 6.2],
)
add_img(fr'{IMG}\chart4_近10场状态对比.png', 15.0)

# ================= 模型概率 =================
heading('🧮 后台模型：接近五五开，江原主场微热', 2)
para('模型给江原39.7%、钢巴34.2%、平局26%。市场那边的定价几乎重合——江原36.6%、钢巴34.3%、平局29.1%，最大差距不到3个百分点，属于正常波动，没有明显的价值差。说白了，这场是"主场状态差"对"客场状态热"，两边定价都打平了。')
add_img(fr'{IMG}\chart1_胜平负概率对比.png', 15.0)

para('最可能的比分是1-1（12.4%），其次是1-0（9.6%）、0-1（8.6%）、2-1（8.5%）、1-2（7.9%）。单场决胜的赛制下，双方开场都会先试探，60分钟后才进入真正的决胜阶段——所以低比分的概率被模型抬得比较高。')
make_table(
    ['比分', '1-1', '1-0', '0-1', '2-1', '1-2', '0-0'],
    [['概率', '12.4%', '9.6%', '8.6%', '8.5%', '7.9%', '6.9%']],
)
add_img(fr'{IMG}\chart2_比分概率分布.png', 15.0)

# ================= 外媒对比 =================
heading('🌍 外媒对比', 2)
para('外媒这次几乎一边倒。tips.gg看好钢巴客场赢球，理由是钢巴近30天胜率75%，江原近6场只赢1场；球天下也认为钢巴常规时间小比分取胜。但细看钢巴那75%胜率，含一场6-0的热身和一场对10人浦和的4-3，含金量没那么高。模型这边更看重江原的主场、钢巴的客场和防线伤停——外媒看状态，模型看结构，谁赢都不算冷门。')

# ================= 信号 =================
heading('💰 信号', 2)
para('市场定价和模型几乎重合，说明这场没有明显被高估或低估的一方。江原主场只被小幅看好，跟它联赛两连败、5场只进4球的进攻荒直接挂钩；钢巴状态虽热，但客场+整条防线伤停的代价，市场也看见了。就像三国里那些看起来兵多将广的，真打起来不一定赢——这场没有稳的一方。')

# ================= 大小球 =================
heading('⚽ 大小球：临界，大球略占便宜', 2)
para('大2.5球49.9%对50.1%，标准临界盘。但注意双方防线都有伤缺：江原后卫线临时拼凑，钢巴门将和中卫一起躺病床——这种局面下进球可能比预期多。真要选方向，大球略占一点便宜。')
add_img(fr'{IMG}\chart3_大小球与进球.png', 15.0)

# ================= 推荐比分 =================
heading('🎯 推荐比分（三档）', 2)
make_table(
    ['维度', '比分', '概率', '逻辑'],
    [
        ['首选', '1-1', '12.4%', '单场决胜+双方谨慎+江原平局大师属性'],
        ['次选', '1-0', '9.6%', '江原主场定位球/反击偷一个，钢巴防线残缺'],
        ['防范', '0-1 / 1-2', '8.6% / 7.9%', '钢巴锋线抓转换，江原后防不稳'],
    ],
)
para('', size=6)

# ================= 互动钩子 =================
heading('💬 互动', 2)
para('单场决胜的附加赛，输了就要去踢亚冠二级。你们觉得江原能守住主场吗？评论区留个比分，赛后回来验证。', bold=True)

# ================= 复盘总结 =================
heading('🏁 模型复盘总结', 2)
para('概率配比：江原39.7% / 平局26% / 钢巴34.2%；最可能比分1-1；大小球临界（大球略优）；局势定性——五五开偏主场的韩日对决，伤停临场确认是唯一能打破天平的信息。')
para('江原这个队吧，你说他强吧，主场能赢蔚山；你说他弱吧，主场0-3输给升班马富川。就是起伏大。真要指望钢巴这条残阵防线在韩国客场稳住？反正我是信了五五开。')

# ================= 免责 =================
p = doc.add_paragraph()
r = p.add_run('以上分析基于公开数据和个人模型推演，仅供参考。足球是圆的，场上什么事都可能发生。理性看球，享受比赛。')
set_cn(r, size=9, color=(0x99, 0x99, 0x99))
p = doc.add_paragraph()
r = p.add_run('数据来源：懂球帝、ESPN、各队官网')
set_cn(r, size=9, color=(0x99, 0x99, 0x99))

doc.save(OUT)
print("已保存:", OUT)
