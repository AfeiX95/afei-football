---
name: football-data-aggregator
description: "赛事数据捕获器——自动从新球体育、懂球帝、竞彩网抓取比赛数据。支持积分榜、近期战绩、H2H交锋、控球率、射门射正、伤停名单等。替代手动粘贴数据的流程，5分钟完成原本2小时的数据收集工作。v1.0"
version: 1.0.0
author: afei
license: MIT
---

# Football Data Aggregator 赛事数据捕获器

> 定位：自动化数据采集，替代手动粘贴竞彩网/新球体育数据
> 适用场景：每场比赛分析前的数据收集阶段
> 搭配使用：match-model-pipeline（数据采集Step）

---

## 一、数据源优先级

| 优先级 | 数据源 | URL | 可抓取内容 | 方法 |
|:------:|:-------|:----|:-----------|:-----|
| 1 | 竞彩网 JSON API | webapi.sporttery.cn | 赛程/赔率/让球/比分 | requests |
| 2 | 新球体育 | titan007.com | 特征分析/百家欧赔/盘路走势 | requests+BeautifulSoup |
| 3 | 懂球帝 | dongqiudi.com | 阵容/身价/射手/教练/评分 | API |
| 4 | 网易彩票 | sports.163.com | 赛程总览/场次编号 | web_extract |

---

## 二、核心脚本

### 2.1 竞彩网数据抓取

脚本位置：`database/scripts/jingcai_fetcher.py`

功能：
- 通过 JSON API 获取当日竞彩赛程
- 提取场次编号、联赛、主客队、赔率、让球数
- 输出结构化 JSON 供模型使用

用法：
```bash
python database/scripts/jingcai_fetcher.py --date 2026-08-02
```

### 2.2 新球体育数据抓取

脚本位置：`database/scripts/titan_fetcher.py`

功能：
- 抓取指定比赛的特征分析页
- 提取：积分排名、近期战绩、H2H交锋、控球率、射门射正、伤停、盘路走势
- 输出 Markdown 格式报告

用法：
```bash
python database/scripts/titan_fetcher.py --match-id 2929675 --output match_data.md
```

### 2.3 懂球帝数据抓取

脚本位置：`database/scripts/dongqiudi_fetcher.py`

功能：
- 通过懂球帝 API 获取球队数据
- 提取：阵容身价、射手榜、教练信息、球员评分
- 输出 JSON 格式

用法：
```bash
python database/scripts/dongqiudi_fetcher.py --team-id 12345
```

---

## 三、工作流集成

### 标准分析流程中的数据采集步骤

```
Step 1: 用户指定比赛 → 调用 jingcai_fetcher.py 获取赛程+赔率
Step 2: 调用 titan_fetcher.py 获取特征分析全量数据
Step 3: 调用 dongqiudi_fetcher.py 获取阵容+身价+射手
Step 4: 汇总输出 match_data.json → 供 14维评分卡 使用
```

### 数据输出格式

```json
{
  "match_id": "20260802_001",
  "league": "韩K联",
  "home_team": "蔚山HD",
  "away_team": "FC安养",
  "kickoff": "2026-08-02 18:30",
  "odds": {"home": 1.86, "draw": 3.45, "away": 3.32},
  "handicap": {"home": -1, "odds": [3.6, 3.7, 1.72]},
  "home_ranking": {"position": 4, "points": 31, "record": "9W4D7L"},
  "away_ranking": {"position": 5, "points": 30, "record": "7W9D4L"},
  "home_form": ["L","W","L","D","L","D"],
  "away_form": ["W","W","W","D","W","L"],
  "h2h": [...],
  "injuries": {...},
  "possession_avg": {...},
  "shots_avg": {...}
}
```

---

## 四、注意事项

1. **API 可用性**：竞彩网 JSON API 仅返回当日比赛，提前抓取需用日期参数
2. **反爬限制**：新球体育/懂球帝有频率限制，单次间隔≥2秒
3. **数据缓存**：抓取结果缓存到 `database/cache/` 目录，24小时内复用
4. **降级方案**：API 不可用时，回退到用户手动粘贴（现有流程）
5. **数据核验**：抓取后必须与竞彩网官方数据交叉验证（见 AGENTS.md 数据核验清单）

---

## 五、依赖

```
requests>=2.28.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```
