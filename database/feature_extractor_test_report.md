# AFEI v3.0 Feature Extractor — 验收报告

## Sprint 2 完成：Feature Extractor v1.0 ✅

---

## 测试结果

| 测试用例 | strength_gap | point_gap | form_gap | injury_gap | 环境特征 |
|:---------|:-----------:|:---------:|:--------:|:----------:|:---------|
| 法国vs西班牙（世界杯） | +0.03（接近均衡） | 0.0✅(无联赛积分) | 0.0 | 0.0 | cup=1 ✅ |
| 杰尔vs雷克维京（资格赛） | 0.0（无排名） | +0.33 | 0.0 | 0.0 | qualifier=1 ✅ |
| 奥勒松vs莫尔德（挪超） | **-0.28**（#13vs#5） | 0.0 | 0.0 | 0.0 | 均=0正常 |
| 哥德堡vs索尔纳（瑞超） | **-0.10**（#14vs#11） | +0.17 | 0.0 | 0.0 | 均=0正常 |

## Bug修复

| Bug | 修复 |
|:-----|:------|
| 世界杯"90分钟"里的"90分"被当积分 | 加`跳过含90分钟的行` |

## 已实现特征（12个）

| 类别 | 特征 | 优先级 | 状态 |
|:-----|:------|:------:|:----:|
| 实力 | strength_gap | P0 | ✅ |
| 实力 | point_gap | P0 | ✅ |
| 主客场 | home_advantage | P0 | ✅ |
| 状态 | form_home / form_away / form_gap | P0 | ✅ |
| 攻防 | attack_home/away / defense_home/away | P1 | ⚪ 占位，待team_basic完备后激活 |
| 伤停 | injury_home / injury_away / injury_gap | P1 | ✅ |
| 市场 | market_confidence / market_warning | P1 | ✅ |
| 环境 | is_cup / is_qualifier / is_derby / data_confidence | P1 | ✅ |

## 数据流验证

```
旧分析文本（14维md）
  ↓
Adapter → JSON（12字段）
  ↓
Feature Extractor → Feature Vector（12特征）
  ↓
[待开发] Model Engine → λ + MC
```

## 输出文件

```
database/tests/features/
├── 法国vs西班牙_features.json
├── 杰尔vs雷克维京_features.json
├── 奥勒松vs莫尔德_features.json
└── 哥德堡vs索尔纳_features.json
```

---

## 下一步建议

Sprint 2完成。可以进入 **Sprint 3: Model Engine v2.0**（λ生成器 + Poisson + MC 10万次模拟）。
