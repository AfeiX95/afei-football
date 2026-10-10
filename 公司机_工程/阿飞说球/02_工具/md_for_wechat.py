# -*- coding: utf-8 -*-
"""
md_for_wechat.py — 头条 md → 微信公众号排版导入版
用法: python md_for_wechat.py <源md路径> <输出md路径>
处理:
  1. 本地图片相对路径 → 绝对路径(墨滴导入可识别本地图)
  2. ——分隔行 → 空行(微信编辑器里显示为生硬横线)
  3. 标签行(#xxx)保留在顶部(公众号摘要用)
  4. 【】信息卡保留(微信正文模块化格式)
"""
import os
import re
import sys


def convert(src, dst):
    with open(src, encoding='utf-8') as f:
        text = f.read()

    base = os.path.dirname(os.path.abspath(src))

    # 1. 本地图片路径 → 绝对路径
    def fix_img(m):
        alt, path = m.group(1), m.group(2)
        if not os.path.isabs(path):
            abs_path = os.path.join(base, path)
            if os.path.exists(abs_path):
                return f'![{alt}]({abs_path})'
        return m.group(0)

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_img, text)

    # 2. 独立成行的 —— → 空行(微信里渲染成生硬横线, 不如空行干净)
    text = re.sub(r'\n——\n', '\n', text)

    # 3. 图注斜体行统一格式
    text = re.sub(r'^\*(图\d+[^\*]*)\*$', r'▸ \1', text, flags=re.MULTILINE)

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(text)

    imgs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)
    abs_ok = sum(1 for p in imgs if os.path.isabs(p))
    print(f'✅ {os.path.basename(dst)}')
    print(f'   图片 {len(imgs)} 张(绝对路径 {abs_ok} 张)')
    print(f'   ——分隔行已清除')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法: python md_for_wechat.py <源md> <输出md>')
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])