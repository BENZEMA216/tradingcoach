"""
Unit tests for CacheManager

Tests all three cache tiers (L1, L2, L3) and their interactions
"""

import pytest
import pandas as pd
import pickle
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tempfile
import shutil

from src.data_sources.cache_manager import CacheManager
from src.models.market_data import MarketData


class TestCacheManagerInit:
    """Test CacheManager initialization"""

    def test_init_default_params(self, tmp_path):
        """Test initialization with default parameters"""
        mock_session = Mock()
        cache_dir = str(tmp_path / 'cache')

        manager = CacheManager(
            db_session=mock_session,
            cache_dir=cache_dir
        )

        assert manager.session == mock_session
        assert manager.expiry_days == 1
        assert manager.l1_max_size == 100
        assert len(manager.l1_cache) == 0
        assert len(manager.l1_access_order) == 0
        assert Path(cache_dir).exists()

    def test_init_custom_params(self, tmp_path):
        """Test initialization with custom parameters"""
        mock_session = Mock()
        cache_dir = str(tmp_path / 'custom_cache')

        manager = CacheManager(
            db_session=mock_session,
            cache_dir=cache_dir,
            expiry_days=7,
            l1_max_size=50
        )

        assert manager.expiry_days == 7
        assert manager.l1_max_size == 50


