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

import asyncio
import random
import time
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
from utils.human_behavior import HumanBehaviorSimulator, human_delay, vary_cooldown
from copy import deepcopy



class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.checks = []
        self.calc_time = timedelta(0)
        self.command_handler.start()
        self.human_simulator = HumanBehaviorSimulator()

    async def start_commands(self):
        await asyncio.sleep(self.bot.random_float(self.bot.config_dict["account"]["commandsHandlerStartDelay"]))
        await self.bot.shuffle_queue()
        self.send_commands.start()
        self.monitor_checks.start()

    async def cog_load(self):
        """Run join_previous_giveaways when bot is ready"""
        asyncio.create_task(self.start_commands())
    
    """send commands"""
    @tasks.loop()
    async def send_commands(self):
        try:
            cmd = await self.bot.queue.get()
            if cmd.get("checks"):
                if cmd.get("id"):
                    in_queue = await self.bot.search_checks(id=cmd["id"])
                    if not in_queue:
                        async with self.bot.lock:
                            self.bot.checks.append((cmd, datetime.now(timezone.utc)))
            if self.bot.config_dict["useSlashCommands"] and cmd.get("slash_cmd_name", False):
                await self.bot.slashCommandSender(cmd["slash_cmd_name"])
            else:
                await self.bot.send(self.bot.construct_command(cmd))
            await asyncio.sleep(self.bot.random_float(self.bot.config_dict["defaultCooldowns"]["commandHandler"]["betweenCommands"]))
        except Exception as e:
            print(f"Error in send_commands loop: {e}")
            await asyncio.sleep(self.bot.random_float(self.bot.config_dict["defaultCooldowns"]["commandHandler"]["betweenCommands"]))

    @tasks.loop(seconds=1)
    async def monitor_checks(self):
        try:
            current_time = datetime.now(timezone.utc)
            if not self.bot.state or self.bot.sleep or self.bot.captcha:
                if not hasattr(self, "calc_time"):
                    self.calc_time = timedelta(0)
                self.calc_time += current_time - getattr(self, "last_check_time", current_time)
            else:
                if not hasattr(self, "calc_time"):
                    self.calc_time = timedelta(0)
                async with self.bot.lock:
                    for index, (command, timestamp) in enumerate(self.bot.checks[:]):
                        if command.get("removed"):
                            self.bot.checks.remove((command, timestamp))
                            continue
                        adjusted_time = timestamp + self.calc_time
                        if (current_time - adjusted_time).total_seconds() > self.bot.config_dict["defaultCooldowns"]["commandHandler"]["beforeReaddingToQueue"]:
                            await self.bot.put_queue(command)
                            self.bot.checks.remove((command, timestamp))
                self.calc_time = timedelta(0)
            self.last_check_time = current_time
        except Exception as e:
            print(f"Error in monitor_checks: {e}")
            if not hasattr(self, "calc_time"):
                self.calc_time = timedelta(0)

    @tasks.loop(seconds=1)
    async def command_handler(self):
        try:
            await asyncio.sleep(self.bot.random_float(self.bot.config_dict["defaultCooldowns"]["commandHandler"]["betweenCommands"]))
            
            # Check if anti-detection is enabled
            use_human_behavior = self.bot.config_dict.get("anti_detection", {}).get("enabled", False)
            
            # If enabled, use human-like delay instead of fixed delay
            if use_human_behavior:
                # Determine command complexity based on queue size
                if self.bot.queue.qsize() > 5:
                    complexity = "simple"  # Faster processing when many commands
                elif self.bot.queue.qsize() > 2:
                    complexity = "normal"
                else:
                    complexity = "complex"  # More careful timing when fewer commands
                
                # Apply human-like delay
                await human_delay(self.human_simulator, complexity)
                
                # Check if we should take a break (simulate human behavior)
                if self.human_simulator.should_take_break():
                    break_duration = self.human_simulator.get_break_duration()
                    await self.bot.log(f"Taking a break for {break_duration:.1f}s to simulate human behavior", "#87af87")
                    self.human_simulator.register_break()
                    await asyncio.sleep(break_duration)
                
                # Check if we should be active right now based on time of day
                should_be_active, probability = self.human_simulator.should_be_active_now()
                if not should_be_active and self.bot.config_dict.get("anti_detection", {}).get("active_hours", {}).get("use_profile", True):
                    # Low chance to still run if inactive period but not zero
                    if random.random() > 0.1:  # 90% chance to follow the activity profile
                        await self.bot.log(f"Inactive period based on human profile ({probability:.2f} probability). Waiting...", "#87af87")
                        await asyncio.sleep(300)  # Wait 5 minutes before checking again
                        return
                    
            while not self.bot.queue.empty() and self.bot.state and not self.bot.captcha:
                try:
                    command = await self.bot.queue.get()
                    retried = False
                    
                    # Skip commands that have been marked for removal
                    if command.get("removed", False):
                        continue
                        
                    # Build complete command string
                    complete_command = self.bot.construct_command(command)
                    
                    # Check if we need to add to checks for wait/retry
                    if command.get("checks", False):
                        retry_count = command.get("retry_count", 0)
                        
                        # Limit retry attempts
                        if retry_count >= 5:
                            await self.bot.log(f"Too many retries for {complete_command}, skipping", "#af7070")
                            continue
                            
                        # Add to checks list for verification
                        command["retry_count"] = retry_count + 1
                        async with self.bot.lock:
                            self.bot.checks.append((command, datetime.now(timezone.utc)))
                        
                    # Execute the command
                    await self.bot.send(complete_command)
                    
                    # Register action with human simulator if enabled
                    if use_human_behavior:
                        self.human_simulator.register_action()
                    
                    # Apply human-like delay after command if enabled
                    if use_human_behavior and self.bot.config_dict.get("anti_detection", {}).get("command_timing", {}).get("randomize_cooldowns", True):
                        base_cooldown = random.uniform(2, 4)
                        cooldown = vary_cooldown(base_cooldown, 
                                               self.bot.config_dict.get("anti_detection", {}).get("command_timing", {}).get("variation_percent", 15))
                        await asyncio.sleep(cooldown)
                    else:
                        # Default delay without human behavior
                        await asyncio.sleep(random.uniform(2, 4))
                        
                    await self.handle_checks()
                    
                except Exception as e:
                    # Error handling with human-like retry behavior
                    await self.bot.log(f"Error in command handler: {e}", "#af7070")
                    
                    # Human-like response to errors
                    if use_human_behavior:
                        # Humans tend to wait a bit after errors before retrying
                        await asyncio.sleep(random.uniform(5, 10))
                    else:
                        await asyncio.sleep(random.uniform(1, 3))
            
        except Exception as e:
            await self.bot.log(f"Command handler error: {e}", "#af7070")

    @command_handler.before_loop
    async def before_cmd_handler(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(
            self.bot.random_float(
                self.bot.config_dict["account"]["commandsHandlerStartDelay"]
            )
        )

    async def handle_checks(self):
        try:
            # Human-like timing between checking results
            use_human_behavior = self.bot.config_dict.get("anti_detection", {}).get("enabled", False)
            if use_human_behavior:
                await asyncio.sleep(random.uniform(0.8, 1.5))  # Human-like variation
            else:
                await asyncio.sleep(1)
                
            current_time = datetime.now(timezone.utc)
            index = 0
            
            async with self.bot.lock:
                while index < len(self.bot.checks):
                    command, timestamp = self.bot.checks[index]
                    
                    # Skip commands marked for removal
                    if command.get("removed", False):
                        self.bot.checks.pop(index)
                        continue
                        
                    # Check if command has been waiting too long
                    # Convert to seconds for comparison if needed
                    time_diff = 0
                    if isinstance(timestamp, datetime):
                        time_diff = (current_time - timestamp).total_seconds()
                    else:  # Handle legacy timestamps stored as float
                        time_diff = (current_time - datetime.fromtimestamp(timestamp, tz=timezone.utc)).total_seconds()
                        
                    if time_diff > self.bot.config_dict["defaultCooldowns"]["commandHandler"]["beforeReaddingToQueue"]:
                        self.bot.checks.pop(index)
                        await self.bot.log(f"Retrying {command.get('cmd_name')} (attempt {command.get('retry_count')})", "#af7070")
                        
                        # Human-like behavior for retries
                        if use_human_behavior and command.get("retry_count", 0) > 1:
                            # Humans might be more careful on second/third attempts
                            await human_delay(self.human_simulator, "complex")
                        
                        await self.bot.put_queue(command)
                    else:
                        index += 1
                        
        except Exception as e:
            await self.bot.log(f"Error in handle_checks: {e}", "#af7070")

    def cog_unload(self):
        self.command_handler.cancel()




async def setup(bot):
    await bot.add_cog(Commands(bot))