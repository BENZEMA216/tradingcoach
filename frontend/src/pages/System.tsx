import { useQuery } from '@tanstack/react-query';
import { systemApi } from '@/api/client';
import { formatNumber, formatDate } from '@/utils/format';
import { Database, Activity, CheckCircle } from 'lucide-react';

export function System() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['system', 'stats'],
    queryFn: () => systemApi.getStats(),
  });

  const { data: health } = useQuery({
    queryKey: ['system', 'health'],
    queryFn: () => systemApi.health(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          System Status
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Database and system information
        </p>
      </div>

      {/* Health Status */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div
            className={`p-2 rounded-full ${
              health?.status === 'healthy'
                ? 'bg-green-100 dark:bg-green-900/30'
                : 'bg-red-100 dark:bg-red-900/30'
            }`}
          >
            {health?.status === 'healthy' ? (
              <CheckCircle className="w-6 h-6 text-green-600" />
            ) : (
              <Activity className="w-6 h-6 text-red-600" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              API Status
            </h3>
            <p
              className={`text-sm ${
                health?.status === 'healthy' ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {health?.status === 'healthy' ? 'All systems operational' : 'System issues detected'}
            </p>
          </div>
        </div>
      </div>

      {/* Database Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Positions */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Database className="w-5 h-5 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Positions
            </h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Total Records</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {formatNumber(stats?.database.positions.count)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Symbols</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {stats?.database.positions.symbols}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Date Range</span>
              <span className="font-medium text-gray-900 dark:text-white text-sm">
                {formatDate(stats?.database.positions.date_range.start)} -{' '}
                {formatDate(stats?.database.positions.date_range.end)}
              </span>
            </div>
          </div>
        </div>

        {/* Trades */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <Database className="w-5 h-5 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Trades
            </h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Total Records</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {formatNumber(stats?.database.trades.count)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Date Range</span>
              <span className="font-medium text-gray-900 dark:text-white text-sm">
                {formatDate(stats?.database.trades.date_range.start)} -{' '}
                {formatDate(stats?.database.trades.date_range.end)}
              </span>
            </div>
          </div>
        </div>

        {/* Market Data */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <Database className="w-5 h-5 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Market Data
            </h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Total Records</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {formatNumber(stats?.database.market_data.count)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Symbols</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {stats?.database.market_data.symbols}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Date Range</span>
              <span className="font-medium text-gray-900 dark:text-white text-sm">
                {formatDate(stats?.database.market_data.date_range.start)} -{' '}
                {formatDate(stats?.database.market_data.date_range.end)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Last Updated */}
      <div className="text-sm text-gray-500 text-center">
        Last updated: {stats?.timestamp ? new Date(stats.timestamp).toLocaleString() : '-'}
      </div>
    </div>
  );
}
