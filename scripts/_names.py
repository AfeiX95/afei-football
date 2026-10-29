"""队名归一与别名词典（fenxi_500 / audit_data / model_v3 共用）。

真源：database/config/team_aliases.json（中文队名 → 外部源标识，可带 alt 列表）。
命中规则：等价写法优先，其次一方是另一方子串（500 常缩写：谢菲尔德联→谢菲联、汉诺威96→汉诺威）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALIAS_FILE = ROOT / "database" / "config" / "team_aliases.json"

_IDX: dict[str, set[str]] | None = None


def norm_name(s: object) -> str:
    """去空格/中点/点号，便于比对"""
    return re.sub(r"[\s\u00b7\.]", "", str(s or ""))


def aliases() -> dict[str, set[str]]:
    """归一化队名 → 同组所有写法（含自身）"""
    global _IDX
    if _IDX is not None:
        return _IDX
    idx: dict[str, set[str]] = {}
    raw: dict = {}
    if ALIAS_FILE.exists():
        try:
            raw = json.loads(ALIAS_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            raw = {}
    for k, v in (raw or {}).items():
        if str(k).startswith("_"):
            continue
        names = {str(k)}
        if isinstance(v, str):
            names.add(v)
        elif isinstance(v, dict):
            for vv in v.values():
                if isinstance(vv, str):
                    names.add(vv)
                elif isinstance(vv, (list, tuple)):
                    names.update(str(x) for x in vv if isinstance(x, str))
        norm = {n for n in (norm_name(x) for x in names) if n}
        for n in norm:
            idx.setdefault(n, set()).update(norm)
    _IDX = idx
    return idx


def equiv(team: object) -> list[str]:
    """队名的所有等价写法（自身在前）"""
    t = norm_name(team)
    if not t:
        return []
    return [t] + [x for x in aliases().get(t, ()) if x != t]


def name_hit(team: object, name: object) -> bool:
    """team 是否就是 name（允许缩写 / 别名）"""
    if not norm_name(team) or not norm_name(name):
        return False
    cands = set(equiv(name))
    for a in equiv(team):
        for b in cands:
            if a == b or (len(a) >= 2 and len(b) >= 2 and (a in b or b in a)):
                return True
    return False
