# -*- coding: utf-8 -*-
"""
08-28 巴西杯 巴西国际vs格雷米奥 头条深度版 docx (R19/R27)
输出: 📝文章/20260828/巴西国际vs格雷米奥_头条深度版.docx
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

CHART_DIR = r'I:\阿飞说球\database\charts_20260828_grenal'
OUT = r'I:\阿飞说球\📝文章\20260828\巴西国际vs格雷米奥_头条深度版.docx'
C_PRIMARY = RGBColor(0x1a, 0x3a, 0x5c)   # 深蓝
C_DARK = RGBColor(0x33, 0x33, 0x33)
C_GRAY = RGBColor(0x88, 0x88, 0x88)

TITLE = '格雷纳尔德比：主队51.5%热度，模型却翻转看客队'
TAGS = '#巴西国际 #格雷米奥 #巴西杯 #足球前瞻 #数据分析'

BODY = [
    ('p', '很多人以为德比主场必占优，机构也确实给巴西国际开了51.5%的主胜热度，近10次坐镇主场打格雷米奥还赢过5场。但后台模型跑完14个维度，结论完全反过来——格雷米奥37.9%反超主队28.8%，一场"主队该赢"的德比，被拆成了"谁都怕输"的僵局。'),
    ('p_bold', '结论先行：这不是主队热度的胜利，是平局的胜利——近10次交锋5平、70%场次不超过2球，模型平局33.3%是全场最高单点；净胜2球几乎没戏（模型只有9.8%），受让方反而有强支撑。'),
    ('h', '一、 状态断崖 vs 德比战意：主队热度从哪来'),
    ('p_bold', '先看表象：'),
    ('p', '巴西国际主场对格雷米奥近10次5胜3平2负，巴西杯16强还3:2淘汰了科林蒂安，机构给51.5%主胜热度不算离谱。'),
    ('p_bold', '再看暗礁：'),
    ('p', '· 巴西国际近10场只有1胜（杯赛2:0科林蒂安），联赛1胜4平5负深陷泥潭'),
    ('p', '· 场均进球0.7个，只有联赛均值的一半多一点——进攻端彻底哑火'),
    ('p', '· 杯赛射手榜第一名是后卫伯纳比（3球、占全队38%）——进球靠定位球和后卫插上，阵地战根本打不动'),
    ('p_bold', '德比定律：'),
    ('p', '格雷纳尔近10次交锋3胜5平2负，平局率50%；10场里7场总进球不超过2个。这不是"强队碾压"的德比，是"谁也输不起"的德比——平局才是这条街的常态。'),
    ('h', '二、 机构态度与模型算力碰撞'),
    ('p', '· 近10场：巴西国际 1胜4平5负 进7失13｜格雷米奥 3胜2平5负 进10失14'),
    ('p', '· 场均进/失：巴西国际 0.7/1.3｜格雷米奥 1.0/1.4'),
    ('p', '· 交锋近10：巴西国际 3胜5平2负｜格雷米奥 2胜5平3负'),
    ('p', '· 主场/客场交锋：巴西国际 5胜3平2负｜格雷米奥 2胜3平5负'),
    ('p', '· 杯赛晋级路：巴西国际 16强总比分3:2科林蒂安｜格雷米奥 16强总比分2:1米拉索尔'),
    ('p', '· 伤停：双方均暂无数据'),
    ('p_bold', '模型 vs 机构：'),
    ('p', '· 巴西国际胜：模型 28.8% vs 机构 51.5%（🔴 -22.7pp）'),
    ('p', '· 平局：模型 33.3% vs 机构 28.1%（+5.2pp）'),
    ('p', '· 格雷米奥胜：模型 37.9% vs 机构 20.4%（🔴 +17.5pp）'),
    ('c', 'bar_gremio'),
    ('p_bold', '⚔️ 战意：'),
    ('p', '巴西杯八强是两回合制，首回合主场求先手，但3天后还有巴甲，次回合（09-04）才是分水岭——首回合没人会孤注一掷。德比双方都想赢，但更不想输。'),
    ('p_bold', '💰 信号：'),
    ('p', '机构对净胜2球的定价是25.3%，模型只有9.8%——门槛阻力比想象中大得多；总进球机构重心压在2球，模型大2.5只有28.8%，双共识指向小球。'),
    ('p_bold', '🌍 外媒：'),
    ('p', '暂无公开预测源可引用。中文媒体对格雷纳尔德比的常规叙事是"德比无弱旅、平局频出"——和交锋数据对得上。'),
    ('c', 'radar_gremio'),
    ('h', '三、 走势推演与核心矩阵'),
    ('p_bold', '剧本A——定位球先手（约30%）：'),
    ('p', '伯纳比角球抢点破门，1-0领先后巴西国际收缩，格雷米奥压上无效率，1-0/2-0收场——但净胜2球门槛大概率走空。'),
    ('p_bold', '剧本B——上半场僵持（约45%，最可能）：'),
    ('p', '中场绞杀，半场0-0，巴西国际求稳、格雷米奥乐得带平回主场，0-0/1-1把悬念留到次回合。'),
    ('p_bold', '剧本C——反击偷分（约25%）：'),
    ('p', '巴西国际压上防空当被反击打穿，0-1/0-2客队带走首回合优势——模型翻转兑现的路径。'),
    ('c', 'score_gremio'),
    ('p_bold', '高概率比分：0-0（16.1%）> 0-1（15.1%）> 1-1（14.0%）> 1-0（12.5%）> 0-2（8.0%）'),
    ('p_bold', '核心矩阵：'),
    ('p', '· 巴西国际 vs 格雷米奥｜机构 51.5% vs 模型 28.8%（🔴 -22.7pp）｜节奏 沉闷/1-2球｜比分 0-0 / 0-1（防 1-1）'),
    ('p_bold', '🎯 落脚：'),
    ('p', '方向 平局为中枢（模型33.3%）、格雷米奥不败有支撑（71.2%）；门槛 净胜2球几乎没戏（受让方+1强支撑）；进球 1-2球；比分 0-0 / 0-1（防 1-1）。'),
    ('h', '互动'),
    ('p_bold', '机构把巴西国际的主场热度拉到51.5%，后台模型却只认28.8%——你们觉得是机构错信了德比主场，还是模型低估了主队的杯赛战意？另一问：近10次交锋5平的两队，你赌继续闷还是出冷门？评论区聊聊。'),
    ('p_gray', '难说。真说不好。'),
    ('p_gray', '数据来源：懂球帝、ESPN、各队官网。'),
    ('p_gray', '注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。'),
    ('p_gray', '配图关键词（中英双语，无水印两队近期赛照）：1.格雷纳尔德比赛场照/Internacional vs Gremio Grenal derby 2026 2.巴西国际训练照/Internacional training 2026 3.格雷米奥客场比赛照/Gremio away match 2026 4.贝拉里奥球场/Beira-Rio stadium Porto Alegre 5.伯纳比头球破门资料图/A. Bernabei header goal 6.巴西杯奖杯/Copa do Brasil 2026 trophy 7.巴西国际晋级庆祝照/Internacional squad celebration 2026。无水印图源：懂球帝/新球体育（无角标）、俱乐部官方社媒、维基共享。'),
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
    run = p.add_run('德比没有弱旅，只有怕输的人。')
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
