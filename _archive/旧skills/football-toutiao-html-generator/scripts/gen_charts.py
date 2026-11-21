"""
头条号文章SVG图表生成器
用法: python gen_charts.py <model_probs> <market_odds> <radar_home> <radar_away> [output_dir]

参数:
  model_probs  - 模型概率,逗号分隔 (主胜,平局,客胜)  例: "56.9,19.7,23.4"
  market_odds  - 市场平均赔率,逗号分隔 (主,平,客)    例: "1.83,3.95,3.60"
  radar_home   - 主队六维数据,逗号分隔               例: "50,78,28,60,55,57"
  radar_away   - 客队六维数据,逗号分隔               例: "67,52,57,20,25,23"
  output_dir   - 输出目录 (可选,默认当前目录)

输出: radar_chart.svg, bar_chart.svg, pie_chart.svg
"""

import math, os, sys

DIMS = ["近期状态","进攻火力","防守稳固","交锋历史","市场支持","模型预测"]

def pie_slice(cx, cy, r, a1, a2, color):
    a1r = math.radians(a1); a2r = math.radians(a2)
    x1 = cx + r * math.cos(a1r); y1 = cy + r * math.sin(a1r)
    x2 = cx + r * math.cos(a2r); y2 = cy + r * math.sin(a2r)
    large = 1 if a2 - a1 > 180 else 0
    return '<path d="M{:.0f},{:.0f} L{:.1f},{:.1f} A{:.0f},{:.0f} 0 {},1 {:.1f},{:.1f} Z" fill="{}" stroke="#1a1a2e" stroke-width="2"/>'.format(cx,cy,x1,y1,r,r,large,x2,y2,color)

def radar_svg(home_data, away_data, home_name="主队", away_name="客队"):
    n = len(DIMS)
    cx, cy, radius = 300, 230, 150
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 460" width="100%" style="max-width:600px">']
    lines.append('<rect width="600" height="460" fill="#1a1a2e" rx="8"/>')
    lines.append(f'<text x="300" y="28" text-anchor="middle" fill="#e0e0e0" font-size="16" font-weight="bold">六维战力对比雷达图</text>')
    for r in [30, 60, 90, 120, 150]:
        pts = []
        for i in range(n):
            angle = math.radians(90 - i * 360 / n)
            x = cx + r * math.cos(angle); y = cy - r * math.sin(angle)
            pts.append("{:.1f},{:.1f}".format(x,y))
        lines.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#333" stroke-width="0.5"/>')
    for i in range(n):
        angle = math.radians(90 - i * 360 / n)
        lx = cx + radius * math.cos(angle); ly = cy - radius * math.sin(angle)
        lines.append(f'<line x1="{cx}" y1="{cy}" x2="{lx:.1f}" y2="{ly:.1f}" stroke="#444" stroke-width="0.5"/>')
        lx2 = cx + (radius + 30) * math.cos(angle); ly2 = cy - (radius + 30) * math.sin(angle)
        lines.append(f'<text x="{lx2:.1f}" y="{ly2:.1f}" text-anchor="middle" fill="#aaa" font-size="12">{DIMS[i]}</text>')
    for name, data, color in [(home_name, home_data, "#4fc3f7"), (away_name, away_data, "#ff6b6b")]:
        pts = []
        for i in range(n):
            val = data[i] / 100 * radius
            angle = math.radians(90 - i * 360 / n)
            x = cx + val * math.cos(angle); y = cy - val * math.sin(angle)
            pts.append("{:.1f},{:.1f}".format(x,y))
        lines.append(f'<polygon points="{" ".join(pts)}" fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="2"/>')
        for i in range(n):
            val = data[i] / 100 * radius
            angle = math.radians(90 - i * 360 / n)
            x = cx + val * math.cos(angle); y = cy - val * math.sin(angle)
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')
    lines.append(f'<rect x="140" y="430" width="12" height="12" fill="#4fc3f7" rx="2"/><text x="156" y="441" fill="#e0e0e0" font-size="13">{home_name}</text>')
    lines.append(f'<rect x="330" y="430" width="12" height="12" fill="#ff6b6b" rx="2"/><text x="346" y="441" fill="#e0e0e0" font-size="13">{away_name}</text>')
    lines.append('</svg>')
    return '\n'.join(lines)

