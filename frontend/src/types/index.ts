// API Response Types

export interface DashboardKPIs {
  total_pnl: number;
  win_rate: number;
  avg_score: number;
  trade_count: number;
  total_fees: number;
  avg_holding_days: number;
}

export interface EquityCurvePoint {
  date: string;
  cumulative_pnl: number;
  trade_count: number;
}

export interface EquityCurveResponse {
  data: EquityCurvePoint[];
  total_pnl: number;
  max_drawdown: number | null;
  max_drawdown_pct: number | null;
}

export interface RecentTradeItem {
  id: number;
  symbol: string;
  close_date: string | null;
  net_pnl: number;
  net_pnl_pct: number | null;
  grade: string | null;
  direction: string;
}

export interface StrategyBreakdownItem {
  strategy: string;
  strategy_name: string;
  count: number;
  total_pnl: number;
  win_rate: number;
}

export interface DailyPnLItem {
  date: string;
  pnl: number;
  trade_count: number;
}

// Position Types
export interface PositionListItem {
  id: number;
  symbol: string;
  symbol_name: string | null;
  direction: string;
  status: string;
  open_date: string;
  close_date: string | null;
  holding_period_days: number | null;
  open_price: number;
  close_price: number | null;
  quantity: number;
  net_pnl: number | null;
  net_pnl_pct: number | null;
  overall_score: number | null;
  score_grade: string | null;
  strategy_type: string | null;
  reviewed_at: string | null;
}

export interface PositionScoreDetail {
  entry_quality_score: number | null;
  exit_quality_score: number | null;
  trend_quality_score: number | null;
  risk_mgmt_score: number | null;
  overall_score: number | null;
  score_grade: string | null;
}

export interface PositionRiskMetrics {
  mae: number | null;
  mae_pct: number | null;
  mae_time: string | null;
  mfe: number | null;
  mfe_pct: number | null;
  mfe_time: string | null;
  risk_reward_ratio: number | null;
}

export interface PositionDetail extends PositionListItem {
  open_time: string | null;
  close_time: string | null;
  holding_period_hours: number | null;
  realized_pnl: number | null;
  realized_pnl_pct: number | null;
  total_fees: number | null;
  open_fee: number | null;
  close_fee: number | null;
  market: string | null;
  currency: string | null;
  is_option: boolean;
  underlying_symbol: string | null;
  scores: PositionScoreDetail;
  risk_metrics: PositionRiskMetrics;
  strategy_confidence: number | null;
  entry_indicators: Record<string, unknown> | null;
  exit_indicators: Record<string, unknown> | null;
  post_exit_5d_pct: number | null;
  post_exit_10d_pct: number | null;
  post_exit_20d_pct: number | null;
  review_notes: Record<string, unknown> | null;
  emotion_tag: string | null;
  discipline_score: number | null;
  analysis_notes: Record<string, unknown> | null;
  trade_ids: number[];
  created_at: string | null;
  updated_at: string | null;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Statistics Types
export interface PerformanceMetrics {
  total_pnl: number;
  total_trades: number;
  winners: number;
  losers: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  avg_pnl: number;
  profit_factor: number | null;
  max_drawdown: number | null;
  max_drawdown_pct: number | null;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  total_fees: number;
  fees_pct_of_pnl: number | null;
  avg_holding_days: number;
  avg_winner_holding_days: number | null;
  avg_loser_holding_days: number | null;
}

export interface SymbolBreakdownItem {
  symbol: string;
  symbol_name: string | null;
  count: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl: number;
  avg_holding_days: number;
}

export interface GradeBreakdownItem {
  grade: string;
  count: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl: number;
}

export interface MonthlyPnLItem {
  year: number;
  month: number;
  pnl: number;
  trade_count: number;
  win_rate: number;
}

// System Types
export interface SystemStats {
  database: {
    positions: {
      count: number;
      symbols: number;
      date_range: { start: string | null; end: string | null };
    };
    trades: {
      count: number;
      date_range: { start: string | null; end: string | null };
    };
    market_data: {
      count: number;
      symbols: number;
      date_range: { start: string | null; end: string | null };
    };
  };
  timestamp: string;
}

// Filter Types
export interface PositionFilters {
  symbol?: string;
  direction?: 'long' | 'short';
  status?: 'open' | 'closed';
  date_start?: string;
  date_end?: string;
  pnl_min?: number;
  pnl_max?: number;
  is_winner?: boolean;
  score_min?: number;
  score_max?: number;
  score_grade?: string;
  strategy_type?: string;
  is_reviewed?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}
