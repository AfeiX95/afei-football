# generate_docx.py - 西班牙vs比利时赛事前瞻 DOCX (降AI版)
import sys
sys.path.insert(0, r'C:\Users\Administrator\AppData\Local\Programs\Python\Python310\Lib\site-packages')

from docx import Document
from docx.shared import Pt

doc = Document()

style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(11)

title = doc.add_heading('', level=1)
run = title.add_run('7月11日 西班牙VS比利时 传控王者遇到反击高手')
run.font.size = Pt(16)

doc.add_paragraph('——')

# 引子
p = doc.add_paragraph()
p.add_run('列位看官，且听我道来。').bold = True

doc.add_paragraph(
    '世界杯打到这个份上，八强里还剩四张脸——法国已经进了半决赛（2比0摩洛哥）。'
    '剩下三席，明早出结果。西班牙碰比利时这场，说实话看点最多。'
)
doc.add_paragraph(
    '倒不是说两边实力碾压其他队——而是这俩的风格撞得厉害。'
    '一个传控宗师，一个反击老手。谁也别笑谁。'
)

doc.add_paragraph('——')

p = doc.add_paragraph()
p.add_run('先说西班牙。').bold = True
doc.add_paragraph(
    'H组头名出线，1比0把葡萄牙送回家了。三场淘汰赛两场零封，后防确实稳。\n\n'
    '队里几个关键人物：罗德里（曼城铁腰），进可攻退可守，西班牙攻防转换的节拍器。'
    '佩德里（巴萨大脑），传控体系的中枢神经——说实在的没有他西班牙中场少了一半创造力。'
    '边路有两个滑板车——左边尼科·威廉姆斯，靠速度生吃；右边亚马尔，靠技术内切。'
    '16岁的小孩，已经踢成主力了，也是邪门。\n\n'
    '主帅德拉富恩特这个人有点东西。2022世界杯之后接手，把西班牙从16强出局的阴影里拉了出来'
    '（话说回来，那届西班牙点球输摩洛哥，也是憋屈）。'
    '传控底子没丢，但加了更多纵向突破和边路爆破。'
)

doc.add_paragraph('——')

p = doc.add_paragraph()
p.add_run('再说比利时。').bold = True
doc.add_paragraph(
    'G组头名，1/8决赛4比1把美国打趴了。四球入账，攻击力不赖。\n\n'
    '德布劳内（曼城传奇中场），34岁了——竟然还是世界上最好的传球手。'
    '卢卡库，比利时历史射手王，这届状态回暖（悄悄说，小组赛那几场他有点挣扎，淘汰赛反而活了）。'
    '多库，曼城边路爆点，一对一过人成功率在这届世界杯排第一——'
    '平均每场能过他那个对位的人三四次。\n\n'
    '比利时"黄金一代"快散伙了，这话说了好几年。'
    '但这批老将的经验和默契，新上来的年轻队真不一定比得了。'
    '4比1美国那场，证明他们还有劲。'
)

doc.add_paragraph('——')

p = doc.add_paragraph()
p.add_run('这场战术本质：传控围城打铁桶反击。').bold = True

doc.add_paragraph(
    '西班牙控球率估计60-65%，边中结合、肋部渗透找空间。'
    '但西班牙的问题——破密集防守一直不太灵光。'
    '1/8打葡萄牙控了六成五的球，就进了一个（赫苏斯·纳瓦斯传中，莫拉塔铲射）。'
    '你要说稳，那是稳；你要说吓人，那也差点意思。'
)
doc.add_paragraph(
    '比利时策略很明确：缩回去，让出控球，等你出错。'
    '德布劳内一脚直塞、卢卡库背身做球、多库边路爆破——随便哪一次打成了都能要命。'
)
doc.add_paragraph(
    '最关键对决在中场：罗德里vs德布劳内。两个世界级的，谁先控制住节奏，谁赢面大。'
)

doc.add_paragraph('——')

p = doc.add_paragraph()
p.add_run('后台模型算了一遍：').bold = True
doc.add_paragraph('西班牙期望进球1.50，比利时1.20。加起来2.70。')

# 表1
t1 = doc.add_table(rows=4, cols=4)
t1.style = 'Table Grid'
for j, h in enumerate(['结果', '后台模型', '欧赔', '市场概率']):
    t1.rows[0].cells[j].text = h
    for r in t1.rows[0].cells[j].paragraphs:
        for rn in r.runs:
            rn.bold = True
for i, rd in enumerate([['西班牙胜','43.9%','1.62','55.9%'],['平局','25.6%','3.60','25.2%'],['比利时胜','30.6%','4.80','18.9%']]):
    for j, v in enumerate(rd):
        t1.rows[i+1].cells[j].text = v

doc.add_paragraph(
    '市场给西班牙开了1.62的赔率。隐含胜率55.9%。'
    '但后台模型算出来西班牙只有43.9%。差了一截。'
    '说到底还是品牌溢价——西班牙这个牌子大了三四百年'
    '（不好意思，足球上的大国周期倒没那么长，但欧洲杯三连冠的老本够吃一阵子）。'
    '比利时这块牌子不值那个钱，但模型觉得他们被低估了。'
)

