# -*- coding: utf-8 -*-
"""第三轮：控制时间混杂——把「让球/打包/问号」放进同一时间窗内再比"""
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

hand = lambda t: bool(re.search(r"让球|让一球|让两球|让2球|让1球|让三球|让4球|让步", t))
pack = lambda t: bool(re.search(r"精选|速览|串烧|合集|双场|双推|三场|四场|六场|两场|四场", t))
ques = lambda t: ("？" in t) or ("?" in t)

def blk(name, g):
    if len(g) < 3:
        print(f"  {name:<26} n={len(g):>3}  （样本太小）")
        return
    print(f"  {name:<26} n={len(g):>3}  展现中位 {median(x['imp'] for x in g):>8,.0f}  阅读中位 {median(x['read'] for x in g):>7,.0f}"
          f"  阅读均值 {mean(x['read'] for x in g):>7,.0f}  CTR中位 {median(x['ctr'] for x in g)*100:>5.1f}%")

windows = [("全期 05-05~10-06", "2026-05-01"), ("2026-07 起", "2026-07-01"),
           ("2026-08 起", "2026-08-01"), ("2026-09 起", "2026-09-01")]
for wname, start in windows:
    W = [r for r in rows if r["date"] >= start]
    print(f"=== 窗口 {wname}（n={len(W)}） ===")
    blk("窗口全体", W)
    blk("含「让球/让步」", [r for r in W if hand(r["title"])])
    blk("不含让球", [r for r in W if not hand(r["title"])])
    blk("含「打包/多场」", [r for r in W if pack(r["title"])])
    blk("不含打包", [r for r in W if not pack(r["title"])])
    blk("含问号", [r for r in W if ques(r["title"])])
    blk("不含问号", [r for r in W if not ques(r["title"])])
    print()

print("=== 近窗（2026-08 起）赛事类别对照 ===")
cats = {
    "日职/日乙": r"日职|日乙|町田|浦和|横滨|柏太阳神|广岛|鹿岛|清水|冈山|福冈|水户|千叶|川崎|神户|名古屋|钢巴|樱花",
    "韩职/韩K": r"韩职|韩K|首尔|全北|蔚山|浦项|济州|仁川|金泉|富川|光州|大田|江原|安养|水原",
    "瑞/挪/芬超": r"瑞超|挪超|芬超|佐加顿斯|天狼星|赫根|哈马比|索尔纳|卡尔马|哥德堡|埃夫斯堡|厄格里特|布鲁马波|米亚尔比|哈尔姆斯|拉赫蒂|瓦萨|博德闪耀|罗森博格|利勒斯特|维京|汉坎|奥勒松|特罗姆瑟|库奥皮奥",
    "五大联赛": r"英超|西甲|意甲|德甲|法甲|英冠|曼联|曼城|利物浦|阿森纳|切尔西|热刺|维拉|皇马|巴萨|马竞|皇社|国米|米兰|尤文|罗马|拜仁|多特|巴黎|朗斯|尼斯|勒沃库森|法兰克福|斯图加特|纽卡|伯恩茅斯|埃弗顿|利兹|西汉姆|水晶宫|桑德兰|奥萨苏纳|贝蒂斯|塞尔塔|巴列卡诺|埃尔切|赫罗纳|拉齐奥|博洛尼亚|那不勒斯|亚特兰大|都灵|萨索洛|科隆|汉堡|赫塔|波鸿|弗赖堡|沃夫斯堡|圣埃蒂安|本菲卡|布拉加|波尔图",
    "国际/亚运": r"世界杯|国际赛|欧国联|欧洲杯|亚运|预选|热身|友谊|洲际",
    "欧冠/欧联/各类杯": r"欧冠|欧联|欧罗巴|欧协|解放者杯|亚冠|英联|意大利杯|德国杯|法国杯|巴西杯|足总杯|欧超杯",
    "巴甲/南美": r"巴甲|巴乙|巴西|弗拉门戈|圣保罗|科林蒂安|帕梅拉斯|格雷米奥|维多利亚|沙佩科|博塔弗戈|瓦斯科|弗鲁米嫩塞|米拉索尔|布拉干蒂诺|里莫",
}
W8 = [r for r in rows if r["date"] >= "2026-08-01"]
for name, pat in cats.items():
    blk(name, [r for r in W8 if re.search(pat, r["title"])])
blk("【近窗全体】", W8)
print()

print("=== 日职/韩职 全部篇目（全期） ===")
for r in sorted([r for r in rows if re.search(cats["日职/日乙"] + "|" + cats["韩职/韩K"], r["title"])], key=lambda x: x["dt"]):
    print(f"  {r['date']} 展现{r['imp']:>7,} 阅读{r['read']:>6,} CTR{r['ctr']*100:>4.0f}% 完成{r['comp']:>5.1f}%  {r['title'][:48]}")
print()

print("=== 五大联赛 近窗（2026-08 起）全部篇目 ===")
for r in sorted([r for r in W8 if re.search(cats["五大联赛"], r["title"])], key=lambda x: x["dt"]):
    print(f"  {r['date']} 展现{r['imp']:>7,} 阅读{r['read']:>6,} CTR{r['ctr']*100:>4.0f}% 完成{r['comp']:>5.1f}%  {r['title'][:48]}")
