# 阿飞说球

头条号「阿飞·赛博聊球」的足球赛事分析与内容创作项目（单平台运营；公众号已于 2026-09-24 停用，历史稿在 `📝文章/_归档/公众号(已停用)/`）。

> **开工只跑一条命令**：`python scripts/brief.py`。任何 agent 的入口契约是 `AGENTS.md`，本文只讲**目录怎么分主次**。详细规则见 `docs/STRUCTURE.md`。

## 目录地图（主 / 次）

**主区**＝每天都要动、脚本强依赖；**次区**＝查历史才翻，不进日常路径。

| 目录 | 主/次 | 装什么 | 能不能动 |
|:--|:--|:--|:--|
| `AGENTS.md` `CLAUDE.md` `SOURCE_OF_TRUTH.md` | 主 | 规则入口、真源声明 | 改内容可以，**别改名** |
| `docs/` | 主 | `WORKFLOW.md`（写文流程）`RULES.md`（规则索引）`SYNC.md`（跨机）`HANDOFF.md`（交接）`STRUCTURE.md`（本目录的详细版）`日记/` | 可加文件 |
| `📚知识库/` | 主 | 长期知识：`skills/`（28 个技能，**路径被所有 agent 引用**）`写作指南/` `模型脚本/` `赛后校验/` `比赛分析/` `数据源/` `球队档案/` `系统架构/` `数据分析/` `公司工程/` `公众号矩阵/` `index.md` | 可加文件；**`skills/` 目录名是契约** |
| `📝文章/` | 主 | 产出。`YYYYMMDD/`（近 60 天，**扁平，脚本按目录名取数**）＋ `_归档/`（更早的按月份组） | 新批次加日期目录 |
| `scripts/` | 主 | 管线脚本（`brief` `model` `sporttery_fetch` `xhs_*` `preflight` `check_dup` `ext_predict` `journal` `sync`…） | 改代码可以，**文件名是契约** |
| `database/` | 主 | 数据：`config/`（模型参数）`archive/` `cache/` `charts/`（历史图表）`legacy/`（旧一次性脚本）`predictions/` `feedback/` `tests/` | 可加数据 |
| `state/` | 主 | 机器状态与缓存：根上只留契约文件（`model-state.json` `task-log.json` `xhs_styles.json` `xhs_templates.json` `api-keys.json` `odds.sqlite`），其余进 `matches/` `batch/` `cache/` `records/` `tmp/` | 见 `docs/STRUCTURE.md` |
| `公司机_工程/` | 主（独立） | 公司 PC 那套 AFEI 引擎 monorepo，自带 `AGENTS.md`，规则自成体系 | **别和根目录混用** |
| `_archive/` | 次 | 归档：`旧docx/` `旧文档/` `图像素材/` `桥接预览/` `工具脚本/` `data/` `杂项/` `tmp_20260820_debug/` | 只读 |
| `卡片发布版.cmd` `小红书出图.cmd` `盘口采集器.cmd` | 主 | 双击启动器（根目录留三个，方便） | 可以新增 |

## 每天的路

```bash
python scripts/brief.py                     # 开工：状态 + 真待办 + 交接指针
python scripts/preflight.py <文章.md>        # 写文收工：字数分档 + 门禁 8 项 + AI 分
python scripts/check_dup.py YYYYMMDD        # 同批多篇去重（必须 0 命中）
python scripts/journal.py                   # 收工：生成当日日记
python scripts/sync.py --push               # 收工：推双远端
```

## 三铁律（写文章前必查）

1. **90 分钟口径**：加时/点球不计；文中模型称「后台模型」，不暴露算法名
2. **合规**：赔率→定价、盘口→设置/门槛、庄家→机构、泊松/MC→后台模型、EV→溢价；无时间锚点
3. **交付**：只出 md、不出 docx/PDF；正文 ~1200 字（R32，`scripts/wordcount.py` 核对）；标题 ≤30 字

## 技术栈

Python 3.11+ / 泊松分布 + 蒙特卡洛（2 万次抽样）/ 竞彩网 webapi 采集 / Chrome 无头渲染出图 / Playwright 仅用于体育预测源。
