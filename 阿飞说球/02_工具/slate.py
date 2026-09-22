# -*- coding: utf-8 -*-
"""slate.py — 当日/当前在售场次: 全盘口 + 角色感知结构判读(紧凑表)

用法:
  python slate.py                 # 当前在售全部场次
  python slate.py 周二 周三        # 只看编号前缀命中的
  python slate.py --json out.json  # 同时落盘原始 JSON

输出每场一行: 编号 赛事 开球 对阵 | 胜平负去水 | 让球线 让球方赢盘/走水/受让方赢盘 | 更重一侧(差) | 单关
结构判读按**角色感知**(见 workflow 坑#38/#45): line<0 时"让胜"=让球方赢够; line>0 时"让负"=让球方赢够。
"""
import io, json, os, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jingcai_fetch import fetch, flat  # noqa: E402


def dvig(o):
    if not o:
        return None, None
    try:
        v = [float(o[k]) for k in 'hda']
    except (KeyError, TypeError, ValueError):
        return None, None
    if any(x <= 1.0 for x in v):
        return None, None
    s = sum(1 / x for x in v)
    return {k: (1 / float(o[k])) / s for k in 'hda'}, s


def main():
    a = sys.argv[1:]
    save = a[a.index('--json') + 1] if '--json' in a else None
    kws = [x for x in a if not x.startswith('--') and x != save]
    j = fetch()
    if save:
        io.open(save, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=1))
    ms = flat(j)
    print('%-8s %-10s %-12s %-30s %-18s %-24s %-22s %s' % (
        '编号', '赛事', '开球', '对阵', '胜平负去水', '让球方/走水/受让方', '更重一侧(差)', '单关'))
    print('-' * 150)
    for m in ms:
        num = m['matchNumStr']
        if kws and not any(k in num for k in kws):
            continue
        q, _ = dvig(m.get('had'))
        qs = '%.1f/%.1f/%.1f' % (q['h'] * 100, q['d'] * 100, q['a'] * 100) if q else '—'
        hh = m.get('hhad') or {}
        q2, _ = dvig(hh)
        if q2:
            line = int(float(hh.get('goalLine', 0)))
            giver, push, taker = (q2['h'], q2['d'], q2['a']) if line < 0 else (q2['a'], q2['d'], q2['h'])
            heavy = '让球方赢够' if giver > taker else '受让方守住'
            role = '%+.0f线 %.1f/%.1f/%.1f' % (line, giver * 100, push * 100, taker * 100)
            hd = '%s(%.1f)' % (heavy, abs(giver - taker) * 100)
        else:
            role, hd = '—', '—'
        single = '可单关' if str(m.get('bettingSingle')) == '1' else '仅串关'
        print('%-8s %-10s %-12s %-30s %-18s %-24s %-22s %s' % (
            num, (m.get('leagueAbbName') or '')[:9], '%s %s' % (m.get('matchDate'), (m.get('matchTime') or '')[:5]),
            '%s vs %s' % ((m.get('homeTeamAllName') or '')[:12], (m.get('awayTeamAllName') or '')[:12]),
            qs, role, hd, single))
    return 0


if __name__ == '__main__':
    sys.exit(main())
