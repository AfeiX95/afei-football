#!/usr/bin/env python3
"""
头条号合规检测脚本 — 验证HTML文章可发布到头条号。

用法:
  # 单场/多场自动检测（自动识别场次数量）
  python3 verify-headline-compliance.py <html_file_path>

  # 指定预期场次数（覆盖自动检测）
  python3 verify-headline-compliance.py --matches=3 <html_file_path>

检测项目（20项）：
  1. 标题 ≤ 30字
  2. 无博彩术语（完整清单）
  3. 无 @1.xx 赔率格式
  4. 无 EV/Edge/仓位/凯利/期望值
  5. 数据来源不含"竞彩网"
  6. 含"仅供参考"（非"不构成"）
  7. 「个人猜测比分方向」×场次数
  8. 「难说。真说不好。」×场次数
  9. 含赛博模型复盘总结
  10. 互动提问（含问号）
  11. 队名覆盖（人工确认）
  12. 数据来源含懂球帝、ESPN
  13. 含HTML表格（≥2）
  14. 无Markdown语法混入
  15. ⏰ 无时间锚点（今天/明天/昨天/刚刚）
  16. 数据采集标注行存在（灰色小字）
  17. 无旧版免责声明（"不构成投注建议"）
  18. 含"后台模型"描述
  19. 含"个人猜测"软化词
  20. 收尾语录轮换提示
"""

import re, sys, os

# ---- Helpers ----

def auto_detect_match_count(text):
    """从文本中自动检测有几场比赛。"""
    # 先找显式的场次标记：如 【第一场】 【第二场】
    cn_nums = ['一','二','三','四','五','六','七','八','九','十']
    cn_map = {n:i+1 for i,n in enumerate(cn_nums)}
    max_marker = 0
    for m in re.finditer(r'【第([一二三四五六七八九十]+)场】', text):
        num_str = m.group(1)
        if num_str in cn_map and cn_map[num_str] > max_marker:
            max_marker = cn_map[num_str]
    if max_marker > 0:
        return max_marker
    # 没有分场标记 = 单场
    return 1


