/**
 * Toast Store - 全局 Toast 通知状态管理
 *
 * input: Toast 添加/移除操作
 * output: Toast 队列和操作方法
 * pos: 全局状态管理 - 管理应用内的 Toast 通知队列
 */
import { create } from 'zustand';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastAction {
  label: string;
  onClick: () => void;
}

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  action?: ToastAction;
  duration?: number; // ms, 0 = no auto-dismiss
  createdAt: number;
}

interface ToastStore {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id' | 'createdAt'>) => string;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

// Generate unique ID
const generateId = () => `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],

  addToast: (toast) => {
    const id = generateId();
    const newToast: Toast = {
      ...toast,
      id,
      createdAt: Date.now(),
      duration: toast.duration ?? 5000, // Default 5 seconds
    };

    set((state) => ({
      toasts: [...state.toasts, newToast],
    }));

    // Auto-dismiss if duration > 0
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }));
      }, newToast.duration);
    }

    return id;
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },

  clearAll: () => {
    set({ toasts: [] });
  },
}));

// Convenience hook for adding toasts
export function useToast() {
  const { addToast, removeToast, clearAll } = useToastStore();

  return {
    success: (title: string, message?: string, action?: ToastAction) =>
      addToast({ type: 'success', title, message, action }),
    error: (title: string, message?: string, action?: ToastAction) =>
      addToast({ type: 'error', title, message, action, duration: 8000 }),
    warning: (title: string, message?: string, action?: ToastAction) =>
      addToast({ type: 'warning', title, message, action }),
    info: (title: string, message?: string, action?: ToastAction) =>
      addToast({ type: 'info', title, message, action }),
    dismiss: removeToast,
    clearAll,
  };
}
