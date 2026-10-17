---
name: football-match-preview-article
user_invocable: true
description: |
  写足球赛事前瞻文章的完整工作流（阿飞说球风格）。v2.2新增：数据来源标注行、伤病语言缓冲措辞、违规词"赔率"在标题中也可能被判定违规。v2.1新增：雷速SWOT吸收流程、二合一两场格式、⚡开场风暴独立章节。v2.0新增：三模板轮换(A悬疑反转/ B硬核对决/ C复盘叙事)、标题公式修正、双互动钩子强制植入、发布时段锁定、合集优先策略。在 Grok TUI 中可通过 /football-match-preview-article 触发；触发后必须先读取项目真源 SKILL.md。
---
# football-match-preview-article

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/football-match-preview-article/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/football-match-preview-article` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
