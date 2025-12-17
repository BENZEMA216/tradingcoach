#!/bin/bash
# Gemini 模型高级修复脚本 - 尝试多种配置方案

echo "=== Gemini 模型高级修复 ==="
echo ""

CURSOR_SETTINGS="$HOME/Library/Application Support/Cursor/User/settings.json"

# 确保设置文件存在
if [ ! -f "$CURSOR_SETTINGS" ]; then
    echo "创建 Cursor 设置文件..."
    mkdir -p "$(dirname "$CURSOR_SETTINGS")"
    echo '{}' > "$CURSOR_SETTINGS"
fi

echo "正在更新 Cursor 配置，尝试多种代理设置方案..."
echo ""

# 使用 Python 更新配置
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

# 方案 1: HTTP 代理配置（主要方案）
settings["http.proxy"] = "http://127.0.0.1:17890"
settings["http.proxySupport"] = "on"
settings["http.proxyStrictSSL"] = False

# 方案 2: 尝试 SOCKS 代理（如果 HTTP 不工作）
# 注意：某些 VPN 客户端可能同时提供 SOCKS 代理
settings["http.proxyStrictSSL"] = False

# 方案 3: 禁用 HTTP/2（某些代理可能不支持）
# 这个选项可能需要在 Cursor 的 settings.json 中手动添加
# 如果 Cursor 支持的话

# 方案 4: 确保所有网络请求都使用代理
settings["http.systemCertificates"] = True

# 保存配置
with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=4)

print("✓ 配置已更新")
print("")
print("当前配置:")
print(json.dumps(settings, indent=2))
PYTHON_SCRIPT

echo ""
echo "=== 配置更新完成 ==="
echo ""
echo "📋 重要步骤："
echo ""
echo "1. 【必须】完全退出 Cursor："
echo "   - 按 Cmd + Q 完全退出"
echo "   - 或在活动监视器中强制退出 Cursor"
echo ""
echo "2. 检查 VPN 客户端设置："
echo "   - 确保切换到'全局代理'模式（不是规则模式）"
echo "   - 确保所有流量都通过代理"
echo ""
echo "3. 等待 10 秒后重新启动 Cursor"
echo ""
echo "4. 如果仍然不行，尝试以下方法："
echo ""
echo "   方法 A: 使用环境变量启动 Cursor"
echo "   在终端中运行："
echo "   export http_proxy=http://127.0.0.1:17890"
echo "   export https_proxy=http://127.0.0.1:17890"
echo "   export HTTP_PROXY=http://127.0.0.1:17890"
echo "   export HTTPS_PROXY=http://127.0.0.1:17890"
echo "   open -a Cursor"
echo ""
echo "   方法 B: 尝试不同的 VPN 节点"
echo "   - 切换到美国节点"
echo "   - 或切换到欧洲节点"
echo ""
echo "   方法 C: 检查 Cursor 账户"
echo "   - 访问 https://cursor.com/account/regions"
echo "   - 确认账户区域设置"
echo ""
echo "   方法 D: 查看详细错误信息"
echo "   - 在 Cursor 中：Help > Toggle Developer Tools"
echo "   - 查看 Console 标签页的错误信息"
echo ""






