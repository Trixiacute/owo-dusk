"""
This file is part of owo-dusk.

Copyright (c) 2024-present EchoQuill

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import json
import time
import os
import sqlite3
import threading
from typing import Any, Dict, Optional, Tuple, Union

# Lock for thread safety
cache_lock = threading.Lock()

# Default settings
DEFAULT_TTL = 300  # 5 minutes in seconds
MAX_MEMORY_CACHE_SIZE = 100  # Maximum entries in memory cache
DB_PATH = "utils/discord_api_cache.db"  # SQLite database path

# In-memory cache for faster access to frequently used data
memory_cache = {}


def initialize_cache_db():
    """Initialize the SQLite database for persistent cache storage."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Create cache table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_cache (
            cache_key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            timestamp REAL NOT NULL,
            expires REAL NOT NULL,
            access_count INTEGER DEFAULT 1
        )
        ''')
        
        # Create index for faster expiration queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires ON api_cache(expires)')
        
        conn.commit()


def _generate_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
    """
    Generate a unique cache key based on the endpoint and parameters.
    
    Args:
        endpoint: The API endpoint path
        params: The parameters for the API call
        
    Returns:
        A unique string to use as cache key
    """
    # Sort params to ensure consistent key generation
    sorted_params = json.dumps(params, sort_keys=True) if params else "{}"
    return f"{endpoint}:{sorted_params}"


def get_cached_api_result(endpoint: str, params: Optional[Dict[str, Any]] = None, 
                          ttl: int = DEFAULT_TTL) -> Optional[Any]:
    """
    Get a result from the cache, or return None if not found or expired.
    
    Args:
        endpoint: The API endpoint path
        params: The parameters for the API call
        ttl: Time to live in seconds for this cache entry
        
    Returns:
        The cached data if found and valid, otherwise None
    """
    if params is None:
        params = {}
        
    cache_key = _generate_cache_key(endpoint, params)
    current_time = time.time()
    
    # First check in-memory cache for faster access
    with cache_lock:
        if cache_key in memory_cache:
            cache_entry = memory_cache[cache_key]
            if cache_entry["expires"] > current_time:
                # Update access count
                cache_entry["access_count"] += 1
                return cache_entry["data"]
    
    # If not in memory, check persistent storage
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT data, access_count FROM api_cache WHERE cache_key = ? AND expires > ?',
                (cache_key, current_time)
            )
            
            result = cursor.fetchone()
            if result:
                data, access_count = result
                # Update access count
                cursor.execute(
                    'UPDATE api_cache SET access_count = ? WHERE cache_key = ?',
                    (access_count + 1, cache_key)
                )
                conn.commit()
                
                # Load the JSON data
                cached_data = json.loads(data)
                
                # If frequently accessed, add to memory cache
                if access_count > 3:
                    with cache_lock:
                        memory_cache[cache_key] = {
                            "data": cached_data,
                            "timestamp": current_time,
                            "expires": current_time + ttl,
                            "access_count": access_count + 1
                        }
                        # Manage memory cache size
                        _manage_memory_cache_size()
                
                return cached_data
    except sqlite3.Error as e:
        print(f"SQLite error in get_cached_api_result: {e}")
    
    return None


def save_api_result(endpoint: str, params: Optional[Dict[str, Any]], 
                    data: Any, ttl: int = DEFAULT_TTL) -> None:
    """
    Save API result to both memory and persistent cache.
    
    Args:
        endpoint: The API endpoint path
        params: The parameters for the API call
        data: The data to cache
        ttl: Time to live in seconds for this cache entry
    """
    if params is None:
        params = {}
        
    cache_key = _generate_cache_key(endpoint, params)
    current_time = time.time()
    expires = current_time + ttl
    
    # Save to memory cache
    with cache_lock:
        memory_cache[cache_key] = {
            "data": data,
            "timestamp": current_time,
            "expires": expires,
            "access_count": 1
        }
        # Manage memory cache size
        _manage_memory_cache_size()
    
    # Save to persistent storage
    try:
        json_data = json.dumps(data)
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT OR REPLACE INTO api_cache 
                (cache_key, data, timestamp, expires, access_count)
                VALUES (?, ?, ?, ?, 1)
                ''',
                (cache_key, json_data, current_time, expires)
            )
            
            conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite error in save_api_result: {e}")


def clear_expired_cache() -> int:
    """
    Clear expired entries from both memory and persistent cache.
    
    Returns:
        Number of entries cleared
    """
    current_time = time.time()
    cleared_count = 0
    
    # Clear from memory cache
    with cache_lock:
        expired_keys = [k for k, v in memory_cache.items() if v["expires"] <= current_time]
        for key in expired_keys:
            del memory_cache[key]
        cleared_count += len(expired_keys)
    
    # Clear from persistent storage
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM api_cache WHERE expires <= ?', (current_time,))
            cleared_count += cursor.rowcount
            
            conn.commit()
    except sqlite3.Error as e:
        print(f"SQLite error in clear_expired_cache: {e}")
    
    return cleared_count


def _manage_memory_cache_size():
    """
    Keep the memory cache size within limits by removing least accessed items.
    """
    if len(memory_cache) <= MAX_MEMORY_CACHE_SIZE:
        return
    
    # Sort by access count and then by expiration time
    sorted_items = sorted(
        memory_cache.items(),
        key=lambda x: (x[1]["access_count"], x[1]["expires"])
    )
    
    # Remove oldest/least accessed items
    items_to_remove = len(memory_cache) - MAX_MEMORY_CACHE_SIZE
    for i in range(items_to_remove):
        del memory_cache[sorted_items[i][0]]


def get_cache_stats() -> Dict[str, Union[int, float]]:
    """
    Get statistics about the cache.
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Get total entries
            cursor.execute('SELECT COUNT(*) FROM api_cache')
            total_entries = cursor.fetchone()[0]
            
            # Get expired entries
            current_time = time.time()
            cursor.execute('SELECT COUNT(*) FROM api_cache WHERE expires <= ?', (current_time,))
            expired_entries = cursor.fetchone()[0]
            
            # Get average TTL
            cursor.execute('SELECT AVG(expires - timestamp) FROM api_cache')
            avg_ttl = cursor.fetchone()[0] or 0
            
            return {
                "memory_cache_size": len(memory_cache),
                "persistent_cache_size": total_entries,
                "expired_entries": expired_entries,
                "average_ttl": avg_ttl,
                "db_path": DB_PATH
            }
    except sqlite3.Error as e:
        print(f"SQLite error in get_cache_stats: {e}")
        return {
            "memory_cache_size": len(memory_cache),
            "error": str(e)
        }


# Initialize the cache database when the module is imported
initialize_cache_db() 