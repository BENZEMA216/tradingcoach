import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
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

vi.mock('recharts', () => {
  const Container = ({ children }: { children?: ReactNode }) => <div>{children}</div>;
  const Empty = () => null;

  return {
    CartesianGrid: Empty,
    Legend: Empty,
    Line: Empty,
    LineChart: Container,
    ResponsiveContainer: Container,
    Tooltip: Empty,
    XAxis: Empty,
    YAxis: Empty,
  };
});

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
  it('prioritizes historical simulated delta over percentage shorthand', async () => {
    const user = userEvent.setup();

    renderBacktest([
      {
        rule_id: 'stop_loss',
        name_cn: '严格止损 -X%',
        name_en: 'Hard stop -X%',
        notes: '对任何亏损超过 -10.0% 的仓位，假设当时严格止损在 -10.0%。',
        notes_en: 'For any position that lost more than -10.0%, assume a hard stop at -10.0%.',
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

    expect(await screen.findByText('历史模拟多赚/少亏')).toBeInTheDocument();
    expect(screen.getByText('实际 $4,590.21 → 模拟 $16,857.26')).toBeInTheDocument();
    expect(screen.queryByText(/\+267%/)).not.toBeInTheDocument();
    expect(screen.queryByText('可省 / 多赚')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /严格止损 -X%/ }));

    expect(screen.getByText(/这不是收益率/)).toBeInTheDocument();
    expect(screen.getByText(/12267\.05 ÷ \|\$4,590\.21\| ≈ 2\.7 倍/)).toBeInTheDocument();
  });
});
