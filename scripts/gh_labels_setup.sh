#!/usr/bin/env bash
# 本仓 issue tracker 的标签一次性建齐（幂等）。
#
#   bash scripts/gh_labels_setup.sh
#   REPO=owner/name bash scripts/gh_labels_setup.sh      # 换仓库
#
# 为什么要有这个脚本：triage / wayfinder 这些技能按字符串打标签，标签没建好
# 它们会静默建出同义不同名的重复标签。建一次，之后跑几遍都只更新不新增。
set -euo pipefail

REPO="${REPO:-AfeiX95/afei-football}"

# gh 可能在 PATH 里也可能只在安装目录（winget 装完当前终端不会刷新 PATH）
gh_bin() {
  local c
  if command -v gh >/dev/null 2>&1; then command -v gh; return 0; fi
  for c in \
    "/c/Program Files/GitHub CLI/gh.exe" \
    "/c/Program Files (x86)/GitHub CLI/gh.exe" \
    "${LOCALAPPDATA:-/nonexistent}/GitHubCLI/bin/gh.exe"; do
    if [ -x "$c" ]; then printf '%s' "$c"; return 0; fi
  done
  return 1
}

if ! GH="$(gh_bin)"; then
  printf '✗ 没找到 gh。先跑：bash scripts/wizard_gh_setup.sh\n' >&2
  exit 1
fi

if ! "$GH" auth status >/dev/null 2>&1; then
  printf '✗ gh 还没登录。先跑：bash scripts/wizard_gh_setup.sh（第 4 阶段是登录）\n' >&2
  exit 1
fi

# 名字|颜色|描述   —— 名字里不许有空格；颜色不带 #
LABELS=(
  "needs-triage|d4c5f9|维护者需要先评估这条"
  "needs-info|fbca04|等提问方补信息"
  "ready-for-agent|0e8a16|已写全，AFK agent 可直接接手"
  "ready-for-human|1d76db|需要人来实现"
  "wontfix|6a737d|不做"
  "wayfinder:map|5319e7|wayfinder 地图：这张是索引，不是票"
  "wayfinder:research|0969da|读文档/API/本地知识库就能定案（AFK）"
  "wayfinder:prototype|d93f0b|做便宜粗糙的实物把讨论抬高一档（HITL）"
  "wayfinder:grilling|bc4c00|靠对话定案，默认情形（HITL）"
  "wayfinder:task|333333|决策前必须先干完的手工活"
)

printf '\n  仓库：%s\n  标签：%d 枚\n\n' "$REPO" "${#LABELS[@]}"

ok=0
for row in "${LABELS[@]}"; do
  IFS='|' read -r name color desc <<<"$row"
  if "$GH" label create "$name" --repo "$REPO" --color "$color" --description "$desc" --force >/dev/null 2>&1; then
    printf '  ✓ %s\n' "$name"
    ok=$((ok + 1))
  else
    printf '  ✗ %s（建失败，可能没权限）\n' "$name" >&2
  fi
done

printf '\n  建好 %d/%d\n\n' "$ok" "${#LABELS[@]}"

# 复核：列一遍仓库现有标签，把上面十枚标出来
printf '  复核（repos/%s 现有标签）：\n' "$REPO"
existing="$("$GH" label list --repo "$REPO" --limit 100 2>/dev/null || true)"
missing=0
for row in "${LABELS[@]}"; do
  name="${row%%|*}"
  if printf '%s\n' "$existing" | grep -qx -- "$name"; then
    printf '    ✓ %s\n' "$name"
  else
    printf '    ✗ %s 缺失\n' "$name"
    missing=$((missing + 1))
  fi
done
[ "$missing" -eq 0 ] && printf '\n  十枚齐全。\n\n' || printf '\n  还缺 %d 枚，见上。\n\n' "$missing"
