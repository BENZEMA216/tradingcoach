/**
 * TickingLogStream - 均匀展示的日志流
 *
 * input: 日志数组
 * output: 均匀节奏展示的日志列表
 * pos: 组件 - 通过队列消费实现均匀的日志展示动画
 */
import { useState, useEffect, useRef, useMemo } from 'react';
import { CheckCircle, AlertCircle, Info, Loader2, Terminal } from 'lucide-react';

interface LogEntry {
  time: string;
  level: 'info' | 'success' | 'warning' | 'error';
  message: string;
  category?: string;
}

interface TickingLogStreamProps {
  logs: LogEntry[];
  maxVisible?: number;
}

export function TickingLogStream({ logs, maxVisible = 12 }: TickingLogStreamProps) {
  const [displayedLogs, setDisplayedLogs] = useState<LogEntry[]>([]);
  const queueRef = useRef<LogEntry[]>([]);
  const lastProcessedIndex = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Enqueue new logs
  useEffect(() => {
    if (logs.length > lastProcessedIndex.current) {
      const newLogs = logs.slice(lastProcessedIndex.current);
      queueRef.current.push(...newLogs);
      lastProcessedIndex.current = logs.length;
    }
  }, [logs]);

  // Consume queue at dynamic rate
  useEffect(() => {
    const consume = () => {
      if (queueRef.current.length > 0) {
        const nextLog = queueRef.current.shift()!;
        setDisplayedLogs((prev) => {
          const updated = [...prev, nextLog];
          // Keep only maxVisible logs
          return updated.slice(-maxVisible);
        });
      }
    };

    // Dynamic interval based on queue length
    const getInterval = () => {
      const len = queueRef.current.length;
      if (len > 30) return 50;   // Very backed up, speed up
      if (len > 20) return 80;
      if (len > 10) return 120;
      if (len > 5) return 180;
      return 280;                 // Few items, slow down
    };

    const timer = setInterval(consume, getInterval());
    return () => clearInterval(timer);
  }, [displayedLogs.length, maxVisible]);

  // Auto scroll to bottom
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [displayedLogs]);

  const getIcon = (level: string) => {
    switch (level) {
      case 'success':
        return <CheckCircle className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />;
      case 'warning':
        return <AlertCircle className="w-3.5 h-3.5 text-yellow-500 flex-shrink-0" />;
      case 'error':
        return <AlertCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />;
      default:
        return <Info className="w-3.5 h-3.5 text-blue-400/60 flex-shrink-0" />;
    }
  };

  const getLevelStyle = (level: string) => {
    switch (level) {
      case 'success':
        return 'text-green-400';
      case 'warning':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-white/60';
    }
  };

  const formatTime = (timeStr: string) => {
    try {
      const date = new Date(timeStr);
      return date.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return '--:--:--';
    }
  };

  // Queue indicator
  const queueLength = queueRef.current.length;

  return (
    <div className="relative">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 px-1">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-white/40" />
          <span className="text-xs font-mono text-white/40 uppercase tracking-wider">
            Processing Log
          </span>
        </div>
        {queueLength > 0 && (
          <div className="flex items-center space-x-2">
            <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
            <span className="text-xs font-mono text-blue-400">
              +{queueLength} pending
            </span>
          </div>
        )}
      </div>

      {/* Log Container */}
      <div
        ref={containerRef}
        className="h-64 overflow-y-auto bg-black/40 rounded-lg border border-white/10 p-3 space-y-1 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
      >
        {displayedLogs.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="w-6 h-6 text-white/20 animate-spin mx-auto mb-2" />
              <p className="text-xs font-mono text-white/30">Waiting for logs...</p>
            </div>
          </div>
        ) : (
          displayedLogs.map((log, index) => (
            <div
              key={`${log.time}-${index}`}
              className="flex items-start space-x-2 py-1 px-2 rounded hover:bg-white/5 transition-colors animate-fade-in"
              style={{
                animationDelay: `${index * 30}ms`,
              }}
            >
              {getIcon(log.level)}
              <span className="text-xs font-mono text-white/30 flex-shrink-0">
                {formatTime(log.time)}
              </span>
              <span className={`text-xs font-mono ${getLevelStyle(log.level)} break-all`}>
                {log.message}
              </span>
            </div>
          ))
        )}
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-black/60 to-transparent pointer-events-none rounded-b-lg" />
    </div>
  );
}
