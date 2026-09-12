# -*- coding: utf-8 -*-
"""
朱雀降AI原理库 + 本地启发式检测器(无次数限制)
================================================
⚠️ 本地检测是【代理指标】,不是朱雀模型本身——朱雀是深度学习模型,无法本地复刻。
   但朱雀抓的核心特征(语言统计指纹)和降AI改写目标高度重合,本地预检能把
   网页版(每天5次)用在刀刃上: 本地分高的段落先改,改完再用朱雀终检。

朱雀检测原理(逆向+公开资料整理, 2026-08-28):
──────────────────────────────────────────────
1. 【困惑度/突发度】(核心信号)
   - 困惑度 Perplexity: 语言模型对文本的"意外程度"。人写的句子用词更意外,
     AI倾向选最高概率词 → 困惑度低。
   - 突发度 Burstiness: 句长/句式的波动幅度。人类写作长短句交错、节奏跳跃,
     AI输出均匀平滑(句长方差小)。朱雀的"疑似AI"段落多数是"平滑且可预测"的段。
2. 【AI高频搭配词】
   训练数据里AI文本的n-gram分布: "值得注意的是/综上所述/总而言之/不仅…更是/
   彰显/赋能/深度融合/显而易见/毋庸置疑/首先其次最后"等,人写体育稿极少这样排比。
3. 【句式模板】
   - "数据不会说谎"-式金句收尾、每段主题句+展开的工整结构、破折号高频、
   - 三段式排比("一边是…一边是…")、精确而空洞的百分比表述。
4. 【段落级判定】segment_labels: 每段给 label(0人工/1AI/2疑似)+conf——
   说明模型在段落粒度上统计特征投票, 长段落更容易被平均成"平滑"→判AI。
   短句、口语词、具体名词(队名/人名/比分)密度高 → 人工信号。

本地启发式评分项(与朱雀信号相关性排序):
  A 句长方差(低=AI嫌)        B AI高频词表命中
  C 段落内句长均匀度          D 破折号/分号密度
  E 具体名词密度(队名/比分/百分比,高=人工信号,加分)
  F 口语锚点词(说白了/邪门/凑合/讲道理…高=加分)

使用:
  python zhuque_local_check.py --file "文章.md"
  输出: 全文本地AI嫌疑分 + 每段评分排行(先改最像AI的段落)
"""
import os
import re
import sys
import math
import json
import argparse

AI_PHRASES = [
    # 中文新闻体/AI高频
    '值得注意的是', '综上所述', '总而言之', '不仅如此', '不仅仅是', '更是',
    '彰显', '赋能', '深度融合', '显而易见', '毋庸置疑', '众所周知',
    '一方面', '另一方面', '换句话说', '整体来看', '综合来看',
    '不难发现', '可以说', '某种意义上', '在一定程度上', '与此同时',
    '值得一提的是', '需要指出的是', '不容忽视', '究其原因', '正因如此',
    '由此可见', '事实上', '显然', '既…也', '从某种角度',
    # humanizer 中文对应: 伪深度/意义拔高
    '标志着', '见证了', '承载着', '彰显着', '诠释了', '展现了…的',
    '成为…的关键', '起到…作用', '具有重要意义', '意义重大',
    '……的重要组成部分', '未来发展', '前景广阔', '未来可期',
    # 否定排比/三连结构触发词
    '不仅', '更是', '更是', '既是', '也是',
    # 自问自答
    '凭什么', '为什么?因为',
]
COLLOQUIAL = [
    '说白了', '邪门', '凑合', '讲道理', '先抛结论', '掰扯', '翻开',
    '摆在那', '写在脸上', '戏精', '打脸', '翻车', '上门', '回血',
    '老底', '老黄历', '硬闯', '咬下', '顶住', '崩', '来劲', '门道',
]
MODULE_PAT = re.compile(r'【[^】]{2,8}】')  # 【xx】模块标签
BRACKET_PAT = re.compile(r'〔|〕|《')

SPECIFIC_PAT = re.compile(
    r'[0-9]+比[0-9]+|[0-9]+:[0-9]+|[0-9]+(?:\.[0-9]+)?%|'
    r'第[0-9一二三四五六七八九十]+[轮名次场]|'
    r'[0-9]+(?:\.[0-9]+)?(?:球|个|分|场|胜|负|平|连)'
)


def split_sentences(par):
    s = re.split(r'(?<=[。!?!?])', par)
    return [x.strip() for x in s if len(x.strip()) >= 4]


