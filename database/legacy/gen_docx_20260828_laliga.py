# -*- coding: utf-8 -*-
"""
08-28 西甲两场 (巴萨vs毕尔巴鄂 + 塞尔塔vs奥萨苏纳) 头条版 docx (R19/R27)
输出: 📝文章/20260828/西甲两场_二合一头条版.docx
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

CHART_DIR = r'I:\阿飞说球\database\charts_20260828_laliga'
OUT = r'I:\阿飞说球\📝文章\20260828\西甲两场_二合一头条版.docx'
C_PRIMARY = RGBColor(0x1a, 0x3a, 0x5c)   # 深蓝
C_DARK = RGBColor(0x33, 0x33, 0x33)
C_GRAY = RGBColor(0x88, 0x88, 0x88)

TITLE = '巴萨超热却难净胜2球？西甲两场一热一闷'
TAGS = '#巴萨 #毕尔巴鄂 #塞尔塔 #奥萨苏纳 #西甲 #足球前瞻 #数据分析'

BODY = [
    ('p', '西甲新一轮有两场焦点：巴萨主场迎战垫底的毕尔巴鄂，机构给主队开出近74%的理论胜率，清一色"稳稳拿下"；另一场塞尔塔对奥萨苏纳，两支首轮都是0:0的球队碰面，看起来就是一场闷局。'),
    ('p', '可后台模型跑完，两场都有反常识的地方。'),
    ('p_bold', '结论先行：巴萨场，热度撑不起净胜2球——市场给出52.7%的净胜2球概率，模型只给40.1%；塞尔塔场，小球是双共识——模型32.4%的大球概率和机构对总进球数2球的重心，罕见一致。'),
    ('h', '一、 巴萨 vs 毕尔巴鄂：热度撑不起净胜2球'),
    ('p_bold', '先看表象：'),
    ('p', '巴萨近10次对毕尔巴鄂 8胜2平0负，首轮客场5:0大胜埃尔切；毕尔巴鄂首轮主场1:3惨败塞维利亚，唯一的进球还是中卫帕雷德斯进的，左后卫Yuri还停赛。怎么看都是碾压局。'),
    ('p_bold', '再看暗礁：'),
    ('p', '机构给巴萨近74%胜率、净胜2球概率52.7%；后台模型只有63.5%和40.1%——分歧12.6个百分点。说白了，市场预期是"血洗"，模型觉得"赢球没问题，赢两个不一定"。'),
    ('p', '· 排名：巴萨 第5（1胜0平0负）｜毕尔巴鄂 第20（0胜0平1负）'),
    ('p', '· 近10场：巴萨 7胜1平2负 进23失10｜毕尔巴鄂 5胜1平4负 进28失13*（含6场友谊赛，11:0为鱼腩泡沫，模型已剔除降权）'),
    ('p', '· 交锋近10：巴萨 8胜2平0负｜毕尔巴鄂 0胜2平8负'),
    ('p', '· 伤停：巴萨 暂无｜毕尔巴鄂 Yuri（左后卫）停赛'),
    ('c', 'bar_barca'),
    ('p_bold', '⚔️ 战意：'),
    ('p', '巴萨少赛一轮，抢分追榜首；毕尔巴鄂垫底，3天后还要客战塞尔塔，连续客场作战，大概率不会跟巴萨对攻。'),
    ('p_bold', '💰 信号：'),
    ('p', '主胜定价从1.22一路降到1.20、净胜2球从1.75降到1.68、半全场胜胜从1.70降到1.65——三个玩法同步收紧，资金一致流向巴萨大胜方向。但模型跑完，净胜2球概率不到一半（40.1%），净胜1球加输掉方向合计近六成——这波热度，有点过头了。'),
    ('p_bold', '🌍 外媒：'),
    ('p', '暂无公开预测源可引用。特征页数据显示巴萨全面占优，但交锋近10场也有0:0、1:0、2:1这种小比分先例——碾压不等于场场大胜。'),
    ('c', 'radar_barca'),
    ('p_bold', '🎬 走势推演：'),
    ('p', '1. 毕尔巴鄂收缩摆大巴 → 巴萨 2-0/1-0 收场，净胜2球门槛走空风险大（约40%）；2. 毕尔巴鄂被迫压上 → 3-0/3-1 大胜（约35%）；3. 久攻不下被偷袭 → 1-1/0-1（约25%）。'),
    ('c', 'score_barca'),
    ('p_bold', '高概率比分：2-0（10.6%）> 1-1（10.0%）> 2-1（9.9%）> 1-0（9.7%）> 3-0（7.4%）'),
    ('p_bold', '🎯 落脚：'),
    ('p', '方向 巴萨取胜；门槛 净胜2球阻力大（净胜1球概率23.4%）；进球 2-3球；比分 2-0 / 2-1（防 1-1）。'),
    ('h', '二、 塞尔塔 vs 奥萨苏纳：0:0开局的两队，小球是双共识'),
    ('p_bold', '先看表象：'),
    ('p', '塞尔塔近10场5胜4平1负，奥萨苏纳3胜1平6负——状态差了一大截，主队1.78的中低位定价看着合理。'),
    ('p_bold', '再看暗礁：'),
    ('p', '两队首轮全是0:0（塞尔塔客平巴伦西亚、奥萨苏纳主平莱万特），合计0进球。后台模型跑完，大2.5只有32.4%，机构对总进球数的重心也压在2球——小球双共识。塞尔塔近10场平局率40%，历史交锋10场里也出现过两场0:0。这场球的悬念，可能不是谁赢，而是有没有人进球。'),
    ('p', '· 排名：塞尔塔 第12（0胜1平0负）｜奥萨苏纳 第11（0胜1平0负）'),
    ('p', '· 近10场：塞尔塔 5胜4平1负 进16失9｜奥萨苏纳 3胜1平6负 进11失14'),
    ('p', '· 交锋近10：4胜2平4负 完全均势（含两场0:0）'),
    ('p', '· 场均进/失：塞尔塔 1.6/0.9｜奥萨苏纳 1.1/1.4'),
    ('c', 'bar_celta'),
    ('p_bold', '⚔️ 战意：'),
    ('p', '塞尔塔3天后主场迎战毕尔巴鄂，本场是抢分和保持势头的窗口；奥萨苏纳客场求分。中游互搏，谁也输不起。'),
    ('p_bold', '💰 信号：'),
    ('p', '模型51.1% vs 市场49.8%，几乎没有偏差——定价精准型比赛，无便宜可占。净胜2球概率模型24.6%、市场23.9%，同样是"市场已定价"。说白了，这场没有价值洼地，只有"小球"这个共识。'),
    ('p_bold', '🌍 外媒：'),
    ('p', '网易体育赛前报道点题"两队首轮均交出1平0进球答卷，谁能打破僵局"——进球荒之战，媒体同样不看好对攻。'),
    ('c', 'radar_celta'),
    ('p_bold', '🎬 走势推演：'),
    ('p', '1. 塞尔塔一球定音 → 1-0（17.1%）；2. 双方都进不了 → 0-0/1-1（合计26.9%）；3. 奥萨苏纳反击偷分 → 0-1。'),
    ('c', 'score_celta'),
    ('p_bold', '高概率比分：1-0（17.1%）> 0-0（14.1%）> 1-1（12.8%）> 2-0（11.7%）> 0-1（8.7%）'),
    ('p_bold', '🎯 落脚：'),
    ('p', '方向 塞尔塔不败；门槛 净胜2球几乎没戏；进球 1-2球；比分 1-0 / 1-1（防 0-0）。'),
    ('h', '🏁 核心推演矩阵'),
    ('p', '· 巴萨 vs 毕尔巴鄂｜机构 73.8% vs 模型 63.5%（-10.3pp）｜节奏 大热/2-3球｜比分 2-0 / 2-1（防 1-1）'),
    ('p', '· 塞尔塔 vs 奥萨苏纳｜机构 49.8% vs 模型 51.1%（+1.3pp）｜节奏 沉闷/1-2球｜比分 1-0 / 1-1（防 0-0）'),
    ('p_bold', '巴萨那场，你们觉得是机构真信巴萨能大胜垫底队，还是模型低估了豪门主场的碾压？另一场，0:0开局的两支球队碰面，你赌有进球还是赌继续闷？评论区聊聊。'),
    ('p_gray', '足球这东西，谁说得准呢。'),
    ('p_gray', '数据来源：懂球帝、ESPN、各队官网。'),
    ('p_gray', '注：本文基于两队技战术、历史数据与赛事背景的客观模型推演，仅供足球运动战术探讨，请理性看待比赛。'),
    ('p_gray', '配图关键词（中英双语，无水印两队近期赛照）：1.巴萨训练照/Barcelona squad training 2026 2.巴萨vs毕尔巴鄂历史交锋照/Barcelona vs Athletic Club 2026 3.毕尔巴鄂尤里停赛资料图/Athletic Yuri 2026 4.塞尔塔巴拉伊多斯球场/Celta Vigo Balaidos stadium 5.塞尔塔训练照/Celta Vigo training 2026 6.奥萨苏纳客场比赛照/Osasuna away 2026 7.西甲官方标识/La Liga 2026 logo。无水印图源：懂球帝/新球体育（无角标）、俱乐部官方社媒、维基共享。'),
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
    run = p.add_run('机构看热，模型看冷，两场西甲都别急着站队。')
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
