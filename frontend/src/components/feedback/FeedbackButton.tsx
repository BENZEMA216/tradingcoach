/**
 * 用户反馈按钮组件
 *
 * 浮动在页面右下角，点击打开反馈表单
 * 反馈会创建 GitHub Issue
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { MessageSquarePlus, X, Send, Bug, Lightbulb, HelpCircle } from 'lucide-react';
import { captureMessage } from '@/lib/sentry';

type FeedbackType = 'bug' | 'feature' | 'question';

const FEEDBACK_CONFIG: Record<FeedbackType, { icon: typeof Bug; label: string; labelZh: string; color: string }> = {
  bug: { icon: Bug, label: 'Bug Report', labelZh: '报告问题', color: 'text-red-500' },
  feature: { icon: Lightbulb, label: 'Feature Request', labelZh: '功能建议', color: 'text-amber-500' },
  question: { icon: HelpCircle, label: 'Question', labelZh: '使用问题', color: 'text-blue-500' },
};

// GitHub Issue 创建 URL
const GITHUB_REPO = 'BENZEMA216/tradingcoach';

function createGitHubIssueUrl(type: FeedbackType, title: string, body: string): string {
  const labels = type === 'bug' ? 'bug' : type === 'feature' ? 'enhancement' : 'question';
  const params = new URLSearchParams({
    title: `[${type.toUpperCase()}] ${title}`,
    body: `## 反馈内容\n\n${body}\n\n---\n*通过应用内反馈提交*`,
    labels,
  });
  return `https://github.com/${GITHUB_REPO}/issues/new?${params.toString()}`;
}

export function FeedbackButton() {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  const [isOpen, setIsOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('feature');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = () => {
    if (!title.trim()) return;

    setIsSubmitting(true);

    // 记录反馈到 Sentry（用于统计）
    captureMessage(`Feedback submitted: [${feedbackType}] ${title}`, 'info');

    // 打开 GitHub Issue 页面
    const url = createGitHubIssueUrl(feedbackType, title, description);
    window.open(url, '_blank');

    // 重置表单
    setTimeout(() => {
      setTitle('');
      setDescription('');
      setIsOpen(false);
      setIsSubmitting(false);
    }, 500);
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
            onClick={() => setIsOpen(false)}
          />

          {/* 弹窗内容 */}
          <div className="relative w-full max-w-md bg-white dark:bg-neutral-900 rounded-lg shadow-2xl">
            {/* 头部 */}
            <div className="flex items-center justify-between p-4 border-b border-neutral-200 dark:border-white/10">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                {isZh ? '反馈建议' : 'Send Feedback'}
              </h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded hover:bg-neutral-100 dark:hover:bg-white/10 text-slate-500"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

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
                      className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border transition-all ${
                        isActive
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-500/10'
                          : 'border-neutral-200 dark:border-white/10 hover:border-neutral-300 dark:hover:border-white/20'
                      }`}
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
                  placeholder={isZh ? '简短描述你的反馈' : 'Brief description'}
                  className="w-full px-3 py-2 rounded-lg border border-neutral-200 dark:border-white/10 bg-white dark:bg-white/5 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  placeholder={isZh ? '提供更多细节帮助我们理解...' : 'Provide more details...'}
                  rows={4}
                  className="w-full px-3 py-2 rounded-lg border border-neutral-200 dark:border-white/10 bg-white dark:bg-white/5 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
              </div>

              {/* 提示 */}
              <p className="text-xs text-slate-500 dark:text-white/40">
                {isZh
                  ? '点击提交将打开 GitHub Issue 页面，你可以在那里完成提交。'
                  : 'Clicking submit will open GitHub Issues where you can complete the submission.'}
              </p>
            </div>

            {/* 底部 */}
            <div className="flex justify-end gap-3 p-4 border-t border-neutral-200 dark:border-white/10">
              <button
                onClick={() => setIsOpen(false)}
                className="px-4 py-2 text-sm text-slate-600 dark:text-white/60 hover:text-slate-900 dark:hover:text-white"
              >
                {isZh ? '取消' : 'Cancel'}
              </button>
              <button
                onClick={handleSubmit}
                disabled={!title.trim() || isSubmitting}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                <Send className="w-4 h-4" />
                {isZh ? '提交反馈' : 'Submit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default FeedbackButton;
