# -*- coding: utf-8 -*-
"""竞彩官方盘口快照库（免费、免 key、自动攒「位移」）

为什么要它
----------
竞彩官方 webapi 的 `getMatchCalculatorV1` 每次只给**当前一档**定价（`oddsHistory` 每档也只有 1 条），
所以「盘口位移」过去只能靠人工粘多个时点。本脚本把这件事自动化：
定时抓取 → 落 `state/odds.sqlite` → 累积「定价 → 去水概率」时间序列 → 随时出位移表。

傻瓜用法
--------
双击仓库根的 **`盘口采集器.cmd`**，按菜单选 1/2/3/4 即可（不用记命令、不用任何 API Key）。

命令行（与菜单等价）
--------------------
  python scripts/odds_snapshot.py once                  # 抓一次并入库
  python scripts/odds_snapshot.py loop --every 15       # 每 15 分钟抓一次（Ctrl+C 停）
  python scripts/odds_snapshot.py move --days 3         # 位移表（首 → 末 + 每个变化点）
  python scripts/odds_snapshot.py move --query 周二004   # 只看某场（编号/队名/id 子串都行）
  python scripts/odds_snapshot.py list --days 3         # 库里已有哪些场次

设计
----
- 只存「提取后的报价」，不存 raw JSON：10 场 × 2 个盘口 ≈ 20 行/次，一天 96 次也就两千行。
- 快照表带 digest：与上一快照完全相同 → `changed=0`，方便筛「真有变化的时点」。
- 概率口径 = 去水（`scripts/devig.py` 的 `devig()`），与站内其它脚本一致。
- 数据源是竞彩官方（`📚知识库/数据源/API接口.md` 的直连配方），**不需要任何第三方 API Key**。
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import sporttery_fetch as sf                     # noqa: E402  （复用 567 配方 + cookie 预热）
from devig import devig                          # noqa: E402

SLATE_PATH = "/gateway/uniform/football/getMatchCalculatorV1.qry"
DEFAULT_DB = os.path.join(ROOT, "state", "odds.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS snap (
  taken_at  TEXT PRIMARY KEY,
  n_matches INTEGER,
  digest    TEXT,
  changed   INTEGER
);
CREATE TABLE IF NOT EXISTS quote (
  taken_at  TEXT,
  match_id  TEXT,
  match_num TEXT,
  kickoff   TEXT,
  league    TEXT,
  home      TEXT,
  away      TEXT,
  market    TEXT,
  line      TEXT,
  h REAL, d REAL, a REAL,
  status    TEXT,
  PRIMARY KEY (taken_at, match_id, market)
);
CREATE INDEX IF NOT EXISTS ix_quote ON quote(match_id, market, taken_at);
"""


# --------------------------------------------------------------------------- 基础
def conn(db):
    os.makedirs(os.path.dirname(db) or ".", exist_ok=True)
    c = sqlite3.connect(db)
    c.executescript(SCHEMA)
    return c


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def probs(h, d, a):
    """去水概率（%）。任一档缺失就返回 None。"""
    if None in (h, d, a):
        return None
    try:
        p, _ = devig([h, d, a])
        return p
    except Exception:
        return None


def fmt_odds(h, d, a):
    return " / ".join(("%.2f" % x) if x is not None else "-" for x in (h, d, a))


def fmt_probs(p):
    return " / ".join("%.1f%%" % x for x in p) if p else "-"


# --------------------------------------------------------------------------- 抓取
def fetch_rows():
    """抓在售全盘口；一次失败就重新预热再试一次。"""
    st, b = sf.get(SLATE_PATH, {"channel": "c"})
    if st != 200 or len(b) < 100:
        sf.warmup()
        st, b = sf.get(SLATE_PATH, {"channel": "c"})
    if st != 200 or len(b) < 100:
        raise RuntimeError("取数失败 HTTP %s（先确认能打开 https://www.sporttery.cn/）" % st)
    val = json.loads(b.decode("utf-8")).get("value") or {}
    rows = []
    for mi in val.get("matchInfoList", []) or []:
        for m in mi.get("subMatchList", []) or []:
            rows.append(m)
    return rows


