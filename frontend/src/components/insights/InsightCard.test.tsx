import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { InsightCard } from './InsightCard';
import type { TradingInsight } from '@/types';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: 'zh' },
    t: (_key: string, params?: { defaultValue?: string }) => params?.defaultValue ?? '',
  }),
}));

describe('InsightCard', () => {
  it('formats consecutive loss counts as counts instead of money', () => {
    const insight: TradingInsight = {
      id: 'S04-TSLL',
      type: 'problem',
      category: 'symbol',
      priority: 80,
      title: 'TSLL连续亏损',
      description: 'TSLL曾出现连续4笔亏损',
      suggestion: '暂停交易 TSLL',
      data_points: {
        symbol: 'TSLL',
        max_consecutive_losses: 4,
        trade_count: 60,
      },
    };

    render(<InsightCard insight={insight} />);

    expect(screen.getByText('TSLL · 4')).toBeInTheDocument();
    expect(screen.queryByText('TSLL · $4')).not.toBeInTheDocument();
  });
});
