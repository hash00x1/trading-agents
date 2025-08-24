import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { ChevronDown } from 'lucide-react'
import apiService from '../services/api'
import TradeHistory from '../components/Trading/TradeHistory'
import LoadingSpinner from '../components/UI/LoadingSpinner'

const Trading: React.FC = () => {
  const [selectedCrypto, setSelectedCrypto] = useState<string>('')

  const { data: cryptos, isLoading: cryptosLoading } = useQuery({
    queryKey: ['cryptos'],
    queryFn: apiService.getCryptos,
  })

  const { data: prices } = useQuery({
    queryKey: ['prices'],
    queryFn: apiService.getCurrentPrices,
    refetchInterval: 30000,
  })

  React.useEffect(() => {
    if (cryptos && cryptos.cryptos.length > 0 && !selectedCrypto) {
      setSelectedCrypto(cryptos.cryptos[0])
    }
  }, [cryptos, selectedCrypto])

  if (cryptosLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trading</h1>
          <p className="text-gray-600 mt-1">Monitor trading activity and performance</p>
        </div>
        
        {/* Crypto Selector */}
        <div className="relative">
          <select
            value={selectedCrypto}
            onChange={(e) => setSelectedCrypto(e.target.value)}
            className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            {cryptos?.cryptos.map((crypto) => (
              <option key={crypto} value={crypto}>
                {crypto.charAt(0).toUpperCase() + crypto.slice(1)}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* Current Price Info */}
      {selectedCrypto && prices && (
        <motion.div variants={itemVariants}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="metric-card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Current Price</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${prices[selectedCrypto]?.current_price?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || 'N/A'}
                  </p>
                </div>
                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-primary-600 font-semibold">
                    {selectedCrypto.slice(0, 2).toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            <div className="metric-card">
              <div>
                <p className="text-sm font-medium text-gray-600">Last Updated</p>
                <p className="text-lg font-semibold text-gray-900">
                  {prices[selectedCrypto]?.timestamp 
                    ? new Date(prices[selectedCrypto].timestamp).toLocaleTimeString()
                    : 'N/A'
                  }
                </p>
              </div>
            </div>

            <div className="metric-card">
              <div>
                <p className="text-sm font-medium text-gray-600">Status</p>
                <div className="flex items-center mt-1">
                  <div className="w-2 h-2 bg-success-500 rounded-full mr-2"></div>
                  <p className="text-lg font-semibold text-gray-900">Active</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Performance Metrics for Selected Crypto */}
      {selectedCrypto && (
        <motion.div variants={itemVariants}>
          <PerformanceMetrics slug={selectedCrypto} />
        </motion.div>
      )}

      {/* Trade History */}
      <motion.div variants={itemVariants}>
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-medium text-gray-900">
              Trade History - {selectedCrypto.charAt(0).toUpperCase() + selectedCrypto.slice(1)}
            </h3>
          </div>
          {selectedCrypto && <TradeHistory slug={selectedCrypto} limit={50} />}
        </div>
      </motion.div>
    </motion.div>
  )
}

const PerformanceMetrics: React.FC<{ slug: string }> = ({ slug }) => {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['performance', slug],
    queryFn: () => apiService.getPerformanceMetrics(slug),
  })

  if (isLoading) {
    return (
      <div className="card">
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      </div>
    )
  }

  if (!metrics || metrics.length === 0) {
    return (
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
        <p className="text-gray-500">No performance data available</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {metrics.map((metric) => (
          <div key={metric.period} className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">{metric.period}</span>
              <span className="text-xs text-gray-500">{metric.trades_count} trades</span>
            </div>
            <div className={`text-xl font-bold ${
              metric.pnl >= 0 ? 'text-success-600' : 'text-danger-600'
            }`}>
              {metric.pnl >= 0 ? '+' : ''}${metric.pnl.toFixed(2)}
            </div>
            <div className={`text-sm ${
              metric.pnl_percentage >= 0 ? 'text-success-500' : 'text-danger-500'
            }`}>
              {metric.pnl_percentage >= 0 ? '+' : ''}{metric.pnl_percentage.toFixed(2)}%
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Trading
