import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChevronUp, ChevronDown, Filter, X, Search } from 'lucide-react';
import { positionsApi } from '@/api/client';
import { formatCurrency, formatPercent, formatDate, getPnLColorClass, getGradeBadgeClass, formatHoldingDays } from '@/utils/format';
import clsx from 'clsx';

type SortField = 'symbol' | 'direction' | 'open_date' | 'close_date' | 'quantity' | 'net_pnl' | 'net_pnl_pct' | 'score_grade' | 'holding_period_days';
type SortOrder = 'asc' | 'desc';

interface Filters {
  symbol: string;
  direction: string;
  status: string;
  date_start: string;
  date_end: string;
  is_winner: string;
  score_grade: string;
}

const defaultFilters: Filters = {
  symbol: '',
  direction: '',
  status: '',
  date_start: '',
  date_end: '',
  is_winner: '',
  score_grade: '',
};

export function Positions() {
  const { t, i18n } = useTranslation();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const navigate = useNavigate();

  const isZh = i18n.language === 'zh';

  // Sorting state
  const [sortBy, setSortBy] = useState<SortField>('close_date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Filter state
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [showFilters, setShowFilters] = useState(false);

  // Build query params
  const queryParams = useMemo(() => {
    const params: Record<string, any> = {
      sort_by: sortBy,
      sort_order: sortOrder,
    };

    if (filters.symbol) params.symbol = filters.symbol;
    if (filters.direction) params.direction = filters.direction;
    if (filters.status) params.status = filters.status;
    if (filters.date_start) params.date_start = filters.date_start;
    if (filters.date_end) params.date_end = filters.date_end;
    if (filters.is_winner) params.is_winner = filters.is_winner === 'true';
    if (filters.score_grade) params.score_grade = filters.score_grade;

    return params;
  }, [sortBy, sortOrder, filters]);

  const { data, isLoading } = useQuery({
    queryKey: ['positions', page, pageSize, queryParams],
    queryFn: () => positionsApi.list(page, pageSize, queryParams),
  });

  // Handle sort
  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
    setPage(1);
  };

  // Handle filter change
  const handleFilterChange = (key: keyof Filters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1);
  };

  // Clear all filters
  const clearFilters = () => {
    setFilters(defaultFilters);
    setPage(1);
  };

  // Check if any filter is active
  const hasActiveFilters = Object.values(filters).some(v => v !== '');

  // Sort indicator component
  const SortIndicator = ({ field }: { field: SortField }) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? (
      <ChevronUp className="w-4 h-4 inline-block ml-1" />
    ) : (
      <ChevronDown className="w-4 h-4 inline-block ml-1" />
    );
  };

  // Sortable header component
  const SortableHeader = ({ field, children, align = 'left' }: { field: SortField; children: React.ReactNode; align?: 'left' | 'right' | 'center' }) => (
    <th
      className={clsx(
        'px-4 py-3 text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors select-none',
        align === 'left' && 'text-left',
        align === 'right' && 'text-right',
        align === 'center' && 'text-center'
      )}
      onClick={() => handleSort(field)}
    >
      {children}
      <SortIndicator field={field} />
    </th>
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('positions.title')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            {data?.total || 0} {isZh ? '条持仓记录' : 'total positions'}
          </p>
        </div>

        {/* Filter Toggle Button */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors',
            showFilters || hasActiveFilters
              ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-300'
              : 'bg-white border-gray-200 text-gray-700 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'
          )}
        >
          <Filter className="w-4 h-4" />
          {isZh ? '筛选' : 'Filter'}
          {hasActiveFilters && (
            <span className="px-1.5 py-0.5 text-xs bg-blue-500 text-white rounded-full">
              {Object.values(filters).filter(v => v !== '').length}
            </span>
          )}
        </button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-gray-900 dark:text-white">
              {isZh ? '筛选条件' : 'Filters'}
            </h3>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1"
              >
                <X className="w-4 h-4" />
                {isZh ? '清除全部' : 'Clear all'}
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Symbol Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {isZh ? '股票代码' : 'Symbol'}
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={filters.symbol}
                  onChange={(e) => handleFilterChange('symbol', e.target.value)}
                  placeholder={isZh ? '搜索代码...' : 'Search symbol...'}
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400"
                />
              </div>
            </div>

            {/* Direction Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {isZh ? '方向' : 'Direction'}
              </label>
              <select
                value={filters.direction}
                onChange={(e) => handleFilterChange('direction', e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">{isZh ? '全部' : 'All'}</option>
                <option value="long">{isZh ? '做多' : 'Long'}</option>
                <option value="short">{isZh ? '做空' : 'Short'}</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {isZh ? '状态' : 'Status'}
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">{isZh ? '全部' : 'All'}</option>
                <option value="CLOSED">{isZh ? '已平仓' : 'Closed'}</option>
                <option value="OPEN">{isZh ? '持仓中' : 'Open'}</option>
              </select>
            </div>

            {/* Winner/Loser Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {isZh ? '盈亏' : 'Result'}
              </label>
              <select
                value={filters.is_winner}
                onChange={(e) => handleFilterChange('is_winner', e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">{isZh ? '全部' : 'All'}</option>
                <option value="true">{isZh ? '盈利' : 'Winners'}</option>
                <option value="false">{isZh ? '亏损' : 'Losers'}</option>
              </select>
            </div>

            {/* Grade Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {isZh ? '评分等级' : 'Grade'}
              </label>
              <select
                value={filters.score_grade}
                onChange={(e) => handleFilterChange('score_grade', e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">{isZh ? '全部' : 'All'}</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
                <option value="F">F</option>
              </select>
            </div>

            {/* Date Start */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {isZh ? '开始日期' : 'Start Date'}
              </label>
              <input
                type="date"
                value={filters.date_start}
                onChange={(e) => handleFilterChange('date_start', e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            {/* Date End */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {isZh ? '结束日期' : 'End Date'}
              </label>
              <input
                type="date"
                value={filters.date_end}
                onChange={(e) => handleFilterChange('date_end', e.target.value)}
                className="w-full px-4 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          </div>
        </div>
      )}

      {/* Positions Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <SortableHeader field="symbol">
                  {t('positions.symbol')}
                </SortableHeader>
                <SortableHeader field="direction">
                  {t('positions.direction')}
                </SortableHeader>
                <SortableHeader field="open_date">
                  {t('positions.openDate')}
                </SortableHeader>
                <SortableHeader field="close_date">
                  {t('positions.closeDate')}
                </SortableHeader>
                <SortableHeader field="quantity" align="right">
                  {isZh ? '数量' : 'Quantity'}
                </SortableHeader>
                <SortableHeader field="net_pnl" align="right">
                  {t('positions.pnl')}
                </SortableHeader>
                <SortableHeader field="net_pnl_pct" align="right">
                  {t('positions.pnlPct')}
                </SortableHeader>
                <SortableHeader field="score_grade" align="center">
                  {t('positions.grade')}
                </SortableHeader>
                <SortableHeader field="holding_period_days" align="right">
                  {t('positions.holdingDays')}
                </SortableHeader>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {isLoading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={9} className="px-4 py-4">
                      <div className="h-4 bg-gray-100 dark:bg-gray-700 rounded animate-pulse"></div>
                    </td>
                  </tr>
                ))
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-gray-500">
                    {isZh ? '没有找到匹配的记录' : 'No positions found'}
                  </td>
                </tr>
              ) : (
                data?.items.map((position) => (
                  <tr
                    key={position.id}
                    onClick={() => navigate(`/positions/${position.id}`)}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-3">
                      <div>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {position.symbol}
                        </span>
                        {position.symbol_name && (
                          <span className="block text-xs text-gray-500">
                            {position.symbol_name}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={clsx(
                          'px-2 py-1 text-xs rounded',
                          position.direction === 'long'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        )}
                      >
                        {t(`direction.${position.direction}`)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDate(position.open_date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDate(position.close_date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900 dark:text-white">
                      {position.quantity}
                    </td>
                    <td
                      className={clsx(
                        'px-4 py-3 text-sm text-right font-medium',
                        getPnLColorClass(position.net_pnl)
                      )}
                    >
                      {formatCurrency(position.net_pnl)}
                    </td>
                    <td
                      className={clsx(
                        'px-4 py-3 text-sm text-right font-medium',
                        getPnLColorClass(position.net_pnl_pct)
                      )}
                    >
                      {formatPercent(position.net_pnl_pct)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={clsx(
                          'px-2 py-1 text-xs font-medium rounded',
                          getGradeBadgeClass(position.score_grade)
                        )}
                      >
                        {position.score_grade || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-500">
                      {formatHoldingDays(position.holding_period_days, isZh)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && (
          <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {isZh
                ? `显示 ${(page - 1) * pageSize + 1} 到 ${Math.min(page * pageSize, data.total)} 条，共 ${data.total} 条`
                : `Showing ${(page - 1) * pageSize + 1} to ${Math.min(page * pageSize, data.total)} of ${data.total}`}
            </p>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                {isZh ? '上一页' : 'Previous'}
              </button>
              <span className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400">
                {page} / {data.total_pages || 1}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.total_pages}
                className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                {isZh ? '下一页' : 'Next'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
