# -*- coding: utf-8 -*-
"""form.py — 官方近10场取数与成色摘要(含"共同对手"自动对照)

用法:
  python form.py 周二001 周三002        # 按竞彩编号(自动从当前在售列表定位)
  python form.py --all                  # 当前在售全部场次

固化了两条踩过的坑:
  ① 数据在 `value.matchList`(不是 teamMatchResult/matchResultList);
  ② 判主客**必须用竞彩简称**(homeAbbCnName/awayAbbCnName vs homeTeamAbbName/awayTeamAbbName)——
     `uniformHomeTeamId/uniformAwayTeamId` 与 `gmTeamId` 不是同一套 ID; 全称子串匹配也会失败(沙特阿拉伯亚足 vs 沙特亚)。
输出: 每队一行摘要 + 逐场明细 + 本节"共同对手"对照(同组同对手时最有用)。
"""
import io, os, sys, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requests  # noqa: E402
from jingcai_fetch import fetch, flat  # noqa: E402

B = 'https://webapi.sporttery.cn/gateway/uniform/football'


def team_form(s, tid):
    r = s.get(B + '/team/getMatchResultV1.qry', params={'gmTeamId': tid, 'termLimits': 10}, timeout=20)
    return ((r.json().get('value') or {}).get('matchList')) or []


def digest(rows, allname, abb):
    keys = {allname, abb}
    out = {'lines': [], 'w': 0, 'd': 0, 'l': 0, 'gf': 0, 'ga': 0,
           'hw': 0, 'hd': 0, 'hl': 0, 'aw': 0, 'ad': 0, 'al': 0, 'y26': 0, 'opp': {}}
    for r0 in rows:
        sc = r0.get('sectionsNo999') or ''
        if ':' not in sc:
            continue
        fh, fa = (int(x) for x in sc.split(':')[:2])
        h, a = r0.get('homeAbbCnName') or '', r0.get('awayAbbCnName') or ''
        if h in keys:
            home, my, op, opp = True, fh, fa, a
        elif a in keys:
            home, my, op, opp = False, fa, fh, h
        else:
            continue
        res = '胜' if my > op else ('平' if my == op else '负')
        out['w' if res == '胜' else ('d' if res == '平' else 'l')] += 1
        out['gf'] += my; out['ga'] += op
        k = ('h' if home else 'a') + ('w' if res == '胜' else ('d' if res == '平' else 'l'))
        out[k] += 1
        if (r0.get('matchDate') or '') >= '2026-01-01':
            out['y26'] += 1
        out['opp'].setdefault(opp, []).append((r0.get('matchDate'), home, my, op, res))
        out['lines'].append('   %s %-8s %-3s %-10s %d:%d %s' % (
            r0.get('matchDate'), (r0.get('leagueAbbCnName') or '')[:8],
            '主' if home else '客', opp[:10], my, op, res))
    return out


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return 2
    s = requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0',
                      'Referer': 'https://www.sporttery.cn/jc/jsq/zqspj/', 'Accept': 'application/json'})
    ms = flat(fetch())
    nums = [m['matchNumStr'] for m in ms] if args == ['--all'] else args
    for num in nums:
        m = next((x for x in ms if x['matchNumStr'] == num), None)
        if not m:
            print('!! 未命中 %s(在售: %s)' % (num, ' '.join(x['matchNumStr'] for x in ms)))
            continue
        print('=' * 92)
        print('%s %s %s %s vs %s  线%s  组别 %s / %s' % (
            num, m['leagueAbbName'], m['matchDate'], m['homeTeamAllName'], m['awayTeamAllName'],
            (m.get('hhad') or {}).get('goalLine'), m['homeRank'], m['awayRank']))
        print('=' * 92)
        D = {}
        for tid, an, ab in ((m['homeTeamId'], m['homeTeamAllName'], m['homeTeamAbbName']),
                            (m['awayTeamId'], m['awayTeamAllName'], m['awayTeamAbbName'])):
            d = digest(team_form(s, tid), an, ab)
            D[an] = d
            n = max(1, d['w'] + d['d'] + d['l'])
            print('\n--- %s (简称%s) 近%d场 %d胜%d平%d负 进%d失%d 场均%.2f/%.2f | 主%d/%d/%d 客%d/%d/%d | 2026年内%d场' % (
                an, ab, d['w'] + d['d'] + d['l'], d['w'], d['d'], d['l'], d['gf'], d['ga'],
                d['gf'] / n, d['ga'] / n, d['hw'], d['hd'], d['hl'], d['aw'], d['ad'], d['al'], d['y26']))
            print('\n'.join(d['lines']))
            time.sleep(0.2)
        # 共同对手对照
        hn, an = m['homeTeamAllName'], m['awayTeamAllName']
        shared = set(D[hn]['opp']) & set(D[an]['opp'])
        if shared:
            print('\n★ 共同对手对照(同批对手最能说明问题):')
            for op in sorted(shared):
                for side, name in (('主', hn), ('客', an)):
                    for dt, home, my, o, res in D[name]['opp'][op]:
                        print('   %-10s | %-10s %s %s %d:%d %s' % (
                            op[:10], name[:10], dt, '主' if home else '客', my, o, res))
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
