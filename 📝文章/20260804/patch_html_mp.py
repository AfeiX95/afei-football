# -*- coding: utf-8 -*-
"""将 20260804 两场合一 HTML 的 SVG 图替换为 matplotlib PNG，并补齐 v3 板块"""
import re, io, sys
sys.stdout.reconfigure(encoding="utf-8")

PATH = r"I:\阿飞说球\📝文章\20260804\欧冠资格赛两场合一_头条版.html"
html = io.open(PATH, encoding="utf-8").read()

# ---- 1) 替换 6 个内联 SVG 为 <img> ----
svg_re = re.compile(r"<svg[^>]*>.*?</svg>", re.S)
svgs = svg_re.findall(html)
assert len(svgs) == 6, "expected 6 svgs, got %d" % len(svgs)

def img_for(svg, idx):
    if "奥胡斯" in svg and "viewBox=\"0 0 600 460\"" in svg:
        return ("m1_radar.png", "六维战力对比雷达图")
    if "费内巴切" in svg and "viewBox=\"0 0 600 460\"" in svg:
        return ("m2_radar.png", "六维战力对比雷达图")
    if "后台模型 vs 市场定价" in svg:
        return ("m1_bar.png" if idx < 3 else "m2_bar.png", "后台模型 vs 市场定价")
    if "模型概率分布" in svg:
        return ("m1_pie.png" if idx < 3 else "m2_pie.png", "模型概率分布与高概率比分")
    raise AssertionError("unrecognized svg #%d" % idx)

def img_tag(fname, alt):
    return ('<img src="charts/mp/%s" alt="%s" style="width:100%%;max-width:600px;display:block;'
            'margin:14px auto;border-radius:8px;">') % (fname, alt)

def replace_svgs(m):
    idx = state["idx"]
    fname, alt = img_for(m.group(0), idx)
    state["idx"] += 1
    return img_tag(fname, alt)

state = {"idx": 0}
html = svg_re.sub(lambda m: replace_svgs(m), html)
assert state["idx"] == 6, "replaced %d svgs" % state["idx"]

# ---- 2) 场1 速览卡：重要指数行 ----
a1 = '<tr style="background:#1a1a2e;"><td style="padding:8px;border:1px solid #333;color:#ddd;">伤停</td><td style="padding:8px;border:1px solid #333;color:#ddd;">奥胡斯中锋里士满'
star1 = ('<tr style="background:#1a1a2e;"><td style="padding:8px;border:1px solid #333;color:#ddd;">重要指数</td>'
         '<td style="padding:8px;border:1px solid #333;color:#ffd93d;">⭐⭐⭐⭐（欧冠资格赛生死战：中立场无退路）</td></tr>')
assert html.count(a1) == 1, "m1 速览卡伤停行定位失败"
html = html.replace(a1, star1 + a1, 1)

# ---- 3) 场1：H2H + 战术对决 + 关键先生 ----
a2 = '<p>差在哪？中立场，主场优势直接归零；中锋里士满伤缺，前场支点没了；一周双赛，三天前刚踢完联赛。</p>'
block1 = '''<p><b style="color:#aaa;">对赛往绩：</b>两队此前从未交过手，这是历史第一次碰面。</p>
<h4 style="color:#aaa;margin:10px 0;">战术对决</h4>
<p>奥胡斯：控球推进，靠中锋支点做文章——里士满一伤，前场接应点直接少一个。萨巴赫：防守反击，四场资格赛只丢一球，防线是看家本领，但左路尖刀哈亚尔·阿利耶夫缺阵，反击锐度要打折扣。</p>
<p><b style="color:#ffd93d;">克制关系：-1</b>——萨巴赫的低位防守，正好克奥胡斯没有支点的攻坚。</p>
<h4 style="color:#aaa;margin:10px 0;">关键先生</h4>
<p>奥胡斯：阿恩斯塔德（10号前锋，上轮评分7.3）——里士满缺阵后，他是唯一能顶在最前面的破门钥匙。萨巴赫：没有单点明星，整条防线就是他们的关键先生。</p>'''
assert html.count(a2) == 1, "m1 差在哪定位失败"
html = html.replace(a2, a2 + "\n" + block1, 1)

