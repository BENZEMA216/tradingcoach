#!/bin/bash
# 使用代理环境变量启动 Cursor

echo "=== 使用代理启动 Cursor ==="
echo ""

# 检查代理端口
PROXY_PORT=17890
if ! nc -z 127.0.0.1 $PROXY_PORT 2>/dev/null; then
    echo "✗ 代理端口 $PROXY_PORT 不可用"
    echo "请先启动 VPN 客户端"
    exit 1
fi

echo "✓ 代理端口 $PROXY_PORT 可用"
echo ""

# 设置代理环境变量
export http_proxy="http://127.0.0.1:$PROXY_PORT"
export https_proxy="http://127.0.0.1:$PROXY_PORT"
export HTTP_PROXY="http://127.0.0.1:$PROXY_PORT"
export HTTPS_PROXY="http://127.0.0.1:$PROXY_PORT"
export NO_PROXY="localhost,127.0.0.1"

echo "已设置代理环境变量:"
echo "  http_proxy=$http_proxy"
echo "  https_proxy=$https_proxy"
echo ""

# 检查当前 IP
echo "验证代理连接..."
CURRENT_IP=$(curl -s --max-time 5 --proxy "$http_proxy" https://ipinfo.io/json 2>/dev/null)
if [ -n "$CURRENT_IP" ]; then
    COUNTRY=$(echo "$CURRENT_IP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['country'])" 2>/dev/null)
    CITY=$(echo "$CURRENT_IP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['city'])" 2>/dev/null)
    echo "✓ 代理连接正常"
    echo "  当前位置: $CITY, $COUNTRY"
else
    echo "⚠ 无法验证代理连接，但继续启动 Cursor"
fi

echo ""
echo "正在启动 Cursor..."
echo ""

# 启动 Cursor（保持环境变量）
open -a Cursor

echo "✓ Cursor 已启动"
echo ""
echo "提示："
echo "- 如果 Cursor 已经在运行，请先完全退出（Cmd + Q）"
echo "- 然后重新运行此脚本启动 Cursor"
echo "- 使用此方式启动的 Cursor 会使用代理环境变量"
echo ""









