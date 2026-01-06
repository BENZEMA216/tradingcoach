/**
 * Privacy Format Hook
 * input: usePrivacyStore state
 * output: privacy-aware formatting functions
 * pos: Abstraction layer for components to use privacy-aware formatters
 *
 * Once updated, update this header
 */
import { useCallback, useMemo } from 'react';
import { usePrivacyStore } from '@/store/usePrivacyStore';

export function usePrivacyFormat() {
  const { isPrivacyMode, initialCapital, hasSetCapital } = usePrivacyStore();

  // Convert dollar amount to percentage of initial capital
  const toPercentage = useCallback(
    (value: number | null | undefined): number | null => {
      if (value === null || value === undefined || !initialCapital) {
        return null;
      }
      return (value / initialCapital) * 100;
    },
    [initialCapital]
  );

  // Format currency with privacy mode support
  const formatPrivacyCurrency = useCallback(
    (
      value: number | null | undefined,
      options?: { showSign?: boolean; decimals?: number }
    ): string => {
      if (value === null || value === undefined) return '-';

      const decimals = options?.decimals ?? 2;

      if (isPrivacyMode && initialCapital) {
        const pct = (value / initialCapital) * 100;
        const sign = pct >= 0 && options?.showSign ? '+' : '';
        return `${sign}${pct.toFixed(decimals)}%`;
      }

      // Default currency format
      const formatted = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(value);

      if (options?.showSign && value > 0) {
        return `+${formatted}`;
      }
      return formatted;
    },
    [isPrivacyMode, initialCapital]
  );

  // Format P&L with sign (always show + or -)
  const formatPrivacyPnL = useCallback(
    (value: number | null | undefined): string => {
      if (value === null || value === undefined) return '-';

      if (isPrivacyMode && initialCapital) {
        const pct = (value / initialCapital) * 100;
        const sign = pct >= 0 ? '+' : '';
        return `${sign}${pct.toFixed(2)}%`;
      }

      // Default P&L format
      const absValue = Math.abs(value);
      const formatted = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(absValue);

      return value >= 0 ? `+${formatted}` : `-${formatted.replace('$', '')}`;
    },
    [isPrivacyMode, initialCapital]
  );

  // Format number for chart axis (shorter format)
  const formatPrivacyAxis = useCallback(
    (value: number): string => {
      if (isPrivacyMode && initialCapital) {
        const pct = (value / initialCapital) * 100;
        return `${pct.toFixed(1)}%`;
      }

      // Default: use K/M suffix
      if (Math.abs(value) >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      }
      if (Math.abs(value) >= 1000) {
        return `$${(value / 1000).toFixed(0)}K`;
      }
      return `$${value.toFixed(0)}`;
    },
    [isPrivacyMode, initialCapital]
  );

  // Get display label for current mode
  const getModeLabel = useCallback(
    (isZh: boolean): string => {
      if (isPrivacyMode) {
        return isZh ? '资本占比' : '% of Capital';
      }
      return isZh ? '实际金额' : 'Actual Amount';
    },
    [isPrivacyMode]
  );

  // Format initial capital for display
  const formatCapitalDisplay = useCallback((amount: number | null): string => {
    if (!amount) return '-';
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    }
    if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount}`;
  }, []);

  return useMemo(
    () => ({
      isPrivacyMode,
      initialCapital,
      hasSetCapital,
      toPercentage,
      formatPrivacyCurrency,
      formatPrivacyPnL,
      formatPrivacyAxis,
      getModeLabel,
      formatCapitalDisplay,
    }),
    [
      isPrivacyMode,
      initialCapital,
      hasSetCapital,
      toPercentage,
      formatPrivacyCurrency,
      formatPrivacyPnL,
      formatPrivacyAxis,
      getModeLabel,
      formatCapitalDisplay,
    ]
  );
}
