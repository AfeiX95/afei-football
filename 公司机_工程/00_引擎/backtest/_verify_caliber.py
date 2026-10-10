# -*- coding: utf-8 -*-
"""口径判决 + 全量抓取 2026-09-18 ~ 2026-09-20

判决逻辑:
  winFlag 是官方对 h/d/a 那三列赔率所对应赛果的判定。
  若 winFlag == 胜平负(不让球)结果 → h/d/a 是【胜平负】赔率
  若 winFlag == 让球后结果         → h/d/a 是【让球胜平负】赔率
"""
import json
import os
import ssl
import urllib.parse
import urllib.request

API = 'https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36'
BASE = os.path.dirname(os.path.abspath(__file__))
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def fetch(begin, end, page_no=1, page_size=100, is_fix=0):
    q = urllib.parse.urlencode({
        'matchBeginDate': begin, 'matchEndDate': end, 'leagueId': '',
        'pageSize': page_size, 'pageNo': page_no, 'isFix': is_fix,
        'pcOrWap': 1, 'matchPage': 1,
    })
    req = urllib.request.Request(API + '?' + q, headers={
        'User-Agent': UA,
        'Referer': 'https://www.sporttery.cn/jc/zqsgkj/',
        'Accept': 'application/json, text/plain, */*',
    })
    with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
        return json.loads(r.read().decode('utf-8'))


def fetch_all(begin, end, is_fix=0):
    """拉全部页, 不过滤"""
    out, page = [], 1
    while True:
        d = fetch(begin, end, page, 100, is_fix)
        v = d.get('value') or {}
        out.extend(v.get('matchResult') or [])
        if page >= (v.get('pages') or 1):
            break
        page += 1
    return out


def outcome(h, a):
    return 'H' if h > a else ('A' if h < a else 'D')


def main():
    report = []

    def say(s=''):
        report.append(s)

    # ---------- 0. 探测 isFix 两种取值下的总数 ----------
    say('## 0. 抓取范围探测 (2026-09-18 ~ 2026-09-20)')
    for is_fix in (0, 1):
        ms = fetch_all('2026-09-18', '2026-09-20', is_fix)
        done = [m for m in ms if m.get('matchResultStatus') == '2']
        withodds = [m for m in done if (m.get('h') or '').strip()]
        # 按日期分布
        bydate = {}
        for m in done:
            bydate[m['matchDate']] = bydate.get(m['matchDate'], 0) + 1
        say(f'- isFix={is_fix}: 返回 {len(ms)} 场 | 已完场 {len(done)} | 有赔率 {len(withodds)}')
        say(f'  按日期: {dict(sorted(bydate.items()))}')

    # ---------- 1. 用主口径(isFix=0, 全部已完场)做口径判决 ----------
    ms = [m for m in fetch_all('2026-09-18', '2026-09-20', 0)
          if m.get('matchResultStatus') == '2']
    say('')
    say(f'## 1. 口径判决 (样本 {len(ms)} 场已完场)')

    tsv_lines = []
    both_ok = 0
    match_plain = 0
    match_hcap = 0
    neither = 0
    hcap_vs_plain_diff = []
    for m in ms:
        try:
            fh, fa = map(int, (m.get('sectionsNo999') or '').split(':'))
        except ValueError:
            continue
        gl = m.get('goalLine') or '0'
        try:
            hcap = int(gl)
        except ValueError:
            hcap = 0
        plain = outcome(fh, fa)
        net = (fh + hcap) - fa
        hres = 'H' if net > 0 else ('A' if net < 0 else 'D')
        wf = (m.get('winFlag') or '').strip()
        if wf:
            if wf == plain:
                match_plain += 1
            if wf == hres:
                match_hcap += 1
            if wf == plain and wf == hres:
                both_ok += 1
            elif wf != plain and wf != hres:
                neither += 1
        if plain != hres:
            hcap_vs_plain_diff.append((m.get('matchNumStr'), gl, f'{fh}:{fa}', plain, hres, wf))

    say(f'- winFlag 与【胜平负】结果一致: **{match_plain}** 场')
    say(f'- winFlag 与【让球后】结果一致: **{match_hcap}** 场')
    say(f'- 两者同时一致(让球不影响结果): {both_ok} 场 | 与两者都不一致: {neither} 场')
    say('')
    say(f'### 判决性证据: 让球会改变结果的场次共 {len(hcap_vs_plain_diff)} 场')
    say('| 编号 | 让球 | 全场 | 胜平负 | 让球后 | 官方winFlag |')
    say('|---|---|---|---|---|---|')
    for row in hcap_vs_plain_diff:
        say('| ' + ' | '.join(str(x) for x in row) + ' |')

    # ---------- 2. 导出原始 TSV ----------
    for m in sorted(ms, key=lambda x: (x['matchDate'], x.get('matchNum', ''))):
        tsv_lines.append('\t'.join([
            m.get('matchDate', ''), m.get('matchNumStr', ''), m.get('leagueNameAbbr', ''),
            f"{m.get('allHomeTeam')}({m.get('goalLine')})VS{m.get('allAwayTeam')}",
            m.get('sectionsNo1', ''), m.get('sectionsNo999', ''),
            m.get('h', '') or '', m.get('d', '') or '', m.get('a', '') or '',
            str(m.get('bettingSingle')), m.get('winFlag', ''), str(m.get('matchId', '')),
        ]))
    raw = os.path.join(BASE, '_raw_20260918_0920.tsv')
    with open(raw, 'w', encoding='utf-8') as f:
        f.write('date\tno\tleague\tmatch\tht\tft\th\td\ta\tsingle\twinFlag\tmatchId\n')
        f.write('\n'.join(tsv_lines) + '\n')

    txt = os.path.join(BASE, '_caliber_verdict.md')
    with open(txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report) + '\n')

    print(f'written: {raw}')
    print(f'written: {txt}')
    print(f'SUMMARY plain_match={match_plain} hcap_match={match_hcap} total_flagged={match_plain + 0}')
    print(f'decisive_rows={len(hcap_vs_plain_diff)}')


if __name__ == '__main__':
    main()
