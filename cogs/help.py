import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json

with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata = json.load(jfile)

class Help(Cog_Extension):
  
  @commands.command() #help指令
  async def help(self,ctx):
    embed=discord.Embed(title="React說明1", color=0x007bff)
    embed.add_field(name="~help", value="指令說明", inline=False)
    embed.add_field(name="~RTsay", value="React列表1", inline=False)
    embed.add_field(name="~RTsay2", value="React列表2", inline=False)
    embed.add_field(name="~join", value="給你機器人的邀請連結", inline=False)
    embed.add_field(name="~伊蕾娜", value="給你香香的伊蕾娜", inline=False)
    embed.add_field(name="~load 所選模塊", value="加載所選的指令模塊", inline=False)
    embed.add_field(name="~unload 所選模塊", value="卸載所選的指令模塊", inline=False)
    embed.add_field(name="~reload 所選模塊", value="重載所選的指令模塊", inline=False)
    await ctx.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(Help(bot))    