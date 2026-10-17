# -*- coding: utf-8 -*-
"""
市场 vs 模型 vs 实际 三方对比分析 (2026-08-14~16 竞彩赛果)
数据源: 竞彩网足球赛果开奖页 (用户粘贴)
模型侧: v2.7.1 修正规则库 C01-C23 规则视角判断
"""
import json

# 数据: 编号, 联赛, 主队, 让球(主队视角), 客队, SP主, SP平, SP客, 半场比分, 全场比分, 状态
# 让球: -1 表示主队让1球(主队(+/-)), +1 表示主队受让1球
MATCHES = [
    # --- 待开奖 (5场) ---
    dict(no="周六013", league="葡超", home="阿尔维卡", hcp="-1", away="阿马多拉", sp_h=2.00, sp_d=2.92, sp_a=3.50, ht=None, ft=None, status="待开奖"),
    dict(no="周六012", league="荷甲", home="威廉二世", hcp="+1", away="奈梅亨", sp_h=4.70, sp_d=4.15, sp_a=1.48, ht=None, ft=None, status="待开奖"),
    dict(no="周六011", league="挪超", home="奥斯KFUM", hcp="+1", away="利勒斯特", sp_h=3.20, sp_d=3.60, sp_a=1.86, ht=None, ft=None, status="待开奖"),
    dict(no="周六010", league="英冠", home="诺维奇", hcp="-1", away="西布罗姆", sp_h=1.87, sp_d=3.25, sp_a=3.48, ht=None, ft=None, status="待开奖"),
    dict(no="周六009", league="瑞超", home="米亚尔比", hcp="+1", away="天狼星", sp_h=2.88, sp_d=3.40, sp_a=2.05, ht=None, ft=None, status="待开奖"),
    # --- 已完成 (25场) ---
    dict(no="周六008", league="英冠", home="博尔顿", hcp="-1", away="普雷斯顿", sp_h=2.15, sp_d=3.08, sp_a=2.95, ht="2:0", ft="2:1", status="已完成"),
    dict(no="周六007", league="德乙", home="柏林赫塔", hcp="-1", away="海登海姆", sp_h=2.40, sp_d=3.40, sp_a=2.40, ht="3:0", ft="4:1", status="已完成"),
    dict(no="周六006", league="韩职", home="光州FC", hcp="+1", away="浦项制铁", sp_h=3.32, sp_d=2.90, sp_a=2.07, ht="0:1", ft="1:2", status="已完成"),
    dict(no="周六005", league="韩职", home="首尔FC", hcp="-1", away="大田市民", sp_h=2.04, sp_d=3.25, sp_a=3.02, ht="0:1", ft="4:2", status="已完成"),
    dict(no="周六004", league="日职", home="神户胜利", hcp="-1", away="东京FC", sp_h=2.03, sp_d=3.12, sp_a=3.16, ht="1:1", ft="2:2", status="已完成"),
    dict(no="周六003", league="日职", home="浦和红钻", hcp="+1", away="广岛三箭", sp_h=3.60, sp_d=3.35, sp_a=1.81, ht="1:2", ft="1:4", status="已完成"),
    dict(no="周六002", league="日乙", home="秋田闪电", hcp="+1", away="富山胜利", sp_h=2.85, sp_d=2.85, sp_a=2.34, ht="0:2", ft="0:4", status="已完成"),
    dict(no="周六001", league="日职", home="鹿岛鹿角", hcp="-1", away="名古屋鲸", sp_h=1.73, sp_d=3.38, sp_a=3.92, ht="1:0", ft="2:1", status="已完成"),
    dict(no="周五017", league="葡超", home="里斯本", hcp="-2", away="吉马良斯", sp_h=1.19, sp_d=5.30, sp_a=10.00, ht="3:0", ft="3:2", status="已完成"),
    dict(no="周五016", league="英冠", home="伍尔弗", hcp="-1", away="布莱克本", sp_h=1.38, sp_d=4.05, sp_a=6.35, ht="1:1", ft="2:2", status="已完成"),
    dict(no="周五015", league="法乙", home="圣埃蒂安", hcp="-1", away="克莱蒙", sp_h=1.33, sp_d=4.40, sp_a=6.70, ht="1:0", ft="3:1", status="已完成"),
    dict(no="周五014", league="法乙", home="兰斯", hcp="-1", away="敦刻尔克", sp_h=1.68, sp_d=3.40, sp_a=4.20, ht="1:1", ft="3:3", status="已完成"),
    dict(no="周五013", league="法乙", home="阿纳西", hcp="-1", away="罗德兹", sp_h=2.16, sp_d=3.05, sp_a=2.95, ht="1:0", ft="2:0", status="已完成"),
    dict(no="周五012", league="荷乙", home="赫拉克勒", hcp="-1", away="登博思", sp_h=1.46, sp_d=4.30, sp_a=4.71, ht="1:0", ft="3:2", status="已完成"),
    dict(no="周五011", league="荷乙", home="瓦尔韦克", hcp="-1", away="多德勒支", sp_h=1.74, sp_d=3.50, sp_a=3.72, ht="0:1", ft="2:2", status="已完成"),
    dict(no="周五010", league="荷甲", home="特尔斯达", hcp="-1", away="鹿斯巴达", sp_h=1.96, sp_d=3.60, sp_a=2.94, ht="0:1", ft="1:3", status="已完成"),
    dict(no="周五009", league="沙职", home="利雅新月", hcp="-3", away="哈马费萨", sp_h=None, sp_d=None, sp_a=None, ht="3:0", ft="4:2", status="已完成"),
    dict(no="周五008", league="沙职", home="达曼协定", hcp="-1", away="利雅得", sp_h=1.90, sp_d=3.35, sp_a=3.28, ht="1:1", ft="4:2", status="已完成"),
    dict(no="周五007", league="挪超", home="罗森博格", hcp="+1", away="维京", sp_h=2.28, sp_d=3.60, sp_a=2.42, ht="1:0", ft="2:1", status="已完成"),
    dict(no="周五006", league="瑞超", home="埃夫斯堡", hcp="-1", away="韦斯特罗", sp_h=1.57, sp_d=3.60, sp_a=4.65, ht="1:0", ft="3:0", status="已完成"),
    dict(no="周五005", league="沙职", home="新未来SC", hcp="-1", away="迈季宽广", sp_h=1.53, sp_d=3.75, sp_a=4.80, ht="2:0", ft="2:1", status="已完成"),
    dict(no="周五004", league="德乙", home="不伦瑞克", hcp="-1", away="波鸿", sp_h=2.18, sp_d=3.20, sp_a=2.80, ht="0:1", ft="0:1", status="已完成"),
    dict(no="周五003", league="德乙", home="基尔", hcp="-1", away="圣保利", sp_h=2.38, sp_d=3.23, sp_a=2.50, ht="0:2", ft="2:2", status="已完成"),
    dict(no="周五002", league="芬超", home="瓦萨", hcp="-1", away="TPS图尔", sp_h=1.61, sp_d=3.65, sp_a=4.30, ht="0:2", ft="1:3", status="已完成"),
    dict(no="周五001", league="日职", home="东京绿茵", hcp="+1", away="柏太阳神", sp_h=4.10, sp_d=3.15, sp_a=1.76, ht="1:1", ft="1:3", status="已完成"),
]


