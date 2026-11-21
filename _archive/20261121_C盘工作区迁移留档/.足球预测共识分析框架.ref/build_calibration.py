# -*- coding: utf-8 -*-
"""生成《预测校准台账.xlsx》：赛果核对 → 期次汇总 → 变差监控 → 纠偏 → 反哺参数出口。
预置 26167 期 14 场「赛前预测基线」（源自 26167_data.json），赛果列 L/M 留空待开奖后录入。
公式写入单元格，由本机 Excel COM 重算生成缓存值；空字符串缓存 <v/> 由 verify_ooxml.py 校验。
"""
import json
from pathlib import Path

try:
    import openpyxl
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "openpyxl>=3.1.0"])
    import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import FormulaRule
from openpyxl.utils import get_column_letter

BASE = Path(r"C:\Users\wuyan\WorkBuddy\2026-11-20-21-07-35")
SRC = BASE / ".足球预测共识分析框架.ref" / "26167_data.json"
OUT = BASE / "预测校准台账.xlsx"


def xl_color(h):
    return "FF" + h.removeprefix("#").upper()


C_HEAD = xl_color("#4472C4")
C_DARK = xl_color("#2F5597")
C_INPUT = xl_color("#D9E2F3")
C_CALC = xl_color("#F2F2F2")
C_WHITE = xl_color("#FFFFFF")
C_TEXT = xl_color("#1A1A1A")
C_BORDER = xl_color("#BFBFBF")
C_GREEN = xl_color("#C6EFCE")
C_RED = xl_color("#FFC7CE")
C_YELLOW = xl_color("#FFEB9C")
thin = Side(style="thin", color=C_BORDER)
BD = Border(left=thin, right=thin, top=thin, bottom=thin)

R0, R1 = 4, 63          # 台账数据区：4–63，共 60 行（14 场已预置，46 行留空追加）
S1 = "'01_赛果核对台账'"
S3 = "'03_期次汇总'"


def banner(ws, text, last_col):
    ws.cell(1, 1, text)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    c = ws.cell(1, 1)
    c.fill = PatternFill("solid", fgColor=C_DARK)
    c.font = Font(bold=True, color=C_WHITE, size=12)
    c.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 26


def header(ws, row, headers, widths):
    for i, h in enumerate(headers, 1):
        c = ws.cell(row, i, h)
        c.fill = PatternFill("solid", fgColor=C_HEAD)
        c.font = Font(bold=True, color=C_WHITE, size=10)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BD
    ws.row_dimensions[row].height = 34
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row + 1, 1)


def put(ws, r, c, v, fill=None, calc=False):
    cell = ws.cell(r, c, v)
    cell.border = BD
    cell.font = Font(color=C_TEXT, size=10)
    cell.alignment = Alignment(vertical="top", wrap_text=True)
    if calc:
        cell.fill = PatternFill("solid", fgColor=C_CALC)
    elif fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    return cell


# ---------------- 预置数据 ----------------
data = json.loads(SRC.read_text(encoding="utf-8"))
M = data["matches"]

SCORE_PLAN = {9: "2-0、3-0", 13: "0-2、1-2", 6: "0-1、1-2",
              5: "3-1、2-1", 2: "2-1、1-1", 10: "1-2、1-1"}
SINGLE = {2, 5, 6, 9, 11, 13}
DOUBLE = {1, 3, 10}
DROP = {4, 7, 8, 12, 14}
FMAP = [3, 1, 0]


def vig(o):
    inv = [1.0 / x for x in o]
    s = sum(inv)
    return [x / s for x in inv]


wb = Workbook()

