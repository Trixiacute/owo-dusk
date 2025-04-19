# OwO-Dusk Utilities

This directory contains utility modules that support the main OwO-Dusk bot functionality.

## API Caching System

OwO-Dusk includes an advanced Discord API caching system that reduces API calls, improves performance, and minimizes resource usage, making it particularly suitable for mobile devices like Termux.

### Features

- **Two-Layer Caching**: Memory cache for fast access and SQLite persistent cache for long-term storage
- **Smart TTL Management**: Different cache lifetimes based on data type (messages, users, channels, etc.)
- **Automatic Cleanup**: Background task removes expired cache entries
- **Adaptive Memory Usage**: Least frequently used items are removed first when memory limit is reached
- **Fallback Mechanism**: Regular API calls are used when cache misses or errors occur

### Files

- `api_cache.py`: Core caching implementation with memory and SQLite storage
- `discord_api_helper.py`: Helper functions for Discord API requests with caching

### Usage Example

```python
# Import the helper module
from utils.discord_api_helper import cached_channel_messages, cached_user_info

# Get channel messages with caching
async def get_recent_messages(bot, channel_id, limit=50):
    messages = await cached_channel_messages(bot.session, channel_id, limit)
    return messages

# Get user information with caching
async def get_user_data(bot, user_id):
    user_info = await cached_user_info(bot.session, user_id)
    return user_info
```

### Benefits for Mobile/Termux Users

1. **Reduced Data Usage**: Minimizes redundant API calls by caching responses
2. **Battery Efficiency**: Fewer network operations means less radio usage and longer battery life
3. **Faster Response Time**: Cached data is retrieved instantly without network latency
4. **Offline Resilience**: Some operations can work with cached data during network interruptions
5. **Rate Limit Protection**: Reduces likelihood of hitting Discord's API rate limits

## Other Utilities

- `platform_utils.py`: Platform-specific utilities for different operating systems
- `misspell.py`: Text manipulation for natural-looking message variations 