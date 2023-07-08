import discord
from discord.ext import commands
from core.classes import Cog_Extension
import json

class cmd(Cog_Extension):

 #刪除所傳的訊息並讓機器人覆誦
  @commands.command()
  async def say(self,ctx,msg):
      if ctx.author.guild_permissions.administrator:
          await ctx.message.delete()
          await ctx.send(msg)
      else:
          await ctx.send("你沒有管理者權限用來執行這個指令")

 #刪除所選數量的訊息
  @commands.command()
  async def delete(self,ctx,num:int):
      if ctx.author.guild_permissions.administrator:
          #刪除訊息(因為指令也算一條訊息 所以num+1)
          await ctx.channel.purge(limit=num+1)
      else:
          await ctx.send("你沒有管理者權限用來執行這個指令")

  @commands.command()
  async def ban(self, ctx, member: discord.Member):
      if ctx.author.guild_permissions.administrator:
          await member.ban()
          await ctx.send(f'{member} 已踢出伺服器')
      else:
          await ctx.send("你沒有管理者權限用來執行這個指令")

async def setup(bot):
    await bot.add_cog(cmd(bot))