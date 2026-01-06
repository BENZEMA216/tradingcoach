/**
 * Format utilities for Trading Coach
 */

import { usePrivacyStore } from '@/store/usePrivacyStore';

// Format number as currency
export const formatCurrency = (value: number | null | undefined, currency = 'USD'): string => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

// Format number as percentage
export const formatPercent = (value: number | null | undefined, decimals = 2): string => {
  if (value === null || value === undefined) return '-';
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

// Format number with sign
export const formatPnL = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  const formatted = formatCurrency(Math.abs(value));
  return value >= 0 ? `+${formatted}` : `-${formatted.replace('$', '')}`;
};

// Format date
export const formatDate = (dateStr: string | null | undefined): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
};

// Format date with time
export const formatDateTime = (dateStr: string | null | undefined): string => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// Get color class for P&L
export const getPnLColorClass = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return 'text-gray-500';
  return value > 0 ? 'text-profit' : value < 0 ? 'text-loss' : 'text-gray-500';
};

// Get grade badge class
export const getGradeBadgeClass = (grade: string | null | undefined): string => {
  if (!grade) return 'bg-gray-100 text-gray-800';
  const baseGrade = grade.charAt(0).toUpperCase();
  switch (baseGrade) {
    case 'A': return 'grade-a';
    case 'B': return 'grade-b';
    case 'C': return 'grade-c';
    case 'D': return 'grade-d';
    case 'F': return 'grade-f';
    default: return 'bg-gray-100 text-gray-800';
  }
};

// Format holding days
export const formatHoldingDays = (days: number | null | undefined, isZh: boolean = false): string => {
  if (days === null || days === undefined) return '-';
  if (isZh) {
    if (days === 0) return '当天';
    return `${days}天`;
  }
  if (days === 0) return 'Same day';
  if (days === 1) return '1 day';
  return `${days} days`;
};

// Format large numbers
export const formatNumber = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('en-US').format(value);
};

// Note: Strategy and direction translations are now handled via i18n
// Use t('strategy.{key}') and t('direction.{key}') in components

// ==================== Privacy Mode Formatters ====================
// For use in non-React contexts (chart callbacks, tooltips, etc.)
// In React components, prefer using the usePrivacyFormat hook

/**
 * Get privacy-aware formatters for use in non-React contexts
 * Call this function inside callbacks to get current privacy state
 */
export function getPrivacyAwareFormatters() {
  const { isPrivacyMode, initialCapital } = usePrivacyStore.getState();

  const formatCurrencyPrivate = (
    value: number | null | undefined,
    options?: { showSign?: boolean }
  ): string => {
    if (value === null || value === undefined) return '-';

    if (isPrivacyMode && initialCapital) {
      const pct = (value / initialCapital) * 100;
      const sign = pct >= 0 && options?.showSign ? '+' : '';
      return `${sign}${pct.toFixed(2)}%`;
    }

    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);

    if (options?.showSign && value > 0) {
      return `+${formatted}`;
    }
    return formatted;
  };

  const formatPnLPrivate = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '-';

    if (isPrivacyMode && initialCapital) {
      const pct = (value / initialCapital) * 100;
      return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`;
    }

    const absValue = Math.abs(value);
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absValue);

    return value >= 0 ? `+${formatted}` : `-${formatted.replace('$', '')}`;
  };

  const formatAxisPrivate = (value: number): string => {
    if (isPrivacyMode && initialCapital) {
      const pct = (value / initialCapital) * 100;
      return `${pct.toFixed(1)}%`;
    }

    if (Math.abs(value) >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (Math.abs(value) >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  return {
    formatCurrency: formatCurrencyPrivate,
    formatPnL: formatPnLPrivate,
    formatAxis: formatAxisPrivate,
    isPrivacyMode,
    initialCapital,
  };
}