def implied_prob(h, d, a):
    """市场隐含概率(去水): 1/odds 归一化"""
    inv = [1.0 / h, 1.0 / d, 1.0 / a]
    s = sum(inv)
    return [x / s for x in inv], s


def fmt_pct(x):
    return f"{x*100:.1f}%"


def actual_ft(ft):
    """全场比分 -> (主胜/平/客胜) 方向"""
    if ft is None:
        return None
    h, a = map(int, ft.split(":"))
    if h > a:
        return "H"
    if h == a:
        return "D"
    return "A"


def rule_trigger(m):
    """基于 SP 结构与让球的规则触发标注 (v2.7.1 规则库视角)"""
    triggers = []
    h, d, a = m["sp_h"], m["sp_d"], m["sp_a"]
    hcp = m["hcp"]
    if h is None:
        return ["无SP(未开售单关)"]
    # C21 超低赔大热让-1恢复信任: 主队定价<1.30 + 让-1
    if h < 1.30 and hcp == "-1":
        triggers.append("C21超低赔大热让-1(恢复信任,市场±5pp)")
    # C22 平局上浮遇超低赔封顶: 市场主胜<1.60
    if h < 1.60:
        triggers.append("C22平局封顶(主胜<1.60)")
    # C15 大热主队让-1冷门陷阱: 主队赔率<1.50 + 让-1 (需客队近3场不败数据,此处按定价近似)
    if h < 1.50 and hcp == "-1":
        triggers.append("C15大热主队让-1(陷阱预警)")
    # C06/C11 低赔修正
    if h < 1.40:
        triggers.append("C06低赔主胜-3~5pp")
    if a < 1.40:
        triggers.append("C11低赔客胜-3~5pp")
    # C09/C12 让球-1方概率下调
    if hcp == "-1":
        triggers.append("C09/C12让球-1方-12~15pp")
    if hcp == "-2":
        triggers.append("让-2深盘(里斯本式大热)")
    if hcp == "-3":
        triggers.append("让-3极端深盘")
    # C16 强强对话平局上浮: 赔率差<0.5
    if h and a and abs(h - a) < 0.5:
        triggers.append("C16强强对话(平局+8~12pp)")
    # C14 平局基础上浮 (全赛事通用)
    triggers.append("C14平局基础上浮")
    return triggers


