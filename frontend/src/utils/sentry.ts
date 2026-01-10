/**
 * Sentry 错误追踪配置
 *
 * 使用方法：
 * 1. 在 https://sentry.io 创建项目
 * 2. 获取 DSN 并设置环境变量 VITE_SENTRY_DSN
 * 3. 应用会自动捕获并上报错误
 */

import * as Sentry from '@sentry/react';

export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;

  // 只在有 DSN 配置时初始化
  if (!dsn) {
    console.log('[Sentry] DSN not configured, error tracking disabled');
    return;
  }

  Sentry.init({
    dsn,
    environment: import.meta.env.VITE_ENV || 'development',

    // 采样率：生产环境 100%，开发环境 10%
    tracesSampleRate: import.meta.env.PROD ? 1.0 : 0.1,

    // 只在生产环境启用 replay
    replaysSessionSampleRate: import.meta.env.PROD ? 0.1 : 0,
    replaysOnErrorSampleRate: import.meta.env.PROD ? 1.0 : 0,

    // 过滤敏感信息
    beforeSend(event) {
      // 移除可能的敏感数据
      if (event.request?.cookies) {
        delete event.request.cookies;
      }
      return event;
    },

    // 忽略常见的无害错误
    ignoreErrors: [
      'ResizeObserver loop limit exceeded',
      'ResizeObserver loop completed with undelivered notifications',
      'Non-Error promise rejection captured',
    ],
  });

  console.log('[Sentry] Error tracking initialized');
}

// 手动报告错误
export function captureError(error: Error, context?: Record<string, unknown>) {
  Sentry.captureException(error, { extra: context });
}

// 手动报告消息
export function captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info') {
  Sentry.captureMessage(message, level);
}

// 设置用户信息（可选）
export function setUser(user: { id?: string; email?: string; username?: string } | null) {
  Sentry.setUser(user);
}

export { Sentry };
