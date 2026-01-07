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
  Zap,
  Target,
  Shield,
  BrainCircuit,
} from 'lucide-react';
import { BackgroundEffects } from '@/components/landing/BackgroundEffects';
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
    <div className="min-h-screen bg-black text-white flex flex-col relative overflow-hidden font-sans selection:bg-white selection:text-black">
      {/* Precision Grid Background */}
      <BackgroundEffects />

      {/* Top Bar - Industrial */}
      <header className="flex items-center justify-between px-8 py-8 relative z-10 border-b border-white/5 bg-black/50 backdrop-blur-sm">
        <div className="flex items-center space-x-4">
          <div className="w-8 h-8 bg-white text-black flex items-center justify-center rounded-sm">
            <TrendingUp className="w-5 h-5" />
          </div>
          <span className="text-sm font-mono tracking-widest uppercase text-white/60">
            TC_TERMINAL_v1
          </span>
        </div>
        <div className="flex items-center space-x-6">
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

          {/* Hero - The "Monolith" */}
          <div className="text-center mb-24 relative z-10 pt-10">
            <div className="inline-block border border-white/20 px-4 py-1.5 rounded-full mb-10 bg-black/50 backdrop-blur">
              <span className="text-xs font-mono text-white/70 uppercase tracking-widest">System Operational • v0.9.2</span>
            </div>

            <h1 className="text-7xl md:text-9xl font-bold text-white mb-8 tracking-tighter leading-[0.9]">
              PURE<br />
              ALPHA.
            </h1>

            <p className="text-xl md:text-2xl text-white/50 max-w-2xl mx-auto leading-relaxed font-light tracking-wide">
              Construct your edge with institutional-grade <span className="text-white">precision metrics</span> and <span className="text-white">psychological profiling</span>.
            </p>
          </div>

          <div className="max-w-4xl mx-auto w-full relative z-10 px-6 pb-24">
            {/* Main Upload Area - Solid Industrial Block */}
            <div className="bg-[#050505] border border-white/10 rounded-sm p-1 shadow-2xl">
              <div className="border border-white/5 border-dashed rounded-sm p-12 md:p-16 text-center bg-black relative overflow-hidden group">

                {/* Scanline Effect on Hover */}
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/5 to-transparent -translate-y-full group-hover:translate-y-full transition-transform duration-1000 ease-in-out pointer-events-none" />
                {/* Hidden file input */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xls,.xlsx"
                  onChange={handleFileChange}
                  className="hidden"
                />

                {/* Dropzone - Industrial */}
                <div
                  className={`relative transition-all duration-300 ${dragActive ? 'scale-[1.01]' : ''}`}
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
                        <div className="mb-8">
                          <UploadIcon className="w-10 h-10 text-white mx-auto mb-4" />
                          <h3 className="text-2xl font-bold text-white tracking-tight uppercase">
                            Upload Protocol
                          </h3>
                        </div>
                        <div className="space-y-2">
                          <p className="text-white/40 font-mono text-sm">
                            DRAG BINARY CSV HERE
                          </p>
                          <div className="flex items-center justify-center space-x-4">
                            <span className="h-px w-8 bg-white/20"></span>
                            <span className="text-white/20 text-xs uppercase tracking-widest">OR</span>
                            <span className="h-px w-8 bg-white/20"></span>
                          </div>
                          <button className="text-white border-b border-white hover:border-transparent transition-colors text-sm uppercase tracking-wide pt-2">
                            Browse Data Source
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Notification Options (shown when file is selected) */}
                {selectedFile && (
                  <div className="bg-white dark:bg-neutral-900 rounded-xl p-5 border border-neutral-200 dark:border-neutral-800 space-y-4 mt-8">
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
                        className={`w-full px-4 py-2.5 rounded-lg border bg-white dark:bg-neutral-800 text-neutral-900 dark:text-white placeholder-neutral-400 focus:outline-none focus:ring-2 ${email && !isValidEmail(email)
                          ? 'border-red-300 dark:border-red-700 focus:ring-red-500'
                          : 'border-neutral-300 dark:border-neutral-700 focus:ring-blue-500'
                          }`}
                      />
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
                          </div>
                        </div>
                        <button
                          onClick={handleNotificationToggle}
                          className={`relative w-11 h-6 rounded-full transition-colors ${enableNotification && notification.isGranted
                            ? 'bg-blue-600'
                            : 'bg-neutral-300 dark:bg-neutral-600'
                            }`}
                        >
                          <span
                            className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-sm ${enableNotification && notification.isGranted ? 'translate-x-5' : ''
                              }`}
                          />
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Upload Button */}
                <button
                  onClick={handleUpload}
                  disabled={createTaskMutation.isPending || (email !== '' && !isValidEmail(email))}
                  className="w-full mt-8 py-4 bg-white text-black hover:bg-gray-200 disabled:bg-gray-800 disabled:text-gray-500 rounded-sm font-bold text-sm uppercase tracking-widest flex items-center justify-center space-x-3 transition-colors"
                >
                  {createTaskMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>INITIALIZING...</span>
                    </>
                  ) : (
                    <>
                      <span>EXECUTE ANALYSIS</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>

                {/* Has Data Link */}
                {hasData && (
                  <div className="text-center pt-6 border-t border-neutral-200 dark:border-neutral-800 mt-6">
                    <p className="text-neutral-500 dark:text-neutral-400">
                      {t('landing.hasData', '已有数据？')}{' '}
                      <button
                        onClick={() => navigate('/statistics')}
                        className="text-white border-b border-white hover:border-transparent transition-colors font-mono uppercase tracking-wide ml-2"
                      >
                        {t('landing.viewResults', '查看分析结果')}
                      </button>
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>


          {/* Industrial Features Grid */}
          <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-px bg-white/10 border border-white/10 relative z-10">
            <div className="bg-black p-10 hover:bg-[#050505] transition-colors group">
              <BrainCircuit className="w-6 h-6 text-white mb-6" />
              <h3 className="text-lg font-bold text-white mb-3 uppercase tracking-wider">Neural Pysch</h3>
              <p className="text-sm text-gray-500 font-mono leading-relaxed group-hover:text-gray-400 transition-colors">
                [MODULE_A] Decoding behavioral patterns using advanced algorithmic sequencing.
              </p>
            </div>

            <div className="bg-black p-10 hover:bg-[#050505] transition-colors group">
              <Target className="w-6 h-6 text-white mb-6" />
              <h3 className="text-lg font-bold text-white mb-3 uppercase tracking-wider">Precision Metric</h3>
              <p className="text-sm text-gray-500 font-mono leading-relaxed group-hover:text-gray-400 transition-colors">
                [MODULE_B] Objective trade grading system based on pre-defined strategy constraints.
              </p>
            </div>

            <div className="bg-black p-10 hover:bg-[#050505] transition-colors group">
              <Shield className="w-6 h-6 text-white mb-6" />
              <h3 className="text-lg font-bold text-white mb-3 uppercase tracking-wider">Risk Struct</h3>
              <p className="text-sm text-gray-500 font-mono leading-relaxed group-hover:text-gray-400 transition-colors">
                [MODULE_C] Real-time visualization of MAE/MFE and drawdown probabilities.
              </p>
            </div>
          </div>

          {/* Processing State - 使用 ProcessingLogPanel */}
          {
            pageState === 'processing' && taskId && (
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
            )
          }

          {/* Complete State */}
          {
            pageState === 'complete' && (
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
            )
          }

          {/* Error State */}
          {
            pageState === 'error' && (
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
            )
          }
        </div >
      </main >

      {/* Footer */}
      < footer className="px-6 py-4 text-center text-sm text-neutral-400" >
        <p>TradingCoach © 2024-2026</p>
      </footer >
    </div >
  );
}
