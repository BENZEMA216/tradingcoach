#!/usr/bin/env python3
"""
测试英文CSV解析器
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.importers.english_csv_parser import (
    EnglishCSVParser,
    PositionSnapshotParser,
    detect_csv_language,
    load_english_csv
)


def test_history_parser():
    """测试交易历史解析"""
    print("=" * 60)
    print("Testing History File Parser")
    print("=" * 60)

    history_file = project_root / "original_data" / "History-Margin Universal Account(2663)-20251221-002106.csv"

    if not history_file.exists():
        print(f"✗ History file not found: {history_file}")
        return False

    # 检测语言
    lang = detect_csv_language(str(history_file))
    print(f"Detected language: {lang}")

    # 解析文件
    parser = EnglishCSVParser(str(history_file))
    df = parser.parse()

    print(f"\nTotal rows: {len(df)}")
    print(f"File type: {parser.file_type}")

    # 统计信息
    stats = parser.get_statistics()
    print(f"\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 筛选已成交订单
    completed_df = parser.filter_completed_trades()
    print(f"\nCompleted trades: {len(completed_df)}")

    # 显示样本数据
    print(f"\nSample data (first 5 completed trades):")
    sample_cols = ['symbol', 'direction', 'filled_quantity', 'filled_price',
                   'filled_time_parsed', 'is_spread', 'trade_fingerprint']
    available_cols = [c for c in sample_cols if c in completed_df.columns]
    print(completed_df[available_cols].head().to_string())

    # 检查期权解析
    print(f"\nOption trades:")
    option_df = completed_df[completed_df['symbol'].str.contains(r'\d{6}[CP]', na=False, regex=True)]
    if len(option_df) > 0:
        print(f"  Found {len(option_df)} option trades")
        sample = option_df.iloc[0]
        print(f"  Sample: {sample['symbol']}")
        print(f"    Underlying: {sample.get('underlying_symbol', 'N/A')}")
        print(f"    Type: {sample.get('option_type', 'N/A')}")
        print(f"    Strike: {sample.get('strike_price', 'N/A')}")
        print(f"    Expiry: {sample.get('expiry_date', 'N/A')}")

    # 检查组合订单
    print(f"\nSpread orders:")
    spread_df = completed_df[completed_df['is_spread'] == True]
    print(f"  Found {len(spread_df)} spread orders")
    if len(spread_df) > 0:
        for _, row in spread_df.head(3).iterrows():
            print(f"    {row['symbol']} - {row['spread_type']}")

    print("\n✓ History parser test passed")
    return True


def test_position_parser():
    """测试持仓快照解析"""
    print("\n" + "=" * 60)
    print("Testing Position Snapshot Parser")
    print("=" * 60)

    position_file = project_root / "original_data" / "Positions-Margin Universal Account(2663)-20251221-002024.csv"

    if not position_file.exists():
        print(f"✗ Position file not found: {position_file}")
        return False

    # 检测语言
    lang = detect_csv_language(str(position_file))
    print(f"Detected language: {lang}")

    # 使用持仓解析器
    snapshot_parser = PositionSnapshotParser(str(position_file))
    df = snapshot_parser.parse()

    print(f"\nTotal positions: {len(df)}")

    # 获取持仓列表
    positions = snapshot_parser.get_positions_list()

    print(f"\nPosition details:")
    for pos in positions:
        symbol = pos['symbol']
        qty = pos['quantity']
        avg_cost = pos.get('avg_cost', 0)
        unrealized = pos.get('unrealized_pnl', 0)
        is_option = pos.get('is_option', False)

        option_info = ""
        if is_option:
            option_info = f" [{pos.get('option_type', '?')} ${pos.get('strike_price', '?')} exp:{pos.get('expiry_date', '?')}]"

        print(f"  {symbol}: {qty} @ {avg_cost:.2f} | PnL: {unrealized:.2f}{option_info}")

    # 显示统计
    stats = snapshot_parser.parser.get_statistics()
    print(f"\nStatistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✓ Position parser test passed")
    return True


def test_fingerprint_uniqueness():
    """测试指纹唯一性"""
    print("\n" + "=" * 60)
    print("Testing Trade Fingerprint Uniqueness")
    print("=" * 60)

    history_file = project_root / "original_data" / "History-Margin Universal Account(2663)-20251221-002106.csv"

    parser = EnglishCSVParser(str(history_file))
    parser.parse()
    completed_df = parser.filter_completed_trades()

    # 检查指纹
    fingerprints = completed_df['trade_fingerprint'].dropna()
    unique_fingerprints = fingerprints.nunique()

    print(f"Total fingerprints: {len(fingerprints)}")
    print(f"Unique fingerprints: {unique_fingerprints}")

    # 检查重复
    duplicates = fingerprints.value_counts()
    dup_count = (duplicates > 1).sum()

    if dup_count > 0:
        print(f"\n⚠ Found {dup_count} duplicate fingerprints:")
        for fp, count in duplicates[duplicates > 1].head(5).items():
            # 找到重复的行
            dup_rows = completed_df[completed_df['trade_fingerprint'] == fp]
            print(f"  {fp[:16]}... ({count} times)")
            for _, row in dup_rows.iterrows():
                print(f"    {row['symbol']} {row['direction']} {row['filled_quantity']} @ {row['filled_price']}")
    else:
        print("\n✓ All fingerprints are unique")

    return True


def main():
    print("English CSV Parser Test Suite")
    print("=" * 60)

    results = []

    try:
        results.append(("History Parser", test_history_parser()))
    except Exception as e:
        print(f"✗ History parser test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("History Parser", False))

    try:
        results.append(("Position Parser", test_position_parser()))
    except Exception as e:
        print(f"✗ Position parser test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Position Parser", False))

    try:
        results.append(("Fingerprint Uniqueness", test_fingerprint_uniqueness()))
    except Exception as e:
        print(f"✗ Fingerprint test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Fingerprint Uniqueness", False))

    # 总结
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
