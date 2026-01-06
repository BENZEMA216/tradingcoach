/**
 * LandingUpload - 首页上传页面
 *
 * input: CSV 文件上传
 * output: 创建分析任务，显示进度，完成后跳转
 * pos: 页面组件 - 应用入口，支持异步分析和多渠道通知
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { taskApi, systemApi } from '@/api/client';
import {
  Upload as UploadIcon,
  FileSpreadsheet,
  AlertCircle,
  Loader2,
  CheckCircle,
  ArrowRight,
  TrendingUp,
  BarChart3,
  Moon,
  Sun,
  Mail,
  Bell,
  X,
} from 'lucide-react';
import { LanguageSwitcher } from '@/components/common/LanguageSwitcher';
import { useNotification, getNotificationPreference, setNotificationPreference } from '@/hooks/useNotification';
import { useTaskStorage } from '@/hooks/useTaskStorage';
import { ProcessingLogPanel } from '@/components/processing';

type PageState = 'upload' | 'processing' | 'complete' | 'error';

export function LandingUpload() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const notification = useNotification();
  const taskStorage = useTaskStorage();

  // UI State
  const [pageState, setPageState] = useState<PageState>('upload');
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [enableNotification, setEnableNotification] = useState(() => getNotificationPreference());
  const [showRecoveryBanner, setShowRecoveryBanner] = useState(true);
  const [darkMode, setDarkMode] = useState(() =>
    document.documentElement.classList.contains('dark')
  );
  const fileInputRef = useRef<HTMLInputElement>(null);
  const hasNotified = useRef(false);

  // Check if data exists
  const { data: systemStats } = useQuery({
    queryKey: ['system', 'stats'],
    queryFn: () => systemApi.getStats(),
  });

  const hasData = (systemStats?.database?.positions?.count ?? 0) > 0;

  // Check for existing task from localStorage
  const { currentTask: storedTask, hasActiveTask, clearTask, saveTask, updateTaskStatus } = taskStorage;

  // Fetch stored task status if exists
  const { data: recoveredTask } = useQuery({
    queryKey: ['task', storedTask?.taskId],
    queryFn: () => taskApi.getStatus(storedTask!.taskId),
    enabled: !!storedTask?.taskId && taskStorage.isLoaded && showRecoveryBanner,
    refetchInterval: (data) => {
      const status = data?.state?.data?.status;
      if (status === 'completed' || status === 'failed' || status === 'cancelled') {
        return false;
      }
      return hasActiveTask ? 2000 : false;
    },
  });

  // Update stored task status
  useEffect(() => {
    if (recoveredTask && storedTask) {
      updateTaskStatus(
        recoveredTask.status as 'pending' | 'running' | 'completed' | 'failed',
        recoveredTask.progress,
        recoveredTask.current_step || undefined
      );
    }
  }, [recoveredTask?.status, recoveredTask?.progress]);

  // Task status polling for current task (only for complete/error states that need task data)
  const { data: task } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => taskApi.getStatus(taskId!),
    enabled: !!taskId && (pageState === 'complete' || pageState === 'error'),
    staleTime: Infinity, // Don't refetch after initial load
  });

  // Note: Task completion handling is now done by ProcessingLogPanel

  // Create task mutation
  const createTaskMutation = useMutation({
    mutationFn: ({ file, userEmail }: { file: File; userEmail?: string }) =>
      taskApi.create(file, userEmail || undefined, true),
    onSuccess: (data) => {
      setTaskId(data.task_id);
      setPageState('processing');
      hasNotified.current = false;

      // Save to localStorage
      saveTask({
        taskId: data.task_id,
        fileName: selectedFile?.name || 'unknown',
        createdAt: new Date().toISOString(),
        status: 'running',
      });
    },
    onError: () => {
      setPageState('error');
    },
  });

  // Request notification permission when checkbox is toggled
  const handleNotificationToggle = async () => {
    if (!enableNotification) {
      // Trying to enable
      const granted = await notification.requestPermission();
      if (granted) {
        setEnableNotification(true);
        setNotificationPreference(true);
      }
    } else {
      setEnableNotification(false);
      setNotificationPreference(false);
    }
  };

  // Drag handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.csv') || file.name.endsWith('.xls') || file.name.endsWith('.xlsx')) {
        setSelectedFile(file);
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      createTaskMutation.mutate({
        file: selectedFile,
        userEmail: email.trim() || undefined,
      });
    }
  };

  const toggleDarkMode = () => {
    document.documentElement.classList.toggle('dark');
    setDarkMode(!darkMode);
  };

  // Handle continue viewing stored task
  const handleContinueTask = () => {
    if (storedTask) {
      if (recoveredTask?.status === 'completed') {
        navigate('/statistics');
      } else {
        navigate(`/tasks/${storedTask.taskId}`);
      }
    }
  };

  // Handle dismiss recovery banner
  const handleDismissRecovery = () => {
    setShowRecoveryBanner(false);
    clearTask();
  };

  // Validate email format
  const isValidEmail = (value: string) => {
    if (!value) return true; // Empty is valid (optional)
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-white to-neutral-100 dark:from-neutral-950 dark:via-neutral-900 dark:to-neutral-950 flex flex-col">
      {/* Top Bar */}
      <header className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-blue-600 rounded-lg">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-semibold text-neutral-900 dark:text-white">
            TradingCoach
          </span>
        </div>
        <div className="flex items-center space-x-3">
          <LanguageSwitcher />
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-colors"
          >
            {darkMode ? (
              <Sun className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
            ) : (
              <Moon className="w-5 h-5 text-neutral-600 dark:text-neutral-400" />
            )}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-2xl">
          {/* Task Recovery Banner */}
          {taskStorage.isLoaded && storedTask && showRecoveryBanner && pageState === 'upload' && (
            <div className="mb-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 animate-fade-in">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-800/50 rounded-lg">
                    <BarChart3 className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-neutral-900 dark:text-white">
                      {hasActiveTask
                        ? t('landing.taskInProgress', '有一个分析任务正在进行中...')
                        : recoveredTask?.status === 'completed'
                        ? t('landing.taskCompleted', '上次的分析已完成')
                        : t('landing.taskFailed', '上次的分析失败了')}
                    </p>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-0.5">
                      {storedTask.fileName}
                      {hasActiveTask && recoveredTask && (
                        <span className="ml-2">
                          {t('landing.taskProgress', '进度: {{progress}}%', {
                            progress: recoveredTask.progress?.toFixed(0) || 0,
                          })}
                        </span>
                      )}
                    </p>
                    <div className="flex space-x-3 mt-3">
                      <button
                        onClick={handleContinueTask}
                        className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 flex items-center space-x-1"
                      >
                        <span>{t('landing.continueViewing', '继续查看')}</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                      <button
                        onClick={handleDismissRecovery}
                        className="px-3 py-1.5 text-neutral-600 dark:text-neutral-400 text-sm hover:bg-neutral-200 dark:hover:bg-neutral-700 rounded-lg"
                      >
                        {t('landing.ignoreAndUpload', '上传新文件')}
                      </button>
                    </div>
                  </div>
                </div>
                <button
                  onClick={handleDismissRecovery}
                  className="p-1 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Title */}
          <div className="text-center mb-10">
            <h1 className="text-4xl font-bold text-neutral-900 dark:text-white mb-3">
              {t('landing.title', '智能交易复盘分析')}
            </h1>
            <p className="text-lg text-neutral-500 dark:text-neutral-400">
              {t('landing.subtitle', '上传交易数据，获取专业分析报告')}
            </p>
          </div>

          {/* Upload State */}
          {pageState === 'upload' && (
            <div className="space-y-6 animate-fade-in">
              {/* Hidden file input */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xls,.xlsx"
                onChange={handleFileChange}
                className="hidden"
              />

              {/* Dropzone */}
              <div
                className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 scale-[1.02]'
                    : selectedFile
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                    : 'border-neutral-300 dark:border-neutral-700 hover:border-neutral-400 dark:hover:border-neutral-600 bg-white dark:bg-neutral-900/50'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="flex flex-col items-center space-y-4">
                  {selectedFile ? (
                    <>
                      <div className="p-4 bg-green-100 dark:bg-green-900/50 rounded-full">
                        <FileSpreadsheet className="w-10 h-10 text-green-600" />
                      </div>
                      <div>
                        <p className="text-lg font-medium text-neutral-900 dark:text-white">
                          {selectedFile.name}
                        </p>
                        <p className="text-sm text-neutral-500 mt-1">
                          {(selectedFile.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className={`p-4 rounded-full ${
                        dragActive ? 'bg-blue-100 dark:bg-blue-900/50' : 'bg-neutral-100 dark:bg-neutral-800'
                      }`}>
                        <UploadIcon className={`w-10 h-10 ${
                          dragActive ? 'text-blue-600' : 'text-neutral-400'
                        }`} />
                      </div>
                      <div>
                        <p className="text-lg font-medium text-neutral-900 dark:text-white">
                          {t('landing.dropzone', '拖拽 CSV 文件到此处')}
                        </p>
                        <p className="text-neutral-500 mt-1">
                          {t('landing.or', '或')} <span className="text-blue-600 hover:underline">{t('landing.selectFile', '点击选择文件')}</span>
                        </p>
                      </div>
                      <p className="text-sm text-neutral-400">
                        {t('landing.supportedFormats', '支持富途中文/英文导出格式、A股对账单')}
                      </p>
                    </>
                  )}
                </div>
              </div>

              {/* Notification Options (shown when file is selected) */}
              {selectedFile && (
                <div className="bg-white dark:bg-neutral-900 rounded-xl p-5 border border-neutral-200 dark:border-neutral-800 space-y-4">
                  {/* Email Input */}
                  <div>
                    <label className="flex items-center text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                      <Mail className="w-4 h-4 mr-2" />
                      {t('landing.emailLabel', '邮箱通知（可选）')}
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder={t('landing.emailPlaceholder', 'your@email.com')}
                      className={`w-full px-4 py-2.5 rounded-lg border bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white placeholder-neutral-400 focus:outline-none focus:ring-2 ${
                        email && !isValidEmail(email)
                          ? 'border-red-300 dark:border-red-700 focus:ring-red-500'
                          : 'border-neutral-300 dark:border-neutral-700 focus:ring-blue-500'
                      }`}
                    />
                    <p className="text-xs text-neutral-500 mt-1.5">
                      {t('landing.emailHint', '分析完成后，我们会发送邮件通知您')}
                    </p>
                  </div>

                  {/* Browser Notification Toggle */}
                  {notification.isSupported && (
                    <div className="flex items-center justify-between pt-3 border-t border-neutral-200 dark:border-neutral-700">
                      <div className="flex items-center">
                        <Bell className="w-4 h-4 text-neutral-500 mr-2" />
                        <div>
                          <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                            {t('notification.enableNotification', '启用桌面通知')}
                          </p>
                          <p className="text-xs text-neutral-500">
                            {t('notification.notificationHint', '分析完成时提醒您')}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={handleNotificationToggle}
                        className={`relative w-11 h-6 rounded-full transition-colors ${
                          enableNotification && notification.isGranted
                            ? 'bg-blue-600'
                            : 'bg-neutral-300 dark:bg-neutral-600'
                        }`}
                      >
                        <span
                          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-sm ${
                            enableNotification && notification.isGranted ? 'translate-x-5' : ''
                          }`}
                        />
                      </button>
                    </div>
                  )}

                  {notification.isDenied && (
                    <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center">
                      <AlertCircle className="w-3 h-3 mr-1" />
                      {t('notification.permissionDenied', '浏览器通知权限被拒绝，请在浏览器设置中开启')}
                    </p>
                  )}
                </div>
              )}

              {/* Upload Button */}
              {selectedFile && (
                <button
                  onClick={handleUpload}
                  disabled={createTaskMutation.isPending || (email !== '' && !isValidEmail(email))}
                  className="w-full px-6 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 font-medium text-lg transition-colors"
                >
                  {createTaskMutation.isPending ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>{t('landing.uploading', '上传中...')}</span>
                    </>
                  ) : (
                    <>
                      <UploadIcon className="w-5 h-5" />
                      <span>{t('landing.startAnalysis', '开始分析')}</span>
                    </>
                  )}
                </button>
              )}

              {/* Has Data Link */}
              {hasData && (
                <div className="text-center pt-6 border-t border-neutral-200 dark:border-neutral-800">
                  <p className="text-neutral-500 dark:text-neutral-400">
                    {t('landing.hasData', '已有数据？')}{' '}
                    <button
                      onClick={() => navigate('/statistics')}
                      className="text-blue-600 hover:text-blue-700 font-medium inline-flex items-center"
                    >
                      {t('landing.viewResults', '查看分析结果')}
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </button>
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Processing State - 使用 ProcessingLogPanel */}
          {pageState === 'processing' && taskId && (
            <ProcessingLogPanel
              taskId={taskId}
              fileName={selectedFile?.name || ''}
              onComplete={() => {
                setPageState('complete');
                queryClient.invalidateQueries({ queryKey: ['positions'] });
                queryClient.invalidateQueries({ queryKey: ['statistics'] });
                queryClient.invalidateQueries({ queryKey: ['system'] });
                updateTaskStatus('completed', 100);
                // Auto redirect after 2 seconds
                setTimeout(() => navigate('/statistics'), 2000);
              }}
              onError={() => {
                setPageState('error');
                updateTaskStatus('failed');
              }}
              onCancel={() => {
                setPageState('upload');
                setSelectedFile(null);
                setTaskId(null);
              }}
            />
          )}

          {/* Complete State */}
          {pageState === 'complete' && (
            <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 shadow-lg border border-green-200 dark:border-green-800 animate-fade-in">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
                <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">
                  {t('task.analysisComplete', '分析完成！')}
                </h2>
                <p className="text-neutral-500 dark:text-neutral-400 mt-1">
                  {t('landing.redirecting', '正在跳转到分析结果...')}
                </p>

                {task?.result && (
                  <div className="grid grid-cols-3 gap-4 mt-6">
                    <div className="bg-neutral-50 dark:bg-neutral-800 p-3 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">
                        {task.result.new_trades || 0}
                      </p>
                      <p className="text-xs text-neutral-500">{t('task.newTrades', '新交易')}</p>
                    </div>
                    <div className="bg-neutral-50 dark:bg-neutral-800 p-3 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">
                        {task.result.positions_matched || 0}
                      </p>
                      <p className="text-xs text-neutral-500">{t('task.positions', '持仓')}</p>
                    </div>
                    <div className="bg-neutral-50 dark:bg-neutral-800 p-3 rounded-lg">
                      <p className="text-2xl font-bold text-purple-600">
                        {task.result.positions_scored || 0}
                      </p>
                      <p className="text-xs text-neutral-500">{t('task.scored', '已评分')}</p>
                    </div>
                  </div>
                )}

                <button
                  onClick={() => navigate('/statistics')}
                  className="mt-6 px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 flex items-center justify-center space-x-2 mx-auto"
                >
                  <BarChart3 className="w-5 h-5" />
                  <span>{t('landing.viewStatistics', '查看统计分析')}</span>
                </button>
              </div>
            </div>
          )}

          {/* Error State */}
          {pageState === 'error' && (
            <div className="bg-white dark:bg-neutral-900 rounded-2xl p-8 shadow-lg border border-red-200 dark:border-red-800 animate-fade-in">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full mb-4">
                  <AlertCircle className="w-8 h-8 text-red-600" />
                </div>
                <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">
                  {t('task.analysisFailed', '分析失败')}
                </h2>
                <p className="text-neutral-500 dark:text-neutral-400 mt-1">
                  {task?.error_message || createTaskMutation.error?.message || t('common.unknownError', '未知错误')}
                </p>
                <button
                  onClick={() => {
                    setPageState('upload');
                    setSelectedFile(null);
                    setTaskId(null);
                    hasNotified.current = false;
                  }}
                  className="mt-6 px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700"
                >
                  {t('task.tryAgain', '重试')}
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-4 text-center text-sm text-neutral-400">
        <p>TradingCoach © 2024-2026</p>
      </footer>
    </div>
  );
}
