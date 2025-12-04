import axios from 'axios';
import type {
  DashboardKPIs,
  EquityCurveResponse,
  RecentTradeItem,
  StrategyBreakdownItem,
  DailyPnLItem,
  PositionListItem,
  PositionDetail,
  PaginatedResponse,
  PerformanceMetrics,
  SymbolBreakdownItem,
  GradeBreakdownItem,
  MonthlyPnLItem,
  SystemStats,
  PositionFilters,
} from '@/types';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Dashboard API
export const dashboardApi = {
  getKPIs: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<DashboardKPIs>('/dashboard/kpis', { params });
    return data;
  },

  getEquityCurve: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<EquityCurveResponse>('/dashboard/equity-curve', { params });
    return data;
  },

  getRecentTrades: async (limit = 10) => {
    const { data } = await api.get<RecentTradeItem[]>('/dashboard/recent-trades', {
      params: { limit },
    });
    return data;
  },

  getStrategyBreakdown: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<StrategyBreakdownItem[]>('/dashboard/strategy-breakdown', {
      params,
    });
    return data;
  },

  getDailyPnL: async (days = 30) => {
    const { data } = await api.get<DailyPnLItem[]>('/dashboard/daily-pnl', {
      params: { days },
    });
    return data;
  },
};

// Positions API
export const positionsApi = {
  list: async (
    page = 1,
    pageSize = 20,
    filters?: PositionFilters
  ) => {
    const { data } = await api.get<PaginatedResponse<PositionListItem>>('/positions', {
      params: { page, page_size: pageSize, ...filters },
    });
    return data;
  },

  getDetail: async (id: number) => {
    const { data } = await api.get<PositionDetail>(`/positions/${id}`);
    return data;
  },

  getSummary: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get('/positions/summary', { params });
    return data;
  },

  updateReview: async (
    id: number,
    review: {
      review_notes?: Record<string, unknown>;
      emotion_tag?: string;
      discipline_score?: number;
    }
  ) => {
    const { data } = await api.patch(`/positions/${id}/review`, review);
    return data;
  },

  getSymbols: async () => {
    const { data } = await api.get<string[]>('/positions/symbols/list');
    return data;
  },
};

// Statistics API
export const statisticsApi = {
  getPerformance: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<PerformanceMetrics>('/statistics/performance', { params });
    return data;
  },

  getBySymbol: async (params?: { date_start?: string; date_end?: string; limit?: number }) => {
    const { data } = await api.get<SymbolBreakdownItem[]>('/statistics/by-symbol', { params });
    return data;
  },

  getByGrade: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<GradeBreakdownItem[]>('/statistics/by-grade', { params });
    return data;
  },

  getByDirection: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get('/statistics/by-direction', { params });
    return data;
  },

  getByHoldingPeriod: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get('/statistics/by-holding-period', { params });
    return data;
  },

  getMonthlyPnL: async (year?: number) => {
    const { data } = await api.get<MonthlyPnLItem[]>('/statistics/monthly-pnl', {
      params: year ? { year } : undefined,
    });
    return data;
  },

  getCalendarHeatmap: async (year: number) => {
    const { data } = await api.get('/statistics/calendar-heatmap', { params: { year } });
    return data;
  },
};

// System API
export const systemApi = {
  health: async () => {
    const { data } = await api.get('/system/health');
    return data;
  },

  getStats: async () => {
    const { data } = await api.get<SystemStats>('/system/stats');
    return data;
  },

  getSymbols: async () => {
    const { data } = await api.get('/system/symbols');
    return data;
  },
};

export default api;
