"""
Unit tests for BaseDataClient abstract class

Tests utility methods like standardize_dataframe, validate_symbol, validate_date_range
"""

import pytest
import pandas as pd
from datetime import date, datetime, timedelta

from src.data_sources.base_client import (
    BaseDataClient,
    DataSourceError,
    RateLimitError,
    DataNotFoundError,
    InvalidSymbolError
)


# Create a concrete implementation for testing abstract base class
class MockDataClient(BaseDataClient):
    """Mock implementation for testing"""

    def get_ohlcv(self, symbol, start_date, end_date, interval='1d'):
        return pd.DataFrame()

    def get_stock_info(self, symbol):
        return {}

    def is_available(self):
        return True

    def get_source_name(self):
        return 'mock'


class TestBaseDataClient:
    """Test BaseDataClient utility methods"""

    @pytest.fixture
    def client(self):
        """Create mock client for testing"""
        return MockDataClient()

    # ==================== standardize_dataframe tests ====================

    def test_standardize_dataframe_basic(self, client):
        """Test basic column standardization"""
        df = pd.DataFrame({
            'open': [100.0, 101.0],
            'high': [102.0, 103.0],
            'low': [99.0, 100.0],
            'close': [101.0, 102.0],
            'volume': [1000, 1500]
        }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02']))

        result = client.standardize_dataframe(df)

        assert 'Open' in result.columns
        assert 'High' in result.columns
        assert 'Low' in result.columns
        assert 'Close' in result.columns
        assert 'Volume' in result.columns
        assert len(result) == 2

    def test_standardize_dataframe_already_standard(self, client):
        """Test DataFrame that's already in standard format"""
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000]
        }, index=pd.DatetimeIndex(['2024-01-01']))

        result = client.standardize_dataframe(df)

        assert list(result.columns[:5]) == ['Open', 'High', 'Low', 'Close', 'Volume']

    def test_standardize_dataframe_missing_columns(self, client):
        """Test DataFrame with missing required columns"""
        df = pd.DataFrame({
            'open': [100.0],
            'high': [102.0],
            'low': [99.0]
            # Missing Close and Volume
        }, index=pd.DatetimeIndex(['2024-01-01']))

        with pytest.raises(ValueError, match="缺少必需的列"):
            client.standardize_dataframe(df)

    def test_standardize_dataframe_empty(self, client):
        """Test empty DataFrame"""
        df = pd.DataFrame()
        result = client.standardize_dataframe(df)
        assert result.empty

    def test_standardize_dataframe_removes_nan_rows(self, client):
        """Test that rows with NaN Close are removed"""
        df = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 103.0, 104.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [101.0, None, 103.0],  # Middle row has NaN
            'Volume': [1000, 1500, 2000]
        }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02', '2024-01-03']))

        result = client.standardize_dataframe(df)

        assert len(result) == 2  # Middle row removed
        assert result.index[0] == pd.Timestamp('2024-01-01')
        assert result.index[1] == pd.Timestamp('2024-01-03')

    def test_standardize_dataframe_converts_index_to_datetime(self, client):
        """Test conversion of non-datetime index"""
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000]
        }, index=['2024-01-01'])  # String index

        result = client.standardize_dataframe(df)

        assert isinstance(result.index, pd.DatetimeIndex)

    def test_standardize_dataframe_with_adj_close(self, client):
        """Test DataFrame with Adj Close column"""
        df = pd.DataFrame({
            'open': [100.0],
            'high': [102.0],
            'low': [99.0],
            'close': [101.0],
            'volume': [1000],
            'adj close': [100.5]
        }, index=pd.DatetimeIndex(['2024-01-01']))

        result = client.standardize_dataframe(df)

        assert 'Adj Close' in result.columns
        assert result['Adj Close'].iloc[0] == 100.5

    # ==================== validate_symbol tests ====================

    def test_validate_symbol_valid_us_stock(self, client):
        """Test valid US stock symbols"""
        assert client.validate_symbol('AAPL') is True
        assert client.validate_symbol('TSLA') is True
        assert client.validate_symbol('BRK.B') is True

    def test_validate_symbol_valid_hk_stock(self, client):
        """Test valid Hong Kong stock symbols"""
        assert client.validate_symbol('09988') is True
        assert client.validate_symbol('01810') is True
        assert client.validate_symbol('9988.HK') is True

    def test_validate_symbol_valid_cn_stock(self, client):
        """Test valid Chinese stock symbols"""
        assert client.validate_symbol('600000') is True
        assert client.validate_symbol('600000.SS') is True
        assert client.validate_symbol('000001.SZ') is True

    def test_validate_symbol_invalid_empty(self, client):
        """Test empty or None symbols"""
        assert client.validate_symbol('') is False
        assert client.validate_symbol(None) is False
        assert client.validate_symbol('   ') is False  # Only whitespace

    def test_validate_symbol_invalid_type(self, client):
        """Test non-string symbols"""
        assert client.validate_symbol(123) is False
        assert client.validate_symbol(['AAPL']) is False

    def test_validate_symbol_invalid_too_long(self, client):
        """Test symbols that are too long"""
        assert client.validate_symbol('A' * 51) is False

    # ==================== validate_date_range tests ====================

    def test_validate_date_range_valid(self, client):
        """Test valid date range"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        assert client.validate_date_range(start, end) is True

    def test_validate_date_range_same_day(self, client):
        """Test date range with same start and end"""
        today = date.today()
        assert client.validate_date_range(today, today) is True

    def test_validate_date_range_invalid_start_after_end(self, client):
        """Test invalid range where start > end"""
        start = date(2024, 2, 1)
        end = date(2024, 1, 1)
        assert client.validate_date_range(start, end) is False

    def test_validate_date_range_invalid_future_end(self, client):
        """Test invalid range with future end date"""
        start = date.today()
        end = date.today() + timedelta(days=30)
        assert client.validate_date_range(start, end) is False

    def test_validate_date_range_invalid_type(self, client):
        """Test invalid types for dates"""
        assert client.validate_date_range('2024-01-01', '2024-01-31') is False
        assert client.validate_date_range(None, date.today()) is False
        assert client.validate_date_range(date.today(), None) is False

    def test_validate_date_range_datetime_objects(self, client):
        """Test with datetime objects instead of date objects"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        # datetime is subclass of date, so should work
        assert client.validate_date_range(start.date(), end.date()) is True


class TestExceptions:
    """Test custom exception classes"""

    def test_data_source_error(self):
        """Test DataSourceError"""
        with pytest.raises(DataSourceError):
            raise DataSourceError("Test error")

    def test_rate_limit_error_inheritance(self):
        """Test RateLimitError inherits from DataSourceError"""
        with pytest.raises(DataSourceError):
            raise RateLimitError("Rate limit exceeded")

    def test_data_not_found_error_inheritance(self):
        """Test DataNotFoundError inherits from DataSourceError"""
        with pytest.raises(DataSourceError):
            raise DataNotFoundError("Data not found")

    def test_invalid_symbol_error_inheritance(self):
        """Test InvalidSymbolError inherits from DataSourceError"""
        with pytest.raises(DataSourceError):
            raise InvalidSymbolError("Invalid symbol")

    def test_exception_messages(self):
        """Test exception messages are preserved"""
        msg = "Custom error message"

        with pytest.raises(DataSourceError, match=msg):
            raise DataSourceError(msg)

        with pytest.raises(RateLimitError, match=msg):
            raise RateLimitError(msg)


