# -*- coding: utf-8 -*-
"""发布前"平台风险"扫描(按平台套用不同门限)

背景与依据(两层):
 (1) 《微信公众平台服务协议》第六条(尤其 6.1.2.1(7) 赌博, 6.1.2.5 不实信息, 6.1.2.8(1) 夸张标题)
     —— 2026-09-15 本项目公众号被封后对照建立。
 (2) 《关于体育违规荐彩内容的治理公告》(微信公众平台运营中心, 2026-01-14)
     —— 2026-09-20 补入。判罚是 **AND 逻辑**:
         违规 = (赛事技术分析缺失/薄弱) AND (稳赢暗示 / 宣传战绩 / 竞彩黑话)
     对应本脚本的新增: E 级词表 + 「分析厚度」启发式(给第 1 点一个可自查的代理指标)。
 (3) 平台分流: 见 `01_工作流SOP/风控_账号被屏蔽处置_20260915.md` §三 与 `公众号写作规范.md`

用法:
    python risk_scan.py <md文件> [更多文件...] [--platform gzh|toutiao]
    python risk_scan.py --toutiao <md文件>          # 简写
默认 --platform gzh(最严, fail-safe)。

退出码: 0 = 无硬性失败; 1 = 有硬性失败(可用于发布流程卡点)
"""
import argparse
import io
import re
import sys

# ---------------- 词表 ----------------
# A 级: 直接触线(赌博/投注语境) —— 两个平台都必须为 0(协议红线)
A = ['买', '押', '下注', '投注', '赢盘', '输盘', '收米', '稳胆', '跟单', '必收', '博彩', '彩票',
     '过关', '串关', '盈利', '回报率', '资金', '仓位', '倍投', '加注',
     # 2026-09-20 补齐: 这些 check_md_release.HI_RISK 已收录, 但本脚本此前漏了
     '必赢', '稳赢', '埋雷', '红单', '回血', '上岸', '梭哈']

# B 级拆两类 —— 关键区分:
#   B1 是"投注推荐框架"(方向/比分/推荐/预测), 它构成公告所指的**清单形态**,
#      两个平台都必须为 0(2026-09-15 被封的《周二11场速评》正是 方向:×11 + 比分参考×12)。
#   B2 是"主观判断词"(看好/倾向/值得留意), 公众号必须 0; 头条属正常分析语言, 只提示。
B1_FRAME = ['首选比分', '比分参考', '方向是', '方向:', '推荐', '预测', '可以跟', '跟哪一手']
B2_JUDGE = ['看好', '稳稳', '必中', '命中', '值得关注', '值得留意', '倾向', '值得探讨']

# C 级: 博彩术语与赔率串 —— 公众号为 0; 头条按分流表可保留(须标"竞彩官方"来源)
C = ['让球', '让胜', '让平', '让负', '走水', '盘口', '奖金', '比分盘', '总进球',
     '半全场', '竞彩', '受让', '深盘', '盘面', '低赔方', '热门']

# D 级: 夸张标题/标题党 —— 两平台都必须为 0
D = ['震惊', '惊天', '炸裂', '暴击', '必看', '罕见', '史上', '最全', '揭秘', '内幕']

# 上下文豁免: 有些词在正常分析里也会出现, 命中时不算风险
#   '史上' → "历史上让球方赢下盘口 52%" 是**事实陈述**, 不是标题党(实测误报 4 次)
EXEMPT = {
    '史上': re.compile(r'(历|队|联赛|赛季|亚冠|球队)史上'),
    '内幕': re.compile(r'内幕(消息|交易)'),
}
# 注: '内幕' 本身是 D 级标题党词, 但公告把它们列为**战绩宣传/独家包装**(E 级),
#     两处都收是有意的(标题里出现按 D, 正文里按 E 也命中), 此处不豁免。