# ================= 00_使用说明 =================
ws = wb.active
ws.title = "00_使用说明"
banner(ws, "预测校准台账 · 使用说明（赛果核对 → 纠偏 → 变差总结 → 反哺预测）", 2)
header(ws, 3, ["项目", "说明"], [26, 108])
notes = [
    ("定位", "把 S5 复盘反哺升级为自动化量化校准闭环。先冻结赛前预测基线，开奖后只录入两列赛果，其余全部自动计算。"),
    ("核心原则", "基线冻结：A–K 与 U/V 列一经登记不得因赛果反向修改；校准只用于下一期，不追溯、不改已交付报告。"),
    ("第一层 · 赛果核对", "01_赛果核对台账：L 填实际赛果 3/1/0（延期腰斩填 *），M 填实际比分如 2-1。N–T 自动算方向命中、Brier、LogLoss、实际项概率、信心偏差、比分命中、qmax。"),
    ("第二层 · 自动纠正", "02_来源权重纠偏：按滚动命中率给出建议权重，带最小样本 30 场与 0.60–1.50 系数上下限；03_期次汇总自动算 24 项指标与三个倒挂差值。"),
    ("第三层 · 变差总结", "04_变差监控：11 条信号自动判「变差 / 正常 / 数据未齐」；05_变差总结归档记录归因、纠正动作与下期验证点。"),
    ("第四层 · 反哺预测", "06_反哺参数出口：参数建议写回目标（框架 04_权重参数、S2 阈值、S3 结构）。默认待确认，人工确认参数版本后才生效。"),
    ("浅蓝底", "录入区：01 表 L、M 两列；02 表 C、D 两列；05 表全表；06 表 D、E、F 列。"),
    ("灰底", "自动计算区，请勿手工覆盖公式。"),
    ("三种入口", "A 赛果页手工录入后运行；B 定时任务（需用户给时间表后挂载）；C --input results.json 批量导入。"),
    ("执行命令", "python3 .足球预测共识分析框架.ref/reconcile.py --issue 26167 ；加 --demo 演示；加 --write-back 才回写 05/06 表。"),
    ("当前状态", "2026-11-21 21:50，26167 期 22:00 停售、11-22 开奖，赛果未产生。14 场预测基线已登记，L/M 留空；引擎此时只输出「等待赛果录入」。"),
    ("基线说明", "04 表基线为首版参考值，跑满 5 期后改用近 5 期滚动均值，替换动作写入参数版本记录。"),
    ("数据缺口", "未取到的外部来源不参与评分、不降权，只标「无样本」；延期/腰斩场次不进入指标分母。"),
    ("合规口径", "纠偏只发生在内部量化层；头条正文继续零赔率、零机构态度解读。预算上限 50 元与单注 2 元为硬约束，不参与纠偏。"),
    ("配套文档", "赛果核对与预测校准闭环_SOP.md（规则）、赛果核对与预测校准闭环_总览.html（速查）、26167期_内部分析报告.html 第 8 章（接口）。"),
    ("免责", "全部内容仅作数据观察与思路参考，不构成投注建议，注意控制仓位与过关风险。"),
]
for i, (k, v) in enumerate(notes, R0):
    put(ws, i, 1, k, fill=C_INPUT)
    put(ws, i, 2, v)
    ws.row_dimensions[i].height = 30

# ================= 01_赛果核对台账 =================
ws = wb.create_sheet("01_赛果核对台账")
H1 = ["期号", "场次", "联赛", "对阵", "预测方向\n3/1/0", "预测主胜 q", "预测平 q", "预测客 q",
      "把握层次", "共振信号", "预测比分区间", "实际赛果\n3/1/0【录入】", "实际比分\n【录入】",
      "方向命中", "Brier", "LogLoss", "实际项概率", "信心偏差", "比分命中", "qmax",
      "任九状态", "备注"]
W1 = [10, 7, 8, 30, 12, 11, 11, 11, 20, 12, 18, 16, 14, 10, 10, 10, 12, 11, 10, 10, 12, 30]
banner(ws, "01 · 赛果核对台账（浅蓝 2 列为录入区；其余为冻结基线与自动计算）", len(H1))
header(ws, 3, H1, W1)

