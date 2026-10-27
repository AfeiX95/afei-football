#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""小红书发布前风控自检（2026-10-12 判罚后新增的硬门禁）。

背景：首篇《10/13 三场我全站对面：机构看好的我都不跟》**22:23 发布、22:24 被处置**，
小红书判「笔记存在易造成财产安全风险的内容」（赌博类 8 条）。原因不是用词，是**形态**：
**方向 + 让球球数 + 具体比分 + 竞彩场次号** 四件凑齐，机器一分钟就能判成博彩信息
（改词「赔率→定价 / 盘口→门槛」无效——平台不看语义）。见 `📚知识库/公司工程/坑清单.md` 坑#69/#70。

这道闸只看形状、不猜语义：命中任一类 → 直接拒绝出图（退出码 2）。宁可错拦，不要漏。

**2026-10-13 二审后的修正（实测，很重要）**：把首篇形态改成「数据向单卡 + 后台模型块（热力图/胜率条）」，
但**正文**里写了「比分我猜 1 比 1（10.8%）／1 比 2（8.7%）」→ **仍然没过**；把正文改成纯技术面（图一字未动）→ **一次通过**。
结论：**判点在正文文字**——图上放概率图表没事，正文里出现比分猜测与概率数字才会判。
因此额外加了 `CAPTION_RULES` / `scan_caption()`（禁「猜/比分我/预测比分」与「% / 胜率 / 概率」），只扫要粘贴的正文。

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
    ("让球盘口", r"让球|受让|让平|升盘|降盘|盘口|水位|让[一二三]球|两球半|半球盘|打穿|净胜两球|赢两个球|赢三个球|这一档|门槛|小球|大球",
     "让球/大小球盘口语言（含「赢两个球以上」「小球率」这类盘口术语）"),
    ("方向投注", r"站[^\s]|跟单|不跟|上车|下注|投注|购彩|竞彩|彩票|彩果|红单|串关|稳赢|必中|推荐|看好|我算|我认为",
     "方向判断 / 投注引导（「彩果」「跟」「站」是平台风控敏感词）"),
    ("市场折算", r"机构|赔率|溢价|定价|三向概率|市场支持|中国体育|体育彩票|竞彩|比分概率|最热三格",
     "机构赔率折算/竞彩出处/比分概率标注属于高风险预测元素"),
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


# 文案正文专属规则：2026-10-13 实测——**同一张卡**（图上仍带比分概率热力图与胜率条）只把正文改成纯技术面
# 就**一次通过**，说明这一轮的判点在**正文文字**：正文里写比分猜测 / 概率数字才会判「财产安全风险」。
CAPTION_RULES = [
    ("正文·比分猜测", r"猜|比分我|高概率比分|预测比分|我看好",
     "正文出现比分猜测＝会被效仿的具体结果（图上的概率图表不判，正文文字判）"),
    ("正文·概率数字", r"\d\s*%|胜率|概率|几成把握",
     "正文出现概率/胜率数字，同属「会被效仿的具体结果」判点"),
]


def scan_caption(text: str, where: str = "文案正文") -> list:
    """只对「要粘贴到平台的正文」跑：禁比分猜测与概率数字。"""
    t = DATE_RE.sub("（日期）", str(text or ""))
    hits = []
    for name, pat, why in CAPTION_RULES:
        for m in re.finditer(pat, t):
            hits.append((name, m.group(0)[:20], where, why))
    return hits


# --------------------------------------------------------------------------- #
# 形态门禁（2026-10-21 立）：账号被先判后下架、解封当天新稿又判——判的是**形态**不是词
# 出处：小红书合规规范_20261021 §3.0 形态禁令 / §6.1.1 绝对不出现的元素 / §2.1.2 逐图归因
# 一句话：**一篇只讲一场，讲发生过什么，不讲接下来会怎样。**
# --------------------------------------------------------------------------- #
FORM_DIR_WORDS = ("方向偏", "我看好", "看好", "拿分", "不败", "推荐", "稳胆", "必中", "值得跟")
FORM_COVER_WORDS = ("比分概率", "综合结论", "概率", "预测", "推荐")
FORM_MAX_MATCHES = 6