class TestCacheManagerL1:
    """Test L1 (memory) cache operations"""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create CacheManager with mocked session"""
        mock_session = Mock()
        return CacheManager(
            db_session=mock_session,
            cache_dir=str(tmp_path / 'cache'),
            l1_max_size=3  # Small size to test LRU
        )

    @pytest.fixture
    def sample_df(self):
        """Sample DataFrame"""
        return pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [102.0, 103.0],
            'Low': [99.0, 100.0],
            'Close': [101.0, 102.0],
            'Volume': [1000, 1500]
        }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02']))

    def test_l1_set_and_get(self, manager, sample_df):
        """Test setting and getting from L1 cache"""
        cache_key = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 2), '1d')

        # Set
        manager._set_to_l1(cache_key, sample_df)

        # Get
        result = manager._get_from_l1(cache_key)

        assert result is not None
        assert len(result) == 2
        assert result['Close'].iloc[0] == 101.0

    def test_l1_returns_copy(self, manager, sample_df):
        """Test that L1 returns a copy, not the original"""
        cache_key = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 2), '1d')

        manager._set_to_l1(cache_key, sample_df)
        result1 = manager._get_from_l1(cache_key)
        result2 = manager._get_from_l1(cache_key)

        # Modify result1
        result1.iloc[0, 0] = 999.0

        # result2 should be unaffected
        assert result2.iloc[0, 0] == 100.0

    def test_l1_lru_eviction(self, manager, sample_df):
        """Test LRU eviction when cache is full"""
        # Fill cache (max_size = 3)
        key1 = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 2), '1d')
        key2 = manager._make_cache_key('MSFT', date(2024, 1, 1), date(2024, 1, 2), '1d')
        key3 = manager._make_cache_key('GOOGL', date(2024, 1, 1), date(2024, 1, 2), '1d')

        manager._set_to_l1(key1, sample_df)
        manager._set_to_l1(key2, sample_df)
        manager._set_to_l1(key3, sample_df)

        # All should be in cache
        assert len(manager.l1_cache) == 3

        # Add one more (should evict key1, the oldest)
        key4 = manager._make_cache_key('TSLA', date(2024, 1, 1), date(2024, 1, 2), '1d')
        manager._set_to_l1(key4, sample_df)

        # Cache size should still be 3
        assert len(manager.l1_cache) == 3

        # key1 should be evicted
        assert key1 not in manager.l1_cache
        assert key2 in manager.l1_cache
        assert key3 in manager.l1_cache
        assert key4 in manager.l1_cache

    def test_l1_lru_access_updates_order(self, manager, sample_df):
        """Test that accessing an item updates LRU order"""
        key1 = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 2), '1d')
        key2 = manager._make_cache_key('MSFT', date(2024, 1, 1), date(2024, 1, 2), '1d')
        key3 = manager._make_cache_key('GOOGL', date(2024, 1, 1), date(2024, 1, 2), '1d')

        # Fill cache
        manager._set_to_l1(key1, sample_df)
        manager._set_to_l1(key2, sample_df)
        manager._set_to_l1(key3, sample_df)

        # Access key1 (moves it to end of LRU queue)
        manager._get_from_l1(key1)

        # Add one more (should evict key2, not key1)
        key4 = manager._make_cache_key('TSLA', date(2024, 1, 1), date(2024, 1, 2), '1d')
        manager._set_to_l1(key4, sample_df)

        # key1 should still be in cache
        assert key1 in manager.l1_cache
        assert key2 not in manager.l1_cache


class TestCacheManagerL2:
    """Test L2 (database) cache operations"""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create CacheManager with mocked session"""
        mock_session = Mock()
        return CacheManager(
            db_session=mock_session,
            cache_dir=str(tmp_path / 'cache')
        )

    @pytest.fixture
    def sample_df(self):
        """Sample DataFrame"""
        return pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [102.0, 103.0],
            'Low': [99.0, 100.0],
            'Close': [101.0, 102.0],
            'Volume': [1000, 1500]
        }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02']))

    def test_l2_get_from_db(self, manager, sample_df):
        """Test getting data from database"""
        # Mock database records
        mock_records = [
            Mock(
                date=date(2024, 1, 1),
                timestamp=pd.Timestamp('2024-01-01'),
                open=100.0,
                high=102.0,
                low=99.0,
                close=101.0,
                volume=1000
            ),
            Mock(
                date=date(2024, 1, 2),
                timestamp=pd.Timestamp('2024-01-02'),
                open=101.0,
                high=103.0,
                low=100.0,
                close=102.0,
                volume=1500
            )
        ]

        # Mock query chain
        mock_query = Mock()
        mock_query.all.return_value = mock_records
        manager.session.query.return_value.filter.return_value.order_by.return_value = mock_query

        # Get from L2
        result = manager._get_from_l2('AAPL', date(2024, 1, 1), date(2024, 1, 2), '1d')

        assert result is not None
        assert len(result) == 2
        assert result['Close'].iloc[0] == 101.0

    def test_l2_get_incomplete_data(self, manager):
        """Test that incomplete data returns None"""
        # Mock only 1 record when 5+ are expected
        mock_records = [
            Mock(
                date=date(2024, 1, 1),
                timestamp=pd.Timestamp('2024-01-01'),
                open=100.0,
                high=102.0,
                low=99.0,
                close=101.0,
                volume=1000
            )
        ]

        mock_query = Mock()
        mock_query.all.return_value = mock_records
        manager.session.query.return_value.filter.return_value.order_by.return_value = mock_query

        # Request 2 weeks of data but only get 1 day (incomplete)
        result = manager._get_from_l2(
            'AAPL',
            date(2024, 1, 1),
            date(2024, 1, 14),  # 2 weeks
            '1d'
        )

        # Should return None because data is incomplete
        assert result is None

    def test_l2_set_to_db_new_records(self, manager, sample_df):
        """Test writing new records to database"""
        # Mock that no existing records found
        manager.session.query.return_value.filter.return_value.first.return_value = None

        manager._set_to_l2('AAPL', sample_df, '1d', 'yfinance')

        # Verify bulk_save_objects was called
        manager.session.bulk_save_objects.assert_called_once()

        # Verify commit was called
        manager.session.commit.assert_called_once()

    def test_l2_set_to_db_update_existing(self, manager):
        """Test updating existing records in database"""
        df = pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000]
        }, index=pd.DatetimeIndex(['2024-01-01']))

        # Mock existing record
        mock_existing = Mock()
        manager.session.query.return_value.filter.return_value.first.return_value = mock_existing

        manager._set_to_l2('AAPL', df, '1d', 'yfinance')

        # Verify existing record was updated
        assert mock_existing.open == 100.0
        assert mock_existing.close == 101.0

    def test_l2_set_rollback_on_error(self, manager, sample_df):
        """Test rollback on database error"""
        # Mock that no existing records found
        manager.session.query.return_value.filter.return_value.first.return_value = None

        # Mock database error
        manager.session.bulk_save_objects.side_effect = Exception("DB error")

        # Should not raise, but log error
        manager._set_to_l2('AAPL', sample_df, '1d', 'yfinance')

        # Verify rollback was called
        manager.session.rollback.assert_called_once()


