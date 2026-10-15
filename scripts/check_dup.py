# -*- coding: utf-8 -*-
"""同批多篇去重检查（R44 第八则）。

用法：
    python scripts/check_dup.py 20261016                # 查 📝文章/20261016/ 全部 md
    python scripts/check_dup.py "📝文章/20261016" "📝文章/20261015"
    python scripts/check_dup.py 20261016 --min 10       # 自定义最小行长（默认 12）

判定：正文行（长度 ≥ min、非表格、非标题、非空行）若在多篇之间重复 → 报重复。
固定句白名单（不算重复）：数据来源…、仅供参考…、#标签行、标题行。
退出码：0 = 无跨篇重复；1 = 有重复（可用于收工前卡口）。
"""
import io, os, re, sys, glob, collections

try:  # Windows 控制台默认 GBK，emoji/✅ 会 UnicodeEncodeError
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIXED = (
    "数据来源",
    "仅供参考",
    "请理性看待比赛",
)


def iter_articles(arg):
    p = arg
    if not os.path.isabs(p):
        p = os.path.join(ROOT, p)
    if os.path.isdir(p):
        return sorted(glob.glob(os.path.join(p, "*.md")))
    if p.endswith(".md"):
        return [p]
    # 当作日期目录名
    d = os.path.join(ROOT, "📝文章", arg)
    return sorted(glob.glob(os.path.join(d, "*.md")))


def is_body(line, min_len):
    s = line.strip()
    if len(s) < min_len:
        return False
    if s.startswith("|") or s.startswith("#"):
        return False
    for f in FIXED:
        if f in s:
            return False
    return True


def main(argv):
    if not argv:
        sys.stdout.write(__doc__)
        return 2
    min_len = 12
    args = []
    i = 0
    while i < len(argv):
        if argv[i] == "--min":
            min_len = int(argv[i + 1])
            i += 2
            continue
        args.append(argv[i])
        i += 1

    files = []
    for a in args:
        files.extend(iter_articles(a))
    if not files:
        sys.stdout.write("no article found\n")
        return 2

    seen = collections.defaultdict(list)
    for p in files:
        name = os.path.basename(p)
        with io.open(p, "r", encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if is_body(line, min_len):
                    seen[line.strip()].append("%s:L%d" % (name[:12], n))

    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    lines = ["检查文件 %d 个（最小行长 %d）" % (len(files), min_len)]
    for p in files:
        lines.append("  - %s" % os.path.basename(p))
    if not dupes:
        lines.append("结果：无跨篇重复 ✅")
    else:
        lines.append("结果：跨篇重复 %d 处 ❌" % len(dupes))
        for k, v in sorted(dupes.items(), key=lambda kv: -len(kv[1])):
            lines.append("  [%s] %s" % (", ".join(v), k[:60]))
    txt = "\n".join(lines)
    sys.stdout.write(txt + "\n")
    return 1 if dupes else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
