# 🗺️ 数据源 — API接口 & 数据抓取

## 竞彩网（sporttery.cn）

| 数据类型 | URL | 方法 | 备注 |
|:---------|:----|:----|:------|
| 赛程+赔率 | `https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c` | curl | ✅ 可用，返回JSON |
| 赛果开奖 | 同上站点的结果页面 | browser | ⚠️ WAF拦截，需浏览器渲染 |

### 字段映射（getMatchCalculatorV1.qry）

```
value.matchInfoList[].subMatchList[]
├── matchId           — 竞彩内部ID（≠mid）
├── matchNumStr       — 竞彩编号（如"周四084"）
├── homeTeamAbbName   — 主队名
├── awayTeamAbbName   — 客队名
├── had               — 胜平负赔率 {h, d, a}
├── hhad              — 让球胜平负 {h, d, a, goalLine}
├── crs               — 比分赔率 {s01s00=1-0, s00s00=0-0...}
├── ttg               — 总进球赔率 {s0, s1, s2...}
├── hafu              — 半全场赔率
├── matchStatus       — "Selling"=在售
├── matchDate/time    — 比赛时间
├── homeRank/awayRank — 排名（如"[世界杯1]"）
└── remark            — 场地备注
```

## 懂球帝（dongqiudi.com）

| 用途 | URL模式 | 方法 |
|:-----|:--------|:-----|
| 球队阵容 | `https://www.dongqiudi.com/team/{teamId}` | browser → 点击"阵容"tab → console提取 |

### 懂球帝球队ID

| 球队 | 懂球帝ID | Leisu阵容ID |
|:----|:--------:|:-----------:|
| 瑞士 | 1931 | 10871 |
| 阿尔及利亚 | 13 | 23383 |
| 葡萄牙 | ? | ? |
| 克罗地亚 | ? | ? |

### 提取阵容的JS代码
```javascript
// browser_console中执行
document.querySelectorAll('table')[N].textContent
// 前锋=N/A, 中场=N/A, 后卫=3, 门将=4（需根据页面实际情况调整索引）
```

## 雷速体育（leisu.com）

| 用途 | URL模式 | 方法 |
|:-----|:--------|:-----|
| SWOT分析 | `https://www.leisu.com/guide/swot-{id}` | browser ✅ |
| 球队阵容 | `https://www.leisu.com/data/zuqiu/team-{id}/lineup` | browser ✅ |

> ⚠️ 雷速会触发滑块验证（WAF），如果遇到验证页面，换个UA或等会儿再试。
