# -*- coding: utf-8 -*-
"""欧冠资格赛两场 SVG 图表生成（基于技能脚本扩展：自定义队名+比分Top）"""
import math, os, sys
sys.stdout.reconfigure(encoding="utf-8")

DIMS = ["近期状态","进攻火力","防守稳固","交锋历史","市场支持","模型预测"]

def pie_slice(cx, cy, r, a1, a2, color):
    a1r = math.radians(a1); a2r = math.radians(a2)
    x1 = cx + r*math.cos(a1r); y1 = cy + r*math.sin(a1r)
    x2 = cx + r*math.cos(a2r); y2 = cy + r*math.sin(a2r)
    large = 1 if a2-a1 > 180 else 0
    return '<path d="M{:.0f},{:.0f} L{:.1f},{:.1f} A{:.0f},{:.0f} 0 {},1 {:.1f},{:.1f} Z" fill="{}" stroke="#1a1a2e" stroke-width="2"/>'.format(cx,cy,x1,y1,r,r,large,x2,y2,color)

def radar_svg(home_data, away_data, home_name, away_name):
    n = len(DIMS); cx, cy, radius = 300, 230, 150
    L = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 460" width="100%" style="max-width:600px">']
    L.append('<rect width="600" height="460" fill="#1a1a2e" rx="8"/>')
    L.append(f'<text x="300" y="28" text-anchor="middle" fill="#e0e0e0" font-size="16" font-weight="bold">六维战力对比雷达图</text>')
    for r0 in [30,60,90,120,150]:
        pts = []
        for i in range(n):
            a = math.radians(90 - i*360/n); x = cx + r0*math.cos(a); y = cy - r0*math.sin(a)
            pts.append("{:.1f},{:.1f}".format(x,y))
        L.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#333" stroke-width="0.5"/>')
    for i in range(n):
        a = math.radians(90 - i*360/n)
        lx = cx + radius*math.cos(a); ly = cy - radius*math.sin(a)
        L.append(f'<line x1="{cx}" y1="{cy}" x2="{lx:.1f}" y2="{ly:.1f}" stroke="#444" stroke-width="0.5"/>')
        lx2 = cx + (radius+30)*math.cos(a); ly2 = cy - (radius+30)*math.sin(a)
        L.append(f'<text x="{lx2:.1f}" y="{ly2:.1f}" text-anchor="middle" fill="#aaa" font-size="12">{DIMS[i]}</text>')
    for name, data, color in [(home_name,home_data,"#4fc3f7"),(away_name,away_data,"#ff6b6b")]:
        pts = []
        for i in range(n):
            v = data[i]/100*radius; a = math.radians(90 - i*360/n)
            x = cx + v*math.cos(a); y = cy - v*math.sin(a)
            pts.append("{:.1f},{:.1f}".format(x,y))
        L.append(f'<polygon points="{" ".join(pts)}" fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="2"/>')
        for i in range(n):
            v = data[i]/100*radius; a = math.radians(90 - i*360/n)
            x = cx + v*math.cos(a); y = cy - v*math.sin(a)
            L.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')
    L.append(f'<rect x="140" y="430" width="12" height="12" fill="#4fc3f7" rx="2"/><text x="156" y="441" fill="#e0e0e0" font-size="13">{home_name}</text>')
    L.append(f'<rect x="330" y="430" width="12" height="12" fill="#ff6b6b" rx="2"/><text x="346" y="441" fill="#e0e0e0" font-size="13">{away_name}</text>')
    L.append('</svg>')
    return '\n'.join(L)

def bar_svg(model_probs, market_odds):
    L = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 420" width="100%" style="max-width:600px">']
    L.append('<rect width="600" height="420" fill="#1a1a2e" rx="8"/>')
    L.append('<text x="300" y="28" text-anchor="middle" fill="#e0e0e0" font-size="16" font-weight="bold">后台模型 vs 市场定价</text>')
    labels = ["主胜","平局","客胜"]
    total_r = sum(1/o for o in market_odds)
    market_probs = [round(100*(1/o)/total_r,1) for o in market_odds]
    bar_w, start_x = 55, 120
    for i in range(3):
        gx = start_x + i*160
        mh = model_probs[i]*3.5; kh = market_probs[i]*3.5
        L.append(f'<rect x="{gx}" y="{370-mh:.1f}" width="{bar_w}" height="{mh:.1f}" fill="#4fc3f7" rx="3"/>')
        L.append(f'<text x="{gx+bar_w/2}" y="{365-mh:.1f}" text-anchor="middle" fill="#4fc3f7" font-size="13">{model_probs[i]}%</text>')
        L.append(f'<rect x="{gx+bar_w+8}" y="{370-kh:.1f}" width="{bar_w}" height="{kh:.1f}" fill="#ffd93d" rx="3"/>')
        L.append(f'<text x="{gx+bar_w+8+bar_w/2}" y="{365-kh:.1f}" text-anchor="middle" fill="#ffd93d" font-size="13">{market_probs[i]}%</text>')
        L.append(f'<text x="{gx+bar_w+4}" y="400" text-anchor="middle" fill="#aaa" font-size="12">{labels[i]}</text>')
        edge = model_probs[i]-market_probs[i]
        ec = "#4fc3f7" if edge>0 else "#ff6b6b"
        L.append(f'<text x="{gx+bar_w+4}" y="360" text-anchor="middle" fill="{ec}" font-size="11">{"+" if edge>0 else ""}{edge:.1f}pp</text>')
    L.append('<line x1="100" y1="372" x2="540" y2="372" stroke="#555" stroke-width="1"/>')
    L.append('<rect x="180" y="8" width="10" height="10" fill="#4fc3f7" rx="2"/><text x="195" y="18" fill="#e0e0e0" font-size="12">后台模型</text>')
    L.append('<rect x="330" y="8" width="10" height="10" fill="#ffd93d" rx="2"/><text x="345" y="18" fill="#e0e0e0" font-size="12">市场定价</text>')
    L.append('</svg>')
    return '\n'.join(L)

