# 小红书信息卡生成代码包

四个脚本 + 一条命令，从「内部报告 md」一路出到「卡片 PNG + 封面 PNG」。

## 文件

| 文件 | 作用 |
|---|---|
| `mk_sun_cards.py` | 从 `20261025_周日29场_内部分析报告.md` 解析 4 场，生成 `cards.json`（含 radar/value/intel/h2h_detail/heat/model） |
| `xhs_card_d.py` | 卡片渲染器：cards.json → 2160×2880 PNG（赛博底色、五套皮肤、六维条、雷达、热力、情报双栏、矛盾、看点） |
| `overlay.py` | 封面叠字：在你给的底图上加日期签 + 赛程面板（底图像素不动） |
| `xhs_riskcheck.py` | 合规自检：`scan_form`（形态）/ `scan_caption`（文案） |

## 一、生成 cards.json

```bash
python -X utf8 mk_sun_cards.py \
  --report "📝文章/20261025/20261025_周日29场_内部分析报告.md" \
  --out state/tmp/cards_sun4.json \
  --only "周日002,周日003,周日004,周日026"
```

`--only` 不写就是全量解析；报告必须是 `slate_report.py` 生成的格式（`### 周日002 日乙 新潟天鹅 vs 仙台七夕　13:00 开赛` + `首选 **客** 53.8% · 1-2` + `综合 1.22 + 1.93 = 3.15；信心 69/100（B` + `近期 主 5 场 …`）。

## 二、渲染卡片

```bash
export XHS_HTML_TMP=<一个已存在的临时目录>   # Windows: $env:XHS_HTML_TMP="I:\阿飞说球\state\tmp\xhs_html_sun"
export CARD_FS=1.15                          # 字号倍率（1.0 原始）
# 可选：export CARD_SKIN=neon|cyan|violet|amber|ice  不设则按日期数字 %5 轮换
python -X utf8 xhs_card_d.py --input cards.json --out <输出目录>
```

> Chrome headless 在受限沙箱里起不来（mojo 0x5），必须能正常启动 `chrome.exe` 的环境跑。

## 三、出封面

```bash
python -X utf8 overlay.py \
  --base assets/brand/base_3x4.png --out <输出>/00_封面.png \
  --ratio 3:4 --date 10.25 --weekday 周日 --rows 4 --font-scale 1.4 --retag \
  --matches "13:00|日乙|新潟天鹅|仙台七夕;15:00|日职|东京FC|水户蜀葵;15:00|日职|川崎前锋|冈山绿雉;03:45|意甲|乌迪内斯|AC米兰"
```

`--matches` 格式固定 `时间|联赛|主队|客队`，多条用 `;` 分隔。`--retag` 把底图上那条「赛果预测」遮掉改成「数据整理」。

## 四、自检

```bash
python -X utf8 -c "import json,io,sys;sys.path.insert(0,'.');import xhs_riskcheck as R;d=json.load(io.open('cards.json',encoding='utf-8'));print(R.scan_form(d))"
```

`scan_form` 里 fatal 必须为 0；热力格与三项概率条只算 warn（比分热力是用户明确保留项）。

## 卡片数据结构（cards.json 里每场一项）

```json
{
  "no": "周日002", "league": "日乙", "kick": "13:00",
  "home": "新潟天鹅", "away": "仙台七夕",
  "value": {"home_text": "1128万欧", "away_text": "1048万欧", "home_m": 1128, "away_m": 1048, "ratio": "0.9×"},
  "form": {"home": {"pj": 1.2, "sj": 1.8, "gf": 6, "ga": 9, "l5": "", "ha": "近 5 场"},
           "away": {"pj": 1.6, "sj": 0.4, "gf": 8, "ga": 2, "l5": "", "ha": "近 5 场"},
           "h2h": {"n": 5, "avg_goals": "2.40"}, "h2h_short": "交锋 5 场 · 场均 2.40 球 · 平 40%"},
  "h2h_detail": {"record": "近 5 次 2胜2平1负", "scores": ["2-1","0-0","1-0"], "note": "本季两回合…"},
  "radar": {"dims": ["进攻","中场控制","防守","近期状态","主客场","进球稳定"],
            "home": [54,52,49,37,44,86], "away": [66,76,86,76,69,77]},
  "intel": {"common": ["场均进失 …", "伤停 0 人", "交锋 5 场 · 场均 2.40 球"]},
  "intel2": {"home": {"good": ["…","…"], "bad": ["…"]}, "away": {"good": ["…"], "bad": ["…"]}},
  "model": {"grid": [[...5x5 百分比...]], "wdl": [32.1, 25.3, 42.6]},
  "narr": "【破防主队 vs 铁血客场】…", "point": "看点一句话"
}
```

`heat: false` 可关掉热力格；`pie_mode: "none"` 不生成功率图。

## 已知边界

- 雷达必须给 `radar.dims` 且 `home/away` 长度与 dims 一致，否则整块不渲染（防用假数据凑图）。
- 身价块只在 `value.home_m`/`away_m` 都有值时才画。
- `模型三向(prob)`、`信心分` 这类内部口径**不进公开卡面**，只在 cards.json 里留着给自检。
