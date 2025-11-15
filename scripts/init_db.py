#!/usr/bin/env python
"""
数据库初始化脚本

创建所有表结构
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import config
from src.models import (
    init_database,
    create_all_tables,
    get_engine,
    Trade,
    Position,
    MarketData,
    MarketEnvironment,
    StockClassification
)
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        logger.info("=" * 60)
        logger.info("Trading Coach - 数据库初始化")
        logger.info("=" * 60)

        # 显示配置信息
        logger.info(f"数据库路径: {config.DATABASE_PATH}")
        logger.info(f"数据库URL: {config.DATABASE_URL}")

        # 检查数据库文件是否已存在
        if config.DATABASE_PATH.exists():
            logger.warning(f"数据库文件已存在: {config.DATABASE_PATH}")
            response = input("是否要删除现有数据库并重新创建？(yes/no): ")
            if response.lower() != 'yes':
                logger.info("操作已取消")
                return

            # 删除现有数据库
            config.DATABASE_PATH.unlink()
            logger.info("已删除现有数据库文件")

        # 初始化数据库连接
        logger.info("初始化数据库连接...")
        engine = init_database(
            config.DATABASE_URL,
            echo=config.SQLALCHEMY_ECHO
        )

        # 创建所有表
        logger.info("创建数据库表...")
        create_all_tables()

        # 验证表创建
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"成功创建 {len(tables)} 个表:")
        for table in sorted(tables):
            logger.info(f"  ✓ {table}")

        # 显示表结构信息
        logger.info("\n表结构详情:")
        logger.info("-" * 60)

        table_info = {
            'trades': Trade,
            'positions': Position,
            'market_data': MarketData,
            'market_environment': MarketEnvironment,
            'stock_classifications': StockClassification,
        }

        for table_name, model in table_info.items():
            if table_name in tables:
                columns = inspector.get_columns(table_name)
                indexes = inspector.get_indexes(table_name)

                logger.info(f"\n{table_name}:")
                logger.info(f"  列数: {len(columns)}")
                logger.info(f"  索引数: {len(indexes)}")

                # 显示主要列
                main_columns = [c['name'] for c in columns[:10]]
                logger.info(f"  主要列: {', '.join(main_columns)}...")

        logger.info("\n" + "=" * 60)
        logger.info("✓ 数据库初始化完成！")
        logger.info("=" * 60)

        # 显示下一步操作
        logger.info("\n下一步操作:")
        logger.info("1. 导入交易数据:")
        logger.info(f"   python scripts/import_trades.py --file original_data/历史*.csv")
        logger.info("\n2. 预加载市场数据:")
        logger.info(f"   python scripts/preload_market_data.py")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
