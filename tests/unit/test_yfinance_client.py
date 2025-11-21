"""
Unit tests for YFinanceClient

Uses mocking to test without making real API calls
"""

import pytest
import pandas as pd
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import time

from src.data_sources.yfinance_client import YFinanceClient
from src.data_sources.base_client import (
    DataNotFoundError,
    InvalidSymbolError,
    RateLimitError,
    DataSourceError
)


class TestYFinanceClientInit:
    """Test YFinanceClient initialization"""

    def test_init_default_params(self):
        """Test initialization with default parameters"""
        client = YFinanceClient()
        assert client.rate_limit == 2000
        assert client.rate_window_seconds == 3600
        assert client.request_times == []

    def test_init_custom_params(self):
        """Test initialization with custom parameters"""
        client = YFinanceClient(rate_limit=1000, rate_window_seconds=1800)
        assert client.rate_limit == 1000
        assert client.rate_window_seconds == 1800

    def test_get_source_name(self):
        """Test get_source_name method"""
        client = YFinanceClient()
        assert client.get_source_name() == 'yfinance'


class TestYFinanceClientAvailability:
    """Test is_available method"""

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_is_available_success(self, mock_ticker):
        """Test availability check when yfinance works"""
        # Mock successful response
        mock_instance = Mock()
        mock_instance.info = {'symbol': 'SPY', 'shortName': 'SPDR S&P 500'}
        mock_ticker.return_value = mock_instance

        client = YFinanceClient()
        assert client.is_available() is True

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_is_available_failure(self, mock_ticker):
        """Test availability check when yfinance fails"""
        # Mock failure
        mock_ticker.side_effect = Exception("Network error")

        client = YFinanceClient()
        assert client.is_available() is False

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_is_available_empty_info(self, mock_ticker):
        """Test availability check with empty info"""
        mock_instance = Mock()
        mock_instance.info = {}
        mock_ticker.return_value = mock_instance

        client = YFinanceClient()
        assert client.is_available() is False


class TestYFinanceClientOHLCV:
    """Test get_ohlcv method"""

    @pytest.fixture
    def client(self):
        """Create client with high rate limit for testing"""
        return YFinanceClient(rate_limit=10000)

    @pytest.fixture
    def sample_df(self):
        """Create sample OHLCV DataFrame"""
        return pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [102.0, 103.0, 104.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [101.0, 102.0, 103.0],
            'Volume': [1000000, 1100000, 1200000]
        }, index=pd.DatetimeIndex([
            '2024-01-01', '2024-01-02', '2024-01-03'
        ]))

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_get_ohlcv_success(self, mock_ticker, client, sample_df):
        """Test successful OHLCV data fetch"""
        # Mock successful response
        mock_instance = Mock()
        mock_instance.history.return_value = sample_df
        mock_ticker.return_value = mock_instance

        result = client.get_ohlcv(
            'AAPL',
            date(2024, 1, 1),
            date(2024, 1, 3)
        )

        assert len(result) == 3
        assert 'Open' in result.columns
        assert 'Close' in result.columns
        assert result['Close'].iloc[0] == 101.0

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_get_ohlcv_empty_data(self, mock_ticker, client):
        """Test when no data is returned"""
        mock_instance = Mock()
        mock_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_instance

        with pytest.raises(DataNotFoundError, match="No data found"):
            client.get_ohlcv('INVALID', date(2024, 1, 1), date(2024, 1, 3))

    def test_get_ohlcv_invalid_symbol(self, client):
        """Test with invalid symbol"""
        with pytest.raises(InvalidSymbolError, match="Invalid symbol"):
            client.get_ohlcv('', date(2024, 1, 1), date(2024, 1, 3))

    def test_get_ohlcv_invalid_date_range(self, client):
        """Test with invalid date range"""
        with pytest.raises(ValueError, match="Invalid date range"):
            client.get_ohlcv(
                'AAPL',
                date(2024, 1, 31),  # Start after end
                date(2024, 1, 1)
            )

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_get_ohlcv_lowercase_columns(self, mock_ticker, client):
        """Test standardization of lowercase column names"""
        # Create DataFrame with lowercase columns
        df_lowercase = pd.DataFrame({
            'open': [100.0],
            'high': [102.0],
            'low': [99.0],
            'close': [101.0],
            'volume': [1000000]
        }, index=pd.DatetimeIndex(['2024-01-01']))

        mock_instance = Mock()
        mock_instance.history.return_value = df_lowercase
        mock_ticker.return_value = mock_instance

        result = client.get_ohlcv('AAPL', date(2024, 1, 1), date(2024, 1, 1))

        # Should be standardized to title case
        assert 'Open' in result.columns
        assert 'Close' in result.columns

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_get_ohlcv_with_interval(self, mock_ticker, client, sample_df):
        """Test fetching with different interval"""
        mock_instance = Mock()
        mock_instance.history.return_value = sample_df
        mock_ticker.return_value = mock_instance

        client.get_ohlcv(
            'AAPL',
            date(2024, 1, 1),
            date(2024, 1, 3),
            interval='1h'
        )

        # Verify interval was passed to yfinance
        mock_instance.history.assert_called_once()
        call_kwargs = mock_instance.history.call_args[1]
        assert call_kwargs['interval'] == '1h'


