# -*- coding: utf-8 -*-
"""
多场串烧前瞻生成器(通用版)
用法: 改 CFGS 列表(每个元素为 config 路径 + 可选 h2h 交锋数据)后运行
产出: 串烧 md + docx(含对比图: 偏差对比/交锋对比/攻防对比, 自动嵌入)
依赖: afei_generator.py 的 run_model / matplotlib(微软雅黑)
"""
import json
import os
import sys
from datetime import date

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

from docx import Document
from docx.shared import Pt, Inches

BASE = r'D:\Hermes\football'
TOOL_DIR = os.path.join(BASE, '阿飞说球', '02_工具')
sys.path.insert(0, TOOL_DIR)
from afei_generator import run_model  # noqa: E402

# ============ 配置区: 每场 = (config路径, 标题段名, 开场时间, 交锋数据, extra段落列表, 三个小节标题) ============
CFGS = [
    (os.path.join(TOOL_DIR, 'match_configs', '赫根vs米亚尔比.json'),
     "赫根 vs 米亚尔比", "01:00",
     {'label': '赫根 vs 米亚尔比(同主客交锋)', 'w': 4, 'd': 4, 'l': 2,
      'note': '赫根主场对米亚尔比10次4胜4平2负,但最近两次在自家门口全被零封(0:3、0:1)'},
     [
         "赫根排第4,20轮8胜8平4负。",
         "主场10场4胜4平2负,进17失17,说白了是个平手账。",
         "米亚尔比那边是塌方,近10场1胜1平8负,进6失22。",
         "场均只进0.6个。讲道理,他们客场能带走1分都算赚。",
         "所以这场球的矛盾很清楚。一边是米亚尔比五连败、场均0.6球的塌方,一边是赫根主场对他们的两连败。你说这球该信哪一边?",
         "模型和市场这场没吵架,主胜62.3%对59.1%,Edge校准只剩0.2个点。",
         "分歧在让1球那道门槛上。",
         "市场给赫根赢到2球以上35.4%,模型给38.5%,全样本基准27%。",
         "米亚尔比近10次交手赢了5次,是赫根的真克星。",
         "两次到访赫根,他们都是零封带分走的。这条老路他们熟。",
         "赫根赛季8平,20轮里8次没能把优势换成3分。",
         "平赔4.10落在砍平局那一档,历史平赔3.5以上的场次平局率只有12%。",
     ],
     ("赫根那边的账本", "克星这条线", "比分落在哪一档")),
    (os.path.join(TOOL_DIR, 'match_configs', '柏林联合vs沙尔克04.json'),
     "柏林联合 vs 沙尔克04", "02:30",
     {'label': '柏林联合 vs 沙尔克04(近6场)', 'w': 1, 'd': 4, 'l': 1,
      'note': '近6次交手4平,柏林联合主场3次交手全是平局(0胜3平0负)'},
     [
         "两队2轮都没赢过。",
         "柏林联合1平1负,进3球丢7球;沙尔克04也是1平1负,进0球丢3球。",
         "上轮沙尔克主场0比0逼平拜仁。防线是硬的,进攻是真哑。",
         "柏林联合那串近10场数字基本是废的。7月热身赛,他们连阿劳、耶拿这种低级别球队都输,回到联赛才在主场3比3追平法兰克福。沙尔克反过来,数字被热身赛刷高了。",
         "模型主胜42.0%,市场43.2%。客胜35.6%对31.2%,方向两边一致。",
         "说白了,这是一场没有热门的均势局。",
         "让1球这头,市场给柏林联合赢到2球以上只有21.3%,低于全样本的27%。",
         "沙尔克受让之后不落下风56.0%,高于全样本的50%。",
         "平局这边的信号是叠着的。交锋6次4平,同主客交锋3次全平,平赔3.45正好落在平局率47%那一档。",
         "沙尔克联赛2轮零进球,可防线顶住过拜仁。受让1球这条路,他们是走得通的。",
         "柏林联合近10场1胜4平5负,数字里全是7月热身赛输球的影子。",
     ],
     ("两队都还没开张", "交锋簿里的4场平", "沙尔克能不能进球")),
]
TITLE = "周五004+007:米亚尔比8负却克赫根,双0胜谁先开张?"
TAGS = "#瑞超 #德甲 #赫根 #米亚尔比 #柏林联合 #沙尔克04"
INFO_CARD = [
    "【对阵】赫根(主)vs米亚尔比 — 周五004 | 柏林联合(主)vs沙尔克04 — 周五007",
    "【赛事】瑞超 2026 常规赛第21轮 | 德甲 2026/2027 常规赛第3轮",
    "【时间】2026-09-12 01:00 / 02:30 北京时间(深夜连场)",
    "【场地】赫根主场 / 柏林联合主场",
    "【天气】待赛前更新",
]
OPENING = "\n\n".join([
    "周五两场深夜球,先把结论摆出来。",
    "004那场,市场把赫根压到1.50,可数据里躺着两个反向信号。",
    "近10次碰面,赫根4胜1平5负,主场近两次还被米亚尔比零封。你说这场有没有门道?",
    "007那场更怪,柏林联合和沙尔克04都没开张。",
    "2轮下来,一个进3丢7,一个进0丢3,市场照样把让球线开到柏林联合让1球。",
    "一边是崩盘客队撞克星魔咒,一边是双0胜球队比谁先开张。",
    "模型给出的答案都在下面。",
])
ENDING_HOOK = "克星魔咒和双0胜的僵局,你觉得哪一边会先破?评论区留下你的判断,周六我们一起复盘这两场。"
SUMMARY = "\n\n".join([
    "双场对比,一句话总结。004那场市场是清醒的,1.50的价格和模型几乎重合,分歧只在让1球那道门槛上。真正的变数是米亚尔比这条克星线。",
    "007那场两队都还没开张,让球线开到1球本身就偏深。平赔3.45又站在平局高产的那一档。",
    "一个看克星会不会再灵一次,一个看谁先把0胜撕掉。",
])

