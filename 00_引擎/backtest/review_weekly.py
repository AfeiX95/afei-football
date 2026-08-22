# -*- coding: utf-8 -*-
"""
review_weekly.py — 每周自动复盘入库 (cron 第二步, no_agent 静默模式)
=====================================================================
流程: 抓近10天竞彩赛果(1次API) → 遍历 match_configs/ 所有已分析场次
      → 有赛果且无复盘块 → 生成复盘 → 增量入库 → 留档 reviews/
输出: 仅在有新增复盘时输出(静默模式); --verbose 打印全部过程
用法:
    python review_weekly.py            # 静默(有新增才输出)
    python review_weekly.py --verbose  # 打印过程
"""
import argparse
import json
import os
import sys
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))       # 00_引擎/backtest
PROJECT = os.path.dirname(os.path.dirname(BASE))        # D:\Hermes\football
TOOL_DIR = os.path.join(PROJECT, '阿飞说球', '02_工具')
KB_DIR = os.path.join(TOOL_DIR, 'kb')
sys.path.insert(0, KB_DIR)
sys.path.insert(0, TOOL_DIR)
sys.path.insert(0, BASE)


def norm(s):
    return (s or '').replace(' ', '')


def name_match(cfg_name, api_name):
    """config 队名 vs 竞彩 API 队名匹配: 包含 或 简称子序列
    例: "巴竞技" ⊂ "巴拉纳竞技", "弗鲁米嫩" ⊂ "弗鲁米嫩塞" """
    a, b = norm(cfg_name), norm(api_name)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    it = iter(b)
    return all(ch in it for ch in a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--days', type=int, default=10, help='赛果回溯天数')
    args = ap.parse_args()
    log = print if args.verbose else (lambda *a, **k: None)

    from kb_core import KB_DIR as _KB_DIR  # noqa: F401  (确保 kb_core 可导入)
    from review_match import build_review, ingest
    from fetch_results import fetch_all
    from afei_generator import run_model

    # 1. 抓一次赛果
    end = date.today().isoformat()
    begin = (date.today() - timedelta(days=args.days)).isoformat()
    log(f'抓取赛果 {begin} ~ {end} ...')
    try:
        matches = fetch_all(begin, end, only_single=False)
    except Exception as e:
        print(f'⚠ 赛果抓取失败: {e}')
        return 1
    results = []
    for m in matches:
        ft = m.get('sectionsNo999') or ''
        if ':' not in ft:
            continue
        results.append((norm(m.get('allHomeTeam') or m.get('homeTeam')),
                        norm(m.get('allAwayTeam') or m.get('awayTeam')),
                        ft.replace('-', ':'), m['matchDate'],
                        m.get('leagueNameAbbr') or ''))
    log(f'已完赛场次 {len(results)} 场')

    # 2. 已复盘场次(幂等)
    done = set()
    with open(os.path.join(_KB_DIR, 'kb_chunks.json'), encoding='utf-8') as f:
        for ck in json.load(f):
            if ck['section'] == '赛后复盘':
                done.add(ck['match'])

    # 3. 遍历 configs
    config_dir = os.path.join(TOOL_DIR, 'match_configs')
    configs = sorted(f for f in os.listdir(config_dir) if f.endswith('.json'))
    log(f'待检查 config {len(configs)} 个')
    added, noresult, skipped = [], 0, 0

    for fn in configs:
        p = os.path.join(config_dir, fn)
        with open(p, encoding='utf-8') as f:
            c = json.load(f)
        home = c['teams']['home']['name']
        away = c['teams']['away']['name']
        match = f'{home}vs{away}'
        if match in done:
            skipped += 1
            log(f'  [已有复盘] {match}')
            continue
        hit = None
        for rh, ra, ft, dt, lg in results:
            if name_match(home, rh) and name_match(away, ra):
                hit = (ft, dt, lg)
                break
        if not hit:
            noresult += 1
            log(f'  [无赛果] {match}')
            continue

        # 4. 生成复盘 + 留档 + 入库
        m = run_model(c)
        text = build_review(c, m, hit[0], hit[1])
        rec = {
            'match': match, 'date': hit[1], 'score': hit[0],
            'league': hit[2], 'config': p, 'review_text': text,
            'pH': m['pH'], 'pD': m['pD'], 'pA': m['pA'],
            'pM': m['pM'], 'pM_cal': m['pM_cal'], 'p_over25': m['p_over25'],
        }
        reviews_dir = os.path.join(BASE, 'reviews')
        os.makedirs(reviews_dir, exist_ok=True)
        with open(os.path.join(reviews_dir, match + '.json'), 'w', encoding='utf-8') as f:
            json.dump(rec, f, ensure_ascii=False, indent=1)
        chunk = [{'text': text, 'match': match, 'section': '赛后复盘',
                  'source': os.path.join('00_引擎', 'backtest', 'reviews', match + '.json')}]
        if ingest(chunk):
            added.append((match, hit[1], hit[0]))
            log(f'  [✔入库] {match} {hit[1]} {hit[0]}')

    # 5. 静默输出: 仅新增时打印
    if added:
        lines = [f'✅ 自动复盘入库 {len(added)} 场:']
        lines += [f'  · {match} ({dt}) {sc}' for match, dt, sc in added]
        if noresult:
            lines.append(f'(另有 {noresult} 场尚无赛果, 下周一自动再试)')
        print('\n'.join(lines))
    else:
        log(f'无新增复盘 (跳过{skipped}/无赛果{noresult})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
