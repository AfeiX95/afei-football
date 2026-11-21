# -*- coding: utf-8 -*-
"""赛果核对与预测校准引擎（自动化反哺版 v1.0）。

链路：赛果核对 → 期次汇总 → 变差信号判定 → 纠偏建议 → 变差总结 → 反哺参数建议。

用法：
  python3 reconcile.py                        # 无赛果时只报「等待赛果录入」
  python3 reconcile.py --issue 26167          # 读台账 L/M 已录入的赛果
  python3 reconcile.py --input results.json   # 批量导入赛果
  python3 reconcile.py --demo                 # 内置模拟赛果演示（明确标注，不改台账、不代表真实赛果）
  python3 reconcile.py --issue 26167 --write-back   # 显式回写 05/06 表（需人工确认参数版本）

默认 dry-run：只输出 JSON 与 Markdown，绝不修改 01 表的赛前预测基线。
退出码：0 正常（含等待赛果）/ 2 台账缺失 / 3 赛果格式非法。
"""
import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path

try:
    import openpyxl
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "openpyxl>=3.1.0"])
    import openpyxl

BASE = Path(r"C:\Users\wuyan\WorkBuddy\2026-11-20-21-07-35")
LEDGER = BASE / "预测校准台账.xlsx"
SHEET = "01_赛果核对台账"
ROW0, ROW1 = 4, 63
FMAP = [3, 1, 0]
MIN_SAMPLE = 30
MAX_WEIGHT_CHANGE = 0.20
MAX_BIAS_STEP = 0.03

# 与 04_变差监控 完全一致：信号名 / 汇总键 / 基线 / 方向 / 容差 / 归因方向
SIGNALS = [
    ("方向命中率衰减", "hit_rate", 0.45, "低", 0.08, "来源失效型 / 盘型漂移型"),
    ("Brier 上升", "brier", 0.60, "高", 0.05, "过拟合型 / 概率校准失效"),
    ("LogLoss 上升", "logloss", 1.00, "高", 0.15, "过拟合型 / 高置信错判"),
    ("实际项概率下降", "q_actual", 0.45, "低", 0.05, "来源失效型"),
    ("信心偏差扩大", "conf_gap", 0.20, "高", 0.05, "临场信息型 / 大热倒灶"),
    ("比分命中率衰减", "score_hit_rate", 0.20, "低", 0.08, "比分区间设置过窄"),
    ("高置信倒灶率上升", "high_conf_miss", 0.15, "高", 0.10, "临场信息型 / 深盘松懈"),
    ("共振兑现率下降", "sig_共振", 0.55, "低", 0.10, "数据缺口型 / 来源失效型"),
    ("剔除规则倒挂", "W", 0.00, "高", 0.05, "S3 剔除优先级错配"),
    ("把握层次倒挂", "X", 0.10, "低", 0.05, "「该赢 vs 真赢得」拆解失效"),
    ("平局低估扩大", "Y", 0.00, "高", 0.08, "系统性低估平局，需加平局偏置"),
]

DEMO = {
    1: (3, "2-1"), 2: (3, "2-1"), 3: (1, "1-1"), 4: (1, "1-1"),
    5: (0, "1-2"), 6: (0, "0-1"), 7: (1, "1-1"), 8: (1, "2-2"),
    9: (3, "2-0"), 10: (1, "1-1"), 11: (0, "0-2"), 12: (1, "1-1"),
    13: (0, "0-2"), 14: (1, "1-1"),
}


def log(msg):
    print(msg, flush=True)


