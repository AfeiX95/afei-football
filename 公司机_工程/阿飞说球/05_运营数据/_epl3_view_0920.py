# -*- coding: utf-8 -*-
"""英超三场: 我自己的方向与比分 (内部 -> 头条可用; 公众号一律不用)

方法(与 周日002/003 一致): 主客场拆分速率 + 小样本收缩(k=4) + 不套模型 form 加成。
"""
import math


def shrink(split, n, season, K=4.0):
    w = n / (n + K)
    return w * split + (1 - w) * season


def pois(k, lam):
    return lam ** k * math.exp(-lam) / math.factorial(k)


def matrix(lh, la, n=9):
    return {(h, a): pois(h, lh) * pois(a, la) for h in range(n) for a in range(n)}


def report(tag, home, away, line, mkt):
    """home/away = (gf_split, ga_split, gf_season, ga_season, n)"""
    hgf, hga, hgfs, hgas, hn = home
    agf, aga, agfs, agas, an = away
    hs_a = shrink(hgf, hn, hgfs)
    hs_d = shrink(hga, hn, hgas)
    as_a = shrink(agf, an, agfs)
    as_d = shrink(aga, an, agas)
    lam_h = (hs_a * 0.92 + as_d * 1.08) / 2 + 0.15
    lam_a = (as_a * 0.92 + hs_d * 1.08) / 2
    P = matrix(lam_h, lam_a)
    ph = sum(p for (h, a), p in P.items() if h > a)
    pd = sum(p for (h, a), p in P.items() if h == a)
    pa = sum(p for (h, a), p in P.items() if h < a)
    print('=' * 88)
    print(tag + '   线 %+d' % line)
    print()
    print('  收缩后速率(%.0f%% 权重给拆分数值):' % (hn / (hn + 4) * 100))
    print('    主: 攻 %.2f->%.2f  防 %.2f->%.2f' % (hgf, hs_a, hga, hs_d))
    print('    客: 攻 %.2f->%.2f  防 %.2f->%.2f' % (agf, as_a, aga, as_d))
    print('  λ_主 %.2f / λ_客 %.2f / 总 %.2f   (市场总进球 %.2f)' % (lam_h, lam_a, lam_h + lam_a, mkt))
    print('  我的: 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (ph * 100, pd * 100, pa * 100))
    top = sorted(P.items(), key=lambda kv: -kv[1])[:5]
    print('  比分排序: ' + '  '.join('%d:%d %.1f%%' % (h, a, p * 100) for (h, a), p in top))
    net = {}
    for (h, a), p in P.items():
        net[h + line - a] = net.get(h + line - a, 0) + p
    win = sum(v for k, v in net.items() if k > 0)
    push = net.get(0, 0.0)
    lose = sum(v for k, v in net.items() if k < 0)
    if line < 0:
        nm = ('让胜(主赢够)', '走水(主恰赢1)', '让负(主赢不到1)')
    else:
        nm = ('让胜(主受让不败)', '走水(客恰赢1)', '让负(客赢够)')
    print('  我的落点: %s %.1f%% / %s %.1f%% / %s %.1f%%' % (nm[0], win * 100, nm[1], push * 100, nm[2], lose * 100))
    tot = {}
    for (h, a), p in P.items():
        tot[h + a] = tot.get(h + a, 0) + p
    print('  总进球: 0-1球 %.1f%% / 2球 %.1f%% / 3球 %.1f%% / 4+球 %.1f%%' % (
        sum(v for k, v in tot.items() if k <= 1) * 100, tot.get(2, 0) * 100,
        tot.get(3, 0) * 100, sum(v for k, v in tot.items() if k >= 4) * 100))
    print()


report('① 周日011 伯恩茅斯(主) vs 利物浦(客)',
       (1.50, 1.50, 1.50, 1.75, 2),      # 主队主场攻/防 + 赛季攻/防
       (2.00, 1.00, 1.50, 1.00, 2),      # 客队客场攻/防 + 赛季攻/防
       1, 3.13)

report('② 周日012 曼城(主) vs 桑德兰(客)',
       (1.50, 0.50, 2.00, 0.50, 2),
       (1.00, 1.50, 0.75, 1.25, 2),
       -1, 3.12)

report('③ 周日020 富勒姆(主) vs 曼联(客)',
       (2.00, 3.00, 1.00, 1.75, 2),
       (1.00, 2.00, 1.75, 1.75, 2),
       1, 3.04)

print('=' * 88)
print('市场对照(去水)')
print()
print('  %-22s %8s %8s %8s | %8s %8s %8s' % ('', '主胜', '平', '客胜', '让胜', '走水', '让负'))
print('  ' + '-' * 78)
for tag, pl, hh in (('011 伯恩茅斯vs利物浦', (29.55, 24.29, 46.17), (47.96, 24.31, 27.73)),
                    ('012 曼城vs桑德兰', (75.02, 15.95, 9.03), (53.02, 23.06, 23.93)),
                    ('020 富勒姆vs曼联', (25.34, 23.97, 50.68), (47.96, 24.31, 27.73))):
    print('  %-22s %7.1f%% %7.1f%% %7.1f%% | %7.1f%% %7.1f%% %7.1f%%' % (
        tag, pl[0], pl[1], pl[2], hh[0], hh[1], hh[2]))
