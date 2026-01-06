#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加新的技术指标字段

Usage:
    python scripts/migrate_add_indicators.py           # 执行迁移
    python scripts/migrate_add_indicators.py --dry-run # 演练模式
"""

import sys
import os
import argparse
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config import DATABASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 新增的字段定义 (字段名, 类型, 注释)
NEW_COLUMNS = [
    # 成交量指标
    ('obv', 'NUMERIC(20, 2)', 'OBV能量潮'),
    ('vwap', 'NUMERIC(15, 4)', '成交量加权平均价'),
    ('mfi_14', 'NUMERIC(6, 2)', 'MFI资金流量指标(14)'),
    ('ad_line', 'NUMERIC(20, 2)', 'A/D累积分布线'),
    ('cmf_20', 'NUMERIC(8, 4)', 'CMF蔡金资金流(20)'),
    ('volume_ratio', 'NUMERIC(8, 2)', '成交量比率'),

    # 动量指标
    ('cci_20', 'NUMERIC(8, 2)', 'CCI商品通道指数(20)'),
    ('willr_14', 'NUMERIC(8, 2)', '威廉指标(14)'),
    ('roc_12', 'NUMERIC(10, 4)', '变动率(12)'),
    ('mom_10', 'NUMERIC(10, 4)', '动量指标(10)'),
    ('uo', 'NUMERIC(6, 2)', '终极震荡指标'),
    ('rsi_div', 'INTEGER', 'RSI背离信号(-1熊/0无/1牛)'),

    # 波动率指标
    ('kc_upper', 'NUMERIC(15, 4)', '肯特纳通道上轨'),
    ('kc_middle', 'NUMERIC(15, 4)', '肯特纳通道中轨'),
    ('kc_lower', 'NUMERIC(15, 4)', '肯特纳通道下轨'),
    ('dc_upper', 'NUMERIC(15, 4)', '唐奇安通道上轨(20)'),
    ('dc_lower', 'NUMERIC(15, 4)', '唐奇安通道下轨(20)'),
    ('hvol_20', 'NUMERIC(8, 4)', '20日历史波动率'),
    ('atr_pct', 'NUMERIC(8, 4)', 'ATR百分比'),
    ('bb_squeeze', 'INTEGER', '布林挤压信号(1=挤压中/0=释放)'),
    ('vol_rank', 'NUMERIC(6, 2)', '波动率排名(0-100)'),

    # 趋势指标 - Ichimoku
    ('ichi_tenkan', 'NUMERIC(15, 4)', '转换线(9)'),
    ('ichi_kijun', 'NUMERIC(15, 4)', '基准线(26)'),
    ('ichi_senkou_a', 'NUMERIC(15, 4)', '先行带A'),
    ('ichi_senkou_b', 'NUMERIC(15, 4)', '先行带B'),
    ('ichi_chikou', 'NUMERIC(15, 4)', '迟行线'),

    # 趋势指标 - 其他
    ('psar', 'NUMERIC(15, 4)', '抛物线SAR'),
    ('psar_dir', 'INTEGER', 'SAR方向(1多/-1空)'),
    ('supertrend', 'NUMERIC(15, 4)', '超级趋势'),
    ('supertrend_dir', 'INTEGER', 'SuperTrend方向(1多/-1空)'),
    ('trix', 'NUMERIC(10, 4)', 'TRIX三重指数平滑'),
    ('dpo', 'NUMERIC(10, 4)', '去趋势价格振荡器'),

    # 期权指标
    ('iv_rank', 'NUMERIC(6, 2)', 'IV排名(0-100)'),
    ('iv_percentile', 'NUMERIC(6, 2)', 'IV百分位(0-100)'),
    ('pcr', 'NUMERIC(8, 4)', '看跌/看涨比率'),
]


def get_existing_columns(engine):
    """获取表中已存在的列"""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(market_data)"))
        return {row[1] for row in result.fetchall()}


def migrate(dry_run: bool = False):
    """执行数据库迁移"""
    engine = create_engine(DATABASE_URL)

    existing_columns = get_existing_columns(engine)
    logger.info(f"Table 'market_data' has {len(existing_columns)} existing columns")

    columns_to_add = []
    columns_skipped = []

    for col_name, col_type, col_comment in NEW_COLUMNS:
        if col_name in existing_columns:
            columns_skipped.append(col_name)
        else:
            columns_to_add.append((col_name, col_type, col_comment))

    if columns_skipped:
        logger.info(f"Skipping {len(columns_skipped)} existing columns: {', '.join(columns_skipped[:5])}...")

    if not columns_to_add:
        logger.info("No new columns to add. Migration complete.")
        return

    logger.info(f"Adding {len(columns_to_add)} new columns...")

    with engine.connect() as conn:
        for col_name, col_type, col_comment in columns_to_add:
            sql = f"ALTER TABLE market_data ADD COLUMN {col_name} {col_type}"

            if dry_run:
                logger.info(f"[DRY RUN] Would execute: {sql}")
            else:
                try:
                    conn.execute(text(sql))
                    logger.info(f"Added column: {col_name} ({col_type})")
                except Exception as e:
                    logger.error(f"Failed to add column {col_name}: {e}")

        if not dry_run:
            conn.commit()

    logger.info("=" * 60)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Columns added:   {len(columns_to_add)}")
    logger.info(f"Columns skipped: {len(columns_skipped)}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Add new indicator columns to market_data table')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes)')

    args = parser.parse_args()
    migrate(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
