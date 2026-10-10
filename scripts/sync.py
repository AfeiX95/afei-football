#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""阿飞说球 · 两台机器同步（家里 PC ↔ 公司 PC）。

用法：
    python scripts/sync.py              # 完整同步：先拉取(rebase) 再推送全部远端
    python scripts/sync.py --pull       # 只拉取（开工前跑）
    python scripts/sync.py --push       # 只推送（收工 commit 之后跑）
    python scripts/sync.py --status     # 只看状态，什么都不改
    python scripts/sync.py --remote gitee   # 只对一个远端操作

为什么这么设计（改这个脚本前先读）：
1. **开工先拉、收工再推**。两台机器最大的风险是各自在旧版本上写，收工时互相覆盖。
   拉取一律用 `--rebase`：历史保持线性，不产生无意义的 merge 提交。
2. **工作区不干净就直接拒绝**。有未提交改动时 `pull --rebase` 会把改动卷进冲突里，
   所以先要求 commit（本仓库收工约定就是「commit 之后再推」）。
3. **冲突绝不自动猜**。rebase 撞冲突立刻 `git rebase --abort` 原样退回，把决定权交回人。
   本仓库含 png/docx 等二进制文件，自动合并必然出错。
4. **某个远端连不上不拖累其他远端**。GitHub 在部分网络（如公司网）不可达，
   不该因此挡住 Gitee 那条主力通道；最后按「至少一条成功」判定。
5. 拉取只用**一个**远端（默认优先 `gitee`，其次 `origin`）——
   多个镜像同时 rebase 会产生重复提交，所以拉取必须单一来源。
