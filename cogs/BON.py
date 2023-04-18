from secrets import choice
import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json
import random

with open('setting.json','r',encoding='utf8') as jfile:
   jdata = json.load(jfile)

class BON(Cog_Extension):
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if self.bot.user.mentioned_in(message) and message.content.endswith("?"):
            if "買" in message.content:
                買不買 = random.choice(jdata['買不買'])
                await message.channel.send(買不買)

async def setup(bot):
    await bot.add_cog(BON(bot)) #因為buy or not沒辦法用所以用這種縮寫