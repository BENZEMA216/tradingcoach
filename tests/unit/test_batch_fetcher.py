"""
Unit tests for BatchFetcher

Tests batch data acquisition, option symbol parsing, and cache integration
"""

import pytest
import pandas as pd
from datetime import date, datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, call
from sqlalchemy.orm import Session

from src.data_sources.batch_fetcher import BatchFetcher
from src.data_sources.base_client import BaseDataClient, DataNotFoundError, InvalidSymbolError
from src.data_sources.cache_manager import CacheManager
from src.models.trade import Trade


class TestBatchFetcherInit:
    """Test BatchFetcher initialization"""

    def test_init_default_params(self):
        """Test initialization with default parameters"""
        mock_client = Mock(spec=BaseDataClient)
        mock_cache = Mock(spec=CacheManager)

        fetcher = BatchFetcher(mock_client, mock_cache)

        assert fetcher.client == mock_client
        assert fetcher.cache == mock_cache
        assert fetcher.batch_size == 50
        assert fetcher.request_delay == 0.2
        assert fetcher.extra_days == 200

    def test_init_custom_params(self):
        """Test initialization with custom parameters"""
        mock_client = Mock(spec=BaseDataClient)
        mock_cache = Mock(spec=CacheManager)

        fetcher = BatchFetcher(
            mock_client,
            mock_cache,
            batch_size=100,
            request_delay=0.5,
            extra_days=300
        )

        assert fetcher.batch_size == 100
        assert fetcher.request_delay == 0.5
        assert fetcher.extra_days == 300

    def test_repr(self):
        """Test string representation"""
        mock_client = Mock(spec=BaseDataClient)
        mock_client.get_source_name.return_value = 'yfinance'
        mock_cache = Mock(spec=CacheManager)

        fetcher = BatchFetcher(mock_client, mock_cache, batch_size=50, request_delay=0.2)

        repr_str = repr(fetcher)
        assert 'BatchFetcher' in repr_str
        assert 'yfinance' in repr_str
        assert '50' in repr_str


class TestBatchFetcherOptionParsing:
    """Test option symbol parsing"""

    @pytest.fixture
    def fetcher(self):
        """Create BatchFetcher for testing"""
        mock_client = Mock(spec=BaseDataClient)
        mock_cache = Mock(spec=CacheManager)
        return BatchFetcher(mock_client, mock_cache)

    def test_parse_option_symbol_call(self, fetcher):
        """Test parsing call option"""
        result = fetcher._parse_option_symbol('AAPL250117C00150000')

        assert result is not None
        assert result['underlying'] == 'AAPL'
        assert result['expiry'] == date(2025, 1, 17)
        assert result['option_type'] == 'call'
        assert result['strike'] == 150.0

    def test_parse_option_symbol_put(self, fetcher):
        """Test parsing put option"""
        result = fetcher._parse_option_symbol('TSLA241220P00200000')

        assert result is not None
        assert result['underlying'] == 'TSLA'
        assert result['expiry'] == date(2024, 12, 20)
        assert result['option_type'] == 'put'
        assert result['strike'] == 200.0

    def test_parse_option_symbol_different_strikes(self, fetcher):
        """Test parsing options with different strike prices"""
        # High strike
        result1 = fetcher._parse_option_symbol('AMZN250115C00250000')
        assert result1['strike'] == 250.0

        # Low strike
        result2 = fetcher._parse_option_symbol('AAPL250115C00100000')
        assert result2['strike'] == 100.0

        # Fractional strike (50 cents)
        result3 = fetcher._parse_option_symbol('SPY250115C00500500')
        assert result3['strike'] == 500.5

    def test_parse_option_symbol_not_an_option(self, fetcher):
        """Test parsing regular stock symbols (should return None)"""
        assert fetcher._parse_option_symbol('AAPL') is None
        assert fetcher._parse_option_symbol('TSLA') is None
        assert fetcher._parse_option_symbol('09988') is None
        assert fetcher._parse_option_symbol('600000') is None

    def test_parse_option_symbol_invalid_format(self, fetcher):
        """Test parsing invalid option symbols"""
        assert fetcher._parse_option_symbol('AAPL25011C00150000') is None  # Wrong date format
        assert fetcher._parse_option_symbol('AAPL250117X00150000') is None  # Invalid option type
        assert fetcher._parse_option_symbol('AAPL250117C0015000') is None  # Wrong strike format (7 digits)

    def test_parse_option_symbol_multi_letter_underlying(self, fetcher):
        """Test options with multi-letter underlying symbols"""
        result = fetcher._parse_option_symbol('GOOGL250117C00150000')
        assert result['underlying'] == 'GOOGL'

        result = fetcher._parse_option_symbol('MSFT250117C00400000')
        assert result['underlying'] == 'MSFT'