class TestCacheManagerL3:
    """Test L3 (disk) cache operations"""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create CacheManager with temp directory"""
        mock_session = Mock()
        cache_dir = tmp_path / 'cache'
        return CacheManager(
            db_session=mock_session,
            cache_dir=str(cache_dir)
        )

    @pytest.fixture
    def sample_df(self):
        """Sample DataFrame"""
        return pd.DataFrame({
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000]
        }, index=pd.DatetimeIndex(['2024-01-01']))

    def test_l3_set_and_get(self, manager, sample_df):
        """Test setting and getting from L3 disk cache"""
        cache_key = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 1), '1d')

        # Set
        manager._set_to_l3(cache_key, sample_df)

        # Verify file exists
        cache_file = manager.cache_dir / f"{cache_key}.pkl"
        assert cache_file.exists()

        # Get
        result = manager._get_from_l3(cache_key)

        assert result is not None
        assert len(result) == 1
        assert result['Close'].iloc[0] == 101.0

    def test_l3_get_nonexistent(self, manager):
        """Test getting non-existent key from L3"""
        cache_key = "nonexistent_key"
        result = manager._get_from_l3(cache_key)
        assert result is None

    def test_l3_expiry(self, manager, sample_df, tmp_path):
        """Test L3 cache expiry"""
        cache_key = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 1), '1d')

        # Set cache
        manager._set_to_l3(cache_key, sample_df)

        # Manually modify file timestamp to be old
        cache_file = manager.cache_dir / f"{cache_key}.pkl"
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        cache_file.touch()
        import os
        os.utime(cache_file, (old_time, old_time))

        # Get should return None because cache is expired
        result = manager._get_from_l3(cache_key)
        assert result is None

    def test_l3_corrupted_file(self, manager, tmp_path):
        """Test handling of corrupted cache file"""
        cache_key = "test_key"
        cache_file = manager.cache_dir / f"{cache_key}.pkl"

        # Create corrupted file
        with open(cache_file, 'w') as f:
            f.write("corrupted data")

        # Should return None and log error
        result = manager._get_from_l3(cache_key)
        assert result is None


class TestCacheManagerIntegration:
    """Test integration of all three cache tiers"""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create CacheManager with mocked session"""
        mock_session = Mock()
        return CacheManager(
            db_session=mock_session,
            cache_dir=str(tmp_path / 'cache')
        )

    @pytest.fixture
    def sample_df(self):
        """Sample DataFrame"""
        return pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [102.0, 103.0],
            'Low': [99.0, 100.0],
            'Close': [101.0, 102.0],
            'Volume': [1000, 1500]
        }, index=pd.DatetimeIndex(['2024-01-01', '2024-01-02']))

    def test_get_cascading_l1_hit(self, manager, sample_df):
        """Test cache hit in L1"""
        # Pre-populate L1
        cache_key = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 2), '1d')
        manager._set_to_l1(cache_key, sample_df)

        # Get should return from L1
        result = manager.get('AAPL', date(2024, 1, 1), date(2024, 1, 2))

        assert result is not None
        assert len(result) == 2

        # L2 should not be queried
        manager.session.query.assert_not_called()

    def test_get_cascading_l2_hit(self, manager, sample_df):
        """Test cache miss in L1, hit in L2"""
        # Mock L2 (database) to return data
        mock_records = [
            Mock(
                date=date(2024, 1, 1),
                timestamp=pd.Timestamp('2024-01-01'),
                open=100.0,
                high=102.0,
                low=99.0,
                close=101.0,
                volume=1000
            )
        ]

        mock_query = Mock()
        mock_query.all.return_value = mock_records
        manager.session.query.return_value.filter.return_value.order_by.return_value = mock_query

        # Get (should hit L2)
        result = manager.get('AAPL', date(2024, 1, 1), date(2024, 1, 1))

        assert result is not None
        assert len(result) == 1

        # L2 should be queried
        manager.session.query.assert_called()

        # Result should be promoted to L1
        cache_key = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 1), '1d')
        assert cache_key in manager.l1_cache

    def test_get_cascading_l3_hit(self, manager, sample_df):
        """Test cache miss in L1 and L2, hit in L3"""
        # Mock L2 to return None
        mock_query = Mock()
        mock_query.all.return_value = []
        manager.session.query.return_value.filter.return_value.order_by.return_value = mock_query

        # Pre-populate L3
        cache_key = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 2), '1d')
        manager._set_to_l3(cache_key, sample_df)

        # Get (should hit L3)
        result = manager.get('AAPL', date(2024, 1, 1), date(2024, 1, 2))

        assert result is not None
        assert len(result) == 2

        # Result should be promoted to L1
        assert cache_key in manager.l1_cache

    def test_set_writes_all_tiers(self, manager, sample_df):
        """Test that set writes to all three cache tiers"""
        # Mock L2 database operations
        manager.session.query.return_value.filter.return_value.first.return_value = None

        # Set cache
        manager.set('AAPL', sample_df, '1d', 'yfinance')

        # Verify L1
        cache_key = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 2), '1d')
        assert cache_key in manager.l1_cache

        # Verify L2 (database write)
        manager.session.bulk_save_objects.assert_called()

        # Verify L3 (disk file)
        cache_file = manager.cache_dir / f"{cache_key}.pkl"
        assert cache_file.exists()

    def test_set_empty_dataframe(self, manager):
        """Test that empty DataFrame is not cached"""
        empty_df = pd.DataFrame()

        # Should not cache
        manager.set('AAPL', empty_df, '1d', 'yfinance')

        # Verify nothing was cached
        assert len(manager.l1_cache) == 0


