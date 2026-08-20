---
name: season-transition-analysis
user_invocable: true
description: |
  分析双方处于不同赛季状态（休赛期vs赛季中/双方休赛但备战深度不同/赛季初vs赛季末）时的λ修正策略。涵盖欧冠资格赛7月数据分析、休赛期双队备战深度比较、同国教练带队倒戈、零H2H+零积分榜同时缺失时的替代数据流程。在 Grok TUI 中可通过 /season-transition-analysis 触发；触发后必须先读取项目真源 SKILL.md。
---
# season-transition-analysis

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/season-transition-analysis/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/season-transition-analysis` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
