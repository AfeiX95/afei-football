---
name: football-publishing-calendar
user_invocable: true
description: |
  阿飞说球每日发文日历管理 — 何时发、发什么、发多少。覆盖16:30凌晨场前瞻、20:30赛后复盘/明日预热两个窗口的决策框架，含日发文量限制、时间窗口敏感度、内容类型选型规则。在 Grok TUI 中可通过 /football-publishing-calendar 触发；触发后必须先读取项目真源 SKILL.md。
---
# football-publishing-calendar

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/football-publishing-calendar/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/football-publishing-calendar` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
