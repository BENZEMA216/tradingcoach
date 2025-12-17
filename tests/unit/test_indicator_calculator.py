"""
Unit tests for IndicatorCalculator

Tests technical indicator calculations (RSI, MACD, Bollinger Bands, ATR, MA)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from src.indicators.calculator import IndicatorCalculator


class TestIndicatorCalculatorInit:
    """Test IndicatorCalculator initialization"""

    def test_init(self):
        """Test calculator initialization"""
        calc = IndicatorCalculator()
        assert calc is not None
        assert repr(calc) == "IndicatorCalculator(RSI, MACD, BB, ATR, MA)"


class TestRSICalculation:
    """Test RSI calculation"""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance"""
        return IndicatorCalculator()

    @pytest.fixture
    def sample_prices(self):
        """Create sample price data"""
        # Simple trend: going up then down
        prices = [100, 102, 105, 103, 107, 110, 108, 112, 115, 113,
                  116, 118, 115, 120, 118, 122, 119, 125, 123, 120]
        dates = pd.date_range('2024-01-01', periods=len(prices), freq='D')
        return pd.DataFrame({'Close': prices}, index=dates)

    def test_rsi_basic_calculation(self, calculator, sample_prices):
        """Test basic RSI calculation"""
        rsi = calculator.calculate_rsi(sample_prices, period=14)

        assert len(rsi) == len(sample_prices)
        # EWM starts producing values early, only first value is NaN
        assert rsi.isna().sum() >= 1

        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_rsi_uptrend(self, calculator):
        """Test RSI in strong uptrend"""
        # Strong uptrend should give high RSI
        prices = list(range(100, 130))  # Continuous uptrend
        df = pd.DataFrame({'Close': prices})

        rsi = calculator.calculate_rsi(df, period=14)

        # Last RSI value should be high (close to 100)
        assert rsi.iloc[-1] > 70

    def test_rsi_downtrend(self, calculator):
        """Test RSI in strong downtrend"""
        # Strong downtrend should give low RSI
        prices = list(range(130, 100, -1))  # Continuous downtrend
        df = pd.DataFrame({'Close': prices})

        rsi = calculator.calculate_rsi(df, period=14)

        # Last RSI value should be low (close to 0)
        assert rsi.iloc[-1] < 30

    def test_rsi_empty_dataframe(self, calculator):
        """Test RSI with empty DataFrame"""
        df = pd.DataFrame()
        rsi = calculator.calculate_rsi(df)

        assert rsi.empty

    def test_rsi_missing_column(self, calculator):
        """Test RSI with missing Close column"""
        df = pd.DataFrame({'Open': [100, 101, 102]})
        rsi = calculator.calculate_rsi(df)

        assert rsi.empty


