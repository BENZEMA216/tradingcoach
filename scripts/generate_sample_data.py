"""
示例数据生成脚本 - 将真实交易数据脱敏后生成示例数据

input: original_data/ 下的真实交易CSV文件
output: frontend/public/sample-data/ 下的脱敏示例CSV文件
pos: 一次性脚本 - 生成示例数据，可多次运行

运行方式: python scripts/generate_sample_data.py
"""

import pandas as pd
import random
import re
from pathlib import Path

# 随机种子确保可重现
random.seed(42)

# 扰动范围
VARIANCE = 0.10  # ±10%


def add_variance(value, variance: float = VARIANCE) -> float:
    """给数值添加随机扰动"""
    if pd.isna(value) or value == 0 or value == '':
        return value
    try:
        val = float(value)
        if val == 0:
            return val
        factor = 1 + random.uniform(-variance, variance)
        return round(val * factor, 2)
    except (ValueError, TypeError):
        return value


def add_variance_int(value, variance: float = VARIANCE) -> int:
    """给整数添加随机扰动"""
    if pd.isna(value) or value == 0 or value == '':
        return value
    try:
        val = int(float(value))
        if val == 0:
            return val
        factor = 1 + random.uniform(-variance, variance)
        return max(1, round(val * factor))
    except (ValueError, TypeError):
        return value


def process_filled_avg_price(value, variance: float = VARIANCE) -> str:
    """处理 'Filled@Avg Price' / '已成交@均价' 字段，格式如 '10@50.1499'"""
    if pd.isna(value) or value == '' or '@' not in str(value):
        return value

    try:
        parts = str(value).split('@')
        if len(parts) == 2:
            qty = add_variance_int(int(parts[0]), variance)
            price = add_variance(float(parts[1]), variance)
            return f"{qty}@{price}"
    except (ValueError, TypeError):
        pass
    return value


def safe_multiply(price, qty):
    """安全地计算 价格 × 数量，处理非数字情况"""
    try:
        p = float(price)
        q = float(qty)
        return round(p * q, 2)
    except (ValueError, TypeError):
        return ''  # 如果价格是 "Market Price" 等非数字，返回空


def anonymize_english_csv(input_path: str, output_path: str):
    """脱敏英文格式CSV"""
    print(f"Processing English CSV: {input_path}")

    # 读取CSV（UTF-8 BOM）
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    original_count = len(df)
    print(f"  Loaded {original_count} rows")

    # 清空敏感字段
    if 'Order Source' in df.columns:
        df['Order Source'] = ''
    if 'Counterparty' in df.columns:
        df['Counterparty'] = ''
    if 'Remarks' in df.columns:
        df['Remarks'] = ''

    # 扰动价格字段（跳过非数字值如 "Market Price"）
    for col in ['Order Price', 'Fill Price']:
        if col in df.columns:
            df[col] = df[col].apply(add_variance)

    # 扰动数量字段
    for col in ['Order Qty', 'Fill Qty']:
        if col in df.columns:
            df[col] = df[col].apply(add_variance_int)

    # 处理 Filled@Avg Price 字段
    if 'Filled@Avg Price' in df.columns:
        df['Filled@Avg Price'] = df['Filled@Avg Price'].apply(process_filled_avg_price)

    # 重新计算金额（价格 × 数量），处理市价单情况
    if 'Order Price' in df.columns and 'Order Qty' in df.columns:
        df['Order Amount'] = df.apply(
            lambda row: safe_multiply(row['Order Price'], row['Order Qty']), axis=1
        )
    if 'Fill Price' in df.columns and 'Fill Qty' in df.columns:
        df['Fill Amount'] = df.apply(
            lambda row: safe_multiply(row['Fill Price'], row['Fill Qty']), axis=1
        )

    # 扰动费用字段
    fee_cols = [
        'Commission', 'Platform Fees', 'Settlement Fees',
        'Options Regulatory Fees', 'OCC Fees', 'Option Settlement Fees',
        'SEC Fees', 'Trading Activity Fees', 'Stamp Duty', 'Trading Fees',
        'SFC Levy', 'FRC Levy', 'Trading Tariff', 'Consolidated Audit Trail Fees'
    ]
    for col in fee_cols:
        if col in df.columns:
            df[col] = df[col].apply(add_variance)

    # 重新计算总费用
    existing_fee_cols = [c for c in fee_cols if c in df.columns]
    if existing_fee_cols and 'Total' in df.columns:
        df['Total'] = df[existing_fee_cols].apply(
            lambda row: round(sum(float(v) if pd.notna(v) and v != '' else 0 for v in row), 2),
            axis=1
        )

    # 保存（UTF-8 BOM 以便 Excel 正确打开）
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"  Saved {len(df)} rows to {output_path}")


