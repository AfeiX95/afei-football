# -*- coding: utf-8 -*-
"""
发布门禁 check_article.py v1.2（md 文章一体化检查）
==================================================
把散落的检查点合成一条命令：合规体检 + AI 痕迹检测 + 必备要素 + 数字合规。
通过标准：硬禁用词 0 / AI 评分 <30 / 必备要素齐全 → PASS 才可发布。

v1.2（2026-10-06）：**修补表格豁免漏洞**——原 `strip_body()` 把所有表格行替换成空格，
  而第 2/3/6 项都跑在它上面，导致 **表格里写「盘口」「北京时间」或 `4.45` 这类裸赔率可完全绕过门禁**
  （实测 87 篇旧稿有 41 篇靠表格藏违规）。现第 2/3/6 项改跑 `full_body()`（**保留表格与标题行**，
  只去代码块/details/免责豁免短语）；第 4/7/8 项仍用 `strip_body()`。

v1.1（2026-10-06）：**外媒从硬性必备降为可选**——用户定「搜索不到就不要」，
  检索无源时直接不写该段，也不写"查不到/待补"的占位说明；缺外媒不判 FAIL。

用法：
  python check_article.py 文章.md            # 输出检查清单 + 最终门禁结果
  python check_article.py 文章.md --json      # JSON 输出（供脚本/CI 集成）

退出码：0=PASS，1=FAIL（有❌项）。
"""
import re
import sys
import os
import json

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ---------------- 词表（来源：football-match-preview-pipeline + afei R20 红线词） ----------------
HARD_BANNED = [
    "赔率", "盘口", "庄家", "泊松", "蒙特卡洛", "EV", "凯利", "打穿", "穿盘",
    "北京时间", "今天", "明天", "昨天", "刚刚", "今晚", "昨晚", "本月", "几个小时",
]
SOFT_BANNED = [
    "投注", "下注", "串关", "过关", "稳胆", "上车", "跟单", "重注", "梭哈",
    "彩票", "博彩", "荐彩", "稳赢", "必中", "私信", "微信号", "赌球", "让球盘", "水位",
    "赌",  # R20: 口语「赌」字（打赌猜测义）机器可能误判为博彩语境 → 改「更信/更看好」
]

REQUIRED_MARKERS = {
    "⚔️ 战意": r"战意|⚔️",
    "💰 信号": r"信号|💰",
    "高概率比分": r"高概率比分",
    "数据来源": r"数据来源",
    "免责": r"免责|理性看球|请理性",
    "互动钩子(问号)": r"？|\?",
}

# 可选要素：有源必写、无源可省。
# 用户 2026-10-06 定：检索不到外媒源就直接不写，**不要写"查不到/待补"的占位说明**（那是废话）。
# 因此外媒从硬性必备降为可选——缺了不判 FAIL，只在第 5 项尾部提示。
OPTIONAL_MARKERS = {
    "🌍 外媒": r"外媒|外部视角|🌍",
}


def strip_body(text):
    """去掉代码块/表格行/标题行/配图建议块，只留正文做词检"""
    t = re.sub(r"<details>.*?</details>", "", text, flags=re.S)   # 配图建议等发布前删除的元信息
    t = re.sub(r"```.*?```", "", t, flags=re.S)
    t = re.sub(r"\|[^\n]*\|", " ", t)
    t = re.sub(r"^#+.*$", "", t, flags=re.M)
    t = re.sub(r"^>\s*.*$", "", t, flags=re.M)
    # 免责模板中的"合法体育彩票"为允许短语，先摘除避免误报
    t = t.replace("合法体育彩票", "")
    # 免责劝诫短语（AGENTS.md 铁律要求文末必带）同样豁免：含"赌"字但属劝退语境，非博彩诱导
    for phrase in ("远离赌博", "远离赌球", "理性购彩", "理性投注"):
        t = t.replace(phrase, "")
    return t


def full_body(text):
    """保留表格行与标题行的检查面（用于第 2/3/6 项）。

    与 strip_body() 的唯一区别：**不删表格行 `|…|`、不删标题行 `^#+`**。
    读者看得见的每一处字面都在这里被检查——表格和标题恰恰是最容易藏违规的地方。
    """
    t = re.sub(r"<details>.*?</details>", "", text, flags=re.S)
    t = re.sub(r"```.*?```", "", t, flags=re.S)
    t = t.replace("合法体育彩票", "")
    for phrase in ("远离赌博", "远离赌球", "理性购彩", "理性投注"):
        t = t.replace(phrase, "")
    return t


def find_hits(text, words):
    hits = []
    for w in words:
        for m in re.finditer(re.escape(w), text):
            line = text.count("\n", 0, m.start()) + 1
            hits.append((w, line))
    return hits


