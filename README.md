# 阿飞说球（v3.1）

头条号「阿飞·赛博聊球」的足球赛事分析与内容创作项目（单平台运营 + 小红书数据卡；微信公众号已于 2026-09-24 停用，历史资料归档于 `📝文章/_归档/公众号(已停用)/`）。

> **开工只跑一条命令**：`python -X utf8 scripts/brief.py`。任何 agent 的入口契约是 `AGENTS.md`，完整工作流速查见 `docs/WORKFLOW-ONE-PAGE.md`，目录分层规范见 `docs/STRUCTURE.md`。

## 目录地图（主 / 次）

| 目录 | 主/次 | 装什么 | 能不能动 |
|:--|:--|:--|:--|
| `AGENTS.md` `CLAUDE.md` `SOURCE_OF_TRUTH.md` | 主 | 规则入口、真源声明 | 改内容可以，**别改名** |
| `docs/` | 主 | `WORKFLOW-ONE-PAGE.md` `WORKFLOW.md` `RULES.md` `SYNC.md` `HANDOFF.md` `STRUCTURE.md` `日记/` | 可加文件 |
| `📚知识库/` | 主 | 长期知识：`skills/`（29 个技能 + `INDEX.md`）`写作指南/` `模型脚本/` `赛后校验/` `比赛分析/` `数据源/` `球队档案/` `系统架构/` `数据分析/` `公司工程/` `索引.md` | 可加文件；**`skills/` 目录名是契约** |
| `📝文章/` | 主 | 产出。`YYYYMMDD/`（近期批次扁平目录）＋ `_归档/`（早期月份与停用渠道归档） | 新批次加日期目录 |
| `scripts/` | 主 | v3.1 主干脚本（`brief` `prematch_intel` `books_500` `market_from_intel` `audit_data` `model_v3` `build_internal_report` `check_report_consistency` `preflight` `reader_lens` `check_dup` `ledger` `journal` `sync`…） | 改代码可以，**核心文件名是契约** |
| `database/` | 主 | 数据：`config/`（模型参数）`archive/` `cache/` `charts/` `legacy/`（旧一次性脚本归档）`predictions/` `feedback/` `tests/` | 可加数据 |
| `state/` | 主 | 机器状态与缓存：根上只留契约文件（`model-state.json` `task-log.json` `xhs_styles.json` `xhs_templates.json` `writing_history.json` `api-keys.json` `odds.sqlite`），其余进 `matches/` `intel/` `model/` `ledger/` `batch/` `cache/` `records/` `tmp/` | 见 `docs/STRUCTURE.md` |
| `公司机_工程/` | 主（独立） | 公司 PC 那套 AFEI 引擎 monorepo，自带 `AGENTS.md` | **别和根目录混用** |
| `_archive/` | 次 | 历史旧文档、旧 docx、图像素材与早期调试脚本归档 | 只读 |

## 每日标准工作流（v3.1）

```bash
python -X utf8 scripts/brief.py                                                 # 0. 开工：状态 + 真待办 + 交接行号
python -X utf8 scripts/prematch_intel.py --date YYYYMMDD --leagues --media      # 1. 盘口 + 积分榜 + 天气 + 外媒
python -X utf8 scripts/books_500.py --date YYYYMMDD --weekday 周N               # 2. 500.com 百家亚盘与欧赔
python -X utf8 scripts/market_from_intel.py --date YYYYMMDD                     # 3. 聚合市场结构
python -X utf8 scripts/audit_data.py --date YYYYMMDD                            # 4. 入模前数据质检
python -X utf8 scripts/model_v3.py --date YYYYMMDD --weekday 周N                # 5. v3.1 模型推演 + 台账登记
python -X utf8 scripts/build_internal_report.py --date YYYYMMDD --weekday 周N   # 6. 生成内部全维度分析报告（A层）
python -X utf8 scripts/check_report_consistency.py "📝文章/YYYYMMDD/YYYYMMDD_周N<k>场_内部分析报告.md"
python -X utf8 scripts/preflight.py "📝文章/YYYYMMDD/<文章>.md"                  # 7. 公开稿门禁（B层：字数+合规+R55视角）
python -X utf8 scripts/check_dup.py YYYYMMDD                                    # 8. 同批多篇去重（必须 0 命中）
python -X utf8 scripts/journal.py && python -X utf8 scripts/sync.py --push      # 9. 收工：日记 + 推双远端
```

## 三铁律（写文章前必查 · R55/R56/R58）

1. **90 分钟口径与内外分层（R41 / R55）**：加时/点球不计；内部报告（A 层）与公开稿（B 层）严格隔离——公开稿以老球迷「阿飞」第一人称行文，严禁出现 `后台模型 / 泊松 / 蒙特卡洛 / 点估计 / 样本量 / 融合权重` 等内部词。
2. **合规与去盘口行话（R41 / R48 / R58）**：禁用词→赔率改定价、盘口改设置/要求、庄家改市场/机构；禁让球行话（`受让 / 平手盘 / 球半 / 上盘 / 下盘`）与押注用语（`押 / 下注 / 重仓 / 稳胆`）；不编造资金流向；无时间锚点。
3. **交付与发布操作（R32 / R56 / R58）**：公开稿只出 `.md`（800–1500 字）；取消 `⚔️战意 / 💰信号` 模板标签，每场必含具体数据 + 明确立场 + `推荐比分`；标题 ≤30 字、前 12 字含队名对位、标点遵守官方白名单；头条后台微调或未通过稿件**严禁删除重发（必在原文点修改防消重）**。
