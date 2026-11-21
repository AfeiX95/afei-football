# -*- coding: utf-8 -*-
"""由空模板脚本派生出「周六赛程_分析底表.xlsx」：预置 22 场对阵，公式扩展至 22 场 × 10 来源。"""
from pathlib import Path

BASE = Path(r"C:\Users\wuyan\WorkBuddy\2026-11-20-21-07-35")
ORIG = BASE / ".足球预测共识分析框架.ref" / "build.py"
NEW = BASE / ".足球预测共识分析框架.ref" / "build_saturday.py"

s = ORIG.read_text(encoding="utf-8")

s = s.replace(
    r'OUT = r"C:\Users\wuyan\WorkBuddy\2026-11-20-21-07-35\足球预测共识分析框架.xlsx"',
    r'OUT = r"C:\Users\wuyan\WorkBuddy\2026-11-20-21-07-35\周六赛程_分析底表.xlsx"')
s = s.replace('TITLE = "足球预测共识分析框架"', 'TITLE = "周六赛程分析底表 261121"')
s = s.replace("N_MATCH = 5\n", "N_MATCH = 22\n")
s = s.replace(
    "from openpyxl.utils import get_column_letter, column_index_from_string",
    "from openpyxl.utils import get_column_letter, column_index_from_string\nfrom datetime import date")

MATCHES_CODE = '''
MATCHES = [
    (date(2026, 11, 21), "日职", "广岛三箭", "横滨水手", "13:00"),
    (date(2026, 11, 21), "日乙", "磐田喜悦", "大宫松鼠RB", "13:00"),
    (date(2026, 11, 21), "日职", "大阪钢巴", "冈山绿雉", "15:00"),
    (date(2026, 11, 21), "澳超", "布里斯班狮吼", "悉尼FC", "16:40"),
    (date(2026, 11, 21), "英超", "曼彻斯特城", "富勒姆", "20:30"),
    (date(2026, 11, 21), "英冠", "米尔沃尔", "女王公园巡游者", "20:30"),
    (date(2026, 11, 21), "意甲", "科莫", "卡利亚里", "22:00"),
    (date(2026, 11, 21), "德甲", "门兴格拉德巴赫", "多特蒙德", "22:30"),
    (date(2026, 11, 21), "德甲", "埃尔沃斯堡", "弗赖堡", "22:30"),
    (date(2026, 11, 21), "德甲", "法兰克福", "霍芬海姆", "22:30"),
    (date(2026, 11, 21), "德甲", "柏林联合", "莱比锡红牛", "22:30"),
    (date(2026, 11, 21), "英超", "伯恩茅斯", "诺丁汉森林", "23:00"),
    (date(2026, 11, 21), "英超", "托特纳姆热刺", "伊普斯维奇", "23:00"),
    (date(2026, 11, 21), "英超", "阿斯顿维拉", "桑德兰", "23:00"),
    (date(2026, 11, 21), "英超", "考文垂", "水晶宫", "23:00"),
    (date(2026, 11, 21), "英超", "切尔西", "利兹联", "23:00"),
    (date(2026, 11, 21), "荷甲", "奈梅亨", "PSV埃因霍温", "23:30"),
    (date(2026, 11, 22), "意甲", "帕尔马", "罗马", "01:00"),
    (date(2026, 11, 22), "英超", "纽卡斯尔联", "阿森纳", "01:30"),
    (date(2026, 11, 22), "德甲", "沙尔克04", "斯图加特", "01:30"),
    (date(2026, 11, 22), "西甲", "塞维利亚", "皇家贝蒂斯", "01:30"),
    (date(2026, 11, 22), "法甲", "摩纳哥", "欧塞尔", "03:45"),
]
'''
s = s.replace("N_MATCH = 22\n", "N_MATCH = 22\n" + MATCHES_CODE, 1)

NEEDLE = '''    for col in range(2, 7):
        c = ws.cell(r, col)
        body(c, "input", "yyyy-mm-dd" if col == 2 else None, wrap=(col == 6))
'''
FILL = NEEDLE + '''    d = MATCHES[r - ROW_START]
    ws.cell(r, 2, d[0])
    ws.cell(r, 3, d[1])
    ws.cell(r, 4, d[2])
    ws.cell(r, 5, d[3])
    ws.cell(r, 6, f"竞彩周六{r - ROW_START + 1:03d} ｜ 开赛 {d[4]} ｜ 开售状态以官方页面为准")
'''
assert NEEDLE in s, "清单循环锚点未找到"
s = s.replace(NEEDLE, FILL, 1)

s = s.replace(
    "版本 v1.0 ｜ 生成日期 2026-11-20 ｜ 本工作簿为空模板，不含任何真实比赛、赔率或预测数据；所有黄色以外的空白输入格等待填写。",
    "周六赛程底表 v1.0 ｜ 生成日期 2026-11-21 ｜ 已预置竞彩周六（编号日期 261121）22 场对阵；赔率、情报与外部预测仍为空，等待 S1 补齐。")
s = s.replace(
    'f"当前预留 {N_MATCH} 场比赛（每场 {N_SRC} 个来源）。需要更多场次时，在三个录入表末尾整行插入并下拉复制公式，或直接告诉我按实际场次数重新生成。"',
    'f"本底表已预置 {N_MATCH} 场周六赛程，每场 {N_SRC} 个来源、共 {N_MATCH * N_SRC} 行录入位。增减场次时在三个录入表末尾整行插入/删除并同步公式，或直接告诉我按实际场次数重新生成。"')
s = s.replace(
    'wb.properties.subject = "外盘欧赔与多来源预测共识分析框架（空模板）"',
    'wb.properties.subject = "周六赛程分析底表（22 场对阵已预置）"')
s = s.replace(
    'wb.properties.description = "不含任何真实比赛、赔率或预测数据；仅含结构、公式与判定规则。"',
    'wb.properties.description = "已预置 2026-11-21 竞彩周六 22 场真实对阵；赔率与预测数据待补齐。"')

NEW.write_text(s, encoding="utf-8")
print("generated:", NEW)
print("checks:", "N_MATCH = 22" in s, "MATCHES = [" in s, "周六赛程_分析底表" in s)
