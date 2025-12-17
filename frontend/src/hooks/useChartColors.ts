import { useEffect, useState } from 'react';

/**
 * Hook for consistent chart colors across light and dark modes.
 * Uses TradingView color scheme for dark mode.
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

  return {
    // Profit/Loss colors
    profit: isDarkMode ? '#26a69a' : '#22c55e',
    loss: isDarkMode ? '#ef5350' : '#ef4444',

    // Chart grid and axis colors
    grid: isDarkMode ? '#374151' : '#e5e7eb',
    text: isDarkMode ? '#9ca3af' : '#6b7280',
    axis: isDarkMode ? '#4b5563' : '#d1d5db',

    // Background colors
    background: isDarkMode ? '#1a1a1a' : '#ffffff',
    tooltipBg: isDarkMode ? '#1f2937' : '#ffffff',
    tooltipBorder: isDarkMode ? '#374151' : '#e5e7eb',

    // State
    isDarkMode,
  };
}

export type ChartColors = ReturnType<typeof useChartColors>;