ISSUE = "26167"
for idx, m in enumerate(M):
    r = R0 + idx
    q = vig(m["nw"])
    fav = FMAP[q.index(max(q))]
    no = m["no"]
    r9 = "单选" if no in SINGLE else ("双选" if no in DOUBLE else "剔除")
    vals = {1: ISSUE, 2: no, 3: m["lg"], 4: f'{m["h"]} vs {m["a"]}', 5: fav,
            6: round(q[0], 4), 7: round(q[1], 4), 8: round(q[2], 4),
            9: m["tier"], 10: m["sig"], 11: SCORE_PLAN.get(no, ""),
            21: r9, 22: f'数据时点 11-20 14:10；来源数 {m["ext_n"]}；{m["dt"]}'}
    for c, v in vals.items():
        put(ws, r, c, v)
    put(ws, r, 12, None, fill=C_INPUT)
    put(ws, r, 13, None, fill=C_INPUT)
    put(ws, r, 14, f'=IF($L{r}="","",IF($E{r}=$L{r},1,0))', calc=True)
    put(ws, r, 15, f'=IF($L{r}="","",($F{r}-IF($L{r}=3,1,0))^2+($G{r}-IF($L{r}=1,1,0))^2+($H{r}-IF($L{r}=0,1,0))^2)', calc=True)
    put(ws, r, 16, f'=IF($L{r}="","",-LN($Q{r}+0.000001))', calc=True)
    put(ws, r, 17, f'=IF($L{r}="","",INDEX($F{r}:$H{r},1,IF($L{r}=3,1,IF($L{r}=1,2,3))))', calc=True)
    put(ws, r, 18, f'=IF($L{r}="","",$T{r}-$Q{r})', calc=True)
    put(ws, r, 19, f'=IF($M{r}="","",IF($K{r}="",0,IFERROR(IF(ISNUMBER(SEARCH($M{r},$K{r})),1,0),0)))', calc=True)
    put(ws, r, 20, f'=IF($F{r}="","",MAX($F{r}:$H{r}))', calc=True)

for r in range(R0 + len(M), R1 + 1):
    for c in (12, 13):
        put(ws, r, c, None, fill=C_INPUT)
    put(ws, r, 14, f'=IF($L{r}="","",IF($E{r}=$L{r},1,0))', calc=True)
    put(ws, r, 15, f'=IF($L{r}="","",($F{r}-IF($L{r}=3,1,0))^2+($G{r}-IF($L{r}=1,1,0))^2+($H{r}-IF($L{r}=0,1,0))^2)', calc=True)
    put(ws, r, 16, f'=IF($L{r}="","",-LN($Q{r}+0.000001))', calc=True)
    put(ws, r, 17, f'=IF($L{r}="","",INDEX($F{r}:$H{r},1,IF($L{r}=3,1,IF($L{r}=1,2,3))))', calc=True)
    put(ws, r, 18, f'=IF($L{r}="","",$T{r}-$Q{r})', calc=True)
    put(ws, r, 19, f'=IF($M{r}="","",IF($K{r}="",0,IFERROR(IF(ISNUMBER(SEARCH($M{r},$K{r})),1,0),0)))', calc=True)
    put(ws, r, 20, f'=IF($F{r}="","",MAX($F{r}:$H{r}))', calc=True)

ws.conditional_formatting.add(f"N{R0}:N{R1}", FormulaRule(formula=[f'AND(ISNUMBER($N{R0}),$N{R0}=1)'], fill=PatternFill("solid", fgColor=C_GREEN)))
ws.conditional_formatting.add(f"N{R0}:N{R1}", FormulaRule(formula=[f'AND(ISNUMBER($N{R0}),$N{R0}=0)'], fill=PatternFill("solid", fgColor=C_RED)))

# ================= 02_来源权重纠偏 =================
ws = wb.create_sheet("02_来源权重纠偏")
H2 = ["来源类别", "基线权重", "滚动有效场数【录入】", "滚动命中数【录入】", "命中率",
      "基准命中率", "权重系数", "建议权重", "系数下限", "系数上限", "最小样本",
      "生效期号", "状态"]
