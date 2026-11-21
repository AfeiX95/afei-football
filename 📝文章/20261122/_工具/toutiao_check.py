# -*- coding: utf-8 -*-
"""头条社区规范专项核对（只读）：对三篇 B 层公开稿做规范层扫描。

覆盖头条 2026-10-28 核实版里 preflight 未单列的红线：
  极限夸张 / 强迫式 / 绝对化推断 / 时间锚点 / 推广互粉 / 荐彩形态 / 标题标点白名单。

用法：
    python -X utf8 "📝文章/20261122/_工具/toutiao_check.py"
"""
from __future__ import annotations

import re
from pathlib import Path

BASE = Path("I:/阿飞说球/📝文章/20261122")
FILES = [
    "20261122_周日001+002_韩职早场_金泉对济州光州对富川_两个主场都不硬_赛事前瞻.md",
    "20261122_周日004+003+006等9场_晚场_一边倒我偏不站_赛事前瞻.md",
    "20261122_周日012+013等7场_凌晨_七场关键都在防守_赛事前瞻.md",
]

GROUPS = {
    "极限夸张": ["震惊", "彻底", "绝了", "百分百", "稳了", "必胜", "必中",
                 "最强", "唯一", "史无前例", "无人能敌", "碾压一切", "吊打"],
    "强迫式": ["不看后悔", "聪明人都", "必看", "赶紧", "速看", "错过就"],
    "绝对化推断": ["肯定", "一定能", "必然", "铁定", "毫无疑问", "绝对会", "包赢", "稳赢"],
    "时间锚点": ["今天", "明天", "昨天", "今晚", "昨晚", "本月", "刚刚",
                 "北京时间", "几个小时", "目前", "现在"],
    "推广互粉": ["微信", "二维码", "私信", "加群", "关注我", "点赞", "转发",
                 "收藏", "站外", "公众号", "首发"],
    "荐彩形态": ["跟单", "上车", "稳胆", "红单", "命中率", "盈利", "回本",
                 "赔率", "盘口", "让球", "投注", "串关", "下注", "买"],
}

# 官方标题标点白名单：？ ！ ， ： “ ” 《 》 —— ｜（另有字母 VS 不计为标点）
TITLE_ALLOWED_PUNCT = set("？！，：“”《》｜—")


def main() -> int:
    total_risk = 0
    for name in FILES:
        p = BASE / name
        text = p.read_text(encoding="utf-8")
        lines = text.splitlines()
        title = next((l[2:].strip() for l in lines if l.startswith("# ")), "")
        print("=" * 68)
        print(name[:40])
        print(f"  标题（{len(title)} 字）：{title}")

        # 标题标点白名单
        bad = sorted({ch for ch in title
                      if not ch.isalnum() and ch not in TITLE_ALLOWED_PUNCT and ch != " "})
        print(f"  标题标点：{'OK（白名单内）' if not bad else '越界 ' + ''.join(bad)}")

        # 每场小标题与信心指数
        subs = [l for l in lines if l.startswith("##")]
        print(f"  小节数：{len(subs)}｜推荐比分出现：{text.count('推荐比分')} 次")

        body = "\n".join(l for l in lines if not l.startswith("#"))
        for gname, words in GROUPS.items():
            hits = []
            for w in words:
                for m in re.finditer(re.escape(w), body):
                    ln = body.count("\n", 0, m.start()) + 1
                    ctx = body[max(0, m.start() - 10): m.end() + 10].replace("\n", " ")
                    hits.append(f"{w}@L{ln}…{ctx}…")
            if hits:
                total_risk += 1
                print(f"  [{gname}] {len(hits)} 处")
                for h in hits[:6]:
                    print(f"      {h}")
            else:
                print(f"  [{gname}] 0")
    print("=" * 68)
    print(f"需人工判断的词组数：{total_risk}（0 = 全部干净）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
