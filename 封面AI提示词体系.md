# 阿飞·赛博聊球 — 封面AI提示词体系

> 一套"填空即用"的封面生成提示词，覆盖所有文章类型。
> 适配 Midjourney / DALL-E 3 / 即梦 / 文心一言 等主流生图工具。

---

## 一、核心风格定义（品牌视觉基调）

所有封面统一在以下风格框架内变化，不跳出这个基调：

| 维度 | 设定 |
|------|------|
| 风格 | 赛博体育数据风 — 科技感+足球+数据可视化融合 |
| 色调 | 暗色底 + 霓虹高光（主色：电光蓝#00d4ff / 霓虹紫#9b59b6 / 荧光绿#39ff14） |
| 光照 | 赛博朋克霓虹光效，侧逆光，发光描边 |
| 构图 | 主体居中或对角线分割，数据元素（网格/数字流/雷达图）作为背景纹理 |
| 质感 | 玻璃质感/金属光泽/发光线条，高对比度 |
| 字体 | 无预留文字空间（文字后期叠加），画面干净无字 |
| 气氛 | 未来感、数据驱动、冷静分析，非热血/激情向 |

**一句话风格锚点：**
> 赛博朋克风格足球数据分析封面，暗色背景，霓虹蓝紫光效，数据网格和发光线条环绕足球或球场，高对比度，未来科技感，无文字。

---

## 二、填空式提示词模板

### 模板A：赛前前瞻 · 双队对决（最常用）

适用于：单场比赛的赛前分析，如日职/法甲/意甲前瞻

```
Prompt:
Cyberpunk football match preview cover, [主队] vs [客队], 
silhouette of two football players facing each other, 
neon [主色1] and [主色2] lighting from both sides, 
dark background with holographic data grid, 
glowing stats numbers floating in the air, 
futuristic stadium silhouette in background, 
cinematic lighting, high contrast, unreal engine 5 style, 
no text, no letters, no words --ar 16:9 --v 6.1 --style raw
```

**填表参考：**

| 变量 | 选择 | 示例 |
|------|------|------|
| [主队] | 球队名称 | Machida Zelvia |
| [客队] | 球队名称 | Urawa Reds |
| [主色1] | 主队代表色 | lime green |
| [主色2] | 客队代表色 | deep red |

---

### 模板B：赛前前瞻 · 球星聚焦

适用于：以某位关键球员为核心的比赛分析（如"头号射手缺阵"类话题）

```
Prompt:
Cyberpunk sports portrait of [球员名], [球队] star player,
wearing futuristic neon-lit [球队色] jersey,
intense focused expression, holographic stat data surrounding the figure,
glowing [主色] light from below, dark cyberpunk city background,
data streams and numbers floating, volumetric lighting,
cinematic portrait photography style, hyper-realistic,
no text, no letters, no words --ar 16:9 --v 6.1 --style raw
```

**填表参考：**

| 变量 | 说明 | 示例 |
|------|------|------|
| [球员名] | 球员英文名全称 | Yuki Soma |
| [球队] | 所属球队 | Machida Zelvia |
| [球队色] | 球队主色 | lime green |
| [主色] | 氛围主色 | cyan |

---

### 模板C：三场串烧 / 多场盘点

适用于：多场比赛组合分析，如芬超+瑞超+意甲串烧

```
Prompt:
Cyberpunk sports data dashboard cover, 
[数字] football matches highlighted on a futuristic screen,
split-screen layout with [数字] match scenes,
each panel glowing in different neon colors,
holographic stats and comparison data floating,
dark control room aesthetic, monitor screens with match footage,
grid overlay, blue and purple ambient lighting,
futuristic sports broadcast style,
no text, no letters, no words --ar 16:9 --v 6.1 --style raw
```

**填表参考：**

| 变量 | 说明 | 示例 |
|------|------|------|
| [数字] | 比赛场数（用英文） | three |

---

### 模板D：赛后复盘

适用于：比赛结束后出复盘文章

```
Prompt:
Cyberpunk football match recap cover, 
dramatic moment on a neon-lit pitch,
long exposure light trails from players running,
scoreboard hologram floating above the stadium,
dark rainy night atmosphere, cyan and magenta lighting,
stadium floodlights cutting through fog,
motion blur, epic cinematic timing,
sports photography style, high drama,
no text, no letters, no words --ar 16:9 --v 6.1 --style raw
```

---

### 模板E：数据深度分析 / 赛博数据专题

适用于：以数据为核心卖点的文章（如角球分析、泊松模型专题）