W2 = [30, 12, 20, 18, 12, 13, 12, 12, 11, 11, 12, 12, 24]
banner(ws, "02 · 来源权重纠偏（缺席来源不降权、不计入分母；单期调整 ≤ 20%）", len(H2))
header(ws, 3, H2, W2)
SOURCES = [
    ("海外主流媒体（Goal / FootballWhispers / SportsGambler / Futbol24）", 0.14),
    ("预测聚合（betiper 等）", 0.10),
    ("预测市场（Polymarket / Kalshi）", 0.12),
    ("AI 模型（BetBuilders xG / adalbet / football-predictions.ai）", 0.14),
    ("统计模型（Forebet / Wincomparator / premierleagueprediction.org）", 0.14),
    ("算法增强（OddAlerts）", 0.08),
    ("中文媒体与数据（腾讯 / 新浪 / 网易 / 纳米数据）", 0.10),
    ("官方伤停与赛程情报", 0.10),
    ("Google 数据模型", 0.08),
    ("外盘欧赔（市场基准，不参与共识加权）", 0.00),
]
for i, (name, w) in enumerate(SOURCES):
    r = R0 + i
    put(ws, r, 1, name)
    put(ws, r, 2, w)
    put(ws, r, 3, None, fill=C_INPUT)
    put(ws, r, 4, None, fill=C_INPUT)
    put(ws, r, 5, f'=IF($C{r}=0,"",$D{r}/$C{r})', calc=True)
    put(ws, r, 6, 0.50 if w > 0 else 0.00)
    put(ws, r, 7, f'=IF(OR($B{r}=0,$E{r}="",$C{r}<$K{r},$F{r}=0),"",MIN($J{r},MAX($I{r},$E{r}/$F{r})))', calc=True)
    put(ws, r, 8, f'=IF($G{r}="","",ROUND($B{r}*$G{r},4))', calc=True)
    put(ws, r, 9, 0.60)
    put(ws, r, 10, 1.50)
    put(ws, r, 11, 30)
    put(ws, r, 12, "")
    put(ws, r, 13, f'=IF($B{r}=0,"市场基准·不参与加权",IF($C{r}=0,"无样本·维持基线",IF($C{r}<$K{r},"样本不足·维持基线",IF(ABS($H{r}-$B{r})/$B{r}>0.2,"需人工复核","自动生效"))))', calc=True)

# ================= 03_期次汇总 =================
ws = wb.create_sheet("03_期次汇总")
H3 = ["期号", "有效场数", "方向命中数", "方向命中率", "平均Brier", "平均LogLoss",
      "平均实际项概率", "平均信心偏差", "比分命中率", "实际主胜占比", "实际平局占比",
      "实际客胜占比", "平均预测平局概率", "最敢碰命中率", "共振命中率", "背离命中率",
      "数据不足命中率", "剔除场命中率", "单选场命中率", "高置信场数", "高置信命中数",
      "高置信未命中率", "W 剔除−单选", "X 最敢碰−数据不足", "Y 平局低估"]
W3 = [11] + [13] * (len(H3) - 1)
banner(ws, "03 · 期次汇总（24 项指标；W/X/Y 为三个倒挂差值，是本闭环核心信号）", len(H3))
header(ws, 3, H3, W3)

A1 = f"{S1}!$A${R0}:$A${R1}"
N1 = f"{S1}!$N${R0}:$N${R1}"
O1 = f"{S1}!$O${R0}:$O${R1}"
P1 = f"{S1}!$P${R0}:$P${R1}"
Q1 = f"{S1}!$Q${R0}:$Q${R1}"
R1c = f"{S1}!$R${R0}:$R${R1}"
S1c = f"{S1}!$S${R0}:$S${R1}"
G1 = f"{S1}!$G${R0}:$G${R1}"
L1 = f"{S1}!$L${R0}:$L${R1}"
I1 = f"{S1}!$I${R0}:$I${R1}"
J1 = f"{S1}!$J${R0}:$J${R1}"
U1 = f"{S1}!$U${R0}:$U${R1}"
T1 = f"{S1}!$T${R0}:$T${R1}"


def cnt(criteria_col, criteria):
    return f'COUNTIFS({A1},$A{{r}},{criteria_col},"{criteria}")'


def sm(col, extra=""):
    return f'SUMIFS({col},{A1},$A{{r}}{extra})'


