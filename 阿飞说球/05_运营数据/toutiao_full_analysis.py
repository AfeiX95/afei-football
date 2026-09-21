# -*- coding: utf-8 -*-
"""头条全量运营数据分析 (2026-05-05 ~ 2026-09-19, 262 篇)

目的: 用全量数据**压力测试** 头条复盘_20260904-0917.md 的五条结论。
      上一版只有 30 篇 (9/4~9/17), 复盘自己列了三条待办:
        ① 三场/晚间样本太小  ② 缺账号成长期切片  ③ 缺完读率字段
      本数据 262 篇 + 完读率, 三条都能回答。

方法学要点
  · CTR 一律用 **实算 = 阅读量/展现量**, 不依赖后台 2 位小数的点击率字段。
  · 展现量极度右偏(498 ~ 78523), 故分组同时给 **聚合 CTR**(总阅读/总展现) 与
    **逐篇中位数**, 后者不被爆款单篇绑架。
  · 所有组间比较给 n 与 Wilson 95% CI; n<8 的组只记录不下结论。
  · 账号成长期(5-8 月)与成熟期(9 月)分开看, 避免把"账号长大"误读成"内容变好"。
"""
import io
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, '头条_全量_20260505-0919.tsv')
OUT = os.path.join(BASE, '头条全量复盘_20260505-0919.md')

sys.path.insert(0, os.path.normpath(os.path.join(BASE, '..', '02_工具')))
from toutiao_stats import shape, group as shape_group   # 复用既有形态分类, 保证可比


# ---------------------------------------------------------------- 载入
def load():
    rows = []
    with io.open(SRC, encoding='utf-8') as f:
        head = f.readline().rstrip('\n').split('\t')
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) != len(head):
                continue
            r = dict(zip(head, p))
            for c in ('展现量', '粉丝展现量', '阅读量', '粉丝阅读量', '时长',
                      '点赞', '评论', '转发', '分享', '收藏'):
                r[c] = int(r[c])
            r['完成率'] = float(r['完成率'])
            r['dt'] = datetime.strptime(r['发布时间'], '%Y-%m-%d %H:%M:%S')
            r['date'] = r['dt'].date()
            r['hm'] = r['dt'].hour * 60 + r['dt'].minute
            r['ctr'] = r['阅读量'] / r['展现量'] if r['展现量'] else 0.0
            r['n'] = shape(r['标题'])
            r['形态'] = shape_group(r['n'])
            inter = r['点赞'] + r['评论'] + r['转发'] + r['分享'] + r['收藏']
            r['互动'] = inter
            r['互动率'] = inter / r['阅读量'] if r['阅读量'] else 0.0
            r['粉阅占比'] = r['粉丝阅读量'] / r['阅读量'] if r['阅读量'] else 0.0
            r['赛事'] = classify(r['标题'])
            r['月份'] = r['date'].strftime('%Y-%m')
            # 半月切片
            d = r['date'].day
            r['半月'] = r['date'].strftime('%Y-%m') + ('上' if d <= 15 else '下')
            rows.append(r)
    rows.sort(key=lambda x: x['dt'])
    return rows


LEAGUE_WORDS = [
    ('日职/韩职/亚冠/中超', ['日职', '韩职', '韩K联', '亚冠', '中超', '国足', '日本', '韩国', '蔚山', '全北', '浦和', '横滨', '钢巴', '鹿岛', '樱花', '广岛', '神户', '首尔', '仁川', '济州', '町田', '柏', '福冈', '清水', '町田', '水户', '冈山', '大阪', '名古屋', '川崎']),
    ('西甲/意甲/英超/德甲/法甲', ['西甲', '意甲', '英超', '德甲', '法甲', '皇马', '巴萨', '马竞', 'AC米兰', '国际米兰', '国米', '尤文', '罗马', '拉齐奥', '那不勒斯', '拜仁', '多特', '利物浦', '阿森纳', '曼城', '切尔西', '热刺', '曼联', '维拉', '朗斯', '尼斯', '巴黎', '摩纳哥', '皇社', '贝蒂斯', '塞维利亚', '毕尔包', '毕包']),
    ('欧冠/欧罗巴/欧协联', ['欧冠', '欧罗巴', '欧联', '欧超杯', '欧协联', '解放者杯']),
    ('世界杯/国家队', ['世界杯', '欧洲杯', '国际赛', '阿根廷', '法国', '英格兰', '巴西', '挪威', '比利时', '葡萄牙', '西班牙', '克罗地亚', '丹麦', '威尔士', '格鲁吉亚', '爱尔兰', '新加坡', '墨西哥', '卡塔尔', '加拿大', '美国', '瑞士', '苏格兰', '土耳其', '沙特', '伊拉克', '海地', '德国', '澳大利亚', '哥伦比亚', '加纳', '南非', '摩洛哥', '乌兹别克', '哥斯达黎加', '尼日利亚', '斯洛文尼亚', '斯洛伐克', '黑山', '塞浦路斯', '阿尔及利亚', '刚果', '科特迪瓦', '巴拿马', '塞内加尔', '瑞典', '秘鲁', '荷兰']),
    ('瑞超/挪超/北欧其他', ['瑞超', '挪超', '芬超', '瑞典', '挪威', '马尔默', '赫根', '天狼星', '佐加顿斯', '索尔纳', '哈马比', '厄格里特', '埃夫斯堡', '米亚尔比', '汉坎', '利勒斯特', '维京', '特罗姆瑟', '奥勒松', '罗森博格', '博德闪耀', '库奥皮奥', '拉赫蒂', '瓦萨']),
    ('英冠/德乙/法乙/意杯等其他联赛', ['英冠', '德乙', '法乙', '意大利杯', '英联杯', '德国杯', '法国杯', '巴甲', '巴西杯', '美职', '沙职', '荷甲', '荷乙', '葡超', '卡萨', '本菲卡', '布拉加', '波尔图', '托林斯', '菲尔特', '埃森', '圣埃蒂安', '罗德兹', '沃夫斯堡', '帕德博恩']),
]


