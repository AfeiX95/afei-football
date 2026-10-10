# -*- coding: utf-8 -*-
"""
check_md_release.py — 公众号深度版 md 文件核查(手工复现 check_release 的 8 项)
针对 .md 适配: 跳过 docx 的段落/表格概念, 直接读全文

检查项:
  1. 高风险词清零 + "投注" 仅免责声明
  2. 破折号 ≤6
  3. 套话清零
  4. 超60字长句 ≤1
  5. 【数据来源】+【免责声明】在位
  6. 标题 ≤60字 (公众号深度版, config.skeleton='深度叙事式') + 无俗语
  7. 占位符残留清零
  8. 章节结构(深度版特有:style 标记 + 至少 6 个 ## 章节 + λ±10% 表存在)
"""
import re
import sys
import os

try:  # Windows 控制台默认 GBK, emoji 一打印就 UnicodeEncodeError 崩掉整轮检查
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HI_RISK = ['买', '押', '下注', '跟单', '稳胆', '必赢', '稳赢', '输盘', '赢盘',
           '埋雷', '收米', '红单', '回血', '上岸', '倍投', '梭哈', '买单']
CLICHE = ['总的来说', '值得注意的是', '综上所述', '无疑', '彰显', '显而易见',
          '众所周知', '不仅仅', '更是', '不言而喻', '令人瞩目']
BANNED_TITLE = ['主场龙', '客场虫', '强强对话', '谁能笑到最后', '激情碰撞', '巅峰对决',
                '王者对决', '狭路相逢', '火星撞地球', '生死战一触即发', '鹿死谁手']
TITLE_MAX_GZH = 60
# 2026-09-17 由 30 放宽到 36; 2026-09-20 全量 262 篇复核: 36 字上限无害也无收益(见 check_toutiao 注释)
TITLE_MAX_TOUTIAO = 36
DASH_LIMIT = 6
LONG_SENT_LIMIT = 60

# SEO: "主队vs客队" 队名对位。
# ⚠️ 规则(2026-09-20 用户确认): 标题里只要有【任意一处】真实的队名对位就算通过。
#    所以必须逐处检查每一个 "vs", 不能只看第一个 —— 否则
#    "模型vs市场 罗马vs国米" 会因为第一处是假阳性而被误判为不通过。
VS_OCC = re.compile(r'vs', re.I)
_RUN_CH = re.compile(r'[\u4e00-\u9fa5A-Za-z0-9]')
# 主客注解: 稿件惯例会写 "布伦特福德(主)vs 切尔西"; 匹配前先摘掉, 否则左侧取到的是"主"
_VS_ANNOT = re.compile(r'[（(]\s*[主客]\s*[)）]')

# ⚠️ 反例: "模型vs市场" "机构vs数据" 这类形状合规但**不含队名**,
#    搜索引擎拿不到任何球队关键词, 属假阳性。命中这些词的那一处对位不算数。
VS_FALSE_POSITIVE = ['模型', '市场', '机构', '数据', '盘口', '赔率', '历史', '实力',
                     '状态', '主队', '客队', '两队', '双方', '攻防', '冷热', '明暗']


def find_team_vs(title):
    """返回标题里第一处【真实队名对位】的字符串; 没有则 None。

    逐处扫描每个 'vs'(不区分大小写), 取它左右两侧的连续中英文/数字串作为队名候选。
    ⚠️ 两侧都要先跳过空格 —— 实测漏掉这一步会误杀 "阿根廷 vs 佛得角" 这类写法。
    用 \\u4e00-\\u9fa5 而非 \\w, 是为了让标点自然截断, 避免把前缀一起吞进来。
    """
    if not title:
        return None
    probe = _VS_ANNOT.sub('', title)      # 摘掉 (主)/(客) 注解
    low = probe.lower()
    pos = 0
    while True:
        i = low.find('vs', pos)
        if i < 0:
            return None
        l = i
        while l > 0 and probe[l - 1].isspace():   # 跳过 vs 左侧空格
            l -= 1
        while l > 0 and _RUN_CH.match(probe[l - 1]):
            l -= 1
        r = i + 2
        while r < len(probe) and probe[r].isspace():   # 跳过 vs 右侧空格
            r += 1
        r0 = r
        while r < len(probe) and _RUN_CH.match(probe[r]):
            r += 1
        left, right = probe[l:i], probe[r0:r]
        if len(left) >= 2 and len(right) >= 2:
            pair = f'{left}vs{right}'
            if not any(w in pair for w in VS_FALSE_POSITIVE):
                return pair
        pos = i + 2


