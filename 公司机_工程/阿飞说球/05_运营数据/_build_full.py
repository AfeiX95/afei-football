# -*- coding: utf-8 -*-
"""头条全量数据: 合并分段转录 + 两重校验

校验1(内部一致性): 点击率必须 ≈ 阅读量/展现量
      —— 抓"展现量/阅读量/点击率"三个字段的转录错误。
校验2(外部交叉): 与既有台账 头条_明细_20260917.tsv (9/17 取数, 30 篇) 比对
      —— 后者是更早的快照, 因此必须满足: 新展现≥旧展现, 新阅读≥旧阅读,
         且 时长/点赞/评论 一致(这些字段不随曝光增长而变)。
"""
import io
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
PARTS = ['_tt_part1.tsv', '_tt_part2.tsv', '_tt_part3.tsv']
OUT = os.path.join(BASE, '头条_全量_20260505-0919.tsv')
OLD = os.path.join(BASE, '头条_明细_20260917.tsv')

COLS = ['标题', '发布时间', 'ID', '展现量', '粉丝展现量', '阅读量', '粉丝阅读量',
        '点击率', '完成率', '时长', '点赞', '评论', '转发', '分享', '收藏']
INT_COLS = ['展现量', '粉丝展现量', '阅读量', '粉丝阅读量', '时长',
            '点赞', '评论', '转发', '分享', '收藏']
FLOAT_COLS = ['点击率', '完成率']


def load_parts():
    rows = []
    for i, fn in enumerate(PARTS):
        path = os.path.join(BASE, fn)
        with io.open(path, encoding='utf-8') as f:
            for ln, line in enumerate(f, 1):
                line = line.rstrip('\n')
                if not line.strip():
                    continue
                if line.startswith('标题\t'):        # part1 的表头
                    continue
                p = line.split('\t')
                if len(p) != len(COLS):
                    print(f'  ⚠ 列数异常 {fn}:{ln} -> {len(p)} 列, 已跳过')
                    continue
                r = dict(zip(COLS, p))
                r['_src'] = f'{fn}:{ln}'
                for c in INT_COLS:
                    try:
                        r[c] = int(r[c])
                    except ValueError:
                        r[c] = None
                for c in FLOAT_COLS:
                    try:
                        r[c] = float(r[c])
                    except ValueError:
                        r[c] = None
                rows.append(r)
    return rows


def check_ctr(rows):
    """校验1: 点击率 ≈ 阅读量/展现量"""
    bad = []
    for r in rows:
        imp, rd, ctr = r['展现量'], r['阅读量'], r['点击率']
        if not imp or rd is None or ctr is None:
            continue
        actual = rd / imp
        # 源数据点击率只有 2 位小数, 容差取 ±0.005 + 极小量
        if abs(actual - ctr) > 0.0055:
            bad.append((r, actual))
    return bad


def check_old(rows):
    """校验2: 与 9/17 旧台账比对"""
    old = []
    with io.open(OLD, encoding='utf-8') as f:
        next(f)
        for line in f:
            p = line.rstrip('\n').split('\t')
            if len(p) < 10:
                continue
            tm = p[1]
            mm, ss = p[6].split(':')
            old.append({'date': p[0], 'hm': tm, 'title': p[2],
                        'imp': int(p[3]), 'read': int(p[4]),
                        'ctr': p[5], 'dur': int(mm) * 60 + int(ss),
                        'like': int(p[7]), 'cmt': int(p[8]), 'rev': p[9]})
    # 用发布时间(时:分)建索引, 旧台账 9/16、9/17 无时间 → 退回用标题
    by_hm, by_title = {}, {}
    for r in rows:
        t = r['发布时间']
        if t and len(t) >= 16:
            by_hm[(t[:10], t[11:16])] = r
        by_title[r['标题']] = r
    results = []
    for o in old:
        key = (o['date'], o['hm'])
        n = by_hm.get(key)
        how = 'time'
        if not n:
            n = by_title.get(o['title'])
            how = 'title'
        results.append((o, n, how))
    return results