def rows_to_recs(rows):
    """→ [(match_id, num, kickoff, league, home, away, market, line, h, d, a, status)]"""
    recs = []
    for m in rows:
        mid = str(m.get("matchId") or "").strip()
        if not mid:
            continue
        base = (mid,
                str(m.get("matchNumStr") or "").strip(),
                ("%s %s" % (m.get("matchDate") or "", m.get("matchTime") or "")).strip(),
                str(m.get("leagueAbbName") or "").strip(),
                str(m.get("homeTeamAbbName") or "").strip(),
                str(m.get("awayTeamAbbName") or "").strip())
        status = str(m.get("matchStatus") or "")
        had = m.get("had") or {}
        if fnum(had.get("h")):
            recs.append(base + ("胜平负", "", fnum(had.get("h")), fnum(had.get("d")),
                                fnum(had.get("a")), status))
        hh = m.get("hhad") or {}
        if fnum(hh.get("h")):
            recs.append(base + ("让球", str(hh.get("goalLine") or ""), fnum(hh.get("h")),
                                fnum(hh.get("d")), fnum(hh.get("a")), status))
    return recs


# --------------------------------------------------------------------------- 快照
def print_snapshot(c, taken_at):
    rs = c.execute("""SELECT match_num, kickoff, league, home, away, market, line, h, d, a
                      FROM quote WHERE taken_at=? ORDER BY kickoff, match_num, market""",
                   (taken_at,)).fetchall()
    print("-" * 78)
    cur = None
    for num, kick, lg, hm, aw, mk, line, h, d, a in rs:
        key = (num, kick, hm, aw)
        if key != cur:
            cur = key
            print("%s  %s  %s  %s vs %s" % (num, kick, lg, hm, aw))
        lbl = mk + ("(%s)" % line if line else "")
        print("    %-9s %-20s %s" % (lbl, fmt_odds(h, d, a), fmt_probs(probs(h, d, a))))
    print("-" * 78)


def print_diff(c, cur_ts, prev_ts):
    prev = {(r[0], r[1]): (r[2], r[3], r[4]) for r in c.execute(
        "SELECT match_id, market, h, d, a FROM quote WHERE taken_at=?", (prev_ts,))}
    n = 0
    for mid, num, hm, aw, mk, line, h, d, a in c.execute(
            """SELECT match_id, match_num, home, away, market, line, h, d, a
               FROM quote WHERE taken_at=? ORDER BY match_num""", (cur_ts,)):
        p = prev.get((mid, mk))
        if not p or p == (h, d, a):
            continue
        n += 1
        lbl = mk + ("(%s)" % line if line else "")
        print("  Δ %s %s vs %s  %-9s %s → %s   概率 %s → %s" % (
            num, hm, aw, lbl, fmt_odds(*p), fmt_odds(h, d, a),
            fmt_probs(probs(*p)), fmt_probs(probs(h, d, a))))
    print("（与上一快照 %s 比：%s）" % (prev_ts, "无变化" if n == 0 else "%d 处报价有变化" % n))


