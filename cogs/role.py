import discord
from discord.ext import commands
from core.classes import Cog_Extension

class Role(Cog_Extension):

  @commands.command()
  async def role(self, ctx, name):
      guild = ctx.guild
      role = await guild.create_role(name=name)    #這兩行用於創建身分組
      category = await guild.create_category(name) #^
      overwrites = {
          guild.default_role: discord.PermissionOverwrite(read_messages=False),
          role: discord.PermissionOverwrite(read_messages=True),
      }
      channel1 = await category.create_text_channel(name, overwrites=overwrites) #創建文字頻道
      channel2 = await category.create_voice_channel(name, overwrites=overwrites) #創建語音頻道
      await ctx.send("完成")

async def setup(bot):
    await bot.add_cog(Role(bot))      