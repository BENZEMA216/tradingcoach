#!/bin/bash
echo "=== VPN 状态检查 ==="
echo ""
echo "1. VPN 客户端进程:"
ps aux | grep -iE "vpn|clash|橘子" | grep -v grep | head -2 || echo "   未找到"
echo ""
echo "2. 系统代理设置:"
networksetup -getwebproxy "Wi-Fi" 2>/dev/null | grep -E "Enabled|Server|Port"
echo ""
echo "3. 代理端口测试:"
for port in 17890 7890 1080 1087; do
    if nc -z -v 127.0.0.1 $port 2>&1 | grep -q "succeeded"; then
        echo "   ✓ 端口 $port 可用"
    fi
done
echo ""
echo "4. 当前 IP:"
curl -s --max-time 5 https://ipinfo.io/json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"   IP: {d['ip']} ({d['city']}, {d['country']})\")" 2>/dev/null || echo "   无法获取"
echo ""
echo "=== 检查完成 ==="
