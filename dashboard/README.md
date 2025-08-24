# 🚀 Crypto Trading Dashboard

A professional, real-time trading dashboard for your crypto agents system with comprehensive analytics, portfolio management, and n8n.io integration.

## ✨ Features

### 🎯 Core Dashboard
- **Real-time Portfolio Overview** - Live balance tracking with 24h/7d/30d PnL
- **Professional Trading Interface** - Clean, responsive design with modern UI/UX
- **Multi-Asset Support** - Bitcoin, Ethereum, Pepe, Dogecoin, Tether, and more
- **Performance Analytics** - Detailed metrics, win rates, and performance charts

### 📊 Analytics & Insights
- **Portfolio Performance Charts** - Interactive charts with historical data
- **Trade History Analysis** - Comprehensive trade logs with filtering
- **Risk Metrics** - Win rates, Sharpe ratios, maximum drawdown
- **Asset Allocation** - Visual pie charts and performance breakdowns

### 🔗 Integration Features
- **Binance Integration** - Real-time trading via Binance API (testnet/mainnet)
- **WebSocket Support** - Live updates without page refresh
- **n8n.io Webhook Ready** - Trigger trades from external workflows
- **RESTful API** - Complete API for external integrations

### 🛡️ Security & Deployment
- **Docker Ready** - Complete containerization with docker-compose
- **Production Optimized** - Nginx reverse proxy, rate limiting, security headers
- **Environment Configuration** - Flexible deployment options (paper/testnet/live)
- **Health Monitoring** - Built-in health checks and status monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend │    │ Binance API     │
│   (TypeScript)   │◄──►│   (Python)      │◄──►│ Integration     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌─────────┐              ┌─────────┐           ┌─────────┐
    │ Nginx   │              │ SQLite  │           │ Agent   │
    │ Proxy   │              │ Trading │           │ System  │
    └─────────┘              │ Data    │           └─────────┘
                            └─────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Your crypto_agents system running
- Binance API credentials (for live trading)

### 1. Clone and Setup

```bash
cd /path/to/crypto_agents
# Dashboard is already created in ./dashboard/
```

### 2. Configure Environment

```bash
cp dashboard/env.example dashboard/.env
# Edit dashboard/.env with your settings:
# - BINANCE_API_KEY=your_testnet_key
# - BINANCE_API_SECRET=your_testnet_secret
# - TRADING_MODE=live (or paper for simulation)
```

### 3. Launch Dashboard

```bash
cd dashboard
docker-compose up -d
```

### 4. Access Your Dashboard

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📡 n8n.io Integration

### Webhook Endpoint
```
POST http://localhost:8000/webhook/trade
```

### Example Payload
```json
{
  "action": "buy",
  "slug": "bitcoin", 
  "amount": 0.001,
  "price": 45000
}
```

### n8n.io Workflow Example
1. **Trigger Node** - Webhook/Schedule/External signal
2. **Decision Logic** - Your trading conditions
3. **HTTP Request Node** - POST to webhook endpoint
4. **Response Handler** - Process trade confirmation

## 🎛️ API Endpoints

### Portfolio & Analytics
- `GET /api/portfolio/summary` - Complete portfolio overview
- `GET /api/performance/{slug}` - Performance metrics by crypto
- `GET /api/trades/{slug}` - Trade history for specific crypto
- `GET /api/prices` - Current prices for all tracked assets

### Trading & Control
- `POST /webhook/trade` - Execute trades via webhook
- `GET /api/balances` - Real Binance account balances
- `WebSocket /ws` - Real-time updates

### System Status
- `GET /` - Health check and system status
- `GET /api/cryptos` - List of available cryptocurrencies

## 🔧 Configuration Options

### Trading Modes
- **Paper Trading** - Simulation mode using local database
- **Testnet** - Binance testnet trading (recommended for testing)
- **Mainnet** - Live trading with real money (production)

