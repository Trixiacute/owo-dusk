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

import re
import asyncio

from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded


won_pattern = r"and won <:cowoncy:\d+> ([\d,]+)"
lose_pattern = r"bet <:cowoncy:\d+> ([\d,]+)"

"""
NOTE:
fix it spamming "won nothing"
"""

class Slots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cmd = {
            "cmd_name": self.bot.alias["slots"]["normal"],
            "cmd_arguments": None,
            "prefix": True,
            "checks": True,
            "retry_count": 0,
            "id": "slots"
        }
        self.turns_lost = 0
        self.exceeded_max_amount = False
        self.goal_reached = False


    async def cog_load(self):
        
        if not self.bot.config_dict["gamble"]["slots"]["enabled"]:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.slots"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.start_slots(startup=True))

    async def cog_unload(self):
        await self.bot.remove_queue(id="slots")

    async def start_slots(self, startup=False):
        try:
            if startup:
                await asyncio.sleep(self.bot.random_float(self.bot.config_dict["defaultCooldowns"]["briefCooldown"]))
            else:
                await self.bot.remove_queue(id="slots")
                await asyncio.sleep(self.bot.random_float(self.bot.config_dict["gamble"]["slots"]["cooldown"]))

            amount_to_gamble = int(self.bot.config_dict["gamble"]["slots"]["startValue"]*(self.bot.config_dict["gamble"]["slots"]["multiplierOnLose"]**self.turns_lost))
            if self.bot.config_dict["gamble"]["goalSystem"]["enabled"] and self.bot.gain_or_lose > self.bot.config_dict["gamble"]["goalSystem"]["amount"]:
                if not self.goal_reached:
                    self.goal_reached = True
                    await self.bot.log(f"goal reached - {self.bot.gain_or_lose}/{self.bot.config_dict["gamble"]["goalSystem"]["amount"]}, stopping slots!", "#ffd7af")

                return await self.start_slots()
            else:
                # ensure goal amount change does not prevent goal recieved message (website dashboard)
                self.goal_reached = False

            if (amount_to_gamble > self.bot.balance) or (self.bot.gain_or_lose+self.bot.config_dict["gamble"]["allottedAmount"] <=0):
                return await self.start_slots()
                
            if amount_to_gamble > 250000:
                self.exceeded_max_amount = True
            else:
                self.cmd["cmd_arguments"] = str(amount_to_gamble)
                await self.bot.put_queue(self.cmd)
                
        except Exception as e:
            print(e)


    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.id != 408785106942164992:
            return
        if before.channel.id != self.bot.channel_id:
            return
        if self.exceeded_max_amount:
            return
        
        if "slots" in after.content.lower():
            if "and won nothing... :c" in after.content:
                """Lose cash"""
                match = int(re.search(lose_pattern, after.content).group(1).replace(",",""))
                self.bot.balance-=match
                self.bot.gain_or_lose-=match
                self.turns_lost+=1
                await self.bot.log(f"lost {match} in slots, net profit - {self.bot.gain_or_lose}", "#ffafaf")
                await self.start_slots()
            else:
                if ("<:eggplant:417475705719226369>" in after.content.lower()
                and "and won" in after.content.lower()):
                    """Didn't lose case but earned nothing"""
                    await self.bot.log(f"didn't win or lose slots", "#ffafaf")
                    await self.start_slots()

                elif "and won" in after.content.lower():
                    """won cash"""
                    won_match = int(re.search(won_pattern, after.content).group(1).replace(",",""))
                    lose_match = int(re.search(won_pattern, after.content).group(1).replace(",",""))
                    profit = won_match-lose_match
                    self.bot.balance+=profit
                    self.bot.gain_or_lose+=profit
                    self.turns_lost = 0
                    await self.bot.log(f"won {won_match} in slots, net profit - {self.bot.gain_or_lose}", "#ffafaf")
                    await self.start_slots()


async def setup(bot):
    await bot.add_cog(Slots(bot))