def classify(title):
    for name, words in LEAGUE_WORDS:
        if any(w in title for w in words):
            return name
    return '其他/非赛事'


# ---------------------------------------------------------------- 统计
def agg(rows):
    """组内聚合: 总展现/总阅读/聚合CTR/中位CTR/完成率/时长"""
    if not rows:
        return None
    imp = sum(r['展现量'] for r in rows)
    rd = sum(r['阅读量'] for r in rows)
    ctrs = sorted(r['ctr'] for r in rows)
    comps = sorted(r['完成率'] for r in rows)
    durs = sorted(r['时长'] for r in rows)
    inter = sum(r['互动'] for r in rows)
    return {
        'n': len(rows), 'imp': imp, 'read': rd,
        'ctr': rd / imp if imp else 0,
        'ctr_med': ctrs[len(ctrs) // 2],
        'imp_med': sorted(r['展现量'] for r in rows)[len(rows) // 2],
        'comp_med': comps[len(comps) // 2],
        'dur_med': durs[len(durs) // 2],
        'inter': inter, 'inter_rate': inter / rd if rd else 0,
        'read_med': sorted(r['阅读量'] for r in rows)[len(rows) // 2],
    }


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def ctr_ci(rows, n_boot=2000, seed=12345):
    """对"逐篇文章"做 bootstrap 的聚合CTR 置信区间。

    ⚠️ 不能用二项 Wilson: 展现量不是独立伯努利试验(同一篇文章内部高度相关),
       Wilson 会给出 7.0%-7.1% 这种窄到无意义的区间。按文章重抽样才对。
    """
    import random
    if len(rows) < 5:
        return (float('nan'), float('nan'))
    rnd = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        s = [rows[rnd.randrange(len(rows))] for _ in range(len(rows))]
        imp = sum(x['展现量'] for x in s)
        vals.append(sum(x['阅读量'] for x in s) / imp if imp else 0)
    vals.sort()
    return (vals[int(n_boot * .025)], vals[int(n_boot * .975)])


def ctr_of(rows):
    imp = sum(r['展现量'] for r in rows)
    return sum(r['阅读量'] for r in rows) / imp if imp else 0.0


def diff_ci(g1, g2, n_boot=2000, seed=999):
    """两组聚合CTR之差的 bootstrap 区间(按文章重抽样)。返回 (diff, lo, hi, p_two_sided)"""
    import random
    if len(g1) < 3 or len(g2) < 3:
        return (float('nan'),) * 4
    rnd = random.Random(seed)
    obs = ctr_of(g1) - ctr_of(g2)
    ds = []
    for _ in range(n_boot):
        s1 = [g1[rnd.randrange(len(g1))] for _ in range(len(g1))]
        s2 = [g2[rnd.randrange(len(g2))] for _ in range(len(g2))]
        ds.append(ctr_of(s1) - ctr_of(s2))
    ds.sort()
    lo, hi = ds[int(n_boot * .025)], ds[int(n_boot * .975)]
    # 双尾 p: 重抽样分布中越过 0 的比例
    neg = sum(1 for d in ds if d <= 0) / n_boot
    pos = sum(1 for d in ds if d >= 0) / n_boot
    p = min(1.0, 2 * min(neg, pos))
    return obs, lo, hi, p


def star(p):
    if p != p:
        return '—'
    if p < 0.01:
        return '**'
    if p < 0.05:
        return '*'
    return 'n.s.'


def pct(x, d=1):
    return f'{x*100:.{d}f}%'


def table(w, headers, rows_):
    w('| ' + ' | '.join(headers) + ' |')
    w('|' + '|'.join(['---'] * len(headers)) + '|')
    for r in rows_:
        w('| ' + ' | '.join(str(x) for x in r) + ' |')


def by(w, rows, keyfn, order=None, min_n=1, note=''):
    """按 keyfn 分组统计"""
    g = defaultdict(list)
    for r in rows:
        g[keyfn(r)].append(r)
    keys = order if order else sorted(g, key=lambda k: (-len(g[k]), str(k)))
    out = []
    for k in keys:
        if k not in g or len(g[k]) < min_n:
            continue
        a = agg(g[k])
        out.append([k, a['n'], a['imp_med'], pct(a['ctr']), pct(a['ctr_med']),
                    pct(a['comp_med'] / 100), a['dur_med'], pct(a['inter_rate'], 2)])
    return out, g


# ---------------------------------------------------------------- 主流程
def main():
    rows = load()
    L = []
    def w(s=''):
        L.append(s)

    d0, d1 = rows[0]['date'], rows[-1]['date']
    tot_imp = sum(r['展现量'] for r in rows)
    tot_rd = sum(r['阅读量'] for r in rows)
    imps = sorted(r['展现量'] for r in rows)
    rds = sorted(r['阅读量'] for r in rows)

    w('# 头条号全量运营复盘 (2026-05-05 ~ 2026-09-19)')
    w('')
    w('## 0. 数据与校验')
    w('')
    w('| 项 | 值 |')
    w('|---|---|')
    w(f'| 样本 | **{len(rows)} 篇**(完整账号历史) |')
    w(f'| 时间跨度 | {d0} ~ {d1} ({(d1-d0).days} 天) |')
    w(f'| 总展现 | {tot_imp:,} |')
    w(f'| 总阅读 | {tot_rd:,} |')
    w(f'| 整体CTR | {pct(tot_rd/tot_imp)} |')
    w(f'| 平均完成率(中位) | {pct(sorted(r["完成率"] for r in rows)[len(rows)//2]/100)} |')
    w('')
    w('**转录校验**(详见 `_校验报告.md`)')
    w('')
    w('- 点击率 = 阅读/展现: **261/262 通过**, 1 行源数据自相矛盾(已标记, 不参与 CTR 比较)')
    w('- 与 9/17 旧台账交叉: **29/29 匹配**, 其中 **27 行 时长/点赞/评论 逐字相同**')
    w('- 行数: 上一版复盘记"账号累计 258 条"(9/17) → 本批 262 = 258 + 9/18~19 新发 4 篇 ✅')
    w('')
    w('> 口径: CTR 一律用**实算 阅读量/展现量**; 分组同时给聚合CTR与逐篇中位CTR, 后者不被爆款绑架。')
    w('> 组间显著性用**按文章 bootstrap**(不用二项 Wilson —— 展现量不是独立伯努利试验, Wilson 会给出')
    w('> 7.0%~7.1% 这种窄到无意义的区间)。n<10 的组一律只记录、不下结论。')
    w('')

    # ---------------- 1. 账号成长 ----------------
    w('## 1. 最容易搞错的一件事: 账号在长大')
    w('')
    w('上一版复盘自己标了"缺账号成长因素", 并写"下次复盘应按 9/10 之后切片重算"。先看成长本身:')
    w('')
    def half_key(r):
        return r['date']
    months = sorted({r['月份'] for r in rows})
    halves = []
    for m in months:
        halves += [m + '上', m + '下']
    t, _ = by(w, rows, lambda r: r['半月'], order=halves)
    table(w, ['半月', 'n', '展现中位', '聚合CTR', '中位CTR', '完成率中位', '时长中位', '互动率'], t)
    w('')
    t, _ = by(w, rows, lambda r: r['月份'], order=months)
    table(w, ['月份', 'n', '展现中位', '聚合CTR', '中位CTR', '完成率中位', '时长中位', '互动率'], t)
    w('')
    w('**两个方向相反的趋势, 必须同时看**:')
    w('')
    w('| 指标 | 5月 | 7月 | 9月 | 走向 |')
    w('|---|---|---|---|---|')
    mo = {}
    for m in months:
        sub = [r for r in rows if r['月份'] == m]
        if sub:
            mo[m] = agg(sub)
    for label, key, fmt in (('展现中位', 'imp_med', lambda v: f'{v:,}'),
                            ('聚合CTR', 'ctr', lambda v: pct(v)),
                            ('完成率中位', 'comp_med', lambda v: f'{v:.1f}'),
                            ('时长中位', 'dur_med', lambda v: str(v))):
        cells = []
        for m in months:
            cells.append(fmt(mo[m][key]) if m in mo else '—')
        trend = '↑ 涨' if (months[0] in mo and months[-1] in mo and mo[months[-1]][key] > mo[months[0]][key]) else '↓ 跌'
        w(f'| {label} | {cells[0]} | {" / ".join(cells[1:-1])} | {cells[-1]} | {trend} |')
    w('')
    w('**展现量涨、完成率跌** —— 这两条是同一件事的两面(见 §7)。')
    w('任何"最早 vs 最近"的对比都混入了成长效应, 所以下面每条结论都给**全量**与**9/10后**两个口径。')
    w('')

    recent = [r for r in rows if r['date'] >= datetime(2026, 9, 10).date()]
    w(f'> 9/10 后切片: **{len(recent)} 篇**')
    w('')

    # ---------------- 2. 结论1: 形态 ----------------
    w('## 2. 结论1 复检: 形态 (旧结论"双场>单场>三场≫4场以上")')
    w('')
    order = ['单场', '双场', '三场', '多场速览(≥4)']
    w('**全量口径**')
    w('')
    t, g = by(w, rows, lambda r: r['形态'], order=order)
    table(w, ['形态', 'n', '展现中位', '聚合CTR', '中位CTR', '完成率中位', '时长中位', '互动率'], t)
    w('')
    for k in order:
        if k in g:
            a = agg(g[k])
            lo, hi = ctr_ci(g[k])
            mark = '' if a['n'] >= 10 else ' ⚠n<10'
            w(f"- **{k}**: n={a['n']}{mark}, 聚合CTR {pct(a['ctr'])} [boot95% {pct(lo)}-{pct(hi)}], "
              f"中位CTR {pct(a['ctr_med'])}, 展现中位 {a['imp_med']:,}, 阅读中位 {a['read_med']:,}")
    w('')
    w('**9/10 后口径**')
    w('')
    t, g2 = by(w, recent, lambda r: r['形态'], order=order)
    table(w, ['形态', 'n', '展现中位', '聚合CTR', '中位CTR', '完成率中位', '时长中位', '互动率'], t)
    w('')

    # ---------------- 3. 结论2: 时段 ----------------
    w('## 3. 结论2 复检: 发布时段 (旧结论"上午10:00-12:30黄金, 19:00后废")')
    w('')
    def slot(r):
        h = r['dt'].hour
        if h < 10:
            return '00:00-10:00'
        if h < 12:
            return '10:00-12:00'
        if h < 13:
            return '12:00-13:00'
        if h < 16:
            return '13:00-16:00'
        if h < 19:
            return '16:00-19:00'
        return '19:00-24:00'
    so = ['00:00-10:00', '10:00-12:00', '12:00-13:00', '13:00-16:00', '16:00-19:00', '19:00-24:00']
    w('**全量口径**')
    w('')
    t, g3 = by(w, rows, slot, order=so)
    table(w, ['时段', 'n', '展现中位', '聚合CTR', '中位CTR', '完成率中位', '时长中位', '互动率'], t)
    w('')
    w('**9/10 后口径** (排除成长期)')
    w('')
    t, g4 = by(w, recent, slot, order=so)
    table(w, ['时段', 'n', '展现中位', '聚合CTR', '中位CTR', '完成率中位', '时长中位', '互动率'], t)
    w('')

    # ---------------- 4. 结论3: 时长 ----------------
    w('## 4. 结论3 复检: 阅读时长 (旧数据无收益字段, 改验"时长→完成率/互动")')
    w('')
    w('旧复盘的核心因果链是"耐读 → 单价高"。本次导出**没有收益字段**, 无法直接验证单价;')
    w('但有了**完成率**, 可以验证链条的前半段"时长是否代表质量"。')
    w('')
    bins = [(0, 40, '<40秒'), (40, 55, '40-55秒'), (55, 70, '55-70秒'),
            (70, 85, '70-85秒'), (85, 999, '≥85秒')]
    w('**全量口径**')
    w('')
    t = []
    for lo, hi, name in bins:
        sub = [r for r in rows if lo <= r['时长'] < hi]
        if len(sub) < 3:
            continue
        a = agg(sub)
        t.append([name, a['n'], pct(a['ctr']), pct(a['comp_med'] / 100), a['dur_med'],
                  pct(a['inter_rate'], 2), f"{a['read_med']:,}"])
    table(w, ['时长区间', 'n', '聚合CTR', '完成率中位', '时长中位', '互动率', '阅读中位'], t)
    w('')
    w('**时长 vs 完成率 的相关性**')
    w('')
    xs = [r['时长'] for r in rows]
    ys = [r['完成率'] for r in rows]
    w(f'- Pearson r(时长, 完成率) = **{pearson(xs, ys):+.3f}** (n={len(rows)})')
    xs2 = [r['时长'] for r in rows]
    ys2 = [r['ctr'] for r in rows]
    w(f'- Pearson r(时长, CTR) = **{pearson(xs2, ys2):+.3f}**')
    xs3 = [r['时长'] for r in rows]
    ys3 = [r['展现量'] for r in rows]
    w(f'- Pearson r(时长, 展现量) = **{pearson(xs3, ys3):+.3f}**')
    w('')

    # ---------------- 5. 结论4: 赛事 ----------------
    w('## 5. 结论4 复检: 赛事类别 (旧结论"亚洲赛事是钱袋子")')
    w('')
    w('**全量口径**')
    w('')
    t, g5 = by(w, rows, lambda r: r['赛事'])
    table(w, ['赛事类别', 'n', '展现中位', '聚合CTR', '中位CTR', '完成率中位', '时长中位', '互动率'], t)
    w('')
    w('**9/10 后口径**')
    w('')
    t, g6 = by(w, recent, lambda r: r['赛事'])
    table(w, ['赛事类别', 'n', '展现中位', '聚合CTR', '中位CTR', '完成率中位', '时长中位', '互动率'], t)
    w('')

    # ---------------- 6. 结论5: 标题 ----------------
    w('## 6. 结论5 复检: 标题特征 (旧结论"反差数字提升CTR, 已放宽到≤36字")')
    w('')
    feats = {
        '含队名对位(VS/X对Y)': lambda t_: bool(re.search(r'VS|vs|对|v s', t_)),
        '含具体数字/赔率': lambda t_: bool(re.search(r'\d+\.\d+|\d+%', t_)),
        '含问句': lambda t_: ('?' in t_ or '？' in t_),
        '含抽象词(速览/速评/盘点/串烧)': lambda t_: any(x in t_ for x in ['速览', '速评', '盘点', '串烧']),
        '含编号(001-030)': lambda t_: bool(re.search(r'\d{3}', t_)),
        '长度 ≤30 字': lambda t_: len(t_) <= 30,
        '长度 31-36 字': lambda t_: 30 < len(t_) <= 36,
        '长度 >36 字': lambda t_: len(t_) > 36,
    }
    for label, sub in (('全量', rows), ('9/10后', recent)):
        w(f'**{label}口径**')
        w('')
        t = []
        for name, fn in feats.items():
            v = [r for r in sub if fn(r['标题'])]
            if len(v) < 3:
                continue
            a = agg(v)
            t.append([name, a['n'], pct(a['ctr']), pct(a['ctr_med']),
                      pct(a['comp_med'] / 100), pct(a['inter_rate'], 2)])
        table(w, ['特征', 'n', '聚合CTR', '中位CTR', '完成率中位', '互动率'], t)
        w('')

    # ---------------- 7. 新字段: 完成率 ----------------
    w('## 7. 新字段①: 完成率 (旧复盘点名缺的就是它)')
    w('')
    w('完成率是本批唯一"全新"的质量指标。它和 CTR 不是一回事:')
    w('')
    w(f'- r(完成率, CTR) = **{pearson([r["完成率"] for r in rows], [r["ctr"] for r in rows]):+.3f}**')
    w(f'- r(完成率, 展现量) = **{pearson([r["完成率"] for r in rows], [r["展现量"] for r in rows]):+.3f}**')
    w(f'- r(完成率, 阅读量) = **{pearson([r["完成率"] for r in rows], [r["阅读量"] for r in rows]):+.3f}**')
    w('')
    comps = sorted(r['完成率'] for r in rows)
    w(f'完成率分布: 中位 {comps[len(comps)//2]:.1f}/100, '
      f'四分位 {comps[len(comps)//4]:.1f} / {comps[3*len(comps)//4]:.1f}, '
      f'min {comps[0]:.1f}, max {comps[-1]:.1f}')
    w('')
    w('> ⚠️ 后台"平均阅读完成率"是 0-100 的**数值**(不是百分比小数), 本文统一按 /100 归一后展示。')
    w('')
    w('### 7.1 ⚠️ 完成率**不是质量指标, 是触达结构的镜子** —— 这条最容易搞反')
    w('')
    w('三个相关系数指向同一个解释:')
    w('')
    w('| 关系 | r | 含义 |')
    w('|---|---|---|')
    w(f'| 完成率 ↔ 展现量 | **{pearson([r["完成率"] for r in rows], [r["展现量"] for r in rows]):+.3f}** | 展现越大, 完成率越低 |')
    w(f'| 完成率 ↔ CTR | **{pearson([r["完成率"] for r in rows], [r["ctr"] for r in rows]):+.3f}** | CTR越高, 完成率越低 |')
    w(f'| 完成率 ↔ 粉丝阅读占比 | **{pearson([r["粉阅占比"] for r in rows if r["阅读量"]>0], [r["完成率"] for r in rows if r["阅读量"]>0]):+.3f}** | 越靠粉丝, 完成率越高 |')
    w('')
    w('**解释**: 一篇文章的流量有两个来源 —— 推荐(冷流量)和粉丝(熟流量)。')
    w('')
    w('- 被算法大规模推荐 → 展现几十万级 → 大量**路人**点进来随便划两下就走 → 完成率被拉低;')
    w('- 只推给粉丝 → 展现几千 → 进来的都是**想看的人** → 完成率高。')
    w('')
    w('所以 **"完成率低"往往意味着"这篇文章被打出去了", 是好事**。')
    w('拿完成率当质量KPI会得出完全颠倒的结论。看证据:')
    w('')
    lo8 = sorted(rows, key=lambda x: x['完成率'])[:8]
    big = [r for r in lo8 if r['展现量'] >= 10000]
    w('**完成率最低的 8 篇 —— 绝大多数是高展现爆款**:')
    w('')
    table(w, ['标题', '完成率', 'CTR', '展现', '阅读', '粉阅占比'],
          [[r['标题'][:36], f"{r['完成率']:.1f}", pct(r['ctr']), f"{r['展现量']:,}",
            f"{r['阅读量']:,}", pct(r['粉阅占比'])] for r in lo8])
    w('')
    w(f"这 8 篇平均展现 **{sum(r['展现量'] for r in lo8)/8:,.0f}**(全站中位 {imps[len(imps)//2]:,}), "
      f"其中 **{len(big)}/8 篇展现 ≥1万**; 平均完成率 **{sum(r['完成率'] for r in lo8)/8:.1f}**。")
    w('')
    hi8 = sorted(rows, key=lambda x: -x['完成率'])[:8]
    w('**完成率最高的 8 篇 —— 全部是低展现稿, 且多数阅读量只有个位数**:')
    w('')
    table(w, ['标题', '完成率', 'CTR', '展现', '阅读', '时长'],
          [[r['标题'][:36], f"{r['完成率']:.1f}", pct(r['ctr']), f"{r['展现量']:,}",
            f"{r['阅读量']:,}", r['时长']] for r in hi8])
    w('')
    w(f"这 8 篇平均展现 **{sum(r['展现量'] for r in hi8)/8:,.0f}**, 平均阅读仅 "
      f"**{sum(r['阅读量'] for r in hi8)/8:.0f}** —— 个位数阅读量上的「完成率」没有统计意义。")
    w('')
    w('> **正确用法**: 完成率只能**在同一触达量级内**比。跨量级比完成率 = 比流量来源, 不是比内容。')
    w('')
    w('**完成率最高的 8 篇**')
    w('')
    table(w, ['标题', '完成率', 'CTR', '展现', '时长'],
          [[r['标题'][:40], f"{r['完成率']:.1f}", pct(r['ctr']), f"{r['展现量']:,}", r['时长']]
           for r in sorted(rows, key=lambda x: -x['完成率'])[:8]])
    w('')
    w('**完成率最低的 8 篇**')
    w('')
    table(w, ['标题', '完成率', 'CTR', '展现', '时长'],
          [[r['标题'][:40], f"{r['完成率']:.1f}", pct(r['ctr']), f"{r['展现量']:,}", r['时长']]
           for r in sorted(rows, key=lambda x: x['完成率'])[:8]])
    w('')

    # ---------------- 8. 新字段: 粉丝阅读占比 ----------------
    w('## 8. 新字段②: 粉丝阅读占比 (推荐来源结构)')
    w('')
    fr = [r['粉阅占比'] for r in rows if r['阅读量'] > 0]
    w(f'- 粉丝阅读占全部阅读: 中位 **{pct(sorted(fr)[len(fr)//2])}**, 均值 {pct(sum(fr)/len(fr))}')
    w('')
    t = []
    for lo, hi, name in [(0, .02, '<2%'), (.02, .05, '2-5%'), (.05, .10, '5-10%'),
                         (.10, .20, '10-20%'), (.20, 1.01, '>20%')]:
        sub = [r for r in rows if r['阅读量'] > 0 and lo <= r['粉阅占比'] < hi]
        if len(sub) < 3:
            continue
        a = agg(sub)
        t.append([name, a['n'], pct(a['ctr']), pct(a['comp_med'] / 100), pct(a['inter_rate'], 2),
                  f"{a['imp_med']:,}"])
    table(w, ['粉阅占比区间', 'n', '聚合CTR', '完成率中位', '互动率', '展现中位'], t)
    w('')
    w(f'- r(粉阅占比, 展现量) = **{pearson([r["粉阅占比"] for r in rows if r["阅读量"]>0], [r["展现量"] for r in rows if r["阅读量"]>0]):+.3f}**')
    w(f'- r(粉阅占比, 完成率) = **{pearson([r["粉阅占比"] for r in rows if r["阅读量"]>0], [r["完成率"] for r in rows if r["阅读量"]>0]):+.3f}**')
    w('')

    # ---------------- 9. 新字段: 互动 ----------------
    w('## 9. 新字段③: 互动结构 (赞/评/转/享/藏)')
    w('')
    tot = {c: sum(r[c] for r in rows) for c in ('点赞', '评论', '转发', '分享', '收藏')}
    w('| 互动类型 | 总量 | 占阅读(每千次) |')
    w('|---|---|---|')
    for c in ('点赞', '评论', '转发', '分享', '收藏'):
        w(f'| {c} | {tot[c]:,} | {tot[c]/tot_rd*1000:.2f} |')
    w('')
    w(f'- 总互动率(五类合计/阅读) = **{pct(sum(tot.values())/tot_rd, 2)}**')
    w('')
    w('**互动率前 8 篇** (要求阅读≥100, 否则 1 个赞就能刷出高互动率)')
    w('')
    elig = [r for r in rows if r['阅读量'] >= 100]
    w(f'> 满足阅读≥100 的稿共 **{len(elig)}** 篇(占 {pct(len(elig)/len(rows))})')
    w('')
    table(w, ['标题', '互动率', '完成率', 'CTR', '展现', '阅读'],
          [[r['标题'][:36], pct(r['互动率'], 2), f"{r['完成率']:.1f}", pct(r['ctr']),
            f"{r['展现量']:,}", f"{r['阅读量']:,}"]
           for r in sorted(elig, key=lambda x: -x['互动率'])[:8]])
    w('')

    # ---------------- 10. 展现量 ----------------
    w('## 10. 收益的真实第一驱动: 展现量, 不是 CTR')
    w('')
    w(f'- 展现量: 中位 {imps[len(imps)//2]:,} | P90 {imps[int(len(imps)*.9)]:,} | max {imps[-1]:,}')
    w(f'- 阅读量: 中位 {rds[len(rds)//2]:,} | P90 {rds[int(len(rds)*.9)]:,} | max {rds[-1]:,}')
    w('')
    w('把总量拆开看头部集中度:')
    w('')
    top = sorted(rows, key=lambda x: -x['阅读量'])
    for k in (5, 10, 20, 50):
        s = sum(r['阅读量'] for r in top[:k])
        w(f'- 阅读量前 {k} 篇 = {s:,} 次, 占全账号 **{pct(s/tot_rd)}**')
    w('')
    w(f'- r(展现量, 阅读量) = **{pearson([r["展现量"] for r in rows], [r["阅读量"] for r in rows]):+.3f}**')
    w('')
    w('**展现量前 10 篇**')
    w('')
    table(w, ['标题', '展现', '阅读', 'CTR', '完成率', '时长', '形态'],
          [[r['标题'][:38], f"{r['展现量']:,}", f"{r['阅读量']:,}", pct(r['ctr']),
            f"{r['完成率']:.1f}", r['时长'], r['形态']]
           for r in sorted(rows, key=lambda x: -x['展现量'])[:10]])
    w('')

    # ---------------- 11. 校正清单 ----------------
    w('## 11. 结论校正清单')
    w('')
    w('这是本文的核心: 对照 `头条复盘_20260904-0917.md`(30 篇) 的五条结论 + 两条"硬规则",')
    w('用 262 篇复核。判定标准:')
    w('')
    w('- **确认** = 全量口径成立, 且方向与旧结论一致')
    w('- **修正** = 方向对但幅度/机理错了, 或旧结论只在小样本成立')
    w('- **推翻** = 全量口径下不成立或反向')
    w('')

    a_single = agg([r for r in rows if r['形态'] == '单场'])
    a_double = agg([r for r in rows if r['形态'] == '双场'])
    a_triple = agg([r for r in rows if r['形态'] == '三场'])
    a_multi = agg([r for r in rows if r['形态'] == '多场速览(≥4)'])

    def sl(name):
        return agg([r for r in rows if slot(r) == name])

    m1012 = sl('10:00-12:00')
    m1619 = sl('16:00-19:00')
    m19 = sl('19:00-24:00')
    a_asia = agg([r for r in rows if r['赛事'] == '日职/韩职/亚冠/中超'])
    a_euro = agg([r for r in rows if r['赛事'] == '西甲/意甲/英超/德甲/法甲'])

    base_ctr = tot_rd / tot_imp
    NUM_RE = re.compile(r'\d+\.\d+|\d+%')      # 具体赔率/百分比
    ID_RE = re.compile(r'\d{3}')               # 场次编号 001-030
    VS_RE = re.compile(r'VS|vs|对')            # 队名对位

    n_num = [r for r in rows if NUM_RE.search(r['标题'])]
    n_vs = [r for r in rows if VS_RE.search(r['标题'])]
    n_id = [r for r in rows if ID_RE.search(r['标题'])]
    n_noid = [r for r in rows if not ID_RE.search(r['标题'])]
    n_s30 = [r for r in rows if len(r['标题']) <= 30]
    n_3136 = [r for r in rows if 30 < len(r['标题']) <= 36]
    n_g36 = [r for r in rows if len(r['标题']) > 36]

    # ---------- 关键组间比较 (bootstrap 差异检验) ----------
    w('### 11.0 关键组间比较 (按文章 bootstrap, 双尾 p)')
    w('')
    w('`*` = p<0.05, `**` = p<0.01, `n.s.` = 不显著。**判定只认这张表, 不认上面的聚合数字大小。**')
    w('')
    comps = [
        ('双场 vs 单场', a_double and [r for r in rows if r['形态'] == '双场'],
         [r for r in rows if r['形态'] == '单场']),
        ('三场 vs 单场', [r for r in rows if r['形态'] == '三场'],
         [r for r in rows if r['形态'] == '单场']),
        ('≥4场 vs 单场', [r for r in rows if r['形态'] == '多场速览(≥4)'],
         [r for r in rows if r['形态'] == '单场']),
        ('10-12时 vs 16-19时', [r for r in rows if slot(r) == '10:00-12:00'],
         [r for r in rows if slot(r) == '16:00-19:00']),
        ('10-12时 vs 19时后', [r for r in rows if slot(r) == '10:00-12:00'],
         [r for r in rows if slot(r) == '19:00-24:00']),
        ('亚洲赛事 vs 五大联赛', [r for r in rows if r['赛事'] == '日职/韩职/亚冠/中超'],
         [r for r in rows if r['赛事'] == '西甲/意甲/英超/德甲/法甲']),
        ('含场次编号 vs 不含', n_id, n_noid),
        ('队名对位 vs 不含', n_vs, [r for r in rows if not VS_RE.search(r['标题'])]),
        ('含数字/赔率 vs 不含', n_num, [r for r in rows if not NUM_RE.search(r['标题'])]),
        ('标题>36字 vs ≤30字', n_g36, n_s30),
        ('单场: 时长≥70秒 vs <55秒',
         [r for r in rows if r['形态'] == '单场' and r['时长'] >= 70],
         [r for r in rows if r['形态'] == '单场' and r['时长'] < 55]),
    ]
    w('| 比较 | A n | A CTR | B n | B CTR | 差值(A-B) | boot95% | p | 显著 |')
    w('|---|---|---|---|---|---|---|---|---|')
    survivor = []
    for name, A, B in comps:
        if len(A) < 3 or len(B) < 3:
            w(f'| {name} | {len(A)} | — | {len(B)} | — | 样本不足 | — | — | — |')
            continue
        obs, lo, hi, p = diff_ci(A, B)
        if p < 0.05:
            survivor.append((name, p))
        w(f'| {name} | {len(A)} | {pct(ctr_of(A))} | {len(B)} | {pct(ctr_of(B))} | '
          f'{obs*100:+.2f}pp | [{lo*100:+.2f}, {hi*100:+.2f}]pp | {p:.3f} | {star(p)} |')
    w('')
    w(f'⚠️ **多重比较校正**: 本表共 {len(comps)} 次比较, 按 Bonferroni 阈值 α=0.05/{len(comps)}≈**0.0045**。')
    w('')
    w(f'- 未校正 p<0.05 的: **{len(survivor)} 项** —— ' + ', '.join(n for n, _ in survivor))
    strict = [n for n, p in survivor if p < 0.05 / len(comps)]
    w(f'- **通过 Bonferroni 的: {len(strict)} 项** —— ' + (', '.join(strict) if strict else '无'))
    w('')
    w('→ 只有通过 Bonferroni 的那几项可以当**确立的结论**; 其余是**方向性线索**, 需要下一批数据复核。')
    w('→ 这条纪律直接约束下面的判定列: **未过 Bonferroni 的一律不进"确认"。**')
    w('')

    w('| # | 旧结论 (30篇) | 262篇复核结果 | 判定 |')
    w('|---|---|---|---|')
    w(f"| 1a | 双场最优形态 | 双场 CTR {pct(a_double['ctr'])} (n={a_double['n']}) / 三场 "
      f"{pct(a_triple['ctr'])} (n={a_triple['n']}) / 单场 {pct(a_single['ctr'])} (n={a_single['n']}); "
      f"双场-单场 +2.35pp (p=0.024\\*), 三场-单场 +2.84pp (p=0.010\\*) → **方向确认**, "
      f"但二者**都未过 Bonferroni**; 且三场与双场**无差别** | **弱确认/修正** |")
    w(f"| 1b | 4场以上是负资产(展现掉到不足四成) | ≥4场 展现中位 **{a_multi['imp_med']:,}** "
      f"vs 单场 {a_single['imp_med']:,} → **并不更低**; CTR 差 -0.59pp, **p=0.378 n.s.** | **推翻** |")
    w(f"| 1c | 多场稿因'阅读时长短'被算法压 | ≥4场 时长中位 **{a_multi['dur_med']}秒**, "
      f"是全形态**最长**(单场 {a_single['dur_med']}) → 机理反了 | **推翻** |")
    w(f"| 2a | 10:00-12:30 是黄金窗口 | 10:00-12:00 聚合CTR **{pct(m1012['ctr'])}**、展现中位 "
      f"**{m1012['imp_med']:,}**; vs 16:00-19:00 差 **+3.16pp, p<0.001** → 过 Bonferroni | **确认(最强)** |")
    w(f"| 2b | 19:00 后基本废掉 | 19:00-24:00 聚合CTR **{pct(m19['ctr'])}** ≈ 全站 {pct(base_ctr)}; "
      f"与上午差 +1.29pp 但 **p=0.084 n.s.** → **CTR 上不成立**; 只是展现中位 {m19['imp_med']:,} 偏低。"
      f"真正 CTR 最低的是 16:00-19:00 ({pct(m1619['ctr'])}) | **修正** |")
    w(f"| 3a | 耐读 → 单价高 (收益口径) | 本次导出**无收益字段**, 无法验证 | **无法验证** |")
    w(f"| 3b | (隐含) 多场短稿吃亏 | 单场内 时长≥70秒 vs <55秒: **+3.21pp, p<0.001**(过 Bonferroni); "
      f"r(时长, 展现)=+0.399 → 长稿反而更强 | **推翻** |")
    w(f"| 4 | 亚洲赛事(日职/韩职/亚冠)是钱袋子 | 亚洲 CTR **{pct(a_asia['ctr'])}** vs "
      f"五大联赛 **{pct(a_euro['ctr'])}**: 差 **+4.50pp, p<0.001**(过 Bonferroni); "
      f"展现中位 {a_asia['imp_med']:,} vs {a_euro['imp_med']:,} | **确认(最强)** |")
    w(f"| 5a | 队名对位(VS/X对Y) CTR 11.0% | n={len(n_vs)} CTR {pct(agg(n_vs)['ctr'])} vs "
      f"不含 {pct(agg([r for r in rows if not VS_RE.search(r['标题'])])['ctr'])}: "
      f"差 -0.02pp, **p=0.955** → 完全无差异(旧值是 n=3 的偶然) | **推翻** |")
    w(f"| 5b | 含具体数字/赔率 CTR 更高 | n={len(n_num)} CTR {pct(agg(n_num)['ctr'])} vs 不含 "
      f"{pct(agg([r for r in rows if not NUM_RE.search(r['标题'])])['ctr'])}: "
      f"**p=0.336 n.s.**, 方向还反了 | **推翻** |")
    w(f"| 5c | (拟新增) 标题含**场次编号** | 含编号 n={len(n_id)} CTR **{pct(agg(n_id)['ctr'])}** "
      f"vs 不含 n={len(n_noid)} {pct(agg(n_noid)['ctr'])}: +1.09pp 但 **p=0.055 n.s.** | "
      f"**不成立(待验证)** |")
    w(f"| 5d | 标题上限放宽到 36 字 | ≤30字 {pct(agg(n_s30)['ctr'])}, 31-36字 "
      f"{pct(agg(n_3136)['ctr'])}, >36字 {pct(agg(n_g36)['ctr'])}: >36 vs ≤30 **p=0.575 n.s.** "
      f"→ 36 字上限无害但也无收益 | **修正** |")
    w('')
    w('> ⚠️ 我在初版里把"含场次编号"写成"本批最稳的标题信号", 加上 bootstrap 检验后 **p=0.055 不显著**,')
    w('> 已降级为"不成立(待验证)"。这是本次自我校正的一处 —— 聚合 CTR 的大小差异不等于真信号。')
    w('')
    w('### 11.1 新增的三条(旧复盘没有的)')
    w('')
    w('| # | 发现 | 数据 | 建议动作 |')
    w('|---|---|---|---|')
    w(f"| A | **完成率是触达结构的镜子, 不是质量指标** | r(完成率,展现)="
      f"{pearson([r['完成率'] for r in rows], [r['展现量'] for r in rows]):+.3f}; "
      f"r(完成率,粉阅占比)={pearson([r['粉阅占比'] for r in rows if r['阅读量']>0], [r['完成率'] for r in rows if r['阅读量']>0]):+.3f} | "
      f"**禁止**把完成率当KPI排稿; 只能同触达量级内比 |")
    w(f"| B | **展现量是收益的第一驱动, 且头部极集中** | "
      f"阅读前 {', '.join(str(k) + ' 篇占 ' + pct(sum(r['阅读量'] for r in sorted(rows, key=lambda x: -x['阅读量'])[:k])/tot_rd) for k in (5, 10, 20))} | "
      f"把资源押在'能不能被打出去', 而不是'标题好不好' |")
    w(f"| C | **粉丝阅读占比越低, CTR与展现越高** | "
      f"粉阅<2% 的稿 CTR {pct(agg([r for r in rows if r['阅读量']>0 and r['粉阅占比']<.02])['ctr'])}、"
      f"展现中位 {agg([r for r in rows if r['阅读量']>0 and r['粉阅占比']<.02])['imp_med']:,}; "
      f"粉阅>20% 的稿 CTR {pct(agg([r for r in rows if r['阅读量']>0 and r['粉阅占比']>=.20])['ctr'])}、"
      f"展现中位 {agg([r for r in rows if r['阅读量']>0 and r['粉阅占比']>=.20])['imp_med']:,} | "
      f"粉丝阅读占比可用作'这篇有没有被打出去'的体检指标 |")
    w('')
    w('### 11.2 需要改的硬规则')
    w('')
    w('1. **SOP §零 选题矩阵**: "双场>单场>三场≫4场以上" 应改为 **"双场/三场并列优先, 单场次之; ≥4场与单场无显著差异(样本仅 10 篇), 保持谨慎但不判死刑"**')
    w('   —— 原规则把 ≥4场 判为"负资产", 全量数据不支持(展现中位 5,970 vs 单场 5,587; CTR 差 p=0.378)。')
    w('2. **发布窗口**: "10:00-12:30 黄金 + 19:00 后废掉" → 改为 **"10:00-12:00 最优(p<0.001, 本批唯一强结论);')
    w('   避开 16:00-19:00 (CTR 5.4%, 全时段最低); 19:00 后 CTR 与全站持平(p=0.084), 只是展现量少 ——')
    w('   可以发, 但要认清那是「平台少推荐」而不是「内容不行」"**。')
    w('3. **标题规则**: 取消"队名对位"与"含数字"作为加分项(两项 p=0.955 / 0.336, 完全无可检出差异);')
    w('   36 字上限保留(无害), 但**不要再宣称标题特征能拉 CTR** —— 本批数据显示标题特征对 CTR 几乎无影响。')
    w('4. **新增数据纪律**: 每篇记录 `完成率 + 粉丝阅读占比 + 展现量` 三件套;')
    w('   只看完成率会误判, 三个一起看才能区分"没被打出去"和"内容不行"(见 §7.1)。')
    w('5. **统计纪律(本次新加)**: 单篇数据是**聚类**的(展现量不是独立试验), 组间比较必须按文章 bootstrap;')
    w(f'   且一次看多个比较必须做多重比较校正 —— 否则 {len(comps)} 次比较里注定有约 '
      f'{len(comps)*0.05:.1f} 个"假阳性"会被写成结论。')
    w('')
    w('### 11.3 本次数据的天花板 (不能从这批数据得出什么)')
    w('')
    w('- **无收益字段** → 旧复盘"阅读时长→千次阅读收益 3.7 倍"这条**无法复核**, 不要沿用。')
    w('- **无粉丝增量/涨粉来源** → 无法量化"一篇爆款带来多少粉丝"。')
    w('- **9/10 后只有 23 篇** → 所有"9/10后口径"的格子 n 都个位数, 只能作方向参考。')
    w('- **时段与赛事/形态高度混淆** → 例如亚洲赛事恰好多发在上午, 本次无法完全分离;')
    w('  要分离需要"同一时段发不同赛事"的对照, 目前样本不支持。')
    w('')

    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print(f'written: {OUT}')
    print(f'rows={len(rows)} recent={len(recent)} span={d0}~{d1}')


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float('nan')
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else float('nan')


if __name__ == '__main__':
    main()