for r in range(R0, R0 + 5):
    put(ws, r, 1, ISSUE if r == R0 else None, fill=C_INPUT)
    f = {
        2: f'=SUMPRODUCT(({A1}=$A{r})*ISNUMBER({N1}))',
        3: f'=SUMIFS({N1},{A1},$A{r})',
        4: f'=IF($B{r}=0,"",$C{r}/$B{r})',
        5: f'=IF($B{r}=0,"",SUMIFS({O1},{A1},$A{r})/$B{r})',
        6: f'=IF($B{r}=0,"",SUMIFS({P1},{A1},$A{r})/$B{r})',
        7: f'=IF($B{r}=0,"",SUMIFS({Q1},{A1},$A{r})/$B{r})',
        8: f'=IF($B{r}=0,"",SUMIFS({R1c},{A1},$A{r})/$B{r})',
        9: f'=IF($B{r}=0,"",SUMIFS({S1c},{A1},$A{r})/$B{r})',
        10: f'=IF($B{r}=0,"",COUNTIFS({A1},$A{r},{L1},3)/$B{r})',
        11: f'=IF($B{r}=0,"",COUNTIFS({A1},$A{r},{L1},1)/$B{r})',
        12: f'=IF($B{r}=0,"",COUNTIFS({A1},$A{r},{L1},0)/$B{r})',
        13: f'=IF($B{r}=0,"",SUMIFS({G1},{A1},$A{r})/$B{r})',
        14: f'=IF(COUNTIFS({A1},$A{r},{I1},"最敢碰")=0,"",SUMIFS({N1},{A1},$A{r},{I1},"最敢碰")/COUNTIFS({A1},$A{r},{I1},"最敢碰"))',
        15: f'=IF(COUNTIFS({A1},$A{r},{J1},"共振")=0,"",SUMIFS({N1},{A1},$A{r},{J1},"共振")/COUNTIFS({A1},$A{r},{J1},"共振"))',
        16: f'=IF(COUNTIFS({A1},$A{r},{J1},"背离")=0,"",SUMIFS({N1},{A1},$A{r},{J1},"背离")/COUNTIFS({A1},$A{r},{J1},"背离"))',
        17: f'=IF(COUNTIFS({A1},$A{r},{J1},"数据不足")=0,"",SUMIFS({N1},{A1},$A{r},{J1},"数据不足")/COUNTIFS({A1},$A{r},{J1},"数据不足"))',
        18: f'=IF(COUNTIFS({A1},$A{r},{U1},"剔除")=0,"",SUMIFS({N1},{A1},$A{r},{U1},"剔除")/COUNTIFS({A1},$A{r},{U1},"剔除"))',
        19: f'=IF(COUNTIFS({A1},$A{r},{U1},"单选")=0,"",SUMIFS({N1},{A1},$A{r},{U1},"单选")/COUNTIFS({A1},$A{r},{U1},"单选"))',
        20: f'=COUNTIFS({A1},$A{r},{T1},">0.6")',
        21: f'=SUMIFS({N1},{A1},$A{r},{T1},">0.6")',
        22: f'=IF($T{r}=0,"",1-$U{r}/$T{r})',
        23: f'=IF(OR($R{r}="",$S{r}=""),"",$R{r}-$S{r})',
        24: f'=IF(OR($N{r}="",$Q{r}=""),"",$N{r}-$Q{r})',
        25: f'=IF(OR($K{r}="",$M{r}=""),"",$K{r}-$M{r})',
    }
    for c, formula in f.items():
        put(ws, r, c, formula, calc=True)

