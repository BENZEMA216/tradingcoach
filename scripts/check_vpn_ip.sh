#!/bin/bash
# VPN IP 检查脚本

echo "=== VPN IP 检查 ==="
echo ""

# 检查代理状态
proxy_info=$(networksetup -getwebproxy "Wi-Fi" 2>/dev/null)
enabled=$(echo "$proxy_info" | grep "Enabled:" | awk '{print $2}')
server=$(echo "$proxy_info" | grep "Server:" | awk '{print $2}')
port=$(echo "$proxy_info" | grep "Port:" | awk '{print $2}')

if [ -n "$server" ] && [ -n "$port" ]; then
    echo "代理设置: $enabled ($server:$port)"
else
    echo "代理设置: $enabled"
fi
echo ""

if [ "$enabled" = "Yes" ] && [ -n "$server" ] && [ -n "$port" ]; then
    # 测试代理连接
    echo "测试代理连接..."
    export http_proxy="http://${server}:${port}"
    export https_proxy="http://${server}:${port}"
    if curl -s --max-time 3 --proxy "http://${server}:${port}" https://ipinfo.io/json > /tmp/ipinfo.json 2>/dev/null; then
        ip=$(python3 -c "import json; d=json.load(open('/tmp/ipinfo.json')); print(d['ip'])" 2>/dev/null)
        country=$(python3 -c "import json; d=json.load(open('/tmp/ipinfo.json')); print(d['country'])" 2>/dev/null)
        city=$(python3 -c "import json; d=json.load(open('/tmp/ipinfo.json')); print(d['city'])" 2>/dev/null)
        
        echo "✓ 代理连接成功"
        echo "IP: $ip"
        echo "位置: $city, $country"
        
        if [ "$country" = "JP" ]; then
            echo "✅ 已连接到日本！"
        else
            echo "❌ 当前不在日本（$country）"
        fi
    else
        echo "✗ 代理连接失败"
        echo "请检查 VPN 客户端是否已启动代理服务"
    fi
else
    echo "系统代理未启用"
fi
