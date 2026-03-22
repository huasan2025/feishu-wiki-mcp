#!/bin/bash
# 飞书 MCP 启动包装脚本 / Feishu MCP startup wrapper
#
# 职责 / Responsibilities:
#   1. 调用 feishu_auth.py 刷新 token（如果 refresh_token 还有效则静默完成）
#      Refresh token via feishu_auth.py (silent if refresh_token is still valid)
#   2. 读取最新 UAT，启动 lark-mcp stdio server
#      Read latest UAT and start lark-mcp stdio server
#
# 环境变量 / Environment variables:
#   LARK_APP_ID      - 飞书 App ID / Feishu App ID
#   LARK_APP_SECRET  - 飞书 App Secret / Feishu App Secret

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOKENS_FILE="$SCRIPT_DIR/tokens.json"
AUTH_SCRIPT="$SCRIPT_DIR/feishu_auth.py"

# 刷新 token / Refresh token
python3 "$AUTH_SCRIPT" 2>/dev/null

# 读取 UAT / Read UAT
UAT=$(python3 -c "
import json, sys
try:
    d = json.load(open('$TOKENS_FILE'))
    t = d.get('access_token', '')
    if not t:
        sys.exit(1)
    print(t)
except Exception:
    sys.exit(1)
" 2>/dev/null)

if [ -z "$UAT" ]; then
    echo "Error: No valid access_token in $TOKENS_FILE" >&2
    echo "Please run: python3 $AUTH_SCRIPT" >&2
    exit 1
fi

# 启动 lark-mcp / Start lark-mcp
exec npx -y @larksuiteoapi/lark-mcp mcp \
    -a "${LARK_APP_ID}" \
    -s "${LARK_APP_SECRET}" \
    -u "$UAT"