def do_snapshot(db, quiet=False):
    rows = fetch_rows()
    recs = rows_to_recs(rows)
    taken_at = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    digest = hashlib.sha1(json.dumps(recs, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]

    c = conn(db)
    prev = c.execute("SELECT taken_at, digest FROM snap ORDER BY taken_at DESC LIMIT 1").fetchone()
    changed = 0 if (prev and prev[1] == digest) else 1
    c.execute("INSERT OR REPLACE INTO snap VALUES (?,?,?,?)", (taken_at, len(rows), digest, changed))
    c.executemany("INSERT OR REPLACE INTO quote VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  [(taken_at,) + r for r in recs])
    c.commit()

    print("[%s] 入库：%d 场 / %d 条报价  digest=%s  %s" % (
        taken_at, len(rows), len(recs), digest, "有变化" if changed else "与上一快照相同"))
    if not quiet:
        print_snapshot(c, taken_at)
        if prev:
            print_diff(c, taken_at, prev[0])
    c.close()
    return taken_at


# --------------------------------------------------------------------------- 位移表
def cmd_move(db, days, query, min_pp):
    c = conn(db)
    since = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    rows = c.execute("""SELECT match_id, match_num, kickoff, league, home, away, market, line,
                               taken_at, h, d, a
                        FROM quote WHERE taken_at>=?""", (since,)).fetchall()
    if query:
        q = query.strip()
        rows = [r for r in rows
                if q in (r[1] or "") or q in (r[4] or "") or q in (r[5] or "") or q in (r[0] or "")]
    if not rows:
        print("库里没有符合条件的快照（先跑 once 抓一次；用 list 看有哪些场次）。")
        return

    blk = {}
    for mid, num, kick, lg, hm, aw, mk, line, ts, h, d, a in rows:
        b = blk.setdefault(mid, {"meta": (num, kick, lg, hm, aw), "mk": {}})
        b["mk"].setdefault(mk, []).append((ts, line, h, d, a))

    shown = 0
    for mid, b in sorted(blk.items(), key=lambda kv: kv[1]["meta"][1]):
        num, kick, lg, hm, aw = b["meta"]
        lines = []
        for mk in ("胜平负", "让球"):
            items = sorted(b["mk"].get(mk) or [])
            if not items:
                continue
            pts = [items[0]]
            for it in items[1:]:
                if (it[2], it[3], it[4]) != (pts[-1][2], pts[-1][3], pts[-1][4]):
                    pts.append(it)
            p0, p1 = probs(pts[0][2], pts[0][3], pts[0][4]), probs(*pts[-1][2:])
            delta = max(abs(x - y) for x, y in zip(p0, p1)) if (p0 and p1) else 0.0
            if min_pp and delta < min_pp:
                continue
            lines.append((mk, items, pts, p0, p1, delta))
        if not lines:
            continue
        shown += 1
        print("=" * 78)
        print("%s %s  %s  %s vs %s   [id=%s]" % (num, lg, kick, hm, aw, mid))
        for mk, items, pts, p0, p1, delta in lines:
            lbl = mk + ("(%s)" % pts[-1][1] if pts[-1][1] else "")
            if len(pts) == 1:
                print("  %s：快照 %d 次，**无位移**  %s  %s" % (
                    lbl, len(items), fmt_odds(pts[0][2], pts[0][3], pts[0][4]),
                    fmt_probs(probs(pts[0][2], pts[0][3], pts[0][4]))))
                continue
            print("  %s：快照 %d 次，变化点 %d 个" % (lbl, len(items), len(pts)))
            for i, (ts, line, h, d, a) in enumerate(pts):
                tag = "首" if i == 0 else ("末" if i == len(pts) - 1 else "中")
                print("      %s %s  %-20s %s" % (tag, ts, fmt_odds(h, d, a),
                                                 fmt_probs(probs(h, d, a))))
            if p0 and p1:
                print("      → 净位移 %s → %s   最大 %.1fpp" % (fmt_probs(p0), fmt_probs(p1), delta))
            else:
                print("      → 定价 %s → %s（有档位缺失，未算概率）" % (
                    fmt_odds(pts[0][2], pts[0][3], pts[0][4]), fmt_odds(*pts[-1][2:])))
    print("=" * 78)
    print("共 %d 场（最近 %.0f 天；过滤=%s；min-pp=%.1f）" % (shown, days, query or "-", min_pp))


def cmd_list(db, days):
    c = conn(db)
    since = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    s = c.execute("SELECT COUNT(*), MIN(taken_at), MAX(taken_at) FROM snap WHERE taken_at>=?",
                  (since,)).fetchone()
    print("库文件：%s" % db)
    print("快照 %s 次%s" % (s[0], ("（%s → %s）" % (s[1], s[2])) if s[0] else ""))
    rs = c.execute("""SELECT match_id, match_num, kickoff, league, home, away,
                             COUNT(DISTINCT taken_at), MIN(taken_at), MAX(taken_at)
                      FROM quote WHERE taken_at>=?
                      GROUP BY match_id ORDER BY kickoff, match_num""", (since,)).fetchall()
    for mid, num, kick, lg, hm, aw, n, t0, t1 in rs:
        print("  %-8s %-10s %-16s %-6s %s vs %s   快照 %d 次  %s → %s" % (
            num, mid, kick, lg, hm, aw, n, t0, t1))
    if not rs:
        print("  （空：先跑一次 once）")


# --------------------------------------------------------------------------- loop
def cmd_loop(db, every, quiet):
    print("自动采集启动：每 %d 分钟一次。**这个窗口开着才抓**，Ctrl+C 或关窗就停。" % every)
    while True:
        t0 = time.time()
        try:
            do_snapshot(db, quiet=quiet)
        except KeyboardInterrupt:
            print("\n已停止。")
            return
        except Exception as e:
            print("本轮失败：%s（%d 分钟后重试）" % (e, every))
        try:
            time.sleep(max(5.0, every * 60 - (time.time() - t0)))
        except KeyboardInterrupt:
            print("\n已停止。")
            return


# --------------------------------------------------------------------------- 傻瓜菜单
DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "📚知识库", "数据源", "本地盘口库.md")


def _pause():
    try:
        input("（回车返回菜单）")
    except (EOFError, KeyboardInterrupt):
        pass


def cmd_menu(db):
    """给 盘口采集器.cmd 用的交互菜单（界面放 python 里，避免 cmd 的编码坑）。"""
    while True:
        print("")
        print("=" * 64)
        print("   阿飞说球 · 盘口采集器")
        print("   数据源：中国竞彩官方（免费，不需要任何 API Key）")
        print("   存到：%s" % db)
        print("=" * 64)
        print("   1   立刻抓一次（显示与上一快照的差异）")
        print("   2   自动抓：每 15 分钟一次（开着这个窗口才抓，Ctrl+C 停）")
        print("   3   看位移表（最近 3 天，可只查某一场）")
        print("   4   看库里已有哪些场次")
        print("   5   打开使用说明")
        print("   0   退出")
        print("=" * 64)
        try:
            c = input("请输入序号后回车：").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return
        try:
            if c == "1":
                sf.warmup()
                do_snapshot(db, quiet=False)
                _pause()
            elif c == "2":
                sf.warmup()
                cmd_loop(db, 15, False)
                _pause()
            elif c == "3":
                q = input("输入竞彩编号 / 队名 / ID（直接回车 = 看全部）：").strip()
                cmd_move(db, 3, q, 0.0)
                _pause()
            elif c == "4":
                cmd_list(db, 3)
                _pause()
            elif c == "5":
                if os.path.exists(DOC) and hasattr(os, "startfile"):
                    os.startfile(DOC)
                else:
                    print("说明文档：%s" % DOC)
                _pause()
            elif c in ("0", "q", "quit", "exit"):
                print("已退出。")
                return
            else:
                print("没看懂这个序号，再输一次。")
        except KeyboardInterrupt:
            print("\n已中断，回到菜单。")


def main():
    ap = argparse.ArgumentParser(description="竞彩官方盘口快照库（免费、免 key）")
    ap.add_argument("mode", choices=["once", "loop", "move", "list", "menu"])
    ap.add_argument("--every", type=int, default=15, help="loop 间隔分钟数（默认 15）")
    ap.add_argument("--days", type=float, default=3, help="move/list 只看最近 N 天（默认 3）")
    ap.add_argument("--query", default="", help="move 过滤：竞彩编号 / 队名 / id 的子串")
    ap.add_argument("--min-pp", type=float, default=0.0, help="move 只列最大位移 ≥ 该值的行")
    ap.add_argument("--db", default=DEFAULT_DB, help="SQLite 路径（默认 state/odds.sqlite）")
    ap.add_argument("--quiet", action="store_true", help="少打印")
    a = ap.parse_args()

    if a.mode == "once":
        sf.warmup()
        do_snapshot(a.db, quiet=a.quiet)
    elif a.mode == "loop":
        sf.warmup()
        cmd_loop(a.db, a.every, a.quiet)
    elif a.mode == "move":
        cmd_move(a.db, a.days, a.query, a.min_pp)
    elif a.mode == "menu":
        cmd_menu(a.db)
        return
    else:
        cmd_list(a.db, a.days)
    print("DONE")


if __name__ == "__main__":
    main()
