# Issue tracker: GitHub

Issues and PRDs for this repo live as **GitHub Issues** on `AfeiX95/afei-football`（`origin` 远端）。
所有操作走 `gh` CLI。

## 先解决一件事：本仓有两个远端

```
gitee   git@gitee.com:wuyanzu1112324/afei-football.git   ← 主力同步（拉取只用它）
origin  git@github.com:AfeiX95/afei-football.git          ← 异地备份 + issue tracker
```

`gh` 在「一个仓多个远端」时会拒绝自动推断仓库，所以**第一次用之前先固定一次**：

```bash
gh repo set-default AfeiX95/afei-football
```

固定之后所有 `gh issue *` 都自动落到 GitHub 上，不用每次带 `-R`。若在别的机器（公司 PC）上跑，同样先执行这一句。
**不要**把 issue 写到 gitee —— 那边只同步代码，没有 issue tracker。

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`。多行正文用 heredoc（`--body-file -` 配 heredoc 更稳，避免 PowerShell 吞引号）。
- **Read an issue**: `gh issue view <number> --comments --json number,title,body,labels,comments`
- **List issues**: `gh issue list --state open --json number,title,body,labels --jq '[.[] | {number, title, body, labels: [.labels[].name]}]'`，配合 `--label` / `--state` 过滤。
- **Comment**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

## 标签词汇

见 `docs/agents/triage-labels.md`（triage 五角色 + wayfinder 五枚）。标签用
`bash scripts/gh_labels_setup.sh` 一次性建齐，幂等（`gh label create --force`）。

## When a skill says "publish to the issue tracker"

建一个 GitHub issue。

## When a skill says "fetch the relevant ticket"

`gh issue view <number> --comments`。
