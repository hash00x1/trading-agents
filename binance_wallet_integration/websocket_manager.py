"""
WebSocket Manager for Binance Integration

Manages real-time data streams from Binance WebSocket API according to:
https://github.com/binance/binance-spot-api-docs/blob/master/testnet/web-socket-streams.md
"""

import asyncio
import json
import logging
import time
import websockets
from websockets.client import WebSocketClientProtocol
from typing import Dict, Any, Optional, Callable, List, Set
from enum import Enum
from dataclasses import dataclass, field
import ssl

from .config import ConfigManager

logger = logging.getLogger(__name__)


class StreamType(Enum):
	"""WebSocket stream types."""

	TRADE = 'trade'
	KLINE = 'kline'
	TICKER = 'ticker'
	DEPTH = 'depth'
	BOOK_TICKER = 'bookTicker'
	INDIVIDUAL_SYMBOL_TICKER = 'ticker'
	AGGREGATE_TRADE = 'aggTrade'


@dataclass
class StreamConfig:
	"""Configuration for a WebSocket stream."""

	symbol: str
	stream_type: StreamType
	interval: Optional[str] = None  # For kline streams
	depth_levels: Optional[int] = None  # For depth streams
	update_speed: Optional[str] = None  # @100ms, @1000ms


@dataclass
class WebSocketConnection:
	"""Represents a WebSocket connection."""

	websocket: Optional[WebSocketClientProtocol] = None
	streams: Set[str] = field(default_factory=set)
	is_connected: bool = False
	last_ping: float = 0
	reconnect_attempts: int = 0
	max_reconnect_attempts: int = 5