```
Prompt:
Cyberpunk data visualization cover,
3D holographic football with digital data rings orbiting around it,
glowing statistics charts and line graphs in neon blue and purple,
dark server room background with laser light beams,
futuristic hacking interface aesthetic,
floating numbers and binary code data stream,
octane render, unreal engine 5, volumetric glow,
no text, no letters, no words --ar 16:9 --v 6.1 --style raw
```

---

## 三、单图场景提示词（配图关键词用）

每篇文章文末需要6张配图搜索关键词，下面是"封面AI提示词"版本的替代方案——用生图提示词替代搜图关键词，每篇直接从以下池子里选6个。

### 场景1：体育场全景空镜

```
Prompt:
Aerial view of [球场名] stadium at night, 
floodlights on, pitch perfectly green,
cyberpunk style neon light strips along stadium roof，
dark blue sky, long exposure, architectural photography,
cinematic wide shot, unreal engine 5,
no text, no letters, no words --ar 16:9

# 示例：Machida Stadium Tokyo, aerial night view
```

### 场景2：球员特写

```
Prompt:
Close-up of a football player in [球队色] jersey,
sweat on face, intense eyes looking forward,
cyberpunk neon rim lighting on the side of the face,
dark background with subtle data grid overlay,
sports portrait photography, shallow depth of field,
canon 85mm f1.2, cinematic lighting,
no text, no letters, no words --ar 16:9
```

### 场景3：教练/主帅

```
Prompt:
[教练名] football manager portrait, 
standing on the sideline in suit and tie,
neon city lights reflecting on stadium glass behind him,
cyberpunk style cold blue and purple lighting,
arms crossed or pointing, serious expression,
editorial sports photography style,
no text, no letters, no words --ar 4:3
```

### 场景4：积分榜/排名视觉化

```
Prompt:
Futuristic sports league standings holographic display,
[联赛名] league table projected on glass panels,
neon glowing ranking numbers, top teams highlighted in green,
dark high-tech control room background,
data dashboard aesthetic, blue holographic light,
futuristic UI interface style,
no text, no letters, no words --ar 16:9
```

### 场景5：历史交锋/对抗

```
Prompt:
Cyberpunk head-to-head matchup visualization,
two team crests or silhouettes facing each other,
neon red vs neon blue energy clash in the middle,
historical data timeline glowing below,
dark night stadium background, sparks and light beams,
futuristic vs battle aesthetic,
no text, no letters, no words --ar 16:9
```

### 场景6：夺冠/决赛/奖杯

```
Prompt:
Football trophy glowing with neon blue light,
floating on a dark cyberpunk pedestal,
confetti falling in slow motion under stadium lights,
dramatic cinematic lighting, rays of light from above,
premium product photography, shallow depth of field,
no text, no letters, no words --ar 16:9
```

---

## 四、不同工具的适配说明

### Midjourney（推荐，效果最好）

追加参数说明：
- `--ar 16:9` — 头条封面标准比例
- `--v 6.1` — 最新版本，人像/场景真实度最高
- `--style raw` — 减少MJ的过度美化，保留摄影感
- `--s 250` — 风格化值，250适中，需要更艺术感可提到500
- `--stylize 250` — 同上，新版本参数名

**单图成本建议：** 每篇文章选1张做主封面即可，不用每张配图都生。
**一次生成量：** 每张Prompt跑4张variations，挑1张最合适的。

### DALL-E 3

直接用上面Prompt去掉尾部参数即可。DALL-E 3对文字理解更强，但赛博朋克风格不如MJ纯粹。建议去掉"no text"约束，DALL-E 3自动不写字。

### 即梦 / 文心一言（国内工具）

- 把Prompt翻译成中文，加"超写实，8k，电影感"
- 国内工具对赛博朋克风格支持普遍不错
- 示例中文Prompt："赛博朋克风格足球比赛封面，暗蓝色背景，霓虹光线，两个球员剪影对峙，数据网格背景，未来科技感，超高清，8k"

---

## 五、封面设计实操指南

### 头条封面技术规格

| 项目 | 要求 |
|------|------|
| 尺寸 | 建议 1280×720px（头条自动裁切） |
| 比例 | 16:9 |
| 文件大小 | ≤5MB |
| 格式 | JPG 或 PNG |
| 文字安全区 | 画面中央70%区域放主体，边缘30%预留裁剪 |

### 文字叠加建议

生图AI生成的是纯画面（无文字），文字用头条自带的编辑功能叠加：

**标题叠加规范：**
- 字体：粗体无衬线（推荐思源黑体 Bold）
- 字号：主标题 ≥60px，副标题 ≥30px
- 位置：底部1/3处或居左对齐
- 颜色：白色为主，用描边或投影保证可读性
- 文字量：不超过画面面积的15%

