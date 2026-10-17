# -*- coding: utf-8 -*-
"""
周五010 阿森纳vs考文垂 头条版 docx 生成 v2（用户精修重构版）
结构：3大段（表象拆解/机构碰撞/走势推演）+ 核心矩阵，去碎片化
输出: 📝文章/20260822/周五010_阿森纳vs考文垂_头条版.docx
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

CHART_DIR = r'I:\阿飞说球\database\charts_20260822_arsenal'
OUT = r'I:\阿飞说球\📝文章\20260822\周五010_阿森纳vs考文垂_头条版.docx'
C_PRIMARY = RGBColor(0x1a, 0x3a, 0x5c)
C_DARK = RGBColor(0x33, 0x33, 0x33)
C_GRAY = RGBColor(0x88, 0x88, 0x88)

TITLE = '阿森纳让两球深开：刚3-0痛击曼城，真能净胜升班马3球？'
TAGS = '#阿森纳 #考文垂 #英超 #足球前瞻 #数据分析 #英超揭幕战 #足球分析 #体育头条'

BODY = [
    ('p', '英超揭幕战，阿森纳坐镇酋长球场迎战升班马考文垂。机构直接开出"净胜3球才能赢下"的深位门槛。不少球迷看到阿森纳的名字就想闭眼跟，但跑完后台多维攻防模型，这场球真正的博弈命门全在这个深位让步里。'),
    ('p_bold', '结论先行：阿森纳全取3分几无悬念（模型主胜概率达 74.1%），但想要净胜3球以上，市场仅给出了 39.7% 的预期。方向稳，但门槛极高，历史上此类超深让步被跨越的难度极大。'),
    ('h', '一、 豪门必胜的表象与细节暗礁'),
    ('p', '阿森纳的势头确实唬人：社区盾 3-0 击溃曼城，前场萨卡与厄德高的联动行云流水，面对英冠上来的升班马，纸面实力完全是降维打击。'),
    ('p', '但拆解热身赛细节会发现隐患：此前 2-3 负于多特、1-3 不敌贝蒂斯，球队防线在面对高压反击时并不稳固。社区盾的大胜吸满了市场关注度，却掩盖了此前攻防磨合的起伏。'),
    ('p', '反观考文垂，近 10 场各项赛事 6 胜 4 平保持不败，场均丢球仅 0.6 个。虽然英冠与热身赛的含金量需要打折，但升班马在英超首秀往往会祭出极度务实的"铁桶阵+反击"，绝非轻易能被撕碎的软柿子。'),
    ('h', '二、 机构态度与模型算力的碰撞'),
    ('c', 'bar_ars'),
    ('p', '机构在胜平负层面给出了压倒性倾斜，但在深位让步上，去水后阿森纳净胜 3 球的概率仅为 39.7%，考文垂守住受让优势的概率达到 36.9%，近乎五五开。机构自身对阿森纳大胜并无十足把握。'),
    ('p_bold', '模型概率推演：'),
    ('p', '· 阿森纳独赢：74.1%（绝对优势）'),
    ('p', '· 净胜 3 球及以上：49.8%（比机构预期高出 10.1 个百分点）'),
    ('p', '· 进球总数：倾向 2-3 球区间，大比分发生的概率约 53.1%'),
    ('c', 'radar_ars'),
    ('p', '外媒（如 Opta 与 CBS）虽然全员看好阿森纳赢球，但主流预测基本锁定在 2-0、3-1 这类两球分差区间，恰好卡在深位门槛边缘。'),
    ('h', '三、 比赛走势推演与核心矩阵'),
    ('p', '本场比赛大概率在以下三种走势中展开：'),
    ('p', '1. 主队压制小胜（约 45%）：考文垂全员退守，阿森纳控球破局但攻坚耗时，打出 2-0 或 2-1。'),
    ('p', '2. 进攻火力全开（约 35%）：阿森纳早早取得进球打破僵局，考文垂被迫压出导致防线崩盘，比分奔向 3-0、4-0。'),
    ('p', '3. 升班马偷袭得手（约 20%）：考文垂依靠定位球或反击偷分，阿森纳久攻不下被逼平（1-1）。'),
    ('c', 'score_ars'),
    ('p_bold', '核心矩阵：阿森纳 vs 考文垂｜模型主胜 74.1%｜净胜3+ 偏高(+10.1pp) 但深位历史阻力大｜控球攻坚 / 2-3球｜前瞻比分 2-0 / 3-0（防 2-1）'),
    ('h', '互动'),
    ('p_bold', '面对考文垂的严密防线与极高的数据门槛，大家觉得阿森纳能延续击败曼城的火力打出大胜，还是会陷入 1-2 球的小胜胶着？评论区聊聊你的预测比分！'),
    ('p_gray', '数据来源：竞彩官方。'),
    ('p_gray', '注：本文基于球队技战术框架、热身赛数据与数学模型推演，仅供足球运动战术探讨，请理性看待比赛。'),
    ('p_gray', '配图关键词（中英双语，无水印两队近期赛照）：1.阿森纳近期比赛照（社区盾）/Arsenal 2026 Community Shield 2.阿森纳主场（酋长球场）/Emirates Stadium 3.阿森纳训练照/Arsenal training 2026 4.考文垂近期比赛照/Coventry City 2026 match 5.考文垂升级庆祝/Coventry promotion celebration 6.英超揭幕战海报/Premier League opening match 7.两队队徽（无水印）/Arsenal vs Coventry crest。无水印图源：懂球帝/新球体育（无角标）、俱乐部官方社媒、维基共享。'),
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
