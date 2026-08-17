# -*- coding: utf-8 -*-
with open(r"I:\阿飞说球\📝文章\20260731\韩K联三场前瞻_头条版.md", "r", encoding="utf-8") as f:
    content = f.read()

# Structure check
checks = [
    ("标题", "# 韩K联" in content),
    ("标签", "标签：" in content),
    ("金句", "数据不会说谎" in content),
    ("核心结论前置", "核心结论（前置）" in content),
    ("浦项分析", "浦项制铁 vs 金泉尚武" in content),
    ("全北分析", "全北现代 vs FC首尔" in content),
    ("江原分析", "江原FC vs 富川FC" in content),
    ("比分预测矩阵", "比分预测矩阵" in content),
    ("互动钩子", "互动钩子" in content),
    ("数据来源", "数据来源" in content),
    ("免责声明", "免责声明" in content),
    ("配图关键词", "配图关键词" in content),
]

print("=== 结构检查 ===")
all_pass = True
for name, ok in checks:
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"  [{status}] {name}")

# Forbidden words
forbidden = ["赔率", "盘口", "庄家", "泊松", "蒙特卡洛", "EV", "凯利", "赢盘"]
print("\n=== 禁用词检查 ===")
found_any = False
for w in forbidden:
    if w in content:
        print(f"  FOUND: {w}")
        found_any = True
if not found_any:
    print("  PASS")

# Title length
title = content.split(chr(10))[0].replace("# ", "")
print(f"\n=== 标题: {title} ({len(title)}字) ===")

# Time anchors
for w in ["今天", "明天", "昨天", "今晚", "明晚"]:
    if w in content:
        print(f"  WARNING: 时间锚点 '{w}'")

# Disclaimer
if "图一乐" in content and "理智看球" in content:
    print("  免责声明: PASS")

# Tags count
import re
tag_match = re.search(r"标签：(.+)", content)
if tag_match:
    tags = [t.strip() for t in tag_match.group(1).split("、")]
    print(f"  标签数: {len(tags)}个")

print(f"\n=== 总体: {'ALL PASS' if all_pass else 'HAS ISSUES'} ===")
