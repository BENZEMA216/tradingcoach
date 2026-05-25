import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { TradingHeatmap } from './TradingHeatmap';
import type { TradingHeatmapCell } from '@/types';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'common.noData': '暂无数据',
        'charts.noTrades': '无交易',
        'charts.moreLoss': '更多亏损',
        'charts.moreProfit': '更多盈利',
        'charts.tradeCount': '交易数',
        'charts.avgPnl': '平均盈亏',
        'charts.tradingHeatmap': '交易时段热力图',
      };
      return translations[key] ?? key;
    },
  }),
}));

describe('TradingHeatmap', () => {
  it('renders backend trading hours directly without timezone shifting', () => {
    const data: TradingHeatmapCell[] = [
      {
        day_of_week: 0,
        day_name: 'Mon',
        hour: 9,
        trade_count: 46,
        win_rate: 71.74,
        avg_pnl: 90.7,
        total_pnl: 4172.02,
      },
      {
        day_of_week: 1,
        day_name: 'Tue',
        hour: 10,
        trade_count: 130,
        win_rate: 55.38,
        avg_pnl: -10.67,
        total_pnl: -1386.75,
      },
    ];

    const { container } = render(<TradingHeatmap data={data} bare />);

    expect(screen.getByText('按交易记录时间 · 共 176 笔 / 2 个时段')).toBeInTheDocument();
    expect(screen.getByText('9')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('46')).toBeInTheDocument();
    expect(screen.getByText('130')).toBeInTheDocument();
    expect(container.textContent).not.toContain('UTC');
  });
});
