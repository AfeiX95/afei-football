import math, sys, os
sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# SVG Chart Generation Functions
# ============================================================

def radar_chart_svg(title, home_name, away_name, home_vals, away_vals, dims, width=600, height=460):
    """Generate a six-dimensional radar chart SVG."""
    cx, cy = width // 2, height // 2 + 10
    max_r = 160
    n = len(dims)
    angle_step = 2 * math.pi / n
    start_angle = -math.pi / 2  # start from top
    
    # Grid rings
    rings = [0.2, 0.4, 0.6, 0.8, 1.0]
    grid_lines = []
    for r in rings:
        points = []
        for i in range(n):
            angle = start_angle + i * angle_step
            x = cx + max_r * r * math.cos(angle)
            y = cy + max_r * r * math.sin(angle)
            points.append(f"{x:.1f},{y:.1f}")
        grid_lines.append(f'<polygon points="{" ".join(points)}" fill="none" stroke="#333" stroke-width="0.5"/>')
    
    # Axis lines
    axis_lines = []
    for i in range(n):
        angle = start_angle + i * angle_step
        x = cx + max_r * math.cos(angle)
        y = cy + max_r * math.sin(angle)
        axis_lines.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#333" stroke-width="0.5"/>')
    
    # Data polygons
    def data_polygon(vals, color, opacity=0.15):
        points = []
        for i, v in enumerate(vals):
            angle = start_angle + i * angle_step
            r = max_r * v / 100
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append(f"{x:.1f},{y:.1f}")
        return f'<polygon points="{" ".join(points)}" fill="{color}" fill-opacity="{opacity}" stroke="{color}" stroke-width="2"/>'
    
    def data_dots(vals, color):
        dots = []
        for i, v in enumerate(vals):
            angle = start_angle + i * angle_step
            r = max_r * v / 100
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')
        return "\n".join(dots)
    
    # Labels
    labels = []
    for i, dim in enumerate(dims):
        angle = start_angle + i * angle_step
        lx = cx + (max_r + 30) * math.cos(angle)
        ly = cy + (max_r + 30) * math.sin(angle)
        anchor = "middle"
        if math.cos(angle) > 0.1: anchor = "start"
        elif math.cos(angle) < -0.1: anchor = "end"
        labels.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#ccc" font-size="11" text-anchor="{anchor}" dominant-baseline="middle">{dim}</text>')
        # Value labels
        for j, (vals, color) in enumerate([(home_vals, "#4fc3f7"), (away_vals, "#ff6b6b")]):
            vr = max_r * vals[i] / 100
            vx = cx + vr * math.cos(angle) + (8 if j == 0 else -8)
            vy = cy + vr * math.sin(angle) - 8
            labels.append(f'<text x="{vx:.1f}" y="{vy:.1f}" fill="{color}" font-size="9" text-anchor="middle">{vals[i]}</text>')
    
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="#1a1a2e"/>
<text x="{cx}" y="25" fill="#fff" font-size="14" text-anchor="middle" font-weight="bold">{title}</text>
{chr(10).join(grid_lines)}
{chr(10).join(axis_lines)}
{data_polygon(home_vals, "#4fc3f7")}
{data_polygon(away_vals, "#ff6b6b")}
{data_dots(home_vals, "#4fc3f7")}
{data_dots(away_vals, "#ff6b6b")}
{chr(10).join(labels)}
<rect x="20" y="{height-30}" width="12" height="12" fill="#4fc3f7" fill-opacity="0.3" stroke="#4fc3f7"/>
<text x="38" y="{height-20}" fill="#ccc" font-size="11">{home_name}</text>
<rect x="120" y="{height-30}" width="12" height="12" fill="#ff6b6b" fill-opacity="0.3" stroke="#ff6b6b"/>
<text x="138" y="{height-20}" fill="#ccc" font-size="11">{away_name}</text>
</svg>'''
    return svg


def bar_chart_svg(title, model_probs, market_probs, labels_list, width=600, height=420):
    """Generate a bar chart comparing model vs market probabilities."""
    cx = width // 2
    bar_w = 55
    gap = 160
    x_base = cx - gap
    y_base = 372
    max_h = 280
    
    bars = []
    texts = []
    for i, (mp, mkp, lbl) in enumerate(zip(model_probs, market_probs, labels_list)):
        x = x_base + i * gap
        h_m = max_h * mp / 100
        h_mk = max_h * mkp / 100
        
        # Model bar (blue)
        bars.append(f'<rect x="{x}" y="{y_base - h_m:.1f}" width="{bar_w}" height="{h_m:.1f}" fill="#4fc3f7" rx="3"/>')
        # Market bar (yellow)
        bars.append(f'<rect x="{x + bar_w + 5}" y="{y_base - h_mk:.1f}" width="{bar_w}" height="{h_mk:.1f}" fill="#ffd93d" rx="3"/>')
        
        # Percentage labels
        texts.append(f'<text x="{x + bar_w//2}" y="{y_base - h_m - 5:.1f}" fill="#4fc3f7" font-size="11" text-anchor="middle">{mp:.1f}%</text>')
        texts.append(f'<text x="{x + bar_w + 5 + bar_w//2}" y="{y_base - h_mk - 5:.1f}" fill="#ffd93d" font-size="11" text-anchor="middle">{mkp:.1f}%</text>')
        
        # Edge label
        edge = mp - mkp
        edge_color = "#4caf50" if edge > 0 else "#ff6b6b"
        edge_sign = "+" if edge > 0 else ""
        texts.append(f'<text x="{x + bar_w + 2}" y="{y_base + 15}" fill="{edge_color}" font-size="10" text-anchor="middle">{edge_sign}{edge:.1f}pp</text>')
        
        # Category label
        texts.append(f'<text x="{x + bar_w}" y="{y_base + 35}" fill="#ccc" font-size="12" text-anchor="middle">{lbl}</text>')
    
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="#1a1a2e"/>
<text x="{cx}" y="25" fill="#fff" font-size="14" text-anchor="middle" font-weight="bold">{title}</text>
<line x1="50" y1="{y_base}" x2="{width-50}" y2="{y_base}" stroke="#444" stroke-width="1"/>
{chr(10).join(bars)}
{chr(10).join(texts)}
<rect x="30" y="{height-25}" width="12" height="12" fill="#4fc3f7"/>
<text x="48" y="{height-14}" fill="#ccc" font-size="11">后台模型</text>
<rect x="130" y="{height-25}" width="12" height="12" fill="#ffd93d"/>
<text x="148" y="{height-14}" fill="#ccc" font-size="11">市场隐含</text>
</svg>'''
    return svg


