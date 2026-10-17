# CLAUDE.md — 阿飞说球 项目配置（Claude Code 兼容层）

> 本项目为「阿飞-赛博聊球」足球赛事分析与内容创作项目。
> **Claude Code 兼容层：平台无关规则以 `AGENTS.md` 为准，本文件仅做薄层桥接。**

## 加载规则

- **项目总规则** → 读取 `I:\阿飞说球\AGENTS.md`（写作铁律/会话记忆/工作流/数据核验清单，三端共用，修改只改它）
- **技能真源** → `I:\阿飞说球\📚知识库\skills\<技能名>\SKILL.md`（27 个技能，真源唯一，修改只改它）
- **写作偏好覆盖层** → `I:\阿飞说球\📚知识库\skills\afei-writing-standards\SKILL.md`（R1-R27 规则）
- **模型修正规则** → `I:\阿飞说球\📚知识库\模型脚本\修正规则.md`（C01-C27）
- **会话交接快照** → `I:\阿飞说球\📚知识库\系统架构\工作记忆.md` 文末「会话快照历史」最新一条

## 技能入口（27个，按优先级）

| 技能 | 用途 | 真源 |
|:-----|:-----|:-----|
| match-model-pipeline | 后台模型全流程 | 📚知识库/skills/match-model-pipeline/SKILL.md |
| football-match-preview-pipeline | 赛事前瞻全流程管线 v3.0 | 📚知识库/skills/football-match-preview-pipeline/SKILL.md |
| afei-writing-standards | 写作偏好覆盖层 R1-R27 | 📚知识库/skills/afei-writing-standards/SKILL.md |
| football-match-preview-article | 文章写作完整工作流 | 📚知识库/skills/football-match-preview-article/SKILL.md |
| humanizer-zh | 降AI写作（中文） | 📚知识库/skills/humanizer-zh/SKILL.md |
| football-calibration-batch | 赛后校验经验库 | 📚知识库/skills/football-calibration-batch/SKILL.md |

（其余 21 个技能同样位于 `📚知识库/skills/`，命名即路径）

## 标准调用顺序

```
match-model-pipeline → 产出模型数据
→ football-match-preview-pipeline → 写文章（10步流程）
→ afei-writing-standards → 应用 R1-R27 偏好
→ humanizer-zh → 降AI
→ 合规体检（禁用词/锚点/降权词脚本）
→ docx 生成（R19 白底图）→ 归档 git
```

## 关键约束（详见 AGENTS.md）

- 竞彩数据只统计90分钟常规时间赛果
- 标题≤30字；禁用词：赔率→定价、盘口→设置/门槛、庄家→机构、泊松/MC→后台模型、EV→溢价
- 写作铁律：无时间锚点、结论前置、每场必含战意+信号+外媒+推荐比分
- 会话开场先读工作记忆「会话交接快照」；任务收尾同步工作记忆 + git 提交

## 本文件性质

本文件为 **Claude Code 薄兼容层**：只做入口指向，长期逻辑维护在 `AGENTS.md` 和 `📚知识库/skills/` 真源。修改规则请改真源，勿改本文件。
