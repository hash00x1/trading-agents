import axios from 'axios'
import { PortfolioSummary, TradeRecord, PerformanceMetrics } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const apiService = {
  // Portfolio endpoints
  getPortfolioSummary: (): Promise<PortfolioSummary> =>
    api.get('/portfolio/summary').then(res => res.data),

  // Trading endpoints
  getTrades: (slug: string, limit = 50): Promise<TradeRecord[]> =>
    api.get(`/trades/${slug}?limit=${limit}`).then(res => res.data),

  // Performance endpoints
  getPerformanceMetrics: (slug: string, periods = '1,7,30'): Promise<PerformanceMetrics[]> =>
    api.get(`/performance/${slug}?periods=${periods}`).then(res => res.data),

  // Crypto data endpoints
  getCryptos: (): Promise<{ cryptos: string[] }> =>
    api.get('/cryptos').then(res => res.data),

  getCurrentPrices: (): Promise<Record<string, any>> =>
    api.get('/prices').then(res => res.data),

  getBinanceBalances: (): Promise<{ balances: any; timestamp: string }> =>
    api.get('/balances').then(res => res.data),

  // Health check
  getHealthCheck: () =>
    api.get('/').then(res => res.data),
}

export default apiService
