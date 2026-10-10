# -*- coding: utf-8 -*-
"""竞彩官网球队数据采集 — 近10场赛果+球队信息, 输出JSON"""
import json
import os
import sys
import time

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
TEAMS = {
    586: '库奥皮奥', 2542: '克拉约瓦大学',
    2206: '比亚韦斯托克', 220: '格拉斯哥流浪者',
    333: '塞萨洛尼基', 223: '安德莱赫特',
    267: '本菲卡', 215: '哈茨',
}

def fetch(sess, path, params, referer):
    url = f'https://webapi.sporttery.cn/gateway/uniform/football/{path}'
    r = sess.get(url, params=params, headers={'Referer': referer}, timeout=20)
    r.raise_for_status()
    return r.json()

def main():
    sess = requests.Session()
    sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36'})
    sess.get('https://www.sporttery.cn/', timeout=15)

    out = {}
    for tid, name in TEAMS.items():
        ref = f'https://www.sporttery.cn/zqlszl/qdzl/index.html?gmtid={tid}'
        try:
            info = fetch(sess, 'team/getTeamInfoV1.qry', {'gmTeamId': tid}, ref)
            res = fetch(sess, 'team/getMatchResultV1.qry', {'gmTeamId': tid, 'termLimits': 10}, ref)
            fut = fetch(sess, 'team/getFutureMatchesV1.qry', {'gmTeamId': tid}, ref)
            out[name] = {
                'id': tid,
                'info': info.get('value'),
                'results': (res.get('value') or {}).get('matchList', []) if isinstance(res.get('value'), dict) else (res.get('value') or []),
                'future': (fut.get('value') or {}).get('matchList', []) if isinstance(fut.get('value'), dict) else (fut.get('value') or []),
            }
            n = len(out[name]['results'])
            print(f"{name}: 近10场 {n} 条")
        except Exception as e:
            print(f"{name}: ERR {e}")
        time.sleep(0.4)

    with open(os.path.join(BASE, 'europa_teams_20260806.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('已保存 europa_teams_20260806.json')

if __name__ == '__main__':
    main()
