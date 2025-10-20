"""
Constants for Order Gateway and system-wide configuration
Centralizes Redis keys, service ports, and other configuration
"""

# Redis Queue/Channel Names
ORDER_QUEUE = "order_queue"
TRADE_EVENTS_CHANNEL = "trade_events"
BBO_UPDATES_CHANNEL = "bbo_updates"
ORDER_BOOK_UPDATES_CHANNEL = "order_book_updates"

# Service Ports
ORDER_GATEWAY_PORT = 8000
MARKET_DATA_PORT = 8001

# API Version
API_VERSION = "v1"

# Symbols
DEFAULT_SYMBOL = "BTC-USDT"

