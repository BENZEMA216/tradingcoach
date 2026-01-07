import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';
import { statisticsApi } from '@/api/client';
import { formatCurrency } from '@/utils/format';
import clsx from 'clsx';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

interface TradingCalendarProps {
    className?: string;
}

interface DailyData {
    date: string;
    pnl: number;
    trade_count: number;
    win_rate: number;
}

export function TradingCalendar({ className }: TradingCalendarProps) {
    const { i18n } = useTranslation();
    const navigate = useNavigate();
    const isZh = i18n.language === 'zh';

    const [currentDate, setCurrentDate] = useState(new Date());

    // Fetch calendar heatmap data for the current year
    const { data: yearData, isLoading } = useQuery({
        queryKey: ['statistics', 'calendar-heatmap', currentDate.getFullYear()],
        queryFn: () => statisticsApi.getCalendarHeatmap(currentDate.getFullYear()),
    });

    // Transform array data into a map for O(1) lookup
    const dailyDataMap = useMemo(() => {
        const map = new Map<string, DailyData>();
        if (Array.isArray(yearData)) {
            yearData.forEach((item: any) => {
                // Assuming item has { date: string, value: number, count: number } structure matches backend
                // We might need to adjust based on actual API response, but strictly typing for now
                map.set(item.date, {
                    date: item.date,
                    pnl: item.value, // value usually maps to pnl in heatmaps
                    trade_count: item.count || 0,
                    win_rate: 0 // Heatmap might not return win_rate, check types later
                });
            });
        }
        return map;
    }, [yearData]);

    // Calendar Logic
    const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
    const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay();

    // Generate calendar grid
    const calendarDays = useMemo(() => {
        const days = [];
        // Padding for prev month
        for (let i = 0; i < firstDayOfMonth; i++) {
            days.push(null);
        }
        // Days of current month
        for (let i = 1; i <= daysInMonth; i++) {
            days.push(new Date(currentDate.getFullYear(), currentDate.getMonth(), i));
        }
        return days;
    }, [currentDate.getFullYear(), currentDate.getMonth()]);

    const handlePrevMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    };

    const handleNextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    };

    const handleDayClick = (date: Date) => {
        const dateStr = date.toISOString().split('T')[0];
        // Navigate to positions with filter
        navigate(`/positions?date_start=${dateStr}&date_end=${dateStr}`);
    };

    const monthNames = isZh
        ? ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月']
        : ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

    const weekDays = isZh
        ? ['日', '一', '二', '三', '四', '五', '六']
        : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    return (
        <div className={clsx("bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 p-6 transition-colors", className)}>
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-blue-50 dark:bg-blue-500/10 rounded-sm">
                        <CalendarIcon className="w-5 h-5 text-blue-600 dark:text-blue-500" />
                    </div>
                    <h2 className="text-lg font-mono font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                        {isZh ? '交易日历' : 'Trading Calendar'}
                    </h2>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex items-center bg-neutral-100 dark:bg-white/5 border border-neutral-200 dark:border-white/10 rounded-sm p-1">
                        <button
                            onClick={handlePrevMonth}
                            className="p-1 hover:bg-neutral-200 dark:hover:bg-white/10 rounded-sm transition-all text-slate-500 dark:text-white/70 hover:text-slate-900 dark:hover:text-white"
                        >
                            <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="px-4 text-sm font-mono font-medium text-slate-900 dark:text-white min-w-[120px] text-center uppercase">
                            {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
                        </span>
                        <button
                            onClick={handleNextMonth}
                            className="p-1 hover:bg-neutral-200 dark:hover:bg-white/10 rounded-sm transition-all text-slate-500 dark:text-white/70 hover:text-slate-900 dark:hover:text-white"
                        >
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Grid Header */}
            <div className="grid grid-cols-7 mb-2">
                {weekDays.map(day => (
                    <div key={day} className="text-center text-[10px] font-mono font-medium text-slate-400 dark:text-white/40 uppercase py-2">
                        {day}
                    </div>
                ))}
            </div>

            {/* Grid Body */}
            <div className="grid grid-cols-7 gap-2">
                {isLoading ? (
                    // Loading skeletons
                    Array.from({ length: 35 }).map((_, i) => (
                        <div key={i} className="aspect-square bg-neutral-100 dark:bg-white/5 rounded-sm animate-pulse" />
                    ))
                ) : (
                    calendarDays.map((date, idx) => {
                        if (!date) return <div key={`empty-${idx}`} className="aspect-square" />;

                        const dateStr = date.toISOString().split('T')[0];
                        const data = dailyDataMap.get(dateStr);
                        const pnl = data?.pnl || 0;
                        const hasData = !!data;
                        const isToday = dateStr === new Date().toISOString().split('T')[0];

                        return (
                            <div
                                key={dateStr}
                                onClick={() => handleDayClick(date)}
                                className={clsx(
                                    "aspect-square rounded-sm p-2 flex flex-col justify-between transition-all cursor-pointer border relative group overflow-hidden",
                                    // Base styles
                                    "hover:border-slate-300 dark:hover:border-white/40",
                                    // Background/Border based on PnL
                                    !hasData && "bg-neutral-50 dark:bg-white/5 border-transparent text-slate-300 dark:text-white/20 hover:bg-neutral-100 dark:hover:bg-white/10",
                                    hasData && pnl > 0 && "bg-green-50 dark:bg-green-500/10 border-green-200 dark:border-green-500/20 text-green-600 dark:text-green-500 hover:bg-green-100 dark:hover:bg-green-500/20",
                                    hasData && pnl < 0 && "bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-500 hover:bg-red-100 dark:hover:bg-red-500/20",
                                    hasData && pnl === 0 && "bg-neutral-100 dark:bg-white/10 border-neutral-200 dark:border-white/20 text-slate-500 dark:text-white/60",
                                    // Today highlight
                                    isToday && "ring-1 ring-blue-500"
                                )}
                            >
                                <div className="flex justify-between items-start">
                                    <span className={clsx(
                                        "text-[10px] font-mono",
                                        hasData ? "text-white/80" : "text-white/20"
                                    )}>
                                        {date.getDate()}
                                    </span>

                                    {hasData && (data?.trade_count || 0) > 0 && (
                                        <span className={clsx(
                                            "text-[9px] px-1 py-0.5 rounded-sm font-mono",
                                            pnl > 0 ? "bg-green-500/20 text-green-400" :
                                                pnl < 0 ? "bg-red-500/20 text-red-400" :
                                                    "bg-white/20 text-white/60"
                                        )}>
                                            {data?.trade_count}
                                        </span>
                                    )}
                                </div>

                                {hasData && (
                                    <div className="text-right mt-1">
                                        <span className={clsx(
                                            "text-[10px] font-mono font-bold block truncate",
                                            pnl > 0 ? "text-green-600 dark:text-green-500" : pnl < 0 ? "text-red-600 dark:text-red-500" : "text-slate-400 dark:text-white/50"
                                        )}>
                                            {pnl > 0 ? '+' : ''}{pnl !== 0 ? formatCurrency(Math.abs(pnl)).replace('$', '') : '-'}
                                        </span>
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}
