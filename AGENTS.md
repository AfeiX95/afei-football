# AGENTS.md - 阿飞说球 足球分析项目

## 项目概述
头条号「阿飞·赛博聊球」+ 公众号「AfeiX聊球」的足球赛事分析与内容创作项目。

## 目录结构
- `YYYYMMDD/` — 每日赛事前瞻文章（.md 头条版 + .docx 公众版）
- `📚知识库/` — 核心知识库
  - `写作指南/` — 风格规范、排版铁律、叙事池
  - `比赛分析/` — 历史分析
  - `赛后校验/` — 模型校验记录
  - `球队档案/` — 球队资料
  - `数据源/` — 数据获取方法
  - `模型脚本/` — 分析模型
  - `系统架构/` — 项目架构文档
  - `索引.md` — 知识库总索引
- `database/` — Python 数据分析脚本（feature_extractor, fusion_engine, poisson 等）
- `⚙️工具/` — 辅助脚本（修复、部署检查等）
- `sporttery_results.json` — 竞彩赛果数据

## 写作铁律
1. 标题 ≤30字，数字+反差+悬念，禁堆砌队名
2. **禁用词汇**：赔率、盘口、庄家、泊松、蒙特卡洛、EV、凯利 → 统一用"后台模型"、"定价"、"溢价"
3. 无时间锚点（今天/明天/昨天）
4. 数据来源标注仅1处
5. 结尾硬立场+留可辩驳漏洞，禁用温和提问
6. "难说。真说不好。"全文仅1处
7. 每场必含 ⚔️战意 + 💰信号 + 🌍外媒 + 推荐比分（首选-次选-防范）
8. 降AI五要素：脏话/跑题比喻/不完整句/视角滑动/反问

## 文章结构
- SCA 开篇（故事/数据锚/反差 3选1）
- 14维全维度分析（百家欧赔→赔率趋势→基础数据→...→综合预测）
- 结尾 3选1：硬立场/留白/数据式
- 互动钩子（数据型/争议型/投票型）+ 首发评论

## 数据源优先级
1. 竞彩网 (sporttery.cn) — 官方赔率最权威
2. 懂球帝 (dongqiudi.com) — 阵容/身价/射手/教练
3. 新球体育 (titan007.com) — 特征分析/百家欧赔
4. 外媒 8-10家对比

## 技术栈
- Python 3.11+（数据处理、Poisson 模型、蒙特卡洛模拟）
- 竞彩网 API 数据采集
- Markdown → DOCX 转换
- 头条号 HTML 深色主题 + 公众号 MD 版（135/秀米模板）

## 注意事项
- 竞彩数据只统计90分钟常规时间赛果，加时+点球不计入彩果
- 文章末尾不出现"数据采集：用户手动提取自中国体育彩票官方平台"
- 模型数据在文中称"后台模型"，不暴露具体算法名

## Skills 知识库（16个足球技能 + 2个写作技能）

所有 Hermes 积累的技能文件存放在 `📚知识库/skills/` 目录下，每个文件夹含 `SKILL.md` 主文件和 `references/`、`scripts/`、`templates/` 子目录。

### 核心技能（按优先级）

| 技能 | 用途 | 何时读取 |
|------|------|---------|
| `match-model-pipeline` | 后台模型全流程（λ/MC/EV/修正规则） | 跑任何模型前 |
| `afei-writing-standards` | 写作偏好覆盖层（R1-R18规则） | 写文章前 |
| `football-match-preview-article` | 文章写作完整工作流 | 写文章前 |
| `football-match-preview-pipeline` | 赛事前瞻全流程管线 | 单场/多场合集 |
| `jingcai-data-acquisition` | 竞彩网数据获取方法 | 采集赔率数据时 |
| `football-lottery-assistant` | 深度分析（七层漏斗+十二维） | 用户要求深度分析时 |
| `football-calibration-batch` | 赛后校验经验库 | 赛后复盘时 |
| `football-14dim-full-analysis` | 11维全维度分析管线 | 用户要求14维分析时 |
| `football-publishing-calendar` | 发文日历管理 | 决定何时发什么时 |
| `afei-model-framework-v3` | 模型升级路线图 | 改进模型时 |
| `season-transition-analysis` | 休赛期vs赛季中修正 | 分析欧战资格赛时 |
| `humanizer-zh` | 降AI写作（中文） | 降AI检测时 |

### 使用方式

读取某个技能的完整内容：
```
read_file("📚知识库/skills/match-model-pipeline/SKILL.md")
```

读取技能的参考文件：
```
read_file("📚知识库/skills/match-model-pipeline/references/post-match-calibration.md")
```

读取技能的脚本：
```
read_file("📚知识库/skills/match-model-pipeline/scripts/mc-simulation.py")
```
