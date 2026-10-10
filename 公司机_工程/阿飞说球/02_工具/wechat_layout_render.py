# -*- coding: utf-8 -*-
"""
公众号排版风格池渲染器 — 把深度版 md 渲染成 4 套风格的 HTML 预览
用法: python wechat_layout_render.py [md路径]
默认: 04_赛事文章/2026-08/巴黎圣曼vs维拉/公众号_深度版.md
输出: wechat_layout/preview_A.html ... preview_D.html (浏览器打开看效果)
"""
import os
import re
import sys

import markdown

BASE = os.path.dirname(os.path.abspath(__file__))          # 02_工具/
LAYOUT = os.path.join(BASE, 'wechat_layout')                # 排版池目录
STYLE_FILES = {
    'A': 'style_A_data_blue.css',
    'B': 'style_B_derby_red.css',
    'C': 'style_C_warm_orange.css',
    'D': 'style_D_pine_green.css',
}
STYLE_NAMES = {
    'A': '数据蓝 · 理性专业',
    'B': '对决红 · 恩怨热血',
    'C': '暖橙 · 叙事温度',
    'D': '墨绿 · 沉稳复盘',
}

def main():
    md_path = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(
        os.path.join(BASE, '..', '04_赛事文章', '2026-08',
                     '巴黎圣曼vs维拉', '公众号_深度版.md'))
    with open(md_path, encoding='utf-8') as f:
        md_text = f.read()

    # 去掉 Illustration Suggestions 附录(不发布)
    md_text = md_text.split('=== Illustration Suggestions ===')[0]

    # 信息卡【】行转成 blockquote.info(视觉统一), 跳过标题行/标签行
    lines = []
    for ln in md_text.split('\n'):
        if re.match(r'^【(对阵|赛事|时间|场地|天气)】', ln.strip()):
            lines.append(f'> {ln.strip()}')
        else:
            lines.append(ln)
    md_text = '\n'.join(lines)

    # 数据段高亮标记: 模型数字行(含%的段落)首句加 ** **
    # (简单处理: 把 "模型" 与 "市场" 对比行中的关键数字加粗由人工决定, 这里仅渲染)

    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])

    # 图片路径修正: md 内相对路径(如 charts/xxx.png) → 相对 md 文件所在目录的绝对路径,
    # 保证 4 套预览 HTML 能直接显示图片(发布时用墨滴/壹伴导入 md 仍走相对路径+手动插图)
    md_dir = os.path.dirname(os.path.abspath(md_path))
    html_body = re.sub(r'src="(charts/[^"]+)"',
                       lambda m: f'src="file:///{os.path.join(md_dir, m.group(1)).replace(chr(92), "/")}"',
                       html_body)

    for key, css_fn in STYLE_FILES.items():
        with open(os.path.join(LAYOUT, css_fn), encoding='utf-8') as f:
            css = f.read()
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>预览 {key} · {STYLE_NAMES[key]}</title>
<style>
/* 模拟微信 375px 手机容器 */
body {{ background: #E8E8E8; margin: 0; padding: 20px 0; }}
.phone {{ max-width: 375px; margin: 0 auto; background: #fff; border-radius: 12px;
         box-shadow: 0 4px 20px rgba(0,0,0,0.15); overflow: hidden; }}
.phone-bar {{ background: #2C2C2C; color: #fff; font-size: 12px; padding: 8px 14px;
             display: flex; justify-content: space-between; }}
#content {{ padding: 18px 16px 30px; }}
{css}
</style>
</head>
<body>
<div class="phone">
  <div class="phone-bar"><span>公众号预览</span><span>{key} · {STYLE_NAMES[key]}</span></div>
  <div id="content">
{html_body}
  </div>
</div>
</body>
</html>"""
        out = os.path.join(LAYOUT, f'preview_{key}.html')
        with open(out, 'w', encoding='utf-8') as f:
            f.write(html)
        print('✔', out)

if __name__ == '__main__':
    main()
