#!/usr/bin/env python3
"""
Test Slug/Ticker Conversion for Binance Integration

This script tests the slug to ticker to trading pair conversion pipeline.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from binance_wallet_integration.crypto_agents_adapter import CryptoAgentsAdapter
from binance_wallet_integration import Environment


def test_conversion_pipeline():
	"""Test the complete conversion pipeline."""
	print('🧪 Testing Slug/Ticker Conversion Pipeline')
	print('=' * 45)

	# Create adapter instance (no need to initialize for testing conversions)
	adapter = CryptoAgentsAdapter(Environment.PAPER)

	# Test cases: (input_symbol, expected_ticker, expected_trading_pair)
	test_cases = [
		# Slugs (crypto_agents format)
		('bitcoin', 'BTC', 'BTCUSDT'),
		('ethereum', 'ETH', 'ETHUSDT'),
		('dogecoin', 'DOGE', 'DOGEUSDT'),
		('tether', 'USDT', 'USDT'),
		# Tickers (already in ticker format)
		('BTC', 'BTC', 'BTCUSDT'),
		('ETH', 'ETH', 'ETHUSDT'),
		('DOGE', 'DOGE', 'DOGEUSDT'),
		# Unknown token (should default to ticker + USDT)
		('UNKNOWN', 'UNKNOWN', 'UNKNOWNUSDT'),
	]

	print('\n📊 Conversion Results:')
	print('-' * 60)
	print(f'{"Input":<12} {"→ Ticker":<10} {"→ Trading Pair":<15} {"Status":<8}')
	print('-' * 60)

	all_passed = True

	for input_symbol, expected_ticker, expected_trading_pair in test_cases:
		try:
			# Test slug to ticker conversion
			if input_symbol.lower() in adapter.slug_to_token_mapping:
				actual_ticker = adapter._slug_to_token(input_symbol)
			else:
				actual_ticker = input_symbol.upper()

			# Test ticker to trading pair conversion
			actual_trading_pair = adapter._convert_symbol(input_symbol)

			# Check results
			ticker_ok = actual_ticker == expected_ticker
			pair_ok = actual_trading_pair == expected_trading_pair

			status = '✅ PASS' if (ticker_ok and pair_ok) else '❌ FAIL'
			if not (ticker_ok and pair_ok):
				all_passed = False

			print(
				f'{input_symbol:<12} {actual_ticker:<10} {actual_trading_pair:<15} {status}'
			)

			if not ticker_ok:
				print(
					f'  ⚠️  Ticker mismatch: got {actual_ticker}, expected {expected_ticker}'
				)
			if not pair_ok:
				print(
					f'  ⚠️  Trading pair mismatch: got {actual_trading_pair}, expected {expected_trading_pair}'
				)

		except Exception as e:
			print(f'{input_symbol:<12} {"ERROR":<10} {"ERROR":<15} ❌ FAIL')
			print(f'  💥 Exception: {e}')
			all_passed = False

	print('-' * 60)

	# Test reverse conversion (ticker to slug)
	print('\n🔄 Reverse Conversion Test (Ticker → Slug):')
	print('-' * 40)
	print(f'{"Ticker":<8} {"→ Slug":<15} {"Status":<8}')
	print('-' * 40)

	reverse_test_cases = [
		('BTC', 'bitcoin'),
		('ETH', 'ethereum'),
		('DOGE', 'dogecoin'),
		('UNKNOWN', 'unknown'),  # Should fallback to lowercase
	]

	for ticker, expected_slug in reverse_test_cases:
		try:
			actual_slug = adapter._token_to_slug(ticker)
			slug_ok = actual_slug == expected_slug
			status = '✅ PASS' if slug_ok else '❌ FAIL'

			if not slug_ok:
				all_passed = False

			print(f'{ticker:<8} {actual_slug:<15} {status}')

			if not slug_ok:
				print(f'  ⚠️  Expected: {expected_slug}, got: {actual_slug}')

		except Exception as e:
			print(f'{ticker:<8} {"ERROR":<15} ❌ FAIL')
			print(f'  💥 Exception: {e}')
			all_passed = False

	print('-' * 40)

	# Test supported mappings
	print(f'\n📋 Supported Mappings ({len(adapter.slug_to_token_mapping)} total):')
	print('-' * 35)
	for slug, ticker in adapter.slug_to_token_mapping.items():
		trading_pair = adapter.token_to_pair_mapping.get(ticker, f'{ticker}USDT')
		print(f'  {slug:<15} → {ticker:<6} → {trading_pair}')

	# Summary
	print('\n🎯 Test Summary:')
	print(
		f'  Overall result: {"✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"}'
	)

	if all_passed:
		print('  ✅ Slug/Ticker conversion pipeline is working correctly')
		print('  ✅ Ready for integration with crypto_agents')
	else:
		print('  ❌ Some conversion tests failed')
		print('  ❌ Review the mapping configuration')

	return all_passed


if __name__ == '__main__':
	success = test_conversion_pipeline()
	sys.exit(0 if success else 1)
