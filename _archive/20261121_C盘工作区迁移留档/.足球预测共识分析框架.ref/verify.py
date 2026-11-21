# -*- coding: utf-8 -*-
"""校验：公式文本合法、全部公式有缓存值、无 Excel 错误值、结构完整。"""
import json
import openpyxl

PATH = r"C:\Users\wuyan\WorkBuddy\2026-11-20-21-07-35\足球预测共识分析框架.xlsx"
ERRS = ("#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A")

wf = openpyxl.load_workbook(PATH, data_only=False)
wv = openpyxl.load_workbook(PATH, data_only=True)
total, missing, bad, per_sheet = 0, [], [], {}
for ws in wf.worksheets:
    wsv = wv[ws.title]
    n = 0
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith("="):
                n += 1
                total += 1
                v = wsv[c.coordinate].value
                if v is None:
                    missing.append([ws.title, c.coordinate, c.value[:90]])
                elif isinstance(v, str) and any(e in v for e in ERRS):
                    bad.append([ws.title, c.coordinate, "cached", str(v)[:60]])
                if any(e in c.value for e in ERRS):
                    bad.append([ws.title, c.coordinate, "formula", c.value[:90]])
    per_sheet[ws.title] = n

samples = {
    "说明_已填比赛数": wv["00_使用说明"]["B5"].value,
    "说明_高共识场次": wv["00_使用说明"]["B8"].value,
    "说明_价值场次": wv["00_使用说明"]["B9"].value,
    "欧赔_水位合计(第1场)": wv["02_外盘欧赔"]["P4"].value,
    "来源_概率和(第1行)": wv["03_来源预测"]["F4"].value,
    "来源_权重(第1行)": wv["03_来源预测"]["J4"].value,
    "汇总_共识主胜(第1场)": wv["05_共识汇总"]["H4"].value,
    "汇总_自动摘要(第1场)": wv["05_共识汇总"]["V4"].value,
    "参数_权重合计": wv["04_权重参数"]["C14"].value,
}
out = {
    "sheets": wf.sheetnames,
    "total_formulas": total,
    "formulas_per_sheet": per_sheet,
    "missing_cached_values": len(missing),
    "error_cells": len(bad),
    "missing_sample": missing[:5],
    "error_sample": bad[:5],
    "samples": samples,
    "merged_ranges": {ws.title: len(ws.merged_cells.ranges) for ws in wf.worksheets},
    "status": "pass" if not missing and not bad else "fail",
}
print(json.dumps(out, ensure_ascii=False, indent=2))
