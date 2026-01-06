/**
 * ResultSummary - 分析结果摘要组件
 *
 * input: result (分析结果), onViewStatistics, onViewPositions, onUploadAnother
 * output: 统计卡片 + 操作按钮
 * pos: ProcessingLogPanel 子组件，任务完成时显示
 */

import { useTranslation } from 'react-i18next';
import { FileText, Layers, Star, BarChart3, List, UploadCloud, CheckCircle, XCircle } from 'lucide-react';
import clsx from 'clsx';

interface TaskResult {
  total_rows?: number;
  new_trades?: number;
  positions_matched?: number;
  positions_scored?: number;
  duplicates_skipped?: number;
  errors?: number;
  broker_name?: string;
}

interface ResultSummaryProps {
  result: TaskResult;
  status: 'completed' | 'failed';
  error?: string;
  onViewStatistics: () => void;
  onViewPositions: () => void;
  onUploadAnother: () => void;
}

interface StatCardProps {
  icon: React.ReactNode;
  value: number | string;
  label: string;
  highlight?: boolean;
}

function StatCard({ icon, value, label, highlight }: StatCardProps) {
  return (
    <div
      className={clsx(
        'flex flex-col items-center justify-center p-4 rounded-xl',
        'bg-white dark:bg-neutral-800 shadow-sm',
        highlight && 'ring-2 ring-green-500/50'
      )}
    >
      <div className="text-neutral-400 dark:text-neutral-500 mb-2">{icon}</div>
      <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">{value}</div>
      <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">{label}</div>
    </div>
  );
}

export function ResultSummary({
  result,
  status,
  error,
  onViewStatistics,
  onViewPositions,
  onUploadAnother,
}: ResultSummaryProps) {
  const { t } = useTranslation();

  if (status === 'failed') {
    return (
      <div className="space-y-6">
        {/* 失败状态 */}
        <div className="flex flex-col items-center justify-center py-8">
          <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            {t('processingLog.analysisFailed', '分析失败')}
          </h3>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 text-center max-w-md">
            {error || t('processingLog.unknownError', '未知错误')}
          </p>
        </div>

        {/* 重试按钮 */}
        <div className="flex justify-center">
          <button
            onClick={onUploadAnother}
            className={clsx(
              'flex items-center gap-2 px-6 py-3 rounded-xl',
              'bg-blue-600 text-white hover:bg-blue-700',
              'transition-colors font-medium'
            )}
          >
            <UploadCloud className="w-5 h-5" />
            {t('processingLog.tryAgain', '重新上传')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 成功状态 */}
      <div className="flex flex-col items-center justify-center py-4">
        <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4">
          <CheckCircle className="w-8 h-8 text-green-500" />
        </div>
        <h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
          {t('processingLog.analysisComplete', '分析完成！')}
        </h3>
        {result.broker_name && (
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {result.broker_name}
          </p>
        )}
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={<FileText className="w-5 h-5" />}
          value={result.total_rows ?? 0}
          label={t('processingLog.stats.totalRows', '总行数')}
        />
        <StatCard
          icon={<Layers className="w-5 h-5" />}
          value={result.new_trades ?? 0}
          label={t('processingLog.stats.newTrades', '新增交易')}
          highlight
        />
        <StatCard
          icon={<BarChart3 className="w-5 h-5" />}
          value={result.positions_matched ?? 0}
          label={t('processingLog.stats.positions', '持仓数')}
        />
        <StatCard
          icon={<Star className="w-5 h-5" />}
          value={result.positions_scored ?? 0}
          label={t('processingLog.stats.scored', '已评分')}
        />
      </div>

      {/* 额外信息 */}
      {((result.duplicates_skipped ?? 0) > 0 || (result.errors ?? 0) > 0) && (
        <div className="flex justify-center gap-4 text-sm text-neutral-500 dark:text-neutral-400">
          {(result.duplicates_skipped ?? 0) > 0 && (
            <span>
              {t('processingLog.stats.skipped', '跳过重复')}: {result.duplicates_skipped}
            </span>
          )}
          {(result.errors ?? 0) > 0 && (
            <span className="text-amber-500">
              {t('processingLog.stats.errors', '错误')}: {result.errors}
            </span>
          )}
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex flex-wrap justify-center gap-3 pt-2">
        <button
          onClick={onViewStatistics}
          className={clsx(
            'flex items-center gap-2 px-6 py-3 rounded-xl',
            'bg-blue-600 text-white hover:bg-blue-700',
            'transition-colors font-medium'
          )}
        >
          <BarChart3 className="w-5 h-5" />
          {t('processingLog.viewStatistics', '查看统计')}
        </button>
        <button
          onClick={onViewPositions}
          className={clsx(
            'flex items-center gap-2 px-6 py-3 rounded-xl',
            'bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-200',
            'border border-neutral-200 dark:border-neutral-700',
            'hover:bg-neutral-50 dark:hover:bg-neutral-700',
            'transition-colors font-medium'
          )}
        >
          <List className="w-5 h-5" />
          {t('processingLog.viewPositions', '查看持仓')}
        </button>
        <button
          onClick={onUploadAnother}
          className={clsx(
            'flex items-center gap-2 px-6 py-3 rounded-xl',
            'text-neutral-500 dark:text-neutral-400',
            'hover:bg-neutral-100 dark:hover:bg-neutral-800',
            'transition-colors font-medium'
          )}
        >
          <UploadCloud className="w-5 h-5" />
          {t('processingLog.uploadAnother', '上传另一个文件')}
        </button>
      </div>
    </div>
  );
}

export default ResultSummary;
