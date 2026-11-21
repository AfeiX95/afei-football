# -*- coding: utf-8 -*-
"""足球比赛预测共识分析框架（空模板）生成脚本。
所有数值均为占位/规则参数，不含任何真实比赛、赔率或预测数据。
"""
try:
    import openpyxl
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "openpyxl>=3.1.0"])
    import openpyxl

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils import get_column_letter, column_index_from_string

OUT = r"I:\阿飞说球\📝文章\20261121\足球预测共识分析框架.xlsx"
TITLE = "足球预测共识分析框架"


def xl_color(css_hex: str) -> str:
    value = css_hex.removeprefix("#").upper()
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB, got: {css_hex}")
    return "FF" + value


XL_PRIMARY = xl_color("#4472C4")
XL_PRIMARY_DARK = xl_color("#2F5597")
XL_INPUT = xl_color("#D9E2F3")
XL_CALC = xl_color("#F2F2F2")
XL_WHITE = xl_color("#FFFFFF")
XL_TEXT = xl_color("#1A1A1A")
XL_BORDER = xl_color("#BFBFBF")
XL_GREEN_BG = xl_color("#C6EFCE")
XL_GREEN_TX = xl_color("#006100")
XL_RED_BG = xl_color("#FFC7CE")
XL_RED_TX = xl_color("#9C0006")
XL_YELLOW_BG = xl_color("#FFEB9C")
XL_YELLOW_TX = xl_color("#9C6500")

thin = Side(style="thin", color=XL_BORDER)
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
F_TITLE = Font(name="微软雅黑", size=14, bold=True, color=XL_WHITE)
F_SUB = Font(name="微软雅黑", size=9, color=XL_TEXT)
F_HEAD = Font(name="微软雅黑", size=10, bold=True, color=XL_WHITE)
F_BODY = Font(name="微软雅黑", size=10, color=XL_TEXT)
F_BOLD = Font(name="微软雅黑", size=10, bold=True, color=XL_TEXT)
FILL_HEAD = PatternFill("solid", fgColor=XL_PRIMARY)
FILL_GROUP = PatternFill("solid", fgColor=XL_PRIMARY_DARK)
FILL_INPUT = PatternFill("solid", fgColor=XL_INPUT)
FILL_CALC = PatternFill("solid", fgColor=XL_CALC)
FILL_GREEN = PatternFill("solid", fgColor=XL_GREEN_BG)
FILL_RED = PatternFill("solid", fgColor=XL_RED_BG)
FILL_YELLOW = PatternFill("solid", fgColor=XL_YELLOW_BG)
FONT_GREEN = Font(name="微软雅黑", size=10, color=XL_GREEN_TX)
FONT_RED = Font(name="微软雅黑", size=10, color=XL_RED_TX)
FONT_YELLOW = Font(name="微软雅黑", size=10, color=XL_YELLOW_TX)

PCT = "0.00%"
ODDS = "0.00"
NUM2 = "0.00"
INT = "0"

# ---- 锚点 ----
ROW_TITLE, ROW_GROUP, ROW_HEAD, ROW_START = 1, 2, 3, 4
N_MATCH = 5
ROW_END = ROW_START + N_MATCH - 1              # 8
SOURCES = [
    ("Google 数据模型", "模型层", 0.15, "赛前机器学习/统计模型输出，优先取 1X2 概率"),
    ("Forebet", "模型层", 0.10, "数学算法预测，常见为概率或最可能比分"),
    ("Wincomparator", "模型层", 0.10, "算法胜平负概率，注意取赛前最新版本"),
    ("BetBuilders AI（xG）", "模型层", 0.15, "xG 模拟输出，质量较高但需确认含伤停修正"),
    ("Polymarket", "预测市场", 0.15, "是/否合约价格，须换算并登记合约标的"),
    ("Kalshi", "预测市场", 0.10, "是/否合约价格，须换算并登记合约标的"),
    ("Goal", "媒体", 0.07, "文字预测，按倾向量化规则赋分"),
    ("FootballWhispers", "媒体", 0.06, "文字预测，按倾向量化规则赋分"),
    ("SportsGambler", "媒体", 0.06, "文字预测/比分倾向，按规则赋分"),
    ("Futbol24", "媒体", 0.06, "文字预测，按倾向量化规则赋分"),
]
N_SRC = len(SOURCES)
PRED_END = ROW_START + N_MATCH * N_SRC - 1      # 53

