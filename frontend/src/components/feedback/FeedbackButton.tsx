/**
 * 用户反馈按钮组件
 *
 * 浮动在页面右下角，点击打开反馈表单
 * 反馈通过后端 API 自动创建 GitHub Issue
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { MessageSquarePlus, X, Send, Bug, Lightbulb, HelpCircle, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

type FeedbackType = 'bug' | 'feature' | 'question';
type SubmitStatus = 'idle' | 'submitting' | 'success' | 'error';

const FEEDBACK_CONFIG: Record<FeedbackType, { icon: typeof Bug; label: string; labelZh: string; color: string }> = {
  bug: { icon: Bug, label: 'Bug Report', labelZh: '报告问题', color: 'text-red-500' },
  feature: { icon: Lightbulb, label: 'Feature Request', labelZh: '功能建议', color: 'text-amber-500' },
  question: { icon: HelpCircle, label: 'Question', labelZh: '使用问题', color: 'text-blue-500' },
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export function FeedbackButton() {
  const { i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  const [isOpen, setIsOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('feature');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async () => {
    if (!title.trim()) return;

    setSubmitStatus('submitting');
    setErrorMessage('');

    try {
      const response = await axios.post(`${API_BASE}/feedback`, {
        type: feedbackType,
        title: title.trim(),
        description: description.trim() || undefined,
        page_url: window.location.href,
        user_agent: navigator.userAgent,
      });

      if (response.data.success) {
        setSubmitStatus('success');
        // 3秒后关闭并重置
        setTimeout(() => {
          setTitle('');
          setDescription('');
          setIsOpen(false);
          setSubmitStatus('idle');
        }, 2000);
      }
    } catch (error) {
      setSubmitStatus('error');
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        setErrorMessage(error.response.data.detail);
      } else {
        setErrorMessage(isZh ? '提交失败，请稍后重试' : 'Submission failed. Please try again.');
      }
    }
  };

  const handleClose = () => {
    if (submitStatus !== 'submitting') {
      setIsOpen(false);
      setSubmitStatus('idle');
      setErrorMessage('');
    }
  };

  return (
    <>
      {/* 浮动按钮 */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 p-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 group"
        title={isZh ? '反馈建议' : 'Feedback'}
      >
        <MessageSquarePlus className="w-5 h-5" />
        <span className="absolute right-full mr-3 top-1/2 -translate-y-1/2 px-2 py-1 rounded bg-neutral-900 text-white text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
          {isZh ? '反馈建议' : 'Feedback'}
        </span>
      </button>

      {/* 反馈弹窗 */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* 遮罩 */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={handleClose}
          />

          {/* 弹窗内容 */}
          <div className="relative w-full max-w-md bg-white dark:bg-neutral-900 rounded-lg shadow-2xl">
            {/* 头部 */}
            <div className="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-white/10">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                {isZh ? '反馈建议' : 'Send Feedback'}
              </h3>
              <button
                onClick={handleClose}
                disabled={submitStatus === 'submitting'}
                className="p-1 rounded hover:bg-neutral-100 dark:hover:bg-white/10 text-slate-500 disabled:opacity-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 成功状态 */}
            {submitStatus === 'success' ? (
              <div className="p-8 text-center">
                <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h4 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  {isZh ? '感谢你的反馈！' : 'Thank you for your feedback!'}
                </h4>
                <p className="text-sm text-slate-500 dark:text-white/60">
                  {isZh ? '我们已收到你的反馈，会尽快处理。' : 'We have received your feedback and will review it soon.'}
                </p>
              </div>
            ) : (
              <>
                {/* 表单 */}
                <div className="p-4 space-y-4">
                  {/* 反馈类型 */}
                  <div className="flex gap-2">
                    {(Object.keys(FEEDBACK_CONFIG) as FeedbackType[]).map((type) => {
                      const config = FEEDBACK_CONFIG[type];
                      const Icon = config.icon;
                      const isActive = feedbackType === type;

                      return (
                        <button
                          key={type}
                          onClick={() => setFeedbackType(type)}
                          disabled={submitStatus === 'submitting'}
                          className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border transition-all ${
                            isActive
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-500/10'
                              : 'border-neutral-200 dark:border-white/10 hover:border-neutral-300 dark:hover:border-white/20'
                          } disabled:opacity-50`}
                        >
                          <Icon className={`w-4 h-4 ${isActive ? config.color : 'text-slate-400'}`} />
                          <span className={`text-sm ${isActive ? 'text-slate-900 dark:text-white' : 'text-slate-500'}`}>
                            {isZh ? config.labelZh : config.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>

                  {/* 标题 */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-white/70 mb-1">
                      {isZh ? '标题' : 'Title'} <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      disabled={submitStatus === 'submitting'}
                      placeholder={isZh ? '简短描述你的反馈' : 'Brief description'}
                      className="w-full px-3 py-2 rounded-lg border border-neutral-200 dark:border-white/10 bg-white dark:bg-white/5 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                    />
                  </div>

                  {/* 详细描述 */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-white/70 mb-1">
                      {isZh ? '详细描述' : 'Details'} ({isZh ? '可选' : 'optional'})
                    </label>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      disabled={submitStatus === 'submitting'}
                      placeholder={isZh ? '提供更多细节帮助我们理解...' : 'Provide more details...'}
                      rows={4}
                      className="w-full px-3 py-2 rounded-lg border border-neutral-200 dark:border-white/10 bg-white dark:bg-white/5 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:opacity-50"
                    />
                  </div>

                  {/* 错误提示 */}
                  {submitStatus === 'error' && (
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-sm">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>{errorMessage}</span>
                    </div>
                  )}
                </div>

                {/* 底部 */}
                <div className="flex justify-end gap-3 p-4 border-t border-neutral-200 dark:border-white/10">
                  <button
                    onClick={handleClose}
                    disabled={submitStatus === 'submitting'}
                    className="px-4 py-2 text-sm text-slate-600 dark:text-white/60 hover:text-slate-900 dark:hover:text-white disabled:opacity-50"
                  >
                    {isZh ? '取消' : 'Cancel'}
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={!title.trim() || submitStatus === 'submitting'}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
                  >
                    {submitStatus === 'submitting' ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        {isZh ? '提交中...' : 'Submitting...'}
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        {isZh ? '提交反馈' : 'Submit'}
                      </>
                    )}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default FeedbackButton;