class TestMACDCalculation:
    """Test MACD calculation"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_prices(self):
        """Create sample price data"""
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        dates = pd.date_range('2024-01-01', periods=len(prices), freq='D')
        return pd.DataFrame({'Close': prices}, index=dates)

    def test_macd_basic_calculation(self, calculator, sample_prices):
        """Test basic MACD calculation"""
        result = calculator.calculate_macd(sample_prices)

        assert 'macd' in result
        assert 'signal' in result
        assert 'histogram' in result

        assert len(result['macd']) == len(sample_prices)
        assert len(result['signal']) == len(sample_prices)
        assert len(result['histogram']) == len(sample_prices)

    def test_macd_histogram_formula(self, calculator, sample_prices):
        """Test MACD histogram formula"""
        result = calculator.calculate_macd(sample_prices)

        # Histogram should be (MACD - Signal) * 2
        macd = result['macd']
        signal = result['signal']
        histogram = result['histogram']

        # Check formula (skip NaN values)
        valid_idx = ~(macd.isna() | signal.isna())
        expected_histogram = (macd[valid_idx] - signal[valid_idx]) * 2

        pd.testing.assert_series_equal(
            histogram[valid_idx],
            expected_histogram,
            check_names=False
        )

    def test_macd_empty_dataframe(self, calculator):
        """Test MACD with empty DataFrame"""
        df = pd.DataFrame()
        result = calculator.calculate_macd(df)

        assert result['macd'].empty
        assert result['signal'].empty
        assert result['histogram'].empty


class TestBollingerBands:
    """Test Bollinger Bands calculation"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_prices(self):
        """Create sample price data"""
        prices = [100] * 10 + [105] * 10 + [100] * 10  # Stable, up, stable
        dates = pd.date_range('2024-01-01', periods=len(prices), freq='D')
        return pd.DataFrame({'Close': prices}, index=dates)

    def test_bb_basic_calculation(self, calculator, sample_prices):
        """Test basic Bollinger Bands calculation"""
        result = calculator.calculate_bollinger_bands(sample_prices)

        assert 'upper' in result
        assert 'middle' in result
        assert 'lower' in result

        assert len(result['upper']) == len(sample_prices)
        assert len(result['middle']) == len(sample_prices)
        assert len(result['lower']) == len(sample_prices)

    def test_bb_relationship(self, calculator, sample_prices):
        """Test Bollinger Bands relationship (upper > middle > lower)"""
        result = calculator.calculate_bollinger_bands(sample_prices)

        upper = result['upper']
        middle = result['middle']
        lower = result['lower']

        # Skip NaN values
        valid_idx = ~(upper.isna() | middle.isna() | lower.isna())

        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_bb_middle_is_ma(self, calculator, sample_prices):
        """Test that middle band equals MA(20)"""
        result = calculator.calculate_bollinger_bands(sample_prices, period=20)

        # Middle band should equal 20-period MA
        expected_ma = sample_prices['Close'].rolling(window=20).mean()

        pd.testing.assert_series_equal(
            result['middle'],
            expected_ma,
            check_names=False
        )

    def test_bb_empty_dataframe(self, calculator):
        """Test Bollinger Bands with empty DataFrame"""
        df = pd.DataFrame()
        result = calculator.calculate_bollinger_bands(df)

        assert result['upper'].empty
        assert result['middle'].empty
        assert result['lower'].empty


class TestATRCalculation:
    """Test ATR calculation"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_ohlc(self):
        """Create sample OHLC data"""
        data = {
            'Open': [100, 102, 105, 103, 107],
            'High': [103, 106, 108, 107, 110],
            'Low': [99, 101, 103, 102, 106],
            'Close': [102, 105, 104, 106, 109]
        }
        dates = pd.date_range('2024-01-01', periods=len(data['Open']), freq='D')
        return pd.DataFrame(data, index=dates)

    def test_atr_basic_calculation(self, calculator, sample_ohlc):
        """Test basic ATR calculation"""
        atr = calculator.calculate_atr(sample_ohlc, period=14)

        assert len(atr) == len(sample_ohlc)
        # EWM-based ATR produces values from the start
        # Just check that we have valid values
        assert not atr.empty

        # ATR should be positive
        valid_atr = atr.dropna()
        assert (valid_atr > 0).all()

    def test_atr_measures_volatility(self, calculator):
        """Test that ATR increases with volatility"""
        # Low volatility
        low_vol_data = {
            'High': [101, 101.5, 101, 101.5, 101],
            'Low': [100, 100.5, 100, 100.5, 100],
            'Close': [100.5, 101, 100.5, 101, 100.5]
        }
        low_vol_df = pd.DataFrame(low_vol_data)
        low_atr = calculator.calculate_atr(low_vol_df, period=3)

        # High volatility
        high_vol_data = {
            'High': [110, 115, 105, 120, 100],
            'Low': [90, 95, 85, 100, 80],
            'Close': [100, 105, 95, 110, 90]
        }
        high_vol_df = pd.DataFrame(high_vol_data)
        high_atr = calculator.calculate_atr(high_vol_df, period=3)

        # High volatility should have higher ATR
        assert high_atr.dropna().mean() > low_atr.dropna().mean()

    def test_atr_empty_dataframe(self, calculator):
        """Test ATR with empty DataFrame"""
        df = pd.DataFrame()
        atr = calculator.calculate_atr(df)

        assert atr.empty

    def test_atr_missing_columns(self, calculator):
        """Test ATR with missing required columns"""
        df = pd.DataFrame({'Close': [100, 101, 102]})
        atr = calculator.calculate_atr(df)

        assert atr.empty


class TestMACalculation:
    """Test Moving Average calculation"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_prices(self):
        """Create sample price data"""
        prices = list(range(100, 150))  # Simple linear trend
        dates = pd.date_range('2024-01-01', periods=len(prices), freq='D')
        return pd.DataFrame({'Close': prices}, index=dates)

    def test_ma_basic_calculation(self, calculator, sample_prices):
        """Test basic MA calculation"""
        result = calculator.calculate_ma(sample_prices, periods=[5, 10, 20])

        assert 'ma_5' in result
        assert 'ma_10' in result
        assert 'ma_20' in result

        assert len(result['ma_5']) == len(sample_prices)
        assert len(result['ma_10']) == len(sample_prices)
        assert len(result['ma_20']) == len(sample_prices)

    def test_ma_values(self, calculator):
        """Test MA calculated values"""
        prices = [10, 20, 30, 40, 50]
        df = pd.DataFrame({'Close': prices})

        result = calculator.calculate_ma(df, periods=[3])

        # MA(3) should be: NaN, NaN, 20, 30, 40
        expected = pd.Series([np.nan, np.nan, 20.0, 30.0, 40.0])

        pd.testing.assert_series_equal(
            result['ma_3'],
            expected,
            check_names=False
        )

    def test_ma_default_periods(self, calculator, sample_prices):
        """Test default MA periods"""
        result = calculator.calculate_ma(sample_prices)

        assert 'ma_5' in result
        assert 'ma_10' in result
        assert 'ma_20' in result
        assert 'ma_50' in result
        assert 'ma_200' in result

    def test_ma_empty_dataframe(self, calculator):
        """Test MA with empty DataFrame"""
        df = pd.DataFrame()
        result = calculator.calculate_ma(df, periods=[5, 10])

        assert result['ma_5'].empty
        assert result['ma_10'].empty


