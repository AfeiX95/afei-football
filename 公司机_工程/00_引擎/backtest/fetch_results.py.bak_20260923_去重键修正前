# -*- coding: utf-8 -*-
"""
竞彩足球赛果抓取器 — 追加到回测数据集
用法:
    python fetch_results.py --begin 2026-08-03 --end 2026-08-05   # 指定范围
    python fetch_results.py --days 7                                # 最近7天
输出: 追加到 00_引擎/backtest/matches_YYYYMMDD_YYYYMMDD.tsv (按比赛编号去重)
"""
import argparse
import json
import os
import re
import sys
import time

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
API = 'https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry'
HOME = 'https://www.sporttery.cn/'
REFERER = 'https://www.sporttery.cn/jc/zqsgkj/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36',
}

def fetch_page(sess, begin, end, page_no, page_size=30):
    params = {
        'matchBeginDate': begin, 'matchEndDate': end, 'leagueId': '',
        'pageSize': page_size, 'pageNo': page_no, 'isFix': 0,
        'pcOrWap': 1, 'matchPage': 1,
    }
    r = sess.get(API, params=params, headers={'Referer': REFERER}, timeout=20)
    r.raise_for_status()
    d = r.json()
    if not d.get('success'):
        raise RuntimeError(f"API失败: {d.get('errorMessage')}")
    return d['value']

def fetch_all(begin, end, only_single=True):
    """抓取全部页, 返回比赛字典列表"""
    sess = requests.Session()
    sess.headers.update(HEADERS)
    sess.get(HOME, timeout=20)  # 初始化会话
    matches = []
    page_no = 1
    while True:
        v = fetch_page(sess, begin, end, page_no)
        page_matches = v.get('matchResult') or []
        matches.extend(page_matches)
        if page_no >= v.get('pages', 1):
            break
        page_no += 1
        time.sleep(0.5)
    # 过滤已开奖 + 单固(与历史样本一致)
    out = []
    for m in matches:
        if m.get('matchResultStatus') != '2':      # 2=已完场
            continue
        if only_single and m.get('bettingSingle') != 1:
            continue
        out.append(m)
    return out

def to_tsv_line(m):
    """比赛字典 → tsv 行"""
    date = m['matchDate']
    no = m.get('matchNumStr', '')
    league = m.get('leagueNameAbbr') or m.get('leagueName', '')
    gl = m.get('goalLine', '0')
    home = m.get('allHomeTeam') or m.get('homeTeam', '')
    away = m.get('allAwayTeam') or m.get('awayTeam', '')
    hva = f"{home}({gl})VS{away}"
    ht = m.get('sectionsNo1', '')
    ft = m.get('sectionsNo999', '')
    h = m.get('h', '--'); d = m.get('d', '--'); a = m.get('a', '--')
    return f"{date}\t{no}\t{league}\t{hva}\t{ht}\t{ft}\t{h}\t{d}\t{a}\tdone"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--begin'); ap.add_argument('--end')
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--all-single', action='store_true', help='不过滤单固')
    args = ap.parse_args()

    from datetime import date, timedelta
    if args.begin and args.end:
        begin, end = args.begin, args.end
    else:
        end = date.today().isoformat()
        begin = (date.today() - timedelta(days=args.days)).isoformat()

    print(f"抓取 {begin} ~ {end} ...")
    matches = fetch_all(begin, end, only_single=not args.all_single)
    print(f"API返回已开奖场次: {len(matches)}")

    # 目标文件: 包含范围的 tsv(按年份月份归档)
    tsv = os.path.join(BASE, f"matches_{begin.replace('-','')}_latest.tsv")
    # 读已有(避免重复)
    existing = set()
    if os.path.exists(tsv):
        with open(tsv, encoding='utf-8') as f:
            for line in f:
                parts = line.rstrip('\n').split('\t')
                if len(parts) >= 6:
                    existing.add((parts[0], parts[3]))  # (date, 对阵)

    added = 0
    with open(tsv, 'a', encoding='utf-8') as f:
        for m in matches:
            hva = f"{(m.get('allHomeTeam') or m.get('homeTeam'))}({m.get('goalLine', '0')})VS{(m.get('allAwayTeam') or m.get('awayTeam'))}"
            key = (m['matchDate'], hva)
            if key in existing:
                continue
            f.write(to_tsv_line(m) + '\n')
            added += 1
            existing.add(key)

    print(f"新增 {added} 场 → {tsv}")
    if added == 0:
        print("(无新增,数据已是最新)")

if __name__ == '__main__':
    main()
