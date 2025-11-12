#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易数据分析脚本 - 生成第一份复盘报告
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


def load_data(filepath):
    """加载CSV数据"""
    print("正在加载交易数据...")
    df = pd.read_csv(filepath, encoding='utf-8-sig')
    print(f"共加载 {len(df)} 条记录")
    return df


def clean_data(df):
    """清洗数据"""
    print("\n正在清洗数据...")

    # 只保留已成交的记录
    df_clean = df[df['交易状态'] == '全部成交'].copy()
    print(f"过滤后保留 {len(df_clean)} 条已成交记录")

    # 转换数值字段
    df_clean['成交价格'] = pd.to_numeric(df_clean['成交价格'], errors='coerce')
    df_clean['成交数量'] = pd.to_numeric(df_clean['成交数量'], errors='coerce')
    df_clean['成交金额'] = pd.to_numeric(df_clean['成交金额'], errors='coerce')
    df_clean['合计费用'] = pd.to_numeric(df_clean['合计费用'], errors='coerce')

    # 转换时间字段
    df_clean['成交时间_parsed'] = pd.to_datetime(
        df_clean['成交时间'].str.extract(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})')[0],
        format='%Y/%m/%d %H:%M:%S',
        errors='coerce'
    )

    return df_clean


def calculate_basic_metrics(df):
    """计算基础指标"""
    print("\n=== 基础统计指标 ===")

    metrics = {}

    # 交易次数
    total_trades = len(df)
    metrics['总交易次数'] = total_trades
    print(f"总交易次数: {total_trades}")

    # 买入和卖出次数
    buy_trades = len(df[df['方向'].isin(['买入'])])
    sell_trades = len(df[df['方向'].isin(['卖出', '卖空'])])
    metrics['买入次数'] = buy_trades
    metrics['卖出次数'] = sell_trades
    print(f"买入次数: {buy_trades}")
    print(f"卖出次数: {sell_trades}")

    # 总交易金额
    total_amount = df['成交金额'].sum()
    metrics['总交易金额'] = total_amount
    print(f"总交易金额: ${total_amount:,.2f}")

    # 总费用
    total_fees = df['合计费用'].sum()
    metrics['总费用'] = total_fees
    print(f"总费用: ${total_fees:,.2f}")
    print(f"费用率: {(total_fees / total_amount * 100):.3f}%")

    return metrics


def analyze_by_symbol(df):
    """按标的分析"""
    print("\n=== 按标的分析 ===")

    # 统计每个标的的交易次数
    symbol_stats = df.groupby('代码').agg({
        '成交金额': 'sum',
        '合计费用': 'sum',
        '方向': 'count'
    }).rename(columns={'方向': '交易次数'})

    symbol_stats = symbol_stats.sort_values('交易次数', ascending=False)

    print("\n交易次数最多的10个标的:")
    print(symbol_stats.head(10).to_string())

    return symbol_stats


def analyze_by_market(df):
    """按市场分析"""
    print("\n=== 按市场分析 ===")

    market_stats = df.groupby('市场').agg({
        '成交金额': 'sum',
        '合计费用': 'sum',
        '方向': 'count'
    }).rename(columns={'方向': '交易次数'})

    print("\n各市场统计:")
    print(market_stats.to_string())

    return market_stats


def analyze_by_direction(df):
    """按方向分析"""
    print("\n=== 按交易方向分析 ===")

    direction_stats = df.groupby('方向').agg({
        '成交金额': ['sum', 'mean'],
        '合计费用': 'sum',
        '代码': 'count'
    })

    direction_stats.columns = ['总金额', '平均金额', '总费用', '交易次数']

    print("\n各方向统计:")
    print(direction_stats.to_string())

    return direction_stats


def analyze_time_pattern(df):
    """分析时间模式"""
    print("\n=== 时间模式分析 ===")

    df_time = df[df['成交时间_parsed'].notna()].copy()

    # 按日期统计
    df_time['日期'] = df_time['成交时间_parsed'].dt.date
    daily_stats = df_time.groupby('日期').agg({
        '代码': 'count',
        '成交金额': 'sum'
    }).rename(columns={'代码': '交易次数'})

    print(f"\n交易日期范围: {df_time['日期'].min()} 至 {df_time['日期'].max()}")
    print(f"交易天数: {len(daily_stats)}")
    print(f"平均每日交易次数: {daily_stats['交易次数'].mean():.1f}")

    # 按星期几统计
    df_time['星期'] = df_time['成交时间_parsed'].dt.dayofweek
    weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
    df_time['星期名'] = df_time['星期'].map(weekday_map)

    weekday_stats = df_time.groupby('星期名').size()
    print("\n按星期几统计:")
    for day in ['周一', '周二', '周三', '周四', '周五', '周六', '周日']:
        if day in weekday_stats.index:
            print(f"{day}: {weekday_stats[day]} 次")

    return daily_stats


