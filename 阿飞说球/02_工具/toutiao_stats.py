# -*- coding: utf-8 -*-
"""toutiao_stats.py — 头条号后台数据 → 形态 / 标题 / 收益 分析

用法:
  python 阿飞说球/02_工具/toutiao_stats.py [明细.tsv]

明细格式(制表符分隔, 首行表头):
  日期 标题 展现量 阅读量 点击率 阅读时长 点赞量 评论量 收益

分析维度:
  · 单篇: 千次阅读收益(元) / 千次展现收益(元) / 互动率
  · 形态分组: 单场 / 双场 / 三场 / 多场速览(≥4场) —— 看 CTR 与展现量的差异
  · 标题特征: 是否带具体数字、是否带问句、标题长度、是否含"速览/盘点/串烧"等抽象词
  · 结论输出: 按 CTR 排名、按收益排名、分形态均值

⚠️ 收益的结算通常滞后(T+1~T+2), 最近 1-2 天的 0 收益不代表真实表现, 分析时需剔除或标注。
"""
import io
import os
import re
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT = os.path.join(BASE, '阿飞说球', '05_运营数据', '头条_明细_20260917.tsv')

MULTI_WORDS = ['速览', '盘点', '串烧', '五场', '双推', '前瞻']
CN_NUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}


def parse(path):
    rows = []
    with io.open(path, encoding='utf-8') as f:
        head = f.readline()
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) < 10:
                continue
            date, tm, title = p[0], p[1], p[2]
            imp, rd = int(p[3]), int(p[4])
            ctr = float(p[5].rstrip('%'))
            mm, ss = p[6].split(':')
            dur = int(mm) * 60 + int(ss)
            like, cmt, rev = int(p[7]), int(p[8]), float(p[9])
            rows.append(dict(date=date, tm=tm, title=title, imp=imp, read=rd, ctr=ctr, dur=dur,
                             like=like, cmt=cmt, rev=rev, n=shape(title)))
    return rows


def shape(title):
    """从标题推断打包场次数

    ⚠️ 只认"明确的打包标记": 编号(如 007+009)、编号区间(001-003)、或"N场+速览/速评/串烧/前瞻/冒号"。
       不能把"5场平局""近5场""8战"里的数字当场次数(2026-09-17 首版就踩了这个坑,
       把 001-003 误判成 5 场、把单场 007 误判成 10 场)。
    """
    t = title
    nums = len(re.findall(r'\d{3}', t))
    rng = re.search(r'(\d{3})\s*[-–]\s*(\d{3})', t)
    if rng:
        nums = max(nums, abs(int(rng.group(2)) - int(rng.group(1))) + 1)
    m = re.search(r'(\d+|[一二三四五六七八九十]+)\s*场(?=速览|速评|串烧|盘点|前瞻|[:：]|$)', t)
    n = nums
    if m:
        s = m.group(1)
        n = max(n, int(s) if s.isdigit() else CN_NUM.get(s, 0))
    if any(w in t for w in ('速览', '速评', '盘点', '串烧')) and n < 3:
        n = 4          # 标题写了"速览/速评/串烧"但没写场次 → 一律视为多场打包
    return max(n, 1)


def group(n):
    if n >= 4:
        return '多场速览(≥4)'
    return {1: '单场', 2: '双场', 3: '三场'}[n]