class TestYFinanceClientStockInfo:
    """Test get_stock_info method"""

    @pytest.fixture
    def client(self):
        return YFinanceClient(rate_limit=10000)

    @pytest.fixture
    def sample_info(self):
        """Sample stock info data"""
        return {
            'symbol': 'AAPL',
            'longName': 'Apple Inc.',
            'shortName': 'Apple',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'marketCap': 3000000000000,
            'currency': 'USD',
            'exchange': 'NMS',
            'country': 'United States',
            'currentPrice': 150.0,
            'previousClose': 149.0,
            'trailingPE': 25.5,
            'dividendYield': 0.005
        }

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_get_stock_info_success(self, mock_ticker, client, sample_info):
        """Test successful stock info fetch"""
        mock_instance = Mock()
        mock_instance.info = sample_info
        mock_ticker.return_value = mock_instance

        result = client.get_stock_info('AAPL')

        assert result['symbol'] == 'AAPL'
        assert result['name'] == 'Apple Inc.'
        assert result['sector'] == 'Technology'
        assert result['market_cap'] == 3000000000000

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_get_stock_info_empty(self, mock_ticker, client):
        """Test when no info is returned"""
        mock_instance = Mock()
        mock_instance.info = {}
        mock_ticker.return_value = mock_instance

        with pytest.raises(DataNotFoundError, match="No info found"):
            client.get_stock_info('INVALID')

    def test_get_stock_info_invalid_symbol(self, client):
        """Test with invalid symbol"""
        with pytest.raises(InvalidSymbolError):
            client.get_stock_info('')


class TestYFinanceClientRateLimit:
    """Test rate limiting functionality"""

    def test_rate_limit_not_exceeded(self):
        """Test normal operation within rate limit"""
        client = YFinanceClient(rate_limit=10, rate_window_seconds=60)

        # Add 5 requests (well below limit)
        for _ in range(5):
            client._record_request()

        # Should not raise
        client._check_rate_limit()

    def test_rate_limit_exceeded(self):
        """Test rate limit enforcement"""
        client = YFinanceClient(rate_limit=5, rate_window_seconds=60)

        # Fill up the rate limit
        for _ in range(5):
            client._record_request()

        # Next check should raise RateLimitError
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            client._check_rate_limit()

    def test_rate_limit_sliding_window(self):
        """Test sliding window behavior"""
        client = YFinanceClient(rate_limit=5, rate_window_seconds=2)

        # Fill up rate limit
        for _ in range(5):
            client._record_request()

        # Should raise immediately
        with pytest.raises(RateLimitError):
            client._check_rate_limit()

        # Wait for window to pass
        time.sleep(2.1)

        # Should not raise after window expires
        client._check_rate_limit()

    def test_record_request(self):
        """Test request recording"""
        client = YFinanceClient()
        initial_count = len(client.request_times)

        client._record_request()

        assert len(client.request_times) == initial_count + 1


