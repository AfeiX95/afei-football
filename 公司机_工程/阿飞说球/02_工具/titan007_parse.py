# -*- coding: utf-8 -*-
"""
titan007_parse.py — 新球体育(titan007)资料页 → 口径数字 + afei_generator config 草稿
=================================================================================
用法:
    python titan007_parse.py --file raw.txt                       # 打印口径报告
    python titan007_parse.py --file raw.txt --emit-config out.json # 同时吐 config 草稿
    python titan007_parse.py --stdin  < raw.txt

口径纪律:
    1) 赔率三盘(让球/进球数/半全场/比分)以竞彩官网为准 -> 用 jingcai_fetch.py 直抓;
       本脚本对 titan007 页面的赔率仅做交叉核对(页面常把赔率粘成一串, 用"枚举切分+返还率过滤"反解)。
    2) 页面独有、竞彩 API 没有的: 联赛积分 / 近10场战绩(含盘路) / 伤停 / 未来赛程 / 天气。
    3) 概率一律"归一化去水"口径; 比分盘含"胜其它/平其它/负其它"聚合项(必须计入)。
"""
import argparse
import json
import os
import re
import sys

CN = r'[\u4e00-\u9fa5A-Za-z0-9·\.\-]'
FULL = r'[\u4e00-\u9fa5A-Za-z0-9·\.\-\(\)]'


# ---------------------------------------------------------------- 基础工具
def norm(odds):
    """赔率 -> (归一化概率, 原始和)"""
    inv = {k: 1.0 / v for k, v in odds.items() if v and v > 1.0}
    if not inv:
        return {}, None
    S = sum(inv.values())
    return {k: v / S for k, v in inv.items()}, S


def split_concat(s, n, lo=1.05, hi=1.45, target=1.13):
    """把 '1.554.63.75' 这类无分隔赔率串切成 n 个数。

    枚举所有切点 -> 只保留每个 token 形如 数字.1~2位小数 的切法 ->
    用"返还率(1/赔率之和)"落在合理区间 + 最接近 target 过滤。
    返回 (best_list, best_overround, 全部候选)
    """
    s = s.strip()
    cands = []

    # 单步可用切分: 数字(可选 .1~2 位小数), 赔率 (1,999]
    #   ⚠️首位常是整数盘(进球数 0球=50 无小数点), 故必须允许无小数 token;
    #     "5014.5" 这类离谱切法由"返还率须落在 [lo,hi]"与 Σ1/x 单调剪枝排除。
    steps = {}
    for i in range(len(s)):
        for j in range(i + 1, min(i + 7, len(s)) + 1):
            tok = s[i:j]
            if re.fullmatch(r'\d+(?:\.\d{1,2})?', tok) and 1.0 < float(tok) <= 999:
                steps.setdefault(i, []).append((j, float(tok)))

    hits = []

    def dfs(pos, k, S, path):
        if S > hi:                      # 每段赔率都 >1 -> Σ1/x 单调递增, 可安全剪枝
            return
        if k == n:
            if pos == len(s) and S >= lo:
                hits.append((S, path))
            return
        for end, v in steps.get(pos, ()):
            dfs(end, k + 1, S + 1.0 / v, path + (v,))

    dfs(0, 0, 0.0, ())
    ok = sorted(((abs(S - target), S, list(p)) for S, p in hits), key=lambda x: (x[0], x[1]))
    if ok:
        return ok[0][2], ok[0][1], [p for _, _, p in ok]
    return None, None, []


def num_list(seg):
    return [float(x) for x in re.findall(r'\d+(?:\.\d+)?', seg)]


def cut(text, start_marker, end_markers):
    """按起止标记取文本块(标记取首次出现)"""
    i = text.find(start_marker)
    if i < 0:
        return ''
    i += len(start_marker)
    j = len(text)
    for m in end_markers:
        k = text.find(m, i)
        if 0 <= k < j:
            j = k
    return text[i:j]


def chunks_by(text, markers):
    """按多个锚点切块, 返回 {锚点: 块}] 顺序锚点各自到下一个锚点"""
    idx = []
    for m in markers:
        k = text.find(m)
        if k >= 0:
            idx.append((k, m))
    idx.sort()
    out = {}
    for n, (k, m) in enumerate(idx):
        end = idx[n + 1][0] if n + 1 < len(idx) else len(text)
        out[m] = text[k + len(m):end]
    return out


