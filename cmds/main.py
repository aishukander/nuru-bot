import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json
import os
import random

with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata = json.load(jfile)

class Main(Cog_Extension):

  @commands.Cog.listener()
  async def on_message(self,msg):
    if msg.content.endswith('好了ㄝ'):
     await msg.channel.send('怎麼又好了ㄝ ?')   

def setup(bot):
  bot.add_cog(Main(bot))