### 不同文章类型的封面方向

| 文章类型 | 推荐模板 | 色调方向 | 主体 |
|---------|---------|---------|------|
| 日职前瞻 | 模板A 双队对决 | 霓虹蓝紫 | 球员剪影+球场 |
| 五大联赛前瞻 | 模板B 球星聚焦 | 球队主色 | 核心球员 |
| 三场串烧 | 模板C 数据面板 | 蓝紫绿 | 分屏/多画面 |
| 法国杯/决赛 | 模板D/模板6 奖杯 | 金+蓝 | 奖杯/决胜瞬间 |
| 赛后复盘 | 模板D 赛后场景 | 暗蓝+红 | 比赛瞬间 |
| 数据专题 | 模板E 数据可视化 | 蓝+荧光绿 | 3D足球+数据环 |

### 快速执行流程

1. 判断文章类型 → 选对应模板
2. 填入球队/球员变量名
3. 查球队主色（第6节色表）
4. 跑Midjourney，4张variations
5. 选最合适的一张 → 下载
6. 头条后台叠加标题文字 → 发布

---

## 六、常用球队配色速查表

### 日职/J联赛

| 球队 | 主色 | 英文色值 |
|------|------|---------|
| 町田泽维 | 荧光绿 | lime green / #7fff00 |
| 浦和红钻 | 深红 | deep red / #8b0000 |
| 广岛三箭 | 紫 | purple / #800080 |
| 神户胜利船 | 深红+黑 | crimson + black |
| 川崎前锋 | 电光蓝 | electric blue / #0000ff |
| 横滨水手 | 蓝+白 | navy blue + white |
| 鹿岛鹿角 | 酒红 | burgundy / #800020 |

### 五大联赛常用

| 球队 | 主色 | 英文色值 |
|------|------|---------|
| 朗斯 | 红+黄 | blood red + gold |
| 尼斯 | 红+黑 | red + black |
| 佛罗伦萨 | 紫 | violet / #8b00ff |
| 亚特兰大 | 蓝黑 | blue + black |
| 佐加顿斯 | 深蓝+红 | navy blue + red |
| 赫尔辛基 | 蓝+白 | royal blue + white |

### 通用配色原则

- 主队色作为主光源 → 客队色作为辅光源，形成左右对撞
- 单队文章：球队单色 + 霓虹蓝作为环境光
- 决赛/杯赛：金色 + 两队色的混合
- 串烧文章：多用霓虹蓝紫（中性色，不偏袒任何一队）

---

## 七、进阶技巧

### 控制人物面部相似度

Midjourney生成具体球员时，用"参考图"模式：
```
[prompt文字] --cref [球员照片URL] --cw 50
```
- `--cw 0`：只参考面部特征，衣服/姿势不限
- `--cw 100`：完全参考，适合直接复刻

### 球队队徽植入

```
[prompt] --sref [队徽图片URL] [队徽图片URL]
```
将队徽的配色和图形特征融入画面，不直接贴logo，但整体色调更像该队风格。

### 批量生成不同色调

同一个Prompt改最后一行形容词即可：
- `cyberpunk blue neon atmosphere` — 蓝调（串烧/中立）
- `cyberpunk red and black atmosphere` — 红黑调（浦和/曼联）
- `cyberpunk purple neon atmosphere` — 紫调（佛罗伦萨/广岛）
- `cyberpunk gold and blue atmosphere` — 金蓝调（决赛/杯赛）

---

## 八、应急方案

### 没有Midjourney怎么办

用即梦（国内可用）+ 中文Prompt替代：

> 赛博朋克风格足球分析封面，深色背景，霓虹蓝色荧光，
> [主队]对阵[客队]，数据网格浮空，两个球员剪影对峙，
> 未来科技感，电影级光影，超写实，8k画质，无文字

### 时间紧迫怎么办

**3分钟出图法：**
1. 从素材库挑一张球场全景图（Getty Images搜"stadium night aerial"）
2. 头条编辑器里用滤镜调成冷蓝调+"锐化"
3. 叠加标题文字 → 发布

### 没有生图工具怎么办

从每篇文章文末的6张配图关键词中选第1张（体育场全景），
在Getty Images/懂球帝图库直接下载使用，同样符合头条封面标准。

---

> 最后提醒：封面决定点击率的30%，标题决定70%。
> 好的封面不能拯救差的标题，但差的封面会拖累好的标题。
> 优先保证标题质量，封面按模板填空即可。
