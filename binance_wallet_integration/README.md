# Binance Wallet Integration

Professional, secure integration with Binance API for real-time crypto trading with the crypto_agents system.

## 🚀 Features

- **Professional Architecture**: Modular design with clear separation of concerns
- **Security First**: HMAC-SHA256 signing, API key validation, and comprehensive security measures
- **Rate Limiting**: Advanced rate limiting to prevent API bans
- **WebSocket Streams**: Real-time market data from Binance WebSocket API
- **Risk Management**: Built-in position limits, order validation, and safety checks
- **Environment Support**: Testnet, Mainnet, and Paper trading modes
- **Easy Integration**: Drop-in replacement for existing crypto_agents trading functions

## 📋 Prerequisites

- Python 3.8+
- Binance API keys (for live trading)
- Required dependencies (see requirements.txt)

## 🛠 Installation

### Option 1: Using Poetry (Recommended for crypto_agents)

Since crypto_agents uses Poetry for dependency management:

1. The integration is already included in your crypto_agents repository
2. Add dependencies to your Poetry project:
```bash
# Add required dependencies
poetry add aiohttp websockets pytest pytest-asyncio

# Install all dependencies
poetry install
```

3. Activate the Poetry environment:
```bash
poetry shell
```

### Option 2: Using pip

If you prefer pip installation:

```bash
pip install aiohttp websockets pytest pytest-asyncio
```

### Environment Setup

Set up environment variables:
```bash
# For testnet (recommended for development)
export BINANCE_ENVIRONMENT=testnet
export BINANCE_API_KEY=your_testnet_api_key
export BINANCE_API_SECRET=your_testnet_api_secret

# For mainnet (production only)
export BINANCE_ENVIRONMENT=mainnet
export BINANCE_API_KEY=your_mainnet_api_key
export BINANCE_API_SECRET=your_mainnet_api_secret

# For paper trading (simulation)
export BINANCE_ENVIRONMENT=paper
```

## 🔧 Quick Start

### Basic Usage

```python
import asyncio
from binance_wallet_integration import BinanceClient, ConfigManager, Environment

async def main():
    # Initialize for testnet
    config = ConfigManager(Environment.TESTNET)
    
    async with BinanceClient(config) as client:
        # Get current Bitcoin price
        price = await client.get_symbol_price("BTCUSDT")
        print(f"BTC Price: ${price['price']}")
        
        # Get account balances
        account = await client.get_account_info()
        print("Account balances:")
        for balance in account['balances']:
            if float(balance['free']) > 0:
                print(f"  {balance['asset']}: {balance['free']}")

asyncio.run(main())
```

### Order Management

```python
from binance_wallet_integration import OrderManager
from binance_wallet_integration.order_manager import OrderRequest, OrderSide, OrderType

async def place_orders():
    config = ConfigManager(Environment.TESTNET)
    
    async with BinanceClient(config) as client:
        order_manager = OrderManager(client, config)
        await order_manager.initialize()
        
        # Place a market buy order
        result = await order_manager.buy_market("BTCUSDT", 0.001)
        print(f"Order result: {result.success}")
        
        # Place a limit sell order
        result = await order_manager.sell_limit("BTCUSDT", 0.001, 55000.0)
        print(f"Order ID: {result.order_id}")

asyncio.run(place_orders())
```

### WebSocket Streams

```python
from binance_wallet_integration import WebSocketManager

async def stream_data():
    config = ConfigManager(Environment.TESTNET)
    ws_manager = WebSocketManager(config)
    
    async def handle_trades(data):
        trade = data['data']
        print(f"BTC Trade: {trade['q']} @ ${trade['p']}")
    
    await ws_manager.start()
    await ws_manager.subscribe_to_trades("BTCUSDT", handle_trades)
    
    # Listen for 30 seconds
    await asyncio.sleep(30)
    await ws_manager.stop()

asyncio.run(stream_data())
```

## 🔄 Integration with Crypto Agents

The integration provides a seamless adapter for the existing crypto_agents system:

```python
from binance_wallet_integration.crypto_agents_adapter import CryptoAgentsAdapter, Environment

async def crypto_agents_integration():
    async with CryptoAgentsAdapter(Environment.TESTNET) as adapter:
        # Replace existing buy() function
        result = await adapter.execute_buy_order(
            slug="bitcoin",
            amount=0.001,
            price=50000.0,
            remaining_cryptos=0.001
        )
        print(result)
        
        # Replace existing sell() function  
        result = await adapter.execute_sell_order(
            slug="bitcoin",
            amount=0.001,
            price=55000.0,
            remaining_dollar=55.0
        )
        print(result)
        
        # Get real-time price (compatible with existing interface)
        price = await adapter.get_real_time_price("BTC")
        print(f"BTC Price: ${price}")

asyncio.run(crypto_agents_integration())
```

## 🏗 Architecture

