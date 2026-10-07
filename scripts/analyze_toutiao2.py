# -*- coding: utf-8 -*-
"""第二轮：场景/钩子/场次数量/趋势细分的交叉分析"""
import re
from datetime import datetime
from statistics import mean, median

SRC = r"I:\阿飞说球\📚知识库\数据分析\头条号全量表现_20260505-20261007.txt"

rows = []
with open(SRC, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = [x.strip() for x in line.split("|")]
        if len(p) != 12:
            continue
        dt = datetime.strptime(p[0], "%Y-%m-%d %H:%M:%S")
        rows.append(dict(dt=dt, date=dt.strftime("%Y-%m-%d"), hour=dt.hour, title=p[1],
                         imp=int(p[2]), read=int(p[3]), ctr=float(p[4]), comp=float(p[5]),
                         dur=int(p[6]), like=int(p[7]), cmt=int(p[8]), rep=int(p[9]),
                         shr=int(p[10]), fav=int(p[11])))

def show(name, g, base=True):
    if not g:
        print(f"  {name:<22} n=0")
        return
    print(f"  {name:<22} n={len(g):>3}  展现中位 {median(x['imp'] for x in g):>8,.0f}  阅读中位 {median(x['read'] for x in g):>7,.0f}"
          f"  阅读均值 {mean(x['read'] for x in g):>7,.0f}  CTR中位 {median(x['ctr'] for x in g)*100:>5.1f}%"
          f"  完成中位 {median(x['comp'] for x in g):>5.1f}%  时长中位 {median(x['dur'] for x in g):>4.0f}s")

print("=== A. 场次数量（标题里数对阵个数） ===")
def n_matches(t):
    # 用 "vs"/"VS"/"VS" 出现次数 + "、" 连接的对阵
    c = len(re.findall(r"vs|VS|Vs", t))
    if c == 0 and re.search(r"三场|四场|六场", t):
        c = {"三场": 3, "四场": 4, "六场": 6}.get(re.search(r"三场|四场|六场", t).group(), 1)
    return max(c, 1)

for label, lo, hi in [("单场(1个对阵)", 1, 1), ("双场(2个)", 2, 2), ("三场及以上", 3, 99)]:
    g = [r for r in rows if lo <= n_matches(r["title"]) <= hi]
    show(label, g)
show("【全体】", rows)
print()

print("=== B. 标题钩子组合（交叉） ===")
def has_handicap(t): return bool(re.search(r"让球|让一球|让两球|让2球|让1球|让三球|让4球", t))
def has_pack(t): return bool(re.search(r"精选|速览|串烧|合集|双场|双推|三场|四场|六场", t))
def has_num(t): return bool(re.search(r"周[一二三四五六日]\d{3}|^\d+月\d+日\s*\S*\d{3}|\s0\d{2}\s|\d{3}\b", t))
def has_q(t): return ("？" in t) or ("?" in t)
def has_pct(t): return bool(re.search(r"\d+%|\d+个点|千分|百分点|成", t))
def has_h2h(t): return bool(re.search(r"克星|没赢过|不败|魔咒|年|次交手|零封|全败|零胜", t))

combos = [
    ("让球 × 打包", lambda t: has_handicap(t) and has_pack(t)),
    ("让球 × 非打包", lambda t: has_handicap(t) and not has_pack(t)),
    ("打包 × 非让球", lambda t: has_pack(t) and not has_handicap(t)),
    ("纯单场 无让球无打包", lambda t: not has_handicap(t) and not has_pack(t)),
    ("含问号", has_q),
    ("无问号", lambda t: not has_q(t)),
    ("含百分比/点数", has_pct),
    ("无百分比/点数", lambda t: not has_pct(t)),
    ("含克星/魔咒/不败", has_h2h),
    ("无克星/魔咒/不败", lambda t: not has_h2h(t)),
    ("含竞彩编号", has_num),
    ("无竞彩编号", lambda t: not has_num(t)),
]
for name, fn in combos:
    show(name, [r for r in rows if fn(r["title"])])
print()

print("=== C. 赛事类别 × 前中后三期（账号成长） ===")
def period(d):
    if d < "2026-07-01": return "①5-6月"
    if d < "2026-09-01": return "②7-8月"
    return "③9-10月"
cats = {
    "日职/日乙": r"日职|日乙|町田|浦和|横滨|柏太阳神|广岛|鹿岛|清水|冈山|福冈|水户|千叶|川崎|神户|名古屋|钢巴|樱花",
    "韩职/韩K": r"韩职|韩K|首尔|全北|蔚山|浦项|济州|仁川|金泉|富川|光州|大田|江原|安养|水原",
    "瑞超/挪超/芬超": r"瑞超|挪超|芬超|佐加顿斯|天狼星|赫根|哈马比|索尔纳|卡尔马|哥德堡|埃夫斯堡|厄格里特|布鲁马波|米亚尔比|哈尔姆斯|拉赫蒂|瓦萨|博德闪耀|罗森博格|利勒斯特|维京|汉坎|奥勒松|特罗姆瑟|库奥皮奥",
    "五大联赛": r"英超|西甲|意甲|德甲|法甲|英冠|曼联|曼城|利物浦|阿森纳|切尔西|热刺|维拉|皇马|巴萨|马竞|皇社|国米|米兰|尤文|罗马|拜仁|多特|巴黎|朗斯|尼斯|勒沃库森|法兰克福|斯图加特|纽卡|伯恩茅斯|埃弗顿|利兹|西汉姆|水晶宫|桑德兰|奥萨苏纳|贝蒂斯|塞尔塔|巴列卡诺|埃尔切|赫罗纳|拉齐奥|博洛尼亚|那不勒斯|亚特兰大|都灵|萨索洛|科隆|汉堡|赫塔|波鸿|弗赖堡|沃夫斯堡|圣埃蒂安|本菲卡|布拉加|波尔图",
    "世界杯/国际赛/亚运": r"世界杯|国际赛|欧国联|欧洲杯|亚运|预选|热身|友谊|洲际",
    "欧冠/欧联/杯赛": r"欧冠|欧联|欧罗巴|欧协|解放者杯|亚冠|英联|意大利杯|德国杯|法国杯|巴西杯|足总杯|欧超杯",
    "巴甲/南美": r"巴甲|巴乙|巴西|弗拉门戈|圣保罗|科林蒂安|帕梅拉斯|格雷米奥|维多利亚|沙佩科|博塔弗戈|瓦斯科|弗鲁米嫩塞|米拉索尔|布拉干蒂诺|里莫",
}
print(f"  {'类别':<16}{'期':<8}{'n':>4}{'展现中位':>10}{'阅读中位':>9}{'CTR中位':>8}{'完成中位':>9}")
for name, pat in cats.items():
    for per in ["①5-6月", "②7-8月", "③9-10月"]:
        g = [r for r in rows if re.search(pat, r["title"]) and period(r["date"]) == per]
        if not g:
            continue
        print(f"  {name:<16}{per:<8}{len(g):>4}{median(x['imp'] for x in g):>10,.0f}{median(x['read'] for x in g):>9,.0f}"
              f"{median(x['ctr'] for x in g)*100:>8.1f}{median(x['comp'] for x in g):>9.1f}")
    g = [r for r in rows if re.search(pat, r["title"])]
    print(f"  {name:<16}{'合计':<8}{len(g):>4}{median(x['imp'] for x in g):>10,.0f}{median(x['read'] for x in g):>9,.0f}"
          f"{median(x['ctr'] for x in g)*100:>8.1f}{median(x['comp'] for x in g):>9.1f}")
    print()
print()

print("=== D. 半月趋势（展现中位 / 阅读中位 / 篇数） ===")
half = {}
for r in rows:
    y, m, d = r["date"].split("-")
    k = f"{y}-{m}-{'上' if int(d) <= 15 else '下'}"
    half.setdefault(k, []).append(r)
for k in sorted(half):
    g = half[k]
    print(f"  {k:<9} n={len(g):>3}  展现中位 {median(x['imp'] for x in g):>8,.0f}  阅读中位 {median(x['read'] for x in g):>7,.0f}"
          f"  CTR中位 {median(x['ctr'] for x in g)*100:>5.1f}%  完成中位 {median(x['comp'] for x in g):>5.1f}%")
print()

print("=== E. 「高阅读」的门槛拆解：阅读>=1000 的篇目有哪些共同点 ===")
hit = [r for r in rows if r["read"] >= 1000]
miss = [r for r in rows if r["read"] < 300]
print(f"  命中组 n={len(hit)}  均值阅读 {mean(x['read'] for x in hit):,.0f}  展现中位 {median(x['imp'] for x in hit):,.0f}  CTR中位 {median(x['ctr'] for x in hit)*100:.1f}%  完成中位 {median(x['comp'] for x in hit):.1f}%")
print(f"  落空组 n={len(miss)}  均值阅读 {mean(x['read'] for x in miss):,.0f}  展现中位 {median(x['imp'] for x in miss):,.0f}  CTR中位 {median(x['ctr'] for x in miss)*100:.1f}%  完成中位 {median(x['comp'] for x in miss):.1f}%")
for name, fn in [("让球", has_handicap), ("打包/多场", has_pack), ("问号", has_q),
                 ("百分比", has_pct), ("克星/魔咒", has_h2h), ("竞彩编号", has_num)]:
    ph = sum(1 for r in hit if fn(r["title"])) / len(hit) * 100
    pm = sum(1 for r in miss if fn(r["title"])) / len(miss) * 100
    print(f"    特征「{name}」：命中组占比 {ph:>5.1f}%   落空组占比 {pm:>5.1f}%   差 {ph-pm:+.1f}pp")
print()

print("=== F. 完成率高 但 阅读低 = 核心读者 vs 泛读者 ===")
core = [r for r in rows if r["comp"] >= 45]
broad = [r for r in rows if r["comp"] < 20]
print(f"  完成率>=45%（读得完）n={len(core)}  展现中位 {median(x['imp'] for x in core):,.0f}  阅读中位 {median(x['read'] for x in core):,.0f}  时长中位 {median(x['dur'] for x in core):.0f}s  互动率 {median((x['like']+x['cmt']+x['shr']+x['fav'])/max(x['read'],1)*100 for x in core):.2f}%")
print(f"  完成率<20%（读不完）n={len(broad)}  展现中位 {median(x['imp'] for x in broad):,.0f}  阅读中位 {median(x['read'] for x in broad):,.0f}  时长中位 {median(x['dur'] for x in broad):.0f}s  互动率 {median((x['like']+x['cmt']+x['shr']+x['fav'])/max(x['read'],1)*100 for x in broad):.2f}%")
print()
print("  完成率>=45% 的篇目 TOP12（按展现）：")
for r in sorted(core, key=lambda x: -x["imp"])[:12]:
    print(f"    {r['date']} 完成{r['comp']:>5.1f}% 时长{r['dur']:>3}s 展现{r['imp']:>6,} 阅读{r['read']:>5,}  {r['title'][:38]}")
print()

print("=== G. 时长（阅读时长）与阅读量 ===")
for lo, hi in [(0, 40), (40, 60), (60, 80), (80, 100), (100, 999)]:
    g = [r for r in rows if lo <= r["dur"] < hi]
    if g:
        print(f"  时长 {lo:>3}-{hi:>3}s  n={len(g):>3}  展现中位 {median(x['imp'] for x in g):>8,.0f}  阅读中位 {median(x['read'] for x in g):>7,.0f}  完成中位 {median(x['comp'] for x in g):>5.1f}%")