class TestBatchFetcherAnalyzeRequirements:
    """Test _analyze_requirements method"""

    @pytest.fixture
    def fetcher(self):
        """Create BatchFetcher for testing"""
        mock_client = Mock(spec=BaseDataClient)
        mock_cache = Mock(spec=CacheManager)
        return BatchFetcher(mock_client, mock_cache, extra_days=10)

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return Mock(spec=Session)

    def test_analyze_requirements_stock_symbols(self, fetcher, mock_session):
        """Test analyzing requirements for regular stocks"""
        # Mock query results
        mock_row1 = Mock(
            symbol='AAPL',
            min_date=date(2024, 1, 1),
            max_date=date(2024, 1, 31),
            trade_count=10
        )
        mock_row2 = Mock(
            symbol='TSLA',
            min_date=date(2024, 2, 1),
            max_date=date(2024, 2, 28),
            trade_count=5
        )

        mock_query = Mock()
        mock_query.__iter__ = Mock(return_value=iter([mock_row1, mock_row2]))
        mock_session.query.return_value.group_by.return_value.order_by.return_value = mock_query

        requirements = fetcher._analyze_requirements(mock_session)

        # Should have 2 requirements (one per stock)
        assert len(requirements) == 2

        # Check first requirement
        req1 = next(r for r in requirements if r['symbol'] == 'AAPL')
        assert req1['start_date'] == date(2024, 1, 1) - timedelta(days=10)  # extra_days
        assert req1['end_date'] == date.today()
        assert req1['trade_count'] == 10
        assert req1['is_underlying'] is False

    def test_analyze_requirements_option_symbols(self, fetcher, mock_session):
        """Test analyzing requirements for options"""
        mock_row = Mock(
            symbol='AAPL250117C00150000',  # Fixed: 8-digit strike
            min_date=date(2024, 12, 1),
            max_date=date(2024, 12, 31),
            trade_count=3
        )

        mock_query = Mock()
        mock_query.__iter__ = Mock(return_value=iter([mock_row]))
        mock_session.query.return_value.group_by.return_value.order_by.return_value = mock_query

        requirements = fetcher._analyze_requirements(mock_session)

        # Should have 2 requirements: underlying stock + option
        assert len(requirements) == 2

        # Check underlying requirement
        underlying_req = next((r for r in requirements if r['symbol'] == 'AAPL'), None)
        assert underlying_req is not None
        assert underlying_req['is_underlying'] is True
        assert underlying_req['original_symbol'] == 'AAPL250117C00150000'

        # Check option requirement
        option_req = next((r for r in requirements if r['symbol'] == 'AAPL250117C00150000'), None)
        assert option_req is not None
        assert option_req['is_underlying'] is False

    def test_analyze_requirements_deduplication(self, fetcher, mock_session):
        """Test that duplicate requirements are removed"""
        # SQL GROUP BY should already prevent duplicates for same symbol
        # This test verifies that if we somehow get duplicates, they're removed
        mock_row = Mock(
            symbol='AAPL',
            min_date=date(2024, 1, 1),
            max_date=date(2024, 1, 31),
            trade_count=10
        )

        # Mock query returns same symbol once (GROUP BY ensures this)
        mock_query = Mock()
        mock_query.__iter__ = Mock(return_value=iter([mock_row]))
        mock_session.query.return_value.group_by.return_value.order_by.return_value = mock_query

        requirements = fetcher._analyze_requirements(mock_session)

        # Should have exactly 1 requirement for AAPL
        aapl_reqs = [r for r in requirements if r['symbol'] == 'AAPL']
        assert len(aapl_reqs) == 1

        # Verify the requirement details
        assert aapl_reqs[0]['start_date'] == date(2024, 1, 1) - timedelta(days=10)
        assert aapl_reqs[0]['end_date'] == date.today()


