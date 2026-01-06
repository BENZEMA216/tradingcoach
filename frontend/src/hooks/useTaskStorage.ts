/**
 * useTaskStorage - 任务本地存储 Hook
 *
 * input: 任务信息
 * output: 本地存储的任务和操作方法
 * pos: Hook 层 - 使用 localStorage 持久化最近的分析任务
 */
import { useState, useEffect, useCallback } from 'react';

export interface StoredTask {
  taskId: string;
  fileName: string;
  createdAt: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress?: number;
  currentStep?: string;
}

const STORAGE_KEY = 'tradingcoach-current-task';

export function useTaskStorage() {
  const [currentTask, setCurrentTask] = useState<StoredTask | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load task from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const task = JSON.parse(stored) as StoredTask;
        // Only restore if task is still active (pending or running)
        if (task.status === 'pending' || task.status === 'running') {
          setCurrentTask(task);
        } else {
          // Clear completed/failed tasks older than 24 hours
          const createdAt = new Date(task.createdAt).getTime();
          const now = Date.now();
          const hoursSinceCreated = (now - createdAt) / (1000 * 60 * 60);
          if (hoursSinceCreated > 24) {
            localStorage.removeItem(STORAGE_KEY);
          } else {
            setCurrentTask(task);
          }
        }
      }
    } catch {
      // Ignore parse errors
      localStorage.removeItem(STORAGE_KEY);
    }
    setIsLoaded(true);
  }, []);

  // Save task to localStorage
  const saveTask = useCallback((task: StoredTask) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(task));
      setCurrentTask(task);
    } catch {
      // Ignore storage errors
    }
  }, []);

  // Update task status
  const updateTaskStatus = useCallback(
    (status: StoredTask['status'], progress?: number, currentStep?: string) => {
      setCurrentTask((prev) => {
        if (!prev) return null;
        const updated = { ...prev, status, progress, currentStep };
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        } catch {
          // Ignore
        }
        return updated;
      });
    },
    []
  );

  // Clear task
  const clearTask = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore
    }
    setCurrentTask(null);
  }, []);

  // Check if task is active (pending or running)
  const hasActiveTask = currentTask
    ? currentTask.status === 'pending' || currentTask.status === 'running'
    : false;

  return {
    currentTask,
    isLoaded,
    hasActiveTask,
    saveTask,
    updateTaskStatus,
    clearTask,
  };
}
