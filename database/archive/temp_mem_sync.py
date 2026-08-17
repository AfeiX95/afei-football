# -*- coding: utf-8 -*-
import io, datetime

path = "I:\\阿飞说球\\\U0001F4DA知识库\\系统架构\\工作记忆.md"
with io.open(path, encoding="utf-8-sig") as f:
    text = f.read()

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

old_header = "> 最后更新：2026-08-07 00:47"
assert old_header in text, "header not found"
text = text.replace(old_header, "> 最后更新：" + now, 1)

new_section = """### 8.8 日职揭幕两场前瞻 docx 版（会话:019fcdba | 2026-08-07 01:02）
1. 交付：`\U0001F4DD文章/20260807/日职揭幕两场赛事前瞻.docx`（约538KB，两场各4张图表）+ `_preview.pdf`（8页）；图表在 `charts/mp/`（m1/m2 各 radar/bar/pie/signals）
2. 场次：横滨水手vs鹿岛鹿角（18:25）+ 大阪钢巴vs浦和红钻（18:30，周五002，竞彩网数据）
3. 结论：横滨场平局第一（约35%）、横滨不败约67%、鹿岛受让、小球；钢巴场浦和客胜+平局双选、比分1-1/0-1/1-0、浦和受让、小球（钢巴主场对浦和近10场1胜2平7负 + 8-11亚冠精英附加赛分心）
4. 合规：禁用词0、时间锚点0、粗体4处（≤5）、破折号0、表格4、段落70、约2402字；免责声明用「远离赌博」新偏好；数据来源一行
5. 关键决策：模型结论沿用分析阶段不重跑；生成/检查脚本保留防改稿；预览PDF逐页核对排版正常

---

"""

marker = "## 九、会话快照历史（追加式，最新在末尾）"
assert marker in text
text = text.replace(marker, new_section + marker, 1)

snapshot = """### 快照 #4 ｜ 会话:019fcdba ｜ 2026-08-07 01:02

**当前状态**
- 日职揭幕两场前瞻 docx 版交付完成（图文+去AI），合规体检通过，预览PDF已逐页核对排版正常
- 文件：\U0001F4DD文章/20260807/日职揭幕两场赛事前瞻.docx（横滨水手vs鹿岛鹿角 + 大阪钢巴vs浦和红钻）

**已知阻碍**
- 旧稿《瑞典超两场》带「今晚」时间锚点，未改时效不能发
- C21/C22/C23 新规则仅1-2场验证，置信度低-中

**下一步目标**
- 08-07 18:25 / 18:30 开球前发布两场前瞻
- 赛果出来后跑赛后校验，重点验证 C21-C23 与日职揭幕战模型
"""

if not text.rstrip().endswith(snapshot.rstrip()):
    text = text.rstrip() + "\n\n" + snapshot + "\n"

with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
    f.write(text)

print("done")