S_LIST = "'01_比赛清单'"
S_ODDS = "'02_外盘欧赔'"
S_PRED = "'03_来源预测'"
S_PARAM = "'04_权重参数'"
S_SUM = "'05_共识汇总'"
PRED_A = f"{S_PRED}!$A${ROW_START}:$A${PRED_END}"


def pcol(col):
    return f"{S_PRED}!${col}${ROW_START}:${col}${PRED_END}"


def banner(ws, last_col, title, subtitle):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    c = ws.cell(1, 1, title)
    c.font = F_TITLE
    c.fill = FILL_GROUP
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 28
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_col)
    c = ws.cell(2, 1, subtitle)
    c.font = F_SUB
    c.fill = FILL_CALC
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1, wrap_text=True)
    ws.row_dimensions[2].height = 30


def header(ws, row, names, start_col=1):
    for i, name in enumerate(names):
        c = ws.cell(row, start_col + i, name)
        c.font = F_HEAD
        c.fill = FILL_HEAD
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER
    ws.row_dimensions[row].height = 30


def body(cell, kind="input", fmt=None, wrap=False):
    cell.font = F_BODY
    cell.border = BORDER
    cell.alignment = Alignment(
        horizontal="left" if wrap else "center",
        vertical="center", wrap_text=wrap,
    )
    cell.fill = FILL_INPUT if kind == "input" else FILL_CALC
    if fmt:
        cell.number_format = fmt


def widths(ws, mapping):
    for col, w in mapping.items():
        ws.column_dimensions[col].width = w


wb = Workbook()
wb.remove(wb.active)
wb.properties.title = TITLE
wb.properties.subject = "外盘欧赔与多来源预测共识分析框架（空模板）"
wb.properties.description = "不含任何真实比赛、赔率或预测数据；仅含结构、公式与判定规则。"

# ============================================================
# 00_使用说明
# ============================================================
ws = wb.create_sheet("00_使用说明")
banner(ws, 8, "足球比赛预测共识分析框架 · 使用说明",
       "版本 v1.0 ｜ 生成日期 2026-11-20 ｜ 本工作簿为空模板，不含任何真实比赛、赔率或预测数据；所有黄色以外的空白输入格等待填写。")
widths(ws, {"A": 24, "B": 16, "C": 44, "D": 12, "E": 12, "F": 12, "G": 12, "H": 12})


def note_row(r, label, text, label_fill=None):
    ws.cell(r, 1, label).font = F_BOLD
    ws.cell(r, 1).fill = label_fill or FILL_CALC
    ws.cell(r, 1).border = BORDER
    ws.cell(r, 1).alignment = Alignment(vertical="center", wrap_text=True)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    c = ws.cell(r, 2, text)
    c.font = F_BODY
    c.alignment = Alignment(vertical="center", wrap_text=True)
    c.border = BORDER
    ws.row_dimensions[r].height = 30


def section(r, text):
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
    c = ws.cell(r, 1, text)
    c.font = F_HEAD
    c.fill = FILL_HEAD
    c.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[r].height = 22


section(4, "① 状态看板（自动统计）")
kpis = [
    (5, "已填比赛数", f"=COUNTA({S_LIST}!D{ROW_START}:D{ROW_END})", "在比赛清单填写主队即计入"),
    (6, "已录欧赔场次", f"=COUNT({S_ODDS}!M{ROW_START}:M{ROW_END})", "至少填 1 家公司的 1X2 赔率"),
    (7, "已录来源组数", f"=COUNTIF({S_PRED}!K{ROW_START}:K{PRED_END},1)", "三项概率齐全且归一化成功的来源行数"),
    (8, "高共识场次", f'=COUNTIF({S_SUM}!R{ROW_START}:R{ROW_END},"高共识")', "分歧度低于高共识阈值"),
    (9, "价值场次", f'=COUNTIF({S_SUM}!S{ROW_START}:S{ROW_END},"价值*")', "共识概率显著高于市场隐含概率"),
]
for r, name, formula, desc in kpis:
    ws.cell(r, 1, name).font = F_BOLD
    ws.cell(r, 1).border = BORDER
    ws.cell(r, 1).fill = FILL_CALC
    c = ws.cell(r, 2, formula)
    c.font = F_BOLD
    c.fill = FILL_INPUT
    c.border = BORDER
    c.alignment = Alignment(horizontal="center")
    c.number_format = INT
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=8)
    d = ws.cell(r, 3, desc)
    d.font = F_SUB
    d.alignment = Alignment(vertical="center", wrap_text=True)

