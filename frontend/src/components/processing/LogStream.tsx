/**
 * LogStream - 日志流组件
 *
 * input: logs (日志数组), filter (筛选器), isProcessing (是否处理中)
 * output: 可滚动的日志列表，支持自动滚动、筛选、加载态
 * pos: ProcessingLogPanel 子组件
 */

import { useRef, useEffect, useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowDown, Filter, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { LogEntry, type LogEntryData } from './LogEntry';

type FilterType = 'all' | 'import' | 'match' | 'score' | 'error';

interface LogStreamProps {
  logs: LogEntryData[];
  className?: string;
  isProcessing?: boolean;
}

const filterButtons: { key: FilterType; labelKey: string; fallback: string }[] = [
  { key: 'all', labelKey: 'processingLog.filters.all', fallback: '全部' },
  { key: 'import', labelKey: 'processingLog.filters.import', fallback: '导入' },
  { key: 'match', labelKey: 'processingLog.filters.match', fallback: '配对' },
  { key: 'score', labelKey: 'processingLog.filters.score', fallback: '评分' },
  { key: 'error', labelKey: 'processingLog.filters.errors', fallback: '错误' },
];

export function LogStream({ logs, className, isProcessing = false }: LogStreamProps) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState<FilterType>('all');
  const [prevLogCount, setPrevLogCount] = useState(0);

  // 筛选日志
  const filteredLogs = useMemo(() => {
    if (filter === 'all') return logs;
    if (filter === 'error') return logs.filter((l) => l.level === 'error');
    return logs.filter((l) => l.category === filter);
  }, [logs, filter]);

  // 检测新增的日志索引
  const newLogStartIndex = useMemo(() => {
    if (filteredLogs.length > prevLogCount) {
      return prevLogCount;
    }
    return -1;
  }, [filteredLogs.length, prevLogCount]);

  // 更新日志计数
  useEffect(() => {
    setPrevLogCount(filteredLogs.length);
  }, [filteredLogs.length]);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScroll]);

  // 检测用户手动滚动
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    setAutoScroll(isAtBottom);
  };

  // 滚动到底部
  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
      setAutoScroll(true);
    }
  };

  return (
    <div className={clsx('flex flex-col relative', className)}>
      {/* 筛选器 */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800">
        <Filter className="w-4 h-4 text-neutral-400" />
        <div className="flex gap-1">
          {filterButtons.map((btn) => (
            <button
              key={btn.key}
              onClick={() => setFilter(btn.key)}
              className={clsx(
                'px-2 py-1 text-xs rounded transition-colors',
                filter === btn.key
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                  : 'text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800'
              )}
            >
              {t(btn.labelKey, btn.fallback)}
            </button>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-2">
          {isProcessing && (
            <span className="loading-dots text-blue-500">
              <span></span>
              <span></span>
              <span></span>
            </span>
          )}
          <span className="text-xs text-neutral-400 tabular-nums">
            {filteredLogs.length} {t('processingLog.entries', '条')}
          </span>
        </div>
      </div>

      {/* 日志列表 - 带扫描线效果 */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className={clsx(
          'flex-1 overflow-y-auto min-h-0 log-container',
          'bg-neutral-50 dark:bg-neutral-900/50',
          isProcessing && 'log-container-scanning'
        )}
        style={{ maxHeight: '50vh', minHeight: '200px' }}
      >
        {filteredLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-neutral-400 gap-2">
            {isProcessing ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                <span className="text-sm">{t('processingLog.waitingLogs', '等待日志...')}</span>
              </>
            ) : (
              <span>{t('processingLog.noLogs', '暂无日志')}</span>
            )}
          </div>
        ) : (
          <div className="py-2">
            {filteredLogs.map((log, index) => (
              <LogEntry
                key={`${log.time}-${index}`}
                log={log}
                isNew={index >= newLogStartIndex && newLogStartIndex >= 0}
              />
            ))}
            {/* 处理中时显示等待指示器 */}
            {isProcessing && (
              <div className="flex items-center gap-2 py-2 px-3 text-sm text-blue-500">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span className="typing-cursor">{t('processingLog.processing', '处理中')}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 滚动到底部按钮 */}
      {!autoScroll && (
        <button
          onClick={scrollToBottom}
          className={clsx(
            'absolute bottom-4 right-4 p-2 rounded-full shadow-lg',
            'bg-blue-500 text-white hover:bg-blue-600',
            'transition-all duration-200 animate-bounce'
          )}
        >
          <ArrowDown className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

export default LogStream;
