# -*- coding: utf-8 -*-
"""
本地 AI 文本检测器 v1.0（纯 Python，零第三方依赖）
====================================================
原理（统计特征启发式，与云端大模型判别器互补）：
  1) 句长均匀性 —— AI 文本句长分布平稳（变异系数低），人类文本长短句交替（变异系数高）
  2) 书面连接词密度 —— AI 爱用 然而/因此/此外/同时/总之 等书面对接词
  3) AI 套话短语命中 —— 值得注意的是/综上所述/不难发现 等 AI 高频填充词
  4) 语气词/口语密度 —— 人类文本 呢/吧/嘛/说白了/说句不好听的 更多
  5) 破折号/冒号密度 —— AI 爱用 —— 和 ： 做解释性补充
  6) 排比结构 —— AI 爱相邻短句同开头（并列推进）
  7) 句长相邻变化率 —— 人类文本节奏起伏大

评分：0-100（AI 痕迹概率）。<30 低 / 30-55 中 / >55 高。
定位：发布前快速自查的“第一道筛”，权威判定请叠加 朱雀AIGC检测（云端 API）等多源交叉。

用法：
  python ai_detect.py 文本文件.md            # 输出报告 + 可疑句 TOP
  python ai_detect.py 文本文件.md --json      # JSON 输出（供脚本集成）
"""
import re
import sys
import json
import statistics

# 控制台编码兜底（Windows GBK 控制台编不了 emoji 路径等字符）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ---------------- 特征词典 ----------------
AI_PHRASES = [
    "值得注意的是", "总的来说", "不难发现", "需要指出的是", "从某种程度上说",
    "与此同时", "换句话说", "综上所述", "进一步来说", "由此可见", "换言之",
    "总而言之", "归根结底", "众所周知", "值得一提的是", "不可否认", "这一现象",
]
CONNECTIVES = [
    "然而", "因此", "此外", "同时", "而且", "并且", "总之", "但是", "不过",
    "所以", "因为", "由于", "尽管", "虽然", "即便", "基于", "随着", "通过",
    "与此同时", "进而", "从而", "因而", "由此可见",
]
PARTICLES = [
    "呢", "吧", "嘛", "啊", "呀", "哈", "哦", "啦", "呗", "唉", "嘿",
    "说白了", "说句不好听的", "讲真", "老实说", "其实吧", "你说", "谁信",
    "啧啧", "就是", "真的",
]

SENT_END = "。！？!?；;\n"
PUNC_AI = ["——", "：", "；", "()", "（ ）"]


