# -*- coding: utf-8 -*-
"""
周五日职两场 头条版 docx 生成 (R19: 白底图/小标题/互动钩子)
输入: 📝文章/20260821/周五日职两场_柏太阳神+东京FC_头条版.md
图表: database/charts_20260821_jleague/*.png
输出: 📝文章/20260821/周五日职两场_柏太阳神+东京FC_头条版.docx
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

CHART_DIR = r'I:\阿飞说球\database\charts_20260821_jleague'
OUT = r'I:\阿飞说球\📝文章\20260821\周五日职两场_柏太阳神+东京FC_头条版.docx'
C_PRIMARY = RGBColor(0x0e, 0x66, 0x55)
C_DARK = RGBColor(0x33, 0x33, 0x33)
C_GRAY = RGBColor(0x88, 0x88, 0x88)

TITLE = '周五日职两场：主场50%的柏太阳神，遇上专克东京的千叶'
TAGS = '#柏太阳神 #长崎航海 #东京FC #千叶市原 #日职 #足球前瞻 #数据分析 #赛博聊球 #J联赛 #足球分析'

BODY = [
    ('p', '周五两场日职，牌面都是主队深热：柏太阳神1.39、东京FC1.37，清一色"主胜稳了"的定价。可后台模型跑完，这两场都不该闭眼跟。'),
    ('p', '先说结论：柏太阳神那场，主胜63%跟市场几乎一样，没便宜可占，真正的坑在让一球；东京FC那场更有意思，市场给它64.6%的胜率，可这家近10场只赢了2场，主场刚被灌了个1-5，对面千叶还是它近7次交手赢过4次的克星。'),
    ('p', '两场深热局，一个虚火，一个真坑。'),
    ('h', '⚽ 场次一：柏太阳神 vs 长崎航海（周五001 18:00）'),
    ('h', '先掰扯数据'),
    ('p', '柏太阳神新赛季2连胜，进5丢2，排第3，看着挺猛。但拆开看主场：同主客近10场5胜5负，正好一半一半。这队主场远没到"稳"的程度。近10场总况6胜1平3负，进17丢9，进攻还行，防守一般。'),
    ('p', '长崎航海排第10，近10场4胜1平5负，但客场是硬伤：同主客1胜1平8负，客场虫没跑。上一场客战0-1输冈山。进攻端还有个致命问题：全队进球100%靠蒂亚戈·桑塔纳一个人，他哑火整队就瘫。'),
    ('h', '交锋是7年前的旧账'),
    ('p', '两队近4次交手柏太阳神3胜，听着像克星。但翻日期：2018、2019年，7年前的比赛。阵容教练全换血了，这账不能算。真正要盯的是柏太阳神主场那50%的胜率，而不是老掉牙的交锋记录。'),
    ('h', '市场态度'),
    ('p', '主胜1.39（63.7%），让一球2.41。去水后让球胜才36.8%，让球负35.7%，几乎五五开。市场自己都没把握柏太阳神能净胜两球。总进球3球最低赔（3.55），半全场胜胜2.15，市场预期主队小胜+中高进球。'),
    ('h', '模型怎么说'),
    ('p', '后台模型跑完：主胜63.3%，平局21.5%，客胜15.2%。跟市场63.7%几乎零偏差，这场定价太准了，没Edge。大2.5概率50.6%，中性。'),
    ('c', 'bar_kashiwa'),
    ('p', '直说吧，这场方向没悬念，但赢1个还是赢2个，真不好说。柏太阳神主场一半的场次在输球，长崎虽然客场虫，可人家就靠一个前锋偷鸡，偷到就1-1甚至0-1。'),
    ('c', 'score_kashiwa'),
    ('p', '这场四重落脚：方向主胜（但别重仓）｜让一球难净胜2球，客队+1有价值｜进球2-3球中性｜比分首选1-0，次选2-1，防范1-1。'),
    ('h', '⚽ 场次二：东京FC vs 千叶市原（周五002 18:30）'),
    ('h', '这场才是真坑'),
    ('p', '东京FC排第17，千叶排第20，标准的垫底德比。市场给东京1.37（64.6%），可你看东京干了啥：近10场2胜3平5负，胜率20%；主场刚1-5被町田血洗，主场0胜1负。赛季2轮丢7球。'),
    ('p', '千叶更惨，2轮0进球，客场1胜1平8负。但问题来了：千叶专治东京。'),
    ('h', '克星信号不是旧账'),
    ('p', '近7次交手，千叶4胜1平2负，东京只赢2场。最关键的：2026年5月6日，千叶客场3-0血洗东京，就在3个月前，当季的交手，不是陈年旧账。东京主场踢千叶，心理上先矮半截。'),
    ('h', '市场为什么还敢深热？'),
    ('p', '因为千叶0进球垫底，市场觉得"再烂也能赢它"。但东京自己的状态呢？近10场20%胜率、主场刚崩盘。一个刚被灌5个的队，凭什么让一球还开1.37？14维评分跑完，东京合计-1，主队根本不占优。'),
    ('h', '模型与市场严重打架'),
    ('c', 'bar_tokyo'),
    ('p', '后台模型：主胜51.0%，平局29.0%，客胜20.1%。市场：主胜64.6%。'),
    ('p', '主胜被高估13.6个百分点，这是近几批校验里最大的Edge信号。平局模型比市场高7.1pp，客胜高6.6pp。让一球去水后，市场自己都只给东京38%的净胜两球概率。'),
    ('p', '小球也是共识：两队合计场均才1.8球，模型大2.5只有32.3%。'),
    ('c', 'score_tokyo'),
    ('p', '这场四重落脚：方向主胜但深度存疑（-13.6pp别追）｜让一球难净胜，千叶+1有价值｜小球1-2球｜比分首选1-0，次选1-1，防范0-1。'),
    ('h', '📊 两场速览'),
    ('p', '周五001 柏太阳神：市场63.7% vs 模型63.3%（差-0.4，无Edge，坑在让-1）'),
    ('p', '周五002 东京FC：市场64.6% vs 模型51.0%（差-13.6pp，克星+状态差双陷阱）'),
    ('h', '🎯 综合推荐'),
    ('p', '方向：两场都倾向主队不败，但东京FC场别追深热，那是全批最被高估的主胜。'),
    ('p', '门槛：两场让一球都难净胜2球，客队+1双场有价值。柏太阳神主场50%胜率、东京刚被千叶3-0，都不是净胜两球的料。'),
    ('p', '进球：两场都偏小，柏太阳神场2-3球中性，东京场明确1-2球小球。'),
    ('p', '比分参考：柏太阳神场1-0/2-1/1-1，东京场1-0/1-1/0-1。'),
    ('h', '互动'),
    ('p_bold', '周五两场日职，一场定价精准没油水，一场深热藏雷。你们觉得东京FC这1.37，是市场真觉得它能赢，还是忘了3个月前被千叶3-0的账？评论区留个比分，赛后回来验证。我先押：柏太阳神2-1，东京FC1-1。理由：一个赢但赢不轻松，一个干脆被克。'),
    ('p_gray', '数据来源：竞彩官方。'),
    ('p_gray', '注：本文为基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨与交流，请理性看待比赛。'),
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
    run = p.add_run('数据不会说谎，但人会。——阿飞·赛博聊球')
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
