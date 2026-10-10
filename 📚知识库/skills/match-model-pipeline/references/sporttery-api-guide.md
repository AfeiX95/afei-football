# 竞彩网API数据提取指南

> 2026-06-29 实战验证 | 比HTML解析更可靠、更完整

---

## API端点

```
GET https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c
```

无需认证，返回完整的JSON。

## JSON结构

```python
# 解析路径
data = response.json()
matches = data['value']['matchInfoList']  # 按比赛日分组

for day in matches:
    business_date = day['businessDate']  # "2026-06-29"
    for match in day['subMatchList']:
        mid = match['mid']               # 比赛ID（可能为None）
        match_num = match['matchNumStr'] # "周一075"
```

## 字段映射表

### 胜平负
| API字段 | 含义 | 示例 |
|---------|------|------|
| `had.h` | 主胜赔率 | 1.22 |
| `had.d` | 平局赔率 | 5.00 |
| `had.a` | 客胜赔率 | 9.10 |
| `had.updateDate` / `had.updateTime` | 最后更新 | 2026-06-29 / 14:53:52 |

### 让球胜平负
| API字段 | 含义 | 示例 |
|---------|------|------|
| `hhad.goalLine` | 让球数 | -1 |
| `hhad.h` | 主队让球胜 | 1.69 |
| `hhad.d` | 让球平 | 4.05 |
| `hhad.a` | 客队受让胜 | 3.44 |

### 比分赔率
| 比分 | API键 | 示例 |
|:----:|:------|:----:|
| 1-0 | `crs.s01s00` | 7.20 |
| 2-0 | `crs.s02s00` | 5.50 |
| 2-1 | `crs.s02s01` | 7.25 |
| 3-0 | `crs.s03s00` | 6.80 |
| 3-1 | `crs.s03s01` | 7.00 |
| 4-0 | `crs.s04s00` | 15.00 |
| 0-0 | `crs.s00s00` | 16.00 |
| 1-1 | `crs.s01s01` | 10.00 |
| 0-1 | `crs.s00s01` | 25.00 |
| 0-2 | `crs.s00s02` | 70.00 |
| 5-0 | `crs.s05s00` | 30.00 |

公式：`s{h}g{s}a` → 例如 `s02s01` = 2-1

### 总进球
| API键 | 含义 |
|:------|:------|
| `ttg.s0` ~ `ttg.s7` | 0~7+球的赔率 |
| `ttg.s3f` | -1=受注, 0=未开 |

### 半全场
| API键 | 含义 | 示例 |
|:------|:------|:------|
| `hafu.hh` | 胜-胜 | 1.63 |
| `hafu.dd` | 平-平 | 8.10 |
| `hafu.dh` | 平-胜 | 4.10 |
| `hafu.aa` | 负-负 | 16.50 |

前缀：`h`=主胜, `d`=平, `a`=客胜。两个字母=半场+全场。

### 赛事信息
| API字段 | 含义 |
|---------|------|
| `homeTeamAbbName` | 主队简称 |
| `awayTeamAbbName` | 客队简称 |
| `homeTeamRank` | 主队排名 |
| `awayTeamRank` | 客队排名 |
| `matchDate` / `matchTime` | 比赛日期/时间 |
| `matchStatus` | 销售状态（Selling=在售） |
| `remark` | 场地信息 |
| `businessDate` | 比赛日（用于分组） |

### 注意事项
- ⚠️ `matchId` ≠ `mid`，匹配用户数据用 `matchNumStr`（如"周一075"）
- ⚠️ 部分`mid`字段为`None`，但比赛数据完整
- ✅ 赔率数据与竞彩网固定奖金页面完全一致

---

## 🔴 2026-10-11 更新：直连 567 的解法 + 全套端点

**打 webapi 吃 567 不是端点不存在，是缺 `Referer`**：加 `Referer: https://www.sporttery.cn/jc/jsq/zqspj/` + Chrome UA，并先预热 `https://www.sporttery.cn/`，则 `getMatchCalculatorV1` / `getFixedBonusV1` / `getMatchResultV1` 等全部 200（本地 python 即可，不需要 playwright）。

完整端点点清单、两套 ID 的参数口径、以及已知坑（`getResultHistoryV1` 默认只回 5 场、`getMatchTablesV2` 空、`getMatchPlayerV1` 的 `playerName` 为 null）**一律见 `📚知识库/数据源/API接口.md` 的「竞彩网」章节**，此处不重复。

- 「伤停信息不在API中」已过时：`getInjurySuspensionV1.qry` 与 `getFutureMatchesV1.qry`（战意线索）都在端点清单里；实测 2026-10-11 两场返回**空列表**，仍需与官方页「暂无数据」互相印证。
- 官方特征分析页（用户粘贴的那一页）含 API 拿不到的三样：**积分榜、射手姓名、8-10 场完整交锋**——它是权威源，API 是交叉源。
