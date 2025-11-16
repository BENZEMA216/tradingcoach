"""
时区转换工具

处理不同市场的时区转换，统一转换为UTC时间存储
"""

from datetime import datetime
import pytz
import re
import logging

logger = logging.getLogger(__name__)

# 市场时区映射
MARKET_TIMEZONES = {
    '美股': 'America/New_York',      # 美东时间 (EST/EDT)
    '港股': 'Asia/Hong_Kong',        # 香港时间 (HKT)
    '沪深': 'Asia/Shanghai',         # 中国时间 (CST)
}


def parse_datetime_with_timezone(datetime_str: str, timezone_hint: str = None) -> datetime:
    """
    解析带时区标记的时间字符串，转换为UTC时间

    Args:
        datetime_str: 时间字符串，如 "2025/11/03 09:38:46 (美东)"
        timezone_hint: 时区提示（如果字符串中没有时区信息）

    Returns:
        datetime: UTC时间

    Examples:
        >>> parse_datetime_with_timezone("2025/11/03 09:38:46 (美东)")
        datetime(2025, 11, 3, 13, 38, 46, tzinfo=UTC)  # 美东9:38 = UTC 13:38

        >>> parse_datetime_with_timezone("2025/10/22 11:38:00 (香港)")
        datetime(2025, 10, 22, 3, 38, 0, tzinfo=UTC)  # 香港11:38 = UTC 3:38
    """
    if not datetime_str or datetime_str.strip() == '':
        return None

    try:
        # 从字符串中提取时区标记
        timezone_match = re.search(r'\(([^)]+)\)', datetime_str)
        if timezone_match:
            timezone_name = timezone_match.group(1)
            # 移除时区标记，只保留日期时间部分
            datetime_part = re.sub(r'\s*\([^)]+\)', '', datetime_str).strip()
        else:
            timezone_name = timezone_hint
            datetime_part = datetime_str.strip()

        # 解析日期时间
        # 支持格式: "2025/11/03 09:38:46" 或 "2025-11-03 09:38:46"
        for fmt in ['%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M', '%Y-%m-%d %H:%M']:
            try:
                naive_dt = datetime.strptime(datetime_part, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unable to parse datetime: {datetime_part}")

        # 确定时区
        if timezone_name in MARKET_TIMEZONES:
            tz_name = MARKET_TIMEZONES[timezone_name]
        elif timezone_name in ['美东', 'ET', 'EST', 'EDT']:
            tz_name = 'America/New_York'
        elif timezone_name in ['香港', 'HKT']:
            tz_name = 'Asia/Hong_Kong'
        elif timezone_name in ['中国', 'CST', 'Beijing']:
            tz_name = 'Asia/Shanghai'
        else:
            logger.warning(f"Unknown timezone: {timezone_name}, using UTC")
            return naive_dt.replace(tzinfo=pytz.UTC)

        # 本地化时间
        local_tz = pytz.timezone(tz_name)
        local_dt = local_tz.localize(naive_dt)

        # 转换为UTC
        utc_dt = local_dt.astimezone(pytz.UTC)

        logger.debug(f"Converted {datetime_str} -> {utc_dt} UTC")
        return utc_dt

    except Exception as e:
        logger.error(f"Error parsing datetime '{datetime_str}': {e}")
        return None


def utc_to_local(utc_dt: datetime, market: str) -> datetime:
    """
    将UTC时间转换为本地市场时间

    Args:
        utc_dt: UTC时间
        market: 市场类型 ('美股', '港股', '沪深')

    Returns:
        datetime: 本地时间
    """
    if not utc_dt:
        return None

    if market not in MARKET_TIMEZONES:
        logger.warning(f"Unknown market: {market}, returning UTC time")
        return utc_dt

    try:
        # 确保输入是UTC时间
        if utc_dt.tzinfo is None:
            utc_dt = pytz.UTC.localize(utc_dt)
        elif utc_dt.tzinfo != pytz.UTC:
            utc_dt = utc_dt.astimezone(pytz.UTC)

        # 转换到本地时区
        local_tz = pytz.timezone(MARKET_TIMEZONES[market])
        local_dt = utc_dt.astimezone(local_tz)

        return local_dt

    except Exception as e:
        logger.error(f"Error converting to local time: {e}")
        return utc_dt


def get_market_timezone(market: str) -> str:
    """
    获取市场的时区名称

    Args:
        market: 市场类型

    Returns:
        str: pytz时区名称
    """
    return MARKET_TIMEZONES.get(market, 'UTC')


def is_market_open(dt: datetime, market: str) -> bool:
    """
    判断给定时间市场是否开盘

    Args:
        dt: 时间（任意时区）
        market: 市场类型

    Returns:
        bool: True表示开盘时间
    """
    # 转换到市场本地时间
    local_dt = utc_to_local(dt, market)
    if not local_dt:
        return False

    # 周末不开盘
    if local_dt.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False

    hour = local_dt.hour
    minute = local_dt.minute

    if market == '美股':
        # 美股: 9:30-16:00 (美东时间)
        return (hour == 9 and minute >= 30) or (10 <= hour < 16)
    elif market == '港股':
        # 港股: 9:30-12:00, 13:00-16:00 (香港时间)
        morning = (hour == 9 and minute >= 30) or (10 <= hour < 12)
        afternoon = (13 <= hour < 16)
        return morning or afternoon
    elif market == '沪深':
        # A股: 9:30-11:30, 13:00-15:00 (北京时间)
        morning = (hour == 9 and minute >= 30) or (10 <= hour < 11) or (hour == 11 and minute < 30)
        afternoon = (13 <= hour < 15)
        return morning or afternoon

    return False


# 便捷函数
def parse_us_datetime(datetime_str: str) -> datetime:
    """解析美东时间"""
    return parse_datetime_with_timezone(datetime_str, timezone_hint='美股')


def parse_hk_datetime(datetime_str: str) -> datetime:
    """解析香港时间"""
    return parse_datetime_with_timezone(datetime_str, timezone_hint='港股')


def parse_cn_datetime(datetime_str: str) -> datetime:
    """解析中国时间"""
    return parse_datetime_with_timezone(datetime_str, timezone_hint='沪深')
