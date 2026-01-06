#!/bin/bash
# Gemini 模型问题深度诊断脚本

echo "=== Gemini 模型问题深度诊断 ==="
echo ""

CURSOR_SETTINGS="$HOME/Library/Application Support/Cursor/User/settings.json"

# 1. 检查当前配置
echo "1. 当前 Cursor 配置:"
if [ -f "$CURSOR_SETTINGS" ]; then
    cat "$CURSOR_SETTINGS" | python3 -m json.tool 2>/dev/null || cat "$CURSOR_SETTINGS"
else
    echo "   ✗ 设置文件不存在"
fi

echo ""
echo "2. 测试代理连接 Google API:"
echo "   测试 generativelanguage.googleapis.com..."
RESPONSE=$(curl -s --max-time 5 --proxy http://127.0.0.1:17890 -I https://generativelanguage.googleapis.com 2>&1 | head -5)
if echo "$RESPONSE" | grep -q "HTTP"; then
    echo "   ✓ 可以连接到 Google API"
    echo "$RESPONSE" | head -3
else
    echo "   ✗ 无法连接到 Google API"
    echo "   响应: $RESPONSE"
fi

echo ""
echo "3. 检查代理类型:"
HTTP_PROXY=$(networksetup -getwebproxy "Wi-Fi" 2>/dev/null | grep "Enabled:" | awk '{print $2}')
SOCKS_PROXY=$(networksetup -getsocksfirewallproxy "Wi-Fi" 2>/dev/null | grep "Enabled:" | awk '{print $2}')
echo "   HTTP 代理: $HTTP_PROXY"
echo "   SOCKS 代理: $SOCKS_PROXY"

echo ""
echo "4. 检查 Cursor 进程:"
CURSOR_PID=$(ps aux | grep -i "Cursor" | grep -v grep | head -1 | awk '{print $2}')
if [ -n "$CURSOR_PID" ]; then
    echo "   ✓ Cursor 正在运行 (PID: $CURSOR_PID)"
    echo "   检查 Cursor 的网络连接..."
    lsof -p "$CURSOR_PID" 2>/dev/null | grep -i "17890" | head -3 || echo "   ⚠ 未发现 Cursor 使用代理端口 17890"
else
    echo "   ✗ Cursor 未运行"
fi

echo ""
echo "=== 诊断完成 ==="
echo ""









