---
name: football-match-preview-pipeline
user_invocable: true
description: |
  阿飞说球赛事前瞻全流程管线 v3.0——从竞彩网数据到发布就绪 docx 的完整生产链。整合：14维分析+模型推演（match-model-pipeline）、R1-R27 写作偏好（afei-writing-standards）、叙事池选型落盘（R11）、素材库（R25）、合规体检、朱雀降AI（humanizer-zh）、白底图 docx 生成（R1。在 Grok TUI 中可通过 /football-match-preview-pipeline 触发；触发后必须先读取项目真源 SKILL.md。
---
# football-match-preview-pipeline

## Grok Bridge

- Source of truth: I:/阿飞说球/📚知识库/skills/football-match-preview-pipeline/SKILL.md
- Read the source-of-truth file before executing this skill.
- Follow the source file's workflow, constraints, examples, and output format.
- Treat this file as a thin Grok bridge only; do not maintain long-form logic here.

## 使用说明

1. 在 Grok TUI 中输入 `/football-match-preview-pipeline` 即可触发。
2. Grok 会优先使用本 bridge 指向的真源。
3. 如需更新，直接修改真源。
