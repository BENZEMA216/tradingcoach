#!/usr/bin/env python3
"""VPN 连接诊断脚本"""
import socket
import subprocess
import json
import requests

def check_port(host, port):
    """检查端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def test_proxy(proxy_url):
    """测试代理"""
    try:
        proxies = {'http': proxy_url, 'https': proxy_url}
        response = requests.get('https://ipinfo.io/json', proxies=proxies, timeout=5)
        data = response.json()
        return True, data
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    print("=== VPN 代理诊断 ===\n")
    
    # 检查常见代理端口
    common_ports = [17890, 7890, 1080, 1087, 8080, 8888, 10808, 10809]
    print("1. 检查代理端口:")
    available_ports = []
    for port in common_ports:
        if check_port('127.0.0.1', port):
            print(f"   ✓ 端口 {port} 可用")
            available_ports.append(port)
        else:
            print(f"   ✗ 端口 {port} 不可用")
    
    # 测试可用端口
    if available_ports:
        print(f"\n2. 测试代理连接:")
        for port in available_ports:
            proxy_url = f"http://127.0.0.1:{port}"
            success, result = test_proxy(proxy_url)
            if success:
                print(f"   ✓ 端口 {port} 代理可用")
                print(f"      IP: {result['ip']}")
                print(f"      位置: {result['city']}, {result['country']}")
                if result['country'] == 'JP':
                    print(f"      ✅ 已连接到日本！")
                    break
            else:
                print(f"   ✗ 端口 {port} 代理不可用: {result[:50]}")
    else:
        print("\n2. 未找到可用的代理端口")
        print("   请检查 VPN 客户端是否正常运行")
    
    # 检查当前 IP
    print("\n3. 当前 IP（不使用代理）:")
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json()
        print(f"   IP: {data['ip']}")
        print(f"   位置: {data['city']}, {data['country']}")
    except Exception as e:
        print(f"   ✗ 无法获取 IP: {e}")
    
    print("\n=== 诊断完成 ===")
