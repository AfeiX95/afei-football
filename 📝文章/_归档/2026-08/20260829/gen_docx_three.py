# -*- coding: utf-8 -*-
"""生成: 三场豪门热度扫描_巴黎米兰曼城_头条版.docx (R19 白底图规范)"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

BASE = r"I:\阿飞说球\_tmp_docx_out"
CHART_DIR = os.path.join(BASE, "charts")
os.makedirs(CHART_DIR, exist_ok=True)

# ===== R19 配色 =====
C_MAIN = "4fc3f7"   # 主队蓝
C_DRAW = "ffd93d"   # 平局黄
C_AWAY = "ff6b6b"   # 客队红
C_DARK = "1a237e"   # 标题深蓝
C_GRAY = "9e9e9e"
C_LIGHT = "f5f5f5"

def set_cn_font(run, size=10.5, bold=False, color=None, name="微软雅黑"):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)

def shade_cell(cell, hexcolor):
    cell._tc.get_or_add_tcPr().append(parse_xml(r'<w:shd {} w:val="clear" w:fill="{}"/>'.format(nsdecls("w"), hexcolor)))

def para(doc, text, size=10.5, bold=False, color=None, align=None, space_after=6, indent=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    if indent:
        p.paragraph_format.first_line_indent = Pt(indent)
    r = p.add_run(text)
    set_cn_font(r, size=size, bold=bold, color=color)
    return p

def heading(doc, text, size=15, color=C_DARK, space_before=10):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(text)
    set_cn_font(r, size=size, bold=True, color=color)
    return p

def bar_chart(title, market, model, fname, ymax=80):
    """市场 vs 模型 胜平负柱状图, 白底 R19 配色"""
    cats = ["主胜", "平局", "客胜"]
    x = [0, 1, 2]
    w = 0.36
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    colors = ["#" + c for c in (C_MAIN, C_DRAW, C_AWAY)]
    b1 = ax.bar([i - w / 2 for i in x], market, width=w, color=colors, label="市场定价", edgecolor="white")
    b2 = ax.bar([i + w / 2 for i in x], model, width=w, color="#37474f", alpha=0.78, label="后台模型", edgecolor="white")
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.0f}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=10)
    ax.set_ylim(0, ymax)
    ax.set_ylabel("概率 (%)", fontsize=9)
    ax.set_title(title, fontsize=11, color="#1a237e", pad=8)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(fname, facecolor="white", bbox_inches="tight")
    plt.close(fig)

# ===== 图表 =====
ch1 = os.path.join(CHART_DIR, "bar_m1.png")
ch2 = os.path.join(CHART_DIR, "bar_m2.png")
ch3 = os.path.join(CHART_DIR, "bar_m3.png")
bar_chart("里尔 vs 巴黎圣日耳曼 · 胜平负概率", [20, 23, 57], [41, 31, 27], ch1)
bar_chart("AC米兰 vs 威尼斯 · 胜平负概率（模型失真降权，仅供参考）", [68, 20, 12], [32, 30, 38], ch2)
bar_chart("水晶宫 vs 曼城 · 胜平负概率", [18, 22, 60], [19, 22, 59], ch3)

# ===== 文档 =====
doc = Document()
# 页面 A4
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin = sec.bottom_margin = Cm(2.0)

# 默认字体
style = doc.styles["Normal"]
style.font.name = "微软雅黑"
style.element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
style.font.size = Pt(10.5)

# 标题
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("三场豪门热度扫描：巴黎米兰曼城集体慢热，价值全在受让侧")
set_cn_font(r, size=17, bold=True, color=C_DARK)
p.paragraph_format.space_after = Pt(4)

para(doc, "#里尔VS巴黎圣日耳曼  #AC米兰VS威尼斯  #水晶宫VS曼城  #法甲  #意甲  #英超  #足球前瞻  #数据分析",
     size=9, color=C_GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
para(doc, "数据不会说谎，但人会。——阿飞·赛博聊球", size=9.5, color=C_GRAY,
     align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

# 核心结论
heading(doc, "核心结论（前置）", size=13)
para(doc, "很多人看到巴黎、米兰、曼城三支豪门，以为这是三场手拿把攥的收割局。但后台模型跑完，三场里没有一场是\u201c名字即答案\u201d：巴黎 57% 的客胜定价，模型只给 27%（里尔 41% 反而是第一）；米兰 68% 的主胜定价，模型只给 32%（升班马样本失真，模型降权，但 68% 也确实全靠 H2H 四连零封撑着）；曼城 59.8% 的客胜定价，模型给 59%，唯一吻合的一场。三场的价值点分三种：里尔这场在受让一球（模型 72.6% 不败 vs 市场 42.4%，本批最强信号）；米兰这场在净胜两球的价格水分（市场 44% vs 模型 13%）；曼城这场没有认知差，只有大球共识（58% vs 60%）。说白了，豪门的价格里，一半是名字，一半才是状态。", size=10.5)

# ===== 第一场 =====
heading(doc, "第一场：里尔 vs 巴黎圣日耳曼 — 卫冕冠军慢热，市场还在为名字付费")
para(doc, "很多人以为欧冠卫冕冠军打里尔是降维打击。但法超杯刚 0:1 输朗斯、近 5 场 1 胜 2 平 2 负、联赛首轮半场 0:2 落后才追平雷恩的巴黎，拿什么降维？", size=10.5)
para(doc, "⚔️ 战意：里尔主场首秀冲联赛两连胜（首轮客 2:0 零封昂热，吉鲁 1 球 1 助）；巴黎卫冕冠军开季不能连败（法超杯已丢，联赛再丢就是三线崩）。里尔近 10 次交锋 0 胜 2 平 8 负，心理劣势实打实，但那是\u201c名字\u201d层面的劣势，状态层面完全倒挂。", size=10.5)
doc.add_picture(ch1, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl = doc.add_table(rows=4, cols=4)
tbl.style = "Table Grid"; tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
hdr = ["结果", "市场定价", "后台模型", "偏差"]
rows_data = [
    ("里尔胜", "20%", "41%", "+21pp", C_MAIN),
    ("平局", "23%", "31%", "+8pp", C_DRAW),
    ("巴黎胜", "57%", "27%", "-30pp", C_AWAY),
]
for j, h in enumerate(hdr):
    c = tbl.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
for i, (a, b, c_, d, tint) in enumerate(rows_data, start=1):
    vals = [a, b, c_, d]
    for j, v in enumerate(vals):
        cell = tbl.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "💰 信号：市场的 57% 押的是巴黎的名字 + 近 10 次交锋 8 胜的统治史；模型的 27% 押的是状态：巴黎近 10 场进 11 失 12，进攻全靠替补托雷斯的双响（首轮落后时上场救主），后卫门德斯还停赛。真正干净的不是方向，是受让一球：模型给里尔 72.6% 不败，市场只给 42.4%；巴黎想净胜两球，模型只给 9.6%，市场却给了 32.6%，这个差价是结构性的。进球数分歧同样尖锐：模型 34% vs 市场六成大球，交锋历史场均 4.4 球，但两队当前场均合计才 2.7 球。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：法甲媒体传统叙事\u201c巴黎客战里尔 10 次赢 8 次\u201d，但开季两队状态完全倒挂，本场是典型的\u201c历史碾压 vs 当下现实\u201d。", size=10.5)
para(doc, "高概率比分：首选 1-0，次选 1-1，留意 0-1。", size=10.5, bold=True, color=C_DARK)

# ===== 第二场 =====
heading(doc, "第二场：AC米兰 vs 威尼斯 — 68% 的价格，一半是 H2H 碾压史")
para(doc, "很多人看到米兰 68% 的主胜定价，以为稳了。但拆开近 10 场：3 胜 3 平 4 负、上季末联赛 1 胜 1 平 3 负、首轮半场 0:0 靠替补拉比奥才 2:1 拿下都灵。这支米兰的稳，是 H2H 给的，不是状态给的。", size=10.5)
para(doc, "⚔️ 战意：米兰下周客尤文、再下周客拉齐奥，本场存在留力动机；威尼斯升班马客场目标就是别崩+争取首分，意大利杯半场 1:2 落后 3:2 逆转摩德纳，说明有韧劲不是鱼腩。", size=10.5)
doc.add_picture(ch2, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl2 = doc.add_table(rows=4, cols=4)
tbl2.style = "Table Grid"; tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, h in enumerate(hdr):
    c = tbl2.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows2 = [
    ("米兰胜", "68%", "32%*", "模型失真", C_MAIN),
    ("平局", "20%", "30%", "+10pp", C_DRAW),
    ("威尼斯胜", "12%", "38%*", "模型失真", C_AWAY),
]
for i, (a, b, c_, d, tint) in enumerate(rows2, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl2.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "*威尼斯近 10 场 29 个进球里，七成来自意乙和热身（对意丙 8:0），模型对升班马的状态样本失真，已整体降权不作方向主张。但反向看：米兰 68% 的定价，也全靠 H2H 近 4 次对威尼斯 4 连零封（4:0/2:0/3:0/2:0）撑着：上季末那个 1 胜 1 平 3 负的米兰，凭什么值 68%？", size=8.5, color=C_GRAY)
para(doc, "💰 信号：68% 的价里，水分最大的是净胜两球那 44%：要么 H2H 惯性兑现（打威尼斯从不小胜），要么 1:0/2:1 走盘收场，走盘概率 25.7% 是结构性的，追满净胜两球的风险就在这里。进球数市场给 56% 偏大，H2H 场均 2.75-4 球支持大球侧。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：强弱分明叙事 vs 两队首轮半场双双 0:0 哑火（米兰对都灵、威尼斯对莱切都是半场交白卷），慢热对慢热。", size=10.5)
para(doc, "高概率比分：首选 2-0，次选 1-0，留意 2:1。", size=10.5, bold=True, color=C_DARK)

# ===== 第三场 =====
heading(doc, "第三场：水晶宫 vs 曼城 — 没有认知差的一场，大球是主线")
para(doc, "很多人被曼城社区盾 0:3 惨败阿森纳吓到，以为曼城崩了。但首轮已 2:1 逆转伯恩茅斯止血，而这场比赛，后台模型和市场罕见地完全一致。", size=10.5)
para(doc, "⚔️ 战意：水晶宫主场首秀（首轮客负埃弗顿 0:2 急需反弹），2025 年足总杯 1:0 掀翻过曼城，杯赛冠军属性是真有心理底气的；曼城卫冕之路一场都不能丢，而且下周就是客曼联的德比战。", size=10.5)
doc.add_picture(ch3, width=Inches(5.9))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

tbl3 = doc.add_table(rows=4, cols=4)
tbl3.style = "Table Grid"; tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, h in enumerate(hdr):
    c = tbl3.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
rows3 = [
    ("水晶宫胜", "18%", "19%", "+0.6pp", C_MAIN),
    ("平局", "22%", "22%", "+0.2pp", C_DRAW),
    ("曼城胜", "60%", "59%", "-0.8pp", C_AWAY),
]
for i, (a, b, c_, d, tint) in enumerate(rows3, start=1):
    for j, v in enumerate([a, b, c_, d]):
        cell = tbl3.rows[i].cells[j]; cell.text = ""
        r = cell.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if j < 3:
            shade_cell(cell, tint)
para(doc, "", size=4, space_after=2)
para(doc, "💰 信号：这场没有认知差：方向、受让、比分三个维度全在 2 个百分点以内，市场已经把这场的价格定得很死。但共识本身也是信号：大球是三方一致的（交锋场均 3.5 球、7/10 场次 ≥3 球；曼城首轮 2:1 的两个进球全来自后卫格瓦迪奥尔和格伊，无锋打法后插上频繁；水晶宫主场 6 胜 3 平 1 负进攻活跃）。净胜两球 35.5% 对直胜 59.8% 的裂口还在，但市场已定价，没有便宜可占。", size=10.5)
para(doc, "🌍 外部视角：综合数据倾向：技术压制 vs 身体对抗的经典剧本，水晶宫杯赛冠军属性是本场最大心理变量。", size=10.5)
para(doc, "高概率比分：首选 1-2，次选 1-1，留意 0-2。", size=10.5, bold=True, color=C_DARK)

# ===== 最终判断 =====
heading(doc, "最终判断：三场矩阵")
mt = doc.add_table(rows=4, cols=4)
mt.style = "Table Grid"; mt.alignment = WD_TABLE_ALIGNMENT.CENTER
mhdr = ["场次", "后台模型", "高概率比分", "核心信号"]
for j, h in enumerate(mhdr):
    c = mt.rows[0].cells[j]; c.text = ""
    r = c.paragraphs[0].add_run(h); set_cn_font(r, size=9.5, bold=True, color="ffffff")
    shade_cell(c, C_DARK)
mrows = [
    ("里尔 vs 巴黎", "主41% / 平31% / 客27%", "1-0 / 1-1 / 0-1", "里尔+1 不败 72.6% vs 42.4%（本批最强受让信号）"),
    ("米兰 vs 威尼斯", "市场骨架 68%", "2-0 / 1-0 / 2-1", "净胜2球 44% 水分大，走盘 25.7% 结构风险"),
    ("水晶宫 vs 曼城", "客 59% vs 59.8%", "1-2 / 1-1 / 0-2", "大球共识 58% vs 60%"),
]
for i, row in enumerate(mrows, start=1):
    for j, v in enumerate(row):
        c = mt.rows[i].cells[j]; c.text = ""
        r = c.paragraphs[0].add_run(v); set_cn_font(r, size=9.5, bold=(j == 3))
        if i % 2 == 0:
            shade_cell(c, C_LIGHT)
para(doc, "", size=4, space_after=2)
para(doc, "三场共同规律：巴黎、米兰、曼城开季集体慢热：巴黎近 5 场 1 胜 2 平 2 负、米兰上季末 1 胜 1 平 3 负、曼城社区盾 0:3 惨败。市场还在为\u201c名字\u201d定价，状态全在打折扣。难说哪场会翻。但受让与门槛的差价是结构性的，这就是本批三个最有用的数字：72.6%、25.7%、58%。", size=10.5, bold=True)

# ===== 互动/来源/免责 =====
heading(doc, "互动钩子", size=12)
para(doc, "三场豪门场拆完了。巴黎 57% 的客胜定价你信吗？米兰 68% 的主胜定价，净胜两球那 44% 里有多少水分？曼城这场你选大球还是小球？评论区留下你的预测比分，赛后我们用实战赛果复盘模型精度。", size=10.5)

para(doc, "数据来源：基础赛事数据取自竞彩官方及竞彩网特征分析页。进球期望值、市场偏差测算均由阿飞个人足球数据模型独立推演生成。", size=8.5, color=C_GRAY)
para(doc, "免责声明：行文仓促，里面的图片和数据都是从官方渠道和权威媒体上整过来的，侵删。这都是我个人图一乐的瞎琢磨，千万别当真，理智看球、购买合法体育彩票才是正道。", size=8.5, color=C_GRAY)

out = os.path.join(BASE, "三场豪门热度扫描_巴黎米兰曼城_头条版.docx")
doc.save(out)
print("SAVED:", out)
