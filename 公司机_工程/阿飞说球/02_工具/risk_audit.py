# -*- coding: utf-8 -*-
"""risk_audit.py — 闸门之外的盲区层(第 4 道), 与 risk_scan / check_md_release / zhuque 配套

由来: 2026-09-18 建的 `.uv-cache/risk_audit_20260918.py` 是一次性脚本(写死 D: 绝对路径 + 硬编码文件清单),
迁移后失效; 2026-09-21 出稿时**人工**才发现"公众号稿里还留着历史比分 4:1 / 2:0", 而三道闸门都没拦
(`risk_scan` 只拦"比分+奖金"; `check_md_release` 不管比分形态) → 按项目"闸门盲区"教训(坑#44 实例三), 提升为本工具。

用法:
  python risk_audit.py <稿件.md> [<稿件.md> ...]      # 自动按文件名判断平台(含"公众号"→公众号口径, 否则头条)
检查项:
  1. 公众号硬禁词(比 risk_scan 的 C 类更全, 含盘口/方向/竞彩/赌注语境)
  2. 比分形态: 任何 `X:X`(排除 H:MM 时间) —— 公众号一律不得出现, 含历史比分
  3. 免责声明语境(公众号不得含 购彩/投注)
  4. 未开售盘口是否被印数(探测稿内是否同时出现"未开售"与赔率形态数字)
  5. 头条博彩术语密度(仅记录, 与已发布基线对照用)
"""
import io, os, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

GZH_BAN = ['赔率', '让球', '受让', '走水', '低赔', '盘口', '竞彩', '比分盘', '奖金',
           '让胜', '让平', '让负', '大2.5', '小2.5', '半全场', '总进球', '投注', '购彩',
           '下注', '跟单', '赢盘', '输盘', '收米', '稳胆', '必赢', '梭哈', '倍投', '买单', '押',
           '方向', '倾向', '看好']
TT_TERMS = ['让球', '让胜', '让平', '让负', '走水', '盘口', '受让', '深盘', '低赔',
            '比分盘', '总进球', '半全场', '奖金', '热门']
RE_TIME = re.compile(r'(?<!\d)\d{1,2}[:：]\d{2}(?!\d)')          # 18:00 这类时间
RE_SCORE = re.compile(r'(?<!\d)\d{1,2}[:：]\d{1,2}(?!\d)')       # 比分形态
RE_ODDS = re.compile(r'(?<![\d.])\d{1,2}\.\d{2}(?![\d])')        # 赔率形态(两位小数)


def audit(path):
    t = io.open(path, encoding='utf-8', errors='ignore').read()
    name = os.path.basename(path)
    gzh = '公众号' in name
    print('=' * 96)
    print('%s   [口径: %s]' % (name, '公众号(收紧)' if gzh else '头条'))
    print('=' * 96)
    bad = 0

    # 1. 硬禁词
    hits = {w: t.count(w) for w in GZH_BAN if w in t}
    if gzh:
        if hits:
            bad += 1
            print('  ❌ 公众号硬禁词命中: %s' % ', '.join('%s×%d' % (k, v) for k, v in hits.items()))
            for w in hits:
                for ln in t.split('\n'):
                    if w in ln:
                        i = ln.find(w)
                        print('       「%s」…%s…' % (w, ln[max(0, i - 18):i + 18].strip()))
                        break
        else:
            print('  ✅ 公众号硬禁词: 0')
    else:
        print('  ℹ 头条: 硬禁词不适用(仅计术语密度); 命中: %s' % (
            ', '.join('%s×%d' % (k, v) for k, v in hits.items()) or '无'))

    # 2. 比分形态(排除时间)
    scores = []
    for m in RE_SCORE.finditer(t):
        s = m.group(0)
        if RE_TIME.fullmatch(s):
            continue
        scores.append(s)
    if gzh:
        if scores:
            bad += 1
            print('  ❌ 公众号出现比分形态 %d 处: %s   (历史比分也不行, 改写"进X球失Y球")'
                  % (len(scores), ', '.join(sorted(set(scores)))))
        else:
            print('  ✅ 比分形态: 0(时间除外)')
    else:
        print('  ℹ 头条: 比分形态 %d 处(允许, 但不许带奖金)' % len(scores))

    # 3. 免责声明语境
    decl = [l for l in t.split('\n') if l.startswith('【免责声明】')]
    if gzh:
        if not decl:
            bad += 1
            print('  ❌ 缺少【免责声明】')
        elif any(w in decl[0] for w in ('购彩', '投注')):
            bad += 1
            print('  ❌ 公众号免责声明含赌注语境: %s' % decl[0][:60])
        else:
            print('  ✅ 免责声明: 无赌注语境')

    # 4. 未开售处是否印数
    if '未开售' in t:
        seg = [l for l in t.split('\n') if '未开售' in l]
        n = sum(len(RE_ODDS.findall(l)) for l in seg)
        print('  %s 提到"未开售"的行内出现赔率形态数字 %d 个(应为 0 或仅指未开售本身)'
              % ('❌' if n else '✅', n))

    # 5. 头条术语密度
    if not gzh:
        cn = sum(1 for ch in t if '\u4e00' <= ch <= '\u9fff')
        c = sum(t.count(w) for w in TT_TERMS)
        per = c / cn * 1000 if cn else 0
        print('  ℹ 术语密度: %d 处 / %d 中文字 = %.1f 处每千字(记录用, 与已发布基线对照)' % (c, cn, per))

    print('  结论: %s' % ('❌ 有需处理项' if bad else '✅ 通过'))
    return bad


if __name__ == '__main__':
    files = sys.argv[1:]
    if not files:
        print(__doc__)
        sys.exit(2)
    n = sum(audit(f) for f in files)
    print('\n合计需处理项: %d' % n)
    sys.exit(1 if n else 0)
