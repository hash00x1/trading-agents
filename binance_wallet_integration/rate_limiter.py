"""
Advanced rate limiting for Binance API integration.

This module implements sophisticated rate limiting to ensure compliance with
Binance API limits and prevent bans or throttling.
"""

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitType(Enum):
	"""Types of rate limits."""

	REQUEST_WEIGHT = 'request_weight'
	RAW_REQUESTS = 'raw_requests'
	ORDERS = 'orders'


@dataclass
class RateLimit:
	"""Rate limit configuration."""

	limit: int
	window_seconds: int
	current_usage: int = 0
	reset_time: float = 0

	def is_exceeded(self) -> bool:
		"""Check if rate limit is exceeded."""
		current_time = time.time()
		if current_time >= self.reset_time:
			self.current_usage = 0
			self.reset_time = current_time + self.window_seconds

		return self.current_usage >= self.limit

	def add_usage(self, amount: int = 1) -> None:
		"""Add usage to the rate limit."""
		current_time = time.time()
		if current_time >= self.reset_time:
			self.current_usage = 0
			self.reset_time = current_time + self.window_seconds

		self.current_usage += amount

	def get_remaining(self) -> int:
		"""Get remaining capacity."""
		current_time = time.time()
		if current_time >= self.reset_time:
			return self.limit
		return max(0, self.limit - self.current_usage)

	def get_reset_in_seconds(self) -> float:
		"""Get seconds until reset."""
		current_time = time.time()
		return max(0, self.reset_time - current_time)


class BackoffStrategy:
	"""Implements exponential backoff for API calls."""

	def __init__(
		self, base_delay: float = 1.0, max_delay: float = 60.0, multiplier: float = 2.0
	):
		"""Initialize backoff strategy.

		Args:
		    base_delay: Initial delay in seconds
		    max_delay: Maximum delay in seconds
		    multiplier: Backoff multiplier
		"""
		self.base_delay = base_delay
		self.max_delay = max_delay
		self.multiplier = multiplier
		self.attempts = 0

	def get_delay(self) -> float:
		"""Get next delay duration."""
		delay = min(self.base_delay * (self.multiplier**self.attempts), self.max_delay)
		self.attempts += 1
		return delay

	def reset(self) -> None:
		"""Reset backoff attempts."""
		self.attempts = 0


