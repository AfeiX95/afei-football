# -*- coding: utf-8 -*-
with open(r"I:\阿飞说球\📝文章\20260731\韩K联三场前瞻_头条版.md", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("今晚还能撑住吗", "这轮还能撑住吗")

with open(r"I:\阿飞说球\📝文章\20260731\韩K联三场前瞻_头条版.md", "w", encoding="utf-8") as f:
    f.write(content)

# Verify
if "今晚" in content:
    print("STILL FOUND")
else:
    print("FIXED - no time anchors")