def read_baseline(path):
    """只读静态列：A–K 预测基线、L/M 赛果输入、U/V 状态。公式列不读，指标由本引擎自行计算。"""
    if not path.exists():
        log(f"[FATAL] 台账不存在：{path}")
        sys.exit(2)
    wb = openpyxl.load_workbook(path, data_only=False)
    if SHEET not in wb.sheetnames:
        log(f"[FATAL] 台账缺少 {SHEET}")
        sys.exit(2)
    ws = wb[SHEET]
    rows = []
    for r in range(ROW0, ROW1 + 1):
        issue = ws.cell(r, 1).value
        no = ws.cell(r, 2).value
        if not issue or not no:
            continue
        q = [ws.cell(r, c).value for c in (6, 7, 8)]
        if not all(isinstance(x, (int, float)) for x in q):
            log(f"[FATAL] 第 {r} 行预测概率非法：{q}")
            sys.exit(3)
        rows.append(dict(
            row=r, issue=str(issue), no=int(no), lg=ws.cell(r, 3).value,
            match=ws.cell(r, 4).value, pred=ws.cell(r, 5).value, q=[float(x) for x in q],
            tier=ws.cell(r, 9).value or "", sig=ws.cell(r, 10).value or "",
            score_plan=ws.cell(r, 11).value or "",
            result=ws.cell(r, 12).value, score=ws.cell(r, 13).value,
            r9=ws.cell(r, 21).value or "", note=ws.cell(r, 22).value or "",
        ))
    wb.close()
    return rows


def load_results(args, rows):
    """优先级：--demo > --input > 台账 L/M 列。"""
    if args.demo:
        log("[DEMO] 使用内置模拟赛果 —— 仅用于演示流程，不代表真实赛果，不写入台账。")
        return {no: {"result": v[0], "score": v[1]} for no, v in DEMO.items()}, "DEMO"
    if args.input:
        p = Path(args.input)
        if not p.exists():
            log(f"[FATAL] 赛果文件不存在：{p}")
            sys.exit(3)
        raw = json.loads(p.read_text(encoding="utf-8"))
        items = raw.get("results", raw) if isinstance(raw, dict) else raw
        out = {}
        if isinstance(items, dict):
            for k, v in items.items():
                out[int(k)] = {"result": v["result"], "score": v.get("score", "")}
        elif isinstance(items, list):
            for v in items:
                out[int(v["no"])] = {"result": v["result"], "score": v.get("score", "")}
        else:
            log("[FATAL] 赛果格式非法")
            sys.exit(3)
        return out, str(p)
    out = {}
    for d in rows:
        if d["result"] in (3, 1, 0, "*"):
            out[d["no"]] = {"result": d["result"], "score": d["score"] or ""}
    return out, str(LEDGER)


def validate(results):
    for no, v in results.items():
        r = v["result"]
        if r not in (3, 1, 0, "*"):
            log(f"[FATAL] 第 {no} 场赛果非法：{r}（只允许 3/1/0/*）")
            sys.exit(3)


