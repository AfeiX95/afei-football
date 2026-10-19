# Domain Docs

工程类技能（`improve-codebase-architecture` / `diagnose` / `tdd` / `domain-modeling` / `grill-with-docs`）
在读这个仓之前应该怎么用它的领域文档。

## 布局：single-context

**本仓是 single-context**（2026-10-20 与用户确认）：一个仓库共用一份根目录的 `GLOSSARY.md`，
架构决定统一放 `docs/adr/`。没有 `GLOSSARY-MAP.md`，也没有各子项目的 `GLOSSARY.md` ——
`公司机_工程/` 虽然自带 `AGENTS.md`，但仍共用根这份 glossary 与 ADR，不单独分层。

## Before exploring, read these

- **`GLOSSARY.md`** at the repo root（现在还**不存在**，第一次真正写下词条时才建）
- **`docs/adr/`** —— 读与你正要改动的区域相关的 ADR
- 若将来出现 `GLOSSARY-MAP.md`（多语境仓），说明布局变了，以它为准；当前没有

这几个文件不存在时**静静往下走**：不要提示「缺文件」，也不要主动提议先建。
生产方技能（`/grill-with-docs`）会在术语或决定真的定下来时才懒创建。

## 文件结构（当前）

```
/
├── GLOSSARY.md            ← 尚未创建，第一次落词条时建
├── docs/
│   ├── adr/               ← 架构决定（0001-xxx.md 起编号）
│   └── agents/            ← 本目录：issue-tracker / triage-labels / domain
├── 📚知识库/skills/        ← 技能真源（29 个）
└── 公司机_工程/            ← 公司 PC 的 AFEI 引擎 monorepo（同一 glossary，不分层）
```

## 本仓的真源优先级（给工程技能看的，别读错文件）

规则看 `📚知识库/skills/afei-writing-standards/SKILL.md`（R1-R49），流程看 `docs/WORKFLOW.md`（v2.9）；
`📚知识库/skills/football-match-preview-pipeline/SKILL.md` v3.0 的 Step 7 朱雀、Step 8 白底图+docx 已过期，
只剩定位、依赖顺序、Step 1-5 骨架与常见错误仍有效。`CLAUDE.md` 只是薄桥接层，真源是 `AGENTS.md`。

## Use the glossary's vocabulary

输出里点到领域概念（issue 标题、重构提案、假设、测试名）时，用 `GLOSSARY.md` 里定义的那个词，
不要漂移到它明确回避的同义词。本仓已有的固定说法举例：**后台模型**（不叫算法名）、**定价**（不叫赔率）、
**设置/门槛**（不叫盘口）、**机构**（不叫庄家）、**溢价**（不叫 EV）。

概念还没进 glossary 时，那是一个信号：要么你在发明这个项目不用的词（先回头想），
要么是真的缺词条（记下来交给 `/grill-with-docs`）。

## Flag ADR conflicts

输出与既有 ADR 冲突时，明写出来，别默默覆盖：

> _与 ADR-0003（X）冲突 —— 但值得重新讨论，因为……_
