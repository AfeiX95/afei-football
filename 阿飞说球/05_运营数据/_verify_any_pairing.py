# -*- coding: utf-8 -*-
"""验证「任意一处真实队名对位即通过」规则, 并回归 262 篇"""
import io
import os
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '02_工具')))
from check_md_release import has_team_vs, find_team_vs, TITLE_MAX_TOUTIAO

print('=== 1. 任意一处通过 (本次修复的核心) ===')
cases = [
    ('7月26日 韩K联 模型vs市场 蔚山vs全北', True, '第一处假阳性, 第二处真队名 -> 应通过'),
    ('周四 模型vs市场 罗马vs国米', True, '同上'),
    ('7月26日 韩K联第20轮四场同开：模型vs市场，谁更准？', False, '只有假阳性 -> 应拦下'),
    ('9月19日 精选场：四场让步，垫底队要赢两球', False, '无 vs -> 应拦下'),
    ('9月19日 意甲前二同积12分，罗马对国米的主场魔咒', False, '"对"不算(搜索认 vs)'),
    ('周六001 日职 长崎vs大阪樱花：垫底队当热门', True, '标准模板'),
]
bad = 0
for t, want, why in cases:
    got = has_team_vs(t)
    if got != want:
        bad += 1
    mark = 'OK  ' if got == want else 'FAIL'
    print('  [%s] got=%-5s 命中=%s' % (mark, got, find_team_vs(t)))
    print('         %s | %s' % (why, t))

print()
print('=== 2. 262 篇真实标题回归 (修复前后应一致) ===')
rows = []
with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '头条_全量_20260505-0919.tsv'), encoding='utf-8') as f:
    head = f.readline().rstrip('\n').split('\t')
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) == len(head):
            rows.append(dict(zip(head, p)))
p_ = [r for r in rows if has_team_vs(r['标题'])]
print('  通过 %d/%d = %.1f%%  (修复前为 142/262 = 54.2%%)' % (
    len(p_), len(rows), len(p_) / len(rows) * 100))
over = [r for r in rows if has_team_vs(r['标题']) and len(r['标题']) > TITLE_MAX_TOUTIAO]
print('  其中同时超 36 字的: %d 篇 (长度与 SEO 是两把独立尺子)' % len(over))

print()
print('=== 3. 多场打包稿: 只写主打场次即可 ===')
for t in ['周三其余12场速览 罗马vs国米：9场偏受让',
          '周二11场 桑德兰vs阿尔克马：受让方更重8场',
          '周日013+021 钢巴vs浦和：双客热']:
    ok = has_team_vs(t) and len(t) <= TITLE_MAX_TOUTIAO
    print('  [%s] %2d字 | %s' % ('OK  ' if ok else 'FAIL', len(t), t))

print()
print('单元测试:', 'all pass' if bad == 0 else '%d FAILED' % bad)
sys.exit(0 if bad == 0 else 1)
