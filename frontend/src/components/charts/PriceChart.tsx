import { useEffect, useRef, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  createChart,
  CrosshairMode,
  ColorType,
  CandlestickSeries,
  LineSeries,
  createSeriesMarkers,
} from 'lightweight-charts';
import type {
  IChartApi,
  ISeriesApi,
  CandlestickData,
  LineData,
  Time,
  SeriesMarker,
} from 'lightweight-charts';
import type { PositionMarketData } from '@/types';

interface PriceChartProps {
  data: PositionMarketData;
  height?: number;
  showIndicators?: boolean;
  bare?: boolean;
}

// Color constants
const COLORS = {
  up: '#22c55e',
  down: '#ef4444',
  ma20: '#3b82f6',
  ma50: '#f59e0b',
  bbUpper: '#8b5cf6',
  bbLower: '#8b5cf6',
  bbFill: 'rgba(139, 92, 246, 0.1)',
  rsiLine: '#06b6d4',
  entryMarker: '#22c55e',
  exitMarker: '#ef4444',
  maeLevel: '#ef4444',
  mfeLevel: '#22c55e',
};

export function PriceChart({ data, height = 400, showIndicators = true, bare = false }: PriceChartProps) {
  const { t } = useTranslation();
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  // Track dark mode with state so chart updates when theme changes
  const [isDarkMode, setIsDarkMode] = useState(
    typeof document !== 'undefined'
      ? document.documentElement.classList.contains('dark')
      : false
  );

  // Listen for dark mode changes
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

  // Update chart colors when dark mode changes
  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.applyOptions({
        layout: {
          textColor: isDarkMode ? '#9ca3af' : '#374151',
        },
        grid: {
          vertLines: { color: isDarkMode ? '#374151' : '#e5e7eb' },
          horzLines: { color: isDarkMode ? '#374151' : '#e5e7eb' },
        },
        crosshair: {
          vertLine: {
            labelBackgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
          },
          horzLine: {
            labelBackgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
          },
        },
        rightPriceScale: {
          borderColor: isDarkMode ? '#374151' : '#e5e7eb',
        },
        timeScale: {
          borderColor: isDarkMode ? '#374151' : '#e5e7eb',
        },
      });
    }
  }, [isDarkMode]);

  // Transform data to Lightweight Charts format
  const chartData = useMemo(() => {
    if (!data?.candles?.length) return null;

    const candles: CandlestickData<Time>[] = data.candles.map((c) => ({
      time: c.date as Time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    // Extract indicator data
    const ma20Data: LineData<Time>[] = [];
    const ma50Data: LineData<Time>[] = [];
    const bbUpperData: LineData<Time>[] = [];
    const bbLowerData: LineData<Time>[] = [];
    const rsiData: LineData<Time>[] = [];

    data.candles.forEach((c) => {
      if (c.ma_20 !== null && c.ma_20 !== undefined) {
        ma20Data.push({ time: c.date as Time, value: c.ma_20 });
      }
      if (c.ma_50 !== null && c.ma_50 !== undefined) {
        ma50Data.push({ time: c.date as Time, value: c.ma_50 });
      }
      if (c.bb_upper !== null && c.bb_upper !== undefined) {
        bbUpperData.push({ time: c.date as Time, value: c.bb_upper });
      }
      if (c.bb_lower !== null && c.bb_lower !== undefined) {
        bbLowerData.push({ time: c.date as Time, value: c.bb_lower });
      }
      if (c.rsi_14 !== null && c.rsi_14 !== undefined) {
        rsiData.push({ time: c.date as Time, value: c.rsi_14 });
      }
    });

    return { candles, ma20Data, ma50Data, bbUpperData, bbLowerData, rsiData };
  }, [data]);

  useEffect(() => {
    if (!chartContainerRef.current || !chartData) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: isDarkMode ? '#9ca3af' : '#374151',
      },
      grid: {
        vertLines: { color: isDarkMode ? '#374151' : '#e5e7eb' },
        horzLines: { color: isDarkMode ? '#374151' : '#e5e7eb' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          labelBackgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
        },
        horzLine: {
          labelBackgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
        },
      },
      rightPriceScale: {
        borderColor: isDarkMode ? '#374151' : '#e5e7eb',
      },
      timeScale: {
        borderColor: isDarkMode ? '#374151' : '#e5e7eb',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: COLORS.up,
      downColor: COLORS.down,
      borderVisible: false,
      wickUpColor: COLORS.up,
      wickDownColor: COLORS.down,
    });
    candlestickSeriesRef.current = candlestickSeries as ISeriesApi<'Candlestick'>;
    candlestickSeries.setData(chartData.candles);

    // Add entry price line
    if (data.entry_marker) {
      candlestickSeries.createPriceLine({
        price: data.entry_marker.price,
        color: COLORS.entryMarker,
        lineWidth: 2,
        lineStyle: 0, // Solid
        axisLabelVisible: true,
        title: t('chart.entry'),
      });
    }

    // Add exit price line
    if (data.exit_marker) {
      candlestickSeries.createPriceLine({
        price: data.exit_marker.price,
        color: COLORS.exitMarker,
        lineWidth: 2,
        lineStyle: 0, // Solid
        axisLabelVisible: true,
        title: t('chart.exit'),
      });
    }

    // Add MAE/MFE price lines
    if (data.mae_level !== null) {
      candlestickSeries.createPriceLine({
        price: data.mae_level,
        color: COLORS.maeLevel,
        lineWidth: 1,
        lineStyle: 2, // Dashed
        axisLabelVisible: true,
        title: t('chart.mae'),
      });
    }

    if (data.mfe_level !== null) {
      candlestickSeries.createPriceLine({
        price: data.mfe_level,
        color: COLORS.mfeLevel,
        lineWidth: 1,
        lineStyle: 2, // Dashed
        axisLabelVisible: true,
        title: t('chart.mfe'),
      });
    }

    // Add entry/exit markers on candles
    const markers: SeriesMarker<Time>[] = [];

    // Buy marker - green arrow below candle
    if (data.entry_marker?.date) {
      markers.push({
        time: data.entry_marker.date as Time,
        position: 'belowBar',
        color: COLORS.entryMarker,
        shape: 'arrowUp',
        text: t('chart.buy'),
      });
    }

    // Sell marker - red arrow above candle
    if (data.exit_marker?.date) {
      markers.push({
        time: data.exit_marker.date as Time,
        position: 'aboveBar',
        color: COLORS.exitMarker,
        shape: 'arrowDown',
        text: t('chart.sell'),
      });
    }

    if (markers.length > 0) {
      createSeriesMarkers(candlestickSeries, markers);
    }

    // Add technical indicators if enabled
    if (showIndicators) {
      // MA20 line
      if (chartData.ma20Data.length > 0) {
        const ma20Series = chart.addSeries(LineSeries, {
          color: COLORS.ma20,
          lineWidth: 1,
          title: 'MA20',
          priceLineVisible: false,
          lastValueVisible: false,
        });
        ma20Series.setData(chartData.ma20Data);
      }

      // MA50 line
      if (chartData.ma50Data.length > 0) {
        const ma50Series = chart.addSeries(LineSeries, {
          color: COLORS.ma50,
          lineWidth: 1,
          title: 'MA50',
          priceLineVisible: false,
          lastValueVisible: false,
        });
        ma50Series.setData(chartData.ma50Data);
      }

      // Bollinger Bands
      if (chartData.bbUpperData.length > 0) {
        const bbUpperSeries = chart.addSeries(LineSeries, {
          color: COLORS.bbUpper,
          lineWidth: 1,
          lineStyle: 2,
          title: 'BB Upper',
          priceLineVisible: false,
          lastValueVisible: false,
        });
        bbUpperSeries.setData(chartData.bbUpperData);
      }

      if (chartData.bbLowerData.length > 0) {
        const bbLowerSeries = chart.addSeries(LineSeries, {
          color: COLORS.bbLower,
          lineWidth: 1,
          lineStyle: 2,
          title: 'BB Lower',
          priceLineVisible: false,
          lastValueVisible: false,
        });
        bbLowerSeries.setData(chartData.bbLowerData);
      }
    }

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartRef.current = null;
      candlestickSeriesRef.current = null;
    };
  }, [chartData, data, height, isDarkMode, showIndicators, t]);

  if (!data?.candles?.length) {
    if (bare) {
      return (
        <div
          className="flex items-center justify-center text-gray-500 dark:text-gray-400"
          style={{ height: height }}
        >
          {data?.message || t('chart.noData')}
        </div>
      );
    }
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('chart.priceChart')}
        </h3>
        <div
          className="flex items-center justify-center text-gray-500 dark:text-gray-400"
          style={{ height: height }}
        >
          {data?.message || t('chart.noData')}
        </div>
      </div>
    );
  }

  const chartContent = (
    <div ref={chartContainerRef} style={{ height: height }} />
  );

  const legend = showIndicators && (
    <div className="flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
      <span className="flex items-center gap-1">
        <span
          className="w-3 h-0.5 inline-block"
          style={{ backgroundColor: COLORS.ma20 }}
        />
        MA20
      </span>
      <span className="flex items-center gap-1">
        <span
          className="w-3 h-0.5 inline-block"
          style={{ backgroundColor: COLORS.ma50 }}
        />
        MA50
      </span>
      <span className="flex items-center gap-1">
        <span
          className="w-3 h-0.5 inline-block border-b border-dashed"
          style={{ borderColor: COLORS.bbUpper }}
        />
        {t('chart.bollingerBands')}
      </span>
    </div>
  );

  if (bare) {
    return (
      <div>
        {showIndicators && (
          <div className="flex items-center justify-end mb-4">
            {legend}
          </div>
        )}
        {chartContent}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t('chart.priceChart')} - {data.symbol}
        </h3>
        {legend}
      </div>
      {chartContent}
    </div>
  );
}
