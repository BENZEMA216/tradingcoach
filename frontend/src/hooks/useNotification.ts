/**
 * useNotification - 浏览器通知 Hook
 *
 * input: 通知标题和选项
 * output: 通知权限状态和发送方法
 * pos: Hook 层 - 封装 Web Notifications API
 */
import { useState, useEffect, useCallback } from 'react';

interface UseNotificationOptions {
  onPermissionChange?: (permission: NotificationPermission) => void;
}

interface NotificationOptions {
  body?: string;
  icon?: string;
  tag?: string;
  requireInteraction?: boolean;
  onClick?: () => void;
}

export function useNotification(options: UseNotificationOptions = {}) {
  const [permission, setPermission] = useState<NotificationPermission>('default');
  const [isSupported, setIsSupported] = useState(false);

  // Check support and current permission on mount
  useEffect(() => {
    const supported = 'Notification' in window;
    setIsSupported(supported);

    if (supported) {
      setPermission(Notification.permission);
    }
  }, []);

  // Request permission
  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (!isSupported) {
      console.warn('Notifications are not supported in this browser');
      return false;
    }

    if (permission === 'granted') {
      return true;
    }

    if (permission === 'denied') {
      console.warn('Notification permission was previously denied');
      return false;
    }

    try {
      const result = await Notification.requestPermission();
      setPermission(result);
      options.onPermissionChange?.(result);
      return result === 'granted';
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }, [isSupported, permission, options]);

  // Send notification
  const sendNotification = useCallback(
    (title: string, notificationOptions: NotificationOptions = {}) => {
      if (!isSupported) {
        console.warn('Notifications are not supported');
        return null;
      }

      if (permission !== 'granted') {
        console.warn('Notification permission not granted');
        return null;
      }

      try {
        const notification = new Notification(title, {
          body: notificationOptions.body,
          icon: notificationOptions.icon || '/favicon.ico',
          tag: notificationOptions.tag,
          requireInteraction: notificationOptions.requireInteraction,
        });

        if (notificationOptions.onClick) {
          notification.onclick = () => {
            window.focus();
            notificationOptions.onClick?.();
            notification.close();
          };
        }

        return notification;
      } catch (error) {
        console.error('Error sending notification:', error);
        return null;
      }
    },
    [isSupported, permission]
  );

  return {
    isSupported,
    permission,
    isGranted: permission === 'granted',
    isDenied: permission === 'denied',
    requestPermission,
    sendNotification,
  };
}

// Preference storage key
const NOTIFICATION_PREF_KEY = 'tradingcoach-notification-pref';

// Helper to get/set notification preference
export function getNotificationPreference(): boolean {
  try {
    return localStorage.getItem(NOTIFICATION_PREF_KEY) === 'true';
  } catch {
    return false;
  }
}

export function setNotificationPreference(enabled: boolean): void {
  try {
    localStorage.setItem(NOTIFICATION_PREF_KEY, String(enabled));
  } catch {
    // Ignore localStorage errors
  }
}
