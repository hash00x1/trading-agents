#!/usr/bin/env python3
"""
Authentication Method Examples

This script demonstrates how to use both HMAC-SHA256 and Ed25519
authentication methods with the Binance integration.

Based on the official Binance documentation at:
https://testnet.binance.vision/
"""

import os
import tempfile
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from binance_wallet_integration.security import SecurityManager


def demonstrate_hmac_authentication():
	"""Demonstrate HMAC-SHA256 authentication method."""
	print('=' * 60)
	print('HMAC-SHA256 Authentication Example')
	print('=' * 60)

	# Create security manager with HMAC credentials
	security = SecurityManager(
		api_key='test_key_for_demonstration', api_secret='test_secret_for_demonstration'
	)

	print(f'Authentication method: {security.auth_method}')
	print(f'API Key: {security.api_key}')
	print(f'Has private key: {security.private_key is not None}')

	# Generate a signature
	params = {
		'symbol': 'BTCUSDT',
		'side': 'SELL',
		'type': 'LIMIT',
		'timeInForce': 'GTC',
		'quantity': '1.0000000',
		'price': '0.20',
		'timestamp': 1640995200000,  # Fixed timestamp for reproducible results
	}

	signature = security.generate_signature(params)
	print(f'Sample signature: {signature}')
	print(f'Signature length: {len(signature)} characters')
	print(
		f'Signature format: {"hex" if all(c in "0123456789abcdef" for c in signature) else "other"}'
	)
	print()


def demonstrate_ed25519_authentication():
	"""Demonstrate Ed25519 authentication method."""
	print('=' * 60)
	print('Ed25519 Authentication Example')
	print('=' * 60)

	try:
		from cryptography.hazmat.primitives.asymmetric import ed25519
		from cryptography.hazmat.primitives import serialization
	except ImportError:
		print('❌ cryptography package not available')
		print('Install with: pip install cryptography>=41.0.0')
		return

	# Generate a temporary Ed25519 private key (like the Binance documentation example)
	private_key = ed25519.Ed25519PrivateKey.generate()

	# Serialize to PEM format
	pem = private_key.private_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.PKCS8,
		encryption_algorithm=serialization.NoEncryption(),
	)

	# Write to temporary file
	with tempfile.NamedTemporaryFile(mode='wb', suffix='.pem', delete=False) as f:
		f.write(pem)
		temp_key_path = f.name

	try:
		print(f'Generated temporary key at: {temp_key_path}')

		# Create security manager with Ed25519 credentials
		security = SecurityManager(
			api_key='test_key_for_demonstration', private_key_path=temp_key_path
		)

		print(f'Authentication method: {security.auth_method}')
		print(f'API Key: {security.api_key}')
		print(f'Has private key: {security.private_key is not None}')

		# Generate a signature with the same parameters as HMAC example
		params = {
			'symbol': 'BTCUSDT',
			'side': 'SELL',
			'type': 'LIMIT',
			'timeInForce': 'GTC',
			'quantity': '1.0000000',
			'price': '0.20',
			'timestamp': 1640995200000,  # Same timestamp as HMAC example
		}

		signature = security.generate_signature(params)
		print(f'Sample signature: {signature}')
		print(f'Signature length: {len(signature)} characters')
		print('Signature format: base64')

		# Verify it's valid base64
		import base64

		try:
			decoded = base64.b64decode(signature)
			print(
				f'Decoded signature length: {len(decoded)} bytes (64 bytes expected for Ed25519)'
			)
		except Exception as e:
			print(f'❌ Invalid base64: {e}')

	finally:
		# Clean up temporary file
		os.unlink(temp_key_path)
		print('Cleaned up temporary key file')

	print()


def show_environment_setup():
	"""Show how to set up environment variables for each method."""
	print('=' * 60)
	print('Environment Variable Setup')
	print('=' * 60)

	print('For HMAC-SHA256 authentication:')
	print('BINANCE_API_KEY=your_api_key_from_testnet')
	print('BINANCE_API_SECRET=your_api_secret_from_testnet')
	print('BINANCE_ENVIRONMENT=testnet')
	print()

	print('For Ed25519 authentication:')
	print('BINANCE_API_KEY=your_api_key_from_testnet')
	print('BINANCE_PRIVATE_KEY_PATH=/path/to/your/test-prv-key.pem')
	print('BINANCE_ENVIRONMENT=testnet')
	print()

	print('To generate an Ed25519 key pair:')
	print('# Generate private key')
	print('openssl genpkey -algorithm ed25519 -out test-prv-key.pem')
	print()
	print('# Generate public key (for testnet registration)')
	print('openssl pkey -pubout -in test-prv-key.pem -out test-pub-key.pem')
	print()
	print('Then register the public key content at https://testnet.binance.vision/')
	print()


def compare_methods():
	"""Compare the two authentication methods."""
	print('=' * 60)
	print('Authentication Method Comparison')
	print('=' * 60)

	print('HMAC-SHA256:')
	print('  ✅ Traditional, widely supported')
	print('  ✅ No additional dependencies')
	print('  ✅ Simple setup')
	print('  ❌ Larger signature size (64 bytes)')
	print('  ❌ Slower signature generation')
	print()

	print('Ed25519:')
	print('  ✅ Modern, cryptographically stronger')
	print('  ✅ Smaller signature size (64 bytes raw, 88 base64)')
	print('  ✅ Faster signature generation')
	print('  ✅ Better security with smaller keys')
	print('  ❌ Requires cryptography package')
	print('  ❌ Slightly more complex setup')
	print()

	print('Recommendation: Use Ed25519 for new implementations')
	print()


def main():
	"""Main function to run all examples."""
	print('Binance Authentication Methods Demo')
	print('Based on https://testnet.binance.vision/ documentation')
	print()

	demonstrate_hmac_authentication()
	demonstrate_ed25519_authentication()
	compare_methods()
	show_environment_setup()

	print('=' * 60)
	print('Ready to use! Run the wallet test with:')
	print('cd tests && python wallet_test.py')
	print('=' * 60)


if __name__ == '__main__':
	main()
