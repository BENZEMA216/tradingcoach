#!/bin/bash
# Gemini 模型访问修复脚本

echo "=== Gemini 模型访问修复指南 ==="
echo ""

# 检查当前状态
echo "1. 检查 VPN 连接状态..."
CURRENT_IP=$(curl -s --max-time 5 https://ipinfo.io/json 2>/dev/null)
if [ -n "$CURRENT_IP" ]; then
    COUNTRY=$(echo "$CURRENT_IP" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['country'])" 2>/dev/null)
    if [ "$COUNTRY" = "CN" ]; then
        echo "   ✗ 当前 IP 仍在中国，请检查 VPN 连接"
        exit 1
    else
        echo "   ✓ VPN 已连接，当前区域: $COUNTRY"
    fi
else
    echo "   ✗ 无法检查 IP，请检查网络连接"
    exit 1
fi

echo ""
echo "2. 检查 Cursor 代理配置..."
CURSOR_SETTINGS="$HOME/Library/Application Support/Cursor/User/settings.json"

if [ ! -f "$CURSOR_SETTINGS" ]; then
    echo "   ✗ Cursor 设置文件不存在，正在创建..."
    mkdir -p "$(dirname "$CURSOR_SETTINGS")"
    echo '{}' > "$CURSOR_SETTINGS"
fi

# 检查并添加代理配置
HAS_PROXY=$(grep -q "http.proxy" "$CURSOR_SETTINGS" && echo "yes" || echo "no")

if [ "$HAS_PROXY" = "no" ]; then
    echo "   ✗ 未找到代理配置，正在添加..."
    
    # 使用 Python 来安全地更新 JSON
    python3 << EOF
import json
import os

settings_path = os.path.expanduser("$CURSOR_SETTINGS")

try:
    with open(settings_path, 'r') as f:
        settings = json.load(f)
except:
    settings = {}

settings["http.proxy"] = "http://127.0.0.1:17890"
settings["http.proxySupport"] = "on"
settings["http.proxyStrictSSL"] = False

with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=4)

print("   ✓ 代理配置已添加")
EOF
else
    echo "   ✓ 代理配置已存在"
fi

echo ""
echo "3. 检查系统代理..."
PROXY_ENABLED=$(networksetup -getwebproxy "Wi-Fi" 2>/dev/null | grep "Enabled:" | awk '{print $2}')
if [ "$PROXY_ENABLED" = "Yes" ]; then
    echo "   ✓ 系统代理已启用"
else
    echo "   ✗ 系统代理未启用"
    echo "   请在 VPN 客户端中启用系统代理"
fi

echo ""
echo "=== 修复步骤完成 ==="
echo ""
echo "📋 接下来请执行以下操作："
echo ""
echo "1. 完全退出 Cursor："
echo "   - 按 Cmd + Q 退出 Cursor"
echo "   - 确认 Cursor 已完全关闭（检查 Dock 或活动监视器）"
echo ""
echo "2. 检查 VPN 规则："
echo "   - 打开您的 VPN 客户端（橘子加速/Clash）"
echo "   - 确保以下域名走代理："
echo "     • *.googleapis.com"
echo "     • *.google.com"
echo "     • generativelanguage.googleapis.com"
echo "     • *.cursor.sh"
echo "   - 如果规则模式不工作，尝试切换到'全局代理'模式"
echo ""
echo "3. 重新启动 Cursor："
echo "   - 等待 5-10 秒后重新打开 Cursor"
echo "   - 尝试切换到 Gemini 模型"
echo ""
echo "4. 如果仍然不行："
echo "   - 访问 https://cursor.com/account/regions 检查账户设置"
echo "   - 尝试切换到其他 VPN 节点（如美国、欧洲）"
echo "   - 检查 Cursor 的开发者工具（Help > Toggle Developer Tools）查看错误信息"
echo ""











