# AGENTS.md — 阿飞说球 足球分析项目（路由总入口）

> 任何 agent（Claude Code / Codex / Hermes / DSH）开工先读本文件。
> **本文件只做路由，不堆细节。长内容都拆到 `docs/` + `state/`，真源在 `📚知识库/skills/`。**

## 项目一句话
头条号「阿飞·赛博聊球」+ 公众号「AfeiX聊球」足球赛事分析与内容创作。竞彩数据仅统计 90 分钟常规时间。

## 开工一步（必读 · 2026-10-07 起）
```bash
python scripts/brief.py
```
一条命令出全部开场信息：时间/模型版本/批次统计、真待办 `open_items`、待校验文章、**最新交接节的行号区间**、写文与收工命令、token 纪律。

- 然后**按需**读：`read docs/HANDOFF.md offset=<简报给的行号> limit=<行数>`（🔴 **禁止全量读 HANDOFF**）
- 需要流程细节再看 `docs/WORKFLOW.md`
- 旧「开工三步」（全量读 HANDOFF + state + 四个重技能 ≈100K tokens/会话）**已废除**

### Token 纪律（2026-10-07 定）
1. **开工只跑 `brief.py`**，不要全量读 `docs/HANDOFF.md`（562 行 ≈16K tokens）或 `state/model-state.json`
2. **技能按需加载**：先看 `📚知识库/skills/INDEX.md`（含分节行号）定位，再 `read SKILL.md offset=<行> limit=<长度>`；行数 >400 的技能**禁止全量读**（`match-model-pipeline` 1243 行 ≈17K tokens）
3. **冷数据不读**：`state/task-log.json`（闭环历史）、`docs/HANDOFF-archive/` 只在按日期 grep 时读
4. 写文收工用一键盘：`python scripts/preflight.py <文章.md>`（字数 R32 + 发布门禁）
5. pwsh 打印中文可能乱码（GBK），**读文件一律用 read 工具**，别信控制台中文

## 去哪找什么（路由表）

| 需要 | 路径 |
|------|------|
| 当前进度/待办/会话交接 | `python scripts/brief.py`（首选）→ `docs/HANDOFF.md` 最新一节 + `state/model-state.json` |
| 写作管线（10步） | `docs/WORKFLOW.md` |
| 修正规则 C01-C42 摘要 | `docs/RULES.md` → 真源 `📚知识库/模型脚本/修正规则.md` |
| 写作铁律 R1-R37 覆盖层 | 真源 `📚知识库/skills/afei-writing-standards/SKILL.md` |
| **技能清单/分节行号** | `📚知识库/skills/INDEX.md`（按需加载入口，先看这个再读 SKILL.md）|
| 历史待办/闭环记录（冷） | `state/task-log.json` |
| 旧会话交接（冷） | `docs/HANDOFF-archive/`（按日期 grep）|
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
3. **交付**：20:00前完稿；🔴 **只出 md（2026-09-19 起：不生成 docx、不出 PDF）**；**正文 ~1200 字（R32，`scripts/wordcount.py` 核对）**；排版按 R33（一屏一视觉块）；标题≤30字；每场必含⚔️战意+💰信号+推荐比分（首选-次选-防范）；🌍外媒**有源必写、无源直接省略**（2026-10-06 定：搜不到就不要，禁止写"待补/查不到/不编造"这类占位说明）

## 收工约定
- 任务收尾：更新 `docs/HANDOFF.md`（追加一节）+ `state/model-state.json`（如有变化）
- **生成当日日记**：`python scripts/journal.py`（自动汇总当日提交 / 产出 / 状态快照 / 交接指针 → `docs/日记/YYYY-MM-DD.md`；补写历史日加 `--date YYYY-MM-DD`；幂等，手记区永不覆盖）
  - ⛔ **不挂计划任务、不做自动触发**（用户 2026-09-19 决定）——由 agent 在任务收尾时手动跑一次即可，勿再提议自动化
- 提交 git 兜底：`git add docs/ state/ 📚知识库/ 📝文章/ && git commit -m "进度同步 YYYYMMDD"`
- 多会话并发：先读后写，发现文件比上次新（别人刚写）先重读合并，严禁整文件覆盖

## 📔 日记 vs 交接 vs 状态（分工，勿混用）
| 文件 | 定位 | 读者 | 写法 |
|:---|:---|:---|:---|
| `docs/HANDOFF.md` | **交接**：当前状态 / 已知阻碍 / 下一步目标 | 下一次会话的 agent | 只追加节，最新在最后 |
| `docs/日记/YYYY-MM-DD.md` | **日记**：当日提交 / 产出清单 / 状态快照 / 手记 | 往后回看的自己 | 脚本生成 AUTO 区块 + 人工手记区（AUTO:END 之后） |
| `state/model-state.json` | **机器可读状态** | 脚本与 agent | 结构化字段，随时覆盖更新 |

## 🔴 记忆原则（2026-09-13 用户明确：只要本地 + 免费）
**不使用任何云端记忆服务；Hindsight（`hindsight_*` 工具）一律不要调用**（其 API 需 apiToken，实测返回 401，且须上传数据到云端）。

记忆唯一真源（全部本地、零成本、随 git 提交）：
1. `docs/HANDOFF.md` — 会话交接（当前状态 / 已知阻碍 / 下一步）
2. `state/model-state.json` — 机器可读状态（批次 / 累计 / 候选规则 / 待办）
3. `📚知识库/` — 长期知识（`模型脚本/修正规则.md`、`赛后校验/`、`比赛分析/`、`写作指南/`）
4. `docs/WORKFLOW.md` + `docs/RULES.md` — 流程与规则索引

会话中学到的经验：**直接写进上述本地文件**（尤其 `修正规则.md`、`WORKFLOW.md`、`afei-writing-standards/SKILL.md`），不依赖任何外部记忆服务。

## 技能真源
所有技能在 `📚知识库/skills/<技能名>/SKILL.md`（唯一真源，共 28 个）。**清单与分节行号见 `📚知识库/skills/INDEX.md`**——技能按任务按需加载，不再无脑按固定顺序全量读。
常用路径：写文 = `afei-writing-standards` → `football-match-preview-article` → `humanizer-zh`；跑模型 = `match-model-pipeline`；赛后校验 = `football-calibration-batch`。

## state 结构（schema v2 · 2026-10-07 冷热分离）
| 键 | 含义 | 热/冷 |
|:---|:---|:---|
| `calibration` | 批次 / 累计场次 / 方向正确数 / 方向率 | 热 |
| `candidate_rules` | 候选+正式规则表 | 热 |
| `open_items` | **真待办**（{type, text}），brief.py 按类型分组打印 | 热 |
| `pending_checks` | 待按 90 分钟口径复核的文章 | 热 |
| `counters` | 各列表条数 | 热 |
| `task_log_ref` | → `state/task-log.json`：已闭环任务/已校验文章的历史归档 | 冷 |

> 🔴 改写规则：**已完成/已闭环的条目搬进 `state/task-log.json`，`open_items` 只留真正待办**（保持 ~15 条以内）。
> 追加待办时同时更新 `counters`。`scripts/journal.py` 读 `open_items`（兼容旧 `active_tasks`）。
