"""
货币换算工具

input: position 对象 / 金额 + 币种
output: USD 等价金额
pos: 后端通用工具 - 把多币种 P&L 归一化到 USD，避免不同端点对总盈亏给出
     冲突数字（之前 /dashboard/kpis 直接对 HKD+USD 求和 = HK$ 当 $）

注意：当前是写死的近似汇率，足够给"USD-equivalent 概览"用。如果将来要更精确，
应当按 position.close_date 拉历史汇率。
"""

from typing import Optional


# 1 unit of CURRENCY = X USD
EXCHANGE_RATES = {
    "USD": 1.0,
    "HKD": 0.128,  # 1 HKD ≈ 0.128 USD (1 USD ≈ 7.8 HKD)
    "CNY": 0.14,   # 1 CNY ≈ 0.14 USD
}


def convert_to_usd(amount: Optional[float], currency: Optional[str]) -> float:
    """Convert an amount in the given currency to USD."""
    if amount is None:
        return 0.0
    rate = EXCHANGE_RATES.get((currency or "USD").upper(), 1.0)
    return float(amount) * rate


def get_pnl_in_usd(position) -> float:
    """Get a position's net_pnl in USD."""
    if not position or position.net_pnl is None:
        return 0.0
    return convert_to_usd(float(position.net_pnl), position.currency or "USD")


def get_fees_in_usd(position) -> float:
    """Get a position's total_fees in USD."""
    if not position or getattr(position, "total_fees", None) is None:
        return 0.0
    return convert_to_usd(float(position.total_fees), position.currency or "USD")
