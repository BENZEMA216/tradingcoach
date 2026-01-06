"""
使用V2评分系统重新评分所有持仓
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.models.position import Position, PositionStatus
from src.analyzers.quality_scorer import QualityScorer

# 直接使用数据库路径
db_path = project_root / "data" / "tradingcoach.db"
engine = create_engine(f"sqlite:///{db_path}")


def rescore_all_positions():
    """使用V2系统重新评分所有已关闭持仓"""
    print("=" * 60)
    print("Re-scoring All Positions with V2 Scoring System")
    print("=" * 60)

    # 创建V2评分器
    scorer = QualityScorer(use_v2=True)
    print(f"Scorer: {scorer}")
    print(f"Weights: {scorer.weights}")
    print()

    with Session(engine) as session:
        # 获取所有已关闭持仓
        positions = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.close_time.isnot(None)
        ).all()

        print(f"Found {len(positions)} closed positions to re-score")
        print("-" * 60)

        success_count = 0
        error_count = 0
        grade_distribution = {}

        for i, pos in enumerate(positions, 1):
            try:
                result = scorer.calculate_overall_score(session, pos)

                # 更新持仓的评分
                pos.overall_score = result['overall_score']
                pos.score_grade = result['grade']
                pos.entry_score = result['entry_score']
                pos.exit_score = result['exit_score']
                pos.trend_score = result['trend_score']
                pos.risk_score = result['risk_score']

                # 新增的V2字段
                pos.market_env_score = result.get('market_env_score')
                pos.behavior_score = result.get('behavior_score')
                pos.execution_score = result.get('execution_score')
                pos.options_greeks_score = result.get('options_greeks_score')
                pos.score_details = result.get('score_details')
                pos.behavior_analysis = result.get('behavior_warnings')

                # 统计
                grade = result['grade']
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
                success_count += 1

                if i % 20 == 0:
                    print(f"  Progress: {i}/{len(positions)} positions scored...")

            except Exception as e:
                error_count += 1
                print(f"  ERROR scoring position {pos.id} ({pos.symbol}): {e}")

        # 提交更改
        session.commit()

        print()
        print("=" * 60)
        print("Re-scoring Complete!")
        print("=" * 60)
        print(f"  Success: {success_count}")
        print(f"  Errors:  {error_count}")
        print()
        print("Grade Distribution:")
        for grade in sorted(grade_distribution.keys()):
            count = grade_distribution[grade]
            pct = count / success_count * 100 if success_count > 0 else 0
            bar = "█" * int(pct / 2)
            print(f"  {grade:4s}: {count:3d} ({pct:5.1f}%) {bar}")


if __name__ == "__main__":
    rescore_all_positions()
