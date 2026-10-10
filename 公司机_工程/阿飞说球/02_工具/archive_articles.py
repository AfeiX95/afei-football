# -*- coding: utf-8 -*-
"""
archive_articles.py — 文章按产出月份归档 (可重复执行)
======================================================
映射表依据: 文章正文比赛日期(前瞻写于赛前) / 文件名日期。
mtime 不可靠(均为批量复制时间), 故手工维护映射。
用法: python archive_articles.py
"""
import os
import shutil
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 阿飞说球/
ART = os.path.join(BASE, '04_赛事文章')

# 场次目录名 → 产出月份 (YYYY-MM)
MAP = {
    '巴西vs日本': '2026-06',          # 正文: 6月30日
    '7月4日_三场串烧_水浒传': '2026-07',
    '7月4日_三场连台_赛博聊球': '2026-07',
    '阿根廷vs佛得角': '2026-07',      # 与7月4日串烧同场次
    '澳大利亚vs埃及': '2026-07',      # 同上(空目录占位)
    '哥伦比亚vs加纳': '2026-07',      # 同上(空目录占位)
    '西班牙vs比利时': '2026-07',      # 正文: 7月11日
    '塞萨洛vs安德莱': '2026-08',
    '大阪钢巴vs浦和红钻': '2026-08',
    '库奥皮奥vs克拉约瓦': '2026-08',
    '弗鲁米嫩塞vs瓦斯科达伽马': '2026-08',
    '日职揭幕战双场串烧': '2026-08',
    '本菲卡vs哈茨': '2026-08',
    '横滨水手vs鹿岛鹿角': '2026-08',
    '比亚韦vs流浪者': '2026-08',
    '维多利亚vs巴竞技': '2026-08',
}


def main():
    moved, missed = [], []
    for name in sorted(os.listdir(ART)):
        p = os.path.join(ART, name)
        if not os.path.isdir(p) or name.startswith('.'):
            continue
        month = MAP.get(name)
        if not month:
            missed.append(name)
            continue
        dst_dir = os.path.join(ART, month)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, name)
        if os.path.exists(dst):
            print(f'⚠ 目标已存在, 跳过: {dst}')
            missed.append(name)
            continue
        shutil.move(p, dst)
        moved.append((name, month))

    print(f'✔ 归档 {len(moved)} 个目录 → 04_赛事文章/<YYYY-MM>/')
    for name, m in moved:
        print(f'   {m}/{name}')
    if missed:
        print(f'⚠ 未归档 {len(missed)}: {missed}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
