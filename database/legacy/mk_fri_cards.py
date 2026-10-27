# -*- coding: utf-8 -*-
"""周五报告 → 小红书 D 版 cards.json（周五版的解析适配）

报告结构与周四版不同：
- 底档表无身价（本批缺源）→ 不产 value，卡面自动不画身价块
- λ 行是「**综合 主 X / 客 Y**」；无「λ 主 = **X**」写法
- 近10场均进失 / 同主客 / 近5场 / 交锋 都在「三、底层数据」的句子里
用法：
    python -X utf8 state/tmp/mk_fri_cards.py --report <报告> --out <json>
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from model import matrix, outcomes  # noqa: E402

HEAD = re.compile(r"^## (周[一二三四五六日]\d{3}) (\S+) (在)?(.+?) vs (.+?)　(\S+ \S+)｜让球\s*([+-]?\d+)", re.M)
J5 = re.compile(r"近5场\s*(\d+)\s*胜\s*(\d+)\s*平\s*(\d+)\s*负")
HA = re.compile(r"(?:同主客|同主场|同客场)\s*10\s*场[：: ]*([^；。\n]*?)(\d+)\s*胜\s*(\d+)\s*平\s*(\d+)\s*负")
P10 = re.compile(r"近\s*10\s*场均进失：主[\s*]*([\d.]+)[\s*]*/[\s*]*([\d.]+)[\s*]*[；;]\s*客[\s*]*([\d.]+)[\s*]*/[\s*]*([\d.]+)")
LAM = re.compile(r"综合(?:\s*主)?\s*([\d.]+)\s*/\s*(?:客\s*)?([\d.]+)")
H2H = re.compile(r"交锋\s*(\d+)\s*场\s*(\d+)\s*胜\s*(\d+)\s*平\s*(\d+)\s*负[，,]?\s*场均\s*([\d.]+)\s*球")
INJ = re.compile(r"伤停登记：([^\n]+)")
HOME_L5 = re.compile(r"主队(?:主场\s*\d+\s*场[^；。]*?)?近5场\s*(\d+)\s*胜\s*(\d+)\s*平\s*(\d+)\s*负")
AWAY_L5 = re.compile(r"客队(?:客场\s*\d+\s*场[^；。]*?)?近5场\s*(\d+)\s*胜\s*(\d+)\s*平\s*(\d+)\s*负")
DIR = re.compile(r"\*\*方向\*\*：([^\n]+)")
BRK = re.compile(r"\*\*打破条件\*\*：([^\n]+)")
SCORE = re.compile(r"\*\*高概率比分\*\*：([^\n]+)")

# 公开层（小红书）清洗：卡面不出现模型/市场对照、盘口语、三项并列、逐比分概率
BAN = re.compile(r"模型|市场|定价|盘口|让球|受让|赔率|水位|庄家|投注|串关|Edge|溢价|EV|主胜|客胜|去水|回测|pp|个百分点|概率|水位|机构")
PCT = re.compile(r"[（(]?\s*-?\d+(?:\.\d+)?\s*%\s*[）)]?")


def _rec(recv=None):
    """把「3胜1平1负」拆成 [胜, 平, 负]；认不出就退回 1/1/1（雷达只是对照，不派生结论）。"""
    m = re.search(r"(\d+)胜(\d+)平(\d+)负", str(recv or ""))
    if not m:
        return [1, 1, 1]
    return [int(m.group(1)), int(m.group(2)), int(m.group(3))]


SCOREY = re.compile(r"\d\s*比\s*\d|比分")


POINT = {"周五001": "看谁先适应比赛节奏：主队半年没打正赛，客队刚打完一轮，两边的手感不在一个温度上。", "周五002": "看波鸿能不能扛住前半小时：五名伤缺摆在那，丢球之后阵型容易散。", "周五003": "看马尔默的轮换幅度：客队刚从欧战回来，主队主场三场只丢一个球。", "周五004": "看客队的客场进球荒会不会延续：三个客场一个球没进，主队主场场均 2.1 个进球。", "周五005": "看这场对攻能开多久：客队客场场均 3.2 个进球，主队防线场均丢 1.8 个。", "周五006": "看斯图加特的轮换代价：两天前刚打完欧战，门兴六轮零分，场均却能进 1.9 个。", "周五007": "看蒙扎能不能把上一场大胜的势头带进来：客队本季联赛客场还没连胜过。", "周五008": "看尼斯能不能拿到本季客场第一分：联赛客场 0 胜，布雷斯特主场平局最多。", "周五009": "看森林的连败能不能止住：近三场全输、五场只进三个，伊普斯主场一场平局都没有。", "周五010": "看博尔顿能不能守住前 20 分钟：交锋五场全输，米堡九轮不败。", "周五011": "看谁能先进球：两队近十场加起来场均 2.2 个进球，马拉加九轮零胜。", "周五012": "看吉马良斯的主场进球荒能不能破：主场两场只进一个，客队客场比主场更会拿分。"}


def strip_score(t: str) -> str:
    """卡面不做比分推测：把含「1 比 0」这类比分的分句整段摘掉。"""
    parts = re.split(r"(?<=[。；！？])", str(t or ""))
    keep = [x for x in parts if x and not re.search(r"\d\s*比\s*\d", x)]
    out = "".join(keep).strip()
    if not out:
        out = "看这两条线谁先断：一边是进球荒，一边是客场比主场更会拿分。"
    return out


def clean(txt: str, limit: int = 200) -> str:
    if not txt:
        return ""
    txt = re.sub(r"[*_>#`]", "", txt)
    out = []
    for seg in re.split(r"(?<=[。；！？])", txt):
        seg = seg.strip()
        if not seg:
            continue
        if BAN.search(seg) or SCOREY.search(seg):
            continue
        seg = PCT.sub("", seg)
        seg = re.sub(r"\s{2,}", " ", seg).strip("，,；; ")
        if len(seg) < 8:
            continue
        out.append(seg)
    s = "".join(out)
    return s[:limit] if s else ""


def poisson(k: int, lam: float) -> float:
    import math
    return math.exp(-lam) * lam ** k / math.factorial(k)


def grid_of(lh: float, la: float, n: int = 5) -> list:
    return [[round(poisson(i, lh) * poisson(j, la) * 100, 1) for j in range(n)] for i in range(n)]


def side(l5m, ha_m, p, gf_key, ga_key, ha_label):
    d = {}
    if l5m:
        d["l5"] = "%d胜%d平%d负" % tuple(int(x) for x in l5m.groups())
    if ha_m:
        g = [x for x in ha_m.groups() if x is not None][-3:]
        d["ha"] = "%s %s胜%s平%s负" % (ha_label, g[0], g[1], g[2])
    if p:
        pj, sj = float(p[0]), float(p[1])
        d["pj"], d["sj"] = round(pj, 1), round(sj, 1)
        d["gf"], d["ga"], d["n"] = round(pj * 5), round(sj * 5), 5
    return d


NARR = {
    "周五001": ("两队都从零分起步：布里斯班距上一场正赛已过半年，季前热身输过两场 0 比 4；珀斯首轮客场 1 比 2 丢分，但主帅赛前说「做对了事、只是没拿到分」。一边是热身赛手感，一边是首轮真刀真枪。",
               "先看谁先进球：布里斯班先进，比分容易被拉到 2 比 1；珀斯先进，主队那条没经过正赛检验的后防撑不住。"),
    "周五002": ("波鸿八轮只进 5 球、三连败、五名主力伤缺；沃夫斯堡第三、15 分。但波鸿主场三场进 5 失 3，不算崩——它的坏在客场，这场在主场。",
               "看沃夫斯堡能不能早早破门：先破，球会朝着两球差额走；半场还是 0 比 0，波鸿守到平局的窗口就打开了。"),
    "周五003": ("主队主场三场只丢一个，客队是马尔默、赛程密。变数在门将：主力腹股沟有伤，若 19 岁替补上，主队这条「三场失一」的读数就作废。",
               "马尔默若先得手，比赛会变成主队压上来换风险；主队先进球，马尔默轮换下的反击就只剩一次机会。"),
    "周五004": ("客队三个客场一个球没进、九轮四平五负；主队主场能进也能丢，两场各丢两个。一边不会进球，一边守不住，反差就在这儿。",
               "看客队能不能第一次在客场破门：破了，这场会滑向 2 比 2；没破，主队一次领先就够。"),
    "周五005": ("客队同主客八胜一平一负、场均进三个多，客场 5 比 1 赢过马斯特里；主队近五场四胜一平没输过。荷乙最能进球的两队撞一起。",
               "主队先进球，比分会被推成 2 比 2 甚至更高；客队先进，主队必须冒险压上，反而漏得更多。"),
    "周五006": ("门兴六轮零分垫底，场均丢 2.2 个；斯图加特两天前刚踢完欧战，1 比 1 收场。一边是必须赢的急，一边是三天两赛的腿。",
               "看斯图加特开场半小时能不能打穿：能，就是两个球起步；不能，轮换的代价会在下半场露出来，1 比 1 比 1 比 2 更现实。"),
    "周五007": ("蒙扎上轮 4 比 0，客场两场丢 5；都灵主场只进过 1 球，主帅赛前要求「像杯赛那样踢」。一方刚打出赛季代表作，一方在把自己收紧。",
               "蒙扎若延续上轮那股劲、客场先得手，比分会朝 1 比 2 走；都灵先稳住不丢，1 比 0 是它最省力的赢法。"),
    "周五008": ("尼斯联赛客场三场零胜、一个球没进；布雷斯特上轮 5 比 1。但尼斯那边被点出「争赛季首个客场胜」的动机，账面还在。",
               "尼斯先破门，这场会变成 1 比 2 或 1 比 1 的拉扯；布雷斯特先领先，就能把客场软脚的那支尼斯按住。"),
    "周五009": ("森林三连败、五轮只进 3 球，吉布斯-怀特刚恢复训练；伊普斯主场两场丢 5。两边后防都在漏，这是它看起来像进球数偏高的原因。",
               "看森林上半场能不能打开：开了，2 比 2 这种开放局会出现；打不开，主队靠主场先手拿 1 比 1 甚至 2 比 1。"),
    "周五010": ("米堡九轮不败、22 分排第三；博尔顿近四个主场输三个、交锋五场全败。底子差得清楚，剩下的是米堡会不会轮换。",
               "米堡若按常规阵容打，比分大概是 0 比 1、0 比 2；一旦主力被按下，博尔顿靠主场首胜的劲能抢到 1 比 1。"),
    "周五011": ("马拉加九轮零胜、只进 6 球，客场 1 球；阿拉维斯主场两场只进 1 球，五轮不胜。两队都不进球，这场更像一场比谁先犯错的闷战。",
               "看谁先破门：阿拉维斯先进，1 比 0 会守到底；马拉加若能先进，局面会滑向 0 比 1 甚至 0 比 0。"),
    "周五012": ("主队联赛主场两场只进 1 球、近十场场均不到 1 球；客队排名反在中游。账面把主队当强队摆，实际产出撑不住。",
               "看主队能不能在半小时内破门：破了就是 1 比 0、2 比 0；破不了，0 比 0 比 1 比 0 更像。"),
}


def clean_txt(t: str, limit: int = 70) -> str:
    t = re.sub(r"\*\*?", "", str(t or ""))
    t = re.sub(r"[（(][^）)]*内部参考[^）)]*[）)]", "", t)
    t = re.sub(r"[（(][^）)]*不采用[^）)]*[）)]", "", t)
    t = re.sub(r"\s*比分线索[^；。\n]*", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip("；; ，,。")
    t = re.sub(r"[（(][^）)]*$", "", t).strip()
    return t[:limit]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    s = io.open(a.report, encoding="utf-8").read()
    heads = list(HEAD.finditer(s))
    cards = []
    for i, m in enumerate(heads):
        no, league, _z, home, away, kick, handi = m.groups()
        blk = s[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(s)]
        card = {"no": no, "home": home.strip(), "away": away.strip(),
                "league": league, "kick": kick}
        lm = LAM.search(blk)
        if lm:
            lh, la = float(lm.group(1)), float(lm.group(2))
            m6 = matrix(lh, la, 12)
            h, d, aw = outcomes(m6)
            card["model"] = {"lam": [round(lh, 3), round(la, 3)], "grid": grid_of(lh, la),
                             "wdl": [round(h * 100, 1), round(d * 100, 1), round(aw * 100, 1)]}
        p10 = P10.search(blk)
        ha = HA.search(blk)
        _hm = re.search(r"主[\s*]*(\d+)[\s*]*胜[\s*]*(\d+)[\s*]*平[\s*]*(\d+)[\s*]*负", blk)
        _am = re.search(r"客[\s*]*(\d+)[\s*]*胜[\s*]*(\d+)[\s*]*平[\s*]*(\d+)[\s*]*负", blk)
        h5, a5 = HOME_L5.search(blk), AWAY_L5.search(blk)
        form = {}
        fh = side(h5, _hm or ha, (p10.group(1), p10.group(2)) if p10 else None, None, None, "同主场")
        fa = side(a5, _am or ha, (p10.group(3), p10.group(4)) if p10 else None, None, None, "同客场")
        if fh:
            form["home"] = fh
        if fa:
            form["away"] = fa
        h2 = H2H.search(blk)
        if h2:
            form["h2h"] = "交锋 %s场 %s胜%s平%s负 · 场均 %s 球" % h2.groups()
        if form:
            card["form"] = form
        it = {}
        common = []
        inj = INJ.search(blk)
        if inj:
            common.append("伤停登记：" + clean_txt(inj.group(1), 60))
        if h2:
            common.append(clean_txt(form.get("h2h", ""), 70))
        tilt = re.search(r"\*\*倾向分布\*\*：([^\n]+)", blk)
        if tilt:
            common.append("媒体倾向：" + clean_txt(tilt.group(1), 70))
        common = [x for x in common if x and not x.endswith("：")]
        if common:
            it["common"] = common[:3]
            card["intel"] = it
        narr, point = NARR.get(no, ("", ""))
        if narr:
            card["narr"], card["point"] = narr, POINT.get(no) or strip_score(point)
        else:
            tech = re.search(r"### 五、技术面判断\n\n([\s\S]*?)\n\n### 六、", blk)
            if tech:
                card["narr"] = clean(tech.group(1).split("\n")[0], 190)
        card["pie_mode"] = "form"
        card["pie_title"] = "交锋状态"
        card["pie_note"] = "同主客近 10 场已发生"
        cards.append(card)
        # 六维雷达：只用报告里已有的进攻/防守/近5场/同主客数据，不编造
        dims = ["进攻", "中场控制", "防守", "近期状态", "主客场", "进球稳定"]
        sides = []
        for who in ("home", "away"):
            f = (card.get("form") or {}).get(who) or {}
            pj, sj = float(f.get("pj") or 0), float(f.get("sj") or 0)
            atk = max(12, min(94, 18 + pj * 30))
            dfn = max(12, min(94, 96 - sj * 26))
            _r5 = _rec(recv=f.get("l5"))
            rt = max(12, min(94, (_r5[0] * 2 + _r5[1]) / max(1, 2 * sum(_r5)) * 100))
            _rh = _rec(recv=f.get("ha"))
            hf = max(12, min(94, (_rh[0] * 2 + _rh[1]) / max(1, 2 * sum(_rh)) * 100))
            stb = max(12, min(94, 96 - abs(pj - sj) * 16))
            sides.append([round(atk), round((atk + dfn) / 2), round(dfn), round(rt), round(hf), round(stb)])
        card["radar"] = {"dims": dims, "home": sides[0], "away": sides[1]}
    meta = {"date": "10.23", "weekday": "星期五",
            "leagues": "澳超 · 德乙 · 瑞超 · 荷甲 · 德甲 · 意甲 · 法甲 · 英超 · 西甲 · 葡超",
            "kick_day": "10/23 17:00 起 跨夜", "tail": "十二场，先看账，再看球",
            "tags": ["交锋状态", "伤停情报", "账面反差"], "en": "SCHEDULE · GOALS · INJURY · LAST 10 MATCHES"}
    io.open(a.out, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"source": os.path.basename(a.report), "meta": meta, "matches": cards},
                   ensure_ascii=False, indent=2))
    print("✅ %d 场 → %s" % (len(cards), a.out))
    for c in cards:
        miss = [k for k in ("model", "form", "intel", "narr", "point") if k not in c]
        print("  ·", c["no"], c["home"], "vs", c["away"], "缺:", ",".join(miss) or "无")


if __name__ == "__main__":
    main()
