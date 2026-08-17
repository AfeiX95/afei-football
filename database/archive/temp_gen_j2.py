# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BASE = r"I:\阿飞说球\📝文章\20260807"
CHARTS = os.path.join(BASE, "charts", "mp")
OUTPUT = os.path.join(BASE, "日职揭幕两场赛事前瞻.docx")

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Microsoft YaHei"
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
style.paragraph_format.space_after = Pt(4)
style.paragraph_format.line_spacing = 1.25
for s in doc.sections:
    s.top_margin = Cm(1.8); s.bottom_margin = Cm(1.8)
    s.left_margin = Cm(2.2); s.right_margin = Cm(2.2)

def heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    return h

def para(text, bold=False, size=10.5, color=None, align=None, italic=False):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Microsoft YaHei"; r.font.size = Pt(size)
    r.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    if bold: r.bold = True
    if italic: r.italic = True
    if color: r.font.color.rgb = color
    if align: p.alignment = align
    return p

def add_image(path, width=Inches(5.5)):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(); r.add_picture(path, width=width)

def caption(text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); r.font.size = Pt(8); r.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

def tbl(headers, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(headers))
    t.style = "Light Grid Accent 1"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = h
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs: r.bold = True; r.font.size = Pt(9)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = t.rows[ri+1].cells[ci]; cell.text = str(val)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs: r.font.size = Pt(9)

def divider():
    p = doc.add_paragraph(); r = p.add_run("-" * 50)
    r.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC); r.font.size = Pt(8)

def img(name, cap):
    add_image(os.path.join(CHARTS, name), width=Inches(5.5))
    caption(cap)

# ============ 封面 ============
h = heading("日职揭幕两场：交锋数据都在唱反调", level=0)
h.alignment = WD_ALIGN_PARAGRAPH.CENTER
para("阿飞·赛博聊球 ｜ 日职联 2026 揭幕战 ｜ 周五傍晚", size=9, color=RGBColor(0x88,0x88,0x88), align=WD_ALIGN_PARAGRAPH.CENTER)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("#日职联 #横滨水手 #鹿岛鹿角 #大阪钢巴 #浦和红钻 #足球前瞻 #数据分析 #赛博聊球 #足球分析")
r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x1A,0x5C,0x9E)
para("数据不会说谎，但人会。- 阿飞·赛博聊球", size=11, italic=True, color=RGBColor(0x33,0x33,0x33), align=WD_ALIGN_PARAGRAPH.CENTER)
divider()

# ============ 开场 + 核心结论 ============
para("日职新赛季揭幕，两场比赛，四种说法。")
para("第一场，横滨水手主场打鹿岛鹿角，市场把鹿岛定成客队热门，可鹿岛最近三个联赛客场一场没赢，还被打出过0-5，两个主力伤停。")
para("第二场，大阪钢巴主场碰浦和红钻，钢巴排名第4、浦和排第17，看着是主队欺负人，翻开历史却全是反的：浦和客场对钢巴近10场赢了7场，近5次联赛交手3次零封。")
para("两场都是同一个剧本：数据在打架，市场只信了一半。")
heading("核心结论", level=2)
para("横滨水手对鹿岛鹿角：后台模型主胜37.4%、平局30.0%、客胜32.6%；市场把客胜定价到50.6%，被高估约18个百分点。鹿岛客场近况差、主力伤停，平局和横滨受让是价值点。", bold=True)
para("大阪钢巴对浦和红钻：基础模型主胜43.5%、平局28.2%、客胜28.4%；但钢巴主场对浦和近10场只有1胜2平7负，4天后还要踢亚冠附加赛。综合修正后：浦和客胜35%、平局33%、钢巴32%。", bold=True)
para("两场共同点就一句：别只看排名，先看交锋和赛程。")
divider()

# ============ 第一场 ============
heading("第一场｜横滨水手 vs 鹿岛鹿角（18:25）", level=1)
tbl(["对阵", "横滨水手（主）vs 鹿岛鹿角"], [["联赛", "日职联 2026 第1轮"], ["场地", "日产体育场 30°C 间中有云"], ["伤停", "横滨：7号前锋远野大弥（伤病）｜ 鹿岛：2号后卫安西幸辉（伤病）、14号中场樋口雄太（腓骨骨折）"]])

heading("战意", level=2)
para("揭幕战，双方都要开门红。横滨主场作战，想先声夺人；鹿岛作为上季第3，客场求稳为先，别把揭幕战踢成追分战。")

heading("信号", level=2)
para("鹿岛最近三个联赛客场不胜，中间夹着一场0-5惨败给神户；客场近10场胜率只有40%，且进球场均刚过1个。横滨主场对鹿岛近5场4胜1平，主场交锋盘面是压着鹿岛打。鹿岛这边还缺了主力后卫安西幸辉和中场樋口雄太，防线要临时拼凑。")

heading("数据平台赛前信号", level=2)
para("主流数据平台给鹿岛的客场进攻画了问号：客场场均进球1.0、近3客不胜，跟1.75的客队定价对不上。横滨虽然也缺主力前锋远野大弥，但主场进攻体系完整，破门点不止一个。")

