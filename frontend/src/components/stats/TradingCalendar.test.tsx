import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { TradingCalendar } from './TradingCalendar';
import { statisticsApi } from '@/api/client';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: { language: 'zh' },
  }),
}));

vi.mock('@/api/client', () => ({
  statisticsApi: {
    getCalendarHeatmap: vi.fn(),
  },
}));

function renderCalendar(anchorDate: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <TradingCalendar anchorDate={anchorDate} />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('TradingCalendar', () => {
  it('opens the anchor month and renders pnl/trade_count calendar data', async () => {
    vi.mocked(statisticsApi.getCalendarHeatmap).mockResolvedValue([
      {
        date: '2025-12-02',
        pnl: -1342.48,
        trade_count: 7,
        is_winner: false,
      },
    ]);

    renderCalendar('2025-12-02');

    expect(await screen.findByText('十二月 2025')).toBeInTheDocument();
    expect(await screen.findAllByText('7')).not.toHaveLength(0);
    expect(await screen.findByText('1,342.48')).toBeInTheDocument();
    expect(statisticsApi.getCalendarHeatmap).toHaveBeenCalledWith(2025);
  });
});
