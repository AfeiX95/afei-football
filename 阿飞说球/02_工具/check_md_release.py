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

HI_RISK = ['买', '押', '下注', '跟单', '稳胆', '必赢', '稳赢', '输盘', '赢盘',
           '埋雷', '收米', '红单', '回血', '上岸', '倍投', '梭哈', '买单']
CLICHE = ['总的来说', '值得注意的是', '综上所述', '无疑', '彰显', '显而易见',
          '众所周知', '不仅仅', '更是', '不言而喻', '令人瞩目']
BANNED_TITLE = ['主场龙', '客场虫', '强强对话', '谁能笑到最后', '激情碰撞', '巅峰对决',
                '王者对决', '狭路相逢', '火星撞地球', '生死战一触即发', '鹿死谁手']
TITLE_MAX_GZH = 60
DASH_LIMIT = 6
LONG_SENT_LIMIT = 60

PLACEHOLDER_RE = re.compile(r'\{[a-zA-Z_][a-zA-Z_0-9]*\}')


def split_md_lines(path):
    """读 md 行,过滤掉特殊格式行(标题/tags/信息卡/表格/图注/引用)"""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    lines = text.split('\n')
    # 提取 H1 标题
    title = ''
    for l in lines:
        m = re.match(r'^# (.+)$', l)
        if m:
            title = m.group(1).strip()
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
        body.append(l)
    return title, text, lines, body


def check(path):
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
    elif '免责声明' in full and not tou_lines:
        problems.append('⚠ 免责声明缺"投注"字样(模板被改动?)')
    else:
        ok_lines.append('✅ 高风险词清零 (投注仅免责声明)')

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
        if len(s) > LONG_SENT_LIMIT:
            long_lines.append(s)
    if len(long_lines) > 1:
        problems.append(f'❌ 单行超{LONG_SENT_LIMIT}字长句 {len(long_lines)} 个 (≤1):')
        for s in long_lines[:5]:
            problems.append(f'    ⚠ {s[:55]}…')
    else:
        ok_lines.append(f'✅ 单行长句 {len(long_lines)} 个 (≤1)')

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
    if len(sys.argv) < 2:
        print('用法: python check_md_release.py <path.md>')
        sys.exit(1)
    sys.exit(check(sys.argv[1]))