def verify(path, expected_matches=None):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # Auto-detect match count
    match_count = auto_detect_match_count(text)
    if expected_matches is None:
        expected_matches = match_count

    checks = []
    all_pass = True

    # 1. Title ≤ 30 chars
    title_match = re.search(r"<h2>(.+?)</h2>", text)
    if title_match:
        t = re.sub(r"<[^>]+>", "", title_match.group(1))
        clen = len(t)
        ok = clen <= 30
        checks.append((f"标题 ≤ 30字", f"{clen}字{' ✅' if ok else ' ❌'}", ok))
        if not ok: all_pass = False
    else:
        checks.append((f"标题存在", f"未找到标题 ❌", False))
        all_pass = False

    # 2. No banned gambling terms (expanded list)
    cleared = True
    banned_terms = ["赔率", "盘口", "庄家", "让球", "打穿", "稳胆", "上车", "跟单", "梭哈", "穿盘"]
    for term in banned_terms:
        if term in text:
            checks.append((f"无'{term}'", f"❌ 发现'{term}'", False))
            cleared = False
            all_pass = False
    if cleared:
        checks.append((f"无博彩术语（完整清单）", f"✅ 全部干净", True))

    # 3. No @1.xx odds
    odds = re.findall(r"@\d+\.\d+", text)
    if odds:
        checks.append((f"无@赔率格式", f"❌ 发现: {odds}", False))
        all_pass = False
    else:
        checks.append((f"无@赔率格式", f"✅ 干净", True))

    # 4. No EV/Edge/仓位/凯利/期望值
    fin_terms = ["EV", "Edge", "仓位", "凯利", "期望值"]
    fin_found = [t for t in fin_terms if t in text]
    if fin_found:
        checks.append((f"无金融术语", f"❌ 发现: {fin_found}", False))
        all_pass = False
    else:
        checks.append((f"无EV/Edge/仓位/凯利", f"✅ 干净", True))

    # 5. Data source not 竞彩网
    if "竞彩网" in text:
        checks.append((f"数据来源无'竞彩网'", f"❌ 发现'竞彩网'", False))
        all_pass = False
    else:
        checks.append((f"数据来源无'竞彩网'", f"✅ 干净", True))

    # 6. 仅供参考 + old version check
    if "仅供参考" not in text:
        checks.append((f"含'仅供参考'", f"❌ 未找到", False))
        all_pass = False
    else:
        checks.append((f"含'仅供参考'", f"✅ 已使用", True))
    if "不构成" in text:
        checks.append((f"无旧版'不构成投注建议'", f"❌ 仍在使用旧版免责", False))
        all_pass = False
    else:
        checks.append((f"无旧版'不构成...'", f"✅ 干净", True))

    # 7. 个人猜测比分方向 × match_count
    gc = text.count("个人猜测比分方向")
    ok = gc == expected_matches
    checks.append((f"「个人猜测比分方向」×{expected_matches}", f"出现{gc}次{' ✅' if ok else ' ❌'}", ok))
    if not ok: all_pass = False

    # 8. 难说。真说不好。 × match_count
    nc = text.count("难说。真说不好。")
    ok = nc == expected_matches
    checks.append((f"「难说。真说不好。」×{expected_matches}", f"出现{nc}次{' ✅' if ok else ' ❌'}", ok))
    if not ok: all_pass = False

    # 9. 赛博模型复盘总结
    if "赛博模型复盘总结" not in text:
        checks.append((f"含赛博模型复盘总结", f"❌ 未找到", False))
        all_pass = False
    else:
        checks.append((f"含赛博模型复盘总结", f"✅ 已包含", True))

    # 10. 互动提问
    if "?" not in text and "？" not in text:
        checks.append((f"互动提问", f"❌ 未找到问句", False))
        all_pass = False
    else:
        checks.append((f"互动提问", f"✅ 有读者互动", True))

    # 11. Team names — placeholder for manual check
    checks.append((f"队名覆盖", f"✅ 需人工确认", True))

    # 12. Data source correct
    if "懂球帝" not in text:
        checks.append((f"数据来源含懂球帝", f"❌ 未找到", False))
        all_pass = False
    else:
        checks.append((f"数据来源含懂球帝", f"✅ 正确", True))
    if "ESPN" not in text:
        checks.append((f"数据来源含ESPN", f"❌ 未找到", False))
        all_pass = False
    else:
        checks.append((f"数据来源含ESPN", f"✅ 正确", True))

    # 13. HTML tables ≥ 2
    table_count = text.count("<table>")
    if table_count < 2:
        checks.append((f"含HTML表格≥2", f"❌ 仅{table_count}个表格", False))
        all_pass = False
    else:
        checks.append((f"含HTML表格≥2", f"✅ {table_count}个表格", True))

    # 14. No markdown syntax in HTML
    md_syntax = ["```", "## ", "### "]
    md_found = None
    for md in md_syntax:
        if md in text:
            md_found = md.strip()
            break
    if md_found:
        checks.append((f"无Markdown语法混入", f"❌ 发现'{md_found}'", False))
        all_pass = False
    else:
        checks.append((f"无Markdown语法混入", f"✅ 干净", True))

    # 15. ⏰ 无时间锚点
    time_anchors = ["今天", "明天", "昨天", "刚刚"]
    found_anchors = [a for a in time_anchors if a in text]
    if found_anchors:
        checks.append((f"⏰ 无时间锚点", f"❌ 发现: {found_anchors}", False))
        all_pass = False
    else:
        checks.append((f"⏰ 无时间锚点", f"✅ 干净", True))

    # 16. 数据采集标注行
    has_data_line = ("数据采集" in text
                     and ("用户手动提取" in text or "中国体育彩票" in text or "雷速体育" in text))
    if not has_data_line:
        checks.append((f"数据采集标注行存在", f"❌ 未找到数据采集标注", False))
        all_pass = False
    else:
        checks.append((f"数据采集标注行存在", f"✅ 已标注", True))

    # 17. Already checked in #6 as sub-check
    # 18. 后台模型
    if "后台模型" not in text and "模型" not in text:
        checks.append((f"含'后台模型'描述", f"❌ 未找到模型相关描述", False))
        all_pass = False
    else:
        checks.append((f"含'后台模型'描述", f"✅ 已包含", True))

    # 19. 个人猜测 (softening word)
    if "个人猜测" not in text or "方向" not in text:
        checks.append((f"含'个人猜测'软化词", f"❌ 未找到", False))
        all_pass = False
    else:
        checks.append((f"含'个人猜测'软化词", f"✅ 已使用", True))

    # 20. 收尾语录轮换提示
    closing_quotes = [
        "难说。真说不好。",
        "足球这东西，谁说得准呢。",
        "反正我是信了。",
        "走着瞧。",
        "你们觉得呢？",
    ]
    found_quote = [q for q in closing_quotes if q in text]
    if not found_quote:
        checks.append((f"收尾语录", f"❌ 未找到已知语录", False))
        all_pass = False
    else:
        checks.append((f"收尾语录", f"✅ 使用已知语录（人工确认轮换）", True))

    # --- Report ---
    mode = "单场" if expected_matches == 1 else f"{expected_matches}场合集"
    print("=" * 56)
    print(f"  🔍 头条号合规检测报告（{mode}）")
    print(f"     文件: {os.path.basename(path)}")
    print("=" * 56)
    pass_count = sum(1 for _, _, ok in checks if ok)
    total = len(checks)
    verdict = "✅ 可发布" if all_pass else "⚠️ 待修正"
    print(f"\n  通过: {pass_count}/{total}  {verdict}")
    print(f"\n{'─' * 56}")
    for name, detail, ok in checks:
        symbol = "✅" if ok else "❌"
        print(f"  {symbol}  {name:<28} {detail}")
    print(f"\n{'=' * 56}")
    if all_pass:
        print("  ✅ 全部通过！文章可发布到头条号。")
    else:
        print(f"  ⚠️  {total-pass_count}项未通过，需修正后发布。")
    print(f"{'=' * 56}")
    return all_pass


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("用法: python3 verify-headline-compliance.py [--matches=N] <html_file_path>")
        print()
        print("  自动检测场次数，或通过 --matches=N 指定")
        sys.exit(1)

    expected_matches = None
    files = []
    for arg in sys.argv[1:]:
        if arg.startswith("--matches="):
            expected_matches = int(arg.split("=")[1])
        elif not arg.startswith("--"):
            files.append(arg)

    for f in files:
        ok = verify(f, expected_matches=expected_matches)
        sys.exit(0 if ok else 1)
