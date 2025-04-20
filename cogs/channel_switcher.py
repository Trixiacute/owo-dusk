# This file is part of owo-dusk.
#
# Copyright (c) 2024-present EchoQuill
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import random
import asyncio
import discord
import time
from discord.ext import commands, tasks
from utils.platform_utils import IS_TERMUX
import json
from datetime import timedelta

class ChannelSwitcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_channel = None
        self.last_switch_time = 0
        self.commands_since_switch = 0
        self.switch_lock = asyncio.Lock()
        self.available_channels = []
        self.available_threads = []
        self.original_channel = None
        
    async def cog_load(self):
        # Store the original channel
        self.original_channel = self.bot.cm
        
        # Initialize channel list from config
        await self.update_channel_list()
        
        # Start switcher task if enabled
        if self.bot.config_dict.get("channel_switcher", {}).get("enabled", False):
            self.channel_switch_task.start()
    
    async def cog_unload(self):
        # Stop the task if running
        if hasattr(self, 'channel_switch_task') and self.channel_switch_task.is_running():
            self.channel_switch_task.cancel()
            
        # Restore original channel
        if self.original_channel:
            self.bot.cm = self.original_channel
    
    async def update_channel_list(self):
        """Update the list of available channels and threads from config"""
        self.available_channels = []
        self.available_threads = []
        
        # Get channel IDs from config
        channel_ids = self.bot.config_dict.get("channel_switcher", {}).get("channels", [])
        
        # Add valid channel IDs to available_channels
        for channel_id in channel_ids:
            try:
                channel = self.bot.get_channel(channel_id)
                if channel is None:
                    channel = await self.bot.fetch_channel(channel_id)
                
                if channel:
                    self.available_channels.append(channel)
                    await self.bot.log(f"Added channel {channel.name} ({channel.id}) to switcher", "#70af87")
            except discord.errors.NotFound:
                await self.bot.log(f"Channel {channel_id} not found", "#af7070")
            except Exception as e:
                await self.bot.log(f"Error adding channel {channel_id}: {e}", "#af7070")
        
        # Get thread info from config
        threads_config = self.bot.config_dict.get("channel_switcher", {}).get("threads", {})
        if threads_config.get("enabled", False):
            parent_id = threads_config.get("parent_channel", 0)
            thread_ids = threads_config.get("thread_ids", [])
            
            try:
                # Get parent channel
                parent_channel = self.bot.get_channel(parent_id)
                if parent_channel is None:
                    parent_channel = await self.bot.fetch_channel(parent_id)
                
                # Get threads
                for thread_id in thread_ids:
                    try:
                        thread = None
                        # First check if thread is in the bot's cached threads
                        for t in self.bot.get_all_threads():
                            if t.id == thread_id:
                                thread = t
                                break
                        
                        # If not found in cache, try to fetch it
                        if thread is None:
                            thread = await self.bot.fetch_channel(thread_id)
                        
                        if thread and isinstance(thread, discord.Thread):
                            self.available_threads.append(thread)
                            await self.bot.log(f"Added thread {thread.name} ({thread.id}) to switcher", "#70af87")
                    except Exception as e:
                        await self.bot.log(f"Error adding thread {thread_id}: {e}", "#af7070")
            except Exception as e:
                await self.bot.log(f"Error setting up thread switching: {e}", "#af7070")
        
        # Auto-discovery: Find recent active channels and threads from guilds
        if self.bot.config_dict.get("channel_switcher", {}).get("auto_discover", False):
            await self.discover_channels()
        
        # Reset to original channel if no channels available
        if not self.available_channels and not self.available_threads:
            self.bot.cm = self.original_channel
            self.active_channel = None
            await self.bot.log("No channels or threads available for switching. Using original channel.", "#70af87")
            
            # Auto-create thread if enabled and no channels/threads are available
            if self.bot.config_dict.get("channel_switcher", {}).get("auto_create_thread", False):
                await self.create_new_thread()
    
    async def discover_channels(self):
        """Discover potential channels and threads for switching based on message activity"""
        try:
            # Auto-discover channels with recent OwO activity
            discovered_count = 0
            guilds = self.bot.guilds
            
            for guild in guilds:
                # Skip guilds with too many members (likely public servers)
                if guild.member_count > 500 and not self.bot.config_dict.get("channel_switcher", {}).get("include_large_servers", False):
                    continue
                    
                # Check text channels with permissions
                for channel in guild.text_channels:
                    # Skip if we already have this channel
                    if channel in self.available_channels:
                        continue
                        
                    # Check permissions
                    if not channel.permissions_for(guild.me).send_messages:
                        continue
                        
                    # Check for recent OwO bot activity
                    try:
                        owo_activity = False
                        async for message in channel.history(limit=20):
                            if message.author.id == self.bot.owo_bot_id:
                                owo_activity = True
                                break
                                
                        if owo_activity:
                            self.available_channels.append(channel)
                            discovered_count += 1
                            
                            # Add to config for persistence
                            if channel.id not in self.bot.config_dict.get("channel_switcher", {}).get("channels", []):
                                channel_ids = self.bot.config_dict.get("channel_switcher", {}).get("channels", [])
                                channel_ids.append(channel.id)
                                self.bot.config_dict["channel_switcher"]["channels"] = channel_ids
                                with open("config.json", "w") as config_file:
                                    json.dump(self.bot.config_dict, config_file, indent=4)
                            
                            await self.bot.log(f"Auto-discovered channel: {channel.name} ({channel.id})", "#70af87")
                    except Exception as e:
                        # Silently continue if we can't check history
                        continue
            
            if discovered_count > 0:
                await self.bot.log(f"Auto-discovered {discovered_count} new channels for switching", "#70af87")
        except Exception as e:
            await self.bot.log(f"Error in channel discovery: {e}", "#af7070")

    async def create_new_thread(self, channel=None, name=None):
        """Create a new thread for safer operation"""
        try:
            if not channel:
                # Use the original channel if no channel specified
                channel = self.original_channel
                
                # Check for any channel with thread permissions
                if channel and hasattr(channel, 'guild') and not channel.permissions_for(channel.guild.me).create_public_threads:
                    for ch in self.available_channels:
                        if hasattr(ch, 'guild') and ch.permissions_for(ch.guild.me).create_public_threads:
                            channel = ch
                            break
            
            # Check if channel exists
            if not channel:
                await self.bot.log("Cannot create thread: no valid channel found", "#af7070")
                return None
                
            # Check permissions
            if not hasattr(channel, 'guild') or not channel.permissions_for(channel.guild.me).create_public_threads:
                await self.bot.log(f"Cannot create thread in {getattr(channel, 'name', 'unknown')}: missing permissions", "#af7070")
                return None
            
            # Generate random thread name if not provided
            if not name:
                adjectives = ["cool", "awesome", "great", "nice", "super", "amazing", "wonderful", "friendly", "lovely"]
                nouns = ["chat", "discussion", "hangout", "lounge", "corner", "place", "spot", "zone", "area"]
                name = f"{random.choice(adjectives)}-{random.choice(nouns)}-{random.randint(1000, 9999)}"
            
            # Create the thread
            try:
                thread = await channel.create_thread(
                    name=name,
                    type=discord.ChannelType.public_thread,
                    auto_archive_duration=1440  # 24 hours
                )
            except Exception as e:
                await self.bot.log(f"Failed to create thread in {getattr(channel, 'name', 'unknown')}: {e}", "#af7070")
                return None
                
            # Check if thread was created successfully
            if thread is None:
                await self.bot.log(f"Thread creation failed in {getattr(channel, 'name', 'unknown')}: returned None", "#af7070")
                return None
            
            # Add to available threads
            self.available_threads.append(thread)
            
            # Add to config for persistence
            threads_config = self.bot.config_dict.get("channel_switcher", {}).get("threads", {})
            
            # Ensure threads section exists in config
            if "threads" not in self.bot.config_dict.get("channel_switcher", {}):
                self.bot.config_dict["channel_switcher"]["threads"] = {
                    "enabled": False,
                    "parent_channel": 0,
                    "thread_ids": []
                }
                threads_config = self.bot.config_dict["channel_switcher"]["threads"]
            
            if not threads_config.get("enabled", False):
                self.bot.config_dict["channel_switcher"]["threads"]["enabled"] = True
            
            # Ensure channel exists before accessing channel.id
            if channel and hasattr(channel, 'id') and channel.id != threads_config.get("parent_channel", 0):
                self.bot.config_dict["channel_switcher"]["threads"]["parent_channel"] = channel.id
            
            thread_ids = threads_config.get("thread_ids", [])
            if not isinstance(thread_ids, list):
                thread_ids = []
            
            # Ensure thread exists and has id before appending
            if thread and hasattr(thread, 'id'):
                thread_ids.append(thread.id)
                self.bot.config_dict["channel_switcher"]["threads"]["thread_ids"] = thread_ids
                
                # Save config
                with open("config.json", "w") as config_file:
                    json.dump(self.bot.config_dict, config_file, indent=4)
                
                await self.bot.log(f"Created new thread: {thread.name} ({thread.id})", "#70af87")
                
                # Switch to the new thread
                await self.switch_channel(specific_thread=thread.id)
                
                return thread
            else:
                await self.bot.log("Thread was created but has no valid ID", "#af7070")
                return None
        
        except Exception as e:
            await self.bot.log(f"Error creating thread: {e}", "#af7070")
            return None

    async def create_new_channel(self, guild, name=None, category=None):
        """Create a new channel for safer operation - USE WITH CAUTION"""
        try:
            # Check if auto-create is enabled
            if not self.bot.config_dict.get("channel_switcher", {}).get("auto_create_channel", False):
                await self.bot.log("Auto-create channel is disabled in config", "#af7070")
                return None
            
            # Check permissions
            if not guild.me.guild_permissions.manage_channels:
                await self.bot.log(f"Cannot create channel in {guild.name}: missing permissions", "#af7070")
                return None
            
            # Generate random channel name if not provided
            if not name:
                adjectives = ["cool", "awesome", "great", "nice", "super", "amazing", "wonderful", "friendly", "lovely"]
                nouns = ["chat", "discussion", "hangout", "lounge", "corner", "place", "spot", "zone", "area"]
                name = f"{random.choice(adjectives)}-{random.choice(nouns)}-{random.randint(1000, 9999)}"
            
            # Create the channel
            channel = await guild.create_text_channel(
                name=name,
                category=category,
                reason="Auto-created by OwO-Dusk Channel Switcher"
            )
            
            # Add to available channels
            self.available_channels.append(channel)
            
            # Add to config for persistence
            channel_ids = self.bot.config_dict.get("channel_switcher", {}).get("channels", [])
            channel_ids.append(channel.id)
            self.bot.config_dict["channel_switcher"]["channels"] = channel_ids
            
            # Save config
            with open("config.json", "w") as config_file:
                json.dump(self.bot.config_dict, config_file, indent=4)
            
            await self.bot.log(f"Created new channel: {channel.name} ({channel.id})", "#70af87")
            
            # Switch to the new channel
            await self.switch_channel(specific_channel=channel.id)
            
            return channel
        
        except Exception as e:
            await self.bot.log(f"Error creating channel: {e}", "#af7070")
            return None
    
    async def analyze_channel_safety(self, channel):
        """Analyze if a channel is safe for bot usage"""
        try:
            # Check if channel is None or invalid
            if channel is None or not hasattr(channel, 'id'):
                return 0  # Not safe at all
                
            safety_score = 100  # Start with perfect score
            
            # Check for slowmode
            if hasattr(channel, 'slowmode_delay') and channel.slowmode_delay > 0:
                safety_score -= 30
            
            # Check message volume from other users
            user_message_count = 0
            try:
                if hasattr(channel, 'history'):
                    async for message in channel.history(limit=50):
                        if hasattr(message, 'author') and hasattr(message.author, 'id') and message.author.id != self.bot.user.id and message.author.id != self.bot.owo_bot_id:
                            user_message_count += 1
            except Exception as e:
                # If we can't check history, assume it's risky
                await self.bot.log(f"Error checking message history in channel {getattr(channel, 'name', 'unknown')}: {e}", "#af7070")
                safety_score -= 20
            
            # Adjust score based on message volume
            if user_message_count > 30:  # Very active channel
                safety_score -= 40
            elif user_message_count > 15:  # Moderately active
                safety_score -= 20
            elif user_message_count < 5:  # Low activity, good for bot
                safety_score += 10
            
            # Check if it's a DM or private channel (safer)
            if isinstance(channel, discord.DMChannel):
                safety_score += 20
            
            # Check member count in guild
            if hasattr(channel, 'guild') and hasattr(channel.guild, 'member_count') and channel.guild.member_count > 1000:
                safety_score -= 20
            
            # Ensure score is within valid range
            safety_score = max(0, min(100, safety_score))
            
            return safety_score
        except Exception as e:
            await self.bot.log(f"Error analyzing channel safety for {getattr(channel, 'name', 'unknown')}: {e}", "#af7070")
            return 30  # Default to somewhat unsafe if analysis fails

    @tasks.loop(seconds=60)
    async def channel_switch_task(self):
        """Task to automatically switch channels based on config settings"""
        if not self.bot.is_ready():
            return
            
        # Don't switch if captcha mode is active
        if self.bot.captcha:
            return
            
        # Get config values
        switch_interval = self.bot.config_dict.get("channel_switcher", {}).get("switch_interval", [5, 15])
        commands_per_switch = self.bot.config_dict.get("channel_switcher", {}).get("commands_per_switch", [3, 8])
        
        # Check if it's time to switch based on time interval
        current_time = time.time()
        min_interval = switch_interval[0] * 60  # Convert to seconds
        max_interval = switch_interval[1] * 60  # Convert to seconds
        time_interval = random.uniform(min_interval, max_interval)
        
        # Check if it's time to switch based on command count
        min_commands = commands_per_switch[0]
        max_commands = commands_per_switch[1]
        command_threshold = random.randint(min_commands, max_commands)
        
        if (current_time - self.last_switch_time >= time_interval or 
            self.commands_since_switch >= command_threshold):
            await self.switch_channel()
    
    @channel_switch_task.before_loop
    async def before_channel_switch_task(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(random.uniform(10, 30))  # Random initial delay
    
    async def switch_channel(self, specific_channel=None, specific_thread=None):
        """Switch to a new channel or thread"""
        async with self.switch_lock:
            available_targets = []
            
            # Add available channels - filter out None
            available_targets.extend([c for c in self.available_channels if c is not None])
            
            # Add available threads - filter out None
            available_targets.extend([t for t in self.available_threads if t is not None])
            
            # Add original channel if it's not already in the list
            if self.original_channel and self.original_channel not in available_targets:
                available_targets.append(self.original_channel)
            
            if not available_targets:
                await self.bot.log("No channels available for switching", "#af7070")
                
                # Try to create a new thread if auto-create is enabled
                if self.bot.config_dict.get("channel_switcher", {}).get("auto_create_thread", False):
                    thread = await self.create_new_thread()
                    # Only return if thread was successfully created
                    if thread and hasattr(thread, 'id'):
                        return True
                return False
            
            # Handle specific channel request
            if specific_channel:
                try:
                    channel = self.bot.get_channel(specific_channel)
                    if channel is None:
                        try:
                            channel = await self.bot.fetch_channel(specific_channel)
                        except Exception as e:
                            await self.bot.log(f"Could not fetch channel {specific_channel}: {e}", "#af7070")
                            return False
                    
                    if channel:
                        self.bot.cm = channel
                        self.active_channel = channel
                        self.last_switch_time = time.time()
                        self.commands_since_switch = 0
                        await self.bot.log(f"Switched to specified channel: {channel.name} ({channel.id})", "#70af87")
                        return True
                    else:
                        await self.bot.log(f"Channel {specific_channel} not found", "#af7070")
                        return False
                except Exception as e:
                    await self.bot.log(f"Error switching to specified channel {specific_channel}: {e}", "#af7070")
                    return False
            
            # Handle specific thread request
            if specific_thread:
                try:
                    thread = None
                    # First try to find in already cached threads
                    for t in self.bot.get_all_threads():
                        if t.id == specific_thread:
                            thread = t
                            break
                    
                    # If not found in cache, try to fetch it
                    if thread is None:
                        try:
                            thread = await self.bot.fetch_channel(specific_thread)
                        except Exception as e:
                            await self.bot.log(f"Could not fetch thread {specific_thread}: {e}", "#af7070")
                            return False
                    
                    if thread and isinstance(thread, discord.Thread):
                        self.bot.cm = thread
                        self.active_channel = thread
                        self.last_switch_time = time.time()
                        self.commands_since_switch = 0
                        await self.bot.log(f"Switched to specified thread: {thread.name} ({thread.id})", "#70af87")
                        return True
                    else:
                        await self.bot.log(f"Thread {specific_thread} not found or not a thread", "#af7070")
                        return False
                except Exception as e:
                    await self.bot.log(f"Error switching to specified thread {specific_thread}: {e}", "#af7070")
                    return False
            
            # Smart channel selection based on safety
            if self.bot.config_dict.get("channel_switcher", {}).get("smart_selection", True):
                safest_channel = None
                highest_safety = -1
                
                # Analyze safety of each channel
                for channel in available_targets:
                    if channel is None:
                        continue  # Skip null channels
                        
                    if len(available_targets) > 1 and channel == self.active_channel:
                        continue  # Skip current channel unless it's the only one
                    
                    try:
                        safety_score = await self.analyze_channel_safety(channel)
                        
                        # Ensure the channel meets minimum safety requirements
                        min_safety = self.bot.config_dict.get("channel_switcher", {}).get("safety_features", {}).get("min_safety_score", 40)
                        if safety_score < min_safety:
                            await self.bot.log(f"Channel {getattr(channel, 'name', 'unknown')} safety score {safety_score} below minimum {min_safety}", "#af7070")
                            continue
                        
                        if safety_score > highest_safety:
                            highest_safety = safety_score
                            safest_channel = channel
                    except Exception as e:
                        await self.bot.log(f"Error analyzing channel {getattr(channel, 'id', 'unknown')}: {e}", "#af7070")
                        continue  # Skip this channel if analysis fails
                
                if safest_channel:
                    new_channel = safest_channel
                    await self.bot.log(f"Smart selection chose channel with safety score: {highest_safety}", "#70af87")
                else:
                    # Fallback to random selection
                    available_targets_filtered = [c for c in available_targets if c is not None and c != self.active_channel]
                    if not available_targets_filtered:
                        available_targets_filtered = [c for c in available_targets if c is not None]
                    
                    if not available_targets_filtered:
                        await self.bot.log("No valid channels available for switching", "#af7070")
                        return False
                        
                    new_channel = random.choice(available_targets_filtered)
            else:
                # Random channel selection
                if len(available_targets) > 1 and self.active_channel in available_targets:
                    # Avoid selecting the current channel
                    available_targets = [c for c in available_targets if c is not None and c != self.active_channel]
                else:
                    available_targets = [c for c in available_targets if c is not None]
                
                if not available_targets:
                    await self.bot.log("No valid channels available for switching", "#af7070")
                    return False
                    
                new_channel = random.choice(available_targets)
            
            if new_channel is None:
                await self.bot.log("Selected channel is None, cannot switch", "#af7070")
                return False
                
            try:
                # Final validation before switching
                if not hasattr(new_channel, 'id') or not hasattr(new_channel, 'name'):
                    await self.bot.log("Selected channel is invalid (missing id or name)", "#af7070")
                    return False
                
                self.bot.cm = new_channel
                self.active_channel = new_channel
                self.last_switch_time = time.time()
                self.commands_since_switch = 0
                
                # Determine channel type for logging
                channel_type = "thread" if isinstance(new_channel, discord.Thread) else "channel"
                await self.bot.log(f"Switched to {channel_type}: {new_channel.name} ({new_channel.id})", "#70af87")
                
                return True
            except Exception as e:
                await self.bot.log(f"Error during final channel switch: {e}", "#af7070")
                return False
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle command count tracking for channel switching"""
        if not self.bot.config_dict.get("channel_switcher", {}).get("enabled", False):
            return
            
        if message.author.id == self.bot.user.id and message.channel.id == self.bot.cm.id:
            self.commands_since_switch += 1
            
        # Check for slowmode
        if (message.channel.id == self.bot.cm.id and 
            self.bot.config_dict.get("channel_switcher", {}).get("switch_on_slowmode", True) and
            hasattr(message.channel, 'slowmode_delay') and 
            message.channel.slowmode_delay > 0):
            # Check for high message volume
            async for msg in message.channel.history(limit=10, after=discord.utils.utcnow() - timedelta(seconds=30)):
                if msg.author.id == self.bot.user.id:
                    # Bot has sent messages in last 30 seconds, switch channels
                    await self.switch_channel()
                    break
                    
        # Smart switching - avoid active channels
        if (self.bot.config_dict.get("channel_switcher", {}).get("avoid_active_channels", True) and
            message.channel.id == self.bot.cm.id and 
            message.author.id != self.bot.user.id and 
            message.author.id != self.bot.owo_bot_id):
            # Count recent messages from other users
            user_msg_count = 0
            async for msg in message.channel.history(limit=20, after=discord.utils.utcnow() - timedelta(seconds=60)):
                if msg.author.id != self.bot.user.id and msg.author.id != self.bot.owo_bot_id:
                    user_msg_count += 1
            
            # If channel is active with other users, consider switching
            if user_msg_count >= 5:  # Threshold for "active" channel
                await self.switch_channel()

    async def handle_channel_command(self, message, command_type):
        """Handle channel-related text commands"""
        prefix = self.bot.config_dict['textCommands']['prefix']
        channel_cmds = self.bot.config_dict["textCommands"].get("channel_commands", {})
        
        # Switch command
        if command_type == "switch":
            args = message.content.replace(f"{prefix}{channel_cmds.get('switch', 'switch')}", "").strip().split()
            
            if not args:
                # No args, just switch to a random channel
                success = await self.switch_channel()
                if success:
                    await message.channel.send("Switched to random channel/thread.")
                else:
                    await message.channel.send("Failed to switch channel. No channels available.")
            else:
                try:
                    channel_id = int(args[0])
                    # Determine if it's a thread or channel
                    is_thread = False
                    
                    # Check if it's in available threads
                    for thread in self.available_threads:
                        if thread.id == channel_id:
                            is_thread = True
                            break
                    
                    if is_thread:
                        success = await self.switch_channel(specific_thread=channel_id)
                    else:
                        success = await self.switch_channel(specific_channel=channel_id)
                    
                    if success:
                        await message.channel.send(f"Switched to {'thread' if is_thread else 'channel'} {channel_id}.")
                    else:
                        await message.channel.send(f"Failed to switch to {channel_id}.")
                except ValueError:
                    await message.channel.send("Invalid channel ID. Please provide a valid ID.")
        
        # List channels command
        elif command_type == "channels":
            try:
                channel_list = "**Available Channels:**\n"
                
                if not self.available_channels:
                    channel_list += "No channels configured.\n"
                else:
                    for channel in self.available_channels:
                        if channel is None:
                            continue
                            
                        try:
                            marker = "→ " if self.active_channel and channel.id == self.active_channel.id else "  "
                            safety_score = await self.analyze_channel_safety(channel)
                            channel_list += f"{marker}Channel: {channel.name} (`{channel.id}`) - Safety: {safety_score}/100\n"
                        except Exception as e:
                            await self.bot.log(f"Error listing channel: {e}", "#af7070")
                            # Add error indication for this channel
                            channel_list += f"  Error retrieving channel info\n"
                
                channel_list += "\n**Available Threads:**\n"
                
                if not self.available_threads:
                    channel_list += "No threads configured.\n"
                else:
                    for thread in self.available_threads:
                        if thread is None:
                            continue
                            
                        try:
                            marker = "→ " if self.active_channel and thread.id == self.active_channel.id else "  "
                            safety_score = await self.analyze_channel_safety(thread)
                            channel_list += f"{marker}Thread: {thread.name} (`{thread.id}`) - Safety: {safety_score}/100\n"
                        except Exception as e:
                            await self.bot.log(f"Error listing thread: {e}", "#af7070")
                            # Add error indication for this thread
                            channel_list += f"  Error retrieving thread info\n"
                
                if not self.available_channels and not self.available_threads:
                    channel_list += "\nNo channels or threads configured. Use the discovery or create commands to add some.\n"
                
                current_info = ""
                if self.active_channel:
                    try:
                        current_info = f"\nCurrent: {self.active_channel.name} (ID: {self.active_channel.id})"
                    except Exception:
                        current_info = "\nCurrent: Unknown (error retrieving info)"
                else:
                    current_info = "\nCurrent: None"
                    
                channel_list += current_info
                
                # Split message if it's too long
                if len(channel_list) > 1900:
                    # Send the first part
                    await message.channel.send(channel_list[:1900] + "...\n(List too long, showing partial results)")
                else:
                    await message.channel.send(channel_list)
                    
            except Exception as e:
                await self.bot.log(f"Error in channels command: {e}", "#af7070")
                await message.channel.send(f"Error listing channels: {e}")
        
        # Create thread command
        elif command_type == "createthread":
            args = message.content.replace(f"{prefix}{channel_cmds.get('createthread', 'createthread')}", "").strip().split()
            
            channel = None
            thread_name = None
            
            # Parse arguments
            if args:
                for arg in args:
                    if arg.isdigit() and len(arg) > 10:  # Likely a channel ID
                        try:
                            channel_id = int(arg)
                            channel = self.bot.get_channel(channel_id)
                            if not channel:
                                channel = await self.bot.fetch_channel(channel_id)
                        except:
                            pass
                    elif not thread_name:  # First non-ID arg is the thread name
                        thread_name = arg
            
            # Create thread
            if not channel:
                channel = message.channel
            
            thread = await self.create_new_thread(channel=channel, name=thread_name)
            
            if thread:
                await message.channel.send(f"Created new thread: {thread.name} (ID: {thread.id}) and switched to it.")
            else:
                await message.channel.send("Failed to create thread. Check permissions or try another channel.")
        
        # Create channel command
        elif command_type == "createchannel":
            if not self.bot.config_dict.get("channel_switcher", {}).get("auto_create_channel", False):
                await message.channel.send("Channel creation is disabled in config for safety. Enable it first.")
                return
                
            args = message.content.replace(f"{prefix}{channel_cmds.get('createchannel', 'createchannel')}", "").strip().split()
            
            channel_name = None
            if args:
                channel_name = args[0]
            
            guild = message.guild
            if not guild:
                await message.channel.send("This command can only be used in a server.")
                return
            
            channel = await self.create_new_channel(guild, name=channel_name)
            
            if channel:
                await message.channel.send(f"Created new channel: {channel.name} (ID: {channel.id}) and switched to it.")
            else:
                await message.channel.send("Failed to create channel. Check permissions.")
        
        # Discover channels command
        elif command_type == "discover":
            if not self.bot.config_dict.get("channel_switcher", {}).get("auto_discover", False):
                await message.channel.send("Channel discovery is disabled in config.")
                return
                
            await message.channel.send("Starting channel discovery... This may take a moment.")
            
            # Store current channel count
            old_channel_count = len(self.available_channels)
            old_thread_count = len(self.available_threads)
            
            # Run discovery
            await self.discover_channels()
            
            # Calculate new additions
            new_channels = len(self.available_channels) - old_channel_count
            new_threads = len(self.available_threads) - old_thread_count
            
            await message.channel.send(f"Discovery complete! Found {new_channels} new channels and {new_threads} new threads.")
        
        # Safety check command
        elif command_type == "safety":
            args = message.content.replace(f"{prefix}{channel_cmds.get('safety', 'safety')}", "").strip().split()
            
            if not args:
                # Check current channel
                channel = self.active_channel if self.active_channel else message.channel
                safety_score = await self.analyze_channel_safety(channel)
                await message.channel.send(f"Safety analysis for {channel.name}:\nSafety score: {safety_score}/100\n{'✅ Recommended' if safety_score >= 60 else '⚠️ Use with caution' if safety_score >= 30 else '❌ Not recommended'}")
            else:
                try:
                    channel_id = int(args[0])
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        channel = await self.bot.fetch_channel(channel_id)
                    
                    if channel:
                        safety_score = await self.analyze_channel_safety(channel)
                        await message.channel.send(f"Safety analysis for {channel.name}:\nSafety score: {safety_score}/100\n{'✅ Recommended' if safety_score >= 60 else '⚠️ Use with caution' if safety_score >= 30 else '❌ Not recommended'}")
                    else:
                        await message.channel.send(f"Channel {channel_id} not found.")
                except:
                    await message.channel.send("Invalid channel ID. Please provide a valid ID.")
        
        # Add channel command
        elif command_type == "addchannel":
            args = message.content.replace(f"{prefix}{channel_cmds.get('addchannel', 'addchannel')}", "").strip().split()
            
            if not args:
                await message.channel.send("Please provide a channel ID to add.")
            else:
                try:
                    channel_id = int(args[0])
                    
                    # Check if channel already exists in config
                    channel_ids = self.bot.config_dict.get("channel_switcher", {}).get("channels", [])
                    if channel_id in channel_ids:
                        await message.channel.send(f"Channel {channel_id} is already in the channel list.")
                        return
                    
                    # Add to config
                    channel_ids.append(channel_id)
                    self.bot.config_dict["channel_switcher"]["channels"] = channel_ids
                    
                    # Save config
                    with open("config.json", "w") as config_file:
                        json.dump(self.bot.config_dict, config_file, indent=4)
                    
                    # Update channel list
                    await self.update_channel_list()
                    
                    await message.channel.send(f"Added channel {channel_id} to the channel list.")
                except ValueError:
                    await message.channel.send("Invalid channel ID. Please provide a valid ID.")
        
        # Remove channel command
        elif command_type == "removechannel":
            args = message.content.replace(f"{prefix}{channel_cmds.get('removechannel', 'removechannel')}", "").strip().split()
            
            if not args:
                await message.channel.send("Please provide a channel ID to remove.")
            else:
                try:
                    channel_id = int(args[0])
                    
                    # Check if channel exists in config
                    channel_ids = self.bot.config_dict.get("channel_switcher", {}).get("channels", [])
                    if channel_id not in channel_ids:
                        await message.channel.send(f"Channel {channel_id} is not in the channel list.")
                        return
                    
                    # Remove from config
                    channel_ids.remove(channel_id)
                    self.bot.config_dict["channel_switcher"]["channels"] = channel_ids
                    
                    # Save config
                    with open("config.json", "w") as config_file:
                        json.dump(self.bot.config_dict, config_file, indent=4)
                    
                    # Update channel list
                    await self.update_channel_list()
                    
                    await message.channel.send(f"Removed channel {channel_id} from the channel list.")
                except ValueError:
                    await message.channel.send("Invalid channel ID. Please provide a valid ID.")
        
        # Add thread command
        elif command_type == "addthread":
            args = message.content.replace(f"{prefix}{channel_cmds.get('addthread', 'addthread')}", "").strip().split()
            
            if len(args) < 1:
                await message.channel.send("Please provide a thread ID to add.")
            else:
                try:
                    thread_id = int(args[0])
                    
                    # Enable threads in config if not already
                    if not self.bot.config_dict["channel_switcher"]["threads"].get("enabled", False):
                        self.bot.config_dict["channel_switcher"]["threads"]["enabled"] = True
                    
                    # Check if thread already exists in config
                    thread_ids = self.bot.config_dict["channel_switcher"]["threads"].get("thread_ids", [])
                    if thread_id in thread_ids:
                        await message.channel.send(f"Thread {thread_id} is already in the thread list.")
                        return
                    
                    # Add to config
                    thread_ids.append(thread_id)
                    self.bot.config_dict["channel_switcher"]["threads"]["thread_ids"] = thread_ids
                    
                    # Try to get parent channel if not set
                    if self.bot.config_dict["channel_switcher"]["threads"].get("parent_channel", 0) == 0:
                        try:
                            thread = None
                            for t in self.bot.get_all_threads():
                                if t.id == thread_id:
                                    thread = t
                                    break
                            
                            if thread is None:
                                thread = await self.bot.fetch_channel(thread_id)
                            
                            if thread and isinstance(thread, discord.Thread):
                                self.bot.config_dict["channel_switcher"]["threads"]["parent_channel"] = thread.parent_id
                        except:
                            pass
                    
                    # Save config
                    with open("config.json", "w") as config_file:
                        json.dump(self.bot.config_dict, config_file, indent=4)
                    
                    # Update channel list
                    await self.update_channel_list()
                    
                    await message.channel.send(f"Added thread {thread_id} to the thread list.")
                except ValueError:
                    await message.channel.send("Invalid thread ID. Please provide a valid ID.")
        
        # Remove thread command
        elif command_type == "removethread":
            args = message.content.replace(f"{prefix}{channel_cmds.get('removethread', 'removethread')}", "").strip().split()
            
            if not args:
                await message.channel.send("Please provide a thread ID to remove.")
            else:
                try:
                    thread_id = int(args[0])
                    
                    # Check if thread exists in config
                    thread_ids = self.bot.config_dict["channel_switcher"]["threads"].get("thread_ids", [])
                    if thread_id not in thread_ids:
                        await message.channel.send(f"Thread {thread_id} is not in the thread list.")
                        return
                    
                    # Remove from config
                    thread_ids.remove(thread_id)
                    self.bot.config_dict["channel_switcher"]["threads"]["thread_ids"] = thread_ids
                    
                    # Save config
                    with open("config.json", "w") as config_file:
                        json.dump(self.bot.config_dict, config_file, indent=4)
                    
                    # Update channel list
                    await self.update_channel_list()
                    
                    await message.channel.send(f"Removed thread {thread_id} from the thread list.")
                except ValueError:
                    await message.channel.send("Invalid thread ID. Please provide a valid ID.")
                    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle command count tracking for channel switching"""
        if not self.bot.config_dict.get("channel_switcher", {}).get("enabled", False):
            return
            
        if message.author.id == self.bot.user.id and message.channel.id == self.bot.cm.id:
            self.commands_since_switch += 1
            
        # Check for slowmode
        if (message.channel.id == self.bot.cm.id and 
            self.bot.config_dict.get("channel_switcher", {}).get("switch_on_slowmode", True) and
            hasattr(message.channel, 'slowmode_delay') and 
            message.channel.slowmode_delay > 0):
            # Check for high message volume
            async for msg in message.channel.history(limit=10, after=discord.utils.utcnow() - timedelta(seconds=30)):
                if msg.author.id == self.bot.user.id:
                    # Bot has sent messages in last 30 seconds, switch channels
                    await self.switch_channel()
                    break
                    
        # Smart switching - avoid active channels
        if (self.bot.config_dict.get("channel_switcher", {}).get("avoid_active_channels", True) and
            message.channel.id == self.bot.cm.id and 
            message.author.id != self.bot.user.id and 
            message.author.id != self.bot.owo_bot_id):
            # Count recent messages from other users
            user_msg_count = 0
            async for msg in message.channel.history(limit=20, after=discord.utils.utcnow() - timedelta(seconds=60)):
                if msg.author.id != self.bot.user.id and msg.author.id != self.bot.owo_bot_id:
                    user_msg_count += 1
            
            # If channel is active with other users, consider switching
            if user_msg_count >= 5:  # Threshold for "active" channel
                await self.switch_channel()
                
        # Check for text commands
        if message.content.startswith(self.bot.config_dict['textCommands']['prefix']) and message.author.id in self.bot.config_dict['textCommands'].get('allowedUsers', []):
            prefix = self.bot.config_dict['textCommands']['prefix']
            channel_cmds = self.bot.config_dict["textCommands"].get("channel_commands", {})
            
            # Check for channel commands
            if message.content.startswith(f"{prefix}{channel_cmds.get('switch', 'switch')}"):
                await self.handle_channel_command(message, "switch")
            elif message.content.startswith(f"{prefix}{channel_cmds.get('channels', 'channels')}"):
                await self.handle_channel_command(message, "channels")
            elif message.content.startswith(f"{prefix}{channel_cmds.get('addchannel', 'addchannel')}"):
                await self.handle_channel_command(message, "addchannel")
            elif message.content.startswith(f"{prefix}{channel_cmds.get('removechannel', 'removechannel')}"):
                await self.handle_channel_command(message, "removechannel")
            elif message.content.startswith(f"{prefix}{channel_cmds.get('addthread', 'addthread')}"):
                await self.handle_channel_command(message, "addthread")
            elif message.content.startswith(f"{prefix}{channel_cmds.get('removethread', 'removethread')}"):
                await self.handle_channel_command(message, "removethread")
            elif message.content.startswith(f"{prefix}{channel_cmds.get('createthread', 'createthread')}"):
                await self.handle_channel_command(message, "createthread")
            elif message.content.startswith(f"{prefix}{channel_cmds.get('createchannel', 'createchannel')}"):
                await self.handle_channel_command(message, "createchannel")
            elif message.content.startswith(f"{prefix}{channel_cmds.get('discover', 'discover')}"):
                await self.handle_channel_command(message, "discover")
            elif message.content.startswith(f"{prefix}{channel_cmds.get('safety', 'safety')}"):
                await self.handle_channel_command(message, "safety")

async def setup(bot):
    await bot.add_cog(ChannelSwitcher(bot)) 