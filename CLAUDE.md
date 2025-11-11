# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a trading coach project in early development. The repository currently contains:
- Trading transaction data from a brokerage account (Chinese securities/options trading)
- Placeholder documentation files

## Data Structure

The primary data source is in `original_data/历史-保证金综合账户(2663)-20251103-231527.csv`, which contains trading history with the following key fields:
- Transaction direction (买入/卖出 - Buy/Sell)
- Security code and name
- Order details: price, quantity, amount
- Execution details: filled price, timestamp
- Transaction fees breakdown (commission, platform fees, clearing fees, taxes, etc.)
- Market type (美股 - US stocks)
- Currency (USD)

The data includes both stock and options transactions (e.g., AMZN, HIMS stock and AMZN options).

## Repository Structure

```
.
├── CLAUDE.md                    # This file
├── original_data/               # Raw trading data
│   ├── readme.md                # (placeholder)
│   └── 历史-保证金综合账户*.csv  # Brokerage transaction history
└── project_docs/                # Project documentation
    ├── PRD.md                   # Product requirements (to be written)
    └── readme.md                # (placeholder)
```

## Development Notes

When implementing this project:

1. **CSV Data Handling**: The transaction CSV file uses Chinese field names and UTF-8 encoding with BOM. Consider using pandas with `encoding='utf-8-sig'` when reading.

2. **Data Fields**: Key fields for analysis include:
   - 方向: Transaction direction
   - 代码/名称: Security code/name
   - 订单价格/成交价格: Order/execution price
   - 订单数量/成交数量: Order/execution quantity
   - 下单时间/成交时间: Order/execution timestamp
   - 合计费用: Total fees

3. **Documentation**: The PRD.md file should be populated with product requirements before major development begins.
