#!/usr/bin/env python3
"""
修复交易与持仓的关联

问题: trades.position_id 为 NULL，导致持仓详情页无法显示相关交易
解决: 删除现有持仓，重新运行配对（配对代码已修复）

input: trades表（已有数据）
output: positions表（重新生成），trades.position_id（更新）
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.models.base import init_database, get_session
from src.matchers import match_trades_from_database

# 数据库路径
DB_PATH = project_root / 'data' / 'tradingcoach.db'


def backup_database():
    """备份数据库"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = DB_PATH.with_suffix(f'.db.backup_{timestamp}')
    shutil.copy2(DB_PATH, backup_path)
    print(f"✓ Database backed up to: {backup_path}")
    return backup_path


def clear_positions(session):
    """清除所有持仓数据"""
    # 先重置所有 trades 的 position_id
    result = session.execute(text("UPDATE trades SET position_id = NULL"))
    print(f"✓ Reset {result.rowcount} trades' position_id to NULL")

    # 删除所有持仓
    result = session.execute(text("DELETE FROM positions"))
    print(f"✓ Deleted {result.rowcount} positions")

    # 删除新闻上下文（因为关联到位置）
    result = session.execute(text("DELETE FROM news_context"))
    print(f"✓ Deleted {result.rowcount} news_context records")

    session.commit()


def main():
    """主函数"""
    print("=" * 60)
    print("修复交易与持仓关联")
    print("=" * 60)

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return 1

    # 确认操作
    print("\n⚠️  此操作将:")
    print("  1. 备份数据库")
    print("  2. 删除所有持仓记录")
    print("  3. 删除所有新闻上下文记录")
    print("  4. 重新配对交易生成持仓")
    print("  5. 更新 trades.position_id")

    confirm = input("\n确认执行? (y/N): ").strip().lower()
    if confirm != 'y':
        print("操作已取消")
        return 0

    try:
        # 1. 备份数据库
        print("\n[Step 1/4] 备份数据库...")
        backup_database()

        # 2. 初始化数据库
        print("\n[Step 2/4] 初始化数据库连接...")
        init_database(f"sqlite:///{DB_PATH}")
        session = get_session()

        # 3. 清除现有数据
        print("\n[Step 3/4] 清除现有持仓数据...")
        clear_positions(session)

        # 4. 重新配对
        print("\n[Step 4/4] 重新配对交易...")
        result = match_trades_from_database(session, dry_run=False)

        # 显示结果
        print("\n" + "=" * 60)
        print("✓ 修复完成!")
        print("=" * 60)
        print(f"Total Trades Processed:  {result['total_trades']}")
        print(f"Positions Created:       {result['positions_created']}")
        print(f"  - Closed Positions:    {result['closed_positions']}")
        print(f"  - Open Positions:      {result['open_positions']}")

        # 验证
        trades_with_position = session.execute(
            text("SELECT COUNT(*) FROM trades WHERE position_id IS NOT NULL")
        ).scalar()
        print(f"\nTrades linked to positions: {trades_with_position}")

        if result['warnings']:
            print(f"\n⚠️  Warnings ({len(result['warnings'])}):")
            for warning in result['warnings']:
                print(f"  - {warning}")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if 'session' in locals():
            session.close()


if __name__ == '__main__':
    sys.exit(main())
