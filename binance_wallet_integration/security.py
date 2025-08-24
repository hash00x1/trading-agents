"""
Security Manager for Binance Integration

Handles API key validation, request signing, and security best practices.
Implements HMAC-SHA256 signing as required by Binance API.
"""

import hmac
import hashlib
import time
import logging
import base64
import os
from typing import Dict, Optional, Union
from urllib.parse import urlencode
import secrets
import re

try:
	from cryptography.hazmat.primitives.serialization import load_pem_private_key
	from cryptography.hazmat.primitives import hashes
	from cryptography.hazmat.primitives.asymmetric import ed25519

	CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
	CRYPTOGRAPHY_AVAILABLE = False

logger = logging.getLogger(__name__)


class SecurityManager:
	"""Manages security aspects of Binance API integration."""

	def __init__(
		self,
		api_key: str,
		api_secret: Optional[str] = None,
		private_key_path: Optional[str] = None,
	):
		"""Initialize security manager.

		Args:
		    api_key: Binance API key
		    api_secret: Binance API secret (for HMAC-SHA256 signing)
		    private_key_path: Path to Ed25519 private key file (for Ed25519 signing)

		Raises:
		    ValueError: If credentials are invalid or missing
		"""
		self.api_key = self._validate_api_key(api_key)

		# Determine authentication method
		if private_key_path:
			self.auth_method = 'ed25519'
			self.private_key = self._load_private_key(private_key_path)
			self.api_secret = None
			logger.info(
				'SecurityManager initialized with Ed25519 private key authentication'
			)
		elif api_secret:
			self.auth_method = 'hmac'
			self.api_secret = self._validate_api_secret(api_secret)
			self.private_key = None
			logger.info('SecurityManager initialized with HMAC-SHA256 authentication')
		else:
			raise ValueError('Either api_secret or private_key_path must be provided')

	def _validate_api_key(self, api_key: str) -> str:
		"""Validate API key format.

		Args:
		    api_key: API key to validate

		Returns:
		    Validated API key

		Raises:
		    ValueError: If API key format is invalid
		"""
		if not api_key or not isinstance(api_key, str):
			raise ValueError('API key must be a non-empty string')

		# Check for common test patterns first
		test_patterns = ['test', 'demo', 'paper_key', 'mock']
		is_test_key = any(pattern in api_key.lower() for pattern in test_patterns)

		if is_test_key:
			logger.warning('Using test/demo API key')
			# Allow shorter test keys for testing purposes
			if len(api_key) < 8:
				raise ValueError('Test API key must be at least 8 characters')
		else:
			# Binance API keys are typically 64 characters long
			if len(api_key) < 32:
				raise ValueError('API key appears to be too short')

		return api_key.strip()

	def _validate_api_secret(self, api_secret: str) -> str:
		"""Validate API secret format.

		Args:
		    api_secret: API secret to validate

		Returns:
		    Validated API secret

		Raises:
		    ValueError: If API secret format is invalid
		"""
		if not api_secret or not isinstance(api_secret, str):
			raise ValueError('API secret must be a non-empty string')

		# Check for common test patterns first
		test_patterns = ['test', 'demo', 'paper_secret', 'mock']
		is_test_secret = any(pattern in api_secret.lower() for pattern in test_patterns)

		if is_test_secret:
			logger.warning('Using test/demo API secret')
			# Allow shorter test secrets for testing purposes
			if len(api_secret) < 8:
				raise ValueError('Test API secret must be at least 8 characters')
		else:
			# Binance API secrets are typically 64 characters long
			if len(api_secret) < 32:
				raise ValueError('API secret appears to be too short')

		return api_secret.strip()

	def _load_private_key(self, private_key_path: str) -> ed25519.Ed25519PrivateKey:
		"""Load Ed25519 private key from PEM file.

		Args:
		    private_key_path: Path to the private key file

		Returns:
		    Ed25519 private key object

		Raises:
		    ValueError: If private key cannot be loaded
		"""
		if not CRYPTOGRAPHY_AVAILABLE:
			raise ValueError(
				'cryptography package is required for Ed25519 signing. '
				'Install it with: pip install cryptography'
			)

		if not os.path.exists(private_key_path):
			raise ValueError(f'Private key file not found: {private_key_path}')

		try:
			with open(private_key_path, 'rb') as key_file:
				private_key = load_pem_private_key(
					key_file.read(),
					password=None,  # Assumes no password protection
				)

			if not isinstance(private_key, ed25519.Ed25519PrivateKey):
				raise ValueError('Private key must be Ed25519 format')

			logger.info(
				f'Successfully loaded Ed25519 private key from {private_key_path}'
			)
			return private_key

		except Exception as e:
			raise ValueError(f'Failed to load private key: {e}')

	def generate_signature(self, params: Dict[str, Union[str, int, float]]) -> str:
		"""Generate signature for Binance API request.

		Supports both HMAC-SHA256 and Ed25519 signing methods.

		Args:
		    params: Request parameters to sign

		Returns:
		    Signature string (hex for HMAC, base64 for Ed25519)
		"""
		if self.auth_method == 'ed25519':
			# Ed25519 signature - use Binance documentation format
			# Payload: '&'.join([f'{param}={value}' for param, value in params.items()])
			payload = '&'.join([f'{param}={value}' for param, value in params.items()])
			signature_bytes = self.private_key.sign(payload.encode('ASCII'))
			signature = base64.b64encode(signature_bytes).decode('ASCII')
			logger.debug(f'Generated Ed25519 signature for payload: {payload}')
		else:
			# HMAC-SHA256 signature (backward compatibility)
			# Use sorted parameters and urlencode for consistency
			query_string = urlencode(sorted(params.items()))
			signature_bytes = hmac.new(
				self.api_secret.encode('utf-8'),
				query_string.encode('utf-8'),
				hashlib.sha256,
			).digest()
			signature = signature_bytes.hex()
			logger.debug(f'Generated HMAC-SHA256 signature for query: {query_string}')

		logger.debug(f'Signature: {signature}')
		return signature

	def create_signed_params(
		self, params: Optional[Dict[str, Union[str, int, float]]] = None
	) -> Dict[str, Union[str, int, float]]:
		"""Create signed parameters for authenticated API requests.

		Args:
		    params: Optional request parameters

		Returns:
		    Parameters with timestamp and signature added
		"""
		if params is None:
			params = {}

		# Add timestamp (required for signed requests)
		params['timestamp'] = int(time.time() * 1000)

		# Generate and add signature
		params['signature'] = self.generate_signature(params)

		return params

	def get_headers(self, include_signature: bool = False) -> Dict[str, str]:
		"""Get HTTP headers for API requests.

		Args:
		    include_signature: Whether this is a signed request

		Returns:
		    HTTP headers dictionary
		"""
		headers = {
			'X-MBX-APIKEY': self.api_key,
			'Content-Type': 'application/json',
			'User-Agent': 'crypto_agents/1.0.0',
		}

		if include_signature:
			headers['X-MBX-TIMESTAMP'] = str(int(time.time() * 1000))

		return headers

	def validate_ip_address(self, ip_address: str) -> bool:
		"""Validate IP address format.

		Args:
		    ip_address: IP address to validate

		Returns:
		    True if valid IP address
		"""
		# Simple IPv4 validation
		ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
		if re.match(ipv4_pattern, ip_address):
			parts = ip_address.split('.')
			return all(0 <= int(part) <= 255 for part in parts)

		# Could add IPv6 validation here if needed
		return False

	def check_permissions(self, required_permissions: list) -> bool:
		"""Check if API key has required permissions.

		Note: This would need to be implemented with actual API calls
		to Binance's account endpoint to check permissions.

		Args:
		    required_permissions: List of required permissions

		Returns:
		    True if all permissions are available
		"""
		# For now, return True - in production, this should make an API call
		# to GET /api/v3/account to check actual permissions
		logger.info(f'Permission check requested for: {required_permissions}')
		return True

	def generate_listen_key_signature(self) -> str:
		"""Generate signature for WebSocket listen key requests.

		Returns:
		    Signature for listen key request
		"""
		timestamp = int(time.time() * 1000)
		params = {'timestamp': timestamp}
		return self.generate_signature(params)

	def mask_sensitive_data(self, data: str) -> str:
		"""Mask sensitive data for logging.

		Args:
		    data: String that may contain sensitive information

		Returns:
		    String with sensitive data masked
		"""
		if not data:
			return data

		# Mask API keys and secrets
		if len(data) > 8:
			return data[:4] + '*' * (len(data) - 8) + data[-4:]
		else:
			return '*' * len(data)

	@staticmethod
	def generate_client_order_id() -> str:
		"""Generate a unique client order ID.

		Returns:
		    Unique order ID string
		"""
		# Generate a secure random string for order ID
		timestamp = int(time.time() * 1000)
		random_suffix = secrets.token_hex(4)
		return f'crypto_agents_{timestamp}_{random_suffix}'

	def validate_order_data(self, order_data: Dict) -> bool:
		"""Validate order data for security and format.

		Args:
		    order_data: Order data to validate

		Returns:
		    True if order data is valid

		Raises:
		    ValueError: If order data is invalid
		"""
		required_fields = ['symbol', 'side', 'type', 'quantity']

		# Check required fields
		for field in required_fields:
			if field not in order_data:
				raise ValueError(f'Missing required field: {field}')

		# Validate symbol format (should be like BTCUSDT)
		symbol = order_data['symbol']
		if not re.match(r'^[A-Z]{2,10}USDT?$', symbol):
			raise ValueError(f'Invalid symbol format: {symbol}')

		# Validate side
		if order_data['side'] not in ['BUY', 'SELL']:
			raise ValueError(f'Invalid order side: {order_data["side"]}')

		# Validate quantity
		try:
			quantity = float(order_data['quantity'])
			if quantity <= 0:
				raise ValueError('Quantity must be positive')
		except (ValueError, TypeError):
			raise ValueError('Invalid quantity format')

		logger.debug(f'Order data validation passed for {symbol}')
		return True
