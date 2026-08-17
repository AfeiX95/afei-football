# -*- coding: utf-8 -*-
"""
市场 vs 模型 vs 实际 三方对比分析 (2026-08-15~17 竞彩赛果, 全69场)
数据源: 竞彩网足球赛果开奖页 (用户粘贴, 第一页30场 + 第二页30场 + 第三页9场)
模型侧: v2.8.0 修正规则库 C01-C26 规则视角判断
"""
import json

# 数据: 编号, 联赛, 主队, 让球(主队视角), 客队, SP主, SP平, SP客, 半场比分, 全场比分, 日期
# 让球: -1 表示主队让1球, +1 表示主队受让1球
MATCHES = [
    # ================= 第一页 (30场, 08-16~17) =================
    dict(no="周日028", league="美职", home="纽约城", hcp="-1", away="费城", sp_h=2.40, sp_d=3.45, sp_a=2.37, ht="2:0", ft="2:3", date="08-17"),
    dict(no="周日026", league="葡超", home="法马利康", hcp="-1", away="马里迪莫", sp_h=1.56, sp_d=3.52, sp_a=4.90, ht="1:1", ft="1:2", date="08-17"),
    dict(no="周日025", league="巴甲", home="达伽马", hcp="-1", away="桑托斯", sp_h=1.77, sp_d=3.40, sp_a=3.70, ht="0:0", ft="0:3", date="08-17"),
    dict(no="周日024", league="挪超", home="腓特烈", hcp="-1", away="克里斯蒂", sp_h=1.65, sp_d=3.66, sp_a=4.00, ht="1:0", ft="1:0", date="08-17"),
    dict(no="周日023", league="葡超", home="阿罗卡", hcp="-1", away="摩雷伦斯", sp_h=1.85, sp_d=3.00, sp_a=3.92, ht="3:0", ft="4:0", date="08-17"),
    dict(no="周日022", league="西甲", home="西班牙人", hcp="-1", away="莱万特", sp_h=1.97, sp_d=2.94, sp_a=3.55, ht="2:0", ft="3:0", date="08-17"),
    dict(no="周日021", league="挪超", home="萨普斯堡", hcp="-1", away="桑纳菲", sp_h=1.58, sp_d=4.00, sp_a=4.05, ht="1:1", ft="1:2", date="08-16"),
    dict(no="周日020", league="挪超", home="布兰", hcp="-1", away="汉坎", sp_h=1.38, sp_d=4.45, sp_a=5.55, ht="1:0", ft="3:0", date="08-16"),
    dict(no="周日019", league="挪超", home="莫尔德", hcp="-1", away="特罗姆瑟", sp_h=1.80, sp_d=3.90, sp_a=3.15, ht="1:0", ft="3:2", date="08-16"),
    dict(no="周日018", league="西甲", home="桑坦德", hcp="+1", away="比利亚雷", sp_h=3.45, sp_d=3.73, sp_a=1.75, ht="2:2", ft="2:2", date="08-16"),
    dict(no="周日017", league="英冠", home="伯恩利", hcp="+1", away="西汉姆联", sp_h=2.95, sp_d=3.38, sp_a=2.02, ht="0:1", ft="2:2", date="08-16"),
    dict(no="周日016", league="荷甲", home="阿贾克斯", hcp="-1", away="海伦芬", sp_h=1.33, sp_d=4.70, sp_a=6.10, ht="2:1", ft="2:2", date="08-16"),
    dict(no="周日015", league="瑞超", home="盖斯", hcp="-1", away="马尔默", sp_h=2.15, sp_d=3.30, sp_a=2.77, ht="0:0", ft="0:1", date="08-16"),
    dict(no="周日014", league="瑞超", home="卡尔马", hcp="+1", away="哈马比", sp_h=4.95, sp_d=4.05, sp_a=1.47, ht="0:1", ft="0:4", date="08-16"),
    dict(no="周日013", league="葡超", home="葡国民", hcp="-1", away="埃斯托里", sp_h=2.73, sp_d=2.95, sp_a=2.36, ht="0:0", ft="2:0", date="08-16"),
    dict(no="周日012", league="芬超", home="AC奥卢", hcp="+1", away="国际图尔", sp_h=2.95, sp_d=3.16, sp_a=2.11, ht="2:0", ft="2:3", date="08-16"),
    dict(no="周日011", league="英社区盾", home="阿森纳", hcp="-1", away="曼城", sp_h=2.65, sp_d=3.03, sp_a=2.37, ht="2:0", ft="3:0", date="08-16"),
    dict(no="周日010", league="挪超", home="奥勒松", hcp="+1", away="瓦勒伦加", sp_h=2.43, sp_d=3.86, sp_a=2.18, ht="4:2", ft="5:5", date="08-16"),
    dict(no="周日009", league="荷甲", home="费耶诺德", hcp="-1", away="前进之鹰", sp_h=1.15, sp_d=6.45, sp_a=9.50, ht="2:0", ft="2:2", date="08-16"),
    dict(no="周日008", league="荷甲", home="特温特", hcp="-2", away="兹沃勒", sp_h=1.16, sp_d=6.00, sp_a=10.00, ht="1:1", ft="3:1", date="08-16"),
    dict(no="周日007", league="瑞超", home="佐加顿斯", hcp="-1", away="索尔纳", sp_h=1.31, sp_d=4.80, sp_a=6.35, ht="0:3", ft="1:3", date="08-16"),
    dict(no="周日006", league="瑞超", home="代格福什", hcp="+1", away="哥德堡", sp_h=3.10, sp_d=3.30, sp_a=1.99, ht="3:0", ft="3:0", date="08-16"),
    dict(no="周日005", league="瑞超", home="布鲁马波", hcp="-1", away="厄格里特", sp_h=1.61, sp_d=3.80, sp_a=4.10, ht="1:0", ft="3:1", date="08-16"),
    dict(no="周日004", league="韩职", home="仁川联", hcp="-1", away="金泉尚武", sp_h=2.00, sp_d=3.00, sp_a=3.38, ht="0:0", ft="1:1", date="08-16"),
    dict(no="周日003", league="韩职", home="富川FC", hcp="+1", away="全北现代", sp_h=4.30, sp_d=3.28, sp_a=1.69, ht="2:0", ft="3:2", date="08-16"),
    dict(no="周日002", league="荷甲", home="海牙", hcp="+1", away="格罗宁根", sp_h=2.42, sp_d=3.30, sp_a=2.42, ht="0:3", ft="1:4", date="08-16"),
    dict(no="周日001", league="日乙", home="德岛漩涡", hcp="-1", away="鸟栖沙岩", sp_h=2.60, sp_d=2.95, sp_a=2.47, ht="0:0", ft="0:0", date="08-16"),
    dict(no="周六027", league="美职", home="盐湖城", hcp="-1", away="明尼苏达", sp_h=1.63, sp_d=3.72, sp_a=4.05, ht="0:0", ft="1:1", date="08-16"),
    dict(no="周六026", league="巴甲", home="弗鲁米嫩", hcp="+1", away="帕梅拉斯", sp_h=2.77, sp_d=2.65, sp_a=2.57, ht="1:1", ft="3:2", date="08-16"),
    dict(no="周六025", league="葡超", home="里奥阿维", hcp="+1", away="波尔图", sp_h=8.55, sp_d=4.70, sp_a=1.25, ht="0:1", ft="0:2", date="08-16"),
    # ================= 第二页 (30场, 08-15~16) =================
    dict(no="周六024", league="西甲", home="塞维利亚", hcp="-1", away="巴列卡诺", sp_h=2.23, sp_d=2.80, sp_a=3.10, ht="0:1", ft="2:1", date="08-16"),
    dict(no="周六023", league="荷甲", home="福图纳", hcp="-1", away="坎布尔", sp_h=1.52, sp_d=4.10, sp_a=4.40, ht="2:1", ft="3:1", date="08-16"),
    dict(no="周六022", league="荷甲", home="SBV精英", hcp="+1", away="埃因霍温", sp_h=5.72, sp_d=4.80, sp_a=1.34, ht="0:1", ft="1:2", date="08-16"),
    dict(no="周六021", league="沙职", home="利雅胜利", hcp="-2", away="穆拜征服", sp_h=None, sp_d=None, sp_a=None, ht="2:0", ft="3:0", date="08-16"),
    dict(no="周六020", league="沙职", home="吉达联合", hcp="-1", away="拉斯永恒", sp_h=1.36, sp_d=4.40, sp_a=6.00, ht="1:0", ft="1:1", date="08-16"),
    dict(no="周六019", league="西甲", home="阿拉维斯", hcp="-1", away="赫塔费", sp_h=2.24, sp_d=2.50, sp_a=3.55, ht="0:0", ft="3:0", date="08-16"),
    dict(no="周六018", league="葡超", home="维塞乌", hcp="+1", away="圣克拉拉", sp_h=2.95, sp_d=2.85, sp_a=2.28, ht="0:1", ft="0:1", date="08-16"),
    dict(no="周六017", league="荷甲", home="乌德勒支", hcp="+1", away="阿尔克马", sp_h=2.58, sp_d=3.53, sp_a=2.18, ht="0:1", ft="1:4", date="08-16"),
    dict(no="周六016", league="英冠", home="谢菲联", hcp="-1", away="伯明翰", sp_h=2.19, sp_d=3.10, sp_a=2.86, ht="0:0", ft="0:0", date="08-16"),
    dict(no="周六015", league="沙职", home="布赖合作", hcp="-1", away="赛哈海湾", sp_h=1.84, sp_d=3.50, sp_a=3.35, ht="0:0", ft="0:0", date="08-16"),
    dict(no="周六014", league="芬超", home="玛丽港", hcp="+1", away="塞伊奈", sp_h=5.00, sp_d=4.35, sp_a=1.43, ht="1:0", ft="2:0", date="08-16"),
    dict(no="周六013", league="葡超", home="阿尔维卡", hcp="-1", away="阿马多拉", sp_h=2.00, sp_d=2.92, sp_a=3.50, ht="0:0", ft="2:2", date="08-15"),
    dict(no="周六012", league="荷甲", home="威廉二世", hcp="+1", away="奈梅亨", sp_h=4.70, sp_d=4.15, sp_a=1.48, ht="0:1", ft="1:4", date="08-15"),
    dict(no="周六011", league="挪超", home="奥斯KFUM", hcp="+1", away="利勒斯特", sp_h=3.20, sp_d=3.60, sp_a=1.86, ht="0:0", ft="1:1", date="08-15"),
    dict(no="周六010", league="英冠", home="诺维奇", hcp="-1", away="西布罗姆", sp_h=1.87, sp_d=3.25, sp_a=3.48, ht="0:0", ft="1:2", date="08-15"),
    dict(no="周六009", league="瑞超", home="米亚尔比", hcp="+1", away="天狼星", sp_h=2.88, sp_d=3.40, sp_a=2.05, ht="0:3", ft="4:3", date="08-15"),
    dict(no="周六008", league="英冠", home="博尔顿", hcp="-1", away="普雷斯顿", sp_h=2.15, sp_d=3.08, sp_a=2.95, ht="2:0", ft="2:1", date="08-15"),
    dict(no="周六007", league="德乙", home="柏林赫塔", hcp="-1", away="海登海姆", sp_h=2.40, sp_d=3.40, sp_a=2.40, ht="3:0", ft="4:1", date="08-15"),
    dict(no="周六006", league="韩职", home="光州FC", hcp="+1", away="浦项制铁", sp_h=3.32, sp_d=2.90, sp_a=2.07, ht="0:1", ft="1:2", date="08-15"),
    dict(no="周六005", league="韩职", home="首尔FC", hcp="-1", away="大田市民", sp_h=2.04, sp_d=3.25, sp_a=3.02, ht="0:1", ft="4:2", date="08-15"),
    dict(no="周六004", league="日职", home="神户胜利", hcp="-1", away="东京FC", sp_h=2.03, sp_d=3.12, sp_a=3.16, ht="1:1", ft="2:2", date="08-15"),
    dict(no="周六003", league="日职", home="浦和红钻", hcp="+1", away="广岛三箭", sp_h=3.60, sp_d=3.35, sp_a=1.81, ht="1:2", ft="1:4", date="08-15"),
    dict(no="周六002", league="日乙", home="秋田闪电", hcp="+1", away="富山胜利", sp_h=2.85, sp_d=2.85, sp_a=2.34, ht="0:2", ft="0:4", date="08-15"),
    dict(no="周六001", league="日职", home="鹿岛鹿角", hcp="-1", away="名古屋鲸", sp_h=1.73, sp_d=3.38, sp_a=3.92, ht="1:0", ft="2:1", date="08-15"),
    dict(no="周五017", league="葡超", home="里斯本", hcp="-2", away="吉马良斯", sp_h=1.19, sp_d=5.30, sp_a=10.00, ht="3:0", ft="3:2", date="08-15"),
    dict(no="周五016", league="英冠", home="伍尔弗", hcp="-1", away="布莱克本", sp_h=1.38, sp_d=4.05, sp_a=6.35, ht="1:1", ft="2:2", date="08-15"),
    dict(no="周五015", league="法乙", home="圣埃蒂安", hcp="-1", away="克莱蒙", sp_h=1.33, sp_d=4.40, sp_a=6.70, ht="1:0", ft="3:1", date="08-15"),
    dict(no="周五014", league="法乙", home="兰斯", hcp="-1", away="敦刻尔克", sp_h=1.68, sp_d=3.40, sp_a=4.20, ht="1:1", ft="3:3", date="08-15"),
    dict(no="周五013", league="法乙", home="阿纳西", hcp="-1", away="罗德兹", sp_h=2.16, sp_d=3.05, sp_a=2.95, ht="1:0", ft="2:0", date="08-15"),
    dict(no="周五012", league="荷乙", home="赫拉克勒", hcp="-1", away="登博思", sp_h=1.46, sp_d=4.30, sp_a=4.71, ht="1:0", ft="3:2", date="08-15"),
    # ================= 第三页 (9场, 08-15) =================
    dict(no="周五011", league="荷乙", home="瓦尔韦克", hcp="-1", away="多德勒支", sp_h=1.74, sp_d=3.50, sp_a=3.72, ht="0:1", ft="2:2", date="08-15"),
    dict(no="周五010", league="荷甲", home="特尔斯达", hcp="-1", away="鹿斯巴达", sp_h=1.96, sp_d=3.60, sp_a=2.94, ht="0:1", ft="1:3", date="08-15"),
    dict(no="周五009", league="沙职", home="利雅新月", hcp="-3", away="哈马费萨", sp_h=None, sp_d=None, sp_a=None, ht="3:0", ft="4:2", date="08-15"),
    dict(no="周五008", league="沙职", home="达曼协定", hcp="-1", away="利雅得", sp_h=1.90, sp_d=3.35, sp_a=3.28, ht="1:1", ft="4:2", date="08-15"),
    dict(no="周五007", league="挪超", home="罗森博格", hcp="+1", away="维京", sp_h=2.28, sp_d=3.60, sp_a=2.42, ht="1:0", ft="2:1", date="08-15"),
    dict(no="周五006", league="瑞超", home="埃夫斯堡", hcp="-1", away="韦斯特罗", sp_h=1.57, sp_d=3.60, sp_a=4.65, ht="1:0", ft="3:0", date="08-15"),
    dict(no="周五005", league="沙职", home="新未来SC", hcp="-1", away="迈季宽广", sp_h=1.53, sp_d=3.75, sp_a=4.80, ht="2:0", ft="2:1", date="08-15"),
    dict(no="周五004", league="德乙", home="不伦瑞克", hcp="-1", away="波鸿", sp_h=2.18, sp_d=3.20, sp_a=2.80, ht="0:1", ft="0:1", date="08-15"),
    dict(no="周五003", league="德乙", home="基尔", hcp="-1", away="圣保利", sp_h=2.38, sp_d=3.23, sp_a=2.50, ht="0:2", ft="2:2", date="08-15"),
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
    """基于 SP 结构与让球的规则触发标注 (v2.8.0 规则库 C01-C26 视角)"""
    triggers = []
    h, d, a = m["sp_h"], m["sp_d"], m["sp_a"]
    hcp = m["hcp"]
    if h is None:
        return ["无SP(未开售单关)"]
    if h < 1.30 and hcp == "-1":
        triggers.append("C21超低赔大热让-1(恢复信任)")
    if h < 1.60:
        triggers.append("C22平局封顶(主胜<1.60)")
    if h < 2.00 and hcp == "-1":
        triggers.append("C15大热让-1陷阱(<2.00)")
    if h < 1.40:
        triggers.append("C06低赔主胜-3~5pp")
    if a < 1.40:
        triggers.append("C11低赔客胜-3~5pp")
    if hcp == "-1":
        triggers.append("C09/C12让球-1方-15~20pp")
    if hcp == "-2":
        triggers.append("让-2深盘")
    if hcp == "-3":
        triggers.append("让-3极端深盘")
    if h and a and abs(h - a) < 0.5:
        triggers.append("C16强强对话(平局+8~12pp)")
    if hcp == "-1" and m["league"] in ("韩职", "K联赛"):
        triggers.append("C26韩职让-1打穿难-5pp")
    if m["league"] in ("韩职", "K联赛"):
        triggers.append("C25韩职大球+10~15pp")
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
            "away": m["away"], "sp": f"{h}/{d}/{a}", "status": "已完成",
            "ft": m["ft"], "ht": m["ht"], "date": m["date"],
            "probs": probs, "triggers": trig, "actual": actual,
        }
        rows.append(row)

    out = []
    out.append("# 市场 vs 模型 vs 实际 三方对比 (2026-08-15~17 竞彩, 全69场)\n")
    out.append("> 模型侧: v2.8.0 规则库 C01-C26 视角 | 数据: 竞彩网赛果开奖页 | 69场全量\n")
    out.append("## 市场隐含概率去水口径: p = (1/odds) / Σ(1/odds)\n")

    out.append("\n## 一、已完成 69 场 — 市场 vs 实际\n")
    out.append("| 日期 | 编号 | 联赛 | 对阵(让球) | SP(胜/平/负) | 市场隐含(H/D/A) | 市场方向 | 实际 | 命中 | 规则触发 |")
    out.append("|:----|:----|:-----|:----------|:------------|:---------------|:--------|:----|:----:|:---------|")
    market_hit = 0
    market_total = 0
    for r in rows:
        if r["probs"] is None:
            out.append(
                f"| {r['date']} | {r['no']} | {r['league']} | {r['home']}({r['hcp']})vs{r['away']} | 无SP | 无SP | — | {r['ft']} | — | {'; '.join(r['triggers'])} |"
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
            f"| {r['date']} | {r['no']} | {r['league']} | {r['home']}({r['hcp']})vs{r['away']} | {r['sp']} | "
            f"{fmt_pct(h)}/{fmt_pct(d)}/{fmt_pct(a)} | {mdir_cn} | {r['ft']} | {hit} | {'; '.join(r['triggers'])} |"
        )
    out.append(f"\n**市场方向命中率: {market_hit}/{market_total} = {market_hit/market_total*100:.1f}%** (有效SP场次)\n")

    # 让球结果验证
    out.append("\n## 二、让球验证 (让球胜平负视角)\n")
    out.append("| 编号 | 对阵(让球) | 全场 | 让球后 | 结果 |")
    out.append("|:----|:----------|:----|:------|:----|")
    hcp_win = hcp_push = hcp_loss = 0
    hcp_1_total = 0
    hcp_1_win = 0
    for r in rows:
        hcp = int(r["hcp"]) if r["hcp"] else 0
        fh, fa = map(int, r["ft"].split(":"))
        adj_h = fh + hcp
        if adj_h > fa:
            hcp_res = "让球方胜"
            hcp_win += 1
        elif adj_h == fa:
            hcp_res = "让球平"
            hcp_push += 1
        else:
            hcp_res = "让球方负"
            hcp_loss += 1
        if hcp == -1:
            hcp_1_total += 1
            if adj_h > fa:
                hcp_1_win += 1
        out.append(f"| {r['no']} | {r['home']}({r['hcp']})vs{r['away']} | {r['ft']} | {adj_h}-{fa} | {hcp_res} |")
    out.append(f"\n**让球统计: 胜{hcp_win}/平{hcp_push}/负{hcp_loss} | 主队让-1场次 {hcp_1_total}场 赢盘 {hcp_1_win}场 (赢盘率 {hcp_1_win/max(hcp_1_total,1)*100:.1f}%)**\n")

    # 大小球统计
    out.append("\n## 三、大小球统计\n")
    over = 0
    for r in rows:
        fh, fa = map(int, r["ft"].split(":"))
        if fh + fa >= 3:
            over += 1
    out.append(f"- 大球(≥3球): {over}/69 = {over/69*100:.1f}%")
    out.append(f"- 小球(<3球): {69-over}/69 = {(69-over)/69*100:.1f}%")

    # 未命中场次
    out.append("\n## 四、市场未命中场次解剖\n")
    out.append("| 编号 | 对阵(让球) | 市场方向 | 市场隐含 | 实际 | 偏差性质 |")
    out.append("|:----|:----------|:--------|:--------|:----|:---------|")
    for r in rows:
        if r["probs"] is None:
            continue
        h, d, a = r["probs"]
        mdir = "H" if h >= d and h >= a else ("D" if d >= h and d >= a else "A")
        mdir_cn = {"H": "主胜", "D": "平", "A": "客胜"}[mdir]
        if mdir != r["actual"]:
            out.append(
                f"| {r['no']} | {r['home']}({r['hcp']})vs{r['away']} | {mdir_cn} | "
                f"{fmt_pct(h)}/{fmt_pct(d)}/{fmt_pct(a)} | {r['ft']} | 见规则触发 |"
            )

    text = "\n".join(out)
    print(text)
    with open(r"I:\阿飞说球\database\market_vs_model_20260817.md", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