# E 级: 战绩宣传 / 稳赢暗示 / 独家包装 —— 两平台都必须为 0
#     —— 来源: 《关于体育违规荐彩内容的治理公告》(2026-01-14) 典型表现第 2 点
#        "大篇幅暗示高命中率/稳赢策略, 通过宣传预测战绩或使用相关竞彩黑话进行稳赢暗示"
#     前 10 个是公告案例里**原文点名**的话术, 其余为同类归纳。
E_PLATFORM = ['红单', '奖金翻倍', '计划单', '连红', '连红多天', '精准拿捏', '私厨', '重磅猛料',
              '稳赢策略', '包赚']
E_SELF_PRAISE = ['命中率', '连续命中', '稳定盈利', '跟单必赢', '稳赚', '不赔', '保本', '翻倍']
E_EXCLUSIVE = ['内部消息', '内幕消息', '独家猛料', '带单', '包赔', '必看推荐']
E = E_PLATFORM + E_SELF_PRAISE + E_EXCLUSIVE

LEVELS = [('A', 'A 直触线(赌博/投注)', A),
          ('B1', 'B1 投注推荐框架', B1_FRAME),
          ('B2', 'B2 主观判断词', B2_JUDGE),
          ('C', 'C 博彩术语与赔率', C),
          ('D', 'D 标题党', D),
          ('E', 'E 战绩宣传/稳赢暗示', E)]

# ---------------- 平台门限(依据 0915 风控文档 §三 分流表) ----------------
PLATFORMS = {
    'gzh': {
        'label': '公众号(收紧)',
        'fail': ['A', 'B1', 'B2', 'C', 'D', 'E'],
        'warn': [],
        'max_combo': 0,          # 比分+奖金组合
        'max_dir': 0,            # "方向/主线 是/落在" 式定调
        'ratio_min': 0.30,
        'listy_max': 8.0,
        'multi_match_allowed': False,   # 0915: 多场扫描 ❌ 不做
        'disclaimer_betting_ok': False,  # 免责声明不得含"购彩/投注"
        'note': '赔率/让球线/走水/方向/具体比分/"竞彩" 一律不写',
    },
    'toutiao': {
        'label': '头条号',
        'fail': ['A', 'B1', 'D', 'E'],
        'warn': ['B2', 'C'],
        'max_combo': 0,          # 0915: 头条 比分 单篇 ≤1 处, **且不带奖金**
        'max_dir': 0,
        'ratio_min': 0.30,
        'listy_max': 8.0,
        'multi_match_allowed': True,
        'disclaimer_betting_ok': True,
        'note': '博彩术语(C)可保留(须标"竞彩官方"来源); 投注推荐框架(A/B1/E)仍须为 0',
    },
}

# 模板行豁免: 免责声明与数据来源是必留的合规文本, 不能算风险(否则每次扫描都是假阳性)
TEMPLATE_MARK = ('不构成', '【数据来源】', '【免责声明】', '阿飞模型推演', '中国体育彩票官方')

# ---------------- 「分析厚度」启发式 ----------------
# 公告第 1 点 = "公开可验证的赛事技术分析占比较小或完全缺失"。
# 平台没有公开阈值, 下面是**本项目自定的代理指标**, 已用已知违禁稿标定, 不等于平台口径。
DATA_PAT = [
    r'\d+\s*[:：]\s*\d+',                      # 比分 2:1
    r'第\s*\d+\s*(名|轮|位)',                   # 第2名 / 第8轮
    r'积\s*\d+\s*分', r'\d+\s*分',
    r'\d+\s*胜\s*\d+\s*平\s*\d+\s*负',           # 5胜2平0负
    r'近\s*\d+\s*场', r'近\s*\d+\s*次',
    r'\d+\s*场', r'\d+\s*球', r'\d+\s*个?球',
    r'场均\s*[\d.]+', r'\d+\.\d+',
    r'\d+\s*%',
    r'(进球|失球|净胜球|助攻|首发|替补|射手|伤停|出场|射门|控球|角球|越位|黄牌|红牌)',
    r'(积分榜|排名|战绩|交锋|赛程|轮次|赛季|主客场|主场|客场)',
    r'(阵型|战术|防守|进攻|中场|后卫|前锋|门将)',
]
DATA_RE = re.compile('|'.join(DATA_PAT))
OPINION_PAT = [
    r'(看好|倾向|推荐|值得|应当|应该|大概率|我认为|个人认为|方向|主线|首选|结论)',
    r'(稳|必|一定|肯定|不难|轻松|显然|无疑)',
    r'(值得探讨|值得留意|可关注|留意|关注)',
]
OPINION_RE = re.compile('|'.join(OPINION_PAT))


