# AFEI Football AI v3.0 — 变更日志

## v3.0-alpha（2026-07-16）

### 架构变更
- 从6层架构升级为7层（新增Layer 0 Match Context）
- 从11个Skill精简为6个核心Skill
- 建立统一JSON Schema（12个一级字段）
- 新增Layer 4 Prediction Fusion Engine（待开发）
- 新增Layer 6 Feedback Learning（待开发）

### 规则变更
- 杯赛情报拆分为阵容/心理/环境/新闻子项
- 资格赛引入数据可信度系数
- 赔率权重引入市场效率系数
- 反馈周期改为20场短周期+100场长周期
- market字段从odds独立
- 反馈存储从Hermes迁移到文件数据库

### 废弃
- football-lottery-assistant（含投资策略）
- 所有"投资方案/资金策略"相关内容

---

*此文件在每次架构/模型版本变更时更新。*