def has_team_vs(title):
    """标题里是否有【真正含队名的】主队vs客队对位(供 SEO 用)"""
    return find_team_vs(title) is not None

PLACEHOLDER_RE = re.compile(r'\{[a-zA-Z_][a-zA-Z_0-9]*\}')


def split_md_lines(path):
    """读 md 行,过滤掉特殊格式行(标题/tags/信息卡/表格/图注/引用)"""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    lines = text.split('\n')
    # 提取标题: 公众号按 H1; 头条版无 H1, 标题是第一行非空文本(2026-09-16 起头条出 md)
    title = ''
    for l in lines:
        m = re.match(r'^# (.+)$', l)
        if m:
            title = m.group(1).strip()
            break
    if not title:
        # 公众号版无 H1: 标题在文末「勿发布」块的"标题候选" 里
        for l in lines:
            m = re.search(r'标题候选[^「]*「(.+?)」', l)
            if m:
                title = m.group(1).strip()
                break
    if not title:
        for l in lines:
            s = l.strip()
            if s and not s.startswith(('#', '<!--', '【', '|')):
                title = s
                break
    # 跳过: tags行 (#xxx) / 信息卡【...】 / 表格 |...| / 引用 >... / H1/H2/H3 / 空行 / 图注 ![](...)
    body = []
    for l in lines:
        s = l.strip()
        if not s: continue
        if s.startswith('#'): continue  # 标题行
        if s.startswith('|') or s.startswith('!['): continue  # 表格/图片
        if s.startswith('>'): continue  # 引用
        if s.startswith('【') and len(s) < 40: continue  # 短信息卡
        if s.startswith('<!--'): continue  # 注释
        if not title or s == title: continue  # 无 H1 时的标题行本身
        body.append(l)
    return title, text, lines, body


