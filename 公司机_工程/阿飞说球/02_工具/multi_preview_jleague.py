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

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL_DIR = os.path.join(BASE, '阿飞说球', '02_工具')
sys.path.insert(0, TOOL_DIR)
from afei_generator import run_model  # noqa: E402

# ============ 配置区: 每场 = (config路径, 标题段名, 开场时间, 交锋数据, extra段落列表) ============
CFGS = [
    (os.path.join(TOOL_DIR, 'match_configs', '浦和红钻vs广岛三箭.json'),
     "浦和红钻 vs 广岛三箭", "18:00",
     {'label': '浦和主场 vs 广岛(近10次交锋)', 'w': 7, 'd': 1, 'l': 2, 'note': '2022年至今主场不败,各赢各的主场'},
     [
         "关键数据:浦和红钻近10场4胜3平3负,场均进1.5球,但首轮客场3-4负大阪钢巴,防线丢4个。广岛三箭近10场8胜1平1负,场均进2.4球,首轮3-0完胜千叶市原,状态正烫。账面差距不小,但浦和的主场是另一回事。",
         "历史交锋:浦和主场对广岛近10次7胜1平2负,2022年至今广岛在埼玉2002没赢过球。广岛主场3-0、2-0、4-1赢过浦和,浦和回到主场就1-0、3-0、2-1还回去——各赢各的主场,是这对冤家的铁律。",
         "冷门路径:①广岛客场破咒,延续8胜1平1负的强势,模型最高概率的方向。②浦和主场魔咒延续,爆冷抢分,历史交锋给了底气。③对攻平局,模型大2.5球64.2%,近期平局潮剧本已从1-1闷平转成2-2、3-3进球大战,这场若平未必闷。",
     ]),
    (os.path.join(TOOL_DIR, 'match_configs', '神户胜利vs东京FC.json'),
     "神户胜利 vs 东京FC", "18:00",
     {'label': '神户主场 vs 东京(近10次交锋)', 'w': 2, 'd': 5, 'l': 3, 'note': '平局率50%,市场却在加注主胜'},
     [
         "关键数据:神户胜利近10场4胜3平3负,场均进1.1球,首轮客场1-0胜福冈,大迫勇也进球。东京FC近10场3胜2平5负,首轮主场1-5惨败町田,但客场近10场5胜4平1负——垫底队的客场硬得离谱。",
         "历史交锋:神户主场对东京近10次2胜5平3负,平局率50%。2025年11月0-0、2024年10月0-2、2023年3-2,东京客场踢神户历来摆低姿态,闷战是招牌。神户火力本就一般,遇到铁桶阵,1-1、0-0是家常便饭。",
         "冷门路径:①东京客场铁桶阵偷分,1-1甚至0-1,垫底队客场5胜4平1负不是闹着玩。②神户主场6胜2平2负的底子兑现,1-0小胜,大迫勇也单点爆破——但竞彩让球盘-1(让球胜4.41),近期深热让球盘全线翻车,神户要打穿让球并不容易。③双方对攻大开大合,2-1或2-2,大2.5球剧本。",
     ]),
]
TITLE = "日职双场:浦和主场8年没输广岛,神户打东京一半是平局"
TAGS = "#日职 #浦和红钻 #广岛三箭 #神户胜利 #东京FC #足球前瞻"
INFO_CARD = [
    "【对阵】浦和红钻(主)vs广岛三箭 — 周六18:00 | 神户胜利(主)vs东京FC — 周六18:00",
    "【赛事】日职2026 常规赛第2轮(双场连播)",
    "【时间】8月15日(周六)18:00 北京时间(两场同时开球)",
    "【场地】埼玉2002体育场(浦和)/诺维达神户球场(神户)",
    "【天气】待赛前更新",
]
OPENING = "开篇先甩两组数据。浦和红钻主场对广岛,近10次交手7胜1平2负,2022年至今没输过;市场却给客胜1.81,隐含49%的翻盘预期。另一边,神户胜利主场对东京,近10次交手2胜5平3负,一半是平局。市场资金却在连续加注主胜,赔率从2.13一路降到1.99。两场日职,两场市场与历史打架,今晚最值得盯的信号,就是这个。"
ENDING_HOOK = "两场都是主场魔咒 vs 状态碾压,你更看好哪边的剧本?评论区留下你的比分,18点赛后回来验。数据不会说谎,但人会。——阿飞·赛博聊球"
FOOTER = [
    "【数据来源】数据取自竞彩官方及公开体育数据库,测算由阿飞个人足球数据模型独立推演。",
    "",
    "【免责声明】本文为个人数据模型推演,属体育赛事分析交流,不构成任何购彩及投注建议。足球是圆的,请理性看待数据,适度娱乐。",
]

# 输出目录: 04_赛事文章/<YYYY-MM>/<串烧名> (按产出月份自动归档)
OUT_DIR = os.path.join(BASE, '阿飞说球', '04_赛事文章', date.today().strftime('%Y-%m'), '日职第2轮双场串烧')
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
        open1=f"浦和红钻主场对广岛,市场给出1.81的客胜赔率(隐含胜率49%),模型算到47.1%,基本一致,但历史交锋7胜1平2负站在主队这边",
        open2=f"神户胜利主场对东京,市场给1.99(隐含44.5%),模型算51.2%,主胜被低估,但历史交锋平局率50%是暗雷")]
    for (c, name, t, h2h, extra), m in zip(cfgs, models):
        lines += ['', '——', '', f"【{name}】({t}开球)", '',
                  f"【数据偏差池】机构主胜隐含:{m['pM']['H']*100:.1f}% / 平局{m['pM']['D']*100:.1f}% / 客胜{m['pM']['A']*100:.1f}%。泊松模型测算:主胜{m['pH']*100:.1f}% / 平局{m['pD']*100:.1f}% / 客胜{m['pA']*100:.1f}%。结论:主胜被{'低估' if m['pH'] > m['pM_cal']['H'] else '高估'}{abs((m['pH']-m['pM_cal']['H'])*100):.1f}个百分点。",
                  '', f"【战术胜负手】{h2h['label']} {h2h['w']}胜{h2h['d']}平{h2h['l']}负——{h2h['note']}。",
                  '', f"【比分演算倾向】模型期望总进球{m['exp_goals']:.2f}球,首选比分参考下方表格。"]
        for ex in extra:
            lines += ['', ex]
    lines += ['', '——', '', '双场对比,一句话总结:第一场是市场信状态、历史信主场。广岛8胜1平1负的火力 vs 浦和2022年至今的主场不败,模型和市场罕见地达成一致,分歧全在交锋簿上。第二场是市场加注、历史唱反调。资金连续4次压低神户主胜,但平局率50%的交锋是最大的暗雷。两场日职,两场"主场魔咒",今晚18点见分晓。', '',
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
