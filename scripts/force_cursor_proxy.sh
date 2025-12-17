#!/bin/bash
# 强制 Cursor 使用代理的完整解决方案

echo "=== 强制 Cursor 使用代理 ==="
echo ""

PROXY_PORT=17890

# 1. 检查代理是否可用
if ! nc -z 127.0.0.1 $PROXY_PORT 2>/dev/null; then
    echo "✗ 代理端口 $PROXY_PORT 不可用"
    echo "请先启动 VPN 客户端"
    exit 1
fi

echo "✓ 代理端口 $PROXY_PORT 可用"
echo ""

# 2. 完全退出 Cursor
echo "正在关闭 Cursor..."
killall Cursor 2>/dev/null
sleep 2

# 检查是否还有进程
if ps aux | grep -i "Cursor" | grep -v grep > /dev/null; then
    echo "⚠ Cursor 仍在运行，强制退出..."
    killall -9 Cursor 2>/dev/null
    sleep 1
fi

echo "✓ Cursor 已完全退出"
echo ""

# 3. 更新 Cursor 设置
CURSOR_SETTINGS="$HOME/Library/Application Support/Cursor/User/settings.json"
echo "更新 Cursor 代理配置..."

python3 << 'PYTHON_SCRIPT'
import json
import os

settings_path = os.path.expanduser("~/Library/Application Support/Cursor/User/settings.json")

# 读取现有配置
try:
    with open(settings_path, 'r') as f:
        settings = json.load(f)
except:
    settings = {}

# 强制设置代理
settings["http.proxy"] = "http://127.0.0.1:17890"
settings["http.proxySupport"] = "on"
settings["http.proxyStrictSSL"] = False
settings["http.systemCertificates"] = True

# 保存配置
with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=4)

print("✓ 代理配置已更新")
PYTHON_SCRIPT

echo ""

# 4. 设置环境变量并启动 Cursor
echo "设置代理环境变量并启动 Cursor..."
echo ""

export http_proxy="http://127.0.0.1:$PROXY_PORT"
export https_proxy="http://127.0.0.1:$PROXY_PORT"
export HTTP_PROXY="http://127.0.0.1:$PROXY_PORT"
export HTTPS_PROXY="http://127.0.0.1:$PROXY_PORT"
export NO_PROXY="localhost,127.0.0.1"

# 验证代理连接
echo "验证代理连接..."
CURRENT_IP=$(curl -s --max-time 5 --proxy "$http_proxy" https://ipinfo.io/json 2>/dev/null)
if [ -n "$CURRENT_IP" ]; then
    COUNTRY=$(echo "$CURRENT_IP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['country'])" 2>/dev/null)
    echo "✓ 代理连接正常，当前区域: $COUNTRY"
else
    echo "⚠ 无法验证代理连接"
fi

echo ""
echo "正在启动 Cursor（使用代理环境变量）..."
echo ""

# 启动 Cursor（保持环境变量）
open -a Cursor

echo "✓ Cursor 已启动"
echo ""
echo "📋 重要提示："
echo ""
echo "1. 请等待 Cursor 完全启动（10-15 秒）"
echo ""
echo "2. 检查 VPN 客户端设置："
echo "   - 确保切换到'全局代理'模式"
echo "   - 确保以下域名走代理："
echo "     • *.cursor.sh"
echo "     • api3.cursor.sh"
echo "     • *.googleapis.com"
echo ""
echo "3. 测试连接："
echo "   - 在 Cursor 中打开开发者工具（Help > Toggle Developer Tools）"
echo "   - 查看 Network 标签页，确认请求通过代理"
echo ""
echo "4. 如果仍然不行："
echo "   - 尝试切换到美国或欧洲的 VPN 节点"
echo "   - 访问 https://cursor.com/account/regions 检查账户设置"
echo ""






