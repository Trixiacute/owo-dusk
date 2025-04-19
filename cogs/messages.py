# This file is part of owo-dusk.
#
# Copyright (c) 2024-present EchoQuill
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
messages.py - Example implementation of Discord API caching for message history
This module is primarily meant to serve as a reference for how to use the caching system
"""

import asyncio
import time
from discord.ext import commands, tasks

# Import custom API caching utilities if available
try:
    from utils.discord_api_helper import (
        cached_channel_messages, 
        cached_user_info,
        cached_channel_info
    )
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


class Messages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_check_time = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        
    async def cog_load(self):
        # Start the task that periodically reports cache statistics
        if CACHE_AVAILABLE and self.bot.config_dict.get("debug", {}).get("enabled", False):
            self.report_cache_stats.start()
    
    async def cog_unload(self):
        # Stop background tasks
        if hasattr(self, 'report_cache_stats') and self.report_cache_stats.is_running():
            self.report_cache_stats.cancel()
    
    @tasks.loop(minutes=30)
    async def report_cache_stats(self):
        """Periodically report cache hit/miss statistics"""
        if self.cache_hit_count + self.cache_miss_count > 0:
            hit_rate = self.cache_hit_count / (self.cache_hit_count + self.cache_miss_count) * 100
            await self.bot.log(
                f"API Cache stats: {self.cache_hit_count} hits, {self.cache_miss_count} misses ({hit_rate:.1f}% hit rate)", 
                "#33245e"
            )
            
            # Get detailed cache stats if available
            try:
                from utils.api_cache import get_cache_stats
                stats = get_cache_stats()
                stats_str = ", ".join([f"{k}: {v}" for k, v in stats.items() if k != 'db_path'])
                await self.bot.log(f"Cache details: {stats_str}", "#33245e")
            except ImportError:
                pass
            
            # Reset counters
            self.cache_hit_count = 0
            self.cache_miss_count = 0
    
    @report_cache_stats.before_loop
    async def before_report_cache_stats(self):
        # Wait until the bot is ready before starting the task
        await self.bot.wait_until_ready()
        await asyncio.sleep(600)  # Start reporting after 10 minutes
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Only process messages in the target channel
        if message.channel.id != self.bot.channel_id:
            return
            
        # Throttle checks to avoid unnecessary processing
        current_time = time.time()
        if current_time - self.last_check_time < 5:  # Check at most once every 5 seconds
            return
            
        self.last_check_time = current_time
        
        # Example: Check for specific command patterns
        if message.content.startswith(f"{self.bot.config_dict.get('setprefix', 'w')}help"):
            await self.analyze_recent_messages()
    
    async def analyze_recent_messages(self):
        """Example function that uses cached channel history"""
        if not CACHE_AVAILABLE:
            return
            
        try:
            # Get cached channel messages
            start_time = time.time()
            messages = await cached_channel_messages(self.bot.session, str(self.bot.channel_id), 20)
            end_time = time.time()
            
            # Update cache statistics
            if end_time - start_time < 0.05:  # If retrieval was fast, likely a cache hit
                self.cache_hit_count += 1
            else:
                self.cache_miss_count += 1
                
            # Process the messages (this is just an example)
            owo_messages = [msg for msg in messages if msg.get('author', {}).get('id') == self.bot.owo_bot_id]
            
            if self.bot.config_dict.get("debug", {}).get("enabled", False) and len(owo_messages) > 0:
                await self.bot.log(
                    f"Found {len(owo_messages)} recent OwO bot messages using cached API", 
                    "#33245e"
                )
                
        except Exception as e:
            if self.bot.config_dict.get("debug", {}).get("enabled", False):
                await self.bot.log(f"Error in cached message analysis: {e}", "#ff0000")
    
    async def get_user_with_cache(self, user_id):
        """Example of using cached user info"""
        if not CACHE_AVAILABLE:
            return await self.bot.fetch_user(user_id)
            
        try:
            user_data = await cached_user_info(self.bot.session, str(user_id))
            return user_data
        except Exception:
            # Fallback to standard API
            return await self.bot.fetch_user(user_id)
    
    async def get_channel_with_cache(self, channel_id):
        """Example of using cached channel info"""
        if not CACHE_AVAILABLE:
            return await self.bot.fetch_channel(channel_id)
            
        try:
            channel_data = await cached_channel_info(self.bot.session, str(channel_id))
            return channel_data
        except Exception:
            # Fallback to standard API
            return await self.bot.fetch_channel(channel_id)


async def setup(bot):
    # Only load this module if API caching is enabled in config
    if bot.config_dict.get("apiCache", {}).get("enabled", False):
        await bot.add_cog(Messages(bot)) 