def compute(rows, results, issue):
    valid, pending, postponed = [], [], []
    for d in rows:
        if str(d["issue"]) != str(issue):
            continue
        v = results.get(d["no"])
        if v is None or v["result"] in (None, ""):
            pending.append(d["no"])
            continue
        if v["result"] == "*":
            postponed.append(d["no"])
            continue
        q, res = d["q"], v["result"]
        y = [1 if FMAP[i] == res else 0 for i in range(3)]
        qa = q[y.index(1)]
        rec = dict(d)
        rec.update(
            result=res, score=v.get("score", ""),
            hit=1 if d["pred"] == res else 0,
            brier=sum((q[i] - y[i]) ** 2 for i in range(3)),
            logloss=-math.log(qa + 1e-6),
            q_actual=qa, qmax=max(q), conf_gap=max(q) - qa,
            score_hit=1 if (d["score_plan"] and v.get("score") and str(v["score"]) in str(d["score_plan"])) else 0,
        )
        valid.append(rec)

    n = len(valid)
    s = dict(issue=str(issue), n=n, pending=pending, postponed=postponed, rows=valid)
    if n == 0:
        return s

    def avg(key, subset=None):
        arr = subset if subset is not None else valid
        return sum(x[key] for x in arr) / len(arr) if arr else None

    def rate(pred, subset=None):
        arr = [x for x in (subset if subset is not None else valid) if pred(x)]
        return sum(x["hit"] for x in arr) / len(arr) if arr else None

    s["hit"] = sum(x["hit"] for x in valid)
    s["hit_rate"] = s["hit"] / n
    s["brier"] = avg("brier")
    s["logloss"] = avg("logloss")
    s["q_actual"] = avg("q_actual")
    s["conf_gap"] = avg("conf_gap")
    s["score_hit_rate"] = sum(x["score_hit"] for x in valid) / n
    s["actual_3"] = sum(1 for x in valid if x["result"] == 3) / n
    s["actual_1"] = sum(1 for x in valid if x["result"] == 1) / n
    s["actual_0"] = sum(1 for x in valid if x["result"] == 0) / n
    s["pred_3"] = sum(x["q"][0] for x in valid) / n
    s["pred_1"] = sum(x["q"][1] for x in valid) / n
    s["pred_0"] = sum(x["q"][2] for x in valid) / n
    # 精确匹配「最敢碰」四场（2/6/9/13）；11 号「最敢碰（但赔率已低）」单独分层，不计入
    s["tier_最敢碰"] = rate(lambda x: x["tier"] == "最敢碰")
    s["sig_共振"] = rate(lambda x: x["sig"] == "共振")
    s["sig_背离"] = rate(lambda x: x["sig"] == "背离")
    s["sig_数据不足"] = rate(lambda x: x["sig"] == "数据不足")
    s["r9_剔除"] = rate(lambda x: x["r9"] == "剔除")
    s["r9_单选"] = rate(lambda x: x["r9"] == "单选")
    hi = [x for x in valid if x["qmax"] > 0.60]
    s["high_conf_n"] = len(hi)
    s["high_conf_miss"] = 1 - sum(x["hit"] for x in hi) / len(hi) if hi else None

    def diff(a, b):
        return round(a - b, 4) if a is not None and b is not None else None

    s["W"] = diff(s["r9_剔除"], s["r9_单选"])
    s["X"] = diff(s["tier_最敢碰"], s["sig_数据不足"])
    s["Y"] = diff(s["actual_1"], s["pred_1"])
    return s


def judge(s):
    out = []
    for name, key, base, direction, tol, attrib in SIGNALS:
        cur = s.get(key)
        if cur is None:
            out.append(dict(signal=name, key=key, current=None, base=base,
                            direction=direction, tol=tol, verdict="数据未齐", attrib=attrib))
            continue
        worse = cur > base + tol if direction == "高" else cur < base - tol
        out.append(dict(signal=name, key=key, current=round(cur, 4), base=base,
                        direction=direction, tol=tol,
                        verdict="变差" if worse else "正常", attrib=attrib))
    return out


