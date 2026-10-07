# -*- coding: utf-8 -*-
"""头条号全量内容表现分析（只读数据文件，不改任何东西）"""
import re
from datetime import datetime
from statistics import mean, median

SRC = r"I:\阿飞说球\📚知识库\数据分析\头条号全量表现_20260505-20261007.txt"

rows = []
with open(SRC, encoding="utf-8") as f:
    for ln, line in enumerate(f, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = [x.strip() for x in line.split("|")]
        if len(p) != 12:
            print(f"!! 第{ln}行字段数 {len(p)}：{line[:60]}")
            continue
        try:
            dt = datetime.strptime(p[0], "%Y-%m-%d %H:%M:%S")
            r = dict(dt=dt, date=dt.strftime("%Y-%m-%d"), hour=dt.hour,
                     title=p[1], imp=int(p[2]), read=int(p[3]),
                     ctr=float(p[4]), comp=float(p[5]), dur=int(p[6]),
                     like=int(p[7]), cmt=int(p[8]), rep=int(p[9]),
                     shr=int(p[10]), fav=int(p[11]))
        except ValueError as e:
            print(f"!! 第{ln}行解析失败 {e}：{line[:60]}")
            continue
        r["real_ctr"] = (r["read"] / r["imp"] * 100) if r["imp"] else 0.0
        r["inter"] = r["like"] + r["cmt"] + r["rep"] + r["shr"] + r["fav"]
        r["inter_rate"] = (r["inter"] / r["read"] * 100) if r["read"] else 0.0
        rows.append(r)

n = len(rows)
print(f"=== 样本 {n} 篇，{rows[-1]['date']} ~ {rows[0]['date']} ===")
print()

# ---------- 1. 月度 ----------
print("=== 1. 按月 ===")
print(f"{'月份':<9}{'篇数':>4}{'展现合计':>10}{'展现中位':>10}{'阅读合计':>10}{'阅读中位':>10}{'CTR中位%':>10}{'完成率中位':>10}")
months = {}
for r in rows:
    months.setdefault(r["date"][:7], []).append(r)
for m in sorted(months):
    g = months[m]
    print(f"{m:<9}{len(g):>4}{sum(x['imp'] for x in g):>10,}{median(x['imp'] for x in g):>10,.0f}"
          f"{sum(x['read'] for x in g):>10,}{median(x['read'] for x in g):>10,.0f}"
          f"{median(x['ctr'] for x in g)*100:>10.1f}{median(x['comp'] for x in g):>10.1f}")
print()

# ---------- 2. 头部 ----------
print("=== 2. 展现量 TOP15 ===")
for r in sorted(rows, key=lambda x: -x["imp"])[:15]:
    print(f"  {r['date']} 展现{r['imp']:>7,} 阅读{r['read']:>6,} CTR{r['ctr']*100:>4.0f}% 完成{r['comp']:>5.1f}% "
          f"时长{r['dur']:>3}s 互动{r['inter']:>3}  {r['title'][:38]}")
print()
print("=== 3. 阅读量 TOP15 ===")
for r in sorted(rows, key=lambda x: -x["read"])[:15]:
    print(f"  {r['date']} 阅读{r['read']:>6,} 展现{r['imp']:>7,} CTR{r['ctr']*100:>4.0f}% 完成{r['comp']:>5.1f}% "
          f"互动{r['inter']:>3}  {r['title'][:38]}")
print()

# ---------- 4. 高展现低转化 ----------
print("=== 4. 高展现(>=8000) 但 CTR<=4% 的浪费展现 TOP12 ===")
waste = [r for r in rows if r["imp"] >= 8000 and r["ctr"] <= 0.04]
for r in sorted(waste, key=lambda x: -x["imp"])[:12]:
    print(f"  {r['date']} 展现{r['imp']:>7,} 只读到{r['read']:>5,} CTR{r['ctr']*100:>4.0f}% 完成{r['comp']:>5.1f}%  {r['title'][:40]}")
print(f"  合计 {len(waste)} 篇，浪费展现 {sum(x['imp'] for x in waste):,}")
print()

# ---------- 5. 标题特征 ----------
print("=== 5. 标题特征对比（中位数） ===")
def feat(r):
    t = r["title"]
    return {
        "含竞彩编号": bool(re.search(r"周[一二三四五六日]\d{3}|00[1-9]|0[1-9]\d", t)),
        "含问号": "？" in t or "?" in t,
        "含对阵vs": ("vs" in t.lower()) or ("VS" in t),
        "含地名日期开头": bool(re.match(r"^\d+月\d+日|^\d{1,2}-\d{1,2}", t)),
        "含精选/速览/串烧": bool(re.search(r"精选|速览|串烧|合集|三场|四场|双场|双推", t)),
        "含让球/让一球": bool(re.search(r"让球|让一球|让两球|让2球|让1球|让三球|让4球", t)),
        "标题<=20字": len(t) <= 20,
        "标题21-30字": 21 <= len(t) <= 30,
        "标题>30字": len(t) > 30,
    }

keys = list(feat(rows[0]).keys())
for k in keys:
    g = [r for r in rows if feat(r)[k]]
    if not g:
        continue
    print(f"  {k:<16} n={len(g):>3}  展现中位 {median(x['imp'] for x in g):>8,.0f}  阅读中位 {median(x['read'] for x in g):>7,.0f}  "
          f"CTR中位 {median(x['ctr'] for x in g)*100:>5.1f}%  完成中位 {median(x['comp'] for x in g):>5.1f}%")
print(f"  {'【全体基准】':<16} n={n:>3}  展现中位 {median(x['imp'] for x in rows):>8,.0f}  阅读中位 {median(x['read'] for x in rows):>7,.0f}  "
      f"CTR中位 {median(x['ctr'] for x in rows)*100:>5.1f}%  完成中位 {median(x['comp'] for x in rows):>5.1f}%")
print()

# ---------- 6. 联赛/赛事 ----------
print("=== 6. 赛事类别（按标题关键词，中位数） ===")
leagues = {
    "日职/日乙": r"日职|日乙|町田|浦和|横滨|柏太阳神|广岛|鹿岛|清水|冈山|福冈|水户|千叶|川崎|神户|名古屋|钢巴|樱花|东京",
    "韩职/韩K": r"韩职|韩K|首尔|全北|蔚山|浦项|济州|仁川|金泉|富川|光州|大田|江原|安养",
    "瑞超": r"瑞超|佐加顿斯|天狼星|赫根|哈马比|索尔纳|卡尔马|哥德堡|埃夫斯堡|厄格里特|布鲁马波|米亚尔比|哈尔姆斯|瓦萨|拉赫蒂",
    "挪超": r"挪超|博德闪耀|罗森博格|利勒斯特|维京|汉坎|奥勒松|特罗姆瑟|斯达|萨普斯堡",
    "五大联赛": r"英超|西甲|意甲|德甲|法甲|曼联|曼城|利物浦|阿森纳|切尔西|热刺|维拉|皇马|巴萨|马竞|皇社|国米|米兰|尤文|罗马|拜仁|多特|巴黎|朗斯|尼斯|勒沃库森|法兰克福|斯图加特|纽卡|伯恩茅斯|埃弗顿|利兹|西汉姆|水晶宫|桑德兰|奥萨苏纳|贝蒂斯|塞尔塔|巴列卡诺|埃尔切|赫罗纳|拉齐奥|博洛尼亚|那不勒斯|亚特兰大|都灵|萨索洛|科隆|汉堡|赫塔|波鸿|弗赖堡",
    "世界杯/国际赛": r"世界杯|国际赛|欧国联|欧洲杯|亚运|预选|热身|友谊",
    "欧冠/欧联/欧协": r"欧冠|欧联|欧罗巴|欧协|解放者杯|亚冠|英联杯|意大利杯|德国杯|法国杯|巴西杯|足总杯",
    "巴甲/南美": r"巴甲|巴乙|巴西|弗拉门戈|圣保罗|科林蒂安|帕梅拉斯|格雷米奥|维多利亚|沙佩科|博塔弗戈|瓦斯科|弗鲁米嫩塞|米拉索尔|布拉干蒂诺|里莫|库奥皮奥|佐加",
    "美职/其他": r"美职|奥克兰|悉尼",
}
seen = set()
for name, pat in leagues.items():
    g = [r for r in rows if re.search(pat, r["title"]) and id(r) not in seen]
    for r in g:
        seen.add(id(r))
    if g:
        print(f"  {name:<14} n={len(g):>3}  展现中位 {median(x['imp'] for x in g):>8,.0f}  阅读中位 {median(x['read'] for x in g):>7,.0f}  "
              f"CTR中位 {median(x['ctr'] for x in g)*100:>5.1f}%  完成中位 {median(x['comp'] for x in g):>5.1f}%")
print()

# ---------- 7. 发布时间 ----------
print("=== 7. 按发布小时 ===")
hours = {}
for r in rows:
    hours.setdefault(r["hour"], []).append(r)
for h in sorted(hours):
    g = hours[h]
    print(f"  {h:>2}点  n={len(g):>3}  展现中位 {median(x['imp'] for x in g):>8,.0f}  阅读中位 {median(x['read'] for x in g):>7,.0f}  "
          f"CTR中位 {median(x['ctr'] for x in g)*100:>5.1f}%  完成中位 {median(x['comp'] for x in g):>5.1f}%")
print()

# ---------- 8. 互动 & 完成率 ----------
print("=== 8. 完成率与时长关系（按完成率分档） ===")
buckets = [(0, 15), (15, 25), (25, 40), (40, 60), (60, 101)]
for lo, hi in buckets:
    g = [r for r in rows if lo <= r["comp"] < hi]
    if not g:
        continue
    print(f"  完成率 {lo:>3}-{hi:>3}%  n={len(g):>3}  时长中位 {median(x['dur'] for x in g):>5.0f}s  "
          f"展现中位 {median(x['imp'] for x in g):>8,.0f}  阅读中位 {median(x['read'] for x in g):>7,.0f}  "
          f"互动率中位 {median(x['inter_rate'] for x in g):>5.2f}%")
print()

print("=== 9. 互动（赞+评+转+享+藏）TOP12 ===")
for r in sorted(rows, key=lambda x: -x["inter"])[:12]:
    print(f"  {r['date']} 互动{r['inter']:>4} (赞{r['like']} 评{r['cmt']} 转{r['rep']} 享{r['shr']} 藏{r['fav']}) "
          f"阅读{r['read']:>6,} 互动率{r['inter_rate']:>5.2f}%  {r['title'][:34]}")
print()

# ---------- 10. 相关 ----------
print("=== 10. 相关与比值 ===")
imp_s = [r["imp"] for r in rows]
read_s = [r["read"] for r in rows]
comp_s = [r["comp"] for r in rows]
dur_s = [r["dur"] for r in rows]

def pearson(a, b):
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else 0.0

import math
def spearman(a, b):
    def rank(v):
        idx = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(idx):
            j = i
            while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                rk[idx[k]] = avg
            i = j + 1
        return rk
    return pearson(rank(a), rank(b))

print(f"  展现 ↔ 阅读      Pearson {pearson(imp_s, read_s):+.3f}   Spearman {spearman(imp_s, read_s):+.3f}")
print(f"  展现 ↔ 完成率    Pearson {pearson(imp_s, comp_s):+.3f}   Spearman {spearman(imp_s, comp_s):+.3f}")
print(f"  完成率 ↔ 时长    Pearson {pearson(comp_s, dur_s):+.3f}   Spearman {spearman(comp_s, dur_s):+.3f}")
print(f"  展现 ↔ 互动      Pearson {pearson(imp_s, [r['inter'] for r in rows]):+.3f}")
print(f"  阅读 ↔ 互动      Pearson {pearson(read_s, [r['inter'] for r in rows]):+.3f}")
print(f"  全期合计：展现 {sum(imp_s):,}  阅读 {sum(read_s):,}  总CTR {sum(read_s)/sum(imp_s)*100:.2f}%")
print(f"  单篇平均：展现 {mean(imp_s):,.0f}  阅读 {mean(read_s):,.0f}  时长 {mean(dur_s):.0f}s  完成率 {mean(comp_s):.1f}%")
print(f"  中位数  ：展现 {median(imp_s):,.0f}  阅读 {median(read_s):,.0f}  时长 {median(dur_s):.0f}s  完成率 {median(comp_s):.1f}%")
print()

# ---------- 11. 头部集中度 ----------
print("=== 11. 阅读量集中度 ===")
sr = sorted(read_s, reverse=True)
tot = sum(sr)
for k in (1, 3, 5, 10, 20, 30):
    print(f"  TOP{k:>2} 篇贡献 {sum(sr[:k]):>7,} 阅读 = 全期 {sum(sr[:k])/tot*100:>5.1f}%")
print(f"  尾部：阅读<=100 的 {sum(1 for x in read_s if x <= 100)} 篇，合计 {sum(x for x in read_s if x <= 100):,} 阅读")
print(f"        阅读<=300 的 {sum(1 for x in read_s if x <= 300)} 篇，合计 {sum(x for x in read_s if x <= 300):,} 阅读")
print()

# ---------- 12. 连续爆发（前一篇是否影响后一篇） ----------
print("=== 12. 展现量「惯性」检验：前一篇展现 vs 本篇展现 ===")
ch = sorted(rows, key=lambda x: x["dt"])
pairs = [(ch[i - 1]["imp"], ch[i]["imp"]) for i in range(1, len(ch))]
print(f"  相邻篇展现 Pearson {pearson([p[0] for p in pairs], [p[1] for p in pairs]):+.3f}  "
      f"Spearman {spearman([p[0] for p in pairs], [p[1] for p in pairs]):+.3f}")
big = [ch[i] for i in range(1, len(ch)) if ch[i - 1]["imp"] >= 20000]
print(f"  前一篇展现>=2万的共 {len(big)} 次，其后一篇展现中位 {median(x['imp'] for x in big):,.0f}"
      f"（全体中位 {median(imp_s):,.0f}）" if big else "  前一篇展现>=2万：无")
print()

# ---------- 13. 近期窗口（2026-08 起） ----------
recent = [r for r in rows if r["date"] >= "2026-08-01"]
print(f"=== 13. 近期窗口 2026-08-01 起（{len(recent)} 篇） ===")
print(f"  展现中位 {median(x['imp'] for x in recent):,.0f}  阅读中位 {median(x['read'] for x in recent):,.0f}  "
      f"CTR中位 {median(x['ctr'] for x in recent)*100:.1f}%  完成中位 {median(x['comp'] for x in recent):.1f}%")
for r in sorted(recent, key=lambda x: -x["read"])[:10]:
    print(f"    {r['date']} 阅读{r['read']:>5,} 展现{r['imp']:>7,} CTR{r['ctr']*100:>4.0f}%  {r['title'][:40]}")
print()
print("  近期最差 10 篇（按阅读）：")
for r in sorted(recent, key=lambda x: x["read"])[:10]:
    print(f"    {r['date']} 阅读{r['read']:>5,} 展现{r['imp']:>7,} CTR{r['ctr']*100:>4.0f}% 完成{r['comp']:>5.1f}%  {r['title'][:40]}")
