# TOOLBOX — 可用 skills / 插件对本项目的改进评估

> 2026-10-18 建。只做**候选评估**，不动配置。采纳与否由人决定，采纳后把结论并进 `docs/WORKFLOW.md` 或对应技能真源。
> 判断标准：能不能解**本项目已记录的痛点**（不是「看起来能用」）。痛点来源 = `state/model-state.json` 的 `open_items` + 五十五/五十六节 HANDOFF。

- **澳客指数（必发盈亏/胜负指数/盘口评测/凯利方差/差异分析/伤停/排序）** —— 2026-10-20 起可用：`scripts/okooo_intel.py`（urllib，需 Referer、gb2312）+ `scripts/intel_fetch.py`（**服务端抓取**，绕开本机 WAF），`www.okooo.com/jingcai/shuju/<页>/`。**覆盖窗口 ≈ 开赛 24h**，临场再抓；bifaw.com 无可用比赛页（弃用）。
  - ⚠️ 2026-10-20 深夜起本机 IP 被 WAF 限流（挑战页/滑动验证/405），`okooo_intel.py` 暂不可用；`intel_fetch.py` 走 `ds_search.fetch` 可拿到 `betfa/dqjc`（15 场 Markdown），`zhishu/peilv/injured/chayi` 仍 404。恢复办法见 `docs/WORKFLOW.md` §1C「抓取现状」。
  - 内部研判层，按 R41 不进公开稿。
- **懂球帝结构化数据（身价/积分榜）** —— 2026-10-20 起可用：`scripts/team_profile.py` 直接抓 `pc.dongqiudi.com/data` 的整张联赛身价表（cid 映射见 `state/cache/_dq_cid.json`），配欧冠联赛阶段榜；**不参与 λ 计算**，只做底档交叉检验。Transfermarkt、雷速实测抓不到（404），别再试。
## 一、优先级 A（直接对应已记录的痛点，建议先试）

### A1. 小红书出图：`claude-design-card` / `guizang-social-card-skill`

- **解的痛点**：自研 `scripts/xhs_html.py` 渲染后仍有「底部仅 0px@2x，页脚可能被裁」告警；且当前模型不支持读图，成图质量只能靠脚本自检，无法人工复核缩略图。
- `guizang-social-card-skill`：专做小红书图文卡 / 3:4 封面 / 微信公众号封面（21:9 + 1:1），有版式模板与实况照片玩法。
- `claude-design-card`：14 种格式（小红书图文卡 / 平台封面 / 社交分享卡 / 长文排版），Playwright 截图出 PNG。
- **落地方式**：不动现有卡（数据向单卡形态已定稿），只在**新形态**（如长图合集、封面重做）时试；若出图稳定，可把底部留白检测从「脚本自检」降级为「首选方案自带余量」。
- ⚠️ 两个都是外部技能，不认本项目的 R41/R44 分层口径，文案层必须自己把关。

### A2. 抓外媒 / 媒体预测：`autocli` / `agent-reach`

> ✅ **2026-10-20 已用自建脚本落地**：`scripts/media_intel.py` + `scripts/ds_search.py`（DeepSeek Search/Fetch，5 元/1000 次）。
> 下面这套 CLI 方案仍可作补充通道（DeepSeek 检索不到时用），不是必需。

- **解的痛点**：`open_items` 记录的「Sports Mole / Sportskeeda 全被 Cloudflare 挡（ProxyError / MaxRetryError）」，以及 `scripts/ext_predict.py` 首轮 22 场全 MISS（别名表缺队名）。
- `autocli`：55+ 站点 CLI（含 Google / Reuters / Bloomberg / BBC / Reddit / 雪球 等），走的是站点自己的通道，不是裸 HTTP，绕 Cloudflare 的成功率高于 `requests`。
- `agent-reach`：15 平台调研路由（小红书 / X / B站 / Reddit / YouTube / GitHub），带多后端路由。
- **落地方式**：先拿「Sports Mole 英超预测页」当靶子跑一次，能出内容就把 `ext_predict.py` 的取数层换成 CLI 调用；出不来就标注「已试不可用」，避免下次重复踩。
- ⚠️ 只补**🌍外媒**一栏与 ext 对照层，不进公开稿的数值口径。

### A3. 标题工程：`title-polisher` + `content-analysis` + `dbs-xhs-title`

- **解的痛点**：m01267 的 30 篇流量结论——CTR 8.5% 是进二波池硬门槛；`模型与市场差出1.3到20个点` 这类标题 CTR 1.2%；R38d 已要求标题前段必须有队名。
- `content-analysis`：拆爆款文章结构 / 爆点 / 可复用模板 —— 可直接喂 TOP5 那五篇（神户全北 9.3%、悉尼 FC 10.1% 等）做反向工程。
- `title-polisher`：改写 AI 模板化标题，走写实生活化风格。
- `dbs-xhs-title`：75 个验证过的爆款标题公式（小红书专用，不是头条口径）。
- **落地方式**：一次性动作 —— 用 `content-analysis` 把 TOP5 拆成「标题公式表」，结论并入 R38d 或 `📚知识库/写作指南/`。不必每次写稿都调技能。

