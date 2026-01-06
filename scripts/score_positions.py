#!/usr/bin/env python3
"""
交易质量评分脚本

为所有已平仓的交易计算质量评分

Usage:
    python3 scripts/score_positions.py [--positions 1,2,3] [--all] [--limit 10]
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from src.analyzers import QualityScorer
from src.models.position import Position, PositionStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/score_positions.log')
    ]
)

logger = logging.getLogger(__name__)


def display_position_scores(session, position_ids=None, limit=10):
    """
    显示持仓的评分结果

    Args:
        session: Database session
        position_ids: 指定position ID列表
        limit: 显示数量限制
    """
    query = session.query(Position).filter(
        Position.status == PositionStatus.CLOSED,
        Position.overall_score.isnot(None)
    )

    if position_ids:
        query = query.filter(Position.id.in_(position_ids))

    positions = query.order_by(Position.overall_score.desc()).limit(limit).all()

    if not positions:
        print("\n没有找到已评分的持仓记录")
        return

    print("\n" + "=" * 120)
    print("交易质量评分结果")
    print("=" * 120)
    print(f"{'ID':<5} {'Symbol':<10} {'方向':<6} {'盈亏':<10} {'持仓天数':<8} "
          f"{'进场':<6} {'出场':<6} {'趋势':<6} {'风险':<6} {'总分':<6} {'等级':<4}")
    print("-" * 120)

    for pos in positions:
        pnl_str = f"${pos.realized_pnl:.2f}" if pos.realized_pnl else "N/A"
        direction_map = {'long': '做多', 'short': '做空'}
        direction_str = direction_map.get(pos.direction, pos.direction)

        print(f"{pos.id:<5} {pos.symbol:<10} {direction_str:<6} {pnl_str:<10} {pos.holding_period_days or 0:<8} "
              f"{pos.entry_quality_score or 0:<6.1f} {pos.exit_quality_score or 0:<6.1f} "
              f"{pos.trend_quality_score or 0:<6.1f} {pos.risk_mgmt_score or 0:<6.1f} "
              f"{pos.overall_score or 0:<6.1f} {pos.score_grade or 'N/A':<4}")

    print("=" * 120)


def display_score_statistics(session):
    """显示评分统计信息"""
    scored_positions = session.query(Position).filter(
        Position.status == PositionStatus.CLOSED,
        Position.overall_score.isnot(None)
    ).all()

    if not scored_positions:
        print("\n没有已评分的持仓记录")
        return

    # 统计各等级数量
    grade_counts = {}
    for pos in scored_positions:
        grade = pos.score_grade or 'N/A'
        grade_counts[grade] = grade_counts.get(grade, 0) + 1

    # 计算平均分
    scores = [float(pos.overall_score) for pos in scored_positions if pos.overall_score]
    avg_score = sum(scores) / len(scores) if scores else 0

    print("\n" + "=" * 60)
    print("评分统计")
    print("=" * 60)
    print(f"总计已评分交易: {len(scored_positions)}")
    print(f"平均总分: {avg_score:.2f}")
    print("\n等级分布:")
    for grade in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']:
        count = grade_counts.get(grade, 0)
        if count > 0:
            pct = count / len(scored_positions) * 100
            print(f"  {grade:<3}: {count:>3} ({pct:>5.1f}%)")

    # 维度平均分
    entry_scores = [float(p.entry_quality_score) for p in scored_positions if p.entry_quality_score]
    exit_scores = [float(p.exit_quality_score) for p in scored_positions if p.exit_quality_score]
    trend_scores = [float(p.trend_quality_score) for p in scored_positions if p.trend_quality_score]
    risk_scores = [float(p.risk_mgmt_score) for p in scored_positions if p.risk_mgmt_score]

    print("\n维度平均分:")
    if entry_scores:
        print(f"  进场质量: {sum(entry_scores)/len(entry_scores):.2f}")
    if exit_scores:
        print(f"  出场质量: {sum(exit_scores)/len(exit_scores):.2f}")
    if trend_scores:
        print(f"  趋势把握: {sum(trend_scores)/len(trend_scores):.2f}")
    if risk_scores:
        print(f"  风险管理: {sum(risk_scores)/len(risk_scores):.2f}")

    print("=" * 60)


def score_and_display(session, scorer, position_ids=None, update_db=True):
    """评分并显示结果"""
    if position_ids:
        # 评分指定positions
        positions = session.query(Position).filter(
            Position.id.in_(position_ids),
            Position.status == PositionStatus.CLOSED
        ).all()

        stats = {
            'total': len(positions),
            'scored': 0,
            'failed': 0
        }

        for pos in positions:
            try:
                result = scorer.calculate_overall_score(session, pos)

                if update_db:
                    pos.entry_quality_score = result['entry_score']
                    pos.exit_quality_score = result['exit_score']
                    pos.trend_quality_score = result['trend_score']
                    pos.risk_mgmt_score = result['risk_score']
                    pos.overall_score = result['overall_score']
                    pos.score_grade = result['grade']

                    # V2 新增评分
                    if result.get('market_env_score') is not None:
                        pos.market_env_score = result['market_env_score']
                    if result.get('behavior_score') is not None:
                        pos.behavior_score = result['behavior_score']
                    if result.get('execution_score') is not None:
                        pos.execution_score = result['execution_score']
                    if result.get('options_greeks_score') is not None:
                        pos.options_greeks_score = result['options_greeks_score']
                    if result.get('news_alignment_score') is not None:
                        pos.news_alignment_score = result['news_alignment_score']

                    # 保存评分详情
                    if result.get('details'):
                        pos.score_details = result['details']

                    # 保存 NewsContext
                    news_search_result = result.get('news_search_result')
                    news_alignment_result = result.get('news_alignment_result')
                    if news_search_result and news_alignment_result:
                        scorer._save_news_context(
                            session, pos,
                            news_search_result, news_alignment_result
                        )

                stats['scored'] += 1
                logger.info(f"Scored position {pos.id}: {result['overall_score']:.1f} ({result['grade']})")

            except Exception as e:
                logger.error(f"Failed to score position {pos.id}: {e}")
                stats['failed'] += 1

        if update_db:
            session.commit()

    else:
        # 评分所有positions
        stats = scorer.score_all_positions(session, update_db=update_db)

    return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='为已平仓交易计算质量评分'
    )
    parser.add_argument(
        '--positions',
        type=str,
        help='指定position IDs（逗号分隔，例如：1,2,3）'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='评分所有已平仓交易'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='显示数量限制（默认20）'
    )
    parser.add_argument(
        '--no-update',
        action='store_true',
        help='不更新数据库（仅计算显示）'
    )
    parser.add_argument(
        '--show-only',
        action='store_true',
        help='仅显示已有评分（不重新计算）'
    )

    args = parser.parse_args()

    try:
        # 设置数据库
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        logger.info("Database connection established")

        # 创建评分器
        scorer = QualityScorer()
        logger.info(f"QualityScorer initialized: {scorer}")

        # 解析position IDs
        position_ids = None
        if args.positions:
            position_ids = [int(id.strip()) for id in args.positions.split(',')]
            logger.info(f"Target positions: {position_ids}")

        # 执行评分
        if not args.show_only:
            if args.all or position_ids:
                print("\n开始计算交易质量评分...")
                start_time = datetime.now()

                stats = score_and_display(
                    session,
                    scorer,
                    position_ids=position_ids,
                    update_db=not args.no_update
                )

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                print(f"\n评分完成:")
                print(f"  总计: {stats['total']}")
                print(f"  成功: {stats['scored']}")
                print(f"  失败: {stats['failed']}")
                print(f"  耗时: {duration:.2f}秒")
            else:
                print("错误: 请指定 --positions 或 --all")
                parser.print_help()
                sys.exit(1)

        # 显示结果
        print("\n最高评分的交易:")
        display_position_scores(session, position_ids=position_ids, limit=args.limit)

        # 显示统计
        display_score_statistics(session)

        # 清理
        session.close()
        engine.dispose()

    except KeyboardInterrupt:
        print("\n\n评分中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"评分失败: {e}", exc_info=True)
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
