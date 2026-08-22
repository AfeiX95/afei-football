# -*- coding: utf-8 -*-
"""
复盘报告生成器 — 市场·模型·赛果复盘 (2026-08-09 ~ 08-11)
产出: 4张图表 + docx 复盘报告
用法: python review_report_docx.py
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))          # 00_引擎/backtest
OUT = os.path.join(BASE, 'review_20260809_0811')
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, BASE)
from fetch_results import fetch_all

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 中文字体 (项目内置逻辑)
for fp in [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\msyhbd.ttc', r'C:\Windows\Fonts\simhei.ttf']:
    if os.path.exists(fp):
        try:
            fm.fontManager.addfont(fp)
        except Exception:
            pass
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


# ---------------- 数据采集 ----------------
def collect():
    m = fetch_all('2026-08-09', '2026-08-11', only_single=False)
    rows = []
    for x in m:
        try:
            oh, od, oa = float(x['h']), float(x['d']), float(x['a'])
        except Exception:
            continue
        ft = x.get('sectionsNo999', '')
        if ':' not in ft:
            continue
        sh, sa = map(int, ft.split(':'))
        res = 'H' if sh > sa else ('D' if sh == sa else 'A')
        inv = {'H': 1/oh, 'D': 1/od, 'A': 1/oa}
        s = sum(inv.values())
        p = {k: v/s for k, v in inv.items()}
        gl = int(x.get('goalLine', '0') or 0)
        net = (sh - gl) - sa
        hres = 'H' if net > 0 else ('D' if net == 0 else 'A')
        ht = x.get('sectionsNo1', '')
        rows.append(dict(
            date=x['matchDate'], no=x.get('matchNumStr', ''),
            lg=x.get('leagueNameAbbr') or x.get('leagueName', ''),
            home=x.get('allHomeTeam') or x.get('homeTeam'),
            away=x.get('allAwayTeam') or x.get('awayTeam'),
            ft=ft, ht=ht, res=res, p=p, single=x.get('bettingSingle') == 1,
            gl=gl, hres=hres))
    return rows


def chart_hot_buckets(rows, out):
    """图1: 热门分档兑现率 vs 历史校准预期"""
    hot = [r for r in rows if max(r['p'].values()) >= 0.45]
    buckets = [(0.45, 0.55, '45-55%'), (0.55, 0.65, '55-65%'), (0.65, 1.0, '65%+')]
    labels, hit_r, n_list, hist = [], [], [], [0.83, 0.83, 0.83]
    for lo, hi, lab in buckets:
        g = [r for r in hot if lo <= max(r['p'].values()) < hi]
        if not g:
            continue
        n = len(g)
        hits = sum(1 for r in g if max(r['p'], key=r['p'].get) == r['res'])
        labels.append(lab + f'\n(n={n})')
        hit_r.append(hits / n * 100)
        n_list.append(n)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = range(len(labels))
    b1 = ax.bar(x, hit_r, width=0.55, color='#c0392b', alpha=0.9, label='本周实际兑现率')
    ax.plot(x, hist[:len(x)], '--', color='#2c3e50', linewidth=1.8,
            label='历史校准预期 78-83%')
    for xi, v in zip(x, hit_r):
        ax.text(xi, v + 2, f'{v:.0f}%', ha='center', fontsize=12, fontweight='bold')
    ax.axhline(50, color='#95a5a6', linestyle=':', linewidth=1)
    ax.text(len(x) - 0.35, 51, '50% 基准', fontsize=9, color='#7f8c8d', ha='right')
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel('兑现率 (%)', fontsize=11)
    ax.set_ylim(0, 100)
    ax.set_title('热门分档兑现率: 中等热门重灾区 (本周 9/21=42.9%)', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()


def chart_draw(rows, out):
    """图2: 平局潮 — 隐含平局 vs 实际平局率"""
    n = len(rows)
    draws = [r for r in rows if r['res'] == 'D']
    impl_avg = sum(r['p']['D'] for r in rows) / n * 100
    act = len(draws) / n * 100
    fig, ax = plt.subplots(figsize=(8, 4.4))
    bars = ax.bar(['市场隐含平均', '本周实际平局率'], [impl_avg, act],
                  width=0.5, color=['#7f8c8d', '#e67e22'])
    for b, v in zip(bars, [impl_avg, act]):
        ax.text(b.get_x() + b.get_width()/2, v + 0.8, f'{v:.1f}%',
                ha='center', fontsize=13, fontweight='bold')
    ax.axhline(25, color='#95a5a6', linestyle=':', linewidth=1)
    ax.text(1.32, 25.6, '历史基线 ~25%', fontsize=9, color='#7f8c8d', ha='right')
    ax.set_ylim(0, 40)
    ax.set_ylabel('占比 (%)', fontsize=11)
    ax.set_title(f'平局潮: 10/{n} 场平局 (29.4%), 全部 1:1 / 2:2 闷平型', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()


def chart_hcap(rows, out):
    """图3: 单固12场让球盘结果分布 + 深热让球兑现"""
    singles = [r for r in rows if r['single']]
    res_cnt = {'H': 0, 'D': 0, 'A': 0}
    for r in singles:
        res_cnt[r['hres']] += 1
    fig, ax = plt.subplots(figsize=(8, 4.4))
    labels = ['主队赢盘', '走盘', '客队赢盘']
    vals = [res_cnt['H'], res_cnt['D'], res_cnt['A']]
    colors = ['#27ae60', '#95a5a6', '#2980b9']
    bars = ax.bar(labels, vals, width=0.5, color=colors)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 0.1, f'{v}场',
                ha='center', fontsize=12, fontweight='bold')
    ax.set_ylim(0, 6)
    ax.set_ylabel('场次', fontsize=11)
    ax.set_title('单固12场让球盘结果: 分布均衡, 无系统性倾向', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.text(0, -1.1, '深热让球(哈马比-1 3-0 / 阿尔克马尔-1 2-0)全兑现 | 中等热门让球(圣克拉拉-1 2-2 / 吉马良斯-1 0-1)翻车',
            fontsize=9, color='#555', ha='left')
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()


def chart_week_snapshot(rows, out):
    """图4: 本周市场特征总览 — 大球率 / 冷门数 / 半场定调"""
    n = len(rows)
    over = sum(1 for r in rows if sum(map(int, r['ft'].split(':'))) > 2.5)
    cold = sum(1 for r in rows for d in 'HDA' if r['p'][d] < 0.30 and r['res'] == d)
    bounce = 0
    for r in rows:
        if ':' not in r['ht']:
            continue
        hs, ha = map(int, r['ht'].split(':'))
        sh, sa = map(int, r['ft'].split(':'))
        if (hs > ha) != (sh > sa):
            bounce += 1
    fig, axes = plt.subplots(1, 3, figsize=(10, 4))
    # 大小球
    ax = axes[0]
    ax.pie([over, n - over], labels=['大球 2.5+', '小球'],
           colors=['#c0392b', '#bdc3c7'], autopct='%.0f%%', startangle=90,
           textprops={'fontsize': 11})
    ax.set_title(f'大小球 (大球率 {over/n*100:.0f}%)', fontsize=12, fontweight='bold')
    # 冷门
    ax = axes[1]
    ax.bar(['冷门方向打出'], [cold], width=0.4, color='#8e44ad')
    ax.text(0, cold + 0.4, f'{cold}次', ha='center', fontsize=13, fontweight='bold')
    ax.set_ylim(0, 22)
    ax.set_title('隐含<30%方向打出次数', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    # 半场
    ax = axes[2]
    ax.bar(['半场逆转'], [bounce], width=0.4, color='#16a085')
    ax.text(0, bounce + 0.2, f'{bounce}场', ha='center', fontsize=13, fontweight='bold')
    ax.set_ylim(0, 3)
    ax.set_title('半场领先方被翻盘', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    fig.suptitle('本周市场特征快照: 小球 · 冷门潮 · 半场定调', fontsize=13, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(out, dpi=150, bbox_inches='tight')
    plt.close()


def build_docx(rows, charts, out):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(11)

    # 标题
    t = doc.add_heading('', level=0)
    run = t.add_run('竞彩市场·模型·赛果复盘 (2026-08-09 ~ 08-11)')
    run.font.size = Pt(18)
    p = doc.add_paragraph()
    p.add_run('复盘日期: 2026-08-11 | 数据源: 中国体彩网官方赛果页(38场) + 竞彩webapi全量核验 | 34场有赔率可算隐含概率')
    p.runs[0].font.size = Pt(9)
    p.runs[0].font.color.rgb = RGBColor(0x88, 0x88, 0x88)

    # 核心结论
    h = doc.add_heading('一、核心结论', level=1)
    for s in [
        '1. 本周是"热门翻车周": 21场热门(隐含≥45%)只兑现9场(42.9%), 与历史校准"热门被低估(实际命中78-83%)"完全相悖。深热(65%+)依然稳(3/4), 但中等热门(45-65%)是重灾区——45-55%档兑现率仅28.6%(2/7)。',
        '2. 平局潮: 34场里10场平局(29.4%), 且集中在1:1/2:2闷平型。平局隐含平均约25%, 实际29.4%——平局再次打超隐含。',
        '3. 冷门方向(隐含<30%)打出17次: 客胜冷门(桑托斯0-2巴竞技、南特0-1圣旺红星、吉马良斯0-1阿罗卡)+平局冷门遍地。',
        '4. 大小球偏小: 大球率仅35.3%(12/34), 与"1:1潮"互相印证。',
        '5. 半场逆转0场: 半场领先的球队全部保住胜果, 本轮走势"半场定调"。',
    ]:
        doc.add_paragraph(s)

    # 市场层面
    doc.add_heading('二、市场层面分析 (34场有赔率)', level=1)
    doc.add_paragraph('2.1 热门分档兑现 —— 中等热门重灾区')
    doc.add_picture(charts[0], width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('与校准结论的冲突: 历史212场样本显示热门实际命中率远超隐含(ratio 1.35封顶, 桶值1.513), 但本周热门集体哑火。'
                      '长期结论(212场)依然成立, 不应据此调低热门系数; 但前瞻时中等热门的"主胜被低估"Edge要降档语气——'
                      '与8月8日模型复盘"主胜Edge连翻3车"结论一致。')

    doc.add_paragraph('2.2 平局潮 —— 平局超卖')
    doc.add_picture(charts[1], width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    draws = [r for r in rows if r['res'] == 'D']
    doc.add_paragraph('10场平局明细: ' + '、'.join(
        f"{r['home']}vs{r['away']} {r['ft']}(隐含{r['p']['D']*100:.0f}%)" for r in draws) + '。'
        '其中9场隐含平局在20-30%区间, 恰好落在校准桶内, 实际打出率却远超历史ratio(0.451)。'
        '单周平局爆炸, 校准系数已EWMA平滑, 不追单周极端。')

    doc.add_paragraph('2.3 单固12场让球盘 (回测样本)')
    doc.add_picture(charts[2], width=Inches(5.8))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('让球结果分布 H 5场 / D 3场 / A 4场——均衡, 让球盘无系统性倾向。'
                      '深热让球盘稳: 哈马比(-1)3-0、阿尔克马尔(-1)2-0均兑现; 中等热门让球翻车: 圣克拉拉(-1)被2-2逼平、吉马良斯(-1)0-1输球。')

    doc.add_paragraph('2.4 本周特征快照')
    doc.add_picture(charts[3], width=Inches(6.2))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 模型层面
    doc.add_heading('三、模型层面 (累计13场, REVIEW_REPORT.md)', level=1)
    tbl = doc.add_table(rows=7, cols=2)
    tbl.style = 'Light Grid Accent 1'
    data = [
        ('指标', '数值'),
        ('方向命中率 · 泊松模型', '5/13 (38.5%)'),
        ('方向命中率 · 市场隐含', '6/13 (46.2%)'),
        ('模型-市场差', '-7.7个百分点'),
        ('Brier score', '模型 0.654 vs 市场 0.653 (几乎打平)'),
        ('首选比分命中', '3/13 (23.1%)'),
        ('Edge信号兑现', '5/12 (41.7%)'),
    ]
    for i, (k, v) in enumerate(data):
        tbl.rows[i].cells[0].text = k
        tbl.rows[i].cells[1].text = v
    doc.add_paragraph()
    doc.add_paragraph('结构性弱点(与上期一致, 已确认): 实际主胜模型命中5/6(83.3%), 实际平局0/2全灭, 实际客胜0/5全灭。'
                      '"主胜被低估"Edge信号偏乐观——本周市场侧中等热门翻车+模型侧主胜Edge连翻, 双重印证, 主胜类Edge结论一律降档表述。')

    # 校准演进
    doc.add_heading('四、校准系统演进 (已自动更新)', level=1)
    tbl = doc.add_table(rows=5, cols=4)
    tbl.style = 'Light Grid Accent 1'
    for i, row in enumerate([
        ('项', '更新前', '更新后', '说明'),
        ('样本', '210场', '212场', '新增2场单固(8/9-8/11窗口)'),
        ('平局系数', '×0.415', '×0.432', 'EWMA 0.7/0.3, 新桶ratio 0.451'),
        ('热门系数', '×1.35', '×1.35', '封顶值, 桶值1.513'),
        ('冷门系数', '×0.5', '×0.5', '封底值, 桶值0.456'),
    ]):
        for j, v in enumerate(row):
            tbl.rows[i].cells[j].text = v

    # 行动项
    doc.add_heading('五、对后续前瞻的行动项', level=1)
    for s in [
        '1. 中等热门(隐含45-65%)Edge信号降档: 本轮45-55%档兑现率28.6%, 与"热门被低估"长期结论冲突。写前瞻时中等热门的"主胜被低估"只作中性提示, 不作核心卖点。',
        '2. 平局场景重新重视: 模型平局0/2全灭+本周平局潮29.4%, 平局方向的Edge信号(如让球盘平局隐含<25%)值得在文章中作为"分歧点"呈现。',
        '3. 深热(65%+)可继续信任: 4场深热兑现3场, 让球盘深热(哈马比/阿尔克马尔)全兑现。',
        '4. 大小球默认偏小: 新赛季揭幕轮(葡超/荷甲/法乙/德乙首轮)进球少、1:1潮, 前瞻大小球分析可标注"赛季初谨慎看大"。',
        '5. 半场定调周: 半场领先方保住率100%, 前瞻"半全场"维度可标注本趋势(样本仅1周, 弱信号)。',
    ]:
        doc.add_paragraph(s)

    # 数据来源
    doc.add_heading('六、数据来源', level=1)
    for s in [
        '· 中国体彩网竞彩足球赛果页(2026-08-09 ~ 2026-08-11, 38场): https://www.sporttery.cn/jc/zqsgkj/',
        '· 竞彩webapi getUniformMatchResultV1.qry 全量核验(38场, 其中单固12场)',
        '· 模型累计: 00_引擎/backtest/REVIEW_REPORT.md (13场)',
        '· 校准: 00_引擎/backtest/calibration_state.json (212场)',
        '',
        '本报告仅作数据复盘与模型校准参考, 不构成任何投注建议。',
    ]:
        doc.add_paragraph(s)

    doc.save(out)
    print('DOCX:', out)


def main():
    rows = collect()
    print(f'采集 {len(rows)} 场 (有赔率且完场)')
    charts = [
        os.path.join(OUT, 'chart1_hot_buckets.png'),
        os.path.join(OUT, 'chart2_draw.png'),
        os.path.join(OUT, 'chart3_hcap.png'),
        os.path.join(OUT, 'chart4_week.png'),
    ]
    chart_hot_buckets(rows, charts[0])
    chart_draw(rows, charts[1])
    chart_hcap(rows, charts[2])
    chart_week_snapshot(rows, charts[3])
    print('图表完成:', ', '.join(os.path.basename(c) for c in charts))

    docx_path = os.path.join(OUT, '复盘_20260809_0811.docx')
    build_docx(rows, charts, docx_path)
    print('全部完成 ->', OUT)


if __name__ == '__main__':
    main()
