import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Backtest } from './Backtest';
import { backtestApi, type BacktestResult } from '@/api/client';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: 'zh' },
  }),
}));

vi.mock('@/api/client', () => ({
  backtestApi: {
    summary: vi.fn(),
  },
}));

function renderBacktest(results: BacktestResult[]) {
  vi.mocked(backtestApi.summary).mockResolvedValue(results);

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <Backtest />
    </QueryClientProvider>
  );
}

describe('Backtest', () => {
  it('explains that the backtest percentage is relative to actual P&L', async () => {
    renderBacktest([
      {
        rule_id: 'stop_loss',
        name_cn: '严格止损 -X%',
        name_en: 'Hard stop -X%',
        notes: '对任何亏损超过 -10.0% 的仓位，假设当时严格止损在 -10.0%。',
        params: { stop_loss_pct: -10 },
        skipped_count: 112,
        actual_total_pnl: 4590.21,
        counterfactual_total_pnl: 16857.26,
        savings: 12267.05,
        savings_pct: 267.24,
        monthly: [],
        skipped_by_symbol: { TSLA: 1 },
      },
    ]);

    expect(await screen.findByText('模拟改善')).toBeInTheDocument();
    expect(screen.getByText('+267% / |实际盈亏| $4,590.21')).toBeInTheDocument();
    expect(screen.queryByText('可省 / 多赚')).not.toBeInTheDocument();
  });
});
