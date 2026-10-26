# Predictions Ledger & 回测（v1 · 2026-10-27 建）

> 目的：把「模型 vs 市场谁更强」从争论变成可复现的数字。
> 纪律：赛前冻结、不可覆盖、结果追加；历史补录必须标 `retrospective=true`，永远不进样本外检验。

## 一、存储结构

```
state/ledger/
  predictions/<YYYYMMDD>.jsonl   # 每行一条赛前记录（append-only，逐条哈希）
  results/<YYYYMMDD>.jsonl       # 每行一条赛后结果（append-only）
  stance/<YYYYMMDD>.json      # 可选：人工决策层 {"005": {"stance":"顺定价","abstained":false}}
  history_audit.json           # 历史方向审计的机器可读产物
  backtest_<YYYYMMDD>.md       # 回测报告
```

`predictions` 与 `results` 以 `match_id`（`<YYYYMMDD>-<竞彩编号>`）关联，**分开写**：赛前只写预测，赛后只追加结果，任何一方都不修改对方。

## 二、字段字典（schema `afei-ledger-v1`）

| 字段 | 类型 | 含义 / 来源 |
|---|---|---|
| `match_id` | str | `<YYYYMMDD>-<001..>`，与竞彩编号一致 |
| `day` / `source_id` | str | 批次日期 / 500.com 单场 id |
| `league` `match` `home` `away` | str? | 联赛、对阵；缺则进 `missing_fields` |
| `kickoff` | ISO8601+08:00 | 开球时间（来自 `_market_*.json` 的 `kickoff`） |
| `prediction_timestamp` | ISO | **预测生成时刻**（取 `_model_v3_*.json` 的 mtime，不是写入账本时刻） |
| `ledger_written_at` | ISO | 落账时刻（两者分开，便于审计） |
| `model_version` `data_snapshot_id` | str | 模型版本 / 数据快照 id（来自模型 json） |
| `probs.A / M / F` | [p_H,p_D,p_A] | 三套三向概率（0–1） |
| `lam.A / M / F` | [λ_h,λ_a] | 三套 λ（A=独立、M=市场联合拟合、F=融合） |
| `w_data` | float | 融合时数据侧权重（v3.1 口径：样本量打折） |
| `n_eff` | [int,int] | 同主客样本量（主/客） |
| `data_grade` / `evidence_grade` | str | 数据完整性等级 / 预测证据等级（两个概念，不混用） |
| `odds.*` | obj | 赛前去水市场概率、返还率、亚盘线、大小线、抓取时间、来源 |
| `stance` / `abstained` | str? / bool | 决策层站位；弃权=true 时不计入损失但计入覆盖率 |
| `retrospective` | bool | 历史补录标记（true 一律不进样本外统计） |
| `post_kickoff` | bool | 预测时刻晚于开球 → 标记污染 |
| `missing_fields` / `flags` | [str] | 缺项与异常（`stance_missing` / `abstained` …） |
| `record_sha256` | hex | 除本字段外整条记录规范化 JSON 的 SHA-256 |

**不可变性**：同 `match_id` 二次写入直接退出码 2 并拒绝，文件一字不动；`verify` 逐条重算哈希，任何静默篡改都会失败。

## 三、命令

```bash
python -X utf8 scripts/ledger.py append --day 20261027            # 赛前写入（已有记录会拒绝）
python -X utf8 scripts/ledger.py append --day 20261027 --dry-run  # 先看会写什么
python -X utf8 scripts/ledger.py add-result --day 20261027 --json res.json   # {"001":{"score":"2:1","ht":"1:0"}}
python -X utf8 scripts/ledger.py add-result --day 20261027 --json res.json --retrospective
python -X utf8 scripts/ledger.py verify      # 哈希与幂等校验（CI 可跑）
python -X utf8 scripts/ledger.py status      # 每日覆盖度

python -X utf8 scripts/backtest.py           # 出 backtest_<today>.md
python -X utf8 scripts/backtest.py --include-retrospective   # 仅作描述性查看，不作结论
python -X utf8 scripts/history_audit.py      # 历史方向审计（P1）
```

## 四、回测口径（写死在脚本里）

- **样本**：`probs.A/M/F` 齐全、`results` 有 90 分钟赛果、`post_kickoff=false`、`retrospective=false`。
- **指标**：Multiclass Brier（Σ(p−y)²）、LogLoss（−ln p_actual，clamp 1e-12）、十档可靠性 + ECE。
- **比较**：同一批场次、同一模型集合；成对损失差（F−M / A−M / A−F）+ bootstrap 95% CI（seed 20261027）。**CI 跨 0 一律读作「无结论」**。
- **P3 权重实验**：按开球时间排序切 train/test（默认 0.6）；w 只在 train 上选，test 只报告；train/test 各 <30 场时只列曲线、不下结论。
- **P3 弃权实验**：按 |A−M|（主胜概率差 pp）分档，同时报告覆盖率与损失——禁止用大量弃权刷准确率。

## 五、当前状态（诚实版）

- 账本已播种 **20261027 10 场**（v3.1 → 已冻结为基线；v3.2 起只改区间口径与溯源，不改 λ/权重）。
- 可回测样本 **0 场**（比赛未开球）：`backtest_20261027.md` 只证明管线可跑。
- 历史 60 份校验文档抽出 **458 条**逐场行（去重后）：L1 213 / L2 140 / L3 103；**没有任何一场带赛前三向概率与赛前时间戳** → 历史只能做方向命中率交叉核对，**不能进概率回测**。
- `stance` 字段目前缺（`flags: stance_missing`）：站位是人工判断，需要按报告「决策看板」逐场回填，不自动推断。

## 六、下一批的标准动作

1. 生成报告后、开球前：`ledger.py append --day <YYYYMMDD>`（失败即视为门禁未过）。
2. 赛果出来后：`ledger.py add-result ...`（只追加，不改预测）。
3. 每累计 ≥30 场：跑 `backtest.py`，只在 CI 不跨 0 时才允许说「更好/更差」。
