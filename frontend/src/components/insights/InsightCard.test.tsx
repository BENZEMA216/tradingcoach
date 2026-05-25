import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { InsightCard } from './InsightCard';
import type { TradingInsight } from '@/types';

const translations = vi.hoisted<Record<string, string>>(() => ({
  'insightRules.H03.title': '{{better}}交易更擅长',
  'insightRules.H03.description': '{{better}}交易胜率{{better_wr}}%，而{{worse}}交易仅{{worse_wr}}%',
  'insightRules.H03.suggestion': '可以考虑增加{{better}}交易的比重，减少{{worse}}交易',
  'insightRules.P02-weekly.title': '连续3周亏损',
  'insightRules.P02-weekly.description': '最近3周连续亏损，共亏损${{total_loss_display}}',
  'insightRules.P02-weekly.suggestion': '建议暂停交易，深入分析原因后再恢复',
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    i18n: {
      language: 'zh',
      exists: (key: string) => key in translations,
    },
    t: (key: string, params?: Record<string, unknown> & { defaultValue?: string }) => {
      const template = translations[key] ?? params?.defaultValue ?? '';
      return template.replace(/{{(.*?)}}/g, (_match, token: string) => {
        const value = params?.[token.trim()];
        return value === undefined || value === null ? `{{${token}}}` : String(value);
      });
    },
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

  it('uses exact rule translation before stripping symbol-like suffixes', () => {
    const insight: TradingInsight = {
      id: 'P02-weekly',
      type: 'problem',
      category: 'trend',
      priority: 85,
      title: '连续3周亏损',
      description: '最近3周连续亏损，共亏损$6,939',
      suggestion: '建议暂停交易，深入分析原因后再恢复',
      data_points: {
        weeks_negative: 3,
        total_loss: -6938.5,
        total_loss_display: '6,939',
      },
    };

    render(<InsightCard insight={insight} />);

    expect(screen.getByText('连续3周亏损')).toBeInTheDocument();
    expect(screen.getByText('最近3周连续亏损，共亏损$6,939')).toBeInTheDocument();
    expect(screen.queryByText('近期表现下滑')).not.toBeInTheDocument();
    expect(screen.queryByText(/{{/)).not.toBeInTheDocument();
  });

  it('interpolates holding style insight copy', () => {
    const insight: TradingInsight = {
      id: 'H03',
      type: 'reminder',
      category: 'holding',
      priority: 65,
      title: '波段交易更擅长',
      description: '波段交易胜率60%，而日内交易仅37%',
      suggestion: '可以考虑增加波段交易的比重，减少日内交易',
      data_points: {
        intraday_count: 112,
        intraday_win_rate: 36.6,
        swing_count: 310,
        swing_win_rate: 60.3,
        better: '波段',
        worse: '日内',
        better_style: 'swing',
        worse_style: 'intraday',
        better_wr: 60.3,
        worse_wr: 36.6,
      },
    };

    render(<InsightCard insight={insight} />);

    expect(screen.getByText('波段交易更擅长')).toBeInTheDocument();
    expect(screen.getByText('波段交易胜率60.3%，而日内交易仅36.6%')).toBeInTheDocument();
    expect(screen.queryByText(/{{/)).not.toBeInTheDocument();
  });
});
