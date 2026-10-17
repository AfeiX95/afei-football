---
name: football-14dim-full-analysis
user_invocable: true
description: |
  14维全维度足球赛事分析管线。搜索双方备战动态、赔率、伤停、天气、裁判、外媒预测等情报，按14维结构输出综合预测(比分/胜平负/大小球)。适合世界杯、欧冠、联赛等赛事赛前分析。在 Grok TUI 中可通过 /football-14dim-full-analysis 触发；触发后必须先读取项目真源 SKILL.md。
---
# football-14dim-full-analysis

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/football-14dim-full-analysis/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/football-14dim-full-analysis` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
