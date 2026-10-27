# SOURCE_OF_TRUTH — 阿飞说球 真源声明（v3.1）

> 本文件声明项目所有 Agent 配置、工作流与规则的唯一真源位置。**所有修改只改真源。**

## 规则与状态层真源

| 层 | 真源路径 | 当前版本 / 说明 |
|:---|:---------|:-----|
| 项目总路由（多端共用） | `I:\阿飞说球\AGENTS.md` | 路由总入口、三铁律、Token 纪律 |
| 工作流一页纸 / 详版 | `I:\阿飞说球\docs\WORKFLOW-ONE-PAGE.md` / `docs\WORKFLOW.md` | v3.1（采→验→算→报→写→检→复） |
| 规则薄索引 | `I:\阿飞说球\docs\RULES.md` | C01–C48 & R1–R58 速查 |
| 写作偏好与合规铁律真源 | `I:\阿飞说球\📚知识库\skills\afei-writing-standards\SKILL.md` | **R1–R58** |
| 头条官方平台规范真源 | `I:\阿飞说球\📚知识库\写作指南\头条社区规范.md` | **2026-10-28 官方 8 份规则核实版** |
| 模型修正规则真源 | `I:\阿飞说球\📚知识库\模型脚本\修正规则.md` | **C01–C48（v1.8.1）** |
| 生产模型引擎 | `I:\阿飞说球\scripts\model_v3.py` + `database\config\model-parameters.json` | **v3.1.0** |
| 会话热交接 | `I:\阿飞说球\docs\HANDOFF.md` | 仅保留近期交接，历史归档于 `docs/HANDOFF-archive/` |
| 机器可读热状态 / 冷归档 | `I:\阿飞说球\state\model-state.json` / `state\task-log.json` | schema v2 冷热分离 |
| Claude / Hermes 兼容层 | `I:\阿飞说球\CLAUDE.md` / `.hermes.md` | 薄桥接，指向 `AGENTS.md` |

## 技能真源

- **唯一真源目录**：`I:\阿飞说球\📚知识库\skills\<技能名>\SKILL.md`（共 29 个技能）
- **分节行号索引**：`I:\阿飞说球\📚知识库\skills\INDEX.md`（由 `python -X utf8 scripts/skill_index.py --write` 自动生成）
