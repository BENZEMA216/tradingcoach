"""
Unit tests for visualization metrics components
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from visualization.components.metrics import (
    grade_badge,
    pnl_badge,
    percentage_badge,
    status_badge,
    coverage_bar,
    dimension_scores_table
)


class TestGradeBadge:
    """Test grade_badge function"""

    def test_a_plus_grade(self):
        """Test A+ grade badge"""
        html = grade_badge('A+')

        assert 'A+' in html
        assert 'span' in html
        assert 'background-color' in html
        assert '#00C851' in html  # Green color

    def test_b_grade(self):
        """Test B grade badge"""
        html = grade_badge('B')

        assert 'B' in html
        assert '#4285F4' in html  # Blue color

    def test_c_grade(self):
        """Test C grade badge"""
        html = grade_badge('C')

        assert 'C' in html
        assert '#FFA000' in html  # Orange color

    def test_d_grade(self):
        """Test D grade badge"""
        html = grade_badge('D')

        assert 'D' in html
        assert '#FF3547' in html  # Red color

    def test_f_grade(self):
        """Test F grade badge"""
        html = grade_badge('F')

        assert 'F' in html
        assert '#CC0000' in html  # Dark red color

    def test_unknown_grade(self):
        """Test unknown grade uses default color"""
        html = grade_badge('X')

        assert 'X' in html
        assert '#999999' in html  # Gray color


class TestPnlBadge:
    """Test pnl_badge function"""

    def test_positive_pnl(self):
        """Test positive P&L badge"""
        html = pnl_badge(500.25)

        assert '+$500.25' in html
        assert '#00C851' in html  # Green color
        assert 'span' in html

    def test_negative_pnl(self):
        """Test negative P&L badge"""
        html = pnl_badge(-200.50)

        assert '$-200.50' in html or '-$200.50' in html  # Accept either format
        assert '#FF3547' in html  # Red color

    def test_zero_pnl(self):
        """Test zero P&L badge"""
        html = pnl_badge(0.0)

        assert '$0.00' in html
        assert '#00C851' in html  # Green color (>=0)

    def test_large_pnl(self):
        """Test large P&L with comma formatting"""
        html = pnl_badge(10000.99)

        assert '10,000.99' in html


class TestPercentageBadge:
    """Test percentage_badge function"""

    def test_positive_percentage(self):
        """Test positive percentage badge"""
        html = percentage_badge(5.75)

        assert '+5.75%' in html
        assert '#00C851' in html  # Green color

    def test_negative_percentage(self):
        """Test negative percentage badge"""
        html = percentage_badge(-3.25)

        assert '-3.25%' in html
        assert '#FF3547' in html  # Red color

    def test_zero_percentage(self):
        """Test zero percentage badge"""
        html = percentage_badge(0.0)

        assert '0.00%' in html
        assert '#00C851' in html  # Green color


class TestStatusBadge:
    """Test status_badge function"""

    def test_pass_status(self):
        """Test pass status badge"""
        html = status_badge('通过')

        assert '通过' in html
        assert '#00C851' in html  # Green color

    def test_checkmark_status(self):
        """Test checkmark status badge"""
        html = status_badge('✓')

        assert '✓' in html
        assert '#00C851' in html  # Green color

    def test_fail_status(self):
        """Test fail status badge"""
        html = status_badge('失败')

        assert '失败' in html
        assert '#FF3547' in html  # Red color

    def test_cross_status(self):
        """Test cross status badge"""
        html = status_badge('✗')

        assert '✗' in html
        assert '#FF3547' in html  # Red color

    def test_warning_status(self):
        """Test warning status badge"""
        html = status_badge('警告')

        assert '警告' in html
        assert '#FFA000' in html  # Orange color

    def test_warning_symbol_status(self):
        """Test warning symbol status badge"""
        html = status_badge('⚠')

        assert '⚠' in html
        assert '#FFA000' in html  # Orange color

    def test_missing_status(self):
        """Test missing status badge"""
        html = status_badge('缺失')

        assert '缺失' in html
        assert '#999999' in html  # Gray color

    def test_unknown_status(self):
        """Test unknown status uses default color"""
        html = status_badge('未知')

        assert '未知' in html
        assert '#4285F4' in html  # Blue color


class TestCoverageBar:
    """Test coverage_bar function"""

    def test_has_data(self):
        """Test coverage bar when data exists"""
        html = coverage_bar(True)

        assert '✓' in html
        assert '#00C851' in html  # Green color
        assert 'div' in html

    def test_no_data(self):
        """Test coverage bar when data missing"""
        html = coverage_bar(False)

        assert '✗' in html
        assert '#FF3547' in html  # Red color

    def test_custom_width(self):
        """Test custom width"""
        html = coverage_bar(True, width=200)

        assert 'width: 200px' in html


class TestDimensionScoresTable:
    """Test dimension_scores_table function"""

    def test_all_dimensions(self):
        """Test table with all dimensions"""
        html = dimension_scores_table(
            entry=70.0,
            exit=80.0,
            trend=75.0,
            risk=85.0
        )

        assert 'table' in html
        assert '进场质量' in html
        assert '出场质量' in html
        assert '趋势质量' in html
        assert '风险管理' in html
        assert '70.0' in html
        assert '80.0' in html
        assert '75.0' in html
        assert '85.0' in html

    def test_high_score_color(self):
        """Test that high scores get green color"""
        html = dimension_scores_table(
            entry=85.0,
            exit=85.0,
            trend=85.0,
            risk=85.0
        )

        # Should have green color for scores >= 80
        assert '#00C851' in html

    def test_medium_score_color(self):
        """Test that medium scores get blue color"""
        html = dimension_scores_table(
            entry=65.0,
            exit=65.0,
            trend=65.0,
            risk=65.0
        )

        # Should have blue color for scores 60-79
        assert '#4285F4' in html

    def test_low_score_color(self):
        """Test that low scores get orange/red color"""
        html = dimension_scores_table(
            entry=45.0,
            exit=35.0,
            trend=25.0,
            risk=55.0
        )

        # Should have orange for 40-59 and red for <40
        assert '#FFA000' in html or '#FF3547' in html

    def test_weight_display(self):
        """Test that weights are displayed correctly"""
        html = dimension_scores_table(
            entry=70.0,
            exit=70.0,
            trend=70.0,
            risk=70.0
        )

        assert '(30%)' in html  # Entry weight
        assert '(25%)' in html  # Exit and Trend weight
        assert '(20%)' in html  # Risk weight


class TestMetricsIntegration:
    """Integration tests for metrics components"""

    def test_all_badges_generate_html(self):
        """Test that all badge functions generate valid HTML"""
        badges = [
            grade_badge('A'),
            pnl_badge(100.0),
            percentage_badge(5.0),
            status_badge('通过'),
            coverage_bar(True)
        ]

        for badge_html in badges:
            assert isinstance(badge_html, str)
            assert len(badge_html) > 0
            assert '<' in badge_html  # Contains HTML tags

    def test_table_generates_valid_html(self):
        """Test that dimension scores table generates valid HTML"""
        html = dimension_scores_table(70.0, 75.0, 80.0, 85.0)

        assert isinstance(html, str)
        assert '<table' in html
        assert '</table>' in html
        assert '<tr>' in html
        assert '<td' in html  # Check for td tag (with or without attributes)

    def test_html_escaping(self):
        """Test that special characters are handled"""
        # Status badge should handle special characters
        html = status_badge('Test<>Status')

        # Should still generate HTML (though Streamlit will escape it)
        assert isinstance(html, str)

    def test_extreme_values(self):
        """Test with extreme values"""
        # Very large P&L
        html1 = pnl_badge(999999999.99)
        assert '999,999,999.99' in html1

        # Very small percentage
        html2 = percentage_badge(0.01)
        assert '0.01%' in html2

        # Extreme scores
        html3 = dimension_scores_table(100.0, 0.0, 50.0, 25.0)
        assert '100.0' in html3
        assert '0.0' in html3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