def fmt_dur(s):
    return '%02d:%02d' % (s // 60, s % 60)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    rows = parse(path)
    print('样本 %d 篇 | %s ~ %s\n' % (len(rows), min(r['date'] for r in rows), max(r['date'] for r in rows)))

    for r in rows:
        r['rpm'] = r['rev'] / r['imp'] * 1000 if r['imp'] else 0      # 千次展现收益
        r['rpk'] = r['rev'] / r['read'] * 1000 if r['read'] else 0    # 千次阅读收益
        r['inter'] = (r['like'] + r['cmt']) / r['read'] * 100 if r['read'] else 0

    print('=' * 118)
    print('%-11s %-4s %7s %6s %6s %6s %6s %6s %7s %7s  %s' % (
        '日期', '形态', '展现', '阅读', 'CTR', '时长', '点赞', '评论', '收益', '元/千阅', '标题'))
    print('-' * 118)
    for r in sorted(rows, key=lambda x: x['date']):
        print('%-11s %-9s %7d %6d %5.1f%% %6s %6d %6d %7.2f %7.2f  %s' % (
            r['date'], group(r['n']), r['imp'], r['read'], r['ctr'], fmt_dur(r['dur']),
            r['like'], r['cmt'], r['rev'], r['rpk'], r['title'][:34]))

    # ---- 形态分组 ----
    print('\n' + '=' * 118)
    print('【按形态分组】(均值; CTR 用展现加权)')
    print('%-14s %4s %8s %8s %8s %8s %8s %9s' % ('形态', '篇数', '总展现', '总阅读', 'CTR', '时长', '总收益', '元/千阅读'))
    print('-' * 118)
    g = defaultdict(list)
    for r in rows:
        g[group(r['n'])].append(r)
    for k in ['单场', '双场', '三场', '多场速览(≥4)']:
        v = g.get(k)
        if not v:
            continue
        imp = sum(x['imp'] for x in v)
        rd = sum(x['read'] for x in v)
        rev = sum(x['rev'] for x in v)
        ctr = rd / imp * 100 if imp else 0
        dur = sum(x['dur'] for x in v) / len(v)
        print('%-14s %4d %8d %8d %7.1f%% %8s %8.2f %9.2f' % (
            k, len(v), imp, rd, ctr, fmt_dur(int(dur)), rev, rev / rd * 1000 if rd else 0))

    # ---- 标题特征 ----
    print('\n【标题特征 vs CTR】(均值, 展现加权)')
    feats = {
        '含具体赔率/数字(如1.96/40%)': lambda t: bool(re.search(r'\d+\.\d+|\d+%', t)),
        '含问句(?)': lambda t: '?' in t or '？' in t,
        '含抽象词(速览/盘点/串烧/前瞻)': lambda t: any(w in t for w in MULTI_WORDS),
        '含"VS/对"队名对位': lambda t: bool(re.search(r'VS|vs|对', t)),
        '标题≤30字': lambda t: len(t) <= 30,
        '标题>30字': lambda t: len(t) > 30,
    }
    print('%-34s %4s %8s %8s %8s' % ('特征', '篇数', '总展现', '总阅读', 'CTR'))
    print('-' * 118)
    for name, fn in feats.items():
        v = [r for r in rows if fn(r['title'])]
        if not v:
            continue
        imp = sum(x['imp'] for x in v)
        rd = sum(x['read'] for x in v)
        print('%-34s %4d %8d %8d %7.1f%%' % (name, len(v), imp, rd, rd / imp * 100 if imp else 0))

    # ---- 阅读时长 vs 千次阅读收益 ----
    print('\n【阅读时长 vs 千次阅读收益】(剔除收益=0 的近期稿)')
    paid = [r for r in rows if r['rev'] > 0]
    print('%-10s %4s %8s %10s' % ('时长区间', '篇数', '总阅读', '元/千阅读'))
    print('-' * 118)
    for lo, hi in [(0, 55), (55, 70), (70, 85), (85, 999)]:
        v = [r for r in paid if lo <= r['dur'] < hi]
        if not v:
            continue
        rd = sum(x['read'] for x in v)
        rev = sum(x['rev'] for x in v)
        print('%-10s %4d %8d %10.2f' % ('%d-%d秒' % (lo, hi if hi < 999 else 999), len(v), rd,
                                        rev / rd * 1000 if rd else 0))

    # ---- 发布时间 vs 表现 ----
    print('\n【发布时段 vs 表现】(剔除未显示发布时间的近期稿)')
    timed = [r for r in rows if r['tm']]
    print('%-14s %4s %9s %8s %8s %8s' % ('时段', '篇数', '平均展现', '总阅读', 'CTR', '总收益'))
    print('-' * 118)
    slots = [('上午 10:00-12:30', 10 * 60, 12 * 60 + 30),
             ('午后 12:30-16:00', 12 * 60 + 30, 16 * 60),
             ('傍晚 16:00-19:00', 16 * 60, 19 * 60),
             ('晚间 19:00 后', 19 * 60, 24 * 60)]
    for name, lo, hi in slots:
        v = [r for r in timed if lo <= int(r['tm'][:2]) * 60 + int(r['tm'][3:]) < hi]
        if not v:
            continue
        imp = sum(x['imp'] for x in v)
        rd = sum(x['read'] for x in v)
        print('%-14s %4d %9d %8d %7.1f%% %8.2f' % (
            name, len(v), imp / len(v), rd, rd / imp * 100 if imp else 0, sum(x['rev'] for x in v)))

    # ---- 排名 ----
    print('\n【CTR 前 6】')
    for r in sorted(rows, key=lambda x: -x['ctr'])[:6]:
        print('  %5.1f%%  展现%6d 阅读%5d  %s' % (r['ctr'], r['imp'], r['read'], r['title'][:52]))
    print('\n【CTR 后 6】')
    for r in sorted(rows, key=lambda x: x['ctr'])[:6]:
        print('  %5.1f%%  展现%6d 阅读%5d  %s' % (r['ctr'], r['imp'], r['read'], r['title'][:52]))
    print('\n【收益前 6】')
    for r in sorted(rows, key=lambda x: -x['rev'])[:6]:
        print('  %6.2f 元  阅读%5d  %s' % (r['rev'], r['read'], r['title'][:52]))
    print('\n【展现量前 6】')
    for r in sorted(rows, key=lambda x: -x['imp'])[:6]:
        print('  %6d  阅读%5d  CTR%5.1f%%  %s' % (r['imp'], r['read'], r['ctr'], r['title'][:52]))


if __name__ == '__main__':
    main()
