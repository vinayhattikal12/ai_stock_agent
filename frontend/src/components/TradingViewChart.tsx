import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData, HistogramData } from 'lightweight-charts';
import { Candle, TradeLevels } from '../types';

interface TradingViewChartProps {
  candles: Candle[];
  levels?: TradeLevels;
  isDark: boolean;
  timeframe: string;
  setTimeframe: (tf: string) => void;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({
  candles,
  levels,
  isDark,
  timeframe,
  setTimeframe
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current || !candles || candles.length === 0) return;

    // Clean up previous instance
    if (chartRef.current) {
      try {
        chartRef.current.remove();
      } catch (e) {
        console.error('Error removing previous chart:', e);
      }
      chartRef.current = null;
    }

    const container = chartContainerRef.current;
    const isDarkTheme = isDark;

    try {
      const chart = createChart(container, {
        width: container.clientWidth || 800,
        height: 440,
        layout: {
          background: { color: isDarkTheme ? '#12141C' : '#FFFFFF' },
          textColor: isDarkTheme ? '#94A3B8' : '#64748B',
          fontFamily: 'Inter, sans-serif',
        },
        grid: {
          vertLines: { color: isDarkTheme ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)' },
          horzLines: { color: isDarkTheme ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)' },
        },
        crosshair: {
          vertLine: {
            color: isDarkTheme ? '#475569' : '#CBD5E1',
            width: 1,
            style: 3,
          },
          horzLine: {
            color: isDarkTheme ? '#475569' : '#CBD5E1',
            width: 1,
            style: 3,
          },
        },
        rightPriceScale: {
          borderColor: isDarkTheme ? '#222738' : '#E2E8F0',
          scaleMargins: {
            top: 0.1,
            bottom: 0.2,
          },
        },
        timeScale: {
          borderColor: isDarkTheme ? '#222738' : '#E2E8F0',
          timeVisible: true,
          secondsVisible: false,
        },
      });

      chartRef.current = chart;

      // 1. Candlestick Series
      const candleSeries = chart.addCandlestickSeries({
        upColor: '#10B981',
        downColor: '#F43F5E',
        borderVisible: false,
        wickUpColor: '#10B981',
        wickDownColor: '#F43F5E',
      });

      // Map, sort, and deduplicate candles by date
      const dateMap = new Map<string, CandlestickData>();
      const volMap = new Map<string, HistogramData>();

      for (const c of candles) {
        if (!c || c.open === undefined || c.close === undefined) continue;
        let dateStr: string;
        try {
          dateStr = typeof c.timestamp === 'string' 
            ? c.timestamp.split('T')[0] 
            : new Date(c.timestamp).toISOString().split('T')[0];
        } catch {
          continue;
        }

        dateMap.set(dateStr, {
          time: dateStr as any,
          open: Number(c.open),
          high: Number(c.high),
          low: Number(c.low),
          close: Number(c.close),
        });

        volMap.set(dateStr, {
          time: dateStr as any,
          value: Number(c.volume || 0),
          color: c.close >= c.open 
            ? (isDarkTheme ? 'rgba(16, 185, 129, 0.25)' : 'rgba(16, 185, 129, 0.4)') 
            : (isDarkTheme ? 'rgba(244, 63, 94, 0.25)' : 'rgba(244, 63, 94, 0.4)'),
        });
      }

      const formattedCandles = Array.from(dateMap.values()).sort((a, b) => (a.time > b.time ? 1 : -1));
      const formattedVolume = Array.from(volMap.values()).sort((a, b) => (a.time > b.time ? 1 : -1));

      if (formattedCandles.length > 0) {
        candleSeries.setData(formattedCandles);

        // 2. Volume Histogram Series
        const volumeSeries = chart.addHistogramSeries({
          color: '#3B82F6',
          priceFormat: { type: 'volume' },
          priceScaleId: '', // Overlay in separate sub-pane margin
        });

        volumeSeries.priceScale().applyOptions({
          scaleMargins: {
            top: 0.8,
            bottom: 0,
          },
        });

        volumeSeries.setData(formattedVolume);

        // 3. Price Lines (Stop Loss, Entry, Targets) if provided
        if (levels) {
          if (levels.stop_loss > 0) {
            candleSeries.createPriceLine({
              price: Number(levels.stop_loss),
              color: '#F43F5E',
              lineWidth: 2,
              lineStyle: 2,
              axisLabelVisible: true,
              title: `Stop Loss ₹${levels.stop_loss}`,
            });
          }

          if (levels.entry_high > 0) {
            candleSeries.createPriceLine({
              price: Number(levels.entry_high),
              color: '#3B82F6',
              lineWidth: 1,
              lineStyle: 1,
              axisLabelVisible: true,
              title: `Entry ₹${levels.entry_high}`,
            });
          }

          if (levels.target_1 > 0) {
            candleSeries.createPriceLine({
              price: Number(levels.target_1),
              color: '#10B981',
              lineWidth: 2,
              lineStyle: 2,
              axisLabelVisible: true,
              title: `Target 1 ₹${levels.target_1}`,
            });
          }

          if (levels.target_2 > 0) {
            candleSeries.createPriceLine({
              price: Number(levels.target_2),
              color: '#06B6D4',
              lineWidth: 1,
              lineStyle: 3,
              axisLabelVisible: true,
              title: `Target 2 ₹${levels.target_2}`,
            });
          }
        }

        chart.timeScale().fitContent();
      }
    } catch (err) {
      console.error('Error creating TradingViewChart:', err);
    }

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        try {
          chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
        } catch {}
      }
    };

    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        try {
          chartRef.current.remove();
        } catch {}
      }
    };
  }, [candles, levels, isDark]);

  const timeframes = ['1D', '1W', '1M', '3M', '6M', '1Y'];

  return (
    <div className="rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark p-4 shadow-subtle">
      {/* Timeframe Controls & Legend */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border-light dark:border-border-dark mb-2">
        <div className="flex items-center space-x-1 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-lg">
          {timeframes.map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 rounded text-xs font-semibold font-mono transition-all ${
                timeframe === tf
                  ? 'bg-white dark:bg-background-cardDark text-blue-600 dark:text-blue-400 shadow-subtle'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Level Legend */}
        {levels && (
          <div className="flex items-center space-x-3 text-xs font-mono">
            {levels.stop_loss > 0 && (
              <div className="flex items-center space-x-1">
                <span className="w-2.5 h-0.5 bg-rose-500 rounded"></span>
                <span className="text-slate-500">SL: ₹{levels.stop_loss}</span>
              </div>
            )}
            {levels.entry_high > 0 && (
              <div className="flex items-center space-x-1">
                <span className="w-2.5 h-0.5 bg-blue-500 rounded"></span>
                <span className="text-slate-500">Entry: ₹{levels.entry_high}</span>
              </div>
            )}
            {levels.target_1 > 0 && (
              <div className="flex items-center space-x-1">
                <span className="w-2.5 h-0.5 bg-emerald-500 rounded"></span>
                <span className="text-slate-500">T1: ₹{levels.target_1}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chart Canvas */}
      <div ref={chartContainerRef} className="w-full relative min-h-[440px]" />
    </div>
  );
};
