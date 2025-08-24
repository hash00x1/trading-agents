# Wallet Testing Script

This directory contains a comprehensive wallet testing script for the Binance integration.

## Setup

### 1. Environment Variables

Create a `.env` file in the project root with your Binance API credentials:

```bash
# Binance API Configuration
BINANCE_API_KEY=your_api_key_here

# Choose ONE authentication method:

# Option 1: HMAC-SHA256 (traditional)
BINANCE_API_SECRET=your_api_secret_here

# Option 2: Ed25519 (modern, recommended)
# BINANCE_PRIVATE_KEY_PATH=/path/to/your/test-prv-key.pem

# Environment (testnet recommended for testing)
BINANCE_ENVIRONMENT=testnet
```

### 2. Testnet Setup

1. Go to [https://testnet.binance.vision/](https://testnet.binance.vision/)
2. Log in with GitHub
3. Generate API credentials

#### For HMAC-SHA256:
- Use the standard API Key and Secret provided by the testnet

#### For Ed25519 (recommended):
1. Generate an Ed25519 private key:
   ```bash
   openssl genpkey -algorithm ed25519 -out test-prv-key.pem
   ```
2. Generate the public key:
   ```bash
   openssl pkey -pubout -in test-prv-key.pem -out test-pub-key.pem
   ```
3. Register the public key on the testnet website
4. Set `BINANCE_PRIVATE_KEY_PATH` to the path of your private key file

## Usage

### Run the Wallet Test

```bash
cd tests
python wallet_test.py
```

### What the Test Does

1. **Authentication Test**: Verifies API credentials and connectivity
2. **Balance Check**: Displays all non-zero wallet balances
3. **Trading Permissions**: Checks if trading is allowed for BTCUSDT
4. **Test Order**: Places a small test order (0.0001 BTC ≈ $5)

### Expected Output

```
=== Starting Comprehensive Wallet Test ===
INFO - Testing authentication and connectivity...
INFO - Server time: {'serverTime': 1703123456789}
INFO - Fetching wallet balances...
INFO - Found 5 assets with balances
INFO -   BTC: 1.00000000 (Free: 1.00000000, Locked: 0.00000000)
INFO -   ETH: 10.00000000 (Free: 10.00000000, Locked: 0.00000000)
INFO -   USDT: 10000.00000000 (Free: 10000.00000000, Locked: 0.00000000)
INFO - Checking trading permissions for BTCUSDT...
INFO - Symbol BTCUSDT status: TRADING
INFO - Spot trading allowed: True
INFO - Placing test order: BUY 0.0001 BTCUSDT
INFO - Current BTC price: $50,000.00
INFO - Estimated order cost: $5.00
INFO - === Test Summary: 4/4 tests passed ===

============================================================
WALLET TEST RESULTS
============================================================
Environment: testnet
Success Rate: 100.0%

authentication: ✅ PASS
balances: ✅ PASS
trading_permissions: ✅ PASS
test_order: ✅ PASS
============================================================

Wallet Balances (5 assets):
  BTC: 1.00000000
  ETH: 10.00000000
  USDT: 10000.00000000
  BNB: 100.00000000
  ADA: 1000.00000000
Estimated total value: 1.20000000 BTC

Test Order Result:
  ✅ Successfully placed test order
  Quantity: 0.0001 BTC
  Estimated cost: $5.00
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check your API key and secret/private key path
   - Ensure you're using testnet credentials for testnet environment
   - Verify the private key file exists and is readable

2. **Insufficient Balance**
   - The testnet automatically provides virtual funds
   - If you see zero balances, the testnet may have been reset
   - Wait a few minutes and try again

3. **Trading Not Allowed**
   - Check if the symbol is active for trading
   - Verify your API key has trading permissions

4. **SSL/Connection Errors**
   - The integration disables SSL verification for testnet
   - Ensure you're connected to the internet

### Environment Variables

- `BINANCE_ENVIRONMENT`: Set to `testnet` for testing, `mainnet` for live trading
- `BINANCE_API_KEY`: Your API key (required)
- `BINANCE_API_SECRET`: Your API secret (for HMAC authentication)
- `BINANCE_PRIVATE_KEY_PATH`: Path to Ed25519 private key (for Ed25519 authentication)

## Safety Features

- Test orders only (no real money spent)
- Small quantities (0.0001 BTC ≈ $5)
- Balance verification before orders
- Comprehensive error handling
- Clear logging of all operations

## Authentication Methods

The script supports both authentication methods supported by Binance:

### HMAC-SHA256 (Traditional)
- Uses API key + secret
- Signatures are 64-character hex strings
- Backward compatible

### Ed25519 (Modern)
- Uses API key + private key file
- Signatures are 88-character base64 strings
- Faster and more secure
- Recommended for new implementations

## Integration with Main System

This test script uses the same `BinanceClient` and `OrderManager` classes that your main trading system uses, ensuring compatibility and reliability.
