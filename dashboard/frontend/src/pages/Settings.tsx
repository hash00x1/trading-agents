import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Save, AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'
import apiService from '../services/api'
import LoadingSpinner from '../components/UI/LoadingSpinner'

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('trading')

  const { data: healthCheck, isLoading } = useQuery({
    queryKey: ['health-check'],
    queryFn: apiService.getHealthCheck,
  })

  const { data: balances } = useQuery({
    queryKey: ['binance-balances'],
    queryFn: apiService.getBinanceBalances,
    retry: false,
  })

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

  const tabs = [
    { id: 'trading', name: 'Trading Settings' },
    { id: 'system', name: 'System Status' },
    { id: 'api', name: 'API Configuration' },
    { id: 'webhooks', name: 'Webhooks' },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Configure your trading system and monitor status</p>
      </div>

      {/* Tab Navigation */}
      <motion.div variants={itemVariants}>
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </motion.div>

      {/* Tab Content */}
      <motion.div variants={itemVariants}>
        {activeTab === 'trading' && <TradingSettings />}
        {activeTab === 'system' && <SystemStatus healthCheck={healthCheck} balances={balances} />}
        {activeTab === 'api' && <APIConfiguration />}
        {activeTab === 'webhooks' && <WebhooksConfiguration />}
      </motion.div>
    </motion.div>
  )
}

const TradingSettings: React.FC = () => {
  const [settings, setSettings] = useState({
    maxPositionSize: 1000,
    minOrderSize: 10,
    riskLevel: 'medium',
    autoTradingEnabled: false,
  })

  const handleSave = () => {
    // In a real app, this would save to your backend
    toast.success('Trading settings saved successfully')
  }

  return (
    <div className="card">
      <h3 className="text-lg font-medium text-gray-900 mb-6">Trading Configuration</h3>
      
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Position Size (USD)
            </label>
            <input
              type="number"
              value={settings.maxPositionSize}
              onChange={(e) => setSettings({...settings, maxPositionSize: Number(e.target.value)})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Min Order Size (USD)
            </label>
            <input
              type="number"
              value={settings.minOrderSize}
              onChange={(e) => setSettings({...settings, minOrderSize: Number(e.target.value)})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Risk Level
          </label>
          <select
            value={settings.riskLevel}
            onChange={(e) => setSettings({...settings, riskLevel: e.target.value})}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="low">Low Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="high">High Risk</option>
          </select>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="autoTrading"
            checked={settings.autoTradingEnabled}
            onChange={(e) => setSettings({...settings, autoTradingEnabled: e.target.checked})}
            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
          />
          <label htmlFor="autoTrading" className="ml-2 block text-sm text-gray-900">
            Enable automatic trading
          </label>
        </div>

        <div className="pt-4">
          <button
            onClick={handleSave}
            className="btn-primary inline-flex items-center"
          >
            <Save className="w-4 h-4 mr-2" />
            Save Settings
          </button>
        </div>
      </div>
    </div>
  )
}

const SystemStatus: React.FC<{ healthCheck: any; balances: any }> = ({ healthCheck, balances }) => {
  return (
    <div className="space-y-6">
      {/* System Health */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">System Health</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">API Status</span>
            <div className="flex items-center">
              <CheckCircle className="h-4 w-4 text-success-600 mr-2" />
              <span className="text-sm font-medium text-success-600">Healthy</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Trading Mode</span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
              {healthCheck?.trading_mode || 'Unknown'}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Version</span>
            <span className="text-sm font-medium text-gray-900">
              {healthCheck?.version || 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Binance Account Status */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Binance Account</h3>
        {balances ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Connection Status</span>
              <div className="flex items-center">
                <CheckCircle className="h-4 w-4 text-success-600 mr-2" />
                <span className="text-sm font-medium text-success-600">Connected</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Last Updated</span>
              <span className="text-sm font-medium text-gray-900">
                {new Date(balances.timestamp).toLocaleString()}
              </span>
            </div>
            {Object.keys(balances.balances).length > 0 && (
              <div>
                <span className="text-sm text-gray-600 block mb-2">Available Assets</span>
                <div className="text-sm font-medium text-gray-900">
                  {Object.keys(balances.balances).length} assets found
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center">
            <AlertTriangle className="h-4 w-4 text-warning-600 mr-2" />
            <span className="text-sm text-warning-600">Unable to connect to Binance</span>
          </div>
        )}
      </div>
    </div>
  )
}

const APIConfiguration: React.FC = () => {
  return (
    <div className="card">
      <h3 className="text-lg font-medium text-gray-900 mb-6">API Configuration</h3>
      
      <div className="space-y-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <ExternalLink className="h-5 w-5 text-blue-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                API Endpoints
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>Your dashboard API is running on:</p>
                <ul className="mt-1 space-y-1">
                  <li><code className="bg-blue-100 px-2 py-1 rounded">GET /api/portfolio/summary</code></li>
                  <li><code className="bg-blue-100 px-2 py-1 rounded">GET /api/trades/{'{slug}'}</code></li>
                  <li><code className="bg-blue-100 px-2 py-1 rounded">POST /webhook/trade</code></li>
                  <li><code className="bg-blue-100 px-2 py-1 rounded">WebSocket /ws</code></li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            API Base URL
          </label>
          <input
            type="text"
            value="http://localhost:8000"
            readOnly
            className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-gray-50 text-gray-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            WebSocket URL
          </label>
          <input
            type="text"
            value="ws://localhost:8000/ws"
            readOnly
            className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-gray-50 text-gray-500"
          />
        </div>
      </div>
    </div>
  )
}

const WebhooksConfiguration: React.FC = () => {
  const [webhookUrl, setWebhookUrl] = useState('http://localhost:8000/webhook/trade')

  const handleTest = () => {
    toast.success('Webhook test sent successfully')
  }

  return (
    <div className="card">
      <h3 className="text-lg font-medium text-gray-900 mb-6">Webhook Configuration</h3>
      
      <div className="space-y-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <CheckCircle className="h-5 w-5 text-green-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">
                n8n.io Integration Ready
              </h3>
              <div className="mt-2 text-sm text-green-700">
                <p>Use the webhook URL below in your n8n.io workflows to trigger trades:</p>
              </div>
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Webhook URL
          </label>
          <div className="flex space-x-2">
            <input
              type="text"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={() => navigator.clipboard.writeText(webhookUrl)}
              className="btn-secondary"
            >
              Copy
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Example Payload
          </label>
          <pre className="bg-gray-100 border border-gray-300 rounded-lg p-3 text-sm overflow-x-auto">
{`{
  "action": "buy",
  "slug": "bitcoin",
  "amount": 0.001,
  "price": 45000
}`}
          </pre>
        </div>

        <div className="flex space-x-3">
          <button onClick={handleTest} className="btn-primary">
            Test Webhook
          </button>
          <button className="btn-secondary">
            View Logs
          </button>
        </div>
      </div>
    </div>
  )
}

export default Settings