def line_block(text, marker, end_markers=()):
    """按"整行锚点"取块 —— 页头常含同名词(如"即时比分"), 按字符 find 会被误伤。"""
    lines = text.split('\n')
    start = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == marker or s.startswith(marker):
            start = i + 1
            break
    if start is None:
        return ''
    out = []
    for ln in lines[start:]:
        s = ln.strip()
        if any(s == e or s.startswith(e) for e in end_markers):
            break
        out.append(ln)
    return '\n'.join(out)


# ---------------------------------------------------------------- 页面解析
def parse_page(text):
    t = text.replace('\u3000', ' ')
    d = {'raw_len': len(t)}

    # 头: 主队(主) ... VS客队 / 时间 / 场地 / 天气
    m = re.search(r'(' + CN + r'{2,})\s*\(主\)', t)
    d['home'] = m.group(1) if m else None
    m = re.search(r'VS\s*(' + CN + r'{2,})', t)
    d['away'] = m.group(1) if m else None
    m = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s*(星期[\u4e00-\u9fa5])?', t)
    if m:
        d['date'], d['time'], d['weekday'] = m.group(1), m.group(2), m.group(3)
    m = re.search(r'场地[：:]\s*(' + FULL + r'+)', t)
    d['venue'] = m.group(1) if m else None
    m = re.search(r'天气[：:]\s*(' + FULL + r'+)', t)
    d['weather'] = m.group(1) if m else None
    m = re.search(r'温度[：:]\s*([0-9]+℃?[～~\-]+[0-9]+℃?)', t)
    d['temp'] = m.group(1) if m else None

    # 竞足数据: 让球串 + 进球数串 (页面常把赔率粘成一串, 用"枚举切分 + 返还率过滤"反解)
    seg = line_block(t, '竞足数据', ['比分', '半全场', '联赛积分'])
    blobs = [x for x in re.findall(r'-?\d[\d\.]{4,}', seg) if '.' in x]
    d['jczq_raw'] = blobs
    d['handicap'] = None
    d['ttg'] = None
    for a in blobs:
        if d['handicap'] is None:
            # 让球串: 头部 = 让球线(0.25 的整数倍), 尾部 = 3 个赔率
            for L in range(2, min(9, len(a))):
                pre = a[:L]
                if not re.fullmatch(r'-?\d+(?:\.\d{1,2})?', pre):
                    continue
                glv = float(pre)
                if abs(glv) > 5 or (abs(glv) * 4) % 1 != 0:
                    continue
                rest = a[L:]
                if not re.match(r'\d+\.\d{1,2}', rest):
                    continue
                vals, S, _ = split_concat(rest, 3, lo=1.05, hi=1.35, target=1.13)
                if vals and vals[0] == min(vals):
                    d['handicap'] = {'goalLine': glv, 'odds': vals, 'overround': S, 'src': a}
                    break
            if d['handicap']:
                continue
        if d['ttg'] is None:
            vals, S, _ = split_concat(a, 8, lo=1.10, hi=1.35, target=1.20)
            if vals:
                d['ttg'] = vals
                d['ttg_src'] = a

    # 比分盘 (行锚点: 页头"即时比分"会误伤)
    crs, keys = {}, []
    seg = line_block(t, '比分', ['半全场', '联赛积分'])
    # 键按出现顺序收集(具名比分 + "X其它"聚合项), 再与同序赔率串逐位对齐
    for m in re.finditer(r'(\d+)\s*:\s*(\d+)|(胜|平|负)其它', seg):
        keys.append('%d:%d' % (int(m.group(1)), int(m.group(2))) if m.group(1)
                    else (m.group(3) + '其它'))
    rest = re.sub(r'\d+\s*:\s*\d+', ' ', seg)
    rest = re.sub(r'(胜|平|负)其它', ' ', rest)
    rest = re.sub(r'[胜平负]', ' ', rest)
    odds = num_list(rest)
    if keys and len(odds) == len(keys):
        crs = dict(zip(keys, odds))
    elif keys:
        d['crs_warn'] = '比分盘键 %d vs 赔率 %d 未对齐' % (len(keys), len(odds))
    d['crs'] = crs

    # 半全场
    seg = line_block(t, '半全场', ['联赛积分', '杯赛积分'])
    labels = re.findall(r'(胜|平|负)\s*/\s*(胜|平|负)', seg)
    rest = re.sub(r'(胜|平|负)\s*/\s*(胜|平|负)', ' ', seg)
    d['hafu'] = {('%s/%s' % l): v for l, v in zip(labels, num_list(rest))} \
        if len(num_list(rest)) >= len(labels) else {}

    # 伤停(分队)
    seg = line_block(t, '阵容情况', ['上一场', '近期战绩'])
    inj_flat, inj_by, cur = [], {}, None
    for ln in seg.split('\n'):
        s = ln.strip()
        if not s:
            continue
        if re.fullmatch(CN + r'{2,}', s) and s in (d.get('home'), d.get('away')):
            cur = s
            inj_by.setdefault(cur, [])
            continue
        for x in re.findall(r'(\d+)\s*(' + CN + r'{2,})\(([^)]{1,10})\)\s*(' + CN + r'{2,6})', s):
            inj_flat.append((cur, x[0], x[1], x[2], x[3]))
            inj_by.setdefault(cur or '?', []).append(x)
    d['injuries_raw'] = inj_flat
    d['injuries'] = inj_by

    # 近期战绩 / 赛程 / 简报 / 积分 / 数据对比 / 盘路 / 评分
    d['results_raw'] = line_block(t, '近期战绩', ['联赛盘路', '相同盘路', '赛前简报'])
    d['schedule_raw'] = line_block(t, '未来五场', ['声明', 'Copyright'])
    d['standing_raw'] = line_block(t, '联赛积分排名', ['杯赛积分排名', '近10场数据对比'])
    d['form10_raw'] = line_block(t, '近10场数据对比', ['阵容情况', '伤停'])
    d['brief_raw'] = line_block(t, '赛前简报', ['未来五场'])
    d['odds_trend_raw'] = line_block(t, '联赛盘路走势', ['相同盘路', '赛前简报'])
    d['same_line_raw'] = line_block(t, '相同盘路', ['赛前简报'])
    d['rating_raw'] = line_block(t, '上一场出场评分', ['近期战绩'])

    # 积分(全场/半场)
    st, mode, cur, d['standings'] = d['standing_raw'], 'full', None, {}
    for ln in st.split('\n'):
        s = ln.strip()
        if not s:
            continue
        m = re.match(r'\[([^\]]+)\]\s*(' + CN + r'{2,})', s)
        if m:
            cur, mode = m.group(2), 'full'
            d['standings'][cur] = {'league_tag': m.group(1)}
            continue
        if s.startswith('半场'):
            mode = 'half'
            continue
        if s.startswith('全场'):
            mode = 'full'
            continue
        if cur and s.split()[0] in ('总', '主', '客', '近6') and len(s.split()) > 5:
            d['standings'][cur].setdefault(mode, {})[s.split()[0]] = s.split()[1:]

    # 近10场数据对比
    d['form10'] = {}
    f = d['form10_raw']
    for nm in (d.get('home'), d.get('away')):
        if not nm or nm not in f:
            d['form10'][nm] = None
            continue
        blk = f[f.find(nm):][:400]
        g = lambda p: (re.search(p, blk).group(1) if re.search(p, blk) else None)
        sv = re.search(r'同主客[^\n]*?胜([\d\.]+)%\s*平([\d\.]+)%\s*负([\d\.]+)%', blk)
        d['form10'][nm] = {
            'wl': [g(r'胜(\d+)%'), g(r'平(\d+)%'), g(r'负(\d+)%')],
            'goals': g(r'场均进球([\d\.]+)'),
            'corners': g(r'场均角球([\d\.]+)'),
            'cards': g(r'场均黄牌([\d\.]+)'),
            'same_venue_goals': g(r'同主客[^\n]*?场均进球([\d\.]+)'),
            'same_venue_wl': sv.groups() if sv else None,
        }

    # 盘路走势 / 相同盘路 / 上一场评分
    d['odds_trend'], d['same_line'], d['rating'] = {}, {}, {}
    for nm in (d.get('home'), d.get('away')):
        if not nm:
            continue
        m = re.search(re.escape(nm) + r'\s*总\s*(.+)', d['odds_trend_raw'])
        if m:
            d['odds_trend'][nm] = m.group(1).strip()
        m = re.search(re.escape(nm) + r'\s*(.+)', d['same_line_raw'])
        if m:
            d['same_line'][nm] = m.group(1).strip()
        ln = ''
        for L in d['rating_raw'].split('\n'):
            if nm in L:
                ln = L
                break
        nums = [float(x) for x in re.findall(r'\d+\.\d+', ln)]
        d['rating'][nm] = {'n': max(0, len(nums) - 1), 'avg': nums[-1] if nums else None}

    d['jczq_src'] = {'handicap': d.get('jczq_goalLine_src'), 'ttg': d.get('ttg_src')}
    return d


