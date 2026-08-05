# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

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

# 一、两场赛事全景表
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

# 三、六维雷达图
p = doc.add_paragraph()
run = p.add_run('三、六维能力雷达图对比')
run.bold = True
run.font.size = Pt(12)

categories = ['近期状态', '进攻能力', '防守能力', '主场优势', '战意', '身价']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

benfica_values = [50, 80, 70, 85, 95, 90]
stgallen_values = [70, 65, 55, 40, 80, 30]
benfica_values += benfica_values[:1]
stgallen_values += stgallen_values[:1]

fig, ax = plt.subplots(figsize=(6, 5), subplot_kw=dict(polar=True))
ax.plot(angles, benfica_values, 'o-', linewidth=2, label='本菲卡', color='#1a1a2e')
ax.fill(angles, benfica_values, alpha=0.25, color='#1a1a2e')
ax.plot(angles, stgallen_values, 'o-', linewidth=2, label='圣加仑', color='#e74c3c')
ax.fill(angles, stgallen_values, alpha=0.25, color='#e74c3c')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylim(0, 100)
ax.set_title('本菲卡 vs 圣加仑 六维对比', fontsize=12, pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
chart1_path = r"I:\阿飞说球\radar_benfica.png"
plt.savefig(chart1_path, dpi=150, bbox_inches='tight')
plt.close()

doc.add_picture(chart1_path, width=Inches(4.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('')

ander_values = [35, 45, 50, 60, 70, 65]
hammarby_values = [55, 75, 60, 35, 60, 40]
ander_values += ander_values[:1]
hammarby_values += hammarby_values[:1]

fig, ax = plt.subplots(figsize=(6, 5), subplot_kw=dict(polar=True))
ax.plot(angles, ander_values, 'o-', linewidth=2, label='安德莱赫特', color='#1a1a2e')
ax.fill(angles, ander_values, alpha=0.25, color='#1a1a2e')
ax.plot(angles, hammarby_values, 'o-', linewidth=2, label='哈马比', color='#27ae60')
ax.fill(angles, hammarby_values, alpha=0.25, color='#27ae60')
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylim(0, 100)
ax.set_title('安德莱赫特 vs 哈马比 六维对比', fontsize=12, pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
chart2_path = r"I:\阿飞说球\radar_ander.png"
plt.savefig(chart2_path, dpi=150, bbox_inches='tight')
plt.close()

doc.add_picture(chart2_path, width=Inches(4.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('')

# 四、模型vs市场偏差对比图
p = doc.add_paragraph()
run = p.add_run('四、模型 vs 市场偏差对比')
run.bold = True
run.font.size = Pt(12)

fig, axes = plt.subplots(1, 2, figsize=(10, 4))

matches = ['主胜', '平局', '客胜']
model_vals = [65.5, 26.5, 8.0]
market_vals = [79.4, 12.2, 8.4]
edge_vals = [model_vals[i] - market_vals[i] for i in range(3)]

x = np.arange(len(matches))
width = 0.25

axes[0].bar(x - width, model_vals, width, label='模型', color='#1a1a2e')
axes[0].bar(x, market_vals, width, label='市场', color='#3498db')
axes[0].bar(x + width, edge_vals, width, label='Edge', color=['#e74c3c' if v < 0 else '#27ae60' for v in edge_vals])
axes[0].set_xlabel('方向')
axes[0].set_ylabel('概率 (%)')
axes[0].set_title('本菲卡 vs 圣加仑')
axes[0].set_xticks(x)
axes[0].set_xticklabels(matches)
axes[0].legend()
axes[0].axhline(y=0, color='gray', linestyle='--', linewidth=0.5)

model_vals2 = [38.0, 38.5, 23.5]
market_vals2 = [64.5, 26.2, 22.2]
edge_vals2 = [model_vals2[i] - market_vals2[i] for i in range(3)]

axes[1].bar(x - width, model_vals2, width, label='模型', color='#1a1a2e')
axes[1].bar(x, market_vals2, width, label='市场', color='#3498db')
axes[1].bar(x + width, edge_vals2, width, label='Edge', color=['#e74c3c' if v < 0 else '#27ae60' for v in edge_vals2])
axes[1].set_xlabel('方向')
axes[1].set_ylabel('概率 (%)')
axes[1].set_title('安德莱赫特 vs 哈马比')
axes[1].set_xticks(x)
axes[1].set_xticklabels(matches)
axes[1].legend()
axes[1].axhline(y=0, color='gray', linestyle='--', linewidth=0.5)

plt.tight_layout()
chart3_path = r"I:\阿飞说球\edge_comparison.png"
plt.savefig(chart3_path, dpi=150, bbox_inches='tight')
plt.close()

doc.add_picture(chart3_path, width=Inches(5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('')

# 五、比分概率分布图
p = doc.add_paragraph()
run = p.add_run('五、比分概率分布')
run.bold = True
run.font.size = Pt(12)

fig, axes = plt.subplots(1, 2, figsize=(10, 4))

scores_benfica = ['2-0', '1-0', '1-1', '2-1', '3-0', '0-0', '3-1', '0-1']
probs_benfica = [11.5, 10.8, 10.5, 10.2, 7.5, 6.2, 5.8, 3.5]
colors_benfica = ['#1a1a2e' if i < 3 else '#95a5a6' for i in range(len(scores_benfica))]
axes[0].barh(scores_benfica[::-1], probs_benfica[::-1], color=colors_benfica[::-1])
axes[0].set_xlabel('概率 (%)')
axes[0].set_title('本菲卡 vs 圣加仑')
for i, v in enumerate(probs_benfica[::-1]):
    axes[0].text(v + 0.2, i, f'{v}%', va='center', fontsize=9)

scores_ander = ['1-1', '0-0', '1-0', '2-1', '1-2', '2-0', '2-2', '0-1']
probs_ander = [13.5, 9.8, 10.2, 8.5, 7.2, 6.8, 5.5, 4.2]
colors_ander = ['#1a1a2e' if i < 3 else '#95a5a6' for i in range(len(scores_ander))]
axes[1].barh(scores_ander[::-1], probs_ander[::-1], color=colors_ander[::-1])
axes[1].set_xlabel('概率 (%)')
axes[1].set_title('安德莱赫特 vs 哈马比')
for i, v in enumerate(probs_ander[::-1]):
    axes[1].text(v + 0.2, i, f'{v}%', va='center', fontsize=9)

plt.tight_layout()
chart4_path = r"I:\阿飞说球\score_distribution.png"
plt.savefig(chart4_path, dpi=150, bbox_inches='tight')
plt.close()

doc.add_picture(chart4_path, width=Inches(5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('')

# 六、14维评分卡对比表
p = doc.add_paragraph()
run = p.add_run('六、14维评分卡对比')
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

# 七、模型推演概率对比表
p = doc.add_paragraph()
run = p.add_run('七、模型推演概率对比')
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

# 八、高概率比分对比表
p = doc.add_paragraph()
run = p.add_run('八、高概率比分对比')
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

# 九、核心研判
p = doc.add_paragraph()
run = p.add_run('九、核心研判（阿飞·赛博聊球版）')
run.bold = True
run.font.size = Pt(12)

doc.add_paragraph('六场欧罗巴，我挑了两场最有意思的。')
doc.add_paragraph('不是因为强队，不是因为冷门，而是因为两组完全相反的数据信号。')

doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

# 本菲卡部分
p = doc.add_paragraph()
run = p.add_run('【首回合回顾】')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('首回合在圣加仑主场，2-1。')
doc.add_paragraph('葡超豪门被瑞超中游队打了个措手不及。那场比赛我看了回放，圣加仑全场拼抢积极，反击效率极高，两次打穿本菲卡防线。本菲卡控球率占优但进攻效率低下，前场创造力严重不足。')
doc.add_paragraph('1-2，客场带走3分+1个客场进球。')

p = doc.add_paragraph()
run = p.add_run('【数据反差】')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('但你把两队近10场数据拉出来看——')
doc.add_paragraph('本菲卡5胜3平2负，50%的胜率。圣加仑7胜1平2负，70%的胜率。')
doc.add_paragraph('等等。圣加仑近10场70%的胜率？比本菲卡还高20个百分点？')
doc.add_paragraph('没错。首回合2-1客胜本菲卡不是偶然。圣加仑正处于赛季最佳状态段。')

p = doc.add_paragraph()
run = p.add_run('【三层递进数据】')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('再看主场数据。本菲卡主场场均进2.4球失1.4球，攻防两端都在线。但圣加仑客场场均进2.0球失1.6球——这个客场数据放在瑞超已经是顶级水准。')
doc.add_paragraph('拉远看，本菲卡近10场进了24球，场均2.4球。圣加仑近10场进了20球，场均2.0球。进攻端差距只有0.4球——不大。')
doc.add_paragraph('这不是豪门碾压中游的剧本。这是势均力敌的对决。')

p = doc.add_paragraph()
run = p.add_run('【模型信号】')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('后台模型跑了20万次，给了本菲卡65.5%的主场胜率。竞彩定价主胜1.25，隐含概率80.0%。差了14.5个百分点。')
doc.add_paragraph('平局概率：市场12.2%，模型26.5%。差了14.3个百分点。这是本场最大的价值信号。')

p = doc.add_paragraph()
run = p.add_run('【戏剧性类比】')
run.italic = True
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_paragraph('说句不好听的，本菲卡现在的处境，有点像上赛季欧冠被利物浦淘汰的翻版——控球率占优但破不了密集防守。圣加仑要是真摆起大巴，本菲卡还真不一定能撕开缺口。')

p = doc.add_paragraph()
run = p.add_run('【比分预测】')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('我的判断：本菲卡能赢，但赢不了2球。最可能的比分是1-0或2-1。圣加仑大概率能守住1球差距，总比分2-2进加时。')
doc.add_paragraph('个人猜测比分方向：本菲卡2-1或1-0。但足球是圆的，圣加仑能客场2-1赢本菲卡，就能在光明球场守住0-0。')

doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

# 安德莱部分
p = doc.add_paragraph()
run = p.add_run('【数据反差开场】')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('安德莱赫特近10场：3胜5平2负。50%的平局率。')
doc.add_paragraph('五成。')
doc.add_paragraph('这不是偶尔平一场的问题，这是结构性的平局倾向。')

p = doc.add_paragraph()
run = p.add_run('【对比式数据】')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('两组数据放一起看：')
doc.add_paragraph('安德莱：场均进1.4球，失1.6球。净进-2球。')
doc.add_paragraph('哈马比：场均进2.1球，失1.2球。净进9球。')
doc.add_paragraph('安德莱的进攻效率只有哈马比的67%。防守漏洞比哈马比大25%。')
doc.add_paragraph('这不是豪门碾压中游的剧本。这是平局大师vs攻击型球队的对决。')

p = doc.add_paragraph()
run = p.add_run('【模型信号】')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('后台模型跑了20万次，给了安德莱赫特38.0%的主场胜率。竞彩定价主胜1.55，隐含概率64.5%。')
doc.add_paragraph('差了26.5个百分点的品牌溢价。')
doc.add_paragraph('平局概率：市场26.2%，模型38.5%。差了12.3个百分点。又是一个平局价值信号。')

p = doc.add_paragraph()
run = p.add_run('【热梗】')
run.italic = True
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_paragraph('说句不好听的，安德莱赫特这支球队，堪称"平局大师"——50%的平局率，比某些球队的胜率都高。你让市场给这支球队定64.5%的主胜概率？市场是不是对"豪门"有什么误解？')

p = doc.add_paragraph()
run = p.add_run('【比分预测】')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('我的判断：安德莱赫特赢不了。最可能的比分是1-1或0-0。哈马比的三叉戟在客场也有进球能力，贝萨拉的中场组织+林德和亚伯拉罕的终结，这套组合在瑞超已经证明了自己。安德莱赫特的进攻效率太低，场均1.4球，面对哈马比的防守很难撕开缺口。')
doc.add_paragraph('个人猜测比分方向：1-1或0-0。安德莱赫特靠首回合客场进球晋级，但过程不会好看。')

doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

# 结尾
doc.add_paragraph('两场总结。')
doc.add_paragraph('本菲卡翻盘概率高但圣加仑70%胜率不容小觑。安德莱赫特平局大师属性+哈马比三叉戟攻击力=平局温床。')
doc.add_paragraph('今晚两场欧罗巴，平局可能是最大的赢家。')

p = doc.add_paragraph()
run = p.add_run('我的最终判断：')
run.bold = True
run.font.size = Pt(11)

doc.add_paragraph('本菲卡vs圣加仑：首选2-1，次选1-0，防冷0-0')
doc.add_paragraph('安德莱vs哈马比：首选1-1，次选0-0，防冷1-0')

doc.add_paragraph('你们觉得本菲卡能翻盘吗？安德莱赫特会不会又是平局？评论区留个比分，赛后回来验证。')

doc.add_paragraph('─' * 50).alignment = WD_ALIGN_PARAGRAPH.CENTER

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('图一乐分析，理智看球。')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

output_path = r"I:\阿飞说球\temp_output.docx"
doc.save(output_path)
print("High-quality article saved")
