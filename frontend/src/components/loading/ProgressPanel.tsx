/**
 * ProgressPanel - 进度面板
 *
 * input: 任务状态数据
 * output: 进度条、步骤指示器、日志流、结果展示
 * pos: 组件 - Loading页面右侧进度展示区
 */
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
  BarChart3,
  RefreshCw,
  FileText,
} from 'lucide-react';
import { TickingLogStream } from './TickingLogStream';
import type { TaskStatus } from '@/api/client';

// 进度步骤
const STEPS = [
  { key: 'import', label: '导入', labelEn: 'Import', progress: 0 },
  { key: 'match', label: '配对', labelEn: 'Match', progress: 40 },
  { key: 'data', label: '行情', labelEn: 'Data', progress: 70 },
  { key: 'score', label: '评分', labelEn: 'Score', progress: 85 },
  { key: 'done', label: '完成', labelEn: 'Done', progress: 100 },
];

interface ProgressPanelProps {
  task?: TaskStatus;
  isLoading: boolean;
  error: Error | null;
  onComplete: () => void;
  onViewPositions: () => void;
  onViewDashboard: () => void;
  onRetry: () => void;
}

export function ProgressPanel({
  task,
  isLoading,
  error,
  onComplete,
  onViewPositions,
  onViewDashboard,
  onRetry,
}: ProgressPanelProps) {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  // Call onComplete when task completes
  useEffect(() => {
    if (task?.status === 'completed') {
      onComplete();
    }
  }, [task?.status, onComplete]);

  // Get current step index
  const getCurrentStepIndex = () => {
    if (!task) return 0;
    const progress = task.progress;
    for (let i = STEPS.length - 1; i >= 0; i--) {
      if (progress >= STEPS[i].progress) {
        return i;
      }
    }
    return 0;
  };

  const currentStepIndex = getCurrentStepIndex();

  // Loading state
  if (isLoading && !task) {
    return (
      <div className="w-full max-w-xl">
        <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-8">
          <div className="flex items-center justify-center space-x-3">
            <Loader2 className="w-6 h-6 text-white/60 animate-spin" />
            <span className="text-white/60 font-mono text-sm">{t('loading.connecting', 'CONNECTING...')}</span>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || task?.status === 'failed') {
    return (
      <div className="w-full max-w-xl">
        <div className="bg-red-900/20 backdrop-blur-xl rounded-2xl border border-red-500/30 p-8">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500/20 rounded-full mb-6">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">
              {t('loading.analysisFailed', 'Analysis Failed')}
            </h2>
            <p className="text-white/50 text-sm mb-6 font-mono">
              {task?.error_message || error?.message || 'Unknown error occurred'}
            </p>
            <button
              onClick={onRetry}
              className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center justify-center space-x-2 mx-auto transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>{t('loading.tryAgain', 'Try Again')}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Completed state
  if (task?.status === 'completed') {
    return (
      <div className="w-full max-w-xl">
        <div className="bg-green-900/20 backdrop-blur-xl rounded-2xl border border-green-500/30 p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-500/20 rounded-full mb-6">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              {t('loading.analysisComplete', 'Analysis Complete')}
            </h2>
            <p className="text-white/50 text-sm font-mono">
              {task.file_name}
            </p>
          </div>

          {/* Result Stats */}
          {task.result && (
            <div className="grid grid-cols-4 gap-3 mb-8">
              <div className="bg-black/40 rounded-lg p-4 text-center border border-white/10">
                <p className="text-2xl font-bold text-green-400 font-mono">
                  {task.result.new_trades || 0}
                </p>
                <p className="text-xs text-white/40 mt-1 uppercase tracking-wider">
                  {t('loading.trades', 'Trades')}
                </p>
              </div>
              <div className="bg-black/40 rounded-lg p-4 text-center border border-white/10">
                <p className="text-2xl font-bold text-blue-400 font-mono">
                  {task.result.positions_matched || 0}
                </p>
                <p className="text-xs text-white/40 mt-1 uppercase tracking-wider">
                  {t('loading.positions', 'Positions')}
                </p>
              </div>
              <div className="bg-black/40 rounded-lg p-4 text-center border border-white/10">
                <p className="text-2xl font-bold text-orange-400 font-mono">
                  {task.result.symbols_fetched || 0}
                </p>
                <p className="text-xs text-white/40 mt-1 uppercase tracking-wider">
                  {t('loading.symbols', 'Symbols')}
                </p>
              </div>
              <div className="bg-black/40 rounded-lg p-4 text-center border border-white/10">
                <p className="text-2xl font-bold text-purple-400 font-mono">
                  {task.result.positions_scored || 0}
                </p>
                <p className="text-xs text-white/40 mt-1 uppercase tracking-wider">
                  {t('loading.scored', 'Scored')}
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex space-x-3">
            <button
              onClick={onViewPositions}
              className="flex-1 px-6 py-3 bg-white text-black rounded-lg hover:bg-gray-200 flex items-center justify-center space-x-2 font-bold transition-colors"
            >
              <FileText className="w-4 h-4" />
              <span>{t('loading.viewPositions', 'View Positions')}</span>
            </button>
            <button
              onClick={onViewDashboard}
              className="flex-1 px-6 py-3 bg-white/10 text-white rounded-lg hover:bg-white/20 flex items-center justify-center space-x-2 border border-white/20 transition-colors"
            >
              <BarChart3 className="w-4 h-4" />
              <span>{t('loading.viewDashboard', 'Dashboard')}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Processing state
  return (
    <div className="w-full max-w-xl">
      <div className="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
            <span className="text-white font-medium">
              {t('loading.analyzing', 'Analyzing...')}
            </span>
          </div>
          {task?.file_name && (
            <span className="text-xs font-mono text-white/40 truncate max-w-[200px]">
              {task.file_name}
            </span>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 bg-[length:200%_100%] animate-gradient-x rounded-full transition-all duration-500"
              style={{ width: `${task?.progress || 0}%` }}
            />
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-xs font-mono text-white/40">
              {task?.current_step || 'Initializing...'}
            </span>
            <span className="text-lg font-bold text-white font-mono">
              {(task?.progress || 0).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Step Indicators */}
        <div className="flex justify-between mb-8 px-2">
          {STEPS.map((step, index) => {
            const isCompleted = index < currentStepIndex || (index === currentStepIndex && task?.status === 'completed');
            const isCurrent = index === currentStepIndex && task?.status !== 'completed';

            return (
              <div key={step.key} className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 transition-all duration-300 ${
                    isCompleted
                      ? 'bg-green-500 text-white scale-100'
                      : isCurrent
                      ? 'bg-blue-500 text-white scale-110 animate-pulse'
                      : 'bg-white/10 text-white/30'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <span className="text-xs font-mono">{index + 1}</span>
                  )}
                </div>
                <span
                  className={`text-xs font-mono uppercase tracking-wider ${
                    isCompleted || isCurrent ? 'text-white' : 'text-white/30'
                  }`}
                >
                  {isZh ? step.label : step.labelEn}
                </span>
              </div>
            );
          })}
        </div>

        {/* Log Stream */}
        {task?.logs && (
          <TickingLogStream logs={task.logs} maxVisible={10} />
        )}
      </div>
    </div>
  );
}
