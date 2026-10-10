# -*- coding: utf-8 -*-
"""把赛照嵌入生成后的 docx(锚点段后插入,宽度5.6in 与图表一致)。
用法: python insert_photos.py <docx路径> [--photos "monza_1.jpg:锚点文本,monza_2.jpg:锚点文本,..."]"""
import sys, os
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

def to_std_jpeg(img):
    """非标准 JPEG(如 WEBP 伪装 .jpg)转标准 JPEG,返回可插入路径。"""
    from PIL import Image
    try:
        im = Image.open(img)
        if im.format != 'JPEG':
            out = img.rsplit('.', 1)[0] + '_std.jpg'
            im.convert('RGB').save(out, 'JPEG', quality=92)
            return out
    except Exception:
        pass
    return img

def insert_photos(docx_path, plan):
    doc = Document(docx_path)
    paras = doc.paragraphs
    # 找锚点段对象(按文本前缀匹配)
    anchors = {}
    for p in paras:
        t = p.text.strip()
        for key, (img, anchor_txt) in plan.items():
            if key not in anchors and t.startswith(anchor_txt):
                anchors[key] = p
    for key, (img, anchor_txt) in plan.items():
        if key not in anchors:
            print(f'  ⚠ 锚点未找到: "{anchor_txt}" (跳过 {os.path.basename(img)})')
            continue
        img = to_std_jpeg(img)
        # 在文档末尾创建图片段
        pic_p = doc.add_paragraph()
        pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = pic_p.add_run()
        run.add_picture(img, width=Inches(5.6))
        # 加图片说明
        cap_p = doc.add_paragraph()
        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = cap_p.add_run('▲ 官方赛照(球队官网图库)。')
        cap.font.size = __import__('docx.shared', fromlist=['Pt']).Pt(9)
        # 移动: 锚点段之后插入 图片段+说明段
        anchor_el = anchors[key]._p
        anchor_el.addnext(cap_p._p)
        anchor_el.addnext(pic_p._p)
        print(f'  ✓ {os.path.basename(img)} → 锚点 "{anchor_txt}"')
    doc.save(docx_path)
    print('已保存:', docx_path)

if __name__ == '__main__':
    d = sys.argv[1]
    photos_dir = os.path.join(os.path.dirname(d), 'photos')
    plan = {
        'p1': (os.path.join(photos_dir, 'inter_1.jpg'), '第一幕【背景】'),
        'p2': (os.path.join(photos_dir, 'monza_1.jpg'), '近7次交锋'),
        'p3': (os.path.join(photos_dir, 'monza_2.jpg'), '关键球员对位'),
        'p4': (os.path.join(photos_dir, 'monza_3.jpg'), '第三幕【结局】'),
    }
    insert_photos(d, plan)