# ---- 4) 场1：关键信号后插 m1_signals.png ----
a3 = '<p><b style="color:#ffd93d;">关键信号：</b>主胜定价1.57对应市场隐含56.5%'
assert html.count(a3) == 1, "m1 关键信号定位失败"
i3 = html.find(a3)
i3_end = html.find("</p>", i3) + len("</p>")
sig1 = ('\n' + img_tag("m1_signals.png", "关键预期对比：让球与大小球") +
        '\n<p style="text-align:center;color:#888;font-size:0.85em;">⬆ 关键预期对比：模型在让球负方向明显占优，大小球分歧更大</p>')
html = html[:i3_end] + sig1 + html[i3_end:]

# ---- 5) 场2 速览卡：重要指数行 ----
a4 = '<td style="padding:8px;border:1px solid #333;color:#ddd;">奥甲第5，新赛季1轮1分，6人伤停</td>'
star2 = ('<tr style="background:#16213e;"><td style="padding:8px;border:1px solid #333;color:#ddd;">重要指数</td>'
         '<td style="padding:8px;border:1px solid #333;color:#ffd93d;">⭐⭐⭐⭐（豪门摸底黑马，晋级天平首回合定调）</td></tr>')
assert html.count(a4) == 1, "m2 速览卡客队行定位失败"
html = html.replace(a4, a4 + '</tr>' + star2, 1)

# ---- 6) 场2：战意 + H2H + 战术对决 + 关键先生 ----
a5 = '<p>所以这场的悬念不是谁赢，是赢几个。</p>'
block2 = '''<p><b style="color:#aaa;">战意：</b>费内巴切上季土超屈居第二，欧冠是眼下最硬的正名舞台；格拉茨风暴奥甲新赛季才踢一轮，欧冠踢一轮赚一轮，光脚的不怕穿鞋的。</p>
<p><b style="color:#aaa;">对赛往绩：</b>2017年欧罗巴两回合，费内巴切客场2-1、主场1-1，保持不败。</p>
<h4 style="color:#aaa;margin:10px 0;">战术对决</h4>
<p>费内巴切：控球渗透，中路直塞、定位球、高空轰炸三件套——牌面碾压，但上轮两回合只进两个球，破铁桶阵是真短板。格拉茨风暴：锋线六人伤停，反击火力大减，预计只能堆人摆低位铁桶，靠定位球偷一个。</p>
<p><b style="color:#ffd93d;">克制关系：0</b>——费内巴切有牌面优势，攻坚效率却撑不起净胜两球的预期。</p>
<h4 style="color:#aaa;margin:10px 0;">关键先生</h4>
<p>费内巴切：塔利斯卡（94号前腰，上轮6.8分）——破密集防守，靠他的最后一传和远射。格拉茨风暴：沃达尔茨克（17号中锋，上轮8.0分）——六个攻击手倒下后，他是残阵里唯一能指望的支点。</p>'''
assert html.count(a5) == 1, "m2 悬念定位失败"
html = html.replace(a5, a5 + "\n" + block2, 1)

# ---- 7) 场2：关键信号后插 m2_signals.png ----
a6 = '<p><b style="color:#ffd93d;">关键信号：</b>'
assert html.count(a6) == 2, "关键信号总数应为2"
i6 = html.find(a6, html.find("费内巴切"))
i6_end = html.find("</p>", i6) + len("</p>")
sig2 = ('\n' + img_tag("m2_signals.png", "关键预期对比：净胜与大小球") +
        '\n<p style="text-align:center;color:#888;font-size:0.85em;">⬆ 关键预期对比：市场更相信费内巴切净胜两球，模型表示怀疑</p>')
html = html[:i6_end] + sig2 + html[i6_end:]

io.open(PATH, "w", encoding="utf-8").write(html)
print("OK 已更新 HTML，长度", len(html))