section(11, "② 填写顺序")
note_row(12, "第 1 步", "01_比赛清单：填日期、联赛、主队、客队；编号自动生成。")
note_row(13, "第 2 步", "02_外盘欧赔：把第 2 行的「公司A/B/C」改成实际公司名，逐场填 1X2 赔率；可插入列增加公司，但需同步扩展均值公式。")
note_row(14, "第 3 步", "03_来源预测：每场已预置 10 个来源行，只需填 C/D/E 三项概率（0–1 小数）、L 数据形态、T 备注；其余列自动计算。")
note_row(15, "第 4 步", "05_共识汇总：全自动，勿手填（仅 W 列人工备注可填）；04_权重参数 中的权重与阈值可按需调整。")

section(17, "③ 口径速查")
note_row(18, "归一化", "来源三项概率先除以自身合计，强制归一为 1，避免不同来源口径不一致。")
note_row(19, "欧赔去水", "比例法：隐含概率 = (1/均赔) ÷ Σ(1/均赔)；Σ(1/均赔) 即水位合计（overround）。")
note_row(20, "共识概率", "按有效来源权重加权平均；缺席来源自动剔除，权重按实际参与来源重新归一。")
note_row(21, "分歧度", "三项「加权标准差」的平均值，衡量各来源意见分散程度（越大越分裂）。")
note_row(22, "价值 / 回避", "带符号最大偏离 = 共识概率 − 市场隐含概率；≥ 阈值记为「价值」，≤ −阈值记为「回避」。")

section(24, "④ 数据缺口处理原则（务必遵守）")
note_row(25, "缺席留空", "来源无数据就整行留空，绝不填 0、绝不猜测；有效标记会自动置 0 并剔除该来源。")
note_row(26, "预测市场", "Polymarket / Kalshi 多为「某队获胜」是/否合约，需换算为三项概率，并在备注写明合约标的、价格与换算方式。")
note_row(27, "媒体文字", "Goal / FootballWhispers 等只有文字倾向时，按 04_权重参数 的倾向量化规则赋分，L 列必须选「媒体量化」。")
note_row(28, "时点一致", "所有赔率与预测须标注采集时间；赛前伤停/首发变动后应重取，避免用过期价格做对比。")

section(30, "⑤ 颜色图例")
note_row(31, "浅蓝底", "输入区：需要你填写。", FILL_INPUT)
note_row(32, "浅灰底", "计算区：公式自动生成，请勿覆盖。", FILL_CALC)
note_row(33, "条件色", "绿=高共识/达标，红=高分歧/回避/数据不足，黄=需复核或临界。")
note_row(34, "容量说明", f"当前预留 {N_MATCH} 场比赛（每场 {N_SRC} 个来源）。需要更多场次时，在三个录入表末尾整行插入并下拉复制公式，或直接告诉我按实际场次数重新生成。")

# ============================================================
# 01_比赛清单
# ============================================================
ws = wb.create_sheet("01_比赛清单")
banner(ws, 6, "① 比赛清单（输入）", "一行一场；编号自动生成。日期用日期格式，备注可记伤停、战意、赛制、是否中立场等会影响模型解释的信息。")
header(ws, ROW_HEAD, ["编号", "日期", "联赛 / 赛事", "主队", "客队", "备注（伤停 / 战意 / 赛制）"])
widths(ws, {"A": 8, "B": 14, "C": 22, "D": 20, "E": 20, "F": 46})
for r in range(ROW_START, ROW_END + 1):
    a = ws.cell(r, 1, f'=IF(COUNTA(B{r}:E{r})=0,"",ROW()-{ROW_START - 1})')
    body(a, "calc", INT)
    for col in range(2, 7):
        c = ws.cell(r, col)
        body(c, "input", "yyyy-mm-dd" if col == 2 else None, wrap=(col == 6))
    ws.row_dimensions[r].height = 22
ws.freeze_panes = "C4"
ws.auto_filter.ref = f"A{ROW_HEAD}:F{ROW_END}"