def clean(text):
    """删掉免责声明/数据来源这类模板行, 避免假阳性"""
    return '\n'.join(l for l in text.split('\n') if not any(k in l for k in TEMPLATE_MARK))


def split_sentences(text):
    """按中文句末标点与换行切句(去表格行, 表格是数据, 单独看)"""
    t = re.sub(r'^\s*\|.*$', '', text, flags=re.M)
    parts = re.split(r'[。！？!?\n]+', t)
    return [p.strip() for p in parts if len(p.strip()) >= 6]


def analysis_ratio(body):
    """分析厚度指标(启发式代理, 非平台口径)

    ⚠️ 标定说明: 2026-09-15 被封的《周二11场速评》是**已知违禁样本**, 必须被判风险。
       只看"纯数据句占比"会放过它(36%, 因为 11 场逐场都有数据),
       问题出在**清单形态**: 每场都跟一句"方向:"+"比分参考"。
       所以必须同时看 ①纯数据句占比 ②结论/推荐密度。
    """
    sents = split_sentences(body)
    data_sents = 0
    n_data = n_op = 0
    for s in sents:
        d = len(DATA_RE.findall(s))
        o = len(OPINION_RE.findall(s))
        n_data += d
        n_op += o
        if d >= 2 and o == 0:          # 纯数据句: 有数据且不带结论
            data_sents += 1
    zh = sum(1 for c in body if '\u4e00' <= c <= '\u9fff') or 1
    listy = sum(body.count(w) for w in ('方向:', '方向是', '比分参考', '首选比分', '推荐', '预测'))
    return {'n_sent': len(sents), 'n_data_sent': data_sents,
            'ratio': data_sents / len(sents) if sents else 0,
            'n_data': n_data, 'n_op': n_op,
            'data_per_1k': n_data / zh * 1000,
            'listy': listy, 'listy_per_1k': listy / zh * 1000}


CN_NUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}

# 竞彩场次编号: 3 位数字, 前后不能再接数字或小数点(排除 2.13 / 100.0 这类赔率)
# ⚠️ 再排除"后接量词"的: **"469场"是回测样本量, 不是场次编号** ——
#    与 toutiao_stats.shape() 记录过的"10场不败/近5场"是同一类坑, 本次又踩了一次。
RE_MATCH_NO = re.compile(r'(?<![\d.])(\d{3})(?![\d.场次轮分球%点倍])')


def count_matches(body, title):
    """粗估稿件覆盖的场次数(抓"多场扫描"形态)

    ⚠️ 只认**编号本身**(周X前缀 / 编号连写 / 裸三位编号), 不认"N场"里的 N ——
       除非 N 后面紧跟打包词(速览/速评/串烧/盘点/精选/前瞻/连台/冒号)。
       实测: 双场稿 → 2; 11 场速评 → 14。区分度足够。
    """
    text = (title or '') + '\n' + body
    nums = set(RE_MATCH_NO.findall(text))
    n = len(nums)
    rng = re.search(r'(\d{3})\s*[-–]\s*(\d{3})', text)     # 002-004 区间写法
    if rng:
        n = max(n, abs(int(rng.group(2)) - int(rng.group(1))) + 1)
    n_title = 0
    m = re.search(r'(\d+|[一二三四五六七八九十]+)\s*场'
                  r'(?=速览|速评|速推|串烧|盘点|精选|前瞻|连台|[:：]|$)', title or '')
    if m:
        s = m.group(1)
        n_title = int(s) if s.isdigit() else CN_NUM.get(s, 0)
    return max(n, n_title), n, n_title


