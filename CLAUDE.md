# CLAUDE.md — 阿飞说球 项目配置（Claude Code 兼容层 · v3.1）

> 本项目为头条号「阿飞·赛博聊球」足球赛事分析与内容创作项目（单平台运营 + 小红书数据卡）。
> **Claude Code 兼容层：平台无关规则以 `AGENTS.md` 为准，本文件仅做薄层桥接。**

## 开工第一步

```bash
python -X utf8 scripts/brief.py
```
- **项目总规则** → 读取 `I:\阿飞说球\AGENTS.md`（写作铁律/会话记忆/工作流/数据核验清单，三端共用）
- **一页纸工作流** → `docs/WORKFLOW-ONE-PAGE.md`；**详版管线** → `docs/WORKFLOW.md`
- **技能索引** → `📚知识库/skills/INDEX.md`（共 29 个技能，按行号区间按需读取，禁止全量读 >400 行技能）
- **写作偏好覆盖层** → `📚知识库/skills/afei-writing-standards/SKILL.md`（**R1–R59**）
- **头条官方合规规范** → `📚知识库/写作指南/头条社区规范.md`（2026-10-28 官方 8 份规则核实）
- **小红书合规规范与门禁（R59）** → `📚知识库/写作指南/小红书合规规范_20261021.md` + `scripts/xhs_card_d.py`（≤4场纯历史数据海报）+ `scripts/xhs_riskcheck.py`
- **模型修正规则** → `📚知识库/模型脚本/修正规则.md`（**C01–C48 v1.8.1**）
- **会话交接** → `docs/HANDOFF.md` 最新一节（按 `brief.py` 给出的行号读取）
- **机器可读进度/待办** → `state/model-state.json`

## 标准生产管线（v3.1）

```bash
# 1. 采集与质检
python -X utf8 scripts/prematch_intel.py --date YYYYMMDD --leagues --media
python -X utf8 scripts/books_500.py --date YYYYMMDD --weekday 周N
python -X utf8 scripts/market_from_intel.py --date YYYYMMDD
python -X utf8 scripts/audit_data.py --date YYYYMMDD

# 2. 模型与内部报告（A 层）
python -X utf8 scripts/model_v3.py --date YYYYMMDD --weekday 周N
python -X utf8 scripts/build_internal_report.py --date YYYYMMDD --weekday 周N
python -X utf8 scripts/check_report_consistency.py "📝文章/YYYYMMDD/YYYYMMDD_周N<k>场_内部分析报告.md"

# 3. 头条公开稿门禁与去重（B 层：只出 .md）
python -X utf8 scripts/preflight.py "📝文章/YYYYMMDD/<文章>.md"
python -X utf8 scripts/check_dup.py YYYYMMDD

# 4. 小红书纯历史数据海报（≤4场）与文案形态风控门禁（R59）
python -X utf8 scripts/xhs_card_d.py --input "📝文章/YYYYMMDD/_cards_<批次>.json" --out "📝文章/YYYYMMDD/小红书_<批次>" --only-cover --cover-style poster
python -X utf8 scripts/xhs_riskcheck.py "📝文章/YYYYMMDD/_cards_<批次>.json" --text "📝文章/YYYYMMDD/小红书_<批次>/文案.md"
```

## 关键约束（详见 `AGENTS.md`）

- 竞彩数据只统计 90 分钟常规时间赛果
- 公开稿只出 `.md`（800–1500 字），内部报告（A 层）与公开稿（B 层）严格分离（R41 / R55 / R56）
- 公开稿以「阿飞」第一人称行文，禁露 `后台模型 / 泊松 / 蒙特卡洛 / 样本量 / 融合权重` 等内部术语，禁写 `⚔️/💰` 标签行，每场必含具体数据 + 明确立场 + `推荐比分`
- 头条后台微调或未通过稿件一律在原文点「修改」，严禁删除重发（R58 防消重）
