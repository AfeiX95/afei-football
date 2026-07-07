# 阿飞说球 · 足球分析项目

> AFEI Football Engine — World Cup 2026 Match Analysis & Prediction System

## 项目结构

```
I:\阿飞说球/
├── YYYYMMDD/               ← 按比赛日分文件夹
│   ├── *模型分析*.html      ← 深色主题可视化仪表盘（浏览器直接打开）
│   ├── *赛事前瞻*.md/.docx  ← 文章草稿
│   └── *三场前瞻*.html      ← 头条号可直接粘贴的HTML文章
│
├── 📚知识库/
│   ├── 索引.md              ← 知识库入口（必读）
│   ├── 比赛分析/2026世界杯R32/  ← 全链路分析存档
│   ├── 球队档案/             ← 各队详细信息（西班牙/瑞士/奥地利等）
│   ├── 写作指南/             ← 梗库/管线清单/战术拆解模板
│   └── 数据源/               ← API接口/懂球帝队名ID映射
│
├── 📋复盘与归档/             ← 往期前瞻存档
├── ⚙️工具/                   ← 部署/MCP脚本
├── references/               ← AFEI引擎v2.1参考文档
└── .hermes/                  ← Python分析脚本（λ估算/MC模拟）
```

## 7个核心技能（Hermes Skills）

| 技能 | 版本 | 功能 | 调用方式 |
|:----|:----:|:-----|:---------|
| `football-project-onboarding` | v1.0 | 项目总入口 | `skill_view(name='football-project-onboarding')` |
| `match-model-pipeline` | v2.0 | 核心引擎（λ/MC/EV/品牌溢价） | `skill_view(name='match-model-pipeline')` |
| `football-match-preview-pipeline` | v1.3 | 全流程管线（数据→文章→HTML→合规） | `skill_view(name='football-match-preview-pipeline')` |
| `football-match-preview-article` | v1.4 | 头条号风格引擎（降AI/合规） | `skill_view(name='football-match-preview-article')` |
| `football-lottery-assistant` | v4.1 | 深度分析（七层漏斗/MPS/出线推演） | `skill_view(name='football-lottery-assistant')` |
| `football-model-dashboard-template` | v1.0 | 深色主题仪表盘HTML模板 | `skill_view(name='football-model-dashboard-template')` |
| `dashboard-js-pitfalls` | v1.0 | JS调试手册 | `skill_view(name='dashboard-js-pitfalls')` |

## 工作流程

```
① 数据采集 → ② λ双方法 → ③ MC 10万次 → ④ 伤停修正
→ ⑤ 品牌溢价 → ⑥ 文章写作 → ⑦ HTML输出 → ⑧ 合规检查
```

### 数据采集
- 竞彩网API：`https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c`
- 必须同时获取：固定奖金页（赔率）+ 特征分析页（伤停/历史/射手/积分榜）

### λ双方法
```python
# 方法1: xG实际数据法
xg_for = 场均进球 × 0.92
lambda = (xg_for_adj + xg_against_opp_adj) / 2

# 方法2: 市场反推法
fair = (1/odds) / sum(1/odds)
lambda_raw = 0.4 + fair * 3.2

# 综合 = (方法1 + 方法2) / 2
```

### 淘汰赛战略目标（L0.5）
- 强势方（FIFA排名高/身价高）：目标"90分钟解决" → xG×0.9
- 弱势方（明显下狗）：目标"不输拖加时" → xG×0.5~0.6
- 实力接近：双方×0.85~0.95

### 伤停修正
- 边锋/后卫OUT → λ下调5-8%
- **中场核心OUT → λ下调10-15%**（穆西亚拉/凯塞多案例验证）
- 数据来源：竞彩网特征分析页 → 伤停一览模块

### Edge公式
```text
Edge = P_model - P_market
Edge > +6% → 强价值 ⭐
Edge > +3% → 中价值 🟡
Edge < 0%  → 无价值 ✗
```

## 头条号合规红线

| ❌ 禁止 | ✅ 替换 |
|---------|---------|
| @1.xx 具体赔率数字 | 直接删除 |
| "赔率""盘口""庄家" | "数据"或省略 |
| EV / Edge / 仓位 / 凯利 | 全部删除 |
| "竞彩网"出现在数据来源 | 懂球帝、ESPN、各队官网 |
| "不构成投注建议" | "仅供参考" |
| "主胜""客胜" | "占优""取胜" |

## 关键教训（2026世界杯实战验证）

1. **特征分析页不可跳过**：纯赔率反推λ偏差可达23pp（拉菲尼亚/穆西亚拉/凯塞多三案例）
2. **中场核心伤缺影响巨大**：修正系数10-15%，是边锋的2倍
3. **Wikipedia小组数据可能过时**：注意"Updated to"日期，需从懂球帝补充
4. **淘汰赛低进球是常态**：所有淘汰赛λ和均低于市场期望，小2.5球概率普遍>50%
5. **品牌溢价普遍存在**：传统强队溢价+10~30pp，是价值信号的主要来源

## 数据源

| 来源 | URL | 用途 |
|:----|:----|:-----|
| 竞彩网API | `webapi.sporttery.cn/gateway/...` | 赔率/让球/比分/总进球 |
| 竞彩网特征分析页 | `sporttery.cn` 比赛详情页 | 伤停/历史交锋/射手 |
| 懂球帝 | `dongqiudi.com/team/{id}` | 阵容/身价/球员数据 |
| 雷速体育 | `leisu.com/guide/swot-{id}` | SWOT情报/天气/裁判 |

## 输出物格式

| 平台 | 格式 | 操作 |
|:----|:-----|:-----|
| 头条号 | HTML | 浏览器打开→全选复制→粘贴到编辑器 |
| 公众号 | 纯文本 | 直接输出 |

## 联系

头条号：**阿飞·赛博聊球**
项目维护：Hermes Agent with AFEI Football Engine v2.1+