def pie_chart_svg(title, pie1_data, pie2_data, width=600, height=420):
    """Generate dual pie chart SVG."""
    # Left pie: model probability distribution
    cx1, cy1, r1 = 170, 200, 110
    # Right pie: top scores distribution
    cx2, cy2, r2 = 430, 200, 75
    
    def draw_pie(cx, cy, r, data, start_angle=-math.pi/2):
        arcs = []
        total = sum(d[1] for d in data)
        angle = start_angle
        for label, pct, color in data:
            sweep = 2 * math.pi * pct / total
            x1 = cx + r * math.cos(angle)
            y1 = cy + r * math.sin(angle)
            x2 = cx + r * math.cos(angle + sweep)
            y2 = cy + r * math.sin(angle + sweep)
            large = 1 if sweep > math.pi else 0
            arcs.append(f'<path d="M {cx},{cy} L {x1:.1f},{y1:.1f} A {r},{r} 0 {large},1 {x2:.1f},{y2:.1f} Z" fill="{color}" stroke="#1a1a2e" stroke-width="1"/>')
            
            # Label
            mid_angle = angle + sweep / 2
            lx = cx + (r + 25) * math.cos(mid_angle)
            ly = cy + (r + 25) * math.sin(mid_angle)
            if pct > 5:
                arcs.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#ccc" font-size="10" text-anchor="middle">{label} {pct:.1f}%</text>')
            
            angle += sweep
        return "\n".join(arcs)
    
    left_pie = draw_pie(cx1, cy1, r1, pie1_data)
    right_pie = draw_pie(cx2, cy2, r2, pie2_data)
    
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="#1a1a2e"/>
<text x="{cx1}" y="30" fill="#fff" font-size="13" text-anchor="middle" font-weight="bold">模型概率分布</text>
<text x="{cx2}" y="30" fill="#fff" font-size="13" text-anchor="middle" font-weight="bold">高概率比分</text>
{left_pie}
{right_pie}
</svg>'''
    return svg


# ============================================================
# Generate Match 1: 瓦勒伦加 vs 汉坎
# ============================================================

# Radar data (normalized 0-100)
dims_m1 = ["近期状态", "进攻火力", "防守稳固", "交锋历史", "市场支持", "模型预测"]
home_m1 = [60, 78, 50, 25, 70, 55]  # 瓦勒伦加
away_m1 = [30, 35, 25, 72, 25, 35]  # 汉坎

# Bar chart data
model_m1 = [48.6, 24.1, 27.2]
market_m1 = [59.4, 21.3, 19.2]
labels_m1 = ["瓦勒伦加胜", "平局", "汉坎胜"]

# Pie chart data
pie1_m1 = [("瓦勒伦加胜", 48.6, "#4fc3f7"), ("平局", 24.1, "#ffd93d"), ("汉坎胜", 27.2, "#ff6b6b")]
pie2_m1 = [("1-1", 11.3, "#4fc3f7"), ("2-1", 9.5, "#ffd93d"), ("1-0", 9.6, "#ff6b6b"), ("2-0", 8.0, "#4caf50"), ("其他", 61.6, "#666")]

radar1 = radar_chart_svg("六维能力雷达图", "瓦勒伦加", "汉坎", home_m1, away_m1, dims_m1)
bar1 = bar_chart_svg("模型 vs 市场概率对比", model_m1, market_m1, labels_m1)
pie1 = pie_chart_svg("概率分布 & 高概率比分", pie1_m1, pie2_m1)

# ============================================================
# Generate Match 2: 博德闪耀 vs 利勒斯特
# ============================================================

dims_m2 = ["近期状态", "进攻火力", "防守稳固", "交锋历史", "市场支持", "模型预测"]
home_m2 = [95, 95, 95, 75, 90, 75]  # 博德闪耀
away_m2 = [45, 40, 60, 30, 15, 25]  # 利勒斯特

model_m2 = [65.7, 19.6, 14.8]
market_m2 = [75.7, 14.5, 9.8]
labels_m2 = ["博德闪耀胜", "平局", "利勒斯特胜"]

pie1_m2 = [("博德闪耀胜", 65.7, "#4fc3f7"), ("平局", 19.6, "#ffd93d"), ("利勒斯特胜", 14.8, "#ff6b6b")]
pie2_m2 = [("2-0", 11.0, "#4fc3f7"), ("1-0", 10.2, "#ffd93d"), ("2-1", 9.9, "#ff6b6b"), ("1-1", 9.3, "#4caf50"), ("其他", 59.6, "#666")]

radar2 = radar_chart_svg("六维能力雷达图", "博德闪耀", "利勒斯特", home_m2, away_m2, dims_m2)
bar2 = bar_chart_svg("模型 vs 市场概率对比", model_m2, market_m2, labels_m2)
pie2 = pie_chart_svg("概率分布 & 高概率比分", pie1_m2, pie2_m2)

# ============================================================
# Generate HTML
# ============================================================

html = f'''<div style="background:#0f0f1a;color:#e0e0e0;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;line-height:1.8;padding:20px;max-width:720px;margin:0 auto;">

