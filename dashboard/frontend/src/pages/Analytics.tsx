import React from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, Target } from 'lucide-react'

// Mock analytics data - in production, this would come from your API
const mockAnalyticsData = {
  monthlyPnL: [
    { month: 'Jan', pnl: 1200, trades: 45 },
    { month: 'Feb', pnl: -800, trades: 38 },
    { month: 'Mar', pnl: 2100, trades: 52 },
    { month: 'Apr', pnl: 1500, trades: 41 },
    { month: 'May', pnl: -300, trades: 29 },
    { month: 'Jun', pnl: 3200, trades: 63 },
  ],
  portfolioGrowth: [
    { date: '2024-01', value: 100000 },
    { date: '2024-02', value: 101200 },
    { date: '2024-03', value: 100400 },
    { date: '2024-04', value: 102500 },
    { date: '2024-05', value: 104000 },
    { date: '2024-06', value: 103700 },
    { date: '2024-07', value: 106900 },
  ],
  cryptoPerformance: [
    { name: 'Bitcoin', winRate: 65, totalTrades: 120, pnl: 4500 },
    { name: 'Ethereum', winRate: 58, totalTrades: 95, pnl: 2800 },
    { name: 'Pepe', winRate: 72, totalTrades: 87, pnl: 1200 },
    { name: 'Dogecoin', winRate: 45, totalTrades: 78, pnl: -800 },
    { name: 'Tether', winRate: 55, totalTrades: 34, pnl: 300 },
  ]
}

const Analytics: React.FC = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  }

  const totalPnL = mockAnalyticsData.monthlyPnL.reduce((sum, month) => sum + month.pnl, 0)
  const totalTrades = mockAnalyticsData.monthlyPnL.reduce((sum, month) => sum + month.trades, 0)
  const winningMonths = mockAnalyticsData.monthlyPnL.filter(month => month.pnl > 0).length
  const winRate = (winningMonths / mockAnalyticsData.monthlyPnL.length) * 100

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600 mt-1">Comprehensive trading performance analysis</p>
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
                <dt className="text-sm font-medium text-gray-500 truncate">Total PnL (6M)</dt>
                <dd className={`text-2xl font-semibold ${totalPnL >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
                  {totalPnL >= 0 ? '+' : ''}${totalPnL.toLocaleString()}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Target className="h-6 w-6 text-warning-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Win Rate</dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {winRate.toFixed(1)}%
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-6 w-6 text-success-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total Trades</dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {totalTrades.toLocaleString()}
                </dd>
              </dl>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingDown className="h-6 w-6 text-danger-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Avg Trade</dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  ${(totalPnL / totalTrades).toFixed(0)}
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly P&L */}
        <motion.div variants={itemVariants}>
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Monthly P&L</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={mockAnalyticsData.monthlyPnL}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="month" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#64748b' }}
                  />
                  <YAxis 
                    tickFormatter={(value) => `$${(value / 1000).toFixed(1)}K`}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#64748b' }}
                  />
                  <Tooltip 
                    formatter={(value: number) => [`$${value.toLocaleString()}`, 'P&L']}
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Bar 
                    dataKey="pnl" 
                    fill="#0ea5e9"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>

        {/* Portfolio Growth */}
        <motion.div variants={itemVariants}>
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Portfolio Growth</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={mockAnalyticsData.portfolioGrowth}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="date" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#64748b' }}
                  />
                  <YAxis 
                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: '#64748b' }}
                  />
                  <Tooltip 
                    formatter={(value: number) => [`$${value.toLocaleString()}`, 'Portfolio Value']}
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#22c55e" 
                    strokeWidth={3}
                    dot={false}
                    activeDot={{ r: 4, fill: '#22c55e' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Crypto Performance Table */}
      <motion.div variants={itemVariants}>
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Asset Performance Analysis</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Asset</th>
                  <th className="table-header">Total Trades</th>
                  <th className="table-header">Win Rate</th>
                  <th className="table-header">Total P&L</th>
                  <th className="table-header">Avg Trade</th>
                  <th className="table-header">Performance</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {mockAnalyticsData.cryptoPerformance
                  .sort((a, b) => b.pnl - a.pnl)
                  .map((crypto) => (
                    <tr key={crypto.name} className="hover:bg-gray-50">
                      <td className="table-cell">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-8 w-8">
                            <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                              <span className="text-xs font-medium text-primary-600">
                                {crypto.name.slice(0, 2).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {crypto.name}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="text-sm text-gray-900">{crypto.totalTrades}</div>
                      </td>
                      <td className="table-cell">
                        <div className="flex items-center">
                          <div className="text-sm text-gray-900">{crypto.winRate}%</div>
                          <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                crypto.winRate >= 60 ? 'bg-success-500' : 
                                crypto.winRate >= 50 ? 'bg-warning-500' : 'bg-danger-500'
                              }`}
                              style={{ width: `${crypto.winRate}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className={`text-sm font-medium ${
                          crypto.pnl >= 0 ? 'text-success-600' : 'text-danger-600'
                        }`}>
                          {crypto.pnl >= 0 ? '+' : ''}${crypto.pnl.toLocaleString()}
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="text-sm text-gray-900">
                          ${(crypto.pnl / crypto.totalTrades).toFixed(0)}
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="flex items-center">
                          {crypto.pnl >= 0 ? (
                            <TrendingUp className="h-4 w-4 text-success-600 mr-1" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-danger-600 mr-1" />
                          )}
                          <span className={`text-sm font-medium ${
                            crypto.winRate >= 60 && crypto.pnl >= 0 ? 'text-success-600' :
                            crypto.winRate >= 50 || crypto.pnl >= 0 ? 'text-warning-600' : 'text-danger-600'
                          }`}>
                            {crypto.winRate >= 60 && crypto.pnl >= 0 ? 'Excellent' :
                             crypto.winRate >= 50 || crypto.pnl >= 0 ? 'Good' : 'Needs Improvement'}
                          </span>
                        </div>
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

export default Analytics