class TestCalculateAllIndicators:
    """Test calculate_all_indicators method"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_ohlcv(self):
        """Create complete OHLCV dataset"""
        np.random.seed(42)
        n = 100

        dates = pd.date_range('2024-01-01', periods=n, freq='D')
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)

        data = {
            'Open': close + np.random.randn(n) * 0.1,
            'High': close + np.abs(np.random.randn(n) * 0.5),
            'Low': close - np.abs(np.random.randn(n) * 0.5),
            'Close': close,
            'Volume': np.random.randint(1000000, 5000000, n)
        }

        return pd.DataFrame(data, index=dates)

    def test_calculate_all_indicators(self, calculator, sample_ohlcv):
        """Test calculating all indicators at once"""
        result = calculator.calculate_all_indicators(sample_ohlcv)

        # Check all indicator columns are present
        assert 'rsi_14' in result.columns
        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_histogram' in result.columns
        assert 'bb_upper' in result.columns
        assert 'bb_middle' in result.columns
        assert 'bb_lower' in result.columns
        assert 'atr_14' in result.columns
        assert 'ma_5' in result.columns
        assert 'ma_10' in result.columns
        assert 'ma_20' in result.columns
        assert 'ma_50' in result.columns
        assert 'ma_200' in result.columns

        # Original columns should still be present
        assert 'Open' in result.columns
        assert 'Close' in result.columns

    def test_calculate_all_does_not_modify_original(self, calculator, sample_ohlcv):
        """Test that calculation doesn't modify original DataFrame"""
        original_columns = sample_ohlcv.columns.tolist()

        result = calculator.calculate_all_indicators(sample_ohlcv)

        # Original should be unchanged
        assert sample_ohlcv.columns.tolist() == original_columns

    def test_calculate_all_empty_dataframe(self, calculator):
        """Test calculate_all with empty DataFrame"""
        df = pd.DataFrame()
        result = calculator.calculate_all_indicators(df)

        assert result.empty


