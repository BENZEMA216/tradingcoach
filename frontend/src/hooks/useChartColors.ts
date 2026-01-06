import { useEffect, useState, useMemo } from 'react';

/**
 * Hook for consistent chart colors across light and dark modes.
 * Uses TradingView-inspired color scheme.
 *
 * Light mode: Tailwind green/red (#22c55e / #ef4444)
 * Dark mode: TradingView teal/coral (#26a69a / #ef5350)
 */
export function useChartColors() {
  const [isDarkMode, setIsDarkMode] = useState(
    typeof document !== 'undefined'
      ? document.documentElement.classList.contains('dark')
      : false
  );

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDarkMode(document.documentElement.classList.contains('dark'));
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class']
    });

    return () => observer.disconnect();
  }, []);

  // Memoize color object to prevent unnecessary re-renders
  const colors = useMemo(() => ({
    // Profit/Loss colors (TradingView style)
    profit: isDarkMode ? '#26a69a' : '#22c55e',
    loss: isDarkMode ? '#ef5350' : '#ef4444',

    // Profit/Loss with transparency for gradients
    profitLight: isDarkMode ? 'rgba(38, 166, 154, 0.3)' : 'rgba(34, 197, 94, 0.3)',
    lossLight: isDarkMode ? 'rgba(239, 83, 80, 0.3)' : 'rgba(239, 68, 68, 0.3)',
    profitFaded: isDarkMode ? 'rgba(38, 166, 154, 0.1)' : 'rgba(34, 197, 94, 0.1)',
    lossFaded: isDarkMode ? 'rgba(239, 83, 80, 0.1)' : 'rgba(239, 68, 68, 0.1)',

    // Primary accent color (blue tones)
    primary: isDarkMode ? '#3b82f6' : '#2563eb',
    primaryLight: isDarkMode ? 'rgba(59, 130, 246, 0.3)' : 'rgba(37, 99, 235, 0.3)',
    primaryFaded: isDarkMode ? 'rgba(59, 130, 246, 0.1)' : 'rgba(37, 99, 235, 0.1)',

    // Secondary accent color (purple/violet)
    secondary: isDarkMode ? '#8b5cf6' : '#7c3aed',
    secondaryLight: isDarkMode ? 'rgba(139, 92, 246, 0.3)' : 'rgba(124, 58, 237, 0.3)',

    // Warning/Neutral color (amber/yellow)
    warning: isDarkMode ? '#f59e0b' : '#d97706',
    warningLight: isDarkMode ? 'rgba(245, 158, 11, 0.3)' : 'rgba(217, 119, 6, 0.3)',

    // Chart grid and axis colors
    grid: isDarkMode ? '#374151' : '#e5e7eb',
    gridLight: isDarkMode ? 'rgba(55, 65, 81, 0.5)' : 'rgba(229, 231, 235, 0.7)',
    text: isDarkMode ? '#9ca3af' : '#6b7280',
    textMuted: isDarkMode ? '#6b7280' : '#9ca3af',
    axis: isDarkMode ? '#4b5563' : '#d1d5db',

    // Background colors
    background: isDarkMode ? '#1a1a1a' : '#ffffff',
    cardBg: isDarkMode ? '#1f2937' : '#ffffff',
    tooltipBg: isDarkMode ? '#1f2937' : '#ffffff',
    tooltipBorder: isDarkMode ? '#374151' : '#e5e7eb',

    // Reference lines
    zeroline: isDarkMode ? '#4b5563' : '#d1d5db',
    benchmark: isDarkMode ? '#6b7280' : '#9ca3af',

    // State
    isDarkMode,
  }), [isDarkMode]);

  return colors;
}

/**
 * Generate gradient definition for SVG charts
 * Use inside <defs> element of Recharts
 */
export function createGradientDef(
  id: string,
  topColor: string,
  bottomColor: string,
  direction: 'vertical' | 'horizontal' = 'vertical'
) {
  return {
    id,
    x1: '0',
    y1: direction === 'vertical' ? '0' : '0',
    x2: direction === 'vertical' ? '0' : '1',
    y2: direction === 'vertical' ? '1' : '0',
    stops: [
      { offset: '0%', color: topColor, opacity: 1 },
      { offset: '100%', color: bottomColor, opacity: 0.1 },
    ],
  };
}

export type ChartColors = ReturnType<typeof useChartColors>;