def identify_paired_trades(df):
    """识别配对交易（简化版）"""
    print("\n=== 配对交易分析 ===")

    paired_trades = []

    # 按标的分组
    for symbol in df['代码'].unique():
        symbol_df = df[df['代码'] == symbol].copy()
        symbol_df = symbol_df.sort_values('成交时间_parsed')

        # 简单配对逻辑：买入后卖出
        buy_records = symbol_df[symbol_df['方向'] == '买入']
        sell_records = symbol_df[symbol_df['方向'].isin(['卖出', '卖空'])]

        for _, buy in buy_records.iterrows():
            # 找到买入后的第一笔卖出
            later_sells = sell_records[sell_records['成交时间_parsed'] > buy['成交时间_parsed']]
            if not later_sells.empty:
                sell = later_sells.iloc[0]

                # 计算盈亏（简化计算）
                buy_amount = buy['成交金额'] + buy['合计费用']
                sell_amount = sell['成交金额'] - sell['合计费用']

                pnl = sell_amount - buy_amount
                pnl_pct = (pnl / buy_amount) * 100 if buy_amount > 0 else 0

                paired_trades.append({
                    '标的': symbol,
                    '名称': buy['名称'],
                    '买入时间': buy['成交时间_parsed'],
                    '卖出时间': sell['成交时间_parsed'],
                    '买入价': buy['成交价格'],
                    '卖出价': sell['成交价格'],
                    '数量': buy['成交数量'],
                    '买入金额': buy_amount,
                    '卖出金额': sell_amount,
                    '盈亏': pnl,
                    '盈亏率': pnl_pct,
                    '市场': buy['市场']
                })

    if paired_trades:
        paired_df = pd.DataFrame(paired_trades)

        print(f"\n识别到 {len(paired_df)} 对配对交易")

        # 盈亏统计
        profit_trades = paired_df[paired_df['盈亏'] > 0]
        loss_trades = paired_df[paired_df['盈亏'] < 0]

        print(f"盈利交易: {len(profit_trades)} 笔")
        print(f"亏损交易: {len(loss_trades)} 笔")

        if len(paired_df) > 0:
            win_rate = len(profit_trades) / len(paired_df) * 100
            print(f"胜率: {win_rate:.2f}%")

        total_pnl = paired_df['盈亏'].sum()
        print(f"\n总盈亏: ${total_pnl:,.2f}")

        if len(profit_trades) > 0:
            avg_profit = profit_trades['盈亏'].mean()
            print(f"平均盈利: ${avg_profit:,.2f}")

        if len(loss_trades) > 0:
            avg_loss = loss_trades['盈亏'].mean()
            print(f"平均亏损: ${avg_loss:,.2f}")

        # 最佳和最差交易
        print("\n最佳交易:")
        best_trade = paired_df.loc[paired_df['盈亏'].idxmax()]
        print(f"  {best_trade['名称']} ({best_trade['标的']})")
        print(f"  盈亏: ${best_trade['盈亏']:,.2f} ({best_trade['盈亏率']:.2f}%)")
        print(f"  时间: {best_trade['买入时间'].date()} -> {best_trade['卖出时间'].date()}")

        print("\n最差交易:")
        worst_trade = paired_df.loc[paired_df['盈亏'].idxmin()]
        print(f"  {worst_trade['名称']} ({worst_trade['标的']})")
        print(f"  盈亏: ${worst_trade['盈亏']:,.2f} ({worst_trade['盈亏率']:.2f}%)")
        print(f"  时间: {worst_trade['买入时间'].date()} -> {worst_trade['卖出时间'].date()}")

        return paired_df

    return None


def generate_insights(df, paired_df):
    """生成AI洞察"""
    print("\n" + "=" * 60)
    print("=== 📊 交易复盘洞察 ===")
    print("=" * 60)

    insights = []

    # 洞察1: 交易频率
    date_range = (df['成交时间_parsed'].max() - df['成交时间_parsed'].min()).days
    if date_range > 0:
        trades_per_day = len(df) / date_range
        insights.append(f"1. 📈 交易频率: 平均每天 {trades_per_day:.1f} 笔交易")
        if trades_per_day > 5:
            insights.append("   ⚠️  交易频率较高，建议关注是否存在过度交易")

    # 洞察2: 费用分析
    total_fees = df['合计费用'].sum()
    total_amount = df['成交金额'].sum()
    fee_rate = (total_fees / total_amount * 100) if total_amount > 0 else 0
    insights.append(f"\n2. 💰 费用分析: 总费用 ${total_fees:,.2f}, 占交易额 {fee_rate:.3f}%")
    if fee_rate > 0.5:
        insights.append("   💡 费用占比较高，可能因为交易金额较小或交易频繁")

    # 洞察3: 市场偏好
    market_counts = df['市场'].value_counts()
    top_market = market_counts.index[0]
    insights.append(f"\n3. 🌍 市场偏好: 主要交易市场为 {top_market} ({market_counts[top_market]} 笔)")

    # 洞察4: 标的集中度
    symbol_counts = df['代码'].value_counts()
    top_3_symbols = symbol_counts.head(3)
    insights.append(f"\n4. 🎯 标的集中度: 交易最频繁的3个标的:")
    for i, (symbol, count) in enumerate(top_3_symbols.items(), 1):
        symbol_name = df[df['代码'] == symbol]['名称'].iloc[0]
        insights.append(f"   {i}. {symbol_name} ({symbol}): {count} 笔")

    # 洞察5: 配对交易表现
    if paired_df is not None and len(paired_df) > 0:
        win_rate = len(paired_df[paired_df['盈亏'] > 0]) / len(paired_df) * 100
        total_pnl = paired_df['盈亏'].sum()
        insights.append(f"\n5. 🎲 交易表现: 胜率 {win_rate:.1f}%, 总盈亏 ${total_pnl:,.2f}")

        if win_rate > 50:
            insights.append(f"   ✅ 胜率超过50%，整体表现不错")
        else:
            insights.append(f"   ⚠️  胜率低于50%，需要反思交易策略")

        if total_pnl > 0:
            insights.append(f"   ✅ 实现正收益")
        else:
            insights.append(f"   ⚠️  当前亏损，需要调整")

    # 洞察6: 交易类型
    has_options = any('C' in str(code) or 'P' in str(code) for code in df['代码'])
    if has_options:
        insights.append(f"\n6. 📋 交易类型: 包含期权交易")
        insights.append("   💡 期权交易风险较高，需要严格的风险管理")

    # 打印所有洞察
    for insight in insights:
        print(insight)

    return insights


