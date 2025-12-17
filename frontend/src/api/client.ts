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
  PositionTrade,
  PositionMarketData,
  PositionInsight,
  RelatedPosition,
  RiskMetrics,
  DrawdownPeriod,
  TradingInsight,
  // Advanced Visualization
  EquityDrawdownItem,
  PnLDistributionBin,
  RollingMetricsItem,
  DurationPnLItem,
  SymbolRiskItem,
  HourlyPerformanceItem,
  TradingHeatmapCell,
  AssetTypeBreakdownItem,
  DirectionBreakdownItem,
  HoldingPeriodBreakdownItem,
  // AI Coach
  ChatMessage,
  ChatResponse,
  ProactiveInsightResponse,
  AICoachStatus,
  InsightsOnlyResponse,
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

  getTrades: async (id: number) => {
    const { data } = await api.get<PositionTrade[]>(`/positions/${id}/trades`);
    return data;
  },

  getMarketData: async (id: number) => {
    const { data } = await api.get<PositionMarketData>(`/positions/${id}/market-data`);
    return data;
  },

  getInsights: async (id: number) => {
    const { data } = await api.get<PositionInsight[]>(`/positions/${id}/insights`);
    return data;
  },

  getRelated: async (id: number) => {
    const { data } = await api.get<RelatedPosition[]>(`/positions/${id}/related`);
    return data;
  },
};

// Statistics API
export const statisticsApi = {
  getDateRange: async () => {
    const { data } = await api.get<{ min_date: string | null; max_date: string | null; total_positions: number }>('/statistics/date-range');
    return data;
  },

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

  getRiskMetrics: async (params?: { date_start?: string; date_end?: string; risk_free_rate?: number }) => {
    const { data } = await api.get<RiskMetrics>('/statistics/risk-metrics', { params });
    return data;
  },

  getDrawdowns: async (params?: { date_start?: string; date_end?: string; min_drawdown?: number }) => {
    const { data } = await api.get<DrawdownPeriod[]>('/statistics/drawdowns', { params });
    return data;
  },

  getInsights: async (params?: { date_start?: string; date_end?: string; limit?: number }) => {
    const { data } = await api.get<TradingInsight[]>('/statistics/insights', { params });
    return data;
  },

  // Advanced Visualization APIs
  getEquityDrawdown: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<EquityDrawdownItem[]>('/statistics/equity-drawdown', { params });
    return data;
  },

  getPnLDistribution: async (params?: { date_start?: string; date_end?: string; bin_count?: number }) => {
    const { data } = await api.get<PnLDistributionBin[]>('/statistics/pnl-distribution', { params });
    return data;
  },

  getRollingMetrics: async (params?: { date_start?: string; date_end?: string; window?: number }) => {
    const { data } = await api.get<RollingMetricsItem[]>('/statistics/rolling-metrics', { params });
    return data;
  },

  getDurationPnL: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<DurationPnLItem[]>('/statistics/duration-pnl', { params });
    return data;
  },

  getSymbolRisk: async (params?: { date_start?: string; date_end?: string; min_trades?: number }) => {
    const { data } = await api.get<SymbolRiskItem[]>('/statistics/symbol-risk', { params });
    return data;
  },

  getHourlyPerformance: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<HourlyPerformanceItem[]>('/statistics/hourly-performance', { params });
    return data;
  },

  getTradingHeatmap: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<TradingHeatmapCell[]>('/statistics/trading-heatmap', { params });
    return data;
  },

  getByAssetType: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<AssetTypeBreakdownItem[]>('/statistics/by-asset-type', { params });
    return data;
  },

  getByDirectionTyped: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<DirectionBreakdownItem[]>('/statistics/by-direction', { params });
    return data;
  },

  getByHoldingPeriodTyped: async (params?: { date_start?: string; date_end?: string }) => {
    const { data } = await api.get<HoldingPeriodBreakdownItem[]>('/statistics/by-holding-period', { params });
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

// AI Coach API
export const aiCoachApi = {
  /**
   * 获取主动推送的洞察（包含 AI 总结）
   */
  getProactiveInsights: async (params?: {
    date_start?: string;
    date_end?: string;
    limit?: number;
  }) => {
    const { data } = await api.get<ProactiveInsightResponse>(
      '/ai-coach/proactive-insights',
      { params }
    );
    return data;
  },

  /**
   * 与 AI 教练对话
   */
  chat: async (message: string, history?: ChatMessage[]) => {
    const { data } = await api.post<ChatResponse>('/ai-coach/chat', {
      message,
      history: history?.map((msg) => ({
        role: msg.role,
        content: msg.content,
      })),
    });
    return data;
  },

  /**
   * 获取快捷问题列表
   */
  getQuickQuestions: async () => {
    const { data } = await api.get<{ questions: string[] }>(
      '/ai-coach/quick-questions'
    );
    return data.questions;
  },

  /**
   * 检查 AI Coach 服务状态
   */
  getStatus: async () => {
    const { data } = await api.get<AICoachStatus>('/ai-coach/status');
    return data;
  },

  /**
   * 仅获取规则引擎洞察（不调用 LLM）
   */
  getInsightsOnly: async (params?: {
    date_start?: string;
    date_end?: string;
    limit?: number;
  }) => {
    const { data } = await api.get<InsightsOnlyResponse>(
      '/ai-coach/insights-only',
      { params }
    );
    return data;
  },
};

export default api;