# ============================================================
# 02_外盘欧赔
# ============================================================
ws = wb.create_sheet("02_外盘欧赔")
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=21)
_c = ws.cell(1, 1, "② 外盘欧赔（输入 + 自动去水）｜ 公司名在第 2 行可改，赔率时点写在备注列")
_c.font = F_TITLE
_c.fill = FILL_GROUP
_c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 28
groups = [(1, 2, "标识"), (3, 5, "公司A（可改名）"), (6, 8, "公司B（可改名）"),
          (9, 11, "公司C（可改名）"), (12, 20, "自动计算区（勿手填）"), (21, 21, "备注")]
for c1, c2, text in groups:
    if c1 != c2:
        ws.merge_cells(start_row=ROW_GROUP, start_column=c1, end_row=ROW_GROUP, end_column=c2)
    c = ws.cell(ROW_GROUP, c1, text)
    c.font = F_HEAD
    c.fill = FILL_GROUP
    c.alignment = Alignment(horizontal="center", vertical="center")
heads = ["编号", "对阵",
         "公A_主", "公A_平", "公A_客", "公B_主", "公B_平", "公B_客", "公C_主", "公C_平", "公C_客",
         "公司数", "均赔_主", "均赔_平", "均赔_客", "水位合计",
         "隐含_主", "隐含_平", "隐含_客", "主胜赔率极差", "备注（公司名 / 赔率时点）"]
header(ws, ROW_HEAD, heads)
widths(ws, {"A": 8, "B": 26, "L": 9, "M": 11, "N": 11, "O": 11, "P": 11,
            "Q": 11, "R": 11, "S": 11, "T": 13, "U": 40})
for col in "CDEFGHIJK":
    ws.column_dimensions[col].width = 10
for r in range(ROW_START, ROW_END + 1):
    ws.cell(r, 1, f'=IF({S_LIST}!D{r}="","",{S_LIST}!A{r})')
    ws.cell(r, 2, f'=IF({S_LIST}!D{r}="","",{S_LIST}!D{r}&" vs "&{S_LIST}!E{r})')
    ws.cell(r, 12, f'=IF(C{r}<>"",1,0)+IF(F{r}<>"",1,0)+IF(I{r}<>"",1,0)')
    ws.cell(r, 13, f'=IF(COUNT(C{r},F{r},I{r})=0,"",AVERAGE(C{r},F{r},I{r}))')
    ws.cell(r, 14, f'=IF(COUNT(D{r},G{r},J{r})=0,"",AVERAGE(D{r},G{r},J{r}))')
    ws.cell(r, 15, f'=IF(COUNT(E{r},H{r},K{r})=0,"",AVERAGE(E{r},H{r},K{r}))')
    ws.cell(r, 16, f'=IF(COUNT(M{r}:O{r})<3,"",IF(OR(M{r}=0,N{r}=0,O{r}=0),"",1/M{r}+1/N{r}+1/O{r}))')
    for col, avg in (("Q", "M"), ("R", "N"), ("S", "O")):
        ws.cell(r, column_index_from_string(col),
                f'=IF(OR({avg}{r}="",{avg}{r}=0,P{r}="",P{r}=0),"",(1/{avg}{r})/P{r})')
    ws.cell(r, 20, f'=IF(COUNT(C{r},F{r},I{r})<2,"",MAX(C{r},F{r},I{r})-MIN(C{r},F{r},I{r}))')
    for col in range(1, 22):
        c = ws.cell(r, col)
        is_input = col in (3, 4, 5, 6, 7, 8, 9, 10, 11, 21)
        fmt = ODDS if col in (3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 20) else (
            PCT if col in (17, 18, 19) else (NUM2 if col == 16 else (INT if col == 12 else None)))
        body(c, "input" if is_input else "calc", fmt, wrap=(col in (2, 21)))
    ws.row_dimensions[r].height = 22
ws.freeze_panes = "C4"
ws.auto_filter.ref = f"A{ROW_HEAD}:U{ROW_END}"
dv_odds = DataValidation(type="decimal", operator="greaterThan", formula1="1", allow_blank=True)
dv_odds.error = "欧赔必须大于 1.00"
dv_odds.errorTitle = "赔率不合法"
ws.add_data_validation(dv_odds)
dv_odds.add(f"C{ROW_START}:K{ROW_END}")

