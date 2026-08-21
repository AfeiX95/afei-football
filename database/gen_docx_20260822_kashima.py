# -*- coding: utf-8 -*-
"""
周六001 鹿岛鹿角vs福冈黄蜂 头条版 docx 生成 (R19)
输入: 📝文章/20260822/周六001_鹿岛鹿角vs福冈黄蜂_头条版.md
图表: database/charts_20260822_kashima/*.png
输出: 📝文章/20260822/周六001_鹿岛鹿角vs福冈黄蜂_头条版.docx
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

CHART_DIR = r'I:\阿飞说球\database\charts_20260822_kashima'
OUT = r'I:\阿飞说球\📝文章\20260822\周六001_鹿岛鹿角vs福冈黄蜂_头条版.docx'
C_PRIMARY = RGBColor(0x0e, 0x66, 0x55)
C_DARK = RGBColor(0x33, 0x33, 0x33)
C_GRAY = RGBColor(0x88, 0x88, 0x88)

TITLE = '鹿岛主场9胜1平，为何偏偏被福冈锁死？'
TAGS = '#鹿岛鹿角 #福冈黄蜂 #日职 #足球前瞻 #数据分析 #赛博聊球 #J联赛 #足球分析 #体育头条'

BODY = [
    ('p', '鹿岛鹿角，日职主场最硬的队之一：同主客 9 胜 1 平 0 负，赛季 2 连胜排第 4。福冈黄蜂呢？中游第 8，赛季客场一场没踢过。机构给鹿岛开出约 55% 的胜率，牌面怎么看都是"主队稳了"。'),
    ('p', '可后台模型跑完，发现一个被大多数人和机构忽略的变量：这两队一碰面，十次有五次是平局。'),
    ('p_bold', '结论先行：鹿岛赢面确实大（模型 52.5%），但本场真正有价值的信号在平局。H2H 近 10 次交手 5 平，主场对福冈 10 场 5 平，最近 2 次交锋全平（1-1、2-2）。机构给平局 26.5%，模型算出来 29%。做多平局，是本场最大的数据机会。'),
    ('h', '一、 主场无敌的表象与"克平"暗礁'),
    ('p', '鹿岛的主场数据是真的唬人：同主客 9 胜 1 平 0 负，赛季前两轮 2-1 胜名古屋、4-3 胜横滨水手，Léo Ceará 和 Čavrić 双前锋火力全开（两人包办全队 5 球）。纸面看，福冈这种中游队来鹿岛，就是送分。'),
    ('p', '但拆开两队的交手记录，画风突变。近 10 次碰面，鹿岛只赢了 3 场，平了 5 场，输了 2 场，胜率 30%，平局率 50%。更扎眼的是主场：鹿岛在自家球场对福冈 10 场 5 平，最近两次交锋（2025-08）全是平局，1-1、2-2。'),
    ('p', '福冈黄蜂不是来送分的，是来"磨"分的。这支球队的打法就是摆大巴+反击，三线火力分散（没人进球超 1 个），防守型中游队的典型做派。面对鹿岛这种控球型强队，福冈的生存法则就是：拖，拖到平局就是胜利。'),
    ('h', '二、 机构态度与模型算力的碰撞'),
    ('c', 'bar_kashima'),
    ('p', '机构给主胜 55.1%，但看让球玩法就露馅了：鹿岛让一球，让胜（净胜 2 球）才 27.7%，让负（福冈+1 不败）高达 43.9%，机构自己都不看好鹿岛净胜 2 球。比分盘 1-0 最低（5.50）、1-1 第二低（6.50），市场嘴上说主胜，身体很诚实：主队小胜或平局。'),
    ('p_bold', '模型概率推演：'),
    ('p', '· 鹿岛独赢：52.5%（方向对但幅度低于市场）'),
    ('p', '· 平局：29.0%（比机构 26.5% 高 2.5 个百分点）'),
    ('p', '· 福冈胜：18.5%（与市场一致，无价值）'),
    ('p', '· 进球：46% 中小球，市场 2 球最低赔'),
    ('c', 'radar_kashima'),
    ('p', '模型给平局的权重比市场高，理由就是那 50% 的 H2H 平局率，这不是模型拍脑袋，是两队近 10 次交手一场一场踢出来的规律。'),
    ('h', '三、 比赛走势推演与核心矩阵'),
    ('p', '这场比赛大概率在三种走势中展开：'),
    ('p', '1. 主队小胜（约 40%）：鹿岛双前锋破门，福冈摆大巴但失守，打出 1-0 或 2-1。鹿岛赢球，但赢不轻松。'),
    ('p', '2. 闷平收场（约 35%）：福冈复制 H2H 剧本，鹿岛攻坚乏力，0-0 或 1-1。50% 平局率不是偶然。'),
    ('p', '3. 客队偷袭（约 25%）：福冈定位球或反击得手，0-1 或 1-2，鹿岛主场爆冷丢分。'),
    ('c', 'score_kashima'),
    ('p_bold', '核心矩阵：日职鹿岛鹿角 vs 福冈黄蜂｜模型主胜 52.5%｜平局偏高(+2.5pp)，H2H 50%平率支撑｜控球攻坚 / 1-2球｜前瞻比分 1-0 / 1-1（防 2-0）'),
    ('p', '研判落脚：方向鹿岛不败为主（主胜+平局约 82%）；门槛让-1 难净胜 2 球，福冈+1 有价值；进球中小球；比分首选 1-0，次选 1-1，防范 2-0（冷门 0-1）。'),
    ('h', '互动'),
    ('p_bold', '鹿岛主场这么硬，福冈的"五平魔咒"这次还能延续吗？你们觉得是鹿岛终于啃下这块硬骨头，还是福冈继续当它的平局大师？评论区留个比分，赛后回来验证。我先看好 1-1，50% 的平局率，赌它是规律不是巧合。'),
    ('p_gray', '数据来源：竞彩官方。'),
    ('p_gray', '注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。'),
    ('p_gray', '配图关键词（中英双语，无水印两队近期赛照）：1.鹿岛鹿角近期比赛照/Kashima Antlers 2026 match 2.鹿岛主场（鹿岛足球场）/Kashima Soccer Stadium 3.Léo Ceará比赛照/Leo Ceara Kashima 2026 4.福冈黄蜂近期比赛照/Avispa Fukuoka 2026 match 5.福冈黄蜂防守照/Avispa Fukuoka defense 2026 6.日职积分榜前6/J1 League 2026 table 7.两队队徽（无水印）/Kashima vs Avispa crest。无水印图源：懂球帝/新球体育（无角标）、俱乐部官方社媒、维基共享。'),
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
    run = p.add_run('数据不会说谎，但热度会造假。')
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
