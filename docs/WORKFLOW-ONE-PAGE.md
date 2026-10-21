# 工作流一页纸（2026-10-21 起）

> 一句话：**采 → 算 → 报 → 写 → 验 → 复**。
> 你原来的三步（复盘 + 全维度报告 + 做内容）等于其中的「报 → 写」，前后各缺一层。
> 全部命令在仓库根执行，Windows 下加 `-X utf8` 防中文乱码。

---

## 0. 开工（30 秒）

```bash
python -X utf8 scripts/brief.py
```
出：模型版本 / 批次统计 / 真待办 / 待校验文章 / **最新交接节行号**。
然后只读需要的那几段：`read docs/HANDOFF.md offset=<行号> limit=<行数>`（🔴 禁止全量读）。

---

## 1. 采集层（不做这层，报告一定是缺的）

| 步骤 | 命令 | 产物 | 常见失败 |
|:--|:--|:--|:--|
| 赛程 | `python -X utf8 scripts/sporttery_fetch.py slate` | `state/batch/_slate.json` | 只返回当日在售，跨日要重跑 |
| 单场缓存 | `python -X utf8 scripts/sporttery_fetch.py match <id> <id> …` | `state/matches/<id>/`（head/feature/result/history/injury/player/future/tables） | 先跑这步，否则下一步报「缺缓存」 |
| 场次表 | `python -X utf8 scripts/model_autofill.py --date YYYYMMDD` | `state/batch/_matches_<date>.json` | 缺缓存会直接列出来 |
| 盘口+媒体 | `python -X utf8 scripts/prematch_intel.py --date YYYYMMDD --leagues --media` | `state/intel/<date>/_intel_*.md`、`_leagues_*.md`、`_media_*.md` | 媒体约 0.005 元/次，13 场 ≈0.13 元；缺 Key 会告警但不断流水线 |
| 球队底档 | `python -X utf8 scripts/team_profile.py --date YYYYMMDD` | `state/intel/<date>/_team_*.md`（排名/身价/伤停） | 队名要先能在 `ALIAS` 里对上；新联赛先 `--discover` 找 cid |
| 澳客指数 | 手工/隔日：`python -X utf8 scripts/intel_fetch.py --date YYYYMMDD --sources betfa` | `state/intel/<date>/_fetch_*.md` | 必发/凯利/伤停/胜负指数**只覆盖开赛 24h 内**；被 WAF 拦就等临场再抓 |

**懂球帝 cid 速查**：欧冠 6 与 510 ｜ 欧罗巴 14 ｜ 巴甲 19 ｜ 阿甲 76 ｜ 波兰超 106 ｜ 日职+日乙 509。

---

## 2. 模型层（算）

```bash
python -X utf8 scripts/model.py <id> <id> … > state/batch/_model_<date>_<周N>.txt
```
- `model.py` **只打印不落盘**，必须重定向，否则报告脚本读不到。
- 只开让球盘的场（强队打弱队，官方不开胜平负）会被模型**跳过**，这类场报告里要**手算六节**：λ 只有方法1、总进球/比分网格/蒙特卡洛/让球三向各算一遍，结论写「以定价为主、模型只作反面参考」。
- 已知坑：客队本季没打过客场时 `away_away=[0,0,0]` 会 `ZeroDivisionError`，`lam_m1()` 已加零样本回落。

---

## 3. 报告层（报）

```bash
python -X utf8 scripts/intel_full.py --date YYYYMMDD --weekday 周N \
  --model state/batch/_model_<date>_<周N>.txt --nums 周N001 周N002 …
```
产物：`📝文章/<date>/<date>_周N<k>场_内部分析报告.md`

**每场六节固定**：一 盘口（五套+位移+跨盘）｜二 泊松解析解｜三 蒙特卡洛（纯泊松 10 万次 + λ±12% 扰动）｜四 外媒与全球 AI 预测｜五 技术面（近 5 场 + 伤停 + 积分榜 + 天气 + 模型自身告警）｜六 **结论 · 核心矛盾 · 看点**（方向 + 两格高概率比分 + 破局条件，后面保留三格排序/冷门指数/信心）。

