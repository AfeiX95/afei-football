# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
import re, os

doc = Document()

# Set default font
style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(11)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

# Read MD file
md_path = r'I:\阿飞说球\📝文章\20260731\挪超两场前瞻_瓦勒伦加汉坎_博德闪耀利勒斯特_头条版_final.md'
with open(md_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

def add_colored_text(paragraph, text, color=None, bold=False, size=None):
    run = paragraph.add_run(text)
    if color:
        run.font.color.rgb = color
    if bold:
        run.bold = True
    if size:
        run.font.size = size
    return run

def parse_inline(paragraph, text):
    """Parse inline markdown formatting like **bold**"""
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            inner = part[2:-2]
            run = paragraph.add_run(inner)
            run.bold = True
        else:
            if part:
                paragraph.add_run(part)

def add_table(doc, header, rows):
    """Add a formatted table"""
    table = doc.add_table(rows=1 + len(rows), cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Style table
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else tbl._add_tblPr()
    
    # Header row
    for i, h in enumerate(header):
        cell = table.rows[0].cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        # Dark blue background
        shading = cell._element.get_or_add_tcPr()
        shading_elm = shading.makeelement(qn('w:shd'), {
            qn('w:fill'): '1e3a5f',
            qn('w:val'): 'clear'
        })
        shading.append(shading_elm)
    
    # Data rows
    for r_idx, row in enumerate(rows):
        bg = '16213e' if r_idx % 2 == 0 else '1a1a2e'
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = ''
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            parse_inline(p, val)
            for run in p.runs:
                run.font.size = Pt(10)
            # Background
            shading = cell._element.get_or_add_tcPr()
            shading_elm = shading.makeelement(qn('w:shd'), {
                qn('w:fill'): bg,
                qn('w:val'): 'clear'
            })
            shading.append(shading_elm)
    
    doc.add_paragraph()  # spacing

# Process lines
i = 0
while i < len(lines):
    line = lines[i].strip()
    
    # Skip empty lines
    if not line:
        i += 1
        continue
    
    # Title (h1)
    if line.startswith('# ') and not line.startswith('##') and not line.startswith('#'):
        # Check if it's the main title or a tag line
        if '挪超' in line or '模型' in line:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(line[2:])
            run.bold = True
            run.font.size = Pt(16)
            run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)
            i += 1
            continue
    
    # Tag line
    if line.startswith('#挪超') or line.startswith('#欧罗巴'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
        i += 1
        continue
    
    # Divider
    if line == '---':
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run('─' * 40)
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0xdd, 0xdd, 0xdd)
        i += 1
        continue
    
    # Quote line (金句)
    if '数据不会说谎' in line:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(line)
        run.italic = True
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        i += 1
        continue
    
    # H3 headers
    if line.startswith('### '):
        text = line[4:]
        # Remove emoji prefixes for cleaner doc
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(13)
        run.font.color.rgb = RGBColor(0x4f, 0xc3, 0xf7)
        i += 1
        continue
    
    # H2 headers
    if line.startswith('## '):
        text = line[3:]
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(15)
        run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)
        i += 1
        continue
    
    # Table detection
    if '|' in line and line.startswith('|'):
        table_lines = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            table_lines.append(lines[i].strip())
            i += 1
        
        if len(table_lines) >= 2:
            # Parse header
            header = [c.strip() for c in table_lines[0].split('|')[1:-1]]
            # Skip separator line
            rows = []
            for tl in table_lines[2:]:
                row = [c.strip() for c in tl.split('|')[1:-1]]
                if row:
                    rows.append(row)
            add_table(doc, header, rows)
        continue
    
    # Blockquote
    if line.startswith('> '):
        text = line[2:]
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        run = p.add_run(text)
        run.italic = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
        i += 1
        continue
    
    # Image keywords (numbered lines)
    if re.match(r'^\d+-', line):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
        i += 1
        continue
    
    # Disclaimer / Data source
    if '【免责声明】' in line or '【数据来源】' in line:
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
        i += 1
        continue
    
    # Regular paragraph with potential inline formatting
    p = doc.add_paragraph()
    parse_inline(p, line)
    for run in p.runs:
        if not run.font.size:
            run.font.size = Pt(11)
    i += 1

# Save
output_path = r'I:\阿飞说球\📝文章\20260731\挪超两场前瞻_瓦勒伦加汉坎_博德闪耀利勒斯特_头条版_final.docx'
doc.save(output_path)
print('Word document saved')
print('Done')

