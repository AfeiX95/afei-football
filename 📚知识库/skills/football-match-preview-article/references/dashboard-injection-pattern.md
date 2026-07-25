# 仪表盘Edge+凯利注入模式

## When to Use
- 需要将v4.1 Edge+凯利模块注入智能搜索版仪表盘
- 新增球队到TEAM_DB（仪表盘搜索不到时）

## 注入流程

### Step 1: 添加CSS
在`</style>`前插入Edge/Kelly专用样式：
- `.edge-bar` — Edge进度条
- `.cyber-kelly-wrap` — 凯利仓位容器
- `.signal-box` / `.signal-strong` / `.signal-medium` / `.signal-none` — 信号徽章
- `.odds-form` — 手动赔率输入表单

### Step 2: 添加HTML卡片
在`<!-- 10. 情景 -->`之后、`<!-- 11. 综合结论 -->`之前插入：
```html
<div class="col-span-6 card"><h3>📐 Edge价值信号（v4.1）</h3><div id="edgeDisplay"></div></div>
<div class="col-span-6 card"><h3>💰 凯利仓位建议（v4.1）</h3><div id="kellyDisplay"></div></div>
```

### Step 3: 添加手动赔率输入
在盘口卡片的trapDesc div后添加：
```html
<button onclick="toggleOddsForm()">✏️ 手动输入赔率</button>
<div class="odds-form" id="oddsForm">
  <div><label>主胜赔率</label><input id="mktOddsH" type="number" step="0.01"></div>
  <div><label>平局赔率</label><input id="mktOddsD" type="number" step="0.01"></div>
  <div><label>客胜赔率</label><input id="mktOddsA" type="number" step="0.01"></div>
</div>
```

### Step 4: 添加JS函数
1. `toggleOddsForm()` — 切换赔率表单显隐
2. `renderEdgeKelly(h, a, hl, al, base, brandPremium)` — 核心渲染函数
   - 优先使用手动输入赔率，否则用品牌溢价估算
   - Edge = P_model - P_market
   - Kelly = (bp-q)/b × 0.5（半凯利，上限25%）
   - 信号分级：≥10pp强价值 / ≥5pp中价值 / ≥3pp轻价值 / <3pp无价值
3. 在`renderCharts()`的`renderFullConclusion()`调用后追加`renderEdgeKelly()`调用

### Step 5: 添加新球队到TEAM_DB
在`_default`之前插入新球队条目：
```javascript
south_africa:{name:'南非',flag:'🇿🇦',cnKey:'南非',enKey:'southafrica',fifa:58,worth:'€0.25亿',form:'...',gScored:0.9,gConceded:1.1,possession:42,attack:48,midfield:46,defense:44,morale:70,worthScore:10}
```

## parseInput增强（处理竞彩网格式）
竞彩网格式：`周日073 世界杯 06-29 03:00 [世界杯2]南非VS加拿大[世界杯2]`
必须先剥离元数据再匹配VS：
```javascript
cleaned = cleaned.replace(/周[日一二三四五六]\d{3}/g,'');  // 竞彩编号
cleaned = cleaned.replace(/\s*世界杯\s*/g,' ');              // 赛事
cleaned = cleaned.replace(/\s*\d{2}-\d{2}\s+\d{2}:\d{2}\s*/g,' '); // 时间
cleaned = cleaned.replace(/\[.*?\]/g,'');                    // [排名]标签
```

## 赛博风格终极预测
渲染函数`renderFullConclusion`输出赛博朋克风格：
- 金色渐变边框+暗黑背景
- 比分3rem金色大字+国旗
- 四维核心指标卡片（红/绿/蓝/金）
- 八维因子4列网格+hover高亮
- Edge进度条+信号徽章
- 凯利仓位渐变进度条
- 终审判决+底部签名"数据不会说谎，但人会"

## Pitfalls
- ⚠️ TEAM_DB没有的球队会导致搜索失败→必须先添加再测试
- ⚠️ parseInput的正则顺序很重要：先剥离元数据再匹配VS，否则[世界杯2]南非无法解析
- ⚠️ Edge计算依赖市场赔率→手动输入更精确，品牌溢价估算有误差
