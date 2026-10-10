# 两台机器同步（家里 PC ↔ 公司 PC）

> 2026-10-07 建立。**日常只需要一条命令：`python scripts/sync.py`**（开工前跑一次，收工 commit 后再跑一次）。
> 🔴 **2026-10-11 架构变了**：Gitee 上那棵是**公司 PC 自己的历史**，已 `merge --allow-unrelated-histories` 并进本仓，
> 公司工程整体搬进 `公司机_工程/`。**公司 PC 不要重新克隆，直接 pull** —— 细节见下面「2026-10-11」与「公司 PC：pull 之后」两节。

## 为什么会有这份文档

原来的 `origin` 指向 GitHub（`git@github.com:AfeiX95/afei-football.git`），但那条线**2026-06-21 之后就停了**：
GitHub 上停在 `88a47c5`，本地领先 **227 个提交**，而且这台机器的 `.git/FETCH_HEAD` 从来不存在（没 fetch 过）。
也就是说三个半月的成果只躺在一台机器上。现在补上 Gitee 作为**主力同步通道**，GitHub 留作异地备份。

## 现在的架构

| 远端名 | 地址 | 角色 | 说明 |
|:--|:--|:--|:--|
| `gitee` | `git@gitee.com:wuyanzu1112324/afei-football.git` | **主力同步** | 国内可达，两台机器靠它对齐 |
| `origin` | `git@github.com:AfeiX95/afei-football.git` | 异地备份 | 公司网络可能连不上，连不上不影响同步 |

- **拉取只用 `gitee`**（单一来源，否则多镜像 rebase 会产生重复提交）。
- **推送两个都推**，某个推不动不阻塞另一个。
- 分支：`master`。仓库规模：1193 个文件 / 工作区 ~59MB / `.git` ~70MB（Gitee 免费额度够用）。

## 本机（家里 PC）现状：✅ 已配好

```bash
git remote -v
# gitee   git@gitee.com:wuyanzu1112324/afei-football.git
# origin  git@github.com:AfeiX95/afei-football.git
python scripts/sync.py --status
```

SSH 公钥（`~/.ssh/id_ed25519`，指纹 `SHA256:zX7JkobNkBNNa3xEHS0Ig9F+F6hS7wtuarJ8fMdICqA`）已注册到
GitHub 与 Gitee。Gitee 后台：设置 → 安全设置 → **SSH 公钥**。

## 2026-10-11：公司那棵历史并进来了（架构变了）

**发生了什么**：Gitee 的 `gitee/master` 不是空仓库，它是**公司 PC 那条独立历史**
（101 个提交 / 2026-08-22 → 2026-10-09 / 作者 `afei`），与本机这条（2026-06-21 起）**没有共同祖先**。
用 `git merge --allow-unrelated-histories` 把两条并入同一个 `master`，随后把公司工程的根层 19 项
**整体搬进 `公司机_工程/`** 子目录（`git mv`，rename 保留历史）。

| 位置 | 谁的 | 说明 |
|:--|:--|:--|
| 仓库根（`docs/` `state/` `scripts/` `📚知识库/` `📝文章/` …） | **家里 PC** | 原来这套工作流（brief.py / preflight.py / HANDOFF / state） |
| `公司机_工程/`（`00_引擎/` `阿飞说球/` `run.ps1` `发布前检查.cmd` …） | **公司 PC** | AFEI 引擎 monorepo，自带 `AGENTS.md` / `.hermes.md` / `.gitignore` / `.gitattributes`，只在该子树生效 |

- 两条历史都**完整保留**（公司那 101 个提交一个没丢），`gitee/master` 现在是 `master` 的**祖先** → 以后推送是 fast-forward，**不需要 force**
- 合并提交 `c9de611`，搬迁提交 `f3dfd80`
- 相关提交：`948aab9`（公司 PC 最后一个提交）也在这条线上，所以公司 PC 能直接 pull

## 公司 PC：pull 之后必须做的两件事（⚠️ 别重新克隆）

