/**
 * useTaskStorage - 任务本地存储 Hook
 *
 * input: 任务信息
 * output: 本地存储的任务和操作方法
 * pos: Hook 层 - 使用 localStorage 持久化最近的分析任务
 */
import { useState, useCallback } from 'react';

export interface StoredTask {
  taskId: string;
  fileName: string;
  createdAt: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress?: number;
  currentStep?: string;
}

const STORAGE_KEY = 'tradingcoach-current-task';

function loadStoredTask(): StoredTask | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;

    const task = JSON.parse(stored) as StoredTask;
    if (task.status === 'pending' || task.status === 'running') {
      return task;
    }

    const createdAt = new Date(task.createdAt).getTime();
    const hoursSinceCreated = (Date.now() - createdAt) / (1000 * 60 * 60);
    if (hoursSinceCreated > 24) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }

    return task;
  } catch {
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function useTaskStorage() {
  const [currentTask, setCurrentTask] = useState<StoredTask | null>(() => loadStoredTask());

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
        if (
          prev.status === status &&
          prev.progress === progress &&
          prev.currentStep === currentStep
        ) {
          return prev;
        }
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
    isLoaded: true,
    hasActiveTask,
    saveTask,
    updateTaskStatus,
    clearTask,
  };
}
