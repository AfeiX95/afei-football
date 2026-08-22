# -*- coding: utf-8 -*-
"""
check_release.py — 头条发布前核查 v1.0
=======================================
用法:
    python check_release.py --docx 04_赛事文章/2026-08/波鸿vs柏林赫塔/波鸿vs柏林赫塔_赛事前瞻.docx
    python check_release.py --docx <路径> --config match_configs/波鸿vs柏林赫塔.json

检查项:
  1. 高风险词清零(买/押/下注/稳胆/赢盘/埋雷/收米/买单等; "投注"仅允许在免责声明)
  2. 破折号 ≤6 处(固定格式:dash分隔线+口头禅不计入, 计正文)
  3. 套话清零(总的来说/值得注意的是/无疑/彰显/众所周知 等)
  4. 超60字长句 ≤1
  5. 【数据来源】+【免责声明】在位
  6. 标题 ≤30字 + 无俗语(主场龙/客场虫/强强对话等)
  7. 钩子类型去重(需 --config): 最近3篇已用 hook_type 不重复
  8. 模板占位符残留清零({lam_h}/{pH} 等 {xxx} 占位符)
退出码: 0=通过, 1=有问题(逐项打印)
"""
import argparse
import json
import os
import re
import sys
from collections import deque

from docx import Document

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(TOOL_DIR, 'match_configs')

# 词表
HI_RISK = ['买', '押', '下注', '跟单', '稳胆', '必赢', '稳赢', '输盘', '赢盘',
           '埋雷', '收米', '红单', '回血', '上岸', '倍投', '梭哈', '买单']
CLICHE = ['总的来说', '值得注意的是', '综上所述', '无疑', '彰显', '显而易见',
          '众所周知', '不仅仅', '更是', '不言而喻', '令人瞩目']
BANNED_TITLE = ['主场龙', '客场虫', '强强对话', '谁能笑到最后', '激情碰撞', '巅峰对决',
                '王者对决', '狭路相逢', '火星撞地球', '生死战一触即发', '鹿死谁手']
TITLE_MAX = 30
DASH_LIMIT = 6
LONG_SENT_LIMIT = 60


def docx_fulltext(path):
    doc = Document(path)
    paras = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            paras.append(' | '.join(c.text for c in row.cells))
    return doc, paras


# 8. 模板占位符残留(关键硬伤: 2026-08-13 巴黎vs维拉 4处 {pH}% 上线事故)
PLACEHOLDER_RE = re.compile(r'\{[a-zA-Z_][a-zA-Z_0-9]*\}')


