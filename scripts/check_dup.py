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

# R44 第八则管的是**可发布的前瞻正文**。内部分析报告（每场固定六块）与全盘分析报告
# 天生就是同一套骨架逐场复用，把它们拉进跨篇去重只会永远报红，属于误用。
# 需要连内部报告一起查时加 --include-internal。
SKIP_MARK = ("内部分析报告", "全盘分析报告", "赛后校验")


def iter_articles(arg, include_internal=False):
    p = arg
    if not os.path.isabs(p):
        p = os.path.join(ROOT, p)
    def keep(files):
        if include_internal:
            return files
        return [x for x in files if not any(k in os.path.basename(x) for k in SKIP_MARK)]

    if os.path.isdir(p):
        return keep(sorted(glob.glob(os.path.join(p, "*.md"))))
    if p.endswith(".md"):
        return [p]
    # 当作日期目录名
    d = os.path.join(ROOT, "📝文章", arg)
    return keep(sorted(glob.glob(os.path.join(d, "*.md"))))


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
    include_internal = "--include-internal" in argv
    argv = [x for x in argv if x != "--include-internal"]
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
        files.extend(iter_articles(a, include_internal))
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
