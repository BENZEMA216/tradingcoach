import clsx from 'clsx';
import { formatPercent } from '@/utils/format';
import { usePrivacyFormat } from '@/hooks/usePrivacyFormat';

interface MetricItem {
  label: string;
  value: string | number;
  subLabel?: string;
}

interface HeroSummaryProps {
  period: string;
  totalPnL: number;
  totalTrades: number;
  winRate: number;
  profitFactor: number | null;
  expectancy: number | null;
  isZh: boolean;
}

export function HeroSummary({
  period,
  totalPnL,
  totalTrades,
  winRate,
  profitFactor,
  expectancy,
  isZh,
}: HeroSummaryProps) {
  const { formatPrivacyCurrency, formatPrivacyPnL } = usePrivacyFormat();

  // Generate summary text based on data
  const getSummary = () => {
    const performance = profitFactor && profitFactor > 1.5
      ? (isZh ? '表现优异' : 'EXCELLENT')
      : profitFactor && profitFactor > 1
        ? (isZh ? '表现稳健' : 'SOLID')
        : (isZh ? '需要改进' : 'NEEDS_WORK');

    if (isZh) {
      return `本周期完成 ${totalTrades} 笔交易，胜率 ${winRate.toFixed(1)}%，盈亏比 ${profitFactor?.toFixed(2) || '-'}，${performance}。`;
    }
    return `EXECUTED ${totalTrades} TRADES. WIN_RATE: ${winRate.toFixed(1)}%. PF: ${profitFactor?.toFixed(2) || 'N/A'}. STATUS: ${performance}.`;
  };

  const metrics: MetricItem[] = [
    {
      label: isZh ? '总交易' : 'Trades',
      value: totalTrades,
    },
    {
      label: isZh ? '胜率' : 'Win Rate',
      value: formatPercent(winRate, 1),
    },
    {
      label: isZh ? '盈亏比' : 'Profit Factor',
      value: profitFactor?.toFixed(2) || '-',
    },
    {
      label: isZh ? '期望值' : 'Expectancy',
      value: expectancy ? formatPrivacyCurrency(expectancy) : '-',
    },
  ];

  return (
    <div className="relative overflow-hidden bg-white dark:bg-black border border-neutral-200 dark:border-white/10 rounded-sm p-8 md:p-12 transition-colors">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-10 border-b border-neutral-200 dark:border-white/10 pb-6">
        <div>
          <p className="text-[10px] font-mono font-bold tracking-[0.2em] uppercase text-slate-400 dark:text-white/40">
            {isZh ? '交易报告' : 'PERFORMANCE_REPORT'}
          </p>
        </div>
        <p className="text-xs font-mono text-slate-500 dark:text-white/60">
          [{period}]
        </p>
      </div>

      {/* Hero Number */}
      <div className="mb-8">
        <p className={clsx(
          'text-5xl md:text-7xl font-mono font-bold tracking-tighter',
          totalPnL >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
        )}>
          {formatPrivacyPnL(totalPnL)}
        </p>
        <p className="text-[10px] font-mono font-bold tracking-[0.2em] uppercase text-slate-400 dark:text-white/40 mt-3">
          {isZh ? '净盈亏' : 'NET_PNL'}
        </p>
      </div>

      {/* Summary Text */}
      <p className="text-sm font-mono text-slate-500 dark:text-white/50 mb-10 max-w-2xl leading-relaxed uppercase">
        // {getSummary()}
      </p>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-8 border-t border-neutral-200 dark:border-white/10 pt-8">
        {metrics.map((metric, index) => (
          <div
            key={index}
            className="text-center md:text-left"
          >
            <p className="text-2xl font-mono font-medium text-slate-900 dark:text-white tracking-tight">
              {metric.value}
            </p>
            <p className="text-[9px] font-mono font-bold tracking-[0.2em] uppercase text-slate-400 dark:text-white/30 mt-1.5">
              {metric.label}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