class TestCacheManagerUtilities:
    """Test utility methods"""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create CacheManager"""
        mock_session = Mock()
        return CacheManager(
            db_session=mock_session,
            cache_dir=str(tmp_path / 'cache')
        )

    def test_make_cache_key(self, manager):
        """Test cache key generation"""
        key1 = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 31), '1d')
        key2 = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 31), '1d')
        key3 = manager._make_cache_key('MSFT', date(2024, 1, 1), date(2024, 1, 31), '1d')

        # Same inputs should generate same key
        assert key1 == key2

        # Different inputs should generate different keys
        assert key1 != key3

        # Keys should be MD5 hashes (32 chars)
        assert len(key1) == 32

    def test_get_expected_trading_days(self, manager):
        """Test trading days calculation"""
        # Week with Monday-Friday
        days = manager._get_expected_trading_days(date(2024, 1, 1), date(2024, 1, 7))

        # Should exclude weekends
        # Jan 1, 2024 is Monday, so we have Mon-Fri = 5 days, Sat-Sun = 2 days
        weekday_count = sum(1 for d in days if d.weekday() < 5)
        assert weekday_count == len(days)  # All should be weekdays

    def test_clear_all(self, manager, tmp_path):
        """Test clearing all caches"""
        # Populate L1
        sample_df = pd.DataFrame({
            'Close': [100.0]
        }, index=pd.DatetimeIndex(['2024-01-01']))

        cache_key = manager._make_cache_key('AAPL', date(2024, 1, 1), date(2024, 1, 1), '1d')
        manager._set_to_l1(cache_key, sample_df)
        manager._set_to_l3(cache_key, sample_df)

        assert len(manager.l1_cache) > 0
        assert len(list(manager.cache_dir.glob('*.pkl'))) > 0

        # Clear all
        manager.clear_all()

        assert len(manager.l1_cache) == 0
        assert len(list(manager.cache_dir.glob('*.pkl'))) == 0

    def test_get_stats(self, manager):
        """Test statistics gathering"""
        # Mock L2 stats
        manager.session.query.return_value.count.return_value = 1000
        manager.session.query.return_value.distinct.return_value.count.return_value = 50

        stats = manager.get_stats()

        assert 'l1_entries' in stats
        assert 'l1_max_size' in stats
        assert 'l2_records' in stats
        assert 'l2_symbols' in stats
        assert 'l3_files' in stats
        assert 'l3_size_mb' in stats

        assert stats['l1_max_size'] == 100
        assert stats['l2_records'] == 1000
        assert stats['l2_symbols'] == 50

    def test_repr(self, manager):
        """Test string representation"""
        repr_str = repr(manager)
        assert 'CacheManager' in repr_str
        assert 'L1=' in repr_str
        assert 'L2=' in repr_str
        assert 'L3=' in repr_str
