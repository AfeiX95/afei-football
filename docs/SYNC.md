# 两台机器同步（家里 PC ↔ 公司 PC）

> 2026-10-07 建立。**日常只需要一条命令：`python scripts/sync.py`**（开工前跑一次，收工 commit 后再跑一次）。

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

## 公司 PC：一次性配置（⚠️ 那份是手工拷过去的文件夹，没有 git 历史）

🔴 **不要**在旧文件夹里 `git init` 再硬推，两份独立历史会打架，而且拷进去的文件可能覆盖新版本。
正确做法是**先抢救独有改动，再重新克隆**：

```bash
# ① 先把公司 PC 上那份独有、家里没有的改动拷出来（人工比对！）
#    这段时间项目主要在推进，但只要有你在公司临时记的东西，先挑出来，
#    可以顺手做一次进度同步提交，避免克隆后被覆盖。

# ② 旧文件夹改名留底（别急着删，确认无误再删）
#    D:\阿飞说球  →  D:\阿飞说球_旧_20261007

# ③ 重新克隆（走 Gitee，国内快）
git clone git@gitee.com:wuyanzu1112324/afei-football.git 阿飞说球

# ④ 验证
cd 阿飞说球
python scripts/brief.py        # 能跑出简报就对了
python scripts/sync.py --status
```

公钥：如果公司 PC 是另一台机器，重新生成一把再贴到 Gitee（`ssh-keygen -t ed25519 -C "公司PC"`），
或者把 `~/.ssh/id_ed25519`（+ `.pub`）拷过去。**别把私钥提交进仓库。**

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
