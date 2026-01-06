/**
 * useResponsiveChart - Responsive chart configuration hook
 *
 * input: Container ref, chart layout options
 * output: Dynamic chart configuration (margin, fontSize, yAxisWidth, showLabels)
 * pos: Hook layer - provides responsive chart sizing based on container width
 */

import { useState, useEffect, useRef } from 'react';
import type { RefObject } from 'react';

export interface ResponsiveChartConfig {
  fontSize: number;
  margin: { top: number; right: number; left: number; bottom: number };
  yAxisWidth: number;
  showLabels: boolean;
  containerWidth: number;
  breakpoint: 'sm' | 'md' | 'lg';
  /** True when container dimensions have been measured */
  isReady: boolean;
}

interface UseResponsiveChartOptions {
  /** Chart layout: 'horizontal' for horizontal bars, 'vertical' for vertical bars */
  layout?: 'horizontal' | 'vertical';
  /** Base margins to scale from */
  baseMargin?: { top: number; right: number; left: number; bottom: number };
  /** Base Y-axis width */
  baseYAxisWidth?: number;
}

// Breakpoint thresholds (in pixels)
const BREAKPOINTS = {
  sm: 400,  // Small: hide labels, reduce font
  md: 550,  // Medium: show labels, standard font
  lg: 700,  // Large: full display
};

// Configuration presets for horizontal bar charts
const HORIZONTAL_CONFIG = {
  sm: {
    fontSize: 9,
    margin: { top: 10, right: 10, left: 75, bottom: 5 },
    yAxisWidth: 70,
    showLabels: false,
  },
  md: {
    fontSize: 10,
    margin: { top: 10, right: 55, left: 85, bottom: 5 },
    yAxisWidth: 80,
    showLabels: true,
  },
  lg: {
    fontSize: 11,
    margin: { top: 10, right: 70, left: 100, bottom: 5 },
    yAxisWidth: 90,
    showLabels: true,
  },
};

// Configuration presets for vertical bar charts
const VERTICAL_CONFIG = {
  sm: {
    fontSize: 9,
    margin: { top: 10, right: 10, left: 0, bottom: 5 },
    yAxisWidth: 40,
    showLabels: true,
  },
  md: {
    fontSize: 10,
    margin: { top: 10, right: 15, left: 0, bottom: 5 },
    yAxisWidth: 50,
    showLabels: true,
  },
  lg: {
    fontSize: 11,
    margin: { top: 10, right: 20, left: 0, bottom: 5 },
    yAxisWidth: 60,
    showLabels: true,
  },
};

/**
 * Hook to get responsive chart configuration based on container width.
 * Uses ResizeObserver to track container size changes.
 *
 * @param containerRef - Reference to the chart container element
 * @param options - Configuration options
 * @returns Responsive chart configuration
 *
 * @example
 * ```tsx
 * const containerRef = useRef<HTMLDivElement>(null);
 * const chartConfig = useResponsiveChart(containerRef, { layout: 'horizontal' });
 *
 * return (
 *   <div ref={containerRef}>
 *     <BarChart margin={chartConfig.margin}>
 *       <YAxis width={chartConfig.yAxisWidth} tick={{ fontSize: chartConfig.fontSize }} />
 *       {chartConfig.showLabels && <LabelList />}
 *     </BarChart>
 *   </div>
 * );
 * ```
 */
export function useResponsiveChart(
  containerRef: RefObject<HTMLDivElement | null>,
  options: UseResponsiveChartOptions = {}
): ResponsiveChartConfig {
  const { layout = 'horizontal' } = options;

  const [config, setConfig] = useState<ResponsiveChartConfig>(() => {
    const presets = layout === 'horizontal' ? HORIZONTAL_CONFIG : VERTICAL_CONFIG;
    return {
      ...presets.lg,
      containerWidth: 0,
      breakpoint: 'lg',
      isReady: false,
    };
  });

  // Track if we've done initial measurement
  const initializedRef = useRef(false);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    const presets = layout === 'horizontal' ? HORIZONTAL_CONFIG : VERTICAL_CONFIG;

    const updateConfig = (width: number) => {
      let breakpoint: 'sm' | 'md' | 'lg';

      if (width < BREAKPOINTS.sm) {
        breakpoint = 'sm';
      } else if (width < BREAKPOINTS.md) {
        breakpoint = 'md';
      } else {
        breakpoint = 'lg';
      }

      const preset = presets[breakpoint];

      setConfig({
        ...preset,
        containerWidth: width,
        breakpoint,
        isReady: true,
      });
    };

    // Initial measurement
    if (!initializedRef.current) {
      const initialWidth = element.clientWidth;
      if (initialWidth > 0) {
        updateConfig(initialWidth);
        initializedRef.current = true;
      }
    }

    // Set up ResizeObserver for dynamic updates
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const width = entry.contentRect.width;
        if (width > 0) {
          updateConfig(width);
        }
      }
    });

    resizeObserver.observe(element);

    return () => {
      resizeObserver.disconnect();
    };
  }, [containerRef, layout]);

  return config;
}

/**
 * Get static responsive config without using a hook.
 * Useful for SSR or when you have the width value already.
 *
 * @param width - Container width in pixels
 * @param layout - Chart layout type
 * @returns Chart configuration for the given width
 */
export function getResponsiveChartConfig(
  width: number,
  layout: 'horizontal' | 'vertical' = 'horizontal'
): ResponsiveChartConfig {
  const presets = layout === 'horizontal' ? HORIZONTAL_CONFIG : VERTICAL_CONFIG;

  let breakpoint: 'sm' | 'md' | 'lg';

  if (width < BREAKPOINTS.sm) {
    breakpoint = 'sm';
  } else if (width < BREAKPOINTS.md) {
    breakpoint = 'md';
  } else {
    breakpoint = 'lg';
  }

  return {
    ...presets[breakpoint],
    containerWidth: width,
    breakpoint,
    isReady: true,
  };
}

export { BREAKPOINTS, HORIZONTAL_CONFIG, VERTICAL_CONFIG };