def paragraph_score(par):
    """返回 (ai_suspicion 0-10, detail dict)"""
    sents = split_sentences(par)
    if not sents:
        return 0.0, {}
    lens = [len(s) for s in sents]
    mean_len = sum(lens) / len(lens)
    # A 句长方差(归一: cv=std/mean, 低→AI)
    if len(lens) > 1:
        std = math.sqrt(sum((x - mean_len) ** 2 for x in lens) / len(lens))
        cv = std / mean_len if mean_len else 0
        a = max(0.0, 3.0 - cv * 6)          # cv<0.2 → 满分3; cv>0.5 → 0
    else:
        # ⚠️ 2026-09-12 修正: 原逻辑"单句段一律 1.5 分"会把**单句短段**全判成 AI,
        #    而按头条排版规范(2-4 行一段)单句短段恰好是人写的强特征 → 属误判。
        #    改为看句子实际长度: ≤45 字的单句几乎不扣; 长单句(难读)才给嫌疑。
        a = 0.0 if len(sents[0]) <= 45 else 1.5
        cv = 0.0
    # B AI高频词
    hits = [w for w in AI_PHRASES if w in par]
    b = min(4.0, len(hits) * 0.8)
    # C 段落太长(>240字)且句多(>4) → 均匀嫌疑
    c = min(1.5, max(0.0, (len(par) - 240) / 200)) if len(sents) > 3 else 0
    # D 破折号/分号密度
    d = min(1.5, (par.count('——') + par.count(';') + par.count(';')) * 0.5)
    # E 数字流惩罚(2026-08-29朱雀实测修正: 均匀数字句是AI指纹, 不是人工信号)
    n_spec = len(SPECIFIC_PAT.findall(par))
    spec_ratio = n_spec / max(1, len(sents))
    e = min(2.0, spec_ratio * 1.2) if spec_ratio > 1.2 else 0
    # F 口语锚点(加分)
    n_col = sum(1 for w in COLLOQUIAL if w in par)
    f = -min(2.0, n_col * 0.7)
    # G 模板化结构惩罚(朱雀实测: 【】模块+工整节奏是头号信号)
    n_mod = len(MODULE_PAT.findall(par))
    g = min(3.5, n_mod * 0.9)
    # H 第二人称/对话感(强人工信号, 加分)
    n_you = sum(par.count(w) for w in ('你', '咱们', '别急', '掂量', '值多'))
    h = -min(1.5, n_you * 0.3)
    score = max(0.0, min(10.0, a + b + c + d + e + f + g + h))
    detail = {
        '句长cv': round(cv if len(lens) > 1 else 0, 2),
        'AI词': hits[:4],
        '句数': len(sents),
        '字数': len(par),
        '数据点': n_spec,
        '口语词': n_col,
        '模块标签': n_mod,
    }
    return score, detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', required=False, help='md/docx/txt')
    ap.add_argument('--top', type=int, default=8)
    ap.add_argument('--threshold', type=float, default=2.5, help='段落预警阈值')
    args = ap.parse_args()

    path = args.file
    if path and path.lower().endswith('.docx'):
        from docx import Document
        d = Document(path)
        paras = [p.text.strip() for p in d.paragraphs
                 if p.text.strip() and not p.text.strip().startswith(('![', '*图'))]
    elif path:
            raw = open(path, encoding='utf-8').read()
            paras = [p.strip() for p in re.split(r'\n+', raw)
                     if p.strip() and not p.strip().startswith(('![', '*图', '#', '|', '<!--'))]
    else:
        ap.error('需要 --file')

    scored = []
    for i, p in enumerate(paras):
        # ⚠️ 2026-09-12 修正: 原阈值 60 字会把"按头条规范压到 2-4 行"的短段全部跳过
        #    → 一段都没评分却输出 "0.0 分通过"(假阴性, 比高分更危险)。
        #    改为 24 字起评 + 下面加"评分覆盖率"保护。
        if len(p) < 24:      # 标题/标签/信息卡/短句跳过
            continue
        sc, detail = paragraph_score(p)
        scored.append((sc, i, p, detail))

    scored.sort(key=lambda x: -x[0])
    avg = sum(s for s, *_ in scored) / max(1, len(scored))
    print('=' * 60)
    print(f'【本地AI嫌疑分】全文均值: {avg:.1f}/10 (校准线: <2.5 可发 | 2.5-4 定点改 | >4 大改; 依据0829朱雀实测校准)')
    print(f'  评分段落 {len(scored)} 段 / 输入 {len(paras)} 段')
    print('  ⚠ 本地分是启发式代理指标, 与朱雀模型强相关但不等价; 终检用朱雀网页版(每日5次)')
    print('=' * 60)
    if len(scored) < 3:
        print('\n⚠ 警告: 参与评分的段落少于 3 段 —— 本分数不具参考性, 请勿据此判断"通过"。')
        print('  (短段落文体请以朱雀网页版终检为准; 或确认 --file 指向的是正文 md 而非摘要文件)')
    hits = [x for x in scored if x[0] >= args.threshold]
    if hits:
        print(f'\nAI嫌疑段落 Top {min(args.top, len(hits))} (按嫌疑分排序, 先改这些):')
        for sc, i, p, det in hits[:args.top]:
            print(f'\n  [{sc:.1f}分] 段#{i + 1} {det}')
            print(f'    {p[:70]}…')
    else:
        print(f'\n无≥{args.threshold}分段落, 全文本地预检通过。')


if __name__ == '__main__':
    main()