def scan_form(data: dict, cards=None) -> list:
    """形态级检查，返回 [(级别fatal|warn, 名称, 片段, 位置, 为什么)]。

    fatal = 命中 2026-10-21 判词的核心形态（多场清单 / 封面自述预测 / 方向+概率+比分）；
    warn  = 概率分布类元素（三项概率条、比分热力图），属「重」但不单独致命。
    """
    cards = cards if cards is not None else (data.get("matches") or [])
    out = []
    n = len(cards)
    if n > FORM_MAX_MATCHES:
        out.append(("fatal", "形态·多场汇总", "%d 场" % n, "matches",
                    "多场清单 + 编号是购彩指南版式（判词第 7 条），单篇上限 4 场"))
    for key in ("cover_kicker", "cover_tail", "cover_hint"):
        v = str(data.get(key) or "")
        for w in FORM_COVER_WORDS:
            if w in v:
                out.append(("fatal", "形态·封面自述", "%s:%s" % (key, w), key,
                            "封面写「比分概率/综合结论」＝自己声明这是预测清单（10/21 自证项）"))
    for c in cards:
        tag = "%s %s vs %s" % (c.get("no") or "?", c.get("home") or "?", c.get("away") or "?")
        vd = c.get("verdict") or {}
        if vd:
            out.append(("fatal", "形态·综合结论", "%s %s" % (vd.get("dir") or "", vd.get("prob") or ""),
                        "%s.verdict" % tag,
                        "方向 + 概率 + 比分三件齐＝预测卡核心（10/21 四条致命项之二）"))
        if c.get("caption_dir"):
            out.append(("fatal", "形态·正文方向", str(c["caption_dir"])[:20], "%s.caption_dir" % tag,
                        "正文给方向＝判词第 8 条"))
        if (c.get("model") or {}).get("wdl"):
            out.append(("warn", "形态·三项概率条", "胜/平/负 三格", "%s.model.wdl" % tag,
                        "三项概率并列＝盘口形状，只降级不豁免"))
        if (c.get("model") or {}).get("grid"):
            out.append(("warn", "形态·比分热力", "主客进球网格", "%s.model.grid" % tag,
                        "比分概率矩阵形状本身即比分预测（用户点名例外：只上色不标数字、不连发）"))
        for i, ln in enumerate(c.get("caption_lines") or [], 1):
            for w in FORM_DIR_WORDS:
                if w in str(ln):
                    out.append(("fatal", "形态·正文方向", "%s:%s" % (w, str(ln)[:16]),
                                "%s.caption_lines[%d]" % (tag, i), "正文给方向＝判词第 8 条"))
    return out


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
    # ⚠️ 2026-10-18：`caption_para` 是**小红书正文**原文，正文判点由 scan_caption 负责
    #    （禁比分猜测/概率数字）；这里再按通用词表扫一遍没有意义——渲染器会把正文
    #    原样喂给 scan_text，历史上「机构/定价/三向概率」这类误判由此而来。
    for c in cards:
        tag = "%s %s vs %s" % (c.get("no") or "?", c.get("home") or "?", c.get("away") or "?")
        for key in ("stance", "stance_label", "contrast", "contradiction", "will",
                    "signal", "note", "brief", "narr", "point", "h2h_short"):
            if c.get(key):
                hits += scan_text(c[key], "%s.%s" % (tag, key))
        hd = c.get("h2h_detail") or {}
        for k in ("record", "note"):
            if hd.get(k):
                hits += scan_text(hd[k], "%s.h2h_detail.%s" % (tag, k))
        for side in ("home", "away"):
            d = ((c.get("intel2") or {}).get(side) or {})
            for k in ("good", "bad"):
                for item in (d.get(k) or []):
                    hits += scan_text(item, "%s.intel2.%s.%s" % (tag, side, k))
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
    # ⚠️ 2026-10-12 用户拍板：信息卡要放**后台模型算出来的胜率与比分概率热力图**
    #    （`model` 字段：lam/grid/wdl/top/guess）。这是一次有意的口径调整——
    #    首篇被判罚的形态是「方向 + 让球球数 + 具体比分 + 竞彩场次号」，这四件依旧全拦；
    #    `model` 与渲染出来的热力图/胜率条属于**概率分布**，不是「首选-次选-防范」那种推荐比分，
    #    所以这里的字段清单**刻意不含 model**。风险已在 docs/HANDOFF.md 夜·十三 记明。
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
        tp = Path(a.text)
        raw_txt = tp.read_text(encoding="utf-8") if tp.is_file() else a.text
        if "## 正文" in raw_txt:
            raw_txt = "\n".join(raw_txt.split("## 正文", 1)[1].split("## 标签", 1)[0].splitlines()[1:])
        hits += scan_text(raw_txt, "(--text)")
        hits += scan_caption(raw_txt, "(--text)")
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
