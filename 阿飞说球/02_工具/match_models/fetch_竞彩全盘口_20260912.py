# -*- coding: utf-8 -*-
"""临时: 抓 09-12 周六候选场次全盘口(had/hhad/ttg/crs/hafu) → JSON 落盘"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, '采集数据'))
from browser import fetch_api  # noqa: E402

URL = ('https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry'
       '?channel=c&poolCode=had,hhad,ttg,crs,hafu')
OUT = os.path.join(ROOT, '.uv-cache', 'sat_0912_pools.json')

d = fetch_api(URL)
blocks = (d.get('value') or {}).get('matchInfoList') or []
ms = [m for blk in blocks for m in blk.get('subMatchList', [])]
print('总场次:', len(ms))

# 全部场次概览
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(ms, f, ensure_ascii=False, indent=1)
print('已落盘:', OUT)

# 打印候选(韩职/日职 + 焦点五大联赛)
keys = ['蔚山', '仁川', '全北', '首尔', '广岛', '樱花', '钢巴', '东京', '弗赖堡', '门兴',
        '美因茨', '法兰克福', '多特', '帕德博恩', '奥格斯堡', '勒沃库森', '切尔西', '赫尔城',
        '伯恩茅斯', '布伦特', '维拉', '诺丁汉', '水晶宫', '伊普斯', '利物浦', '富勒姆']
for m in ms:
    tag = f"{m.get('homeTeamAbbName','')}{m.get('awayTeamAbbName','')}"
    if any(k in tag for k in keys):
        had = m.get('had') or {}
        hh = m.get('hhad') or {}
        print(f"{m.get('matchNumStr')} {m.get('leagueAbbName'):4s} {m.get('matchTime','')[-5:]} "
              f"{m.get('homeTeamAbbName')} vs {m.get('awayTeamAbbName')} | "
              f"had {had.get('h')}/{had.get('d')}/{had.get('a')} | "
              f"hhad {hh.get('goalLine')} {hh.get('h')}/{hh.get('d')}/{hh.get('a')} | "
              f"single={m.get('bettingSingle')}")
