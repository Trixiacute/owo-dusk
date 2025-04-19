"""
This file is part of owo-dusk.

Copyright (c) 2024-present EchoQuill

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union

from utils.api_cache import (
    get_cached_api_result,
    save_api_result,
    clear_expired_cache,
    get_cache_stats
)

# TTL (Time-to-live) values in seconds for different types of API calls
TTL_SETTINGS = {
    "default": 300,           # Default: 5 minutes
    "message_history": 60,    # Message history: 1 minute
    "channel_info": 3600,     # Channel info: 1 hour
    "user_info": 3600,        # User info: 1 hour
    "guild_info": 7200,       # Guild info: 2 hours
    "static_assets": 86400,   # Static assets: 24 hours
}

# Endpoints categorized by TTL type
ENDPOINT_CATEGORIES = {
    "message_history": [
        "channels/{channel_id}/messages"
    ],
    "channel_info": [
        "channels/{channel_id}",
        "guilds/{guild_id}/channels"
    ],
    "user_info": [
        "users/{user_id}",
        "users/@me"
    ],
    "guild_info": [
        "guilds/{guild_id}"
    ],
    "static_assets": [
        "stickers",
        "emojis"
    ]
}


def _determine_ttl(endpoint: str) -> int:
    """
    Determine the appropriate TTL for an endpoint based on its category.
    
    Args:
        endpoint: The API endpoint
        
    Returns:
        The TTL in seconds
    """
    for category, patterns in ENDPOINT_CATEGORIES.items():
        for pattern in patterns:
            if pattern.replace("{channel_id}", "\\d+").replace("{guild_id}", "\\d+").replace("{user_id}", "\\d+") in endpoint:
                return TTL_SETTINGS[category]
    
    return TTL_SETTINGS["default"]


async def cached_api_request(client_session, endpoint: str, 
                            params: Optional[Dict[str, Any]] = None,
                            method: str = "GET",
                            custom_ttl: Optional[int] = None,
                            force_refresh: bool = False) -> Any:
    """
    Make an API request with caching.
    
    Args:
        client_session: The aiohttp ClientSession to use for requests
        endpoint: The API endpoint
        params: Query parameters
        method: HTTP method (GET, POST, etc.)
        custom_ttl: Override the default TTL
        force_refresh: Force a refresh of the cache
        
    Returns:
        The API response data
    """
    if params is None:
        params = {}
    
    # For non-GET methods, we don't use cache
    if method != "GET":
        force_refresh = True
    
    # Determine TTL
    ttl = custom_ttl if custom_ttl is not None else _determine_ttl(endpoint)
    
    # Try to get from cache unless force_refresh is True
    if not force_refresh:
        cached_result = get_cached_api_result(endpoint, params, ttl)
        if cached_result is not None:
            return cached_result
    
    # Cache miss or forced refresh, make the actual API call
    response = await client_session.request(
        method=method,
        url=f"https://discord.com/api/v10/{endpoint}",
        params=params
    )
    
    # Check for rate limits
    if response.status == 429:
        # Get retry after time
        retry_after = float(response.headers.get("Retry-After", 1))
        print(f"Rate limited on {endpoint}, waiting {retry_after} seconds")
        await asyncio.sleep(retry_after)
        # Recursively retry the request
        return await cached_api_request(client_session, endpoint, params, method, custom_ttl, force_refresh)
    
    # Parse the response
    try:
        if "application/json" in response.headers.get("Content-Type", ""):
            data = await response.json()
        else:
            data = await response.text()
    except Exception as e:
        print(f"Error parsing API response: {e}")
        data = await response.text()
    
    # Cache successful GET responses
    if response.status == 200 and method == "GET":
        save_api_result(endpoint, params, data, ttl)
    
    # Periodically clean the cache
    if random.random() < 0.05:  # 5% chance each request
        asyncio.create_task(asyncio.to_thread(clear_expired_cache))
    
    return data


async def cached_channel_messages(client_session, channel_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get cached channel messages.
    
    Args:
        client_session: The aiohttp ClientSession
        channel_id: The channel ID
        limit: Number of messages to fetch
        
    Returns:
        List of message objects
    """
    endpoint = f"channels/{channel_id}/messages"
    params = {"limit": limit}
    
    return await cached_api_request(client_session, endpoint, params)


async def cached_user_info(client_session, user_id: str) -> Dict[str, Any]:
    """
    Get cached user info.
    
    Args:
        client_session: The aiohttp ClientSession
        user_id: The user ID
        
    Returns:
        User info object
    """
    endpoint = f"users/{user_id}"
    
    return await cached_api_request(client_session, endpoint)


async def cached_channel_info(client_session, channel_id: str) -> Dict[str, Any]:
    """
    Get cached channel info.
    
    Args:
        client_session: The aiohttp ClientSession
        channel_id: The channel ID
        
    Returns:
        Channel info object
    """
    endpoint = f"channels/{channel_id}"
    
    return await cached_api_request(client_session, endpoint)


async def cached_guild_info(client_session, guild_id: str) -> Dict[str, Any]:
    """
    Get cached guild info.
    
    Args:
        client_session: The aiohttp ClientSession
        guild_id: The guild ID
        
    Returns:
        Guild info object
    """
    endpoint = f"guilds/{guild_id}"
    
    return await cached_api_request(client_session, endpoint)


# Missing import added here
import random 