<h2 style="color:#fff;text-align:center;border-bottom:2px solid #4fc3f7;padding-bottom:10px;">挪超双响：瓦勒伦加碰克星 博德闪耀欧冠要留力</h2>
<p style="text-align:center;color:#888;font-size:0.9em;">#挪超 #瓦勒伦加 #汉坎 #博德闪耀 #利勒斯特 #足球前瞻 · 2026-08-01 · 第16轮</p>

<hr style="border-color:#333;">

<p style="text-align:center;color:#aaa;font-style:italic;">数据不会说谎，但人会。——阿飞·赛博聊球</p>

<hr style="border-color:#333;">

<p>今晚两场挪超，市场又被"排名差"骗了。</p>
<p>后台模型跑了20万次，跑出了两个被忽略的信号：第一场主胜溢价10.8pp，第二场主胜过热10pp。两场加起来，市场在主胜方向多给了20个百分点的"面子钱"。</p>

<hr style="border-color:#333;">

<h3 style="color:#4fc3f7;">⚔️ 瓦勒伦加 vs 汉坎 | 01:00</h3>

<p><strong>⚔️ 战意：</strong>瓦勒伦加第7，汉坎第10。排名差3位，听起来主队稳了？</p>
<p>但你把H2H拉出来看——近9场交锋，瓦勒伦加2胜4平3负。<strong style="color:#ff6b6b;">22%的胜率。</strong></p>
<p>汉坎是瓦勒伦加的绝对克星。9场只输2场，赢了3场，平了4场。这不是偶然，这是结构性压制。</p>
<p>说白了，汉坎不怕瓦勒伦加。怕的是比瓦勒伦加更强的队。</p>

