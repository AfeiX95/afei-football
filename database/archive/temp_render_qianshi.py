# -*- coding: utf-8 -*-
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32com.client

SRC = r"I:\阿飞说球\📝文章\20260804\欧冠资格赛两场赛事前瞻.docx"
PDF = r"I:\阿飞说球\📝文章\20260804\欧冠资格赛两场赛事前瞻_preview.pdf"

app = win32com.client.Dispatch("Word.Application")
app.Visible = False
doc = app.Documents.Open(SRC, ReadOnly=True)
doc.SaveAs(PDF, FileFormat=17)  # 17 = wdFormatPDF
doc.Close(False)
app.Quit()
print("pdf saved:", os.path.exists(PDF), os.path.getsize(PDF) if os.path.exists(PDF) else "")
