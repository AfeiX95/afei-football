# 工作流一页纸（v3.1 · 2026-10-28 更新）

> 一句话：**采 → 验 → 算 → 报 → 写 → 检 → 复**。
> 全部命令在仓库根执行，Windows 下统一加 `-X utf8` 防中文编码问题。

---

## 0. 开工（30 秒）

```bash
python -X utf8 scripts/sync.py --pull   # 换机器/多机协作先拉最新（只从 gitee 拉）
python -X utf8 scripts/brief.py         # 一条命令看模型版本/批次统计/真待办/最新交接行号
```
- 按需读交接：`read docs/HANDOFF.md offset=<行号> limit=<行数>`（🔴 **禁止全量读 HANDOFF**）。

---

## 1. 采集与数据质检层（采 → 验）

| 步骤 | 命令 | 产物 | 说明 / 常见故障 |
|:--|:---|:---|:---|
| ① 竞彩盘口+情报+排名+外媒 | `python -X utf8 scripts/prematch_intel.py --date YYYYMMDD --leagues --media` | `state/intel/<date>/_intel_<date>.{json,md}`、`_leagues_*.md`、`_media_*.md` | 五套盘快照+去水+位移+跨盘校验+维基积分榜+比赛时刻天气+DeepSeek外媒 |
| ② 500.com 百家亚盘欧赔 | `python -X utf8 scripts/books_500.py --date YYYYMMDD --weekday 周N` | `state/intel/<date>/_books_<date>.{json,md}` | 采集亚盘水位、主客让球方向、百家欧赔均值 |
| ③ 市场结构聚合 | `python -X utf8 scripts/market_from_intel.py --date YYYYMMDD` | `state/intel/<date>/_market_<date>.json` | 合并竞彩去水与外围亚盘欧赔 |
| ④ 球队底档（身价/伤停） | `python -X utf8 scripts/team_profile.py --date YYYYMMDD` | `state/intel/<date>/_team_<date>.{json,md}` | 懂球帝联赛身价表 + 伤停交叉 |
| ⑤ **入模前数据质检（必跑）** | `python -X utf8 scripts/audit_data.py --date YYYYMMDD` | 终端质检报告（阻断级/警告级） | 拦主客场颠倒、跨赛季污染、单边空近期、亚盘方向写反 |

---

## 2. 模型与内部报告层（算 → 报）

```bash
# ① 跑 v3.1 模型（自动执行 100k MC + Brier 校准融合 + 写盘 + 登记待结算台账）
python -X utf8 scripts/model_v3.py 20261028

# ② 生成内部全维度分析报告（A 层：仅供内部研判，不公开发布）
python -X utf8 scripts/build_internal_report.py 20261028 周三13场

# ③ 报告与公开稿一致性硬验收（必跑：0 ERROR 才算合格）
python -X utf8 scripts/check_report_consistency.py 20261028
```
- **产物**：
  - `state/model/v3_<date>.json`（结构化三向概率、融合权重 $w_{\text{mkt}}$、置信区间、Top 比分）
  - `📝文章/<date>/<date>_周N<k>场_内部分析报告.md`（每场七节：盘口与外围对照 / 泊松与DC / 蒙特卡洛与稳定率 / 外媒与AI / 技术面 / 融合收敛与剧本比分）

---

## 3. 内容创作与门禁层（写 → 检）

