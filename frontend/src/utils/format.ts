/**
 * Format utilities for Trading Coach
 */

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
export const formatHoldingDays = (days: number | null | undefined): string => {
  if (days === null || days === undefined) return '-';
  if (days === 0) return 'Same day';
  if (days === 1) return '1 day';
  return `${days} days`;
};

// Format large numbers
export const formatNumber = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('en-US').format(value);
};

// Translate strategy type
export const translateStrategy = (strategy: string | null): string => {
  if (!strategy) return 'Unclassified';
  const map: Record<string, string> = {
    trend: 'Trend Following',
    mean_reversion: 'Mean Reversion',
    breakout: 'Breakout',
    range: 'Range Trading',
    momentum: 'Momentum',
    unknown: 'Unclassified',
  };
  return map[strategy] || strategy;
};

// Translate direction
export const translateDirection = (direction: string): string => {
  return direction === 'long' ? 'Long' : 'Short';
};