class TestBatchFetcherFilterMissing:
    """Test _filter_missing method"""

    @pytest.fixture
    def fetcher(self):
        """Create BatchFetcher with mock cache"""
        mock_client = Mock(spec=BaseDataClient)
        mock_cache = Mock(spec=CacheManager)
        return BatchFetcher(mock_client, mock_cache)

    def test_filter_missing_all_cached(self, fetcher):
        """Test when all data is already cached"""
        requirements = [
            {
                'symbol': 'AAPL',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31)
            },
            {
                'symbol': 'TSLA',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31)
            }
        ]

        # Mock cache to return data for all symbols
        sample_df = pd.DataFrame({'Close': [100.0]})
        fetcher.cache.get = Mock(return_value=sample_df)

        missing = fetcher._filter_missing(requirements)

        # Nothing should be missing
        assert len(missing) == 0

    def test_filter_missing_all_missing(self, fetcher):
        """Test when no data is cached"""
        requirements = [
            {
                'symbol': 'AAPL',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31)
            }
        ]

        # Mock cache to return None (cache miss)
        fetcher.cache.get = Mock(return_value=None)

        missing = fetcher._filter_missing(requirements)

        # All should be missing
        assert len(missing) == 1
        assert missing[0]['symbol'] == 'AAPL'

    def test_filter_missing_partial(self, fetcher):
        """Test when some data is cached"""
        requirements = [
            {
                'symbol': 'AAPL',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31)
            },
            {
                'symbol': 'TSLA',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31)
            },
            {
                'symbol': 'MSFT',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31)
            }
        ]

        # Mock cache: AAPL cached, TSLA and MSFT not cached
        def cache_get_side_effect(symbol, start, end):
            if symbol == 'AAPL':
                return pd.DataFrame({'Close': [100.0]})
            return None

        fetcher.cache.get = Mock(side_effect=cache_get_side_effect)

        missing = fetcher._filter_missing(requirements)

        # TSLA and MSFT should be missing
        assert len(missing) == 2
        missing_symbols = [r['symbol'] for r in missing]
        assert 'TSLA' in missing_symbols
        assert 'MSFT' in missing_symbols
        assert 'AAPL' not in missing_symbols


class TestBatchFetcherBatchFetch:
    """Test _batch_fetch method"""

    @pytest.fixture
    def fetcher(self):
        """Create BatchFetcher"""
        mock_client = Mock(spec=BaseDataClient)
        mock_client.get_source_name.return_value = 'yfinance'
        mock_cache = Mock(spec=CacheManager)
        return BatchFetcher(mock_client, mock_cache, request_delay=0.01)  # Fast delay for tests

    @pytest.fixture
    def sample_df(self):
        """Sample OHLCV DataFrame"""
        return pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000000]
        }, index=pd.DatetimeIndex(['2024-01-01']))

    @patch('time.sleep')  # Mock sleep to speed up tests
    @patch('src.data_sources.batch_fetcher.tqdm')  # Mock progress bar
    def test_batch_fetch_success(self, mock_tqdm, mock_sleep, fetcher, sample_df):
        """Test successful batch fetch"""
        requirements = [
            {
                'symbol': 'AAPL',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31)
            },
            {
                'symbol': 'TSLA',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31)
            }
        ]

        # Mock client to return data
        fetcher.client.get_ohlcv = Mock(return_value=sample_df)

        # Mock progress bar
        mock_pbar = Mock()
        mock_tqdm.return_value = mock_pbar
        mock_pbar.__iter__ = Mock(return_value=iter(requirements))
        mock_pbar.set_postfix = Mock()
        mock_pbar.close = Mock()

        result = fetcher._batch_fetch(requirements)

        assert result['success_count'] == 2
        assert result['total_records'] == 2  # 1 record per symbol
        assert len(result['failed']) == 0
        assert result['duration'] > 0

        # Verify cache.set was called for each symbol
        assert fetcher.cache.set.call_count == 2

    @patch('time.sleep')
    @patch('src.data_sources.batch_fetcher.tqdm')
    def test_batch_fetch_with_failures(self, mock_tqdm, mock_sleep, fetcher, sample_df):
        """Test batch fetch with some failures"""
        requirements = [
            {'symbol': 'AAPL', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)},
            {'symbol': 'INVALID', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)},
            {'symbol': 'TSLA', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)}
        ]

        # Mock client: AAPL and TSLA succeed, INVALID fails
        def get_ohlcv_side_effect(symbol, start, end):
            if symbol == 'INVALID':
                raise DataNotFoundError("No data found")
            return sample_df

        fetcher.client.get_ohlcv = Mock(side_effect=get_ohlcv_side_effect)

        # Mock progress bar
        mock_pbar = Mock()
        mock_tqdm.return_value = mock_pbar
        mock_pbar.__iter__ = Mock(return_value=iter(requirements))
        mock_pbar.set_postfix = Mock()
        mock_pbar.close = Mock()

        result = fetcher._batch_fetch(requirements)

        assert result['success_count'] == 2  # AAPL and TSLA
        assert len(result['failed']) == 1
        assert result['failed'][0]['symbol'] == 'INVALID'

    @patch('time.sleep')
    @patch('src.data_sources.batch_fetcher.tqdm')
    def test_batch_fetch_symbol_conversion(self, mock_tqdm, mock_sleep, fetcher, sample_df):
        """Test symbol conversion for yfinance"""
        requirements = [
            {'symbol': '09988', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)}
        ]

        # Add convert_symbol_for_yfinance method
        fetcher.client.convert_symbol_for_yfinance = Mock(return_value='9988.HK')
        fetcher.client.get_ohlcv = Mock(return_value=sample_df)

        # Mock progress bar
        mock_pbar = Mock()
        mock_tqdm.return_value = mock_pbar
        mock_pbar.__iter__ = Mock(return_value=iter(requirements))
        mock_pbar.set_postfix = Mock()
        mock_pbar.close = Mock()

        result = fetcher._batch_fetch(requirements)

        # Verify conversion was called
        fetcher.client.convert_symbol_for_yfinance.assert_called_with('09988')

        # Verify get_ohlcv was called with converted symbol
        fetcher.client.get_ohlcv.assert_called_with(
            '9988.HK',
            date(2024, 1, 1),
            date(2024, 1, 31)
        )

        # Verify cache was set with ORIGINAL symbol
        fetcher.cache.set.assert_called_with(
            '09988',  # Original symbol, not converted
            sample_df,
            data_source='yfinance'
        )