def check(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    body = strip_body(text)
    full = full_body(text)     # 第 2/3/6 项用：表格与标题行照查（v1.2 修漏洞）
    items = []

    # 1. 标题
    m = re.search(r"^#\s*(.+)$", text, flags=re.M)
    title = m.group(1).strip() if m else ""
    tlen = len(title)
    items.append(("1. 标题 ≤30字", tlen <= 30, f'"{title[:40]}"（{tlen}字）'))

    # 2. 硬禁用词
    hard = find_hits(full, HARD_BANNED)
    items.append(("2. 硬禁用词 = 0", len(hard) == 0,
                  "0" if not hard else "；".join(f"{w}@L{ln}" for w, ln in hard)))

    # 3. 红线词（需人工确认语境）
    soft = find_hits(full, SOFT_BANNED)
    items.append(("3. 红线词（语境确认）", len(soft) == 0,
                  "0" if not soft else "；".join(f"{w}@L{ln}" for w, ln in soft[:8])))

    # 4. 破折号 ≤3（金句除外，超限警告）
    dash = body.count("——")
    items.append(("4. 破折号 ≤3", dash <= 3, f"{dash}"))

    # 5. 必备要素（容忍多种写法）；外媒为"有源必写、无源可省"
    missing = [k for k, pat in REQUIRED_MARKERS.items() if not re.search(pat, text)]
    opt_missing = [k for k, pat in OPTIONAL_MARKERS.items() if not re.search(pat, text)]
    d5 = "齐" if not missing else "缺：" + "/".join(missing)
    if opt_missing:
        d5 += "（" + "/".join(opt_missing) + "无源，按规则省略）"
    items.append(("5. 必备要素齐全", not missing, d5))

    # 6. 数字合规（裸赔率小数提醒；百分比/场均进球区间不算）
    t6 = re.sub(r"\d\.\d{1,2}-\d", "", full)          # 去掉 "2.75-4" 进球区间
    t6 = re.sub(r"\d\.\d{1,2}(?=球|个|场)", "", t6)    # 去掉 "2.75球" 类
    decimals = re.findall(r"\d\.\d{2}(?!%)", t6)
    items.append(("6. 裸赔率小数 = 0", len(decimals) == 0,
                  "0" if not decimals else f"{len(decimals)}处：{decimals[:6]}"))

    # 7. AI 痕迹（复用 ai_detect）
    ai_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_detect.py")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ai_detect import analyze
    ai = analyze(body)
    ai_pass = ai["score"] < 30
    items.append(("7. AI 评分 <30", ai_pass,
                  f"{ai['score']}（{ai['verdict']}）"))

    # 8. 占位符/乱码（图N占位符、控制字符、乱码星号）
    ph = re.findall(r"图\s*[0-9一二三四五六七八九十]\s*[ ：]\s*[^。\n]{1,12}", text)  # "图1 场均进失球对比"类；"图一乐"不算
    ctrl = re.findall(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ufffd]", text)
    stars = re.findall(r"\*\s+\*", text)   # 单星号+空白+单星号（#足球竞彩#* * 类乱码；**加粗不算）
    bad = []
    if ph:
        bad.append(f"图占位符{len(ph)}处:{ph[:3]}")
    if ctrl:
        bad.append(f"控制字符{len(ctrl)}处")
    if stars:
        bad.append(f"乱码星号{len(stars)}处")
    items.append(("8. 占位符/乱码 = 0", not bad,
                  "0" if not bad else "；".join(bad)))

    # 汇总
    fails = [it[0] for it in items if not it[1]]
    warns = [it[0] for it in items if it[2] and isinstance(it[2], str) and ("L" in it[2] or it[0] == "4. 破折号 ≤3" and it[1] is False)]
    passed = len(items) - len(fails)
    return {
        "file": path, "title": title, "title_len": tlen,
        "items": [{"name": n, "ok": ok, "detail": d} for n, ok, d in items],
        "ai": {"score": ai["score"], "verdict": ai["verdict"],
               "suspicious_top": [s[0][:50] for s in ai["suspicious"][:5]]},
        "pass": not fails, "fail_count": len(fails),
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    r = check(path)
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0 if r["pass"] else 1)
    print("=" * 52)
    print(f"发布门禁: {path}")
    print("-" * 52)
    for it in r["items"]:
        mark = "✅" if it["ok"] else "❌"
        if it["name"].startswith("3.") and not it["ok"]:
            mark = "⚠️"  # 红线词仅警告
        print(f"{mark} {it['name']}: {it['detail']}")
    if r["ai"]["suspicious_top"]:
        print("   AI可疑句(降AI参考): " + " | ".join(r["ai"]["suspicious_top"]))
    print("-" * 52)
    if r["pass"]:
        print(f"结果: PASS ✅（{len(r['items'])} 项检查 {len(r['items'])} 通过）→ 可发布")
    else:
        print(f"结果: FAIL ❌（{r['fail_count']} 项未过）→ 修完再跑")
    print("=" * 52)
    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
