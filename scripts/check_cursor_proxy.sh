#!/bin/bash
# Cursor 代理配置检查脚本

echo "=== Cursor 代理配置检查 ==="
echo ""

# 检查 Cursor 设置文件
CURSOR_SETTINGS="$HOME/Library/Application Support/Cursor/User/settings.json"

if [ -f "$CURSOR_SETTINGS" ]; then
    echo "1. Cursor 设置文件存在: ✓"
    echo ""
    echo "   当前代理配置:"
    
    # 检查代理设置
    if grep -q "http.proxy" "$CURSOR_SETTINGS"; then
        echo "   ✓ 找到 http.proxy 配置:"
        grep "http.proxy" "$CURSOR_SETTINGS" | head -1
    else
        echo "   ✗ 未找到 http.proxy 配置"
    fi
    
    if grep -q "http.proxySupport" "$CURSOR_SETTINGS"; then
        echo "   ✓ 找到 http.proxySupport 配置:"
        grep "http.proxySupport" "$CURSOR_SETTINGS" | head -1
    else
        echo "   ✗ 未找到 http.proxySupport 配置"
    fi
    
    if grep -q "http.proxyStrictSSL" "$CURSOR_SETTINGS"; then
        echo "   ✓ 找到 http.proxyStrictSSL 配置:"
        grep "http.proxyStrictSSL" "$CURSOR_SETTINGS" | head -1
    else
        echo "   ✗ 未找到 http.proxyStrictSSL 配置"
    fi
else
    echo "1. Cursor 设置文件不存在: ✗"
    echo "   路径: $CURSOR_SETTINGS"
fi

echo ""
echo "2. 系统代理设置:"
PROXY_INFO=$(networksetup -getwebproxy "Wi-Fi" 2>/dev/null)
ENABLED=$(echo "$PROXY_INFO" | grep "Enabled:" | awk '{print $2}')
SERVER=$(echo "$PROXY_INFO" | grep "Server:" | awk '{print $2}')
PORT=$(echo "$PROXY_INFO" | grep "Port:" | awk '{print $2}')

if [ "$ENABLED" = "Yes" ]; then
    echo "   ✓ 系统代理已启用: $SERVER:$PORT"
else
    echo "   ✗ 系统代理未启用"
fi

echo ""
echo "3. 当前 IP 位置:"
CURRENT_IP=$(curl -s --max-time 5 https://ipinfo.io/json 2>/dev/null)
if [ -n "$CURRENT_IP" ]; then
    IP=$(echo "$CURRENT_IP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['ip'])" 2>/dev/null)
    COUNTRY=$(echo "$CURRENT_IP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['country'])" 2>/dev/null)
    CITY=$(echo "$CURRENT_IP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['city'])" 2>/dev/null)
    echo "   IP: $IP"
    echo "   位置: $CITY, $COUNTRY"
    
    if [ "$COUNTRY" != "CN" ]; then
        echo "   ✓ 已连接到非中国区域"
    else
        echo "   ✗ 仍在中国的 IP"
    fi
else
    echo "   ✗ 无法获取 IP 信息"
fi

echo ""
echo "4. 建议的配置:"
echo ""
echo "   如果 Cursor 设置中没有代理配置，请添加以下内容到"
echo "   $CURSOR_SETTINGS:"
echo ""
echo "   {"
echo "       \"http.proxy\": \"http://127.0.0.1:17890\","
echo "       \"http.proxySupport\": \"on\","
echo "       \"http.proxyStrictSSL\": false"
echo "   }"
echo ""
echo "   配置后，请完全重启 Cursor (Cmd + Q 退出，然后重新打开)"
echo ""
echo "=== 检查完成 ==="