def parse_results(seg, teams):
    """解析近期战绩行 -> 每队: 场次/胜平负/进失/净胜分布/场均"""
    out = {}
    lines = re.split(r'\n', seg)
    rows = []
    for ln in lines:
        m = re.match(r'\s*(\d{2}-\d{2}-\d{2})\s+(\S+)\s+(' + FULL + r'+?)\s+(\d+)\s*-\s*(\d+)\s+(' + FULL + r'+)', ln)
        if not m:
            continue
        d0, comp, home, hs, aws, away = m.groups()
        rows.append({'date': d0, 'comp': comp, 'home': home, 'hs': int(hs),
                     'as': int(aws), 'away': away, 'tail': ln[m.end():].strip()})
    for name in teams:
        if not name:
            continue
        recs = []
        for r in rows:
            hn = r['home'].replace('(中)', '')
            an = r['away'].replace('(中)', '')
            if name in hn or hn in name or name in r['home']:
                gf, ga = r['hs'], r['as']
            elif name in an or an in name or name in r['away']:
                gf, ga = r['as'], r['hs']
            else:
                continue
            recs.append((gf, ga, r))
        if not recs:
            out[name] = None
            continue
        w = sum(1 for gf, ga, _ in recs if gf > ga)
        dr = sum(1 for gf, ga, _ in recs if gf == ga)
        l = sum(1 for gf, ga, _ in recs if gf < ga)
        gf = sum(x[0] for x in recs)
        ga = sum(x[1] for x in recs)
        nets = [x[0] - x[1] for x in recs]
        n = len(recs)
        out[name] = {
            'n': n, 'w': w, 'd': dr, 'l': l, 'gf': gf, 'ga': ga,
            'gf_pg': round(gf / n, 2), 'ga_pg': round(ga / n, 2),
            'net3plus': sum(1 for x in nets if x >= 3),
            'net_ge3_pct': round(100.0 * sum(1 for x in nets if x >= 3) / n, 1),
            'nets': nets,
            'last6': recs[:6],
        }
    return out


