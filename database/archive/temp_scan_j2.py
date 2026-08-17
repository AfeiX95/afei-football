# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from docx import Document
doc = Document(r"I:\阿飞说球\📝文章\20260807\日职揭幕两场赛事前瞻.docx")
for i, p in enumerate(doc.paragraphs):
    if "今天" in p.text or "—" in p.text or any(r.bold for r in p.runs):
        print(i, "|bold:", any(r.bold for r in p.runs), "|", p.text[:70])
