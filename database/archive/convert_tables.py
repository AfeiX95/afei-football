# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()

style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(10)

# 标题
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
run = p.add_run('周四003欧罗巴安德莱VS哈马比 周四005欧罗巴本菲卡VS圣加仑')
run.bold = True
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)

p = doc.add_paragraph()
run = p.add_run('#欧罗巴 #本菲卡 #圣加仑 #安德莱 #哈马比 · 2026-07-30/31 · 资格赛第二轮次回合')
run.font.size = Pt(8)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('数据不会说谎，但人会。——阿飞·赛博聊球')
run.italic = True
run.font.size = Pt(11)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

# 一、赛事全景对比表
p = doc.add_paragraph()
run = p.add_run('一、两场赛事全景')
run.bold = True
run.font.size = Pt(12)

table = doc.add_table(rows=8, cols=3)
table.style = 'Light Grid Accent 1'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

headers = ['对比项', '本菲卡 vs 圣加仑', '安德莱赫特 vs 哈马比']
data = [
    ['赛事', '欧罗巴资格赛次回合', '欧罗巴资格赛次回合'],
    ['时间', '07-31 03:00', '07-31 02:30'],
    ['首回合', '圣加仑 2-1 本菲卡', '哈马比 1-1 安德莱'],
    ['翻盘条件', '本菲卡需赢2球晋级', '安德莱赢球即晋级'],
    ['客队策略', '摆大巴守0-0晋级', '稳守反击争客场进球'],
    ['核心看点', '豪门复仇vs黑马坚守', '平局大师vs三叉戟攻击'],
    ['模型倾向', '平局有价值（+14.3pp）', '平局有价值（+12.3pp）'],
]

for i, h in enumerate(headers):
    cell = table.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(9)

for row_idx, row_data in enumerate(data):
    for col_idx, cell_data in enumerate(row_data):
        cell = table.rows[row_idx + 1].cells[col_idx]
        cell.text = cell_data
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9)

doc.add_paragraph('')

# 二、近10场战绩对比表
p = doc.add_paragraph()
run = p.add_run('二、近10场战绩对比（竞彩网官方数据）')
run.bold = True
run.font.size = Pt(12)

table2 = doc.add_table(rows=5, cols=5)
table2.style = 'Light Grid Accent 1'
table2.alignment = WD_TABLE_ALIGNMENT.CENTER

headers2 = ['球队', '胜/平/负', '胜率', '场均进球', '场均失球']
data2 = [
    ['本菲卡', '5胜3平2负', '50%', '2.4', '1.4'],
    ['圣加仑', '7胜1平2负', '70%🔥', '2.0', '1.6'],
    ['安德莱赫特', '3胜5平2负', '30%', '1.4', '1.6'],
    ['哈马比', '5胜2平3负', '50%', '2.1', '1.2'],
]

for i, h in enumerate(headers2):
    cell = table2.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(9)

for row_idx, row_data in enumerate(data2):
    for col_idx, cell_data in enumerate(row_data):
        cell = table2.rows[row_idx + 1].cells[col_idx]
        cell.text = cell_data
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9)

doc.add_paragraph('')

# 三、本菲卡近10场详细战绩
p = doc.add_paragraph()
run = p.add_run('三、本菲卡近10场详细战绩')
run.bold = True
run.font.size = Pt(12)

table3 = doc.add_table(rows=11, cols=5)
table3.style = 'Light Grid Accent 1'
table3.alignment = WD_TABLE_ALIGNMENT.CENTER

headers3 = ['日期', '赛事', '主队', '比分', '结果']
data3 = [
    ['07-25', '俱乐部赛', '本菲卡', '5:1 贝伦enses', '胜'],
    ['07-24', '欧罗巴', '圣加仑', '2:1 本菲卡', '负'],
    ['07-18', '俱乐部赛', '本菲卡', '2:0 比利亚雷亚尔', '胜'],
    ['07-12', '俱乐部赛', '本菲卡', '1:2 弗拉门戈', '负'],
    ['07-04', '俱乐部赛', '本菲卡', '2:2 卡尔达什', '平'],
    ['05-17', '葡超', '埃斯托里尔', '1:3 本菲卡', '胜'],
    ['05-12', '葡超', '本菲卡', '2:2 布拉加', '平'],
    ['05-03', '葡超', '法马利康', '2:2 本菲卡', '平'],
    ['04-26', '葡超', '本菲卡', '4:1 摩雷伦斯', '胜'],
    ['04-20', '葡超', '里斯本竞技', '1:2 本菲卡', '胜'],
]

