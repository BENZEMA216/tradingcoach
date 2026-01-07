import { useState, useMemo } from 'react';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChevronUp, ChevronDown, Filter, X, Search } from 'lucide-react';
import { positionsApi } from '@/api/client';
import { formatCurrency, formatPercent, formatDate, getPnLColorClass, getGradeBadgeClass, formatHoldingDays } from '@/utils/format';
import clsx from 'clsx';
import type { PositionSummary } from '@/types';

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
  // Initialize from URL params if present
  const [filters, setFilters] = useState<Filters>(() => {
    const params = new URLSearchParams(window.location.search);
    return {
      ...defaultFilters,
      date_start: params.get('date_start') || '',
      date_end: params.get('date_end') || '',
    };
  });
  const [showFilters, setShowFilters] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return !!(params.get('date_start') || params.get('date_end'));
  });

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

  // Fetch summary stats based on SAME filters
  const { data: summaryData } = useQuery<PositionSummary>({
    queryKey: ['positions', 'summary', queryParams],
    queryFn: () => positionsApi.getSummary(queryParams),
    placeholderData: keepPreviousData,
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
        'px-4 py-3 text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-widest cursor-pointer hover:bg-neutral-50 dark:hover:bg-white/5 transition-colors select-none',
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
    <div className="space-y-6 pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-mono font-bold text-white tracking-tight uppercase">
            {t('positions.title')}
          </h1>
          <p className="text-xs font-mono text-white/50 mt-1">
            // TRACKING_ID: {data?.total || 0} // {isZh ? '持仓记录' : 'POSITIONS_FOUND'}
          </p>
        </div>

        {/* Dynamic Summary Stats - Industrial */}
        {summaryData && (
          <div className="hidden lg:flex items-center gap-8 px-6 py-3 bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 transition-colors">
            <div className="flex flex-col">
              <span className="text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-[0.2em]">{t('positions.pnl')}</span>
              <span className={clsx("text-xl font-mono font-medium tracking-tight", summaryData.total_pnl >= 0 ? "text-green-600 dark:text-green-500" : "text-red-600 dark:text-red-500")}>
                {formatCurrency(summaryData.total_pnl)}
              </span>
            </div>
            <div className="w-px h-8 bg-neutral-200 dark:bg-white/10" />
            <div className="flex flex-col">
              <span className="text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-[0.2em]">{isZh ? '胜率' : 'WIN_RATE'}</span>
              <span className="text-xl font-mono font-medium tracking-tight text-slate-900 dark:text-white">
                {formatPercent(summaryData.win_rate)}
              </span>
            </div>
            <div className="w-px h-8 bg-neutral-200 dark:bg-white/10" />
            <div className="flex flex-col">
              <span className="text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-[0.2em]">{isZh ? '盈亏比' : 'PROFIT_FACTOR'}</span>
              <span className="text-xl font-mono font-medium tracking-tight text-slate-900 dark:text-white">
                {summaryData.profit_factor?.toFixed(2) || '-'}
              </span>
            </div>
          </div>
        )}

        {/* Filter Toggle Button */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-sm border transition-all font-mono text-xs uppercase tracking-wide',
            showFilters || hasActiveFilters
              ? 'bg-neutral-900 text-white border-neutral-900 dark:bg-white dark:text-black dark:border-white'
              : 'bg-white dark:bg-black text-slate-900 dark:text-white border-neutral-200 dark:border-white/20 hover:border-neutral-300 dark:hover:border-white/50'
          )}
        >
          <Filter className="w-3 h-3" />
          {isZh ? '筛选' : 'FILTER'}
          {hasActiveFilters && (
            <span className="px-1.5 py-0.5 text-[9px] bg-red-500 text-white rounded-sm">
              {Object.values(filters).filter(v => v !== '').length}
            </span>
          )}
        </button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 p-6 animate-in slide-in-from-top-2 duration-200 transition-colors">
          <div className="flex items-center justify-between mb-6 border-b border-neutral-200 dark:border-white/10 pb-4">
            <h3 className="text-xs font-mono font-bold text-slate-900 dark:text-white uppercase tracking-[0.2em]">
              {isZh ? '筛选条件' : 'SEARCH_PARAMETERS'}
            </h3>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="text-xs font-mono text-slate-500 dark:text-white/50 hover:text-slate-900 dark:hover:text-white flex items-center gap-2 uppercase tracking-wide transition-colors"
              >
                <X className="w-3 h-3" />
                {isZh ? '清除全部' : 'RESET_ALL'}
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Symbol Search */}
            <div>
              <label className="block text-[10px] font-mono text-slate-400 dark:text-white/40 uppercase tracking-widest mb-2">
                {isZh ? '股票代码' : 'SYMBOL'}
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-white/30" />
                <input
                  type="text"
                  value={filters.symbol}
                  onChange={(e) => handleFilterChange('symbol', e.target.value)}
                  placeholder={isZh ? '搜索代码...' : 'ENTER_SYMBOL...'}
                  className="w-full pl-10 pr-4 py-2 border border-neutral-200 dark:border-white/10 rounded-sm bg-neutral-50 dark:bg-black text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-white/20 focus:outline-none focus:border-neutral-400 dark:focus:border-white/40 font-mono text-sm uppercase transition-colors"
                />
              </div>
            </div>

            {/* Direction Filter */}
            <div>
              <label className="block text-[10px] font-mono text-slate-400 dark:text-white/40 uppercase tracking-widest mb-2">
                {isZh ? '方向' : 'DIRECTION'}
              </label>
              <select
                value={filters.direction}
                onChange={(e) => handleFilterChange('direction', e.target.value)}
                className="w-full px-4 py-2 border border-neutral-200 dark:border-white/10 rounded-sm bg-neutral-50 dark:bg-black text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:border-neutral-400 dark:focus:border-white/40 appearance-none transition-colors"
              >
                <option value="">{isZh ? '全部' : 'ALL_DIRECTIONS'}</option>
                <option value="long">{isZh ? '做多' : 'LONG'}</option>
                <option value="short">{isZh ? '做空' : 'SHORT'}</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-[10px] font-mono text-slate-400 dark:text-white/40 uppercase tracking-widest mb-2">
                {isZh ? '状态' : 'STATUS'}
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-4 py-2 border border-neutral-200 dark:border-white/10 rounded-sm bg-neutral-50 dark:bg-black text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:border-neutral-400 dark:focus:border-white/40 appearance-none transition-colors"
              >
                <option value="">{isZh ? '全部' : 'ALL_STATUS'}</option>
                <option value="CLOSED">{isZh ? '已平仓' : 'CLOSED'}</option>
                <option value="OPEN">{isZh ? '持仓中' : 'OPEN'}</option>
              </select>
            </div>

            {/* Winner/Loser Filter */}
            <div>
              <label className="block text-[10px] font-mono text-slate-400 dark:text-white/40 uppercase tracking-widest mb-2">
                {isZh ? '盈亏' : 'RESULT'}
              </label>
              <select
                value={filters.is_winner}
                onChange={(e) => handleFilterChange('is_winner', e.target.value)}
                className="w-full px-4 py-2 border border-neutral-200 dark:border-white/10 rounded-sm bg-neutral-50 dark:bg-black text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:border-neutral-400 dark:focus:border-white/40 appearance-none transition-colors"
              >
                <option value="">{isZh ? '全部' : 'ALL_RESULTS'}</option>
                <option value="true">{isZh ? '盈利' : 'WINNERS'}</option>
                <option value="false">{isZh ? '亏损' : 'LOSERS'}</option>
              </select>
            </div>

            {/* Grade Filter */}
            <div>
              <label className="block text-[10px] font-mono text-slate-400 dark:text-white/40 uppercase tracking-widest mb-2">
                {isZh ? '评分等级' : 'GRADE'}
              </label>
              <select
                value={filters.score_grade}
                onChange={(e) => handleFilterChange('score_grade', e.target.value)}
                className="w-full px-4 py-2 border border-neutral-200 dark:border-white/10 rounded-sm bg-neutral-50 dark:bg-black text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:border-neutral-400 dark:focus:border-white/40 appearance-none transition-colors"
              >
                <option value="">{isZh ? '全部' : 'ALL_GRADES'}</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
                <option value="F">F</option>
              </select>
            </div>

            {/* Date Start */}
            <div>
              <label className="block text-[10px] font-mono text-slate-400 dark:text-white/40 uppercase tracking-widest mb-2">
                {isZh ? '开始日期' : 'START_DATE'}
              </label>
              <input
                type="date"
                value={filters.date_start}
                onChange={(e) => handleFilterChange('date_start', e.target.value)}
                className="w-full px-4 py-2 border border-neutral-200 dark:border-white/10 rounded-sm bg-neutral-50 dark:bg-black text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:border-neutral-400 dark:focus:border-white/40 transition-colors"
              />
            </div>

            {/* Date End */}
            <div>
              <label className="block text-[10px] font-mono text-slate-400 dark:text-white/40 uppercase tracking-widest mb-2">
                {isZh ? '结束日期' : 'END_DATE'}
              </label>
              <input
                type="date"
                value={filters.date_end}
                onChange={(e) => handleFilterChange('date_end', e.target.value)}
                className="w-full px-4 py-2 border border-neutral-200 dark:border-white/10 rounded-sm bg-neutral-50 dark:bg-black text-slate-900 dark:text-white font-mono text-sm focus:outline-none focus:border-neutral-400 dark:focus:border-white/40 transition-colors"
              />
            </div>
          </div>
        </div>
      )}

      {/* Positions Table */}
      <div className="bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 overflow-hidden transition-colors">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-neutral-50 dark:bg-black border-b border-neutral-200 dark:border-white/10">
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
                  {isZh ? '数量' : 'SIZE'}
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
                <th className="px-4 py-3 text-left w-24"></th> {/* Visual Bar */}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={10} className="px-4 py-4">
                      <div className="h-4 bg-neutral-100 dark:bg-white/5 rounded animate-pulse"></div>
                    </td>
                  </tr>
                ))
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center text-slate-400 dark:text-white/40 font-mono">
                    // {isZh ? '没有找到匹配的记录' : 'NO_DATA_FOUND'}
                  </td>
                </tr>
              ) : (
                data?.items.map((position) => (
                  <tr
                    key={position.id}
                    onClick={() => navigate(`/positions/${position.id}`)}
                    className="hover:bg-neutral-50 dark:hover:bg-white/5 transition-colors cursor-pointer group"
                  >
                    <td className="px-4 py-3">
                      <div>
                        <span className="font-mono font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                          {position.symbol}
                        </span>
                        {position.symbol_name && (
                          <span className="block text-[10px] text-white/30 truncate max-w-[120px]">
                            {position.symbol_name}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={clsx(
                          'px-1 py-0.5 text-[10px] font-bold rounded-sm uppercase tracking-wider',
                          position.direction === 'long'
                            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20'
                            : 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-500/20'
                        )}
                      >
                        {position.direction === 'long' ? 'LONG' : 'SHORT'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-slate-500 dark:text-white/50">
                      {formatDate(position.open_date)}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-slate-500 dark:text-white/50">
                      {formatDate(position.close_date)}
                    </td>
                    <td className="px-4 py-3 text-sm font-mono text-right text-slate-700 dark:text-white/80">
                      {position.quantity}
                    </td>
                    <td
                      className={clsx(
                        'px-4 py-3 text-sm font-mono font-bold text-right tracking-tight',
                        (position.net_pnl || 0) >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
                      )}
                    >
                      {formatCurrency(position.net_pnl)}
                    </td>
                    <td
                      className={clsx(
                        'px-4 py-3 text-sm font-mono font-bold text-right tracking-tight',
                        (position.net_pnl_pct || 0) >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
                      )}
                    >
                      {formatPercent(position.net_pnl_pct)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={clsx(
                          'px-2 py-0.5 text-[10px] font-bold rounded-sm border',
                          position.score_grade === 'A' || position.score_grade === 'A+' ? 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-200 dark:border-green-500/30' :
                            position.score_grade === 'B' ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-500/30' :
                              position.score_grade === 'C' ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400 border-yellow-200 dark:border-yellow-500/30' :
                                'bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-200 dark:border-red-500/30'
                        )}
                      >
                        {position.score_grade || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-right text-slate-500 dark:text-white/50">
                      {position.holding_period_days}D
                    </td>
                    <td className="px-4 py-3 align-middle">
                      {/* Visual PnL Bar - Industrial */}
                      <div className="flex items-center justify-start h-full w-24 opacity-30 group-hover:opacity-100 transition-opacity">
                        <div
                          className={clsx(
                            "h-1",
                            position.net_pnl && position.net_pnl > 0 ? "bg-green-500" : "bg-red-500"
                          )}
                          style={{
                            width: `${Math.min(Math.abs(position.net_pnl_pct || 0) * 10, 100)}%`,
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination - Industrial */}
        {data && (
          <div className="px-6 py-4 border-t border-neutral-200 dark:border-white/10 flex items-center justify-between bg-neutral-50 dark:bg-black transition-colors">
            <p className="text-xs font-mono text-slate-500 dark:text-white/40 uppercase tracking-wide">
              {isZh
                ? `显示 ${(page - 1) * pageSize + 1} - ${Math.min(page * pageSize, data.total)} / ${data.total}`
                : `SHOWING ${(page - 1) * pageSize + 1} - ${Math.min(page * pageSize, data.total)} OF ${data.total}`}
            </p>
            <div className="flex space-x-px">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 text-xs font-mono bg-white dark:bg-black text-slate-600 dark:text-white/70 border border-neutral-200 dark:border-white/10 hover:bg-neutral-100 dark:hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-transparent transition-colors uppercase tracking-wider"
              >
                {isZh ? '上一页' : 'PREV'}
              </button>
              <div className="px-4 py-2 text-xs font-mono bg-neutral-100 dark:bg-white/5 text-slate-900 dark:text-white border-y border-neutral-200 dark:border-white/10 flex items-center">
                {page} / {data.total_pages || 1}
              </div>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.total_pages}
                className="px-4 py-2 text-xs font-mono bg-white dark:bg-black text-slate-600 dark:text-white/70 border border-neutral-200 dark:border-white/10 hover:bg-neutral-100 dark:hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-transparent transition-colors uppercase tracking-wider"
              >
                {isZh ? '下一页' : 'NEXT'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
