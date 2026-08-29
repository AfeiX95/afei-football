# -*- coding: utf-8 -*-
"""
发布门禁 check_article.py v1.0（md 文章一体化检查）
==================================================
把散落的检查点合成一条命令：合规体检 + AI 痕迹检测 + 必备要素 + 数字合规。
通过标准：硬禁用词 0 / AI 评分 <30 / 必备要素齐全 → PASS 才可发布。

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
]

REQUIRED_MARKERS = {
    "⚔️ 战意": r"战意|⚔️",
    "💰 信号": r"信号|💰",
    "🌍 外媒": r"外媒|外部视角|🌍",
    "高概率比分": r"高概率比分",
    "数据来源": r"数据来源",
    "免责": r"免责|理性看球|请理性",
    "互动钩子(问号)": r"？|\?",
}


def strip_body(text):
    """去掉代码块/表格行/标题行，只留正文做词检"""
    t = re.sub(r"```.*?```", "", text, flags=re.S)
    t = re.sub(r"\|[^\n]*\|", " ", t)
    t = re.sub(r"^#+.*$", "", t, flags=re.M)
    t = re.sub(r"^>\s*.*$", "", t, flags=re.M)
    # 免责模板中的"合法体育彩票"为允许短语，先摘除避免误报
    t = t.replace("合法体育彩票", "")
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
    items = []

    # 1. 标题
    m = re.search(r"^#\s*(.+)$", text, flags=re.M)
    title = m.group(1).strip() if m else ""
    tlen = len(title)
    items.append(("1. 标题 ≤30字", tlen <= 30, f'"{title[:40]}"（{tlen}字）'))

    # 2. 硬禁用词
    hard = find_hits(body, HARD_BANNED)
    items.append(("2. 硬禁用词 = 0", len(hard) == 0,
                  "0" if not hard else "；".join(f"{w}@L{ln}" for w, ln in hard)))

    # 3. 红线词（需人工确认语境）
    soft = find_hits(body, SOFT_BANNED)
    items.append(("3. 红线词（语境确认）", len(soft) == 0,
                  "0" if not soft else "；".join(f"{w}@L{ln}" for w, ln in soft[:8])))

    # 4. 破折号 ≤3（金句除外，超限警告）
    dash = body.count("——")
    items.append(("4. 破折号 ≤3", dash <= 3, f"{dash}"))

    # 5. 必备要素（容忍多种写法）
    missing = [k for k, pat in REQUIRED_MARKERS.items() if not re.search(pat, text)]
    items.append(("5. 必备要素齐全", not missing,
                  "齐" if not missing else "缺：" + "/".join(missing)))

    # 6. 数字合规（裸赔率小数提醒；百分比/场均进球区间不算）
    t6 = re.sub(r"\d\.\d{1,2}-\d", "", body)          # 去掉 "2.75-4" 进球区间
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
