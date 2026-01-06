/**
 * LogEntry - 单条日志条目组件
 *
 * input: log (日志对象), isNew (是否新条目)
 * output: 带图标和动画的日志行
 * pos: ProcessingLogPanel 子组件
 */

import { memo } from 'react';
import { Info, CheckCircle, AlertTriangle, XCircle, Terminal } from 'lucide-react';
import clsx from 'clsx';

export interface LogEntryData {
  time: string;
  level: 'info' | 'success' | 'warning' | 'error' | 'debug';
  message: string;
  category?: 'import' | 'match' | 'score' | 'system';
}

interface LogEntryProps {
  log: LogEntryData;
  isNew?: boolean;
}

const levelConfig = {
  info: {
    icon: Info,
    iconClass: 'text-blue-500',
    iconAnimClass: '',
    textClass: 'text-neutral-600 dark:text-neutral-400',
    bgClass: '',
  },
  success: {
    icon: CheckCircle,
    iconClass: 'text-green-500',
    iconAnimClass: 'log-success-icon',
    textClass: 'text-green-600 dark:text-green-400 font-medium',
    bgClass: 'bg-green-50/50 dark:bg-green-900/10',
  },
  warning: {
    icon: AlertTriangle,
    iconClass: 'text-amber-500',
    iconAnimClass: 'log-warning-icon',
    textClass: 'text-amber-600 dark:text-amber-400',
    bgClass: 'bg-amber-50/50 dark:bg-amber-900/10',
  },
  error: {
    icon: XCircle,
    iconClass: 'text-red-500',
    iconAnimClass: 'log-error-icon',
    textClass: 'text-red-600 dark:text-red-400 font-medium',
    bgClass: 'bg-red-50/50 dark:bg-red-900/10',
  },
  debug: {
    icon: Terminal,
    iconClass: 'text-purple-400',
    iconAnimClass: '',
    textClass: 'text-purple-500 dark:text-purple-400 text-xs opacity-70',
    bgClass: '',
  },
};

function formatTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return '--:--:--';
  }
}

export const LogEntry = memo(function LogEntry({ log, isNew }: LogEntryProps) {
  const config = levelConfig[log.level] || levelConfig.info;
  const Icon = config.icon;

  return (
    <div
      className={clsx(
        'flex items-start gap-2 py-1.5 px-3 text-sm font-mono',
        'log-entry-hover rounded mx-1',
        'transition-all duration-150',
        config.bgClass,
        isNew && 'log-entry-new'
      )}
    >
      {/* 时间戳 */}
      <span className="text-neutral-400 dark:text-neutral-500 text-xs shrink-0 w-16 tabular-nums">
        {formatTime(log.time)}
      </span>

      {/* 级别图标 - 带动画 */}
      <span className={clsx('shrink-0', config.iconClass, isNew && config.iconAnimClass)}>
        <Icon className="w-3.5 h-3.5" />
      </span>

      {/* 消息内容 */}
      <span className={clsx('flex-1', config.textClass)}>{log.message}</span>
    </div>
  );
});

export default LogEntry;
