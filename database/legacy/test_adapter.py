"""
AFEI v3.0 Adapter 验收测试

测试集：4场不同类型比赛
1. 世界杯半决赛（法国vs西班牙）→ cup_knockout
2. 欧冠资格赛（杰尔vs雷克维京）→ qualifier
3. 挪超联赛（奥勒松vs莫尔德）→ normal_league
4. 瑞超（哥德堡vs索尔纳）→ normal_league
"""

import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapter_v1 import adapter_pipeline
from schema_validator import validate

# 测试集
TEST_CASES = [
    {
        "name": "法国vs西班牙（世界杯半决赛）",
        "file": "I:/阿飞说球/📚知识库/比赛分析/2026世界杯半决赛/周二101_法国VS西班牙_14维全维度分析.md",
        "expected_type": "cup_knockout"
    },
    {
        "name": "杰尔vs雷克维京（欧冠资格赛）",
        "file": "I:/阿飞说球/📚知识库/比赛分析/欧冠资格赛/周二201_杰尔VS雷克维京_14维全维度分析.md",
        "expected_type": "qualifier"
    },
    {
        "name": "奥勒松vs莫尔德（挪超）",
        "file": "I:/阿飞说球/📚知识库/比赛分析/挪超/周六207_奥勒松VS莫尔德_全维度分析.md",
        "expected_type": "normal_league"
    },
    {
        "name": "哥德堡vs索尔纳（瑞超）",
        "file": "I:/阿飞说球/📚知识库/比赛分析/瑞超/哥德堡VS索尔纳_全维度分析.md",
        "expected_type": "normal_league"
    }
]

results = {"passed": 0, "failed": 0, "warnings": []}

for case in TEST_CASES:
    name = case["name"]
    path = case["file"]
    expected = case["expected_type"]

    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"预期类型: {expected}")
    print(f"{'='*60}")

    if not os.path.exists(path):
        print(f"❌ 文件不存在: {path}")
        results["failed"] += 1
        continue

    with open(path, 'r', encoding='utf-8') as f:
        md = f.read()

    # 跑Adapter
    try:
        parsed = adapter_pipeline(md, match_id=name[:6])
    except Exception as e:
        print(f"❌ Adapter异常: {e}")
        results["failed"] += 1
        continue

    # Schema验证
    warnings = validate(parsed)

    # 保存JSON到测试输出
    out_path = f"I:/阿飞说球/database/tests/{name[:6].replace('（','_').replace('）','')}.json"
    os.makedirs("I:/阿飞说球/database/tests", exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)

    # 检查match_context类型匹配
    ctx_type = parsed.get("match_context", {}).get("match_type", "")
    type_ok = ctx_type == expected

    # 报告
    lines = [
        f"  match_type: {ctx_type} {'✅' if type_ok else '❌'}",
        f"  data_confidence: {parsed.get('match_context',{}).get('data_confidence', '?')}",
        f"  odds implied: {parsed.get('odds',{}).get('implied_prob', {})}",
        f"  form_score home: {parsed.get('performance',{}).get('home',{}).get('form_score', '?')}",
        f"  form_score away: {parsed.get('performance',{}).get('away',{}).get('form_score', '?')}",
        f"  Schema warnings: {len(warnings)}",
    ]
    for line in lines:
        print(line)

    if not type_ok:
        print(f"  -> ❌ 类型识别错误")
        results["failed"] += 1
    else:
        print(f"  -> ✅ 通过")
        results["passed"] += 1

    results["warnings"].extend([f"{name}: {w}" for w in warnings])

# 汇总
print(f"\n{'='*60}")
print(f"测试完成")
print(f"  通过: {results['passed']}/{len(TEST_CASES)}")
print(f"  失败: {results['failed']}/{len(TEST_CASES)}")
print(f"  总warnings: {len(results['warnings'])}")
if results["warnings"]:
    print(f"  前10个warnings:")
    for w in results["warnings"][:10]:
        print(f"    - {w}")
