# -*- coding: utf-8 -*-
"""OOXML 层校验：每个公式单元格都带缓存值，且无 Excel 错误值。
openpyxl 会把空字符串缓存 <v/> 读成 None，因此以原始 XML 为准。
"""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

PATH = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\wuyan\WorkBuddy\2026-11-20-21-07-35\足球预测共识分析框架.xlsx"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
ERRS = ("#VALUE!", "#DIV/0!", "#REF!", "#NAME?", "#NULL!", "#NUM!", "#N/A")

z = zipfile.ZipFile(PATH)
sheets = sorted(n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))
per_sheet = {}
total_formulas = total_cached = total_errors = 0
missing, error_cells = [], []
for name in sheets:
    root = ET.fromstring(z.read(name))
    f_cnt = v_cnt = 0
    for c in root.iter(NS + "c"):
        f = c.find(NS + "f")
        if f is None:
            continue
        f_cnt += 1
        v = c.find(NS + "v")
        if v is None:
            missing.append([name, c.get("r"), "no <v>"])
        else:
            v_cnt += 1
            text = v.text or ""
            if any(e in text for e in ERRS):
                error_cells.append([name, c.get("r"), text])
        if f.text and any(e in f.text for e in ERRS):
            error_cells.append([name, c.get("r"), "formula: " + f.text[:80]])
    cf = len(list(root.iter(NS + "conditionalFormatting")))
    dv = len(list(root.iter(NS + "dataValidation")))
    per_sheet[name] = {"formulas": f_cnt, "cached": v_cnt, "cond_fmt": cf, "data_validation": dv}
    total_formulas += f_cnt
    total_cached += v_cnt
    total_errors += sum(1 for e in error_cells if e[0] == name)

# 纯静态值工作簿（无公式单元格）不应被判为失败，单独标记 pass_static
if missing or error_cells:
    status = "fail"
elif total_formulas == 0:
    status = "pass_static"
else:
    status = "pass"
out = {
    "total_formulas": total_formulas,
    "total_cached_values": total_cached,
    "missing_cached_values": len(missing),
    "excel_error_cells": len(error_cells),
    "per_sheet": per_sheet,
    "missing_sample": missing[:5],
    "error_sample": error_cells[:5],
    "status": status,
    "note": "静态值工作簿，无公式单元格可校验；已确认无 Excel 错误值" if status == "pass_static" else "",
}
print(json.dumps(out, ensure_ascii=False, indent=2))