### Environment Variables
```bash
BINANCE_ENVIRONMENT=testnet|mainnet|paper
TRADING_MODE=live|paper
MAX_POSITION_SIZE_USD=1000
MIN_ORDER_SIZE_USD=10
```

### Risk Management
Built-in position sizing limits and order validation:
- Maximum position size per trade
- Minimum order size requirements
- Balance validation before execution

## 📊 Dashboard Features

### 🏠 Dashboard Page
- Portfolio value overview
- 24h PnL with percentage change
- Active positions summary
- Recent trading activity
- Performance charts

### 💼 Portfolio Page
- Asset allocation pie charts
- Detailed position breakdown
- Individual asset performance
- Balance distribution analysis

### 📈 Trading Page
- Live price feeds
- Trade execution history
- Performance metrics by timeframe
- Asset-specific analytics

### 📉 Analytics Page
- Monthly PnL trends
- Portfolio growth charts
- Win rate analysis
- Asset performance comparison

### ⚙️ Settings Page
- Trading configuration
- System status monitoring
- API endpoint documentation
- Webhook setup guide

## 🔐 Security Features

- **Rate Limiting** - API and webhook endpoint protection
- **CORS Protection** - Secure frontend-backend communication
- **Input Validation** - Comprehensive request validation
- **Health Checks** - Service monitoring and auto-recovery
- **Non-root Containers** - Security-hardened Docker containers

## 🚀 Production Deployment

### Cloud Deployment (Recommended)

```bash
# For VPS/Cloud server:
1. Clone repository to your server
2. Configure environment variables
3. Set up SSL certificates in ./ssl/
4. Update nginx.conf with your domain
5. Run: docker-compose -f docker-compose.prod.yml up -d
```

### n8n.io Cloud Integration

```bash
# Use public URL for webhooks:
https://your-domain.com/webhook/trade

# Or ngrok for development:
ngrok http 8000
# Use: https://xyz.ngrok.io/webhook/trade
```

## 📱 Mobile Responsive

The dashboard is fully responsive and works perfectly on:
- Desktop computers
- Tablets 
- Mobile phones
- All modern browsers

## 🔄 Real-time Updates

- **WebSocket Connection** - Live price feeds and trade notifications
- **Auto-refresh** - Portfolio data updates every 30 seconds
- **Push Notifications** - Trade execution confirmations
- **Live Charts** - Real-time portfolio performance visualization

## 🛠️ Development

### Local Development Setup

```bash
# Backend
cd dashboard/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend  
cd dashboard/frontend
npm install
npm run dev  # Runs on port 3000
```

### Extending the Dashboard

- **Add New Charts** - Modify components in `src/components/Charts/`
- **New API Endpoints** - Extend `backend/main.py`
- **Custom Analytics** - Add functions in `backend/main.py`
- **UI Components** - Create reusable components in `src/components/UI/`

## 📈 Performance Metrics

The dashboard tracks and displays:
- **Total Portfolio Value** - Real-time USD value
- **PnL Analysis** - 24h, 7d, 30d performance
- **Win/Loss Ratios** - Trading success metrics
- **Asset Performance** - Individual crypto analysis
- **Trade Frequency** - Activity monitoring
- **Risk Metrics** - Position sizing and exposure

## 🎯 Key Benefits

1. **Professional Interface** - Clean, modern design suitable for serious trading
2. **Real-time Data** - Live updates keep you informed of market changes
3. **Comprehensive Analytics** - Deep insights into trading performance
4. **Easy Integration** - Works seamlessly with n8n.io and other automation tools
5. **Scalable Architecture** - Docker-based deployment scales with your needs
6. **Security First** - Built with production security best practices

## 📞 Support & Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **WebSocket Events**: Real-time price updates and trade notifications
- **Error Handling**: Comprehensive error messages and fallback strategies
- **Logging**: Detailed logs for debugging and monitoring

---

**Ready to transform your crypto trading with professional-grade analytics and automation!** 🚀

Start with paper trading to test the system, then upgrade to testnet, and finally go live when you're confident in your setup.