# ============================================================
# 03_来源预测
# ============================================================
ws = wb.create_sheet("03_来源预测")
banner(ws, 20, "③ 多来源预测录入（长表）",
       f"每场预置 {N_SRC} 行来源，共 {N_MATCH * N_SRC} 行。只需填 C/D/E 三项概率、L 数据形态、T 备注；来源缺席则整行留空，权重自动重分配。")
heads = ["比赛编号", "来源", "主胜概率", "平局概率", "客胜概率", "概率和",
         "归一_主", "归一_平", "归一_客", "权重", "有效", "数据形态",
         "加权_主", "加权_平", "加权_客", "有效权重",
         "加权_主²", "加权_平²", "加权_客²", "备注（时点 / 链接 / 换算说明）"]
header(ws, ROW_HEAD, heads)
widths(ws, {"A": 11, "B": 24, "F": 10, "J": 9, "K": 8, "L": 15, "P": 11, "T": 44})
for col in "CDEGHIMNOQRS":
    ws.column_dimensions[col].width = 11
for idx in range(N_MATCH * N_SRC):
    r = ROW_START + idx
    match_no = idx // N_SRC + 1
    src_name = SOURCES[idx % N_SRC][0]
    ws.cell(r, 1, match_no)
    ws.cell(r, 2, src_name)
    ws.cell(r, 6, f'=IF(COUNT(C{r}:E{r})=0,"",SUM(C{r}:E{r}))')
    for col, src in (("G", "C"), ("H", "D"), ("I", "E")):
        ws.cell(r, column_index_from_string(col),
                f'=IF(OR(F{r}="",F{r}=0,COUNT(C{r}:E{r})<3),"",{src}{r}/F{r})')
    ws.cell(r, 10, f'=IFERROR(VLOOKUP(B{r},{S_PARAM}!$A$4:$C$13,3,FALSE),0)')
    ws.cell(r, 11, f'=IF(AND(COUNT(C{r}:E{r})=3,F{r}>0,G{r}<>"",H{r}<>"",I{r}<>""),1,0)')
    ws.cell(r, 13, f'=IF(K{r}=1,J{r}*G{r},0)')
    ws.cell(r, 14, f'=IF(K{r}=1,J{r}*H{r},0)')
    ws.cell(r, 15, f'=IF(K{r}=1,J{r}*I{r},0)')
    ws.cell(r, 16, f'=IF(K{r}=1,J{r},0)')
    for col, src in (("Q", "G"), ("R", "H"), ("S", "I")):
        ws.cell(r, column_index_from_string(col), f'=IF(K{r}=1,J{r}*{src}{r}^2,0)')
    for col in range(1, 21):
        c = ws.cell(r, col)
        is_input = col in (3, 4, 5, 12, 20) or col == 1 or col == 2
        fmt = PCT if col in (3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19) else (
            INT if col in (1, 11) else None)
        body(c, "input" if is_input else "calc", fmt, wrap=(col in (2, 20)))
    ws.row_dimensions[r].height = 20
    if idx % N_SRC == 0 and idx > 0:
        for col in range(1, 21):
            ws.cell(r, col).border = Border(left=thin, right=thin, top=Side(style="medium", color=XL_PRIMARY), bottom=thin)
ws.freeze_panes = "C4"
ws.auto_filter.ref = f"A{ROW_HEAD}:T{PRED_END}"
dv_prob = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True)
dv_prob.error = "概率请用 0–1 之间的小数（如 0.45）"
dv_prob.errorTitle = "概率不合法"
ws.add_data_validation(dv_prob)
dv_prob.add(f"C{ROW_START}:E{PRED_END}")
dv_kind = DataValidation(type="list", formula1='"数值概率,媒体量化,合约换算,缺席"', allow_blank=True)
ws.add_data_validation(dv_kind)
dv_kind.add(f"L{ROW_START}:L{PRED_END}")
ws.conditional_formatting.add(
    f"F{ROW_START}:F{PRED_END}",
    FormulaRule(formula=[f'AND(F{ROW_START}<>"",OR(F{ROW_START}<0.95,F{ROW_START}>1.05))'],
                fill=FILL_YELLOW, font=FONT_YELLOW))
ws.conditional_formatting.add(
    f"K{ROW_START}:K{PRED_END}",
    FormulaRule(formula=[f'AND(K{ROW_START}=0,COUNT(C{ROW_START}:E{ROW_START})>0)'],
                fill=FILL_RED, font=FONT_RED))

