# Poetry Integration Guide for Binance Wallet Integration

This guide explains how to properly integrate the Binance wallet integration with the existing crypto_agents Poetry project.

## 🎯 Quick Start

Since crypto_agents already uses Poetry for dependency management, the integration process is streamlined:

### 1. Add Dependencies

The required dependencies have been added to the main `pyproject.toml`:

```toml
# Binance wallet integration dependencies
aiohttp = "^3.8.0"
websockets = "^11.0.0"
```

### 2. Install Dependencies

```bash
# Install all dependencies including the new ones
poetry install

# Activate the Poetry environment
poetry shell
```

### 3. Run Setup (Optional)

The automated setup script is Poetry-aware:

```bash
poetry run python binance_wallet_integration/setup_integration.py
```

## 🔧 Development Workflow

### Running Examples

```bash
# Run basic usage examples
poetry run python binance_wallet_integration/examples/basic_usage.py

# Set environment variables for testing
export BINANCE_ENVIRONMENT=testnet
export BINANCE_API_KEY=your_testnet_key
export BINANCE_API_SECRET=your_testnet_secret
poetry run python binance_wallet_integration/examples/basic_usage.py
```

### Running Tests

```bash
# Run all tests
poetry run pytest binance_wallet_integration/tests/ -v

# Run only unit tests (no API keys needed)
poetry run pytest binance_wallet_integration/tests/ -k "not integration" -v

# Run integration tests (requires API keys)
poetry run pytest binance_wallet_integration/tests/ -m integration -v
```

### Running the Main crypto_agents System

```bash
# Run the existing crypto_agents system
poetry run python tests/main.py

# Or use the Poetry script if defined
poetry run main
```

## 🔄 Integration with Existing crypto_agents Code

### Method 1: Direct Integration (Recommended)

Modify the existing `base_workflow/agents/portfolio_manager.py` to use the Binance integration:

```python
import asyncio
from binance_wallet_integration.crypto_agents_adapter import CryptoAgentsAdapter, Environment

def portfolio_manager(state: AgentState):
    # ... existing logic ...
    
    # Replace the existing buy/sell/hold calls
    if decision == 'Buy':
        if dollar_balance > 0:
            buy_quantity = calculate_buy_quantity(dollar_balance, crypto_price)
            
            # New: Use Binance integration
            async def execute_buy():
                async with CryptoAgentsAdapter(Environment.TESTNET) as adapter:
                    return await adapter.execute_buy_order(
                        slug=slug,
                        amount=buy_quantity,
                        price=crypto_price,
                        remaining_cryptos=buy_quantity
                    )
            
            action = asyncio.run(execute_buy())
        else:
            # Keep existing hold logic
            action = hold(slug=slug)
    
    # Similar changes for sell operations
    elif decision == 'Sell':
        if token_balance > 0:
            async def execute_sell():
                async with CryptoAgentsAdapter(Environment.TESTNET) as adapter:
                    return await adapter.execute_sell_order(
                        slug=slug,
                        amount=token_balance,
                        price=crypto_price,
                        remaining_dollar=value
                    )
            
            action = asyncio.run(execute_sell())
        else:
            action = hold(slug=slug)
    
    # ... rest of existing logic ...
```

### Method 2: Replace Price Function

Update the `get_real_time_price` function in `base_workflow/tools/api_price.py`:

```python
import asyncio
from binance_wallet_integration.crypto_agents_adapter import CryptoAgentsAdapter, Environment

def get_real_time_price(symbol: str, exchange_id: str = 'binance') -> float:
    """
    Get the real-time price using Binance integration.
    """
    async def get_price():
        async with CryptoAgentsAdapter(Environment.TESTNET) as adapter:
            return await adapter.get_real_time_price(symbol)
    
    return asyncio.run(get_price())
```

## 🏗️ Project Structure Integration

The Binance integration fits seamlessly into the existing project structure:

```
crypto_agents/
├── pyproject.toml                    # ✅ Updated with new dependencies
├── poetry.lock                       # ✅ Will be updated by Poetry
├── base_workflow/                    # ✅ Existing crypto_agents code
│   ├── agents/
│   │   └── portfolio_manager.py      # 🔄 Modify to use Binance integration
│   └── tools/
│       └── api_price.py              # 🔄 Optionally replace with Binance
├── binance_wallet_integration/       # 🆕 New Binance integration
│   ├── __init__.py
│   ├── client.py
│   ├── order_manager.py
│   ├── crypto_agents_adapter.py      # 🎯 Main integration point
│   └── examples/
└── tests/
    └── main.py                       # ✅ Existing crypto_agents tests
```

## 🔒 Environment Configuration

### For Development (Testnet)

Create a `.env` file in the project root:

```bash
# Binance Integration
BINANCE_ENVIRONMENT=testnet
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret

# Risk Management
BINANCE_MAX_POSITION_SIZE_USD=1000.0
BINANCE_MAX_DAILY_LOSS_USD=100.0
BINANCE_MIN_ORDER_SIZE_USD=10.0

# Existing crypto_agents env vars
OPENAI_API_KEY=your_openai_key
# ... other existing variables
```

### For Production (Use with Extreme Caution)

```bash
# ONLY change this when you're ready for live trading
BINANCE_ENVIRONMENT=mainnet
BINANCE_API_KEY=your_mainnet_api_key
BINANCE_API_SECRET=your_mainnet_api_secret
```

## 🧪 Testing Strategy

### 1. Unit Tests (No API Keys Required)

```bash
poetry run pytest binance_wallet_integration/tests/ -k "not integration"
```

### 2. Integration Tests (Testnet API Keys)

```bash
export BINANCE_API_KEY=your_testnet_key
export BINANCE_API_SECRET=your_testnet_secret
poetry run pytest binance_wallet_integration/tests/ -m integration
```

### 3. End-to-End Testing

```bash
# Test the complete crypto_agents system with Binance integration
export BINANCE_ENVIRONMENT=testnet
poetry run python tests/main.py
```

## 🚀 Deployment Checklist

- [ ] Dependencies added to `pyproject.toml`
- [ ] Environment variables configured
- [ ] Tests passing with testnet
- [ ] Integration points updated in crypto_agents code
- [ ] Risk limits configured appropriately
- [ ] Monitoring and logging set up
- [ ] Emergency stop procedures in place

## 📞 Troubleshooting

### Poetry Environment Issues

```bash
# Reset Poetry environment
poetry env remove python
poetry install

# Check Poetry environment
poetry env info

# Activate shell
poetry shell
```

### Import Issues

```bash
# Ensure you're in the Poetry environment
poetry shell

# Check Python path
poetry run python -c "import sys; print(sys.path)"

# Verify Binance integration import
poetry run python -c "from binance_wallet_integration import BinanceClient; print('✅ Import successful')"
```

### API Connection Issues

```bash
# Test basic connectivity
poetry run python -c "
import asyncio
from binance_wallet_integration import BinanceClient, ConfigManager, Environment

async def test():
    config = ConfigManager(Environment.TESTNET)
    async with BinanceClient(config) as client:
        info = await client.get_exchange_info()
        print(f'✅ Connected to Binance {config.environment.value}')

asyncio.run(test())
"
```

---

**⚡ Ready to trade with Poetry?** The integration is designed to work seamlessly with your existing Poetry workflow while adding professional-grade trading capabilities!