def generate_report(df, paired_df):
    """生成完整报告"""
    print("\n" + "=" * 60)
    print("=== 📄 交易复盘报告 ===")
    print("=" * 60)
    print(f"\n报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 基础信息
    print("\n【报告期间】")
    date_min = df['成交时间_parsed'].min()
    date_max = df['成交时间_parsed'].max()
    print(f"从 {date_min.date()} 到 {date_max.date()}")
    print(f"共 {(date_max - date_min).days} 天")

    # 交易概况
    print("\n【交易概况】")
    print(f"总交易笔数: {len(df)}")
    print(f"买入: {len(df[df['方向'] == '买入'])} 笔")
    print(f"卖出: {len(df[df['方向'].isin(['卖出', '卖空'])])} 笔")
    print(f"总交易金额: ${df['成交金额'].sum():,.2f}")
    print(f"总费用: ${df['合计费用'].sum():,.2f}")

    # 市场分布
    print("\n【市场分布】")
    for market, count in df['市场'].value_counts().items():
        pct = count / len(df) * 100
        print(f"{market}: {count} 笔 ({pct:.1f}%)")

    # 标的统计
    print("\n【交易标的 TOP 5】")
    top_symbols = df['代码'].value_counts().head(5)
    for i, (symbol, count) in enumerate(top_symbols.items(), 1):
        name = df[df['代码'] == symbol]['名称'].iloc[0]
        print(f"{i}. {name} ({symbol}): {count} 笔")

    # 配对交易分析
    if paired_df is not None and len(paired_df) > 0:
        print("\n【配对交易分析】")
        print(f"配对交易数: {len(paired_df)}")
        profit_count = len(paired_df[paired_df['盈亏'] > 0])
        loss_count = len(paired_df[paired_df['盈亏'] < 0])
        print(f"盈利: {profit_count} 笔")
        print(f"亏损: {loss_count} 笔")
        print(f"胜率: {profit_count / len(paired_df) * 100:.2f}%")
        print(f"总盈亏: ${paired_df['盈亏'].sum():,.2f}")

        if profit_count > 0:
            print(f"平均盈利: ${paired_df[paired_df['盈亏'] > 0]['盈亏'].mean():,.2f}")
        if loss_count > 0:
            print(f"平均亏损: ${paired_df[paired_df['盈亏'] < 0]['盈亏'].mean():,.2f}")

        print(f"最大盈利: ${paired_df['盈亏'].max():,.2f}")
        print(f"最大亏损: ${paired_df['盈亏'].min():,.2f}")


def main():
    """主函数"""
    print("=" * 60)
    print("交易数据分析与复盘报告系统")
    print("=" * 60)

    # 加载数据
    filepath = 'original_data/历史-保证金综合账户(2663)-20251103-231527.csv'
    df = load_data(filepath)

    # 清洗数据
    df_clean = clean_data(df)

    # 基础指标分析
    metrics = calculate_basic_metrics(df_clean)

    # 按标的分析
    symbol_stats = analyze_by_symbol(df_clean)

    # 按市场分析
    market_stats = analyze_by_market(df_clean)

    # 按方向分析
    direction_stats = analyze_by_direction(df_clean)

    # 时间模式分析
    daily_stats = analyze_time_pattern(df_clean)

    # 配对交易分析
    paired_df = identify_paired_trades(df_clean)

    # 生成洞察
    insights = generate_insights(df_clean, paired_df)

    # 生成完整报告
    generate_report(df_clean, paired_df)

    print("\n" + "=" * 60)
    print("报告生成完成！")
    print("=" * 60)

    # 保存配对交易数据
    if paired_df is not None:
        output_file = 'paired_trades_analysis.csv'
        paired_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n配对交易详细数据已保存到: {output_file}")


if __name__ == '__main__':
    main()