# ============================================================
# 04_权重参数
# ============================================================
ws = wb.create_sheet("04_权重参数")
banner(ws, 4, "④ 权重与判定阈值（可调整）",
       "默认权重是起点而非结论：建议用历史命中率/Brier 分数回测后再校准。权重合计应等于 1.00。")
header(ws, 3, ["来源", "层级", "默认权重", "依据 / 注意事项"])
widths(ws, {"A": 28, "B": 16, "C": 14, "D": 62})
for i, (name, tier, w, desc) in enumerate(SOURCES):
    r = 4 + i
    ws.cell(r, 1, name)
    ws.cell(r, 2, tier)
    ws.cell(r, 3, w)
    ws.cell(r, 4, desc)
    for col in range(1, 5):
        body(ws.cell(r, col), "input" if col != 4 else "input", PCT if col == 3 else None, wrap=(col == 4))
    ws.row_dimensions[r].height = 24
ws.cell(14, 1, "权重合计").font = F_BOLD
ws.cell(14, 3, "=SUM(C4:C13)")
for col in range(1, 5):
    c = ws.cell(14, col)
    c.fill = FILL_CALC
    c.font = F_BOLD
    c.border = BORDER
    c.alignment = Alignment(vertical="center", wrap_text=(col == 4))
ws.cell(14, 3).number_format = PCT
ws.cell(14, 4, "应等于 1.00；调整单项权重后请核对").font = F_SUB

ws.merge_cells("A16:D16")
c = ws.cell(16, 1, "判定阈值（可调整）")
c.font = F_HEAD
c.fill = FILL_HEAD
c.alignment = Alignment(vertical="center", indent=1)
header(ws, 17, ["参数", "取值", "说明", ""])
ws.merge_cells("C17:D17")
thresholds = [
    (18, "价值偏离阈值", 0.05, "共识概率相对市场隐含概率的优势达到该幅度才标记价值/回避"),
    (19, "高共识分歧阈值", 0.06, "分歧度 ≤ 该值记为高共识"),
    (20, "高分歧阈值", 0.12, "分歧度 ≥ 该值记为高分歧"),
    (21, "最低数据完整度", 0.60, "低于该值不做价值判定，只标数据不足"),
]
for r, name, val, desc in thresholds:
    ws.cell(r, 1, name)
    ws.cell(r, 2, val)
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=4)
    ws.cell(r, 3, desc)
    for col in range(1, 5):
        cc = ws.cell(r, col)
        cc.font = F_BODY if col != 2 else F_BOLD
        cc.fill = FILL_INPUT if col == 2 else FILL_CALC
        cc.border = BORDER
        cc.alignment = Alignment(vertical="center", wrap_text=(col >= 3))
    ws.cell(r, 2).number_format = PCT
    ws.row_dimensions[r].height = 24

ws.merge_cells("A23:D23")
c = ws.cell(23, 1, "媒体文字倾向量化规则（仅当来源无数值概率时使用，必须在来源表备注标注「媒体量化」）")
c.font = F_HEAD
c.fill = FILL_HEAD
c.alignment = Alignment(vertical="center", indent=1)
header(ws, 24, ["文字倾向", "主胜", "平局", "客胜"])
for r, vals in enumerate([("主胜倾向", .55, .27, .18), ("平局倾向", .30, .40, .30), ("客胜倾向", .18, .27, .55)], start=25):
    for col, v in enumerate(vals, start=1):
        cc = ws.cell(r, col, v)
        body(cc, "calc" if col > 1 else "input", PCT if col > 1 else None)
    ws.row_dimensions[r].height = 22

ws.merge_cells("A29:D29")
c = ws.cell(29, 1, "口径说明")
c.font = F_HEAD
c.fill = FILL_HEAD
c.alignment = Alignment(vertical="center", indent=1)
for r, (k, v) in enumerate([
    ("去水方法", "比例法（隐含概率 ÷ 水位合计）。如需 Shin / 幂法去水，可在此扩展，需同步改写欧赔表公式。"),
    ("共识公式", "Σ(权重 × 归一化概率) ÷ Σ(有效权重)；缺席来源自动剔除，等价按参与来源重新归一。"),
    ("分歧度", "三项加权标准差的平均：σ = √(Σw·p²/Σw − 共识²)，取三项均值。"),
    ("价值定义", "共识概率高于市场隐含概率且超过阈值；反向偏离记为「回避」。均需满足最低数据完整度。"),
    ("凯利提示", "正式报告可附 f* = (b·p − q)/b，但框架不自动给出仓位建议；赔率时效与水位须先复核。"),
], start=30):
    ws.cell(r, 1, k).font = F_BOLD
    ws.cell(r, 1).fill = FILL_CALC
    ws.cell(r, 1).border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    cc = ws.cell(r, 2, v)
    cc.font = F_BODY
    cc.alignment = Alignment(vertical="center", wrap_text=True)
    cc.border = BORDER
    ws.row_dimensions[r].height = 28

