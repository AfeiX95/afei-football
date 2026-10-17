# -*- coding: utf-8 -*-
"""
欧冠次回合两场 (LASK林茨vs凯尔特人 + 博德闪耀vs奈梅亨) 头条版 docx (R19/R27)
输出: 📝文章/20260826/欧冠次回合两场_头条版.docx
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

CHART_DIR = r'I:\阿飞说球\database\charts_20260826_uefa'
OUT = r'I:\阿飞说球\📝文章\20260826\欧冠次回合两场_头条版.docx'
C_PRIMARY = RGBColor(0x1a, 0x3a, 0x5c)   # 深蓝
C_DARK = RGBColor(0x33, 0x33, 0x33)
C_GRAY = RGBColor(0x88, 0x88, 0x88)

TITLE = '欧冠次回合双拆：0:3的坑市场给面子，3:1的局市场不松口'
TAGS = '#LASK林茨 #凯尔特人 #博德闪耀 #奈梅亨 #欧冠 #足球前瞻 #数据分析 #欧冠附加赛 #足球分析 #体育头条'

BODY = [
    ('p', '欧冠附加赛次回合，两场都是"领先方守成 vs 落后方搏命"的剧本，市场却给出了两副面孔：LASK林茨主场 0:3 落后，机构还给主队 49.2% 的理论胜率；博德闪耀手握 3:1，机构给主队 61.5% 一点不松口。'),
    ('p_bold', '结论先行：落后方的面子，往往撑不起现实。LASK 那场，后台模型直接把方向翻了过来——凯尔特人胜率反超（+12.1pp），让-1 净胜2球概率只有 19.9%；博德闪耀那场，模型与市场罕见一致（62.6% vs 61.5%），真正的价值信号全在大球（73% 双共识）。两场共性是：晋级基本没悬念（91%-94%），悬念全在赢几个球、进几个球。'),
    ('h', '一、 LASK vs 凯尔特人：0:3的坑太深，主场面子撑不起'),
    ('p', '首回合凯尔特人主场 3:0 完胜，半场就 2:0。回主场 LASK 需要 3-0 才进加时、4-0 才能翻盘。后台模型算下来，翻盘概率合计 8.6%，凯尔特人晋级 91.4%。'),
    ('p', '反常就在这：0:3 惨败的一方，机构还开 49.2% 主胜微热。主场 6胜2平2负、奥甲 3 连胜，这些数据是真的，但对手级别完全不同。凯尔特人苏超开局全胜（5:1 基马诺克），攻防和心理全面占上风。'),
    ('p_bold', '模型跑完，方向直接翻转：'),
    ('p', '· 凯尔特人胜 39.0%（比市场 26.8% 高 12 个百分点）'),
    ('p', '· LASK 胜 36.4%（比市场 49.2% 低 13 个百分点）'),
    ('p', '· 凯尔特人+1 不败 62.1%——让-1 净胜2球概率只有 19.9%'),
    ('c', 'bar_lask'),
    ('p', '澳门推介直接给了凯尔特人五星，"攻防更胜一筹，心理占上风，剑指胜利"。这场的主胜热度，是市场给主场面子，撑不起让-1 的门槛。'),
    ('c', 'radar_lask'),
    ('h', '二、 博德闪耀 vs 奈梅亨：3:1的局，大球共识最稳'),
    ('p', '另一场剧本相同、市场态度相反：博德闪耀首回合客场 3:1，回北极圈人造草主场，输 2 球才进加时、输 3 球才出局，晋级 94.3%。市场给 61.5% 主胜，模型 62.6%，罕见一致，无便宜可占。'),
    ('p_bold', '这场真正的信号在进球：'),
    ('p', '· 大 2.5 高达 73%（市场与模型双共识）——奈梅亨必须客场赢 3 球才能翻盘，只能压上'),
    ('p', '· 奈梅亨连续 10 场竞技比赛没零封过，10 场全部双方都进球'),
    ('p', '· 博德闪耀连续 7 场至少进 2 球，主场场均 2.7 球'),
    ('c', 'bar_bodo'),
    ('p', '唯一要留个心眼的是门槛：博德闪耀 3:1 领先不需要赢，守成战意下让-1 净胜2球概率只有 42.8%，净胜 1 球（走盘）的概率 21.2%——赢球大概率，赢两个球不一定。'),
    ('c', 'radar_bodo'),
    ('h', '三、 比赛走势推演与核心矩阵'),
    ('p_bold', 'LASK vs 凯尔特人（总比分 0:3）：'),
    ('p', '1. 凯尔特人守成反击 2-1/1-2 双杀（约 40%）；2. LASK 主场搏命进球但翻不动，2-2/1-1 平局（约 30%）；3. LASK 主场面子局 2-1 小胜（约 30%）。'),
    ('p_bold', '博德闪耀 vs 奈梅亨（总比分 3:1）：'),
    ('p', '1. 对攻大战博德闪耀 3-1/2-1 双杀（约 45%）；2. 奈梅亨压上被反击打成 1-1/2-2（约 30%）；3. 博德闪耀 1-0 收工（1球主义，约 25%）。'),
    ('c', 'score_lask'),
    ('c', 'score_bodo'),
    ('p_bold', '核心矩阵：'),
    ('p', '· LASK vs 凯尔特人｜模型 凯尔特人39.0% > LASK 36.4%（+12.1pp）｜让-1打穿仅19.9%｜2-3球｜前瞻 1-1 / 1-2（防 2-1）'),
    ('p', '· 博德闪耀 vs 奈梅亨｜模型 62.6% ≈ 市场 61.5%｜大2.5 双共识73%｜3球+｜前瞻 2-1 / 3-1（防 1-1）'),
    ('p_bold', '研判落脚：LASK 场方向看凯尔特人不败+受让+1（模型 62.1%），进球偏大；博德闪耀场方向看主队不败，但让-1 净胜2球不是好标的，大 2.5 才是全场最干净的方向。两场晋级方向都无悬念，别在"谁晋级"上浪费时间。'),
    ('h', '互动'),
    ('p_bold', '凯尔特人 3-0 的领先 + 市场 49.2% 的主场面子，你觉得是机构真信 LASK 主场能翻，还是单纯的"主场人情价"？博德闪耀那场你更信大球对攻，还是守成小比分？评论区亮个比分，我先看好 1-1 和 2-1。'),
    ('p_gray', '数据来源：竞彩官方。'),
    ('p_gray', '注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。'),
    ('p_gray', '配图关键词（中英双语，无水印两队近期赛照）：1.LASK林茨近期比赛照/LASK Linz 2026 match 2.凯尔特人近期比赛照/Celtic 2026 match 3.凯尔特人客场作战照/Celtic away 2026 4.博德闪耀主场（阿斯普米拉球场）/Aspmyra Stadion 5.博德闪耀近期比赛照/Bodo Glimt 2026 match 6.奈梅亨近期比赛照/NEC Nijmegen 2026 match 7.欧冠附加赛海报（次回合）/UCL playoff second leg。无水印图源：懂球帝/新球体育（无角标）、俱乐部官方社媒、维基共享。'),
]


def set_font(run, size=11, bold=False, color=C_DARK, name='微软雅黑'):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)


def build_doc():
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(11)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(TITLE)
    set_font(run, size=16, bold=True, color=C_PRIMARY)

    p = doc.add_paragraph()
    run = p.add_run(TAGS)
    set_font(run, size=9, color=C_GRAY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('数据不会说谎，但人会。')
    set_font(run, size=10, color=C_GRAY)

    for item in BODY:
        kind = item[0]
        if kind == 'p':
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(item[1])
            set_font(run, size=11)
        elif kind == 'p_bold':
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(item[1])
            set_font(run, size=11, bold=True)
        elif kind == 'p_gray':
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(item[1])
            set_font(run, size=9, color=C_GRAY)
        elif kind == 'h':
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(item[1])
            set_font(run, size=13, bold=True, color=C_PRIMARY)
        elif kind == 'c':
            fname = item[1] + '.png'
            path = os.path.join(CHART_DIR, fname)
            if os.path.exists(path):
                doc.add_picture(path, width=Inches(5.5))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p = doc.add_paragraph()
                run = p.add_run('[图表缺失: %s]' % fname)
                set_font(run, size=10, color=C_GRAY)

    doc.save(OUT)
    print('DOCX saved: %s (%d KB)' % (OUT, os.path.getsize(OUT) // 1024))


build_doc()
print('完成')
