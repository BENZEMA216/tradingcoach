# tests/data_integrity/test_position_integrity.py
"""
input: positions 表
output: 12 项检查结果 (字段完整、盈亏计算、评分范围、期权字段)
pos: 验证持仓记录的数据完整性

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

对应检查项: DI-POS-001 ~ DI-POS-012
"""
import pytest
from .conftest import execute_check, execute_query


class TestPositionIntegrity:
    """Position 表完整性检查"""

    def test_di_pos_001_required_fields_not_null(self, db_session):
        """DI-POS-001: 基础字段非空"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE symbol IS NULL
               OR direction IS NULL
               OR status IS NULL
               OR open_price IS NULL
               OR open_time IS NULL
               OR quantity IS NULL
        """)
        assert count == 0, f"发现 {count} 条持仓记录缺少必填字段"

    def test_di_pos_002_valid_direction_enum(self, db_session):
        """DI-POS-002: 方向枚举值有效"""
        result = execute_query(db_session, """
            SELECT DISTINCT direction FROM positions
            WHERE direction NOT IN ('long', 'short')
        """)
        assert len(result) == 0, f"发现无效方向值: {[r[0] for r in result]}"

    def test_di_pos_003_valid_status_enum(self, db_session):
        """DI-POS-003: 状态枚举值有效"""
        result = execute_query(db_session, """
            SELECT DISTINCT status FROM positions
            WHERE status NOT IN ('OPEN', 'CLOSED', 'PARTIALLY_CLOSED')
        """)
        assert len(result) == 0, f"发现无效状态值: {[r[0] for r in result]}"

    def test_di_pos_004_closed_position_complete(self, db_session):
        """DI-POS-004: 已平仓持仓字段完整"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE status = 'CLOSED'
              AND (close_price IS NULL
                   OR close_time IS NULL
                   OR net_pnl IS NULL)
        """)
        assert count == 0, f"发现 {count} 条已平仓持仓缺少平仓信息"

    def test_di_pos_005_open_position_fields_null(self, db_session):
        """DI-POS-005: 开放持仓字段为空"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE status = 'OPEN'
              AND (close_price IS NOT NULL
                   OR close_time IS NOT NULL)
        """)
        assert count == 0, f"发现 {count} 条开放持仓有平仓信息"

    def test_di_pos_006_long_pnl_calculation(self, db_session):
        """DI-POS-006: 多头盈亏计算正确"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE direction = 'long'
              AND status = 'CLOSED'
              AND ABS(realized_pnl - (close_price - open_price) * quantity *
                  CASE WHEN is_option = 1 THEN 100 ELSE 1 END) > 0.01
        """)
        assert count == 0, f"发现 {count} 条多头持仓盈亏计算错误"

    def test_di_pos_007_short_pnl_calculation(self, db_session):
        """DI-POS-007: 空头盈亏计算正确"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE direction = 'short'
              AND status = 'CLOSED'
              AND ABS(realized_pnl - (open_price - close_price) * quantity *
                  CASE WHEN is_option = 1 THEN 100 ELSE 1 END) > 0.01
        """)
        assert count == 0, f"发现 {count} 条空头持仓盈亏计算错误"

    def test_di_pos_008_net_pnl_calculation(self, db_session):
        """DI-POS-008: 净盈亏计算正确"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE status = 'CLOSED'
              AND ABS(net_pnl - (realized_pnl - total_fees)) > 0.01
        """)
        assert count == 0, f"发现 {count} 条持仓净盈亏计算错误"

    def test_di_pos_010_score_range_valid(self, db_session):
        """DI-POS-010: 评分范围有效 (0-100)"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE overall_score IS NOT NULL
              AND (overall_score < 0 OR overall_score > 100)
        """)
        assert count == 0, f"发现 {count} 条持仓总评分超出范围"

    def test_di_pos_011_grade_matches_score(self, db_session):
        """DI-POS-011: 评分等级与分数匹配

        等级划分（支持细分等级）：
        A+: 95-100, A: 90-94, A-: 85-89
        B+: 80-84, B: 75-79, B-: 70-74
        C+: 65-69, C: 60-64, C-: 55-59
        D: 50-54, F: 0-49
        """
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE overall_score IS NOT NULL
              AND score_grade IS NOT NULL
              AND NOT (
                (overall_score >= 95 AND score_grade = 'A+') OR
                (overall_score >= 90 AND overall_score < 95 AND score_grade = 'A') OR
                (overall_score >= 85 AND overall_score < 90 AND score_grade = 'A-') OR
                (overall_score >= 80 AND overall_score < 85 AND score_grade = 'B+') OR
                (overall_score >= 75 AND overall_score < 80 AND score_grade = 'B') OR
                (overall_score >= 70 AND overall_score < 75 AND score_grade = 'B-') OR
                (overall_score >= 65 AND overall_score < 70 AND score_grade = 'C+') OR
                (overall_score >= 60 AND overall_score < 65 AND score_grade = 'C') OR
                (overall_score >= 55 AND overall_score < 60 AND score_grade = 'C-') OR
                (overall_score >= 50 AND overall_score < 55 AND score_grade = 'D') OR
                (overall_score < 50 AND score_grade = 'F')
              )
        """)
        assert count == 0, f"发现 {count} 条持仓评分等级与分数不匹配"

    def test_di_pos_012_option_fields_consistency(self, db_session):
        """DI-POS-012: 期权字段一致性"""
        count = execute_check(db_session, """
            SELECT COUNT(*) FROM positions
            WHERE is_option = 1
              AND (option_type IS NULL
                   OR strike_price IS NULL
                   OR expiry_date IS NULL)
        """)
        assert count == 0, f"发现 {count} 条期权持仓字段不完整"
