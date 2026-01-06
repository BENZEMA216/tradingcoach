#!/usr/bin/env python3
"""
Fix Option Classification Script - 修复期权分类脚本

input: SQLite database with misclassified options
output: Updated is_option and option fields for trades and positions

Usage:
    python scripts/fix_option_classification.py              # 预览模式
    python scripts/fix_option_classification.py --apply      # 应用修复
"""

import sys
import os
import re
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3


def parse_us_option(symbol: str) -> dict:
    """
    解析美股期权代码

    格式: 标的(1-5字母) + 到期日(6位YYMMDD) + C/P + 行权价(5-8位数字)
    示例: NVDA250207C120000 -> NVDA, 2025-02-07, CALL, $120.00
    """
    if not symbol or len(symbol) < 15:
        return None

    pattern = r'^([A-Z]{1,5})(\d{6})([CP])(\d{5,8})$'
    match = re.match(pattern, symbol)

    if not match:
        return None

    underlying = match.group(1)
    date_str = match.group(2)
    option_type = 'CALL' if match.group(3) == 'C' else 'PUT'
    strike_str = match.group(4)

    try:
        # 解析到期日: YYMMDD -> YYYY-MM-DD
        year = 2000 + int(date_str[0:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])
        expiry_date = datetime(year, month, day).strftime('%Y-%m-%d')

        # 解析行权价: 除以 1000
        strike_price = int(strike_str) / 1000.0

        return {
            'underlying_symbol': underlying,
            'option_type': option_type,
            'strike_price': strike_price,
            'expiry_date': expiry_date,
            'is_option': True
        }
    except (ValueError, ArithmeticError):
        return None


def is_us_option(symbol: str) -> bool:
    """判断是否为美股期权"""
    return parse_us_option(symbol) is not None


def fix_option_classification(db_path: str, dry_run: bool = True):
    """修复期权分类和字段"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 60)
    print("  期权分类修复工具")
    print("=" * 60)
    print(f"模式: {'预览 (Dry Run)' if dry_run else '应用修复'}")
    print()

    # 1. 修复 trades 表
    print("📋 检查 trades 表...")
    cursor.execute("""
        SELECT id, symbol, is_option, underlying_symbol, option_type, strike_price, expiration_date
        FROM trades
    """)
    trades = cursor.fetchall()

    trades_to_fix = []
    for trade in trades:
        symbol = trade['symbol']
        option_info = parse_us_option(symbol)

        if option_info:
            # 是期权，检查字段是否需要更新
            needs_fix = (
                not trade['is_option'] or
                trade['underlying_symbol'] != option_info['underlying_symbol'] or
                trade['option_type'] != option_info['option_type'] or
                trade['strike_price'] != option_info['strike_price'] or
                trade['expiration_date'] != option_info['expiry_date']
            )
            if needs_fix:
                trades_to_fix.append({
                    'id': trade['id'],
                    'symbol': symbol,
                    **option_info
                })
        elif trade['is_option']:
            # 不是期权但被标记为期权，需要清除
            trades_to_fix.append({
                'id': trade['id'],
                'symbol': symbol,
                'is_option': False,
                'underlying_symbol': None,
                'option_type': None,
                'strike_price': None,
                'expiry_date': None
            })

    print(f"  总交易数: {len(trades)}")
    print(f"  需修复数: {len(trades_to_fix)}")

    if trades_to_fix and not dry_run:
        for fix in trades_to_fix:
            cursor.execute("""
                UPDATE trades
                SET is_option = ?,
                    underlying_symbol = ?,
                    option_type = ?,
                    strike_price = ?,
                    expiration_date = ?
                WHERE id = ?
            """, (
                1 if fix['is_option'] else 0,
                fix['underlying_symbol'],
                fix['option_type'],
                fix['strike_price'],
                fix['expiry_date'],
                fix['id']
            ))
        print(f"  ✓ 已修复 {len(trades_to_fix)} 条交易记录")
    elif trades_to_fix:
        print(f"  示例 (前5条):")
        for fix in trades_to_fix[:5]:
            print(f"    - {fix['symbol']}: {fix['option_type']} ${fix.get('strike_price', 'N/A')} exp:{fix.get('expiry_date', 'N/A')}")

    print()

    # 2. 修复 positions 表
    print("📋 检查 positions 表...")
    cursor.execute("""
        SELECT id, symbol, is_option, underlying_symbol, option_type, strike_price, expiry_date
        FROM positions
    """)
    positions = cursor.fetchall()

    positions_to_fix = []
    for pos in positions:
        symbol = pos['symbol']
        option_info = parse_us_option(symbol)

        if option_info:
            # 是期权，检查字段是否需要更新
            needs_fix = (
                not pos['is_option'] or
                pos['underlying_symbol'] != option_info['underlying_symbol'] or
                pos['option_type'] != option_info['option_type'] or
                pos['strike_price'] != option_info['strike_price'] or
                pos['expiry_date'] != option_info['expiry_date']
            )
            if needs_fix:
                positions_to_fix.append({
                    'id': pos['id'],
                    'symbol': symbol,
                    **option_info
                })
        elif pos['is_option']:
            # 不是期权但被标记为期权，需要清除
            positions_to_fix.append({
                'id': pos['id'],
                'symbol': symbol,
                'is_option': False,
                'underlying_symbol': None,
                'option_type': None,
                'strike_price': None,
                'expiry_date': None
            })

    print(f"  总持仓数: {len(positions)}")
    print(f"  需修复数: {len(positions_to_fix)}")

    if positions_to_fix and not dry_run:
        for fix in positions_to_fix:
            cursor.execute("""
                UPDATE positions
                SET is_option = ?,
                    underlying_symbol = ?,
                    option_type = ?,
                    strike_price = ?,
                    expiry_date = ?
                WHERE id = ?
            """, (
                1 if fix['is_option'] else 0,
                fix['underlying_symbol'],
                fix['option_type'],
                fix['strike_price'],
                fix['expiry_date'],
                fix['id']
            ))
        print(f"  ✓ 已修复 {len(positions_to_fix)} 条持仓记录")
    elif positions_to_fix:
        print(f"  示例 (前5条):")
        for fix in positions_to_fix[:5]:
            print(f"    - {fix['symbol']}: {fix['option_type']} ${fix.get('strike_price', 'N/A')} exp:{fix.get('expiry_date', 'N/A')}")

    print()

    # 3. 提交或回滚
    if not dry_run:
        conn.commit()
        print("✓ 所有修复已应用")
    else:
        conn.rollback()
        print("ℹ️  预览模式，未应用任何修改")
        print("   使用 --apply 参数来应用修复")

    conn.close()

    print()
    print("=" * 60)

    return {
        'trades_fixed': len(trades_to_fix),
        'positions_fixed': len(positions_to_fix)
    }


def main():
    parser = argparse.ArgumentParser(description="修复期权分类")
    parser.add_argument("--db", default="data/tradingcoach.db", help="数据库路径")
    parser.add_argument("--apply", action="store_true", help="应用修复 (默认预览)")

    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"错误: 数据库不存在: {args.db}")
        sys.exit(1)

    dry_run = not args.apply
    result = fix_option_classification(args.db, dry_run=dry_run)

    # 返回状态码
    if result['trades_fixed'] > 0 or result['positions_fixed'] > 0:
        if dry_run:
            sys.exit(1)  # 有待修复项
        else:
            sys.exit(0)  # 已修复
    else:
        sys.exit(0)  # 无需修复


if __name__ == "__main__":
    main()
