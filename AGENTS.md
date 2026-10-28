# AGENTS.md — 阿飞说球 足球分析项目（路由总入口 · v3.1）

> 任何 agent（Claude Code / Codex / Hermes / DSH）开工先读本文件。
> **本文件只做路由，不堆细节。长内容都拆到 `docs/` + `state/`，真源在 `📚知识库/skills/`。**

## 项目一句话
头条号「阿飞·赛博聊球」——**单平台运营**（附小红书纯数据信息卡；微信侧公众号 2026-09-24 被永久封禁，依据微信运营规范 3.29.2 体育荐彩类主体资质条款，非用词问题；见 `📚知识库/公司工程/平台风控与自查.md`）。竞彩数据仅统计 90 分钟常规时间。

## 开工一步（必读 · 2026-10-07 起）
```bash
python -X utf8 scripts/brief.py
```
一条命令出全部开场信息：时间/模型版本/批次统计、真待办 `open_items`、待校验文章、**最新交接节的行号区间**、写文与收工命令、token 纪律。

- 然后**按需**读：`read docs/HANDOFF.md offset=<简报给的行号> limit=<行数>`（🔴 **禁止全量读 HANDOFF**）
- 需要流程细节看 `docs/WORKFLOW-ONE-PAGE.md`（速查）或 `docs/WORKFLOW.md`（详版）
- **换机器 / 新克隆先拉一次**：`python -X utf8 scripts/sync.py --pull`（跨机同步见下节）

### 🔴 写稿前必跑：盘口采集、质检与 v3.1 模型报告（R48 / R55 · 2026-10-27 起）
```bash
python -X utf8 scripts/prematch_intel.py --date YYYYMMDD --leagues --media  # 1. 竞彩五套盘+维基积分榜+天气+外媒
python -X utf8 scripts/books_500.py YYYYMMDD                                # 2. 500.com 百家亚盘与欧赔
python -X utf8 scripts/market_from_intel.py YYYYMMDD                        # 3. 聚合市场结构
python -X utf8 scripts/audit_data.py YYYYMMDD                               # 4. 入模前数据质检（阻断主客颠倒/跨季污染）
python -X utf8 scripts/model_v3.py YYYYMMDD                                 # 5. 跑 v3.1 模型并自动登记台账
python -X utf8 scripts/build_internal_report.py YYYYMMDD 周N<k>场           # 6. 生成内部全维度报告
python -X utf8 scripts/check_report_consistency.py YYYYMMDD                 # 7. 报告与公开稿一致性硬验收
```
- **写头条文章、做小红书信息卡之前必须先出内部报告并通过自洽检查（0 不一致）**
- 纪律：内部报告（A 层）与公开稿（B 层）严格分离（**R41 / R55 / R56**）；公开稿以老球迷「阿飞」第一人称行文，不露 `后台模型/泊松/MC/样本量/融合权重` 等内部词，不写 `⚔️战意/💰信号` 模板标签，不编造资金流向；缺源项一律省略不写「待补」

### Token 纪律（2026-10-07 定）
1. **开工只跑 `brief.py`**，不要全量读 `docs/HANDOFF.md` 或 `state/model-state.json`
2. **技能按需加载**：先看 `📚知识库/skills/INDEX.md`（含分节行号）定位，再 `read SKILL.md offset=<行> limit=<长度>`；行数 >400 的技能**禁止全量读**
3. **冷数据不读**：`state/task-log.json`（闭环历史）、`docs/HANDOFF-archive/` 只在按日期 grep 时读
4. 写文收工用一键盘：`python -X utf8 scripts/preflight.py <文章.md>`（字数 R32 + 8项合规 + R55视角 + 句长sd提示）；**同批多篇再跑 `python -X utf8 scripts/check_dup.py <日期目录名>`**（逐行去重，必须 0 命中）
5. pwsh 打印中文可能乱码（GBK），**读文件一律用 read 工具**，别信控制台中文

## 跨机同步（2026-10-07 起）
两台机器（家里 / 公司 PC）靠 git 远端对齐：`gitee` = 主力同步，`origin`(GitHub) = 异地备份。
```bash
python -X utf8 scripts/sync.py --pull     # 开工第一件事：拉最新（只用 gitee）
python -X utf8 scripts/sync.py --push     # 收工最后一件事：推所有远端
python -X utf8 scripts/sync.py --status   # 只看状态
```
- 🔴 **机器角色（2026-10-11 用户定）**：**家里这台（`I:\阿飞说球`）= 主机 / 权威版本**；公司 PC（`X:\阿飞说球`，本仓内路径 `公司机_工程/`）= 副机。规则与 `docs/`、`state/` 以家里为准，公司侧改动也要 push 回来对齐
- 🔴 **拉取只用 `gitee` 单一来源**（多镜像互相 rebase 会产生重复提交）；**推送推给所有远端**，一个连不上不拖累另一个
- 工作区不干净时脚本拒绝执行；rebase 冲突一律 `git rebase --abort` 退回，**冲突由人决定**
- 详细说明（含公司 PC 一次性配置、故障表）：`docs/SYNC.md`

