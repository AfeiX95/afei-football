# SOURCE_OF_TRUTH — 阿飞说球 真源声明

> 本文件声明项目所有 Agent 配置与技能的真源位置。**所有修改只改真源，bridge 一律从真源生成。**

## 规则层真源

| 层 | 真源路径 | 说明 |
|:---|:---------|:-----|
| 项目总规则（三端共用） | `I:\阿飞说球\AGENTS.md` | 写作铁律/会话记忆/工作流/数据核验清单 |
| Hermes 配置 | `I:\阿飞说球\.hermes.md` | Hermes 专属（L1-L6） |
| Claude Code 兼容层 | `I:\阿飞说球\CLAUDE.md` | 薄桥接，指向 AGENTS.md + skills |
| 写作偏好覆盖层 | `I:\阿飞说球\📚知识库\skills\afei-writing-standards\SKILL.md` | R1-R27 |
| 模型修正规则 | `I:\阿飞说球\📚知识库\模型脚本\修正规则.md` | C01-C27 |
| 模型参数 | `I:\阿飞说球\database\config\model-parameters.json` | v2.9.0 |
| 会话记忆 | `I:\阿飞说球\📚知识库\系统架构\工作记忆.md` | 含会话快照历史 |

## 技能真源

- **唯一真源目录**：`I:\阿飞说球\📚知识库\skills\<技能名>\SKILL.md`（27 个技能）
- **bridge 目录**（由真源生成，勿手改）：
  - Claude Code：`~/.claude/skills/<技能名>/SKILL.md`
  - Codex：`~/.codex/skills/<技能名>/SKILL.md`
  - Grok：`~/.grok/skills/<技能名>/SKILL.md`

## 维护规则

1. 修改规则/技能 → 只改真源（AGENTS.md / 修正规则.md / 📚知识库/skills/）
2. 修改后 → 重新运行 bridge 生成脚本（`database/gen_agent_bridges.py`）同步三端
3. bridge 是薄指针，不维护长逻辑
4. 本项目判断为 **C 类→完整迁移**：规则层（AGENTS.md）+ 真源（skills/）+ 三端 bridge 齐备
