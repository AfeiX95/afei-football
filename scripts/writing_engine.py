# -*- coding: utf-8 -*-
"""AFEI-WRITING-ENGINE v1.0 —— 双层轮换：风格（A–H）× 结构（S01–S10）+ 去重检查。

真源：📚知识库/写作指南/AFEI-WRITING-ENGINE-v1.0.md（R62，2026-11-07 起取代 R53 旧结构池）

顺序：先选题 → 再选风格 → 再选结构 → 最后写文章。
脚本只负责「按素材打分 + 读历史避重 + 落账 + 去重体检」，不碰概率、不碰方向。

用法
----
  # 1) 看风格池/结构池、最近使用、比例执行情况
  python -X utf8 scripts/writing_engine.py --list

  # 2) 按素材特征选风格 + 结构（特征逗号分隔，见 --features-help）
  python -X utf8 scripts/writing_engine.py --pick --matches 4 \
      --feat anomaly,same_theme,fav_risk
  python -X utf8 scripts/writing_engine.py --pick --matches 1 --feat tactical \
      --tactical-source "两队近 5 场阵型与边路传中数据（官方技术统计）"
  python -X utf8 scripts/writing_engine.py --pick --stage post --matches 4

  # 3) 写完后体检（开头/论证顺序/固定句式/结尾/标题 与最近 3 篇比对）
  python -X utf8 scripts/writing_engine.py --check "<文章.md>"

  # 4) 过 preflight 后落账（开头、结尾、标题模式自动从文章里抽）
  python -X utf8 scripts/writing_engine.py --record --article "<文章.md>" \
      --style E --structure S04 --stage pre

纪律
----
- 风格与结构独立选择、不固定绑定；结构以素材为先，近期用过只扣分不封杀。
- D（战术对抗）必须给 --tactical-source；F（故事叙事）必须给 --story-source，否则不触发。
- 风格/结构选择 **不得改变** 内部报告的方向与比分三档（check_report_consistency 把关）。
- 只有过 preflight 的稿子才 --record；失败/中止不落账。
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import statistics
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "state", "writing_history.json")
SCHEME = "engine-v1"
KEEP = 60
RECENT = 3
RATIO_WINDOW = 20

# ── 风格池（表达口吻）────────────────────────────────────────────
STYLES = {
    "A": ("老球迷观察型", "口语、幽默、个人情绪", 0.20),
    "B": ("数据分析师型", "数据、逻辑、反向验证", 0.20),
    "C": ("悬念推理型", "疑问、推理、逐层揭示", 0.15),
    "D": ("战术对抗型", "阵型、对位、攻防博弈（必须有战术资料）", 0.10),
    "E": ("反常识纠偏型", "质疑、验证、拆解误区", 0.15),
    "F": ("故事叙事型", "球队变化、人物、背景（必须可核实）", 0.05),
    "G": ("赛后复盘型", "预测、结果、误差分析（仅赛后）", 0.10),
    "H": ("极简快评型", "短句、重点、快速判断", 0.05),
}
# 素材触发 → 风格（顺序即用户给的优先级）
STYLE_TRIGGER = [("post", "G", 6), ("tactical", "D", 5), ("counter", "E", 4),
                 ("story", "F", 3), ("question", "C", 2), ("simple", "H", 1)]

# ── 结构池（叙事顺序）────────────────────────────────────────────
STRUCTS = {
    "S01": ("反常现象型", "反常数据 → 正常认知 → 数据拆解 → 异常原因 → 反向证据 → 阿飞判断"),
    "S02": ("悬念递进型", "提出疑问 → 第一条证据 → 第二条证据 → 意外发现 → 最终判断"),
    "S03": ("双方对照型", "主队优势 → 主队隐患 → 客队优势 → 客队隐患 → 核心对抗 → 判断"),
    "S04": ("分类归因型", "共同主题 → 案例一及原因 → 案例二 → 案例三 → 横向比较 → 总结"),
    "S05": ("焦点主线型", "多场概览 → 核心比赛深拆 → 两场辅助对照 → 其余快评 → 核心观点"),
    "S06": ("结论先行型", "先亮判断 → 最关键证据 → 补充证据 → 不利因素 → 修正判断 → 比分参考"),
    "S07": ("状态演变型", "此前状态 → 近期变化 → 关键转折 → 当前问题 → 下一场的影响"),
    "S08": ("交叉验证型", "比较对象 → 共同对手 → 比赛表现 → 主客场修正 → 样本局限 → 判断"),
    "S09": ("风险拆解型", "表面优势 → 三大风险 → 风险影响 → 哪些可化解 → 判断"),
    "S10": ("论点反证型", "初始观点 → 支持证据 → 反向证据 → 两边权衡 → 修正结论"),
}
STRUCT_W = {
    "S01": {"anomaly": 3, "counter": 1},
    "S02": {"question": 3, "split": 1},
    "S03": {"balanced": 3, "tactical": 2},
    "S04": {"same_theme": 3},
    "S05": {"focus": 3},
    "S06": {"strong_view": 3, "simple": 1},
    "S07": {"form_change": 3, "story": 2, "post": 1},
    "S08": {"common_opp": 3},
    "S09": {"fav_risk": 3},
    "S10": {"split": 3, "counter": 2, "post": 1},
}
FEATURES = {
    "anomaly": "反常现象：主客倒挂 / 排名与状态反差 / 攻守失衡",
    "question": "有一个具体疑问：连续交锋、市场预期与表现矛盾",
    "balanced": "强弱接近、双方各有特点",
    "same_theme": "多场共享同一数据主题（需 ≥2 场）",
    "focus": "多场里有一场特别值得深拆（需 ≥3 场）",
    "strong_view": "观点鲜明、证据充分、读者熟悉",
    "form_change": "状态演变：连败反弹 / 换帅 / 伤员回归 / 密集赛程",
    "common_opp": "共同对手多、交叉资料丰富",
    "fav_risk": "热门占优但有明显隐患",
    "split": "模型与市场分歧 / 热冷争议",
    "tactical": "风格冲突明显（必须配 --tactical-source）",
    "counter": "反常识数据：常识说法被数据推翻",
    "story": "有可核实的连续故事线（必须配 --story-source）",
    "simple": "简单比赛、数据差异不大",
    "post": "赛后复盘（--stage post 自动带上）",
}

OPENINGS = ["反常数据切入", "疑问切入", "对位切入", "共同主题切入", "焦点切入",
            "结论先行", "故事场景切入", "比较对象切入", "风险切入", "观点切入",
            "纠偏切入", "复盘切入", "极简直述"]
OPEN_BY_STRUCT = {"S01": "反常数据切入", "S02": "疑问切入", "S03": "对位切入",
                  "S04": "共同主题切入", "S05": "焦点切入", "S06": "结论先行",
                  "S07": "故事场景切入", "S08": "比较对象切入", "S09": "风险切入",
                  "S10": "观点切入"}
OPEN_BY_STYLE = {"C": "疑问切入", "D": "对位切入", "E": "纠偏切入",
                 "F": "故事场景切入", "G": "复盘切入", "H": "极简直述"}
ENDINGS = ["总结观点", "悬念留白", "观点反问", "比赛观察点", "认错条件"]

STOCK = [r"我的判断是", r"站主队", r"站客队", r"防平局", r"说白了", r"老球迷都懂",
         r"问题来了", r"先给结论", r"这场有点意思", r"阿飞认为", r"真到了比赛里"]
STALE_OPEN = [r"^今天", r"有几场", r"这一批", r"本批", r"这几场里", r"这.场里", r"共同点"]


# ── 账本 ────────────────────────────────────────────────────────
def load() -> dict:
    data = {}
    if os.path.exists(HIST):
        with io.open(HIST, encoding="utf-8") as f:
            data = json.load(f)
    data.setdefault("articles", [])
    for a in data["articles"]:
        a.setdefault("scheme", "R53-v1")  # 旧结构池 ID，含义与新池不同，不参与新轮换
    return data


def engine_arts(data: dict) -> list:
    return [a for a in data["articles"] if a.get("scheme") == SCHEME]


def summarize(data: dict) -> dict:
    arts = engine_arts(data)
    styles = [a.get("style") for a in arts if a.get("style")]
    ab = [s for s in styles if s in ("A", "B")]
    return {
        "version": "AFEI-WRITING-ENGINE v1.0",
        "last_style": styles[-1] if styles else None,
        "last_ab": ab[-1] if ab else None,
        "last_structures": [a.get("structure") for a in arts if a.get("structure")][-RECENT:],
        "last_openings": [a.get("opening") for a in arts][-RECENT:],
        "last_ending": arts[-1].get("ending") if arts else None,
        "rotation_rule": {
            "style_default": "A_B_alternating",
            "special_styles": "content_driven",
            "structure_pool": 10,
            "avoid_recent_structure": RECENT,
            "avoid_repeated_opening": True,
        },
    }


def save(data: dict) -> None:
    data["articles"] = data["articles"][-KEEP:]
    data["engine"] = summarize(data)
    data["note"] = ("写作轮换账本（R62 双层轮换）：scheme=engine-v1 的记录参与新轮换；"
                    "scheme=R53-v1 为旧十结构池，ID 含义不同，只留档。只记已过 preflight 的稿。")
    tmp = HIST + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, HIST)


def ratios(arts: list) -> dict:
    win = [a.get("style") for a in arts if a.get("style")][-RATIO_WINDOW:]
    n = len(win) or 1
    c = Counter(win)
    return {k: c.get(k, 0) / n for k in STYLES}, len(win)


def age(seq: list, item: str) -> int:
    for i in range(len(seq) - 1, -1, -1):
        if seq[i] == item:
            return len(seq) - i
    return 10 ** 6


# ── 选择 ────────────────────────────────────────────────────────
def choose_style(feats: set, arts: list) -> tuple:
    share, n = ratios(arts)
    styles = [a.get("style") for a in arts if a.get("style")]
    last = styles[-1] if styles else None
    if "post" in feats:
        return "G", ["赛后稿固定走 G"], []
    cands = []
    for f, sid, base in STYLE_TRIGGER:
        if f in feats and sid != "G":
            deficit = STYLES[sid][2] - share[sid]
            score = base + deficit * 10 - (2 if sid == last else 0)
            cands.append((score, sid, f"{f} 触发 · 基础 {base} · 比例差 {deficit:+.0%}"
                          + (" · 上篇同风格 −2" if sid == last else "")))
    if cands:
        cands.sort(key=lambda x: -x[0])
        return cands[0][1], [cands[0][2]], cands
    ab = [s for s in styles if s in ("A", "B")]
    nxt = "B" if (ab and ab[-1] == "A") else "A"
    return nxt, [f"无特殊素材 → A/B 交替（上一篇基础口吻 {ab[-1] if ab else '无'}）"], []


def choose_structure(feats: set, matches: int, arts: list) -> list:
    used = [a.get("structure") for a in arts if a.get("structure")]
    recent = used[-RECENT:]
    rows = []
    for sid, w in STRUCT_W.items():
        if sid == "S04" and matches < 2:
            continue
        if sid == "S05" and matches < 3:
            continue
        if sid == "S08" and "common_opp" not in feats:
            continue
        fit = sum(v for k, v in w.items() if k in feats)
        pen = 0.0
        if sid in recent:
            pen = 2.5 if used and used[-1] == sid else 2.0
        rows.append((fit - pen, fit, pen, -age(used, sid), sid))
    rows.sort(key=lambda r: (-r[0], r[3], r[4]))
    return rows


def suggest_opening(style: str, sid: str, arts: list) -> str:
    last2 = [a.get("opening") for a in arts][-2:]
    for o in (OPEN_BY_STYLE.get(style), OPEN_BY_STRUCT.get(sid)):
        if o and o not in last2:
            return o
    for o in OPENINGS:
        if o not in last2:
            return o
    return OPENINGS[0]


def suggest_ending(arts: list) -> str:
    ends = [a.get("ending") for a in arts]
    last = ends[-1] if ends else None
    for e in ENDINGS:
        if e != last and not (e == "观点反问" and ends[-2:].count("观点反问") >= 1):
            return e
    return ENDINGS[0]


# ── 文章解析 ────────────────────────────────────────────────────
def parse_article(path: str) -> dict:
    text = io.open(path, encoding="utf-8").read()
    lines = text.splitlines()
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), "")
    paras, cur = [], []
    for l in lines:
        s = l.strip()
        if not s:
            if cur:
                paras.append(" ".join(cur)); cur = []
            continue
        cur.append(s)
    if cur:
        paras.append(" ".join(cur))
    body = [p for p in paras if not p.startswith(("# ", ">", "|"))]
    tail_re = re.compile(r"^(话题标签|标签|数据来源|免责声明|本文|内容为|#)")
    content = []
    for p in body:
        if tail_re.match(p) and not p.startswith("## "):
            break
        content.append(p)
    opening = next((p for p in content if not p.startswith("## ")), "")
    ending = next((p for p in reversed(content)
                   if not (p.startswith("## ") or "推荐比分" in p[:16])), "")
    sections, sec = [], None
    for p in content:
        if p.startswith("## "):
            sec = [p]; sections.append(sec)
        elif sec is not None:
            sec.append(p)
    return {"title": title, "opening": opening, "ending": ending,
            "sections": sections, "text": "\n".join(content)}


def classify_opening(s: str) -> str:
    head = "".join(re.split(r"(?<=[。！？])", s)[:2])
    if "？" in head or "?" in head:
        return "疑问切入"
    if re.search(r"先给结论|结论|我站|我更看好|不站方向", head):
        return "结论先行"
    if re.search(r"未必|都说|大家都|真的.{0,8}吗|别急着", head):
        return "纠偏切入"
    if re.search(r"赛前我|赛后|结果", head):
        return "复盘切入"
    if re.search(r"[0-9一二三四五六七八九十两]+.{0,12}(却|反而|倒是|可)", head):
        return "反常数据切入"
    if not re.search(r"[0-9]|[一二三四五六七八九十]场|[一二三四五六七八九十]个", head):
        return "故事场景切入"
    return "陈述切入"


def classify_ending(s: str) -> str:
    if s.rstrip().endswith(("？", "?")):
        return "观点反问"
    if re.search(r"如果.{0,20}(错|看走眼|被打脸)|认错", s):
        return "认错条件"
    if re.search(r"盯|看点|观察|留意", s):
        return "比赛观察点"
    if re.search(r"留个|悬念|等着看|再说", s):
        return "悬念留白"
    return "总结观点"


def classify_title(t: str) -> str:
    if "？" in t or "?" in t:
        return "问句式"
    if re.search(r"但|却|可是|不等于|未必", t):
        return "转折反差式"
    if re.search(r"我(更)?看好|我站|值得", t):
        return "观点陈述式"
    if re.search(r"[0-9一二三四五六七八九十]", t):
        return "数字陈述式"
    return "陈述式"


ARG_KEYS = [("排名", r"排第|积\S{0,3}分|排名"), ("主客", r"主场|客场"),
            ("近况", r"近五场|近5场|最近五场|近期"), ("交锋", r"交锋|碰面|交手"),
            ("伤停", r"伤停|停赛|缺阵|缺 ")]


def arg_signature(sec: list) -> tuple:
    txt = " ".join(sec[1:])
    pos = []
    for name, rx in ARG_KEYS:
        m = re.search(rx, txt)
        if m:
            pos.append((m.start(), name))
    return tuple(n for _, n in sorted(pos)[:3])


def bigram_jaccard(a: str, b: str) -> float:
    def grams(s):
        s = re.sub(r"\s+", "", s)[:120]
        return {s[i:i + 2] for i in range(len(s) - 1)}
    A, B = grams(a), grams(b)
    return len(A & B) / len(A | B) if A and B else 0.0


def analyze(path: str) -> dict:
    art = parse_article(path)
    data = load()
    me = os.path.normcase(os.path.abspath(path))
    arts = [a for a in engine_arts(data)
            if not a.get("path") or os.path.normcase(os.path.join(ROOT, a["path"])) != me]
    recent = arts[-RECENT:]
    hard, soft = [], []

    op_type = classify_opening(art["opening"])
    last_ops = [a.get("opening") for a in arts][-2:]
    if len(last_ops) == 2 and all(o == op_type for o in last_ops):
        hard.append(f"开头套路「{op_type}」已连用两篇，第三篇必须换")
    for rx in STALE_OPEN:
        if re.search(rx, art["opening"][:40]):
            soft.append(f"开头命中老套路「{rx.strip('^')}」：{art['opening'][:30]}…")
            break
    for a in recent:
        j = bigram_jaccard(art["opening"], a.get("opening_text", ""))
        if j >= 0.30:
            soft.append(f"开头与 {a.get('date')}《{a.get('title', '')[:18]}》相似度 {j:.2f}")

    sigs = [arg_signature(s) for s in art["sections"]]
    sigs = [s for s in sigs if len(s) >= 2]
    if len(sigs) >= 3:
        top, cnt = Counter(sigs).most_common(1)[0]
        if cnt / len(sigs) >= 0.6:
            hard.append(f"论证顺序流水线：{cnt}/{len(sigs)} 场都按「{' → '.join(top)}」排")
    heads = [s[1][:3] for s in art["sections"] if len(s) > 1]
    if len(heads) >= 3:
        h, c = Counter(heads).most_common(1)[0]
        if c >= 3:
            soft.append(f"{c} 场小节首句同一个开头「{h}…」（像模板标签）")

    for rx in STOCK:
        n = len(re.findall(rx, art["text"]))
        if n >= 3:
            soft.append(f"固定句式「{rx}」出现 {n} 次")

    plens = [len(p) for p in art["text"].split("\n") if not p.startswith("## ") and len(p) > 8]
    if len(plens) >= 6:
        cv = statistics.pstdev(plens) / (statistics.mean(plens) or 1)
        if cv < 0.30:
            soft.append(f"段落长度过于整齐（变异系数 {cv:.2f} < 0.30），节奏像流水线")

    end_type = classify_ending(art["ending"])
    ends = [a.get("ending") for a in arts]
    if ends and ends[-1] == end_type:
        soft.append(f"结尾方式「{end_type}」与上一篇相同")
    if end_type == "观点反问" and ends[-2:].count("观点反问") == 2:
        hard.append("连续第三篇以提问收尾")

    t_type = classify_title(art["title"])
    if arts and arts[-1].get("title_pattern") == t_type:
        soft.append(f"标题模式「{t_type}」与上一期相同")
    return {"art": art, "recent": recent, "hard": hard, "soft": soft,
            "opening": op_type, "ending": end_type, "title": t_type}


def check(path: str, strict: bool = False) -> int:
    r = analyze(path)
    art, recent, hard, soft = r["art"], r["recent"], r["hard"], r["soft"]
    op_type, end_type, t_type = r["opening"], r["ending"], r["title"]

    print("=" * 60)
    print(f"  轮换去重体检 · {os.path.basename(path)}")
    print("=" * 60)
    print(f"  开头 {op_type}｜结尾 {end_type}｜标题 {t_type}｜比赛小节 {len(art['sections'])}")
    print(f"  对照最近 {len(recent)} 篇（engine-v1 账本）："
          + ("、".join(f"{a.get('style')}/{a.get('structure')}/{a.get('opening')}" for a in recent) or "无"))
    for h in hard:
        print(f"  ❌ {h}")
    for s in soft:
        print(f"  ⚠️ {s}")
    if not hard and not soft:
        print("  ✅ 未发现重复套路")
    print("  提醒：去重不是换同义词，而是换信息组织方式。")
    return 1 if (hard and strict) else 0


# ── CLI ─────────────────────────────────────────────────────────
def cmd_list() -> None:
    data = load()
    arts = engine_arts(data)
    share, n = ratios(arts)
    styles = [a.get("style") for a in arts]
    structs = [a.get("structure") for a in arts]
    print(f"风格池（最近 {n} 篇实际占比 / 目标）")
    for k, (name, desc, tgt) in STYLES.items():
        print(f"  {k} {name:<7} {share[k]:>4.0%} / {tgt:.0%}   {desc}")
    print("\n结构池（次数 / 上次）")
    for sid, (name, flow) in STRUCTS.items():
        a = age(structs, sid)
        print(f"  {sid} {name:<6} {structs.count(sid)} 次  "
              f"{'未用过' if a >= 10 ** 6 else str(a) + ' 篇前':<6}  {flow}")
    print("\n最近 3 篇：" + ("；".join(
        f"{a.get('date')} {a.get('style')}/{a.get('structure')}/{a.get('opening')}/{a.get('ending')}"
        for a in arts[-RECENT:]) or "（engine-v1 账本为空）"))
    legacy = len(data["articles"]) - len(arts)
    if legacy:
        print(f"（另有 {legacy} 条 R53 旧池记录，只留档，不参与新轮换）")


def cmd_pick(a) -> None:
    feats = {f.strip() for f in (a.feat or "").split(",") if f.strip()}
    bad = feats - set(FEATURES)
    if bad:
        raise SystemExit(f"未知特征：{', '.join(sorted(bad))}（--features-help 看全表）")
    if a.stage == "post":
        feats.add("post")
    notes = []
    if "tactical" in feats and not a.tactical_source:
        feats.discard("tactical")
        notes.append("tactical 未给 --tactical-source → 不触发 D（R62：战术必须有资料支撑）")
    if "story" in feats and not a.story_source:
        feats.discard("story")
        notes.append("story 未给 --story-source → 不触发 F（R58：故事必须可核实）")
    data = load()
    arts = engine_arts(data)
    style, why, cands = choose_style(feats, arts)
    rows = choose_structure(feats, a.matches, arts)
    sid = rows[0][4]
    print("=" * 60)
    print("  AFEI-WRITING-ENGINE v1.0 · 选风格 + 选结构")
    print("=" * 60)
    print(f"  素材特征：{', '.join(sorted(feats)) or '（未给，建议先提炼素材再选）'}")
    for n_ in notes:
        print(f"  ⚠️ {n_}")
    print(f"\n  风格 → {style} {STYLES[style][0]}（{STYLES[style][1]}）")
    for w in why:
        print(f"    依据：{w}")
    for sc, s, d in cands[1:3]:
        print(f"    备选：{s} {STYLES[s][0]}  {sc:.1f}  {d}")
    if style == "H":
        print("    ℹ️ H 型极简快评：单独成稿（微头条/短图文）控制在 300–500 字，"
              "跑 preflight 时加 --short 或文件名带 _快评/_微头条/_短图文。")
    if style == "G":
        print("    ⚠️ 公开稿只写「赛前忽略了什么」，模型参数修正写进赛后校验 md（R55）。")
    print(f"\n  结构 → {sid} {STRUCTS[sid][0]}：{STRUCTS[sid][1]}")
    for sc, fit, pen, _, s in rows[:4]:
        print(f"    {s} {STRUCTS[s][0]:<6} 总分 {sc:>4.1f}（适配 {fit}" + (f" · 近期 −{pen}" if pen else "") + "）")
    if rows[0][1] == 0:
        print("    ⚠️ 没有任何结构命中素材特征 —— 先回去找这批比赛真正值得讲的点。")
    print(f"\n  开头建议：{suggest_opening(style, sid, arts)}　结尾建议：{suggest_ending(arts)}")
    print("  纪律：风格/结构不改方向与比分三档；写完跑 --check，过 preflight 后再 --record。")


def cmd_record(a) -> None:
    if a.backfill:
        # 引擎上线前的旧稿：只抽开头/结尾/标题做去重基线，风格与结构留空，不参与比例统计
        a.style = a.style if a.style in STYLES else None
        a.structure = a.structure if a.structure in STRUCTS else None
    else:
        if a.style not in STYLES:
            raise SystemExit("--record 需要 --style（A–H）")
        if a.structure not in STRUCTS:
            raise SystemExit("--record 需要 --structure（S01–S10）")
    art = parse_article(a.article) if a.article else {"title": a.title, "opening": "", "ending": ""}
    data = load()
    rec = {
        "id": "%s-%02d" % (a.date.replace("-", ""), len(data["articles"]) + 1),
        "scheme": SCHEME,
        "date": a.date,
        "title": a.title or art["title"],
        "teams": a.teams,
        "stage": a.stage,
        "style": a.style,
        "structure": a.structure,
        "opening": a.opening or classify_opening(art["opening"]),
        "opening_text": art["opening"][:120],
        "ending": a.ending or classify_ending(art["ending"]),
        "title_pattern": classify_title(a.title or art["title"]),
        "humor": a.humor,
        "column": a.column,
        "path": os.path.relpath(a.article, ROOT) if a.article else "",
        "status": "published",
    }
    if a.backfill:
        rec["backfill"] = True
    data["articles"].append(rec)
    save(data)
    sn = STYLES[rec["style"]][0] if rec["style"] else "（未标）"
    tn = STRUCTS[rec["structure"]][0] if rec["structure"] else "（未标）"
    print(f"已落账：{rec['style']} {sn} × {rec['structure']} {tn}"
          f"｜开头 {rec['opening']}｜结尾 {rec['ending']}｜标题 {rec['title_pattern']}"
          + ("｜回填基线" if a.backfill else ""))


def main() -> int:
    ap = argparse.ArgumentParser(description="AFEI-WRITING-ENGINE v1.0：风格 × 结构双层轮换")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--pick", action="store_true")
    ap.add_argument("--check", metavar="ARTICLE")
    ap.add_argument("--strict", action="store_true", help="--check 有硬问题时退出码 1")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--backfill", action="store_true",
                    help="引擎上线前的旧稿回填为去重基线（风格/结构可留空）")
    ap.add_argument("--features-help", action="store_true")
    ap.add_argument("--feat", default="")
    ap.add_argument("--matches", type=int, default=1)
    ap.add_argument("--stage", default="pre", choices=["pre", "post"])
    ap.add_argument("--tactical-source", default="")
    ap.add_argument("--story-source", default="")
    ap.add_argument("--article")
    ap.add_argument("--style")
    ap.add_argument("--structure")
    ap.add_argument("--opening", default="")
    ap.add_argument("--ending", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--teams", default="")
    ap.add_argument("--humor", default="")
    ap.add_argument("--column", default="", help="阿飞看球 / 阿飞拆局 / 阿飞复盘")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args()
    if a.features_help:
        for k, v in FEATURES.items():
            print(f"  {k:<12} {v}")
        return 0
    if a.list:
        cmd_list(); return 0
    if a.pick:
        cmd_pick(a); return 0
    if a.check:
        return check(a.check, a.strict)
    if a.record:
        cmd_record(a); return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