def check_toutiao(path):
    """头条版 md 终检(2026-09-16 起: 头条出 md、不配图、图表改表格)"""
    print(f'🔍 头条版核查: {os.path.basename(path)}')
    print('=' * 70)
    title, full, lines, body = split_md_lines(path)
    problems, ok = [], []
    # 1. 标题
    #    长度: 2026-09-17 由 30 放宽到 36。⚠️ 2026-09-20 用全量 262 篇复核后修正依据:
    #    旧依据"≤30字组 CTR 5.3% vs >30字组 8.9%"是 30 篇小样本的产物。
    #    全量口径: ≤30字 6.9% / 31-36字 7.6% / >36字 7.4%, >36 vs ≤30 差 +0.49pp, p=0.575 不显著。
    #    → 36 字上限**无害但也无收益**, 保留它只是为了避免搜索/feed 截断, 不是 CTR 杠杆。
    if not title:
        problems.append('❌ 未取到标题(头条版第一行应为标题)')
    elif len(title) > TITLE_MAX_TOUTIAO:
        problems.append(f'❌ 标题 {len(title)} 字 > {TITLE_MAX_TOUTIAO} (头条上限)')
    elif len(title) > 30:
        ok.append(f'⚠ 标题 {len(title)} 字(超 30 提示线但 ≤{TITLE_MAX_TOUTIAO})')
    else:
        ok.append(f'✅ 标题 {len(title)} 字 ≤ 30')
    # 1b. SEO: 标题必须含"主队vs客队"
    #     依据(2026-09-20 全量复盘 §11/§SEO): 无搜索来源字段, **无法验证搜索收益**;
    #     但可验证"加 vs 无推荐侧代价" —— CTR 差 -0.03pp (p=0.991),
    #     且原始的"含vs展现更低"经月份分层后反转(4个月里3个月含vs更高), 属辛普森悖论。
    #     同时全量 262 篇里约 1/3 标题连双方队名都没有, 搜索侧等于放弃。
    if title:
        if has_team_vs(title):
            ok.append('✅ 标题含"主队vs客队"队名对位(SEO)')
        else:
            problems.append('❌ 标题缺"主队vs客队"队名对位(SEO 必需; 搜索只认队名, 不认"精选场/速览")')
    bw = [w for w in BANNED_TITLE if w in title]
    if bw:
        problems.append(f'❌ 标题俗语: {bw}')
    # 2. 不配图 + 必须有表格(替代图表)
    if '![' in full:
        problems.append(f'❌ 出现图片语法 {full.count("![")} 处(头条版不配图)')
    else:
        ok.append('✅ 无图片(已按要求改为表格/数据)')
    n_tbl = sum(1 for l in lines if l.strip().startswith('|---') or l.strip().startswith('|:--'))
    if n_tbl == 0:
        problems.append('❌ 无表格: 头条版要求用表格表达核心矛盾与数据对比')
    else:
        ok.append(f'✅ 表格 {n_tbl} 张')
    # 3. 高风险词 / 投注
    hits = [w for w in HI_RISK if w in full]
    if hits:
        problems.append(f'❌ 高风险词: {hits}')
    else:
        ok.append('✅ 高风险词清零')
    # 4. 破折号 / 长句
    body_text = '\n'.join(body)
    dash = body_text.count('——')
    ok.append(f'{"✅" if dash <= 6 else "❌"} 破折号 {dash} 处 (≤6)')
    if dash > 6:
        problems.append(f'❌ 破折号 {dash} 处 > 6')
    # 长句 = 单句 >60 字(按句号/问号/叹号切, 不是按行切)
    long_lines = []
    for s in body:
        if s.startswith('【'):
            continue
        for sent in re.split(r'[。！？]', s):
            if len(sent.strip()) > 60:
                long_lines.append(sent.strip())
    if len(long_lines) > 1:
        problems.append(f'❌ 超60字长句 {len(long_lines)} 个 (≤1):')
        for s in long_lines[:4]:
            problems.append(f'    ⚠ {s[:52]}…')
    else:
        ok.append(f'✅ 长句 {len(long_lines)} 个 (≤1)')
    # 5. 套话 + footer
    cl = [w for w in CLICHE if w in full]
    if cl:
        problems.append(f'❌ 套话: {cl}')
    else:
        ok.append('✅ 套话清零')
    if '数据来源' in full and '免责声明' in full:
        ok.append('✅ 数据来源 + 免责声明 在位')
    else:
        problems.append('❌ 缺【数据来源】或【免责声明】')
    print('\n'.join('  ' + l for l in ok))
    print()
    if problems:
        print(f'❌ 头条版核查未通过 ({len(problems)} 项):')
        for p in problems:
            print('  ' + p)
        return 1
    print('✅ 头条版核查全部通过')
    return 0


