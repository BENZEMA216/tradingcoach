-- TradingCoach Test Fixtures - 固定测试数据集
--
-- 用途: 数据完整性测试的固定数据，确保测试可重复
-- 数据设计: 涵盖股票/期权、做多/做空、盈利/亏损等场景
--
-- 使用方法:
--   1. 在内存数据库中执行此脚本
--   2. 运行数据完整性测试
--
-- 一旦我被更新，务必更新所属文件夹的README.md

-- ============================================================
-- 交易记录 (trades)
-- ============================================================

-- 股票做多 - 完整交易周期 (AAPL)
-- Position 1: AAPL 做多盈利
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, broker_id, trade_fingerprint, position_id)
VALUES
(1, 'AAPL', 'Apple Inc.', 'buy', 'filled', 150.0000, 100, 15000.00, '2024-01-15 14:30:00', '2024-01-15', '美股', 'USD', 1.00, 1.00, 0, 'test_broker', 'AAPL_BUY_20240115_100', 1),
(2, 'AAPL', 'Apple Inc.', 'sell', 'filled', 165.0000, 100, 16500.00, '2024-01-25 15:45:00', '2024-01-25', '美股', 'USD', 1.00, 1.00, 0, 'test_broker', 'AAPL_SELL_20240125_100', 1);

-- Position 2: GOOGL 做多亏损
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, broker_id, trade_fingerprint, position_id)
VALUES
(3, 'GOOGL', 'Alphabet Inc.', 'buy', 'filled', 140.0000, 50, 7000.00, '2024-02-01 10:15:00', '2024-02-01', '美股', 'USD', 0.50, 0.50, 0, 'test_broker', 'GOOGL_BUY_20240201_50', 2),
(4, 'GOOGL', 'Alphabet Inc.', 'sell', 'filled', 130.0000, 50, 6500.00, '2024-02-10 11:30:00', '2024-02-10', '美股', 'USD', 0.50, 0.50, 0, 'test_broker', 'GOOGL_SELL_20240210_50', 2);

-- 股票做空 - 完整交易周期 (TSLA)
-- Position 3: TSLA 做空盈利
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, broker_id, trade_fingerprint, position_id)
VALUES
(5, 'TSLA', 'Tesla Inc.', 'sell_short', 'filled', 250.0000, 30, 7500.00, '2024-03-01 09:30:00', '2024-03-01', '美股', 'USD', 0.75, 0.75, 0, 'test_broker', 'TSLA_SHORT_20240301_30', 3),
(6, 'TSLA', 'Tesla Inc.', 'buy_to_cover', 'filled', 220.0000, 30, 6600.00, '2024-03-15 14:00:00', '2024-03-15', '美股', 'USD', 0.75, 0.75, 0, 'test_broker', 'TSLA_COVER_20240315_30', 3);

-- Position 4: NVDA 做空亏损
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, broker_id, trade_fingerprint, position_id)
VALUES
(7, 'NVDA', 'NVIDIA Corp.', 'sell_short', 'filled', 500.0000, 20, 10000.00, '2024-03-20 10:00:00', '2024-03-20', '美股', 'USD', 1.00, 1.00, 0, 'test_broker', 'NVDA_SHORT_20240320_20', 4),
(8, 'NVDA', 'NVIDIA Corp.', 'buy_to_cover', 'filled', 550.0000, 20, 11000.00, '2024-04-01 11:30:00', '2024-04-01', '美股', 'USD', 1.00, 1.00, 0, 'test_broker', 'NVDA_COVER_20240401_20', 4);