## 去哪找什么（路由表）

| 需要 | 路径 |
|------|------|
| 当前进度/待办/会话交接 | `python -X utf8 scripts/brief.py`（首选）→ `docs/HANDOFF.md` 最新一节 + `state/model-state.json` |
| **工作流一页纸（采→验→算→报→写→检→复）** | `docs/WORKFLOW-ONE-PAGE.md`（每步命令 + 产物 + 失败速查） |
| 写作与分析管线详版（v3.1） | `docs/WORKFLOW.md` |
| 修正规则 C01-C51 摘要 | `docs/RULES.md` → 真源 `📚知识库/模型脚本/修正规则.md`（v1.8.2） |
| 写作铁律 R1-R59 覆盖层 | 真源 `📚知识库/skills/afei-writing-standards/SKILL.md`（**R41 = 去盘口语 + 内外分层；R55 = 读者视角去模型内部词；R56 = 去模板标签与自然语气；R58 = 头条官方信用分与禁删重发；R59 = 小红书纯历史数据看板 ≤4场、禁方向/区间/竞彩口径**）|
| **小红书合规规范与风控门禁** | `📚知识库/写作指南/小红书合规规范_20261021.md` + `scripts/xhs_card_d.py` + `scripts/xhs_riskcheck.py` + `📚知识库/公司工程/平台风控与自查.md` |
| **头条官方社区规范与信用分细则** | `📚知识库/写作指南/头条社区规范.md`（2026-10-28 核实：70/20/10/5 四档扣分、首次违规答题秒恢复、消重禁删重发、标题标点白名单）|
| **技能清单/分节行号** | `📚知识库/skills/INDEX.md`（按需加载入口，先看这个再读 SKILL.md）|
| 历史待办/闭环记录（冷） | `state/task-log.json` |
| 旧会话交接（冷） | `docs/HANDOFF-archive/`（按日期 grep）|
| 模型全流程（λ/MC/Edge） | `scripts/model_v3.py` + 技能 `match-model-pipeline` |
| 文章写作工作流 | 技能 `football-match-preview-article` |
| 赛后校验与台账结算 | `scripts/ledger.py` + 技能 `football-calibration-batch` + `📚知识库/赛后校验/` |
| 历史比赛分析 | `📚知识库/比赛分析/{联赛}/` |
| 模型参数全量 | `database/config/model-parameters.json` |
| 图表/文章交付物 | `📝文章/YYYYMMDD/` |
| **目录结构 / 新文件放哪 / 归档规则** | `docs/STRUCTURE.md`（主次分区、state 分层、不许改名的路径清单；一句话版见根 `README.md`） |
| **可用 skills / 插件对本项目的改进评估** | `docs/TOOLBOX.md` |
| 项目真源声明 | `SOURCE_OF_TRUTH.md` |
| 跨机同步 / 换机器 / 推远端 | `python -X utf8 scripts/sync.py` + `docs/SYNC.md` |
| **公司电脑那份工程**（AFEI 引擎 monorepo） | `公司机_工程/`（该子树自带 `AGENTS.md`/`.hermes.md`/`.gitignore`）|
| **公司工程并入的知识**（坑清单 / 硬指标 / 风控） | `📚知识库/公司工程/`（`坑清单.md`、`硬指标与运营实证.md`、`平台风控与自查.md`）|

## 两套工程同仓（2026-10-11 合并 · 勿混用）
本仓库现在装**两套并行工程**，历史与规则各自独立：

| 位置 | 谁的 | 说明 |
|:--|:--|:--|
| 仓库根（`docs/` `state/` `scripts/` `📚知识库/` `📝文章/` …） | **家里这台** | 就是本文件描述的工作流（`brief.py` / `model_v3.py` / `preflight.py` / `HANDOFF` / `state`） |
| `公司机_工程/`（`00_引擎/` `01_数据采集/` `阿飞说球/` `run.ps1` `发布前检查.cmd` …） | **公司 PC** | AFEI 引擎 monorepo；规则看 `公司机_工程/AGENTS.md`，发布前跑 `公司机_工程/发布前检查.cmd` |

- **口径冲突一律以家里为准**：本地 **R1–R59** / **C01–C51**、正文 **800–1500 字（R32）**、标题 **≤30 字（R20）**。
- ⚠️ `公司机_工程/` 只在真要用公司工具链时按需读，**别全量浏览**（725 个文件）。