# ============================================================
# 05_共识汇总
# ============================================================
ws = wb.create_sheet("05_共识汇总")
banner(ws, 23, "⑤ 共识汇总与研判指标（全自动）",
       "全部由公式生成，请勿手填；仅 W 列人工备注可填写。市场基准来自 02_外盘欧赔，共识来自 03_来源预测，阈值来自 04_权重参数。")
heads = ["编号", "对阵", "有效来源数", "数据完整度",
         "市场_主", "市场_平", "市场_客", "共识_主", "共识_平", "共识_客",
         "偏离_主", "偏离_平", "偏离_客", "最大偏离项", "最大偏离幅度", "带符号偏离",
         "分歧度", "共识标签", "价值标签", "优先级分", "优先级", "自动摘要", "人工备注"]
header(ws, ROW_HEAD, heads)
widths(ws, {"A": 8, "B": 26, "C": 12, "D": 12, "N": 13, "O": 14,
            "P": 13, "Q": 11, "R": 13, "S": 16, "T": 11, "U": 10, "V": 52, "W": 34})
for col in "EFGHIJKLM":
    ws.column_dimensions[col].width = 11

W = lambda r: f"SUMIF({PRED_A},A{r},{pcol('P')})"
P_MARK = f"{S_PARAM}!$B$18"
P_CONS = f"{S_PARAM}!$B$19"
P_DIV = f"{S_PARAM}!$B$20"
P_MIN = f"{S_PARAM}!$B$21"
P_TOTAL = f"{S_PARAM}!$C$14"

for r in range(ROW_START, ROW_END + 1):
    ws.cell(r, 1, f'=IF({S_LIST}!D{r}="","",{S_LIST}!A{r})')
    ws.cell(r, 2, f'=IF({S_LIST}!D{r}="","",{S_LIST}!D{r}&" vs "&{S_LIST}!E{r})')
    ws.cell(r, 3, f'=IF(A{r}="","",SUMIF({PRED_A},A{r},{pcol("K")}))')
    ws.cell(r, 4, f'=IF(OR(A{r}="",{P_TOTAL}=0),"",SUMIF({PRED_A},A{r},{pcol("P")})/{P_TOTAL})')
    for col, odds_col in (("E", "Q"), ("F", "R"), ("G", "S")):
        ws.cell(r, column_index_from_string(col),
                f'=IF(OR(A{r}="",{S_ODDS}!{odds_col}{r}=""),"",{S_ODDS}!{odds_col}{r})')
    for col, pred_col in (("H", "M"), ("I", "N"), ("J", "O")):
        ws.cell(r, column_index_from_string(col),
                f'=IF(A{r}="","",IF({W(r)}=0,"",SUMIF({PRED_A},A{r},{pcol(pred_col)})/{W(r)}))')
    for col, consensus, market in (("K", "H", "E"), ("L", "I", "F"), ("M", "J", "G")):
        ws.cell(r, column_index_from_string(col),
                f'=IF(OR({consensus}{r}="",{market}{r}=""),"",{consensus}{r}-{market}{r})')
    ws.cell(r, 14,
            f'=IF(OR(K{r}="",L{r}="",M{r}=""),"",IF(ABS(K{r})>=ABS(L{r}),IF(ABS(K{r})>=ABS(M{r}),"主胜","客胜"),IF(ABS(L{r})>=ABS(M{r}),"平局","客胜")))')
    ws.cell(r, 15, f'=IF(OR(K{r}="",L{r}="",M{r}=""),"",MAX(ABS(K{r}),ABS(L{r}),ABS(M{r})))')
    ws.cell(r, 16, f'=IF(N{r}="","",IF(N{r}="主胜",K{r},IF(N{r}="平局",L{r},M{r})))')
    var = "+".join([
        f"SQRT(MAX(0,SUMIF({PRED_A},A{r},{pcol(q)})/{W(r)}-{cons}{r}^2))"
        for q, cons in (("Q", "H"), ("R", "I"), ("S", "J"))
    ])
    ws.cell(r, 17, f'=IF(OR(A{r}="",H{r}="",I{r}="",J{r}=""),"",IF({W(r)}=0,"",({var})/3))')
    ws.cell(r, 18,
            f'=IF(OR(Q{r}="",D{r}=""),"",IF(D{r}<{P_MIN},"数据不足",IF(Q{r}<={P_CONS},"高共识",IF(Q{r}>={P_DIV},"高分歧","一般"))))')
    ws.cell(r, 19,
            f'=IF(OR(P{r}="",N{r}="",D{r}=""),"",IF(AND(P{r}>={P_MARK},D{r}>={P_MIN}),"价值 · "&N{r},IF(AND(P{r}<=-{P_MARK},D{r}>={P_MIN}),"回避 · "&N{r},"无")))')
    ws.cell(r, 20,
            f'=IF(OR(D{r}="",Q{r}="",O{r}=""),"",ROUND(MAX(0,MIN(100,D{r}*30+(1-MIN(Q{r}/MAX({P_DIV},0.01),1))*30+MIN(O{r}/0.15,1)*40)),0))')
    ws.cell(r, 21, f'=IF(T{r}="","",IF(T{r}>=70,"A",IF(T{r}>=45,"B","C")))')
    ws.cell(r, 22,
            f'=IF(OR(A{r}="",H{r}=""),"","共识 "&TEXT(H{r},"0%")&"/"&TEXT(I{r},"0%")&"/"&TEXT(J{r},"0%")&"｜"&R{r}&"｜"&S{r}&"｜完整度 "&TEXT(D{r},"0%"))')
    for col in range(1, 24):
        c = ws.cell(r, col)
        is_input = col == 23
        fmt = PCT if col in (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17) else (
            INT if col in (1, 3, 20) else None)
        body(c, "input" if is_input else "calc", fmt, wrap=(col in (2, 22, 23)))
    ws.row_dimensions[r].height = 24

