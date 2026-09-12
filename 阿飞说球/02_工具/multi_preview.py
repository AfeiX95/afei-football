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

# 文末合规模板: 用 afei_generator 的单一出处(2026-09-12 精简到 30-40 字, 避免两处漂移)
from afei_generator import FOOTER  # noqa: E402

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


# ============================================================ 内容序列 → md / docx / 导入版
# 2026-09-12 重构: 三种产出(md, 含图 docx, 头条导入版)统一由 **一份内容序列** 渲染,
# 不再"先拼 md 行、再从行里猜结构"(旧做法导致: 正文重复两遍 / H2 空标题 / 模板套话混入)。
# 内容序列元素: ('h1'|'h2'|'p'|'div'|'img', 文本或图键)

def build_content(cfgs, models, sub_headings=True, with_images=True):
    """把模板文案 + 每场(小节标题/独有信号/比分) 组装成一份结构序列

    sub_headings=True  → md 留档用(保留三小节标题, 便于公众号复用)
    sub_headings=False → docx 用(拍平: 只留"每场一个 H2", 避免小节标题下面空着)
    with_images=False   → 不产出任何配图/占位符(多场"速览"类稿件用, 配图由编辑另配)
    """
    blocks = [('h1', TITLE), ('p', TAGS)]
    for c in INFO_CARD:
        blocks.append(('p', c))
    for seg in OPENING.split('\n\n'):
        if seg.strip():
            blocks.append(('p', seg.strip()))
    if with_images:
        blocks.append(('img', 'cmp1'))
    _n_match = len(cfgs)
    for idx, (item, m) in enumerate(zip(cfgs, models), 1):
        c, name, t, h2h, extra = item[0], item[1], item[2], item[3], item[4]
        labels = item[5] if len(item) > 5 else ('【数据偏差池】', '【战术胜负手】', '【比分演算倾向】')
        blocks.append(('div', ''))
        blocks.append(('h2', f'{name}({t}开球)'))          # 每场独立搜索入口(SEO 长尾)
        n = len(labels)
        for i, ex in enumerate(extra):
            if ex.strip():
                blocks.append(('p', ex.strip()))
            # 配图分配: 2 场时每场配一张(003→交锋对位/004→四队攻防);
            #   3 场以上(速览)只有 3 张图可用, 不再每场配图, 统一放到末尾
            if with_images and _n_match == 2 and i == n - 1 and n > 0:
                blocks.append(('img', 'cmp2' if idx == 1 else 'cmp3'))
        if sub_headings:
            for lab in labels:
                blocks.append(('h2', lab))
    if with_images and _n_match > 2:
        blocks.append(('div', ''))
        blocks.append(('img', 'cmp3'))                      # 多场速览: 末尾统一放攻防对比图
    if SUMMARY.strip():
        blocks.append(('div', ''))
        for seg in SUMMARY.split('\n\n'):
            if seg.strip():
                blocks.append(('p', seg.strip()))
    blocks.append(('p', ENDING_HOOK))
    return blocks


IMG_FILE = {
    'cmp1': 'cmp1_双场模型vs市场偏差.png',
    'cmp2': 'cmp2_双场交锋克星对比.png',
    'cmp3': 'cmp3_四队攻防对比.png',
}
IMG_CAP = {
    'cmp1': '图1 双场模型vs市场偏差对比',
    'cmp2': '图2 双场交锋对位对比',
    'cmp3': '图3 四队攻防数据对比(近10场)',
}


def render_md(blocks):
    """md 留档(公众号复用): 保留图片语法"""
    out = []
    for kind, txt in blocks:
        if kind == 'h1':
            out += [txt, '']
        elif kind == 'h2':
            out += ['## ' + txt, '']
        elif kind == 'div':
            out += ['---', '']
        elif kind == 'img':
            out += [f'![{IMG_CAP[txt]}](charts/{IMG_FILE[txt]})', f'*{IMG_CAP[txt]}*', '']
        else:
            out += [txt, '']
    out += [l for l in FOOTER]
    return '\n'.join(out) + '\n'


