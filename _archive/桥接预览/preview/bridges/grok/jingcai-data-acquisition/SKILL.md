---
name: jingcai-data-acquisition
user_invocable: true
description: |
  竞彩网数据获取的完整方法论——API用法、局限性、备选方案、百家欧赔获取、赔率时间序列分析。覆盖API仅返回当前日比赛的陷阱、特征分析页数据提取、API不可用时的赔率估算方法。v1.1新增：新球体育百家欧赔数据提取、赔率时间序列资金流向分析。与match-model-pipeline搭配使用，在Step 2A前后调用。在 Grok TUI 中可通过 /jingcai-data-acquisition 触发；触发后必须先读取项目真源 SKILL.md。
---
# jingcai-data-acquisition

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/jingcai-data-acquisition/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/jingcai-data-acquisition` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
