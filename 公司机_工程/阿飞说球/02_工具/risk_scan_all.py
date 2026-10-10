# -*- coding: utf-8 -*-
"""历史成稿平台风险自查 v2(2026-09-15)

v1 把内部工作稿(模型分析/数据处理/选场分析/复盘)也算进去了, 噪音大。
v2 先分"发布稿 / 工作稿", 只对发布稿出下架整改清单, 并打印具体触线词。
"""
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, '阿飞说球', '02_工具'))
from risk_scan import A, B1_FRAME, B2_JUDGE, C, D, clean  # noqa: E402

# 2026-09-21 修复: risk_scan.py 已把旧 B 拆成 B1_FRAME(投注推荐框架, 两平台硬性失败)
# 与 B2_JUDGE(主观判断词, 仅公众号硬性); 本脚本做历史稿打分, 合并两者以保持原语义。
B = B1_FRAME + B2_JUDGE

ART = os.path.join(BASE, '阿飞说球', '04_赛事文章')
WORK_MARK = ('模型分析', '数据处理', '选场分析', '复盘', '审查', '简报', '数据来源', '口径', '他方')
PUB_MARK = ('公众号', '深度版', '赛事前瞻', '头条', '串烧', '发布')


def kind(path):
    n = os.path.basename(path)
    if any(m in n for m in WORK_MARK):
        return '工作稿'
    return '发布稿'


def scan(path):
    t = io.open(path, encoding='utf-8', errors='ignore').read()
    body = clean(t.split('## 勿发布')[0])
    hitA = [w for w in A if w in body]
    hitB = [w for w in B if w in body]
    c = sum(body.count(w) for w in C)
    combo = len(re.findall(r'\d+[:：]\d+\(\d+\.\d+\)', body))
    risk = len(hitA) * 40 + combo * 3 + len(hitB) * 4 + min(c, 40) * 0.5
    return dict(path=path, A=hitA, B=hitB, C=c, combo=combo, risk=risk,
                zh=sum(1 for ch in body if '\u4e00' <= ch <= '\u9fff'))


rows = []
for root, _, files in os.walk(ART):
    for f in files:
        if f.endswith('.md'):
            rows.append(scan(os.path.join(root, f)))

pub = sorted([r for r in rows if kind(r['path']) == '发布稿'], key=lambda r: -r['risk'])
work = sorted([r for r in rows if kind(r['path']) == '工作稿'], key=lambda r: -r['risk'])

print('发布稿 %d 篇 / 工作稿 %d 篇' % (len(pub), len(work)))
print()
print('=========== 发布稿: 风险排序(前 18) ===========')
for r in pub[:18]:
    print('%-52s A%-12s B%-16s C%-4d 比分组合%-3d 风险%.0f' % (
        os.path.relpath(r['path'], ART)[:50],
        ','.join(r['A'])[:10] or '-', ','.join(r['B'])[:14] or '-', r['C'], r['combo'], r['risk']))
print()
print('=========== 发布稿里 A 级词命中(必须处理) ===========')
for r in pub:
    if r['A']:
        print('  %-50s → %s' % (os.path.relpath(r['path'], ART)[:48], ','.join(r['A'])))
print()
print('=========== 发布稿里"清单形态"(比分+奖金 >=3 处) ===========')
for r in pub:
    if r['combo'] >= 3:
        print('  %-50s → %d 处' % (os.path.relpath(r['path'], ART)[:48], r['combo']))
