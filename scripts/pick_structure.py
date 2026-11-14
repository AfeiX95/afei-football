# -*- coding: utf-8 -*-
"""【已并入 writing_engine.py】R53 旧十结构池选择器 —— 2026-11-07 起由 R62 双层轮换取代。

旧池（S01 悬念追问 / S02 老球迷吐槽 / … / S10 误区粉碎）与新池 ID 含义不同；
旧账本记录已在 state/writing_history.json 里标 scheme=R53-v1，只留档不参与新轮换。

本文件保留为转发壳，避免旧文档/旧命令失效：
    python -X utf8 scripts/pick_structure.py --pick --matches 4   → writing_engine.py --pick --matches 4
    python -X utf8 scripts/pick_structure.py --list               → writing_engine.py --list
--record 不再转发（新账本必须同时写风格），请直接用：
    python -X utf8 scripts/writing_engine.py --record --article <文章.md> --style X --structure SNN
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    args = sys.argv[1:]
    print("⚠️ pick_structure.py 已并入 writing_engine.py（R62 双层轮换），以下为转发结果：\n")
    if "--record" in args:
        raise SystemExit("--record 请改用：writing_engine.py --record --article <文章.md> --style X --structure SNN")
    keep, skip = [], False
    for i, x in enumerate(args):
        if skip:
            skip = False
            continue
        if x == "--rich":
            continue  # 旧参数：新引擎用 --feat 描述素材
        keep.append(x)
    sys.exit(subprocess.call([sys.executable, "-X", "utf8", os.path.join(HERE, "writing_engine.py"), *keep]))
