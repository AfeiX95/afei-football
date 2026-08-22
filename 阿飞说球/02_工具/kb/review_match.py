# -*- coding: utf-8 -*-
"""
review_match.py — 赛后复盘入库 v1.0 (验证闭环)
===============================================
用法:
    python review_match.py --home 横滨水手 --away 鹿岛鹿角 --score 1-1   # 手动给比分
    python review_match.py --home X --away Y --auto                      # 自动从竞彩API抓赛果
    python review_match.py --home X --away Y --score 2:1 --dry-run       # 只预览, 不入库

流程:
    match_configs 找 config → run_model 重算赛前预测 → 对比实际比分
    → 生成复盘结论块(命中/偏差/教训) → 增量进知识库(FAISS add)
    → 留档 00_引擎/backtest/reviews/<场次>.json (供周更统计复盘命中率)

说明:
    - 复盘块 section='赛后复盘', 检索时与历史文章一起被召回,
      新场次分析可直接引用"相似盘口/同队的实战结果"
    - 同一场次重复入库会被拦截(需先删旧块)
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL_DIR = os.path.dirname(HERE)                      # 阿飞说球/02_工具
BASE = os.path.dirname(os.path.dirname(TOOL_DIR))     # D:\Hermes\football
sys.path.insert(0, TOOL_DIR)
from kb_core import KB_DIR, load_kb  # noqa: E402

CONFIG_DIR = os.path.join(TOOL_DIR, 'match_configs')
REVIEW_DIR = os.path.join(BASE, '00_引擎', 'backtest', 'reviews')
DIR_NAME = {'H': '主胜', 'D': '平局', 'A': '客胜'}


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


def find_config(home, away):
    """match_configs 下找对应 config: 精确名 → 模糊匹配队名"""
    cand = os.path.join(CONFIG_DIR, f'{home}vs{away}.json')
    if os.path.exists(cand):
        return cand
    for fn in os.listdir(CONFIG_DIR):
        if not fn.endswith('.json'):
            continue
        p = os.path.join(CONFIG_DIR, fn)
        try:
            with open(p, encoding='utf-8') as f:
                c = json.load(f)
            th = c['teams']['home']['name']
            ta = c['teams']['away']['name']
        except Exception:
            continue
        if (home in th or th in home) and (away in ta or ta in away):
            return p
    return None


def fetch_actual(home, away, days=10):
    """竞彩API抓已完赛果, 返回命中列表 [{date, score, ht, league}]"""
    sys.path.insert(0, os.path.join(BASE, '00_引擎', 'backtest'))
    from fetch_results import fetch_all
    from datetime import date, timedelta
    end = date.today().isoformat()
    begin = (date.today() - timedelta(days=days)).isoformat()
    print(f'抓取竞彩赛果 {begin} ~ {end} ...')
    matches = fetch_all(begin, end, only_single=False)
    hits = []
    for m in matches:
        ah = norm(m.get('allHomeTeam') or m.get('homeTeam'))
        aa = norm(m.get('allAwayTeam') or m.get('awayTeam'))
        ft = m.get('sectionsNo999') or ''
        if ':' not in ft:
            continue
        if name_match(home, ah) and name_match(away, aa):
            hits.append({'date': m['matchDate'], 'score': ft,
                         'ht': m.get('sectionsNo1') or '',
                         'league': m.get('leagueNameAbbr') or ''})
    return hits


def build_review(cfg, m, score, mdate):
    """预测 vs 实际 → 复盘结论文本(自包含, 检索友好)"""
    th, ta = cfg['teams']['home'], cfg['teams']['away']
    sh, sa = map(int, score.split(':'))
    actual = 'H' if sh > sa else ('D' if sh == sa else 'A')
    mdir = max(('H', m['pH']), ('D', m['pD']), ('A', m['pA']), key=lambda x: x[1])
    kdir = max(('H', m['pM']['H']), ('D', m['pM']['D']), ('A', m['pM']['A']), key=lambda x: x[1])
    top = max(m['probs'], key=lambda k: m['probs'][k])
    total = sh + sa
    edge_h = m['pH'] - m['pM_cal']['H']
    edge_a = m['pA'] - m['pM_cal']['A']

    L = [f"[{th['name']}vs{ta['name']}] 赛后复盘({mdate}) 实际比分{sh}-{sa}({DIR_NAME[actual]})。"]
    L.append(
        f"赛前模型:主{m['pH']*100:.1f}%/平{m['pD']*100:.1f}%/客{m['pA']*100:.1f}%,"
        f"最高概率指向{DIR_NAME[mdir[0]]}({'✔命中' if mdir[0] == actual else '✘未中'});"
        f"市场隐含:主{m['pM']['H']*100:.1f}%/平{m['pM']['D']*100:.1f}%/客{m['pM']['A']*100:.1f}%,"
        f"最高指向{DIR_NAME[kdir[0]]}({'✔命中' if kdir[0] == actual else '✘未中'})。")
    L.append(
        f"模型首选比分{top[0]}-{top[1]}(概率{m['probs'][top]*100:.1f}%)"
        f"({'✔命中' if (sh, sa) == top else '✘未中'});"
        f"大2.5球模型{m['p_over25']*100:.1f}%倾向{'出' if m['p_over25'] > 0.5 else '不出'}"
        f"(实际{total}球,{'✔' if (total > 2.5) == (m['p_over25'] > 0.5) else '✘'})。")
    if abs(edge_h) >= 3 or abs(edge_a) >= 3:
        ev, ed = (edge_h, '主胜') if edge_h >= edge_a else (edge_a, '客胜')
        ok = (ed == '主胜' and actual == 'H') or (ed == '客胜' and actual == 'A')
        L.append(f"Edge信号:模型{ed}Edge{ev*100:+.1f}%,实际{DIR_NAME[actual]}"
                 f"({'✔方向兑现' if ok else '✘未兑现'})。")
    return ' '.join(L)


def ingest(chunks):
    """增量入库: chunks 追加 + FAISS add(秒级, 不重建全库)"""
    import faiss
    import numpy as np
    chunk_path = os.path.join(KB_DIR, 'kb_chunks.json')
    with open(chunk_path, encoding='utf-8') as f:
        old = json.load(f)
    match_name = chunks[0]['match']
    if any(c['match'] == match_name and c['section'] == '赛后复盘' for c in old):
        print(f'⚠ {match_name} 已有复盘块, 跳过(覆盖需先删 kb_chunks.json 中旧块)')
        return False
    model, index, _ = load_kb()
    emb = model.encode([c['text'] for c in chunks], normalize_embeddings=True)
    index.add(np.asarray(emb, dtype='float32'))
    old.extend(chunks)
    with open(chunk_path, 'w', encoding='utf-8') as f:
        json.dump(old, f, ensure_ascii=False, indent=1)
    with open(os.path.join(KB_DIR, 'kb_index.faiss'), 'wb') as f:
        f.write(faiss.serialize_index(index))
    print(f'✔ 入库 {len(chunks)} 块, 知识库现有 {len(old)} 块')
    return True


def main():
    ap = argparse.ArgumentParser(description='赛后复盘入库(验证闭环)')
    ap.add_argument('--home', required=True, help='主队名')
    ap.add_argument('--away', required=True, help='客队名')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--score', help='实际比分 如 1-1 / 2:1')
    g.add_argument('--auto', action='store_true', help='自动从竞彩API抓赛果')
    ap.add_argument('--days', type=int, default=10, help='--auto 回溯天数')
    ap.add_argument('--dry-run', action='store_true', help='只打印复盘文本, 不入库')
    args = ap.parse_args()

    cfg_path = find_config(args.home, args.away)
    if not cfg_path:
        print(f'⚠ 未找到 {args.home}vs{args.away} 的 config (match_configs/)')
        return 1
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    from afei_generator import run_model
    m = run_model(cfg)
    print(f'✓ config: {os.path.basename(cfg_path)}')

    if args.score:
        score = args.score.replace('-', ':')
        mdate = '赛后'
    else:
        hits = fetch_actual(args.home, args.away, args.days)
        if not hits:
            print(f'⚠ 竞彩API近{args.days}天无 {args.home} vs {args.away} 已完赛场次')
            return 1
        if len(hits) > 1:
            print(f'⚠ 命中 {len(hits)} 场, 请用 --score 指定:')
            for h in hits:
                print(f'   {h["date"]} {h["league"]} 半场{h["ht"]} 全场{h["score"]}')
            return 1
        score = hits[0]['score'].replace('-', ':')
        mdate = hits[0]['date']
        print(f'✓ 赛果: {mdate} {score}')

    text = build_review(cfg, m, score, mdate)
    print('=' * 62)
    print(text)
    print('=' * 62)

    rec = {
        'match': f"{cfg['teams']['home']['name']}vs{cfg['teams']['away']['name']}",
        'date': mdate, 'score': score, 'config': cfg_path,
        'review_text': text,
        'pH': m['pH'], 'pD': m['pD'], 'pA': m['pA'],
        'pM': m['pM'], 'pM_cal': m['pM_cal'],
        'p_over25': m['p_over25'],
    }
    os.makedirs(REVIEW_DIR, exist_ok=True)
    with open(os.path.join(REVIEW_DIR, rec['match'] + '.json'), 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(f'留档 → 00_引擎/backtest/reviews/{rec["match"]}.json')

    if args.dry_run:
        print('(--dry-run 未入库)')
        return 0
    chunk = [{
        'text': text,
        'match': rec['match'],
        'section': '赛后复盘',
        'source': os.path.join('00_引擎', 'backtest', 'reviews', rec['match'] + '.json'),
    }]
    ingest(chunk)
    return 0


if __name__ == '__main__':
    sys.exit(main())
