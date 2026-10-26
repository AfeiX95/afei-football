# AFEI Football Cover System v1.0

用一份已校验的比赛 JSON，生成三种封面（每日总览 / 单场深度 / 多场矩阵），每套同时出 3:4 与 16:9 两个版本。

> 设计纪律：**渲染器只读已校验 JSON**——不搜索、不预测、不补数据。所有中文由程序绘制（不经图像模型），队徽只从合法资源库读取，缺失时显示「缩写 + 队伍配色」，绝不伪造官方徽章。

## 目录

```
scripts/cover/
├── main.py                 # CLI 入口（--type / --input / --match / --ratio / --batch / --check）
├── theme.py                # 配色 COLORS、字体、星期/日期工具、队伍配色哈希
├── art.py                  # SVG 球场（透视草皮 + 看台灯点）、全息球、HUD 四角刻度
├── components.py           # badge / panel / kpi / stat_pair / prob_bar / record_chips / footer / disclaimer
├── render.py               # Chrome headless 截图 + Pillow 缩略图
├── checks.py               # 9 项质量自检
├── templates/
│   ├── daily.py            # A 每日赛事总览（8～20 场）
│   ├── single.py           # B 单场深度前瞻（1 场）
│   └── multi.py            # C 多场矩阵前瞻（2～6 场）
└── config/
    ├── theme.json          # 配色与品牌（可覆盖）
    └── sample_matches.json # 12 场示例输入（2026-10-23 周五档）
```

## 输入 JSON

```json
{
  "date": "2026-10-23",
  "timezone": "Asia/Shanghai",
  "brand": "阿飞 · 赛博聊球",
  "subtitle": "用数据拆解比赛",
  "matches": [
    {
      "league": "德甲",
      "kickoff": "02:30",
      "round": 9,
      "home": "斯图加特", "away": "门兴",
      "home_en": "STUTTGART", "away_en": "GLADBACH",
      "home_record": "3胜1平1负", "away_record": "1胜1平3负",
      "home_goals_for": 2.2, "home_goals_against": 0.7,
      "away_goals_for": 1.9, "away_goals_against": 2.2,
      "h2h": {"n": 5, "avg_goals": 2.6, "note": "..."},
      "probs": {"home": 71.2, "draw": 16.9, "away": 11.9},
      "prob_source": "模型概率",
      "pick": {"dir": "主胜", "score_ref": "2-0、1-0", "score_risk": "1-1", "confidence": "中高"},
      "observations": ["门兴六轮零分垫底", "斯图加特两天前刚踢完欧战"]
    }
  ]
}
```

`probs` 必须标注 `prob_source`（模型概率 / 市场隐含 / 其他），**同一张图不得混用口径**；缺字段就留空，不自动补。

## 用法

```powershell
# 自动选模板（1 场→single，2~6 场→multi，其余→daily）
python -X utf8 scripts/cover/main.py --type auto --input scripts/cover/config/sample_matches.json --ratio 3:4

# 指定模板 / 指定某一场
python -X utf8 scripts/cover/main.py --type single --input ... --match 5 --ratio 16:9

# 一次出全部（三模板 × 两比例）
python -X utf8 scripts/cover/main.py --batch --input scripts/cover/config/sample_matches.json --out state/tmp/cover_sys
```

输出命名：`AFEI_<daily|single|multi>_<yyyyMMdd>[_<home>_vs_<away>]_<3x4|16x9>.png`，尺寸 2160×2880 / 3840×2160（`--scale` 可调）。

## 质量自检（--check，默认开启）

日期与星期一致、场次数、联赛去重、必填字段（home/away/kickoff）、概率和≠100%、概率口径混用、占位符（待补/TBD/??）、输出尺寸、文字是否越安全区。

## 依赖

Python 3.11+、Chrome（headless 截图）、Pillow。见 `requirements.txt`。

## 队徽（真实徽标）

```powershell
python -X utf8 scripts/cover/fetch_logos.py          # 补缺
python -X utf8 scripts/cover/fetch_logos.py --force  # 全量重下
```

- 取英文维基条目主图（330px PNG），落到 `scripts/cover/assets/logos/<中文名>.png`，映射写 `scripts/cover/config/logos.json`。
- `components.badge()` 优先用本地徽标；**没有的队仍降级为「缩写 + 队伍配色」，绝不画假徽章**。
- 要加新队：在 `fetch_logos.py` 的 `TEAMS` 里加一行 `中文名 → 英文维基条目`，再跑一次。
- 渲染需要 `--allow-file-access-from-files`（`render.py` 已加），否则本地图片会被 Chrome 拦掉。
- 队徽是俱乐部商标：内部与评论性使用，公开商用请自行确认授权。

## 背景图（照片级质感）

默认用 SVG 画球场；想要实拍质感，就在输入 JSON 顶层加 `background`，渲染器会把图铺到画布上、再用双向渐隐压暗到可读：

```json
"background": {
  "3x4":  "state/tmp/gen/stadium_v1.png",
  "16x9": "state/tmp/gen/stadium_wide.png"
}
```

- 路径相对**仓库根**（也可绝对路径）；`&` 会转成 `&quot;` 以适配 `file://`。
- 缺省或空串自动回落 SVG 球场；有背景图时 daily 不画全息球（否则球会飘在天上）。
- 3:4 用竖构图（球门后方视角最佳），16:9 用角旗/边线全景。

### 本地生成背景（Qwen-Image-2.1-Turbo，离线）

```powershell
$cli="D:\ImageAITurboU\stable-diffusion\sd-cli.exe"
& $cli --diffusion-model "D:\ImageAITurboU\models\Qwen-Image-2.1-Turbo-AD-Q4_K.gguf" `
  --vae "D:\ImageAITurboU\models\qwen_image_2.1_vae_bf16.safetensors" `
  --llm "D:\ImageAITurboU\models\Qwen-Image-2.1-Turbo-Uncensored-AD-Q3_K.gguf" `
  --width 1024 --height 1536 --cfg-scale 1.0 --sampling-method euler `
  --sigmas qwen-image-2.1-turbo --model-args "qwen_image_2_1_prefix_cache_type=q8_0" `
  --offload-to-cpu `
  -p "photorealistic empty football stadium at night, camera behind the goal, bright floodlights, mowing stripes, volumetric haze, cinematic, no people, no text, no logos" `
  --negative-prompt "text, letters, watermark, logo, people, ui, cartoon" `
  --seed 20261023 -o state/tmp/gen/stadium_v1.png
```

- `--sigmas` 预设已含步数，**不要再传 `--steps`**；文生图不要带 `--llm_vision`（白占显存）。
- 8GB 显存实测：1024×1536 ≈ 8 分钟，1536×864 ≈ 10 分钟。
- 一次生成、多日复用：把成图放进 `assets/backgrounds/` 再引用即可。

## 已知限制

- 无背景图时球场是 SVG 矢量绘制，不是照片级实拍；`background` 可换成自备实拍/生成图。
- 队徽为「缩写 + 配色」占位；接入真实徽标需自备授权素材放进 `assets/logos/`。
- 队徽为「缩写 + 配色」占位；接入真实徽标需自备授权素材放进 `assets/logos/`。
- 中文依赖系统字体（微软雅黑 / Noto Sans SC），换机器需确认字形覆盖。