公司 PC 那份**有 git 历史**（不是手工拷的文件夹）→ **不要重新 clone**：
`*.docx`、`采集数据/*.js|*.json`、`阿飞说球/03_参考资料/kb_models/`、`公司机_工程/阿飞说球/04_赛事文章/**/charts/`
这些都是 `.gitignore` 里的**未跟踪资产，克隆拿不回来**。
（先确认：在旧文件夹里 `git rev-parse --is-inside-work-tree`；若真不是 git 仓库，才退回「拷出独有文件 → 重新克隆」的老办法。）

```bash
# ① 拉（公司工程的文件会被 git 整体改名到 公司机_工程/ 下面）
python scripts/sync.py --pull     # 或 git fetch gitee && git merge --ff-only gitee/master

# ② 把被 git 忽略、留在原地的文件也挪进新位置（git 只搬「已跟踪」的文件）
#    在公司 PC 的仓库根跑（robocopy /E 合并目录，/MOVE 搬完删空壳）
foreach ($d in @("00_引擎","01_数据采集","02_可视化","采集数据","阿飞说球")) {
  if (Test-Path $d) { robocopy $d "公司机_工程\$d" /E /MOVE /NFL /NDL /NJH /NJS }
}

# ③ 验证
cd 公司机_工程
.\发布前检查.cmd                      # 或 python 阿飞说球\02_工具\gate.py <稿件.md>
```

- 公司 PC 上的桌面快捷方式 / 自定路径要**重新指到 `公司机_工程\`**（`运行.cmd`、`发布前检查.cmd`、`run.ps1` 随目录一起搬走了）
- 公司工程内部脚本用 `__file__` 自解析仓库根，整体下移一层**依然能跑**（2026-09-20 迁移时已改好）
- 公司 PC 的 `core.autocrlf=false` / `core.eol=lf` 不用改；`.gitattributes(* text=auto eol=lf)` 已随工程搬进 `公司机_工程/`
- 公钥：公司 PC 若换过机器，重新生成一把贴到 Gitee（`ssh-keygen -t ed25519 -C "公司PC"`）。
  **别把私钥提交进仓库。**

## 日常用法

```bash
# 开工前：把另一台机器的提交拉下来（rebase 保持线性历史）
python scripts/sync.py --pull

# …干活…收工按 AGENTS.md 提交…
git add -A && git commit -m "进度同步 YYYYMMDD：..."

# 收工后：推送到全部远端
python scripts/sync.py --push

# 不确定现在什么状态（只看不动，最安全）
python scripts/sync.py --status

# 完整同步 = 先拉后推（等于 --pull 然后 --push）
python scripts/sync.py
```

## 冲突与故障

| 情况 | 脚本的行为 | 你该做什么 |
|:--|:--|:--|
| 有未提交改动就拉取 | **拒绝**并列出未提交文件 | 先 `git add -A && git commit`，再拉 |
| rebase 撞冲突 | **自动 `git rebase --abort` 退回原状**，你的改动不丢 | 看 HANDOFF 判断哪边最新，人工合并后再提交 |
| GitHub 连不上 | 记录 ❌ 但**继续**推 Gitee，整体不算失败 | 不管它，Gitee 通了就能同步 |
| 全部远端都推不动 | 退出码 1 | 查网络与凭据；`ssh -T git@gitee.com` 看公钥是否还有效 |
| `couldn't create signal pipe, Win32 error 5` | —— | 这是 **DSH 沙箱**禁子进程建命名管道，不是网络问题。让 agent 提权跑，或自己在终端里跑 |

### 为什么脚本不自动解决冲突

本仓库有 png / docx 等**二进制文件**（`assets/charts/`、`📝文章/`），git 无法自动合并它们。
任何"自动挑一边"的策略都会静默丢文件，所以撞冲突一律中止，把决定权交回人。

## 两台机器同时改同一个文件？

AGENTS.md 已有约定：**先读后写**。跨机同步后这条更重要 —— 开工前 `sync.py --pull`，
发现某文件比记忆中新（另一台机器刚写的）就先重读合并，**严禁整文件覆盖**。
