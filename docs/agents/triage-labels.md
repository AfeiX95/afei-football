# Triage Labels

技能以「五个 triage 角色」说话；这张表把角色映射到本仓 issue tracker 里**真实存在**的标签字符串。

| Label in mattpocock/skills | Label in our tracker | Meaning |
| --- | --- | --- |
| `needs-triage` | `needs-triage` | 维护者需要先评估这条 |
| `needs-info` | `needs-info` | 等提问方补信息 |
| `ready-for-agent` | `ready-for-agent` | 已写全，AFK agent 可直接接手 |
| `ready-for-human` | `ready-for-human` | 需要人来实现 |
| `wontfix` | `wontfix` | 不做 |

技能提到某个角色时（例如「打上 AFK-ready 的 triage 标签」），用右列那个字符串。

## wayfinder 标签（建图与派票）

`wayfinder` 技能把大块工作拆成一张 map + 若干 child ticket，靠以下五枚标签区分：

| 标签 | 打在哪 | 含义 |
| --- | --- | --- |
| `wayfinder:map` | map 本身那一张 issue | 这张是地图（索引），不是票 |
| `wayfinder:research` | child ticket | 读文档 / 三方 API / 本地知识库就能定案（AFK） |
| `wayfinder:prototype` | child ticket | 做便宜粗糙的实物把讨论抬高一档（HITL） |
| `wayfinder:grilling` | child ticket | 靠对话定案，默认情形（HITL） |
| `wayfinder:task` | child ticket | 决策前必须先干完的手工活，本身没什么可决定的 |

票的阻塞关系用 GitHub 原生依赖（不是标签）；票由驱动这张 map 的人**先认领再动手**。

## 不额外强加标签

除上面十枚之外，**不强制**任何标签。要加就按技能规则临时加，别预先塞一堆没人用的。

## 建标签

```bash
bash scripts/gh_labels_setup.sh        # 幂等，10 枚全建（已存在则更新颜色/描述）
```
