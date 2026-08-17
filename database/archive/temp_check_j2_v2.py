# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from docx import Document

path = r"I:\阿飞说球\📝文章\20260807\日职揭幕两场赛事前瞻_干货版.docx"
doc = Document(path)

texts = []
for p in doc.paragraphs:
    texts.append(p.text)
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            texts.append(c.text)
full = "\n".join(texts)

banned = ["赔率", "盘口", "庄家", "泊松", "蒙特卡洛", "EV", "凯利", "赢盘率"]
anchors = ["今天", "明天", "昨天", "今晚", "明日", "昨日", "今晚"]

print("== 禁用词 ==")
for w in banned:
    n = full.count(w)
    if n: print(f"  {w}: {n}")
print("禁用词总数:", sum(full.count(w) for w in banned))

print("== 时间锚点 ==")
for w in anchors:
    n = full.count(w)
    if n: print(f"  {w}: {n}")
print("锚点总数:", sum(full.count(w) for w in anchors))

print("== 粗体段 ==")
b = sum(1 for p in doc.paragraphs if any(r.bold for r in p.runs))
print("正文粗体段落:", b)

print("== 破折号 ==")
print("破折号数:", full.count("—"))

print("== 表格 ==")
print("表格数:", len(doc.tables))

print("== 段落/字数 ==")
print("段落数:", len(doc.paragraphs), "| 总字数:", len(full.replace("\n","")))

print("== 图片 ==")
import zipfile
z = zipfile.ZipFile(path)
imgs = [n for n in z.namelist() if n.startswith("word/media/")]
print("图片数:", len(imgs))