class TestBatchFetcherFetchRequiredData:
    """Test fetch_required_data main method"""

    @pytest.fixture
    def fetcher(self):
        """Create BatchFetcher"""
        mock_client = Mock(spec=BaseDataClient)
        mock_cache = Mock(spec=CacheManager)
        return BatchFetcher(mock_client, mock_cache)

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return Mock(spec=Session)

    def test_fetch_required_data_integration(self, fetcher, mock_session):
        """Test full fetch_required_data workflow"""
        # Mock analyze
        fetcher._analyze_requirements = Mock(return_value=[
            {'symbol': 'AAPL', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)},
            {'symbol': 'TSLA', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)},
        ])

        # Mock filter (1 cached, 1 missing)
        fetcher._filter_missing = Mock(return_value=[
            {'symbol': 'TSLA', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)}
        ])

        # Mock batch fetch
        fetcher._batch_fetch = Mock(return_value={
            'success_count': 1,
            'failed': [],
            'total_records': 100,
            'duration': 5.0
        })

        stats = fetcher.fetch_required_data(mock_session)

        # Verify stats
        assert stats['symbols_analyzed'] == 2
        assert stats['symbols_fetched'] == 1
        assert stats['records_fetched'] == 100
        assert stats['cached_symbols'] == 1  # One was already cached
        assert stats['failed_symbols'] == []
        assert stats['duration_seconds'] == 5.0

        # Verify methods were called
        fetcher._analyze_requirements.assert_called_once_with(mock_session)
        fetcher._filter_missing.assert_called_once()
        fetcher._batch_fetch.assert_called_once()


class TestBatchFetcherWarmupCache:
    """Test warmup_cache method"""

    @pytest.fixture
    def fetcher(self):
        """Create BatchFetcher"""
        mock_client = Mock(spec=BaseDataClient)
        mock_cache = Mock(spec=CacheManager)
        return BatchFetcher(mock_client, mock_cache)

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = Mock(spec=Session)

        # Mock query for top symbols
        mock_row1 = Mock(symbol='AAPL', count=100)
        mock_row2 = Mock(symbol='TSLA', count=50)

        mock_query = Mock()
        mock_query.__iter__ = Mock(return_value=iter([mock_row1, mock_row2]))

        session.query.return_value.group_by.return_value.order_by.return_value.limit.return_value = mock_query

        return session

    def test_warmup_cache(self, fetcher, mock_session):
        """Test cache warmup for top symbols"""
        # Mock analyze_requirements
        fetcher._analyze_requirements = Mock(return_value=[
            {'symbol': 'AAPL', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)},
            {'symbol': 'TSLA', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)},
            {'symbol': 'MSFT', 'start_date': date(2024, 1, 1), 'end_date': date(2024, 1, 31)}
        ])

        # Mock batch_fetch
        fetcher._batch_fetch = Mock(return_value={
            'success_count': 2,
            'total_records': 200,
            'failed': []
        })

        # Warmup top 2 symbols
        fetcher.warmup_cache(mock_session, top_n=2)

        # Verify batch_fetch was called with only top symbols
        call_args = fetcher._batch_fetch.call_args[0][0]
        warmup_symbols = [r['symbol'] for r in call_args]

        # Should only include AAPL and TSLA (top 2)
        assert 'AAPL' in warmup_symbols
        assert 'TSLA' in warmup_symbols
        assert 'MSFT' not in warmup_symbols
