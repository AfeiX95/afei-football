# -*- coding: utf-8 -*-
"""
Batch #20 赛后校验 - 2026-08-17~19 竞彩13场单固
重点: 卡萨皮亚0:7本菲卡 / 拉科1:1埃尔切 (两场有模型预测记录)
"""
import math

MATCHES = [
    # no, league, home, hcp, away, sp_h, sp_d, sp_a, ht, ft
    dict(no="周一006", league="巴甲", home="巴西国际", hcp="-1", away="里莫", sp_h=1.41, sp_d=3.95, sp_a=6.00, ht="1:0", ft="1:1"),
    dict(no="周一005", league="葡超", home="卡萨皮亚", hcp="+2", away="本菲卡", sp_h=None, sp_d=None, sp_a=None, ht="0:2", ft="0:7"),
    dict(no="周一004", league="西甲", home="拉科", hcp="-1", away="埃尔切", sp_h=1.98, sp_d=2.90, sp_a=3.60, ht="1:0", ft="1:1"),
    dict(no="周一003", league="英冠", home="加的夫城", hcp="-1", away="雷克斯", sp_h=2.37, sp_d=3.14, sp_a=2.57, ht="0:1", ft="1:1"),
    dict(no="周一002", league="瑞超", home="赫根", hcp="-1", away="哈尔姆斯", sp_h=1.22, sp_d=5.40, sp_a=8.05, ht="1:0", ft="1:0"),
    dict(no="周一001", league="芬超", home="赫尔火花", hcp="-1", away="坦山猫", sp_h=2.50, sp_d=3.35, sp_a=2.32, ht="2:2", ft="3:2"),
    dict(no="周日028", league="美职", home="纽约城", hcp="-1", away="费城", sp_h=2.40, sp_d=3.45, sp_a=2.37, ht="2:0", ft="2:3"),
    dict(no="周日027", league="葡超", home="布拉加", hcp="-1", away="吉维森特", sp_h=1.44, sp_d=3.80, sp_a=5.90, ht="无效", ft="无效"),
    dict(no="周日026", league="葡超", home="法马利康", hcp="-1", away="马里迪莫", sp_h=1.56, sp_d=3.52, sp_a=4.90, ht="1:1", ft="1:2"),
    dict(no="周日025", league="巴甲", home="达伽马", hcp="-1", away="桑托斯", sp_h=1.77, sp_d=3.40, sp_a=3.70, ht="0:0", ft="0:3"),
    dict(no="周日024", league="挪超", home="腓特烈", hcp="-1", away="克里斯蒂", sp_h=1.65, sp_d=3.66, sp_a=4.00, ht="1:0", ft="1:0"),
    dict(no="周日023", league="葡超", home="阿罗卡", hcp="-1", away="摩雷伦斯", sp_h=1.85, sp_d=3.00, sp_a=3.92, ht="3:0", ft="4:0"),
    dict(no="周日022", league="西甲", home="西班牙人", hcp="-1", away="莱万特", sp_h=1.97, sp_d=2.94, sp_a=3.55, ht="2:0", ft="3:0"),
]

def implied(h, d, a):
    inv = [1/h, 1/d, 1/a]
    s = sum(inv)
    return [x/s for x in inv]

def actual_dir(ft):
    h, a = map(int, ft.split(":"))
    return "H" if h > a else ("D" if h == a else "A")

def c15_trigger(sp_h, hcp):
    """C15分档: <1.50让-1 = C15a; 1.50-2.00让-1 = C15b"""
    if sp_h is None or hcp != "-1":
        return None
    if sp_h < 1.50:
        return "C15a(<1.50)"
    if sp_h < 2.00:
        return "C15b(1.50-2.00)"
    return None

print("=" * 78)
print("Batch #20 赛后校验 | 2026-08-17~19 竞彩13场单固")
print("=" * 78)

print("\n## 一、全部13场：市场 vs 实际")
print("| 编号 | 联赛 | 对阵(让球) | SP | 市场隐含(H/D/A) | 市场方向 | 实际 | 命中 | 规则 |")
print("|:----|:-----|:----------|:---|:---------------|:--------|:----|:----:|:-----|")
hit = 0; total = 0
for m in MATCHES:
    if m["ft"] == "无效":
        print(f"| {m['no']} | {m['league']} | {m['home']}({m['hcp']})vs{m['away']} | {m['sp_h']}/{m['sp_d']}/{m['sp_a']} | 无效场次 | — | 无效 | — | — |")
        continue
    h, d, a = m["sp_h"], m["sp_d"], m["sp_a"]
    if h is None:
        print(f"| {m['no']} | {m['league']} | {m['home']}({m['hcp']})vs{m['away']} | 无SP | — | — | {m['ft']} | — | — |")
        continue
    probs = implied(h, d, a)
    mdir = "H" if probs[0] >= probs[1] and probs[0] >= probs[2] else ("D" if probs[1] >= probs[2] else "A")
    ad = actual_dir(m["ft"])
    is_hit = "✅" if mdir == ad else "❌"
    if mdir == ad: hit += 1
    total += 1
    mdir_cn = {"H": "主胜", "D": "平", "A": "客胜"}[mdir]
    c15 = c15_trigger(h, m["hcp"])
    trig = c15 if c15 else "-"
    print(f"| {m['no']} | {m['league']} | {m['home']}({m['hcp']})vs{m['away']} | {h}/{d}/{a} | {probs[0]*100:.1f}%/{probs[1]*100:.1f}%/{probs[2]*100:.1f}% | {mdir_cn} | {m['ft']} | {is_hit} | {trig} |")
print(f"\n**市场方向命中率: {hit}/{total} = {hit/total*100:.1f}%**")

print("\n## 二、让球验证")
print("| 编号 | 对阵 | 全场 | 让球后 | 结果 |")
print("|:----|:----|:----|:------|:----|")
for m in MATCHES:
    if m["ft"] == "无效": continue
    hcp = int(m["hcp"])
    fh, fa = map(int, m["ft"].split(":"))
    adj = fh + hcp
    res = "让球方胜" if adj > fa else ("让球平" if adj == fa else "让球方负")
    print(f"| {m['no']} | {m['home']}({m['hcp']})vs{m['away']} | {m['ft']} | {adj}-{fa} | {res} |")

print("\n## 三、C15 分档验证（让-1场次）")
print("| 编号 | 对阵 | SP | 分档 | 实际 | C15判定 |")
print("|:----|:----|:---|:----|:----|:-------|")
for m in MATCHES:
    c15 = c15_trigger(m["sp_h"], m["hcp"])
    if c15:
        fh, fa = map(int, m["ft"].split(":"))
        verdict = "✅翻车(主未胜)" if fh <= fa else "❌未翻车"
        print(f"| {m['no']} | {m['home']}({m['hcp']})vs{m['away']} | {m['sp_h']} | {c15} | {m['ft']} | {verdict} |")
