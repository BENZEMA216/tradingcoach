import clsx from 'clsx';
import { formatCurrency, formatPercent } from '@/utils/format';

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
  // Generate summary text based on data
  const getSummary = () => {
    const performance = profitFactor && profitFactor > 1.5
      ? (isZh ? '表现优异' : 'excellent performance')
      : profitFactor && profitFactor > 1
        ? (isZh ? '表现稳健' : 'solid performance')
        : (isZh ? '需要改进' : 'needs improvement');

    if (isZh) {
      return `本周期完成 ${totalTrades} 笔交易，胜率 ${winRate.toFixed(1)}%，盈亏比 ${profitFactor?.toFixed(2) || '-'}，${performance}。`;
    }
    return `Completed ${totalTrades} trades with ${winRate.toFixed(1)}% win rate and ${profitFactor?.toFixed(2) || '-'} profit factor. ${performance.charAt(0).toUpperCase() + performance.slice(1)}.`;
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
      value: expectancy ? formatCurrency(expectancy) : '-',
    },
  ];

  return (
    <div className="relative overflow-hidden">
      {/* Background subtle pattern */}
      <div className="absolute inset-0 opacity-[0.02] dark:opacity-[0.05]">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23000000' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }} />
      </div>

      <div className="relative bg-white/80 dark:bg-neutral-900/80 backdrop-blur-sm rounded-2xl border border-neutral-200 dark:border-neutral-800 p-8 md:p-14">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-10">
          <div>
            <p className="text-[11px] font-medium tracking-[0.25em] uppercase text-neutral-400 dark:text-neutral-500">
              {isZh ? '交易报告' : 'Trading Report'}
            </p>
          </div>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 font-medium">
            {period}
          </p>
        </div>

        {/* Hero Number */}
        <div className="mb-8">
          <p className={clsx(
            'hero-number',
            totalPnL >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
          )}>
            {formatCurrency(totalPnL)}
          </p>
          <p className="text-xs font-semibold tracking-[0.15em] uppercase text-neutral-400 dark:text-neutral-500 mt-3">
            {isZh ? '净盈亏' : 'Net P&L'}
          </p>
        </div>

        {/* Summary Text */}
        <p className="text-base text-neutral-600 dark:text-neutral-400 mb-10 max-w-2xl leading-relaxed">
          "{getSummary()}"
        </p>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {metrics.map((metric, index) => (
            <div key={index} className="text-center md:text-left">
              <p className="text-2xl md:text-3xl font-semibold text-neutral-900 dark:text-neutral-100 tracking-tight">
                {metric.value}
              </p>
              <p className="text-[11px] font-medium tracking-[0.1em] uppercase text-neutral-400 dark:text-neutral-500 mt-1.5">
                {metric.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
