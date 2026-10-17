---
name: football-project-onboarding
user_invocable: true
description: |
  阿飞说球足球分析项目总入口。其他Agent接手足球相关任务时，先加载此skill了解项目全貌，再按需调用具体技能。在 Grok TUI 中可通过 /football-project-onboarding 触发；触发后必须先读取项目真源 SKILL.md。
---
# football-project-onboarding

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/football-project-onboarding/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/football-project-onboarding` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
