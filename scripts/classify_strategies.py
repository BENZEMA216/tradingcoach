#!/usr/bin/env python3
"""
批量计算持仓的策略分类
"""

import sys
import logging
from pathlib import Path

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.base import init_database, get_session
from src.analyzers.strategy_classifier import StrategyClassifier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    # 初始化数据库
    db_path = Path(__file__).parent.parent / 'data' / 'tradingcoach.db'
    init_database(f'sqlite:///{db_path}', echo=False)

    logger.info("Database connection established")

    # 创建分类器
    classifier = StrategyClassifier()

    # 执行分类
    session = get_session()
    try:
        stats = classifier.classify_all_positions(session, update_db=True)

        # 打印统计
        print("\n" + "=" * 50)
        print("策略分类完成")
        print("=" * 50)
        print(f"总持仓数: {stats['total']}")
        print(f"已分类数: {stats['classified']}")
        print("-" * 50)
        print("策略分布:")
        print(f"  趋势跟踪 (trend):       {stats.get('trend', 0)}")
        print(f"  均值回归 (mean_reversion): {stats.get('mean_reversion', 0)}")
        print(f"  突破交易 (breakout):    {stats.get('breakout', 0)}")
        print(f"  震荡交易 (range):       {stats.get('range', 0)}")
        print(f"  动量交易 (momentum):    {stats.get('momentum', 0)}")
        print(f"  未知策略 (unknown):     {stats.get('unknown', 0)}")
        print("=" * 50)

    finally:
        session.close()


if __name__ == '__main__':
    main()
