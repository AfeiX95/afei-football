---
name: match-model-pipeline
user_invocable: true
description: |
  在撰写赛事前瞻文章前，先运行全维度后台模型。包含官方数据优先原则、H2H数据读取陷阱、国内联赛专项分析、竞彩90分钟口径铁律、双方法lambda估算、伤停/天气/更衣室/主客场/H2Hλ修正、比分EV计算、10万次MC模拟、品牌溢价、置信度三重检查、外媒对比、赛后校验。v2.6:H2H历史λ量化修正(法国vs西班牙案例Edge+8pp→归零)。v2.7。在 Grok TUI 中可通过 /match-model-pipeline 触发；触发后必须先读取项目真源 SKILL.md。
---
# match-model-pipeline

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/match-model-pipeline/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/match-model-pipeline` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
