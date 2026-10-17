# -*- coding: utf-8 -*-
"""追加两条 open_items：标题格式待拍板 + 定时发布核对。"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = Path(r"I:\阿飞说球\state\model-state.json")
d = json.loads(p.read_text(encoding="utf-8"))
oi = d["open_items"]
texts = {x.get("text", "")[:30] for x in oi}

add = [
    {
        "type": "待拍板",
        "text": (
            "头条标题格式 A/B 实测待拍板（2026-10-17 十条后台数据）：R38c 格式 "
            "`{M月D日}赛事前瞻:{主队}VS{客队},{钩子}` 头三篇 CTR 3.25%/2.25%/1.48%，"
            "同窗口旧格式六篇 7.20%–10.23%。差异点集中在①钩子可验证性（「分歧超 20 个点」是内部指标）"
            "②`10月17日赛事前瞻:` 占 9 字＝30 字闸的 30%，而站内本就写着日期。"
            "待定：日期前缀改 `10/17` 短格式还是直接去掉、「赛事前瞻」是否移入正文。数据见 "
            "`📚知识库/公司工程/硬指标与运营实证.md` §C2，规则侧已在 R38c 加⚠️实测注记（未改规则）。"
        ),
    },
    {
        "type": "流程",
        "text": (
            "定时发布核对（2026-10-17 事故）：10-18 04:48 定时的《贝蒂斯vs巴萨》稿晚于两场开赛"
            "（026 = 00:30、029 = 03:00）→ 需用户改到 10-17 当晚 20:00–23:00 间。"
            "规则已写进 R39：定时须早于最早一场开赛 ≥3 小时、凌晨场次前一晚发、同日多篇间隔 ≥2 小时"
            "（13:29/13:30 连发两篇互抢曝光，展现 4,271 vs 881）。"
        ),
    },
]
n = 0
for item in add:
    if item["text"][:30] not in texts:
        oi.append(item)
        n += 1
d["counters"]["open_items"] = len(oi)
p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"追加 {n} 条，open_items 现有 {len(oi)} 条")