def anonymize_chinese_csv(input_path: str, output_path: str):
    """脱敏中文格式CSV"""
    print(f"Processing Chinese CSV: {input_path}")

    # 读取CSV（UTF-8 BOM）
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    original_count = len(df)
    print(f"  Loaded {original_count} rows")

    # 清空敏感字段
    if '订单来源' in df.columns:
        df['订单来源'] = ''
    if '对手经纪' in df.columns:
        df['对手经纪'] = ''
    if '备注' in df.columns:
        df['备注'] = ''

    # 扰动价格字段
    for col in ['订单价格', '成交价格']:
        if col in df.columns:
            df[col] = df[col].apply(add_variance)

    # 扰动数量字段
    for col in ['订单数量', '成交数量']:
        if col in df.columns:
            df[col] = df[col].apply(add_variance_int)

    # 处理 已成交@均价 字段
    if '已成交@均价' in df.columns:
        df['已成交@均价'] = df['已成交@均价'].apply(process_filled_avg_price)

    # 重新计算金额（价格 × 数量），处理市价单情况
    if '订单价格' in df.columns and '订单数量' in df.columns:
        df['订单金额'] = df.apply(
            lambda row: safe_multiply(row['订单价格'], row['订单数量']), axis=1
        )
    if '成交价格' in df.columns and '成交数量' in df.columns:
        df['成交金额'] = df.apply(
            lambda row: safe_multiply(row['成交价格'], row['成交数量']), axis=1
        )

    # 扰动费用字段
    fee_cols = [
        '佣金', '平台使用费', '交收费', '印花税', '交易费',
        '证监会征费', '财汇局征费', '期权监管费', '期权清算费', '期权交收费',
        '证监会规费', '交易活动费', '交易系统使用费', '综合审计跟踪监管费'
    ]
    for col in fee_cols:
        if col in df.columns:
            df[col] = df[col].apply(add_variance)

    # 重新计算总费用
    existing_fee_cols = [c for c in fee_cols if c in df.columns]
    if existing_fee_cols and '合计费用' in df.columns:
        df['合计费用'] = df[existing_fee_cols].apply(
            lambda row: round(sum(float(v) if pd.notna(v) and v != '' else 0 for v in row), 2),
            axis=1
        )

    # 保存（UTF-8 BOM 以便 Excel 正确打开）
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"  Saved {len(df)} rows to {output_path}")


def main():
    # 项目根目录
    project_root = Path(__file__).parent.parent

    # 输入文件
    en_input = project_root / 'original_data' / 'History-Margin Universal Account(2663)-20251221-002106.csv'
    zh_input = project_root / 'original_data' / '历史-保证金综合账户(2663)-20251103-231527.csv'

    # 输出目录
    output_dir = project_root / 'frontend' / 'public' / 'sample-data'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating anonymized sample data...")
    print("=" * 60)

    # 生成英文版示例数据
    if en_input.exists():
        anonymize_english_csv(str(en_input), str(output_dir / 'sample_trades_en.csv'))
    else:
        print(f"Warning: English CSV not found: {en_input}")

    print()

    # 生成中文版示例数据
    if zh_input.exists():
        anonymize_chinese_csv(str(zh_input), str(output_dir / 'sample_trades_zh.csv'))
    else:
        print(f"Warning: Chinese CSV not found: {zh_input}")

    print()
    print("=" * 60)
    print("Sample data generated successfully!")
    print(f"Output directory: {output_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
