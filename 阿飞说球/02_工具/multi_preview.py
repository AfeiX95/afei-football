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

# ============ 配置区: 每场 = (config路径, 标题段名, 开场时间, 交锋数据, extra段落列表) ============
CFGS = [
    (os.path.join(TOOL_DIR, 'match_configs', '帕梅拉斯vs波特诺.json'),
     "帕梅拉斯 vs 波特诺", "06:00",
     {'label': '帕梅拉斯 vs 波特诺(近10次交锋)', 'w': 7, 'd': 1, 'l': 2, 'note': '历史碾压,但今年小组赛1胜1平不败'},
     [
         "关键数据:帕梅拉斯近10场场均进2.1球失0.8球,火力在线,但防线是残阵——主力前锋保利尼奥加三名后卫全部挂彩。波特诺近10场5胜1平4负,巴拉圭联赛近4轮1胜3负,状态一般。解放者杯小组赛4胜1平1负拿头名,欧战成色和联赛完全是两副面孔。",
         "历史交锋:近10次交手帕梅拉斯7胜1平2负,占绝对上风。今年小组赛两回合,波特诺主场1-1、客场1-0,1胜1平不败,还踩着帕梅拉斯拿了小组第一。帕梅拉斯1.20的深热里,藏着0-1的旧账。",
         "冷门路径:①波特诺复制5月剧本,反击偷一球,帕梅拉斯残阵后防压上再丢。②帕梅拉斯伤停影响发酵,主场久攻不下,1-1平局把悬念留到次回合。③维格蒂(小组赛3球占全队60%)状态在线,是客队最现实的进球点。",
     ]),
    (os.path.join(TOOL_DIR, 'match_configs', '普拉滕斯vs科金博联.json'),
     "普拉滕斯 vs 科金博联", "06:00",
     {'label': '普拉滕斯 vs 科金博联(历史交锋)', 'w': 0, 'd': 0, 'l': 0, 'note': '首次交锋,白纸对决'},
     [
         "关键数据:普拉滕斯近10场3胜3平4负,场均进1.0球,进攻偏弱。主力中卫库艾斯塔(5场5首发)缺阵,后防更脆。科金博联近10场4胜5平1负,只输1场,平局占一半,典型的不败体质,场均失0.8球。",
         "赛制变量:两队历史首次交锋,没有任何对位参考,主场权重被放大。普拉滕斯4天后要在阿甲主场打博卡,会不会分心值得观察。科金博联次回合回主场,首回合可以接受平局。",
         "冷门路径:①科金博联不败体质发威,0-0或1-1,让球负1.86的低赔应验。②普拉滕斯主场小组赛1胜1平1负并不强势,0-4惨败铁路工场的防守表现再演。③客队拿到进球,把淘汰赛悬念拖回智利。",
     ]),
]
TITLE = "解放者杯双场:帕梅拉斯1.20有前科,普拉滕斯主胜高估20点"
TAGS = "#解放者杯 #帕梅拉斯 #波特诺 #普拉滕斯 #科金博联 #足球前瞻"
INFO_CARD = [
    "【对阵】帕梅拉斯(主)vs波特诺 — 周三003 | 普拉滕斯(主)vs科金博联 — 周三002",
    "【赛事】解放者杯2026 1/8决赛首回合(两回合制,总比分定晋级)",
    "【时间】8月13日(周四)06:00 北京时间(两场同时开球)",
    "【场地】帕梅拉斯主场(巴西)/普拉滕斯主场(阿根廷)",
    "【天气】待赛前更新",
]
OPENING = "开篇先甩两组数据。帕梅拉斯1.20的深热背后,藏着0-1的旧账:今年小组赛,波特诺对帕梅拉斯1胜1平不败,还踩着它拿了小组第一。另一边,普拉滕斯1.74的主场定价,模型只认三成,客队科金博联近10场只输过1场。两场1/8决赛首回合,两场主胜都被市场高估20个点,今晚解放者杯最值得盯的信号,就是这个。"
ENDING_HOOK = "两场都是首回合,你更看好哪边的剧本?评论区留下你的比分,6点赛后回来验。数据不会说谎,但人会。——阿飞·赛博聊球"
FOOTER = [
    "【数据来源】数据取自竞彩官方及公开体育数据库,测算由阿飞个人足球数据模型独立推演。",
    "",
    "【免责声明】本文为个人数据模型推演,属体育赛事分析交流,不构成任何购彩及投注建议。足球是圆的,请理性看待数据,适度娱乐。",
]

