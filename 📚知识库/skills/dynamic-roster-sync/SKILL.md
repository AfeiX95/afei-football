---
name: dynamic-roster-sync
description: "阵容与转会动态同步器——自动对接转会传闻、球员租借/复出、身价变动，确保模型使用的是最新人员数据。解决'某前锋已租借离队但模型还在用旧数据'的滞后问题。v1.0"
version: 1.0.0
author: afei
license: MIT
---

# Dynamic Roster & Market Sync 阵容与转会动态同步器

> 定位：实时同步球员变动（转会/租借/伤停/复出/身价变化）
> 核心价值：确保模型永远用最新人员数据，不被过期信息误导
> 搭配使用：football-injury-tracker + 14维评分卡维度#3/#4

---

## 一、追踪维度

### 1.1 球员流动追踪

| 事件类型 | 数据来源 | 更新延迟 |
|:---------|:---------|:--------:|
| 转会（买入/卖出） | Transfermarkt/罗马诺推特 | 1-24小时 |
| 租借（加入/离队） | 俱乐部官网 | 1-7天 |
| 伤病（新增/复出） | 俱乐部公告/记者 | 实时-24小时 |
| 停赛（红黄牌累积） | 联赛官方 | 即时 |
| 青年队提拔 | 俱乐部官网 | 1-7天 |

### 1.2 身价动态追踪

| 追踪项 | 数据来源 | 更新频率 |
|:-------|:---------|:---------|
| 球员市场身价 | Transfermarkt | 每月 |
| 球队总身价 | Transfermarkt | 每月 |
| 身价涨幅TOP10 | Transfermarkt | 每月 |
| 年龄结构变化 | Transfermarkt | 每季度 |

### 1.3 状态追踪

| 追踪项 | 数据来源 | 判断标准 |
|:-------|:---------|:---------|
| 球员可用状态 | 俱乐部公告 | 可用/伤疑/缺阵/停赛 |
| 球员竞技状态 | 近5场评分 | >7.0=优秀, 6.0-7.0=正常, <6.0=低迷 |
| 球员位置变化 | 比赛数据 | 是否被改造位置 |

---

## 二、核心脚本

### 2.1 球员状态同步器

脚本位置：`database/scripts/roster_sync.py`

功能：
- 从Transfermarkt抓取球队当前阵容
- 标记伤停/停赛/可用状态
- 输出最新阵容JSON

```bash
python database/scripts/roster_sync.py --team "Ulsan HD"
```

### 2.2 转会动态监控

脚本位置：`database/scripts/transfer_monitor.py`

功能：
- 监控Transfermarkt转会页面
- 检测新增转会/租借事件
- 输出转会动态报告

```bash
python database/scripts/transfer_monitor.py --league "K-League" --days 7
```

### 2.3 身价变动追踪

脚本位置：`database/scripts/market_value_tracker.py`

功能：
- 追踪球员身价变化
- 识别身价大幅波动（>20%变化）
- 输出身价变动报告

```bash
python database/scripts/market_value_tracker.py --team "Ulsan HD"
```

---

## 三、球员状态数据库结构

```json
{
  "team": "蔚山HD",
  "last_synced": "2026-08-02T10:00:00",
  "squad": [
    {
      "name": "埃里克·法里亚斯",
      "position": "中锋",
      "nationality": "巴西",
      "age": 28,
      "market_value": "350万欧",
      "status": "injured",
      "injury_details": "跟腱手术，预计2026年10月复出",
      "season_stats": {"goals": 8, "assists": 3, "appearances": 18},
      "recent_form": 6.8
    },
    {
      "name": "托马斯·欧德科特",
      "position": "中卫",
      "nationality": "澳大利亚",
      "age": 30,
      "market_value": "200万欧",
      "status": "injured",
      "injury_details": "未知损伤，恢复中",
      "season_stats": {"goals": 1, "assists": 0, "appearances": 15},
      "recent_form": 6.5
    },
    {
      "name": "卡扎伊什维利",
      "position": "前腰",
      "nationality": "格鲁吉亚",
      "age": 26,
      "market_value": "500万欧",
      "status": "available",
      "injury_details": null,
      "season_stats": {"goals": 10, "assists": 7, "appearances": 20},
      "recent_form": 7.2
    }
  ]
}
```

---

## 四、状态变更检测规则

### 4.1 自动标记规则

| 规则 | 触发条件 | 动作 |
|:-----|:---------|:-----|
| 伤病标记 | 俱乐部公告/记者报道 | status → "injured" |
| 复出标记 | 训练合练/官方宣布 | status → "available" |
| 停赛标记 | 红牌/累积黄牌 | status → "suspended" |
| 转会标记 | Transfermarkt更新 | 从阵容中移除/添加 |
| 状态预警 | 近3场评分<6.0 | 标记 "form_concern" |

### 4.2 与14维评分卡对接

| 评分卡维度 | 球员数据对接 |
|:-----------|:-------------|
| #3 伤停影响 | status="injured"的球员 → 累积λ修正 |
| #4 球员身价差 | 比赛可用球员总身价 → 身价差修正 |
| #6 核心球员对位 | available球员的recent_form → 对位评估 |

---

## 五、数据源优先级

| 优先级 | 数据源 | 可靠性 | 更新速度 |
|:------:|:-------|:------:|:--------:|
| 1 | 俱乐部官方网站 | ★★★★★ | 慢（1-7天） |
| 2 | Transfermarkt | ★★★★☆ | 中（1-24小时） |
| 3 | 懂球帝 | ★★★★☆ | 快（实时） |
| 4 | 随队记者推特 | ★★★☆☆ | 快（实时） |
| 5 | 罗马诺/奥恩斯坦 | ★★★★★ | 快（转会窗口期） |

---

## 六、注意事项

1. **转会窗口期**：夏窗/冬窗期间更新频率需要提高到每日
2. **虚假消息**：转会传闻需交叉验证，不能单凭一条推文就更新
3. **青年队球员**：提拔的一线队新人可能没有历史数据，需要特殊处理
4. **身价滞后**：Transfermarkt身价每月更新一次，比赛中可能已有变化
5. **国籍变更**：归化球员的国籍可能变化，影响国家队征召逻辑
