#!/bin/bash
# =============================================================================
# 阿飞说球 MCP Server 启动脚本
# L7: Agentic OS — 对外提供标准MCP接口
# =============================================================================
# 启动方式: bash mcp-server-start.sh
# 连接方式: 其他Agent通过 hermes mcp add afc-football --url http://localhost:8123/mcp
# =============================================================================

MCP_PORT=${MCP_PORT:-8123}
WORKDIR="I:/阿飞说球"

echo "=========================================="
echo "  阿飞·赛博聊球 — MCP Server"
echo "  Port: $MCP_PORT"
echo "  Workdir: $WORKDIR"
echo "=========================================="

# 启动 Hermes MCP Server
# --skills 预加载足球分析技能
# 其他Agent可通过配置 mcp_servers 连接到本服务
hermes mcp serve \
  --verbose

echo "MCP Server 已停止"