**必须在生成后手工补三块**：
1. `## 零、球队底档（k 场）` —— 排名 / 身价 / 倍数表（来自 `_team_<date>.md`）
2. 被模型跳过的场：手写整节六节
3. `## 全批总结（k 场）` —— 分歧排序 + 共性 + 缺口清单

**清理**：抓来的正文里 `## 正面交手统计数据` 之类会破坏结构，把所有非 `## 周N` / `### 一~六` / `## 球队底档` / `## 全批总结` 的 `#` 行改成 `· `。

---

## 4. 内容层（写）

### 4.1 头条（每篇 md，2~4 场）

- 标题：`10月22日 波兹南vs桑德兰、贝西克塔vs水晶宫 前瞻`（≤30 字，**带日期 + 主队vs客队**，利于搜索）
- 每场两节：**核心矛盾与看点**（⚔️ 动机 / 💰 定价 vs 模型差值 + 冷门指数 + 门槛读数）+ **剧本推演**（方向 + 幅度 + 首选-次选-防范 + 触发条件）
- 站位必须各场不同：缺锚跟定价 / 跟方向砍幅度 / 反定价浅 / 同向取中（R49，禁止场场「跟定价」）
- 🔴 **标题（R50）**：前 12 字内必须有「赛事名 + 具体队名 + vs 对位」；**禁用数字黑话当钩子**（「两个三十九个点」「定价最满的那三格」实测冷启动 CTR 0.4% / 2.0%）
- 🔴 **窗口（R52）**：主力篇 10:00–11:00 首发、3–5 场打包；16:00–19:00 不发
- 🔴 **复盘（R51）**：不单独成篇，压 ≤150 字放当日第一篇开头
- 门禁：
```bash
python -X utf8 scripts/preflight.py "<文章.md>"     # 字数 R32 + 8 项门禁
python -X utf8 scripts/check_dup.py YYYYMMDD          # 同批跨篇去重，必须 0 命中
```

**结构轮换（R53）**：动笔前先 `python -X utf8 scripts/pick_structure.py --pick --stage pre --matches N`，按它给的结构写；过门禁后 `--record` 落账（最近 3 篇结构禁用）。
**概率同口径（R54）**：动笔前跑 `python -X utf8 scripts/prob_gate.py --date YYYYMMDD --model state/batch/_model_*.txt`；正文里概率相减前先写「同一个事件＝90 分钟主胜/平/客胜」，让球三格必须写全映射（+1 受让＝不败／正好输一球／输两球以上，−1 让球＝赢两球以上／正好赢一球／对手不败），换算差 >2.5pp 先改映射。

**读者视角（R55，已并入 `preflight.py`）**：跑 `python -X utf8 scripts/preflight.py "<文章.md>"` 会多一行「视角」，有命中即 FAIL（单独看命中可跑 `scripts/reader_lens.py`）；命中概率差/去水/三格/回测/代号就重写那句话——内部算得细，对外讲得简单，公开稿 900–1200 字。

### 4.2 小红书卡（单场深挖，D 版）

```bash
# 从报告直接生成卡片数据（推荐，报告里已有情报/结论/底档）
python -X utf8 scripts/card_from_report.py --report "<报告.md>" --out state/tmp/cards_<周N>.json
# 六维雷达（可选补全）
python -X utf8 scripts/xhs_data.py --input state/tmp/cards_<周N>.json --force
# 出图
export XHS_HTML_TMP="$PWD/state/tmp/xhs_html_tmp"
python -X utf8 scripts/xhs_card_d.py --input state/tmp/cards_<周N>.json \
  --out "📝文章/<date>/小红书_<周N>k场_D版" --cover
```
- 卡面六块：身价对标 → 数据对照·六维 → 数据分布（胜平负饼 + 比分热度只上色）→ 情报整理（主/客各一栏 + 身价·交锋·伤停通栏）→ 核心矛盾与看点（100–200 字，老球迷口气）→ 页脚签名
- 🔴 **形态纪律（10/21 判罚点，判的是形态不是词）**：一场一卡、**不写场次号**、不写页码 `03/13`、图里不给「方向 + 比分结论」、三项概率不并列展示、封面**不列逐场清单**
- 发布正文：`文案.md`，每场一行「主 VS 客：矛盾一句话」，标题带日期（≤20 字），总字数 ≤1000
- 门禁：`xhs_riskcheck.scan_cards`（词表）+ **`scan_form`**（形态）—— 有致命项直接 `exit 2`，别用 `--allow-form-risk` 硬闯