def split_sentences(text):
    """按句末标点/换行切句，返回 [句长, 句文本] 列表"""
    sents = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in SENT_END:
            s = buf.strip()
            if len(s) >= 2:
                sents.append(s)
            buf = ""
    if buf.strip() and len(buf.strip()) >= 2:
        sents.append(buf.strip())
    return sents


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def analyze(text):
    n_char = max(len(text), 1)
    sents = split_sentences(text)
    lens = [len(s) for s in sents]
    report = {}

    # 1) 句长均匀性（变异系数 CV）：AI 低
    if len(lens) >= 4 and statistics.mean(lens) > 0:
        cv = statistics.stdev(lens) / statistics.mean(lens)
        f_sent = clamp((0.55 - cv) / 0.35)          # cv=0.20→1.0, cv=0.55→0
    else:
        cv, f_sent = None, 0.5
    report["句长变异系数CV"] = (round(cv, 3) if cv is not None else None)

    # 2) 书面连接词密度（每100字）
    d_conn = sum(text.count(c) for c in CONNECTIVES) / n_char * 100
    f_conn = clamp((d_conn - 1.0) / 2.0)             # 1.0→0, 3.0→1.0

    # 3) AI 套话短语命中数
    hit_phrases = [p for p in AI_PHRASES if p in text]
    f_phr = min(len(hit_phrases) / 4.0, 1.0)

    # 4) 语气词/口语密度（每100字）：人类更高 → AI 分反向
    d_part = sum(text.count(c) for c in PARTICLES) / n_char * 100
    f_part = 1.0 - clamp((d_part - 0.5) / 2.5)       # 0.5→1.0(AI), 3.0→0(人)

    # 5) 破折号/冒号密度（每100字）
    d_punc = (text.count("——") + text.count("：")) / n_char * 100
    f_punc = clamp((d_punc - 0.5) / 2.0)

    # 6) 排比结构：相邻短句同开头（≥2字）比例
    same = 0
    for i in range(1, len(sents)):
        a, b = sents[i - 1], sents[i]
        common = 0
        for x, y in zip(a, b):
            if x == y:
                common += 1
            else:
                break
        if common >= 2:
            same += 1
    r_para = same / max(len(sents) - 1, 1)
    f_para = clamp((r_para - 0.15) / 0.30)

    # 7) 相邻句长变化率：人类起伏大 → AI 分反向
    if len(lens) >= 4 and statistics.mean(lens) > 0:
        diffs = [abs(lens[i] - lens[i - 1]) for i in range(1, len(lens))]
        v_adj = statistics.mean(diffs) / statistics.mean(lens)
        f_var = 1.0 - clamp((v_adj - 0.35) / 0.45)
    else:
        v_adj, f_var = None, 0.5

    # 加权合成
    weights = {
        "句长均匀": 0.25, "连接词密度": 0.15, "套话短语": 0.20,
        "语气词缺失": 0.15, "标点AI倾向": 0.10, "排比结构": 0.10, "节奏平缓": 0.05,
    }
    scores = {
        "句长均匀": f_sent, "连接词密度": f_conn, "套话短语": f_phr,
        "语气词缺失": f_part, "标点AI倾向": f_punc, "排比结构": f_para, "节奏平缓": f_var,
    }
    total = sum(weights[k] * scores[k] for k in weights)
    score = round(total * 100, 1)

    if score < 30:
        verdict = "低（像人写）"
    elif score < 55:
        verdict = "中（有AI痕迹，建议降AI）"
    else:
        verdict = "高（AI痕迹重，必须降AI）"

    # 可疑句 TOP（含套话 / 连接词密集 / 与相邻句长几乎相同的句簇）
    suspicious = []
    for s in sents:
        reasons = []
        if any(p in s for p in AI_PHRASES):
            reasons.append("含AI套话")
        c_count = sum(s.count(c) for c in CONNECTIVES)
        if c_count >= 2 and len(s) < 60:
            reasons.append("连接词密集")
        if len(s) > 90:
            reasons.append("超长句")
        if reasons:
            suspicious.append((s, "; ".join(reasons)))
    suspicious = suspicious[:10]

    return {
        "chars": n_char, "sentences": len(lens),
        "metrics": {
            "cv_sentlen": round(cv, 3) if cv is not None else None,
            "connective_per100": round(d_conn, 2),
            "ai_phrase_hits": hit_phrases,
            "particle_per100": round(d_part, 2),
            "punc_per100": round(d_punc, 2),
            "parallel_ratio": round(r_para, 2),
            "adj_len_var": round(v_adj, 3) if v_adj is not None else None,
        },
        "features": {k: round(v, 2) for k, v in scores.items()},
        "score": score, "verdict": verdict,
        "suspicious": suspicious,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # 去掉 markdown 符号噪音（表格/标题/代码块对句长特征影响大）
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    body = re.sub(r"\|[^\n]*\|", " ", body)
    body = re.sub(r"^#+.*$", "", body, flags=re.M)
    body = re.sub(r"[*_`>]", "", body)
    r = analyze(body)
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    print("=" * 46)
    print(f"文件: {path}")
    print(f"字符数 {r['chars']} | 句数 {r['sentences']}")
    print("-" * 46)
    m = r["metrics"]
    print(f"句长变异系数 CV : {m['cv_sentlen']}   (AI<0.35, 人>0.5)")
    print(f"书面连接词/100字: {m['connective_per100']}")
    print(f"AI套话命中       : {m['ai_phrase_hits']}")
    print(f"语气词/100字     : {m['particle_per100']}   (人更多)")
    print(f"破折号冒号/100字 : {m['punc_per100']}")
    print(f"排比起始比       : {m['parallel_ratio']}")
    print(f"相邻句长变化率   : {m['adj_len_var']}")
    print("-" * 46)
    print("特征分: " + "  ".join(f"{k}={v:.2f}" for k, v in r["features"].items()))
    print("=" * 46)
    print(f"AI痕迹评分: {r['score']} / 100  →  判定: {r['verdict']}")
    print("=" * 46)
    if r["suspicious"]:
        print("可疑句 TOP（降AI重点）:")
        for s, why in r["suspicious"]:
            print(f"  [{why}] {s[:60]}")
    print()
    print("提示: 启发式检测=第一道筛, 权威判定请叠加朱雀AIGC检测(云端API)多源交叉")


if __name__ == "__main__":
    main()
