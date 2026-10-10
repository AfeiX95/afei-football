# -*- coding: utf-8 -*-
"""
头条 md 生成器(2026-09-16 起: 头条不再出 docx、不再配图, 图表数据一律改表格)

用法: 复制本文件改 CFGS/表格, 或 import 后调用 write_md()
模板来源: multi_preview_wed123 的文案 + 三张图的数据(偏差/交锋/攻防)全部表格化
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(BASE, '阿飞说球', '02_工具')
sys.path.insert(0, TOOL)

FOOTER = ['【数据来源】竞彩官方(sporttery.cn)及公开数据库,阿飞模型推演。',
          '【免责声明】本文为个人数据模型推演,属赛事分析交流,不构成购彩及投注建议。']


def bar(v, base=100):
    """数据条: 把百分比画成方块条(替代柱状图)"""
    n = max(1, int(round(v / base * 20)))
    return '█' * n


def write_md(path, title, tags, info_card, opening, blocks, tables, summary, hook):
    """blocks: [(小节标题, [段落...]), ...]; tables: [(标题, 表头list, 行list)]"""
    out = [title, '', tags, '']
    out += info_card + ['']
    out += [opening, '']
    for tname, head, rows in tables[:1]:
        out += [f'**{tname}**', '',
                '| ' + ' | '.join(head) + ' |',
                '|' + '|'.join(['---'] * len(head)) + '|']
        out += ['| ' + ' | '.join(r) + ' |' for r in rows]
        out += ['']
    for tname, head, rows in tables[1:]:
        out += [f'**{tname}**', '',
                '| ' + ' | '.join(head) + ' |',
                '|' + '|'.join(['---'] * len(head)) + '|']
        out += ['| ' + ' | '.join(r) + ' |' for r in rows]
        out += ['']
    out += ['---', '']
    for h2, paras in blocks:
        out += [f'## {h2}', '']
        for p in paras:
            out += [p, '']
        out += ['---', '']
    out += [summary, '', hook, '']
    out += FOOTER
    io.open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    return path
