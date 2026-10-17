# -*- coding: utf-8 -*-
"""
阿飞说球 三端 Agent bridge 生成脚本
真源: I:\阿飞说球\📚知识库\skills\<技能名>\SKILL.md (27个)
输出(预览模式): I:\阿飞说球\preview\bridges\{claude,codex,grok}\<技能名>\SKILL.md
用法: python database/gen_agent_bridges.py [--deploy]
  --deploy 时直接写入宿主目录 (~/.claude/skills, ~/.codex/skills, ~/.grok/skills)
"""
import os
import sys
import shutil
import re
import io

sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'I:\阿飞说球'
SKILLS_DIR = os.path.join(ROOT, '📚知识库', 'skills')
PREVIEW_DIR = os.path.join(ROOT, 'preview', 'bridges')

HOST_DIRS = {
    'claude': os.path.expanduser(r'~\.claude\skills'),
    'codex': os.path.expanduser(r'~\.codex\skills'),
    'grok': os.path.expanduser(r'~\.grok\skills'),
}


def read_frontmatter(skill_dir):
    """读取 SKILL.md 的 name + description"""
    path = os.path.join(skill_dir, 'SKILL.md')
    with open(path, encoding='utf-8') as f:
        text = f.read()
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    # name 优先用目录名（稳定），frontmatter name 仅作参考
    name = os.path.basename(skill_dir)
    desc = '足球分析技能（阿飞说球）'
    if m:
        fm = m.group(1)
        nm = re.search(r'^name:\s*(.+)$', fm, re.MULTILINE)
        if nm:
            candidate = nm.group(1).strip().strip('"\'')
            # 目录名与 frontmatter name 不一致时以目录名为准（三端统一）
            if candidate and candidate.lower().replace('-', '_') == name.lower().replace('-', '_'):
                name = candidate
        dm = re.search(r'^description:\s*["\']?(.+?)$', fm, re.MULTILINE)
        if dm:
            desc = dm.group(1).strip().strip('"\'')
            if len(desc) > 180:
                desc = desc[:177] + '...'
    return name, desc


def gen_claude_bridge(name, desc, abs_source):
    return f'''---
name: {name}
description: {desc}
source_of_truth: {abs_source}
bridge_mode: passthrough
---
# {name}（Claude Code Bridge）

请读取真源：
`{abs_source}`

本文件为薄 bridge，仅做入口指向。长期逻辑维护在真源。
'''


def gen_codex_bridge(name, desc, abs_source):
    return f'''---
name: {name}
description: {desc}
source_of_truth: {abs_source}
bridge_mode: passthrough
---
# {name}（Codex Bridge）

请读取真源：
`{abs_source}`

本文件为薄 bridge，仅做入口指向。长期逻辑维护在真源。
'''


def gen_grok_bridge(name, desc, abs_source):
    desc_clean = desc.rstrip('。.')
    return f'''---
name: {name}
user_invocable: true
description: |
  {desc_clean}。在 Grok TUI 中可通过 /{name} 触发；触发后必须先读取项目真源 SKILL.md。
---
# {name}

## Grok Bridge

- Source of truth: {abs_source}
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/{name}` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
'''


def main():
    deploy = '--deploy' in sys.argv
    if not os.path.isdir(SKILLS_DIR):
        print('错误: 技能真源目录不存在:', SKILLS_DIR)
        sys.exit(1)

    skills = sorted([d for d in os.listdir(SKILLS_DIR)
                     if os.path.isdir(os.path.join(SKILLS_DIR, d))])
    print(f'发现 {len(skills)} 个技能真源')

    gen_map = {
        'claude': gen_claude_bridge,
        'codex': gen_codex_bridge,
        'grok': gen_grok_bridge,
    }

    for host, gen_fn in gen_map.items():
        base = HOST_DIRS[host] if deploy else os.path.join(PREVIEW_DIR, host)
        os.makedirs(base, exist_ok=True)
        for skill in skills:
            skill_dir = os.path.join(SKILLS_DIR, skill)
            name, desc = read_frontmatter(skill_dir)
            abs_source = os.path.join(SKILLS_DIR, skill, 'SKILL.md').replace('\\', '/')
            content = gen_fn(name, desc, abs_source)
            out_dir = os.path.join(base, name)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, 'SKILL.md')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content)
        print(f'[{host}] {"部署" if deploy else "预览"} {len(skills)} 个 bridge → {base}')

    if deploy:
        print('\n已部署到宿主目录。')
    else:
        print('\n预览完成 → ' + PREVIEW_DIR)
        print('检查无误后，运行: python database/gen_agent_bridges.py --deploy 写入宿主目录')


if __name__ == '__main__':
    main()
