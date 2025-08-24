"""
Unit tests for wallet authentication methods.

These tests verify that both HMAC-SHA256 and Ed25519 authentication
methods work correctly with the Binance integration.
"""

import pytest
import os
import tempfile
from unittest.mock import patch
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from binance_wallet_integration.security import SecurityManager
from binance_wallet_integration.config import ConfigManager, Environment


class TestAuthenticationMethods:
	"""Test both HMAC and Ed25519 authentication methods."""

	def test_hmac_authentication_initialization(self):
		"""Test HMAC-SHA256 authentication initialization."""
		security = SecurityManager(
			api_key='test_key_for_testing', api_secret='test_secret_for_testing'
		)

		assert security.auth_method == 'hmac'
		assert security.api_key == 'test_key_for_testing'
		assert security.api_secret == 'test_secret_for_testing'
		assert security.private_key is None

	def test_hmac_signature_generation(self):
		"""Test HMAC-SHA256 signature generation."""
		security = SecurityManager(
			api_key='test_key_for_testing', api_secret='test_secret_for_testing'
		)

		params = {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET'}
		signature = security.generate_signature(params)

		# HMAC signatures should be 64-character hex strings
		assert isinstance(signature, str)
		assert len(signature) == 64
		assert all(c in '0123456789abcdef' for c in signature)

	def test_ed25519_authentication_with_test_key(self):
		"""Test Ed25519 authentication with a generated test key."""
		# Create a temporary Ed25519 private key
		try:
			from cryptography.hazmat.primitives.asymmetric import ed25519
			from cryptography.hazmat.primitives import serialization
		except ImportError:
			pytest.skip('cryptography package not available')

		private_key = ed25519.Ed25519PrivateKey.generate()
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
			# Test Ed25519 initialization
			security = SecurityManager(
				api_key='test_key_for_testing', private_key_path=temp_key_path
			)

			assert security.auth_method == 'ed25519'
			assert security.api_key == 'test_key_for_testing'
			assert security.api_secret is None
			assert security.private_key is not None

			# Test signature generation
			params = {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET'}
			signature = security.generate_signature(params)

			# Ed25519 signatures should be 88-character base64 strings
			assert isinstance(signature, str)
			assert len(signature) == 88
			# Should be valid base64
			import base64

			base64.b64decode(signature)  # Should not raise exception

		finally:
			# Clean up temporary file
			os.unlink(temp_key_path)

	def test_config_manager_hmac_credentials(self):
		"""Test ConfigManager with HMAC credentials."""
		with patch.dict(
			os.environ,
			{
				'BINANCE_API_KEY': 'test_api_key',
				'BINANCE_API_SECRET': 'test_api_secret',
			},
		):
			config = ConfigManager(Environment.TESTNET)
			creds = config.get_api_credentials()

			assert creds['api_key'] == 'test_api_key'
			assert creds['api_secret'] == 'test_api_secret'
			assert 'private_key_path' not in creds

	def test_config_manager_ed25519_credentials(self):
		"""Test ConfigManager with Ed25519 credentials."""
		with patch.dict(
			os.environ,
			{
				'BINANCE_API_KEY': 'test_api_key',
				'BINANCE_PRIVATE_KEY_PATH': '/path/to/key.pem',
			},
		):
			config = ConfigManager(Environment.TESTNET)
			creds = config.get_api_credentials()

			assert creds['api_key'] == 'test_api_key'
			assert creds['private_key_path'] == '/path/to/key.pem'
			assert 'api_secret' not in creds

	def test_config_manager_missing_credentials(self):
		"""Test ConfigManager with missing credentials."""
		with patch.dict(
			os.environ,
			{
				'BINANCE_API_KEY': 'test_api_key'
				# No secret or private key path
			},
			clear=True,
		):
			config = ConfigManager(Environment.TESTNET)

			with pytest.raises(ValueError, match='Missing authentication credentials'):
				config.get_api_credentials()

	def test_config_manager_paper_mode(self):
		"""Test ConfigManager in paper mode."""
		config = ConfigManager(Environment.PAPER)
		creds = config.get_api_credentials()

		assert 'paper_key' in creds['api_key']
		assert 'paper_secret' in creds['api_secret']

	def test_security_manager_invalid_initialization(self):
		"""Test SecurityManager with invalid initialization."""
		# No credentials provided
		with pytest.raises(
			ValueError, match='Either api_secret or private_key_path must be provided'
		):
			SecurityManager(api_key='test_key')

		# Non-existent private key file
		with pytest.raises(ValueError, match='Private key file not found'):
			SecurityManager(api_key='test_key', private_key_path='/nonexistent/key.pem')


if __name__ == '__main__':
	pytest.main([__file__, '-v'])
