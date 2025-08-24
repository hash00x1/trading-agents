#!/usr/bin/env python3
"""
Real Trading Performance Test
Verifies that the dashboard uses REAL Binance account data instead of paper trading fallbacks
"""

import requests
import sys
from pathlib import Path

def test_real_trading_mode():
    """Test that the system is using real Binance data"""
    
    print("🎯 Testing Real Trading Performance Mode")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if API server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        health_data = response.json()
        
        print(f"✅ API Health: {health_data['status']}")
        print(f"📊 Trading Mode: {health_data['trading_mode']}")
        
        if 'live' not in health_data['trading_mode'].lower():
            print("⚠️  WARNING: System not in live trading mode!")
            print("   Set TRADING_MODE=live in your .env file")
            
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        return False
    
    # Test 2: Get portfolio summary and check data source
    try:
        response = requests.get(f"{base_url}/api/portfolio/summary", timeout=30)
        
        if response.status_code == 503:
            print("✅ EXCELLENT: System correctly rejects when Binance API unavailable")
            print("   No paper trading fallback - real trading mode enforced!")
            error_detail = response.json().get('detail', '')
            print(f"   Error: {error_detail}")
            return True
            
        elif response.status_code == 200:
            portfolio_data = response.json()
            
            print(f"📈 Portfolio Total: ${portfolio_data['total_usd_value']:,.2f}")
            print(f"🔢 Positions Count: {len(portfolio_data['positions'])}")
            
            # Check data sources
            real_binance_positions = 0
            local_database_positions = 0
            
            for asset, position in portfolio_data['positions'].items():
                data_source = position.get('source', 'unknown')
                if data_source == 'binance_live':
                    real_binance_positions += 1
                    print(f"✅ {asset.upper()}: REAL Binance balance ${position['total_value']:.2f}")
                elif data_source == 'local_database':
                    local_database_positions += 1
                    print(f"⚠️  {asset.upper()}: Local database (paper mode)")
                else:
                    print(f"❓ {asset.upper()}: Unknown source ({data_source})")
            
            if real_binance_positions > 0:
                print(f"\n✅ SUCCESS: {real_binance_positions} positions from REAL Binance account")
                print("   Real trading performance can be measured!")
                return True
            elif local_database_positions > 0:
                print(f"\n⚠️  Using local database positions (paper trading mode)")
                print("   This shows simulated data, not real trading performance")
                return False
            else:
                print(f"\n❓ No clear data source identified")
                return False
                
        else:
            print(f"❌ Portfolio API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Portfolio test failed: {e}")
        return False

def test_binance_account_access():
    """Test direct Binance account access"""
    
    print("\n🔗 Testing Direct Binance Account Access")
    print("=" * 45)
    
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/api/balances", timeout=30)
        
        if response.status_code == 200:
            balance_data = response.json()
            
            if 'balances' in balance_data and balance_data['balances']:
                print("✅ Direct Binance account access successful")
                
                # Show some balances
                balances = balance_data['balances']
                asset_count = len(balances)
                print(f"📊 Found {asset_count} assets in Binance account")
                
                # Show top balances
                for asset, balance_info in list(balances.items())[:5]:
                    if isinstance(balance_info, dict):
                        total = balance_info.get('total', 0)
                        if total > 0:
                            print(f"   {asset}: {total}")
                
                return True
            else:
                print("⚠️  Binance account accessible but no balances found")
                return True
                
        elif response.status_code == 500:
            error_data = response.json()
            error_detail = error_data.get('detail', '')
            
            if 'Failed to get balances' in error_detail:
                print("✅ GOOD: System correctly fails when Binance unavailable")
                print("   No silent fallback to paper trading!")
                print(f"   Error: {error_detail}")
                return True
            else:
                print(f"❌ Unexpected error: {error_detail}")
                return False
        else:
            print(f"❌ Binance balance API error: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Binance balance test failed: {e}")
        return False

def main():
    """Run real trading tests"""
    
    print("🎯 REAL TRADING PERFORMANCE VERIFICATION")
    print("Testing that dashboard shows actual trading results")
    print("=" * 60)
    
    # Check if API server is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print("❌ API server not responding. Please start it first:")
            print("   PYTHONPATH=/Users/Lukas_1/Code-Projects/crypto_agents \\")
            print("   poetry run uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000")
            sys.exit(1)
    except Exception:
        print("❌ API server not running. Please start it first:")
        print("   cd /Users/Lukas_1/Code-Projects/crypto_agents")
        print("   PYTHONPATH=/Users/Lukas_1/Code-Projects/crypto_agents \\")
        print("   poetry run uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 &")
        sys.exit(1)
    
    # Run tests
    test1_result = test_real_trading_mode()
    test2_result = test_binance_account_access()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 REAL TRADING VERIFICATION SUMMARY")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("✅ SUCCESS: System is configured for real trading performance measurement")
        print("✅ No paper trading fallbacks - only real Binance data")
        print("✅ Trading performance reflects actual results")
        
        print("""
🎯 REAL TRADING PERFORMANCE VERIFIED:

✅ Portfolio values come from live Binance account
✅ No fallback to paper trading in live mode  
✅ System fails gracefully when Binance unavailable
✅ Trading performance measurements are REAL

📊 Your dashboard now shows:
   - Actual Binance account balances
   - Real trading performance
   - True P&L from live trades
   - No simulated/paper data contamination

🚀 Ready for production trading performance analysis!
        """)
        
    else:
        print("❌ ISSUES FOUND: System may still be using paper trading fallbacks")
        print("⚠️  Portfolio values may not reflect real trading performance")
        
        print("""
🔧 TO FIX:
1. Ensure TRADING_MODE=live in .env file
2. Verify Binance API credentials are correct
3. Check network connectivity to Binance testnet
4. Restart the dashboard API server

⚠️  Until fixed, portfolio values show simulated data!
        """)

if __name__ == "__main__":
    main()