### 3.1 头条公开稿（B 层：读者视角 · 只出 `.md`）
- **结构轮换（R53）**：动笔前跑 `python -X utf8 scripts/pick_structure.py --pick --stage pre --matches N`，过门禁后 `--record` 落账（近 3 篇结构禁用）。
- **内外严格分层（R41 / R55 / R56）**：
  - **人设**：以老球迷「阿飞」第一人称行文，亮出面对数据冲突时的判断取舍（如顺着走 / 砍幅度 / 单边缺数据直接留白）。
  - **严禁露内部词（`reader_lens.py` 硬拦）**：不写 `后台模型 / 模型 v3.1 / 泊松 / 蒙特卡洛 / 点估计 / 置信区间 / 样本量 / 融合权重 / 去水`，不写押注黑话（`押 / 下注 / 重仓 / 稳胆 / 跟单`），不写让球行话（`球半 / 平手盘 / 受让 / 上盘 / 下盘 / 走盘 / 打穿`）。
  - **取消模板标签（R56）**：公开稿**不写 `⚔️战意`、`💰信号`、`🌍外媒` 标签行**，动机与失球依据自然融进段落。
  - **每场必备三要素**：**具体赛事数据 + 明确立场 + `推荐比分：A 比 B（首选）／C 比 D（次选）／E 比 F（防范）`**。
  - **不编资金流向（R48）**：价格变动只写「定价往哪边倾斜」，禁写「有资金在往主队压 / 机构在防平」。
- **标题与信用分红线（R38 / R50 / R58）**：
  - 标题 ≤30 字，前 12 字内必含赛事或具体队名对位；标点仅用官方白名单（`？` `！` `，` `：` `“ ”` `《》` `——` `｜`）。
  - **严禁删稿重发（R58）**：审核中、未通过或微调的稿件一律在头条后台点「修改」，删后重发触发消重仅推粉丝。
- **一键盘门禁（写完必跑，全绿才交付）**：
```bash
python -X utf8 scripts/preflight.py "📝文章/YYYYMMDD/<文章>.md"   # 字数(800-1500) + 8项合规 + R55视角 + 句长sd提示
python -X utf8 scripts/check_dup.py YYYYMMDD                      # 同批多篇逐行去重，必须 0 命中
```

### 3.2 小红书（R59 · 2026-10-28 晚修订：凌晨版已撤销）
> 🔴 先读 `📚知识库/写作指南/小红书合规规范_20261021.md` 一页纸。凌晨版「多场一图流 + 战术倾向文案」10-28 11:33 发、11:57 即判涉赌（第 7 次违规）。

- **只讲发生过什么**：图与文都不写方向（倾向/占优/不败/保留平局）、进球区间（`2—3球`）、比分、概率。
- **单篇 ≤4 场**，能 1–2 场就别多；标题不写「N 场焦点战 / 推演 / 倾向」；5/6 场模板停用。
- **不上图不入文**：`90 分钟 / 常规时间 / ≤2球占比 / 场次编号`、「不构成建议 / 理性观赛」类撇清句。
```bash
python -X utf8 scripts/xhs_card_d.py --input "<cards.json>" --out "<目录>" --only-cover --cover-style poster   # 入口已接 scan_cards + scan_form，命中即拒绝出图
python -X utf8 scripts/xhs_riskcheck.py "<cards.json>" --text "<文案.md>"                                    # 文案形态门禁（方向/区间/口径/撇清）
```
- 0 命中 ≠ 安全：发前按 10-21 规范 §6.2 人工过一遍。

---

## 4. 赛后校验与台账闭环（复）

```bash
# ① 拉取官方 90 分钟赛果
python -X utf8 scripts/sporttery_fetch.py results YYYY-MM-DD YYYY-MM-DD

# ② 自动结算台账（对比模型 vs 市场 vs 融合 Brier / LogLoss / 方向命中率）
python -X utf8 scripts/ledger.py settle --date YYYYMMDD
python -X utf8 scripts/ledger.py summary

# ③ 生成批次赛后校验报告
python -X utf8 scripts/calib_run.py --dates YYYYMMDD YYYYMMDD
```
- 校验结论回写 `state/model-state.json`（已闭环项迁入 `state/task-log.json`）与 `📚知识库/赛后校验/batchNN_calibration.md`。

---

## 5. 收工（每轮必做）

```bash
python -X utf8 scripts/journal.py            # 更新 docs/日记/YYYY-MM-DD.md
git add docs/ state/ 📚知识库/ 📝文章/ scripts/ && git commit -m "进度同步 YYYYMMDD"
python -X utf8 scripts/sync.py --push        # 推送 gitee + origin
```
