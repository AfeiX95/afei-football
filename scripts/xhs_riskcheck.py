#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""小红书发布前风控自检（2026-10-12 判罚后新增的硬门禁）。

背景：首篇《10/13 三场我全站对面：机构看好的我都不跟》**22:23 发布、22:24 被处置**，
小红书判「笔记存在易造成财产安全风险的内容」（赌博类 8 条）。原因不是用词，是**形态**：
**方向 + 让球球数 + 具体比分 + 竞彩场次号** 四件凑齐，机器一分钟就能判成博彩信息
（改词「赔率→定价 / 盘口→门槛」无效——平台不看语义）。见 `📚知识库/公司工程/坑清单.md` 坑#69/#70。

这道闸只看形状、不猜语义：命中任一类 → 直接拒绝出图（退出码 2）。宁可错拦，不要漏。

用法：
  python scripts/xhs_riskcheck.py "📝文章/20261014/小红书_第二批/cards.json"
  python scripts/xhs_riskcheck.py <cards.json> --text "另一段要发的文案"
  python scripts/xhs_riskcheck.py <cards.json> --quiet     # 只回退出码
被 `scripts/xhs_html.py` 的 build() 以硬门禁方式调用（命中即 sys.exit(2)，不出图）。
"""
import argparse
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 日期/时间先抠掉，免得「10/14」「2026-10-12」被当成比分
DATE_RE = re.compile(r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}\s*[/月]\s*\d{1,2}\s*日?|\d{1,2}:\d{2}")

RULES = [
    ("场次号", r"周[一二三四五六日]\s*\d{2,3}",
     "「周二004」类竞彩场次号 = 指向购彩渠道"),
    ("比分串", r"(?<![\d.])\d{1,2}\s*[-:]\s*\d{1,2}(?![\d])",
     "具体比分是会被效仿的博彩信息（战绩串「7胜3平0负」不受影响）"),
    ("让球盘口", r"让球|受让|让平|升盘|降盘|盘口|水位|让[一二三]球|两球半|半球盘|打穿|净胜两球|赢两个球|赢三个球|这一档|门槛",
     "让球盘口语言（含「赢两个球以上」这类让球球数）"),
    ("方向投注", r"站[^\s]|跟单|不跟|上车|下注|投注|购彩|竞彩|彩票|红单|串关|稳赢|必中|推荐|看好|我算|我认为",
     "方向判断 / 投注引导（「跟」「站」是小红书判罚里点名的跟单语）"),
    ("市场折算", r"机构|赔率|溢价|定价|三向概率|市场支持|中国体育|体育彩票|竞彩",
     "机构赔率折算/竞彩出处属于线上彩票信息（六维第 6 轴已换成进球稳定性）"),
    ("站外导流", r"微信|QQ|加群|私信|公众号|二维码|网址|https?://",
     "站外联系方式/跳转（软禁词，简介里也禁）"),
]


def scan_text(text: str, where: str = "") -> list:
    """返回 [(类别, 命中片段, 位置, 说明)]。"""
    t = DATE_RE.sub("（日期）", str(text or ""))
    hits = []
    for name, pat, why in RULES:
        for m in re.finditer(pat, t):
            frag = m.group(0)
            if len(frag) > 20:
                frag = frag[:20] + "…"
            hits.append((name, frag, where, why))
    return hits


def scan_cards(data: dict, cards=None) -> list:
    """扫整份 cards.json（含标题/封面条目/每场文本/雷达维度名）。"""
    cards = cards if cards is not None else (data.get("matches") or [])
    hits = []
    # 元信息与封面
    for key in ("title", "xhs_title", "subtitle", "cover_kicker", "cover_hint", "cover_tail",
                "tags", "brand", "source"):
        if data.get(key):
            hits += scan_text(data[key], key)
    for i, it in enumerate(data.get("cover_items") or [], 1):
        hits += scan_text(it, "cover_items[%d]" % i)
    # 每场（注意：`no`（如「周二005」）只是本地文件名标识，数据向卡片不渲染、文案也不写，故不扫）
    for c in cards:
        tag = "%s %s vs %s" % (c.get("no") or "?", c.get("home") or "?", c.get("away") or "?")
        for key in ("stance", "stance_label", "contrast", "contradiction", "will",
                    "signal", "note"):
            if c.get(key):
                hits += scan_text(c[key], "%s.%s" % (tag, key))
        for i, t in enumerate(c.get("focus") or [], 1):
            hits += scan_text(t, "%s.focus[%d]" % (tag, i))
        for i, t in enumerate(c.get("score") or [], 1):
            hits += scan_text(t, "%s.score[%d]" % (tag, i))
        fr = c.get("form") or {}
        for side in ("home", "away"):
            s = fr.get(side) or {}
            hits += scan_text(s.get("name"), "%s.form.%s.name" % (tag, side))
        hits += scan_text(fr.get("h2h"), "%s.form.h2h" % tag)
        hits += scan_text(fr.get("h2h_short"), "%s.form.h2h_short" % tag)
        rd = c.get("radar") or {}
        for d in rd.get("dims") or []:
            hits += scan_text(d, "%s.radar.dims" % tag)
        # 概率/比分这类字段在数据向形态里根本不该出现
        for key in ("probs_mine", "probs_mkt"):
            if c.get(key):
                hits.append(("市场折算", str(c[key]), "%s.%s" % (tag, key),
                             "数据向卡片不放机构/模型概率"))
        if c.get("stance"):
            hits.append(("方向投注", str(c["stance"]), "%s.stance" % tag, "数据向卡片不放立场判断"))
        if c.get("score"):
            hits.append(("比分串", str(c["score"]), "%s.score" % tag, "数据向卡片不放推荐比分"))
    return hits


def main() -> None:
    ap = argparse.ArgumentParser(description="小红书发布前风控自检（命中即拦停）")
    ap.add_argument("cards", help="cards.json 路径")
    ap.add_argument("--text", default="", help="额外检查的一段自由文本（比如文案草稿）")
    ap.add_argument("--quiet", action="store_true", help="只输出结果行")
    a = ap.parse_args()
    p = Path(a.cards)
    if not p.exists():
        print("找不到 " + str(p))
        sys.exit(1)
    data = json.load(io.open(p, encoding="utf-8"))
    hits = scan_cards(data)
    if a.text:
        hits += scan_text(a.text, "(--text)")
    if not hits:
        print("✅ 风控自检通过：" + str(p))
        sys.exit(0)
    print("❌ 风控自检拦停：%d 处命中（小红书博彩形态：方向/让球球数/具体比分/场次号/市场折算）" % len(hits))
    if not a.quiet:
        seen = set()
        for name, frag, where, why in hits:
            k = (name, frag, where)
            if k in seen:
                continue
            seen.add(k)
            print("   · [%s] %s  ← %s" % (name, frag, where))
            print("     为什么拦：%s" % why)
        print("   改法：删掉方向/比分/让球球数/场次号/机构折算，只留官方赛果数据（战绩·同主客·进失球·六维·看点）。")
    sys.exit(2)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
