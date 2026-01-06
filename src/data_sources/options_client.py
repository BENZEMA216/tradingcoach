"""
OptionsClient - 期权数据客户端

获取期权相关数据：
- Greeks (Delta, Gamma, Theta, Vega)
- Implied Volatility (IV)
- IV Rank / IV Percentile
- Put/Call Ratio
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import math


def _norm_cdf(x: float) -> float:
    """标准正态分布的累积分布函数"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _norm_pdf(x: float) -> float:
    """标准正态分布的概率密度函数"""
    return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)


def _percentileofscore(data: np.ndarray, score: float) -> float:
    """计算分数在数据中的百分位"""
    n = len(data)
    if n == 0:
        return 50.0
    left = np.sum(data < score)
    right = np.sum(data <= score)
    return (left + right) / 2 / n * 100

logger = logging.getLogger(__name__)


class OptionsClient:
    """
    期权数据客户端

    使用 yfinance 获取期权链数据，计算各种期权指标
    """

    def __init__(self):
        """初始化期权客户端"""
        logger.info("OptionsClient initialized")

    # ==================== 期权链数据获取 ====================

    def get_option_chain(
        self,
        symbol: str,
        expiration_date: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        获取期权链数据

        Args:
            symbol: 标的代码
            expiration_date: 到期日（YYYY-MM-DD格式），None则获取最近到期日

        Returns:
            dict: {'calls': DataFrame, 'puts': DataFrame}
        """
        try:
            ticker = yf.Ticker(symbol)

            # 获取可用到期日
            expirations = ticker.options
            if not expirations:
                logger.warning(f"No options available for {symbol}")
                return {'calls': pd.DataFrame(), 'puts': pd.DataFrame()}

            # 选择到期日
            if expiration_date is None:
                exp = expirations[0]  # 最近到期日
            elif expiration_date in expirations:
                exp = expiration_date
            else:
                logger.warning(f"Expiration {expiration_date} not available for {symbol}")
                exp = expirations[0]

            # 获取期权链
            chain = ticker.option_chain(exp)

            return {
                'calls': chain.calls,
                'puts': chain.puts,
                'expiration': exp
            }

        except Exception as e:
            logger.error(f"Error getting option chain for {symbol}: {e}")
            return {'calls': pd.DataFrame(), 'puts': pd.DataFrame()}

    def get_all_expirations(self, symbol: str) -> List[str]:
        """获取所有可用的到期日"""
        try:
            ticker = yf.Ticker(symbol)
            return list(ticker.options) if ticker.options else []
        except Exception as e:
            logger.error(f"Error getting expirations for {symbol}: {e}")
            return []

    # ==================== Implied Volatility ====================

    def get_current_iv(self, symbol: str) -> Optional[float]:
        """
        获取当前隐含波动率（ATM期权的平均IV）

        Args:
            symbol: 标的代码

        Returns:
            float: 隐含波动率（百分比形式，如 30.5 表示 30.5%）
        """
        try:
            ticker = yf.Ticker(symbol)

            # 获取当前价格
            current_price = ticker.info.get('regularMarketPrice') or ticker.info.get('currentPrice')
            if not current_price:
                return None

            # 获取最近到期日期权链
            chain_data = self.get_option_chain(symbol)
            if chain_data['calls'].empty:
                return None

            calls = chain_data['calls']
            puts = chain_data['puts']

            # 找到ATM期权（行权价最接近当前价格）
            calls['distance'] = abs(calls['strike'] - current_price)
            puts['distance'] = abs(puts['strike'] - current_price)

            atm_call = calls.loc[calls['distance'].idxmin()]
            atm_put = puts.loc[puts['distance'].idxmin()]

            # 获取IV
            call_iv = atm_call.get('impliedVolatility', 0) * 100
            put_iv = atm_put.get('impliedVolatility', 0) * 100

            # 返回平均IV
            if call_iv > 0 and put_iv > 0:
                return (call_iv + put_iv) / 2
            elif call_iv > 0:
                return call_iv
            elif put_iv > 0:
                return put_iv

            return None

        except Exception as e:
            logger.error(f"Error getting IV for {symbol}: {e}")
            return None

    def calculate_iv_rank(
        self,
        symbol: str,
        lookback_days: int = 252
    ) -> Optional[float]:
        """
        计算 IV Rank

        IV Rank = (当前IV - 52周最低IV) / (52周最高IV - 52周最低IV) × 100

        Args:
            symbol: 标的代码
            lookback_days: 回望天数（默认252个交易日≈1年）

        Returns:
            float: IV Rank (0-100)
        """
        try:
            # 获取历史数据计算历史波动率作为IV代理
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 30)

            hist = ticker.history(start=start_date, end=end_date)
            if hist.empty or len(hist) < 20:
                return None

            # 计算历史波动率序列（20日滚动）
            returns = np.log(hist['Close'] / hist['Close'].shift(1))
            hvol_series = returns.rolling(window=20).std() * np.sqrt(252) * 100
            hvol_series = hvol_series.dropna()

            if len(hvol_series) < lookback_days * 0.8:
                return None

            # 取最近 lookback_days 的数据
            hvol_recent = hvol_series.tail(lookback_days)

            current_hvol = hvol_series.iloc[-1]
            min_hvol = hvol_recent.min()
            max_hvol = hvol_recent.max()

            if max_hvol == min_hvol:
                return 50.0  # 如果没有波动，返回中间值

            iv_rank = ((current_hvol - min_hvol) / (max_hvol - min_hvol)) * 100

            return round(float(iv_rank), 2)

        except Exception as e:
            logger.error(f"Error calculating IV Rank for {symbol}: {e}")
            return None

    def calculate_iv_percentile(
        self,
        symbol: str,
        lookback_days: int = 252
    ) -> Optional[float]:
        """
        计算 IV Percentile

        IV Percentile = 过去N天中IV低于当前IV的天数百分比

        Args:
            symbol: 标的代码
            lookback_days: 回望天数

        Returns:
            float: IV Percentile (0-100)
        """
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 30)

            hist = ticker.history(start=start_date, end=end_date)
            if hist.empty or len(hist) < 20:
                return None

            # 计算历史波动率序列
            returns = np.log(hist['Close'] / hist['Close'].shift(1))
            hvol_series = returns.rolling(window=20).std() * np.sqrt(252) * 100
            hvol_series = hvol_series.dropna()

            if len(hvol_series) < lookback_days * 0.8:
                return None

            hvol_recent = hvol_series.tail(lookback_days)
            current_hvol = hvol_series.iloc[-1]

            # 计算百分位
            iv_percentile = _percentileofscore(hvol_recent.values, current_hvol)

            return round(float(iv_percentile), 2)

        except Exception as e:
            logger.error(f"Error calculating IV Percentile for {symbol}: {e}")
            return None

    # ==================== Put/Call Ratio ====================

    def calculate_put_call_ratio(self, symbol: str) -> Optional[float]:
        """
        计算 Put/Call Ratio（基于成交量）

        PCR = Put成交量 / Call成交量

        Args:
            symbol: 标的代码

        Returns:
            float: Put/Call Ratio
        """
        try:
            chain_data = self.get_option_chain(symbol)

            if chain_data['calls'].empty or chain_data['puts'].empty:
                return None

            call_volume = chain_data['calls']['volume'].sum()
            put_volume = chain_data['puts']['volume'].sum()

            if call_volume == 0:
                return None

            pcr = put_volume / call_volume

            return round(float(pcr), 4)

        except Exception as e:
            logger.error(f"Error calculating PCR for {symbol}: {e}")
            return None

    def calculate_put_call_oi_ratio(self, symbol: str) -> Optional[float]:
        """
        计算基于未平仓量的 Put/Call Ratio

        PCR(OI) = Put未平仓量 / Call未平仓量
        """
        try:
            chain_data = self.get_option_chain(symbol)

            if chain_data['calls'].empty or chain_data['puts'].empty:
                return None

            call_oi = chain_data['calls']['openInterest'].sum()
            put_oi = chain_data['puts']['openInterest'].sum()

            if call_oi == 0:
                return None

            pcr_oi = put_oi / call_oi

            return round(float(pcr_oi), 4)

        except Exception as e:
            logger.error(f"Error calculating PCR(OI) for {symbol}: {e}")
            return None

    # ==================== Greeks 计算 ====================

    def calculate_greeks(
        self,
        option_type: str,
        underlying_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float = 0.05,
        dividend_yield: float = 0.0
    ) -> Dict[str, float]:
        """
        使用 Black-Scholes 模型计算期权 Greeks

        Args:
            option_type: 'call' 或 'put'
            underlying_price: 标的价格
            strike_price: 行权价
            time_to_expiry: 到期时间（年）
            volatility: 波动率（小数形式，如 0.3）
            risk_free_rate: 无风险利率
            dividend_yield: 股息率

        Returns:
            dict: {'delta', 'gamma', 'theta', 'vega', 'rho'}
        """
        if time_to_expiry <= 0:
            return {
                'delta': 1.0 if option_type == 'call' else -1.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'rho': 0.0
            }

        S = underlying_price
        K = strike_price
        T = time_to_expiry
        r = risk_free_rate
        q = dividend_yield
        sigma = volatility

        # d1 和 d2
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # N(d1), N(d2), n(d1)
        Nd1 = _norm_cdf(d1)
        Nd2 = _norm_cdf(d2)
        nd1 = _norm_pdf(d1)

        if option_type.lower() == 'call':
            delta = np.exp(-q * T) * Nd1
            theta = (-S * sigma * np.exp(-q * T) * nd1 / (2 * np.sqrt(T))
                    - r * K * np.exp(-r * T) * Nd2
                    + q * S * np.exp(-q * T) * Nd1) / 365
            rho = K * T * np.exp(-r * T) * Nd2 / 100
        else:  # put
            delta = np.exp(-q * T) * (Nd1 - 1)
            theta = (-S * sigma * np.exp(-q * T) * nd1 / (2 * np.sqrt(T))
                    + r * K * np.exp(-r * T) * (1 - Nd2)
                    - q * S * np.exp(-q * T) * (1 - Nd1)) / 365
            rho = -K * T * np.exp(-r * T) * (1 - Nd2) / 100

        gamma = np.exp(-q * T) * nd1 / (S * sigma * np.sqrt(T))
        vega = S * np.exp(-q * T) * nd1 * np.sqrt(T) / 100

        return {
            'delta': round(float(delta), 6),
            'gamma': round(float(gamma), 6),
            'theta': round(float(theta), 6),
            'vega': round(float(vega), 6),
            'rho': round(float(rho), 6)
        }

    def get_option_greeks_from_chain(
        self,
        symbol: str,
        option_type: str = 'call',
        moneyness: str = 'atm'
    ) -> Optional[Dict[str, float]]:
        """
        从期权链获取指定期权的Greeks

        Args:
            symbol: 标的代码
            option_type: 'call' 或 'put'
            moneyness: 'atm'(平值), 'itm'(实值), 'otm'(虚值)

        Returns:
            dict: Greeks 或 None
        """
        try:
            ticker = yf.Ticker(symbol)
            current_price = ticker.info.get('regularMarketPrice') or ticker.info.get('currentPrice')

            if not current_price:
                return None

            chain_data = self.get_option_chain(symbol)
            options = chain_data['calls'] if option_type == 'call' else chain_data['puts']

            if options.empty:
                return None

            # 选择期权
            options['distance'] = abs(options['strike'] - current_price)

            if moneyness == 'atm':
                selected = options.loc[options['distance'].idxmin()]
            elif moneyness == 'itm':
                if option_type == 'call':
                    itm_options = options[options['strike'] < current_price]
                else:
                    itm_options = options[options['strike'] > current_price]
                if itm_options.empty:
                    return None
                selected = itm_options.loc[itm_options['distance'].idxmin()]
            else:  # otm
                if option_type == 'call':
                    otm_options = options[options['strike'] > current_price]
                else:
                    otm_options = options[options['strike'] < current_price]
                if otm_options.empty:
                    return None
                selected = otm_options.loc[otm_options['distance'].idxmin()]

            # 计算到期时间
            exp_str = chain_data.get('expiration', '')
            if exp_str:
                exp_date = datetime.strptime(exp_str, '%Y-%m-%d')
                tte = (exp_date - datetime.now()).days / 365
            else:
                tte = 30 / 365  # 默认30天

            # 获取IV
            iv = selected.get('impliedVolatility', 0.3)

            # 计算Greeks
            greeks = self.calculate_greeks(
                option_type=option_type,
                underlying_price=current_price,
                strike_price=selected['strike'],
                time_to_expiry=max(tte, 0.001),
                volatility=iv
            )

            return greeks

        except Exception as e:
            logger.error(f"Error getting Greeks for {symbol}: {e}")
            return None

    # ==================== 综合期权指标 ====================

    def get_all_option_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        获取所有期权相关指标

        Args:
            symbol: 标的代码

        Returns:
            dict: {
                'iv': 隐含波动率,
                'iv_rank': IV排名,
                'iv_percentile': IV百分位,
                'pcr': Put/Call比率,
                'pcr_oi': 基于OI的PCR,
                'greeks': ATM看涨期权的Greeks
            }
        """
        result = {
            'iv': None,
            'iv_rank': None,
            'iv_percentile': None,
            'pcr': None,
            'pcr_oi': None,
            'greeks': None
        }

        try:
            result['iv'] = self.get_current_iv(symbol)
            result['iv_rank'] = self.calculate_iv_rank(symbol)
            result['iv_percentile'] = self.calculate_iv_percentile(symbol)
            result['pcr'] = self.calculate_put_call_ratio(symbol)
            result['pcr_oi'] = self.calculate_put_call_oi_ratio(symbol)
            result['greeks'] = self.get_option_greeks_from_chain(symbol)

            logger.info(f"Got option indicators for {symbol}: IV={result['iv']}, IVR={result['iv_rank']}")

        except Exception as e:
            logger.error(f"Error getting option indicators for {symbol}: {e}")

        return result


# 单例实例
_options_client_instance = None


def get_options_client() -> OptionsClient:
    """获取期权客户端单例"""
    global _options_client_instance
    if _options_client_instance is None:
        _options_client_instance = OptionsClient()
    return _options_client_instance