FOOTER = [
    "【数据来源】数据取自竞彩官方(竞彩网 sporttery.cn)及公开体育数据库,测算由阿飞个人足球数据模型独立推演。",
    "",
    "【免责声明】本文为个人数据模型推演,属体育赛事分析交流,不构成任何购彩及投注建议。足球是圆的,请理性看待数据,适度娱乐。",
]

# 输出目录: 04_赛事文章/<YYYY-MM>/<串烧名> (按产出月份自动归档)
OUT_DIR = os.path.join(BASE, '阿飞说球', '04_赛事文章', date.today().strftime('%Y-%m'), '周五深夜双场串烧_瑞超德甲')
os.makedirs(os.path.join(OUT_DIR, 'charts'), exist_ok=True)

# 中文字体
for f in [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\simsun.ttc']:
    if os.path.exists(f):
        fm.fontManager.addfont(f)
        matplotlib.rcParams['font.family'] = fm.FontProperties(fname=f).get_name()
        break
matplotlib.rcParams['axes.unicode_minus'] = False
BLUE, RED, GRAY = '#2b7bba', '#d62728', '#7f7f7f'


def run_all():
    cfgs, models = [], []
    for item in CFGS:
        path, name, t, h2h, extra = item[0], item[1], item[2], item[3], item[4]
        labels = item[5] if len(item) > 5 else None
        c = json.load(open(path, encoding='utf-8'))
        m = run_model(c)
        cfgs.append((c, name, t, h2h, extra, labels))
        models.append(m)
    return cfgs, models


def chart_deviation(cfgs, models, out):
    """图1: 双场模型 vs 市场偏差对比"""
    fig, axes = plt.subplots(1, len(cfgs), figsize=(5.6 * len(cfgs), 4.5))
    if len(cfgs) == 1:
        axes = [axes]
    labels = ['主胜', '平局', '客胜']
    x = np.arange(3)
    w = 0.35
    for ax, it, m in zip(axes, cfgs, models):
        c, name, t, h2h, extra = it[0], it[1], it[2], it[3], it[4]
        model = [m['pH'] * 100, m['pD'] * 100, m['pA'] * 100]
        mkt = [m['pM']['H'] * 100, m['pM']['D'] * 100, m['pM']['A'] * 100]
        ax.bar(x - w / 2, model, w, label='泊松模型', color=BLUE)
        ax.bar(x + w / 2, mkt, w, label='市场隐含', color=RED, alpha=0.85)
        ax.set_title(name, fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=11)
        ax.set_ylim(0, max(max(model), max(mkt)) + 12)
        ax.set_ylabel('概率 %')
        for i in range(3):
            ax.text(i - w / 2, model[i] + 0.8, f'{model[i]:.0f}', ha='center', fontsize=9, color=BLUE)
            ax.text(i + w / 2, mkt[i] + 0.8, f'{mkt[i]:.0f}', ha='center', fontsize=9, color=RED)
        e = (m['pH'] - m['pM_cal']['H']) * 100
        note = f"Edge {e:+.0f}%"
        ax.text(0.02, 0.95, note, transform=ax.transAxes, fontsize=10, color='#8a6d00',
                bbox=dict(boxstyle='round', fc='#fff8dc', ec='#d4b106'))
    axes[0].legend(fontsize=10, loc='upper right')
    fig.suptitle('串烧双场:模型 vs 市场胜平负偏差对比', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()


def chart_h2h(cfgs, out):
    """图2: 双场交锋克星对比(支持无交锋=首次碰面场景)"""
    fig, axes = plt.subplots(1, len(cfgs), figsize=(5.6 * len(cfgs), 4.5))
    if len(cfgs) == 1:
        axes = [axes]
    for ax, it in zip(axes, cfgs):
        c, name, t, h2h, extra = it[0], it[1], it[2], it[3], it[4]
        r = [h2h['w'], h2h['d'], h2h['l']]
        if sum(r) == 0:
            # 首次交锋: 无历史数据, 画信息卡
            ax.text(0.5, 0.62, '历史首次交锋', ha='center', va='center',
                    fontsize=20, fontweight='bold', color=GRAY)
            ax.text(0.5, 0.38, '无历史数据可比\n主场权重首次放大', ha='center', va='center',
                    fontsize=11, color='#555555')
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(False)
        else:
            bars = ax.bar(['胜', '平', '负'], r, color=[BLUE, GRAY, RED])
            for b, v in zip(bars, r):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.1, str(v), ha='center', fontsize=12, fontweight='bold')
            ax.set_ylim(0, max(r) + 1.2)
        ax.set_title(f"{h2h['label']}\n{h2h['note']}", fontsize=11, fontweight='bold')
    fig.suptitle('串烧双场:交锋克星剧本对比', fontsize=14, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()


def chart_attack(cfgs, out):
    """图3: 四队攻防对比(所有队)"""
    teams, gf, ga = [], [], []
    for it in cfgs:
        c, name, t, h2h, extra = it[0], it[1], it[2], it[3], it[4]
        for k in ['home', 'away']:
            teams.append(c['teams'][k]['name'])
            gf.append(c['teams'][k]['gf'])
            ga.append(c['teams'][k]['ga'])
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(teams))
    w = 0.35
    b1 = ax.bar(x - w / 2, gf, w, label='场均进球', color=BLUE)
    b2 = ax.bar(x + w / 2, ga, w, label='场均失球', color=RED, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(teams, fontsize=11)
    ax.set_ylim(0, max(gf + ga) + 0.5)
    ax.set_ylabel('近10场场均')
    ax.legend(fontsize=10)
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.03, f'{b.get_height():.1f}',
                ha='center', fontsize=9)
    ax.set_title('各队攻防数据对比(近10场)', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()


def safe_name(s):
    """Windows 文件名安全化: 半角冒号等非法字符转全角"""
    return s.replace(':', '：').replace('*', '＊').replace('?', '？').replace('"', '＂').replace('<', '＜').replace('>', '＞').replace('|', '｜')


def main():
    cfgs, models = run_all()

    # 历史案例参考(知识库检索, 写稿参考, 不进文章)
    try:
        from kb.kb_core import kb_search, match_query
        for it, m in zip(cfgs, models):
            c, name, t, h2h, extra = it[0], it[1], it[2], it[3], it[4]
            th, ta = c['teams']['home'], c['teams']['away']
            query = match_query(th['name'], ta['name'], th['league'],
                                c.get('competition', ''), '盘口 数据 历史交锋')
            hits = kb_search(query, topk=3)
            if hits:
                print(f"\n【历史案例参考】{name} (写稿参考, 不进文章):")
                for i, h in enumerate(hits, 1):
                    tx = h['text'].replace('\n', ' ')
                    if len(tx) > 80:
                        tx = tx[:80] + '…'
                    print(f"  [{i}] 相关度{h['score']:.3f} | {h['match']} | {tx}")
    except Exception as e:
        print(f"\n【历史案例参考】检索失败: {e} (先运行 kb/build_kb.py)")

    # 1. 生成3张对比图
    chart_deviation(cfgs, models, os.path.join(OUT_DIR, 'charts', 'cmp1_双场模型vs市场偏差.png'))
    chart_h2h(cfgs, os.path.join(OUT_DIR, 'charts', 'cmp2_双场交锋克星对比.png'))
    chart_attack(cfgs, os.path.join(OUT_DIR, 'charts', 'cmp3_四队攻防对比.png'))
    print('对比图 3 张 →', os.path.join(OUT_DIR, 'charts'))

    # 2. 文章内容(md)
    lines = [TITLE, '', TAGS, '']
    lines += INFO_CARD
    lines += ['', OPENING, '',
              '![双场模型vs市场偏差对比](charts/cmp1_双场模型vs市场偏差.png)', '*图1 双场模型vs市场偏差对比*', '']
    for item, m in zip(cfgs, models):
        c, name, t, h2h, extra = item[0], item[1], item[2], item[3], item[4]
        labels = item[5] if len(item) > 5 else ('【数据偏差池】', '【战术胜负手】', '【比分演算倾向】')
        l1, l2, l3 = labels
        # 小节标题独立带赛事名, 每场比赛成为独立搜索入口(SEO长尾, 2026-08-27)
        sec_title = "|".join(x for x in (name, c.get('competition', '')) if x)
        # 截短到60字内,避免被长句检查误判
        if len(f"【{sec_title}】({t}开球)") > 60:
            sec_title = name  # 只保留赛事名
        lines += ['', '|', '', f"【{sec_title}】({t}开球)", '',
                  l1,
                  f"机构主胜隐含:{m['pM']['H']*100:.1f}%,平局{m['pM']['D']*100:.1f}%,客胜{m['pM']['A']*100:.1f}%。",
                  f"泊松模型测算:主胜{m['pH']*100:.1f}%,客胜{m['pA']*100:.1f}%。",
                  f"结论:主胜被{'低估' if m['pH'] > m['pM_cal']['H'] else '高估'}{abs((m['pH']-m['pM_cal']['H'])*100):.1f}个百分点。",
                  '', l2,
                  f"{h2h['label']} {h2h['w']}胜{h2h['d']}平{h2h['l']}负。",
                  f"{h2h['note']}",
                  '', l3,
                  f"模型期望总进球{m['exp_goals']:.2f}球,首选比分参考下方表格。"]
        for ex in extra:
            lines += ['', ex]
    lines += ['', '|', '', SUMMARY, '',
              '![双场交锋克星对比](charts/cmp2_双场交锋克星对比.png)', '*图2 双场交锋克星对比*', '',
              '![四队攻防对比](charts/cmp3_四队攻防对比.png)', '*图3 四队攻防对比*', '',
              ENDING_HOOK, '']
    lines += FOOTER

    md_path = os.path.join(OUT_DIR, safe_name(TITLE) + '.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('MD →', md_path)

    # 3. docx(含图)
    doc = Document()
    doc.add_heading(TITLE, level=1)
    doc.add_paragraph(TAGS)
    for c in INFO_CARD:
        doc.add_paragraph(c)
    _labels = set()
    for item in cfgs:
        if len(item) > 5:
            _labels.update(item[5])
    for para in lines[10:]:
        # 多段字符串(OPENING/SUMMARY)拆成独立段落; md 图片语法行不进 docx(由图片插入逻辑负责)
        chunks = para.split('\n\n') if para in (OPENING, SUMMARY) else [para]
        for ch in chunks:
            ch = ch.strip()
            if not ch or ch.startswith('![') or ch.startswith('*图'):
                continue
            if ch == '|':
                doc.add_paragraph('·')
            elif ch.startswith('【') or ch.startswith('第一场') or ch.startswith('第二场') or ch in _labels:
                p = doc.add_paragraph()
                run = p.add_run(ch)
                run.bold = True
            else:
                doc.add_paragraph(ch)
        if para == OPENING:
            doc.add_picture(os.path.join(OUT_DIR, 'charts', 'cmp1_双场模型vs市场偏差.png'), width=Inches(5.9))
            doc.add_paragraph('图1 双场模型vs市场偏差对比(核心卖点)')
        if para == SUMMARY:
            doc.add_picture(os.path.join(OUT_DIR, 'charts', 'cmp2_双场交锋克星对比.png'), width=Inches(5.9))
            doc.add_paragraph('图2 双场交锋克星对比')
            doc.add_picture(os.path.join(OUT_DIR, 'charts', 'cmp3_四队攻防对比.png'), width=Inches(5.9))
            doc.add_paragraph('图3 四队攻防对比')

    # 比分参考表(合规措辞: 数据推演参考, 不构成预测)
    doc.add_paragraph('附:各场模型比分倾向(数据推演参考)')
    t = doc.add_table(rows=1, cols=4)
    t.style = 'Light Grid Accent 1'
    for i, h in enumerate(['场次', '模型倾向', '推演概率', '参考赔率']):
        t.rows[0].cells[i].text = h
    for it, m in zip(cfgs, models):
        c, name, tt, h2h, extra = it[0], it[1], it[2], it[3], it[4]
        so = {(int(s[0]), int(s[1])): float(s[2]) for s in c.get('score_odds', [])}
        for (h, a), p in sorted(m['probs'].items(), key=lambda kv: -kv[1])[:3]:
            r = t.add_row().cells
            r[0].text = name
            r[1].text = f"{h}-{a}"
            r[2].text = f"{p*100:.1f}%"
            r[3].text = f"{so.get((h, a), '-'):.2f}" if isinstance(so.get((h, a)), (int, float)) else '-'

    docx_path = os.path.join(OUT_DIR, safe_name(TITLE) + '.docx')
    doc.save(docx_path)
    print('DOCX →', docx_path)


if __name__ == '__main__':
    main()
