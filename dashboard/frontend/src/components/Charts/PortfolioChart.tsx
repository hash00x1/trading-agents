import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useQuery } from '@tanstack/react-query'
import apiService from '../../services/api'

// Mock data generator for portfolio performance
const generateMockData = () => {
  const data = []
  const now = new Date()
  
  for (let i = 23; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000).toISOString()
    const baseValue = 100000
    const variation = Math.sin(i * 0.3) * 5000 + Math.random() * 2000 - 1000
    
    data.push({
      timestamp,
      time: new Date(timestamp).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      }),
      value: baseValue + variation,
      pnl: variation
    })
  }
  
  return data
}

const PortfolioChart: React.FC = () => {
  const { data: portfolio } = useQuery({
    queryKey: ['portfolio-summary'],
    queryFn: apiService.getPortfolioSummary,
  })

  // Use mock data for now - in production, this would come from historical data API
  const chartData = generateMockData()

  const formatValue = (value: number) => {
    return `$${(value / 1000).toFixed(1)}K`
  }

  const formatTooltip = (value: number, name: string) => {
    if (name === 'value') {
      return [`$${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`, 'Portfolio Value']
    }
    return [value, name]
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis 
            dataKey="time" 
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#64748b' }}
          />
          <YAxis 
            tickFormatter={formatValue}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 12, fill: '#64748b' }}
          />
          <Tooltip 
            formatter={formatTooltip}
            labelStyle={{ color: '#1f2937' }}
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
            stroke="#0ea5e9" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#0ea5e9' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default PortfolioChart
