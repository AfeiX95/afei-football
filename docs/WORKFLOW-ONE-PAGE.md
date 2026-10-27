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

### 3.2 小红书一图流赛博黑金全维海报 + 纯战术倾向文案（R59 · 2026-10-28 进化定版）
- **形态准则**：**只做 1 张图（既是封面也是内容）**，`1080×1440`（3:4）赛博黑金风格，内置 **3场 (`n3`) / 4场 (`n4`) / 5场 (`n5`) / 6场 (`n6`)** 四套自适应模板。
- **海报构成**：**2 倍六维雷达图**（`R=82/78/60/48px`）+ **主客各 6 格核心技术参数**（近5场均进/失、同主客战力、上半场抢开局、下半场后程得失、进球波动 $\sigma$/净胜、六维综合均值）+ 近5战得失球轨迹胶条（`进2失0胜`）+ 顶栏积分榜/交锋档案（`≤2球占比`）+ 底栏双对比条。
```bash
# ① 生成单张赛博黑金全维海报（自动按 JSON 场次数匹配 3/4/5/6 场模板）
python -X utf8 scripts/xhs_card_d.py --input "📝文章/<date>/_cards_<批次>.json" --out "📝文章/<date>/小红书_<批次>" --only-cover --cover-style poster

# ② 强制指定 3 / 4 / 5 / 6 场模板（或用 --all-templates 一次性导出 4 套样板图）
python -X utf8 scripts/xhs_card_d.py --input "📝文章/<date>/_cards_<批次>.json" --out "📝文章/<date>/小红书_<批次>" --template 4

# ③ 图面数据 + 纯战术倾向文案联合风控门禁（必须 0 命中）
python -X utf8 scripts/xhs_riskcheck.py --cards "📝文章/<date>/_cards_<批次>.json" --text "📝文章/<date>/小红书_<批次>/文案.md"
```
- **文案定式（严控 `<1000` 字小红书上限）**：
  - 每场 `📌 HH:MM｜主队 vs 客队` 下首行写 `战术倾向：...（方向倾向 + X—Y球区间 + 战术观察点）`。
  - 正文结合六维分值与上下半场得失，密集融入教练战术词（`边路推进 / 肋部接应 / 边后卫前压 / 第二落点 / 转换空档`）。
  - 文末固定附合规护盾（「`本文为纯体育竞技分析，所有内容基于公开赛事数据与战术逻辑推演，仅供球迷交流参考，不涉及任何不良导向。请理性观赛，享受足球本身。`」）与 `#理性观赛` `#战术分析`。
- **风控硬红线**：图面与 `文案.md` **严禁出现 `周X00Y / 彩果 / 小球率 / 让球 / 赔率 / 机构` 等彩票/盘口词，严禁出现具体比分（`2-1`）与胜率百分比（`65%`）**。

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
