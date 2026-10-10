# -*- coding: utf-8 -*-
"""竞彩官方全盘口抓取 (webapi.sporttery.cn: getMatchCalculatorV1.qry)

用法:
  python jingcai_fetch.py                       # 列当日场次(编号/日期/对阵/开售状态)
  python jingcai_fetch.py 曼联                   # 命中队名的场次, 打印全部盘口
  python jingcai_fetch.py 曼联 --json out.json   # 同时落盘原始 JSON
"""
import sys, io, json, requests

POOLS = 'had,hhad,ttg,crs,hafu'
URL = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
H = {'User-Agent': UA, 'Referer': 'https://www.sporttery.cn/jc/jsq/zqspf/',
     'Accept': 'application/json, text/plain, */*'}


def fetch():
    s = requests.Session()
    s.headers.update(H)
    s.get('https://www.sporttery.cn/jc/jsq/zqspf/', timeout=15)   # 预热拿 cookie
    r = s.get(URL, params={'channel': 'c', 'poolCode': POOLS}, timeout=20)
    r.raise_for_status()
    return r.json()


def flat(j):
    out = []
    v = j.get('value') or {}
    for g in (v.get('matchInfoList') or []):
        for m in (g.get('subMatchList') or []):
            out.append(m)
    return out


def main():
    kw, save = None, None
    a = sys.argv[1:]
    i = 0
    while i < len(a):
        if a[i] == '--json' and i + 1 < len(a):
            save, i = a[i + 1], i + 2
            continue
        kw, i = a[i], i + 1
    j = fetch()
    if save:
        io.open(save, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=1))
    ms = flat(j)
    if not ms:
        print('!! 未取到场次, 顶层键: %s' % list((j.get('value') or j).keys()))
        return
    print('场次数 %d' % len(ms))
    if not kw:
        for m in ms:
            print('%s %s %s vs %s sales=%s' % (m.get('matchNumStr'), m.get('matchDate'),
                  m.get('homeTeamAllName'), m.get('awayTeamAllName'), m.get('sellStatus')))
        return
    hit = [m for m in ms if kw in (m.get('homeTeamAllName') or '') + (m.get('awayTeamAllName') or '')]
    if not hit:
        print('!! 未命中 %s' % kw)
        return
    for m in hit:
        print('=== %s %s %s %s vs %s bettingSingle=%s 联赛=%s' % (
            m.get('matchNumStr'), m.get('matchDate'), m.get('matchTime'),
            m.get('homeTeamAllName'), m.get('awayTeamAllName'),
            m.get('bettingSingle'), m.get('leagueAllName')))
        for p in POOLS.split(','):
            print('  %-5s %s' % (p, json.dumps(m.get(p), ensure_ascii=False)))


if __name__ == '__main__':
    main()
