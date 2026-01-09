import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { uploadApi, taskApi, systemApi } from '@/api/client';
import type { UploadHistoryItem, TaskStatus } from '@/api/client';
import {
  Upload as UploadIcon,
  FileText,
  AlertCircle,
  Clock,
  Loader2,
  History,
  FileSpreadsheet,
  Mail,
  Trash2,
  AlertTriangle,
  X,
  CheckCircle,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { formatDate, formatNumber } from '@/utils/format';
import { useNavigate } from 'react-router-dom';

// 动态处理消息
const LOADING_MESSAGES = [
  'Initializing environment...',
  'Reading trade data...',
  'Matching opening and closing trades...',
  'Fetching market data from YFinance...',
  'Analyzing stock price trends...',
  'Calculating technical indicators...',
  'Analyzing risk factors...',
  'Generating performance insights...',
  'Finalizing report...',
];

// 进度步骤 (包含市场数据获取)
const STEPS = [
  { key: 'upload', label: '上传文件', labelEn: 'Upload', progress: 0 },
  { key: 'import', label: '导入数据', labelEn: 'Import', progress: 20 },
  { key: 'match', label: '持仓配对', labelEn: 'Match', progress: 45 },
  { key: 'data', label: '获取行情', labelEn: 'Fetch Data', progress: 70 },
  { key: 'score', label: '质量评分', labelEn: 'Score', progress: 85 },
  { key: 'complete', label: '完成', labelEn: 'Done', progress: 100 },
];

export function Upload() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [email, setEmail] = useState('');
  const [replaceMode, setReplaceMode] = useState(true);
  const [showResetModal, setShowResetModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 任务状态管理
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
  const [showLogs, setShowLogs] = useState(false);

  // 循环显示动态消息
  useEffect(() => {
    if (!isProcessing) return;
    const interval = setInterval(() => {
      setLoadingMsgIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 2000);
    return () => clearInterval(interval);
  }, [isProcessing]);

  // 任务状态轮询
  const { data: task } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => taskApi.getStatus(taskId!),
    enabled: !!taskId && isProcessing,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed' || data?.status === 'cancelled') {
        return false;
      }
      return 1000; // 每秒轮询
    },
  });

  // 任务完成时刷新缓存
  useEffect(() => {
    if (task?.status === 'completed') {
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['statistics'] });
      queryClient.invalidateQueries({ queryKey: ['upload', 'history'] });
    }
  }, [task?.status, queryClient]);

  // 计算当前步骤
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

  // 重置上传状态
  const resetUpload = () => {
    setTaskId(null);
    setIsProcessing(false);
    setSelectedFile(null);
    setShowLogs(false);
  };

  // Handle click to open file dialog
  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  // Get system stats for data count
  const { data: systemStats } = useQuery({
    queryKey: ['system', 'stats'],
    queryFn: () => systemApi.getStats(),
  });

  // Reset all data mutation
  const resetMutation = useMutation({
    mutationFn: () => systemApi.resetAllData(),
    onSuccess: () => {
      setShowResetModal(false);
      // Invalidate all queries to refresh data
      queryClient.invalidateQueries();
    },
  });

  // Get upload history
  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['upload', 'history'],
    queryFn: () => uploadApi.getHistory(10),
  });

  // Create task mutation (async)
  const createTaskMutation = useMutation({
    mutationFn: ({ file, email }: { file: File; email?: string }) =>
      taskApi.create(file, email, replaceMode),
    onSuccess: (data) => {
      // 不再跳转，在当前页面显示进度
      setTaskId(data.task_id);
      setIsProcessing(true);
    },
  });

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.csv')) {
        setSelectedFile(file);
      }
    }
  }, []);

  // Handle file input change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  // Handle upload
  const handleUpload = () => {
    if (selectedFile) {
      createTaskMutation.mutate({
        file: selectedFile,
        email: email.trim() || undefined,
      });
    }
  };

  // Validate email
  const isValidEmail = (email: string) => {
    if (!email) return true; // Empty is valid (optional field)
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          {t('upload.title', 'Upload Trades')}
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          {t('upload.subtitle', 'Import your trading history from CSV file')}
        </p>
      </div>

      {/* Data Reset Section */}
      {(systemStats?.database?.positions?.count ?? 0) > 0 && (
        <div className="glass-card bg-amber-50/50 dark:bg-amber-900/10 border-amber-200/50 dark:border-amber-800/30 p-5 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-500" />
              </div>
              <div>
                <p className="font-semibold text-amber-900 dark:text-amber-100">
                  {t('upload.existingData', 'You have existing data')}
                </p>
                <p className="text-sm text-amber-700 dark:text-amber-300/80 mt-0.5">
                  {t('upload.existingDataDesc', '{{positions}} positions, {{trades}} trades', {
                    positions: systemStats?.database?.positions?.count || 0,
                    trades: systemStats?.database?.trades?.count || 0,
                  })}
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowResetModal(true)}
              className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 rounded-lg border border-red-200/50 dark:border-red-800/50 transition-all duration-200 flex items-center space-x-2 text-sm font-medium backdrop-blur-sm"
            >
              <Trash2 className="w-4 h-4" />
              <span>{t('upload.resetData', 'Reset All Data')}</span>
            </button>
          </div>
        </div>
      )}

      {/* Reset Confirmation Modal */}
      {showResetModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full mx-4 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-full">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {t('upload.resetConfirmTitle', 'Confirm Data Reset')}
                </h3>
              </div>
              <button
                onClick={() => setShowResetModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mb-6">
              <p className="text-gray-600 dark:text-gray-300 mb-4">
                {t('upload.resetConfirmDesc', 'This action will permanently delete:')}
              </p>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                <li className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  <span>{t('upload.resetItem1', 'All trade records ({{count}})', { count: systemStats?.database?.trades?.count || 0 })}</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  <span>{t('upload.resetItem2', 'All position data ({{count}})', { count: systemStats?.database?.positions?.count || 0 })}</span>
                </li>
                <li className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  <span>{t('upload.resetItem3', 'All import history')}</span>
                </li>
              </ul>
              <p className="mt-4 text-sm font-medium text-red-600 dark:text-red-400">
                {t('upload.resetWarning', 'This action cannot be undone!')}
              </p>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => setShowResetModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                {t('common.cancel', 'Cancel')}
              </button>
              <button
                onClick={() => resetMutation.mutate()}
                disabled={resetMutation.isPending}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {resetMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>{t('upload.resetting', 'Resetting...')}</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    <span>{t('upload.confirmReset', 'Yes, Reset All')}</span>
                  </>
                )}
              </button>
            </div>

            {resetMutation.isError && (
              <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <p className="text-sm text-red-600 dark:text-red-400">
                  {(resetMutation.error as Error)?.message || 'Reset failed'}
                </p>
              </div>
            )}

            {resetMutation.isSuccess && (
              <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-sm text-green-600 dark:text-green-400">
                  {t('upload.resetSuccess', 'All data has been reset successfully!')}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Upload Area / Processing Progress */}
      <div className="glass-card p-8 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none transition-opacity duration-500 opacity-0 group-hover:opacity-100" />

        {/* 处理中 - 显示进度 */}
        {(isProcessing || task?.status === 'completed' || task?.status === 'failed') && task ? (
          <div className="space-y-6">
            {/* 进度头部 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {task.status === 'running' || task.status === 'pending' ? (
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                    <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                  </div>
                ) : task.status === 'completed' ? (
                  <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-full">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                ) : (
                  <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full">
                    <AlertCircle className="w-6 h-6 text-red-600" />
                  </div>
                )}
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {task.status === 'completed'
                      ? t('upload.analysisComplete', 'Analysis Complete!')
                      : task.status === 'failed'
                      ? t('upload.analysisFailed', 'Analysis Failed')
                      : t('upload.analyzing', 'Analyzing Trade Data...')}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {task.file_name}
                  </p>
                </div>
              </div>
              {task.status !== 'running' && task.status !== 'pending' && (
                <button
                  onClick={resetUpload}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            {/* 进度条 */}
            <div className="relative pt-2">
              <div className="h-3 bg-gray-100 dark:bg-gray-700/50 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    task.status === 'failed'
                      ? 'bg-red-500'
                      : task.status === 'completed'
                      ? 'bg-green-500'
                      : 'bg-gradient-to-r from-blue-600 via-purple-500 to-blue-600 bg-[length:200%_100%] animate-pulse'
                  }`}
                  style={{ width: `${task.progress}%` }}
                />
              </div>
              <div className="flex justify-between mt-2">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {task.status === 'running' && LOADING_MESSAGES[loadingMsgIndex]}
                </span>
                <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {task.progress.toFixed(0)}%
                </span>
              </div>
            </div>

            {/* 步骤指示器 */}
            <div className="flex justify-between px-4">
              {STEPS.map((step, index) => {
                const currentStepIndex = getCurrentStepIndex();
                const isCompleted = index < currentStepIndex || (index === currentStepIndex && task.status === 'completed');
                const isCurrent = index === currentStepIndex && (task.status === 'running' || task.status === 'pending');

                return (
                  <div key={step.key} className="flex flex-col items-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 transition-colors ${
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isCurrent
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : isCurrent ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <span className="text-sm">{index + 1}</span>
                      )}
                    </div>
                    <span className={`text-xs text-center ${
                      isCompleted || isCurrent
                        ? 'text-gray-900 dark:text-white font-medium'
                        : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      {i18n.language === 'zh' ? step.label : step.labelEn}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* 当前步骤消息 */}
            {task.current_step && (task.status === 'running' || task.status === 'pending') && (
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  {task.current_step}
                </p>
              </div>
            )}

            {/* 完成结果 */}
            {task.status === 'completed' && task.result && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-100 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('task.newTrades', 'New Trades')}
                    </p>
                    <p className="text-xl font-bold text-green-600">
                      {formatNumber(task.result.new_trades || 0)}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-100 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('task.positions', 'Positions')}
                    </p>
                    <p className="text-xl font-bold text-blue-600">
                      {formatNumber(task.result.positions_matched || 0)}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-100 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('task.symbols', 'Symbols')}
                    </p>
                    <p className="text-xl font-bold text-orange-600">
                      {formatNumber(task.result.symbols_fetched || 0)}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-100 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('task.scored', 'Scored')}
                    </p>
                    <p className="text-xl font-bold text-purple-600">
                      {formatNumber(task.result.positions_scored || 0)}
                    </p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-100 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {t('task.language', 'Format')}
                    </p>
                    <p className="text-xl font-bold text-gray-600 dark:text-gray-300">
                      {task.result.language === 'english' ? 'EN' : 'CN'}
                    </p>
                  </div>
                </div>

                <div className="flex space-x-3">
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
                  <button
                    onClick={resetUpload}
                    className="px-4 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>{t('upload.uploadMore', 'Upload More')}</span>
                  </button>
                </div>
              </div>
            )}

            {/* 失败信息 */}
            {task.status === 'failed' && (
              <div className="space-y-4">
                <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                  <p className="text-red-700 dark:text-red-300">
                    {task.error_message || 'An unknown error occurred'}
                  </p>
                </div>
                <button
                  onClick={resetUpload}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>{t('task.tryAgain', 'Try Again')}</span>
                </button>
              </div>
            )}

            {/* 处理日志 */}
            {task.logs && task.logs.length > 0 && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                <button
                  onClick={() => setShowLogs(!showLogs)}
                  className="flex items-center justify-between w-full text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  <span>{t('task.logs', 'Processing Logs')} ({task.logs.length})</span>
                  <span>{showLogs ? '▲' : '▼'}</span>
                </button>

                {showLogs && (
                  <div className="mt-3 space-y-1 max-h-40 overflow-y-auto">
                    {task.logs.slice(-20).map((log, index) => (
                      <div
                        key={index}
                        className={`text-xs font-mono p-2 rounded ${
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
          </div>
        ) : (
          /* 上传区域 - 未处理时显示 */
          <>
        {/* Hidden file input - outside the clickable area */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="hidden"
        />

        <div
          className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 cursor-pointer ${dragActive
              ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/10 scale-[1.02] shadow-lg shadow-blue-500/10'
              : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500 hover:bg-gray-50/50 dark:hover:bg-gray-700/30'
            }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={handleClick}
        >
          <div className="flex flex-col items-center space-y-4">
            <div className={`p-5 rounded-full transition-transform duration-300 ${dragActive ? 'bg-blue-100 dark:bg-blue-900/40 scale-110' : 'bg-gray-100 dark:bg-gray-800 group-hover:scale-110'
              }`}>
              <UploadIcon className={`w-10 h-10 transition-colors duration-300 ${dragActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500 group-hover:text-blue-500 dark:group-hover:text-blue-400'
                }`} />
            </div>

            <div>
              <p className="text-lg font-medium text-gray-900 dark:text-white">
                {t('upload.dragDrop', 'Drag and drop your CSV file here')}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {t('upload.orClick', 'or click to browse')}
              </p>
            </div>

            <p className="text-xs text-gray-400">
              {t('upload.supportedFormats', 'Supports Futu Securities CSV export (Chinese/English)')}
            </p>
          </div>
        </div>

        {/* Selected File and Options */}
        {selectedFile && (
          <div className="mt-6 space-y-4">
            {/* File Info */}
            <div className="p-4 bg-gray-50/50 dark:bg-gray-800/50 rounded-xl flex items-center justify-between border border-gray-100 dark:border-gray-700/50 backdrop-blur-sm">
              <div className="flex items-center space-x-3">
                <FileSpreadsheet className="w-8 h-8 text-green-600" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedFile(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                &times;
              </button>
            </div>

            {/* Email Input (Optional) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Mail className="w-4 h-4 inline mr-2" />
                {t('upload.emailLabel', 'Email for notification (optional)')}
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('upload.emailPlaceholder', 'your@email.com')}
                className={`w-full px-4 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${!isValidEmail(email)
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-gray-300 dark:border-gray-600'
                  }`}
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {t('upload.emailHint', 'We will notify you when analysis is complete')}
              </p>
            </div>

            {/* Replace Mode Toggle */}
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="replaceMode"
                checked={replaceMode}
                onChange={(e) => setReplaceMode(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <label htmlFor="replaceMode" className="text-sm text-gray-700 dark:text-gray-300">
                {t('upload.replaceMode', 'Replace existing data (recommended for full re-analysis)')}
              </label>
            </div>

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={createTaskMutation.isPending || !isValidEmail(email)}
              className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none flex items-center justify-center space-x-2 font-semibold text-lg transition-all duration-200 active:scale-[0.98]"
            >
              {createTaskMutation.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>{t('upload.creating', 'Creating task...')}</span>
                </>
              ) : (
                <>
                  <UploadIcon className="w-5 h-5" />
                  <span>{t('upload.startAnalysis', 'Start Analysis')}</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Error */}
        {createTaskMutation.isError && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div>
                <p className="font-medium text-red-800 dark:text-red-200">
                  {t('upload.error', 'Failed to create task')}
                </p>
                <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                  {(createTaskMutation.error as Error)?.message || 'Unknown error'}
                </p>
              </div>
            </div>
          </div>
        )}
          </>
        )}
      </div>

      {/* Upload History */}
      <div className="glass-card p-6">
        <div className="flex items-center space-x-3 mb-4">
          <History className="w-5 h-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('upload.history', 'Import History')}
          </h2>
        </div>

        {historyLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : history && history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <th className="pb-3 pr-4">{t('upload.historyDate', 'Date')}</th>
                  <th className="pb-3 pr-4">{t('upload.historyFile', 'File')}</th>
                  <th className="pb-3 pr-4">{t('upload.historyType', 'Type')}</th>
                  <th className="pb-3 pr-4 text-right">{t('upload.historyNew', 'New')}</th>
                  <th className="pb-3 pr-4 text-right">{t('upload.historySkipped', 'Skipped')}</th>
                  <th className="pb-3">{t('upload.historyStatus', 'Status')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {history.map((item: UploadHistoryItem) => (
                  <tr key={item.id} className="text-sm">
                    <td className="py-3 pr-4 text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4" />
                        <span>{formatDate(item.import_time)}</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-gray-900 dark:text-white max-w-[200px] truncate">
                      {item.file_name}
                    </td>
                    <td className="py-3 pr-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${item.file_type === 'english'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                          : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                        }`}>
                        {item.file_type === 'english' ? 'EN' : 'CN'}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-right font-medium text-green-600">
                      +{item.new_trades}
                    </td>
                    <td className="py-3 pr-4 text-right text-gray-500">
                      {item.duplicates_skipped}
                    </td>
                    <td className="py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${item.status === 'success'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                          : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                        }`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>{t('upload.noHistory', 'No import history yet')}</p>
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="glass-card border-blue-200/50 dark:border-blue-800/30 bg-blue-50/30 dark:bg-blue-900/10 p-6">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
          {t('upload.howTo', 'How to export from Futu')}
        </h3>
        <ol className="text-sm text-blue-800 dark:text-blue-200 space-y-1 list-decimal list-inside">
          <li>{t('upload.step1', 'Open Futu Trading App or Web')}</li>
          <li>{t('upload.step2', 'Go to Trade History')}</li>
          <li>{t('upload.step3', 'Click Export and select CSV format')}</li>
          <li>{t('upload.step4', 'Upload the downloaded file here')}</li>
        </ol>
      </div>
    </div>
  );
}