# ---------------------------------------------------------------- 口径计算
def report(d):
    R = []
    A = R.append
    A('== 头 ==')
    A('  %s(主) vs %s | %s %s %s | %s | %s %s' % (
        d.get('home'), d.get('away'), d.get('date'), d.get('time'),
        d.get('weekday') or '', d.get('venue') or '', d.get('weather') or '', d.get('temp') or ''))

    crs = d.get('crs') or {}
    if crs:
        win = {k: v for k, v in crs.items() if ':' in k and int(k.split(':')[0]) > int(k.split(':')[1])}
        win.update({k: v for k, v in crs.items() if k.endswith('其它') and k.startswith('胜')})
        drw = {k: v for k, v in crs.items() if ':' in k and int(k.split(':')[0]) == int(k.split(':')[1])}
        drw.update({k: v for k, v in crs.items() if k == '平其它'})
        los = {k: v for k, v in crs.items() if ':' in k and int(k.split(':')[0]) < int(k.split(':')[1])}
        los.update({k: v for k, v in crs.items() if k == '负其它'})
        pw, sw = norm(win)
        pd, sd = norm(drw)
        pl, sl = norm(los)
        tot = sw + sd + sl
        A('== 比分盘反推(含"其它"聚合项; 返还率%.1f%%) ==' % (100.0 / tot))
        A('  主胜 %.2f%%  平 %.2f%%  客胜 %.2f%%' % (
            100 * sw / tot, 100 * sd / tot, 100 * sl / tot))
        allp = {}
        for k, v in list(win.items()) + list(drw.items()) + list(los.items()):
            allp[k] = (1.0 / v) / tot
        top = sorted([(k, v) for k, v in allp.items() if ':' in k and v > 0.03], key=lambda x: -x[1])[:8]
        A('  热区比分: ' + '  '.join('%s %.2f%%' % (k, 100 * v) for k, v in top))
        # 净胜分布 + 期望比分(具名)
        nets = {}
        gh = ga = 0.0
        for k, v in allp.items():
            if ':' not in k:
                continue
            h, a = map(int, k.split(':'))
            nets[h - a] = nets.get(h - a, 0.0) + v
            gh += h * v
            ga += a * v
        named = sum(v for k, v in allp.items() if ':' in k)
        A('  具名净胜分布: ' + ' '.join('%+d球 %.2f%%' % (k, 100 * nets[k]) for k in sorted(nets, reverse=True)))
        A('  具名期望比分 %.2f : %.2f (样本覆盖 %.1f%%, 剔"其它"故偏低) 净胜 %.2f' % (
            gh / named, ga / named, 100 * named, (gh - ga) / named))
        n3 = sum(v for k, v in nets.items() if k >= 3)
        A('  具名净胜3+ = %.2f%% (下界)' % (100 * n3))
        zero = sum(v for k, v in allp.items() if ':' in k and k.split(':')[1] == '0')
        A('  具名客队0球 = %.2f%% (下界)' % (100 * zero))

    hc = d.get('handicap')
    A('== 亚让 ==')
    if hc:
        o = hc['odds']
        p, S = norm({'h': o[0], 'd': o[1], 'a': o[2]})
        A('  让球线 %+g  | 赔率 %.2f / %.2f / %.2f (返还率%.1f%%)' % (hc['goalLine'], o[0], o[1], o[2], 100 / S))
        A('  让胜 %.2f%%  让平 %.2f%%  让负 %.2f%%' % (100 * p['h'], 100 * p['d'], 100 * p['a']))
    else:
        A('  !! 未解析出(页面粘连或缺失) -> 以竞彩官网 jingcai_fetch.py 为准')

    ttg = d.get('ttg')
    A('== 进球数盘 ==')
    if ttg:
        p, S = norm({str(i): v for i, v in enumerate(ttg)})
        e = sum(i * p[str(i)] for i in range(7)) + 8.0 * p.get('7', 0)
        A('  0..7+: ' + ' '.join('%.2f' % x for x in ttg) + ' (返还率%.1f%%)' % (100 / S))
        A('  期望总进球 %.2f | 大2.5 %.2f%% | 大3.5 %.2f%% | 大4.5 %.2f%%' % (
            e, 100 * sum(p[str(i)] for i in range(3, 8)),
            100 * sum(p[str(i)] for i in range(4, 8)),
            100 * sum(p[str(i)] for i in range(5, 8))))

    hf = d.get('hafu') or {}
    A('== 半全场 ==')
    if hf:
        p, S = norm(hf)
        A('  ' + ' '.join('%s %.2f%%' % (k, 100 * v) for k, v in p.items()))
        hw = sum(v for k, v in p.items() if k.startswith('胜') or k.endswith('/胜'))
        A('  全场主胜(9格合计) %.2f%% | 半场主胜 %.2f%%' % (
            100 * sum(v for k, v in p.items() if k.split('/')[1] == '胜'),
            100 * sum(v for k, v in p.items() if k.split('/')[0] == '胜')))

    A('== 近10场战绩(页面口径) ==')
    res = d.get('results') or {}
    for k, v in res.items():
        if not v:
            A('  %s: 未解析' % k)
            continue
        A('  %s: %d场 %d胜%d平%d负 进%d失%d 场均%.2f/%.2f | 净胜3+ %d场(%.1f%%)' % (
            k, v['n'], v['w'], v['d'], v['l'], v['gf'], v['ga'], v['gf_pg'], v['ga_pg'],
            v['net3plus'], v['net_ge3_pct']))
        A('    近6场: ' + ' '.join('%d-%d' % (x[0], x[1]) for x in v['last6']))

    A('== 联赛积分(页面口径) ==')
    for nm in (d.get('home'), d.get('away')):
        s = (d.get('standings') or {}).get(nm)
        if not s:
            A('  %s: 未解析' % nm)
            continue
        A('  %s [%s]' % (nm, s.get('league_tag')))
        for mode, lab in (('full', '全场'), ('half', '半场')):
            for tag in ('总', '主', '客', '近6'):
                v = (s.get(mode) or {}).get(tag)
                if v:
                    A('    %s%s: %s' % (lab, tag, ' '.join(v)))

    A('== 伤停(页面口径; 竞彩网该栏残缺, 须外媒互证) ==')
    inj_by = d.get('injuries') or {}
    for nm in (d.get('home'), d.get('away')):
        lst = inj_by.get(nm) or []
        A('  %s: %d 人' % (nm, len(lst)))
        for no, who, pos, stt in lst:
            A('    %s %s(%s) %s' % (no, who, pos, stt))

    A('== 近10场数据对比 ==')
    for nm in (d.get('home'), d.get('away')):
        v = (d.get('form10') or {}).get(nm)
        if not v:
            A('  %s: 未解析' % nm)
            continue
        A('  %s 胜平负%s%%/%s%%/%s%% 场均进%s 角球%s 黄牌%s' % (
            nm, v['wl'][0], v['wl'][1], v['wl'][2], v['goals'], v['corners'], v['cards']))
        A('    同主客 场均进%s 胜平负%s' % (
            v['same_venue_goals'], '/'.join('%s%%' % x for x in (v['same_venue_wl'] or ['-'] * 3))))

    A('== 盘路 ==')
    for nm in (d.get('home'), d.get('away')):
        A('  %s 走势: %s' % (nm, (d.get('odds_trend') or {}).get(nm) or '—'))
        A('  %s 相同盘路: %s' % (nm, (d.get('same_line') or {}).get(nm) or '—'))

    A('== 上一场评分(客队空 = 数据盲区, 不可当"阵容完整") ==')
    for nm in (d.get('home'), d.get('away')):
        v = (d.get('rating') or {}).get(nm) or {}
        A('  %s: 平均 %s (样本 %s)' % (nm, v.get('avg') if v.get('avg') else '缺失', v.get('n')))

    A('== 未来赛程 ==')
    sch = (d.get('schedule_raw') or '').strip()
    A('  ' + ' / '.join(re.split(r'\s{2,}|\n', sch)[:12])[:400])
    return '\n'.join(R)


