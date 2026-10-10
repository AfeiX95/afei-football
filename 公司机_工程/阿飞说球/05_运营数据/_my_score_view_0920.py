# -*- coding: utf-8 -*-
"""我自己对两场的比分走向判断(内部参考, 不是发布稿)

方法(与文章里的"不选边"是两件事):
  1. 用【主客场拆分】速率, 不用赛季均值 —— 因为这两场的赛季均值都被非联赛场次污染过。
  2. 对 3 场的主客场小样本做**收缩**(向赛季值回归, k=4): 3 场的 0.33 失球不能全信。
  3. 不套用 afei_generator 的 form 加成(它把杯赛赢球也算进去, 两场都偏高)。
  4. 与市场比分盘/总进球盘口对照, 看我的偏差在哪。
"""
import math

LG_AVG = 1.30       # 日职场均单边进球 ≈ 2.6/2
K = 4.0             # 收缩强度: w = n/(n+K)


def shrink(split, n, season):
    w = n / (n + K)
    return w * split + (1 - w) * season, w


def pois(k, lam):
    return lam ** k * math.exp(-lam) / math.factorial(k)


def matrix(lh, la, n=8):
    return {(h, a): pois(h, lh) * pois(a, la) for h in range(n) for a in range(n)}


def report(name, home, away, line, mkt_score_top, mkt_total):
    """home/away = (gf_split, ga_split, gf_season, ga_season, n_split)"""
    hgf, hga, hgfs, hgas, hn = home
    agf, aga, agfs, agas, an = away
    hgf_s, wh = shrink(hgf, hn, hgfs)
    hga_s, _ = shrink(hga, hn, hgas)
    agf_s, wa = shrink(agf, an, agfs)
    aga_s, _ = shrink(aga, an, agas)

    print('=' * 92)
    print(f'{name}   让球线 {line:+d}')
    print()
    print('  收缩后的可比速率(3 场样本收缩 %.0f%%)' % (wh * 100))
    print('    主队: 攻 %.2f -> %.2f   防 %.2f -> %.2f' % (hgf, hgf_s, hga, hga_s))
    print('    客队: 攻 %.2f -> %.2f   防 %.2f -> %.2f' % (agf, agf_s, aga, aga_s))

    # λ: 沿用工具的"攻/防取平均"结构, 但不加 form, 只留主场优势
    lam_h = (hgf_s * 0.92 + aga_s * 1.08) / 2 + 0.15
    lam_a = (agf_s * 0.92 + hga_s * 1.08) / 2
    P = matrix(lam_h, lam_a)
    ph = sum(p for (h, a), p in P.items() if h > a)
    pd = sum(p for (h, a), p in P.items() if h == a)
    pa = sum(p for (h, a), p in P.items() if h < a)
    print()
    print('  λ_主 %.2f / λ_客 %.2f / 期望总进球 %.2f     (市场总进球 %.2f)' % (
        lam_h, lam_a, lam_h + lam_a, mkt_total))
    print('  我的概率: 主 %.1f%% / 平 %.1f%% / 客 %.1f%%' % (ph * 100, pd * 100, pa * 100))

    # 我的前 6 比分
    top = sorted(P.items(), key=lambda kv: -kv[1])[:6]
    print()
    print('  我的比分排序:      ' + '  '.join('%d:%d %.1f%%' % (h, a, p * 100) for (h, a), p in top))
    print('  市场比分盘最热三档: ' + mkt_score_top)

    # 让球落点
    if line < 0:
        win = sum(p for (h, a), p in P.items() if h + line > a)
        push = sum(p for (h, a), p in P.items() if h + line == a)
        lose = sum(p for (h, a), p in P.items() if h + line < a)
        names = ('让胜(主队赢够)', '走水', '让负(受让方赢)')
    else:
        win = sum(p for (h, a), p in P.items() if h + line > a)
        push = sum(p for (h, a), p in P.items() if h + line == a)
        lose = sum(p for (h, a), p in P.items() if h + line < a)
        names = ('让胜(主队受让不败)', '走水(客队恰好赢1)', '让负(客队赢够)')
    print()
    print('  我的让球落点:  %s %.1f%% / %s %.1f%% / %s %.1f%%'
          % (names[0], win * 100, names[1], push * 100, names[2], lose * 100))

    # 进球区间
    tot = {}
    for (h, a), p in P.items():
        tot[h + a] = tot.get(h + a, 0) + p
    o01 = sum(v for k, v in tot.items() if k <= 1)
    o23 = sum(v for k, v in tot.items() if 2 <= k <= 3)
    o4 = sum(v for k, v in tot.items() if k >= 4)
    print('  总进球区间: 0-1球 %.1f%% / 2-3球 %.1f%% / 4+球 %.1f%%' % (
        o01 * 100, o23 * 100, o4 * 100))

    # 主客净胜球
    net = {}
    for (h, a), p in P.items():
        net[h - a] = net.get(h - a, 0) + p
    print('  净胜球: ' + ' '.join('%+d %.0f%%' % (k, net[k] * 100)
                                  for k in sorted(net) if net[k] > 0.03))
    print()


report('① 周日002 町田泽维(主) vs 柏太阳神(客)',
       (2.00, 1.00, 2.71, 0.86, 3),      # 主队: 主场攻/防 + 赛季攻/防
       (1.75, 1.25, 1.86, 1.43, 4),      # 客队: 客场攻/防 + 赛季攻/防
       -1,
       '1:1 11.5% / 2:1 9.3% / 1:0 8.8%',
       2.82)

report('② 周日003 大阪钢巴(主) vs 神户胜利(客)',
       (1.33, 1.67, 1.14, 1.86, 3),
       (1.00, 0.33, 1.57, 0.71, 3),
       +1,
       '1:1 11.5% / 1:2 10.7% / 0:1 10.0%',
       2.69)
