# tests/data_integrity/test_matching_integrity.py
"""
input: trades 表, positions 表
output: 7 项检查结果 (配对关联、方向一致、外键有效)
pos: 验证 FIFO 配对和外键关系的完整性

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

对应检查项: DI-MATCH-001 ~ DI-MATCH-005, DI-FK-001 ~ DI-FK-004

业务说明:
- FIFO 配对中，一笔交易可能被拆分到多个 position（部分成交）
- 因此一个 CLOSED position 可能只关联 1 笔交易
- 期权卖出场景: position.direction='short' 但 trade.direction='BUY'/'SELL'
"""
import pytest
from .conftest import execute_check, execute_query


class TestMatchingIntegrity:
    """FIFO 配对完整性检查"""

    def test_di_match_001_closed_position_has_complete_info(self, db_session):
        """DI-MATCH-001: 已平仓持仓有完整开平仓信息（不检查交易数量）

        业务说明: 由于部分成交，一个 position 可能只关联开仓或平仓交易中的一笔
        改为检查: CLOSED 持仓必须有 open_price 和 close_price
        """
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE status = 'CLOSED'
              AND (open_price IS NULL OR close_price IS NULL)
        """)
        assert count == 0, f"发现 {count} 条已平仓持仓缺少开平仓价格"

    def test_di_match_001b_closed_position_has_at_least_one_trade(self, db_session):
        """DI-MATCH-001b: 已平仓持仓至少有一笔关联交易"""
        result = execute_query(db_session, """
            SELECT p.id, p.symbol, COUNT(t.id) as trade_count
            FROM positions p
            LEFT JOIN trades t ON t.position_id = p.id
            WHERE p.status = 'CLOSED'
            GROUP BY p.id
            HAVING trade_count = 0
        """)
        assert len(result) == 0, f"发现 {len(result)} 个已平仓持仓无任何关联交易"

    def test_di_match_002_open_position_single_trade(self, db_session):
        """DI-MATCH-002: 开放持仓只有开仓交易"""
        result = execute_query(db_session, """
            SELECT p.id, p.symbol, COUNT(t.id) as trade_count
            FROM positions p
            LEFT JOIN trades t ON t.position_id = p.id
            WHERE p.status = 'OPEN'
            GROUP BY p.id
            HAVING trade_count != 1
        """)
        assert len(result) == 0, f"发现 {len(result)} 个开放持仓交易数异常"

    def test_di_match_003_long_direction_consistency(self, db_session):
        """DI-MATCH-003: 多头持仓交易方向一致（非期权）"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE p.direction = 'long'
              AND p.is_option = 0
              AND t.direction NOT IN ('BUY', 'SELL')
        """)
        assert count == 0, f"发现 {count} 条非期权多头持仓交易方向不一致"

    def test_di_match_003_short_direction_consistency(self, db_session):
        """DI-MATCH-003: 空头持仓交易方向一致（非期权）

        业务说明: 期权卖出（sell put/call）场景中，
        position.direction='short' 但 trade.direction='BUY'/'SELL' 是正常的
        因此只检查非期权的空头持仓
        """
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE p.direction = 'short'
              AND p.is_option = 0
              AND t.direction NOT IN ('SELL_SHORT', 'BUY_TO_COVER')
        """)
        assert count == 0, f"发现 {count} 条非期权空头持仓交易方向不一致"


class TestForeignKeyIntegrity:
    """外键关系完整性检查"""

    def test_di_fk_001_trade_position_id_valid(self, db_session):
        """DI-FK-001: Trade.position_id 有效"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM trades t
            LEFT JOIN positions p ON t.position_id = p.id
            WHERE t.position_id IS NOT NULL
              AND p.id IS NULL
        """)
        assert count == 0, f"发现 {count} 条交易的 position_id 无效"

    def test_di_fk_002_trade_market_data_id_valid(self, db_session):
        """DI-FK-002: Trade.market_data_id 有效"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM trades t
            LEFT JOIN market_data m ON t.market_data_id = m.id
            WHERE t.market_data_id IS NOT NULL
              AND m.id IS NULL
        """)
        assert count == 0, f"发现 {count} 条交易的 market_data_id 无效"

    def test_di_fk_004_news_context_position_id_unique(self, db_session):
        """DI-FK-004: NewsContext.position_id 一对一"""
        result = execute_query(db_session, """
            SELECT position_id, COUNT(*) as cnt
            FROM news_context
            WHERE position_id IS NOT NULL
            GROUP BY position_id
            HAVING cnt > 1
        """)
        assert len(result) == 0, f"发现 {len(result)} 个持仓有多条新闻上下文"
