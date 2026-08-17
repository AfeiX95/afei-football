# -*- coding: utf-8 -*-
"""卡萨比亚 vs 本菲卡 头条版 Word (三刀拆解式结构, 深绿色系)"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"I:\阿飞说球\20260818_卡萨比亚vs本菲卡_头条版.docx"
IMG = r"I:\阿飞说球\charts_benfica"

doc = Document()

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
        set_cn(r, size=16, bold=True, color=(0x0E, 0x66, 0x55))
    elif level == 2:
        set_cn(r, size=13, bold=True, color=(0x0E, 0x66, 0x55))
    else:
        set_cn(r, size=12, bold=True, color=(0x2D, 0x34, 0x36))
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    return p

def shade_cell(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), hexcolor)
    tcPr.append(shd)

def make_table(headers, rows, widths=None, header_bg='0E6655'):
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

# ================= 标题 (冲突词: 高估/留力, 竞彩编号吃搜索) =================
heading('周一005卡萨比亚VS本菲卡：豪门80%胜率被模型砍半', 1)
para('#卡萨比亚 #本菲卡 #葡超 · 2026-08-18 03:15 · 葡超第2轮 · 皮纳马尼克球场',
     size=9.5, color=(0x88, 0x88, 0x88), align=WD_ALIGN_PARAGRAPH.LEFT)

# ================= 开篇直抛矛盾 (对比上篇SCA, 用数据锚开场) =================
para('市场给本菲卡的胜率是80%。后台模型跑完，四个场景最高给到49.6%，最低41.6%。中间差了30多个点。')
para('这种级别的分歧，通常不是模型抽风，就是市场漏了什么。这场漏的，是本菲卡自己。')

# ================= 第一刀: 赛程留力 =================
heading('🔪 第一刀：本菲卡一周三赛，欧战在即', 2)
para('先看本菲卡的赛程表：08-14欧战客场踢哈茨，08-18联赛客场踢卡萨比亚，08-21欧战主场迎战奥胡斯。')
para('一周三赛，中间还夹着两场欧战资格赛。欧战打到这个阶段，晋级就在眼前，本菲卡没理由在一场客场联赛里跟保级队死磕。轮换，几乎是明牌。市场那80%的定价，是按本菲卡全主力算的。')

# ================= 第二刀: 盘路深热 =================
heading('🔪 第二刀：客场让两球，历史盘路只有41.7%', 2)
para('再看盘路。本菲卡客场让球半/两球这个深度，历史赢盘率41.7%，10场里输掉7场。')
para('卡萨比亚主场受让同样深度，赢指率66.7%。一边是豪门客场让深设置翻车率高，一边是保级队主场受让坚挺，市场却把本菲卡-2胜开到了36.3%，这个数字比历史数据告诉我们的高太多了。')

# ================= 第三刀: 主场H2H =================
heading('🔪 第三刀：卡萨比亚主场，近两次没输过本菲卡', 2)
para('历史交锋看着难看，近9场卡萨比亚只赢1场。但把主场单拎出来：2025年1月，卡萨比亚主场3-1赢过本菲卡；2026年4月，主场1-1又平了。')
para('近两次主场，1胜1平，不败。保级队踢豪门，心理上最怕的是没赢过，而卡萨比亚恰恰赢过。')
add_img(fr'{IMG}\b_radar.png', 15.0)

# ================= 数据表 =================
heading('📊 两队数据对比', 2)
make_table(
    ['维度', '卡萨比亚（主）', '本菲卡（客）'],
    [
        ['联赛排名', '第16（0分）', '第9（1分）'],
        ['赛季战绩', '0胜0平1负', '0胜1平0负'],
        ['近10场', '3胜2平5负', '5胜3平2负'],
        ['进/失球', '进8 失13', '进28 失12'],
        ['场均进球', '0.8个', '2.8个'],
        ['场均失球', '1.3个', '1.2个'],
        ['头号火力', '锋线整体乏力', '欧战5-0/6-1大胜中'],
        ['伤停', '后卫古拉特（疑似）', '中场奥尔斯内斯（伤）'],
        ['赛程', '联赛单线', '一周三赛+欧战在即'],
    ],
    widths=[3.2, 6.1, 6.2],
)

# ================= 模型 =================
heading('🧮 后台模型：80%的胜率，四个场景都撑不住', 2)
para('模型把赛程、盘路、H2H、伤停全喂进去跑了10万次模拟，再用四个不同力度的留力假设做敏感性检验。结果：本菲卡胜率42%-50%之间，没有一个场景接近市场的80%。')
make_table(
    ['场景', '卡萨胜', '平局', '本菲卡胜', '对80%的偏离'],
    [
        ['原始λ', '28.5%', '28.7%', '42.8%', '-37.2pp'],
        ['留力修正', '21.1%', '29.3%', '49.6%', '-30.4pp'],
        ['保守假设', '27.9%', '30.5%', '41.6%', '-38.4pp'],
        ['中等假设', '23.7%', '29.9%', '46.4%', '-33.6pp'],
    ],
)
add_img(fr'{IMG}\b_bar.png', 15.0)

para('四刀砍完，结论清晰：本菲卡胜率被市场高估30-38pp，平局概率被低估（模型29% vs 市场13.6%）。')
add_img(fr'{IMG}\b_pie.png', 15.0)

# ================= 让球信号 =================
heading('💰 最强信号：卡萨+2不败', 2)
para('让球+2（卡萨受让两球）才是这场真正值得看的地方：')
make_table(
    ['结果', '模型', '市场', '价值差'],
    [
        ['卡萨+2不败', '74.5%', '40.7%', '+33.8pp'],
        ['让平（输2球）', '15.0%', '23.0%', '-8.0pp'],
        ['本菲卡-2胜', '10.6%', '36.3%', '-25.7pp'],
    ],
)
para('市场一边在比分盘捧0-2、0-3，一边在让球设置给卡萨+2开了40.7%，两个定价自己打架。模型站卡萨这头：受让两球，74.5%不败。')
add_img(fr'{IMG}\b_signals.png', 15.0)

# ================= 比分 =================
heading('🎯 比分怎么看', 2)
make_table(
    ['比分', '1-1', '0-1', '1-2', '0-2', '1-0', '0-0'],
    [['概率', '11.8%', '10.8%', '9.5%', '8.6%', '7.4%', '6.7%']],
)

# ================= 剧本 =================
heading('🎬 剧本推演', 2)
para('大概率剧本：本菲卡轮换阵容客场压上，但卡萨比亚主场龟缩+边路传中骚扰。欧战在即，本菲卡踢得松，1-1、0-1这种比分最顺。模型高频答案是1-1（11.8%）。')
para('冷门剧本也有两条：一是本菲卡轮换后进攻失灵，被卡萨比亚偷一个，1-0复刻2025年1月那场3-1的剧情；二是本菲卡干脆放弃联赛留力欧战，0-0闷平收场。真要指望本菲卡客场3球大胜，盘路先不答应。')

# ================= 复盘 =================
heading('🏁 赛博模型复盘总结', 2)
para('📊 胜负概率：卡萨21.1% | 平局29.3% | 本菲卡49.6% | 市场80%被砍半')
para('💰 最强信号：卡萨+2不败74.5%（vs 市场40.7%）')
para('⚽ 大小球：临界盘，大2.5约50.8%')
para('🎭 局势定性：豪门留力+客场深热陷阱+卡萨主场不怵，市场80%定价站不住，平局和受让是本场的价值所在。')

# ================= 互动 (带具体预测) =================
heading('💬 互动', 2)
para('本菲卡一周三赛+欧战在即，客场还能打出市场说的80%吗？我先押1-1，理由是本菲卡留力+卡萨主场H2H近2次不败。你们站哪边？评论区留个比分，赛后回来验证。', bold=True)

# ================= 免责 =================
p = doc.add_paragraph()
r = p.add_run('以上分析基于公开数据和个人模型推演，仅供参考。足球是圆的，场上什么事都可能发生。理性看球，享受比赛。')
set_cn(r, size=9, color=(0x99, 0x99, 0x99))
p = doc.add_paragraph()
r = p.add_run('数据来源：懂球帝、ESPN、各队官网')
set_cn(r, size=9, color=(0x99, 0x99, 0x99))

doc.save(OUT)
print("已保存:", OUT)
