# reports - 报告生成层

生成交易复盘分析报告，提供可操作的交易洞察。

## 设计思路

### 核心理念

**问题**: 评分数字缺乏解释性，难以指导改进。

**解决方案**: 生成结构化报告，包含:
1. 汇总统计 - 全局视角
2. 详情分析 - 单笔复盘
3. 策略洞察 - 优化建议

### 报告类型

```
OptionTradeReport (期权报告)
    ├── generate_summary()         # 汇总统计
    ├── generate_position_detail() # 单笔详情
    └── generate_strategy_insights() # 策略洞察

[计划中]
├── PerformanceReport    # 绩效报告
├── RiskReport          # 风险报告
└── WeeklyDigest        # 周报摘要
```

## 文件说明

| 文件 | 说明 | 行数 |
|------|------|------|
| `option_report.py` | 期权交易报告生成器 | ~450 |

## OptionTradeReport

### 汇总统计 (generate_summary)

生成期权交易的全局统计视图。

```python
from src.reports.option_report import OptionTradeReport

report = OptionTradeReport(session)
summary = report.generate_summary(option_positions)
```

**输出结构**:

```python
{
    # 总体统计
    'total_count': 64,           # 期权交易总数
    'total_pnl': -1234.56,       # 总盈亏
    'win_rate': 0.35,            # 胜率
    'avg_win': 500.0,            # 平均盈利
    'avg_loss': -300.0,          # 平均亏损
    'profit_factor': 0.85,       # 盈亏比

    # 按类型分组
    'by_type': {
        'call': {
            'count': 40,
            'pnl': -800.0,
            'win_rate': 0.30,
            'avg_holding_days': 5.2
        },
        'put': {
            'count': 24,
            'pnl': -434.56,
            'win_rate': 0.42,
            'avg_holding_days': 4.8
        }
    },

    # 按 Moneyness 分组
    'by_moneyness': {
        'itm': {'count': 10, 'pnl': 200, 'win_rate': 0.60},
        'atm': {'count': 30, 'pnl': -500, 'win_rate': 0.40},
        'otm': {'count': 24, 'pnl': -934, 'win_rate': 0.20}
    },

    # 按 DTE 分组
    'by_dte': {
        'short': {'count': 15, 'pnl': -600, 'win_rate': 0.20},   # <7天
        'medium': {'count': 35, 'pnl': -400, 'win_rate': 0.40},  # 7-30天
        'long': {'count': 14, 'pnl': -234, 'win_rate': 0.50}     # >30天
    },

    # 按持有天数分组
    'by_holding_period': {
        'intraday': {'count': 5, 'pnl': -100},    # 当天
        'short': {'count': 30, 'pnl': -800},      # 1-5天
        'medium': {'count': 20, 'pnl': -300},     # 6-14天
        'long': {'count': 9, 'pnl': -34}          # >14天
    }
}
```

### 持仓详情 (generate_position_detail)

生成单笔期权交易的详细分析。

```python
detail = report.generate_position_detail(position)
```

**输出结构**:

```python
{
    # 基本信息
    'basic_info': {
        'symbol': 'AAPL250404C227500',
        'underlying': 'AAPL',
        'option_type': 'call',
        'strike': 227.50,
        'expiry': '2025-04-04',
        'direction': 'long',
        'quantity': 10,
        'entry_price': 5.50,
        'exit_price': 3.20,
        'pnl': -2300.00,
        'pnl_pct': -41.8
    },

    # 入场分析
    'entry_analysis': {
        'entry_date': '2025-03-15',
        'underlying_price': 220.00,
        'moneyness': -3.3,              # OTM 3.3%
        'moneyness_category': 'otm',
        'dte': 20,
        'dte_category': 'medium',
        'rsi_14': 45,
        'macd_signal': 'neutral',
        'trend_alignment': False,       # Call 但趋势向下
        'entry_score': 55
    },

    # 出场分析
    'exit_analysis': {
        'exit_date': '2025-03-25',
        'underlying_price': 215.00,
        'exit_dte': 10,
        'price_change': -2.27,          # 正股跌幅
        'hit_strike': False,
        'exit_score': 60
    },

    # Greeks 影响估算
    'greeks_impact': {
        'estimated_delta': 0.35,
        'delta_impact': -1750.00,       # Delta损失
        'estimated_theta': -0.15,
        'theta_impact': -150.00,        # Theta损失
        'total_theoretical_loss': -1900.00
    },

    # 评分详情
    'scores': {
        'entry_score': 55,
        'exit_score': 60,
        'strategy_score': 50,
        'overall_option_score': 55,
        'overall_combined_score': 58,
        'grade': 'D'
    },

    # 改进建议
    'suggestions': [
        "入场时 RSI 中性 (45)，建议等待超卖信号后买入 Call",
        "Moneyness -3.3% (OTM)，考虑选择更接近 ATM 的行权价",
        "DTE 20天较短，考虑选择 30-45 天到期的合约减少 Theta 损耗",
        "正股趋势向下时买入 Call，建议顺势交易或等待趋势反转"
    ]
}
```

### 策略洞察 (generate_strategy_insights)

基于历史交易数据生成优化建议。

```python
insights = report.generate_strategy_insights(option_positions)
```

**输出结构**:

```python
{
    # 最佳策略组合
    'best_strategies': [
        {
            'type': 'put',
            'moneyness': 'atm',
            'dte_range': '30-60',
            'win_rate': 0.65,
            'avg_pnl': 350.0,
            'sample_size': 15
        }
    ],

    # 亏损模式识别
    'loss_patterns': [
        {
            'pattern': 'OTM Call + Short DTE',
            'frequency': 12,
            'avg_loss': -450.0,
            'recommendation': '避免购买 DTE<7 天的 OTM Call'
        },
        {
            'pattern': '逆趋势交易',
            'frequency': 8,
            'avg_loss': -380.0,
            'recommendation': '等待趋势确认后再入场'
        }
    ],

    # 最优参数
    'optimal_params': {
        'best_dte_range': '30-60天',
        'best_moneyness': 'ATM ± 5%',
        'best_holding_period': '5-15天',
        'best_entry_rsi': '<35 (超卖买Call) 或 >65 (超买买Put)'
    },

    # 风险警示
    'risk_warnings': [
        "OTM 期权胜率仅 20%，考虑减少虚值期权交易",
        "短期期权 (<7天) 平均亏损 $400，建议延长到期时间"
    ],

    # 绩效对比
    'performance_comparison': {
        'call_vs_put': {
            'call_win_rate': 0.30,
            'put_win_rate': 0.42,
            'recommendation': '当前市场环境 Put 表现更好'
        },
        'moneyness_comparison': {
            'itm_roi': 15.0,
            'atm_roi': -5.0,
            'otm_roi': -25.0
        }
    }
}
```

## 使用流程

```
┌─────────────────────────────────────────────────────────────┐
│                 获取期权持仓列表                             │
│  SELECT * FROM positions WHERE is_option=1                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ 汇总统计    │   │ 详情分析    │   │ 策略洞察    │
│ summary()   │   │ detail()    │   │ insights()  │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    完整复盘报告                              │
│  - 整体表现如何?                                            │
│  - 每笔交易问题在哪?                                        │
│  - 如何优化策略?                                            │
└─────────────────────────────────────────────────────────────┘
```

## 扩展计划

### PerformanceReport (绩效报告)
- 月度/季度绩效统计
- 夏普比率、最大回撤
- 收益曲线图表

### RiskReport (风险报告)
- 风险敞口分析
- VaR 计算
- 集中度风险

### WeeklyDigest (周报)
- 本周交易汇总
- 关键指标变化
- 下周重点关注