class TestDatabaseUpdate:
    """Test database update functionality"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return Mock()

    @pytest.fixture
    def sample_data_with_indicators(self):
        """Create sample data with calculated indicators"""
        dates = pd.DatetimeIndex(['2024-01-01', '2024-01-02', '2024-01-03'])
        data = {
            'Close': [100.0, 101.0, 102.0],
            'rsi_14': [50.0, 55.0, 60.0],
            'macd': [0.5, 0.6, 0.7],
            'macd_signal': [0.4, 0.5, 0.6],
            'macd_histogram': [0.2, 0.2, 0.2],
            'bb_upper': [105.0, 106.0, 107.0],
            'bb_middle': [100.0, 101.0, 102.0],
            'bb_lower': [95.0, 96.0, 97.0],
            'atr_14': [2.0, 2.1, 2.2],
            'ma_5': [99.0, 100.0, 101.0],
            'ma_10': [98.0, 99.0, 100.0],
            'ma_20': [97.0, 98.0, 99.0],
            'ma_50': [95.0, 96.0, 97.0],
            'ma_200': [90.0, 91.0, 92.0]
        }
        return pd.DataFrame(data, index=dates)

    def test_update_market_data_indicators(self, calculator, mock_session, sample_data_with_indicators):
        """Test updating market_data records with indicators"""
        # Mock database records
        mock_records = []
        for timestamp in sample_data_with_indicators.index:
            mock_record = Mock()
            mock_record.symbol = 'AAPL'
            mock_record.timestamp = timestamp
            mock_records.append(mock_record)

        # Setup query mock
        mock_session.query.return_value.filter.return_value.first.side_effect = mock_records

        # Update
        updated_count = calculator.update_market_data_indicators(
            mock_session,
            'AAPL',
            sample_data_with_indicators
        )

        assert updated_count == 3
        mock_session.commit.assert_called_once()

        # Verify first record was updated
        assert mock_records[0].rsi_14 == 50.0
        assert mock_records[0].macd == 0.5

    def test_update_empty_dataframe(self, calculator, mock_session):
        """Test update with empty DataFrame"""
        df = pd.DataFrame()
        updated_count = calculator.update_market_data_indicators(
            mock_session, 'AAPL', df
        )

        assert updated_count == 0
        mock_session.commit.assert_not_called()


class TestBatchCalculation:
    """Test batch calculation functionality"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def mock_session(self):
        return Mock()

    def test_batch_calculate_and_update(self, calculator, mock_session):
        """Test batch processing of multiple symbols"""
        # Mock cache function
        def mock_cache_func(symbol):
            if symbol in ['AAPL', 'MSFT']:
                data = {
                    'Open': [100, 101, 102],
                    'High': [103, 104, 105],
                    'Low': [99, 100, 101],
                    'Close': [102, 103, 104],
                    'Volume': [1000000, 1100000, 1200000]
                }
                dates = pd.date_range('2024-01-01', periods=3, freq='D')
                return pd.DataFrame(data, index=dates)
            return pd.DataFrame()  # Empty for other symbols

        # Mock database query to return no records (simplified)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        symbols = ['AAPL', 'MSFT', 'TSLA']
        results = calculator.batch_calculate_and_update(
            mock_session,
            symbols,
            mock_cache_func
        )

        assert 'AAPL' in results
        assert 'MSFT' in results
        assert 'TSLA' in results

        # AAPL and MSFT should have 0 (no matching records in DB)
        # TSLA should have 0 (empty DataFrame)
        assert results['TSLA'] == 0


# ==================== 新增指标测试 ====================

