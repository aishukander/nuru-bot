import discord
from discord.ext import commands
from core.classes import Cog_Extension

class role(Cog_Extension):

  #創建身分組並且添加文字和語音頻道
  @commands.command()
  async def role(self, ctx, name):
      guild = ctx.guild
      role = await guild.create_role(name=name)
      category = await guild.create_category(name)
      overwrites = {
          guild.default_role: discord.PermissionOverwrite(read_messages=False),
          role: discord.PermissionOverwrite(read_messages=True),
      }
      channel1 = await category.create_text_channel(name, overwrites=overwrites)
      channel2 = await category.create_voice_channel(name, overwrites=overwrites)
      await ctx.send("完成")

async def setup(bot):
    await bot.add_cog(role(bot))