/**
 * ProcessingLogPanel - 实时处理日志面板
 *
 * input: taskId, fileName, callbacks
 * output: 完整的处理进度面板（进度条 + 日志流 + 结果摘要）
 * pos: LandingUpload 页面的核心子组件
 *
 * 一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { X, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import clsx from 'clsx';
import { taskApi, type TaskStatus } from '@/api/client';
import { useNotification } from '@/hooks/useNotification';
import { useToast } from '@/store/useToastStore';

import { ProgressHeader } from './ProgressHeader';
import { LogStream } from './LogStream';
import { type LogEntryData } from './LogEntry';
import { ResultSummary } from './ResultSummary';

interface ProcessingLogPanelProps {
  taskId: string;
  fileName: string;
  onComplete?: (result: TaskStatus['result']) => void;
  onError?: (error: string) => void;
  onCancel?: () => void;
}

export function ProcessingLogPanel({
  taskId,
  fileName,
  onComplete,
  onError,
  onCancel,
}: ProcessingLogPanelProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { sendNotification, isGranted } = useNotification();
  const toast = useToast();

  const [showLogs, setShowLogs] = useState(true);
  const [hasNotified, setHasNotified] = useState(false);

  // 轮询任务状态
  const { data: task } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => taskApi.getStatus(taskId),
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 800;
      if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
        return false; // 停止轮询
      }
      // 处理中时快速轮询
      return data.progress > 0 && data.progress < 100 ? 500 : 1000;
    },
    retry: 3,
  });

  // 任务完成/失败时触发通知
  useEffect(() => {
    if (!task || hasNotified) return;

    if (task.status === 'completed') {
      setHasNotified(true);

      // 浏览器通知
      if (isGranted) {
        sendNotification(t('notification.analysisComplete', '分析完成'), {
          body: t('notification.analysisCompleteBody', {
            defaultValue: '已导入 {{trades}} 笔交易，配对 {{positions}} 个持仓',
            trades: task.result?.new_trades ?? 0,
            positions: task.result?.positions_matched ?? 0,
          }),
          tag: 'analysis-complete',
        });
      }

      // Toast 通知
      toast.success(
        t('notification.analysisComplete', '分析完成'),
        t('notification.analysisCompleteBody', {
          defaultValue: '已导入 {{trades}} 笔交易',
          trades: task.result?.new_trades ?? 0,
          positions: task.result?.positions_matched ?? 0,
        })
      );

      onComplete?.(task.result);
    }

    if (task.status === 'failed') {
      setHasNotified(true);

      // 浏览器通知
      if (isGranted) {
        sendNotification(t('notification.analysisFailed', '分析失败'), {
          body: task.error_message || t('notification.unknownError', '未知错误'),
          tag: 'analysis-failed',
        });
      }

      // Toast 通知
      toast.error(
        t('notification.analysisFailed', '分析失败'),
        task.error_message || t('notification.unknownError', '未知错误')
      );

      onError?.(task.error_message || 'Unknown error');
    }
  }, [task?.status, hasNotified]);

  // 处理取消
  const handleCancel = () => {
    // TODO: 调用取消 API
    onCancel?.();
  };

  // 导航到统计页
  const handleViewStatistics = () => {
    navigate('/statistics');
  };

  // 导航到持仓页
  const handleViewPositions = () => {
    navigate('/positions');
  };

  // 上传另一个文件
  const handleUploadAnother = () => {
    onCancel?.();
  };

  // 转换日志格式
  const logs: LogEntryData[] = (task?.logs || []).map((log: any) => ({
    time: log.time,
    level: log.level || 'info',
    message: log.message,
    category: log.category,
  }));

  const isProcessing = task?.status === 'running' || task?.status === 'pending';
  const isComplete = task?.status === 'completed' || task?.status === 'failed';

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* 主卡片 */}
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl overflow-hidden">
        {/* 头部 */}
        <div className="px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h2 className="font-semibold text-neutral-900 dark:text-neutral-100">
                  {t('processingLog.title', '处理日志')}
                </h2>
                <p className="text-sm text-neutral-500 dark:text-neutral-400 truncate max-w-xs">
                  {fileName}
                </p>
              </div>
            </div>

            {/* 取消按钮 (仅处理中显示) */}
            {isProcessing && (
              <button
                onClick={handleCancel}
                className="p-2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 transition-colors"
                title={t('common.cancel', '取消')}
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {/* 进度区域 */}
        <div className="px-6 py-4 bg-neutral-50 dark:bg-neutral-900/30">
          <ProgressHeader
            progress={task?.progress ?? 0}
            currentStep={task?.current_step ?? t('processingLog.preparing', '准备中...')}
            status={(task?.status as any) ?? 'pending'}
          />
        </div>

        {/* 日志区域 (可折叠) */}
        {isProcessing && (
          <div className="relative">
            <button
              onClick={() => setShowLogs(!showLogs)}
              className={clsx(
                'w-full px-6 py-2 flex items-center justify-between',
                'text-sm text-neutral-500 dark:text-neutral-400',
                'hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors',
                'border-b border-neutral-200 dark:border-neutral-700'
              )}
            >
              <span>
                {t('processingLog.showLogs', { count: logs.length, defaultValue: '显示 {{count}} 条日志' })}
              </span>
              {showLogs ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showLogs && <LogStream logs={logs} isProcessing={isProcessing} className="border-b border-neutral-200 dark:border-neutral-700" />}
          </div>
        )}

        {/* 结果摘要 (完成后显示) */}
        {isComplete && (
          <div className="p-6">
            <ResultSummary
              result={task?.result || {}}
              status={task?.status as 'completed' | 'failed'}
              error={task?.error_message ?? undefined}
              onViewStatistics={handleViewStatistics}
              onViewPositions={handleViewPositions}
              onUploadAnother={handleUploadAnother}
            />

            {/* 日志展开 */}
            {logs.length > 0 && (
              <div className="mt-6 pt-6 border-t border-neutral-200 dark:border-neutral-700">
                <button
                  onClick={() => setShowLogs(!showLogs)}
                  className={clsx(
                    'w-full py-2 flex items-center justify-center gap-2',
                    'text-sm text-neutral-500 dark:text-neutral-400',
                    'hover:text-neutral-700 dark:hover:text-neutral-300 transition-colors'
                  )}
                >
                  <span>
                    {showLogs
                      ? t('processingLog.hideLogs', '隐藏日志')
                      : t('processingLog.showLogs', { count: logs.length, defaultValue: '显示 {{count}} 条日志' })}
                  </span>
                  {showLogs ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {showLogs && <LogStream logs={logs} isProcessing={false} className="mt-2 rounded-lg overflow-hidden" />}
              </div>
            )}
          </div>
        )}

        {/* 处理中提示 */}
        {isProcessing && (
          <div className="px-6 py-3 bg-blue-50 dark:bg-blue-900/20 text-center">
            <p className="text-sm text-blue-600 dark:text-blue-400">
              {t('landing.canClosePage', '您可以关闭此页面，分析会在后台继续进行')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProcessingLogPanel;
