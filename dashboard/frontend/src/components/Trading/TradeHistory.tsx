import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import apiService from '../../services/api'
import LoadingSpinner from '../UI/LoadingSpinner'

interface TradeHistoryProps {
  slug?: string
  limit?: number
  compact?: boolean
}

const TradeHistory: React.FC<TradeHistoryProps> = ({ 
  slug, 
  limit = 20, 
  compact = false 
}) => {
  const { data: cryptos } = useQuery({
    queryKey: ['cryptos'],
    queryFn: apiService.getCryptos,
  })

  // Get trades for the first crypto or specified slug
  const targetSlug = slug || cryptos?.cryptos[0] || 'bitcoin'
  
  const { data: trades, isLoading } = useQuery({
    queryKey: ['trades', targetSlug, limit],
    queryFn: () => apiService.getTrades(targetSlug, limit),
    enabled: !!targetSlug,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    )
  }

  if (!trades || trades.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No trades found for {targetSlug}
      </div>
    )
  }

  const getActionIcon = (action: string | null) => {
    switch (action) {
      case 'buy':
        return <TrendingUp className="h-4 w-4 text-success-600" />
      case 'sell':
        return <TrendingDown className="h-4 w-4 text-danger-600" />
      default:
        return <Minus className="h-4 w-4 text-gray-400" />
    }
  }

  const getActionColor = (action: string | null) => {
    switch (action) {
      case 'buy':
        return 'text-success-600'
      case 'sell':
        return 'text-danger-600'
      default:
        return 'text-gray-500'
    }
  }

  if (compact) {
    return (
      <div className="space-y-3">
        {trades.slice(0, 5).map((trade) => (
          <div key={trade.id} className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getActionIcon(trade.action)}
              <div>
                <div className="text-sm font-medium text-gray-900 capitalize">
                  {trade.action || 'Hold'} {trade.slug}
                </div>
                <div className="text-xs text-gray-500">
                  {format(new Date(trade.timestamp), 'MMM d, HH:mm')}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium text-gray-900">
                {trade.amount > 0 ? trade.amount.toFixed(4) : '-'}
              </div>
              <div className="text-xs text-gray-500">
                ${trade.price.toFixed(2)}
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="table-header">Time</th>
            <th className="table-header">Action</th>
            <th className="table-header">Amount</th>
            <th className="table-header">Price</th>
            <th className="table-header">Value</th>
            <th className="table-header">Balance</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {trades.map((trade) => (
            <tr key={trade.id} className="hover:bg-gray-50">
              <td className="table-cell">
                <div className="text-sm text-gray-900">
                  {format(new Date(trade.timestamp), 'MMM d, yyyy')}
                </div>
                <div className="text-xs text-gray-500">
                  {format(new Date(trade.timestamp), 'HH:mm:ss')}
                </div>
              </td>
              <td className="table-cell">
                <div className="flex items-center space-x-2">
                  {getActionIcon(trade.action)}
                  <span className={`text-sm font-medium ${getActionColor(trade.action)}`}>
                    {trade.action?.toUpperCase() || 'HOLD'}
                  </span>
                </div>
              </td>
              <td className="table-cell">
                <div className="text-sm text-gray-900">
                  {trade.amount > 0 ? trade.amount.toFixed(6) : '-'}
                </div>
              </td>
              <td className="table-cell">
                <div className="text-sm text-gray-900">
                  ${trade.price.toFixed(2)}
                </div>
              </td>
              <td className="table-cell">
                <div className="text-sm text-gray-900">
                  {trade.amount > 0 ? `$${(trade.amount * trade.price).toFixed(2)}` : '-'}
                </div>
              </td>
              <td className="table-cell">
                <div className="text-sm text-gray-900">
                  {trade.remaining_cryptos.toFixed(6)} {targetSlug.toUpperCase()}
                </div>
                <div className="text-xs text-gray-500">
                  ${trade.remaining_dollar.toFixed(2)} USD
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default TradeHistory
