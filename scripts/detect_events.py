#!/usr/bin/env python3
"""
input: positions表, market_data表, yfinance财报日历
output: event_context表记录
pos: 数据处理脚本 - 为持仓检测关联事件

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

用法:
    python scripts/detect_events.py --all              # 处理所有已平仓持仓
    python scripts/detect_events.py --position 123    # 处理指定持仓
    python scripts/detect_events.py --symbol AAPL     # 处理指定标的
    python scripts/detect_events.py --stats           # 显示事件统计
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_PATH
from src.models.position import Position, PositionStatus
from src.analyzers.event_detector import EventDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="检测持仓关联的市场事件（财报、价格异常等）"
    )
    parser.add_argument('--all', action='store_true', help='处理所有已平仓持仓')
    parser.add_argument('--position', type=int, help='处理指定持仓ID')
    parser.add_argument('--symbol', type=str, help='处理指定标的的所有持仓')
    parser.add_argument('--limit', type=int, default=100, help='最大处理数量')
    parser.add_argument('--force', action='store_true', help='强制重新检测（不跳过已有事件）')
    parser.add_argument('--stats', action='store_true', help='显示事件统计')
    parser.add_argument('--no-earnings', action='store_true', help='不获取财报事件')
    parser.add_argument('--no-anomalies', action='store_true', help='不检测异常事件')

    args = parser.parse_args()

    # 初始化数据库连接
    engine = create_engine(f"sqlite:///{DATABASE_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()

    detector = EventDetector(session)

    try:
        if args.stats:
            # 显示统计
            stats = detector.get_event_statistics()
            print("\n=== 事件统计 ===")
            print(f"总事件数: {stats['total_events']}")
            print("\n按类型:")
            for t, c in stats['by_type'].items():
                print(f"  {t}: {c}")
            print("\n按影响方向:")
            for i, c in stats['by_impact'].items():
                print(f"  {i}: {c}")
            return

        if args.position:
            # 处理单个持仓
            position = session.query(Position).get(args.position)
            if not position:
                logger.error(f"持仓 {args.position} 不存在")
                sys.exit(1)

            logger.info(f"处理持仓 {position.id}: {position.symbol}")
            events = detector.detect_events_for_position(
                position,
                include_earnings=not args.no_earnings,
                include_anomalies=not args.no_anomalies
            )
            logger.info(f"发现 {len(events)} 个事件")

            if events:
                saved = detector.save_events(events, deduplicate=not args.force)
                logger.info(f"保存 {saved} 个新事件")

                for e in events:
                    print(f"  [{e['event_date']}] {e['event_type']}: {e['event_title']}")

        elif args.symbol:
            # 处理指定标的的所有持仓
            positions = session.query(Position).filter(
                Position.symbol.like(f"%{args.symbol}%")
            ).limit(args.limit).all()

            logger.info(f"找到 {len(positions)} 个 {args.symbol} 相关持仓")

            total_events = 0
            for position in positions:
                events = detector.detect_events_for_position(
                    position,
                    include_earnings=not args.no_earnings,
                    include_anomalies=not args.no_anomalies
                )
                if events:
                    saved = detector.save_events(events, deduplicate=not args.force)
                    total_events += saved

            logger.info(f"共保存 {total_events} 个事件")

        elif args.all:
            # 处理所有已平仓持仓
            stats = detector.detect_events_for_all_positions(
                status=PositionStatus.CLOSED,
                limit=args.limit,
                skip_existing=not args.force
            )

            print("\n=== 处理结果 ===")
            print(f"处理持仓数: {stats['processed']}")
            print(f"发现事件数: {stats['events_found']}")
            print(f"保存事件数: {stats['events_saved']}")

        else:
            parser.print_help()

    finally:
        session.close()


if __name__ == "__main__":
    main()
