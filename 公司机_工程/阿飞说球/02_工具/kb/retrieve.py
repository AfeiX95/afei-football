# -*- coding: utf-8 -*-
"""
retrieve.py — 历史案例召回 CLI v1.0
===================================
用法:
    python retrieve.py --query "强队降盘 高水 诱多" [--topk 5]
    python retrieve.py --home 横滨水手 --away 鹿岛鹿角 [--league 日职] [--topk 5]
    python retrieve.py --home 大阪钢巴 --away 浦和红钻 --json   # 程序化输出

说明:
    - 自由文本查询: 直接按语义召回最相关历史分析块
    - 对阵式查询:   自动拼 "主队 vs 客队 联赛 赛事" 检索语句
    - 输出含来源文章路径, 打开原文可看完整上下文
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kb_core import kb_search, match_query


def main():
    ap = argparse.ArgumentParser(description='阿飞·赛博聊球 历史案例召回')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--query', help='自由文本查询(语义检索)')
    g.add_argument('--home', help='对阵式查询: 主队名')
    ap.add_argument('--away', help='对阵式查询: 客队名(--home 时必填)')
    ap.add_argument('--league', default='', help='联赛名(增强检索)')
    ap.add_argument('--competition', default='', help='赛事名(增强检索)')
    ap.add_argument('--topk', type=int, default=5)
    ap.add_argument('--json', action='store_true', help='输出 JSON(供程序调用)')
    ap.add_argument('--vector', action='store_true', help='纯向量检索(默认混合: 向量+关键词 RRF)')
    args = ap.parse_args()

    if args.home:
        if not args.away:
            ap.error('--home 需配合 --away')
        query = match_query(args.home, args.away, args.league, args.competition,
                            '历史交锋 盘口 数据分析 比分')
    else:
        query = args.query

    res = kb_search(query, topk=args.topk, hybrid=not args.vector)
    if res is None:
        print('⚠ 知识库索引不存在, 请先运行: python build_kb.py')
        return 1
    if not res:
        print('无结果')
        return 0

    if args.json:
        print(json.dumps({'query': query, 'hits': res}, ensure_ascii=False, indent=1))
        return 0

    print('=' * 62)
    print(f'查询: {query} ({("混合检索" if not args.vector else "纯向量")})')
    print('=' * 62)
    label = '相似度' if args.vector else '相关度'
    for i, h in enumerate(res, 1):
        text = h['text'].replace('\n', ' ')
        if len(text) > 130:
            text = text[:130] + '…'
        print(f"[{i}] {label} {h['score']:.3f} | {h['match']} | {h['section']}")
        print(f"    {text}")
        print(f"    来源: 04_赛事文章/{h['source']}")
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