def corrections(s, judged, path):
    """四类纠偏建议；全部只给建议，不改已发布预测。"""
    acts = []
    bad = {j["key"] for j in judged if j["verdict"] == "变差"}

    # A 来源权重：读 02 表滚动样本
    try:
        wb = openpyxl.load_workbook(path, data_only=False)
        ws = wb["02_来源权重纠偏"]
        for r in range(4, 14):
            name = ws.cell(r, 1).value
            base_w = ws.cell(r, 2).value
            cnt = ws.cell(r, 3).value or 0
            hit = ws.cell(r, 4).value or 0
            if not name or not base_w:
                continue
            if cnt < MIN_SAMPLE:
                acts.append(dict(type="A 来源权重", param=str(name), current=base_w,
                                 suggest=base_w, version="—",
                                 basis=f"滚动样本 {cnt} < {MIN_SAMPLE}，维持基线", status="样本不足"))
                continue
            hr = hit / cnt
            coef = min(1.50, max(0.60, hr / 0.50))
            suggest = round(base_w * coef, 4)
            if abs(suggest - base_w) / base_w > MAX_WEIGHT_CHANGE:
                suggest = round(base_w * (1 + MAX_WEIGHT_CHANGE * (1 if coef > 1 else -1)), 4)
            acts.append(dict(type="A 来源权重", param=str(name), current=base_w,
                             suggest=suggest, version="待确认",
                             basis=f"滚动命中率 {hr:.3f}、样本 {cnt}", status="自动生效"))
        wb.close()
    except Exception as e:
        acts.append(dict(type="A 来源权重", param="—", current="—", suggest="—",
                         version="—", basis=f"02 表读取失败：{e}", status="需人工处理"))

    # B 判定阈值
    if "sig_共振" in bad or "hit_rate" in bad:
        acts.append(dict(type="B 阈值", param="价值 / 回避阈值", current="+5% / −5%",
                         suggest="各收紧 1pp（连续 2 期同向才生效）", version="待确认",
                         basis="方向命中率或共振兑现率低于基线", status="建议"))
    if "sig_数据不足" in bad or s.get("n", 0) < 10:
        acts.append(dict(type="B 阈值", param="完整度阈值", current="60%",
                         suggest="按低完整度场实测命中率复核，单次 ≤ 1pp", version="待确认",
                         basis="数据不足场表现异常或样本偏小", status="建议"))

    # C 结果偏置（指数平滑 + 单期幅度上限）
    for label, akey, pkey in (("主胜", "actual_3", "pred_3"), ("平局", "actual_1", "pred_1"), ("客胜", "actual_0", "pred_0")):
        actual = s.get(akey)
        pred = s.get(pkey)
        if actual is None or pred is None:
            continue
        raw = 0.3 * (actual - pred)
        step = min(MAX_BIAS_STEP, max(-MAX_BIAS_STEP, raw))
        if abs(step) >= 0.005:
            acts.append(dict(type="C 结果偏置", param=f"{label}校准偏置", current=0.00,
                             suggest=round(step, 4), version="待确认",
                             basis=f"实测占比 {actual:.3f} vs 预测均值 {pred:.3f}，单期幅度已封顶 0.03",
                             status="建议"))

    # D 剔除规则 / 把握层次
    if s.get("W") is not None and s["W"] > 0.05:
        acts.append(dict(type="D 剔除规则", param="任九剔除场数", current=5, suggest=4,
                         version="待确认",
                         basis=f"W={s['W']:.3f} > 0.05：剔除场命中率反超单选场，剔除优先级错配",
                         status="建议（需 ≥3 期样本）"))
    if s.get("X") is not None and s["X"] < 0.05:
        acts.append(dict(type="D 把握层次", param="最敢碰排序规则", current="沿用 S2 落差拆解",
                         suggest="下期重新拉开层次，优先核查体能/伤停权重", version="待确认",
                         basis=f"X={s['X']:.3f} < 0.05：最敢碰与数据不足场命中率未拉开",
                         status="建议（需 ≥3 期样本）"))
    if s.get("Y") is not None and s["Y"] > 0.08:
        acts.append(dict(type="C 结果偏置", param="平局校准偏置（信号 11）", current=0.00,
                         suggest=round(min(0.03, 0.3 * s["Y"]), 4), version="待确认",
                         basis=f"Y={s['Y']:.3f} > 0.08：系统性低估平局", status="建议"))
    return acts


