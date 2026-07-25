# v3.0 架构映射 — 14维分析 → 系统管线

本文件记录14维分析各维度映射到AFEI v3.0工程系统的位置。
v3.0代码在 `database/` 目录。

## 完整数据流

```
14维分析文本 (旧系统)
  ↓ Adapter v1.5 (adapter_v1.py)
标准化JSON（12字段）
  ↓ Schema Validator (schema_validator.py)
数据完整性验证
  ↓ Feature Extractor v1.0 (feature_extractor.py)
特征向量（12维）
  ↓ Model Engine v2.0 (model_engine.py)
λ = base × (1 + Σ因子贡献)  [乘法公式]
  ↓ Monte Carlo 10万次（带±5%随机扰动）
MC概率 + 比分Top3
  ↓ Fusion Engine v1.0 (fusion_engine.py)
四源评分 → Context权重加权 → 校准映射 → 概率
  ↓ Output Generator v1.0 (output_generator.py)
最终预测报告（.md）
  ↓ Feedback Learning v1.0 (feedback_learning.py)
结果记录 → 偏差分析 → 20场短周期 → 100场长周期
```

## λ乘法公式

λ_home = base × (1 + strength_gap×0.35 + point_gap×0.15 + home_advantage×0.20 + form_gap×0.20 + injury_away×(-0.30))

λ_away = base × (1 - strength_gap×0.35 - point_gap×0.15 - home_advantage×0.12 + form_away×0.20 + injury_home×(-0.30))

base = 1.4,  λ ∈ [0.3, 4.0]

## 融合权重

| 赛事类型 | Model | Analysis | Market | Intel |
|:---------|:-----:|:--------:|:------:|:-----:|
| 普通联赛 | 35% | 30% | 20% | 15% |
| 杯赛淘汰 | 25% | 25% | 15% | 35% |
| 德比 | 30% | 20% | 20% | 30% |
| 资格赛 | 25% | 30% | 25% | 20% |

## 校准映射

Score 85 → Win 70% / Draw 18% / Loss 12%
Score 65 → Win 50% / Draw 26% / Loss 24%
Score 45 → Win 28% / Draw 30% / Loss 42%
Score 35 → Win 20% / Draw 26% / Loss 54%

## 异常检测

- 热门过热: 主胜<1.40 且 模型胜率<市场-10pp → favorite_overheat
- 模型冲突: 模型vs市场概率差异>15pp → probability_gap_warning

## 双周期反馈

- 短周期（20场窗口）: 偏差模式检测，>30%频率自动修正
- 长周期（100场累计）: 各赛事准确率分析，权重调整建议

## 配置文件

- database/config/model-parameters.json — λ公式系数 + MC参数
- database/config/feature-parameters.json — 特征归一化参数
- database/config/fusion-parameters.json — 融合权重 + 校准映射
