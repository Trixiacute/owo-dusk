# This file is part of owo-dusk.
#
# Copyright (c) 2024-present EchoQuill
#
# Portions of this file are based on code by EchoQuill, licensed under the
# GNU General Public License v3.0 (GPL-3.0).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import time
import discord
import psutil
import json
from discord.ext import commands
from utils.platform_utils import IS_TERMUX


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_status_time = 0
    
    @commands.Cog.listener()
    async def on_message(self, message):
        prefix = self.bot.config_dict['textCommands']['prefix']
        
        # Check if message author is allowed to use commands
        if message.author.id in [self.bot.user.id, 1209017744696279041] + self.bot.config_dict["textCommands"]["allowedUsers"]:
            # Process standard commands
            if f"{prefix}{self.bot.config_dict['textCommands']['commandToStopUser']}" in message.content.lower():
                await self.bot.log("stopping owo-dusk..","#87875f")
                self.bot.sleep=True

            elif f"{prefix}{self.bot.config_dict['textCommands']['commandToStartUser']}" in message.content.lower():
                await self.bot.log("starting owo-dusk..","#87875f")
                self.bot.sleep=False
                
            # Process Termux-specific commands if enabled
            termux_mode_enabled = self.bot.config_dict.get("termux_mode", {}).get("enabled", False)
            extended_commands_enabled = self.bot.config_dict.get("termux_mode", {}).get("extended_text_commands", False)
            
            if (IS_TERMUX and termux_mode_enabled and extended_commands_enabled) or self.bot.config_dict.get("termux_mode", {}).get("enabled", False):
                termux_cmds = self.bot.config_dict["textCommands"].get("termux_commands", {})
                
                # Status command
                if f"{prefix}{termux_cmds.get('status', 'status')}" in message.content.lower():
                    await self.send_status(message.channel)
                
                # Info command
                elif f"{prefix}{termux_cmds.get('info', 'info')}" in message.content.lower():
                    await self.send_info(message.channel)
                
                # Stats command
                elif f"{prefix}{termux_cmds.get('stats', 'stats')}" in message.content.lower():
                    await self.send_stats(message.channel)
                
                # Cash command
                elif f"{prefix}{termux_cmds.get('cash', 'cash')}" in message.content.lower():
                    await self.send_cash_info(message.channel)
                
                # Commands command
                elif f"{prefix}{termux_cmds.get('commands', 'commands')}" in message.content.lower():
                    await self.list_commands(message.channel)
                
                # Help command
                elif f"{prefix}{termux_cmds.get('help', 'help')}" in message.content.lower():
                    await self.send_help(message.channel)
                
                # Restart command
                elif f"{prefix}{termux_cmds.get('restart', 'restart')}" in message.content.lower():
                    await self.restart_bot(message.channel)
                    
    async def send_status(self, channel):
        # Rate limit status command to prevent spam
        current_time = time.time()
        if current_time - self.last_status_time < self.bot.config_dict.get("termux_mode", {}).get("status_interval", 60):
            return
            
        self.last_status_time = current_time
        
        # Get bot status information
        uptime = time.time() - self.bot.uptime if hasattr(self.bot, 'uptime') else time.time() - time.time()
        hours, remainder = divmod(int(uptime), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        
        # Get system information
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        
        status_msg = (
            f"**OwO-Dusk Status**\n"
            f"• Running: {'Yes' if not self.bot.sleep else 'No (Paused)'}\n"
            f"• Captcha: {'Yes' if self.bot.captcha else 'No'}\n"
            f"• Connected: {'Yes' if self.bot.is_ready() else 'No'}\n"
            f"• Uptime: {uptime_str}\n"
            f"• CPU: {cpu}%\n"
            f"• Memory: {mem}%\n"
            f"• Commands in queue: {self.bot.queue.qsize() if hasattr(self.bot, 'queue') else 'N/A'}"
        )
        
        await channel.send(status_msg)
        
    async def send_info(self, channel):
        # Basic bot information
        info_msg = (
            f"**OwO-Dusk Information**\n"
            f"• Version: {self.bot.version if hasattr(self.bot, 'version') else 'Unknown'}\n"
            f"• User: {self.bot.user.name}\n"
            f"• Channel: {getattr(self.bot.cm, 'name', 'Unknown')}\n"
            f"• Termux Mode: Enabled\n"
            f"• Prefix: {self.bot.config_dict['setprefix']}\n"
            f"• Text Command Prefix: {self.bot.config_dict['textCommands']['prefix']}"
        )
        
        await channel.send(info_msg)
        
    async def send_stats(self, channel):
        # Get bot statistics
        try:
            with open("utils/stats.json", "r") as f:
                stats = json.load(f)
                
            user_stats = stats.get(str(self.bot.user.id), {})
            
            stats_msg = (
                f"**OwO-Dusk Statistics**\n"
                f"• Daily Claims: {user_stats.get('daily', 0)}\n"
                f"• Cookies Given: {user_stats.get('cookie', 0)}\n"
                f"• Lottery Tickets: {user_stats.get('lottery', 0)}\n"
                f"• Giveaways Joined: {user_stats.get('giveaways', 0)}\n"
            )
            
            await channel.send(stats_msg)
        except Exception as e:
            await channel.send(f"Error retrieving stats: {e}")
            
    async def send_cash_info(self, channel):
        await channel.send("Checking current balance...")
        
        # Add command to check balance to queue
        cash_cmd = {
            "cmd_name": self.bot.alias["cash"]["normal"] if hasattr(self.bot, "alias") and "cash" in self.bot.alias else "cash",
            "prefix": True,
            "checks": True,
            "retry_count": 0,
            "id": "cash_check",
            "removed": False
        }
        
        await self.bot.put_queue(cash_cmd, priority=True)
        
    async def list_commands(self, channel):
        prefix = self.bot.config_dict['textCommands']['prefix']
        termux_cmds = self.bot.config_dict["textCommands"].get("termux_commands", {})
        
        commands_msg = (
            f"**Available Text Commands**\n"
            f"• `{prefix}{self.bot.config_dict['textCommands']['commandToStartUser']}` - Start the bot\n"
            f"• `{prefix}{self.bot.config_dict['textCommands']['commandToStopUser']}` - Stop the bot\n"
            f"• `{prefix}{termux_cmds.get('status', 'status')}` - Show bot status\n"
            f"• `{prefix}{termux_cmds.get('info', 'info')}` - Show bot information\n"
            f"• `{prefix}{termux_cmds.get('stats', 'stats')}` - Show statistics\n"
            f"• `{prefix}{termux_cmds.get('cash', 'cash')}` - Check current balance\n"
            f"• `{prefix}{termux_cmds.get('commands', 'commands')}` - List commands\n"
            f"• `{prefix}{termux_cmds.get('help', 'help')}` - Show help\n"
            f"• `{prefix}{termux_cmds.get('restart', 'restart')}` - Restart bot\n"
        )
        
        await channel.send(commands_msg)
        
    async def send_help(self, channel):
        help_msg = (
            "**OwO-Dusk Termux Mode Help**\n\n"
            "This is a special mode optimized for Termux environments. "
            "The web interface is disabled to save resources, but you can "
            "control the bot using text commands.\n\n"
            "Type `.commands` to see available commands.\n\n"
            "For more detailed help and documentation, visit: "
            "https://github.com/echoqueill/owo-dusk"
        )
        
        await channel.send(help_msg)
        
    async def restart_bot(self, channel):
        await channel.send("Restarting bot processes...")
        
        # Reset bot state
        self.bot.captcha = False
        self.bot.sleep = False
        
        # Clear the queue
        if hasattr(self.bot, 'queue'):
            while not self.bot.queue.empty():
                try:
                    self.bot.queue.get_nowait()
                except:
                    pass
                    
        await channel.send("Bot processes have been restarted.")


async def setup(bot):
    await bot.add_cog(Chat(bot))