def render_md(s, judged, acts, source, demo=False):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = []
    L.append(f"# 变差总结 · 第 {s['issue']} 期")
    L.append("")
    if demo:
        L.append("> ⚠️ **演示数据**：以下赛果为内置模拟值，仅用于验证核对链路，**不代表真实赛果**，未写入台账。")
        L.append("")
    L.append(f"- 生成时间：{now}")
    L.append(f"- 赛果来源：{source}")
    L.append(f"- 有效场数：{s['n']} ｜ 方向命中：{s.get('hit', 0)} ｜ 待录入：{len(s['pending'])} 场 ｜ 延期/腰斩：{len(s['postponed'])} 场")
    L.append(f"- 参数版本：v{s['issue']}（基线）→ 建议版本待人工确认")
    L.append("")
    L.append("## 一、核对结果")
    L.append("")
    L.append("| 指标 | 本期值 | 基线 | 判定 |")
    L.append("| --- | --- | --- | --- |")
    for j in judged:
        cur = "数据未齐" if j["current"] is None else f"{j['current']:.4f}"
        L.append(f"| {j['signal']}（{j['key']}） | {cur} | {j['base']:.2f} ± {j['tol']:.2f} | {j['verdict']} |")
    L.append("")
    L.append("## 二、触发的变差信号")
    L.append("")
    bad = [j for j in judged if j["verdict"] == "变差"]
    if not bad:
        L.append("本期未触发变差信号（或赛果数据未齐，保持基线不动）。")
    else:
        for j in bad:
            L.append(f"- **{j['signal']}**：当前 `{j['current']}`，阈值 `{j['base']} ± {j['tol']}`，归因方向：{j['attrib']}")
    L.append("")
    L.append("## 三、归因")
    L.append("")
    attribs = sorted({j["attrib"] for j in bad}) if bad else []
    if attribs:
        for a in attribs:
            L.append(f"- {a}")
    else:
        L.append("- 无变差信号，不启动归因；若为「数据未齐」，先补齐赛果与缺口来源，不调参数。")
    L.append("")
    L.append("## 四、纠正动作（下期生效，不追溯本期）")
    L.append("")
    L.append("| 类型 | 参数 | 当前值 | 建议值 | 变更依据 | 状态 |")
    L.append("| --- | --- | --- | --- | --- | --- |")
    for a in acts:
        L.append(f"| {a['type']} | {a['param']} | {a['current']} | {a['suggest']} | {a['basis']} | {a['status']} |")
    L.append("")
    L.append("## 五、下期验证点")
    L.append("")
    L.append("- 方向命中率回到 0.45 以上、Brier 回落至 0.60 附近，说明纠偏有效；否则回滚到上一稳定参数版本。")
    L.append("- W 重新转负（剔除场命中率低于单选场）、X 重新 > 0.10（最敢碰明显更准），说明剔除规则与把握层次排序恢复。")
    L.append("- 高置信（qmax > 0.60）场未命中率回落到 0.15 以下，说明临场信息复核到位。")
    L.append("")
    L.append("## 六、未关闭项")
    L.append("")
    L.append("- 停售前 22:00 二次定盘口径、临场首发名单、14 场逐场天气未复核。")
    L.append("- Polymarket / Kalshi、Forebet / Wincomparator / BetBuilders xG / OddAlerts、Google 数据模型、Futbol24、官方凯利指数未取到；缺席来源不降权、不计入分母。")
    L.append("- 首版基线为参考值，跑满 5 期后改用近 5 期滚动均值。")
    L.append("")
    L.append("> 全部内容仅作数据观察与思路参考，不构成投注建议，注意控制仓位与过关风险。")
    return "\n".join(L)


def write_back(s, judged, acts, source):
    """仅当 --write-back：追加 05 归档一行，并把 06 表建议值与生效期号填入。不触碰 01 表基线。"""
    wb = openpyxl.load_workbook(LEDGER)
    ws5 = wb["05_变差总结归档"]
    r = 4
    while ws5.cell(r, 1).value:
        r += 1
    bad = [j for j in judged if j["verdict"] == "变差"]
    ws5.cell(r, 1, s["issue"])
    ws5.cell(r, 2, datetime.now().strftime("%Y-%m-%d"))
    ws5.cell(r, 3, s["n"])
    ws5.cell(r, 4, len(bad))
    ws5.cell(r, 5, "；".join(j["signal"] for j in bad) or "无")
    ws5.cell(r, 6, "；".join(sorted({j["attrib"] for j in bad})) or "—")
    ws5.cell(r, 7, "；".join(f"{a['param']}→{a['suggest']}" for a in acts[:8]) or "—")
    ws5.cell(r, 8, f"v{s['issue']}+1（待确认）")
    ws5.cell(r, 9, "下期核对方向命中率、W/X/Y 三个倒挂差值是否回归")
    ws5.cell(r, 10, "临场首发、天气、定盘口径、缺席来源")
    ws5.cell(r, 11, "已生成·待确认")

    ws6 = wb["06_反哺参数出口"]
    by_param = {}
    for a in acts:
        by_param.setdefault(str(a["param"]), a)
    for rr in range(4, 22):
        name = str(ws6.cell(rr, 1).value or "")
        if name in by_param:
            a = by_param[name]
            ws6.cell(rr, 4, a["suggest"])
            ws6.cell(rr, 5, f"v{s['issue']}+1")
            ws6.cell(rr, 8, "待确认")
    wb.save(LEDGER)
    log(f"[WRITE-BACK] 已追加 05 归档第 {r} 行，并回填 06 表建议值（01 表基线未改动）。")


