import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { taskApi } from '@/api/client';
import {
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowRight,
  Clock,
  FileSpreadsheet,
  Mail,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import { formatNumber } from '@/utils/format';

// Progress step data
const STEPS = [
  { key: 'upload', label: '上传文件', progress: 0 },
  { key: 'import', label: '导入数据', progress: 20 },
  { key: 'match', label: '持仓配对', progress: 50 },
  { key: 'score', label: '质量评分', progress: 80 },
  { key: 'complete', label: '完成', progress: 100 },
];

export function TaskStatus() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const [showLogs, setShowLogs] = useState(false);

  // Fetch task status with auto-refresh
  const { data: task, isLoading, isError, error } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => taskApi.getStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (data) => {
      // Stop polling when task is complete
      if (data?.state?.data?.status === 'completed' ||
          data?.state?.data?.status === 'failed' ||
          data?.state?.data?.status === 'cancelled') {
        return false;
      }
      return 1000; // Poll every 1 second
    },
  });

  // Invalidate queries when task completes
  useEffect(() => {
    if (task?.status === 'completed') {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['statistics'] });
      queryClient.invalidateQueries({ queryKey: ['upload', 'history'] });
    }
  }, [task?.status, queryClient]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (isError || !task) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <AlertCircle className="w-12 h-12 text-red-500" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          {t('task.notFound', 'Task not found')}
        </h2>
        <p className="text-gray-500 dark:text-gray-400">
          {(error as Error)?.message || 'The task you are looking for does not exist.'}
        </p>
        <button
          onClick={() => navigate('/upload')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {t('task.backToUpload', 'Back to Upload')}
        </button>
      </div>
    );
  }

  // Get status icon and color
  const getStatusDisplay = () => {
    switch (task.status) {
      case 'pending':
        return {
          icon: <Clock className="w-6 h-6" />,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
          label: t('task.pending', 'Pending'),
        };
      case 'running':
        return {
          icon: <Loader2 className="w-6 h-6 animate-spin" />,
          color: 'text-blue-500',
          bgColor: 'bg-blue-100 dark:bg-blue-900/30',
          label: t('task.running', 'Processing'),
        };
      case 'completed':
        return {
          icon: <CheckCircle className="w-6 h-6" />,
          color: 'text-green-500',
          bgColor: 'bg-green-100 dark:bg-green-900/30',
          label: t('task.completed', 'Completed'),
        };
      case 'failed':
        return {
          icon: <AlertCircle className="w-6 h-6" />,
          color: 'text-red-500',
          bgColor: 'bg-red-100 dark:bg-red-900/30',
          label: t('task.failed', 'Failed'),
        };
      case 'cancelled':
        return {
          icon: <XCircle className="w-6 h-6" />,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100 dark:bg-gray-700',
          label: t('task.cancelled', 'Cancelled'),
        };
      default:
        return {
          icon: <Clock className="w-6 h-6" />,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100 dark:bg-gray-700',
          label: task.status,
        };
    }
  };

  const statusDisplay = getStatusDisplay();

  // Calculate current step index
  const getCurrentStepIndex = () => {
    const progress = task.progress;
    for (let i = STEPS.length - 1; i >= 0; i--) {
      if (progress >= STEPS[i].progress) {
        return i;
      }
    }
    return 0;
  };

  const currentStepIndex = getCurrentStepIndex();

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {t('task.title', 'Analysis Task')}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 flex items-center mt-1">
            <span className="font-mono text-sm">{task.task_id}</span>
          </p>
        </div>
        <div className={`px-4 py-2 rounded-full flex items-center space-x-2 ${statusDisplay.bgColor} ${statusDisplay.color}`}>
          {statusDisplay.icon}
          <span className="font-medium">{statusDisplay.label}</span>
        </div>
      </div>

      {/* File Info Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <FileSpreadsheet className="w-8 h-8 text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-medium text-gray-900 dark:text-white">
              {task.file_name || 'Unknown file'}
            </h3>
            {task.email && (
              <p className="text-sm text-gray-500 dark:text-gray-400 flex items-center mt-1">
                <Mail className="w-4 h-4 mr-1" />
                {task.email}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Progress Section */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
          {t('task.progress', 'Progress')}
        </h3>

        {/* Progress Bar */}
        <div className="relative mb-6">
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-500"
              style={{ width: `${task.progress}%` }}
            />
          </div>
          <div className="absolute right-0 top-4 text-sm font-medium text-gray-600 dark:text-gray-400">
            {task.progress.toFixed(0)}%
          </div>
        </div>

        {/* Steps */}
        <div className="flex justify-between">
          {STEPS.map((step, index) => (
            <div key={step.key} className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 transition-colors ${
                  index < currentStepIndex
                    ? 'bg-green-500 text-white'
                    : index === currentStepIndex && task.status === 'running'
                    ? 'bg-blue-500 text-white'
                    : index === currentStepIndex && task.status === 'completed'
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                }`}
              >
                {index < currentStepIndex || (index === currentStepIndex && task.status === 'completed') ? (
                  <CheckCircle className="w-5 h-5" />
                ) : index === currentStepIndex && task.status === 'running' ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <span className="text-sm">{index + 1}</span>
                )}
              </div>
              <span
                className={`text-xs text-center ${
                  index <= currentStepIndex
                    ? 'text-gray-900 dark:text-white font-medium'
                    : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                {step.label}
              </span>
            </div>
          ))}
        </div>

        {/* Current Step Message */}
        {task.current_step && task.status === 'running' && (
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              {task.current_step}
            </p>
          </div>
        )}
      </div>

      {/* Result Section (Completed) */}
      {task.status === 'completed' && task.result && (
        <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-6 border border-green-200 dark:border-green-800">
          <div className="flex items-center space-x-3 mb-4">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <h3 className="font-semibold text-green-800 dark:text-green-200">
              {t('task.analysisComplete', 'Analysis Complete!')}
            </h3>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('task.newTrades', 'New Trades')}
              </p>
              <p className="text-xl font-bold text-green-600">
                {formatNumber(task.result.new_trades || 0)}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('task.positions', 'Positions')}
              </p>
              <p className="text-xl font-bold text-blue-600">
                {formatNumber(task.result.positions_matched || 0)}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('task.scored', 'Scored')}
              </p>
              <p className="text-xl font-bold text-purple-600">
                {formatNumber(task.result.positions_scored || 0)}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('task.language', 'Format')}
              </p>
              <p className="text-xl font-bold text-gray-600">
                {task.result.language === 'english' ? 'EN' : 'CN'}
              </p>
            </div>
          </div>

          <div className="mt-4 flex space-x-3">
            <button
              onClick={() => navigate('/positions')}
              className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center space-x-2"
            >
              <span>{t('task.viewPositions', 'View Positions')}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              {t('task.viewDashboard', 'Dashboard')}
            </button>
          </div>
        </div>
      )}

      {/* Error Section (Failed) */}
      {task.status === 'failed' && (
        <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 border border-red-200 dark:border-red-800">
          <div className="flex items-center space-x-3 mb-4">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <h3 className="font-semibold text-red-800 dark:text-red-200">
              {t('task.analysisFailed', 'Analysis Failed')}
            </h3>
          </div>

          <p className="text-red-700 dark:text-red-300 mb-4">
            {task.error_message || 'An unknown error occurred'}
          </p>

          <button
            onClick={() => navigate('/upload')}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>{t('task.tryAgain', 'Try Again')}</span>
          </button>
        </div>
      )}

      {/* Logs Section */}
      {task.logs && task.logs.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
          <button
            onClick={() => setShowLogs(!showLogs)}
            className="flex items-center justify-between w-full"
          >
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {t('task.logs', 'Processing Logs')}
            </h3>
            <span className="text-gray-500 dark:text-gray-400 text-sm">
              {showLogs ? '▲' : '▼'}
            </span>
          </button>

          {showLogs && (
            <div className="mt-4 space-y-2 max-h-60 overflow-y-auto">
              {task.logs.map((log, index) => (
                <div
                  key={index}
                  className={`text-sm font-mono p-2 rounded ${
                    log.level === 'error'
                      ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                      : 'bg-gray-50 dark:bg-gray-700/50 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  <span className="text-gray-400 dark:text-gray-500 mr-2">
                    {new Date(log.time).toLocaleTimeString()}
                  </span>
                  {log.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Back Button */}
      <div className="text-center">
        <button
          onClick={() => navigate('/upload')}
          className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
        >
          ← {t('task.backToUpload', 'Back to Upload')}
        </button>
      </div>
    </div>
  );
}