# ================= 04_变差监控 =================
ws = wb.create_sheet("04_变差监控")
H4 = ["#", "变差信号", "计算口径", "基线", "当前值", "方向", "容差", "判定", "观察窗口", "归因方向"]
W4 = [6, 26, 40, 11, 13, 9, 10, 14, 16, 34]
banner(ws, "04 · 变差监控（11 条信号；「变差」= 预测校准度衰减，不是单场输赢）", len(H4))
header(ws, 3, H4, W4)
SIGNALS = [
    (1, "方向命中率衰减", "03!D 方向命中率", 0.45, "='03_期次汇总'!D4", "低", 0.08, "近 5 期", "来源失效型 / 盘型漂移型"),
    (2, "Brier 上升", "03!E 平均 Brier（越小越好）", 0.60, "='03_期次汇总'!E4", "高", 0.05, "近 5 期", "过拟合型 / 概率校准失效"),
    (3, "LogLoss 上升", "03!F 平均 LogLoss", 1.00, "='03_期次汇总'!F4", "高", 0.15, "近 5 期", "过拟合型 / 高置信错判"),
    (4, "实际项概率下降", "03!G 平均实际项概率", 0.45, "='03_期次汇总'!G4", "低", 0.05, "近 5 期", "来源失效型"),
    (5, "信心偏差扩大", "03!H 平均信心偏差", 0.20, "='03_期次汇总'!H4", "高", 0.05, "近 5 期", "临场信息型 / 大热倒灶"),
    (6, "比分命中率衰减", "03!I 比分命中率", 0.20, "='03_期次汇总'!I4", "低", 0.08, "近 5 期", "比分区间设置过窄"),
    (7, "高置信倒灶率上升", "03!V 高置信(qmax>0.6)未命中率", 0.15, "='03_期次汇总'!V4", "高", 0.10, "近 5 期", "临场信息型 / 深盘松懈"),
    (8, "共振兑现率下降", "03!O 共振场命中率", 0.55, "='03_期次汇总'!O4", "低", 0.10, "近 5 期", "数据缺口型 / 来源失效型"),
    (9, "剔除规则倒挂", "03!W = 剔除场命中率 − 单选场命中率", 0.00, "='03_期次汇总'!W4", "高", 0.05, "近 3 期", "S3 剔除优先级错配"),
    (10, "把握层次倒挂", "03!X = 最敢碰命中率 − 数据不足命中率", 0.10, "='03_期次汇总'!X4", "低", 0.05, "近 3 期", "「该赢 vs 真赢得」拆解失效"),
    (11, "平局低估扩大", "03!Y = 实际平局占比 − 平均预测平局概率", 0.00, "='03_期次汇总'!Y4", "高", 0.08, "近 5 期", "系统性低估平局，需加平局偏置"),
]
for i, (n, name, how, base, cur, direction, tol, window, attrib) in enumerate(SIGNALS):
    r = R0 + i
    put(ws, r, 1, n)
    put(ws, r, 2, name)
    put(ws, r, 3, how)
    put(ws, r, 4, base)
    put(ws, r, 5, cur, calc=True)
    put(ws, r, 6, direction)
    put(ws, r, 7, tol)
    put(ws, r, 8, f'=IF($E{r}="","数据未齐",IF(IF($F{r}="高",$E{r}>$D{r}+$G{r},$E{r}<$D{r}-$G{r}),"变差","正常"))', calc=True)
    put(ws, r, 9, window)
    put(ws, r, 10, attrib)
ws.conditional_formatting.add(f"H{R0}:H{R0+len(SIGNALS)-1}", FormulaRule(formula=[f'$H{R0}="变差"'], fill=PatternFill("solid", fgColor=C_RED)))
ws.conditional_formatting.add(f"H{R0}:H{R0+len(SIGNALS)-1}", FormulaRule(formula=[f'$H{R0}="正常"'], fill=PatternFill("solid", fgColor=C_GREEN)))
ws.conditional_formatting.add(f"H{R0}:H{R0+len(SIGNALS)-1}", FormulaRule(formula=[f'$H{R0}="数据未齐"'], fill=PatternFill("solid", fgColor=C_YELLOW)))

# ================= 05_变差总结归档 =================
ws = wb.create_sheet("05_变差总结归档")
H5 = ["期号", "生成日期", "有效场数", "变差信号数", "主要变差项", "归因分类",
      "纠正动作（下期生效）", "参数版本", "下期验证点", "未关闭项", "状态"]
W5 = [11, 14, 12, 12, 32, 26, 40, 14, 36, 32, 14]
banner(ws, "05 · 变差总结归档（由 reconcile.py --write-back 自动追加；不追溯修改本期）", len(H5))
header(ws, 3, H5, W5)
row5 = ["26167", "2026-11-21", 0, 0, "赛果未产生，暂不生成结论",
        "—", "—", "v26167（基线）", "开奖后回填 L/M 列，重跑引擎并核对 W/X/Y 三个倒挂差值",
        "停售前 22:00 二次定盘、临场首发、逐场天气；预测市场与主流算法模型未取到",
        "等待赛果录入"]
