import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react'
import apiService from '../services/api'
import LoadingSpinner from '../components/UI/LoadingSpinner'

const Portfolio: React.FC = () => {
  const { data: portfolio, isLoading } = useQuery({
    queryKey: ['portfolio-summary'],
    queryFn: apiService.getPortfolioSummary,
    refetchInterval: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  if (!portfolio) {
    return <div className="text-center py-12">Failed to load portfolio data</div>
  }

  const pieData = Object.entries(portfolio.positions)
    .filter(([, position]) => position.total_value > 0)
    .map(([slug, position]) => ({
      name: slug,
      value: position.total_value,
      percentage: (position.total_value / portfolio.total_usd_value) * 100
    }))

  const barData = Object.entries(portfolio.positions)
    .sort(([,a], [,b]) => b.total_value - a.total_value)
    .slice(0, 10)
    .map(([slug, position]) => ({
      name: slug.charAt(0).toUpperCase() + slug.slice(1),
      value: position.total_value,
      pnl: position.pnl_24h
    }))

  const COLORS = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316']

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

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Portfolio</h1>
        <p className="text-gray-600 mt-1">
          Total Value: ${portfolio.total_usd_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </p>
      </div>

      {/* Portfolio Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={itemVariants}>
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Asset Allocation</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percentage }) => `${name} ${percentage.toFixed(1)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number) => [`$${value.toFixed(2)}`, 'Value']}
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants}>
          <div className="card">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Position Values</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="name" 
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
                    formatter={(value: number) => [`$${value.toFixed(2)}`, 'Value']}
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                    }}
                  />
                  <Bar dataKey="value" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Detailed Positions */}
      <motion.div variants={itemVariants}>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Detailed Positions</h3>
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              portfolio.total_pnl >= 0 
                ? 'bg-success-100 text-success-800' 
                : 'bg-danger-100 text-danger-800'
            }`}>
              {portfolio.total_pnl >= 0 ? (
                <TrendingUp className="w-4 h-4 mr-1" />
              ) : (
                <TrendingDown className="w-4 h-4 mr-1" />
              )}
              {portfolio.total_pnl >= 0 ? '+' : ''}${portfolio.total_pnl.toFixed(2)} 24h
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Asset</th>
                  <th className="table-header">Holdings</th>
                  <th className="table-header">Current Price</th>
                  <th className="table-header">Market Value</th>
                  <th className="table-header">USD Balance</th>
                  <th className="table-header">Total Value</th>
                  <th className="table-header">24h PnL</th>
                  <th className="table-header">Allocation</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(portfolio.positions)
                  .sort(([,a], [,b]) => b.total_value - a.total_value)
                  .map(([slug, position]) => (
                    <tr key={slug} className="hover:bg-gray-50">
                      <td className="table-cell">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                              <span className="text-sm font-medium text-primary-600">
                                {slug.slice(0, 2).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 capitalize">
                              {slug}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="text-sm text-gray-900">
                          {position.crypto_balance.toFixed(6)}
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="text-sm text-gray-900">
                          ${position.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="text-sm text-gray-900">
                          ${position.crypto_value.toFixed(2)}
                        </div>
                      </td>
                      <td className="table-cell">
                        <div className="text-sm text-gray-900">
                          ${position.usd_balance.toFixed(2)}
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
                        <div className="text-sm text-gray-900">
                          {((position.total_value / portfolio.total_usd_value) * 100).toFixed(1)}%
                        </div>
                        <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                          <div 
                            className="bg-primary-600 h-2 rounded-full" 
                            style={{ 
                              width: `${Math.min(100, (position.total_value / portfolio.total_usd_value) * 100)}%` 
                            }}
                          ></div>
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

export default Portfolio