class TestNewVolumeIndicators:
    """Test new volume indicators (OBV, VWAP, MFI, AD, CMF)"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data"""
        np.random.seed(42)
        n = 50
        dates = pd.date_range('2024-01-01', periods=n, freq='D')
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)

        data = {
            'Open': close + np.random.randn(n) * 0.1,
            'High': close + np.abs(np.random.randn(n) * 0.5),
            'Low': close - np.abs(np.random.randn(n) * 0.5),
            'Close': close,
            'Volume': np.random.randint(1000000, 5000000, n)
        }
        return pd.DataFrame(data, index=dates)

    def test_obv_calculation(self, calculator, sample_ohlcv):
        """Test OBV (On Balance Volume) calculation"""
        obv = calculator.calculate_obv(sample_ohlcv)

        assert len(obv) == len(sample_ohlcv)
        assert not obv.empty
        # OBV should have one NaN at start
        assert obv.isna().sum() <= 1

    def test_vwap_calculation(self, calculator, sample_ohlcv):
        """Test VWAP (Volume Weighted Average Price) calculation"""
        vwap = calculator.calculate_vwap(sample_ohlcv)

        assert len(vwap) == len(sample_ohlcv)
        # VWAP should be positive
        valid_vwap = vwap.dropna()
        assert (valid_vwap > 0).all()

    def test_mfi_calculation(self, calculator, sample_ohlcv):
        """Test MFI (Money Flow Index) calculation"""
        mfi = calculator.calculate_mfi(sample_ohlcv, period=14)

        assert len(mfi) == len(sample_ohlcv)
        # MFI should be between 0 and 100
        valid_mfi = mfi.dropna()
        assert (valid_mfi >= 0).all()
        assert (valid_mfi <= 100).all()

    def test_ad_line_calculation(self, calculator, sample_ohlcv):
        """Test A/D Line (Accumulation/Distribution) calculation"""
        ad_line = calculator.calculate_ad_line(sample_ohlcv)

        assert len(ad_line) == len(sample_ohlcv)
        assert not ad_line.empty

    def test_cmf_calculation(self, calculator, sample_ohlcv):
        """Test CMF (Chaikin Money Flow) calculation"""
        cmf = calculator.calculate_cmf(sample_ohlcv, period=20)

        assert len(cmf) == len(sample_ohlcv)
        # CMF should be between -1 and 1
        valid_cmf = cmf.dropna()
        assert (valid_cmf >= -1).all()
        assert (valid_cmf <= 1).all()

    def test_volume_ratio_calculation(self, calculator, sample_ohlcv):
        """Test Volume Ratio calculation"""
        vol_ratio = calculator.calculate_volume_ratio(sample_ohlcv, period=20)

        assert len(vol_ratio) == len(sample_ohlcv)
        # Volume ratio should be positive
        valid_ratio = vol_ratio.dropna()
        assert (valid_ratio > 0).all()


class TestNewMomentumIndicators:
    """Test new momentum indicators (CCI, Williams %R, ROC, Momentum, UO)"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data"""
        np.random.seed(42)
        n = 50
        dates = pd.date_range('2024-01-01', periods=n, freq='D')
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)

        data = {
            'Open': close + np.random.randn(n) * 0.1,
            'High': close + np.abs(np.random.randn(n) * 0.5),
            'Low': close - np.abs(np.random.randn(n) * 0.5),
            'Close': close,
            'Volume': np.random.randint(1000000, 5000000, n)
        }
        return pd.DataFrame(data, index=dates)

    def test_cci_calculation(self, calculator, sample_ohlcv):
        """Test CCI (Commodity Channel Index) calculation"""
        cci = calculator.calculate_cci(sample_ohlcv, period=20)

        assert len(cci) == len(sample_ohlcv)
        assert not cci.empty

    def test_williams_r_calculation(self, calculator, sample_ohlcv):
        """Test Williams %R calculation"""
        willr = calculator.calculate_williams_r(sample_ohlcv, period=14)

        assert len(willr) == len(sample_ohlcv)
        # Williams %R should be between -100 and 0
        valid_willr = willr.dropna()
        assert (valid_willr >= -100).all()
        assert (valid_willr <= 0).all()

    def test_roc_calculation(self, calculator, sample_ohlcv):
        """Test ROC (Rate of Change) calculation"""
        roc = calculator.calculate_roc(sample_ohlcv, period=12)

        assert len(roc) == len(sample_ohlcv)
        assert not roc.empty

    def test_momentum_calculation(self, calculator, sample_ohlcv):
        """Test Momentum calculation"""
        mom = calculator.calculate_momentum(sample_ohlcv, period=10)

        assert len(mom) == len(sample_ohlcv)
        assert not mom.empty

    def test_ultimate_oscillator_calculation(self, calculator, sample_ohlcv):
        """Test Ultimate Oscillator calculation"""
        uo = calculator.calculate_ultimate_oscillator(sample_ohlcv)

        assert len(uo) == len(sample_ohlcv)
        # UO should be between 0 and 100
        valid_uo = uo.dropna()
        assert (valid_uo >= 0).all()
        assert (valid_uo <= 100).all()