def check(path, config_path=None):
    problems = []
    doc, paras = docx_fulltext(path)
    full = '\n'.join(paras)

    # 8. 模板占位符残留
    leftover = []
    for i, s in enumerate(paras):
        for m in PLACEHOLDER_RE.finditer(s):
            ctx = s[max(0, m.start()-12):m.end()+12].replace('\n', ' ')
            leftover.append((m.group(), i, ctx))
    if leftover:
        problems.append(f'❌ 模板占位符残留 {len(leftover)} 处 (如 {leftover[0][0]}):')
        for ph, i, ctx in leftover[:5]:
            problems.append(f'    ⚠ 第{i}段 …{ctx}…')

    # 1. 高风险词
    hits = [w for w in HI_RISK if w in full]
    tou = [s for s in paras if '投注' in s]
    if hits:
        problems.append(f'❌ 高风险词: {hits}')
    if tou and not all('免责声明' in s for s in tou):
        problems.append(f'❌ "投注"出现在非免责声明: {tou}')
    elif '免责声明' in full and not tou:
        problems.append('⚠ 免责声明模板缺"投注"字样(模板被改动?)')

    # 2. 破折号(仅正文, 排除 dash 分隔线与口头禅)
    body = [s for s in paras if s not in ('——',) and '阿飞·赛博聊球' not in s]
    dash = sum(s.count('——') for s in body)
    if dash > DASH_LIMIT:
        problems.append(f'❌ 破折号 {dash} 处 > {DASH_LIMIT}')

    # 3. 套话
    cl = [w for w in CLICHE if w in full]
    if cl:
        problems.append(f'❌ 套话词: {cl}')

    # 4. 超60字长句(排除固定格式行: 标题/tags/信息卡/图注/表格)
    body = [s for s in paras[2:]  # 跳过标题+tags
            if not (s.startswith('【') and len(s) < 40)   # 短信息卡行
            and not s.startswith('图') and not s.startswith('|')
            and ' | ' not in s                            # 表格行
            and s not in ('——',) and '阿飞·赛博聊球' not in s]
    body_text = '\n'.join(body)
    longs = [s for s in re.split(r'[。！？!?]', body_text) if len(s) > LONG_SENT_LIMIT]
    if len(longs) > 1:
        problems.append(f'❌ 超{LONG_SENT_LIMIT}字长句 {len(longs)} 个 (≤1):')
        for s in longs[:3]:
            problems.append(f'    ⚠ {s.strip()[:55]}…')

    # 5. 数据来源/免责声明
    if '数据来源' not in full:
        problems.append('❌ 缺【数据来源】')
    if '免责声明' not in full:
        problems.append('❌ 缺【免责声明】')

    # 6. 标题(2026-08-22: 深度版 config 走公众号 60 字 SEO 上限, 其余按头条 30 字)
    cfg = {}
    if config_path and os.path.exists(config_path):
        with open(config_path, encoding='utf-8') as f:
            cfg = json.load(f)
    title = paras[0] if paras else ''
    title_max = 60 if cfg.get('skeleton') == '深度叙事式' else TITLE_MAX
    if len(title) > title_max:
        problems.append(f'❌ 标题 {len(title)} 字 > {title_max}')
    bw = [w for w in BANNED_TITLE if w in title]
    if bw:
        problems.append(f'❌ 标题俗语: {bw}')

    # 7. 钩子类型去重 + 骨架去重
    if cfg:
        recent = []
        cfgs = sorted(
            (os.path.join(CONFIG_DIR, fn) for fn in os.listdir(CONFIG_DIR) if fn.endswith('.json')),
            key=os.path.getmtime, reverse=True)
        for cp in cfgs:
            if cp == os.path.abspath(config_path):
                continue
            try:
                with open(cp, encoding='utf-8') as f:
                    recent.append(json.load(f))
            except Exception:
                pass
            if len(recent) >= 3:
                break

        ht = cfg.get('hook_type', '')
        if ht:
            recent_ht = [r.get('hook_type', '') for r in recent]
            if ht in recent_ht:
                problems.append(f'❌ 钩子类型 "{ht}" 与最近文章重复 (近期: {recent_ht})')
            else:
                print(f'✅ 钩子类型 "{ht}" 未与近3篇重复 (近期: {recent_ht})')

        sk = cfg.get('skeleton', '')
        if sk:
            recent_sk = [r.get('skeleton', '') for r in recent]
            if sk in recent_sk:
                problems.append(f'❌ 骨架 "{sk}" 与最近文章重复 (近期: {recent_sk})')
            else:
                print(f'✅ 骨架 "{sk}" 未与近3篇重复 (近期: {recent_sk})')

    # 汇总
    if problems:
        print(f'🔍 {os.path.basename(path)} 核查未通过 ({len(problems)} 项):')
        for p in problems:
            print('  ' + p)
        return 1
    ok_lines = ['✅ 高风险词清零', f'✅ 破折号 {dash} 处', '✅ 套话清零',
                f'✅ 长句 {len(longs)} 个', '✅ 数据来源/免责声明在位',
                f'✅ 标题 {len(title)} 字无俗语', '✅ 模板占位符清零']
    print(f'✅ {os.path.basename(path)} 发布核查全部通过:')
    for l in ok_lines:
        print('  ' + l)
    return 0


def main():
    ap = argparse.ArgumentParser(description='头条发布前核查')
    ap.add_argument('--docx', required=True, help='文章 docx 路径')
    ap.add_argument('--config', help='对应 config(钩子去重需要)')
    args = ap.parse_args()
    if not os.path.exists(args.docx):
        print(f'❌ 文件不存在: {args.docx}')
        return 1
    sys.exit(check(args.docx, args.config))


if __name__ == '__main__':
    main()
