# -*- coding: utf-8 -*-
import re

with open(r"I:\阿飞说球\📝文章\20260731\韩K联三场前瞻_头条版.md", "r", encoding="utf-8") as f:
    content = f.read()

forbidden = {
    "赔率": "定价",
    "盘口": "设置",
    "庄家": "机构",
    "泊松": "后台模型",
    "蒙特卡洛": "后台模型",
    "EV": "溢价",
    "凯利": "系数",
    "赢盘": "赢指",
    "赢盘率": "赢指率",
}

print("=== 禁用词检查 ===")
found = False
for word, replacement in forbidden.items():
    if word in content:
        print(f"  FOUND: '{word}' -> replace with '{replacement}'")
        found = True
if not found:
    print("  PASS - no forbidden words found")

# Check title length
title = content.split("\n")[0].replace("# ", "")
print(f"\n=== 标题检查 ===")
print(f"  Title: {title}")
print(f"  Length: {len(title)} chars (limit: 30)")
if len(title) > 30:
    print(f"  WARNING: Title too long!")
else:
    print(f"  PASS")

# Check for time anchors
time_words = ["今天", "明天", "昨天", "今晚", "明晚"]
print(f"\n=== 时间锚点检查 ===")
found_time = False
for w in time_words:
    if w in content:
        print(f"  FOUND: '{w}'")
        found_time = True
if not found_time:
    print("  PASS - no time anchors found")

# Check disclaimer
print(f"\n=== 免责声明检查 ===")
if "图一乐" in content and "理智看球" in content:
    print("  PASS - disclaimer present")
else:
    print("  WARNING - disclaimer missing")

# Check data source
print(f"\n=== 数据来源检查 ===")
if "官方渠道" in content or "权威媒体" in content:
    print("  PASS - data source present")
else:
    print("  WARNING - data source missing")
