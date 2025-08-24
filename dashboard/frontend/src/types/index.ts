export interface TradeRecord {
  id: number
  timestamp: string
  action: string | null
  slug: string
  amount: number
  price: number
  remaining_cryptos: number
  remaining_dollar: number
}

export interface Position {
  crypto_balance: number
  usd_balance: number
  current_price: number
  crypto_value: number
  total_value: number
  pnl_24h: number
  pnl_24h_percentage: number
  last_action: string | null
  last_trade_time: string
}

export interface PortfolioSummary {
  total_usd_value: number
  total_pnl: number
  total_pnl_percentage: number
  positions: Record<string, Position>
  last_updated: string
}

export interface PerformanceMetrics {
  period: string
  pnl: number
  pnl_percentage: number
  trades_count: number
  win_rate: number
  sharpe_ratio: number | null
  max_drawdown: number
}

export interface PriceData {
  slug: string
  current_price: number
  change_24h?: number
  timestamp: string
}

export interface WebSocketMessage {
  type: 'price_update' | 'trade_executed' | 'trade_error' | 'subscribed'
  data?: any
  slug?: string
  action?: string
  result?: string
  error?: string
  timestamp: string
}

export interface ChartDataPoint {
  timestamp: string
  value: number
  pnl?: number
  price?: number
}

export interface CryptoInfo {
  slug: string
  name: string
  symbol: string
  color: string
}