def extract_title(text):
    """取标题: 优先 H1(`# xxx`), 其次第一条非空且非 HTML 注释的行。

    ⚠️ 必须跳过 `<!-- style: X -->` —— 否则加了 style 标记后, 标题会被当成注释,
       连带 count_matches 的"场次数"也会跟着错(实测踩过一次)。
    """
    h1 = None
    first = None
    for l in text.split('\n'):
        s = l.strip()
        if not s:
            continue
        if s.startswith('<!--'):
            continue
        if s.startswith('# ') and h1 is None:
            h1 = s[2:].strip()
        if first is None and not s.startswith('#'):
            first = s
    return h1 or first or ''


def scan(path, plat):
    t = io.open(path, encoding='utf-8').read()
    body = clean(t.split('## 勿发布')[0])
    title = extract_title(t)
    P = PLATFORMS[plat]
    fails, warns = [], []

    print('=' * 88)
    print('%s   [平台: %s]' % (path.split('\\')[-1], P['label']))
    print('  门限: ' + P['note'])

    hits_by_level = {}
    for code, name, words in LEVELS:
        hits = []
        for w in words:
            n = body.count(w)
            ex = EXEMPT.get(w)
            if ex:                       # 扣掉正常语境里的出现(如"历史上")
                n -= len(ex.findall(body))
            if n > 0:
                hits.append('%s×%d' % (w, n))
        hits_by_level[code] = hits
        mark = ''
        if hits:
            if code in P['fail']:
                mark = '  ❌ 硬性失败'
                fails.append('%s: %s' % (name, ' '.join(hits)))
            elif code in P['warn']:
                mark = '  ⚠ 提示(该平台允许)'
                warns.append('%s: %s' % (name, ' '.join(hits)))
        print('  %-20s %s%s' % (name, (' '.join(hits) if hits else '无'), mark))

    # 比分 + 奖金组合
    combos = re.findall(r'\d+[:：]\d+\(\d+\.\d+\)', body)
    ok_combo = len(combos) <= P['max_combo']
    print('  %-20s %d 处 (上限 %d)%s' % ('比分+奖金组合', len(combos), P['max_combo'],
                                        '' if ok_combo else '  ❌ 硬性失败'))
    if not ok_combo:
        fails.append('比分+奖金组合 %d 处 > %d' % (len(combos), P['max_combo']))

    # "方向/主线 是/落在" 式定调
    ndir = len(re.findall(r'(方向|主线)[是落在]', body))
    print('  %-20s %d 处 (上限 %d)%s' % ('"方向"式定调', ndir, P['max_dir'],
                                        '' if ndir <= P['max_dir'] else '  ❌ 硬性失败'))
    if ndir > P['max_dir']:
        fails.append('"方向"式定调 %d 处 > %d' % (ndir, P['max_dir']))

    # 多场扫描形态
    # ⚠️ 门限 = 4 场, 不是 3 场(2026-09-20 校正)。依据 SOP §三·五:
    #    "多场串烧(双场/三场打包)" 是**常规双平台形态**;
    #    0915 风控里"公众号不做多场扫描"针对的是 §三·五·〇 的 **6-8 场速评/盘点** 清单形态。
    #    旧门限 3 会把正常的三场串烧误判为违规(实测 三场稿 编号=3 会命中)。
    nm, n_num, n_title = count_matches(body, title)
    multi_like = nm >= 4
    if multi_like:
        if P['multi_match_allowed']:
            print('  %-20s %d 场(编号%d/标题%d) ⚠ 头条低频形态, 谨慎' % ('覆盖场次', nm, n_num, n_title))
            warns.append('多场扫描形态: %d 场' % nm)
        else:
            print('  %-20s %d 场(编号%d/标题%d)  ❌ 硬性失败(公众号不做 4 场以上速评/盘点)'
                  % ('覆盖场次', nm, n_num, n_title))
            fails.append('多场扫描形态: %d 场(公众号不做 4 场以上)' % nm)
    else:
        print('  %-20s %d 场%s' % ('覆盖场次', nm,
                                   ' (双场/三场串烧, 属常规形态 ✅)' if nm >= 2 else ''))

    # 免责声明赌注语境
    has_bet_words = any(w in t for w in ('购彩', '投注', '下注'))
    if has_bet_words and not P['disclaimer_betting_ok']:
        print('  %-20s 含"购彩/投注"  ❌ 硬性失败(该平台须改写为不含赌注语境)' % '免责声明')
        fails.append('免责声明含赌注语境')
    elif has_bet_words:
        print('  %-20s 含"购彩/投注"(该平台允许)' % '免责声明')
    else:
        print('  %-20s 无赌注语境' % '免责声明')

    print('  %-20s 全字符 %d / 中文字 %d' % ('篇幅', len(body.replace('\n', '')),
                                             sum(1 for c in body if '\u4e00' <= c <= '\u9fff')))

    # ---- 公告第 1 点: 分析厚度 ----
    s = analysis_ratio(body)
    print('  ' + '-' * 64)
    print('  【分析厚度·启发式】公告第 1 点 = "可验证的技术分析占比较小或完全缺失"')
    print('     平台无公开阈值; 本指标为项目自定, 已用 2026-09-15 已知违禁稿标定。')
    print('  %-20s %d 句 (纯数据句 %d)' % ('可分析句数', s['n_sent'], s['n_data_sent']))
    print('  %-20s %.0f%%  (下限 %.0f%%)' % ('纯数据句占比', s['ratio'] * 100, P['ratio_min'] * 100))
    print('  %-20s 数据标记 %d / 结论标记 %d' % ('标记统计', s['n_data'], s['n_op']))
    print('  %-20s %.1f 处/千字  (上限 %.1f)' % ('结论·推荐密度', s['listy_per_1k'], P['listy_max']))
    if s['ratio'] < P['ratio_min']:
        fails.append('纯数据句占比 %.0f%% < %.0f%%' % (s['ratio'] * 100, P['ratio_min'] * 100))
    if s['listy_per_1k'] > P['listy_max']:
        fails.append('结论·推荐密度 %.1f > %.1f(清单形态)' % (s['listy_per_1k'], P['listy_max']))
    if s['ratio'] < P['ratio_min'] or s['listy_per_1k'] > P['listy_max']:
        print('  ⚠️ 第 1 点风险 —— 若同时命中 E 级词或 B1 框架, 即构成公告的"同时命中 2 点"')
    else:
        print('  ✅ 分析厚度达标 —— 公告第 1 点不成立')
    if s['n_op'] and s['n_data'] / s['n_op'] < 1.0:
        print('  ⚠️ 结论标记多于数据标记 —— 偏向"怎么看"而非"是什么"')

    # ---- 汇总 ----
    print('  ' + '-' * 64)
    if fails:
        print('  ❌ %s 未通过 (%d 项):' % (P['label'], len(fails)))
        for f in fails:
            print('     - ' + f)
    else:
        print('  ✅ %s 检查通过' % P['label'])
    if warns:
        print('  ⚠ 提示 %d 项(该平台允许, 仅记录):' % len(warns))
        for x in warns:
            print('     - ' + x)
    if not (P['fail'] and 'C' not in P['fail']) and hits_by_level.get('C'):
        print('  💡 若这是头条稿, 加 --platform toutiao 复核(C 级在头条允许)')
    return len(fails) == 0


def main():
    ap = argparse.ArgumentParser(description='发布前平台风险扫描(按平台套用不同门限)',
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='*', help='待扫描的 md 文件')
    ap.add_argument('--platform', choices=sorted(PLATFORMS), default='gzh',
                    help='平台口径, 默认 gzh(最严)')
    ap.add_argument('--toutiao', action='store_true', help='等价于 --platform toutiao')
    ap.add_argument('--gzh', action='store_true', help='等价于 --platform gzh')
    args = ap.parse_args()
    plat = 'toutiao' if args.toutiao else ('gzh' if args.gzh else args.platform)
    if not args.files:
        ap.print_help()
        return 1
    allok = True
    for p in args.files:
        allok &= scan(p, plat)
    print()
    print('总体: %s' % ('✅ 全部通过' if allok else '❌ 存在硬性失败'))
    return 0 if allok else 1


if __name__ == '__main__':
    sys.exit(main())
