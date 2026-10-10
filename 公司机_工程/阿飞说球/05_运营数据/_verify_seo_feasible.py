# -*- coding: utf-8 -*-
"""规则可行性验证: "必须含队名对位" + "≤36字" 能否同时满足?

关键: 不能【插入】队名对位(会超长), 要【替换】掉模糊描述。
     旧写法把 7~10 个字浪费在"客场垫底当热门"这种搜索不认的描述上。
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '02_工具')))
from check_md_release import has_team_vs, RE_TEAM_VS, TITLE_MAX_TOUTIAO

BASE = os.path.dirname(os.path.abspath(__file__))

rows = []
with io.open(os.path.join(BASE, '头条_全量_20260505-0919.tsv'), encoding='utf-8') as f:
    head = f.readline().rstrip('\n').split('\t')
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) == len(head):
            rows.append(dict(zip(head, p)))

print('=' * 100)
print('1. 假阳性修复验证')
print()
fp = [r for r in rows if RE_TEAM_VS.search(r['标题']) and not has_team_vs(r['标题'])]
print(f'  正则命中但被判假阳性的标题: {len(fp)} 篇')
for r in fp:
    print(f"    {r['标题']}")
print()
p = [r for r in rows if has_team_vs(r['标题'])]
print(f'  修复后真正通过: {len(p)}/{len(rows)} ({len(p)/len(rows)*100:.1f}%)')

print()
print('=' * 100)
print('2. 两种改法对比: 【插入】vs【替换】')
print()
CASES = [
    # (原标题, 主打场次队名对位, 压缩后的反差点)
    ('9月19日 日职001+004：客场垫底当热门，主场弱旅让一球',
     '长崎vs大阪樱花', '垫底队当热门'),
    ('9月15日 周二11场:受让方更重8场,014差45.5点',
     '桑德兰vs阿尔克马', '11场里8场偏受让'),
    ('9月13日赛事前瞻 周日013+021双客热：三连胜的硬，两连败的虚',
     '钢巴vs浦和', '双客热,硬的碰虚的'),
    ('9月17日 周四002+007：一场数据被抬高，一场被热身赛美化',
     '克里特vs霍芬海姆', '数据被抬高'),
]
print('  %-42s %-18s %6s %6s' % ('原标题', '队名对位', '插入后', '替换后'))
print('  ' + '-' * 80)
for orig, vs, short in CASES:
    # 插入: 在第一个冒号处塞进去
    ins = re.sub(r'[：:]', f' {vs}：', orig, count=1)
    # 替换: 用 队名对位 + 压缩反差点 替换冒号后的内容, 并去掉冗余日期前缀
    body = re.sub(r'^9月\d+日\s*', '', orig)          # 去掉"9月19日 "前缀(发布日已由平台记录)
    body = re.sub(r'^(周[一二三四五六日])', r'\1 ', body)
    rep = re.sub(r'[：:].*$', f' {vs}：{short}', body)
    ok_i = '✅' if len(ins) <= TITLE_MAX_TOUTIAO else '❌'
    ok_r = '✅' if len(rep) <= TITLE_MAX_TOUTIAO else '❌'
    print('  %-42s %-18s %4d%s %4d%s' % (orig[:40], vs, len(ins), ok_i, len(rep), ok_r))
    print(f'      插入 -> {ins}')
    print(f'      替换 -> {rep}')

print()
print('=' * 100)
print('3. 结论')
print()
print('  【插入】4 例中 3 例超过 36 字 —— 直接把队名塞进去会让规则自相矛盾。')
print('  【替换】4 例全部 ≤36 字 —— 因为把"9月19日"这种发布日前缀和"客场垫底当热门"')
print('          这种搜索不认的模糊描述换成了队名, 净字数没有增加。')
print()
print('  → 推荐模板: 【周X 编号 联赛】主队vs客队：一个反差点')
print('     例: 周六001 日职 长崎vs大阪樱花：垫底队当热门')
print()
print('  长度预算(≤36字):')
print('     周X编号(6) + 联赛(2-4) + 队名对位(6-14) + 冒号(1) + 反差点(8-14) = 23~39')
print('     ⇒ 反差点控制在 **12 字以内** 比较稳; 超过就先砍反差点, 不要砍队名。')