# ---------------------------------------------------------------- config 草稿
def emit_config(d, path, title='', competition='', tags=''):
    crs = d.get('crs') or {}
    res = d.get('results') or {}
    home, away = d.get('home'), d.get('away')
    hh, aa = res.get(home) or {}, res.get(away) or {}
    st = d.get('standings') or {}
    f10 = d.get('form10') or {}
    rt = d.get('rating') or {}

    def last6(t):
        recs = (t or {}).get('last6') or []
        if not recs:
            return {'w': 0, 'd': 0, 'l': 0}, {'gf': 0, 'ga': 0}
        w = sum(1 for r in recs if r[0] > r[1])
        dr = sum(1 for r in recs if r[0] == r[1])
        return ({'w': w, 'd': dr, 'l': len(recs) - w - dr},
                {'gf': round(sum(x[0] for x in recs) / len(recs), 2),
                 'ga': round(sum(x[1] for x in recs) / len(recs), 2)})

    (hf6, hr6), (af6, ar6) = last6(hh), last6(aa)

    def sv_pct(nm, fb):
        v = (f10.get(nm) or {}).get('same_venue_wl')
        return [int(float(x)) for x in v] if v else fb

    def sv_g(nm, fb):
        v = (f10.get(nm) or {}).get('same_venue_goals')
        return float(v) if v else fb

    # 1X2 市场赔率: 竞彩常不开胜平负 -> 用比分盘反推的"公平赔率"占位
    odds = {'H': 1.15, 'D': 8.0, 'A': 15.0}
    if crs:
        tot = 0.0
        masses = {'H': 0.0, 'D': 0.0, 'A': 0.0}
        for k, v in crs.items():
            if ':' in k:
                h, a = map(int, k.split(':'))
                m = 1.0 / v
            else:
                h = a = None
                m = 1.0 / v
                if k.startswith('胜'):
                    h, a = 9, 0
                elif k == '平其它':
                    h, a = 4, 4
                else:
                    h, a = 0, 9
            tot += m
            masses['H' if h > a else ('D' if h == a else 'A')] += m
        odds = {k: round(1.0 / (m / tot), 2) for k, m in masses.items()}

    score_odds = []
    for k, v in crs.items():
        if ':' in k:
            h, a = map(int, k.split(':'))
            score_odds.append([h, a, v])

    cfg = {
        'title': title,
        'tags': tags,
        'competition': competition,
        'first_leg': '',
        'match_time': '%s(%s)%s(北京时间)' % (d.get('date'), d.get('weekday') or '', d.get('time')),
        'venue': d.get('venue') or '',
        'weather': '%s,%s' % (d.get('temp') or '', d.get('weather') or ''),
        'draw_to_penalties': False,
        'promotion': '',
        'skeleton': '深度叙事式',
        'hook_type': '',
        'ending_hook': '',
        'ending_line': '',
        'odds': odds,
        'score_odds': score_odds,
        'strategy': {
            'home_mult': 1.0, 'away_mult': 0.6, 'home_adv': 0.15,
            'home_form': hf6, 'away_form': af6,
        },
        'teams': {
            'home': {'name': home, 'league': (st.get(home) or {}).get('league_tag', ''),
                     'gf': hh.get('gf_pg', 0), 'ga': hh.get('ga_pg', 0),
                     'gf_special': sv_g(home, hh.get('gf_pg', 0)), 'ga_special': hh.get('ga_pg', 0),
                     'special_label': '同主客', 'recent': hr6,
                     'rating': (rt.get(home) or {}).get('avg') or 0},
            'away': {'name': away, 'league': (st.get(away) or {}).get('league_tag', ''),
                     'gf': aa.get('gf_pg', 0), 'ga': aa.get('ga_pg', 0),
                     'gf_special': sv_g(away, aa.get('gf_pg', 0)), 'ga_special': aa.get('ga_pg', 0),
                     'special_label': '同主客', 'recent': ar6,
                     'rating': (rt.get(away) or {}).get('avg') or 0},
        },
        'recent10': {
            'h_all': [hh.get('w', 0) * 10, hh.get('d', 0) * 10, hh.get('l', 0) * 10],
            'h_home': sv_pct(home, [0, 0, 0]),
            'a_all': [aa.get('w', 0) * 10, aa.get('d', 0) * 10, aa.get('l', 0) * 10],
            'a_away': sv_pct(away, [0, 0, 0]),
        },
        'charts': {'wdl': True, 'goals': True, 'heatmap': True, 'edge': False, 'promote': False},
        'illustration': {'en': '', 'cn': ''},
        'sections': [
            {'type': 'para', 'text': 'TODO 开篇(type 必须写 para, 写 lead 会被渲染器静默丢掉)'},
        ],
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return cfg


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file')
    ap.add_argument('--stdin', action='store_true')
    ap.add_argument('--emit-config')
    ap.add_argument('--out', default='')
    ap.add_argument('--title', default='')
    ap.add_argument('--competition', default='')
    ap.add_argument('--tags', default='')
    a = ap.parse_args()

    if a.stdin:
        text = sys.stdin.read()
    elif a.file:
        with open(a.file, encoding='utf-8') as f:
            text = f.read()
    else:
        print('用法: --file raw.txt [--emit-config out.json]'); sys.exit(1)

    d = parse_page(text)
    d['results'] = parse_results(d.get('results_raw') or '', [d.get('home'), d.get('away')])
    rep = report(d)
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(rep + '\n')
    print(rep)
    if a.emit_config:
        emit_config(d, a.emit_config, a.title, a.competition, a.tags)
        print('\n[config 草稿] -> %s' % a.emit_config)
    return 0


if __name__ == '__main__':
    sys.exit(main())
