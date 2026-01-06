import { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { X, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { positionsApi } from '@/api/client';
import { formatCurrency, formatPercent, formatDate, getPnLColorClass, getGradeBadgeClass } from '@/utils/format';
import type { PositionFilters } from '@/types';
import clsx from 'clsx';

interface DrillDownModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  filters: PositionFilters;
}

export function DrillDownModal({ isOpen, onClose, title, subtitle, filters }: DrillDownModalProps) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const isZh = i18n.language === 'zh';

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [filters]);

  // Fetch positions with filters
  const { data, isLoading } = useQuery({
    queryKey: ['drilldown-positions', filters, page, pageSize],
    queryFn: () => positionsApi.list(page, pageSize, filters),
    enabled: isOpen,
  });

  // Handle ESC key
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = '';
      };
    }
  }, [isOpen, onClose]);

  // Handle row click - navigate to position detail
  const handleRowClick = useCallback((positionId: number) => {
    onClose();
    navigate(`/positions/${positionId}`);
  }, [navigate, onClose]);

  // Handle "View All" click - navigate to positions with filters
  const handleViewAll = useCallback(() => {
    const params = new URLSearchParams();
    if (filters.symbol) params.set('symbol', filters.symbol);
    if (filters.score_grade) params.set('grade', filters.score_grade);
    if (filters.strategy_type) params.set('strategy', filters.strategy_type);
    if (filters.date_start) params.set('from', filters.date_start);
    if (filters.date_end) params.set('to', filters.date_end);

    onClose();
    navigate(`/positions${params.toString() ? `?${params.toString()}` : ''}`);
  }, [navigate, onClose, filters]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col
                     animate-in fade-in zoom-in-95 duration-200"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                {title}
              </h2>
              {subtitle && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  {subtitle}
                </p>
              )}
              {data && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  {isZh ? `共 ${data.total} 笔交易` : `${data.total} trades total`}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300
                       hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : !data?.items.length ? (
              <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                <p>{isZh ? '暂无匹配的交易记录' : 'No matching trades'}</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900/50 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {t('positions.symbol')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {t('positions.direction')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {t('positions.openDate')}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      {t('positions.closeDate')}
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      {t('positions.pnl')}
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      {t('positions.pnlPct')}
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      {t('positions.grade')}
                    </th>
                    <th className="px-4 py-3 w-8"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                  {data.items.map((position) => (
                    <tr
                      key={position.id}
                      onClick={() => handleRowClick(position.id)}
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
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                        {formatDate(position.open_date)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                        {formatDate(position.close_date)}
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
                      <td className="px-4 py-3 text-gray-400">
                        <ChevronRight className="w-4 h-4" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Footer */}
          {data && data.total > 0 && (
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              {/* Pagination */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300
                           hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg
                           disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {page} / {data.total_pages}
                </span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= data.total_pages}
                  className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300
                           hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg
                           disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>

              {/* View All Link */}
              <button
                onClick={handleViewAll}
                className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700
                         dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
              >
                {isZh ? '在持仓列表中查看全部' : 'View All in Positions'}
                <ExternalLink className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
