# tests/data_integrity/test_business_rules.py
"""
input: trades, positions, market_data, market_environment 表
output: 7 项检查结果 (时序一致、数量价格匹配、市场数据完整)
pos: 验证跨表业务规则和市场数据完整性

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

对应检查项: DI-BIZ-001 ~ DI-BIZ-006, DI-MD-001 ~ DI-MD-003, DI-ME-001
"""
import pytest
from .conftest import execute_check, execute_query


class TestBusinessRules:
    """业务规则检查"""

    def test_di_biz_001_open_before_close(self, db_session):
        """DI-BIZ-001: 开仓时间早于平仓时间"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE status = 'CLOSED'
              AND open_time >= close_time
        """)
        assert count == 0, f"发现 {count} 条持仓开仓时间晚于平仓时间"

    def test_di_biz_002_trade_time_reasonable(self, db_session):
        """DI-BIZ-002: 交易时间在合理范围内"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM trades
            WHERE filled_time < '2020-01-01'
               OR filled_time > datetime('now', '+1 day')
        """)
        assert count == 0, f"发现 {count} 条交易时间超出合理范围"

    def test_di_biz_005_position_quantity_reasonable(self, db_session):
        """DI-BIZ-005: 持仓数量合理（部分成交场景下 position.qty <= trade.qty）

        业务说明: FIFO 部分成交时，一笔交易被拆分到多个 position
        因此 position.quantity <= trade.filled_quantity 是正常的
        只检查 position.quantity > trade.filled_quantity 的异常情况
        """
        result = execute_query(db_session, """
            SELECT p.id, p.symbol, p.quantity as pos_qty, t.filled_quantity as trade_qty
            FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE t.direction IN ('BUY', 'SELL_SHORT')
              AND p.quantity > t.filled_quantity
        """)
        assert len(result) == 0, f"发现 {len(result)} 条持仓数量超过交易数量（异常）"

    def test_di_biz_006_position_price_matches_trade(self, db_session):
        """DI-BIZ-006: 持仓价格与开仓交易价格一致（非期权）

        业务说明:
        - 部分成交时 position.open_price 应该等于开仓交易的 filled_price
        - 期权卖出场景中，position 关联的可能是平仓交易（BUY），因此排除期权
        """
        result = execute_query(db_session, """
            SELECT p.id, p.open_price, t.filled_price
            FROM positions p
            JOIN trades t ON t.position_id = p.id
            WHERE t.direction IN ('BUY', 'SELL_SHORT')
              AND p.is_option = 0
              AND ABS(p.open_price - t.filled_price) > 0.01
        """)
        assert len(result) == 0, f"发现 {len(result)} 条非期权持仓价格与交易不一致"


class TestMarketDataIntegrity:
    """市场数据完整性检查"""

    def test_di_md_001_unique_constraint(self, db_session):
        """DI-MD-001: (symbol, timestamp, interval) 唯一"""
        result = execute_query(db_session, """
            SELECT symbol, timestamp, interval, COUNT(*) as cnt
            FROM market_data
            GROUP BY symbol, timestamp, interval
            HAVING cnt > 1
        """)
        assert len(result) == 0, f"发现 {len(result)} 组重复市场数据"

    def test_di_md_002_ohlc_logic(self, db_session):
        """DI-MD-002: OHLC 逻辑正确 (low <= open/close <= high)"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM market_data
            WHERE low > open OR low > close
               OR high < open OR high < close
        """)
        assert count == 0, f"发现 {count} 条市场数据 OHLC 逻辑错误"

    def test_di_md_003_rsi_range(self, db_session):
        """DI-MD-003: RSI 在 0-100 范围内"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM market_data
            WHERE rsi_14 IS NOT NULL
              AND (rsi_14 < 0 OR rsi_14 > 100)
        """)
        assert count == 0, f"发现 {count} 条 RSI 超出范围"


class TestMarketEnvironmentIntegrity:
    """市场环境完整性检查"""

    def test_di_me_001_date_unique(self, db_session):
        """DI-ME-001: 每天只有一条记录"""
        result = execute_query(db_session, """
            SELECT date, COUNT(*) as cnt
            FROM market_environment
            GROUP BY date
            HAVING cnt > 1
        """)
        assert len(result) == 0, f"发现 {len(result)} 个日期有重复记录"