# 表2
t2 = doc.add_table(rows=6, cols=3)
t2.style = 'Table Grid'
for j, h in enumerate(['比分','概率','参考赔率']):
    t2.rows[0].cells[j].text = h
    for r in t2.rows[0].cells[j].paragraphs:
        for rn in r.runs:
            rn.bold = True
for i, rd in enumerate([['1-1','12.1%','6.50'],['1-0','10.0%','7.00'],['2-1','8.9%','8.50'],['0-1','8.1%','9.00'],['2-0','7.6%','9.50']]):
    for j, v in enumerate(rd):
        t2.rows[i+1].cells[j].text = v

doc.add_paragraph(
    '进球区间：0-1球24.8%、2-3球46.6%、4+球28.6%。'
    '大小球五五开——大2.5是50.6%、小2.5是49.4%。'
    '说白了，这场球2-3球最稳妥。'
)

doc.add_paragraph('——')

p = doc.add_paragraph()
p.add_run('四个胜负点。').bold = True

doc.add_paragraph(
    '第一，首球时间。西班牙25分钟前破门——那球就进入他们最舒服的传控消耗节奏了，'
    '比利时很难翻。35分钟还0-0——比利时反击效率会上去，西班牙体能开始往下掉'
    '（啧啧，7月美国那个天气不是开玩笑的）。'
)
doc.add_paragraph(
    '第二，多库vs西班牙左后卫。多库过人成功率接近70%（英超数据）。'
    '西班牙左后卫不管是库库雷利亚还是格里马尔多，都需要协防。'
    '多库突破成功一次，比利时反击就有站位点。'
)
doc.add_paragraph(
    '第三，卢卡库vs西班牙后防线。西班牙后卫平均183cm。'
    '卢卡库190cm、90公斤。背身拿球、禁区争顶——老实说有点欺负人。'
)
doc.add_paragraph(
    '第四，替补深度。比利时替补席还有特罗萨德、奥蓬达。'
    '60-70分钟后换人冲刺，攻击力反而比首发更吓人。'
    '上半场0-0的话——下半场比利时后程发力，这个冷门剧本看过很多次了。'
)

doc.add_paragraph('——')

p = doc.add_paragraph()
p.add_run('冷门路径？').bold = True

doc.add_paragraph(
    '路径A（最现实）：上半场0-0，65分钟后比利时换人冲击。'
    '西班牙体能下降，德布劳内一脚直塞打穿防线——卢卡库或者替补捡漏。概率大约18%。'
)
doc.add_paragraph(
    '路径B：比利时开场闪击先破门。西班牙压上反扑，反而给比利时更多空间。'
    '最终两球或以上。大约8%。'
)
doc.add_paragraph(
    '路径C：对攻局，比分交替上升。2-2进加时甚至点球。大约15%。\n\n'
    '顺便说一句——法国已经在半决赛等着了。谁赢这场谁打法国。'
    '西班牙打法国=欧洲杯决赛翻版（2024欧洲杯西班牙赢了法国晋级决赛）。'
    '比利时打法国=2018半决赛翻版（当时法国1-0赢了比利时）。'
    '两边都有心理账要算。'
)

doc.add_paragraph('——')

p = doc.add_paragraph()
run = p.add_run('数据不会说谎，但人会。——阿飞·赛博聊球')
run.bold = True

doc.add_paragraph('\n你觉得这场咋样，比分写评论区。')
doc.add_paragraph('明晨三点，赛后见。')

p = doc.add_paragraph()
run = p.add_run('\n图一乐的赛事分析，纯个人看法别当真。')
run.font.size = Pt(9)
p = doc.add_paragraph()
run = p.add_run('数据来源：懂球帝、新浪体育')
run.font.size = Pt(9)

doc.add_paragraph()
p = doc.add_paragraph()
run = p.add_run('=== Illustration Suggestions ===')
run.bold = True

for s in [
    '[1] Spain national team group photo (2026 World Cup) — official FIFA portrait',
    '[2] Belgium national team group photo (2026 World Cup) — official FIFA portrait',
    '[3] Rodri in action vs Portugal (2026-07-06 R16) — midfield control shot',
    '[4] Kevin De Bruyne action shot vs USA (2026-07-05 R16) — key pass moment',
    '[5] Tactical comparison: Spain 4-3-3 possession vs Belgium 3-4-3 counter-attack — formation diagram',
    '[6] Data visualization: Poisson probability matrix for ESP-BEL QF — bar chart of top 5 scores',
]:
    p = doc.add_paragraph()
    run = p.add_run(s)
    run.font.size = Pt(9)

doc.save(r'D:\Hermes\football\阿飞说球\04_赛事文章\西班牙vs比利时\西班牙vs比利时_赛事前瞻.docx')
print('OK')