-- 期权做多 CALL (NVDA Call Option)
-- Position 5: NVDA 期权做多盈利
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, underlying_symbol, option_type, strike_price, expiration_date, broker_id, trade_fingerprint, position_id)
VALUES
(9, 'NVDA240419C500000', 'NVDA 2024-04-19 $500 Call', 'buy', 'filled', 25.5000, 5, 12750.00, '2024-04-01 13:00:00', '2024-04-01', '美股', 'USD', 3.25, 3.25, 1, 'NVDA', 'CALL', 500.0000, '2024-04-19', 'test_broker', 'NVDA240419C500_BUY_5', 5),
(10, 'NVDA240419C500000', 'NVDA 2024-04-19 $500 Call', 'sell', 'filled', 35.0000, 5, 17500.00, '2024-04-15 10:30:00', '2024-04-15', '美股', 'USD', 3.25, 3.25, 1, 'NVDA', 'CALL', 500.0000, '2024-04-19', 'test_broker', 'NVDA240419C500_SELL_5', 5);

-- 期权做多 PUT (TSLA Put Option)
-- Position 6: TSLA 期权做多亏损
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, underlying_symbol, option_type, strike_price, expiration_date, broker_id, trade_fingerprint, position_id)
VALUES
(11, 'TSLA240517P200000', 'TSLA 2024-05-17 $200 Put', 'buy', 'filled', 8.0000, 10, 8000.00, '2024-05-01 14:00:00', '2024-05-01', '美股', 'USD', 6.50, 6.50, 1, 'TSLA', 'PUT', 200.0000, '2024-05-17', 'test_broker', 'TSLA240517P200_BUY_10', 6),
(12, 'TSLA240517P200000', 'TSLA 2024-05-17 $200 Put', 'sell', 'filled', 5.0000, 10, 5000.00, '2024-05-15 11:00:00', '2024-05-15', '美股', 'USD', 6.50, 6.50, 1, 'TSLA', 'PUT', 200.0000, '2024-05-17', 'test_broker', 'TSLA240517P200_SELL_10', 6);

-- 边界情况: 零费用交易
-- Position 7: META 零费用
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, broker_id, trade_fingerprint, position_id)
VALUES
(13, 'META', 'Meta Platforms', 'buy', 'filled', 300.0000, 10, 3000.00, '2024-06-01 10:00:00', '2024-06-01', '美股', 'USD', 0.00, 0.00, 0, 'test_broker', 'META_BUY_20240601_10', 7),
(14, 'META', 'Meta Platforms', 'sell', 'filled', 320.0000, 10, 3200.00, '2024-06-05 15:00:00', '2024-06-05', '美股', 'USD', 0.00, 0.00, 0, 'test_broker', 'META_SELL_20240605_10', 7);

-- 边界情况: 当日交易 (day trade)
-- Position 8: AMZN 当日交易
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, broker_id, trade_fingerprint, position_id)
VALUES
(15, 'AMZN', 'Amazon.com', 'buy', 'filled', 180.0000, 25, 4500.00, '2024-07-10 09:35:00', '2024-07-10', '美股', 'USD', 0.50, 0.50, 0, 'test_broker', 'AMZN_BUY_20240710_25', 8),
(16, 'AMZN', 'Amazon.com', 'sell', 'filled', 182.5000, 25, 4562.50, '2024-07-10 15:55:00', '2024-07-10', '美股', 'USD', 0.50, 0.50, 0, 'test_broker', 'AMZN_SELL_20240710_25', 8);

-- 未配对交易 (open position)
-- Position 9: MSFT 未平仓
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, broker_id, trade_fingerprint, position_id)
VALUES
(17, 'MSFT', 'Microsoft Corp.', 'buy', 'filled', 400.0000, 15, 6000.00, '2024-08-01 10:00:00', '2024-08-01', '美股', 'USD', 0.75, 0.75, 0, 'test_broker', 'MSFT_BUY_20240801_15', 9);

