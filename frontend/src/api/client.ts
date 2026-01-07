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
  PositionSummary,
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

  getSummary: async (filters?: PositionFilters) => {
    const { data } = await api.get<PositionSummary>('/positions/summary', { params: filters });
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
export interface DataResetResponse {
  success: boolean;
  message: string;
  deleted_counts: {
    positions: number;
    trades: number;
    import_history: number;
    tasks: number;
  };
  timestamp: string;
}

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

  /**
   * 重置所有交易数据
   * 警告：此操作不可撤销！
   */
  resetAllData: async (): Promise<DataResetResponse> => {
    const { data } = await api.delete<DataResetResponse>('/system/data/reset');
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

// Upload API
export interface UploadResponse {
  success: boolean;
  message: string;
  file_name: string;
  file_hash: string;
  language: string;
  total_rows: number;
  completed_trades: number;
  new_trades: number;
  duplicates_skipped: number;
  positions_matched: number;
  positions_scored: number;
  processing_time_ms: number;
  errors: number;
  error_messages: string[];
}

export interface UploadHistoryItem {
  id: number;
  import_time: string;
  file_name: string;
  file_type: string;
  total_rows: number;
  new_trades: number;
  duplicates_skipped: number;
  status: string;
}

export const uploadApi = {
  /**
   * 上传交易记录CSV文件
   * @param file CSV文件
   * @param replaceMode 替换模式(默认true) - 清除旧数据，只分析本次上传
   */
  uploadTrades: async (file: File, replaceMode: boolean = true): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await api.post<UploadResponse>(
      `/upload/trades?replace_mode=${replaceMode}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 seconds for upload
      }
    );
    return data;
  },

  /**
   * 获取导入历史
   */
  getHistory: async (limit: number = 20): Promise<UploadHistoryItem[]> => {
    const { data } = await api.get<UploadHistoryItem[]>('/upload/history', {
      params: { limit },
    });
    return data;
  },

  /**
   * 上传持仓快照进行对账
   */
  uploadSnapshot: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await api.post('/upload/snapshot', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },
};

// Task API
export interface TaskStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_step: string | null;
  file_name: string | null;
  email: string | null;
  result: {
    language?: string;
    total_rows?: number;
    completed_trades?: number;
    new_trades?: number;
    duplicates_skipped?: number;
    positions_matched?: number;
    positions_scored?: number;
    errors?: number;
    error_messages?: string[];
  } | null;
  error_message: string | null;
  logs: { time: string; level: string; message: string }[];
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface TaskCreateResponse {
  success: boolean;
  task_id: string;
  message: string;
}

export interface TaskListResponse {
  tasks: TaskStatus[];
  total: number;
}

export const taskApi = {
  /**
   * 创建分析任务
   * @param file CSV文件
   * @param email 邮箱地址（可选）
   * @param replaceMode 替换模式（默认true）
   */
  create: async (file: File, email?: string, replaceMode: boolean = true): Promise<TaskCreateResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams();
    if (email) params.append('email', email);
    params.append('replace_mode', String(replaceMode));

    const { data } = await api.post<TaskCreateResponse>(
      `/tasks/create?${params.toString()}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000,
      }
    );
    return data;
  },

  /**
   * 获取任务状态
   */
  getStatus: async (taskId: string): Promise<TaskStatus> => {
    const { data } = await api.get<TaskStatus>(`/tasks/${taskId}`);
    return data;
  },

  /**
   * 获取任务列表
   */
  list: async (limit: number = 10, status?: string): Promise<TaskListResponse> => {
    const params: Record<string, unknown> = { limit };
    if (status) params.status = status;
    const { data } = await api.get<TaskListResponse>('/tasks/', { params });
    return data;
  },

  /**
   * 取消任务
   */
  cancel: async (taskId: string): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.delete(`/tasks/${taskId}`);
    return data;
  },
};

// Events API
import type {
  EventListItem,
  EventDetail,
  EventStatistics,
  EventPerformanceByType,
  PaginatedEvents,
  PositionEventsResponse,
} from '@/types';

export interface EventFilters {
  symbol?: string;
  event_type?: string;
  event_impact?: string;
  date_start?: string;
  date_end?: string;
  min_importance?: number;
  is_key_event?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export const eventsApi = {
  /**
   * 获取事件列表（分页）
   */
  list: async (page = 1, pageSize = 20, filters?: EventFilters): Promise<PaginatedEvents> => {
    const { data } = await api.get<PaginatedEvents>('/events', {
      params: { page, page_size: pageSize, ...filters },
    });
    return data;
  },

  /**
   * 获取事件详情
   */
  getDetail: async (eventId: number): Promise<EventDetail> => {
    const { data } = await api.get<EventDetail>(`/events/${eventId}`);
    return data;
  },

  /**
   * 获取事件统计
   */
  getStatistics: async (params?: {
    symbol?: string;
    date_start?: string;
    date_end?: string;
  }): Promise<EventStatistics> => {
    const { data } = await api.get<EventStatistics>('/events/statistics', { params });
    return data;
  },

  /**
   * 按事件类型获取绩效
   */
  getPerformanceByType: async (): Promise<EventPerformanceByType[]> => {
    const { data } = await api.get<EventPerformanceByType[]>('/events/by-type-performance');
    return data;
  },

  /**
   * 获取持仓关联的事件
   */
  getForPosition: async (positionId: number): Promise<PositionEventsResponse> => {
    const { data } = await api.get<PositionEventsResponse>(`/events/position/${positionId}`);
    return data;
  },

  /**
   * 获取标的事件时间线
   */
  getSymbolTimeline: async (symbol: string, days = 90): Promise<EventListItem[]> => {
    const { data } = await api.get<EventListItem[]>(`/events/symbol/${symbol}/timeline`, {
      params: { days },
    });
    return data;
  },

  /**
   * 标记关键事件
   */
  markAsKey: async (eventId: number, isKey = true): Promise<EventDetail> => {
    const { data } = await api.put<EventDetail>(`/events/${eventId}/mark-key`, null, {
      params: { is_key: isKey },
    });
    return data;
  },

  /**
   * 更新事件备注
   */
  updateNotes: async (eventId: number, notes: string): Promise<EventDetail> => {
    const { data } = await api.put<EventDetail>(`/events/${eventId}/notes`, null, {
      params: { notes },
    });
    return data;
  },
};

export default api;
