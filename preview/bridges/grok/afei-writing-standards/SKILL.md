---
name: afei-writing-standards
user_invocable: true
description: |
  阿飞说球写作偏好覆盖层 — 不断累积的用户格式/风格/维度修正。加载在football-match-preview-article之上，覆盖其默认行为。每次用户指出写作问题时在此记录修正，确保后续会话直接使用正确格式。在 Grok TUI 中可通过 /afei-writing-standards 触发；触发后必须先读取项目真源 SKILL.md。
---
# afei-writing-standards

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/afei-writing-standards/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/afei-writing-standards` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