for i, h in enumerate(headers3):
    cell = table3.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(9)

for row_idx, row_data in enumerate(data3):
    for col_idx, cell_data in enumerate(row_data):
        cell = table3.rows[row_idx + 1].cells[col_idx]
        cell.text = cell_data
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9)

doc.add_paragraph('')

# 四、圣加仑近10场详细战绩
p = doc.add_paragraph()
run = p.add_run('四、圣加仑近10场详细战绩')
run.bold = True
run.font.size = Pt(12)

table4 = doc.add_table(rows=11, cols=5)
table4.style = 'Light Grid Accent 1'
table4.alignment = WD_TABLE_ALIGNMENT.CENTER

headers4 = ['日期', '赛事', '主队', '比分', '结果']
data4 = [
    ['07-26', '瑞士超', '圣加仑', '2:1 苏黎世', '胜'],
    ['07-24', '欧罗巴', '圣加仑', '2:1 本菲卡', '胜'],
    ['07-18', '俱乐部赛', '圣加仑', '0:3 诺维奇', '负'],
    ['07-11', '俱乐部赛', '里昂', '6:3 圣加仑', '负'],
    ['07-02', '俱乐部赛', '温特图尔', '0:1 圣加仑', '胜'],
    ['06-27', '俱乐部赛', '圣加仑', '3:2 阿特阿赫', '胜'],
    ['05-24', '瑞士杯', '洛桑奥希', '0:3 圣加仑', '胜'],
    ['05-17', '瑞士超', '圣加仑', '1:1 图恩', '平'],
    ['05-14', '瑞士超', '巴塞尔', '1:3 圣加仑', '胜'],
    ['05-10', '瑞士超', '卢加诺', '1:2 圣加仑', '胜'],
]

for i, h in enumerate(headers4):
    cell = table4.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(9)

for row_idx, row_data in enumerate(data4):
    for col_idx, cell_data in enumerate(row_data):
        cell = table4.rows[row_idx + 1].cells[col_idx]
        cell.text = cell_data
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9)

doc.add_paragraph('')

# 五、安德莱赫特近10场详细战绩
p = doc.add_paragraph()
run = p.add_run('五、安德莱赫特近10场详细战绩')
run.bold = True
run.font.size = Pt(12)

table5 = doc.add_table(rows=11, cols=5)
table5.style = 'Light Grid Accent 1'
table5.alignment = WD_TABLE_ALIGNMENT.CENTER

headers5 = ['日期', '赛事', '主队', '比分', '结果']
data5 = [
    ['07-24', '欧罗巴', '哈马比', '1:1 安德莱', '平'],
    ['07-16', '俱乐部赛', '阿尔克马', '0:1 安德莱', '胜'],
    ['07-11', '俱乐部赛', '安德莱', '3:2 奈梅亨', '胜'],
    ['07-04', '俱乐部赛', '安德莱', '0:0 布洛涅', '平'],
    ['05-25', '比甲', '圣吉联合', '5:1 安德莱', '负'],
    ['05-22', '比甲', '安德莱', '3:1 圣图尔登', '胜'],
    ['05-17', '比甲', '安德莱', '2:2 梅赫伦', '平'],
    ['05-14', '比利时杯', '圣吉联合', '1:1 安德莱', '平'],
    ['05-10', '比甲', '根特', '1:1 安德莱', '平'],
    ['05-04', '比甲', '安德莱', '1:3 布鲁日', '负'],
]

for i, h in enumerate(headers5):
    cell = table5.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(9)

