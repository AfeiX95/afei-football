# 目录结构与归档规则（2026-10-17 定，v1）

> 本文件回答一个问题：**新东西该放哪、旧东西什么时候搬走、哪些路径不许改。**
> 一句话版见根目录 `README.md`；流程见 `docs/WORKFLOW.md`；规则见 `docs/RULES.md`。

## 一、两层分区：主区 / 次区

| | 判据 | 目录 |
|:--|:--|:--|
| **主区** | 每天的管线会读写，或被 `AGENTS.md` 路由表同时指向 | `docs/` `📚知识库/` `📝文章/` `scripts/` `database/` `state/` `公司机_工程/` ＋ 根上 4 份 md ＋ 3 个 `.cmd` |
| **次区** | 只有查历史/翻旧版才进入（只读） | `_archive/` |

判据不是「重不重要」而是**会不会被日常路径碰到**。放错区的典型症状：主区里躺着一堆一次性脚本，或次区里塞了脚本还要 import 的文件。

## 二、state 分层（机器状态，2026-10-17 起）

`state/` 根上**只允许 6 个契约文件**，其它一律进子目录：

```
state/
├── model-state.json      # 机器可读状态（brief/journal 都读它）
├── task-log.json         # 闭环历史（冷数据）
├── xhs_styles.json       # 小红书风格账本（轮换用）
├── xhs_templates.json    # 小红书版式账本
├── api-keys.json         # 本地 API key（gitignored）
├── odds.sqlite           # 本地盘口库（gitignored）
├── matches/<竞彩id>/      # 单场官方缓存：feature/history/injury/odds…（可重取）
├── batch/                # _model_YYYYMMDD_<星期>.txt、_slate.json
├── cache/                # _bonus_<matchId>.json 盘口快照、_form*.json、_results_*.json、_ext_raw/、xhs_auto/
├── records/              # _ext_<日期>.json 外部预测、_move_<日期>.json 盘口位移（**入库**，体量小、要留档）
├── cache/_leagues/       # 维基积分榜与球队页缓存（12h TTL）
├── intel/<日期>/         # 赛前情报单 _intel_<日期>.md / .json（**入库**，R48 写稿前必看）
└── tmp/                  # 临时件，永不入库（出图浏览器目录本机可达 100MB+）
```

- `.gitignore` 按**整个子目录**忽略：`state/matches/` `state/cache/` `state/batch/` `state/tmp/`；`state/records/` 与 `state/intel/` 不忽略
- 脚本里的路径常量：`model.py` 有 `STATE_MATCHES`/`STATE_BATCH`，`sporttery_fetch.py` 有 `OUT_MATCHES`/`OUT_BATCH`/`OUT_CACHE`，`ext_predict.py` 有 `RAW`/`RECORDS`/`BATCH_DIR`，`prematch_intel.py` 有 `INTEL`/`CACHE`/`MATCHES`，`doc_pack.py` 有 `STATE_BATCH`
- **外部源配置**：`database/config/league_sources.json`（竞彩联赛简称 → 维基赛季页检索名 + 英文页名）、`database/config/stadiums.json`（主场城市，**英文名**，供 open-meteo 地理编码）、`database/config/team_aliases.json`（`wiki`=维基中文名，`en_wiki/af/en`=英文页队名）
- 新增一类缓存时：先落 `state/cache/<类别>/`，再在对应脚本加常量，**不要往 state 根上扔**

## 三、📝文章 的规则

- **近 60 天**：`📝文章/YYYYMMDD/`（扁平）。目录名是契约——`preflight.py`、`check_dup.py`、`journal.py`、`xhs_*.py` 都按 `YYYYMMDD` 取数
- **更早的**：按月份进 `📝文章/_归档/YYYY-MM/`
- **公众号旧稿**：`📝文章/_归档/公众号(已停用)/`（账号 2026-09-24 永久封禁，留档不再产出）
- 一天之内的产物都放同一个日期目录：头条稿 `.md`、`_外部预测对照.md`、`小红书_<批次>/`（图 + `cards.json` + `文案.md`）
- 派生件（`发布版/`、`卡片合集.pdf`、`小红书_预览/`）由 `.gitignore` 排除，可用 `卡片发布版.cmd` 重生

## 四、database 的规则

| 子目录 | 装什么 |
|:--|:--|
| `config/` | 契约配置：`model-parameters.json`、`team_aliases.json` 等，**不许挪** |
| `charts/<日期>` | 历史出图（2026-08 之前的 matplotlib 产物） |
| `legacy/` | 2026-07/08 的一次性脚本（`analyze_*` `gen_charts_*` `gen_docx_*` `fetch_preds*` 等），**没有脚本 import 它们**，只为可追溯而留 |
| `predictions/` `feedback/` `short_term/` `archive/` `cache/` `tests/` | 各自的旧数据区 |

判据：**被 `scripts/` import 的进 `config/` 或根，不被 import 的一次性脚本进 `legacy/`。**

## 五、_archive（次区）的分格

| 目录 | 来源 |
|:--|:--|
| `旧docx/` | 2026-09-19 之前根目录散落的 `.docx`（md-only 交付之前的历史产物） |
| `旧文档/` | `_archive_*` 前缀文档、`temp_article.md` |
| `图像素材/` | 原根目录 `assets/`（57 个历史图表） |
| `桥接预览/` | 原根目录 `preview/`（81 个 agent bridge 文件，未部署） |
| `工具脚本/` | 原根目录 `⚙️工具/`（`poisson_dist.py` `gen_html.py` 等一次性工具） |
| `data/` `tmp_20260820_debug/` `文章_旧版/` `pycache_backup/` `杂项/` | 历史遗留 |

**归档三原则**：①只搬不改（保住 mtime，`preflight` 的「最近一篇」才不会指错）②搬之前先 `grep` 一遍引用 ③搬完在 `docs/HANDOFF.md` 当节记一行。

## 六、不许改名的路径（契约清单）

改这些会让脚本或 agent 直接报错，**要改先改代码再改名**：

```
AGENTS.md  CLAUDE.md  SOURCE_OF_TRUTH.md
docs/WORKFLOW.md  docs/RULES.md  docs/HANDOFF.md  docs/日记/
📚知识库/skills/<技能名>/SKILL.md          ← 28 个技能的唯一真源
📚知识库/写作指南/结构轮换台账.md
📚知识库/模型脚本/修正规则.md  check_article.py
📚知识库/公司工程/坑清单.md
📝文章/YYYYMMDD/
scripts/*.py                                ← 文件名即命令
database/config/model-parameters.json  team_aliases.json
state/model-state.json  task-log.json
公司机_工程/                                ← 自成一套，别动
```

## 七、整理记录

| 日期 | 做了什么 |
|:--|:--|
| 2026-10-17 | 建本文件。根目录 7 个旧 docx → `_archive/旧docx/`；删 3 个 0 字节垃圾（`处理时间：2026-09-19` 等误重定向产物）；`assets/`→`_archive/图像素材/`、`preview/`→`_archive/桥接预览/`、`⚙️工具/`→`_archive/工具脚本/`；`state/` 分 `matches/batch/cache/records/tmp`（118 项搬迁，6 个脚本改路径常量，`.gitignore` 改整目录忽略）；`database/charts_*`→`database/charts/`、74 个一次性脚本→`database/legacy/`；`📝文章/` 29 个 8 月及更早目录→`_归档/2026-07`、`2026-08`，3 个公众号旧稿目录→`_归档/公众号(已停用)` |
