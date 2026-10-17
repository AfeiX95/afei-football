"""
AFEI v3.0 Final Output Generator
把Fusion Engine的输出转成用户可读的预测结果。
"""

import json, os


def generate(fusion_result, match_name="", top_scores=None):
    """
    生成最终预测输出。
    fusion_result: Fusion Engine的输出dict
    top_scores: Model Engine的Top3比分列表
    """
    pred = fusion_result["prediction"]
    scores = fusion_result["scores"]
    confidence = fusion_result["confidence"]
    risks = fusion_result["risks"]

    lines = []
    lines.append(f"# {match_name} — 比赛预测")
    lines.append("")
    lines.append(f"> **一句话穿透：** {_one_liner(pred, fusion_result)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 模型概率")
    lines.append(f"")
    lines.append(f"| 结果 | 概率 |")
    lines.append(f"|:-----|:----:|")
    lines.append(f"| 主胜 | **{pred['home_pct']}%** |")
    lines.append(f"| 平局 | **{pred['draw_pct']}%** |")
    lines.append(f"| 客胜 | **{pred['away_pct']}%** |")
    lines.append(f"")
    lines.append(f"> 置信度：**{confidence:.0%}**")

    if top_scores:
        lines.append("")
        lines.append("## 推荐比分")
        lines.append(f"主推 **{top_scores[0]}** / 次选 {top_scores[1]} / 冷门 {top_scores[2]}")

    lines.append("")
    lines.append("## 评分明细")
    lines.append(f"| 维度 | 评分 | 权重 |")
    lines.append(f"|:-----|:----:|:----:|")
    weights = fusion_result.get("_weights", {})
    for k, v in scores.items():
        w = weights.get({"model": "model", "analysis": "analysis", "market": "market", "intel": "info"}.get(k, k), 0)
        lines.append(f"| {k} | {v} | {w:.0%} |")
    lines.append(f"")
    lines.append(f"综合评分：**{fusion_result['final_score']}**")

    if risks:
        lines.append("")
        lines.append("## ⚠️ 风险提示")
        risk_map = {
            "market_overheat": "市场热度偏高，存在过热风险",
            "limited_data": "数据有限（资格赛/次级联赛），预测置信度打折",
            "low_data_confidence": "数据可信度低，结果仅供参考",
            "highly_balanced": "三向概率接近，比赛结果高度不确定"
        }
        for r in risks:
            desc = risk_map.get(r, r)
            lines.append(f"- {desc}")

    lines.append("")
    lines.append("---")
    lines.append("*仅供参考。足球结果存在偶然性。*")

    return "\n".join(lines)


def _one_liner(pred, fr):
    """一句话穿透比赛本质"""
    h, d, a = pred["home_pct"], pred["draw_pct"], pred["away_pct"]
    max_p = max(h, d, a)
    if max_p - min(h, d, a) < 10:
        return "三向概率接近，谁赢都不意外"
    if h == max_p:
        return f"主队略占优势（{h:.0f}%），但不确定因素较多"
    if a == max_p:
        return f"客队略占优势（{a:.0f}%），主场未必稳"
    return "平局概率不可忽视"


def generate_to_file(fusion_json_path, match_name="", top_scores=None):
    with open(fusion_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    output = generate(data, match_name, top_scores)
    base = os.path.splitext(fusion_json_path)[0]
    out_path = f"{base}_report.md"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"✅ 报告输出: {out_path}")
    return output


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        generate_to_file(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
    else:
        # 测试
        test = {
            "prediction": {"home_pct": 38.0, "draw_pct": 30.0, "away_pct": 32.0},
            "scores": {"model": 51, "analysis": 53, "market": 43, "intel": 55},
            "final_score": 52.3,
            "confidence": 0.85,
            "risks": [],
            "_weights": {"model": 0.35, "analysis": 0.30, "market": 0.20, "info": 0.15}
        }
        print(generate(test, "法国 vs 西班牙", ["1-1", "1-0", "0-0"]))
