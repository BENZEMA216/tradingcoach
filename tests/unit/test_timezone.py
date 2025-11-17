"""
测试timezone.py模块
"""

import pytest
from datetime import datetime
import pytz

from src.utils.timezone import (
    parse_datetime_with_timezone,
    utc_to_local,
    get_market_timezone,
    is_market_open,
    parse_us_datetime,
    parse_hk_datetime,
    parse_cn_datetime,
    MARKET_TIMEZONES
)


class TestParseDatetimeWithTimezone:
    """测试时区解析函数"""

    def test_parse_us_eastern_time(self):
        """测试解析美东时间"""
        dt_str = "2025/11/03 09:38:46 (美东)"
        result = parse_datetime_with_timezone(dt_str)

        assert result is not None
        assert result.tzinfo == pytz.UTC
        # 美东9:38 = UTC 13:38 (EST) 或 14:38 (EDT)
        assert result.hour in [13, 14]  # 取决于夏令时

    def test_parse_hong_kong_time(self):
        """测试解析香港时间"""
        dt_str = "2025/10/22 11:38:00 (香港)"
        result = parse_datetime_with_timezone(dt_str)

        assert result is not None
        assert result.tzinfo == pytz.UTC
        # 香港11:38 = UTC 3:38 (HKT没有夏令时)
        assert result.hour == 3
        assert result.minute == 38

    def test_parse_with_timezone_hint(self):
        """测试使用时区提示"""
        dt_str = "2025/10/22 11:38:00"
        result = parse_datetime_with_timezone(dt_str, timezone_hint='港股')

        assert result is not None
        assert result.tzinfo == pytz.UTC

    def test_parse_different_formats(self):
        """测试不同的日期格式"""
        # 格式1: YYYY/MM/DD HH:MM:SS
        dt1 = parse_datetime_with_timezone("2025/10/22 11:38:00 (香港)")
        assert dt1 is not None

        # 格式2: YYYY-MM-DD HH:MM:SS
        dt2 = parse_datetime_with_timezone("2025-10-22 11:38:00 (香港)")
        assert dt2 is not None

        # 两个结果应该相同
        assert dt1 == dt2

    def test_parse_empty_string(self):
        """测试空字符串"""
        result = parse_datetime_with_timezone("")
        assert result is None

    def test_parse_none(self):
        """测试None值"""
        result = parse_datetime_with_timezone(None)
        assert result is None


class TestUtcToLocal:
    """测试UTC到本地时间转换"""

    def test_utc_to_us_eastern(self):
        """测试UTC转美东时间"""
        utc_time = datetime(2025, 1, 15, 14, 30, 0, tzinfo=pytz.UTC)
        local_time = utc_to_local(utc_time, '美股')

        assert local_time is not None
        # 美东时间应该比UTC早5或6小时（取决于夏令时）
        assert local_time.hour in [8, 9]

    def test_utc_to_hong_kong(self):
        """测试UTC转香港时间"""
        utc_time = datetime(2025, 1, 15, 3, 30, 0, tzinfo=pytz.UTC)
        local_time = utc_to_local(utc_time, '港股')

        assert local_time is not None
        # 香港时间 = UTC+8
        assert local_time.hour == 11
        assert local_time.minute == 30

    def test_invalid_market(self):
        """测试无效的市场类型"""
        utc_time = datetime(2025, 1, 15, 14, 30, 0, tzinfo=pytz.UTC)
        result = utc_to_local(utc_time, '无效市场')

        # 应该返回原始UTC时间
        assert result == utc_time

    def test_none_input(self):
        """测试None输入"""
        result = utc_to_local(None, '美股')
        assert result is None


class TestMarketTimezone:
    """测试市场时区获取"""

    def test_get_us_timezone(self):
        """测试获取美股时区"""
        tz = get_market_timezone('美股')
        assert tz == 'America/New_York'

    def test_get_hk_timezone(self):
        """测试获取港股时区"""
        tz = get_market_timezone('港股')
        assert tz == 'Asia/Hong_Kong'

    def test_get_cn_timezone(self):
        """测试获取A股时区"""
        tz = get_market_timezone('沪深')
        assert tz == 'Asia/Shanghai'

    def test_invalid_market(self):
        """测试无效市场"""
        tz = get_market_timezone('无效市场')
        assert tz == 'UTC'


class TestIsMarketOpen:
    """测试市场开盘判断"""

    def test_us_market_open_time(self):
        """测试美股开盘时间（9:30-16:00 ET）"""
        # 创建美东时间 2025年1月15日 10:00（星期三）
        et_tz = pytz.timezone('America/New_York')
        et_time = et_tz.localize(datetime(2025, 1, 15, 10, 0, 0))

        result = is_market_open(et_time, '美股')
        assert result is True

    def test_us_market_closed_time(self):
        """测试美股闭市时间"""
        et_tz = pytz.timezone('America/New_York')
        et_time = et_tz.localize(datetime(2025, 1, 15, 17, 0, 0))

        result = is_market_open(et_time, '美股')
        assert result is False

    def test_weekend(self):
        """测试周末"""
        # 2025年1月18日是周六
        et_tz = pytz.timezone('America/New_York')
        et_time = et_tz.localize(datetime(2025, 1, 18, 10, 0, 0))

        result = is_market_open(et_time, '美股')
        assert result is False


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_parse_us_datetime(self):
        """测试美东时间解析便捷函数"""
        dt_str = "2025/10/22 09:30:00"
        result = parse_us_datetime(dt_str)

        assert result is not None
        assert result.tzinfo == pytz.UTC

    def test_parse_hk_datetime(self):
        """测试香港时间解析便捷函数"""
        dt_str = "2025/10/22 09:30:00"
        result = parse_hk_datetime(dt_str)

        assert result is not None
        assert result.tzinfo == pytz.UTC

    def test_parse_cn_datetime(self):
        """测试中国时间解析便捷函数"""
        dt_str = "2025/10/22 09:30:00"
        result = parse_cn_datetime(dt_str)

        assert result is not None
        assert result.tzinfo == pytz.UTC


class TestMarketTimezonesConstant:
    """测试市场时区常量"""

    def test_market_timezones_dict(self):
        """测试MARKET_TIMEZONES字典"""
        assert '美股' in MARKET_TIMEZONES
        assert '港股' in MARKET_TIMEZONES
        assert '沪深' in MARKET_TIMEZONES

        assert MARKET_TIMEZONES['美股'] == 'America/New_York'
        assert MARKET_TIMEZONES['港股'] == 'Asia/Hong_Kong'
        assert MARKET_TIMEZONES['沪深'] == 'Asia/Shanghai'