for row_idx, row_data in enumerate(data5):
    for col_idx, cell_data in enumerate(row_data):
        cell = table5.rows[row_idx + 1].cells[col_idx]
        cell.text = cell_data
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9)

doc.add_paragraph('')

# 六、哈马比近10场详细战绩
p = doc.add_paragraph()
run = p.add_run('六、哈马比近10场详细战绩')
run.bold = True
run.font.size = Pt(12)

table6 = doc.add_table(rows=11, cols=5)
table6.style = 'Light Grid Accent 1'
table6.alignment = WD_TABLE_ALIGNMENT.CENTER

headers6 = ['日期', '赛事', '主队', '比分', '结果']
data6 = [
    ['07-26', '瑞超', '布鲁马波', '1:1 哈马比', '平'],
    ['07-24', '欧罗巴', '哈马比', '1:1 安德莱', '平'],
    ['07-19', '瑞超', '哈马比', '4:0 代格福什', '胜'],
    ['07-12', '瑞超', '哈马比', '2:0 卡尔马', '胜'],
    ['07-05', '瑞超', '埃夫斯堡', '1:2 哈马比', '胜'],
    ['06-24', '俱乐部赛', '赫根', '1:4 哈马比', '胜'],
    ['05-31', '瑞超', '赫根', '3:2 哈马比', '负'],
    ['05-24', '瑞超', '哈马比', '1:2 索尔纳', '负'],
    ['05-21', '瑞超', '盖斯', '2:0 哈马比', '负'],
    ['05-17', '瑞超', '哈马比', '4:1 马尔默', '胜'],
]

for i, h in enumerate(headers6):
    cell = table6.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(9)

for row_idx, row_data in enumerate(data6):
    for col_idx, cell_data in enumerate(row_data):
        cell = table6.rows[row_idx + 1].cells[col_idx]
        cell.text = cell_data
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9)

doc.add_paragraph('')

# 七、14维评分卡对比
p = doc.add_paragraph()
run = p.add_run('七、14维评分卡对比')
run.bold = True
run.font.size = Pt(12)

table7 = doc.add_table(rows=8, cols=5)
table7.style = 'Light Grid Accent 1'
table7.alignment = WD_TABLE_ALIGNMENT.CENTER

headers7 = ['维度', '本菲卡评分', '本菲卡修正量', '安德莱评分', '安德莱修正量']
data7 = [
    ['近期状态', '0', '0.000', '-1', '-0.040'],
    ['主客场分离', '+2', '+0.080', '+1', '+0.040'],
    ['伤停影响', '0', '0.000', '0', '0.000'],
    ['球员身价差', '+2', '+0.100', '+1', '+0.050'],
    ['战意差', '+2', '+0.080', '+1', '+0.040'],
    ['H2H交锋', '-1', '-0.025', '0', '0.000'],
    ['xG数据', '0', '0.000', '-1', '-0.050'],
]

for i, h in enumerate(headers7):
    cell = table7.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(9)

for row_idx, row_data in enumerate(data7):
    for col_idx, cell_data in enumerate(row_data):
        cell = table7.rows[row_idx + 1].cells[col_idx]
        cell.text = cell_data
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9)

doc.add_paragraph('')

# 八、模型推演概率对比
p = doc.add_paragraph()
run = p.add_run('八、模型推演概率对比')
run.bold = True
run.font.size = Pt(12)

table8 = doc.add_table(rows=4, cols=5)
table8.style = 'Light Grid Accent 1'
table8.alignment = WD_TABLE_ALIGNMENT.CENTER

headers8 = ['方向', '本菲卡模型', '本菲卡市场', '安德莱模型', '安德莱市场']
data8 = [
    ['主胜', '65.5%', '79.4%', '38.0%', '64.5%'],
    ['平局', '26.5%🔥', '12.2%', '38.5%🔥', '26.2%'],
    ['客胜', '8.0%', '8.4%', '23.5%', '22.2%'],
]

for i, h in enumerate(headers8):
    cell = table8.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(9)

for row_idx, row_data in enumerate(data8):
    for col_idx, cell_data in enumerate(row_data):
        cell = table8.rows[row_idx + 1].cells[col_idx]
        cell.text = cell_data
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9)