def check(path, mode='gzh'):
    """mode='gzh' 公众号深度版 | mode='toutiao' 头条版(标题≤30字, 无图, 必须有表格)"""
    if mode == 'toutiao':
        return check_toutiao(path)
    print(f'🔍 公众号深度版核查: {os.path.basename(path)}')
    print('=' * 70)

    title, full, lines, body = split_md_lines(path)
    problems = []
    ok_lines = []

    # 7. 占位符残留
    leftover = []
    for i, s in enumerate(lines):
        for m in PLACEHOLDER_RE.finditer(s):
            ctx = s[max(0, m.start()-12):m.end()+12].replace('\n', ' ')
            leftover.append((m.group(), i, ctx))
    if leftover:
        problems.append(f'❌ 占位符残留 {len(leftover)} 处 (如 {leftover[0][0]}):')
        for ph, i, ctx in leftover[:3]:
            problems.append(f'    ⚠ 第{i}行 …{ctx}…')
    else:
        ok_lines.append('✅ 占位符清零')

    # 1. 高风险词
    hits = [w for w in HI_RISK if w in full]
    tou_lines = [i for i, l in enumerate(lines) if '投注' in l]
    tou_disclaimer_only = all('免责声明' in lines[i] for i in tou_lines)
    if hits:
        problems.append(f'❌ 高风险词: {hits}')
    elif tou_lines and not tou_disclaimer_only:
        problems.append(f'❌ "投注"出现在非免责声明行: {tou_lines}')
    elif tou_lines:
        ok_lines.append('✅ 高风险词清零 (投注仅免责声明)')
    elif '免责声明' in full:
        # 2026-09-15 平台规则: 公众号免责声明**故意不含**"购彩/投注"字样(赌注语境会触发检测)
        ok_lines.append('✅ 高风险词清零 (公众号口径: 免责声明不含赌注语境)')
    else:
        problems.append('❌ 缺免责声明')

    # 2. 破折号
    body_text = '\n'.join(body)
    dash = body_text.count('——')
    if dash > DASH_LIMIT:
        problems.append(f'❌ 破折号 {dash} 处 > {DASH_LIMIT}')
    else:
        ok_lines.append(f'✅ 破折号 {dash} 处 (≤{DASH_LIMIT})')

    # 3. 套话
    cl = [w for w in CLICHE if w in full]
    if cl:
        problems.append(f'❌ 套话词: {cl}')
    else:
        ok_lines.append('✅ 套话清零')

    # 5. 数据来源/免责声明 (先把模板行过滤)
    #    ⚠️ 过滤器不能依赖模板的**具体措辞**(2026-09-12 教训: 模板精简后 '基础数据取自' 失效)
    #       → 改为按"以【数据来源】/【免责声明】开头"识别模板行
    body_for_long = [l for l in body
                     if not l.strip().startswith('【数据来源】')
                     and not l.strip().startswith('【免责声明】')]
    long_lines = []
    for l in body_for_long:
        s = l.strip()
        if not s: continue
        if s.startswith('- ') or s.startswith('* '): continue
        if s.startswith('|') or s.startswith('!['): continue
        if s.startswith('>'): continue
        if s.startswith('【') and len(s) < 40: continue
        if s.startswith('#'): continue
        if s.startswith('<!--'): continue
        # ⚠️ 长句按"单句"算(2026-09-16 修): 原来按整行算, 2-4 句的段落必然全被误判
        for sent in re.split(r'[。！？]', s):
            if len(sent.strip()) > LONG_SENT_LIMIT:
                long_lines.append(sent.strip())
    if len(long_lines) > 1:
        problems.append(f'❌ 超{LONG_SENT_LIMIT}字长句 {len(long_lines)} 个 (≤1):')
        for s in long_lines[:5]:
            problems.append(f'    ⚠ {s[:55]}…')
    else:
        ok_lines.append(f'✅ 长句 {len(long_lines)} 个 (≤1)')

    # 5. 数据来源/免责声明
    if '数据来源' not in full:
        problems.append('❌ 缺【数据来源】')
    if '免责声明' not in full:
        problems.append('❌ 缺【免责声明】')
    if '数据来源' in full and '免责声明' in full:
        ok_lines.append('✅ 数据来源 + 免责声明 在位')

    # 6. 标题
    if len(title) > TITLE_MAX_GZH:
        problems.append(f'❌ 标题 {len(title)} 字 > {TITLE_MAX_GZH} (公众号深度版上限)')
    bw = [w for w in BANNED_TITLE if w in title]
    if bw:
        problems.append(f'❌ 标题俗语: {bw}')
    if len(title) <= TITLE_MAX_GZH and not bw:
        ok_lines.append(f'✅ 标题 {len(title)} 字 ≤ {TITLE_MAX_GZH}, 无俗语')

    # 8. 公众号深度版特有: style 标记 + ≥6个 ## 章节 + λ±10% 区间表
    has_style = '<!-- style:' in full
    h2_count = sum(1 for l in lines if l.startswith('## ') and not l.startswith('### '))
    has_lambda_table = 'λ' in full and ('±10%' in full or '± 10%' in full or '场景' in full)
    extra = []
    if has_style:
        m = re.search(r'<!-- style: (.+?) -->', full)
        extra.append(f'✅ style: {m.group(1) if m else "?"}')
    else:
        extra.append('⚠ style 标记缺失')
    extra.append(f'{"✅" if h2_count>=6 else "⚠"} ## 章节数: {h2_count} (深度版 ≥6)')
    extra.append(f'{"✅" if has_lambda_table else "⚠"} λ±10% 区间表: {"有" if has_lambda_table else "无"}')

    # 汇总
    print('\n'.join('  ' + l for l in ok_lines + extra))
    print()
    if problems:
        print(f'❌ 核查未通过 ({len(problems)} 项):')
        for p in problems:
            print('  ' + p)
        return 1
    print('✅ 公众号深度版核查全部通过')
    return 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    mode = 'toutiao' if '--toutiao' in sys.argv else 'gzh'
    if not args:
        print('用法: python check_md_release.py <path.md> [--toutiao]')
        sys.exit(1)
    sys.exit(check(args[0], mode))