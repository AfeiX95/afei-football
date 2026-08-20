# -*- coding: utf-8 -*-
"""
周五010 阿森纳vs考文垂 头条版 docx 生成 (R19)
输入: 📝文章/20260822/周五010_阿森纳vs考文垂_头条版.md
图表: database/charts_20260822_arsenal/*.png
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

TITLE = '阿森纳让两球：3-0曼城的火力，敢信净胜3球吗'
TAGS = '#阿森纳 #考文垂 #英超 #足球前瞻 #数据分析 #赛博聊球 #英超揭幕战 #足球分析 #体育头条'

BODY = [
    ('p', '英超揭幕战，阿森纳主场打升班马考文垂，机构直接开出让两球的深盘。有人看到"阿森纳"三个字就想闭眼跟，可后台模型跑完，这场真正的坑就藏在这个"让两球"里。'),
    ('p_bold', '结论先行：阿森纳赢球没悬念（模型主胜74%），但让两球要净胜3球。市场只给39.7%的概率，模型算出来49.8%。方向稳，深盘才是博弈点，而且这个点历史上翻车率不低。'),
    ('h', '🔪 撕开"豪门必胜"的假象'),
    ('p', '阿森纳这状态确实唬人：社区盾刚3-0干翻曼城，欧冠决赛跟巴黎圣曼踢到1:1，近10场6胜2平2负，进17球丢10球。酋长球场的主场，配上萨卡、厄德高这条线，打英冠升班马，谁看都觉得是送分题。'),
    ('p', '但拆开看细节。阿森纳热身赛其实两连败：2:3输多特、1:3输贝蒂斯，状态不是一路高涨。社区盾3-0曼城是真，热身赛连败也是真，只是大家选择性记住前者。'),
    ('p', '考文垂这边，近10场6胜4平0负，一场没输过，进21球只丢6球，热身赛2:0摩纳哥、3:1西班牙人。英冠升班马的数据要打折扣，但"不败韧性"是实打实的。这队摆起大巴来，不是那么好啃。'),
    ('h', '🔪 让两球，市场自己都虚'),
    ('p', '这场胜平负没开，直接开让两球深盘：机构给让两球胜开出约40%的理论概率（净胜3球以上才算赢），考文垂+2不败约37%。去水之后：净胜3球以上39.7%，考文垂+2不败36.9%，几乎五五开。'),
    ('p', '市场自己都没把握阿森纳能净胜3球。这跟"豪门必胜"的直觉是拧着的。'),
    ('h', '🔪 深盘的历史账，得翻一翻'),
    ('p', '后台模型跑完，阿森纳净胜3+概率是49.8%，比市场的39.7%高了10个百分点。模型认为阿森纳火力被低估，3-0曼城那场不是偶然。'),
    ('p', '但翻深盘的历史账：此前让两球/三球的深盘，让球方赢盘率0/2，全灭。里斯本让两球输吉马良斯、利雅新月让三球输对手，豪门让深盘照样翻车。深盘不像让一球，净胜3球的难度是几何级上升的，升班马摆大巴+门将超神，1-0、2-1这种比分随时可能。'),
    ('h', '📊 数据速览'),
    ('p', '阿森纳(主)：英超豪门（欧冠决赛级），近10场6胜2平2负，场均进1.7/失1.0，社区盾3-0曼城，热身2连败'),
    ('p', '考文垂(客)：英冠升班马，近10场6胜4平0负不败，场均进2.1/失0.6，热身2-0摩纳哥/3-1西班牙人'),
    ('c', 'bar_ars'),
    ('h', '🧮 模型'),
    ('p', '后台模型跑完（λ主2.20/λ客0.60，C05升班马修正）：阿森纳胜74.1%、平局17.2%、考文垂胜8.7%、大2.5概率53.1%。让两球维度：模型净胜3+ 49.8% vs 市场39.7%（+10.1pp）；考文垂+2不败模型25.9% vs 市场36.9%（-11.0pp）。模型认为阿森纳净胜3球概率被低估10个百分点，但深盘历史不佳，这个Edge要打折看。'),
    ('c', 'radar_ars'),
    ('h', '🌍 外媒'),
    ('p', '外媒几乎一边倒看阿森纳赢球：Opta分析师给阿森纳主胜高概率，CBS和Goal都预测阿森纳拿下揭幕战。但有意思的是，几乎没人敢打包票"净胜3球"，多数预测落在2-0、3-1这种两球区间，正好是让两球的"走盘边缘"。外媒的乐观，跟模型的谨慎撞了个满怀。'),
    ('h', '💰 信号'),
    ('p', '直说吧，这场方向没悬念，悬念全在"赢几个"。阿森纳赢球概率74%，但净胜3球概率只有一半。这就是让两球深盘最尴尬的地方：你觉得他会赢，可他赢2个还是赢3个，市场、模型、外媒三方都没底。'),
    ('p', '考文垂的不败韧性（近10场0负）+ 阿森纳热身赛的连败，这两个信号都在说同一件事：别把社区盾3-0当常态。'),
    ('h', '🎬 剧本'),
    ('p', '剧本A（主队碾压，约40%）：阿森纳前30分钟破门，升班马防线崩盘，3-0/4-0/5-0，社区盾火力重现。支持让两球胜、大球。'),
    ('p', '剧本B（主队小胜，约35%）：阿森纳控球但攻坚效率一般，1-0/2-0/2-1，考文垂摆大巴拖时间，阿森纳赢得不轻松。支持让两球平/负、小球。'),
    ('p', '剧本C（升班马偷分，约25%）：考文垂定位球/反击得手，1-1/0-1，酋长球场爆冷。支持让两球负、冷门方向。英超首秀的兴奋劲，是升班马最锋利的武器。'),
    ('h', '🎯 核心推演矩阵'),
    ('c', 'score_ars'),
    ('p', '阿森纳vs考文垂：模型主胜74.1%｜让-2净胜3+ 49.8% vs 市场39.7%（+10.1pp，深盘打折）｜中高进球｜比分2-0/3-0（防1-0）。'),
    ('p', '四重落脚：方向阿森纳胜（无悬念）｜门槛让两球难净胜3球，考文垂+2有价值（深盘历史0/2全灭）｜进球中高2-3球｜比分首选2-0，次选3-0，防范1-0（冷门1-1）。'),
    ('h', '互动'),
    ('p_bold', '阿森纳让两球这个盘，你们觉得是"3-0曼城的火力该信"，还是"深盘翻车的教训更深"？评论区留个比分，赛后回来验证。我先押2-0。阿森纳赢球没问题，但净胜3球，我持保留态度。'),
    ('p_gray', '数据来源：竞彩官方。'),
    ('p_gray', '注：本文为基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨与交流，请理性看待比赛。'),
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
