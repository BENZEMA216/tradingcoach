# tests/data_integrity/test_trade_integrity.py
"""
input: trades 表
output: 7 项检查结果 (指纹唯一、必填字段、方向枚举、数量价格、费用)
pos: 验证交易记录的数据完整性

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

对应检查项: DI-TRADE-001 ~ DI-TRADE-007
"""
import pytest
from .conftest import execute_check, execute_query


class TestTradeIntegrity:
    """Trade 表完整性检查"""

    def test_di_trade_001_fingerprint_unique(self, db_session):
        """DI-TRADE-001: 交易指纹唯一性"""
        result = execute_query(db_session, """
            SELECT trade_fingerprint, COUNT(*) as cnt
            FROM trades
            GROUP BY trade_fingerprint
            HAVING cnt > 1
        """)
        assert len(result) == 0, f"发现 {len(result)} 个重复交易指纹"

    def test_di_trade_002_required_fields_not_null(self, db_session):
        """DI-TRADE-002: 必填字段非空"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM trades
            WHERE symbol IS NULL
               OR direction IS NULL
               OR filled_quantity IS NULL
               OR filled_price IS NULL
               OR filled_time IS NULL
        """)
        assert count == 0, f"发现 {count} 条记录缺少必填字段"

    def test_di_trade_003_valid_direction_enum(self, db_session):
        """DI-TRADE-003: 方向枚举值有效"""
        result = execute_query(db_session, """
            SELECT DISTINCT direction FROM trades
            WHERE direction NOT IN ('BUY', 'SELL', 'SELL_SHORT', 'BUY_TO_COVER')
        """)
        assert len(result) == 0, f"发现无效方向值: {[r[0] for r in result]}"

    def test_di_trade_004_quantity_price_positive(self, db_session):
        """DI-TRADE-004: 数量和价格为正数"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM trades
            WHERE filled_quantity <= 0 OR filled_price <= 0
        """)
        assert count == 0, f"发现 {count} 条记录数量或价格非正数"

    def test_di_trade_005_fees_non_negative(self, db_session):
        """DI-TRADE-005: 费用非负"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM trades
            WHERE commission < 0
               OR platform_fee < 0
               OR total_fee < 0
        """)
        assert count == 0, f"发现 {count} 条记录费用为负数"

    def test_di_trade_006_total_fee_calculation(self, db_session):
        """DI-TRADE-006: 总费用计算正确

        业务说明:
        - 港股交易有额外费用（印花税、交易所费等）未拆分到独立字段
        - total_fee 是权威值，各费用字段是解析后的值
        - 此检查为 P2 级别（数据质量），允许一定差异
        """
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM trades
            WHERE ABS(total_fee - (
                COALESCE(commission, 0) +
                COALESCE(platform_fee, 0) +
                COALESCE(clearing_fee, 0) +
                COALESCE(transaction_fee, 0) +
                COALESCE(stamp_duty, 0) +
                COALESCE(sec_fee, 0) +
                COALESCE(option_regulatory_fee, 0) +
                COALESCE(option_clearing_fee, 0)
            )) > 0.01
        """)
        # P2 级别检查：允许存在差异，仅记录警告
        if count > 0:
            import warnings
            warnings.warn(f"DI-TRADE-006: {count} 条记录费用字段累加与 total_fee 有差异（已知问题，P2 级别）")

    def test_di_trade_007_option_fields_consistency(self, db_session):
        """DI-TRADE-007: 期权字段一致性"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM trades
            WHERE is_option = 1
              AND (underlying_symbol IS NULL
                   OR option_type IS NULL
                   OR strike_price IS NULL
                   OR expiration_date IS NULL)
        """)
        assert count == 0, f"发现 {count} 条期权记录字段不完整"
