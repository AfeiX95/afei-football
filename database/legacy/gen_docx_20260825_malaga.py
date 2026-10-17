# -*- coding: utf-8 -*-
"""
周一010 马拉加vs拉科 头条版 docx 生成 (R19/R27b)
结构：3大段 + 核心矩阵，去碎片化
输出: 📝文章/20260825/周一010_马拉加vs拉科_头条版.docx
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

CHART_DIR = r'I:\阿飞说球\database\charts_20260825_malaga'
OUT = r'I:\阿飞说球\📝文章\20260825\周一010_马拉加vs拉科_头条版.docx'
C_PRIMARY = RGBColor(0x0e, 0x66, 0x55)   # 深绿 (轮换色系)
C_DARK = RGBColor(0x33, 0x33, 0x33)
C_GRAY = RGBColor(0x88, 0x88, 0x88)

TITLE = '西甲升班马德比：第18的热度，撑不起净胜2球的门槛'
TAGS = '#马拉加 #拉科鲁尼亚 #西甲 #足球前瞻 #数据分析 #升班马德比 #足球分析 #体育头条'

BODY = [
    ('p', '西甲这轮有个奇景：第18名的马拉加主场迎战第9名的拉科鲁尼亚，两支都是升班马，机构给主队的理论胜率只有 38%，却还是让出了一球。'),
    ('p', '可后台多维模型跑完，发现真正有意思的不是谁赢谁输，而是市场自己先打架了：胜平负盘面微热主队，让球盘面却把"客队+1 不败"顶到了 60.6%，比分盘 1-1 还挂着全场最低价。'),
    ('p_bold', '结论先行：马拉加的主场热度撑不起净胜 2 球的门槛（市场预期只有 16.1%，连净胜 1 球都只给 23.3%）。模型跑完直接把方向翻了过来——拉科胜率 36.7% 反超马拉加的 32.9%，平局 30.4% 是全场第二落点。我的倾向：拉科不败价值更高，平局是本场最硬的规律。'),
    ('h', '一、 第18让第9：升班马德比的反常开局'),
    ('p', '马拉加首轮客场被马竞 0-2 零封，锋线颗粒无收；拉科首轮主场 1-1 被埃尔切逼平。两个升班马，一个垫底区 0 分，一个中游 1 分，排名差了 9 位。'),
    ('p', '反常就在这：排名第 18 的马拉加，盘面反而微热第 9 的拉科（38.0% vs 30.3%）。主场因素能解释一部分，但解释不了全部——拉科客场近 10 场 5 胜 5 平 0 负，十场不败，场均失球只有 0.6 个，客场韧性强得离谱。'),
    ('p', '更扎眼的是马拉加的防线：5 人伤停里有 3 个是后卫，季前 4 场热身赛一场没零封过（2-2 富勒姆、4-2 阿拉比、2-2 吉达联合、3-3 莱斯特，四场丢 9 球），首轮再被马竞零封还丢 2 球。这样的防线，市场却让它们去给对手"一球门槛"？'),
    ('h', '二、 机构态度与模型算力的碰撞'),
    ('p_bold', '机构定价（去水后）：'),
    ('p', '· 马拉加胜 38.0% / 平局 31.6% / 拉科胜 30.3%'),
    ('p', '· 马拉加让-1 净胜2+ 仅 16.1%，拉科+1 不败高达 60.6%'),
    ('c', 'bar_malaga'),
    ('p', '平局 31.6% 是第二热门，比分盘 1-1 挂着全场最低价，总进球 2 球最低——机构嘴上给主队热度，身体语言全是"小比分平局或险胜"。'),
    ('p_bold', '模型概率推演：'),
    ('p', '· 拉科独赢：36.7%（反超马拉加，比市场高 6.3 个百分点）'),
    ('p', '· 马拉加独赢：32.9%（比市场低 5.1 个百分点，主队热度虚高）'),
    ('p', '· 平局：30.4%（与市场 31.6% 基本一致）'),
    ('p', '· 拉科不败：67.1%（比市场 62% 高 5 个百分点）'),
    ('c', 'radar_malaga'),
    ('p', '平局这个 30% 的高位不是拍脑袋：H2H 近 10 次交手马拉加 3 胜 5 平 2 负，平局率 50%；马拉加主场近 10 场 3 胜 6 平 1 负，平局率 60%；拉科客场近 10 场 5 平，平局率 50%。三个独立口径全指向平局。'),
    ('p', '外媒也全线不站主队：Sports Mole 直接预测 2-2 平局；7M 推介和局 + 半场客胜；印尼媒体 liga.id 更激进，看好拉科 1-2 客场带走三分。'),
    ('h', '三、 比赛走势推演与核心矩阵'),
    ('p', '1. 闷平收场（约 40%）：升班马互啄双方都怕输，马拉加防线残阵不敢压上，拉科客场求稳，0-0 或 1-1。平局三印证下这是最顺的剧本。'),
    ('p', '2. 拉科客场偷分（约 32%）：奥巴梅扬反击效率+马拉加防线 3 后卫缺阵，0-1 或 1-2。7M 都点名"半场客胜"。'),
    ('p', '3. 马拉加主场小胜（约 28%）：0 分主场+下轮客场踢皇马的抢分窗口逼出全力，楚佩（上季西乙 25 球）破门，1-0 或 2-1。马拉加唯一能讲的剧本。'),
    ('c', 'score_malaga'),
    ('p_bold', '核心矩阵：马拉加 vs 拉科鲁尼亚｜模型 拉科36.7%/平30.4%/马拉加32.9%｜模型翻转市场（+6.3pp）＋平局三印证｜谨慎互啄 / 1-2球｜前瞻比分 1-1 / 0-1（防 1-0）'),
    ('p_bold', '研判落脚：方向倾向拉科不败+平局价值（模型拉科不败 67.1%）；门槛马拉加让-1 净胜 2 球概率仅 16%，拉科+1 有支撑；进球倾向 1-2 球小比分；比分参考 1-1、0-1（防范 1-0）。'),
    ('h', '互动'),
    ('p_bold', '马拉加这个 38% 的热度，你觉得是机构真看好升班马主场，还是互啄局里给主队留的体面？你站马拉加小胜，还是站拉科客场拿分？评论区亮个比分，我先看好 1-1，50% 的平局率摆在那，我更信它是规律不是巧合。'),
    ('p_gray', '数据来源：竞彩官方。'),
    ('p_gray', '注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。'),
    ('p_gray', '配图关键词（中英双语，无水印两队近期赛照）：1.马拉加近期比赛照/Malaga CF 2026 match 2.马拉加主场（玫瑰园球场）/La Rosaleda Stadium 3.拉科鲁尼亚近期比赛照/Deportivo La Coruna 2026 match 4.奥巴梅扬比赛照/Aubameyang Deportivo 2026 5.拉科鲁尼亚客场作战照/Deportivo away 2026 6.西甲联赛积分榜（中游区域）/La Liga 2026 table 7.两队队徽（无水印）/Malaga vs Deportivo crest。无水印图源：懂球帝/新球体育（无角标）、俱乐部官方社媒、维基共享。'),
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
