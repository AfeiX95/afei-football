# -*- coding: utf-8 -*-
"""控制时间混杂后, 再问一次: "含vs" 的展现差异是真的吗?

初步结果: 含vs 展现中位 5,074 vs 不含 7,003 —— 但 9 月的稿子展现本来就高,
而 9 月恰好有很多"精选场/速览"类无 vs 标题。必须按月份分层再看。
"""
import io
import os
import re
import statistics as st

BASE = os.path.dirname(os.path.abspath(__file__))
rows = []
with io.open(os.path.join(BASE, '头条_全量_20260505-0919.tsv'), encoding='utf-8') as f:
    head = f.readline().rstrip('\n').split('\t')
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) != len(head):
            continue
        r = dict(zip(head, p))
        for c in ('展现量', '阅读量'):
            r[c] = int(r[c])
        r['月份'] = r['发布时间'][:7]
        rows.append(r)

VS = re.compile(r'\bvs\b|VS|Vs', re.I)

print('=' * 100)
print('按月份分层: 含vs vs 不含vs')
print()
print('  %-9s %-14s %4s %11s %8s' % ('月份', '分组', 'n', '展现中位', '聚合CTR'))
print('  ' + '-' * 60)
for m in sorted({r['月份'] for r in rows}):
    sub = [r for r in rows if r['月份'] == m]
    for label, grp in (('含vs', [r for r in sub if VS.search(r['标题'])]),
                       ('不含vs', [r for r in sub if not VS.search(r['标题'])])):
        if not grp:
            continue
        imps = sorted(r['展现量'] for r in grp)
        imp = sum(r['展现量'] for r in grp)
        rd = sum(r['阅读量'] for r in grp)
        print('  %-9s %-14s %4d %11s %7.1f%%' % (
            m, label, len(grp), f"{imps[len(imps)//2]:,}", rd / imp * 100))
    # 组内差
    a = [r['展现量'] for r in sub if VS.search(r['标题'])]
    b = [r['展现量'] for r in sub if not VS.search(r['标题'])]
    if a and b:
        d = st.median(a) - st.median(b)
        print(f'  {"":9s} {"":14s} 含-不含 展现中位差 = {d:+,.0f}')

print()
print('=' * 100)
print('全校正: 以"月份"为层, 用层内中位数差做符号检验')
print()
diffs = []
for m in sorted({r['月份'] for r in rows}):
    sub = [r for r in rows if r['月份'] == m]
    a = [r['展现量'] for r in sub if VS.search(r['标题'])]
    b = [r['展现量'] for r in sub if not VS.search(r['标题'])]
    if len(a) >= 3 and len(b) >= 3:
        d = st.median(a) - st.median(b)
        diffs.append((m, d))
        print(f'  {m}: {d:+,.0f}')
print()
pos = sum(1 for _, d in diffs if d > 0)
print(f'  含vs更高的月份: {pos}/{len(diffs)}')
print()
print('  判读:')
print('   - 若各月符号不一致/量级远小于原始差 -> 原始的 -1,929 差主要是月份混杂, 不是 vs 造成的。')
print('   - 这正好复现了我们批判旧复盘时的同一个错误: 拿未分层的聚合数字当结论。')

