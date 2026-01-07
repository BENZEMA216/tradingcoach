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

export interface PositionSummary {
  total_positions: number;
  closed_positions: number;
  open_positions: number;
  total_pnl: number;
  total_realized_pnl: number;
  total_fees: number;
  winners: number;
  losers: number;
  win_rate: number;
  avg_pnl: number;
  avg_winner: number;
  avg_loser: number;
  profit_factor: number | null;
  avg_score: number | null;
  avg_holding_days: number;
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
  // 新闻上下文
  news_context?: NewsContext | null;
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

// Trade Types (linked to position)
export interface PositionTrade {
  id: number;
  symbol: string;
  symbol_name: string | null;
  direction: string;
  filled_price: number;
  filled_quantity: number;
  filled_amount: number;
  filled_time: string;
  total_fees: number;
  slippage: number | null;
  slippage_pct: number | null;
}

// Market Data for chart
export interface MarketDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  // Technical indicators (optional)
  rsi_14?: number | null;
  macd?: number | null;
  macd_signal?: number | null;
  bb_upper?: number | null;
  bb_middle?: number | null;
  bb_lower?: number | null;
  ma_20?: number | null;
  ma_50?: number | null;
}

// Lightweight Charts data format
export interface CandleData {
  time: string;  // YYYY-MM-DD format
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface LineData {
  time: string;
  value: number;
}

export interface ChartMarker {
  date: string;
  price: number;
  type: 'entry' | 'exit';
}

export interface PositionMarketData {
  symbol: string;
  position_id: number;
  candles: MarketDataPoint[];
  entry_marker: ChartMarker;
  exit_marker: ChartMarker | null;
  mae_level: number | null;
  mfe_level: number | null;
  holding_period: {
    start: string;
    end: string | null;
  };
  message?: string;
}

// Insight Types
export interface PositionInsight {
  category: 'entry' | 'exit' | 'risk' | 'behavior' | 'pattern';
  type: 'positive' | 'negative' | 'neutral' | 'warning';
  title: string;
  description: string;
  evidence: Record<string, unknown> | null;
  suggestion: string | null;
  priority: number;
}

// Related Position (option-stock bundling)
export interface RelatedPosition {
  id: number;
  symbol: string;
  symbol_name: string | null;
  direction: string;
  is_option: boolean;
  underlying_symbol: string | null;
  open_date: string | null;
  close_date: string | null;
  holding_period_days: number | null;
  net_pnl: number | null;
  net_pnl_pct: number | null;
  overall_score: number | null;
  score_grade: string | null;
}

// Risk Metrics
export interface RiskMetrics {
  max_drawdown: number;
  max_drawdown_pct: number | null;
  avg_drawdown: number | null;
  max_drawdown_duration_days: number | null;
  current_drawdown: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  calmar_ratio: number | null;
  var_95: number | null;
  expected_shortfall: number | null;
  profit_factor: number | null;
  payoff_ratio: number | null;
  expectancy: number | null;
  daily_volatility: number | null;
  annualized_volatility: number | null;
}

export interface DrawdownPeriod {
  start_date: string;
  end_date: string | null;
  peak_value: number;
  trough_value: number;
  drawdown: number;
  drawdown_pct: number;
  recovery_date: string | null;
  duration_days: number;
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
  asset_type?: string;
  open_hour?: number;
  is_reviewed?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// AI Coach Insight Types
export type InsightType = 'problem' | 'strength' | 'reminder';

export type InsightCategory =
  | 'time'
  | 'holding'
  | 'symbol'
  | 'direction'
  | 'risk'
  | 'behavior'
  | 'fees'
  | 'options'
  | 'benchmark'
  | 'trend';

export interface TradingInsight {
  id: string;
  type: InsightType;
  category: InsightCategory;
  priority: number;
  title: string;
  description: string;
  suggestion: string;
  data_points: Record<string, unknown>;
}

// ============================================================
// Advanced Visualization Types
// ============================================================

export interface EquityDrawdownItem {
  date: string;
  cumulative_pnl: number;
  drawdown: number;
  drawdown_pct: number | null;
  peak: number;
}

export interface PnLDistributionBin {
  min_value: number;
  max_value: number;
  count: number;
  is_profit: boolean;
}

export interface RollingMetricsItem {
  trade_index: number;
  close_date: string;
  rolling_win_rate: number;
  rolling_avg_pnl: number;
  cumulative_pnl: number;
}

export interface DurationPnLItem {
  position_id: number;
  holding_days: number;
  pnl: number;
  pnl_pct: number | null;
  symbol: string;
  direction: string;
  is_winner: boolean;
}

export interface SymbolRiskItem {
  symbol: string;
  avg_win: number;
  avg_loss: number;
  trade_count: number;
  win_rate: number;
  total_pnl: number;
  risk_reward_ratio: number | null;
}

export interface HourlyPerformanceItem {
  hour: number;
  trade_count: number;
  win_rate: number;
  total_pnl: number;
  avg_pnl: number;
}

export interface TradingHeatmapCell {
  day_of_week: number;
  day_name: string;
  hour: number;
  trade_count: number;
  win_rate: number;
  avg_pnl: number;
  total_pnl: number;
}

export interface AssetTypeBreakdownItem {
  asset_type: string;
  count: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl: number;
  avg_holding_days: number;
}

export interface DirectionBreakdownItem {
  direction: string;
  count: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl: number;
}

export interface HoldingPeriodBreakdownItem {
  period_label: string;
  min_days: number;
  max_days: number;
  count: number;
  total_pnl: number;
  win_rate: number;
  avg_pnl: number;
}

// ============================================================
// AI Coach Types
// ============================================================

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  history?: ChatMessage[];
}

export interface ChatResponse {
  answer: string;
  supporting_data?: Record<string, unknown> | null;
  related_insights?: TradingInsight[] | null;
}

export interface ProactiveInsightResponse {
  insights: TradingInsight[];
  ai_summary: string;
  key_metrics: {
    total_trades?: number;
    win_rate?: number;
    total_pnl?: number;
    avg_win?: number;
    avg_loss?: number;
    winners?: number;
    losers?: number;
  };
  date_range: {
    start: string;
    end: string;
    display?: string;
  };
  generated_at: string;
}

export interface AICoachStatus {
  available: boolean;
  provider: string | null;
  model: string | null;
  message: string;
}

export interface InsightsOnlyResponse {
  insights: TradingInsight[];
  total: number;
  date_range: {
    start: string;
    end: string;
  };
}

// ============================================================
// News Context Types
// ============================================================

export interface NewsItem {
  title: string;
  source: string;
  date: string;
  url?: string;
  category: string;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  relevance?: number;
}

export interface NewsScoreBreakdown {
  direction: number;      // 方向对齐 (0-100)
  timing: number;         // 时机质量 (0-100)
  completeness: number;   // 信息完整度 (0-100)
  risk: number;           // 风险意识 (0-100)
}

export interface NewsContext {
  id: number;
  position_id: number;
  symbol: string;
  search_date: string;
  // 分类标记
  has_earnings: boolean;
  has_product_news: boolean;
  has_analyst_rating: boolean;
  has_sector_news: boolean;
  has_macro_news: boolean;
  has_geopolitical: boolean;
  // 情感分析
  overall_sentiment: 'bullish' | 'bearish' | 'neutral' | 'mixed' | null;
  sentiment_score: number | null;  // -100 to +100
  news_impact_level: 'high' | 'medium' | 'low' | 'none';
  // 评分
  news_alignment_score: number | null;
  score_breakdown: NewsScoreBreakdown | null;
  // 新闻数据
  news_items: NewsItem[] | null;
  news_count: number;
}

// ============================================================
// Event Context Types
// ============================================================

export type EventType =
  | 'earnings'
  | 'earnings_pre'
  | 'earnings_post'
  | 'dividend'
  | 'split'
  | 'product'
  | 'guidance'
  | 'analyst'
  | 'insider'
  | 'buyback'
  | 'offering'
  | 'fda'
  | 'contract'
  | 'management'
  | 'macro'
  | 'fed'
  | 'cpi'
  | 'nfp'
  | 'geopolitical'
  | 'sector'
  | 'price_anomaly'
  | 'volume_anomaly'
  | 'other';

export type EventImpact = 'positive' | 'negative' | 'neutral' | 'mixed' | 'unknown';

export interface EventListItem {
  id: number;
  symbol: string;
  event_type: EventType;
  event_date: string;
  event_title: string;
  event_impact: EventImpact | null;
  event_importance: number | null;
  price_change_pct: number | null;
  volume_spike: number | null;
  position_id: number | null;
  position_pnl_on_event: number | null;
  is_key_event: boolean;
}

export interface EventDetail extends EventListItem {
  underlying_symbol: string | null;
  event_time: string | null;
  event_description: string | null;
  is_surprise: boolean;
  surprise_direction: 'beat' | 'miss' | null;
  surprise_magnitude: number | null;
  price_before: number | null;
  price_after: number | null;
  price_change: number | null;
  event_day_high: number | null;
  event_day_low: number | null;
  event_day_range_pct: number | null;
  gap_pct: number | null;
  volume_on_event: number | null;
  volume_avg_20d: number | null;
  position_pnl_pct_on_event: number | null;
  source: string | null;
  confidence: number | null;
  user_notes: string | null;
}

export interface EventStatistics {
  total_events: number;
  by_type: Record<string, number>;
  by_impact: Record<string, number>;
  high_impact_count: number;
  avg_price_change: number | null;
}

export interface EventPerformanceByType {
  event_type: EventType;
  event_count: number;
  total_pnl: number;
  avg_pnl: number;
  win_rate: number;
  avg_price_change: number | null;
}

export interface PaginatedEvents {
  items: EventListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PositionEventsResponse {
  position_id: number;
  symbol: string;
  events: EventListItem[];
  total_events: number;
  key_events_count: number;
}
