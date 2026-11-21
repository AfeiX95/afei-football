# -*- coding: utf-8 -*-
"""20261122 批次专属工具：用模型真实输出覆盖 v3.2 第九块「50 元以内方案」。

为什么需要：build_internal_report.py 的 ZQ 字典按日期硬编码，20261122 走通用兜底 →
方案 A 的方向位显示「选 —」。项目支持 `state/intel/<date>/_plan_<date>.json` 覆盖，
这里据 `_model_v3_<date>.json` 的融合三向与报告第八块的把握分层，生成方向完整、
金额精确核算（单注 2 元、总额 ≤50 元）的方案，不编造方向。

方向规则：取 three_c 最高格；最高与次高差 <5pp 时双选且不用强词（R61）。
运行：python -X utf8 "I:/阿飞说球/📝文章/20261122/_工具/build_plan.py"
"""
import json, re
from pathlib import Path

ROOT = Path(r"I:\阿飞说球")
BASE = ROOT / "📝文章" / "20261122"
INTEL = ROOT / "state" / "intel" / "20261122"
DAY = "20261122"
REPORT = BASE / f"{DAY}_周日16场_内部分析报告.md"


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


model = jload(INTEL / f"_model_v3_{DAY}.json")
text = REPORT.read_text(encoding="utf-8")

tier_rank = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
tiers = {}
for key in ("S", "A", "B", "C", "D"):
    m = re.search(r"-\s*" + key + r"\s[^：\n]*：([^\n]+)", text)
    if not m:
        continue
    for no in re.findall(r"\b(\d{3})\b", m.group(1)):
        if no in model:
            tiers[no] = key

if not tiers:
    raise SystemExit("报告第八块没解析到把握分层，先生成报告再跑本工具")

core = [n for n, t in tiers.items() if t in ("S", "A", "B")]
cautious = [n for n, t in tiers.items() if t == "C"]
skip = [n for n, t in tiers.items() if t == "D"]
ranked = sorted(core + cautious, key=lambda n: (tier_rank[tiers[n]], -max(model[n]["three_fused"]), n))


def name_of(no):
    m = re.search(r"^### " + no + r"\s([^｜]+)｜([^｜]+)｜", text, flags=re.M)
    if m:
        return m.group(2).strip().replace(" vs ", "–")
    return no


def direction(no):
    tc = model[no]["three_fused"]
    order = sorted([(tc[0], "主胜"), (tc[1], "平局"), (tc[2], "客胜")], reverse=True)
    if order[0][0] - order[1][0] < 0.05:
        return f"{order[0][1]}/{order[1][1]}（双选，分歧不足 5pp 不用强词）", 2
    return order[0][1], 1


def scores(no):
    """从报告第五块的「比分前六（λ_C）」取前三格；取不到就返回空，绝不编造。"""
    sec = re.search(r"^### " + no + r"[\s\S]*?(?=^### |\Z)", text, flags=re.M)
    if sec:
        m = re.search(r"- 比分前六（λ_C）：([^\n]+)", sec.group(0))
        if m:
            got = re.findall(r"\b(\d+-\d+)\b", m.group(1))[:3]
            if len(got) == 3:
                return got
    return []


lines = [
    "> 口径：竞彩 90 分钟常规时间，单注 2 元，总预算硬上限 50 元；仅作内部数据观察与仓位演练，临场首发/核心伤停异动自动熔断。",
    "> 本块由 `📝文章/20261122/_工具/build_plan.py` 依据 `_model_v3_20261122.json` 的融合三向与本报告第八块把握分层生成；",
    "> 方向取三向最高格，最高与次高差 <5pp 时双选且不用强词（R61）。用于覆盖生成器 `ZQ` 字典未配置造成的「选 —」占位。",
    "",
]

total = 0
if len(ranked) >= 2:
    a, b = ranked[0], ranked[1]
    da, ca = direction(a)
    db, cb = direction(b)
    units = ca * cb
    mult = max(1, min(3, 24 // (units * 2)))
    cost_a = units * 2 * mult
    total += cost_a
    lines += [
        f"### 方案 A · 稳健方向 2 串 1（{cost_a} 元）",
        f"- 选场：`{a} {name_of(a)}`（{tiers[a]} 级，选 **{da}**）× `{b} {name_of(b)}`（{tiers[b]} 级，选 **{db}**）",
        f"- 核算：{ca} × {cb} = {units} 注 × {mult} 倍 × 2 元 = **{cost_a} 元**",
        "",
        "",
    ]
    sc_a, sc_b = scores(a), scores(b)
    if sc_a and sc_b:
        lines += [
            "### 方案 B · 剧本比分 2 串 1 博弈（18 元）",
            f"- 选场：`{a} {name_of(a)}`（{' / '.join(sc_a)}）× `{b} {name_of(b)}`（{' / '.join(sc_b)}）",
            "- 核算：3 × 3 = 9 注 × 1 倍 × 2 元 = **18 元**",
            "",
        ]
        total += 18
    else:
        lines += ["### 方案 B · 比分结构未取到，不组比分串关（0 元）", ""]
elif len(ranked) == 1:
    a = ranked[0]
    da, ca = direction(a)
    mult = max(1, min(5, 20 // (ca * 2)))
    cost_a = ca * 2 * mult
    total += cost_a
    lines += [
        f"### 方案 A · 稳健方向单关（{cost_a} 元）",
        f"- 选场：`{a} {name_of(a)}`（{tiers[a]} 级，选 **{da}**）→ {ca} 注 × {mult} 倍 × 2 元 = **{cost_a} 元**",
        "",
        "### 方案 B · 本批仅 1 场达标，不组比分串关（0 元）",
        "",
    ]
else:
    lines += ["### 方案 A / B · 本批无达标场次，空仓观望（0 元）", ""]

lines += [
    f"- **总预算校验**：合计 **{total} 元**（硬上限 50 元，状态：{'✅ 合规' if total <= 50 else '❌ 超限'}）",
    "- **剔除不碰清单（D 级 / 证据不足）**：" + ("、".join(f"{n} {name_of(n)}" for n in sorted(skip)) or "无"),
    "- **临场首发熔断**：任一选中场次若出现核心支点 / 主力中卫临时缺阵，或官方胜平负定价相对本方案采集时点发生显著位移，该场自动熔断不跟，方案 A 相应降为单关或空仓。",
    "- **口径提醒**：外围亚盘在客队让球场次未录真实水位，本报告不折亚盘 EV；大小盘溢价标注为 C50 拦截项，不买入。",
    "",
    "> 免责：全部内容仅作数据观察与思路参考，不构成投注建议，注意控制仓位与过关风险。",
]

out = INTEL / f"_plan_{DAY}.json"
out.write_text(json.dumps({"markdown": "\n".join(lines),
                           "source": "build_plan.py / _model_v3_20261122.json",
                           "total_cost": total}, ensure_ascii=False, indent=1), encoding="utf-8")
print("OK 方案已生成：场次 %s / %s，合计 %d 元 → %s" % (ranked[:2], len(skip), total, out))
