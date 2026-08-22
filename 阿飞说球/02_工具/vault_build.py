# -*- coding: utf-8 -*-
"""
vault_build.py — 阿飞说球 Obsidian 金库构建器 v1.0
===================================================
把 04_赛事文章 变成可对话的第二大脑:
1. docx→md     : 为仅有 docx 的文章生成 md(金库/知识库双用)
2. frontmatter : 全部文章 md 注入 YAML 属性(产出月份/赛事/球队/tags)
3. 复盘 md     : reviews/*.json → 文章目录 <场次>_赛后复盘.md(含 [[前瞻]] 双链)
                并在前瞻 md 末尾加反向链
4. MOC 索引    : 04_赛事文章/00_MOC_赛事文章.md (按月+赛事索引全部文章)

幂等: md 已存在不覆盖; frontmatter 已注入跳过; 双链已加跳过。
用法: python vault_build.py
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 阿飞说球/
ART = os.path.join(BASE, '04_赛事文章')
REVIEWS = os.path.normpath(os.path.join(BASE, '..', '00_引擎', 'backtest', 'reviews'))

FM_KEYS = ('title:', 'type: match-preview')  # frontmatter 已注入的判据


def docx_to_md(path):
    """docx → 简单 md(段落 + 表格)"""
    from docx import Document
    doc = Document(path)
    lines = []
    for p in doc.paragraphs:
        t = p.text.strip()
        if t:
            lines.append(t)
    for tbl in doc.tables:
        if not tbl.rows:
            continue
        ncols = len(tbl.rows[0].cells)
        lines.append('| ' + ' | '.join(c.text.strip() for c in tbl.rows[0].cells) + ' |')
        lines.append('|' + '---|' * ncols)
        for row in tbl.rows[1:]:
            lines.append('| ' + ' | '.join(c.text.strip() for c in row.cells) + ' |')
    return '\n\n'.join(lines)


def build_frontmatter(match_name, month, text):
    comp = re.search(r'【赛事】([^\n]+)', text)
    mt = re.search(r'【时间】([^\n]+)', text)
    teams = [t.strip() for t in match_name.split('vs')] if 'vs' in match_name else []
    teams_yaml = '[' + ', '.join(f'"{t}"' for t in teams) + ']' if teams else '[]'
    return (f'---\n'
            f'title: "{match_name} 赛事前瞻"\n'
            f'date: "{month}"\n'
            f'type: match-preview\n'
            f'competition: "{comp.group(1).strip() if comp else ""}"\n'
            f'match_time: "{mt.group(1).strip() if mt else ""}"\n'
            f'teams: {teams_yaml}\n'
            f'tags: [赛事前瞻, {month}]\n'
            f'---\n\n')


def ensure_frontmatter(md_path, match_name, month):
    """幂等注入 frontmatter"""
    with open(md_path, encoding='utf-8') as f:
        text = f.read()
    head = text[:200]
    if 'type: match-preview' in head:
        return False
    fm = build_frontmatter(match_name, month, text[:1500])
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(fm + text)
    return True


def review_md_path(match, month):
    """复盘 md 放对应文章目录(与前瞻同级, 便于双链)"""
    return os.path.join(ART, month, match, f'{match}_赛后复盘.md')


def build_review_md(rec):
    match = rec['match']
    # 从留档 source 或 config 反推月份目录: 用 reviews 里 date 的 YYYY-MM
    month = rec.get('date', '')[:7] or '2026'
    text = rec.get('review_text', '')
    return (f'---\n'
            f'title: "{match} 赛后复盘"\n'
            f'date: "{rec.get("date", "")}"\n'
            f'type: match-review\n'
            f'link: "[[{match}_赛事前瞻]]"\n'
            f'tags: [赛后复盘, 验证闭环]\n'
            f'---\n\n'
            f'> 关联前瞻: [[{match}_赛事前瞻]]\n\n'
            f'{text}\n')


def add_backlink(md_path, review_note):
    """前瞻 md 末尾加反向链(幂等)"""
    with open(md_path, encoding='utf-8') as f:
        text = f.read()
    marker = f'[[{review_note}]]'
    if marker in text:
        return False
    with open(md_path, 'a', encoding='utf-8') as f:
        f.write(f'\n---\n📎 赛后复盘: {marker}\n')
    return True


def main():
    # 1. 收集文章(月份, 场次, md路径或docx路径)
    articles = []  # (month, match, md_path|None, docx_path|None)
    for month in sorted(os.listdir(ART)):
        md = os.path.join(ART, month)
        if not os.path.isdir(md) or not re.match(r'^\d{4}-\d{2}$', month):
            continue
        for match in sorted(os.listdir(md)):
            d = os.path.join(md, match)
            if not os.path.isdir(d):
                continue
            mds = sorted(f for f in os.listdir(d) if f.endswith('.md') and '复盘' not in f)
            dxs = sorted(f for f in os.listdir(d) if f.endswith('.docx'))
            articles.append((month, match, d,
                             os.path.join(d, mds[0]) if mds else None,
                             os.path.join(d, dxs[0]) if dxs else None))

    # 2. docx→md 补齐
    gen = 0
    for month, match, d, mdp, dxp in articles:
        if not mdp and dxp:
            md_out = os.path.join(d, os.path.splitext(os.path.basename(dxp))[0] + '.md')
            with open(md_out, 'w', encoding='utf-8') as f:
                f.write(docx_to_md(dxp))
            gen += 1
            print(f'  docx→md: {month}/{match}')
    print(f'✔ 生成 md {gen} 篇' + ('' if gen else ' (无)'))

    # 3. frontmatter 注入
    fm_n = 0
    for month, match, d, mdp, dxp in articles:
        md_file = mdp or os.path.join(d, os.path.splitext(os.path.basename(dxp))[0] + '.md') if dxp else None
        if md_file and os.path.exists(md_file):
            if ensure_frontmatter(md_file, match, month):
                fm_n += 1
    print(f'✔ frontmatter 注入 {fm_n} 篇')

    # 4. 复盘 md + 反向链
    rev_n = bl_n = 0
    if os.path.isdir(REVIEWS):
        for fn in sorted(os.listdir(REVIEWS)):
            if not fn.endswith('.json'):
                continue
            with open(os.path.join(REVIEWS, fn), encoding='utf-8') as f:
                rec = json.load(f)
            match = rec['match']
            month = rec.get('date', '')[:7]
            rmd = review_md_path(match, month)
            if not os.path.exists(rmd):
                os.makedirs(os.path.dirname(rmd), exist_ok=True)
                with open(rmd, 'w', encoding='utf-8') as f:
                    f.write(build_review_md(rec))
                rev_n += 1
            # 反向链: 找前瞻 md
            pdir = os.path.dirname(rmd)
            for f2 in os.listdir(pdir):
                if f2.endswith('.md') and '复盘' not in f2:
                    if add_backlink(os.path.join(pdir, f2), f'{match}_赛后复盘'):
                        bl_n += 1
                    break
    print(f'✔ 复盘 md {rev_n} 篇 | 反向链 {bl_n} 处')

    # 5. MOC 索引(重写)
    moc_lines = ['---', 'title: 赛事分析索引', 'type: moc', 'tags: [索引]', '---', '',
                 '# 🗂 阿飞·赛博聊球 赛事分析索引', '',
                 '> 文章按产出月份归档于 `04_赛事文章/<YYYY-MM>/`; 复盘与前瞻互为双链。', '']
    for month in sorted(os.listdir(ART)):
        md = os.path.join(ART, month)
        if not os.path.isdir(md) or not re.match(r'^\d{4}-\d{2}$', month):
            continue
        items = []
        for match in sorted(os.listdir(md)):
            d = os.path.join(md, match)
            if not os.path.isdir(d):
                continue
            mds = [f for f in os.listdir(d) if f.endswith('.md')]
            preview = next((f for f in mds if '复盘' not in f), None)
            review = next((f for f in mds if '复盘' in f), None)
            if preview:
                note = os.path.splitext(preview)[0]
                comp = ''
                try:
                    head = open(os.path.join(d, preview), encoding='utf-8').read(600)
                    cm = re.search(r'competition: "([^"]*)"', head)
                    comp = cm.group(1) if cm else ''
                except Exception:
                    pass
                line = f'- [[{note}|{match}]]' + (f' — {comp}' if comp else '')
                if review:
                    line += f' 📎 [[{os.path.splitext(review)[0]}|复盘]]'
                items.append(line)
        if items:
            ym = month.replace('-', '年') + '月'
            moc_lines += [f'## {ym} ({month})', *items, '']
    moc_path = os.path.join(ART, '00_MOC_赛事文章.md')
    with open(moc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(moc_lines))
    print(f'✔ MOC: {moc_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