---

## 5. 闭环层（复）

```bash
python -X utf8 scripts/sporttery_fetch.py results <起始日> <结束日>
python -X utf8 scripts/calib_run.py --dates YYYYMMDD YYYYMMDD
```
产物：`📚知识库/赛后校验/<区间>_赛后校验.md`（方向命中 / 三档比分命中 / 让球方向 / 大小球 / 偏差分档）。

**必须回填**：把「偏差分档」写进 `docs/HANDOFF.md` 当批结论——
≥15pp 命中约 23%、6–15pp 约 50%、<6pp 约 78%，即「**大偏差是缺口信号，不是便宜**」。
不回填，复盘就只是一份报告，不变成经验。

---

## 6. 收工（每轮必做）

```bash
python -X utf8 scripts/journal.py            # docs/日记/<date>.md
git add docs/ state/ 📚知识库/ 📝文章/ && git commit -m "进度同步 YYYYMMDD"
python -X utf8 scripts/sync.py --push        # gitee + origin，一个连不上不阻塞
```
`docs/HANDOFF.md` 追加当节（当前状态 / 已知阻碍 / 下一步），`state/model-state.json` 有变化才改。

---

## 7. 失败速查

| 现象 | 原因 | 处置 |
|:--|:--|:--|
| `model_autofill` 报「缺缓存」 | 没跑 `match <id>` | 先抓缓存 |
| `model.py` 报 `ZeroDivisionError` | 某队同主客样本 0 场 | 已修（`lam_m1` 零样本回落）；仍报就查 `_matches` 里 `[0,0,0]` |
| 报告缺某场 | 该场无胜平负，模型跳过 | 手写六节，结论以定价为主 |
| `preflight` 报「裸赔率」 | 出现两位小数（含身价/倍数/λ） | 改成一位小数（5.60 亿 → 5.6 亿） |
| `preflight` 报「缺高概率比分」 | 门禁要**字面**这四个字 | 正文里明确写「高概率比分：…」 |
| `check_dup` 报跨篇重复 | 两篇标签/免责句相同 | 标签各带队名，免责句各写一版（必含「请理性看待比赛」） |
| 出图 `PermissionError` / `WinError 5` | 临时目录/管道受限 | 设 `XHS_HTML_TMP` 指向可写目录；`shot()` 已改 DEVNULL |
| 出图被 `scan_form` 拦 | 触发形态禁令 | 按提示删（场次号 / 页码 / 三项概率 / 方向结论），不要放行 |
| 澳客抓 404 / 滑动验证 | WAF 限流，且页面只覆盖开赛 24h | 隔日或临场补抓，不硬刷 |
| 懂球帝身价抓不到 | 该联赛 cid 不在表里 | `team_profile.py --discover --max-cid 120` 找 cid 再加进 `STAND_CIDS` |

---

## 8. 三条铁律（写在任何产出之前）

1. **90 分钟口径**：加时、点球不计；公开稿里模型只叫「后台模型」
2. **合规替写**：赔率→定价、盘口→门槛/设置、庄家→机构、泊松/MC→后台模型、EV→溢价；公开稿不给方向与比分结论（小红书形态禁令）
3. **交付**：只出 md；小红书出 PNG 2160×2880；正文 ~1200 字；标题 ≤30 字（小红书 ≤20 字）