<h3 style="color:#ffd93d;">📊 基础数据对比</h3>
<table style="width:100%;border-collapse:collapse;text-align:center;">
<tr style="background:#1e3a5f;color:#fff;">
<th>对比项</th><th>瓦勒伦加（主）</th><th>汉坎（客）</th>
</tr>
<tr style="background:#16213e;">
<td>联赛排名</td><td style="color:#4fc3f7;">第7</td><td>第10</td>
</tr>
<tr style="background:#1a1a2e;">
<td>赛季总成绩</td><td style="color:#4fc3f7;">6胜2平6负（43%）</td><td>5胜3平6负（36%）</td>
</tr>
<tr style="background:#16213e;">
<td>主/客场成绩</td><td style="color:#4fc3f7;">4胜1平2负（57%）</td><td style="color:#ff6b6b;">0胜3平4负（0%）</td>
</tr>
<tr style="background:#1a1a2e;">
<td>赛季进球/失球</td><td>22/24（净-2）</td><td>20/26（净-6）</td>
</tr>
<tr style="background:#16213e;">
<td>场均进球</td><td style="color:#4fc3f7;">2.14</td><td>1.00（客场）</td>
</tr>
<tr style="background:#1a1a2e;">
<td>场均失球</td><td>1.29</td><td style="color:#ff6b6b;">2.14（客场）</td>
</tr>
<tr style="background:#16213e;">
<td>H2H（近9场）</td><td>2胜4平3负</td><td style="color:#ff6b6b;">3胜4平2负</td>
</tr>
</table>

{radar1}
<p style="text-align:center;color:#888;font-size:0.85em;">⬆ 六维能力雷达图：汉坎在交锋历史维度全面压制瓦勒伦加</p>

<h3 style="color:#ffd93d;">📊 近5场状态对比</h3>
<table style="width:100%;border-collapse:collapse;text-align:center;">
<tr style="background:#1e3a5f;color:#fff;">
<th>日期</th><th>瓦勒伦加</th><th>比分</th><th>汉坎</th>
</tr>
<tr style="background:#16213e;"><td>7/26</td><td style="color:#4caf50;">布兰(客) ✅2-3</td><td></td><td style="color:#ff6b6b;">萨普斯堡(客) ❌0-1</td></tr>
<tr style="background:#1a1a2e;"><td>7/17</td><td style="color:#4caf50;">奥勒松(主) ✅6-1</td><td></td><td style="color:#ff6b6b;">博德闪耀(客) ❌0-3</td></tr>
<tr style="background:#16213e;"><td>7/12</td><td style="color:#ff6b6b;">特罗姆瑟(客) ❌0-4</td><td></td><td style="color:#ff6b6b;">特罗姆瑟(主) ❌1-4</td></tr>
<tr style="background:#1a1a2e;"><td>5/30</td><td style="color:#4caf50;">克里斯蒂(主) ✅3-1</td><td></td><td style="color:#ffd93d;">奥勒松(客) 🟰2-2</td></tr>
<tr style="background:#16213e;"><td>5/25</td><td style="color:#ff6b6b;">斯达(客) ❌0-2</td><td></td><td style="color:#4caf50;">利勒斯特(主) ✅2-0</td></tr>
</table>

