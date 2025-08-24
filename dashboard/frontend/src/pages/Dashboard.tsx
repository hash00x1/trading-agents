import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw
} from 'lucide-react'
import apiService from '../services/api'
import { PortfolioSummary } from '../types'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import PortfolioChart from '../components/Charts/PortfolioChart'
import TradeHistory from '../components/Trading/TradeHistory'

const Dashboard: React.FC = () => {
  const { data: portfolio, isLoading, error, refetch } = useQuery<PortfolioSummary>({
    queryKey: ['portfolio-summary'],
    queryFn: apiService.getPortfolioSummary,
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const { data: cryptos } = useQuery({
    queryKey: ['cryptos'],
    queryFn: apiService.getCryptos,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (error || !portfolio) {
    return (
      <div className="text-center py-12">
        <div className="text-red-500 mb-4">Failed to load portfolio data</div>
        <button
          onClick={() => refetch()}
          className="btn-primary inline-flex items-center"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </button>
      </div>
    )
  }

  const totalPositions = Object.keys(portfolio.positions).length
  const activePositions = Object.values(portfolio.positions).filter(
    pos => pos.crypto_balance > 0
  ).length

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Last updated: {new Date(portfolio.last_updated).toLocaleString()}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn-secondary inline-flex items-center"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DollarSign className="h-6 w-6 text-primary-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Portfolio Value
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    ${portfolio.total_usd_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              {portfolio.total_pnl >= 0 ? (
                <TrendingUp className="h-6 w-6 text-success-600" />
              ) : (
                <TrendingDown className="h-6 w-6 text-danger-600" />
              )}
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  24h PnL
                </dt>
                <dd className="flex items-baseline">
                  <div className={`text-2xl font-semibold ${
                    portfolio.total_pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}>
                    {portfolio.total_pnl >= 0 ? '+' : ''}${portfolio.total_pnl.toFixed(2)}
                  </div>
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                    portfolio.total_pnl_percentage >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}>
                    {portfolio.total_pnl_percentage >= 0 ? (
                      <ArrowUpRight className="h-3 w-3 mr-1" />
                    ) : (
                      <ArrowDownRight className="h-3 w-3 mr-1" />
                    )}
                    {Math.abs(portfolio.total_pnl_percentage).toFixed(2)}%
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-6 w-6 text-warning-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Active Positions
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {activePositions}
                  </div>
                  <div className="ml-2 text-sm text-gray-500">
                    of {totalPositions}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-6 w-6 text-primary-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Assets Tracked
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-2xl font-semibold text-gray-900">
                    {cryptos?.cryptos.length || 0}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Portfolio Chart */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Portfolio Performance</h3>
              <div className="flex space-x-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                  24H
                </span>
              </div>
            </div>
            <PortfolioChart />
          </div>
        </motion.div>

        {/* Recent Trades */}
        <motion.div variants={itemVariants}>
          <div className="card h-full">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
            <TradeHistory limit={5} compact />
          </div>
        </motion.div>
      </div>

      {/* Top Positions */}
      <motion.div variants={itemVariants}>
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top Positions</h3>
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Asset</th>
                  <th className="table-header">Balance</th>
                  <th className="table-header">Value</th>
                  <th className="table-header">24h PnL</th>
                  <th className="table-header">Last Action</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(portfolio.positions)
                  .sort(([,a], [,b]) => b.total_value - a.total_value)
                  .slice(0, 5)
                  .map(([slug, position]) => (
                    <tr key={slug} className="hover:bg-gray-50">
                      <td className="table-cell">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-8 w-8">
                            <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                              <span className="text-xs font-medium text-primary-600">
                                {slug.slice(0, 2).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 capitalize">
                              {slug}
                            </div>
                            <div className="text-sm text-gray-500">
                              ${position.current_price.toFixed(2)}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="text-sm text-gray-900">
                          {position.crypto_balance.toFixed(6)}
                        </div>
                        <div className="text-sm text-gray-500">
                          ${position.usd_balance.toFixed(2)} USD
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="text-sm font-medium text-gray-900">
                          ${position.total_value.toFixed(2)}
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className={`text-sm font-medium ${
                          position.pnl_24h >= 0 ? 'text-success-600' : 'text-danger-600'
                        }`}>
                          {position.pnl_24h >= 0 ? '+' : ''}${position.pnl_24h.toFixed(2)}
                        </div>
                        <div className={`text-xs ${
                          position.pnl_24h_percentage >= 0 ? 'text-success-500' : 'text-danger-500'
                        }`}>
                          {position.pnl_24h_percentage >= 0 ? '+' : ''}{position.pnl_24h_percentage.toFixed(2)}%
                        </div>
                      </td>
                      <td className="table-cell">
                        {position.last_action ? (
                          <span className={`status-${position.last_action}`}>
                            {position.last_action.toUpperCase()}
                          </span>
                        ) : (
                          <span className="status-hold">HOLD</span>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}

export default Dashboard
