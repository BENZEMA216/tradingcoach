import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { DollarSign, TrendingUp, Target, Clock } from 'lucide-react';
import { dashboardApi } from '@/api/client';
import { KPICard } from '@/components/dashboard/KPICard';
import { RecentTradesTable } from '@/components/dashboard/RecentTradesTable';
import { EquityCurveChart } from '@/components/charts/EquityCurveChart';
import { StrategyPieChart } from '@/components/charts/StrategyPieChart';
import { formatCurrency, formatPercent } from '@/utils/format';
import { InfoTooltip, DrillDownModal } from '@/components/common';
import type { PositionFilters } from '@/types';

// Drill-down filter state type
interface DrillDownState {
  isOpen: boolean;
  title: string;
  subtitle?: string;
  filters: PositionFilters;
}

export function Dashboard() {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  // Drill-down modal state
  const [drillDown, setDrillDown] = useState<DrillDownState>({
    isOpen: false,
    title: '',
    filters: {},
  });

  // Handle strategy drill-down
  const handleStrategyDrillDown = (strategyType: string, strategyName: string) => {
    setDrillDown({
      isOpen: true,
      title: isZh ? `${strategyName} 策略交易` : `${strategyName} Trades`,
      filters: { strategy_type: strategyType },
    });
  };

  // Close drill-down modal
  const closeDrillDown = () => {
    setDrillDown({ isOpen: false, title: '', filters: {} });
  };

  // Fetch KPIs
  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: ['dashboard', 'kpis'],
    queryFn: () => dashboardApi.getKPIs(),
  });

  // Fetch equity curve
  const { data: equityCurve } = useQuery({
    queryKey: ['dashboard', 'equity-curve'],
    queryFn: () => dashboardApi.getEquityCurve(),
  });

  // Fetch recent trades
  const { data: recentTrades, isLoading: tradesLoading } = useQuery({
    queryKey: ['dashboard', 'recent-trades'],
    queryFn: () => dashboardApi.getRecentTrades(10),
  });

  // Fetch strategy breakdown
  const { data: strategyBreakdown } = useQuery({
    queryKey: ['dashboard', 'strategy-breakdown'],
    queryFn: () => dashboardApi.getStrategyBreakdown(),
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('dashboard.title')}
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          {t('dashboard.subtitle')}
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title={
            <span className="flex items-center">
              {t('dashboard.totalPnl')}
              <InfoTooltip termKey="pnl" />
            </span>
          }
          value={kpisLoading ? '...' : formatCurrency(kpis?.total_pnl)}
          trend={kpis?.total_pnl && kpis.total_pnl > 0 ? 'up' : kpis?.total_pnl && kpis.total_pnl < 0 ? 'down' : 'neutral'}
          icon={<DollarSign className="w-6 h-6 text-blue-600" />}
        />
        <KPICard
          title={
            <span className="flex items-center">
              {t('dashboard.winRate')}
              <InfoTooltip termKey="winRate" />
            </span>
          }
          value={kpisLoading ? '...' : formatPercent(kpis?.win_rate, 1)}
          subtitle={`${kpis?.trade_count || 0} ${isZh ? '笔交易' : 'trades'}`}
          icon={<TrendingUp className="w-6 h-6 text-green-600" />}
        />
        <KPICard
          title={t('dashboard.avgScore')}
          value={kpisLoading ? '...' : `${kpis?.avg_score?.toFixed(1) || '-'}`}
          subtitle={isZh ? '满分100' : 'Out of 100'}
          icon={<Target className="w-6 h-6 text-yellow-600" />}
        />
        <KPICard
          title={
            <span className="flex items-center">
              {t('dashboard.avgHoldingDays')}
              <InfoTooltip termKey="holdingPeriod" />
            </span>
          }
          value={kpisLoading ? '...' : `${kpis?.avg_holding_days?.toFixed(1) || '-'} ${isZh ? '天' : 'days'}`}
          subtitle={`${isZh ? '费用' : 'Fees'}: ${formatCurrency(kpis?.total_fees)}`}
          icon={<Clock className="w-6 h-6 text-purple-600" />}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <EquityCurveChart
            data={equityCurve?.data || []}
            totalPnL={equityCurve?.total_pnl || 0}
            maxDrawdown={equityCurve?.max_drawdown}
            title={t('dashboard.equityCurve')}
          />
        </div>
        <div>
          <StrategyPieChart
            data={strategyBreakdown || []}
            title={t('dashboard.strategyBreakdown')}
            onDrillDown={handleStrategyDrillDown}
          />
        </div>
      </div>

      {/* Recent Trades */}
      <RecentTradesTable trades={recentTrades || []} isLoading={tradesLoading} title={t('dashboard.recentTrades')} />

      {/* Drill-Down Modal */}
      <DrillDownModal
        isOpen={drillDown.isOpen}
        onClose={closeDrillDown}
        title={drillDown.title}
        subtitle={drillDown.subtitle}
        filters={drillDown.filters}
      />
    </div>
  );
}
