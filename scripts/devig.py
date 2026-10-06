# -*- coding: utf-8 -*-
"""竞彩去水工具 v1.0

把固定奖金（十进制赔率）换算成隐含概率，去掉机构抽水：

    隐含概率_i = (1/odds_i) / Σ(1/odds_j)
    抽水率     = Σ(1/odds_j) - 1

用法
----
    python scripts/devig.py <输入文件> [--labels 主 平 客]
    python scripts/devig.py -            # 从 stdin 读
    echo "09:39 | 1.65 3.35 4.45" | python scripts/devig.py -

输入行格式（分隔符可用 | 、制表符、逗号；不含数字的行原样忽略）
    09:39:49 | 1.65 3.35 4.45
    16:05:47 | 1.62 3.35 4.70

输出：每个时间点一行的 Markdown 表（去水百分比，保留一位小数）。

注意
----
- 只做数学换算，不做任何规则修正；修正按 `📚知识库/模型脚本/修正规则.md` 叠加。
- 让球盘同样适用：主让-N 时三档依次是「打穿 / 走盘 / 让负」；客让-N 时顺序相反。
"""
import io
import re
import sys


def devig(odds):
    inv = [1.0 / o for o in odds]
    s = sum(inv)
    return [x / s * 100.0 for x in inv], (s - 1.0) * 100.0


def parse(line):
    """返回 (标签, [odds...])；无法解析则返回 None。"""
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", line.split("|")[-1])]
    nums = [n for n in nums if n > 1.0]          # 赔率必然 > 1
    if len(nums) < 2:
        return None
    label = line.split("|")[0].strip() if "|" in line else ""
    return label, nums


def main():
    args = sys.argv[1:]
    labels = None
    if "--labels" in args:
        i = args.index("--labels")
        labels = args[i + 1:]
        args = args[:i]

    if not args:
        print(__doc__)
        return 1

    if args[0] == "-":
        text = sys.stdin.read()
    else:
        # utf-8-sig：PowerShell 5.1 的 Out-File -Encoding utf8 会写 BOM，
        # 用 utf-8 读会把 BOM 并进第一行、导致注释行被当成数据行解析
        text = io.open(args[0], encoding="utf-8-sig").read()

    rows = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        r = parse(line)
        if r:
            rows.append(r)

    if not rows:
        print("[!] 没有解析到任何一行赔率")
        return 1

    n = len(rows[0][1])
    for _, nums in rows:
        if len(nums) != n:
            print("[!] 各行的档位数不一致：第一行 %d 档，本行 %d 档" % (n, len(nums)))
            return 1

    if labels and len(labels) == n:
        head = ["时间"] + list(labels)
    else:
        head = ["时间"] + ["档%d" % (i + 1) for i in range(n)]

    print("| " + " | ".join(head) + " | 抽水 |")
    print("|:---|" + ":---:|" * n + ":---:|")
    for label, nums in rows:
        probs, vig = devig(nums)
        cells = " | ".join("%.1f%%" % p for p in probs)
        print("| %s | %s | %.2f%% |" % (label or "-", cells, vig))

    print()
    print("> 去水口径：隐含概率 =(1/赔率)/Σ(1/赔率)；抽水 =Σ(1/赔率)-1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