```
binance_wallet_integration/
├── __init__.py                 # Main module exports
├── config.py                   # Configuration management
├── security.py                 # Security and signing
├── rate_limiter.py            # Rate limiting system
├── client.py                   # REST API client
├── websocket_manager.py        # WebSocket streams
├── order_manager.py            # Order management
├── crypto_agents_adapter.py    # Integration adapter
├── examples/
│   └── basic_usage.py         # Usage examples
└── tests/
    └── test_integration.py    # Comprehensive tests
```

### Key Components

- **ConfigManager**: Environment and configuration handling
- **SecurityManager**: API key validation and request signing
- **RateLimitManager**: Sophisticated rate limiting to prevent bans
- **BinanceClient**: Professional REST API client
- **WebSocketManager**: Real-time data streams
- **OrderManager**: Trade execution with risk controls
- **CryptoAgentsAdapter**: Seamless integration layer

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BINANCE_ENVIRONMENT` | Trading environment (testnet/mainnet/paper) | testnet |
| `BINANCE_API_KEY` | Binance API key | Required for live trading |
| `BINANCE_API_SECRET` | Binance API secret | Required for live trading |
| `BINANCE_MAX_POSITION_SIZE_USD` | Maximum position size | 10000.0 |
| `BINANCE_MAX_DAILY_LOSS_USD` | Maximum daily loss | 1000.0 |
| `BINANCE_MIN_ORDER_SIZE_USD` | Minimum order size | 10.0 |

### Trading Environments

1. **TESTNET** (Recommended for development)
   - Uses Binance testnet
   - Fake money, real market data
   - Safe for testing

2. **MAINNET** (Production only)
   - Real Binance trading
   - Real money at risk
   - Use with extreme caution

3. **PAPER** (Simulation)
   - No API calls to Binance
   - Simulated orders
   - Good for strategy testing

## 🛡️ Security Features

- **API Key Validation**: Comprehensive validation of API credentials
- **Request Signing**: HMAC-SHA256 signing for authenticated requests
- **Rate Limiting**: Prevents API bans with intelligent rate limiting
- **Order Validation**: Validates all orders before execution
- **Risk Limits**: Configurable position and loss limits
- **Secure Defaults**: Testnet by default, explicit mainnet opt-in

## 📊 Rate Limits

The system automatically manages Binance API rate limits:

- **Request Weight**: 1,200 per minute
- **Orders**: 50 per 10 seconds, 160,000 per 24 hours
- **WebSocket**: 300 connections per 5 minutes

## 🧪 Testing

Run the comprehensive test suite:

### With Poetry (Recommended)

```bash
# Run all tests with Poetry
poetry run pytest binance_wallet_integration/tests/ -v

# Run integration tests (requires API keys)
poetry run pytest binance_wallet_integration/tests/ -m integration -v

# Run specific test
poetry run pytest binance_wallet_integration/tests/test_integration.py::TestOrderManager -v
```

### With pip

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest binance_wallet_integration/tests/ -v

# Run integration tests (requires API keys)
pytest binance_wallet_integration/tests/ -m integration -v

# Run specific test
pytest binance_wallet_integration/tests/test_integration.py::TestOrderManager -v
```

## 📖 Examples

See the `examples/` directory for comprehensive usage examples:

- `basic_usage.py`: Complete examples of all features
- Integration with crypto_agents portfolio manager
- WebSocket stream handling
- Order management workflows

### Running Examples

With Poetry:
```bash
poetry run python binance_wallet_integration/examples/basic_usage.py
```

With pip:
```bash
python binance_wallet_integration/examples/basic_usage.py
```

## 🔧 Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   ValueError: Missing Binance API credentials
   ```
   - Ensure `BINANCE_API_KEY` and `BINANCE_API_SECRET` are set
   - Verify keys are for the correct environment (testnet vs mainnet)

2. **Rate Limit Errors**
   ```
   BinanceAPIError: Rate limit exceeded
   ```
   - The system handles this automatically with backoff
   - Check if you're making too many manual API calls

3. **Order Validation Errors**
   ```
   ValueError: Order size below minimum
   ```
   - Check Binance minimum order requirements
   - Ensure sufficient balance for the order

4. **WebSocket Connection Issues**
   ```
   Failed to connect to WebSocket
   ```
   - Check internet connection
   - Verify WebSocket endpoints are accessible
   - Check rate limiting for connections

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚨 Risk Warnings

⚠️ **Important**: This system can execute real trades with real money. Always:

1. **Start with testnet** - Never begin with mainnet
2. **Use small amounts** - Test with minimal capital first
3. **Set strict limits** - Configure position and loss limits
4. **Monitor actively** - Never leave automated trading unattended
5. **Have stop mechanisms** - Implement emergency stop procedures

## 📝 License

This integration is part of the crypto_agents project. See the main project license for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review the examples
3. Run the test suite
4. Open an issue with detailed error information

---

**⚡ Ready to trade? Start with testnet and gradually move to production as you gain confidence!**
