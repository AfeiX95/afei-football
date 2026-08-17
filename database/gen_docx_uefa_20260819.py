# -*- coding: utf-8 -*-
"""
欧冠附加赛两场 头条版 docx 生成 (R19: 白底图/小标题/互动钩子/无PDF预览)
输入: 📝文章/20260819/欧冠附加赛两场_..._头条版.md (读取)
图表: database/charts_uefa_20260819/*.png
输出: database/欧冠附加赛两场_费内巴切vs里昂+萨格勒布vs维京_头条版.docx
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

MD_PATH = r'I:\阿飞说球\📝文章\20260819\欧冠附加赛两场_费内巴切vs里昂+萨格勒布vs维京_头条版.md'
CHART_DIR = r'I:\阿飞说球\database\charts_uefa_20260819'
OUT_PATH = r'I:\阿飞说球\database\欧冠附加赛两场_费内巴切vs里昂+萨格勒布vs维京_头条版.docx'

C_PRIMARY = RGBColor(0x1a, 0x3a, 0x5c)   # 深蓝
C_ACCENT = RGBColor(0x0e, 0x66, 0x55)    # 深绿
C_DARK = RGBColor(0x33, 0x33, 0x33)
C_GRAY = RGBColor(0x88, 0x88, 0x88)

def set_font(run, size=11, bold=False, color=C_DARK, name='微软雅黑'):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)

def add_para(doc, text, size=11, bold=False, color=C_DARK, align=None, space_after=6):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    set_font(run, size=size, bold=bold, color=color)
    return p

def add_heading_styled(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    size = 16 if level == 0 else (14 if level == 1 else 12)
    set_font(run, size=size, bold=True, color=C_PRIMARY)
    return p

def add_chart(doc, filename, width=6.0):
    path = os.path.join(CHART_DIR, filename)
    if os.path.exists(path):
        doc.add_picture(path, width=Inches(width))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        add_para(doc, f'[图表缺失: {filename}]', color=C_GRAY)

doc = Document()
# 默认字体
style = doc.styles['Normal']
style.font.name = '微软雅黑'
style.font.size = Pt(11)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

# ===== 标题 =====
add_heading_styled(doc, '费内巴切主场藏着三根刺，萨格勒布自认"轻微热门"也怕偷袭', 0)
add_para(doc, '#欧冠附加赛 #费内巴切 #里昂 #萨格勒布迪纳摩 #维京 #足球前瞻 #数据分析 #赛博聊球 #欧冠 #足球分析', size=9, color=C_GRAY)
add_para(doc, '数据不会说谎，但人会。——阿飞·赛博聊球', size=10, color=C_GRAY, align=WD_ALIGN_PARAGRAPH.CENTER)

# ===== 速览卡 =====
add_heading_styled(doc, '赛事速览', 1)
add_para(doc, '场次一：费内巴切(主) vs 里昂(客) ｜ 欧冠附加赛首回合 ｜ 08-19 03:00 ｜ 萨拉科格鲁球场 ｜ 次回合08-27里昂主场')
add_para(doc, '场次二：萨格勒布迪纳摩(主) vs 维京(客) ｜ 欧冠附加赛首回合 ｜ 08-19 03:00 ｜ 马克西米尔球场 ｜ 次回合08-26维京主场(人造草)')

# ===== 核心结论 =====
add_heading_styled(doc, '核心结论（先说重点）', 1)
add_para(doc, '后台模型跑完这两场欧冠附加赛，结论有点反直觉：费内巴切这场市场定价在"半球"到"半一"之间，听着像豪门主场该有的样子，但模型拆完发现——土超揭幕战刚爆冷输球、欧战主场此前3场不胜、卢卡库大概率替补。主胜55.8%，比市场定价隐含的46%高出一截，却也远没到"稳赢"的份上。')
add_para(doc, '萨格勒布这场，克媒自己都说"轻微热门"，主队近10场不败、主场7胜3平0负、防守场均只丢0.6球，但3名新援不报名、克甲强度打折，维京还是2025挪超卫冕冠军、队史首次打进欧冠、带着定位球杀招来的。模型主胜64.8%，大球概率跟MatchPulse的62%撞了个满怀。')
add_para(doc, '一句话：两场都是"主场热门但热得有水分"，次回合都在客队主场——首回合的每一球都值钱。', bold=True)

# ===== 场次一 =====
add_heading_styled(doc, '场次一：费内巴切 vs 里昂', 1)

add_heading_styled(doc, '⚔️ 战意', 2)
add_para(doc, '费内巴切主场作战，主帅卡塔尔赛前放话"要在主场球迷面前拿到优势比分"——他们18年没进过欧冠正赛，把这份"18年之痒"当机会看。首回合在自家地盘，目标明确：多进球、少丢球，给08-27的客场次回合留缓冲。')
add_para(doc, '里昂这边目标完全不同。法甲还没开赛（08-23才打首轮），全队心思就在这两回合。客场进球规则已经取消，首回合0-1、1-2这种小负完全能接受——只要不崩，回里昂主场3-0翻盘的事他们上轮刚干过（布拉格斯巴达就是被他们主场打花的）。')

add_heading_styled(doc, '📊 数据', 2)
add_para(doc, '费内巴切：近10场8胜2平0负，场均进球2.5/失球0.6，同主客7胜3平0负，欧战R2/R3 3胜1平进5丢1。')
add_para(doc, '里昂：近10场6胜0平4负，场均进球2.5/失球2.2，同主客（客场）2胜3平5负，欧战R3客1-2负/主3-0胜。')
add_para(doc, '费内巴切欧冠资格赛4场只丢1球，防守是真稳。但里昂客场10场只赢2场，客战能力是硬伤——可问题出在"状态"上。竞彩网近10场列的是8胜2平，但那没算上08-16的土超揭幕战——费内巴切客场1-2爆冷输给根克勒比利吉，塔利斯卡先进球都被逆转，高层赛后还炮轰裁判。刚输完球就来踢欧冠，士气不是满格。')

add_heading_styled(doc, '🧵 暗线：卢卡库这个悬念', 2)
add_para(doc, '这场的最大变数不是战术，是卢卡库。时间线很有意思：8月14日比利时媒体说他联赛首轮不打、欧冠附加赛也不打 → 8月17日初版名单果然没有他 → 结果同一天俱乐部更新名单，又把他补进去了。主帅卡塔尔说得很委婉："还没100%恢复，但具备出场条件。"')
add_para(doc, '翻译一下：大概率替补待命。真要首发且状态在线，费内巴切攻坚能力上一个档次；要是不上，比赛就可能被拖进慢节奏。这个悬念到赛前1小时出23人名单才揭晓。')

add_heading_styled(doc, '🧮 模型', 2)
add_para(doc, '后台模型v2.9.0跑完（λ主1.71 / λ客0.93）：费内巴切胜55.8%、平局23.9%、里昂胜20.2%、大2.5概率49.1%。')
add_chart(doc, 'bar_m1.png')
add_chart(doc, 'radar_m1.png')

add_heading_styled(doc, '🌍 外媒对比', 2)
add_para(doc, 'Onefootball直接问了个扎心的问题："里昂真的是弱势方吗？"Le Progrès说里昂欧战经验不如费内巴切，Afrik-Foot说里昂碰上了难缠对手。但土媒这边全是主场论——费内巴切近31场欧战主场赢了20场，卡迪柯伊是块硬骨头。外媒大方向一致：主队热门，但没人敢说稳。')

add_heading_styled(doc, '💰 信号', 2)
add_para(doc, '市场信号其实在"分歧"里：6家主流公司从平/半集体升盘到半球（365/韦德/明陞/12B/利记/盈禾），澳门更是开到半一——资金在往主队方向走。但威廉希尔和香港盘还停在平/半低水，保守派明显。主胜定价从开盘2.03降到2.00，资金偏主队但幅度不大。')
add_para(doc, '说白了，市场信费内巴切的主场，但不信它能大胜。这个"半球"而不是"一球"的定价，本身就是对费内巴切状态水分的最诚实表达。')
add_chart(doc, 'signals_m1.png')
add_chart(doc, 'score_m1.png')

add_heading_styled(doc, '🎬 剧本', 2)
add_para(doc, '剧本A（主队控制小胜，约42%）：费内巴切定位球或塔利斯卡破门，1-0/2-1，次回合带优势去法国。')
add_para(doc, '剧本B（闷平/小比分，约32%）：里昂摆低位防守，卢卡库不上场的话主队攻坚费劲，0-0/1-1——里昂的目标直接达成。')
add_para(doc, '剧本C（客队偷袭，约26%）：里昂奥彭达/奈尔斯反击得手，1-1/1-2，费内巴切主场丢分。')

add_heading_styled(doc, '🎯 推荐', 2)
add_para(doc, '推荐比分：首选 1-0（12.3%）→ 次选 2-1（9.7%）→ 留意 1-1（11.4%）。冷门方向 0-1（6.6%）。大小球方面，模型49.1%接近市场2.75盘，中性略偏大，别追大。')

# ===== 场次二 =====
add_heading_styled(doc, '场次二：萨格勒布迪纳摩 vs 维京', 1)

add_heading_styled(doc, '⚔️ 战意', 2)
add_para(doc, '萨格勒布迪纳摩近10场6胜4平0负，克甲+欧冠双线不败，主场7胜3平0负，防守场均丢0.6球。主场看台开赛前两天就卖光了三个看台，气势拉满。')
add_para(doc, '但维京是另一种心态——2025挪超卫冕冠军，队史第一次踏上欧冠赛场，队长赛前放话"要做第一支淘汰迪纳摩的挪威队"。欧战经验为零，可这股子新鲜劲和野心，恰恰是最难量化的东西。而且克媒还爆了个细节：维京赛前拒绝了一份约2000万欧的报价，核心阵容稳得很，就是要来拼一把。')
add_para(doc, '挪超的球队平时踢人造草，首回合在萨格勒布天然草上客场作战，目标就是别崩、别大输，把悬念留回08-26的斯塔万格主场——那里有人造草，那才是他们的主场杀招。')

add_heading_styled(doc, '📊 数据', 2)
add_para(doc, '萨格勒布：近10场6胜4平0负，场均进球2.3/失球0.6，同主客7胜3平0负。近期克甲4-0、欧冠5-0/2-1。')
add_para(doc, '维京：近10场6胜2平2负，场均进球2.0/失球1.2，同主客6胜2平2负。近期挪超1-2客负罗森博格。')
add_para(doc, '首次交锋，没有H2H参考。萨格勒布欧冠打图恩两回合惊险过关（客2-2、主3-2加时），打考纳斯倒是7-1碾压——面对摆大巴的球队，他们的攻坚能力没那么吓人。维京这边，近两个挪超客场0-1、1-2都输了，客战强队是真不行。')

add_heading_styled(doc, '🧵 暗线', 2)
add_para(doc, '克媒把这场看得挺透：主帅Bjelica亲口说"我们是轻微热门"，然后补了一句——要警惕维京的定位球。更狠的是，克媒还点名了：维京队里有个出生于里耶卡的前锋，对克罗地亚足球门儿清。')
add_para(doc, '另外还有两个冷信号：萨格勒布3名夏窗新援不会为这场附加赛报名——阵容深度打了折；而执法本场的荷兰裁判Gözübüyük，迪纳摩此前在他手下全败——这裁判不是迪纳摩的福星。')

add_heading_styled(doc, '🧮 模型', 2)
add_para(doc, '后台模型v2.9.0跑完（λ主1.94 / λ客0.78）：萨格勒布胜64.8%、平局21.0%、维京胜14.2%、大2.5概率63.2%（含C27赛季初大球修正）。模型给主胜64.8%，比克媒"五五开偏主"要激进一点，但大球概率跟MatchPulse的62%几乎重合——大球是共识。')
add_chart(doc, 'bar_m2.png')
add_chart(doc, 'radar_m2.png')

add_heading_styled(doc, '🌍 外媒对比', 2)
add_para(doc, '克媒这边：Jutarnji说"轻微热门但有一件事会特别难受"，Sportklub说得更直白"迪纳摩略强，但维京在人工草皮上能制造麻烦"，24sata干脆说"五五开的比赛，但迪纳摩是热门"。挪媒那边全是"历史性时刻"的叙事。外媒的分歧不在主队赢不赢，而在"赢几个"和"维京能不能偷一个"。')

add_heading_styled(doc, '💰 信号', 2)
add_para(doc, '信号全在"定性"里：主帅自己都只说"轻微热门"，说明机构层面的优势没那么碾压。模型64.8%对应的是"让一球到一球半"之间——如果萨格勒布只让半球/半一，那是便宜了主队；要是让到一球以上，就得掂量掂量让-1陷阱的教训（本批69场里，主队让-1翻车率51.9%）。')
add_para(doc, '大球这边倒是难得的共识：模型63.2% + MatchPulse 62%，两个独立信号指向同一方向。')
add_chart(doc, 'signals_m2.png')
add_chart(doc, 'score_m2.png')

add_heading_styled(doc, '🎬 剧本', 2)
add_para(doc, '剧本A（主队控制胜，约45%）：萨格勒布控球压制，2-0/2-1，次回合带优势去挪威。')
add_para(doc, '剧本B（主队小胜/闷平，约35%）：维京摆大巴+定位球制造威胁，1-0/1-1/0-0。')
add_para(doc, '剧本C（客队偷袭，约20%）：维京反击得手，1-1/0-1，悬念拉满到次回合。')

add_heading_styled(doc, '🎯 推荐', 2)
add_para(doc, '推荐比分：首选 1-0（12.9%）→ 次选 2-0（12.3%）→ 留意 1-1（9.9%）。冷门方向 0-1（5.1%）。大小球：模型63.2%，大2.5可以跟，但别重仓——附加赛首回合客队保守是常态。')

# ===== 看点 =====
add_heading_styled(doc, '三个看点', 1)
add_para(doc, '1. 费内巴切"半球盘"的热门，能不能扛住自己刚爆冷的状态和卢卡库的替补悬念？')
add_para(doc, '2. 萨格勒布的"轻微热门"，会不会被维京的定位球和队史首次的野性咬下一口？')
add_para(doc, '3. 两场的次回合都在客队主场，首回合的比分差，会不会成为决定命运的伏笔？')

# ===== 钩子 =====
add_heading_styled(doc, '互动', 1)
add_para(doc, '两场都是"主场热门但热得有水分"——费内巴切靠防守和主场，萨格勒布靠不败和气势，但次回合的主动权都在客队手里。我押费内巴切1-0、萨格勒布2-0，你们呢？评论区留比分，赛后回来验证。', bold=True)

# ===== 数据来源+免责 =====
add_para(doc, '数据来源：竞彩官方及新球体育（titan007）、外媒多源交叉。', size=9, color=C_GRAY)
add_para(doc, '行文仓促，里面的图片和数据都是从官方渠道和权威媒体上整过来的，侵删。这都是我个人图一乐的瞎琢磨，千万别当真，理智看球、远离赌博才是正道。', size=9, color=C_GRAY)

doc.save(OUT_PATH)
print(f'DOCX saved: {OUT_PATH}')
print(f'Size: {os.path.getsize(OUT_PATH)/1024:.0f} KB')
