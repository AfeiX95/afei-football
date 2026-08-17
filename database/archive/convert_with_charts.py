# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

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

# ============ 一、赛事全景对比表 ============
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

# ============ 二、近10场战绩对比表 ============
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

# ============ 三、六维雷达图 ============
p = doc.add_paragraph()
run = p.add_run('三、六维能力雷达图对比')
run.bold = True
run.font.size = Pt(12)

categories = ['近期状态', '进攻能力', '防守能力', '主场优势', '战意', '身价']
N = len(categories)
angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

# 本菲卡 vs 圣加仑
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
ax.set_title('本菲卡 vs 圣加仑 六维对比', fontsize=12, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
chart1_path = r"I:\阿飞说球\radar_benfica.png"
plt.savefig(chart1_path, dpi=150, bbox_inches='tight')
plt.close()

doc.add_picture(chart1_path, width=Inches(4.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('')

# 安德莱 vs 哈马比
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
ax.set_title('安德莱赫特 vs 哈马比 六维对比', fontsize=12, fontweight='bold', pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
chart2_path = r"I:\阿飞说球\radar_ander.png"
plt.savefig(chart2_path, dpi=150, bbox_inches='tight')
plt.close()

doc.add_picture(chart2_path, width=Inches(4.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('')

# ============ 四、模型vs市场偏差对比图 ============
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
axes[0].set_title('本菲卡 vs 圣加仑', fontweight='bold')
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
axes[1].set_title('安德莱赫特 vs 哈马比', fontweight='bold')
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

# ============ 五、比分概率分布图 ============
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
axes[0].set_title('本菲卡 vs 圣加仑', fontweight='bold')
for i, v in enumerate(probs_benfica[::-1]):
    axes[0].text(v + 0.2, i, f'{v}%', va='center', fontsize=9)

scores_ander = ['1-1', '0-0', '1-0', '2-1', '1-2', '2-0', '2-2', '0-1']
probs_ander = [13.5, 9.8, 10.2, 8.5, 7.2, 6.8, 5.5, 4.2]
colors_ander = ['#1a1a2e' if i < 3 else '#95a5a6' for i in range(len(scores_ander))]
axes[1].barh(scores_ander[::-1], probs_ander[::-1], color=colors_ander[::-1])
axes[1].set_xlabel('概率 (%)')
axes[1].set_title('安德莱赫特 vs 哈马比', fontweight='bold')
for i, v in enumerate(probs_ander[::-1]):
    axes[1].text(v + 0.2, i, f'{v}%', va='center', fontsize=9)

plt.tight_layout()
chart4_path = r"I:\阿飞说球\score_distribution.png"
plt.savefig(chart4_path, dpi=150, bbox_inches='tight')
plt.close()

doc.add_picture(chart4_path, width=Inches(5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('')

# ============ 六、14维评分卡对比表 ============
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

# ============ 七、模型推演概率对比表 ============
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

# ============ 八、高概率比分对比表 ============
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

# ============ 九、核心研判 ============
p = doc.add_paragraph()
run = p.add_run('九、核心研判')
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
print("Word document with charts saved successfully")
