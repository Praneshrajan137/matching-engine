"""
Redis client singleton for Order Gateway
Implements Redis connection with error handling and connection pooling
"""

import os
import redis
from typing import Optional
from functools import lru_cache


class RedisConnectionError(Exception):
    """Custom exception for Redis connection failures"""
    pass


class RedisClient:
    """
    Redis client wrapper with connection pooling
    
    Implements singleton pattern to reuse connections
    Handles connection errors gracefully per FR-3.1 error handling
    """
    
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        Get or create Redis client instance
        
        Returns:
            redis.Redis: Configured Redis client
            
        Raises:
            RedisConnectionError: If connection to Redis fails
        """
        if cls._instance is None:
            try:
                # Get Redis configuration from environment (defaults for development)
                host = os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", "6379"))
                db = int(os.getenv("REDIS_DB", "0"))
                
                # Create connection pool for better performance
                pool = redis.ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,  # Auto-decode bytes to strings
                    max_connections=10,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
                cls._instance = redis.Redis(connection_pool=pool)
                
                # Test connection
                cls._instance.ping()
                
            except (redis.ConnectionError, redis.TimeoutError) as e:
                raise RedisConnectionError(f"Failed to connect to Redis: {str(e)}")
            except Exception as e:
                raise RedisConnectionError(f"Unexpected Redis error: {str(e)}")
        
        return cls._instance
    
    @classmethod
    def reset_client(cls):
        """Reset client instance (useful for testing)"""
        if cls._instance:
            cls._instance.close()
        cls._instance = None


@lru_cache
def get_redis_client() -> redis.Redis:
    """
    Dependency injection function for FastAPI
    
    Returns cached Redis client instance
    Time complexity: O(1) with connection pooling
    """
    return RedisClient.get_client()

