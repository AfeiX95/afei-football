# -*- coding: utf-8 -*-
"""
公众号深度版 md → Word(docx) 转换器 v2
======================================
用法: python md_to_docx.py <深度版.md> [输出.docx]
功能:
  - 一级标题(#): 居中大号蓝色
  - 二级标题(##): 左对齐蓝色粗体 14pt
  - 三级标题(###): 左对齐深蓝粗体 12pt
  - 标签行(#tag #tag): 灰色 10pt
  - 信息卡(【】): 浅蓝背景 + 粗体
  - 引用(>): 灰色斜体
  - 表格(|): 带边框, 表头深蓝底白字
  - 图片(![]): 相对路径解析嵌入
  - 行内加粗(**text**): 粗体
  - 行内高亮(<strong class="hl">text</strong>): 红色粗体(公众号排版高亮)
图片按 md 所在目录的相对路径解析并嵌入 Word
字体: 微软雅黑
"""
import os
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


def set_font(run, size=11, bold=False, color=None, italic=False):
    run.font.name = '微软雅黑'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)


def shade_cell(cell, hex_color):
    """给单元格/段落加背景色"""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.makeelement(qn('w:shd'), {qn('w:val'): 'clear', qn('w:fill'): hex_color})
    tc_pr.append(shd)


def shade_paragraph(p, hex_color):
    p_pr = p._p.get_or_add_pPr()
    shd = p_pr.makeelement(qn('w:shd'), {qn('w:val'): 'clear', qn('w:fill'): hex_color})
    p_pr.append(shd)


def add_runs_with_markup(p, text, size=11, base_color=None):
    """解析行内标记: **bold** 和 <strong class="hl">text</strong>"""
    # 先处理 <strong class="hl">...</strong> → 临时占位
    hl_re = re.compile(r'<strong class="hl">([^<]+)</strong>')
    tokens = []
    pos = 0
    for m in hl_re.finditer(text):
        if m.start() > pos:
            tokens.append(('n', text[pos:m.start()]))
        tokens.append(('hl', m.group(1)))
        pos = m.end()
    if pos < len(text):
        tokens.append(('n', text[pos:]))

    for kind, seg in tokens:
        # 段内再拆 **bold**
        if kind == 'hl':
            set_font(p.add_run(seg), size=size, bold=True, color=(0xD6, 0x27, 0x28))
            continue
        for part in re.split(r'(\*\*[^*]+\*\*)', seg):
            if not part:
                continue
            if part.startswith('**') and part.endswith('**'):
                set_font(p.add_run(part[2:-2]), size=size, bold=True,
                         color=base_color if base_color else (0x1B, 0x4B, 0x8C))
            else:
                set_font(p.add_run(part), size=size, color=base_color)


def md_to_docx(md_path, out_path):
    with open(md_path, encoding='utf-8') as f:
        lines = f.read().split('\n')

    md_dir = os.path.dirname(os.path.abspath(md_path))
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(11)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip()
        s = line.strip()

        # 跳过空行和 style 注释
        if not s or s.startswith('<!--'):
            i += 1
            continue

        # 一级标题
        if s.startswith('# ') and not s.startswith('## '):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_font(p.add_run(s[2:]), size=18, bold=True, color=(0x1B, 0x4B, 0x8C))
            i += 1
            continue

        # 二级标题
        if s.startswith('## ') and not s.startswith('### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            set_font(p.add_run(s[3:]), size=14, bold=True, color=(0x1B, 0x4B, 0x8C))
            i += 1
            continue

        # 三级标题
        if s.startswith('### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            set_font(p.add_run(s[4:]), size=12, bold=True, color=(0x2E, 0x6B, 0xB5))
            i += 1
            continue

        # 标签行: #tag #tag ... (多个以#开头的词, 空格分隔)
        if re.match(r'^#\S+(?:\s+#\S+)+$', s):
            p = doc.add_paragraph()
            set_font(p.add_run(s), size=10, color=(0x88, 0x88, 0x88))
            i += 1
            continue

        # 表格: 连续 | 行
        if s.startswith('|'):
            rows = []
            while i < n and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                rows.append(cells)
                i += 1
            if len(rows) >= 2:
                header, body = rows[0], [r for r in rows[1:] if not all(re.match(r'^:?-+:?$', c) for c in r)]
                t = doc.add_table(rows=1 + len(body), cols=len(header))
                t.style = 'Table Grid'
                for j, h in enumerate(header):
                    cell = t.cell(0, j)
                    shade_cell(cell, '1B4B8C')
                    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    set_font(cell.paragraphs[0].add_run(h), size=10, bold=True, color=(0xFF, 0xFF, 0xFF))
                for ri, row in enumerate(body):
                    for j, v in enumerate(row):
                        cell = t.cell(ri + 1, j)
                        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                        set_font(cell.paragraphs[0].add_run(v), size=10)
                doc.add_paragraph()
            continue

        # 图片
        m = re.match(r'!\[[^\]]*\]\((charts/[^)]+)\)', s)
        if m:
            img_rel = m.group(1)
            img_path = os.path.join(md_dir, img_rel)
            if os.path.exists(img_path):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.add_run().add_picture(img_path, width=Inches(5.4))
                if i + 1 < n and re.match(r'^\*图', lines[i + 1].strip()):
                    cap = doc.add_paragraph()
                    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    set_font(cap.add_run(lines[i + 1].strip().strip('*')), size=9,
                             color=(0x77, 0x77, 0x77))
                    i += 1
            i += 1
            continue

        # 引用(blockquote)
        if s.startswith('>'):
            p = doc.add_paragraph()
            shade_paragraph(p, 'F5F5F5')
            set_font(p.add_run(s.lstrip('> ')), size=10, color=(0x66, 0x66, 0x66), italic=True)
            i += 1
            continue

        # 信息卡【】行: 浅蓝背景 + 粗体
        if s.startswith('【') and '】' in s:
            p = doc.add_paragraph()
            shade_paragraph(p, 'E8F0FA')
            set_font(p.add_run(s), size=11, bold=True, color=(0x1B, 0x4B, 0x8C))
            i += 1
            continue

        # 普通段落
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.4
        add_runs_with_markup(p, s)
        i += 1

    doc.save(out_path)
    print(f'✅ DOCX → {out_path}')
    return out_path


if __name__ == '__main__':
    md_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(md_path)[0] + '.docx'
    md_to_docx(md_path, out_path)