-- 多次加仓的交易
-- Position 10: AMD 分批买入
INSERT INTO trades (id, symbol, symbol_name, direction, status, filled_price, filled_quantity, filled_amount, filled_time, trade_date, market, currency, commission, total_fee, is_option, broker_id, trade_fingerprint, position_id)
VALUES
(18, 'AMD', 'AMD Inc.', 'buy', 'filled', 150.0000, 20, 3000.00, '2024-09-01 10:00:00', '2024-09-01', '美股', 'USD', 0.50, 0.50, 0, 'test_broker', 'AMD_BUY_20240901_20', 10),
(19, 'AMD', 'AMD Inc.', 'buy', 'filled', 145.0000, 30, 4350.00, '2024-09-05 11:00:00', '2024-09-05', '美股', 'USD', 0.50, 0.50, 0, 'test_broker', 'AMD_BUY_20240905_30', 10),
(20, 'AMD', 'AMD Inc.', 'sell', 'filled', 160.0000, 50, 8000.00, '2024-09-15 14:00:00', '2024-09-15', '美股', 'USD', 0.50, 0.50, 0, 'test_broker', 'AMD_SELL_20240915_50', 10);

-- ============================================================
-- 持仓记录 (positions)
-- ============================================================

-- Position 1: AAPL 做多盈利 (net_pnl = 1500 - 2 = 1498)
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, overall_score, score_grade, entry_quality_score, exit_quality_score, trend_quality_score, risk_mgmt_score)
VALUES
(1, 'AAPL', 'Apple Inc.', 'closed', 'long', '2024-01-15 14:30:00', '2024-01-25 15:45:00', '2024-01-15', '2024-01-25', 10, 150.0000, 165.0000, 100, 1500.00, 10.0000, 2.00, 1.00, 1.00, 1498.00, 9.9867, '美股', 'USD', 0, 85.00, 'B', 82.00, 88.00, 86.00, 84.00);

-- Position 2: GOOGL 做多亏损 (net_pnl = -500 - 1 = -501)
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, overall_score, score_grade, entry_quality_score, exit_quality_score, trend_quality_score, risk_mgmt_score)
VALUES
(2, 'GOOGL', 'Alphabet Inc.', 'closed', 'long', '2024-02-01 10:15:00', '2024-02-10 11:30:00', '2024-02-01', '2024-02-10', 9, 140.0000, 130.0000, 50, -500.00, -7.1429, 1.00, 0.50, 0.50, -501.00, -7.1571, '美股', 'USD', 0, 62.00, 'D', 55.00, 60.00, 68.00, 65.00);

-- Position 3: TSLA 做空盈利 (net_pnl = 900 - 1.5 = 898.50)
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, overall_score, score_grade, entry_quality_score, exit_quality_score, trend_quality_score, risk_mgmt_score)
VALUES
(3, 'TSLA', 'Tesla Inc.', 'closed', 'short', '2024-03-01 09:30:00', '2024-03-15 14:00:00', '2024-03-01', '2024-03-15', 14, 250.0000, 220.0000, 30, 900.00, 12.0000, 1.50, 0.75, 0.75, 898.50, 11.9800, '美股', 'USD', 0, 78.00, 'C', 75.00, 80.00, 78.00, 79.00);

-- Position 4: NVDA 做空亏损 (net_pnl = -1000 - 2 = -1002)
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, overall_score, score_grade, entry_quality_score, exit_quality_score, trend_quality_score, risk_mgmt_score)
VALUES
(4, 'NVDA', 'NVIDIA Corp.', 'closed', 'short', '2024-03-20 10:00:00', '2024-04-01 11:30:00', '2024-03-20', '2024-04-01', 12, 500.0000, 550.0000, 20, -1000.00, -10.0000, 2.00, 1.00, 1.00, -1002.00, -10.0200, '美股', 'USD', 0, 55.00, 'F', 50.00, 52.00, 58.00, 60.00);

-- Position 5: NVDA 期权做多盈利 (net_pnl = 950*100 - 6.5 = 9493.5) - 期权乘数100
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, underlying_symbol, option_type, strike_price, expiry_date, entry_dte, exit_dte, overall_score, score_grade, entry_quality_score, exit_quality_score, trend_quality_score, risk_mgmt_score, option_entry_score, option_exit_score, option_strategy_score)
VALUES
(5, 'NVDA240419C500000', 'NVDA 2024-04-19 $500 Call', 'closed', 'long', '2024-04-01 13:00:00', '2024-04-15 10:30:00', '2024-04-01', '2024-04-15', 14, 25.5000, 35.0000, 5, 4750.00, 37.2549, 6.50, 3.25, 3.25, 4743.50, 37.2039, '美股', 'USD', 1, 'NVDA', 'CALL', 500.0000, '2024-04-19', 18, 4, 82.00, 'B', 80.00, 85.00, 82.00, 81.00, 78.00, 85.00, 80.00);

