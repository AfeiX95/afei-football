# -*- coding: utf-8 -*-
"""提取 WAF 挑战页, 分析其依赖的 DOM API"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "live_home.html"), encoding="utf-8", errors="replace") as f:
    html = f.read()

# 提取 aliyunwaf 脚本
m = re.search(r'<script name="aliyunwaf_[^"]*">(.*?)</script>', html, re.S)
if m:
    js = m.group(1)
    with open(os.path.join(HERE, "waf_challenge.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print("waf script len:", len(js))
    # 找用到的全局标识符
    for token in ["document", "location", "window", "navigator", "cookie", "getElementById", "reload", "setCookie", "renderData", "arg1"]:
        print(token, "count:", js.count(token))
    # 提取 eval/Function 调用
    for m2 in re.finditer(r'(eval|Function|new Function)\(', js):
        print("eval-like at", m2.start())
else:
    print("no waf script found")
