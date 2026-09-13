# AGENTS.md — 阿飞说球 足球分析项目（路由总入口）

> 任何 agent（Claude Code / Codex / Hermes / DSH）开工先读本文件。
> **本文件只做路由，不堆细节。长内容都拆到 `docs/` + `state/`，真源在 `📚知识库/skills/`。**

## 项目一句话
头条号「阿飞·赛博聊球」+ 公众号「AfeiX聊球」足球赛事分析与内容创作。竞彩数据仅统计 90 分钟常规时间。

## 开工三步（必读）
1. **读交接**：`docs/HANDOFF.md` 最新一节（当前进度/阻碍/下一步）
2. **读状态**：`state/model-state.json`（模型版本/批次/候选规则/待办，机器可读）
3. **跑流程**：`docs/WORKFLOW.md`（10步写作管线速查）

## 去哪找什么（路由表）

| 需要 | 路径 |
|------|------|
| 当前进度/待办/会话交接 | `docs/HANDOFF.md`（最新一节）+ `state/model-state.json` |
| 写作管线（10步） | `docs/WORKFLOW.md` |
| 修正规则 C01-C33 摘要 | `docs/RULES.md` → 真源 `📚知识库/模型脚本/修正规则.md` |
| 写作铁律 R1-R28 覆盖层 | 真源 `📚知识库/skills/afei-writing-standards/SKILL.md` |
| 模型全流程（λ/MC/Edge） | 技能 `match-model-pipeline` |
| 文章写作工作流 | 技能 `football-match-preview-article` |
| 赛后校验经验库 | 技能 `football-calibration-batch` + `📚知识库/赛后校验/` |
| 历史比赛分析 | `📚知识库/比赛分析/{联赛}/` |
| 模型参数全量 | `database/config/model-parameters.json` |
| 图表/文章交付物 | `📝文章/YYYYMMDD/` |
| 项目真源声明 | `SOURCE_OF_TRUTH.md` |

## 三铁律（写进任何文章前必查）
1. **90分钟口径**：加时/点球不计彩果；文中模型称「后台模型」，不暴露算法名
2. **合规**：禁用词→赔率改定价、盘口改设置/门槛、庄家改机构、泊松/MC改后台模型、EV改溢价；无时间锚点（今天/明天/昨天/今晚/北京时间）
3. **交付**：20:00前完稿；docx白底图（R19）；标题≤30字；每场必含⚔️战意+💰信号+🌍外媒+推荐比分（首选-次选-防范）

## 收工约定
- 任务收尾：更新 `docs/HANDOFF.md`（追加一节）+ `state/model-state.json`（如有变化）
- 提交 git 兜底：`git add docs/ state/ 📚知识库/ 📝文章/ && git commit -m "进度同步 YYYYMMDD"`
- 多会话并发：先读后写，发现文件比上次新（别人刚写）先重读合并，严禁整文件覆盖

## 🔴 记忆原则（2026-09-13 用户明确：只要本地 + 免费）
**不使用任何云端记忆服务；Hindsight（`hindsight_*` 工具）一律不要调用**（其 API 需 apiToken，实测返回 401，且须上传数据到云端）。

记忆唯一真源（全部本地、零成本、随 git 提交）：
1. `docs/HANDOFF.md` — 会话交接（当前状态 / 已知阻碍 / 下一步）
2. `state/model-state.json` — 机器可读状态（批次 / 累计 / 候选规则 / 待办）
3. `📚知识库/` — 长期知识（`模型脚本/修正规则.md`、`赛后校验/`、`比赛分析/`、`写作指南/`）
4. `docs/WORKFLOW.md` + `docs/RULES.md` — 流程与规则索引

会话中学到的经验：**直接写进上述本地文件**（尤其 `修正规则.md`、`WORKFLOW.md`、`afei-writing-standards/SKILL.md`），不依赖任何外部记忆服务。

## 技能真源
所有技能在 `📚知识库/skills/<技能名>/SKILL.md`（唯一真源）。27 个技能，按 `match-model-pipeline → football-match-preview-pipeline → afei-writing-standards → humanizer-zh` 顺序调用。
