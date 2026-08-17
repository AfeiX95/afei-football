# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32com.client

docx_path = os.path.abspath(r"📝文章/20260807/日职揭幕两场赛事前瞻.docx")
pdf_path = os.path.abspath(r"📝文章/20260807/日职揭幕两场赛事前瞻_preview.pdf")
if os.path.exists(pdf_path):
    os.remove(pdf_path)
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
try:
    doc = word.Documents.Open(docx_path)
    doc.SaveAs(pdf_path, FileFormat=17)
    doc.Close(False)
finally:
    word.Quit()
print("pdf saved:", pdf_path, os.path.getsize(pdf_path))
