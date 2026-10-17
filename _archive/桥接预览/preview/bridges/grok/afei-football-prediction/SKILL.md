---
name: afei-football-prediction
user_invocable: true
description: |
  足球赛事全维度数据情报预测系统v3.1。7层架构：情报搜索→数据采集→特征工程→数学模型→预测融合→内容生成→反馈学习。输出赛果概率/比分预测/大小球预测。验证运营阶段。在 Grok TUI 中可通过 /afei-football-prediction 触发；触发后必须先读取项目真源 SKILL.md。
---
# afei-football-prediction

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/afei-football-prediction/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/afei-football-prediction` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