### A4. 降 AI 分 / 去模板腔：`natural-flow-writer` + `concise-rewriter` + `proofreader-zh`

- **解的痛点**：R46 已定位到「语气词缺失 + 节奏平缓」两项，但手法仍是手工拆句；六篇里 012（28.0）、001（28.9）贴着 30 的死线。
- `natural-flow-writer`：禁「首先/其次/最后/综上所述/总分总」，随性切入、口语自然 —— 与 R46 要的「口语短尾」同向。
- `concise-rewriter`：删 AI 铺垫、空洞过渡、凑字数废话。
- `proofreader-zh`：纠错别字、标点、病句，统一语气。
- **落地方式**：写 R46 的「机检不过关时的第二道手」：AI 分 ≥28 就先过 `natural-flow-writer`，再过门禁。⚠️ 它们会改句子，**改完必须重跑 `preflight.py`**（字数 + 8 项门禁会变）。

### A5. 运营指标台账：`office-xlsx`

- **解的痛点**：R40 要求台账必记「展现 / 阅读 / CTR / 平均阅读时长 / 单篇收益」，现在是靠 `docs/日记` 与 `📚知识库/公司工程/硬指标与运营实证.md` 的 md 表格手工维护，10 篇就得占几十行。
- **落地方式**：建 `state/ops-ledger.xlsx`（或 `📚知识库/公司工程/运营台账.xlsx`），逐篇一行，CTR 分档、RPM、发布时间窗三列可算。⚠️ 本项目铁律是**只出 md**，但这个台账不是交付物（不给读者看），是内部数据文件，不违反 R19；若坚持全 md，则用 TSV。

## 二、优先级 B（可用但非当前瓶颈）

| 工具 | 用途 | 判断 |
|---|---|---|
| `longtext-structure-opt` | 长文结构重整（分段、理顺逻辑、合并碎句） | 与本项目 R34 八档轮换**不同源**，容易把已有骨架改回模板腔，慎用 |
| `trend-tracking` / `positioning` | 热点选题、人设定位 | 本项目选题由**赛程**驱动，不是热点驱动，用处有限 |
| `web-browsing-pro` | 实时搜索 + 抓取 + 总结 | 现有 `web_search` / `research` 已够；作为外媒抓取的备选 |
| `archify` | 架构 / 流程图（HTML+SVG） | 若要做《后台模型怎么算的》科普图可用；日常不需要 |
| `office` / `office-docx` / `office-pptx` | Office 三件套 | 🔴 **与 R19「只出 md」直接冲突**，不要用 |
| `dsh-ppt` 插件 | 生成 HTML/PPTX 演示 | 同上，与 R19 冲突 |

## 三、优先级别 C（已装插件，本项目用得上但需先确认边界）

| 插件 | 能干什么 | 本项目该不该用 |
|---|---|---|
| `@linxin666/dsh-client-ui-task-board` | 任务板 + 真实 Session 执行 + Host cron 调度 | ⚠️ **仅限赛程抓取类**（如每天 08:00 拉 slates + 跑 model）。**不挂 journal / 不挂自动发文** —— 用户 2026-09-19 明确拒绝自动化收尾 |
| `@michengai/dsh-automation` | 独立 Session 定时任务 | 同上边界 |
| `@michengai/dsh-agency-agents` | 331 名可召唤专家 | 可在「赛后校验复盘」「流量诊断」时召唤数据分析类专家；⚠️ 结果只是材料，规则口径仍以本地 R/C 系列为准 |
| `dsh-cost-meter` / `@kenz1117/dsh-ui-usage-billing` | 会话成本、日费用 | 已装，可直接看每批写稿的 token 成本，用于判断「一篇稿值不值」 |
| `dsh-mnemon` | 组合式记忆 | ⚠️ 与 AGENTS.md「只用本地 + 免费、不接云端记忆」冲突，**不要写入**；Hindsight 同理（apiToken 401） |
| `dsh-univer-office` | 表格 / 文档 / 幻灯片编辑 | 只有在做上面 A5 的 xlsx 台账时才相关 |

## 四、明确不要碰的

- `office` / `office-docx` / `office-pptx` / `dsh-ppt` —— 与 R19「只出 md，不出 docx、不出 PDF」冲突。
- `hindsight_*` 全部工具、`dsh-mnemon` 写入 —— 与「不使用任何云端记忆服务」冲突（AGENTS.md 记忆原则）。
- `@deepseek-ai/dsh-experimental-agent-team-profile` —— 未安装；本项目是单人单线写作，不构成瓶颈。

## 五、建议的第一个动作

只挑一个试，别铺开：

```
用 content-analysis 把 TOP5 那五篇（10-14 神户全北 9.3% / 10-16 悉尼FC 10.1% / 10-07 巴西国际 9.6% / 10-09 仁川柏太阳神 8.7% / 10-11 光州蔚山 9.1%）拆成标题公式表
```

理由：这是**一次性投入、长期复用**的动作，直接对应 CTR 门槛这个最硬的运营瓶颈；而 A3 的另外两个技能（title-polisher / dbs-xhs-title）是小红书口径，头条未必适用。

第二顺位是 A1（小红书出图），因为每期都要出图，边际收益最高。