# -*- coding: utf-8 -*-
"""
check_publish.py — 兼容别名(2026-09-11 改造)
=============================================
原来这里是一份**硬编码绝对路径**的一次性脚本(写死
`D:/Hermes/football/阿飞说球/04_赛事文章/2026-09/马尔默vs索尔纳_深度/...`),
换个场次/换台机器就跑不动, 且检查逻辑与 `check_release.py` 重复。

现改为**薄壳**: 不再自己实现检查, 一律转发给唯一权威工具
`阿飞说球/02_工具/check_release.py`, 避免两套词表各自漂移。

用法(项目根):
    python check_publish.py --docx "阿飞说球/04_赛事文章/2026-09/xx/xx_赛事前瞻.docx"
    python check_publish.py --docx <docx> --config "阿飞说球/02_工具/match_configs/xx.json"

说明: 头条稿(合规终检) = docx 走 check_release.py;
      公众号深度版(md) = 走 `check_md_release.py`(检查项不同, 不是本文覆盖范围)。
"""
import os
import subprocess
import sys

TOOL = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '阿飞说球', '02_工具', 'check_release.py'))


def main():
    if not os.path.exists(TOOL):
        print(f'❌ 找不到权威检查工具: {TOOL}')
        return 2
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = [sys.executable, TOOL] + sys.argv[1:]
    print(f'→ 转发到 {os.path.relpath(TOOL)} {" ".join(sys.argv[1:])}\n')
    return subprocess.call(cmd)


if __name__ == '__main__':
    sys.exit(main())