doc.add_paragraph('')

# 九、高概率比分对比
p = doc.add_paragraph()
run = p.add_run('九、高概率比分对比')
run.bold = True
run.font.size = Pt(12)

table9 = doc.add_table(rows=5, cols=5)
table9.style = 'Light Grid Accent 1'
table9.alignment = WD_TABLE_ALIGNMENT.CENTER

headers9 = ['排名', '本菲卡比分', '本菲卡概率', '安德莱比分', '安德莱概率']
data9 = [
    ['1', '2-0', '11.5%', '1-1', '13.5%'],
    ['2', '1-0', '10.8%', '0-0', '9.8%'],
    ['3', '1-1', '10.5%', '1-0', '10.2%'],
    ['4', '2-1', '10.2%', '2-1', '8.5%'],
]

for i, h in enumerate(headers9):
    cell = table9.rows[0].cells[i]
    cell.text = h
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(9)

for row_idx, row_data in enumerate(data9):
    for col_idx, cell_data in enumerate(row_data):
        cell = table9.rows[row_idx + 1].cells[col_idx]
        cell.text = cell_data
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(9)

doc.add_paragraph('')

# 十、核心研判
p = doc.add_paragraph()
run = p.add_run('十、核心研判')
run.bold = True
run.font.size = Pt(12)

doc.add_paragraph('六场欧罗巴，我挑了两场最值得聊的。')
doc.add_paragraph('一场是本菲卡被圣加仑2-1打脸后的复仇夜。一场是安德莱赫特这支平局大师主场翻盘的生死局。')
doc.add_paragraph('后台模型跑完20万次蒙特卡洛模拟，给了两个完全相反的信号。')

doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('本菲卡主场迎战圣加仑。')
doc.add_paragraph('首回合圣加仑2-1客胜本菲卡。葡超豪门被瑞超中游队打了个措手不及。')
doc.add_paragraph('圣加仑近10场70%的胜率？比本菲卡还高20个百分点？')
doc.add_paragraph('没错。首回合2-1客胜本菲卡不是偶然。圣加仑正处于赛季最佳状态段。')
doc.add_paragraph('后台模型跑了20万次，给了本菲卡65.5%的主场胜率。竞彩定价主胜1.25，隐含概率80.0%。差了14.5个百分点。')
doc.add_paragraph('平局概率：市场12.2%，模型26.5%。差了14.3个百分点。这是本场最大的价值信号。')

doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('安德莱赫特主场迎战哈马比。')
doc.add_paragraph('安德莱赫特近10场3胜5平2负。50%的平局率。五成。')
doc.add_paragraph('这不是偶尔平一场的问题，这是结构性的平局倾向。')
doc.add_paragraph('后台模型跑了20万次，给了安德莱赫特38.0%的主场胜率。竞彩定价主胜1.55，隐含概率64.5%。')
doc.add_paragraph('差了26.5个百分点的品牌溢价。')
doc.add_paragraph('平局概率：市场26.2%，模型38.5%。差了12.3个百分点。又是一个平局价值信号。')

doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('两场总结。本菲卡翻盘概率高但圣加仑70%胜率不容小觑。安德莱赫特平局大师属性+哈马比三叉戟攻击力=平局温床。')
doc.add_paragraph('今晚两场欧罗巴，平局可能是最大的赢家。')
doc.add_paragraph('你们觉得本菲卡能翻盘吗？安德莱赫特会不会又是平局？评论区留个比分，赛后回来验证。')

doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

p = doc.add_paragraph()
run = p.add_run('行文仓促，里面的图片和数据都是从官方渠道和权威媒体上整过来的，侵删。')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

p = doc.add_paragraph()
run = p.add_run('这都是我个人图一乐的瞎琢磨，千万别当真，理智看球、购买合法体育彩票才是正道。')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

p = doc.add_paragraph()
run = p.add_run('数据来源：中国竞彩网及各大权威外媒动态。')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

output_path = r"I:\阿飞说球\temp_output.docx"
doc.save(output_path)
print("Word document saved successfully")
