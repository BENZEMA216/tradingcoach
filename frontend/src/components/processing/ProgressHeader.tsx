/**
 * ProgressHeader - 进度条和步骤指示器
 *
 * input: progress (0-100), currentStep, status
 * output: 进度条 + 四阶段步骤指示器
 * pos: ProcessingLogPanel 子组件
 */

import { Fragment } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, GitMerge, Star, CheckCircle, Loader2 } from 'lucide-react';
import clsx from 'clsx';

interface ProgressHeaderProps {
  progress: number;
  currentStep: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

const steps = [
  { key: 'import', icon: Upload, range: [0, 40] },
  { key: 'match', icon: GitMerge, range: [40, 70] },
  { key: 'score', icon: Star, range: [70, 95] },
  { key: 'complete', icon: CheckCircle, range: [95, 100] },
];

function getStepStatus(
  stepRange: [number, number],
  progress: number,
  taskStatus: string
): 'done' | 'current' | 'pending' {
  if (taskStatus === 'completed') return 'done';
  if (taskStatus === 'failed') return progress >= stepRange[0] ? 'current' : 'pending';

  if (progress >= stepRange[1]) return 'done';
  if (progress >= stepRange[0]) return 'current';
  return 'pending';
}

export function ProgressHeader({ progress, currentStep, status }: ProgressHeaderProps) {
  const { t } = useTranslation();

  const stepLabels: Record<string, string> = {
    import: t('processingLog.steps.import', '导入'),
    match: t('processingLog.steps.match', '配对'),
    score: t('processingLog.steps.score', '评分'),
    complete: t('processingLog.steps.complete', '完成'),
  };

  return (
    <div className="space-y-4">
      {/* 进度条 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className={clsx(
            'text-neutral-600 dark:text-neutral-400',
            status === 'running' && 'typing-cursor'
          )}>
            {status === 'completed'
              ? t('processingLog.completed', '已完成')
              : status === 'failed'
              ? t('processingLog.failed', '处理失败')
              : currentStep}
          </span>
          <span className={clsx(
            'font-medium tabular-nums',
            status === 'completed' ? 'text-green-600 dark:text-green-400' :
            status === 'failed' ? 'text-red-600 dark:text-red-400' :
            'text-blue-600 dark:text-blue-400'
          )}>
            {Math.round(progress)}%
          </span>
        </div>

        <div className="h-2.5 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
          <div
            className={clsx(
              'h-full rounded-full transition-all duration-300 ease-out',
              status === 'completed'
                ? 'bg-green-500'
                : status === 'failed'
                ? 'bg-red-500'
                : 'bg-gradient-to-r from-blue-500 via-blue-400 to-blue-500 progress-bar-glow'
            )}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* 步骤指示器 */}
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const stepStatus = getStepStatus(step.range as [number, number], progress, status);
          const Icon = step.icon;

          return (
            <Fragment key={step.key}>
              {/* 步骤 */}
              <div className="flex flex-col items-center gap-1">
                <div
                  className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300',
                    stepStatus === 'done' && 'bg-green-100 dark:bg-green-900/30',
                    stepStatus === 'current' && 'bg-blue-100 dark:bg-blue-900/30',
                    stepStatus === 'pending' && 'bg-neutral-100 dark:bg-neutral-800',
                    stepStatus === 'current' && status === 'running' && 'step-indicator-active'
                  )}
                >
                  {stepStatus === 'current' && status === 'running' ? (
                    <Loader2
                      className={clsx(
                        'w-4 h-4 animate-spin',
                        'text-blue-600 dark:text-blue-400'
                      )}
                    />
                  ) : (
                    <Icon
                      className={clsx(
                        'w-4 h-4',
                        stepStatus === 'done' && 'text-green-600 dark:text-green-400',
                        stepStatus === 'current' && 'text-blue-600 dark:text-blue-400',
                        stepStatus === 'pending' && 'text-neutral-400 dark:text-neutral-500'
                      )}
                    />
                  )}
                </div>
                <span
                  className={clsx(
                    'text-xs font-medium transition-all duration-300',
                    stepStatus === 'done' && 'text-green-600 dark:text-green-400',
                    stepStatus === 'current' && 'text-blue-600 dark:text-blue-400 font-semibold',
                    stepStatus === 'pending' && 'text-neutral-400 dark:text-neutral-500'
                  )}
                >
                  {stepLabels[step.key]}
                </span>
              </div>

              {/* 连接线 */}
              {index < steps.length - 1 && (
                <div
                  className={clsx(
                    'flex-1 h-0.5 mx-2 rounded transition-colors duration-300',
                    progress >= steps[index + 1].range[0]
                      ? 'bg-green-500'
                      : 'bg-neutral-200 dark:bg-neutral-700'
                  )}
                />
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}

export default ProgressHeader;
