"""
测试V2评分系统
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


def test_v2_scoring():
    """测试V2评分系统"""
    print("=" * 60)
    print("Testing V2 Scoring System")
    print("=" * 60)

    # 创建评分器
    scorer = QualityScorer(use_v2=True)
    print(f"Scorer: {scorer}")
    print(f"Weights: {scorer.weights}")
    print()

    # 创建数据库会话
    with Session(engine) as session:
        # 获取几个样本持仓
        positions = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.close_time.isnot(None)
        ).limit(3).all()

        print(f"Testing with {len(positions)} positions")
        print("-" * 60)

        for pos in positions:
            print(f"\nPosition {pos.id}: {pos.symbol}")
            print(f"  Direction: {pos.direction}")
            print(f"  PnL: ${pos.net_pnl:.2f} ({pos.net_pnl_pct:.2f}%)")

            try:
                result = scorer.calculate_overall_score(session, pos)

                print(f"\n  === V2 Scores ===")
                print(f"  Overall: {result['overall_score']:.1f} ({result['grade']})")
                print(f"  Entry:       {result['entry_score']:.1f}")
                print(f"  Exit:        {result['exit_score']:.1f}")
                print(f"  Market Env:  {result.get('market_env_score', 'N/A')}")
                print(f"  Behavior:    {result.get('behavior_score', 'N/A')}")
                print(f"  Trend:       {result['trend_score']:.1f}")
                print(f"  Risk:        {result['risk_score']:.1f}")
                print(f"  Execution:   {result.get('execution_score', 'N/A')}")
                print(f"  Options:     {result.get('options_greeks_score', 'N/A')}")

                if result.get('behavior_warnings'):
                    print(f"\n  Warnings: {result['behavior_warnings']}")

            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "=" * 60)
        print("Test completed!")


if __name__ == "__main__":
    test_v2_scoring()
