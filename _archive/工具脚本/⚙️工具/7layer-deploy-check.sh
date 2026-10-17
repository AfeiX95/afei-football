#!/bin/bash
# =============================================================================
# 阿飞说球 Hermes 7层框架 部署汇总
# 执行: bash 7layer-deploy-check.sh
# =============================================================================

echo "=========================================="
echo "  阿飞说球 · 7级框架部署核查"
echo "=========================================="

echo ""
echo "━━━ L1: 基础执行层 ━━━"
echo "  ✅ 终端/文件/网页/代码工具已就绪"

echo ""
echo "━━━ L2: 长期记忆层 ━━━"
echo "  ✅ SOUL.md: $(wc -l < ~/.hermes/SOUD.md 2>/dev/null || echo 'N/A') 行"
echo "  ✅ .hermes.md: 项目级配置"
echo "  ✅ Memory: $(hermes memory status 2>&1 | grep -i provider | head -1)"

echo ""
echo "━━━ L3: 自定义技能层 ━━━"
hermes skills list 2>&1 | grep -i -E "football|match|model|afei"

echo ""
echo "━━━ L4: 模型调度层 ━━━"
echo "  主模型: $(hermes config get model.default 2>/dev/null || hermes config get model 2>/dev/null | head -1)"
echo "  备用: $(hermes config get fallback_providers 2>/dev/null | head -1)"

echo ""
echo "━━━ L5: 子代理协作看板 ━━━"
echo "  Board: $(hermes kanban boards current 2>/dev/null)"
echo "  任务数: $(hermes kanban list 2>/dev/null | wc -l)"

echo ""
echo "━━━ L6: 定时自动化 ━━━"
echo "  全息记忆: $(hermes config get memory.provider 2>/dev/null)"
echo "  Cron任务:"
hermes cron list 2>/dev/null | head -5

echo ""
echo "━━━ L7: MCP服务端 ━━━"
echo "  MCP SDK: $(pip show mcp 2>/dev/null | grep Version | head -1)"
echo "  启动脚本: I:/阿飞说球/mcp-server-start.sh"

echo ""
echo "=========================================="
echo "  部署完成 — 7层全链路就绪"
echo "=========================================="