<h3 style="color:#ffd93d;">🌍 外媒方向</h3>
<p>FootballPredictions.com看好瓦勒伦加3-1大胜，BTTS是+大3.5球+Promise Meliga任何时间进球。</p>
<p>但说句不好听的，FootballPredictions的3-1预测完全忽略了H2H因素。汉坎在9场交锋中3胜4平2负——这不是一支能被瓦勒伦加轻松拿下的球队。</p>

<h3 style="color:#ffd93d;">💰 信号</h3>
<table style="width:100%;border-collapse:collapse;text-align:center;">
<tr style="background:#1e3a5f;color:#fff;">
<th>指标</th><th>后台模型</th><th>市场隐含</th><th>Edge</th>
</tr>
<tr style="background:#16213e;">
<td>瓦勒伦加胜</td><td style="color:#4fc3f7;">48.6%</td><td>59.4%</td><td style="color:#ff6b6b;">-10.8pp</td>
</tr>
<tr style="background:#1a1a2e;">
<td>平局</td><td style="color:#ffd93d;">24.1%</td><td>21.3%</td><td style="color:#4caf50;">+2.8pp</td>
</tr>
<tr style="background:#16213e;">
<td>汉坎胜</td><td style="color:#ff6b6b;">27.2%</td><td>19.2%</td><td style="color:#4caf50;"><strong>+8.0pp</strong></td>
</tr>
</table>

{bar1}
<p style="text-align:center;color:#888;font-size:0.85em;">⬆ 模型 vs 市场概率：主胜被高估10.8pp，汉坎客胜有8.0pp价值</p>

<h3 style="color:#ffd93d;">📊 高概率比分</h3>
<table style="width:100%;border-collapse:collapse;text-align:center;">
<tr style="background:#1e3a5f;color:#fff;">
<th>维度</th><th>比分</th><th>概率</th>
</tr>
<tr style="background:#16213e;"><td style="color:#4caf50;"><strong>首选</strong></td><td><strong>1-1</strong></td><td><strong>11.3%</strong></td></tr>
<tr style="background:#1a1a2e;"><td>次选</td><td>2-1</td><td>9.5%</td></tr>
<tr style="background:#16213e;"><td style="color:#ffd93d;">留意</td><td>0-1</td><td>6.9%</td></tr>
</table>

{pie1}
<p style="text-align:center;color:#888;font-size:0.85em;">⬆ 概率分布：1-1最高概率11.3%，2-1次之9.5%</p>

<hr style="border-color:#333;">

<h3 style="color:#ff6b6b;">⚔️ 博德闪耀 vs 利勒斯特 | 03:00</h3>

<p><strong>⚔️ 战意：</strong>博德闪耀第1，利勒斯特第4。挪超最强vs联赛第四。</p>
<p>但有个变量被市场完全忽略了——<strong style="color:#ff6b6b;">5天后欧冠资格赛客战圣吉联合</strong>。</p>
<p>博德闪耀近10场9胜1平0负，进31球仅失5球。主场7场6胜0平1负，进20球仅失2球。</p>
<p>但问题是：欧冠生死战在即，教练Knutsen几乎必然轮换2-3名核心。Høgh（7球4助攻）、埃夫延（5球2助攻）——如果轮休，进攻效率至少下降20-30%。</p>