class RateLimitManager:
	"""Advanced rate limiting manager for Binance API."""

	def __init__(self):
		"""Initialize rate limit manager."""
		self._lock = threading.RLock()
		self._rate_limits = {
			RateLimitType.REQUEST_WEIGHT: RateLimit(1200, 60),  # 1200 per minute
			RateLimitType.RAW_REQUESTS: RateLimit(6000, 60),  # 6000 per minute
			RateLimitType.ORDERS: RateLimit(50, 10),  # 50 per 10 seconds
		}

		# Track request history for better prediction
		self._request_history = defaultdict(lambda: deque(maxlen=1000))
		self._backoff_strategies = defaultdict(BackoffStrategy)

		# Ban tracking
		self._is_banned = False
		self._ban_until = 0

		logger.info('RateLimitManager initialized')

	def check_limits(
		self,
		endpoint_weight: int = 1,
		limit_type: RateLimitType = RateLimitType.REQUEST_WEIGHT,
	) -> bool:
		"""Check if request can be made without exceeding limits.

		Args:
		    endpoint_weight: API weight of the request
		    limit_type: Type of rate limit to check

		Returns:
		    True if request can be made, False otherwise
		"""
		with self._lock:
			# Check if we're currently banned
			if self._is_banned and time.time() < self._ban_until:
				logger.warning(
					f'API requests blocked due to ban until {self._ban_until}'
				)
				return False
			elif self._is_banned and time.time() >= self._ban_until:
				self._is_banned = False
				logger.info('API ban period ended, resuming requests')

			rate_limit = self._rate_limits[limit_type]

			# Check if adding this request would exceed the limit
			if rate_limit.current_usage + endpoint_weight > rate_limit.limit:
				logger.warning(
					f'Rate limit check failed: {rate_limit.current_usage + endpoint_weight} > {rate_limit.limit}'
				)
				return False

			return True

	def acquire(
		self,
		endpoint_weight: int = 1,
		limit_type: RateLimitType = RateLimitType.REQUEST_WEIGHT,
		timeout: float = 30.0,
	) -> bool:
		"""Acquire permission to make API request.

		Args:
		    endpoint_weight: API weight of the request
		    limit_type: Type of rate limit
		    timeout: Maximum time to wait in seconds

		Returns:
		    True if permission acquired, False if timeout
		"""
		start_time = time.time()

		while time.time() - start_time < timeout:
			with self._lock:
				if self.check_limits(endpoint_weight, limit_type):
					# Grant permission and update usage
					self._rate_limits[limit_type].add_usage(endpoint_weight)
					self._record_request(limit_type, endpoint_weight)
					logger.debug(
						f'Rate limit acquired: {endpoint_weight} weight, {limit_type.value}'
					)
					return True

			# Wait before retrying
			backoff = self._backoff_strategies[limit_type]
			delay = min(backoff.get_delay(), 5.0)  # Max 5 second delay
			logger.debug(f'Rate limit exceeded, waiting {delay:.2f}s')
			time.sleep(delay)

		logger.error(f'Rate limit acquisition timeout after {timeout}s')
		return False

	def update_from_response_headers(self, headers: Dict[str, str]) -> None:
		"""Update rate limits from Binance API response headers.

		Args:
		    headers: HTTP response headers from Binance API
		"""
		with self._lock:
			# Update request weight usage
			if 'x-mbx-used-weight-1m' in headers:
				used_weight = int(headers['x-mbx-used-weight-1m'])
				self._rate_limits[
					RateLimitType.REQUEST_WEIGHT
				].current_usage = used_weight
				logger.debug(f'Updated request weight from headers: {used_weight}/1200')

			# Update order count
			if 'x-mbx-order-count-10s' in headers:
				order_count = int(headers['x-mbx-order-count-10s'])
				self._rate_limits[RateLimitType.ORDERS].current_usage = order_count
				logger.debug(f'Updated order count from headers: {order_count}/50')

			# Check for retry-after header (ban indication)
			if 'retry-after' in headers:
				retry_after = int(headers['retry-after'])
				self._set_ban(retry_after)

	def handle_rate_limit_error(
		self, status_code: int, headers: Dict[str, str]
	) -> float:
		"""Handle rate limit error response.

		Args:
		    status_code: HTTP status code
		    headers: Response headers

		Returns:
		    Recommended wait time in seconds
		"""
		if status_code == 429:  # Too Many Requests
			retry_after = headers.get('retry-after', '60')
			wait_time = int(retry_after)
			logger.warning(f'Rate limit exceeded (429), waiting {wait_time}s')
			return wait_time

		elif status_code == 418:  # I'm a teapot (IP banned)
			# Binance uses 418 to indicate IP ban
			ban_duration = 3600  # 1 hour default
			self._set_ban(ban_duration)
			logger.error(f'IP banned (418), banned for {ban_duration}s')
			return ban_duration

		return 0

	def _set_ban(self, duration_seconds: int) -> None:
		"""Set API ban status.

		Args:
		    duration_seconds: Ban duration in seconds
		"""
		with self._lock:
			self._is_banned = True
			self._ban_until = time.time() + duration_seconds
			logger.error(f'API banned until {time.ctime(self._ban_until)}')

	def _record_request(self, limit_type: RateLimitType, weight: int) -> None:
		"""Record request for analytics.

		Args:
		    limit_type: Type of rate limit
		    weight: Request weight
		"""
		current_time = time.time()
		self._request_history[limit_type].append(
			{'timestamp': current_time, 'weight': weight}
		)

	def get_status(self) -> Dict[str, Any]:
		"""Get current rate limit status.

		Returns:
		    Dictionary with rate limit status
		"""
		with self._lock:
			status = {}

			for limit_type, rate_limit in self._rate_limits.items():
				status[limit_type.value] = {
					'limit': rate_limit.limit,
					'current_usage': rate_limit.current_usage,
					'remaining': rate_limit.get_remaining(),
					'reset_in_seconds': rate_limit.get_reset_in_seconds(),
					'window_seconds': rate_limit.window_seconds,
				}

			status['is_banned'] = self._is_banned
			if self._is_banned:
				status['ban_until'] = self._ban_until
				status['ban_remaining_seconds'] = max(0, self._ban_until - time.time())

			return status

	def reset_limits(self) -> None:
		"""Reset all rate limits (for testing)."""
		with self._lock:
			for rate_limit in self._rate_limits.values():
				rate_limit.current_usage = 0
				rate_limit.reset_time = 0

			self._is_banned = False
			self._ban_until = 0

			for backoff in self._backoff_strategies.values():
				backoff.reset()

			logger.info('All rate limits reset')

	def get_request_stats(self) -> Dict[str, Any]:
		"""Get request statistics.

		Returns:
		    Dictionary with request statistics
		"""
		with self._lock:
			stats = {}
			current_time = time.time()

			for limit_type, history in self._request_history.items():
				recent_requests = [
					req for req in history if current_time - req['timestamp'] < 300
				]  # Last 5 minutes

				if recent_requests:
					total_weight = sum(req['weight'] for req in recent_requests)
					avg_weight = total_weight / len(recent_requests)
					requests_per_minute = len(
						[
							req
							for req in recent_requests
							if current_time - req['timestamp'] < 60
						]
					)
				else:
					total_weight = avg_weight = requests_per_minute = 0

				stats[limit_type.value] = {
					'requests_last_5min': len(recent_requests),
					'requests_per_minute': requests_per_minute,
					'total_weight_5min': total_weight,
					'avg_weight': avg_weight,
				}

			return stats
