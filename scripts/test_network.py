#!/usr/bin/env python3
"""网络连接诊断脚本"""
import requests
import os

# 清除代理环境变量
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(key, None)

def test_connection(url):
    """测试连接（不使用代理）"""
    try:
        response = requests.get(url, timeout=5)
        return True, f"✓ {url} - 状态码: {response.status_code}"
    except requests.exceptions.Timeout:
        return False, f"✗ {url} - 连接超时"
    except requests.exceptions.ConnectionError as e:
        return False, f"✗ {url} - 连接错误: {str(e)[:50]}"
    except Exception as e:
        return False, f"✗ {url} - {str(e)[:50]}"

if __name__ == "__main__":
    print("=== 网络连接诊断 ===\n")
    
    # 测试基本连接
    print("1. 基本连接测试:")
    sites = [
        ("百度", "https://www.baidu.com"),
        ("Alpha Vantage", "https://www.alphavantage.co"),
        ("Polygon.io", "https://api.polygon.io"),
        ("Tiingo", "https://api.tiingo.com")
    ]
    for name, site in sites:
        success, msg = test_connection(site)
        print(f"   {name}: {msg}")
    
    # 测试 yfinance
    print("\n2. yfinance API 测试:")
    try:
        import yfinance as yf
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        print(f"   ✓ yfinance 连接成功")
        print(f"   股票: {info.get('longName', 'N/A')}")
    except Exception as e:
        print(f"   ✗ yfinance 连接失败: {str(e)[:80]}")
    
    print("\n=== 诊断完成 ===")