## 三铁律（写进任何文章前必查 · R55/R56/R58 同步）
1. **90分钟口径与内外分层（R41 / R55）**：加时/点球不计彩果；内部报告（A 层）与公开稿（B 层）严格分离——公开稿以老球迷「阿飞」第一人称行文，**不出现 `后台模型 / 泊松 / 蒙特卡洛 / 点估计 / 置信区间 / 样本量 / 融合权重` 等内部术语**（`scripts/reader_lens.py` 强制拦截）。
2. **合规与去盘口行话（R41 / R48 / R58）**：禁用词→赔率改定价、盘口改设置/要求、庄家改市场/机构；严禁让球行话（`受让 / 平手盘 / 球半 / 上盘 / 下盘 / 走盘 / 打穿`）与押注用语（`押 / 下注 / 重仓 / 稳胆 / 跟单`）；不编造资金流向；无时间锚点（今天/明天/昨天/今晚/本月/北京时间）。
3. **交付与发布操作（R32 / R56 / R57 / R58）**：20:00前完稿；🔴 **公开稿只出 `.md`**；**正文 800–1500 字（R32，`scripts/wordcount.py` 核对）**；标题 ≤30 字、前 12 字含队名对位、标点仅用白名单（`？` `！` `，` `：` `“ ”` `《》` `——` `｜`）；**取消 `⚔️战意 / 💰信号` 模板标签行（R56）**，每场必含具体数据 + 明确立场 + `推荐比分：X 比 Y（首选）／…（次选）／…（防范）`；外媒有源自然引述、无源直接省略；**头条后台微调或未通过稿件一律在原文点「修改」，严禁删除重发（R58 防消重）**。

## 收工约定
- 任务收尾：更新 `docs/HANDOFF.md`（追加一节）+ `state/model-state.json`（如有变化）
- **生成当日日记**：`python -X utf8 scripts/journal.py`（自动汇总当日提交 / 产出 / 状态快照 / 交接指针 → `docs/日记/YYYY-MM-DD.md`）
- 提交 git 兜底：`git add docs/ state/ 📚知识库/ 📝文章/ scripts/ && git commit -m "进度同步 YYYYMMDD"`
- **推送远端（每轮收工必做）**：`python -X utf8 scripts/sync.py --push`（推 `gitee` + `origin`，一个连不上不阻塞另一个）

## 📔 日记 vs 交接 vs 状态（分工，勿混用）
| 文件 | 定位 | 读者 | 写法 |
|:---|:---|:---|:---|
| `docs/HANDOFF.md` | **交接**：当前状态 / 已知阻碍 / 下一步目标 | 下一次会话的 agent | 只追加节，最新在最后 |
| `docs/日记/YYYY-MM-DD.md` | **日记**：当日提交 / 产出清单 / 状态快照 / 手记 | 往后回看的自己 | 脚本生成 AUTO 区块 + 人工手记区（AUTO:END 之后） |
| `state/model-state.json` | **机器可读状态** | 脚本与 agent | 结构化字段，随时覆盖更新 |

## 🔴 记忆原则（2026-09-13 用户明确：只要本地 + 免费）
**不使用任何云端记忆服务；Hindsight（`hindsight_*` 工具）一律不要调用。**
记忆唯一真源（全部本地、零成本、随 git 提交）：
1. `docs/HANDOFF.md` — 会话交接
2. `state/model-state.json` — 机器可读状态
3. `📚知识库/` — 长期知识（`模型脚本/修正规则.md`、`赛后校验/`、`比赛分析/`、`写作指南/`）
4. `docs/WORKFLOW.md` + `docs/RULES.md` — 流程与规则索引

## 技能真源
所有技能在 `📚知识库/skills/<技能名>/SKILL.md`（唯一真源，共 29 个）。**清单与分节行号见 `📚知识库/skills/INDEX.md`**——技能按任务按需加载。

## Agent skills

### Issue tracker
GitHub Issues on `AfeiX95/afei-football`（`origin`；`gitee` 只同步代码，没有 issue tracker）。See `docs/agents/issue-tracker.md`.

### Triage labels
triage 五角色同名字符串，另加 wayfinder 五枚（`wayfinder:map` / `research` / `prototype` / `grilling` / `task`）。See `docs/agents/triage-labels.md`.

### Domain docs
single-context（根目录 `GLOSSARY.md`，架构决定放 `docs/adr/`）。See `docs/agents/domain.md`.

## state 结构（schema v2 · 冷热分离）

> 📁 **目录分层**：`state/` 根上只留契约文件（`model-state.json` `task-log.json` `xhs_styles.json` `xhs_templates.json` `writing_history.json` `api-keys.json` `odds.sqlite`），其余进 `matches/<竞彩id>/`、`intel/<日期>/`、`model/`、`ledger/`、`batch/`、`cache/`、`records/`、`tmp/` —— 详见 `docs/STRUCTURE.md`。

| 键 | 含义 | 热/冷 |
|:---|:---|:---|
| `calibration` | 批次 / 累计场次 / 方向正确数 / 方向率 | 热 |
| `candidate_rules` | 候选+正式规则表 | 热 |
| `open_items` | **真待办**（{type, text}），brief.py 按类型分组打印（保持 ~15 条以内） | 热 |
| `pending_checks` | 待按 90 分钟口径复核的文章与批次 | 热 |
| `counters` | 各列表条数 | 热 |
| `task_log_ref` | → `state/task-log.json`：已闭环任务/已校验文章的历史归档 | 冷 |
