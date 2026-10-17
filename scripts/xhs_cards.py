# -*- coding: utf-8 -*-
"""小红书图文卡片矩阵（每场一张 3:4 图，纯 Pillow，无需联网、无需 Playwright）

为什么要它
----------
头条/公众号发长文，小红书是**图文**平台：一屏一张图、3:4 竖版、一图一个信息块。
所以「矩阵」＝把一次在售档里挑出的场次，**每场渲一张卡**，再配一段可直接粘贴的文案。

两种用法
--------
1) 有编辑内容的（推荐）：给一份 JSON（立场 / 三向概率 / 比分 / 战意 / 信号），出全套卡 + 文案
     python scripts/xhs_cards.py --input 📝文章/20261014/小红书/cards.json --out 📝文章/20261014/小红书
2) 只出「市场版矩阵」（没有立场，纯定价+机构概率，用来铺量/当底稿）
     python scripts/xhs_cards.py --auto --num 周二 --limit 9 --out state/xhs_auto

傻瓜用法：双击仓库根的 **`小红书出图.cmd`**。

合规
----
渲染前用 `📚知识库/模型脚本/check_article.py` 的 HARD_BANNED / SOFT_BANNED 逐字段查
（赔率·盘口·打穿·北京时间·今天·明天… 一律拒绝出图），命中就报字段名并停。
"""
import argparse
import importlib.util
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

W, H = 1080, 1440                      # 小红书 3:4
BG = (14, 18, 32)
CARD = (23, 29, 49)
LINE = (38, 46, 74)
TEXT = (244, 247, 255)
MUTED = (152, 163, 192)
ACCENT = (77, 163, 255)
ACCENT2 = (255, 209, 102)
DANGER = (255, 107, 107)

FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_R = r"C:\Windows\Fonts\msyh.ttc"
FONT_FALLBACK = [r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc"]

_font_cache = {}


def _font_path(bold):
    cands = [FONT_B if bold else FONT_R] + FONT_FALLBACK
    for p in cands:
        if os.path.exists(p):
            return p
    raise RuntimeError("找不到中文字体（试过 %s）" % "、".join(cands))


def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(_font_path(bold), size)
    return _font_cache[key]


# --------------------------------------------------------------------------- 词表（动态复用真源）
def load_banned():
    src = os.path.join(ROOT, "📚知识库", "模型脚本", "check_article.py")
    try:
        spec = importlib.util.spec_from_file_location("_ca", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return list(mod.HARD_BANNED), list(mod.SOFT_BANNED)
    except Exception:
        return (["赔率", "盘口", "庄家", "泊松", "蒙特卡洛", "EV", "凯利", "打穿", "穿盘",
                 "北京时间", "今天", "明天", "昨天", "刚刚", "今晚", "昨晚", "本月", "几个小时"],
                ["投注", "下注", "串关", "过关", "稳胆", "上车", "跟单", "重注", "梭哈", "彩票",
                 "博彩", "荐彩", "稳赢", "必中", "私信", "微信号", "赌球", "让球盘", "水位", "赌"])


HARD, SOFT = load_banned()


AUDIT_LABELS = {
    "title": "标题", "xhs_title": "小红书标题", "subtitle": "封面副标题", "cover_items": "封面要点",
    "cover_hint": "封面提示", "cover_tail": "读图说明", "stance": "立场", "stance_label": "立场标签",
    "contradiction": "核心矛盾", "focus": "本次看点", "will": "战意", "signal": "信号", "note": "补充",
}


def audit(cards):
    """递归查禁用词（含 contradiction/focus/form/radar 等嵌套字段）；返回 [(场次, 字段, 词, 等级)]。"""
    hits = []

    def walk(who, name, val):
        if isinstance(val, dict):
            for k, v in val.items():
                walk(who, "%s.%s" % (name, k), v)
        elif isinstance(val, (list, tuple)):
            for i, v in enumerate(val):
                walk(who, "%s[%d]" % (name, i), v)
        elif isinstance(val, str) and val:
            for w in HARD:
                if w in val:
                    hits.append((who, name, w, "硬红线"))
            for w in SOFT:
                if w in val:
                    hits.append((who, name, w, "软红线"))

    for c in cards:
        who = c.get("no") or c.get("title") or "封面"
        for key, val in c.items():
            walk(who, AUDIT_LABELS.get(key, key), val)
    return hits


# --------------------------------------------------------------------------- 绘制小工具
NO_HEAD = "、。，；：？！）】》」』”’%…·"


def wrap(draw, text, f, max_w):
    """中文按字断行 + 简单禁则（不让标点出现在行首）。"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if draw.textlength(cur + ch, font=f) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    for i in range(1, len(lines)):
        while lines[i] and lines[i][0] in NO_HEAD:
            lines[i - 1] += lines[i][0]
            lines[i] = lines[i][1:]
    return lines


def fit(draw, text, max_w, size, bold=True, min_size=28):
    while size > min_size:
        f = font(size, bold)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return font(min_size, bold)


def chip(draw, x, y, text, f, fg, bg, padx=22, pady=10, radius=14):
    tw = draw.textlength(text, font=f)
    th = f.size
    draw.rounded_rectangle([x, y, x + tw + padx * 2, y + th + pady * 2], radius=radius, fill=bg)
    draw.text((x + padx, y + pady - 2), text, font=f, fill=fg)
    return x + tw + padx * 2


def bar(draw, x, y, w, h, ratio, color, bg=LINE):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    ww = max(h, int(w * max(0.0, min(1.0, ratio))))
    draw.rounded_rectangle([x, y, x + ww, y + h], radius=h // 2, fill=color)


def base_canvas():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # 顶部一条渐变色带（纯色块拼，避免 numpy 依赖）
    for i in range(8):
        a = 1.0 - i / 8.0
        col = tuple(int(BG[k] + (ACCENT[k] - BG[k]) * a * 0.55) for k in range(3))
        d.rectangle([0, i * 3, W, i * 3 + 3], fill=col)
    return img, d


def footer(d, card):
    y = H - 118
    d.line([48, y - 18, W - 48, y - 18], fill=LINE, width=2)
    f_small = font(26)
    d.text((48, y), card.get("source", "数据来源：中国体育官方数据平台"), font=f_small, fill=MUTED)
    brand = card.get("brand", "@阿飞·赛博聊球")
    bw = d.textlength(brand, font=font(28, True))
    d.text((W - 48 - bw, y - 2), brand, font=font(28, True), fill=ACCENT)
    d.text((48, y + 40), "仅供参考，请理性看待比赛。", font=f_small, fill=MUTED)
    tags = card.get("tags", "#足球前瞻 #数据分析 #赛博聊球")
    tw = d.textlength(tags, font=font(26, True))
    d.text((W - 48 - tw, y + 42), tags, font=font(26, True), fill=ACCENT2)


def header(d, card, idx, total):
    f = font(30, True)
    x = 48
    x = chip(d, x, 56, card.get("league", "足球"), f, (10, 20, 38), ACCENT2, 20, 8)
    if card.get("no"):
        x += 14
        x = chip(d, x, 56, card["no"], f, TEXT, CARD, 20, 8, 12)
    right = "%s   %d/%d" % (card.get("kick", ""), idx, total)
    fr = font(28)
    d.text((W - 48 - d.textlength(right, font=fr), 62), right, font=fr, fill=MUTED)


def vs_block(d, card):
    y = 168
    home, away = card.get("home", "主队"), card.get("away", "客队")
    f_vs = font(48, True)
    fh = fit(d, home, 420, 84, True, 44)
    fa = fit(d, away, 420, 84, True, 44)
    wh, wa = d.textlength(home, font=fh), d.textlength(away, font=fa)
    wvs = d.textlength(" VS ", font=f_vs)
    total = wh + wa + wvs
    x = (W - total) / 2
    d.text((x, y + (84 - fh.size) / 2), home, font=fh, fill=TEXT)
    d.text((x + wh, y + 12), " VS ", font=f_vs, fill=MUTED)
    d.text((x + wh + wvs, y + (84 - fa.size) / 2), away, font=fa, fill=TEXT)
    # 主客标注
    f_s = font(26)
    d.text((48, y + 96), "主队", font=f_s, fill=MUTED)
    aw = d.textlength("客队", font=f_s)
    d.text((W - 48 - aw, y + 96), "客队", font=f_s, fill=MUTED)


def stance_block(d, card):
    y = 340
    text = card.get("stance", "")
    if not text:
        return y
    label = card.get("stance_label") or "我的判断"
    f_lab = font(28)
    f = fit(d, text, W - 200, 60, True, 34)
    tw = d.textlength(text, font=f)
    box_h = 118
    d.rounded_rectangle([48, y, W - 48, y + box_h], radius=24, fill=(22, 34, 60))
    d.rounded_rectangle([48, y, 54, y + box_h], radius=3, fill=ACCENT2)
    d.text((80, y + 22), label, font=f_lab, fill=MUTED)
    d.text((80, y + 56), text, font=f, fill=ACCENT2)
    return y + box_h + 34


def probs_block(d, card, y):
    mine = card.get("probs_mine")
    mkt = card.get("probs_mkt")
    if not mine:
        return y
    names = card.get("probs_names", ["主胜", "平", "客胜"])
    d.text((48, y), "三向概率", font=font(30, True), fill=TEXT)
    if mkt:
        lab = "我 / 机构"
    else:
        lab = "机构"
    f_r = font(26)
    d.text((W - 48 - d.textlength(lab, font=f_r), y + 4), lab, font=f_r, fill=MUTED)
    y += 52
    colw = (W - 96 - 32) / 3
    for i in range(3):
        x = 48 + i * (colw + 16)
        p_mine = float(mine[i]) if mine else 0.0
        p_mkt = float(mkt[i]) if mkt else 0.0
        d.text((x, y), names[i], font=font(28), fill=MUTED)
        d.text((x, y + 42), "%.1f%%" % p_mine, font=font(52, True), fill=ACCENT)
        bar(d, x, y + 116, colw, 14, p_mine / 100.0, ACCENT)
        if mkt:
            d.text((x, y + 146), "机构 %.1f%%" % p_mkt, font=font(26), fill=MUTED)
            bar(d, x, y + 186, colw, 10, p_mkt / 100.0, (120, 132, 160))
    return y + 240


def score_block(d, card, y):
    sc = card.get("score") or []
    if not sc:
        return y
    labels = ["首选", "次选", "防范"]
    d.text((48, y), "高概率比分", font=font(30, True), fill=TEXT)
    y += 50
    x = 48
    for i, s in enumerate(sc[:3]):
        f = font(38, True)
        txt = "%s %s" % (labels[i], s)
        col = ACCENT if i == 0 else TEXT
        x = chip(d, x, y, txt, f, col, CARD, 26, 12, 16) + 16
    return y + 100


def text_block(d, card, y, label, text, color=TEXT, dot=ACCENT):
    if not text:
        return y
    d.rounded_rectangle([48, y + 6, 62, y + 20], radius=4, fill=dot)
    d.text((76, y), label, font=font(28, True), fill=MUTED)
    y += 44
    f = font(32)
    for ln in wrap(d, text, f, W - 96)[:2]:
        d.text((48, y), ln, font=f, fill=color)
        y += 44
    return y + 18


def render_card(card, idx, total, out_path):
    img, d = base_canvas()
    header(d, card, idx, total)
    vs_block(d, card)
    y = stance_block(d, card)
    y = probs_block(d, card, y)
    y = score_block(d, card, y)
    y = text_block(d, card, y, "战意", card.get("will", ""), dot=ACCENT2)
    y = text_block(d, card, y, "信号", card.get("signal", ""), dot=ACCENT)
    if card.get("note"):
        y = text_block(d, card, y, "补充", card["note"], MUTED, MUTED)
    footer(d, card)
    img.save(out_path, quality=95)
    return out_path


def render_cover(card, total, out_path):
    img, d = base_canvas()
    header(d, card, 1, total)
    y = 172
    d.text((48, y), card.get("cover_kicker") or "图文｜今日前瞻", font=font(30, True), fill=ACCENT2)
    y += 60
    title = card.get("title", "")
    f = font(66, True)
    for ln in wrap(d, title, f, W - 96):
        d.text((48, y), ln, font=f, fill=TEXT)
        y += 84
    y += 12
    if card.get("subtitle"):
        f2 = font(34)
        for ln in wrap(d, card["subtitle"], f2, W - 96):
            d.text((48, y), ln, font=f2, fill=MUTED)
            y += 46
    y += 30
    items = card.get("cover_items") or []
    if items:
        d.rounded_rectangle([48, y, W - 48, y + 60 + 62 * len(items)], radius=24, fill=CARD)
        yy = y + 30
        for it in items:
            f3 = font(34, True)
            d.text((80, yy), "·", font=f3, fill=ACCENT)
            d.text((110, yy), it, font=font(34), fill=TEXT)
            yy += 62
        y = y + 60 + 62 * len(items) + 46
    d.line([48, y, W - 48, y], fill=LINE, width=2)
    y += 36
    hint = card.get("cover_hint") or "下面每场一张图：判断 · 三向概率 · 高概率比分 · 战意 · 信号"
    f4 = font(30)
    for ln in wrap(d, hint, f4, W - 96):
        d.text((48, y), ln, font=f4, fill=MUTED)
        y += 46
    # 底部固定一块「读图说明」把版面撑起来（也可用 cover_tail 覆盖）
    tail = card.get("cover_tail") or ("读图：概率左边「我」是后台模型算的，右边「机构」是官方固定奖金折算；"
                                      "比分三档只给方向。右滑看每场判断 →")
    ft = font(29)
    tl = wrap(d, tail, ft, W - 128)
    ph = 40 + 44 * len(tl)
    top = H - 118 - 34 - ph
    d.rounded_rectangle([48, top, W - 48, top + ph], radius=20, fill=CARD)
    d.rounded_rectangle([48, top, 54, top + ph], radius=3, fill=ACCENT)
    ty = top + 22
    for ln in tl:
        d.text((80, ty), ln, font=ft, fill=MUTED)
        ty += 44
    footer(d, card)
    img.save(out_path, quality=95)
    return out_path


# --------------------------------------------------------------------------- 输入
def load_input(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cards = data.get("matches") or []
    for c in cards:
        for k in ("title", "tags", "source", "brand", "stance_label", "cover_kicker"):
            c.setdefault(k, data.get(k, ""))
        c["tags"] = c.get("tags") or data.get("tags", "#足球前瞻 #数据分析 #赛博聊球")
        c["source"] = c.get("source") or data.get("source", "数据来源：中国体育官方数据平台")
        c["brand"] = c.get("brand") or data.get("brand", "@阿飞·赛博聊球")
    return data, cards


def safe(name):
    return re.sub(r'[\\/:*?"<>|\s]+', "", name)


def auto_cards(num=""):
    """从本地盘口库（state/odds.sqlite）出「市场版」卡：只讲机构定价，不含立场。"""
    import odds_snapshot as osnap
    c = osnap.conn(osnap.DEFAULT_DB)
    rows = c.execute("""SELECT match_id, match_num, kickoff, league, home, away, market, line, h, d, a
                        FROM quote WHERE taken_at=(SELECT MAX(taken_at) FROM snap)
                        ORDER BY kickoff""").fetchall()
    out = []
    for mid, num_, kick, lg, hm, aw, mk, line, h, d, a in rows:
        if mk != "胜平负":
            continue
        if num and num not in (num_ or ""):
            continue
        p, _vig = osnap.devig([h, d, a])
        out.append({
            "no": num_, "league": lg, "kick": (kick or "")[5:16].replace("-", "/"),
            "home": hm, "away": aw, "stance": "", "probs_mine": [round(x, 1) for x in p],
            "score": [], "will": "", "signal": "",
        })
    return {"title": "今日在售：机构定价一览", "matches": out}


# --------------------------------------------------------------------------- 出图主流程
def caption_text(data, cards):
    """小红书正文（可直接粘贴）。HTML 版渲染器也复用这个函数。"""
    caps = []
    # caption_title：只给文案用的标题（封面仍读 xhs_title）——2026-10-16 用户「只修改文案就行」
    if data.get("caption_title") or data.get("xhs_title"):
        # 2026-10-16 用户定：小红书标题必须带日期（20 字内）
        _t = data.get("caption_title") or data["xhs_title"]
        _has_date = bool(re.search(r"\d{1,2}\s*[/月.\-]\s*\d{1,2}", _t))
        caps += ["【标题】%s（%d 字，小红书上限 20%s）"
                 % (_t, len(_t), "" if _has_date else "，⚠️ 缺日期"), ""]
    # caption_para（逐场分析段落，2026-10-16 用户给模板）在场时，正文首行与卡片说明都省掉
    manual = [str(c.get("caption_para") or "").strip() for c in cards]
    has_manual = any(manual)
    if not has_manual:
        caps += ["【正文】", data.get("title", ""), ""]
    else:
        caps += ["【正文】", ""]
    per = int(data.get("per_match_cards") or 1)
    mode = data.get("card_mode") or ""
    if mode == "data":
        # 2026-10-13 二审仍不过后的定版：正文**只做纯技术/数据描述**——不猜比分、不给胜率方向、不提模型推演
        # 2026-10-16：八场批次正文会顶到小红书 1000 字上限（实测 1028）→ 超过 6 场自动用紧凑措辞
        compact = len(cards) > 6
        if not has_manual:
            caps += ["每场两张图：数据卡（战绩 / 雷达 / 看点）＋后台模型卡（胜率 / 比分概率热力图）。"
                     if per >= 2 else
                     ("每场一张图：战绩 · 雷达 · 主客场攻防数据 · 看点" if compact else
                      "每场一张图：近期战绩 · 六维雷达 · 主客场攻防数据 · 数据看点"), ""]
        for c, para in zip(cards, manual):
            if para:
                caps.append("%s 对 %s：%s" % (c.get("home", ""), c.get("away", ""), para))
                caps.append("")
                continue
            f = c.get("form") or {}
            h, a = f.get("home") or {}, f.get("away") or {}
            seg = []
            for s in (h, a):
                if s.get("name"):
                    seg.append("%s%s（场均进 %.1f 失 %.1f）"
                               % (s["name"], str(s.get("ha") or "").strip(),
                                  float(s.get("pj") or 0), float(s.get("sj") or 0)))
            line = "%s vs %s：" % (c.get("home", ""), c.get("away", "")) + "、".join(seg) + "。"
            rd = c.get("radar") or {}
            dims, rh, ra = rd.get("dims") or [], rd.get("home") or [], rd.get("away") or []
            if dims and len(dims) == len(rh) == len(ra):
                i = max(range(len(dims)), key=lambda k: abs(float(rh[k]) - float(ra[k])))
                line += (("雷达最大差：%s %.0f 对 %.0f。" if compact else
                          "六维雷达里差得最大的是%s %.0f 对 %.0f。")
                         % (dims[i], rh[i], ra[i]))
            hh = str(f.get("h2h_short") or "").strip()
            if hh:
                line += "交锋：%s。" % hh
            caps.append(line)
            caps.append("")
        while caps and caps[-1] == "":
            caps.pop()
    elif per >= 2:
        caps += ["每场 %d 张图：①判断卡（核心矛盾 · 三向概率 · 高概率比分）"
                 "②战绩卡（近期战绩对比 · 本次看点）③深读卡（六维雷达对比 · 战意 · 信号）" % per, ""]
    else:
        caps += ["每场一张图，一图看完：核心矛盾 · 三向概率 · 高概率比分 · 两队近期战绩 · "
                 "六维雷达对比 · 本次看点 · 战意 · 信号", ""]
    if mode != "data":
        for c in cards:
            caps.append("%s %s vs %s：%s" % (c.get("no", ""), c.get("home", ""), c.get("away", ""),
                                             c.get("stance") or "看机构定价"))
            if c.get("score"):
                caps.append("高概率比分：首选%s，次选%s，防范%s。" % tuple(c["score"][:3]))
    src = data.get("source", "")
    if mode == "data" and ("中国体育" in src or "彩票" in src or not src):
        src = "数据来源：公开赛事数据"
    src = src or "数据来源：公开赛事数据"
    tail = ("以上为公开赛果数据与技术面整理，只做数据对比，不含胜负与比分判断，不构成任何购买建议。"
            if mode == "data" else "仅供参考，请理性看待比赛。")
    caps += ["", data.get("tags", "#足球前瞻 #数据分析 #赛博聊球"), src, tail,
             "", "【发布窗口】主档 10:30–13:00（避开 16:00–19:00，见 R39）"]
    return "\n".join(caps) + "\n"


def write_caption(data, cards, outdir):
    """把文案写到 outdir/文案.md，返回路径。"""
    p = os.path.join(outdir, "文案.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(caption_text(data, cards))
    return p


def run(input_path=None, auto=False, num="", limit=0, out=""):
    if input_path:
        data, cards = load_input(input_path)
        outdir = out or os.path.dirname(os.path.abspath(input_path))
    else:
        data = auto_cards(num)
        cards = data["matches"]
        outdir = out or os.path.join(ROOT, "state", "cache", "xhs_auto")

    if limit:
        cards = cards[:limit]
    if not cards:
        print("没有可出的场次。")
        return [], outdir
    os.makedirs(outdir, exist_ok=True)

    hits = audit([dict(data, **{})] + cards)
    if hits:
        print("❌ 有禁用词，拒绝出图（真源 📚知识库/模型脚本/check_article.py）：")
        for no, field, w, lvl in hits:
            print("   [%s] %s ← 「%s」（%s）" % (no, field, w, lvl))
        sys.exit(2)

    total = len(cards) + (1 if data.get("title") else 0)
    made = []
    idx = 1
    if data.get("title"):
        p = os.path.join(outdir, "01_封面.png")
        made.append(render_cover(dict(data, matches=cards), total, p))
        idx = 2
    for c in cards:
        name = "%02d_%s_%svs%s.png" % (idx, safe(c.get("no", "")), safe(c.get("home", "主")),
                                       safe(c.get("away", "客")))
        made.append(render_card(c, idx, total, os.path.join(outdir, name)))
        idx += 1

    # 配套文案（小红书正文可直接粘贴）
    cap_path = write_caption(data, cards, outdir)

    print("✅ 出图 %d 张 + 文案 1 份 → %s" % (len(made), outdir))
    for m in made:
        print("   %s" % os.path.basename(m))
    print("   %s" % os.path.basename(cap_path))
    return made, outdir


# --------------------------------------------------------------------------- 傻瓜菜单
def find_card_files():
    base = os.path.join(ROOT, "📝文章")
    out = []
    if os.path.isdir(base):
        for d in sorted(os.listdir(base), reverse=True):
            p = os.path.join(base, d, "小红书", "cards.json")
            if os.path.exists(p):
                out.append(p)
    return out


def _pause():
    try:
        input("（回车返回菜单）")
    except (EOFError, KeyboardInterrupt):
        pass


def cmd_menu():
    last_dir = {"v": None}
    while True:
        files = find_card_files()
        newest = files[0] if files else None
        print("")
        print("=" * 66)
        print("   阿飞说球 · 小红书图文卡片矩阵（每场一张 3:4 图）")
        print("   产出：PNG + 可直接粘贴的文案；不联网、不需要任何 Key")
        print("=" * 66)
        if newest:
            print("   1   出一批（默认最新：%s）" % os.path.relpath(newest, ROOT))
        else:
            print("   1   出一批（还没有 cards.json，可用 3 或让 agent 写一批）")
        print("   2   选一批（列出全部 cards.json）")
        print("   3   只出「市场版」矩阵（本地盘口库全部在售场次，不含立场）")
        print("   4   打开最近一次的输出目录")
        print("   0   退出")
        print("=" * 66)
        try:
            c = input("请输入序号后回车：").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return
        if c in ("0", "q", "quit", "exit"):
            print("已退出。")
            return
        try:
            if c == "1":
                if not newest:
                    print("没有 cards.json。可让 agent 按 📚知识库/写作指南/小红书图文卡片.md 写一批。")
                else:
                    _, d = run(input_path=newest)
                    last_dir["v"] = d
                _pause()
            elif c == "2":
                if not files:
                    print("还没有 cards.json。")
                else:
                    for i, p in enumerate(files, 1):
                        print("   %d) %s" % (i, os.path.relpath(p, ROOT)))
                    pick = input("输入序号（回车取消）：").strip()
                    if pick.isdigit() and 1 <= int(pick) <= len(files):
                        _, d = run(input_path=files[int(pick) - 1])
                        last_dir["v"] = d
                _pause()
            elif c == "3":
                num = input("只出哪个编号段（如 周二，直接回车=全部在售）：").strip()
                _, d = run(auto=True, num=num)
                last_dir["v"] = d
                _pause()
            elif c == "4":
                d = last_dir["v"] or os.path.join(ROOT, "📝文章")
                if hasattr(os, "startfile"):
                    os.startfile(d)
                else:
                    print("输出目录：%s" % d)
                _pause()
            else:
                print("没看懂这个序号，再输一次。")
        except KeyboardInterrupt:
            print("\n已中断，回到菜单。")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="小红书图文卡片矩阵（每场一张 3:4 图）")
    ap.add_argument("--input", help="编辑内容 JSON（立场/概率/比分/战意/信号）")
    ap.add_argument("--auto", action="store_true", help="从本地盘口库自动出「市场版」矩阵")
    ap.add_argument("--num", default="", help="auto 模式：只取编号含该字串的场次（如 周二）")
    ap.add_argument("--limit", type=int, default=0, help="最多出几张场次卡（0=不限）")
    ap.add_argument("--out", default="", help="输出目录（默认与 input 同目录 / auto 时 state/xhs_auto）")
    ap.add_argument("--menu", action="store_true", help="双击启动的交互菜单")
    a = ap.parse_args()

    if a.menu:
        cmd_menu()
        return
    if not a.input and not a.auto:
        ap.error("要么 --input（编辑版），要么 --auto（市场版），要么 --menu（菜单）")
    run(input_path=a.input if not a.auto else None, auto=a.auto, num=a.num,
        limit=a.limit, out=a.out)


if __name__ == "__main__":
    main()