"""
import argparse
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 拉取的来源优先级：gitee 是主力同步通道，origin(GitHub) 是异地备份
PULL_PREFERENCE = ("gitee", "origin")


def git(*args, check=False, timeout=600):
    """跑一条 git 命令。返回 (returncode, stdout, stderr)。"""
    env = dict(os.environ)
    # 教训：GIT_SSH_COMMAND 会让 git 走 shell 解析，在受限沙箱下会撞命名管道限制，
    # 且会覆盖用户自己的 ssh 配置，所以一律清掉。
    env.pop("GIT_SSH_COMMAND", None)
    env["GIT_TERMINAL_PROMPT"] = "0"  # 缺凭据时立刻失败，不要卡在交互输入
    # 中文路径在 Windows 下默认会被转义成 \xxx，关掉以便输出可读
    env["LC_ALL"] = "C.UTF-8"
    try:
        p = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return 124, "", f"git {' '.join(args)} 超时（>{timeout}s）"


def line(title=""):
    print("\n" + "=" * 62)
    if title:
        print("  " + title)
        print("=" * 62)


def remotes():
    """返回 [{'name','url'}]。"""
    rc, out, _ = git("remote")
    if rc != 0 or not out:
        return []
    result = []
    for name in out.splitlines():
        name = name.strip()
        if not name:
            continue
        _, url, _ = git("remote", "get-url", name)
        result.append({"name": name, "url": url})
    return result


def pick_pull_remote(names, forced=None):
    if forced:
        return forced if forced in names else None
    for want in PULL_PREFERENCE:
        if want in names:
            return want
    return names[0] if names else None


def branch():
    rc, out, _ = git("branch", "--show-current")
    return out if rc == 0 and out else "master"


def dirty():
    rc, out, _ = git("status", "--porcelain")
    return out.splitlines() if rc == 0 and out else []


def porcelain_status():
    """返回 (branch, dirty_paths, ahead_text)。"""
    br = branch()
    d = dirty()
    return br, d


def show_status(remotes_list, forced=None):
    br, d = porcelain_status()
    line("阿飞说球 · 同步状态")
    print(f"[分支] {br}")
    if d:
        print(f"[工作区] ⚠️ 不干净，{len(d)} 项未提交：")
        for p in d[:10]:
            print("   " + p)
        if len(d) > 10:
            print(f"   …还有 {len(d) - 10} 项")
    else:
        print("[工作区] ✅ 干净")
    if not remotes_list:
        print("[远端] ⚠️ 一个都没配。先做 docs/SYNC.md 的「首次配置」。")
        return
    print("[远端]")
    for r in remotes_list:
        # 只读探测：能连上才显示领先/落后，连不上不算错误
        rc, out, _ = git("rev-list", "--left-right", "--count", f"{r['name']}/{br}...{br}", timeout=30)
        ahead = ""
        if rc == 0 and out:
            parts = out.split()
            if len(parts) == 2:
                behind, ahead_n = parts[0], parts[1]
                ahead = f"  落后 {behind} / 领先 {ahead_n}"
        print(f"   - {r['name']}: {r['url']}{ahead}")
    print(f"[拉取来源] {pick_pull_remote([r['name'] for r in remotes_list], forced) or '—'}")


def do_pull(remotes_list, forced=None):
    br, d = porcelain_status()
    if d:
        line("拒绝拉取")
        print("⚠️ 工作区有未提交改动，直接 rebase 会把它们卷进冲突里。")
        print("   先提交（收工约定：git add -A && git commit -m \"...\"）再同步。")
        print(f"   当前 {len(d)} 项未提交，例如：")
        for p in d[:5]:
            print("   " + p)
        return False
    names = [r["name"] for r in remotes_list]
    src = pick_pull_remote(names, forced)
    if not src:
        line("无法拉取")
        print("⚠️ 没有可用的远端。先做 docs/SYNC.md 的「首次配置」。")
        return False

    line(f"拉取：{src} → {br}（rebase）")
    rc, out, err = git("fetch", src, br)
    if rc != 0:
        print(f"❌ fetch 失败（{src}）：")
        print(err or out)
        print("\n提示：网络不通或凭据没配好。若是公司网连不上 GitHub，属预期，")
        print("      直接用 --remote gitee 走主力通道即可。")
        return False
    print(out or "(已是最新)")

    rc, out, err = git("rebase", f"{src}/{br}")
    if rc != 0:
        print(f"❌ rebase 冲突，已退回原状：")
        print(err or out)
        git("rebase", "--abort")
        print("\n⚠️ 冲突已中止（git rebase --abort 已执行），你的改动都在，没丢。")
        print("   两台机器都改过同一批文件时会出现这种情况——尤其 png/docx 二进制文件。")
        print("   处理办法：打开 HANDOFF 确认哪边是最新的，人工合并后再 commit 推送。")
        return False
    print(out or "(已与远端对齐)")
    return True


def do_push(remotes_list, forced=None):
    if not remotes_list:
        line("无法推送")
        print("⚠️ 没有可用的远端。先做 docs/SYNC.md 的「首次配置」。")
        return False
    targets = [r for r in remotes_list if not forced or r["name"] == forced]
    if not targets:
        line("无法推送")
        print(f"⚠️ 远端 {forced} 不存在。现有：{[r['name'] for r in remotes_list]}")
        return False
    br = branch()
    ok = []
    for r in targets:
        line(f"推送：{br} → {r['name']}（{r['url']}）")
        rc, out, err = git("push", r["name"], br, timeout=1800)
        if rc == 0:
            print(out or "(已推送)")
            print(f"✅ {r['name']} 成功")
            ok.append(r["name"])
        else:
            print(f"❌ {r['name']} 失败：")
            print(err or out)
            print("（不中断，继续尝试其他远端）")
    line("推送结果")
    for r in targets:
        print(f"   {'✅' if r['name'] in ok else '❌'} {r['name']}")
    if not ok:
        print("\n⚠️ 全部远端都没推成功。检查网络与凭据：docs/SYNC.md。")
        return False
    if len(ok) < len(targets):
        print(f"\n⚠️ 部分成功。没推上去的：{[r['name'] for r in targets if r['name'] not in ok]}")
        print("   只要有一条通了，两台机器就还能同步，不慌。")
    return True


def main():
    ap = argparse.ArgumentParser(description="阿飞说球两台机器同步")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--pull", action="store_true", help="只拉取（开工前）")
    g.add_argument("--push", action="store_true", help="只推送（收工 commit 后）")
    g.add_argument("--status", action="store_true", help="只看状态，什么都不改")
    ap.add_argument("--remote", help="只对指定远端操作，例如 gitee")
    args = ap.parse_args()

    remotes_list = remotes()
    if args.status or not (args.pull or args.push):
        show_status(remotes_list, args.remote)
        if args.status:
            return 0
        if not (args.pull or args.push):
            print("\n（没给参数 = 完整同步：先拉取再推送。加 --status 只看不动。）")
            args.pull = args.push = True

    ok = True
    if args.pull:
        ok = do_pull(remotes_list, args.remote) and ok
    if args.push:
        ok = do_push(remotes_list, args.remote) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