for c, v in enumerate(row5, 1):
    put(ws, R0, c, v, fill=C_INPUT)
for r in range(R0 + 1, R0 + 30):
    for c in range(1, len(H5) + 1):
        put(ws, r, c, None, fill=C_INPUT)

# ================= 06_反哺参数出口 =================
ws = wb.create_sheet("06_反哺参数出口")
H6 = ["参数名", "所属模块", "当前值", "建议值", "生效期号", "变更依据", "写回目标", "状态"]
W6 = [30, 16, 14, 14, 14, 40, 42, 16]
banner(ws, "06 · 反哺参数出口（默认待确认；人工确认参数版本后才写回分析预测）", len(H6))
header(ws, 3, H6, W6)
PARAMS = [
    ("海外主流媒体权重", "S1 共识", 0.14, "02 表建议权重", "足球预测共识分析框架.xlsx → 04_权重参数"),
    ("预测聚合权重", "S1 共识", 0.10, "02 表建议权重", "足球预测共识分析框架.xlsx → 04_权重参数"),
    ("预测市场权重", "S1 共识", 0.12, "缺席不降权", "足球预测共识分析框架.xlsx → 04_权重参数"),
    ("AI 模型权重", "S1 共识", 0.14, "02 表建议权重", "足球预测共识分析框架.xlsx → 04_权重参数"),
    ("统计模型权重", "S1 共识", 0.14, "02 表建议权重", "足球预测共识分析框架.xlsx → 04_权重参数"),
    ("算法增强权重", "S1 共识", 0.08, "缺席不降权", "足球预测共识分析框架.xlsx → 04_权重参数"),
    ("中文媒体与数据权重", "S1 共识", 0.10, "02 表建议权重", "足球预测共识分析框架.xlsx → 04_权重参数"),
    ("官方伤停情报权重", "S1 共识", 0.10, "02 表建议权重", "足球预测共识分析框架.xlsx → 04_权重参数"),
    ("价值阈值", "S2 判定", "+5%", "按实测回撤微调，单次 ≤ 1pp", "S2 共识汇总价值标签"),
    ("回避阈值", "S2 判定", "−5%", "按实测回撤微调，单次 ≤ 1pp", "S2 共识汇总回避标签"),
    ("完整度阈值", "S2 判定", "60%", "按低完整度场实测命中率复核", "S2 数据不足判定"),
    ("主胜校准偏置", "S1→S2 概率", 0.00, "指数平滑，单期 ≤ 0.03", "去水概率 → 共识输入"),
    ("平局校准偏置", "S1→S2 概率", 0.00, "信号 11 触发时上调", "去水概率 → 共识输入"),
    ("客胜校准偏置", "S1→S2 概率", 0.00, "指数平滑，单期 ≤ 0.03", "去水概率 → 共识输入"),
    ("高置信门槛", "S2 稳胆", 0.60, "按信号 7 复核", "S2 稳胆识别、S3 双胆选择"),
    ("任九剔除场数", "S3 结构", 5, "信号 9 倒挂时减 1 或重排", "S3 任选九场剔除优先级"),
    ("共振 / 分歧度阈值", "S1 共振表", "沿用框架", "按信号 8 复核", "S1 多维共振总表标记"),
    ("预算上限 / 单注", "S3 硬约束", "50 元 / 2 元", "恒定，不参与纠偏", "不写回（硬约束）"),
]
for i, (name, mod, cur, basis, target) in enumerate(PARAMS):
    r = R0 + i
    put(ws, r, 1, name)
    put(ws, r, 2, mod)
    put(ws, r, 3, cur)
    put(ws, r, 4, None, fill=C_INPUT)
    put(ws, r, 5, None, fill=C_INPUT)
    put(ws, r, 6, basis)
    put(ws, r, 7, target)
    put(ws, r, 8, "待确认", calc=False)

OUT.parent.mkdir(parents=True, exist_ok=True)
wb.save(OUT)
print("xlsx:", OUT)
print("sheets:", wb.sheetnames)
print("01 预置场次:", len(M), " 空行:", R1 - R0 - len(M) + 1)
