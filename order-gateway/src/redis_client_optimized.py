"""
Redis client singleton - OPTIMIZED VERSION
Performance improvements for high-frequency trading

Optimizations:
1. Increased connection pool size (10 -> 50)
2. Reduced timeouts (5s -> 1s) for faster failure detection
3. Added pipeline support for batch operations
4. Health check with automatic reconnection
5. Connection pre-warming
"""

import os
import redis
from typing import Optional, List, Dict, Any
from functools import lru_cache
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class RedisConnectionError(Exception):
    """Custom exception for Redis connection failures"""
    pass


class OptimizedRedisClient:
    """
    High-performance Redis client with optimizations for HFT workloads
    
    Performance Features:
    - Connection pool: 50 connections (5x increase)
    - Socket timeout: 1s (5x faster failure detection)
    - Pipeline support: Batch operations for reduced RTT
    - Health monitoring: Auto-reconnect on failures
    - Pre-warmed connections: Faster first request
    """
    
    _instance: Optional[redis.Redis] = None
    _pool: Optional[redis.ConnectionPool] = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        Get or create Redis client instance with optimized settings
        
        Returns:
            redis.Redis: High-performance Redis client
            
        Raises:
            RedisConnectionError: If connection to Redis fails
        """
        if cls._instance is None:
            try:
                # Get Redis configuration from environment
                host = os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", "6379"))
                db = int(os.getenv("REDIS_DB", "0"))
                
                # OPTIMIZATION 1: Larger connection pool for high concurrency
                # Increased from 10 to 50 connections
                max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
                
                # OPTIMIZATION 2: Aggressive timeouts for HFT
                # Reduced from 5s to 1s for faster failure detection
                socket_timeout = float(os.getenv("REDIS_SOCKET_TIMEOUT", "1.0"))
                connect_timeout = float(os.getenv("REDIS_CONNECT_TIMEOUT", "1.0"))
                
                # OPTIMIZATION 3: TCP keepalive for connection health
                socket_keepalive = True
                socket_keepalive_options = {
                    redis.connection.socket.TCP_KEEPIDLE: 1,  # Start keepalive after 1s idle
                    redis.connection.socket.TCP_KEEPINTVL: 1, # Send probes every 1s
                    redis.connection.socket.TCP_KEEPCNT: 3    # 3 failed probes = dead connection
                }
                
                # Create optimized connection pool
                cls._pool = redis.ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,
                    max_connections=max_connections,
                    socket_connect_timeout=connect_timeout,
                    socket_timeout=socket_timeout,
                    socket_keepalive=socket_keepalive,
                    socket_keepalive_options=socket_keepalive_options,
                    health_check_interval=30,  # Check connection health every 30s
                    retry_on_timeout=True,     # Retry failed operations once
                )
                
                cls._instance = redis.Redis(connection_pool=cls._pool)
                
                # Test connection
                cls._instance.ping()
                
                # OPTIMIZATION 4: Pre-warm connection pool
                cls._prewarm_connections()
                
                logger.info(f"✅ Optimized Redis client initialized: "
                           f"pool_size={max_connections}, "
                           f"timeout={socket_timeout}s")
                
            except (redis.ConnectionError, redis.TimeoutError) as e:
                raise RedisConnectionError(f"Failed to connect to Redis: {str(e)}")
            except Exception as e:
                raise RedisConnectionError(f"Unexpected Redis error: {str(e)}")
        
        return cls._instance
    
    @classmethod
    def _prewarm_connections(cls, num_connections: int = 5):
        """
        Pre-warm connection pool by creating connections in advance
        
        This eliminates connection overhead on first requests
        """
        try:
            for i in range(num_connections):
                conn = cls._pool.get_connection('ping')
                cls._pool.release(conn)
            
            logger.debug(f"Pre-warmed {num_connections} Redis connections")
        except Exception as e:
            logger.warning(f"Failed to pre-warm connections: {e}")
    
    @classmethod
    @contextmanager
    def pipeline(cls, transaction: bool = True):
        """
        Context manager for Redis pipeline (batch operations)
        
        Usage:
            with OptimizedRedisClient.pipeline() as pipe:
                pipe.rpush("queue1", "data1")
                pipe.rpush("queue2", "data2")
                pipe.execute()  # Send all commands in one RTT
        
        Args:
            transaction: If True, commands execute atomically
            
        Yields:
            redis.client.Pipeline: Redis pipeline object
        """
        client = cls.get_client()
        pipe = client.pipeline(transaction=transaction)
        try:
            yield pipe
        finally:
            pipe.reset()
    
    @classmethod
    def batch_rpush(cls, queue_data: Dict[str, List[str]]) -> None:
        """
        Batch RPUSH operations using pipeline for better performance
        
        Instead of N network round trips, executes in 1 RTT
        
        Args:
            queue_data: Dict mapping queue names to lists of items
            
        Example:
            batch_rpush({
                "order_queue": ["order1", "order2"],
                "trade_queue": ["trade1"]
            })
        """
        with cls.pipeline(transaction=False) as pipe:
            for queue_name, items in queue_data.items():
                for item in items:
                    pipe.rpush(queue_name, item)
            pipe.execute()
    
    @classmethod
    def batch_publish(cls, channel_messages: Dict[str, List[str]]) -> None:
        """
        Batch PUBLISH operations using pipeline
        
        Reduces network overhead when publishing multiple messages
        
        Args:
            channel_messages: Dict mapping channel names to message lists
        """
        with cls.pipeline(transaction=False) as pipe:
            for channel, messages in channel_messages.items():
                for message in messages:
                    pipe.publish(channel, message)
            pipe.execute()
    
    @classmethod
    def health_check(cls) -> bool:
        """
        Perform health check on Redis connection
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if cls._instance:
                cls._instance.ping()
                return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        
        return False
    
    @classmethod
    def reset_client(cls):
        """Reset client instance (useful for testing)"""
        if cls._instance:
            cls._instance.close()
        cls._instance = None
        cls._pool = None


@lru_cache
def get_redis_client() -> redis.Redis:
    """
    Dependency injection function for FastAPI
    
    Returns cached optimized Redis client instance
    Time complexity: O(1) with connection pooling
    """
    return OptimizedRedisClient.get_client()


def get_redis_pipeline(transaction: bool = True):
    """
    Get Redis pipeline for batch operations
    
    Use this for submitting multiple orders efficiently:
        with get_redis_pipeline() as pipe:
            for order in orders:
                pipe.rpush("order_queue", json.dumps(order))
            pipe.execute()
    """
    return OptimizedRedisClient.pipeline(transaction=transaction)

