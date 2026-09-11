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
    (os.path.join(TOOL_DIR, 'match_configs', '水户蜀葵vs町田泽维.json'),
     "水户蜀葵 vs 町田泽维", "17:00",
     {'label': '水户主场对町田(近10次)', 'w': 3, 'd': 4, 'l': 3, 'note': '10场里6场踢平,最近3次全平,磨功一流'},
     [
         "町田这开局多少有点不讲理。3战全胜9分领跑,客场两场灌了人家9个,5比1东京FC、4比0千叶,10场下来就漏了5球。更气人的是你在这队身上找不到下嘴的地方:西村拓真、外援前锋Yengi、中村和田,一人俩球,你掐死一个,另外两个照样进球。",
         "水户这边锋线是真钝,10场2胜7负,场均1.1个球,说难听点,进球全靠捡。但有两笔账得算。一笔是主场:就输过1场,磨10场能磨出6场平局,牛皮糖名不虚传。另一笔是状态:上轮联赛刚3比1赢京都,转头天皇杯就0比2栽给京都产业大学。一支大学队。这过山车坐得,你都不知道哪天的水户是真水户。",
         "从数据看,模型和市场对町田取胜的倾向比较统一,客胜一个给57.1%,一个给53.8%。真正值得留意的数据差在让球+1:町田想拿下让球得赢够2个,模型给32.7%,市场只按25.4%定价,差出7个点。这个差值说明市场对町田大胜没那么有信心,但临场伤病、轮换都可能改变走势,差值不代表必然打出。比分排出来0比1、1比1、0比2,全卡两球以内。水户主场磨,町田破密集防守历来费劲,低比分优先,磨人的闷仗跑不了。",
     ]),
    (os.path.join(TOOL_DIR, 'match_configs', '清水鼓动vs柏太阳神.json'),
     "清水鼓动 vs 柏太阳神", "17:30",
     {'label': '清水主场对柏太阳神(近5次)', 'w': 2, 'd': 1, 'l': 2, 'note': '怪就怪在这,主场反而能咬住,近3回赢了2回;可一换到联赛大盘,10场还是得输5场'},
     [
         "柏太阳神现在是日职最烫的一支队。10场8胜,场均2.3球,联赛3连胜,跟町田并排领跑。火力还散:中场Segawa两球一助,替补身份踢出来的;中场Koizumi两球;中场Kubo一球一助。你防得住一个,防不住轮着来。",
         "清水那头有点蔫。天皇杯1比1让人家逼平,点球才过的关;3天后联赛又0比1输给大阪樱花。连着两场运动战颗粒无收,锋线快生锈了。怪的是主场:1胜5平4负,5个主场就进2个球,出了门反倒会踢,这队的属性拧着长。交锋簿给了点念想:主场碰柏近3次2胜1平,联赛整体输5场,同一个对手换个场地换副面孔。",
         "这场的数字反而最没分歧,模型49.8%,市场46.1%,校准完差价不到1个点,双方观点高度趋同。真正值得探讨的是那个不过五成:榜二打下游,市场却不敢把客胜抬起来。是柏的连胜有水分,还是这个日本平球场真有古怪,踢了才知道。比分压着1比1、1比2、0比1走,总期望3.04,比水户那场多一口气。清水防反、柏控球,拉锯局里低比分概率自然靠前。",
     ]),
]
TITLE = "日职双场:町田客场撞牛皮糖,柏神8胜清水主场难翻"
TAGS = "#日职 #水户蜀葵 #町田泽维 #清水鼓动 #柏太阳神 #足球前瞻"
INFO_CARD = [
    "【对阵】水户蜀葵(主)vs町田泽维 — 周六001 | 清水鼓动(主)vs柏太阳神 — 周六002",
    "【赛事】日职J1 2026赛季 第4轮",
    "【时间】8月29日(周六)17:00/17:30 北京时间(两场相隔半小时)",
    "【场地】K's denki Stadium水户 / IAIスタジアム日本平",
    "【天气】待赛前更新",
]
OPENING = "周六两场日职,方向都往客队偏,但偏得不是一回事。001场是盾撞墙:町田10场丢5球,水户主场10回踢平6回,模型给客胜57.1%,市场53.8%,看着没悬念,踢起来未必。002场反过来,是火烤冰。柏太阳神10场8胜,烧得发烫,可模型死活不肯把客胜抬过五成。49.8%,市场46.1%,榜二打下游,愣是没人敢重仓。一个赌能赢几个,一个赌能不能赢。顺带说一句:今年是世界杯年,日职8月底才开赛,这才第4轮,两队拢共踢了3场正式比赛,样本薄。所以下文的概率,都只敢给区间,不敢拍死。"
ENDING_HOOK = "一场是牛皮糖能不能拖住领头羊,一场是主场鱼腩能不能咬住榜眼。两场日职你更信哪个剧本?评论区留下你的比分,赛后我们对答案。再次提醒:所有内容仅基于数据推演,临场伤病、天气、轮换都会改变走势,理性观赛,适度娱乐。数据不会说谎,但人会。——阿飞·赛博聊球"
FOOTER = [
    "【数据来源】数据取自竞彩官方及公开体育数据库,测算由阿飞个人足球数据模型独立推演。",
    "",
    "【免责声明】本文为个人数据模型推演,属体育赛事分析交流,不构成任何购彩及投注建议。足球是圆的,请理性看待数据,适度娱乐。",
]

# 输出目录: 04_赛事文章/<YYYY-MM>/<串烧名> (按产出月份自动归档)
OUT_DIR = os.path.join(BASE, '阿飞说球', '04_赛事文章', date.today().strftime('%Y-%m'), '日职第4轮周六双场串烧')
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
    lines += ['', OPENING]
    for (c, name, t, h2h, extra), m in zip(cfgs, models):
        # 小节标题独立带赛事名, 每场比赛成为独立搜索入口(SEO长尾, 2026-08-27)
        sec_title = "|".join(x for x in (name, c.get('competition', '')) if x)
        lines += ['', '——', '', f"【{sec_title}】({t}开球)", '',
                  f"先摆盘口。机构开价:主胜{m['pM']['H']*100:.1f}%、平局{m['pM']['D']*100:.1f}%、客胜{m['pM']['A']*100:.1f}%。我这边的模型跑出来:主胜{m['pH']*100:.1f}%、平局{m['pD']*100:.1f}%、客胜{m['pA']*100:.1f}%。两边一碰,主胜被{'低估' if m['pH'] > m['pM_cal']['H'] else '高估'}了{abs((m['pH']-m['pM_cal']['H'])*100):.1f}个点。",
                  '', f"交锋簿单独翻一眼:{h2h['label']}是{h2h['w']}胜{h2h['d']}平{h2h['l']}负。{h2h['note']}。",
                  '', f"比分模型排了序,期望总进球{m['exp_goals']:.2f}球,前三个在下面的表里。"]
        for ex in extra:
            lines += ['', ex]
    lines += ['', '——', '', '两场小结。001场,方向几乎没分歧,值得留意的只有让球+1那7个点的数据差。但临场变量多,别当结论用。002场,客胜不过五成本身就是信号,清水主场对柏的历史占优是暗线。两场都偏客队,但都不适合拍胸脯。', '',
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
        if para.startswith('周六两场日职'):
            doc.add_picture(os.path.join(OUT_DIR, 'charts', 'cmp1_双场模型vs市场偏差.png'), width=Inches(5.9))
            doc.add_paragraph('图1 双场模型vs市场偏差对比(核心卖点)')
        if para.startswith('最后提个醒。'):
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