def pie_svg(model_probs, top_scores):
    L = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 420" width="100%" style="max-width:600px">']
    L.append('<rect width="600" height="420" fill="#1a1a2e" rx="8"/>')
    L.append('<text x="300" y="28" text-anchor="middle" fill="#e0e0e0" font-size="16" font-weight="bold">模型概率分布 &amp; 高概率比分</text>')
    labels = ["主队胜","平局","客队胜"]; colors = ["#4fc3f7","#ffd93d","#ff6b6b"]
    pcx, pcy, pr = 170, 215, 110; ang = -90
    for i in range(3):
        da = model_probs[i]/100*360
        L.append(pie_slice(pcx,pcy,pr,ang,ang+da,colors[i]))
        ma = math.radians(ang+da/2)
        lx = pcx+(pr+20)*math.cos(ma); ly = pcy+(pr+20)*math.sin(ma)
        lx2 = pcx+(pr+50)*math.cos(ma); ly2 = pcy+(pr+50)*math.sin(ma)
        L.append(f'<line x1="{lx:.1f}" y1="{ly:.1f}" x2="{lx2:.1f}" y2="{ly2:.1f}" stroke="{colors[i]}" stroke-width="1"/>')
        a = "start" if lx2>pcx else "end"
        L.append(f'<text x="{lx2:.1f}" y="{ly2+4:.1f}" text-anchor="{a}" fill="{colors[i]}" font-size="11">{labels[i]} {model_probs[i]:.1f}%</text>')
        ang += da
    scx, scy, sr = 420, 210, 75
    s_colors = ["#4fc3f7","#ffd93d","#ff6b6b","#555"]; ang = -90
    for i,(label,val) in enumerate(top_scores):
        da = val/100*360
        L.append(pie_slice(scx,scy,sr,ang,ang+da,s_colors[i]))
        if i < 3:
            ma = math.radians(ang+da/2)
            lx = scx+(sr*0.6)*math.cos(ma); ly = scy+(sr*0.6)*math.sin(ma)
            L.append(f'<text x="{lx:.1f}" y="{ly+3:.1f}" text-anchor="middle" fill="#fff" font-size="11" font-weight="bold">{label} {val:.1f}%</text>')
        ang += da
    L.append('<text x="420" y="315" text-anchor="middle" fill="#aaa" font-size="12">高概率比分</text>')
    L.append('</svg>')
    return '\n'.join(L)

OUT = r"I:\阿飞说球\📝文章\20260804\charts"
os.makedirs(OUT, exist_ok=True)

# 场1 奥胡斯 vs 萨巴赫
m1 = dict(
    probs=[29.8,37.2,33.0], odds=[1.57,3.65,4.60],
    home=[50,62,45,50,57,30], away=[67,50,78,50,19,33],
    home_name="奥胡斯", away_name="萨巴赫",
    scores=[("0-0",19.5),("1-0",17.8),("0-1",14.0),("其他",48.7)])
# 场2 费内巴切 vs 格拉茨风暴
m2 = dict(
    probs=[52.7,27.9,19.4], odds=[1.24,5.05,8.0],
    home=[60,75,65,55,71,53], away=[70,55,68,45,11,19],
    home_name="费内巴切", away_name="格拉茨风暴",
    scores=[("1-0",19.4),("2-0",14.6),("0-0",13.0),("其他",53.0)])

for tag, m in [("m1",m1),("m2",m2)]:
    files = {
        f"{tag}_radar.svg": radar_svg(m["home"],m["away"],m["home_name"],m["away_name"]),
        f"{tag}_bar.svg": bar_svg(m["probs"],m["odds"]),
        f"{tag}_pie.svg": pie_svg(m["probs"],m["scores"]),
    }
    for name, content in files.items():
        with open(os.path.join(OUT,name),"w",encoding="utf-8") as f:
            f.write(content)
        print("OK", name, os.path.getsize(os.path.join(OUT,name)))
print("DONE")