class TestNewVolatilityIndicators:
    """Test new volatility indicators (Keltner, Donchian, HVol, Squeeze)"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data"""
        np.random.seed(42)
        n = 50
        dates = pd.date_range('2024-01-01', periods=n, freq='D')
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)

        data = {
            'Open': close + np.random.randn(n) * 0.1,
            'High': close + np.abs(np.random.randn(n) * 0.5),
            'Low': close - np.abs(np.random.randn(n) * 0.5),
            'Close': close,
            'Volume': np.random.randint(1000000, 5000000, n)
        }
        return pd.DataFrame(data, index=dates)

    def test_keltner_channel_calculation(self, calculator, sample_ohlcv):
        """Test Keltner Channel calculation"""
        kc = calculator.calculate_keltner_channel(sample_ohlcv)

        assert 'kc_upper' in kc
        assert 'kc_middle' in kc
        assert 'kc_lower' in kc
        assert len(kc['kc_upper']) == len(sample_ohlcv)

        # Upper > Middle > Lower
        valid_idx = ~(kc['kc_upper'].isna() | kc['kc_lower'].isna())
        assert (kc['kc_upper'][valid_idx] >= kc['kc_middle'][valid_idx]).all()
        assert (kc['kc_middle'][valid_idx] >= kc['kc_lower'][valid_idx]).all()

    def test_donchian_channel_calculation(self, calculator, sample_ohlcv):
        """Test Donchian Channel calculation"""
        dc = calculator.calculate_donchian_channel(sample_ohlcv, period=20)

        assert 'dc_upper' in dc
        assert 'dc_lower' in dc
        assert len(dc['dc_upper']) == len(sample_ohlcv)

        # Upper >= Lower
        valid_idx = ~(dc['dc_upper'].isna() | dc['dc_lower'].isna())
        assert (dc['dc_upper'][valid_idx] >= dc['dc_lower'][valid_idx]).all()

    def test_historical_volatility_calculation(self, calculator, sample_ohlcv):
        """Test Historical Volatility calculation"""
        hvol = calculator.calculate_historical_volatility(sample_ohlcv, period=20)

        assert len(hvol) == len(sample_ohlcv)
        # Volatility should be positive
        valid_hvol = hvol.dropna()
        assert (valid_hvol >= 0).all()

    def test_bb_squeeze_calculation(self, calculator, sample_ohlcv):
        """Test Bollinger Band Squeeze calculation"""
        squeeze = calculator.calculate_bb_squeeze(sample_ohlcv)

        assert len(squeeze) == len(sample_ohlcv)
        # Squeeze should be 0 or 1
        valid_squeeze = squeeze.dropna()
        assert set(valid_squeeze.unique()).issubset({0, 1})


