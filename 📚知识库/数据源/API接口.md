# 🗺️ 数据源 — API接口 & 数据抓取

## 竞彩网（sporttery.cn）

### 🔑 直连配方（2026-10-11 打通，先看这段）

**症状**：`requests` / `urllib` 直接打 `webapi.sporttery.cn/gateway/...` 一律返回 **HTTP 567**（空 body）。
**病因**：**缺 `Referer` 与浏览器上下文**，不是端点不存在，也不是 IP 被封。
**解法（本地 python 即可，不需要 playwright）**：

```python
import urllib.request, json
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
REF = 'https://www.sporttery.cn/jc/jsq/zqspj/'

def api(url):
    # ① 先预热站点（同一进程同一次访问即可）
    urllib.request.urlopen(urllib.request.Request('https://www.sporttery.cn/',
        headers={'User-Agent': UA}), timeout=20).read()
    # ② 再打 webapi，带上 Referer
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Referer': REF, 'Accept': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=20).read().decode('utf-8'))
```

- ✅ 带 Referer 后：`getMatchCalculatorV1` 200 / 265KB、`getMatchResultV1` 200、`getTeamInfoV1` 200。
- ❌ 不带的后果：`getFixedBonusV1` 直接 567；harness 的 `web_fetch` 不带 Referer，所以只有个别 URL 恰好可用。
- ⚠️ **harness 的 `web_fetch` 会截断大 JSON**（`getMatchResultV1` 只回 5 条就是被截的），**必须落到本地脚本取数**。
- 公司机的等价路径是 `公司机_工程/采集数据/browser.py:85-104` 的 `fetch_api()`（playwright + chrome/msedge 通道 + `--no-proxy-server`）——本地已不需要它。

### 端点清单（从 `static.sporttery.cn/res_1_0/jcw/default/jc/zqzbComponent.js` 与 `zqbsComponent.js` 挖出）

| 用途 | 路径 |
|:--|:--|
| 赛程+全量赔率 | `/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c` |
| 固定奖金历史 | `/gateway/uniform/football/getFixedBonusV1.qry?clientCode=3001&matchId=<竞彩id>` |
| 球队近N场逐场 | `/gateway/uniform/football/team/getMatchResultV1.qry?gmTeamId=<id>&termLimits=10` |
| 球队信息 | `/gateway/uniform/football/team/getTeamInfoV1.qry?channel=c&gmTeamId=<id>` |
| 特征分析（主客拆分/近况/场均） | `/gateway/uniform/football/getMatchFeatureV1.qry` |
| 球员/射手 | `/gateway/uniform/football/getMatchPlayerV1.qry` |
| 历史交锋 | `/gateway/uniform/football/getResultHistoryV1.qry` |
| 积分榜 | `/gateway/uniform/football/getMatchTablesV2.qry` |
| 伤停 | `/gateway/uniform/football/getInjurySuspensionV1.qry` |
| 未来赛程（战意） | `/gateway/uniform/football/getFutureMatchesV1.qry` |
| 特征页头 | `/gateway/uniform/football/getMatchHeadV1.qry?source=web&matchId=<比赛id>` |
| 赛况 | `/gateway/uniform/fb/getMatchScoreV1.qry`、`/gateway/uniform/fb/getMatchEventV1.qry` |
| 直播统计 | `/gateway/uniform/football/matchlive/getPlayerStatisV1.qry`、`getTeamStatisV1.qry` |

### 🔴 参数口径（两套 ID 必须区分）

- `football/*` 这一族用 **`?source=web&sportteryMatchId=<竞彩id>`**；用 `matchId` 会返回空值。
- `getFixedBonusV1.qry` 参数必须**恰好** `clientCode=3001&matchId=<竞彩id>`：多给任何参数（`source=web` / `sportteryMatchId` / `clientCode=3002`）立刻 567 或 `errorCode 20013 前端编码错误`。
- `fb/getMatchScoreV1.qry`、`fb/getMatchEventV1.qry`、`getMatchTablesV2.qry` 用 `matchId` 也能出（值里带 `gmMatchId` / `wbsjMatchId` 两套 id）。
- ⚠️ `uniformHomeTeamId/uniformAwayTeamId` 与 `gmTeamId` **不是同一套 ID**。
- ⚠️ `teamMatchResult` 字段**不是主客标志**（实测整批恒为 `home`）；判主客必须**用队名匹配 `homeAbbCnName/awayAbbCnName`**（全称子串匹配会失败：沙特阿拉伯亚足 vs 沙特亚）。

### 🔴 已知坑

- `getResultHistoryV1` **默认只回 5 场**交锋（002 实际 8 场、003 实际 10 场）→ 只看 API 会得出**方向相反**的结论。
- `getMatchTablesV2` 返回空、`getMatchPlayerV1` 的 `playerName` 全为 `null` → **积分榜与射手姓名只能从官方页面复制**（用户粘贴的特征分析页有）。
- `getAnalysisV1` / `getMatchAnalysisV1` / `getMatchInfoV1` / `getMatchDetailV1` / `getHistoryMatchV1` / `getVersusHistoryV1` / `team/getTeamRankV1` / `league/getLeagueRankV1` **均不存在**（一律 `E0001`）；`getMatchFeatureV1.qry` 在无参时返回 `success:true, value:{}`。
- 比分口径：`sectionsNo999` = **home:away**。
- 官方特征分析页页脚写明「赛事数据统计进行至全场90分钟（含伤停补时阶段）结果」——即 **90 分钟口径的官方背书**。
- 比分盘 / 总进球盘的 `oddsHistory` 每档**只有 1 条记录**（与 calculator 同批时点）→ **读不到位移**，位移要另抓或靠用户粘贴多时点。

### 基础端点

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