def main():
    global LEDGER
    ap = argparse.ArgumentParser(description="赛果核对与预测校准引擎")
    ap.add_argument("--issue", default="26167", help="目标期号")
    ap.add_argument("--input", help="赛果 JSON 路径")
    ap.add_argument("--demo", action="store_true", help="内置模拟赛果演示（不写入台账）")
    ap.add_argument("--write-back", action="store_true", help="显式回写 05/06 表")
    ap.add_argument("--ledger", default=str(LEDGER), help="台账路径")
    args = ap.parse_args()

    LEDGER = Path(args.ledger)
    rows = read_baseline(LEDGER)
    log(f"[LOAD] 台账 {LEDGER.name}：登记 {len(rows)} 场预测基线")

    results, source = load_results(args, rows)
    validate(results)
    issue = args.issue

    if not results:
        log(f"[WAIT] 第 {issue} 期赛果未录入（当前 2026-11-21 21:50 停售前，11-22 开奖）。")
        log("[WAIT] 不生成任何核对结论、不编造赛果、不修改参数。")
        log("[NEXT] 开奖后填写 01 表 L/M 两列，或用 --input results.json 导入，再重跑本引擎。")
        sys.exit(0)

    s = compute(rows, results, issue)
    if s["n"] == 0:
        log(f"[WAIT] 第 {issue} 期无有效赛果（待录入 {len(s['pending'])} 场）。")
        sys.exit(0)

    judged = judge(s)
    acts = corrections(s, judged, LEDGER)
    bad = [j for j in judged if j["verdict"] == "变差"]

    log(f"[CHECK] 第 {issue} 期有效 {s['n']} 场，方向命中 {s['hit']}/{s['n']} = {s['hit_rate']:.3f}")
    log(f"[CHECK] Brier {s['brier']:.4f} ｜ LogLoss {s['logloss']:.4f} ｜ 实际项概率 {s['q_actual']:.4f}")
    log(f"[CHECK] 倒挂差值 W={s['W']} X={s['X']} Y={s['Y']}")
    log(f"[JUDGE] 变差信号 {len(bad)} 条：{'、'.join(j['signal'] for j in bad) or '无'}")
    log(f"[FIX] 纠偏建议 {len(acts)} 条")

    payload = dict(issue=issue, source=source, demo=args.demo,
                   generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   summary={k: v for k, v in s.items() if k != "rows"},
                   signals=judged, corrections=acts,
                   per_match=[{k: v for k, v in x.items() if k in
                               ("no", "match", "lg", "pred", "q", "tier", "sig", "r9",
                                "result", "score", "hit", "brier", "logloss", "q_actual",
                                "conf_gap", "score_hit", "qmax")} for x in s["rows"]])
    suffix = "_DEMO" if args.demo else ""
    out_json = BASE / f"校准结果_{issue}{suffix}.json"
    out_md = BASE / f"变差总结_{issue}{suffix}.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_md(s, judged, acts, source, args.demo), encoding="utf-8")
    log(f"[OUT] {out_json.name}")
    log(f"[OUT] {out_md.name}")

    if args.write_back and not args.demo:
        write_back(s, judged, acts, source)
    elif args.demo:
        log("[DEMO] 演示模式不回写台账。")

    sys.exit(0)


if __name__ == "__main__":
    main()