def bar_svg(model_probs, market_odds):
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 420" width="100%" style="max-width:600px">']
    lines.append('<rect width="600" height="420" fill="#1a1a2e" rx="8"/>')
    lines.append('<text x="300" y="28" text-anchor="middle" fill="#e0e0e0" font-size="16" font-weight="bold">模型概率 vs 市场隐含概率</text>')
    labels = ["主胜", "平局", "客胜"]
    total_r = sum(1/o for o in market_odds)
    market_probs = [round(100*(1/o)/total_r, 1) for o in market_odds]
    bar_w, start_x = 55, 120
    for i in range(3):
        gx = start_x + i * 160
        mh = model_probs[i] * 3.5; kh = market_probs[i] * 3.5
        lines.append(f'<rect x="{gx}" y="{370-mh:.1f}" width="{bar_w}" height="{mh:.1f}" fill="#4fc3f7" rx="3"/>')
        lines.append(f'<text x="{gx+bar_w/2}" y="{365-mh:.1f}" text-anchor="middle" fill="#4fc3f7" font-size="13">{model_probs[i]}%</text>')
        lines.append(f'<rect x="{gx+bar_w+8}" y="{370-kh:.1f}" width="{bar_w}" height="{kh:.1f}" fill="#ffd93d" rx="3"/>')
        lines.append(f'<text x="{gx+bar_w+8+bar_w/2}" y="{365-kh:.1f}" text-anchor="middle" fill="#ffd93d" font-size="13">{market_probs[i]}%</text>')
        lines.append(f'<text x="{gx+bar_w+4}" y="400" text-anchor="middle" fill="#aaa" font-size="12">{labels[i]}</text>')
        edge = model_probs[i] - market_probs[i]
        ec = "#4fc3f7" if edge > 0 else "#ff6b6b"
        lines.append(f'<text x="{gx+bar_w+4}" y="362" text-anchor="middle" fill="{ec}" font-size="11">{"+" if edge>0 else ""}{edge:.1f}pp</text>')
    lines.append(f'<line x1="100" y1="372" x2="540" y2="372" stroke="#555" stroke-width="1"/>')
    lines.append(f'<rect x="180" y="8" width="10" height="10" fill="#4fc3f7" rx="2"/><text x="195" y="18" fill="#e0e0e0" font-size="12">模型概率</text>')
    lines.append(f'<rect x="330" y="8" width="10" height="10" fill="#ffd93d" rx="2"/><text x="345" y="18" fill="#e0e0e0" font-size="12">市场隐含</text>')
    lines.append('</svg>')
    return '\n'.join(lines)

def pie_svg(model_probs, top_scores):
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 420" width="100%" style="max-width:600px">']
    lines.append('<rect width="600" height="420" fill="#1a1a2e" rx="8"/>')
    lines.append('<text x="300" y="28" text-anchor="middle" fill="#e0e0e0" font-size="16" font-weight="bold">模型概率分布 &amp; 比分概率</text>')
    labels = ["主队胜", "平局", "客队胜"]
    colors = ["#4fc3f7", "#ffd93d", "#ff6b6b"]
    pcx, pcy, pr = 170, 215, 110
    ang = -90
    for i in range(3):
        da = model_probs[i] / 100 * 360
        lines.append(pie_slice(pcx, pcy, pr, ang, ang+da, colors[i]))
        ma = math.radians(ang + da/2)
        lx = pcx + (pr+20)*math.cos(ma); ly = pcy + (pr+20)*math.sin(ma)
        lx2 = pcx + (pr+50)*math.cos(ma); ly2 = pcy + (pr+50)*math.sin(ma)
        lines.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{lx2:.1f}" y2="{ly2:.1f}" stroke="{colors[i]}" stroke-width="1"/>')
        a = "start" if lx2 > pcx else "end"
        lines.append(f'<text x="{lx2:.1f}" y="{ly2+4:.1f}" text-anchor="{a}" fill="{colors[i]}" font-size="11">{labels[i]} {model_probs[i]:.1f}%</text>')
        ang += da
    scx, scy, sr = 420, 210, 75
    s_colors = ["#4fc3f7", "#ffd93d", "#ff6b6b", "#555"]
    ang = -90
    for i, (label, val) in enumerate(top_scores):
        da = val / 100 * 360
        lines.append(pie_slice(scx, scy, sr, ang, ang+da, s_colors[i]))
        if i < 3:
            ma = math.radians(ang + da/2)
            lx = scx + (sr*0.6)*math.cos(ma); ly = scy + (sr*0.6)*math.sin(ma)
            lines.append(f'<text x="{lx:.1f}" y="{ly+3:.1f}" text-anchor="middle" fill="#fff" font-size="11" font-weight="bold">{label} {val:.1f}%</text>')
        ang += da
    lines.append('<text x="420" y="315" text-anchor="middle" fill="#aaa" font-size="12">高概率比分</text>')
    lines.append('</svg>')
    return '\n'.join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        model_probs = [56.9, 19.7, 23.4]
        market_odds = [1.83, 3.95, 3.60]
        radar_home = [50, 78, 28, 60, 55, 57]
        radar_away = [67, 52, 57, 20, 25, 23]
        top_scores = [("2-1", 9.0), ("1-1", 7.8), ("3-1", 6.9), ("其他", 76.3)]
        outdir = "."
    else:
        model_probs = [float(x) for x in sys.argv[1].split(",")]
        market_odds = [float(x) for x in sys.argv[2].split(",")]
        radar_home = [float(x) for x in sys.argv[3].split(",")]
        radar_away = [float(x) for x in sys.argv[4].split(",")]
        top_scores = [("2-1", 9.0), ("1-1", 7.8), ("3-1", 6.9), ("其他", 76.3)]
        outdir = sys.argv[5] if len(sys.argv) > 5 else "."
    
    files = [
        (os.path.join(outdir, "radar_chart.svg"), radar_svg(radar_home, radar_away)),
        (os.path.join(outdir, "bar_chart.svg"), bar_svg(model_probs, market_odds)),
        (os.path.join(outdir, "pie_chart.svg"), pie_svg(model_probs, top_scores)),
    ]
    for path, content in files:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"OK {path} ({os.path.getsize(path)} bytes)")
    print("Done")