class TestYFinanceClientMultipleOHLCV:
    """Test get_multiple_ohlcv method"""

    @pytest.fixture
    def client(self):
        return YFinanceClient(rate_limit=10000)

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.DatetimeIndex(['2024-01-01']))

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_get_multiple_ohlcv_success(self, mock_sleep, mock_ticker, client, sample_df):
        """Test batch fetching multiple symbols"""
        mock_instance = Mock()
        mock_instance.history.return_value = sample_df
        mock_ticker.return_value = mock_instance

        symbols = ['AAPL', 'MSFT', 'GOOGL']
        result = client.get_multiple_ohlcv(
            symbols,
            date(2024, 1, 1),
            date(2024, 1, 1)
        )

        assert len(result) == 3
        assert 'AAPL' in result
        assert 'MSFT' in result
        assert 'GOOGL' in result

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    @patch('time.sleep')
    def test_get_multiple_ohlcv_partial_failure(self, mock_sleep, mock_ticker, client, sample_df):
        """Test batch fetching with some failures"""
        def side_effect(symbol):
            mock_instance = Mock()
            if symbol == 'INVALID':
                mock_instance.history.return_value = pd.DataFrame()  # Empty
            else:
                mock_instance.history.return_value = sample_df
            return mock_instance

        mock_ticker.side_effect = side_effect

        symbols = ['AAPL', 'INVALID', 'MSFT']
        result = client.get_multiple_ohlcv(
            symbols,
            date(2024, 1, 1),
            date(2024, 1, 1)
        )

        # Should have 2 successful fetches
        assert len(result) == 2
        assert 'AAPL' in result
        assert 'MSFT' in result
        assert 'INVALID' not in result


class TestYFinanceClientSymbolConversion:
    """Test convert_symbol_for_yfinance method"""

    @pytest.fixture
    def client(self):
        return YFinanceClient()

    def test_convert_us_stock(self, client):
        """Test US stock symbols (no conversion needed)"""
        assert client.convert_symbol_for_yfinance('AAPL') == 'AAPL'
        assert client.convert_symbol_for_yfinance('BRK.B') == 'BRK.B'  # Already has dot

    def test_convert_hk_stock(self, client):
        """Test Hong Kong stock conversion"""
        assert client.convert_symbol_for_yfinance('09988') == '9988.HK'
        assert client.convert_symbol_for_yfinance('01810') == '1810.HK'
        assert client.convert_symbol_for_yfinance('00700') == '700.HK'

    def test_convert_cn_stock_shanghai(self, client):
        """Test Chinese stock (Shanghai) conversion"""
        assert client.convert_symbol_for_yfinance('600000') == '600000.SS'
        assert client.convert_symbol_for_yfinance('601857') == '601857.SS'
        assert client.convert_symbol_for_yfinance('688111') == '688111.SS'

    def test_convert_cn_stock_shenzhen(self, client):
        """Test Chinese stock (Shenzhen) conversion"""
        assert client.convert_symbol_for_yfinance('000001') == '000001.SZ'
        assert client.convert_symbol_for_yfinance('002594') == '002594.SZ'
        assert client.convert_symbol_for_yfinance('300750') == '300750.SZ'

    def test_convert_already_converted(self, client):
        """Test symbols already in yfinance format"""
        assert client.convert_symbol_for_yfinance('9988.HK') == '9988.HK'
        assert client.convert_symbol_for_yfinance('600000.SS') == '600000.SS'
        assert client.convert_symbol_for_yfinance('000001.SZ') == '000001.SZ'

    def test_convert_with_whitespace(self, client):
        """Test symbol with whitespace"""
        assert client.convert_symbol_for_yfinance('  AAPL  ') == 'AAPL'
        assert client.convert_symbol_for_yfinance('  09988  ') == '9988.HK'


class TestYFinanceClientRetry:
    """Test retry mechanism"""

    @pytest.fixture
    def client(self):
        return YFinanceClient(rate_limit=10000)

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_retry_on_connection_error(self, mock_ticker, client):
        """Test that connection errors trigger retry"""
        mock_instance = Mock()

        # First two calls fail, third succeeds
        sample_df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.DatetimeIndex(['2024-01-01']))

        mock_instance.history.side_effect = [
            ConnectionError("Network error"),
            ConnectionError("Network error"),
            sample_df
        ]
        mock_ticker.return_value = mock_instance

        # Should succeed after retries
        result = client.get_ohlcv('AAPL', date(2024, 1, 1), date(2024, 1, 1))
        assert len(result) == 1

    @patch('src.data_sources.yfinance_client.yf.Ticker')
    def test_retry_exhausted(self, mock_ticker, client):
        """Test when all retries are exhausted"""
        mock_instance = Mock()
        mock_instance.history.side_effect = ConnectionError("Persistent error")
        mock_ticker.return_value = mock_instance

        # Should raise after max retries
        with pytest.raises(DataSourceError):
            client.get_ohlcv('AAPL', date(2024, 1, 1), date(2024, 1, 1))
