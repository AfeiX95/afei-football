# AFEI Football Brand Cover

阿飞·赛博聊球 的**固定品牌封面**：不含日期、场次、球队、比分，用于长期品牌展示。
一条命令出两张，全部中文由 Pillow 绘制（图像只负责氛围背景）。

## 用法

```bash
python -m pip install -r requirements.txt   # 只需 Pillow
python main.py
```

输出：

| 文件 | 尺寸 | 用途 |
|---|---|---|
| `output/afei_cover_3x4.png` | 1536 × 2048 | 竖版（小红书 / 公众号首图） |
| `output/afei_cover_16x9.png` | 1920 × 1080 | 横版（头条 / 视频号） |

不联网也能重渲：背景是本地资产，字体走系统字体。

## 目录

```
afei-brand-cover/
├── main.py              入口：读 theme.json，依次渲染竖版与横版
├── requirements.txt     Pillow
├── config/theme.json    文案、配色、字号、发光参数（改配色只动这里）
├── assets/background/   portrait_bg.png / landscape_bg.png（图像模型生成的**无字**球场）
├── src/
│   ├── typography.py    字体加载、发光文字、斜切标题
│   ├── hud.py           HUD 面板、折线、柱状、迷你战术板、刻度
│   ├── stadium.py       背景加载/压暗/暗角、全息足球
│   ├── portrait.py      竖版版面
│   └── landscape.py     横版版面（独立排版，不是竖版裁切）
└── output/              成品 PNG
```

## 分层

1. **背景层**：`assets/background/*.png`（可用任意无字球场图替换，换背景不影响文字与品牌识别）
2. **压暗层**：上下压黑 + 暗角，保证文字对比度
3. **HUD 层**：战术板、折线、柱状、刻度（纯代码绘制）
4. **主体层**：全息足球（球面明暗 + 荧光缝线 + 外发光）
5. **文字层**：品牌、口号、主标题（斜切 + 发光）、标签、底部三栏目

## 固定文案（在 config/theme.json 里改）

- 品牌：`阿飞·赛博聊球` / `用数据拆解比赛`
- 主标题：`足球赛事` `前瞻`
- 口号：`数据不会说谎，但人会。` `—— 阿飞`
- 标签：`数据拆解 / 赛况分析 / 赛果预测 / 风险提示`
- 底部：`每日更新` `专业视角` `理性分析`

**本文件不含任何日期与场次。** 需要带日期/场次的版本用另一条线：`scripts/cover/overlay.py`（在给定底图上叠字，不动底图像素）。

## 设计约束

- 中文全部由 Pillow 渲染，图像模型不负责最终排字
- 两张图不是同一版缩放：横版重新排（左侧标题、右侧球与面板、底部三栏目）
- 安全边距：竖版左右 ≥ 96px、横版 ≥ 88px；文字不压角标与面板
- 输出 sRGB PNG（Pillow 直存 PNG，无 ICC 嵌入）
- 改配色：只改 `config/theme.json` 的 `colors`，重跑 `python main.py`

## 已知边界

- 队徽不使用（商标风险）；需要时把授权素材放 `assets/icons/` 自行合成
- 足球是代码绘制的风格化球体，不是实拍照片；要更真实可替换成去掉文字的实拍球素材
