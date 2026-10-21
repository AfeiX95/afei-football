# -*- coding: utf-8 -*-
"""文章结构轮换（S01–S10）—— 读历史、挑选、落账。

背景：2026-10-21 外部评审指出「两篇只换了标题，骨架一样」，于是把结构从「写进提示词」
改成「落成文件 + 选择脚本」，避免靠记忆轮换。

用法
    python -X utf8 scripts/pick_structure.py --list
    python -X utf8 scripts/pick_structure.py --pick --stage pre --matches 2
    python -X utf8 scripts/pick_structure.py --record --structure S01 \
        --title "10月22日 波兹南vs桑德兰…" --teams "波兹南/桑德兰、贝西克塔/水晶宫" \
        --stage pre --date 2026-10-22

规则（对应评审第 2 条「结构轮换」）
- 最近 3 篇用过的结构，下一篇禁用；
- S05 只用于赛后；S06/S07 需要数据充足（人工用 --rich 声明）；S08 需要 ≥2 场；
- 在合格候选里优先「最久没用过」的，同分按目录顺序，避免假随机；
- 只有写完并通过门禁的稿子才 --record；失败/中止不写。
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "state", "writing_history.json")
KEEP = 30
BLOCK_RECENT = 3

CATALOG = [
    ("S01", "悬念追问型", "模型与市场方向相反、有反常识问题", {"pre"}),
    ("S02", "老球迷吐槽型", "名气与状态错位、豪门低迷", {"pre", "post"}),
    ("S03", "法庭辩论型", "两种判断针锋相对、需要交叉质证", {"pre"}),
    ("S04", "三幕剧型", "强弱分明、需要情景推演", {"pre"}),
    ("S05", "倒叙复盘型", "赛后从意外结果倒查赛前信号", {"post"}),
    ("S06", "数据侦探型", "异常数字、口径陷阱（需数据充足）", {"pre"}),
    ("S07", "战术棋局型", "阵型对位、关键位置（需战术信息）", {"pre"}),
    ("S08", "双线平行型", "两场或多场对照", {"pre", "post"}),
    ("S09", "假设实验型", "首发未定、按情形分支", {"pre"}),
    ("S10", "误区粉碎型", "身价/排名等直觉误区", {"pre", "post"}),
]
NAMES = {c[0]: c[1] for c in CATALOG}


def load() -> dict:
    if os.path.exists(HIST):
        with io.open(HIST, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("articles", [])
    data.setdefault("note", "结构轮换账本：最近 3 篇用过的结构下一篇禁用；只记已过门禁的稿。")
    return data


def save(data: dict) -> None:
    data["articles"] = data["articles"][-KEEP:]
    tmp = HIST + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, HIST)


def eligible(stage: str, matches: int, rich: bool) -> list:
    out = []
    for sid, name, best, stages in CATALOG:
        if stage not in stages:
            continue
        if sid == "S08" and matches < 2:
            continue
        if sid in ("S06", "S07") and not rich:
            continue
        out.append((sid, name, best))
    return out


def pick(stage: str, matches: int, rich: bool) -> tuple:
    data = load()
    arts = data["articles"]
    used = [a.get("structure") for a in arts if a.get("structure")]
    recent = used[-BLOCK_RECENT:]
    cands = eligible(stage, matches, rich)
    fresh = [c for c in cands if c[0] not in recent] or cands
    # 最久没用过优先；没用过的按目录顺序排前面
    def age(sid: str) -> int:
        for i in range(len(used) - 1, -1, -1):
            if used[i] == sid:
                return len(used) - i
        return 10 ** 6
    fresh.sort(key=lambda c: (-age(c[0]), c[0]))
    sid, name, best = fresh[0]
    return data, sid, name, best, recent


def record(sid: str, title: str, teams: str, stage: str, date: str,
           hook: str, ending: str, humor: str) -> dict:
    data = load()
    data["articles"].append({
        "id": "%s-%02d" % (date.replace("-", ""), len(data["articles"]) + 1),
        "date": date,
        "title": title,
        "teams": teams,
        "stage": stage,
        "structure": sid,
        "hook": hook,
        "ending": ending,
        "humor": humor,
        "status": "published" if stage else "draft",
    })
    save(data)
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description="文章结构轮换（S01–S10）")
    ap.add_argument("--list", action="store_true", help="列出结构池与最近使用情况")
    ap.add_argument("--pick", action="store_true", help="选一个结构")
    ap.add_argument("--record", action="store_true", help="稿子过门禁后落账")
    ap.add_argument("--stage", default="pre", choices=["pre", "post"])
    ap.add_argument("--matches", type=int, default=1)
    ap.add_argument("--rich", action="store_true", help="数据充足：允许 S06/S07")
    ap.add_argument("--structure")
    ap.add_argument("--title", default="")
    ap.add_argument("--teams", default="")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--hook", default="")
    ap.add_argument("--ending", default="")
    ap.add_argument("--humor", default="")
    a = ap.parse_args()

    if a.list:
        data = load()
        used = [x.get("structure") for x in data["articles"]]
        print("结构池（最近使用距离 / 次数）")
        for sid, name, best, stages in CATALOG:
            n = used.count(sid)
            last = max([i for i, s in enumerate(used) if s == sid], default=None)
            dist = "未用过" if last is None else "%d 篇前" % (len(used) - last)
            print("  %s %-6s 次数 %d  上次 %-8s 适用：%s" % (sid, name, n, dist, best))
        print("\n最近 3 篇：%s" % ", ".join(used[-BLOCK_RECENT:] or ["（空）"]))
        return

    if a.pick:
        data, sid, name, best, recent = pick(a.stage, a.matches, a.rich)
        print("本篇结构：%s %s" % (sid, name))
        print("  适合：%s" % best)
        print("  最近 3 篇用过：%s（本篇避开了）" % (", ".join(recent) or "无"))
        print("  写完并过门禁后再跑 --record 落账，别提前写。")
        return

    if a.record:
        if not a.structure:
            raise SystemExit("--record 需要 --structure（例如 S01）")
        if a.structure not in NAMES:
            raise SystemExit("未知结构：%s" % a.structure)
        data = record(a.structure, a.title, a.teams, a.stage, a.date,
                      a.hook, a.ending, a.humor)
        print("已落账：%s %s｜共 %d 篇" % (a.structure, NAMES[a.structure], len(data["articles"])))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