ws.freeze_panes = "C4"
ws.auto_filter.ref = f"A{ROW_HEAD}:W{ROW_END}"
def cr(col):
    return f"{col}{ROW_START}:{col}{ROW_END}"


ws.conditional_formatting.add(cr("R"), FormulaRule(formula=[f'R{ROW_START}="高共识"'], fill=FILL_GREEN, font=FONT_GREEN))
ws.conditional_formatting.add(cr("R"), FormulaRule(formula=[f'R{ROW_START}="高分歧"'], fill=FILL_RED, font=FONT_RED))
ws.conditional_formatting.add(cr("R"), FormulaRule(formula=[f'R{ROW_START}="数据不足"'], fill=FILL_YELLOW, font=FONT_YELLOW))
ws.conditional_formatting.add(cr("S"), FormulaRule(formula=[f'LEFT(S{ROW_START},2)="价值"'], fill=FILL_GREEN, font=FONT_GREEN))
ws.conditional_formatting.add(cr("S"), FormulaRule(formula=[f'LEFT(S{ROW_START},2)="回避"'], fill=FILL_RED, font=FONT_RED))
ws.conditional_formatting.add(cr("D"), FormulaRule(formula=[f'AND(D{ROW_START}<>"",D{ROW_START}<{P_MIN})'], fill=FILL_RED, font=FONT_RED))
ws.conditional_formatting.add(cr("D"), FormulaRule(formula=[f'AND(D{ROW_START}<>"",D{ROW_START}>=0.8)'], fill=FILL_GREEN, font=FONT_GREEN))
ws.conditional_formatting.add(cr("O"), FormulaRule(formula=[f'AND(O{ROW_START}<>"",O{ROW_START}>={P_MARK})'], fill=FILL_YELLOW, font=FONT_YELLOW))
ws.conditional_formatting.add(cr("U"), FormulaRule(formula=[f'U{ROW_START}="A"'], fill=FILL_GREEN, font=FONT_GREEN))

# 标签色：结果区表头加深
for c in ws[3]:
    if c.column in (18, 19, 20, 21, 22):
        c.fill = FILL_GROUP

wb.save(OUT)
print("saved:", OUT)
