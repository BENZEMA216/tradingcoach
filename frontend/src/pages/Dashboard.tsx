import { useQuery } from '@tanstack/react-query';
import { DollarSign, TrendingUp, Target, Clock } from 'lucide-react';
import { dashboardApi } from '@/api/client';
import { KPICard } from '@/components/dashboard/KPICard';
import { RecentTradesTable } from '@/components/dashboard/RecentTradesTable';
import { EquityCurveChart } from '@/components/charts/EquityCurveChart';
import { StrategyPieChart } from '@/components/charts/StrategyPieChart';
import { formatCurrency, formatPercent } from '@/utils/format';

export function Dashboard() {
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
          Dashboard
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Overview of your trading performance
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total P&L"
          value={kpisLoading ? '...' : formatCurrency(kpis?.total_pnl)}
          trend={kpis?.total_pnl && kpis.total_pnl > 0 ? 'up' : kpis?.total_pnl && kpis.total_pnl < 0 ? 'down' : 'neutral'}
          icon={<DollarSign className="w-6 h-6 text-blue-600" />}
        />
        <KPICard
          title="Win Rate"
          value={kpisLoading ? '...' : formatPercent(kpis?.win_rate, 1)}
          subtitle={`${kpis?.trade_count || 0} trades`}
          icon={<TrendingUp className="w-6 h-6 text-green-600" />}
        />
        <KPICard
          title="Average Score"
          value={kpisLoading ? '...' : `${kpis?.avg_score?.toFixed(1) || '-'}`}
          subtitle="Out of 100"
          icon={<Target className="w-6 h-6 text-yellow-600" />}
        />
        <KPICard
          title="Avg Holding"
          value={kpisLoading ? '...' : `${kpis?.avg_holding_days?.toFixed(1) || '-'} days`}
          subtitle={`Fees: ${formatCurrency(kpis?.total_fees)}`}
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
          />
        </div>
        <div>
          <StrategyPieChart data={strategyBreakdown || []} />
        </div>
      </div>

      {/* Recent Trades */}
      <RecentTradesTable trades={recentTrades || []} isLoading={tradesLoading} />
    </div>
  );
}