# 输出目录: 04_赛事文章/<YYYY-MM>/<串烧名> (按产出月份自动归档)
OUT_DIR = os.path.join(BASE, '阿飞说球', '04_赛事文章', date.today().strftime('%Y-%m'), '解放者杯16强首回合双场串烧')
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
    for path, name, t, h2h, extra in CFGS:
        c = json.load(open(path, encoding='utf-8'))
        m = run_model(c)
        cfgs.append((c, name, t, h2h, extra))
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
    for ax, (c, name, t, h2h, extra), m in zip(axes, cfgs, models):
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
    for ax, (c, name, t, h2h, extra) in zip(axes, cfgs):
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
    for c, name, t, h2h, extra in cfgs:
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
        for (c, name, t, h2h, extra), m in zip(cfgs, models):
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
    lines += ['', OPENING.format(
        open1=f"帕梅拉斯主场对波特诺,市场给出1.20的深热赔率(隐含胜率73.9%),模型只算到52.9%,差21个点",
        open2=f"普拉滕斯主场对科金博联,市场给1.74(隐含50.9%),模型只认30.9%,客胜却被低估22.7个点")]
    for (c, name, t, h2h, extra), m in zip(cfgs, models):
        lines += ['', '——', '', f"【{name}】({t}开球)", '',
                  f"【数据偏差池】机构主胜隐含:{m['pM']['H']*100:.1f}% / 平局{m['pM']['D']*100:.1f}% / 客胜{m['pM']['A']*100:.1f}%。泊松模型测算:主胜{m['pH']*100:.1f}% / 平局{m['pD']*100:.1f}% / 客胜{m['pA']*100:.1f}%。结论:主胜被{'低估' if m['pH'] > m['pM_cal']['H'] else '高估'}{abs((m['pH']-m['pM_cal']['H'])*100):.1f}个百分点。",
                  '', f"【战术胜负手】{h2h['label']} {h2h['w']}胜{h2h['d']}平{h2h['l']}负——{h2h['note']}。",
                  '', f"【比分演算倾向】模型期望总进球{m['exp_goals']:.2f}球,首选比分参考下方表格。"]
        for ex in extra:
            lines += ['', ex]
    lines += ['', '——', '', '双场对比,一句话总结:第一场是历史碾压下的旧账未清,市场给1.20的绝对信任,模型只认五成出头。第二场是白纸对决,市场给主队五成信任,模型更信客队的不败体质。两场主胜都被高估20个点,这是今晚解放者杯最值得盯的信号。', '',
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
    for para in lines[10:]:
        if para == '——':
            doc.add_paragraph('——')
        elif para.startswith('【') or para.startswith('第一场') or para.startswith('第二场'):
            p = doc.add_paragraph()
            run = p.add_run(para)
            run.bold = True
        else:
            doc.add_paragraph(para)
        if para.startswith('开篇先甩两组数据'):
            doc.add_picture(os.path.join(OUT_DIR, 'charts', 'cmp1_双场模型vs市场偏差.png'), width=Inches(5.9))
            doc.add_paragraph('图1 双场模型vs市场偏差对比(核心卖点)')
        if para.startswith('双场对比,一句话总结'):
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
    for (c, name, tt, h2h, extra), m in zip(cfgs, models):
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