class WebSocketManager:
	"""Manages WebSocket connections to Binance streams."""

	def __init__(self, config_manager: Optional[ConfigManager] = None):
		"""Initialize WebSocket manager.

		Args:
		    config_manager: Configuration manager instance
		"""
		self.config = config_manager or ConfigManager()

		# Connection management
		self._connections: Dict[str, WebSocketConnection] = {}
		self._message_handlers: Dict[str, Callable] = {}
		self._running = False

		# Stream management
		self._active_streams: Dict[str, StreamConfig] = {}

		# Rate limiting (WebSocket specific)
		self._connection_attempts = []
		self._max_connections = 5  # Conservative limit

		logger.info('WebSocketManager initialized')

	def _format_stream_name(self, config: StreamConfig) -> str:
		"""Format stream name according to Binance specification.

		Args:
		    config: Stream configuration

		Returns:
		    Formatted stream name
		"""
		symbol = config.symbol.lower()

		if config.stream_type == StreamType.TRADE:
			return f'{symbol}@trade'

		elif config.stream_type == StreamType.KLINE:
			interval = config.interval or '1m'
			return f'{symbol}@kline_{interval}'

		elif config.stream_type == StreamType.TICKER:
			return f'{symbol}@ticker'

		elif config.stream_type == StreamType.DEPTH:
			if config.depth_levels:
				speed = config.update_speed or '@100ms'
				return f'{symbol}@depth{config.depth_levels}{speed}'
			else:
				speed = config.update_speed or '@100ms'
				return f'{symbol}@depth{speed}'

		elif config.stream_type == StreamType.BOOK_TICKER:
			return f'{symbol}@bookTicker'

		elif config.stream_type == StreamType.AGGREGATE_TRADE:
			return f'{symbol}@aggTrade'

		else:
			raise ValueError(f'Unsupported stream type: {config.stream_type}')

	def _check_connection_rate_limit(self) -> bool:
		"""Check if we can make a new connection.

		Returns:
		    True if connection is allowed
		"""
		current_time = time.time()

		# Remove old attempts (5 minute window)
		self._connection_attempts = [
			attempt
			for attempt in self._connection_attempts
			if current_time - attempt < 300
		]

		# Check if we're under the limit (300 attempts per 5 minutes)
		return len(self._connection_attempts) < 300

	def _record_connection_attempt(self) -> None:
		"""Record a connection attempt for rate limiting."""
		self._connection_attempts.append(time.time())

	async def _create_connection(self, streams: List[str]) -> WebSocketConnection:
		"""Create a new WebSocket connection.

		Args:
		    streams: List of stream names to subscribe to

		Returns:
		    WebSocket connection object

		Raises:
		    Exception: If connection fails
		"""
		if not self._check_connection_rate_limit():
			raise Exception('WebSocket connection rate limit exceeded')

		self._record_connection_attempt()

		# Prepare URL
		if len(streams) == 1:
			# Single stream
			url = f'{self.config.endpoints.websocket_stream}/{streams[0]}'
		else:
			# Multiple streams
			streams_param = '/'.join(streams)
			url = f'{self.config.endpoints.websocket_stream}/{streams_param}'

		logger.info(f'Connecting to WebSocket: {url}')

		# SSL context for secure connections
		ssl_context = ssl.create_default_context()

		try:
			websocket = await websockets.connect(
				url,
				ssl=ssl_context,
				ping_interval=20,
				ping_timeout=10,
				close_timeout=10,
			)

			connection = WebSocketConnection(
				websocket=websocket,
				streams=set(streams),
				is_connected=True,
				last_ping=time.time(),
			)

			logger.info(f'WebSocket connected successfully for streams: {streams}')
			return connection

		except Exception as e:
			logger.error(f'Failed to connect to WebSocket: {e}')
			raise

	async def _handle_message(self, connection_id: str, message: str) -> None:
		"""Handle incoming WebSocket message.

		Args:
		    connection_id: Connection identifier
		    message: Raw message string
		"""
		try:
			data = json.loads(message)

			# Extract stream name
			stream = data.get('stream')
			if not stream:
				logger.warning(f'Message without stream identifier: {message[:100]}')
				return

			# Call registered handlers
			if stream in self._message_handlers:
				await self._message_handlers[stream](data)
			else:
				logger.debug(f'No handler for stream: {stream}')

		except json.JSONDecodeError as e:
			logger.error(f'Failed to parse WebSocket message: {e}')
		except Exception as e:
			logger.error(f'Error handling WebSocket message: {e}')

	async def _connection_loop(
		self, connection_id: str, connection: WebSocketConnection
	) -> None:
		"""Main loop for a WebSocket connection.

		Args:
		    connection_id: Connection identifier
		    connection: WebSocket connection object
		"""
		try:
			async for message in connection.websocket:
				if not self._running:
					break

				await self._handle_message(connection_id, message)
				connection.last_ping = time.time()

		except websockets.exceptions.ConnectionClosed:
			logger.warning(f'WebSocket connection {connection_id} closed')
			connection.is_connected = False

		except Exception as e:
			logger.error(f'Error in WebSocket connection {connection_id}: {e}')
			connection.is_connected = False

		finally:
			if connection.websocket and not connection.websocket.closed:
				await connection.websocket.close()
			connection.is_connected = False

	async def _reconnect_loop(self, connection_id: str) -> None:
		"""Reconnection loop for failed connections.

		Args:
		    connection_id: Connection identifier
		"""
		connection = self._connections[connection_id]

		while (
			self._running
			and connection.reconnect_attempts < connection.max_reconnect_attempts
		):
			try:
				await asyncio.sleep(
					min(2**connection.reconnect_attempts, 60)
				)  # Exponential backoff

				logger.info(
					f'Attempting to reconnect {connection_id} (attempt {connection.reconnect_attempts + 1})'
				)

				# Recreate connection
				streams = list(connection.streams)
				new_connection = await self._create_connection(streams)

				# Update connection
				connection.websocket = new_connection.websocket
				connection.is_connected = True
				connection.reconnect_attempts = 0

				# Restart connection loop
				asyncio.create_task(self._connection_loop(connection_id, connection))
				break

			except Exception as e:
				connection.reconnect_attempts += 1
				logger.error(
					f'Reconnection attempt {connection.reconnect_attempts} failed for {connection_id}: {e}'
				)

		if connection.reconnect_attempts >= connection.max_reconnect_attempts:
			logger.error(f'Max reconnection attempts reached for {connection_id}')

	def register_handler(self, stream_name: str, handler: Callable) -> None:
		"""Register a message handler for a stream.

		Args:
		    stream_name: Stream name to handle
		    handler: Async callable to handle messages
		"""
		self._message_handlers[stream_name] = handler
		logger.info(f'Registered handler for stream: {stream_name}')

	async def subscribe_to_stream(
		self, config: StreamConfig, handler: Optional[Callable] = None
	) -> str:
		"""Subscribe to a WebSocket stream.

		Args:
		    config: Stream configuration
		    handler: Optional message handler

		Returns:
		    Stream name
		"""
		stream_name = self._format_stream_name(config)

		# Register handler if provided
		if handler:
			self.register_handler(stream_name, handler)

		# Store stream config
		self._active_streams[stream_name] = config

		# Create or find connection
		connection_id = f'conn_{len(self._connections)}'

		if len(self._connections) < self._max_connections:
			# Create new connection
			try:
				connection = await self._create_connection([stream_name])
				self._connections[connection_id] = connection

				# Start connection loop
				asyncio.create_task(self._connection_loop(connection_id, connection))

			except Exception as e:
				logger.error(f'Failed to create connection for {stream_name}: {e}')
				raise
		else:
			# Add to existing connection (if possible)
			# For simplicity, we'll create a new connection
			# In production, you might want to combine streams
			logger.warning(
				'Maximum connections reached, creating new connection anyway'
			)
			try:
				connection = await self._create_connection([stream_name])
				self._connections[connection_id] = connection
				asyncio.create_task(self._connection_loop(connection_id, connection))
			except Exception as e:
				logger.error(
					f'Failed to create additional connection for {stream_name}: {e}'
				)
				raise

		logger.info(f'Subscribed to stream: {stream_name}')
		return stream_name

	async def unsubscribe_from_stream(self, stream_name: str) -> None:
		"""Unsubscribe from a WebSocket stream.

		Args:
		    stream_name: Stream name to unsubscribe from
		"""
		# Remove from active streams
		if stream_name in self._active_streams:
			del self._active_streams[stream_name]

		# Remove handler
		if stream_name in self._message_handlers:
			del self._message_handlers[stream_name]

		# Find and close connection if it only has this stream
		for conn_id, connection in self._connections.items():
			if stream_name in connection.streams:
				connection.streams.discard(stream_name)

				# If no more streams, close connection
				if not connection.streams and connection.websocket:
					await connection.websocket.close()
					connection.is_connected = False

		logger.info(f'Unsubscribed from stream: {stream_name}')

	async def start(self) -> None:
		"""Start the WebSocket manager."""
		self._running = True
		logger.info('WebSocket manager started')

	async def stop(self) -> None:
		"""Stop the WebSocket manager and close all connections."""
		self._running = False

		# Close all connections
		for connection in self._connections.values():
			if connection.websocket and not connection.websocket.closed:
				await connection.websocket.close()
			connection.is_connected = False

		self._connections.clear()
		self._active_streams.clear()
		self._message_handlers.clear()

		logger.info('WebSocket manager stopped')

	def get_status(self) -> Dict[str, Any]:
		"""Get WebSocket manager status.

		Returns:
		    Status information
		"""
		return {
			'running': self._running,
			'active_connections': len(self._connections),
			'connected_streams': len(self._active_streams),
			'connection_attempts_5min': len(self._connection_attempts),
			'connections': {
				conn_id: {
					'connected': conn.is_connected,
					'streams': list(conn.streams),
					'reconnect_attempts': conn.reconnect_attempts,
				}
				for conn_id, conn in self._connections.items()
			},
		}

	# Convenience methods for common streams

	async def subscribe_to_trades(self, symbol: str, handler: Callable) -> str:
		"""Subscribe to trade stream for a symbol.

		Args:
		    symbol: Trading pair symbol
		    handler: Message handler

		Returns:
		    Stream name
		"""
		config = StreamConfig(symbol=symbol, stream_type=StreamType.TRADE)
		return await self.subscribe_to_stream(config, handler)

	async def subscribe_to_klines(
		self, symbol: str, interval: str, handler: Callable
	) -> str:
		"""Subscribe to kline stream for a symbol.

		Args:
		    symbol: Trading pair symbol
		    interval: Kline interval (1m, 5m, 1h, etc.)
		    handler: Message handler

		Returns:
		    Stream name
		"""
		config = StreamConfig(
			symbol=symbol, stream_type=StreamType.KLINE, interval=interval
		)
		return await self.subscribe_to_stream(config, handler)

	async def subscribe_to_ticker(self, symbol: str, handler: Callable) -> str:
		"""Subscribe to 24hr ticker stream for a symbol.

		Args:
		    symbol: Trading pair symbol
		    handler: Message handler

		Returns:
		    Stream name
		"""
		config = StreamConfig(symbol=symbol, stream_type=StreamType.TICKER)
		return await self.subscribe_to_stream(config, handler)

	async def subscribe_to_depth(
		self, symbol: str, levels: int = 20, handler: Optional[Callable] = None
	) -> str:
		"""Subscribe to order book depth stream.

		Args:
		    symbol: Trading pair symbol
		    levels: Depth levels (5, 10, 20)
		    handler: Message handler

		Returns:
		    Stream name
		"""
		config = StreamConfig(
			symbol=symbol, stream_type=StreamType.DEPTH, depth_levels=levels
		)
		return await self.subscribe_to_stream(config, handler)