<h3 style="color:#ffd93d;">📊 基础数据对比</h3>
<table style="width:100%;border-collapse:collapse;text-align:center;">
<tr style="background:#1e3a5f;color:#fff;">
<th>对比项</th><th>博德闪耀（主）</th><th>利勒斯特（客）</th>
</tr>
<tr style="background:#16213e;"><td>联赛排名</td><td style="color:#4fc3f7;"><strong>第1</strong></td><td>第4</td></tr>
<tr style="background:#1a1a2e;"><td>赛季总成绩</td><td style="color:#4fc3f7;">11胜2平2负（73%）</td><td>8胜1平5负（57%）</td></tr>
<tr style="background:#16213e;"><td>主/客场成绩</td><td style="color:#4fc3f7;">6胜0平1负（86%）</td><td>4胜1平2负（57%）</td></tr>
<tr style="background:#1a1a2e;"><td>赛季进球/失球</td><td style="color:#4fc3f7;"><strong>37/11（净+26）</strong></td><td>22/14（净+8）</td></tr>
<tr style="background:#16213e;"><td>场均进球</td><td style="color:#4fc3f7;">2.86</td><td>1.14（客场）</td></tr>
<tr style="background:#1a1a2e;"><td>场均失球</td><td style="color:#4fc3f7;">0.29</td><td>0.71（客场）</td></tr>
<tr style="background:#16213e;"><td>积分</td><td style="color:#4fc3f7;"><strong>35分</strong></td><td>25分</td></tr>
</table>

{radar2}
<p style="text-align:center;color:#888;font-size:0.85em;">⬆ 六维能力雷达图：博德闪耀全面碾压，但欧冠轮换是最大变量</p>

<h3 style="color:#ffd93d;">📊 近5场状态对比</h3>
<table style="width:100%;border-collapse:collapse;text-align:center;">
<tr style="background:#1e3a5f;color:#fff;">
<th>日期</th><th>博德闪耀</th><th>比分</th><th>利勒斯特</th>
</tr>
<tr style="background:#16213e;"><td>7/26</td><td style="color:#4caf50;">桑纳菲(客) ✅0-3</td><td></td><td style="color:#ff6b6b;">维京(主) ❌1-2</td></tr>
<tr style="background:#1a1a2e;"><td>7/23</td><td style="color:#4caf50;">汉坎(主) ✅3-0</td><td></td><td style="color:#4caf50;">奥斯KFUM(主) ✅2-1</td></tr>
<tr style="background:#16213e;"><td>7/18</td><td style="color:#4caf50;">腓特烈(主) ✅1-0</td><td></td><td style="color:#4caf50;">腓特烈(客) ✅0-2</td></tr>
<tr style="background:#1a1a2e;"><td>7/12</td><td style="color:#4caf50;">奥斯KFUM(客) ✅0-2</td><td></td><td style="color:#ff6b6b;">中日德兰(客) ❌1-0</td></tr>
<tr style="background:#16213e;"><td>7/4</td><td style="color:#4caf50;">斯达(主·杯赛) ✅4-0</td><td></td><td style="color:#ff6b6b;">汉坎(客) ❌2-0</td></tr>
</table>

<h3 style="color:#ffd93d;">🌍 外媒方向</h3>
<p>FootballPredictions.com看好博德闪耀3-1大胜，BTTS是+大3.5球+Helmersen任何时间进球。</p>
<p>H2H数据（20场）：博德闪耀45%胜、25%平、利勒斯特30%胜。85%的比赛进球≥2。</p>
<p>但说白了，FootballPredictions的3-1预测建立在博德闪耀全主力出战的假设上。5天后就是欧冠生死战——这个变量被所有外媒忽略了。</p>

<h3 style="color:#ffd93d;">💰 信号</h3>
<table style="width:100%;border-collapse:collapse;text-align:center;">
<tr style="background:#1e3a5f;color:#fff;">
<th>指标</th><th>后台模型</th><th>市场隐含</th><th>Edge</th>
</tr>
<tr style="background:#16213e;">
<td>博德闪耀胜</td><td style="color:#4fc3f7;">65.7%</td><td>75.7%</td><td style="color:#ff6b6b;">-10.0pp</td>
</tr>
<tr style="background:#1a1a2e;">
<td>平局</td><td style="color:#ffd93d;">19.6%</td><td>14.5%</td><td style="color:#4caf50;"><strong>+5.1pp</strong></td>
</tr>
<tr style="background:#16213e;">
<td>利勒斯特胜</td><td style="color:#ff6b6b;">14.8%</td><td>9.8%</td><td style="color:#4caf50;"><strong>+5.0pp</strong></td>
</tr>
</table>