img("m1_radar.png", "图1｜六维战力对比：横滨交锋占优，鹿岛客场疲软")
img("m1_bar.png", "图2｜胜平负概率：模型 vs 市场定价（鹿岛客胜被高估18pp）")
img("m1_pie.png", "图3｜修正后概率：平局第一")

heading("模型与市场", level=2)
tbl(["方向", "后台模型", "市场定价", "偏差"], [
    ["横滨胜", "37.4%", "22.7%（3.90）", "+14.7pp"],
    ["平局", "30.0%", "26.7%（3.32）", "+3.3pp"],
    ["鹿岛胜", "32.6%", "50.6%（1.75）", "-18.0pp"],
])
para("λ估算1.38对1.33，模型判定五五开；期望总进球2.71，大2.5概率51%。首选中低比分。")

heading("推荐", level=2)
para("方向：平局第一（修正后约35%），横滨主场不败概率约67%，不追鹿岛客胜。", bold=True)
para("比分：首选1-1，次选1-0，留意0-1。")
para("让球：鹿岛客让半球附近，看好横滨受让不败。")
para("大小：2-3球区间，大2.5谨慎偏小，30°C高温揭幕战节奏慢，双方近期小球占比高。")
img("m1_signals.png", "图4｜信号图：鹿岛客场成色不足")
divider()

# ============ 第二场 ============
heading("第二场｜大阪钢巴 vs 浦和红钻（18:30）", level=1)
tbl(["对阵", "大阪钢巴（主）vs 浦和红钻"], [["联赛", "日职联 2026 第1轮"], ["赛程", "钢巴8-11踢亚冠精英附加赛（对江原FC），4天后"], ["伤停", "暂无官方数据"]])

heading("战意", level=2)
para("钢巴4天后要踢亚冠精英附加赛，揭幕战大概率收着踢、保人不保分；浦和赛程宽松，下一场要等一周，这场是全力抢分的最佳窗口。战意差一截。")

heading("信号", level=2)
para("最硬的信号在交锋：钢巴主场对浦和近10场只有1胜2平7负，浦和是钢巴的克星，近5次联赛交手3次零封钢巴。浦和防守是看家本领，近10场场均失球0.7，近期6场5场不败。钢巴进攻火（近10场场均2.1球、进21球），但专打浦和打不动。")

heading("数据平台赛前信号", level=2)
para("数据平台给浦和的防守评分明显高于钢巴，且浦和客场近10场4胜2平4负，遇到强队反击效率不差。钢巴近10场5胜2平3负，赢球的对手多是中下游，含金量要打个折。")

img("m2_radar.png", "图5｜六维战力对比：浦和防守+交锋双压制")
img("m2_bar.png", "图6｜胜平负概率：基础模型 vs 综合修正（H2H+分心）")
img("m2_pie.png", "图7｜修正后概率：浦和略占优")

heading("模型与修正", level=2)
tbl(["方向", "基础模型", "综合修正", "说明"], [
    ["钢巴胜", "43.5%", "32%", "交锋1胜7负+亚冠分心，下调11pp"],
    ["平局", "28.2%", "33%", "日职揭幕战平局概率上浮"],
    ["浦和胜", "28.4%", "35%", "客场克星+防守顶级，上调7pp"],
])
para("基础模型λ估算1.70对1.19，账面钢巴占优；但交锋数据和赛程分心把优势抹平了。")

heading("推荐", level=2)
para("方向：浦和客胜+平局双选，钢巴主场赢球难度大。", bold=True)
para("比分：首选1-1，次选0-1，留意1-0。")
para("让球：钢巴账面强但交锋虚，让球方向站不住，看好浦和受让。")
para("大小：交锋近5场4场≤2球，小球为主，2球区间；大2.5谨慎。")
img("m2_signals.png", "图8｜信号图：交锋克星+赛程分心")
divider()

# ============ 结尾 ============
heading("互动", level=2)
para("你看好哪边？评论区聊聊，这两场要是都被我说中了，记得回来点个赞。")
para("首发评论：两场都站平局的人，这场可能笑得最开心。", italic=True)

heading("配图关键词", level=2)
para("日职联揭幕 横滨水手 鹿岛鹿角 比赛图｜J.League opening Yokohama F. Marinos Kashima Antlers match photos", size=9, color=RGBColor(0x66,0x66,0x66))
para("大阪钢巴 浦和红钻 日职联 比赛图｜Gamba Osaka Urawa Reds J.League match photos", size=9, color=RGBColor(0x66,0x66,0x66))

heading("免责声明", level=2)
para("行文仓促，图片和数据来自官方平台和权威媒体，侵删。", size=9, color=RGBColor(0x88,0x88,0x88))
para("都是我个人图一乐的瞎琢磨，千万别当真，理智看球、远离赌博才是正道。", size=9, color=RGBColor(0x88,0x88,0x88))
para("数据来源：中国体育彩票官方平台 + 新球体育", size=8, color=RGBColor(0xAA,0xAA,0xAA))

doc.save(OUTPUT)
print("saved:", OUTPUT)