-- Position 6: TSLA 期权做多亏损 (net_pnl = -300*100 - 13 = -3013)
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, underlying_symbol, option_type, strike_price, expiry_date, entry_dte, exit_dte, overall_score, score_grade, entry_quality_score, exit_quality_score, trend_quality_score, risk_mgmt_score, option_entry_score, option_exit_score, option_strategy_score)
VALUES
(6, 'TSLA240517P200000', 'TSLA 2024-05-17 $200 Put', 'closed', 'long', '2024-05-01 14:00:00', '2024-05-15 11:00:00', '2024-05-01', '2024-05-15', 14, 8.0000, 5.0000, 10, -3000.00, -37.5000, 13.00, 6.50, 6.50, -3013.00, -37.6625, '美股', 'USD', 1, 'TSLA', 'PUT', 200.0000, '2024-05-17', 16, 2, 58.00, 'F', 55.00, 52.00, 60.00, 65.00, 50.00, 48.00, 55.00);

-- Position 7: META 零费用 (net_pnl = 200 - 0 = 200)
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, overall_score, score_grade, entry_quality_score, exit_quality_score, trend_quality_score, risk_mgmt_score)
VALUES
(7, 'META', 'Meta Platforms', 'closed', 'long', '2024-06-01 10:00:00', '2024-06-05 15:00:00', '2024-06-01', '2024-06-05', 4, 300.0000, 320.0000, 10, 200.00, 6.6667, 0.00, 0.00, 0.00, 200.00, 6.6667, '美股', 'USD', 0, 75.00, 'C', 72.00, 78.00, 74.00, 76.00);

-- Position 8: AMZN 当日交易 (net_pnl = 62.5 - 1 = 61.5)
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, overall_score, score_grade, entry_quality_score, exit_quality_score, trend_quality_score, risk_mgmt_score)
VALUES
(8, 'AMZN', 'Amazon.com', 'closed', 'long', '2024-07-10 09:35:00', '2024-07-10 15:55:00', '2024-07-10', '2024-07-10', 0, 180.0000, 182.5000, 25, 62.50, 1.3889, 1.00, 0.50, 0.50, 61.50, 1.3667, '美股', 'USD', 0, 68.00, 'D', 65.00, 70.00, 68.00, 69.00);

-- Position 9: MSFT 未平仓
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, overall_score, score_grade)
VALUES
(9, 'MSFT', 'Microsoft Corp.', 'open', 'long', '2024-08-01 10:00:00', NULL, '2024-08-01', NULL, NULL, 400.0000, NULL, 15, NULL, NULL, 0.75, 0.75, NULL, NULL, NULL, '美股', 'USD', 0, NULL, NULL);

-- Position 10: AMD 分批买入 (加权均价 = (20*150 + 30*145)/50 = 147, net_pnl = 650 - 1.5 = 648.5)
INSERT INTO positions (id, symbol, symbol_name, status, direction, open_time, close_time, open_date, close_date, holding_period_days, open_price, close_price, quantity, realized_pnl, realized_pnl_pct, total_fees, open_fee, close_fee, net_pnl, net_pnl_pct, market, currency, is_option, overall_score, score_grade, entry_quality_score, exit_quality_score, trend_quality_score, risk_mgmt_score)
VALUES
(10, 'AMD', 'AMD Inc.', 'closed', 'long', '2024-09-01 10:00:00', '2024-09-15 14:00:00', '2024-09-01', '2024-09-15', 14, 147.0000, 160.0000, 50, 650.00, 8.8435, 1.50, 1.00, 0.50, 648.50, 8.8231, '美股', 'USD', 0, 80.00, 'B', 78.00, 82.00, 80.00, 80.00);