def render_docx(blocks, out_path, with_images=True, publish=False, score_table=True):
    """docx 渲染。

    with_images=True  → 含图正式版(本地审阅/留档)
    publish=True      → 头条【文档导入】版:
        规范(用户 2026-09-12 提供《Word导入头条号完整排版方案》):
        ① 图片不嵌入, 用文字占位符  ② 小标题用 Heading 2  ③ 不用表格
        ④ 不设字体/颜色/缩进  ⑤ 段间空行, 短段
    score_table=True  → 文末补"比分倾向参考"(纯文本条目)
    """
    doc = Document()
    pic_i = 0
    for kind, txt in blocks:
        if kind == 'h1':
            doc.add_heading(txt, level=1)
        elif kind == 'h2':
            doc.add_heading(txt, level=2)
        elif kind == 'div':
            doc.add_paragraph('——')          # 纯文字分割线
        elif kind == 'img':
            pic_i += 1
            if publish:
                doc.add_paragraph(f'【此处插入图{pic_i}:{IMG_CAP[txt]} ｜ 传图后删掉本行】')
            elif with_images:
                doc.add_picture(os.path.join(OUT_DIR, 'charts', IMG_FILE[txt]), width=Inches(5.9))
                doc.add_paragraph(IMG_CAP[txt])
        else:
            doc.add_paragraph(txt)
    if score_table and publish:
        # 比分参考: 纯文本条目替代表格(复杂表格导入易变形)
        doc.add_heading('比分倾向参考', level=2)
        for item, m in zip(_cfgs_pub, _models_pub):
            c, name = item[0], item[1]
            so = {(int(s[0]), int(s[1])): float(s[2]) for s in c.get('score_odds', [])}
            doc.add_paragraph(f'{name}:')
            for (h, a), p in sorted(m['probs'].items(), key=lambda kv: -kv[1])[:3]:
                o = so.get((h, a))
                tail = f',参考赔率{o:.2f}' if isinstance(o, (int, float)) else ''
                doc.add_paragraph(f'{h}-{a},模型{p*100:.1f}%{tail}')
        doc.add_paragraph('以上为数据推演参考,不构成预测。')
    elif score_table:
        # 含图正式版保留比分表格
        doc.add_paragraph('附:各场模型比分倾向(数据推演参考)')
        t = doc.add_table(rows=1, cols=4)
        t.style = 'Light Grid Accent 1'
        for i, h in enumerate(['场次', '模型倾向', '推演概率', '参考赔率']):
            t.rows[0].cells[i].text = h
        for item, m in zip(_cfgs_pub, _models_pub):
            c, name = item[0], item[1]
            so = {(int(s[0]), int(s[1])): float(s[2]) for s in c.get('score_odds', [])}
            for (h, a), p in sorted(m['probs'].items(), key=lambda kv: -kv[1])[:3]:
                r = t.add_row().cells
                r[0].text = name
                r[1].text = f'{h}-{a}'
                r[2].text = f'{p*100:.1f}%'
                r[3].text = f"{so.get((h, a), '-'):.2f}" if isinstance(so.get((h, a)), (int, float)) else '-'
    for line in FOOTER:
        if line.strip():
            doc.add_paragraph(line)
    doc.save(out_path)
    return out_path


def main():
    global _cfgs_pub, _models_pub
    cfgs, models = run_all()
    _cfgs_pub, _models_pub = cfgs, models

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

    # 1. 生成 3 张对比图
    chart_deviation(cfgs, models, os.path.join(OUT_DIR, 'charts', 'cmp1_双场模型vs市场偏差.png'))
    chart_h2h(cfgs, os.path.join(OUT_DIR, 'charts', 'cmp2_双场交锋克星对比.png'))
    chart_attack(cfgs, os.path.join(OUT_DIR, 'charts', 'cmp3_四队攻防对比.png'))
    print('对比图 3 张 →', os.path.join(OUT_DIR, 'charts'))

    blocks_md = build_content(cfgs, models, sub_headings=True)
    blocks_docx = build_content(cfgs, models, sub_headings=False)
    stem = safe_name(TITLE)

    md_path = os.path.join(OUT_DIR, stem + '.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(render_md(blocks_md))
    print('MD →', md_path)

    dx = os.path.join(OUT_DIR, stem + '.docx')
    render_docx(blocks_docx, dx, with_images=True, publish=False)
    print('DOCX(含图正式版) →', dx)

    pub = os.path.join(OUT_DIR, stem + '_发布导入版.docx')
    render_docx(blocks_docx, pub, with_images=False, publish=True)
    imgs = sum(1 for k, _ in blocks_docx if k == 'img')
    print(f'DOCX(头条导入版: {imgs} 个图片占位符 / 0 表格 / Heading2 层级) →', pub)


if __name__ == '__main__':
    main()
