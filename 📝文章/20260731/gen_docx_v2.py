import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

CHARTS_DIR = r'I:\阿飞说球\📝文章\20260731\charts'
OUTPUT_PATH = r'I:\阿飞说球\📝文章\20260731\挪超前瞻_头条版_图表版_v2.docx'

doc = Document()

# ============ 样式设置 ============
style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
style.paragraph_format.line_spacing = 1.35

for section in doc.sections:
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

# ============ 工具函数 ============
def set_run_font(run, name='微软雅黑', size=None, bold=False, color=None):
    run.font.name = name
    run.element.rPr.rFonts.set(qn('w:eastAsia'), name)
    if size:
        run.font.size = Pt(size)
    if bold:
        run.bold = True
    if color:
        run.font.color.rgb = color

def add_heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        set_run_font(run, size=16 if level==1 else 13, bold=True, color=RGBColor(0x1A, 0x1A, 0x2E))
    return h

def add_para(text, bold=False, size=10.5, color=None, align=None, spacing_after=None):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, color=color)
    if align:
        p.alignment = align
    if spacing_after is not None:
        p.paragraph_format.space_after = Pt(spacing_after)
    return p

def add_table(headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                set_run_font(run, size=9, bold=True)
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = str(val)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    set_run_font(run, size=9)
    doc.add_paragraph()  # spacing
    return table

def add_chart(filename, width=5.5):
    path = os.path.join(CHARTS_DIR, filename)
    if os.path.exists(path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(path, width=Inches(width))
    else:
        add_para(f'[图表缺失: {filename}]', color=RGBColor(0xFF, 0x00, 0x00))

def add_sep():
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('━' * 36)
    set_run_font(run, size=8, color=RGBColor(0xCC, 0xCC, 0xCC))

def add_signal_box(text):
    """加粗信号框"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run('>>> ' + text)
    set_run_font(run, size=10.5, bold=True, color=RGBColor(0xC0, 0x39, 0x2B))

# =============================================
#  标题页（SEO优化 ≤30字）
# =============================================
# 标题：挪超前瞻：两场主胜被高估 模型跑出20pp偏差（22字）
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(40)
run = p.add_run('挪超前瞻：两场主胜被高估')
set_run_font(run, size=24, bold=True, color=RGBColor(0x1A, 0x1A, 0x2E))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('模型跑出20pp偏差')
set_run_font(run, size=18, bold=True, color=RGBColor(0xC0, 0x39, 0x2B))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('瓦勒伦加VS汉坎 · 博德闪耀VS利勒斯特')
set_run_font(run, size=12, color=RGBColor(0x55, 0x55, 0x55))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('阿飞·赛博聊球 | 2026-08-01 | 挪超第16轮')
set_run_font(run, size=10, color=RGBColor(0x88, 0x88, 0x88))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('#挪超 #瓦勒伦加 #汉坎 #博德闪耀 #利勒斯特 #足球前瞻 #数据分析')
set_run_font(run, size=9, color=RGBColor(0x2E, 0x86, 0xC1))

add_sep()

# =============================================
#  金句 + 核心结论前置
# =============================================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('数据不会说谎，但人会。')
set_run_font(run, size=12, bold=True, color=RGBColor(0x33, 0x33, 0x33))

add_para('')

add_para('后台模型跑了20万次，跑出了一个今晚最硬的信号：两场挪超主胜都被市场高估了，总偏差20个百分点。', size=10.5)
add_para('')

add_para('瓦勒伦加主场定价1.49，市场隐含59.4%。模型只给了48.6%。差了10.8pp。', size=10.5)
add_para('博德闪耀主场定价1.17，市场隐含75.7%。模型只给了65.7%。差了10.0pp。', size=10.5)
add_para('')

add_para('说白了，市场被"排名差"和"豪门光环"骗了。你看到第7打第10、第1打第4，自动觉得主队稳了。但后台模型拆开了H2H、主客场分离数据、欧冠轮换变量后，发现这两场的真正价值藏在客队方向。', size=10.5)

add_sep()

# =============================================
#  场次一：瓦勒伦加 vs 汉坎
# =============================================
add_heading('⚔️ 瓦勒伦加 vs 汉坎 | 01:00 | Intility Arena', level=1)

add_chart('radar_m1.png', width=4.5)
add_para('')

# 战意
add_para('⚔️ 战意', bold=True, size=13)
add_para('')
add_para('瓦勒伦加第7，汉坎第10。排名差3位，听起来主队稳了？')
add_para('但你把H2H拉出来看——近9场交锋，瓦勒伦加2胜4平3负。22%的胜率。')
add_para('汉坎是瓦勒伦加的绝对克星。9场只输2场，赢了3场，平了4场。这不是偶然，这是结构性压制。')
add_para('')
add_para('瓦勒伦加主场确实不差——4胜1平2负，57%的胜率，进15球失9球。但汉坎的客场？0胜3平4负，0%的胜率。听起来汉坎客场是鱼腩，但你仔细看——4场输球的对手是博德闪耀、特罗姆瑟、萨普斯堡、腓特烈，全是中上游球队。面对同档位的瓦勒伦加？H2H数据完全不同。')

add_sep()

# 基础数据
add_para('📊 基础数据对比', bold=True, size=13)
add_table(
    ['对比项', '瓦勒伦加（主）', '汉坎（客）'],
    [
        ['联赛排名', '第7', '第10'],
        ['赛季总成绩', '6胜2平6负（43%）', '5胜3平6负（36%）'],
        ['主/客场成绩', '4胜1平2负（57%）', '0胜3平4负（0%）'],
        ['赛季进球/失球', '22/24（净-2）', '20/26（净-6）'],
        ['主/客场进球/失球', '15/9（净+6）', '7/15（净-8）'],
        ['场均进球', '2.14', '1.00（客场）'],
        ['场均失球', '1.29', '2.14（客场）'],
        ['积分', '20分', '18分'],
        ['核心射手', 'Ravn-Haren 6球(25%)', 'Niang 6球(30%)'],
    ]
)

# 近5场
add_para('📊 近5场状态对比', bold=True, size=13)
add_table(
    ['日期', '瓦勒伦加', '比分', '汉坎'],
    [
        ['7/26', '布兰(客) ✅2-3胜', 'vs', '萨普斯堡(客) ❌0-1负'],
        ['7/17', '奥勒松(主) ✅6-1胜', 'vs', '博德闪耀(客) ❌0-3负'],
        ['7/12', '特罗姆瑟(客) ❌0-4负', 'vs', '特罗姆瑟(主) ❌1-4负'],
        ['5/30', '克里斯蒂(主) ✅3-1胜', 'vs', '奥勒松(客) 🟰2-2平'],
        ['5/25', '斯达(客) ❌0-2负', 'vs', '利勒斯特(主) ✅2-0胜'],
    ]
)

add_signal_box('瓦勒伦加主场3胜2负，攻击爆发力强（6:1大胜），但客场脆弱（0:4惨败）。汉坎三连败，但三场对手全是强队。汉坎唯一胜利是主场2:0利勒斯特。确实够烂的战绩，但烂得有原因。')

add_sep()

# 外媒
add_para('🌍 外媒方向', bold=True, size=13)
add_para('')
add_para('FootballPredictions.com看好瓦勒伦加3-1大胜，BTTS是+大3.5球+Promise Meliga任何时间进球。')
add_para('但说句不好听的，FootballPredictions的3-1预测完全忽略了H2H因素。汉坎在9场交锋中3胜4平2负——这不是一支能被瓦勒伦加轻松拿下的球队。')
add_para('')
add_para('竞彩主胜定价1.49，市场隐含59.4%。后台模型只给了48.6%。差了10.8个百分点。')
add_para('这10.8个百分点就是"排名差溢价"——市场看到第7打第10，自动给主队加了一层光环。但H2H数据说：汉坎不怕你。')

add_sep()

# 信号
add_para('💰 信号', bold=True, size=13)
add_para('')
add_para('后台模型跑完14个维度后，给出了一个非常清晰的结论：让1球方向，客队（汉坎+1球）有巨大价值。')

add_chart('bar_m1.png', width=5.0)

add_table(
    ['指标', '模型', '市场', 'Edge'],
    [
        ['瓦勒伦加胜', '48.6%', '59.4%', '-10.8pp'],
        ['平局', '24.1%', '21.3%', '+2.8pp'],
        ['汉坎胜', '27.2%', '19.2%', '+8.0pp'],
    ]
)

add_chart('pie_m1.png', width=4.0)

add_para('期望总进球：2.86球。大球率54.6%。')
add_para('')
add_signal_box('真正有价值的是让1球客胜——模型49.9%，市场39.3%，Edge+10.6pp。意思是：瓦勒伦加大概率赢球，但赢不了2球以上。汉坎+1球的防线有足够的H2H底气守住。')

add_sep()

# 剧本
add_para('🎬 剧本推演', bold=True, size=13)
add_para('')
add_para('上半场：汉坎三连败后大概率先稳守，前30分钟胶着（0-0或1-0）。瓦勒伦加主场攻势会在30分钟后施压。')
add_para('下半场：60-75分钟是瓦勒伦加体能瓶颈期，也是汉坎反击窗口。如果0-0进入下半场，汉坎可能稳守拿1分。')
add_para('冷门路径：Niang一次反击破门+瓦勒伦加急于进攻暴露后防空档→0:1或1:2客胜。H2H历史支持这一路径。')

add_sep()

# 高概率比分
add_para('📊 高概率比分', bold=True, size=13)
add_table(
    ['维度', '比分', '概率'],
    [
        ['首选', '1-1', '11.3%'],
        ['次选', '2-1', '10.8%'],
        ['留意', '0-1', '8.7%'],
    ]
)

add_sep()

# =============================================
#  场次二：博德闪耀 vs 利勒斯特
# =============================================
add_heading('⚔️ 博德闪耀 vs 利勒斯特 | 03:00 | Aspmyra Stadion', level=1)

add_chart('radar_m2.png', width=4.5)
add_para('')

# 战意
add_para('⚔️ 战意', bold=True, size=13)
add_para('')
add_para('博德闪耀第1，利勒斯特第4。排名第1打第4，差距明显？')
add_para('但你把H2H拉出来看——近10场交锋，博德闪耀7胜1平2负。70%的胜率。')
add_para('博德闪耀主场碾压级数据——7胜0平1负，86%的胜率，进20球仅失2球。')
add_para('但利勒斯特客场也不差——4胜1平2负，57%的胜率，进8球失5球。')
add_para('')
add_signal_box('关键变量：博德闪耀欧冠资格赛8/5客战圣吉联合，5天后就是生死战。教练几乎必然轮换。')

add_sep()

# 基础数据
add_para('📊 基础数据对比', bold=True, size=13)
add_table(
    ['对比项', '博德闪耀（主）', '利勒斯特（客）'],
    [
        ['联赛排名', '第1', '第4'],
        ['赛季总成绩', '11胜2平2负（73%）', '8胜1平5负（57%）'],
        ['主/客场成绩', '6胜0平1负（86%）', '4胜1平2负（57%）'],
        ['赛季进球/失球', '37/11（净+26）', '22/14（净+8）'],
        ['主/客场进球/失球', '20/2（净+18）', '8/5（净+3）'],
        ['场均进球', '2.86', '1.14（客场）'],
        ['场均失球', '0.29', '0.71（客场）'],
        ['积分', '35分', '25分'],
        ['核心射手', 'Høgh 7球(19%)', 'Gulbrandsen 4球(15%)'],
    ]
)

# 近5场
add_para('📊 近5场状态对比', bold=True, size=13)
add_table(
    ['日期', '博德闪耀', '比分', '利勒斯特'],
    [
        ['7/26', '桑纳菲(客) ✅0-3胜', 'vs', '维京(主) ❌1-2负'],
        ['7/23', '汉坎(主) ✅3-0胜', 'vs', '奥斯KFUM(主) ✅2-1胜'],
        ['7/18', '腓特烈(主) ✅1-0胜', 'vs', '腓特烈(客) ✅0-2胜'],
        ['7/12', '奥斯KFUM(客) ✅0-2胜', 'vs', '中日德兰(客) ❌1-0负'],
        ['7/4', '斯达(主·杯赛) ✅4-0胜', 'vs', '汉坎(客) ❌2-0负'],
    ]
)

add_signal_box('博德闪耀近10场9胜1平，状态恐怖级别。但利勒斯特近10场4胜6负——走势不稳定但客场有竞争力（4胜1平2负）。')
add_signal_box('关键变量：博德闪耀欧冠资格赛8/5客战圣吉联合，5天后就是生死战。教练几乎必然轮换。')

add_sep()

# 外媒
add_para('🌍 外媒方向', bold=True, size=13)
add_para('')
add_para('FootballPredictions.com看好博德闪耀3-1大胜，BTTS是+大3.5球+Helmersen任何时间进球。')
add_para('H2H数据（20场）：博德闪耀45%胜、25%平、利勒斯特30%胜。85%的比赛进球≥2。')
add_para('')
add_para('但说白了，FootballPredictions的3-1预测建立在博德闪耀全主力出战的假设上。5天后就是欧冠生死战——这个变量被所有外媒忽略了。')
add_para('博德闪耀的赛季战略重心已经转向欧冠。挪威杯8/22还有一轮，联赛19轮还有14场——博德闪耀的联赛冠军几乎锁定（领先10分）。教练完全有理由在这场"可以输但不能伤人"的比赛中轮换主力。')

add_sep()

# 信号
add_para('💰 信号', bold=True, size=13)
add_para('')
add_signal_box('后台模型给出的结论非常清晰：主胜严重过热。')

add_chart('bar_m2.png', width=5.0)

add_table(
    ['指标', '模型', '市场', 'Edge'],
    [
        ['博德闪耀胜', '65.7%', '75.7%', '-10.0pp'],
        ['平局', '19.6%', '14.5%', '+5.1pp'],
        ['利勒斯特胜', '14.8%', '9.8%', '+5.0pp'],
    ]
)

add_chart('pie_m2.png', width=4.0)

add_para('期望总进球：3.03球。大球率58.4%。')
add_para('')
add_signal_box('让2球客胜：模型54.6%，市场42.8%，Edge+11.8pp。这是今晚两场比赛中最强的单一信号。意思是：博德闪耀大概率赢球，但赢3球以上的概率不超过40%。利勒斯特客场防守（场均失0.71球）有能力将分差控制在2球以内。')

add_sep()

# H2H
add_para('📊 H2H历史（FootballPredictions 20场）', bold=True, size=13)
add_table(
    ['维度', '数据'],
    [
        ['博德闪耀胜率', '45%（9场）'],
        ['平局率', '25%（5场）'],
        ['利勒斯特胜率', '30%（6场）'],
        ['进球≥2场次', '85%'],
        ['BTTS场次', '55%'],
        ['博德零封场次', '25%'],
    ]
)

add_sep()

# 剧本
add_para('🎬 剧本推演', bold=True, size=13)
add_para('')
add_para('上半场：博德闪耀主场强势开局，前15分钟抢攻。若轮换阵容则前30分钟节奏放缓。利勒斯特摆大巴争取上半场不失球。')
add_para('下半场：60分钟后博德闪耀替补深度优势显现。若未进球则急躁，可能暴露后防空档→利勒斯特反击机会。')
add_para('冷门路径：博德闪耀大幅轮换+欧冠分心→进攻效率下降→利勒斯特稳守反击1球制胜。类似案例：博德闪耀上赛季欧战前联赛曾0:1负于中游球队。')

add_sep()

# 高概率比分
add_para('📊 高概率比分', bold=True, size=13)
add_table(
    ['维度', '比分', '概率'],
    [
        ['首选', '2-0', '11.0%'],
        ['次选', '1-0', '10.2%'],
        ['留意', '2-1', '9.9%'],
    ]
)

add_sep()

# =============================================
#  两场总览
# =============================================
add_heading('📊 两场总览', level=1)

add_chart('line_goals.png', width=5.5)
add_para('')

add_chart('bar_edge.png', width=5.5)
add_para('')

add_table(
    ['场次', '对阵', '模型倾向', '最强信号', '高概率比分'],
    [
        ['①', '瓦勒伦加VS汉坎', '主胜被高估', '让1球客胜 +10.6pp', '1-1 / 2-1 / 0-1'],
        ['②', '博德闪耀VS利勒斯特', '主胜过热', '让2球客胜 +11.8pp', '2-0 / 1-0 / 2-1'],
    ]
)

add_sep()

# =============================================
#  结尾（轮换钩子 + 硬立场）
# =============================================
add_para('两场挪超，两个被市场高估的主胜。瓦勒伦加被H2H克星压制，博德闪耀被欧冠轮换拖累。', bold=True, size=10.5)
add_para('')
add_para('今晚的剧本：两场都是主队赢球但赢不了大胜。让球方向的客队才是真正的价值洼地。', size=10.5)
add_para('')

# 轮换钩子：主打数据与实战的碰撞（适合模型偏差大的场次）
add_para('后台模型跑出了10.8pp和10.0pp的偏差，但概率只是概率。汉坎今晚能打破三连败吗？博德闪耀会不会因为欧冠轮换翻车？把你的预测比分打在评论区，赛后我们回来复盘。', bold=True, size=10.5, color=RGBColor(0x2E, 0x86, 0xC1))

add_sep()

# =============================================
#  数据来源（标准模板）
# =============================================
add_para('【数据来源】', bold=True, size=9, color=RGBColor(0x66, 0x66, 0x66))
add_para('基础赛事数据取自竞彩官方及海外主流体育数据库。进球期望值（xG）、六维能力雷达图及市场偏差测算，均由阿飞个人足球数据模型独立推演生成。', size=8.5, color=RGBColor(0x99, 0x99, 0x99))

add_para('')

# =============================================
#  免责声明（标准模板）
# =============================================
add_para('【免责声明】', bold=True, size=9, color=RGBColor(0x66, 0x66, 0x66))
add_para('本文内容仅代表作者个人的数据模型推演结果，属于体育赛事分析交流范畴，不构成任何指向性的购彩及投注建议。足球是圆的，概率不等于绝对。请各位球迷严格遵守国家法律法规，理性看待数据，适度娱乐。', size=8.5, color=RGBColor(0x99, 0x99, 0x99))

# 保存
doc.save(OUTPUT_PATH)
print(f'DOCX saved: {OUTPUT_PATH}')
print(f'File size: {os.path.getsize(OUTPUT_PATH):,} bytes')