print()
print('=' * 100)
print('真正该关心的问题: 标题里有没有【双方队名】(与 vs 这个连接词无关)')
print()
TEAMS = ['罗马', '国米', '国际米兰', 'AC米兰', '尤文', '拉齐奥', '那不勒斯', '佛罗伦萨',
         '博洛尼亚', '都灵', '乌迪内斯', '卡利亚里', '威尼斯', '蒙扎', '萨索洛', '科莫', '帕尔马',
         '巴萨', '皇马', '马竞', '塞维利亚', '贝蒂斯', '皇社', '毕尔巴鄂', '比利亚雷',
         '奥萨苏纳', '塞尔塔', '赫塔费', '阿拉维斯', '埃尔切', '西班牙人', '巴列卡诺', '桑坦德',
         '利物浦', '阿森纳', '曼城', '切尔西', '热刺', '曼联', '维拉', '埃弗顿', '纽卡', '诺丁汉',
         '伯恩茅斯', '西汉姆', '水晶宫', '利兹联', '伊普斯', '赫尔城', '考文垂', '斯托克城', '谢菲联',
         '拜仁', '多特', '斯图加特', '法兰克福', '弗赖堡', '门兴', '不来梅', '汉堡', '科隆', '奥格斯堡',
         '美因茨', '柏林', '勒沃库森', '波鸿', '赫塔', '沙尔克', '达姆施塔特', '帕德博恩', '沃夫斯堡',
         '巴黎', '摩纳哥', '里昂', '雷恩', '朗斯', '里尔', '马赛', '尼斯', '南特', '昂热', '兰斯',
         '蒙彼利埃', '斯特拉斯堡', '图卢兹', '圣埃蒂安', '罗德兹', '特鲁瓦',
         '横滨', '水户', '浦和', '鹿岛', '钢巴', '樱花', '广岛', '神户', '町田', '福冈', '清水',
         '冈山', '名古屋', '川崎', '大阪', '千叶', '京都', '东京',
         '蔚山', '全北', '首尔', '仁川', '济州', '金泉', '浦项', '富川', '安养', '光州', '大田', '江原',
         '马尔默', '赫根', '天狼星', '佐加顿斯', '索尔纳', '哈马比', '厄格里特', '埃夫斯堡', '米亚尔比',
         '汉坎', '利勒斯特', '维京', '特罗姆瑟', '奥勒松', '罗森博格', '博德闪耀', '萨尔普斯堡', '克里斯蒂',
         '本菲卡', '布拉加', '波尔图', '里斯本', '阿罗卡', '托林斯', '卡萨', '吉马良斯',
         '弗拉门戈', '帕尔梅拉斯', '博塔弗戈', '科林蒂安', '格雷米奥', '弗鲁米嫩塞', '瓦斯科', '米拉索尔',
         '库奥皮奥', '赫尔辛基', '拉赫蒂', '瓦萨', '雅罗', '柔佛', '国安', '申花',
         '采列', '奈梅亨', '霍芬海姆', '贝西克塔', '格拉茨', '安德莱', '拉科', '奥莫尼亚', '克里特',
         '波兹南', '桑德兰', '阿尔克马', '费内巴切', '萨格勒布', '索列夫', '雅典', '江原', '比亚韦',
         '流浪者', '帕福斯', '萨尔茨堡', '哈茨', '淡宾尼士', '卡塔尔', '沙特', '挪威', '瑞典', '丹麦',
         '威尔士', '格鲁吉亚', '爱尔兰', '新加坡', '墨西哥', '加拿大', '美国', '瑞士', '苏格兰',
         '土耳其', '伊拉克', '海地', '德国', '澳大利亚', '哥伦比亚', '加纳', '南非', '摩洛哥',
         '乌兹别克', '哥斯达黎加', '尼日利亚', '斯洛文尼亚', '斯洛伐克', '黑山', '塞浦路斯',
         '阿尔及利亚', '刚果', '科特迪瓦', '巴拿马', '塞内加尔', '秘鲁', '荷兰', '阿根廷', '巴西',
         '英格兰', '法国', '西班牙', '比利时', '葡萄牙', '克罗地亚', '厄瓜多尔', '波黑', '伊朗',
         '埃及', '捷克', '韩国', '佛得角', '库拉索', '巴拉圭', '乌拉圭', '奥地利', '约旦', '阿联酋']


def cnt(t):
    return len({x for x in TEAMS if x in t})


two = [r for r in rows if cnt(r['标题']) >= 2]
lt2 = [r for r in rows if cnt(r['标题']) < 2]
print(f'  标题含【双方队名】(≥2支): {len(two)} 篇 ({len(two)/len(rows)*100:.1f}%)')
print(f'  标题含队名 <2 支:        {len(lt2)} 篇 ({len(lt2)/len(rows)*100:.1f}%)  <- SEO 缺口')
print()
for label, g in (('≥2支队名', two), ('<2支队名', lt2)):
    imps = sorted(r['展现量'] for r in g)
    imp = sum(r['展现量'] for r in g)
    rd = sum(r['阅读量'] for r in g)
    print(f'  {label:12s} n={len(g):3d}  展现中位 {imps[len(imps)//2]:>7,}  聚合CTR {rd/imp*100:.1f}%')

print()
print('  <2支队名 的稿子里, 按月份分布:')
from collections import Counter
c = Counter(r['月份'] for r in lt2)
for m in sorted(c):
    tot = sum(1 for r in rows if r['月份'] == m)
    print(f'    {m}: {c[m]}/{tot}')