{bar2}
<p style="text-align:center;color:#888;font-size:0.85em;">⬆ 模型 vs 市场概率：主胜过热10pp，平局+客胜均有正Edge</p>

<h3 style="color:#ffd93d;">📊 高概率比分</h3>
<table style="width:100%;border-collapse:collapse;text-align:center;">
<tr style="background:#1e3a5f;color:#fff;">
<th>维度</th><th>比分</th><th>概率</th>
</tr>
<tr style="background:#16213e;"><td style="color:#4caf50;"><strong>首选</strong></td><td><strong>2-0</strong></td><td><strong>11.0%</strong></td></tr>
<tr style="background:#1a1a2e;"><td>次选</td><td>1-0</td><td>10.2%</td></tr>
<tr style="background:#16213e;"><td style="color:#ffd93d;">留意</td><td>2-1</td><td>9.9%</td></tr>
</table>

{pie2}
<p style="text-align:center;color:#888;font-size:0.85em;">⬆ 概率分布：2-0最高概率11.0%，1-0次之10.2%</p>

<hr style="border-color:#333;">

<h3 style="color:#fff;text-align:center;">📊 两场总览</h3>
<table style="width:100%;border-collapse:collapse;text-align:center;">
<tr style="background:#1e3a5f;color:#fff;">
<th>场次</th><th>对阵</th><th>模型倾向</th><th>最强信号</th><th>高概率比分</th>
</tr>
<tr style="background:#16213e;">
<td>①</td><td>瓦勒伦加VS汉坎</td><td style="color:#ff6b6b;">主胜被高估</td><td style="color:#4caf50;">让1球客胜 +10.6pp</td><td>1-1 / 2-1 / 0-1</td>
</tr>
<tr style="background:#1a1a2e;">
<td>②</td><td>博德闪耀VS利勒斯特</td><td style="color:#ff6b6b;">主胜过热</td><td style="color:#4caf50;">让2球客胜 +11.8pp</td><td>2-0 / 1-0 / 2-1</td>
</tr>
</table>

<hr style="border-color:#333;">

<p>两场挪超，两个被市场高估的主胜。瓦勒伦加被H2H克星压制，博德闪耀被欧冠轮换拖累。</p>
<p>今晚的剧本：两场都是主队赢球但赢不了大胜。让球方向的客队才是真正的价值洼地。</p>

<p style="text-align:center;color:#4fc3f7;"><strong>你们觉得汉坎今晚能打破三连败吗？博德闪耀会不会因为欧冠轮换翻车？评论区留个比分，赛后回来验证。</strong></p>

<hr style="border-color:#333;">

<p style="color:#888;font-size:0.85em;"><strong>【免责声明】</strong><br>
本文内容仅代表作者个人的数据模型推演结果，属于体育赛事分析交流范畴，不构成任何指向性的购彩及投注建议。足球是圆的，概率不等于绝对。请各位球迷严格遵守国家法律法规，理性看待数据，适度娱乐。</p>

<p style="color:#666;font-size:0.8em;text-align:center;">1-封面-挪超前瞻瓦勒伦加碰克星 · 推荐图源：新球体育<br>
2-数据-瓦勒伦加vs汉坎近10场对比 · 推荐图源：竞彩网</p>

</div>'''

# Write HTML file
output_path = r'I:\阿飞说球\📝文章\20260731\挪超两场前瞻_瓦勒伦加汉坎_博德闪耀利勒斯特_头条版.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'HTML file written to: {output_path}')
print(f'File size: {os.path.getsize(output_path)} bytes')