def main():
    rows = []
    for m in MATCHES:
        h, d, a = m["sp_h"], m["sp_d"], m["sp_a"]
        probs = None
        if h is not None:
            probs, margin = implied_prob(h, d, a)
        trig = rule_trigger(m)
        actual = actual_ft(m["ft"])
        row = {
            "no": m["no"], "league": m["league"], "home": m["home"], "hcp": m["hcp"],
            "away": m["away"], "sp": f"{h}/{d}/{a}", "status": m["status"],
            "ft": m["ft"], "ht": m["ht"],
            "probs": probs, "triggers": trig, "actual": actual,
        }
        rows.append(row)

    # 输出表格 (Markdown)
    out = []
    out.append("# 市场 vs 模型 vs 实际 三方对比 (2026-08-14~16 竞彩)\n")
    out.append("> 模型侧: v2.7.1 规则库 C01-C23 视角 | 数据: 竞彩网赛果开奖页 | 共30场(总40场,缺第二页10场)\n")
    out.append("## 市场隐含概率去水口径: p = (1/odds) / Σ(1/odds)\n")

    # 已完成
    done = [r for r in rows if r["status"] == "已完成"]
    out.append(f"\n## 一、已完成 {len(done)} 场 — 市场 vs 实际\n")
    out.append("| 编号 | 联赛 | 对阵(让球) | SP(胜/平/负) | 市场隐含(H/D/A) | 市场方向 | 实际 | 命中 | 规则触发 |")
    out.append("|:----|:-----|:----------|:------------|:---------------|:--------|:----|:----:|:---------|")
    market_hit = 0
    market_total = 0
    for r in done:
        if r["probs"] is None:
            out.append(
                f"| {r['no']} | {r['league']} | {r['home']}({r['hcp']})vs{r['away']} | {r['sp']} | 无SP | — | {r['ft']} | — | {'; '.join(r['triggers'])} |"
            )
            continue
        market_total += 1
        h, d, a = r["probs"]
        mdir = "H" if h >= d and h >= a else ("D" if d >= h and d >= a else "A")
        mdir_cn = {"H": "主胜", "D": "平", "A": "客胜"}[mdir]
        hit = "✅" if mdir == r["actual"] else "❌"
        if mdir == r["actual"]:
            market_hit += 1
        out.append(
            f"| {r['no']} | {r['league']} | {r['home']}({r['hcp']})vs{r['away']} | {r['sp']} | "
            f"{fmt_pct(h)}/{fmt_pct(d)}/{fmt_pct(a)} | {mdir_cn} | {r['ft']} | {hit} | {'; '.join(r['triggers'])} |"
        )
    out.append(f"\n**市场方向命中率: {market_hit}/{market_total} = {market_hit/market_total*100:.1f}%** (有效SP场次)\n")

    # 让球结果验证
    out.append("\n## 二、让球验证 (让球胜平负视角)\n")
    out.append("| 编号 | 对阵(让球) | 全场 | 让球后结果 | 让球方向判断 |")
    out.append("|:----|:----------|:----|:----------|:------------|")
    for r in done:
        hcp = int(r["hcp"]) if r["hcp"] else 0
        fh, fa = map(int, r["ft"].split(":"))
        adj_h = fh + hcp
        if adj_h > fa:
            hcp_res = "让球方胜"
        elif adj_h == fa:
            hcp_res = "让球平"
        else:
            hcp_res = "让球方负"
        out.append(f"| {r['no']} | {r['home']}({r['hcp']})vs{r['away']} | {r['ft']} | {hcp_res} | 让{abs(hcp)}后{adj_h}-{fa} |")

    # 待开奖
    pending = [r for r in rows if r["status"] == "待开奖"]
    out.append(f"\n## 三、待开奖 {len(pending)} 场 — 市场 vs 模型规则\n")
    out.append("| 编号 | 联赛 | 对阵(让球) | SP | 市场隐含(H/D/A) | 市场方向 | 规则视角模型倾向 |")
    out.append("|:----|:-----|:----------|:---|:---------------|:--------|:----------------|")
    for r in pending:
        if r["probs"] is None:
            out.append(
                f"| {r['no']} | {r['league']} | {r['home']}({r['hcp']})vs{r['away']} | {r['sp']} | 无SP | — | {'; '.join(r['triggers'])} |"
            )
            continue
        h, d, a = r["probs"]
        mdir = "H" if h >= d and h >= a else ("D" if d >= h and d >= a else "A")
        mdir_cn = {"H": "主胜", "D": "平", "A": "客胜"}[mdir]
        out.append(
            f"| {r['no']} | {r['league']} | {r['home']}({r['hcp']})vs{r['away']} | {r['sp']} | "
            f"{fmt_pct(h)}/{fmt_pct(d)}/{fmt_pct(a)} | {mdir_cn} | {'; '.join(r['triggers'])} |"
        )

    # 规则命中统计
    out.append("\n## 四、规则触发与命中统计\n")
    rule_stats = {}
    for r in done:
        for t in r["triggers"]:
            key = t.split("(")[0]
            if key not in rule_stats:
                rule_stats[key] = {"n": 0, "hit": 0}
            rule_stats[key]["n"] += 1
    out.append("| 规则 | 触发场次 | 说明 |")
    out.append("|:-----|:--------:|:-----|")
    for k, v in sorted(rule_stats.items(), key=lambda x: -x[1]["n"]):
        out.append(f"| {k} | {v['n']} | 待人工核验 |")

    text = "\n".join(out)
    print(text)
    with open(r"I:\阿飞说球\database\market_vs_model_20260815.md", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
