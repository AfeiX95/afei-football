# -*- coding: utf-8 -*-
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from docx import Document

doc = Document(r"I:\阿飞说球\📝文章\20260804\欧冠资格赛两场赛事前瞻.docx")
texts = []
bolds = 0
dash = 0
for p in doc.paragraphs:
    texts.append(p.text)
    for r in p.runs:
        if r.bold and r.text.strip(): bolds += 1
    dash += p.text.count("——") + p.text.count("—")
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            texts.append(c.text)
full = "\n".join(texts)

banned = ["赔率", "盘口", "庄家", "泊松", "蒙特卡洛", "EV", "凯利", "打穿", "竞彩官方", "购买合法体育彩票"]
anchor = ["今天", "明天", "昨天", "今晚", "今日", "明日", "昨夜"]

print("== 禁用词 ==")
hit = False
for w in banned:
    n = full.count(w)
    if n: print(f"  {w}: {n}"); hit = True
if not hit: print("  0 命中 ✅")
print("== 时间锚点 ==")
hit = False
for w in anchor:
    n = full.count(w)
    if n: print(f"  {w}: {n}"); hit = True
if not hit: print("  0 命中 ✅")
print(f"== 粗体段数: {bolds}（要求<=5，仅核心结论/关键句）")
print(f"== 破折号: {dash}（要求克制，每段<=2-3）")
print(f"== 总段落: {len(doc.paragraphs)} | 表格: {len(doc.tables)}")