def main():
    L = []
    def w(s=''):
        L.append(s)
        print(s.encode('ascii', 'replace').decode('ascii'))

    w('=' * 100)
    w('【合并】')
    rows = load_parts()
    # 去重(ID 唯一)
    seen, ded = set(), []
    for r in rows:
        if r['ID'] in seen:
            w(f"  ! 重复 ID {r['ID']} @ {r['_src']}, 跳过")
            continue
        seen.add(r['ID'])
        ded.append(r)
    w(f'  part1+2+3 = {len(rows)} 行 -> 去重后 {len(ded)} 行')

    # 排序: 发布时间倒序
    def key(r):
        try:
            return datetime.strptime(r['发布时间'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime.min
    ded.sort(key=key, reverse=True)
    dates = [r['发布时间'][:10] for r in ded if r['发布时间']]
    w(f"  时间跨度: {min(dates)} ~ {max(dates)}")

    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write('\t'.join(COLS) + '\n')
        for r in ded:
            f.write('\t'.join(str(r[c]) for c in COLS) + '\n')
    w(f'  已写出: {OUT}')

    # ---------- 校验1 ----------
    w('')
    w('=' * 100)
    w('【校验1】点击率 = 阅读量/展现量')
    bad = check_ctr(ded)
    ok = len([r for r in ded if r['展现量'] and r['阅读量'] is not None and r['点击率'] is not None]) - len(bad)
    w(f'  可验算 {ok + len(bad)} 行 | 通过 {ok} | 不一致 {len(bad)}')
    if bad:
        w('')
        w('  | 标题 | 展现 | 阅读 | 源CTR | 实算CTR | 出处 |')
        w('  |---|---|---|---|---|---|')
        for r, actual in bad:
            w(f"  | {r['标题'][:44]} | {r['展现量']} | {r['阅读量']} | {r['点击率']:.3f} | "
              f"{actual:.4f} | {r['_src']} |")
        w('')
        w('  > 说明: 源后台点击率只给 2 位小数, 4.92% 与 4.0% 的差距超出舍入范围,')
        w('  > 属**源数据自身不一致**(或该行转录存疑)。分析一律用 **实算 CTR = 阅读/展现**, 不依赖此字段。')

    # ---------- 校验2 ----------
    w('')
    w('=' * 100)
    w('【校验2】与 9/17 旧台账交叉比对')
    w('  规则: 旧台账是更早快照 → 必须 新展现≥旧展现, 新阅读≥旧阅读, 且 时长/点赞/评论 完全一致')
    w('  (时长/赞/评 不随曝光累积而变, 是最好的转录指纹)')
    w('')
    res = check_old(ded)
    hit = sum(1 for _, n, _ in res if n)
    w(f'  旧台账 {len(res)} 行 | 匹配到 {hit} 行 | 未匹配 {len(res) - hit}')
    w('')
    w('  | 标题(旧台账) | 展现 旧→新 | 阅读 旧→新 | 时长 | 赞/评 | 判定 |')
    w('  |---|---|---|---|---|---|')
    prob = []
    for o, n, how in res:
        if not n:
            w(f"  | {o['title'][:38]} | — | — | — | — | 未匹配 |")
            prob.append((o, n, '未匹配'))
            continue
        imp_ok = n['展现量'] >= o['imp']
        rd_ok = n['阅读量'] >= o['read']
        dur_ok = n['时长'] == o['dur']
        lk_ok = n['点赞'] == o['like'] and n['评论'] == o['cmt']
        verdict = 'OK' if (imp_ok and rd_ok and dur_ok and lk_ok) else '需查'
        if verdict != 'OK':
            prob.append((o, n, f"imp{imp_ok} rd{rd_ok} dur{dur_ok} lk{lk_ok}"))
        w('  | %s | %d→%d | %d→%d | %s | %s | %s |' % (
            o['title'][:38], o['imp'], n['展现量'], o['read'], n['阅读量'],
            'ok' if dur_ok else f"{o['dur']}→{n['时长']}",
            'ok' if lk_ok else f"{o['like']}/{o['cmt']}→{n['点赞']}/{n['评论']}",
            verdict))
    w('')
    if prob:
        w(f'  ! 需人工确认 {len(prob)} 行:')
        for o, n, why in prob:
            w(f"    - {o['title'][:50]} | {why}")
    else:
        w('  全部一致')

    w('')
    w('=' * 100)
    w(f'结论: 校验1 {"全通过" if not bad else str(len(bad)) + " 行不一致"} | '
      f'校验2 {"全通过" if not prob else str(len(prob)) + " 行待确认"} | 总行数 {len(ded)}')

    with io.open(os.path.join(BASE, '_校验报告.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    return 0 if (not bad and not prob) else 2


if __name__ == '__main__':
    sys.exit(main())