class TestNewTrendIndicators:
    """Test new trend indicators (Ichimoku, SAR, SuperTrend, TRIX, DPO)"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_ohlcv(self):
        """Create sample OHLCV data with enough history for Ichimoku"""
        np.random.seed(42)
        n = 100  # Ichimoku needs at least 52 periods
        dates = pd.date_range('2024-01-01', periods=n, freq='D')
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)

        data = {
            'Open': close + np.random.randn(n) * 0.1,
            'High': close + np.abs(np.random.randn(n) * 0.5),
            'Low': close - np.abs(np.random.randn(n) * 0.5),
            'Close': close,
            'Volume': np.random.randint(1000000, 5000000, n)
        }
        return pd.DataFrame(data, index=dates)

    def test_ichimoku_calculation(self, calculator, sample_ohlcv):
        """Test Ichimoku Cloud calculation"""
        ichi = calculator.calculate_ichimoku(sample_ohlcv)

        assert 'ichi_tenkan' in ichi
        assert 'ichi_kijun' in ichi
        assert 'ichi_senkou_a' in ichi
        assert 'ichi_senkou_b' in ichi
        assert 'ichi_chikou' in ichi
        assert len(ichi['ichi_tenkan']) == len(sample_ohlcv)

    def test_parabolic_sar_calculation(self, calculator, sample_ohlcv):
        """Test Parabolic SAR calculation"""
        psar = calculator.calculate_parabolic_sar(sample_ohlcv)

        assert 'psar' in psar
        assert 'psar_dir' in psar
        assert len(psar['psar']) == len(sample_ohlcv)

        # Direction should be 1 or -1
        valid_dir = psar['psar_dir'].dropna()
        assert set(valid_dir.unique()).issubset({1, -1})

    def test_supertrend_calculation(self, calculator, sample_ohlcv):
        """Test SuperTrend calculation"""
        st = calculator.calculate_supertrend(sample_ohlcv)

        assert 'supertrend' in st
        assert 'supertrend_dir' in st
        assert len(st['supertrend']) == len(sample_ohlcv)

        # Direction should be 1 or -1
        valid_dir = st['supertrend_dir'].dropna()
        assert set(valid_dir.unique()).issubset({1, -1})

    def test_trix_calculation(self, calculator, sample_ohlcv):
        """Test TRIX calculation"""
        trix = calculator.calculate_trix(sample_ohlcv, period=15)

        assert len(trix) == len(sample_ohlcv)
        assert not trix.empty

    def test_dpo_calculation(self, calculator, sample_ohlcv):
        """Test DPO (Detrended Price Oscillator) calculation"""
        dpo = calculator.calculate_dpo(sample_ohlcv, period=20)

        assert len(dpo) == len(sample_ohlcv)
        assert not dpo.empty


class TestCalculateAllIndicatorsWithNew:
    """Test that calculate_all_indicators includes new indicators"""

    @pytest.fixture
    def calculator(self):
        return IndicatorCalculator()

    @pytest.fixture
    def sample_ohlcv(self):
        """Create complete OHLCV dataset"""
        np.random.seed(42)
        n = 100

        dates = pd.date_range('2024-01-01', periods=n, freq='D')
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)

        data = {
            'Open': close + np.random.randn(n) * 0.1,
            'High': close + np.abs(np.random.randn(n) * 0.5),
            'Low': close - np.abs(np.random.randn(n) * 0.5),
            'Close': close,
            'Volume': np.random.randint(1000000, 5000000, n)
        }
        return pd.DataFrame(data, index=dates)

    def test_new_volume_indicators_included(self, calculator, sample_ohlcv):
        """Test that new volume indicators are calculated"""
        result = calculator.calculate_all_indicators(sample_ohlcv)

        assert 'obv' in result.columns
        assert 'vwap' in result.columns
        assert 'mfi_14' in result.columns
        assert 'ad_line' in result.columns
        assert 'cmf_20' in result.columns
        assert 'volume_ratio' in result.columns

    def test_new_momentum_indicators_included(self, calculator, sample_ohlcv):
        """Test that new momentum indicators are calculated"""
        result = calculator.calculate_all_indicators(sample_ohlcv)

        assert 'cci_20' in result.columns
        assert 'willr_14' in result.columns
        assert 'roc_12' in result.columns
        assert 'mom_10' in result.columns
        assert 'uo' in result.columns

    def test_new_volatility_indicators_included(self, calculator, sample_ohlcv):
        """Test that new volatility indicators are calculated"""
        result = calculator.calculate_all_indicators(sample_ohlcv)

        assert 'kc_upper' in result.columns
        assert 'kc_middle' in result.columns
        assert 'kc_lower' in result.columns
        assert 'dc_upper' in result.columns
        assert 'dc_lower' in result.columns
        assert 'hvol_20' in result.columns
        assert 'bb_squeeze' in result.columns

    def test_new_trend_indicators_included(self, calculator, sample_ohlcv):
        """Test that new trend indicators are calculated"""
        result = calculator.calculate_all_indicators(sample_ohlcv)

        assert 'ichi_tenkan' in result.columns
        assert 'ichi_kijun' in result.columns
        assert 'psar' in result.columns
        assert 'psar_dir' in result.columns
        assert 'supertrend' in result.columns
        assert 'supertrend_dir' in result.columns
        assert 'trix' in result.columns
        assert 'dpo' in result.columns
