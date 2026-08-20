---
name: football-calibration-batch
user_invocable: true
description: |
  足球模型赛后校验批次记录与经验库。每次批量校验后记录结果、发现的偏差模式、新增修正规则。与match-model-pipeline搭配使用。v1.1:Batch#11惨败(2/7=28.6%),累计47/70(67.1%),新增R10(巴甲平率+5pp)。休赛期欧战方差极大+友谊赛不可信+巴甲平率低估三大教训。在 Grok TUI 中可通过 /football-calibration-batch 触发；触发后必须先读取项目真源 SKILL.md。
---
# football-calibration-batch

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/football-calibration-batch/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/football-calibration-batch` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
