# AFEI Football AI v3.0 — 版本基线

## 当前版本

```
AFEI Football AI v3.0
发布日期：2026-07-17
架构状态：✅ 全6层完成
```

## 模型版本

| 模块 | 版本 | 状态 |
|:-----|:----:|:------|
| Architecture | v3.0.0 | ✅ 完成 |
| Data Schema | v1.0 | ✅ 完成 |
| Adapter | v1.5 | ✅ 完成 |
| Schema Validator | v1.0 | ✅ 完成 |
| Feature Extractor | v1.0 | ✅ 完成 |
| Model Engine | v2.4.2 | ✅ 完成 (2026-07-20校准) |
| Fusion Engine | v1.0 | ✅ 完成 |
| Confidence Engine | v1.0 | ✅ 完成 |
| Output Generator | v1.0 | ✅ 完成 |
| **Feedback Learning** | **v1.0** | **✅ 完成** |

## 最新校准 (Batch #7, 2026-07-20)

### 新增修正规则
| # | 规则 | 触发条件 | 修正 | 来源 |
|:-:|:----|:---------|:----|:-----|
| R1 | 决赛极端防守 | 决赛级别 | λ×0.90 | 西班牙0-0阿根廷 |
| R2 | 三四名/已出局开放 | 三四名决赛/双方已出局 | λ×1.10~1.25 | 法国4-6英格兰 |
| R3 | K联赛过热收紧 | K联赛 rank_gap<6 | 阈值1.40→1.30 | 安养1.49→1-1 |
| R4 | 超低赔例外 | rank_gap≥12 赔率≤1.20 | 不触发过热 | 哈马比1.13→4-0 |
| R5 | 挪超主场不稳 | 挪超联赛 | 主场优势0.15→0.10 | 莫尔德@1.77→1-2 |

### 累计方向准确率: 29/45 (64.4%)

## 迁移状态

- [x] 版本基线建立
- [x] Adapter Layer (v1.5)
- [x] Feature Extractor (v1.0)
- [x] Model Engine (v2.0)
- [x] Fusion Engine (v1.0)
- [x] Feedback Learning (v1.0)

## 完整数据链路

```
14维分析文本
  ↓ Adapter v1.5
标准化JSON（12字段）
  ↓ Schema Validator
数据完整性验证
  ↓ Feature Extractor v1.0
特征向量（12维）
  ↓ Model Engine v2.0
λ + MC概率 + 比分Top3
  ↓ Fusion Engine v1.0
四源评分融合 + 置信度 + 风险
  ↓ Output Generator v1.0
最终预测报告
  ↓ Feedback Learning v1.0
结果记录 → 偏差分析 → 20场修正 → 100场校准
```

---

*此文件在每次架构/模型版本变更时更新。*
